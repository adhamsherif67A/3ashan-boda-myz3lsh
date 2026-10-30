"""Launcher control-flow checks; no GPU, controller or Docker daemon needed."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

spec=importlib.util.spec_from_file_location('launcher',Path(__file__).resolve().parents[1]/'launch_all.py')
launcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def session(self):
        return launcher.Session(SimpleNamespace(repo=Path('/repo'),world='pool.world',qgroundcontrol=None,no_mapping=True))

    def test_failed_preflight_does_not_stop_existing_container(self):
        session=self.session()
        def fake_run(command, **_):
            if command[1]=='info': return subprocess.CompletedProcess(command,0,'{"nvidia":{}}')
            if command[1:3]==['container','inspect']: return subprocess.CompletedProcess(command,0,'existing')
            raise AssertionError(command)
        with patch.object(launcher,'resolve_qgc',return_value=Path('/qgc')), \
             patch.object(launcher.shutil,'which',return_value='/bin/fake'), \
             patch.object(launcher.Path,'is_file',return_value=True), \
             patch.object(launcher.Path,'exists',return_value=True), \
             patch.dict(launcher.os.environ,{'DISPLAY':':1'}), \
             patch.object(launcher,'run',side_effect=fake_run) as run:
            session.env['DISPLAY']=':1'
            with self.assertRaisesRegex(RuntimeError,'already exists'):
                session.preflight()
            session.cleanup()
            self.assertFalse(any('stop' in call.args[0] for call in run.call_args_list))

    def test_failed_build_does_not_start_motion_or_guis(self):
        session=self.session(); session.qgc=Path('/qgc')
        build=Mock();build.poll.return_value=1;build.returncode=1
        with patch.object(session,'start',side_effect=[Mock(),build]) as start, \
             patch.object(session,'wait_container'),patch.object(session,'wait_mavros'):
            with self.assertRaisesRegex(RuntimeError,'build/tests failed'):
                session.launch()
            self.assertEqual([c.args[0] for c in start.call_args_list],['gazebo','build'])

    def test_cleanup_uses_owned_id_not_container_name(self):
        session=self.session();session.container_id='owned-123'
        session.processes=[('motion',Mock()),('gazebo',Mock())]
        reply=subprocess.CompletedProcess([],0,'success: true')
        with patch.object(launcher,'run',return_value=reply) as run,patch.object(session,'stop_process'):
            session.cleanup()
            stop=[c.args[0] for c in run.call_args_list if c.args[0][1]=='stop']
            self.assertEqual(stop,[['docker','stop','--time','15','owned-123']])

    def test_missing_explicit_qgc_reports_error(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(launcher,'PACKAGE',Path(folder)):
            with self.assertRaisesRegex(RuntimeError,'missing or not executable'):
                launcher.resolve_qgc('/nonexistent/QGroundControl.AppImage')

    def test_mapping_shutdown_flushes_before_container_removal(self):
        session=self.session();session.mapping_enabled=True;session.container_id='owned-mapping'
        simulator=Mock();session.processes=[('gazebo',simulator)]
        reply=subprocess.CompletedProcess([],0,'success: true')
        with patch.object(launcher,'run',return_value=reply) as run,patch.object(session,'stop_process'):
            session.cleanup()
            simulator.wait.assert_called_once_with(timeout=180)
            commands=[c.args[0] for c in run.call_args_list]
            self.assertIn(['docker','kill','--signal=SIGINT','owned-mapping'],commands)
            self.assertFalse(any(c[1]=='stop' for c in commands))


if __name__=='__main__': unittest.main()
