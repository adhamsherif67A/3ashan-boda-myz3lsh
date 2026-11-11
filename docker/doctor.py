#!/usr/bin/env python3
"""Read-only dependency check; no downloads or installation at runtime."""
import importlib,os,shutil,subprocess,sys
from pathlib import Path
from ament_index_python.packages import get_package_prefix
workspace=Path(os.environ.get('MAKO_WORKSPACE','/opt/mako_ws'))
autopilot=Path(os.environ.get('MAKO_ARDUPILOT','/opt/ardupilot'))
plugin=Path(os.environ.get('MAKO_ARDUPILOT_GAZEBO','/opt/ardupilot_gazebo'))/'build/libArduPilotPlugin.so'
failed=[]
def check(label,operation):
    try:
        assert operation(), 'not found'
        print('OK:',label)
    except Exception as error:
        failed.append(label);print('MISSING:',label,'-',error)
for package in ['robot_description','mako_control','mako_vision','mako_bringup','ros_gz_sim','ros_gz_bridge','mavros','joy','rtabmap_odom','rviz2']:
    check('ROS '+package,lambda p=package:get_package_prefix(p))
for module in ['rclpy','pymavlink','MAVProxy','psutil','em','PyQt5']:
    check('Python '+module,lambda m=module:importlib.import_module(m))
check('MAVProxy launcher',lambda:shutil.which('mavproxy.py'))
check('Gazebo Harmonic CLI',lambda:shutil.which('gz') and '8.' in subprocess.check_output(['gz','sim','--versions'],text=True))
check('Harmonic ROS launch',lambda:'gz_args' in (Path(get_package_prefix('ros_gz_sim'))/'share/ros_gz_sim/launch/gz_sim.launch.py').read_text())
check('ArduSub binary',lambda:(autopilot/'build/sitl/bin/ardusub').is_file())
check('ArduPilot Harmonic plugin',lambda:plugin.is_file() and 'not found' not in subprocess.check_output(['ldd',str(plugin)],text=True))
check('EGM96 geoid',lambda:any(p.is_file() for p in [Path('/usr/share/GeographicLib/geoids/egm96-5.pgm'),Path('/usr/local/share/GeographicLib/geoids/egm96-5.pgm')]))
for name in ['pool.world','ocean.world']:
    check('World '+name,lambda n=name:(workspace/'src/robot_description/worlds'/n).is_file())
print('RESULT:', 'ready' if not failed else 'incomplete ('+str(len(failed))+' missing)')
sys.exit(bool(failed))
