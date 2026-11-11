"""Manual regression: RGB-D depth must survive yaw with the acrylic dome visible.

Isolated ROS domain 161 / random Gazebo partition, no SITL or vehicle commands.
"""
import os,subprocess,signal,tempfile,time,uuid,math,importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import xacro
root=Path(__file__).resolve().parents[1]
os.environ['ROS_DOMAIN_ID']='161';os.environ['GZ_PARTITION']='camera-yaw-'+uuid.uuid4().hex
os.environ['GZ_SIM_RESOURCE_PATH']=str(root.parent)
os.environ['__EGL_VENDOR_LIBRARY_FILENAMES']='/usr/share/glvnd/egl_vendor.d/10_nvidia.json'
spec=importlib.util.spec_from_file_location('world_launch',root/'launch/gazebo.launch.py');launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
directory=Path(tempfile.mkdtemp(prefix='mx-camera-yaw-'));os.environ['ROS_LOG_DIR']=str(directory/'ros')
description=xacro.process_file(str(root/'urdf/robot_description.urdf'),mappings={'camera_width':'640','camera_height':'360','camera_fps':'10','pilot_fps':'15'}).toxml()
world_path=launch.prepare_world(root/'worlds/pool.world',description,directory)
tree=ET.parse(world_path);world=tree.find('world');world_name=world.get('name');model=world.find("model[@name='mako']")
ET.SubElement(model,'static').text='true'
for plugin in list(model.findall('plugin')):model.remove(plugin)
for plugin in list(world.findall('plugin')):
 if plugin.get('name') not in ['gz::sim::systems::Physics','gz::sim::systems::Sensors','gz::sim::systems::UserCommands']:world.remove(plugin)
tree.write(world_path)
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from gz.transport13 import Node as GzNode
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.boolean_pb2 import Boolean
rclpy.init();node=rclpy.create_node('camera_yaw_fixture');samples=[]
node.create_subscription(Image,'/zed2i/rgbd/left/depth/image_raw',lambda m:samples.append(float(np.isfinite(np.frombuffer(m.data,dtype=np.float32)).mean())),qos_profile_sensor_data)
transport=GzNode();processes=[];logs=[]
try:
 for name,cmd in [('gz',['gz','sim','-s','-r','--headless-rendering',str(world_path)]),('bridge',['ros2','run','ros_gz_bridge','parameter_bridge','--ros-args','-p','config_file:='+str(root/'config/zed2i_rgbd_bridge.yaml')])]:
  log=(directory/(name+'.log')).open('w');logs.append(log);processes.append(subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True))
 end=time.monotonic()+25
 while not samples and time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.1)
 assert samples,'No depth received'
 for yaw in [0.,.785,1.,1.57,2.55,3.14,3.93,4.7,5.5,0.]:
  p=Pose(name='mako');p.position.x=-.47;p.position.y=-.54;p.position.z=-1.8;p.orientation.z=math.sin(yaw/2);p.orientation.w=math.cos(yaw/2)
  ok,response=transport.request('/world/'+world_name+'/set_pose',p,Pose,Boolean,1000);assert ok and response.data
  samples.clear();end=time.monotonic()+2
  while time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.1)
  assert len(samples)>=5 and float(np.median(samples[-5:]))>.10, ('Depth lost at heading',yaw,samples[-5:])
  print('YAW',yaw,'valid depth median',float(np.median(samples[-5:])),'samples',len(samples),flush=True)
 print('Logs:',directory,flush=True)
finally:
 for p in processes:
  if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
 for p in processes:
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 for log in logs:log.close()
 node.destroy_node();rclpy.shutdown()
