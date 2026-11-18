import os,sys,time,math,json
os.environ['ROS_DOMAIN_ID']='86'
sys.path.insert(0,'/opt/mako_ws/gui')
from mako_station.simulation import SimulationSession
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy
from nav_msgs.msg import Odometry
from mavros_msgs.msg import State,ManualControl
from mavros_msgs.srv import CommandBool,SetMode
rclpy.init();n=rclpy.create_node('isolated_original_joystick_motion');state={};position={};commands=[];truth=[];external=[];grids=[];infos=[]
n.create_subscription(State,'/mavros/state',lambda m:state.update(connected=m.connected,armed=m.armed,mode=m.mode),10)
n.create_subscription(Odometry,'/odometry/gz',truth.append,qos_profile_sensor_data)
n.create_subscription(Odometry,'/mavros/odometry/out',external.append,10)
from rtabmap_msgs.msg import Info
n.create_subscription(Info,'/rtabmap/info',infos.append,10)
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import QoSProfile,DurabilityPolicy
n.create_subscription(OccupancyGrid,'/rtabmap/map',grids.append,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
n.create_subscription(Odometry,'/odometry/gz',lambda m:position.update(x=m.pose.pose.position.x,y=m.pose.pose.position.y,z=m.pose.pose.position.z),qos_profile_sensor_data)
n.create_subscription(ManualControl,'/mavros/manual_control/send',lambda m:commands.append(m.x),10)
pub=n.create_publisher(Joy,'/joy',qos_profile_sensor_data);joy=Joy();joy.axes=[0.]*6;joy.buttons=[0]*21
arm=n.create_client(CommandBool,'/mavros/cmd/arming');mode=n.create_client(SetMode,'/mavros/set_mode')
def pump(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:pub.publish(joy);rclpy.spin_once(n,timeout_sec=.02)
def wait(pred,timeout=90):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  pump(.1)
  if pred():return
 raise RuntimeError('timeout '+str(state))
def call(c,req):
 assert c.wait_for_service(timeout_sec=10);f=c.call_async(req);wait(f.done,12)
 result=f.result();assert getattr(result,'success',getattr(result,'mode_sent',False)),str(result)
s=SimulationSession(domain=86,instance=15,outputs=(25150,25151));spawn=s.processes.spawn
# Synthetic sticks go through the repository's realjoy_node. The physical driver
# is excluded only from this isolated test, so it cannot mix with these inputs.
def launch(name,*args):
 if name!='Joystick':return spawn(name,*args)
s.processes.spawn=launch
try:
 s.start(odometry='vision',slam=True);wait(lambda:state.get('connected') and position);pump(5)
 call(mode,SetMode.Request(custom_mode='MANUAL'));wait(lambda:state.get('mode')=='MANUAL',10)
 call(arm,CommandBool.Request(value=True));wait(lambda:state.get('armed'),10)
 start=dict(position);commands.clear();joy.axes[1]=.6;pump(3);joy.axes[1]=0.;pump(1)
 joy.axes[5]=-.45;pump(3);joy.axes[5]=0.;pump(1)
 distance=math.hypot(position['x']-start['x'],position['y']-start['y']);peak=max(map(abs,commands),default=0)
 call(arm,CommandBool.Request(value=False));wait(lambda:not state.get('armed'),10)
 def stamp(m):return m.header.stamp.sec+m.header.stamp.nanosec/1e9
 errors=[]
 for m in external:
  ref=min(truth,key=lambda t:abs(stamp(t)-stamp(m)))
  if abs(stamp(ref)-stamp(m))<.025:errors.append(sum((getattr(m.pose.pose.position,k)-getattr(ref.pose.pose.position,k))**2 for k in ('x','y','z'))**.5)
 assert errors and max(errors)<.15,('Visual pose error',max(errors,default=-1))
 print('Mapping diagnostics:',len(grids),'grids,',len(infos),'updates; map age',stamp(truth[-1])-stamp(grids[-1]) if grids else None,'info age',stamp(truth[-1])-stamp(infos[-1]) if infos else None,flush=True)
 assert grids and len(grids[-1].data)>0,'Missing SLAM grid'
 assert infos and stamp(truth[-1])-stamp(infos[-1])<1.,'SLAM processing stopped'
 result={'slam':True,'max_visual_pose_error_m':max(errors),'grid_size':[grids[-1].info.width,grids[-1].info.height],'status':'PASS' if distance>.03 and peak>100 else 'FAIL','horizontal_displacement_m':distance,'peak_manual_forward':peak,'disarmed_after_test':not state['armed'],'controller':'MarineXperts realjoy_node plus Fish roll/pitch extension','session':str(s.directory)}
 print(json.dumps(result),flush=True);open('/opt/mako_ws/fish-vision-motion-result.json','w').write(json.dumps(result,indent=2));assert result['status']=='PASS',result
finally:s.stop();n.destroy_node();rclpy.shutdown()
