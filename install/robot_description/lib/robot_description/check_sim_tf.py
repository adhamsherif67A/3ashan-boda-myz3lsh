#!/usr/bin/env python3
"""Validate live simulation TF and sensor headers before adding algorithms."""
import argparse
import sys
import time

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.time import Time
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CameraInfo, Image, Imu, PointCloud2
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformException, TransformListener


class SimulationFrames(Node):
    def __init__(self):
        super().__init__('check_sim_tf')
        self.buffer = Buffer(node=self)
        self.listener = TransformListener(self.buffer, self)
        self.messages = {}
        self.subscriptions_kept = []
        self.parents = {}
        self.clock_samples = set()
        topics = {
            '/odometry/gz': Odometry, '/imu/data': Imu,
            '/zed2i/zed_node/left/image_rect_color': Image,
            '/zed2i/zed_node/right/image_rect_color': Image,
            '/zed2i/zed_node/left/camera_info': CameraInfo,
            '/zed2i/zed_node/right/camera_info': CameraInfo,
            '/zed2i/zed_node/depth/depth_registered': Image,
            '/zed2i/zed_node/point_cloud/cloud_registered': PointCloud2,
        }
        self.topics = topics
        for topic, message_type in topics.items():
            self.subscriptions_kept.append(self.create_subscription(
                message_type, topic, lambda msg, t=topic: self.record(t, msg),
                qos_profile_sensor_data))
        self.subscriptions_kept.append(self.create_subscription(
            Clock, '/clock', self.clock_callback, qos_profile_sensor_data))
        self.subscriptions_kept.append(self.create_subscription(
            TFMessage, '/tf', self.tf_callback, qos_profile_sensor_data))

        self.subscriptions_kept.append(self.create_subscription(
            TFMessage, '/tf_static', self.tf_callback,
            QoSProfile(depth=100, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                       reliability=ReliabilityPolicy.RELIABLE)))

    def record(self, topic, msg):
        previous = self.messages.get(topic)
        if previous and self.buffer.can_transform(
                'odom', previous.header.frame_id, Time.from_msg(previous.header.stamp)):
            return
        self.messages[topic] = msg

    def clock_callback(self, msg):
        self.clock_samples.add((msg.clock.sec, msg.clock.nanosec))

    def tf_callback(self, msg):
        for transform in msg.transforms:
            self.parents.setdefault(transform.child_frame_id, set()).add(transform.header.frame_id)

    def problems(self):
        issues = ['No data on ' + t for t in self.topics if t not in self.messages]
        if len(self.clock_samples) < 2:
            issues.append('/clock is not advancing')
        for child, parents in self.parents.items():
            if len(parents) > 1:
                issues.append(f'Multiple TF parents for {child}: {sorted(parents)}')
        for frame in ['base_link', 'rov_base_link', 'center_body_link', 'imu_link',
                      'imu_ros_link', 'bar30_link', 'zed2i_camera_link', 'zed2i_camera_center',
                      'zed2i_left_camera_frame', 'zed2i_right_camera_frame',
                      'zed2i_left_camera_frame_optical', 'zed2i_right_camera_frame_optical',
                      't1_link', 't2_link', 't3_link', 't4_link', 't5_link', 't6_link']:
            try:
                self.buffer.lookup_transform('odom', frame, Time())
            except TransformException:
                issues.append('Missing odom -> ' + frame)
        for topic, msg in self.messages.items():
            if not msg.header.frame_id:
                issues.append('Empty frame_id on ' + topic)
                continue
            try:
                self.buffer.lookup_transform('odom', msg.header.frame_id,
                                             Time.from_msg(msg.header.stamp))
            except TransformException:
                issues.append('No transform at the sensor timestamp on ' + topic)
        imu = self.messages.get('/imu/data')
        if imu and imu.header.frame_id != 'imu_ros_link':
            issues.append('ROS IMU has wrong frame: ' + imu.header.frame_id)
        for eye in ['left', 'right']:
            for suffix in ['image_rect_color', 'camera_info']:
                msg = self.messages.get('/zed2i/zed_node/' + eye + '/' + suffix)
                if msg and msg.header.frame_id != 'zed2i_' + eye + '_camera_frame_optical':
                    issues.append('Wrong ' + eye + ' optical frame on ' + suffix)
        cloud = self.messages.get('/zed2i/zed_node/point_cloud/cloud_registered')
        if cloud and cloud.header.frame_id != 'zed2i_left_camera_frame':
            issues.append('Gazebo cloud XYZ must use the left camera body frame')
        odom = self.messages.get('/odometry/gz')
        if odom and (odom.header.frame_id != 'odom' or odom.child_frame_id != 'base_link'):
            issues.append('Odometry must describe odom -> base_link')
        try:
            t = self.buffer.lookup_transform('rov_base_link', 'zed2i_left_camera_frame_optical', Time())
            q = t.transform.rotation
            # The optical forward vector (local Z) must coincide with body +X.
            forward = (2*(q.x*q.z + q.w*q.y), 2*(q.y*q.z - q.w*q.x),
                       1-2*(q.x*q.x + q.y*q.y))
            if any(abs(a-b) > 1e-6 for a, b in zip(forward, (1, 0, 0))):
                issues.append('Camera does not face rov_base_link +X')
        except TransformException:
            pass  # Missing tree edges are reported above.
        return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=30.0)
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = SimulationFrames()
    deadline = time.monotonic() + args.timeout
    issues = ['Waiting for simulation']
    try:
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            issues = node.problems()
            if not issues:
                print('PASS: connected odom/body/sensor TF, optical axes, sensor timestamps, advancing /clock.')
                return 0
        for issue in sorted(set(issues)):
            print('FAIL: ' + issue, file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
