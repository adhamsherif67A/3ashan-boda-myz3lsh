"""Check runtime creation without starting Docker or touching a live container."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class RuntimeSetupTests(unittest.TestCase):
    def invoke(self, *, existing=False, image=True, other_workspace=False):
        source = Path(__file__).resolve().parents[1] / 'tools/setup_container.py'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / 'tools/setup_container.py'
            script.parent.mkdir()
            shutil.copy2(source, script)
            calls = []

            def run(arguments, **kwargs):
                calls.append(arguments)
                status = 0
                if arguments[:2] == ['docker', 'inspect']:
                    status = 0 if existing else 1
                if arguments[:3] == ['docker', 'image', 'inspect']:
                    status = 0 if image else 1
                return subprocess.CompletedProcess(arguments, status)

            mount = '/another/workspace' if other_workspace else str(root)
            inspect = json.dumps([{'Mounts': [{'Destination': '/opt/mako_ws', 'Source': mount}]}]).encode()
            with patch.object(sys, 'argv', [str(script), '--build']), \
                 patch.dict('os.environ', {'FISH_CONTAINER_NAME': 'fish-team-test',
                                          'FISH_RUNTIME_IMAGE': 'fish-test:local'}), \
                 patch('subprocess.run', side_effect=run), \
                 patch('subprocess.check_output', return_value=inspect):
                try:
                    runpy.run_path(str(script))
                except SystemExit as error:
                    return calls, str(error)
            return calls, None

    def test_creates_independent_runtime_and_builds_workspace(self):
        calls, error = self.invoke()
        self.assertIsNone(error)
        create = next(call for call in calls if call[:2] == ['docker', 'run'])
        self.assertIn('fish-team-test', create)
        self.assertEqual(create[-2:], ['fish-test:local', 'infinity'])
        self.assertIn('c 13:* rmw', create)
        self.assertTrue(any('target=/opt/mako_ws' in item for item in create))
        self.assertTrue(any('calibrate_allocation.py' in item and 'colcon build' in item
                            and 'build_fish_firmware.py' in item for call in calls for item in call))

    def test_missing_image_explains_build_without_creating_container(self):
        calls, error = self.invoke(image=False)
        self.assertIn('Build the image first', error)
        self.assertFalse(any(call[:2] == ['docker', 'run'] for call in calls))

    def test_never_reuses_container_mounted_from_another_workspace(self):
        calls, error = self.invoke(existing=True, other_workspace=True)
        self.assertIn('another workspace', error)
        self.assertFalse(any(call[:2] in (['docker', 'start'], ['docker', 'exec']) for call in calls))


if __name__ == '__main__':
    unittest.main()
