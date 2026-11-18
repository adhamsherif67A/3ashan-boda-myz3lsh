"""Real controller node -> MAVROS -> custom SITL -> physical Gazebo model."""
import os, sys, time, json, math
from pathlib import Path
import numpy as np
os.environ['ROS_DOMAIN_ID']='84'
sys.path.insert(0,'/opt/mako_ws/gui')
from mako_station.simulation import SimulationSession
import rclpy
from sensor_msgs.msg import Joy
from nav_msgs.msg import Odometry
from mavros_msgs.msg import State, ManualControl, RCIn
from mavros_msgs.srv import SetMode, CommandBool
from rclpy.qos import qos_profile_sensor_data

rclpy.init();node=rclpy.create_node('fish_physical_six_axis_check')
states=[];poses=[];manual=[];rc=[]
node.create_subscription(State,'/mavros/state',states.append,10)
node.create_subscription(Odometry,'/odometry/gz',poses.append,qos_profile_sensor_data)
node.create_subscription(ManualControl,'/mavros/manual_control/send',manual.append,10)
node.create_subscription(RCIn,'/mavros/rc/in',rc.append,qos_profile_sensor_data)
pub=node.create_publisher(Joy,'/joy',qos_profile_sensor_data)
joy=Joy();joy.axes=[0.]*6;joy.buttons=[0]*21
def pump(duration,publish=True):
 end=time.monotonic()+duration
 while time.monotonic()<end:
  if publish:pub.publish(joy)
  rclpy.spin_once(node,timeout_sec=.015)
def wait(pred,timeout=100):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  pump(.1)
  if pred():return
 raise AssertionError('Timed out: '+str(states[-1] if states else 'no FCU'))
def call(name,kind,req):
 c=node.create_client(kind,name);assert c.wait_for_service(timeout_sec=10)
 future=c.call_async(req);wait(future.done,15);reply=future.result()
 assert getattr(reply,'success',getattr(reply,'mode_sent',False)),str(reply)
def R(q):
 x,y,z,w=q.x,q.y,q.z,q.w
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def position(m):return np.array([m.pose.pose.position.x,m.pose.pose.position.y,m.pose.pose.position.z])
def rotation_vector(mat):
 angle=math.acos(float(np.clip((np.trace(mat)-1)/2,-1,1)))
 if angle<1e-8:return np.zeros(3)
 return angle/(2*math.sin(angle))*np.array([mat[2,1]-mat[1,2],mat[0,2]-mat[2,0],mat[1,0]-mat[0,1]])

session=SimulationSession(domain=84,instance=13,outputs=(24950,24951))
spawn=session.processes.spawn
def isolated(name,*args):
 if name!='Joystick':return spawn(name,*args)
session.processes.spawn=isolated
report={}
try:
 session.start(world=os.environ.get('FISH_TEST_WORLD','pool.world'),odometry='ground_truth',slam=False,notify=lambda s:print(s,flush=True))
 wait(lambda:states and states[-1].connected and poses);pump(5)
 p0=position(poses[-1]);pump(3);drift=float(np.linalg.norm(position(poses[-1])-p0))
 print('Neutral drift',drift,flush=True);assert drift<.05,'Buoyancy or idle motor force is unbalanced'
 call('/mavros/set_mode',SetMode,SetMode.Request(custom_mode='MANUAL'));wait(lambda:states[-1].mode=='MANUAL')
 # Verify the modifier at the published command and the actual FCU RC input.
 joy.axes[3]=.6;joy.buttons[10]=1;pump(.4)
 assert abs(manual[-1].s)>30 and abs(manual[-1].z-500)<1,manual[-1]
 print('Pitch modifier command',manual[-1].s,'RC',rc[-1].channels if rc else None,flush=True)
 wait(lambda:rc and rc[-1].channels[0]>1520,4)
 print('Pitch RC confirmed',rc[-1].channels,flush=True)
 joy.buttons[10]=0;pump(.2)
 assert abs(manual[-1].s)<1 and manual[-1].z>550,manual[-1]
 wait(lambda:rc and rc[-1].channels[0]==1500 and rc[-1].channels[2]>1500,3)
 print('R1 released: restored heave RC',rc[-1].channels,flush=True)
 joy.axes=[0.]*6;pump(.2);joy.axes[2]=-.5;pump(.3)
 assert manual[-1].t>30 and abs(manual[-1].s)<1,manual[-1]
 joy.axes=[0.]*6;pump(.8,publish=False)
 assert abs(manual[-1].t)<1 and abs(manual[-1].s)<1 and abs(manual[-1].z-500)<1,'Stale attitude command'
 pump(.2)
 joy.buttons[11]=1;pump(.4);joy.buttons[11]=0;pump(.3)
 assert states[-1].mode=='MANUAL' and not states[-1].armed,'D-pad Up changed the flight mode or armed'
 call('/mavros/cmd/arming',CommandBool,CommandBool.Request(value=True));wait(lambda:states[-1].armed)
 # Each positive pilot input must move along the expected local physical axis.
 cases=[('forward',1,.45,None,[1,0,0]),('lateral',0,-.45,None,[0,-1,0]),
        ('heave',3,.45,None,[0,0,1]),('yaw',5,-.4,None,[0,0,-1]),
        ('roll',2,-.35,None,[1,0,0]),('pitch',3,.35,10,[0,-1,0])]
 if os.environ.get('FISH_TEST_NEGATIVE')=='1':
  cases=[('forward',1,-.45,None,[-1,0,0]),('lateral',0,.45,None,[0,1,0]),
         ('heave',3,-.45,None,[0,0,-1]),('yaw',4,-.4,None,[0,0,1]),
         ('roll',2,.35,None,[-1,0,0]),('pitch',3,-.35,10,[0,1,0])]
 results=[]
 for name,index,value,button,expected in cases:
  joy.axes=[0.]*6;joy.buttons=[0]*21;pump(3)
  before=poses[-1];rotation=R(before.pose.pose.orientation)
  joy.axes[index]=value
  if button is not None:joy.buttons[button]=1
  pump(.5);after=poses[-1]
  assert states[-1].mode=='MANUAL','Pilot input changed mode: '+name
  delta=rotation.T@(position(after)-position(before)) if name in ['forward','lateral','heave'] else rotation_vector(rotation.T@R(after.pose.pose.orientation))
  desired=np.array(expected);signed=float(delta@desired)
  result={'axis':name,'local_delta':delta.tolist(),'signed_primary':signed,'units':'m' if name in ['forward','lateral','heave'] else 'rad'}
  results.append(result);print('MOTION',json.dumps(result),flush=True)
  assert signed>(.015 if result['units']=='m' else .025),'Wrong or missing '+name+' motion'
  # Opposing short command arrests motion before passive settling.
  joy.axes[index]=-value;pump(.35);joy.axes=[0.]*6;joy.buttons=[0]*21;pump(3)
 call('/mavros/cmd/arming',CommandBool,CommandBool.Request(value=False));wait(lambda:not states[-1].armed)
 report={'status':'PASS','neutral_drift_m':drift,'dpad_up_has_no_mode_action':True,'motion_keeps_manual_mode':True,'modifier_rc_verified':True,'stale_input_neutral_verified':True,'motions':results,'disarmed_after_test':True,'session':str(session.directory)}
finally:
 session.stop();node.destroy_node();rclpy.shutdown()
 if report:Path('/opt/mako_ws/fish-control-'+('negative-' if os.environ.get('FISH_TEST_NEGATIVE')=='1' else '')+'restored-test-result.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
