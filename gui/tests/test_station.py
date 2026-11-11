import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PyQt5.QtWidgets import QApplication
from mako_station.app import PilotWindow
from mako_station.ros_worker import RosWorker,image_to_qimage
from mako_station.simulation import commands_from_file,SimulationSession


class StationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_commands_preserve_user_sitl_model_and_mavros_endpoint(self):
        sitl,mavros=commands_from_file(Path(__file__).resolve().parents[2]/'commands.txt')
        self.assertIn('--model=JSON',sitl)
        self.assertIn('--out=udp:127.0.0.1:14551',sitl)
        self.assertIn('fcu_url:=udp://127.0.0.1:14551@',mavros)

    def test_startup_loads_motor_configuration_before_launch_without_late_writes(self):
        import tempfile,shutil,runpy
        from unittest.mock import patch
        root=Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            workspace=Path(directory)
            shutil.copy2(root/'commands.txt',workspace/'commands.txt')
            config=workspace/'src/mako_control/config/ardusub_external_nav.parm'
            config.parent.mkdir(parents=True)
            shutil.copy2(root/'src/mako_control/config/ardusub_external_nav.parm',config)
            autopilot=workspace/'autopilot'
            script=autopilot/'Tools/autotest/sim_vehicle.py'
            script.parent.mkdir(parents=True);script.touch()
            session=SimulationSession(workspace=workspace,ardupilot=autopilot)
            with patch('mako_station.simulation.source_environment',return_value={'PATH':'/usr/bin'}), \
                 patch('mako_station.simulation.socket.socket'), \
                 patch('mako_station.simulation.subprocess.run'), \
                 patch('mako_station.simulation.time.sleep'), \
                 patch.object(session.processes,'spawn') as spawn:
                session.start()
                commands={call.args[0]:call.args[1] for call in spawn.call_args_list}
                sitl=commands['SITL']
                self.assertEqual(sitl[sitl.index('--add-param-file')+1],str(config))
                self.assertNotIn('--no-rebuild',sitl)
                self.assertIn('configure_ardusub:=false',commands['Gazebo'])
                self.assertEqual(commands['Gazebo'][:4],['ros2','launch','mako_bringup','simulation.launch.py'])
                self.assertEqual(commands['Pilot control'],['ros2','run','mako_control','realjoy_node'])
                session.stop()
            values={line.split()[0]:float(line.split()[1]) for line in config.read_text().splitlines()
                    if line.strip() and not line.startswith('#')}
            params=runpy.run_path(str(root/'src/mako_control/scripts/fix_ardusub_params.py'))['PARAMS']
            for key,(value,_) in params.items():self.assertEqual(values[key],value,key)
            self.assertLess(values['MOT_PWM_MIN'],1500)
            self.assertGreater(values['MOT_PWM_MAX'],1500)

    def test_validated_tracking_freshness_is_independent_of_ground_truth(self):
        from unittest.mock import patch
        worker=RosWorker()
        with patch('mako_station.ros_worker.time.monotonic',return_value=123.):
            worker.validated_odometry(None)
        self.assertEqual(worker.snapshot()[1]['tracking_time'],123.)
        self.assertNotIn('nav_time',worker.snapshot()[1])
        worker.clear_session()
        self.assertNotIn('tracking_time',worker.snapshot()[1])

    def test_rgb_with_row_padding_and_incomplete_frame(self):
        msg=SimpleNamespace(width=1,height=2,step=4,encoding='rgb8',data=bytes([255,0,0,0,0,255,0,0]))
        image=image_to_qimage(msg)
        self.assertEqual(image.pixelColor(0,0).red(),255)
        self.assertEqual(image.pixelColor(0,1).green(),255)
        msg.data=b'\0'
        with self.assertRaises(ValueError):image_to_qimage(msg)

    def test_video_switch_rejects_old_callbacks_and_keeps_bottom(self):
        worker=RosWorker()
        msg=SimpleNamespace(width=1,height=1,step=3,encoding='rgb8',data=bytes([255,0,0]))
        worker.frame(msg,'main','First person');worker.frame(msg,'bottom')
        worker.set_view('Third person')
        worker.frame(msg,'main','First person')
        self.assertNotIn('main',worker.snapshot()[0])
        self.assertIn('bottom',worker.snapshot()[0])
        for _ in range(100):worker.frame(msg,'main','Third person')
        self.assertEqual(set(worker.snapshot()[0]),{'main','bottom'})

    def test_lifecycle_buttons_and_no_offline_arming(self):
        window=PilotWindow(start_workers=False)
        self.assertTrue(window.start_button.isEnabled())
        self.assertFalse(window.reset_button.isEnabled())
        self.assertFalse(window.arm_button.isEnabled())
        window.on_phase('Starting')
        self.assertFalse(window.start_button.isEnabled())
        self.assertFalse(window.world.isEnabled())
        window.on_phase('Running');window.tick()
        self.assertTrue(window.reset_button.isEnabled())
        self.assertFalse(window.arm_button.isEnabled())
        window.close()


if __name__=='__main__':unittest.main()
