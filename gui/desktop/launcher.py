#!/usr/bin/env python3
"""Stable launcher: activate verified updates between application sessions."""
import argparse
import base64
import fcntl
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import traceback

from updater import atomic_json, archive_valid, extract_archive, verify_manifest, version, host_compatible


class SimulationBusy(RuntimeError):
    pass


def require_idle_backend():
    """Also catch orphaned or manually started default-instance backends."""
    for port, kind in [(9002, socket.SOCK_DGRAM), (9003, socket.SOCK_DGRAM),
                       (14551, socket.SOCK_DGRAM), (5760, socket.SOCK_STREAM)]:
        with socket.socket(socket.AF_INET, kind) as probe:
            if kind == socket.SOCK_STREAM:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(('127.0.0.1', port))
            except OSError as error:
                raise SimulationBusy('Update postponed: stop the existing SITL/Gazebo/MAVROS session first.') from error


def environment(root, release, config):
    env = os.environ.copy()
    workspace = release/'workspace'
    runtime = release/'runtime'
    prefix = runtime/'opt/ros/humble'
    env.update(OPERATION_MX_INSTALL_ROOT=str(root), MAKO_WORKSPACE=str(workspace),
               MAKO_SOFTWARE_WORKSPACE=config.get('software') or str(workspace), MAKO_ARDUPILOT=config['ardupilot'],
               MAKO_ARDUPILOT_GAZEBO=str(Path(config['ardupilot'])/'ardupilot_gazebo'),
               MAKO_DATA_DIR=str(root/'data'), MAKO_APP_ICON=str(root/'data/icon.png'),
               MAKO_ROS_SETUP=config['ros_setup'])
    additions = {
        'AMENT_PREFIX_PATH': [prefix],
        'LD_LIBRARY_PATH': [prefix/'lib', prefix/'lib/x86_64-linux-gnu', runtime/'usr/lib/x86_64-linux-gnu', runtime/'usr/lib'],
        'PYTHONPATH': [prefix/'local/lib/python3.10/dist-packages', prefix/'lib/python3.10/site-packages'],
    }
    for key, paths in additions.items():
        old = [p for p in env.get(key, '').split(':') if p and '/operation-mx/releases/' not in p]
        env[key] = ':'.join([str(p) for p in paths]+old)
    env['MAKO_VO_PREFIX'] = str(prefix)
    return env


def shell_setup(release, config, built=True):
    paths = [Path(config['ros_setup'])]
    # realjoy_node is built in this workspace (mako_control); an extra overlay is optional.
    if config.get('software'):
        paths.append(Path(config['software'])/'install/local_setup.bash')
    if built:
        paths.append(release/'workspace/install/setup.bash')
    for path in paths:
        if not path.is_file():
            raise RuntimeError('Required ROS environment is missing: '+str(path))
    return '\n'.join('source '+shlex.quote(str(p)) for p in paths)+'\n'


