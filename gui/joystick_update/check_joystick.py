import os,time,subprocess,signal,math
from pathlib import Path
os.environ['ROS_DOMAIN_ID']='144';os.environ['RMW_IMPLEMENTATION']='rmw_fastrtps_cpp'
import rclpy
from rclpy.parameter import Parameter
from rcl_interfaces.srv import SetParametersAtomically
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy
from mavros_msgs.msg import State,ManualControl
from mavros_msgs.srv import CommandBool,SetMode
from rosgraph_msgs.msg import Clock
rclpy.init();node=rclpy.create_node('joystick_contract_test')
state=State();state.connected=True;state.armed=True;state.mode='STABILIZE'
joy=Joy();joy.axes=[0.0]*6;joy.buttons=[0]*8
statepub=node.create_publisher(State,'/mavros/state',10);joypub=node.create_publisher(Joy,'/joy',qos_profile_sensor_data);clockpub=node.create_publisher(Clock,'/clock',10)
frames=[];arms=[];modes=[];accept={'arm':True,'mode':True,'confirm':True};clock_time=1000
autopub=node.create_publisher(ManualControl,'/mako/autopilot/manual_control',10);auto_cmd=None
node.create_subscription(ManualControl,'/mavros/manual_control/send',lambda m:frames.append(m),10)
def arm(req,resp):
 arms.append(req.value);resp.success=accept['arm'];resp.result=0 if resp.success else 4
 if resp.success:state.armed=req.value
 return resp
def mode(req,resp):
 modes.append(req.custom_mode);resp.mode_sent=accept['mode']
 if resp.mode_sent and accept['confirm']:state.mode=req.custom_mode
 return resp
node.create_service(CommandBool,'/mavros/cmd/arming',arm);node.create_service(SetMode,'/mavros/set_mode',mode)
log=Path(os.environ.get('MAKO_WORKSPACE',str(Path.home()/'mako_ws')))/'gui/runs/joystick_contract.log';log.parent.mkdir(exist_ok=True)
process=subprocess.Popen([str(Path(os.environ.get('MAKO_SOFTWARE_WORKSPACE',str(Path.home()/'Software2026')))/'install/real_joy/lib/real_joy/realjoy_node'),'--ros-args','-p','use_sim_time:=true'],stdout=log.open('w'),stderr=subprocess.STDOUT,start_new_session=True)
client=node.create_client(SetParametersAtomically,'/realjoy_node/set_parameters_atomically')
def pump(seconds,sendjoy=True):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  assert process.poll() is None,log.read_text()
  statepub.publish(state)
  if sendjoy:joypub.publish(joy)
  if auto_cmd is not None:autopub.publish(auto_cmd)
  clock=Clock();clock.clock.sec=clock_time;clockpub.publish(clock)
  rclpy.spin_once(node,timeout_sec=.02)
def setparams(**values):
 req=SetParametersAtomically.Request();req.parameters=[Parameter(k,value=v).to_parameter_msg() for k,v in values.items()];f=client.call_async(req)
 end=time.monotonic()+5
 while not f.done() and time.monotonic()<end:pump(.05)
 assert f.done();return f.result().result

def press(button):
 joy.buttons[button]=1;pump(.15);joy.buttons[button]=0;pump(.2)
try:
 assert client.wait_for_service(timeout_sec=10)
 pump(1)
 assert frames and frames[-1].z==500
 assert setparams(smoothing_tau=0.0).successful
 joy.axes=[2.0,-2.0,0.0,2.0,-2.0,2.0];pump(.3)
 m=frames[-1];assert (m.x,m.y,m.z,m.r)==(1000,1000,1000,-1000),(m.x,m.y,m.z,m.r)
 joy.axes=[math.nan,math.inf,0.0,math.nan,math.nan,0.0];pump(.3)
 m=frames[-1];assert (m.x,m.y,m.z,m.r)==(0,0,500,0)
 joy.axes=[0.,.6,0.,.6,0.,0.];pump(.25);before=frames[-1];assert before.x<0 and before.z>500
 assert setparams(invert_forward=False,invert_vertical=True,sensitivity_forward=.5).successful
 pump(.25);after=frames[-1];assert after.x>0 and abs(after.x)<abs(before.x) and after.z<500
 assert not setparams(deadzone_forward=1.0,invert_forward=True).successful
 pump(.2);assert frames[-1].x>0,'Rejected batch changed inversion'
 assert setparams(smoothing_tau=.1,publish_rate_hz=80.0).successful
 joy.axes=[0.]*6;pump(.7);assert abs(frames[-1].x)<2
 joy.axes[1]=1.;pump(.07);assert 0<frames[-1].x<500,'Smoothing did not limit initial step'
 clock_time=1;pump(.75,sendjoy=False);m=frames[-1];assert (m.x,m.y,m.z,m.r)==(0,0,500,0),'Timeout failed across clock reset'
 joy.axes=[0.]*6;pump(.25)
 state.mode='STABILIZE';pump(.2);press(2);assert modes[-1]=='MANUAL','Square ignored externally selected STABILIZE'
 state.mode='ALT_HOLD';pump(.2);press(3);assert modes[-1]=='MANUAL','ALT_HOLD toggle ignored external state'
 state.armed=True;pump(.2);press(6);assert arms[-1] is False,'GUI arming state ignored'
 state.armed=False;state.mode='MANUAL';accept['arm']=False;pump(.2);press(6);assert arms[-1] is True and not state.armed
 press(6);assert arms[-1] is True,'Rejected arming desynchronized toggle'
 accept['mode']=False;state.mode='MANUAL';pump(.2);press(2);press(2);assert modes[-2:]==['STABILIZE','STABILIZE']
 state.armed=False;state.mode='STABILIZE';pump(.2);count=len(arms);press(6)
 assert len(arms)==count,'Armed despite rejected mode request'
 accept['mode']=True;accept['arm']=True;accept['confirm']=False;state.mode='STABILIZE';pump(.2);press(6)
 assert len(arms)==count,'Armed before FCU mode confirmation'
 pump(5.2);assert len(arms)==count,'Timed-out mode request armed vehicle'
 accept['confirm']=True;press(6);assert state.mode=='MANUAL' and state.armed and arms[-1] is True
 joy.axes=[0.]*6;auto_cmd=ManualControl(x=300.,y=-200.,z=650.,r=100.);pump(.4)
 m=frames[-1];assert (m.x,m.y,m.z,m.r)==(300,-200,650,100),'Autopilot command not forwarded'
 joy.axes[1]=1.;pump(.3);assert frames[-1].x>350,'Pilot stick did not override the autopilot'
 joy.axes[1]=0.;pump(.3);assert frames[-1].x==300,'Autopilot did not resume after the stick was released'
 auto_cmd=ManualControl(x=5000.,y=math.nan,z=-50.,r=-5000.);pump(.3);m=frames[-1];assert (m.x,m.y,m.z,m.r)==(1000,0,0,-1000),'Autopilot command not bounded'
 auto_cmd=None;pump(.6);m=frames[-1];assert (m.x,m.y,m.z,m.r)==(0,0,500,0),'Stale autopilot command was not released'
 state.connected=False;pump(.2);joy.axes[1]=1.;pump(.2);assert frames[-1].x==0
 print('PASS: clamping/nonfinite input, live tuning, atomic rejection, smoothing, timeout across clock reset, external mode/arm synchronization and rejection handling, autopilot forwarding/override/release')
 assert 'rejected' in log.read_text().lower(),log.read_text()
finally:
 process.send_signal(signal.SIGINT)
 try:process.wait(timeout=5)
 except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
 node.destroy_node();rclpy.shutdown()
