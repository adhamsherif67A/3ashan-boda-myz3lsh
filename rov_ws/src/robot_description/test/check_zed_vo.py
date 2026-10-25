"""Manual ZED visual-odometry integration check (requires ROS setup and built package).
Runs isolated Gazebo/ROS, real MAVROS, and a mock FCU endpoint without SITL.
Usage: python3 src/robot_description/test/check_zed_vo.py
"""
import os,time,subprocess,signal,tempfile,uuid,importlib.util
import numpy as np
from pathlib import Path
import xml.etree.ElementTree as ET
import xacro
from ament_index_python.packages import get_package_share_directory

share = Path(get_package_share_directory('robot_description'))
spec = importlib.util.spec_from_file_location('mako_launch', share / 'launch/gazebo.launch.py')
launch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch_module)
temporary = tempfile.TemporaryDirectory(prefix='mako-reset-regression-')
description = xacro.process_file(str(share / 'urdf/robot_description.urdf'),mappings={'camera_width':os.environ.get('VO_TEST_WIDTH','1280'),'camera_height':os.environ.get('VO_TEST_HEIGHT','720'),'pilot_fps':os.environ.get('PILOT_TEST_FPS','30')}).toxml()
world_file = launch_module.prepare_world(share / 'worlds' / os.environ.get('VO_TEST_WORLD','pool.world'), description, temporary.name)
world = ET.parse(world_file)
world_name=world.find('world').get('name')
model = world.find("world/model[@name='mako']")
for plugin in list(model.findall('plugin')):
    if 'ArduPilot' in plugin.get('name', ''):
        model.remove(plugin)
world.write(world_file)
os.environ['__NV_PRIME_RENDER_OFFLOAD']='1'
os.environ['__GLX_VENDOR_LIBRARY_NAME']='nvidia'
os.environ['GZ_PARTITION']='mako_reset_'+uuid.uuid4().hex
os.environ['GZ_SIM_SYSTEM_PLUGIN_PATH']=str(share.parent.parent / 'lib')+':'+os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH','')
os.environ['GZ_SIM_RESOURCE_PATH']=str(share.parent)+':'+os.environ.get('GZ_SIM_RESOURCE_PATH','')
import rclpy,yaml,threading
os.environ['MAVLINK20']='1'
from pymavlink import mavutil
from nav_msgs.msg import Odometry
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
os.environ['ROS_DOMAIN_ID']='125';os.environ['ROS_LOG_DIR']=str(Path(temporary.name)/'roslogs')
spec=importlib.util.spec_from_file_location('vo_launch',share/'launch/zed_vo.launch.py');vo_launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(vo_launch);vo_launch.setup(None)
params=Path(temporary.name)/'rsp.yaml';params.write_text(yaml.safe_dump({'/**':{'ros__parameters':{'robot_description':description,'use_sim_time':True}}}))
commands=[('mavros',['ros2','launch','mavros','apm.launch','fcu_url:=udp://127.0.0.1:14651@127.0.0.1:14650']),
 ('ned',['ros2','run','tf2_ros','static_transform_publisher','--frame-id','odom','--child-frame-id','odom_ned','--roll','3.141592653589793','--pitch','0','--yaw','1.570796326794897']),
 ('gz',['gz','sim','-s','-r','--headless-rendering',str(world_file)]),
 ('rsp',['ros2','run','robot_state_publisher','robot_state_publisher','--ros-args','--params-file',str(params)]),
 ('bridge',['ros2','run','ros_gz_bridge','parameter_bridge','/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock','/model/mako/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry','--ros-args','-r','/model/mako/odometry:=/odometry/gz']),
 ('camera_bridge',['ros2','run','ros_gz_bridge','parameter_bridge','--ros-args','-p','config_file:='+str(share/'config/zed2i_bridge.yaml')]),
 ('vo',['ros2','launch','robot_description','zed_vo.launch.py']),
 ('relay',['ros2','run','robot_description','gz_odom_to_mavros.py','--ros-args','-p','use_sim_time:=true','-p','source_topic:=/zed2i/vo/odometry','-p','require_covariance:=true','-p','reset_on_clock_jump:=true','-p','max_linear_speed:=2.0','-p','max_angular_speed:=3.0','-p','publish_tf:=true'])]
