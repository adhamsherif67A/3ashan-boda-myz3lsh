#!/usr/bin/env python3
"""One-time per-user installer for a signed Operation MX release."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from updater import MANIFEST, atomic_json, queue_update, host_compatible, verify_manifest, version
from launcher import activate_pending, require_idle_backend


def desktop_quote(value):
    return '"'+str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')+'"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))/'operation-mx')
    parser.add_argument('--software-workspace', type=Path, default=Path(os.environ.get('MAKO_SOFTWARE_WORKSPACE', Path.home()/'Software2026')))
    parser.add_argument('--ardupilot', type=Path, default=Path(os.environ.get('MAKO_ARDUPILOT', Path.home()/'ardupilot')))
    parser.add_argument('--ros-setup', type=Path, default=Path('/opt/ros/humble/setup.bash'))
    parser.add_argument('--upgrade', action='store_true', help='Upgrade an existing installation, preserving data and local paths')
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if args.upgrade and (root/'config.json').is_file():
        previous = json.loads((root/'config.json').read_text())
        for flag, attribute, key in [('--software-workspace', 'software_workspace', 'software'),
                                     ('--ardupilot', 'ardupilot', 'ardupilot'), ('--ros-setup', 'ros_setup', 'ros_setup')]:
            if not any(item == flag or item.startswith(flag+'=') for item in sys.argv):
                setattr(args, attribute, Path(previous[key]))
    if not host_compatible():
        parser.error('Supported platform: Ubuntu 22.04 x86_64 with ROS Humble and Gazebo Harmonic')
    for path in [args.ros_setup, args.software_workspace/'install/local_setup.bash', args.ardupilot/'Tools/autotest/sim_vehicle.py']:
        if not path.is_file():
            parser.error('Missing prerequisite: '+str(path)+'; see UPDATES.md')
    source = Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    (root/'data').mkdir(exist_ok=True)
    with (root/'launch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        existing = (root/'current.json').exists()
        if existing and not args.upgrade:
            parser.error('Already installed. Use --upgrade for the one-time private-update migration.')
        raw = (source/MANIFEST).read_bytes()
        signature = (source/(MANIFEST+'.sig')).read_bytes()
        if existing and (root/'update_public_key.pem').read_bytes() != (source/'update_public_key.pem').read_bytes():
            parser.error('Installer signing key differs from the existing trusted key')
        manifest = verify_manifest(raw, signature, root/'update_public_key.pem' if existing else source/'update_public_key.pem')
        if existing and version(manifest['version']) <= version(json.loads((root/'current.json').read_text())['version']):
            parser.error('Installer must be newer than the installed version')
        require_idle_backend()
        for name in ['launcher.py', 'updater.py', 'update_public_key.pem']:
            shutil.copy2(source/name, root/name)
        atomic_json(root/'config.json', {'software': str(args.software_workspace.expanduser().resolve()),
                                         'ardupilot': str(args.ardupilot.expanduser().resolve()),
                                         'ros_setup': str(args.ros_setup.resolve())})
        archive = source/json.loads(raw)['archive']['name']
        # Copy the installer archive: activation may delete its cache copy.
        cache = root/'cache'
        cache.mkdir(exist_ok=True)
        shutil.copy2(archive, cache/archive.name)
        queue_update(root, raw, signature, cache/archive.name)
        print('Preparing Operation MX. Build/startup log: '+str(root/'data/update-setup.log'), flush=True)
        activate_pending(root)
        state = json.loads((root/'current.json').read_text())
        release = root/'releases'/state['version']
        icon = root/'data/icon.png'
        old_desktop = Path.home()/'Desktop/OperationMX.desktop'
        previous_icon = None
        if old_desktop.exists():
            for line in old_desktop.read_text().splitlines():
                if line.startswith('Icon='):
                    candidate = Path(line[5:])
                    if candidate.is_file() and candidate.suffix.lower() == '.png':
                        previous_icon = candidate
        if not icon.exists():
            shutil.copy2(previous_icon or release/'workspace/gui/mako_station/assets/operation_mx_icon.png', icon)
        binary = root/'bin/operation-mx'
        binary.parent.mkdir(exist_ok=True)
        binary.write_text('#!/bin/sh\nexec /usr/bin/python3 '+__import__('shlex').quote(str(root/'launcher.py'))+' "$@"\n')
        binary.chmod(0o755)
        entry = ('[Desktop Entry]\nType=Application\nName=Operation MX\nComment=MarineXperts ROV simulation\n'
                 'Exec='+desktop_quote(binary)+'\nIcon='+str(icon)+'\nTerminal=false\nCategories=Science;Engineering;\nStartupNotify=true\n')
        applications = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))/'applications'
        applications.mkdir(parents=True, exist_ok=True)
        for target in [applications/'operation-mx.desktop', old_desktop]:
            if target.parent.exists():
                target.write_text(entry)
                target.chmod(0o755)
        # Keep the existing team's launcher as an entry point to the managed app.
        legacy = args.software_workspace/'run_mako_gui.sh'
        if legacy.exists():
            backup = legacy.with_name('run_mako_gui.before-online-updates.sh')
            if not backup.exists():
                shutil.copy2(legacy, backup)
            legacy.write_text(binary.read_text())
            legacy.chmod(0o755)
        old_entry = args.software_workspace/'OperationMX.desktop'
        if old_entry.exists():
            old_entry.write_text(entry)
            old_entry.chmod(0o755)
        if shutil.which('update-desktop-database'):
            subprocess.run(['update-desktop-database', str(applications)], check=False)
        if shutil.which('gio') and old_desktop.exists():
            subprocess.run(['gio', 'set', str(old_desktop), 'metadata::trusted', 'true'], check=False)
    print('Operation MX installed. Open it from your desktop. Data and updates:', root)


if __name__ == '__main__':
    main()
