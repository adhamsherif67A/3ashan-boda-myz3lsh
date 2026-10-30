"""Read-only RGB/depth feature diagnostic for an active mapping session."""
import json
from pathlib import Path
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rtabmap_msgs.msg import RGBDImage
from cv_bridge import CvBridge

class Probe(Node):
    def __init__(self):
        super().__init__('pool_image_probe');self.bridge=CvBridge();self.previous=-10.
        self.file=Path('/data/image_probe.jsonl').open('a',buffering=1)
        self.create_subscription(RGBDImage,'/pool_mapping/rgbd_image',self.image,1)
    def image(self,msg):
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        if stamp-self.previous<2:return
        self.previous=stamp
        gray=self.bridge.imgmsg_to_cv2(msg.rgb,'mono8')[::2,::2]
        depth=self.bridge.imgmsg_to_cv2(msg.depth,'passthrough')[::2,::2]
        valid=np.isfinite(depth)&(depth>.2)&(depth<14)
        row={'stamp':stamp,'gray_min':int(gray.min()),'gray_max':int(gray.max()),
             'gray_std':float(gray.std()),'depth_valid_fraction':float(valid.mean()),'depth_encoding':msg.depth.encoding, 'finite_fraction':float(np.isfinite(depth).mean()), 'nan_fraction':float(np.isnan(depth).mean()), 'posinf_fraction':float(np.isposinf(depth).mean()), 'neginf_fraction':float(np.isneginf(depth).mean()), 'finite_min':float(depth[np.isfinite(depth)].min()) if np.isfinite(depth).any() else None, 'finite_max':float(depth[np.isfinite(depth)].max()) if np.isfinite(depth).any() else None}
        for threshold in [.04,.01,.005]:
            keys=cv2.SIFT_create(contrastThreshold=threshold).detect(gray)
            row['sift_'+str(threshold)]=len(keys)
        keys=cv2.goodFeaturesToTrack(gray,2000,.0001,5)
        row['gftt']=0 if keys is None else len(keys)
        if keys is not None:
            indices=np.round(keys[:,0,:]).astype(int)
            row['gftt_with_depth']=int(sum(valid[min(y,valid.shape[0]-1),min(x,valid.shape[1]-1)] for x,y in indices))
        self.file.write(json.dumps(row)+'\n')
        cv2.imwrite('/data/probe_rgb.png',gray)

if __name__=='__main__':
    rclpy.init();node=Probe()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.file.close();node.destroy_node();rclpy.try_shutdown()
