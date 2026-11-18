"""Keep update activity out of running pilot sessions; tolerate offline checks."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PyQt5.QtWidgets import QApplication
from mako_station.app import PilotWindow


class UpdateUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        context = patch.dict(os.environ, {'OPERATION_MX_INSTALL_ROOT': self.temp.name})
        context.start()
        self.addCleanup(context.stop)
        self.window = PilotWindow(start_workers=False)
        self.addCleanup(self.window.close)

    def test_running_or_starting_simulation_blocks_update_checks(self):
        for phase in ('Starting', 'Running', 'Resetting', 'Stopping'):
            self.window.phase = phase
            with patch('mako_station.update_ui.threading.Thread') as worker:
                self.window.updates.check(manual=True)
                worker.assert_not_called()
        self.assertIn('simulation is stopped', self.window.log_box.toPlainText())

    def test_ready_update_only_requests_a_future_restart(self):
        (Path(self.temp.name)/'pending.json').write_text('{}')
        with patch('mako_station.update_ui.threading.Thread') as worker:
            self.window.updates.check(manual=True)
            worker.assert_not_called()
        self.assertEqual(self.window.updates.button.text(), 'Update on next launch')
        self.assertEqual(self.window.phase, 'Stopped')

    def test_offline_checks_keep_pilot_controls_usable(self):
        with patch('mako_station.update_ui.latest', side_effect=OSError('offline')):
            self.window.updates.work(manual=True)
        self.assertTrue(self.window.start_button.isEnabled())
        self.assertTrue(self.window.updates.button.isEnabled())
        self.assertIn('keeping the installed version', self.window.log_box.toPlainText())
        self.assertFalse((Path(self.temp.name)/'pending.json').exists())