def prepare(root, release, config):
    """Build in the final version directory; symlink-install paths stay valid."""
    env = environment(root, release, config)
    env.update(CCACHE_DIR=str(root/'data/ccache'), CCACHE_TEMPDIR=str(root/'data/ccache-tmp'))
    log_path = root/'data/update-setup.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('ab') as log:
        sources = shell_setup(release, config, built=False)
        command = sources+'exec colcon build --symlink-install --packages-up-to mako_bringup --cmake-args -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release\n'
        subprocess.run(['bash', '-c', command], cwd=release/'workspace', env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
        sources = shell_setup(release, config)
        checks = "from ament_index_python.packages import get_package_prefix; " \
                 "[get_package_prefix(p) for p in ['robot_description','mako_control','mako_vision','mako_bringup','rtabmap_launch','rtabmap_slam','rtabmap_viz','rtabmap_odom','mavros','joy','ros_gz_sim','ros_gz_bridge']]"
        subprocess.run(['bash', '-c', sources+'exec /usr/bin/python3 -c '+shlex.quote(checks)],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=30)
        for package, binary in [('rtabmap_slam', 'rtabmap'), ('rtabmap_viz', 'rtabmap_viz'), ('rtabmap_odom', 'rgbd_odometry')]:
            output = subprocess.check_output(['ldd', str(release/'runtime/opt/ros/humble/lib'/package/binary)], env=env, text=True)
            if 'not found' in output:
                raise RuntimeError('Missing native SLAM libraries; see '+str(log_path)+'\n'+output)
        smoke_env = dict(env, QT_QPA_PLATFORM='offscreen')
        script = release/'workspace/gui/rov_gui_gst.py'
        subprocess.run(['bash', '-c', sources+'exec /usr/bin/python3 '+shlex.quote(str(script))+' --smoke-test'],
                       env=smoke_env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=30)
    (release/'.ready').write_text('ok\n')


def activate_pending(root, prepare_release=prepare):
    pending_path = root/'pending.json'
    if not pending_path.exists():
        return False
    require_idle_backend()
    pending = json.loads(pending_path.read_text())
    manifest = verify_manifest(base64.b64decode(pending['manifest'], validate=True),
                               pending['signature'].encode(), root/'update_public_key.pem')
    state_path = root/'current.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    if state and version(manifest['version']) <= version(state['version']):
        pending_path.unlink()
        return False
    archive = Path(pending['archive'])
    if not archive_valid(archive, manifest):
        raise ValueError('Downloaded update has changed or is incomplete')
    target = root/'releases'/manifest['version']
    # Only incomplete candidates can be replaced, never the active release.
    if target.exists():
        shutil.rmtree(target)
    try:
        extract_archive(archive, target)
        metadata = json.loads((target/'release.json').read_text())
        if metadata['version'] != manifest['version']:
            raise ValueError('Archive version disagrees with signed manifest')
        config = json.loads((root/'config.json').read_text())
        prepare_release(root, target, config)
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        failed_path = root/'failed-updates.json'
        failed = json.loads(failed_path.read_text()) if failed_path.exists() else []
        atomic_json(failed_path, sorted(set(failed+[manifest['version']])))
        pending_path.unlink(missing_ok=True)
        raise
    new_state = {'version': manifest['version']}
    if state:
        new_state['previous'] = state['version']
    atomic_json(state_path, new_state)
    # After the pointer commits, cleanup must never delete the active release.
    pending_path.unlink(missing_ok=True)
    try:
        archive.unlink(missing_ok=True)
    except OSError:
        pass
    keep = {new_state['version'], new_state.get('previous')}
    for directory in (root/'releases').iterdir():
        if directory.is_dir() and directory.name not in keep:
            shutil.rmtree(directory, ignore_errors=True)
    return True


def rollback(root):
    state = json.loads((root/'current.json').read_text())
    previous = state.get('previous')
    if not previous or not (root/'releases'/previous/'.ready').exists():
        raise RuntimeError('There is no previous working version to restore')
    failed_path = root/'failed-updates.json'
    failed = json.loads(failed_path.read_text()) if failed_path.exists() else []
    atomic_json(failed_path, sorted(set(failed+[state['version']])))
    atomic_json(root/'current.json', {'version': previous, 'previous': state['version']})
    (root/'pending.json').unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rollback', action='store_true')
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if not host_compatible():
        raise RuntimeError('Operation MX currently supports Ubuntu 22.04 x86_64 / ROS Humble')
    with (root/'launch.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Operation MX is already running; close it before changing versions.', file=sys.stderr)
            return 1
        if args.rollback:
            rollback(root)
        if (root/'pending.json').exists() and os.environ.get('DISPLAY') and shutil.which('notify-send'):
            try:
                subprocess.run(['notify-send', 'Operation MX',
                                'Preparing a verified update. The application will open when setup finishes.'],
                               check=False, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        try:
            activate_pending(root)
        except SimulationBusy as error:
            print(str(error), file=sys.stderr)
        except Exception:
            (root/'pending.json').unlink(missing_ok=True)
            with (root/'data/update-setup.log').open('a') as log:
                traceback.print_exc(file=log)
            if not (root/'current.json').exists():
                raise
            print('Update failed; starting the previous working version. See data/update-setup.log.', file=sys.stderr)
        state = json.loads((root/'current.json').read_text())
        release = root/'releases'/state['version']
        config = json.loads((root/'config.json').read_text())
        env = environment(root, release, config)
        command = shell_setup(release, config)+'exec /usr/bin/python3 '+shlex.quote(str(release/'workspace/gui/rov_gui_gst.py'))
        if args.smoke_test:
            command += ' --smoke-test'
        return subprocess.call(['bash', '-c', command], env=env)


if __name__ == '__main__':
    raise SystemExit(main())