processes=[];logs=[];visual=[];truth=[];external=[];transforms=[];mavlink_odometry=[];camera_rss=[]
stop=threading.Event()
endpoint=mavutil.mavlink_connection('udpin:127.0.0.1:14650',source_system=1,source_component=1)
def receive():
 last=0
 while not stop.is_set():
  message=endpoint.recv_match(blocking=False)
  if message and message.get_type()=='ODOMETRY':mavlink_odometry.append(message)
  if time.monotonic()-last>.5:
   endpoint.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_SUBMARINE,mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,0,0,mavutil.mavlink.MAV_STATE_ACTIVE)
   last=time.monotonic()
  time.sleep(.005)
receiver=threading.Thread(target=receive,daemon=True);receiver.start()
try:
 for name,cmd in commands:
  log=open('/tmp/mako_vo_'+name+'.log','w');logs.append(log);processes.append(subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
 rclpy.init();node=rclpy.create_node('vo_live_check',parameter_overrides=[Parameter('use_sim_time',value=True)])
 subscriptions=[node.create_subscription(Odometry,'/zed2i/vo/odometry',visual.append,qos_profile_sensor_data),node.create_subscription(Odometry,'/odometry/gz',truth.append,qos_profile_sensor_data),node.create_subscription(Odometry,'/mavros/odometry/out',external.append,10)]
 from tf2_msgs.msg import TFMessage
 subscriptions.append(node.create_subscription(TFMessage,'/tf',lambda message:transforms.extend(t for t in message.transforms if t.header.frame_id=='odom' and t.child_frame_id=='base_link'),10))
 from sensor_msgs.msg import Image, CameraInfo
 eyes={eye:[] for eye in ('left','right')}; calibration={}
 for eye in eyes:
  subscriptions.append(node.create_subscription(Image,f'/zed2i/zed_node/{eye}/image_rect_color',lambda message,eye=eye: eyes[eye].append((message.width,message.height,message.header.stamp.sec+message.header.stamp.nanosec*1e-9,message.encoding,message.header.frame_id,int(np.ptp(np.frombuffer(message.data,dtype=np.uint8)[::96])),time.monotonic())),qos_profile_sensor_data))
  subscriptions.append(node.create_subscription(CameraInfo,f'/zed2i/zed_node/{eye}/camera_info',lambda message,eye=eye: calibration.update({eye:message}),qos_profile_sensor_data))
 saved=set()
 def save_preview(message,name):
  if name not in saved:
   from PIL import Image as PILImage
   PILImage.frombytes('RGB',(message.width,message.height),bytes(message.data),'raw','RGB',message.step).save('/tmp/mako_'+name+'.png')
   saved.add(name)
 subscriptions.append(node.create_subscription(Image,'/zed2i/zed_node/left/image_rect_color',lambda message:save_preview(message,'processing_eye'),qos_profile_sensor_data))
 subscriptions.append(node.create_subscription(Image,'/zed2i/zed_node/left/image_rect_color',lambda message:save_preview(message,'pilot_eye'),qos_profile_sensor_data))
 end=time.monotonic()+30
 while time.monotonic()<end and len(external)<50:rclpy.spin_once(node,timeout_sec=.05)
 print('Counts:',len(visual),len(truth),len(external),flush=True)
 assert len(external)>=30,'No healthy visual stream: inspect /tmp/mako_vo_*.log'
 stamps=[m.header.stamp.sec+m.header.stamp.nanosec*1e-9 for m in external];rate=(len(stamps)-1)/(stamps[-1]-stamps[0])
 assert rate>=4,rate
 print('PASS: visual -> MAVROS at',rate,'Hz; pose',external[-1].pose.pose,flush=True)
 for eye,frames in eyes.items():
  expected=(int(os.environ.get('VO_TEST_WIDTH','1280')),int(os.environ.get('VO_TEST_HEIGHT','720')))
  assert len(frames)>=20,(eye,len(frames))
  assert all(frame[:2]==expected and frame[3]=='rgb8' and frame[4]==f'zed2i_{eye}_camera_frame_optical' for frame in frames),eye
  info=calibration[eye]
  assert (info.width,info.height)==expected and info.k[0]>0 and info.k[4]>0,eye
  # Exclude rendering/shader initialization from the steady camera-rate check.
  steady_frames=frames[-30:]
  image_rate=(len(steady_frames)-1)/(steady_frames[-1][2]-steady_frames[0][2])
  assert image_rate>=float(os.environ.get('PILOT_TEST_FPS','30'))*.85,(eye,image_rate)
  print('PASS:',eye,'native RGB and calibration',expected,'at',image_rate,'Hz',flush=True)
 from gz.transport13 import Node as GzNode
 from gz.msgs10.double_pb2 import Double
 from gz.msgs10.world_control_pb2 import WorldControl
 from google.protobuf.text_format import MessageToString
 transport=GzNode();motors=[transport.advertise(f'/model/robot_description/joint/t{i}_joint/cmd_thrust',Double) for i in range(1,7)]
 def sample_camera_memory():
  process=processes[next(i for i,(name,_) in enumerate(commands) if name=='camera_bridge')]
  def resident(pid):
   try:
    status=Path(f'/proc/{pid}/status').read_text().splitlines()
    own=next((int(line.split()[1])/1024 for line in status if line.startswith('VmRSS:')),0)
    children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
    return own+sum(resident(int(child)) for child in children)
   except FileNotFoundError:return 0
  camera_rss.append(resident(process.pid))
 def spin_for(seconds,pattern):
  start=node.get_clock().now().nanoseconds
  deadline=time.monotonic()+seconds*4+5
  while (node.get_clock().now().nanoseconds-start)/1e9 < seconds:
   assert time.monotonic()<deadline,'Simulation clock stalled'
   for motor,value in zip(motors,pattern):motor.publish(Double(data=float(value)))
   rclpy.spin_once(node,timeout_sec=.03)
   sample_camera_memory()
 for name,pattern in [('surge',[-4,-4,4,4,0,0]),('sway',[4,-4,4,-4,0,0]),('heave',[0,0,0,0,3,3])]:
  before_visual=external[-1].pose.pose.position;before_truth=truth[-1].pose.pose.position
  spin_for(1.5,pattern);spin_for(1.5,[0]*6)
  after_visual=external[-1].pose.pose.position;after_truth=truth[-1].pose.pose.position
  delta_visual=[getattr(after_visual,k)-getattr(before_visual,k) for k in ['x','y','z']]
  delta_truth=[getattr(after_truth,k)-getattr(before_truth,k) for k in ['x','y','z']]
  error=sum((a-b)**2 for a,b in zip(delta_visual,delta_truth))**.5
  assert sum(x*x for x in delta_truth)**.5>.02,(name,'No physical movement',delta_truth)
  assert error<.1,(name,error,delta_visual,delta_truth)
  print(name,'PASS: visual displacement',delta_visual,'truth',delta_truth,'error',error,flush=True)
 yaw_start={eye:len(frames) for eye,frames in eyes.items()}
 yaw_truth_start=len(truth)
 yaw_external_start=len(external)
 spin_for(3.0,[12,-12,-12,12,0,0])
 rotating_poses=truth[yaw_truth_start:]
 yaw_angles=[2*np.arctan2(m.pose.pose.orientation.z,m.pose.pose.orientation.w) for m in rotating_poses]
 yaw_stamps=[m.header.stamp.sec+m.header.stamp.nanosec*1e-9 for m in rotating_poses]
 peak_yaw=max(abs(np.diff(np.unwrap(yaw_angles))/np.diff(yaw_stamps)))
 assert peak_yaw>.4,('Yaw test did not rotate fast enough',peak_yaw)
 # Covariance alone previously admitted position errors of up to 18 m.
 # Compare at equal simulation timestamps, including accepted yaw samples.
 def stamp(message):return message.header.stamp.sec+message.header.stamp.nanosec*1e-9
 yaw_errors=[]
 for message in external[yaw_external_start:]:
  reference=min(truth,key=lambda candidate:abs(stamp(candidate)-stamp(message)))
  assert abs(stamp(reference)-stamp(message))<.025
  actual=message.pose.pose.position;expected=reference.pose.pose.position
  yaw_errors.append(sum((getattr(actual,k)-getattr(expected,k))**2 for k in ('x','y','z'))**.5)
 assert yaw_errors and max(yaw_errors)<.15,('Inaccurate yaw pose sent to ArduSub',yaw_errors)
 print('PASS: accepted ExternalNav poses during rapid yaw; max error',max(yaw_errors),'m; rejected tracking updates are not forwarded',flush=True)
 for eye,frames in eyes.items():
  rotating=frames[yaw_start[eye]:]
  assert len(rotating)>=50,(eye,'Camera stalled during yaw',len(rotating))
  assert all(frame[5]>3 for frame in rotating),(eye,'Blank frame during yaw')
  gaps=np.diff([frame[2] for frame in rotating])
  assert max(gaps)<.15,(eye,'Image gap during yaw',max(gaps))
  wall_gaps=np.diff([frame[6] for frame in rotating])
  print('PASS:',eye,'rapid yaw at',peak_yaw,'rad/s;',len(rotating),'nonblank frames; max sim/wall gap',max(gaps),max(wall_gaps),flush=True)
 assert transforms,'Validated odometry TF is missing'
 for transform in transforms:
  transform_stamp=transform.header.stamp.sec+transform.header.stamp.nanosec*1e-9
  reference=min(external,key=lambda message:abs(stamp(message)-transform_stamp))
  assert abs(stamp(reference)-transform_stamp)<.001
  assert all(abs(getattr(transform.transform.translation,k)-getattr(reference.pose.pose.position,k))<1e-8 for k in ('x','y','z'))
 print('PASS: TF contains only validated ExternalNav poses',flush=True)
 spin_for(1.0,[0]*6)
 before=len(external)
 reset=WorldControl(pause=False);reset.reset.all=True
 response=subprocess.run(['gz','service','-s',f'/world/{world_name}/control','--reqtype','gz.msgs.WorldControl','--reptype','gz.msgs.Boolean','--timeout','10000','--req',MessageToString(reset)],capture_output=True,text=True,timeout=15)
 assert 'data: true' in response.stdout,response.stdout
 end=time.monotonic()+20
 while time.monotonic()<end and (len(external)<before+15 or abs(external[-1].pose.pose.position.z+1)>.08):rclpy.spin_once(node,timeout_sec=.05)
 assert len(external)>=before+15 and abs(external[-1].pose.pose.position.x)<.1 and abs(external[-1].pose.pose.position.z+1)<.08
 print('Measured camera bridge + launcher process-tree peak RSS:',max(camera_rss),'MiB',flush=True)
 print('PASS: visual odometry and ExternalNav recover at the initial pose after Reset',flush=True)
 assert len(mavlink_odometry)>=20, ('No MAVLink ODOMETRY received',len(mavlink_odometry))
 for message in mavlink_odometry:
  assert message.frame_id==mavutil.mavlink.MAV_FRAME_LOCAL_FRD
  assert message.child_frame_id==mavutil.mavlink.MAV_FRAME_BODY_FRD
 print('PASS: MAVROS transmitted',len(mavlink_odometry),'MAVLink ODOMETRY messages to isolated FCU endpoint',flush=True)
 node.destroy_node();rclpy.shutdown()
finally:
 stop.set();receiver.join(timeout=2);endpoint.close()
 for process in processes:
  if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
 for process in processes:
  try:process.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
 for log in logs:log.close()
 temporary.cleanup()
