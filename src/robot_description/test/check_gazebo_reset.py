"""Manual Gazebo reset regression (requires ROS setup, built package and transport).
Runs an isolated headless world without the external ArduPilot/SITL connection.
Usage: python3 src/robot_description/test/check_gazebo_reset.py
"""
import os,time,subprocess,signal,tempfile,uuid,importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
import xacro
from ament_index_python.packages import get_package_share_directory

share = Path(get_package_share_directory('robot_description'))
spec = importlib.util.spec_from_file_location('mako_launch', share / 'launch/gazebo.launch.py')
launch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch_module)
temporary = tempfile.TemporaryDirectory(prefix='mako-reset-regression-')
description = xacro.process_file(str(share / 'urdf/robot_description.urdf')).toxml()
world_file = launch_module.prepare_world(share / 'worlds/pool.sdf', description, temporary.name)
world = ET.parse(world_file)
model = world.find("world/model[@name='mako']")
for plugin in list(model.findall('plugin')):
    if 'ArduPilot' in plugin.get('name', ''):
        model.remove(plugin)
world.write(world_file)
os.environ['GZ_PARTITION']='mako_reset_'+uuid.uuid4().hex
os.environ['GZ_SIM_SYSTEM_PLUGIN_PATH']=str(share.parent.parent / 'lib')+':'+os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH','')
os.environ['GZ_SIM_RESOURCE_PATH']=str(share.parent)+':'+os.environ.get('GZ_SIM_RESOURCE_PATH','')
from gz.transport13 import Node
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.world_control_pb2 import WorldControl
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.image_pb2 import Image
from gz.msgs10.odometry_pb2 import Odometry
from google.protobuf.text_format import MessageToString
node=Node();poses=[];images=[];odom=[];clocks=[]
node.subscribe(Pose_V,'/world/CompetitionWorld2025/pose/info',lambda m:poses.extend(p for p in m.pose if p.name=='mako'))
node.subscribe(Clock,'/clock',lambda m:clocks.append(m.sim.sec+m.sim.nsec*1e-9))
node.subscribe(Image,'/zed2i/sim/left/image',lambda m:images.append(m.header.stamp.sec+m.header.stamp.nsec*1e-9))
node.subscribe(Odometry,'/model/mako/odometry',lambda m:odom.append(m.header.stamp.sec+m.header.stamp.nsec*1e-9))
f=open(Path(temporary.name)/'gazebo.log','w');p=subprocess.Popen(['gz','sim','-s','-r','--headless-rendering',str(world_file)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
def wait(condition,timeout=30):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if condition():return
  time.sleep(.05)
 raise AssertionError('Timed out: '+str((len(poses),len(images),len(odom),clocks[-1:], [(v.position.x,v.position.z) for v in poses[-2:]])))
def service(name, request):
 result=subprocess.run(['gz','service','-s','/world/CompetitionWorld2025/'+name,
    '--reqtype',request.DESCRIPTOR.full_name,'--reptype','gz.msgs.Boolean',
    '--timeout','10000','--req',MessageToString(request)],capture_output=True,text=True,timeout=15)
 assert 'data: true' in result.stdout, (name,result.stdout,result.stderr)
try:
 wait(lambda:len(images)>5 and len(odom)>5 and bool(poses))
 for cycle in range(3):
  request=Pose(name='mako');request.position.x=2;request.position.y=1;request.position.z=-1.5;request.orientation.w=1
  service('set_pose',request)
  wait(lambda:abs(poses[-1].position.x-2)<.05)
  before=(len(poses),len(images),len(odom),len(clocks))
  request=WorldControl(pause=False);request.reset.all=True
  service('control',request)
  wait(lambda:len(poses)>before[0]+5 and abs(poses[-1].position.x)<.05 and abs(poses[-1].position.z+1)<.05)
  wait(lambda:len(images)>before[1]+5 and len(odom)>before[2]+5)
  assert any(t<.3 for t in clocks[before[3]:]), 'Clock did not reset'
  print('Reset',cycle+1,'PASS: Mako restored to (0,0,-1); camera and odometry resumed',flush=True)
 # Allow time for a missing buoyancy force to reveal itself as sinking.
 time.sleep(8)
 assert abs(poses[-1].position.z+1)<.05, ('Buoyancy lost after reset',poses[-1].position.z)
 print('PASS: neutral depth retained eight seconds after final reset',flush=True)
finally:
 os.killpg(p.pid,signal.SIGTERM)
 try:p.wait(timeout=4)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 f.close()
 temporary.cleanup()
