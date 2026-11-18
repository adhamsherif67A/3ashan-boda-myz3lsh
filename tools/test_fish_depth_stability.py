"""Measure real Fish physics and ArduSub depth/attitude response in isolation."""
import os,sys,time,json,math,argparse
from pathlib import Path
import numpy as np
os.environ['ROS_DOMAIN_ID']='84'
sys.path.insert(0,'/opt/mako_ws/gui')
from mako_station.simulation import SimulationSession
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy
from nav_msgs.msg import Odometry
from mavros_msgs.msg import State,RCOut
from mavros_msgs.srv import SetMode,CommandBool,ParamSetV2
from rcl_interfaces.msg import ParameterValue
p=argparse.ArgumentParser();p.add_argument('--odometry',default='ground_truth');p.add_argument('--output',default='depth-baseline.json');p.add_argument('--params',default='{}');p.add_argument('--slam',action='store_true');p.add_argument('--hold-only',action='store_true');p.add_argument('--world',default='pool.world');args=p.parse_args()
rclpy.init();n=rclpy.create_node('fish_depth_stability_check');states=[];poses=[];fcu=[];servo=[];mapping_infos=[];grids=[];external=[]
n.create_subscription(State,'/mavros/state',states.append,10)
n.create_subscription(Odometry,'/odometry/gz',poses.append,qos_profile_sensor_data)
n.create_subscription(Odometry,'/mavros/local_position/odom',fcu.append,qos_profile_sensor_data)
n.create_subscription(RCOut,'/mavros/rc/out',servo.append,qos_profile_sensor_data)
n.create_subscription(Odometry,'/mavros/odometry/out',external.append,qos_profile_sensor_data)
if args.slam:
 from rtabmap_msgs.msg import Info
 from nav_msgs.msg import OccupancyGrid
 from rclpy.qos import QoSProfile,DurabilityPolicy
 n.create_subscription(Info,'/rtabmap/info',mapping_infos.append,10)
 n.create_subscription(OccupancyGrid,'/rtabmap/map',grids.append,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
pub=n.create_publisher(Joy,'/joy',qos_profile_sensor_data);joy=Joy();joy.axes=[0.]*6;joy.buttons=[0]*21
samples=[];phase='startup'
def euler(q):
 x,y,z,w=q.x,q.y,q.z,q.w
 return [math.degrees(math.atan2(2*(w*x+y*z),1-2*(x*x+y*y))),math.degrees(math.asin(np.clip(2*(w*y-z*x),-1,1))),math.degrees(math.atan2(2*(w*z+x*y),1-2*(y*y+z*z)))]
def pump(t):
 end=time.monotonic()+t;last=None
 while time.monotonic()<end:
  pub.publish(joy);rclpy.spin_once(n,timeout_sec=.015)
  if poses and poses[-1] is not last:
   m=poses[-1];last=m;q=m.pose.pose;v=m.twist.twist.linear
   samples.append({'phase':phase,'time':m.header.stamp.sec+m.header.stamp.nanosec*1e-9,'xyz':[q.position.x,q.position.y,q.position.z],'rpy_deg':euler(q.orientation),'velocity':[v.x,v.y,v.z],'fcu_z':fcu[-1].pose.pose.position.z if fcu else None,'pwm':list(servo[-1].channels[:6]) if servo else []})
def wait(pred,t=90):
 end=time.monotonic()+t
 while time.monotonic()<end:
  pump(.1)
  if pred():return
 raise RuntimeError('Timeout '+str(states[-1] if states else 'no FCU'))
def call(name,typ,req):
 c=n.create_client(typ,name);assert c.wait_for_service(timeout_sec=10);f=c.call_async(req);wait(f.done,15);r=f.result();assert getattr(r,'success',getattr(r,'mode_sent',False)),str(r);return r
def mode(s):
 call('/mavros/set_mode',SetMode,SetMode.Request(custom_mode=s));wait(lambda:states[-1].mode==s,10)
def measure(name,t,forward=0,vertical=0):
 global phase
 phase=name;joy.axes=[0.]*6;joy.axes[1]=forward;joy.axes[3]=vertical;start=len(samples);pump(t);a=samples[start:];z=[s['xyz'][2] for s in a];rp=np.array([s['rpy_deg'][:2] for s in a]);r={'phase':name,'z_start':z[0],'z_end':z[-1],'z_range':max(z)-min(z),'max_roll_pitch_deg':np.max(abs(rp),axis=0).tolist(),'end_rpy_deg':a[-1]['rpy_deg'],'horizontal_distance_m':float(np.linalg.norm(np.array(a[-1]['xyz'][:2])-a[0]['xyz'][:2]))};print(json.dumps(r),flush=True);return r
s=SimulationSession(domain=84,instance=13,outputs=(24950,24951));spawn=s.processes.spawn
s.processes.spawn=lambda name,*a:None if name=='Joystick' else spawn(name,*a)
result={};phases=[]
try:
 s.start(world=args.world,odometry=args.odometry,slam=args.slam,notify=lambda v:print(v,flush=True));wait(lambda:states and states[-1].connected and poses and fcu);pump(5)
 for name,value in json.loads(args.params).items():
  call('/mavros/param/set',ParamSetV2,ParamSetV2.Request(param_id=name,value=ParameterValue(type=3,double_value=float(value))))
 mode('MANUAL');call('/mavros/cmd/arming',CommandBool,CommandBool.Request(value=True));wait(lambda:states[-1].armed)
 if not args.hold_only:
  phases.append(measure('manual_idle',3));phases.append(measure('manual_forward',6,forward=.5));phases.append(measure('manual_release',5))
  mode('STABILIZE');phases.append(measure('stabilize_idle',5));phases.append(measure('stabilize_forward',6,forward=.5));phases.append(measure('stabilize_release',5))
 mode('ALT_HOLD');phases.append(measure('hold_idle',10));phases.append(measure('hold_forward',6,forward=.5));phases.append(measure('hold_release',10));phases.append(measure('hold_climb',3,vertical=.6));phases.append(measure('hold_new_depth',12))
 call('/mavros/cmd/arming',CommandBool,CommandBool.Request(value=False));wait(lambda:not states[-1].armed)
 checks={}
 for item in phases:
  if item['phase'] in ['manual_forward','stabilize_forward','hold_forward']:
   checks[item['phase']+'_attitude']=max(item['max_roll_pitch_deg'])<1.0
  if item['phase'] in ['hold_idle','hold_forward','hold_release']:
   checks[item['phase']+'_depth']=item['z_range']<.10
  if item['phase']=='hold_climb':checks['climb_command_moves_up']=item['z_end']-item['z_start']>.04
  if item['phase']=='hold_new_depth':
   tail=[row['xyz'][2] for row in samples if row['phase']=='hold_new_depth'][-120:]
   checks['new_depth_settled']=max(tail)-min(tail)<.05
 if args.slam:
  checks['nonempty_slam_map']=bool(grids and len(grids[-1].data)>0)
  stamp=lambda m:m.header.stamp.sec+m.header.stamp.nanosec*1e-9
  checks['slam_still_updating']=bool(mapping_infos and stamp(poses[-1])-stamp(mapping_infos[-1])<1.5)
  checks['vision_still_updating']=bool(external and stamp(poses[-1])-stamp(external[-1])<1.0)
 result={'mapping_updates':len(mapping_infos),'grid_size':[grids[-1].info.width,grids[-1].info.height] if grids else None,'checks':checks,'status':'PASS' if all(checks.values()) else 'FAIL','odometry':args.odometry,'params':json.loads(args.params),'phases':phases,'session':str(s.directory),'samples':samples,'disarmed_after_test':True}
 print('RESULT',json.dumps({k:v for k,v in result.items() if k!='samples'}),flush=True)
 assert all(checks.values()),checks
finally:
 s.stop();n.destroy_node();rclpy.shutdown();Path('/opt/mako_ws/'+args.output).write_text(json.dumps(result or {'phases':phases,'samples':samples},indent=2))
