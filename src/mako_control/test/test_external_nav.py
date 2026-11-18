"""Reject tracking failures and malformed odometry rather than feeding EKF3."""
import importlib.util
import unittest
import math
from pathlib import Path
from nav_msgs.msg import Odometry
spec=importlib.util.spec_from_file_location('external_nav',Path(__file__).resolve().parents[1]/'scripts/gz_odom_to_mavros.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ExternalNav(unittest.TestCase):
    def message(self):
        msg=Odometry();msg.header.frame_id='odom';msg.child_frame_id='base_link'
        msg.header.stamp.sec=10;msg.pose.pose.orientation.w=1.0
        for i in range(6):msg.pose.covariance[i*7]=.001;msg.twist.covariance[i*7]=.01
        return msg
    def validate(self,msg):return module.validation_error(msg,10_100_000_000,require_covariance=True)
    def test_valid_body_odometry(self):self.assertIsNone(self.validate(self.message()))
    def test_wrong_frame_is_not_relabelled(self):
        msg=self.message();msg.child_frame_id='zed2i_camera_center';self.assertIsNotNone(self.validate(msg))
    def test_tracking_failure(self):
        msg=self.message();msg.pose.covariance[0]=9999.0;self.assertIsNotNone(self.validate(msg))
        msg=self.message();msg.pose.pose.orientation.w=0.0;self.assertIsNotNone(self.validate(msg))
    def test_stale_and_future_data(self):
        for stamp in [8,11]:
            msg=self.message();msg.header.stamp.sec=stamp;self.assertIsNotNone(self.validate(msg))
    def test_missing_covariance(self):
        msg=self.message();msg.pose.covariance=[0.0]*36;self.assertIsNotNone(self.validate(msg))
    def test_nonfinite_covariance(self):
        msg=self.message();msg.twist.covariance[3]=float('nan');self.assertIsNotNone(self.validate(msg))
    def test_low_variance_position_jump(self):
        previous=self.message();msg=self.message();msg.header.stamp.nanosec=66_000_000
        msg.pose.pose.position.x=.339
        self.assertIsNone(self.validate(msg))
        self.assertIsNotNone(module.motion_error(msg,previous,2.0,3.0))
    def test_outage_does_not_authorize_large_jump(self):
        previous=self.message();msg=self.message();msg.header.stamp.sec=30
        msg.pose.pose.position.x=18.5
        self.assertIsNotNone(module.motion_error(msg,previous,2.0,3.0))
    def test_regular_motion_and_quaternion_sign(self):
        previous=self.message();msg=self.message();msg.header.stamp.nanosec=100_000_000
        msg.pose.pose.position.x=.15;msg.pose.pose.orientation.w=-1.0
        self.assertIsNone(module.motion_error(msg,previous,2.0,3.0))
    def test_orientation_jump(self):
        previous=self.message();msg=self.message();msg.header.stamp.nanosec=100_000_000
        msg.pose.pose.orientation.z=math.sin(.5);msg.pose.pose.orientation.w=math.cos(.5)
        self.assertIsNotNone(module.motion_error(msg,previous,2.0,3.0))
    def test_reset_and_ground_truth(self):
        msg=self.message();msg.pose.pose.position.x=18.5
        self.assertIsNone(module.motion_error(msg,None,2.0,3.0))
        self.assertIsNone(module.motion_error(msg,self.message()))
