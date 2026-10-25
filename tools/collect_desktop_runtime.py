#!/usr/bin/env python3
"""Collect installed RTAB-Map packages and their native library closure for releases.

Run inside the Ubuntu 22.04 ROS build container, after apt installs RTAB-Map.
Host GPU drivers and the C/C++ runtime remain platform prerequisites.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists():
        parser.error('Destination must be a new directory')
    packages = subprocess.check_output(['dpkg-query', '-W', '-f=${binary:Package}\n', 'ros-humble-rtabmap*'], text=True).splitlines()
    packages += ['ros-humble-apriltag-msgs', 'ros-humble-aruco-msgs', 'ros-humble-aruco-opencv-msgs', 'ros-humble-nav2-msgs']
    files = set()
    for package in packages:
        for line in subprocess.check_output(['dpkg-query', '-L', package], text=True).splitlines():
            path = Path(line)
            if path.is_file() and not path.name.endswith(('.a', '.h', '.hpp', '.pyc')):
                files.add(path)
    libraries = set()
    for path in files:
        try:
            with path.open('rb') as stream:
                elf = stream.read(4) == b'\x7fELF'
            if not elf:
                continue
            result = subprocess.run(['ldd', str(path)], capture_output=True, text=True)
            if 'not found' in result.stdout:
                raise RuntimeError(result.stdout)
            for match in re.finditer(r'=> (/\S+)', result.stdout):
                library = Path(match.group(1))
                if re.match(r'(lib(c|m|dl|pthread|rt|util|resolv|gcc_s|stdc\+\+)\.so|lib(GL|EGL|GLX|GLdispatch)\.so)', library.name):
                    continue
                # /lib is often merged into /usr/lib; store libraries in the
                # runtime's searched directory while keeping their SONAME.
                libraries.add(library)
        except OSError as error:
            raise RuntimeError('Cannot collect '+str(path)) from error
    for path in sorted(files):
        target = destination/str(path).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target, follow_symlinks=True)
    for path in sorted(libraries):
        if str(path).startswith('/opt/ros/humble/'):
            target = destination/str(path).lstrip('/')
        else:
            target = destination/'usr/lib/x86_64-linux-gnu'/path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(path, target, follow_symlinks=True)
    print('Collected runtime:', destination)


if __name__ == '__main__':
    main()
