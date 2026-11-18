"""Read the physical controller and control outputs without injecting commands."""
import json,time
import rclpy
from sensor_msgs.msg import Joy
from nav_msgs.msg import Odometry
from mavros_msgs.msg import State,ManualControl
from rclpy.qos import qos_profile_sensor_data
rclpy.init();node=rclpy.create_node('fish_gamepad_check');data={};counts={};ranges={}
def observe(name,msg):
 counts[name]=counts.get(name,0)+1
 if name=='joy':
  data[name]={'axes':list(msg.axes),'buttons':list(msg.buttons)}
  for i,v in enumerate(msg.axes):
   lo,hi=ranges.get(str(i),(v,v));ranges[str(i)]=[min(lo,v),max(hi,v)]
 elif name=='state':data[name]={'connected':msg.connected,'armed':msg.armed,'mode':msg.mode}
 elif name=='odom':
  p=msg.pose.pose.position;data.setdefault('first_position',[p.x,p.y,p.z]);data[name]=[p.x,p.y,p.z]
 else:
  data[name]={k:getattr(msg,k) for k in ['x','y','z','r','s','t']}
  for k,v in data[name].items():
   lo,hi=ranges.get('manual_'+k,(v,v));ranges['manual_'+k]=[min(lo,v),max(hi,v)]
subs=[node.create_subscription(t,topic,lambda msg,n=name:observe(n,msg),qos_profile_sensor_data) for t,topic,name in [(Odometry,'/odometry/gz','odom'),(Joy,'/joy','joy'),(State,'/mavros/state','state'),(ManualControl,'/mavros/manual_control/send','manual')]]
end=time.monotonic()+20
while time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.1)
result={'counts':counts,'last':data,'physical_axes_ranges':ranges};print(json.dumps(result,indent=2));node.destroy_node();rclpy.shutdown()
