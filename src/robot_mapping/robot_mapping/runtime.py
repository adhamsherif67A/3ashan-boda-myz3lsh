"""Resolve apt or bundled RTAB-Map runtimes for independent vision launches."""
import os
from pathlib import Path
from ament_index_python.packages import (
    get_package_prefix, get_package_share_directory, PackageNotFoundError)


def configure_runtime(package):
    """Return launch environment overrides and expose package lookup to Python."""
    try:
        get_package_prefix(package)
        return {}
    except PackageNotFoundError:
        pass
    share = Path(get_package_share_directory('robot_mapping'))
    candidates = [Path(os.environ.get('MAKO_VO_PREFIX', '/nonexistent'))]
    candidates += [p / '.deps/rtabmap/root/opt/ros/humble'
                   for p in list(share.parents) + list(share.resolve().parents)]
    prefix = next((p for p in candidates if (p / 'share' / package).is_dir()), None)
    if prefix is None:
        raise RuntimeError(f'{package} missing. Install the matching ROS Humble RTAB-Map '
                           'package or set MAKO_VO_PREFIX to the bundled runtime prefix.')
    root = prefix.parents[2]
    paths = {
        'AMENT_PREFIX_PATH': [prefix],
        'PYTHONPATH': [prefix / 'local/lib/python3.10/dist-packages',
                       prefix / 'lib/python3.10/site-packages'],
        'LD_LIBRARY_PATH': [prefix / 'lib', prefix / 'lib/x86_64-linux-gnu',
                            root / 'usr/lib/x86_64-linux-gnu', root / 'usr/lib'],
    }
    environment = {key: ':'.join(map(str, values)) + ':' + os.environ.get(key, '')
                   for key, values in paths.items()}
    os.environ.update(environment)
    return environment
