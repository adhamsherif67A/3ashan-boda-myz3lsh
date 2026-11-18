import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mako_supervisor',ROOT/'docker/simulation.py')
supervisor=importlib.util.module_from_spec(spec);spec.loader.exec_module(supervisor)

class ContainerSetup(unittest.TestCase):
    def test_apt_installer_skips_existing_packages_and_batches_missing_packages(self):
        import os,subprocess
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            query=folder/'dpkg-query';query.write_text('#!/bin/bash\n[[ "${@: -1}" == present ]] && echo "install ok installed"\n');query.chmod(0o755)
            apt=folder/'apt-get';apt.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$MAKO_APT_LOG"\n');apt.chmod(0o755)
            log=folder/'apt.log';env=os.environ.copy();env.update(PATH=str(folder)+':'+env['PATH'],MAKO_APT_LOG=str(log))
            command=['bash',str(ROOT/'docker/install-apt.sh')]
            subprocess.run(command+['present'],env=env,check=True,capture_output=True)
            self.assertFalse(log.exists())
            subprocess.run(command+['present','missing'],env=env,check=True,capture_output=True)
            self.assertEqual(log.read_text().splitlines(),['update','install --no-install-recommends -y missing'])

    def test_default_commands_preserve_endpoints_and_preload_parameters(self):
        jobs=dict(supervisor.plan(ROOT,Path('/opt/ardupilot'),'pool.world','vision',True,30))
        self.assertIn('--out=udp:127.0.0.1:14550',jobs['SITL'])
        self.assertIn('fcu_url:=udp://127.0.0.1:14551@',jobs['MAVROS'])
        self.assertIn('--add-param-file',jobs['SITL'])
        self.assertNotIn('--no-rebuild',jobs['SITL'])
        self.assertIn('configure_ardusub:=false',jobs['Gazebo'])
        self.assertIn('headless:=true',jobs['Gazebo'])
        self.assertEqual(set(jobs),{'SITL','MAVROS','Gazebo'})
        self.assertEqual(jobs['Gazebo'][:4],['ros2','launch','mako_bringup','simulation.launch.py'])
        self.assertIn(str(ROOT/'src/mako_control/config/ardusub_external_nav.parm'),jobs['SITL'])

    def test_slam_forces_vision_and_pilot_adds_realjoy(self):
        jobs=dict(supervisor.plan(ROOT,Path('/opt/ardupilot'),'pool.world','ground_truth',True,30,slam=True,pilot=True,gamepad=False))
        self.assertIn('odometry_source:=vision',jobs['Gazebo'])
        self.assertIn('slam:=true',jobs['Gazebo'])
        self.assertEqual(jobs['Pilot'],['ros2','launch','mako_control','pilot.launch.py','joystick:=false'])

    def test_instance_ports_stay_consistent_across_all_three_processes(self):
        jobs=dict(supervisor.plan(ROOT,Path('/opt/ardupilot'),'ocean.world','ground_truth',True,30,9))
        self.assertIn('--out=udp:127.0.0.1:14641',jobs['SITL'])
        self.assertIn('fcu_url:=udp://127.0.0.1:14641@',jobs['MAVROS'])
        self.assertIn('sitl_port_in:=9092',jobs['Gazebo'])
        self.assertEqual(len(jobs),3)

    def test_supervisor_initializes_and_stops_owned_processes(self):
        class Finished:
            pid=987654321
            returncode=7
            def poll(self):return self.returncode
            def wait(self,timeout):return self.returncode
        with tempfile.TemporaryDirectory() as folder:
            with patch('sys.argv',['simulation','--headless','--log-dir',folder]), \
                 patch.dict('os.environ',MAKO_WORKSPACE=str(ROOT)), \
                 patch.object(supervisor.socket,'socket'), \
                 patch.object(supervisor.subprocess,'Popen',return_value=Finished()) as spawn, \
                 patch.object(supervisor.os,'killpg',side_effect=ProcessLookupError):
                self.assertEqual(supervisor.main(),7)
                argv=spawn.call_args_list[0].args[0]
                self.assertIn('--use-dir',argv)
                self.assertTrue(spawn.call_args.kwargs['start_new_session'])

if __name__=='__main__':unittest.main()
