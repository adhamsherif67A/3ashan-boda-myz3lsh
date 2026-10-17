"""Reject tracking failures and malformed odometry rather than feeding EKF3."""
import importlib.util
import unittest
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
