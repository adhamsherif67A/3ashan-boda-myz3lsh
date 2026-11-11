#!/usr/bin/env python3
"""Manually verify RGB-D mapping in an isolated ROS domain without a vehicle."""
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import CameraInfo, Image, PointCloud2
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def main():
    """Feed textured images and a depth plane; require an occupied map output."""
    os.environ.setdefault('ROS_DOMAIN_ID', '159')
    if os.environ['ROS_DOMAIN_ID'] in ('0', '42'):
        raise SystemExit('Use an isolated ROS_DOMAIN_ID such as 159')
    os.environ.setdefault('ROS_LOG_DIR', '/tmp/mx-mapping-fixture-ros')
    directory = Path(tempfile.mkdtemp(prefix='mx-mapping-check-'))
    log = (directory / 'mapping.log').open('w')
    process = subprocess.Popen([
        'ros2', 'launch', 'robot_mapping', 'mapping.launch.py',
        'use_sim_time:=false', 'database_path:=' + str(directory / 'map.db'),
    ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    rclpy.init()
    node = Node('mapping_fixture')
    broadcaster = StaticTransformBroadcaster(node)
    transform = TransformStamped()
    transform.header.frame_id = 'base_link'
    transform.child_frame_id = 'fixture_optical'
    transform.transform.rotation.x = -.5
    transform.transform.rotation.y = .5
    transform.transform.rotation.z = -.5
    transform.transform.rotation.w = .5
    body = TransformStamped()
    body.header.frame_id = 'odom'
    body.child_frame_id = 'base_link'
    body.transform.rotation.w = 1.
    broadcaster.sendTransform([transform, body])
    topics = '/zed2i/rgbd/left/'
    rgb_pub = node.create_publisher(Image, topics + 'image_rect_color', 1)
    depth_pub = node.create_publisher(Image, topics + 'depth/image_raw', 1)
    info_pub = node.create_publisher(CameraInfo, topics + 'camera_info', 1)
    odom_pub = node.create_publisher(Odometry, '/mavros/odometry/out', 1)
    output = []
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(PointCloud2, '/rtabmap/cloud_map',
                             lambda message: output.append(message), qos)
    texture = np.random.default_rng(5).integers(
        0, 256, (240, 320, 3), dtype=np.uint8).tobytes()
    plane = np.full((240, 320), 2., dtype=np.float32).tobytes()
    try:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            assert process.poll() is None, 'Mapper exited: ' + str(directory)
            rgb = Image()
            rgb.header.stamp = node.get_clock().now().to_msg()
            rgb.header.frame_id = 'fixture_optical'
            rgb.width, rgb.height = 320, 240
            rgb.encoding, rgb.step, rgb.data = 'rgb8', 960, texture
            depth = Image()
            depth.header = rgb.header
            depth.width, depth.height = 320, 240
            depth.encoding, depth.step, depth.data = '32FC1', 1280, plane
            info = CameraInfo()
            info.header = rgb.header
            info.width, info.height = 320, 240
            info.k = [250., 0., 160., 0., 250., 120., 0., 0., 1.]
            info.p = [250., 0., 160., 0., 0., 250., 120., 0., 0., 0., 1., 0.]
            info.distortion_model = 'plumb_bob'
            info.d = [0.] * 5
            odom = Odometry()
            odom.header.stamp = rgb.header.stamp
            odom.header.frame_id, odom.child_frame_id = 'odom', 'base_link'
            odom.pose.pose.orientation.w = 1.
            for i in range(6):
                odom.pose.covariance[i * 7] = .001
                odom.twist.covariance[i * 7] = .01
            odom_pub.publish(odom)
            info_pub.publish(info)
            depth_pub.publish(depth)
            rgb_pub.publish(rgb)
            rclpy.spin_once(node, timeout_sec=.1)
            if output and output[-1].width * output[-1].height > 0:
                print('PASS: RGB-D produced a 3D map with', output[-1].width,
                      'points. Logs/database:', directory)
                break
        else:
            raise AssertionError('No map output; inspect ' + str(directory))
    finally:
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        node.destroy_node()
        rclpy.shutdown()
        log.close()


if __name__ == '__main__':
    main()
