"""Release authenticity, extraction, activation and rollback regressions."""
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import socket
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'gui/mako_station'))
sys.path.insert(0, str(ROOT/'gui/desktop'))
import updater
import launcher


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = Ed25519PrivateKey.generate()
        self.public = self.root/'update_public_key.pem'
        self.public.write_bytes(self.key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        idle = patch('launcher.require_idle_backend')
        idle.start()
        self.addCleanup(idle.stop)

    def release(self, number='1.1.0', members=None):
        archive = self.root/f'operation-mx-{number}-linux-x86_64.tar.gz'
        if members is None:
            members = [('release.json', json.dumps({'version': number}).encode()),
                       ('workspace/gui/mako_station/VERSION', number.encode())]
        with tarfile.open(archive, 'w:gz') as tar:
            for name, data in members:
                item = tarfile.TarInfo(name)
                item.size = len(data)
                tar.addfile(item, io.BytesIO(data))
        manifest = {'schema': 1, 'launcher_version': 1, 'version': number,
                    'platform': 'ubuntu-22.04-x86_64',
                    'archive': {'name': archive.name, 'size': archive.stat().st_size,
                                'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}}
        raw = json.dumps(manifest).encode()
        signature = base64.b64encode(self.key.sign(raw))
        return archive, raw, signature, manifest

    def installed(self, number='1.0.0'):
        release = self.root/'releases'/number
        release.mkdir(parents=True)
        (release/'.ready').write_text('ok')
        updater.atomic_json(self.root/'current.json', {'version': number})
        updater.atomic_json(self.root/'config.json', {})
        data = self.root/'data'
        data.mkdir()
        (data/'rtabmap.db').write_bytes(b'keep this map')
        return release

    def test_signature_and_checksum(self):
        archive, raw, sig, manifest = self.release()
        self.assertEqual(updater.verify_manifest(raw, sig, self.public), manifest)
        self.assertTrue(updater.archive_valid(archive, manifest))
        with self.assertRaises(Exception):
            updater.verify_manifest(raw.replace(b'1.1.0', b'9.9.9'), sig, self.public)
        archive.write_bytes(b'corrupt')
        self.assertFalse(updater.archive_valid(archive, manifest))
        with self.assertRaises(ValueError):
            updater.queue_update(self.root, raw, sig, archive)
        self.assertFalse((self.root/'pending.json').exists())

    def test_another_signing_key_is_rejected(self):
        _, raw, _, _ = self.release()
        signature = base64.b64encode(Ed25519PrivateKey.generate().sign(raw))
        with self.assertRaises(Exception):
            updater.verify_manifest(raw, signature, self.public)

    def test_private_update_installer_upgrades_and_preserves_local_paths(self):
        import shutil
        self.installed()
        software, autopilot, ros = self.root/'custom-software', self.root/'custom-ardupilot', self.root/'custom-ros.bash'
        (software/'install').mkdir(parents=True)
        (software/'install/local_setup.bash').touch()
        (autopilot/'Tools/autotest').mkdir(parents=True)
        (autopilot/'Tools/autotest/sim_vehicle.py').touch()
        ros.touch()
        config = {'software':str(software), 'ardupilot':str(autopilot), 'ros_setup':str(ros)}
        updater.atomic_json(self.root/'config.json', config)
        icon = self.root/'data/icon.png'; icon.write_bytes(b'preserve-icon')
        archive, raw, sig, _ = self.release()
        bundle = self.root/'installer'; bundle.mkdir()
        for path in [archive, self.public]: shutil.copy2(path, bundle/path.name)
        for name in ['launcher.py', 'updater.py']: (bundle/name).write_text('# verified bootstrap fixture\n')
        (bundle/updater.MANIFEST).write_bytes(raw)
        (bundle/(updater.MANIFEST+'.sig')).write_bytes(sig)
        spec = importlib.util.spec_from_file_location('mx_installer_test', ROOT/'gui/desktop/install.py')
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        installer.__file__ = str(bundle/'install.py')
        def activate(root):
            return launcher.activate_pending(root, prepare_release=lambda root, release, config: (release/'.ready').write_text('ok'))
        with patch.object(sys, 'argv', ['install.py', '--root', str(self.root), '--upgrade']), \
             patch('pathlib.Path.home', return_value=self.root/'fake-home'), \
             patch.object(installer, 'host_compatible', return_value=True), \
             patch.object(installer, 'require_idle_backend'), \
             patch.object(installer, 'activate_pending', side_effect=activate), \
             patch('shutil.which', return_value=None):
            installer.main()
        self.assertEqual(json.loads((self.root/'config.json').read_text()), config)
        self.assertEqual(json.loads((self.root/'current.json').read_text()), {'version':'1.1.0','previous':'1.0.0'})
        self.assertEqual(icon.read_bytes(), b'preserve-icon')
        self.assertEqual((self.root/'data/rtabmap.db').read_bytes(), b'keep this map')

    def test_versions_compare_numerically_and_reject_prereleases(self):
        self.assertGreater(updater.version('1.10.0'), updater.version('v1.9.9'))
        for value in ['main', '1.0', '1.0.0-rc1', '../1.0.0', '01.0.0']:
            with self.assertRaises(ValueError):
                updater.version(value)

    def test_latest_requires_matching_signed_tag_and_assets(self):
        _, raw, sig, manifest = self.release()
        prefix = 'https://github.com/team/repo/releases/download/v1.1.0/'
        names = [updater.MANIFEST, updater.MANIFEST+'.sig', manifest['archive']['name']]
        release = {'tag_name': 'v1.1.0', 'assets': [{'name': n, 'browser_download_url': prefix+n} for n in names]}
        responses = {prefix+updater.MANIFEST: raw, prefix+updater.MANIFEST+'.sig': sig}
        def get(url, limit):
            return json.dumps(release).encode() if url.startswith('https://api.github.com/') else responses[url]
        self.assertEqual(updater.latest(self.public, '1.0.0', get)[0], manifest)
        self.assertIsNone(updater.latest(self.public, '1.1.0', get))
        release['tag_name'] = 'v2.0.0'
        with self.assertRaises(ValueError):
            updater.latest(self.public, '1.0.0', get)
        release['assets'] = []
        self.assertIsNone(updater.latest(self.public, '1.0.0', get))

    def test_transport_requires_https_and_github(self):
        for url in ['http://github.com/file', 'https://example.com/file', 'file:///etc/passwd']:
            with self.assertRaises(ValueError):
                updater.fetch(url)

    def test_partial_or_oversized_download_is_not_installed(self):
        _, _, _, manifest = self.release()
        class Response(io.BytesIO):
            url = 'https://release-assets.githubusercontent.com/file'
        target = self.root/'cache/download.tar.gz'
        with patch('updater.open_github', return_value=Response(b'not the signed archive')):
            with self.assertRaises(ValueError):
                updater.download('https://github.com/team/repo/file', target, manifest)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_suffix('.part').exists())

    def test_traversal_and_duplicate_members_rejected(self):
        for names in [[('../escape', b'x')], [('/absolute', b'x')],
                      [('workspace/same', b'a'), ('workspace/same', b'b')]]:
            archive, _, _, _ = self.release(members=names)
            destination = self.root/'candidate'
            with self.assertRaises(ValueError):
                updater.extract_archive(archive, destination)
            self.assertFalse(destination.exists())
        self.assertFalse((self.root.parent/'escape').exists())

    def test_links_are_rejected(self):
        archive = self.root/'link.tar.gz'
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            with tarfile.open(archive, 'w:gz') as tar:
                item = tarfile.TarInfo('workspace/link')
                item.type = kind
                item.linkname = '../../escape'
                tar.addfile(item)
            with self.assertRaises(ValueError):
                updater.extract_archive(archive, self.root/'candidate')

    def test_successful_activation_preserves_previous_version_and_data(self):
        old = self.installed()
        archive, raw, sig, _ = self.release()
        updater.queue_update(self.root, raw, sig, archive)
        def prepare(root, candidate, config):
            self.assertEqual(json.loads((root/'current.json').read_text())['version'], '1.0.0')
            (candidate/'.ready').write_text('ok')
        self.assertTrue(launcher.activate_pending(self.root, prepare))
        self.assertEqual(json.loads((self.root/'current.json').read_text()), {'version': '1.1.0', 'previous': '1.0.0'})
        self.assertTrue(old.exists())
        self.assertEqual((self.root/'data/rtabmap.db').read_bytes(), b'keep this map')
        self.assertFalse((self.root/'pending.json').exists())
        launcher.rollback(self.root)
        self.assertEqual(json.loads((self.root/'current.json').read_text())['version'], '1.0.0')
        self.assertIn('1.1.0', json.loads((self.root/'failed-updates.json').read_text()))

    def test_failed_setup_does_not_change_active_release(self):
        old = self.installed()
        archive, raw, sig, _ = self.release()
        updater.queue_update(self.root, raw, sig, archive)
        def fail(*args):
            raise RuntimeError('Dependency unavailable')
        with self.assertRaises(RuntimeError):
            launcher.activate_pending(self.root, fail)
        self.assertEqual(json.loads((self.root/'current.json').read_text())['version'], '1.0.0')
        self.assertTrue(old.exists())
        self.assertFalse((self.root/'releases/1.1.0').exists())
        self.assertIn('1.1.0', json.loads((self.root/'failed-updates.json').read_text()))
        self.assertTrue((self.root/'data/rtabmap.db').exists())

    def test_queued_archive_is_reverified_before_activation(self):
        self.installed()
        archive, raw, sig, _ = self.release()
        updater.queue_update(self.root, raw, sig, archive)
        archive.write_bytes(b'changed after download')
        with self.assertRaises(ValueError):
            launcher.activate_pending(self.root, lambda *args: self.fail('must not run'))

    def test_lower_version_cannot_replace_installed_version(self):
        self.installed('2.0.0')
        archive, raw, sig, _ = self.release('1.0.0')
        updater.queue_update(self.root, raw, sig, archive)
        self.assertFalse(launcher.activate_pending(self.root, lambda *args: self.fail('must not run')))
        self.assertEqual(json.loads((self.root/'current.json').read_text())['version'], '2.0.0')

    def test_busy_backend_keeps_update_queued_without_activation(self):
        self.installed()
        archive, raw, sig, _ = self.release()
        updater.queue_update(self.root, raw, sig, archive)
        with patch('launcher.require_idle_backend', side_effect=launcher.SimulationBusy('busy')):
            with self.assertRaises(launcher.SimulationBusy):
                launcher.activate_pending(self.root, lambda *args: self.fail('must not build'))
        self.assertTrue((self.root/'pending.json').exists())
        self.assertEqual(json.loads((self.root/'current.json').read_text())['version'], '1.0.0')

    def test_packaging_uses_release_tag_not_development_version(self):
        spec = importlib.util.spec_from_file_location('desktop_builder', ROOT/'tools/build_desktop_release.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        source = self.root/'source'
        for folder in ['gui/mako_station', 'gui/desktop', 'src/robot_description']:
            (source/folder).mkdir(parents=True)
        for file in ['commands.txt', 'gui/rov_gui_gst.py', 'gui/UPDATES.md', 'gui/mako_station/updater.py', 'gui/desktop/install.py', 'gui/desktop/launcher.py']:
            (source/file).write_text('fixture')
        (source/'gui/mako_station/VERSION').write_text('0.0.1')
        (source/'gui/update_public_key.pem').write_bytes(self.public.read_bytes())
        key = self.root/'private.pem'
        key.write_bytes(self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        runtime = self.root/'runtime'
        for package, binary in [('rtabmap_slam', 'rtabmap'), ('rtabmap_viz', 'rtabmap_viz'), ('rtabmap_odom', 'rgbd_odometry')]:
            path = runtime/'opt/ros/humble/lib'/package/binary
            path.parent.mkdir(parents=True)
            path.write_text('fixture')
        result = builder.build(self.root/'dist', 'v1.2.3', key, runtime, source)
        with tarfile.open(result) as tar:
            self.assertEqual(tar.extractfile('workspace/gui/mako_station/VERSION').read().strip(), b'1.2.3')
            self.assertEqual(len(tar.getnames()), len(set(tar.getnames())))
        updater.verify_manifest((result.parent/updater.MANIFEST).read_bytes(),
                                (result.parent/(updater.MANIFEST+'.sig')).read_bytes(), self.public)


if __name__ == '__main__':
    unittest.main()
