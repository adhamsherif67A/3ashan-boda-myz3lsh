#!/usr/bin/env python3
"""Package a matching desktop, simulation and RTAB-Map runtime; sign its manifest."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'gui/mako_station'))
from updater import MANIFEST, version


def build(output, release_version, key_path, runtime, source=ROOT):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    version(release_version)
    release_version = release_version.removeprefix('v')
    key = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError('The signing key must be Ed25519')
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    if public != (source/'gui/update_public_key.pem').read_bytes():
        raise ValueError('Signing key does not match the public key shipped to users')
    runtime = Path(runtime)
    for package, binary in [('rtabmap_slam', 'rtabmap'), ('rtabmap_viz', 'rtabmap_viz'), ('rtabmap_odom', 'rgbd_odometry')]:
        if not (runtime/'opt/ros/humble/lib'/package/binary).is_file():
            raise ValueError('Complete RTAB-Map runtime required: '+package)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output/f'operation-mx-{release_version}-linux-x86_64.tar.gz'
    def include(member):
        if member.name == 'workspace/gui/mako_station/VERSION':
            return None
        if '__pycache__' in Path(member.name).parts or member.name.endswith('.pyc'):
            return None
        member.uid = member.gid = 0
        member.uname = member.gname = ''
        return member
    with tempfile.TemporaryDirectory() as temp:
        metadata = Path(temp)/'release.json'
        metadata.write_text(json.dumps({'version': release_version, 'ros_distro': 'humble'}))
        with tarfile.open(archive, 'w:gz', dereference=True) as tar:
            tar.add(metadata, arcname='release.json', filter=include)
            for package in ['robot_description', 'mako_control', 'mako_vision', 'mako_bringup', 'mako_navigation', 'robot_mapping']:
                if (source/'src'/package).is_dir():
                    tar.add(source/'src'/package, arcname='workspace/src/'+package, filter=include)
            tar.add(source/'commands.txt', arcname='workspace/commands.txt', filter=include)
            if (source/'firmware/ardusub-autotune').is_dir():
                tar.add(source/'firmware/ardusub-autotune', arcname='workspace/firmware/ardusub-autotune', filter=include)
            tar.add(source/'gui/rov_gui_gst.py', arcname='workspace/gui/rov_gui_gst.py', filter=include)
            tar.add(source/'gui/mako_station', arcname='workspace/gui/mako_station', filter=include)
            data = (release_version+'\n').encode()
            item = tarfile.TarInfo('workspace/gui/mako_station/VERSION')
            item.size = len(data)
            item.mode = 0o644
            tar.addfile(item, io.BytesIO(data))
            # Debian sysroots can contain dangling documentation links. Ship
            # runtime files individually, dereferencing valid library links.
            tar.add(runtime, arcname='runtime', recursive=False, filter=include)
            for directory, folders, files in os.walk(runtime):
                folders[:] = sorted(f for f in folders if f not in {'include', '__pycache__', 'doc', 'man'})
                relative = Path(directory).relative_to(runtime)
                for name in sorted(files):
                    path = Path(directory)/name
                    if path.is_file():
                        tar.add(path, arcname=str(Path('runtime')/relative/name), recursive=False, filter=include)
    digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    manifest = {'schema': 1, 'launcher_version': 1, 'version': release_version,
                'platform': 'ubuntu-22.04-x86_64',
                'dependencies': {'ros_distro': 'humble', 'rtabmap': 'bundled', 'simulation': 'included'},
                'archive': {'name': archive.name, 'size': archive.stat().st_size, 'sha256': digest.hexdigest()}}
    raw = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    (output/MANIFEST).write_bytes(raw)
    (output/(MANIFEST+'.sig')).write_bytes(base64.b64encode(key.sign(raw)))
    with tempfile.TemporaryDirectory() as temp:
        installer = Path(temp)/'operation-mx-installer'
        installer.mkdir()
        for name in ['launcher.py', 'install.py']:
            shutil.copy2(source/'gui/desktop'/name, installer/name)
        shutil.copy2(source/'gui/mako_station/updater.py', installer/'updater.py')
        shutil.copy2(source/'gui/update_public_key.pem', installer/'update_public_key.pem')
        shutil.copy2(source/'gui/UPDATES.md', installer/'UPDATES.md')
        for path in [archive, output/MANIFEST, output/(MANIFEST+'.sig')]:
            shutil.copy2(path, installer/path.name)
        with tarfile.open(output/f'operation-mx-installer-{release_version}.tar.gz', 'w:gz') as tar:
            tar.add(installer, arcname=installer.name, filter=include)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--output', default=ROOT/'dist/desktop', type=Path)
    parser.add_argument('--signing-key', type=Path)
    args = parser.parse_args()
    if args.signing_key:
        result = build(args.output, args.version, args.signing_key, args.runtime)
    else:
        secret = os.environ.get('OPERATION_MX_SIGNING_KEY')
        if not secret:
            parser.error('Set OPERATION_MX_SIGNING_KEY or supply --signing-key; unsigned releases are refused')
        with tempfile.TemporaryDirectory() as temp:
            key = Path(temp)/'private.pem'
            key.write_text(secret)
            key.chmod(0o600)
            result = build(args.output, args.version, key, args.runtime)
    print('Signed desktop release:', result)


if __name__ == '__main__':
    main()
