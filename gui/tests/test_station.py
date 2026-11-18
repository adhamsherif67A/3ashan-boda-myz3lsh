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
            with patch.dict(os.environ,{'MAKO_PERFORMANCE_PROFILE':'maximum_fps','MAKO_PILOT_FPS':'30','MAKO_CAMERA_FPS':'30','MAKO_PILOT_WIDTH':'1280','MAKO_PILOT_HEIGHT':'720'}), \
                 patch('mako_station.simulation.source_environment',return_value={'PATH':'/usr/bin'}), \
                 patch('mako_station.simulation.socket.socket'), \
                 patch('mako_station.simulation.subprocess.run'), \
                 patch('mako_station.simulation.time.sleep'), \
                 patch.object(session.processes,'spawn') as spawn:
                session.start()
                commands={call.args[0]:call.args[1] for call in spawn.call_args_list}
                sitl=commands['SITL']
                self.assertEqual(sitl[sitl.index('--add-param-file')+1],str(config))
                self.assertIn('--no-rebuild',sitl)  # preserve the CAD-calibrated SITL binary
                self.assertIn('configure_ardusub:=false',commands['Gazebo'])
                self.assertIn('performance_profile:=maximum_fps',commands['Gazebo'])
                self.assertIn('pilot_fps:=30',commands['Gazebo'])
                self.assertIn('camera_fps:=30',commands['Gazebo'])
                self.assertIn('pilot_width:=1280',commands['Gazebo'])
                self.assertIn('pilot_height:=720',commands['Gazebo'])
                self.assertEqual(commands['Gazebo'][:4],['ros2','launch','mako_bringup','simulation.launch.py'])
                self.assertEqual(commands['Pilot control'],['ros2','run','mako_control','realjoy_node'])
                session.stop()
            values={line.split()[0]:float(line.split()[1]) for line in config.read_text().splitlines()
                    if line.strip() and not line.startswith('#')}
            params=runpy.run_path(str(root/'src/mako_control/scripts/fix_ardusub_params.py'))['PARAMS']
            for key,(value,_) in params.items():self.assertEqual(values[key],value,key)
            self.assertLess(values['MOT_PWM_MIN'],1500)
            self.assertGreater(values['MOT_PWM_MAX'],1500)

    def test_hd_pilot_does_not_change_tracking_depth_resolution(self):
        import xacro,xml.etree.ElementTree as ET
        root=Path(__file__).resolve().parents[2]
        document=xacro.process_file(str(root/'src/robot_description/urdf/robot_description.urdf'),
            mappings={'camera_width':'640','camera_height':'360','pilot_width':'1280','pilot_height':'720'})
        sensors={item.get('name'):item for item in ET.fromstring(document.toxml()).findall('.//sensor')}
        def dimensions(name):
            image=sensors[name].find('camera/image')
            return int(image.findtext('width')),int(image.findtext('height'))
        self.assertEqual(dimensions('zed2i_left_pilot'),(1280,720))
        self.assertEqual(dimensions('zed2i_left_rgbd'),(640,360))
        self.assertEqual(dimensions('third_person_rgb_camera'),(1280,720))
        self.assertEqual(dimensions('bottom_rgb_camera'),(640,360))

    def test_validated_tracking_freshness_is_independent_of_ground_truth(self):
        from unittest.mock import patch
        worker=RosWorker()
        with patch('mako_station.ros_worker.time.monotonic',return_value=123.):
            worker.validated_odometry(None)
        self.assertEqual(worker.snapshot()[1]['tracking_time'],123.)
        self.assertNotIn('nav_time',worker.snapshot()[1])
        worker.clear_session()
        self.assertNotIn('tracking_time',worker.snapshot()[1])

    def test_tracker_cannot_report_a_dead_mapper_as_active(self):
        import time
        window=PilotWindow(start_workers=False)
        window.phase='Running';window.running_settings=('pool.world','vision',True)
        window.ros.telemetry={'tracking_time':time.monotonic()}
        window.tick()
        self.assertIn('Waiting for SLAM',window.session_hint.text())
        window.ros.mapping_info(None);window.tick()
        self.assertIn('SLAM mapping active',window.session_hint.text())
        window.ros.telemetry['mapping_time']=time.monotonic()-5
        window.tick()
        self.assertIn('mapping stopped',window.session_hint.text())
        window.close()

    def test_disk_guard_pauses_own_mapper_and_resumes_only_after_space_recovers(self):
        from unittest.mock import Mock,patch
        from concurrent.futures import Future
        worker=RosWorker();worker.telemetry={'mapping_time':100.}
        pause,resume=Mock(),Mock()
        for client in (pause,resume):
            future=Future();future.set_result(object())
            client.call_async.return_value=future
        with patch('mako_station.ros_worker.shutil.disk_usage',return_value=SimpleNamespace(free=200*1024**2)):
            worker.protect_mapping_storage(pause,resume,100.)
        pause.call_async.assert_called_once()
        self.assertTrue(worker.snapshot()[1]['mapping_storage_paused'])
        with patch('mako_station.ros_worker.shutil.disk_usage',return_value=SimpleNamespace(free=700*1024**2)):
            worker.protect_mapping_storage(pause,resume,103.)
        resume.call_async.assert_not_called()
        with patch('mako_station.ros_worker.shutil.disk_usage',return_value=SimpleNamespace(free=2*1024**3)):
            worker.protect_mapping_storage(pause,resume,106.)
        resume.call_async.assert_called_once()
        self.assertFalse(worker.snapshot()[1]['mapping_storage_paused'])
        # No new mapping messages: do not pause an unrelated/stopped mapper.
        with patch('mako_station.ros_worker.shutil.disk_usage',return_value=SimpleNamespace(free=200*1024**2)):
            worker.protect_mapping_storage(pause,resume,110.)
        pause.call_async.assert_called_once()

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

    def test_compact_window_keeps_world_and_slam_controls_clickable(self):
        from PyQt5.QtTest import QTest
        from PyQt5.QtCore import Qt
        window=PilotWindow(start_workers=False)
        window.resize(1280,800);window.show();self.app.processEvents()
        self.assertGreaterEqual(window.world.height(),40)
        self.assertGreaterEqual(window.slam.height(),26)
        window.running_settings=('pool.world','vision',False)
        window.on_phase('Running')
        window.world.setCurrentIndex(window.world.findData('ocean.world'))
        QTest.mouseClick(window.slam,Qt.LeftButton)
        self.assertTrue(window.slam.isChecked())
        self.assertEqual(window.reset_button.text(),'Apply & restart')
        self.assertFalse(window.odometry.isEnabled())
        from unittest.mock import Mock
        window.manager.request=Mock()
        window.action('reset')
        window.manager.request.assert_called_once_with('reset','ocean.world','vision',True)
        window.close()

    def test_rviz_uses_active_slam_settings_and_a_portable_map_layout(self):
        from unittest.mock import Mock
        import yaml
        window=PilotWindow(start_workers=False)
        window.running_settings=('pool.world','vision',False);window.on_phase('Running')
        window.slam.setChecked(True)  # pending change, not the active session
        window.launch_tool=Mock();window.open_rviz()
        self.assertIn('model_tf.rviz',window.launch_tool.call_args.args[2][1])
        window.running_settings=('pool.world','vision',True);window.open_rviz()
        path=Path(window.launch_tool.call_args.args[2][1])
        config=yaml.safe_load(path.read_text())
        self.assertEqual(config['Visualization Manager']['Global Options']['Fixed Frame'],'map')
        self.assertNotIn('QMainWindow State',config['Window Geometry'])
        displays=config['Visualization Manager']['Displays']
        hd=next(item for item in displays if item['Class']=='rtabmap_rviz_plugins/MapCloud')
        self.assertTrue(hd['Enabled'])
        self.assertEqual(hd['Topic']['Value'],'/rtabmap/mapData')
        self.assertEqual(hd['Download namespace'],'/rtabmap/rtabmap')
        self.assertTrue(any(item['Class']=='rviz_default_plugins/PointCloud2' and not item['Enabled'] and item['Topic']['Value']=='/rtabmap/cloud_map' for item in displays))
        self.assertTrue(any(item['Class']=='rviz_default_plugins/Map' and not item['Enabled'] for item in displays))
        self.assertFalse(any(item['Class']=='rviz_default_plugins/Image' for item in displays))
        window.close()

    def test_stop_waits_for_rviz_before_stopping_ros_publishers(self):
        from unittest.mock import Mock
        from PyQt5.QtCore import QProcess
        window=PilotWindow(start_workers=False)
        window.running_settings=('pool.world','vision',False);window.on_phase('Running')
        rviz=SimpleNamespace(state=Mock(return_value=QProcess.Running))
        window.external_tools['RViz']=rviz;window.stop_rviz=Mock();window.manager.request=Mock()
        window.action('stop')
        self.assertEqual(window.pending_session_action,'stop')
        window.manager.request.assert_not_called()
        window.stop_rviz.assert_called_once()
        rviz.state.return_value=QProcess.NotRunning
        window.tool_finished('RViz',0)
        self.assertIsNone(window.pending_session_action)
        window.manager.request.assert_called_once_with('stop','pool.world','vision',False)
        window.close()

    def test_old_source_frame_is_dropped_instead_of_marked_live(self):
        worker=RosWorker()
        worker.clock(SimpleNamespace(clock=SimpleNamespace(sec=10,nanosec=0)))
        msg=SimpleNamespace(width=1,height=1,step=3,encoding='rgb8',data=bytes([255,0,0]),
                            header=SimpleNamespace(stamp=SimpleNamespace(sec=9,nanosec=0)))
        worker.frame(msg,'main','First person')
        self.assertNotIn('main',worker.snapshot()[0])
        msg.header.stamp.sec=10
        worker.frame(msg,'main','First person')
        self.assertIn('main',worker.snapshot()[0])
        worker.clear_session()
        self.assertIsNone(worker.sim_time)

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
