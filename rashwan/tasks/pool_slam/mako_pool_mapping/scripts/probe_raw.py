"""Compare raw simulated sensor streams, without changing SLAM inputs."""
import json
import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2
from cv_bridge import CvBridge
class Probe(Node):
 def __init__(self):
  super().__init__('raw_probe');self.b=CvBridge();self.last={};self.f=open('/data/raw_probe.jsonl','a',buffering=1)
  self.create_subscription(Image,'/zed2i/zed_node/left/depth/image_raw',self.depth,1)
  self.create_subscription(Image,'/diagnostic/rgb',self.rgb,1)
  self.create_subscription(Image,'/zed2i/zed_node/left/image_rect_color',lambda m:cv2.imwrite('/data/pilot_rgb.png',self.b.imgmsg_to_cv2(m,'bgr8')) if self.due('pilot',m) else None,1)
  self.create_subscription(PointCloud2,'/zed2i/sim_ros/left/points_raw',self.cloud,1)
 def due(self,key,m):
  t=m.header.stamp.sec+m.header.stamp.nanosec*1e-9
  if t-self.last.get(key,-100)<2:return False
  self.last[key]=t;return True
 def stats(self,key,m,a):
  self.f.write(json.dumps({'kind':key,'stamp':m.header.stamp.sec+m.header.stamp.nanosec*1e-9,'finite':float(np.isfinite(a).mean()),'neginf':float(np.isneginf(a).mean()),'posinf':float(np.isposinf(a).mean()),'min':float(a[np.isfinite(a)].min()) if np.isfinite(a).any() else None,'max':float(a[np.isfinite(a)].max()) if np.isfinite(a).any() else None})+'\n')
 def depth(self,m):
  if self.due('depth',m):
   a=self.b.imgmsg_to_cv2(m);self.stats('depth',m,a);np.save('/data/depth.npy',a)
 def cloud(self,m):
  if self.due('cloud',m):
   fields={f.name:f.offset for f in m.fields}
   a=np.ndarray((m.height,m.width),dtype='<f4',buffer=m.data,offset=fields['x'],strides=(m.row_step,m.point_step));self.stats('cloud_x',m,a)
 def rgb(self,m):
  if self.due('rgb',m):cv2.imwrite('/data/raw_rgb.png',self.b.imgmsg_to_cv2(m,'bgr8'))
rclpy.init();n=Probe()
try:rclpy.spin(n)
except KeyboardInterrupt:pass
finally:n.f.close();rclpy.try_shutdown()
