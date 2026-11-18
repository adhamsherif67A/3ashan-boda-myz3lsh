import os,sys,time,json,collections
os.environ['QT_QPA_PLATFORM']='xcb'
sys.path.insert(0,'/opt/mako_ws/gui')
from PyQt5.QtWidgets import QApplication
from mako_station.app import PilotWindow
from mako_station.simulation import SimulationSession,SessionThread
app=QApplication([]);w=PilotWindow(start_workers=False)
s=SimulationSession(domain=85,instance=14,outputs=(25050,25051))
w.manager=SessionThread(w.session_state.emit,w.log_message.emit,s);w.workers_started=True;w.manager.start();w.ros.domain=85
import rclpy
from rtabmap_msgs.msg import Info
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import QoSProfile,DurabilityPolicy
rclpy.init();monitor=rclpy.create_node('native_slam_render_probe');infos=[];grids=[]
monitor.create_subscription(Info,'/rtabmap/info',infos.append,10)
monitor.create_subscription(OccupancyGrid,'/rtabmap/map',grids.append,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
latency=[];paint_age=[];paint_count=[0];paint_begin=[None];paint_last=[None]
paint_original=w.canvas.paintEvent
def paint(event):
 stamp=w.canvas.stamp
 fresh=stamp!=w.canvas.painted_stamp and w.canvas.image is not None
 paint_original(event)
 if fresh:
  now=time.monotonic();paint_count[0]+=1;paint_begin[0]=paint_begin[0] or now;paint_last[0]=now;paint_age.append((now-stamp)*1000)
w.canvas.paintEvent=paint
counts=collections.Counter();original=w.ros.frame
clock=[]
def frame(msg,name,view=None):
 counts[name]+=1
 if clock and name=='main':latency.append(max(0.,clock[-1][1]+time.monotonic()-clock[-1][0]-msg.header.stamp.sec-msg.header.stamp.nanosec/1e9))
 original(msg,name,view)
def odom(msg):clock.append((time.monotonic(),msg.header.stamp.sec+msg.header.stamp.nanosec/1e9))
w.ros.frame=frame;w.ros.odometry=odom
spawn=s.processes.spawn
profile=sys.argv[1]
def launch(name,args,*other):
 if name=='Gazebo' and profile=='gpu30':args=args+['pilot_fps:=30','camera_fps:=15']
 elif name=='Gazebo' and profile not in ('baseline','gpu','gpu-ocean'):args=args+['performance_profile:='+profile]
 return spawn(name,args,*other)
s.processes.spawn=launch
w.world.setCurrentIndex(w.world.findData(os.environ.get('BENCH_WORLD','pool.world')))
w.slam.setChecked(True);w.ros.start();w.showFullScreen()
def pump(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  app.processEvents();rclpy.spin_once(monitor,timeout_sec=0);time.sleep(.002)
  if w.phase=='Error':raise RuntimeError(w.log_box.toPlainText())
try:
 w.action('start');end=time.monotonic()+120
 while time.monotonic()<end:
  pump(.1)
  f,t=w.ros.snapshot()
  if t.get('connected') and 'bottom' in f and 'main' in f:break
 else:raise RuntimeError('not ready')
 pump(8);w.open_rviz();pump(12);counts.clear();clock.clear();latency.clear();paint_age.clear();paint_count[0]=0;paint_begin[0]=None;paint_last[0]=None;begin=time.monotonic();pump(20);elapsed=time.monotonic()-begin
 f,t=w.ros.snapshot()
 result={'world':os.environ.get('BENCH_WORLD','pool.world'),'slam':True,'mapping_updates':len(infos),'grid_size':[grids[-1].info.width,grids[-1].info.height] if grids else None,'rviz_running':bool(w.external_tools.get('RViz') and w.external_tools['RViz'].state()),'renderer':os.environ.get('MAKO_GPU_VIDEO','0'),'painted_fps':(paint_count[0]-1)/(paint_last[0]-paint_begin[0]) if paint_count[0]>1 else 0,'receive_to_paint_p95_ms':sorted(paint_age)[int(len(paint_age)*.95)] if paint_age else None,'latency_ms_p50': sorted(latency)[len(latency)//2]*1000 if latency else None,'latency_ms_p95': sorted(latency)[int(len(latency)*.95)]*1000 if latency else None,'profile':profile,'fps_wall':{k:v/elapsed for k,v in counts.items()},'size':{k:[v[0].width(),v[0].height()] for k,v in f.items()},'connected':t.get('connected'),'sim_speed':(clock[-1][1]-clock[0][1])/(clock[-1][0]-clock[0][0]) if len(clock)>1 else None,'session':str(s.directory)}
 assert infos and grids and len(grids[-1].data)>0,'No SLAM map';print(json.dumps(result),flush=True);open('/opt/mako_ws/fish-native-slam-result.json','w').write(json.dumps(result,indent=2))
 w.ros.snapshot()[0]['main'][0].save('/opt/mako_ws/fish-first-person-camera.png')
 w.switch_view('Third person');pump(3);w.ros.snapshot()[0]['main'][0].save('/opt/mako_ws/fish-third-person-camera.png')
 from Xlib import display,X
 from PIL import Image
 d=display.Display();root=d.screen().root
 own=d.create_resource_object('window',int(w.winId()));g=own.get_geometry();raw=own.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff);Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX').save('/opt/mako_ws/fish-station-desktop.png')
 for wid in root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'),X.AnyPropertyType).value:
  win=d.create_resource_object('window',int(wid))
  if 'slam_live.rviz' in str(win.get_wm_name()):
   g=win.get_geometry();raw=win.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff);Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX').save('/opt/mako_ws/fish-live-slam.png');break
 d.close()
finally:
 w.stop_rviz();pump(4);w.closing=True;w.manager.request('close');end=time.monotonic()+15
 while w.manager.is_alive() and time.monotonic()<end:app.processEvents();time.sleep(.05)
 s.stop();w.ros.stop();w.finished=True;w.close()
