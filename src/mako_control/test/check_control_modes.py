"""Live isolated SITL/Gazebo control-mode check. Requires ROS setup sourced."""
import os,sys,tempfile,shutil,time,math,json
from pathlib import Path
os.environ['ROS_DOMAIN_ID']='143'
os.environ['RMW_IMPLEMENTATION']='rmw_fastrtps_cpp'
WORKSPACE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(WORKSPACE/'gui'))
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--odometry-source',choices=['ground_truth','vision'],default='ground_truth')
args=parser.parse_args()
from mako_station.simulation import SimulationSession
import rclpy
from rclpy.qos import qos_profile_sensor_data
from mavros_msgs.msg import State,ManualControl
from mavros_msgs.srv import CommandBool,SetMode
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
rclpy.init();node=rclpy.create_node('isolated_mode_check')
state={};pose={};estimate={};command=ManualControl();command.z=500.0
node.create_subscription(State,'/mavros/state',lambda m:state.update(connected=m.connected,armed=m.armed,mode=m.mode),10)
node.create_subscription(Odometry,'/odometry/gz',lambda m:pose.update(p=m.pose.pose.position,q=m.pose.pose.orientation,w=m.twist.twist.angular),qos_profile_sensor_data)
node.create_subscription(PoseStamped,'/mavros/local_position/pose',lambda m:estimate.update(p=m.pose.position,q=m.pose.orientation),qos_profile_sensor_data)
pub=node.create_publisher(ManualControl,'/mavros/manual_control/send',10)
arm=node.create_client(CommandBool,'/mavros/cmd/arming');mode=node.create_client(SetMode,'/mavros/set_mode')
def pump(duration):
 end=time.monotonic()+duration
 while time.monotonic()<end:
  pub.publish(command);rclpy.spin_once(node,timeout_sec=.02)
def wait(predicate,timeout):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  pump(.1)
  if predicate():return
 raise RuntimeError('Timeout '+str(state))
def call(client,req):
 assert client.wait_for_service(timeout_sec=10)
 future=client.call_async(req);wait(future.done,15)
 response=future.result();assert getattr(response,'success',getattr(response,'mode_sent',False)),response
 return response
def attitude():
 q=pose['q'];return [math.atan2(2*(q.w*q.x+q.y*q.z),1-2*(q.x*q.x+q.y*q.y)),math.asin(max(-1,min(1,2*(q.w*q.y-q.z*q.x))))]
def report(name):
 print(name,json.dumps(dict(state=state,z=pose['p'].z,rp=attitude(),yaw_rate=pose['w'].z,estimated_z=estimate.get('p').z if estimate else None)),flush=True)
with tempfile.TemporaryDirectory(prefix='mako-mode-test-') as folder:
 root=Path(folder);(root/'install').symlink_to(WORKSPACE/'install');(root/'src').symlink_to(WORKSPACE/'src');shutil.copy2(WORKSPACE/'commands.txt',root/'commands.txt')
 session=SimulationSession(workspace=root,domain=143,instance=9,outputs=(24750,24751))
 spawn=session.processes.spawn
 def only_sim(name,*args):
  if name not in ('Joystick','Pilot control'):return spawn(name,*args)
 session.processes.spawn=only_sim
 try:
  session.start(odometry=args.odometry_source,notify=lambda s:print(s,flush=True));print('LOGS',session.directory,flush=True)
  wait(lambda:state.get('connected') and bool(pose) and bool(estimate),100);pump(15)
  req=SetMode.Request();req.custom_mode='STABILIZE';call(mode,req)
  req=CommandBool.Request();req.value=True;call(arm,req);wait(lambda:state.get('armed') and state.get('mode')=='STABILIZE',10)
  pump(10);report('STABILIZE neutral')
  command.r=150.0;pump(3);command.r=0.0;pump(12);report('STABILIZE after yaw')
  assert max(abs(v) for v in attitude())<.2 and abs(pose['w'].z)<.1,'STABILIZE failed to settle'
  req=SetMode.Request();req.custom_mode='ALT_HOLD';call(mode,req);wait(lambda:state.get('mode')=='ALT_HOLD',10)
  pump(12);start_z=pose['p'].z;pump(12);report('ALT_HOLD neutral');assert abs(pose['p'].z-start_z)<.15,'Depth drift'
  command.z=600.;pump(3);command.z=500.;pump(10);report('ALT_HOLD after vertical input');target=pose['p'].z;pump(12);report('ALT_HOLD settled')
  assert max(abs(v) for v in attitude())<.2 and abs(pose['p'].z-target)<.15,'ALT_HOLD failed to settle'
  print('PASS: STABILIZE and ALT_HOLD remain stable after yaw and vertical input',flush=True)
 finally:
  session.stop()
  destination=(WORKSPACE/'gui/runs/control_checks')/session.directory.name
  shutil.copytree(session.directory,destination,dirs_exist_ok=True)
  node.destroy_node()
  if rclpy.ok():rclpy.shutdown()
