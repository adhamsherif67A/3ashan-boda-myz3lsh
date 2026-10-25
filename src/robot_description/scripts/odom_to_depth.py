#!/usr/bin/env python3
"""Publish positive-down ROV depth from simulated world odometry."""
import math

import rclpy
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Float32


def depth_from_z(z, surface_z=0.0):
    """Return meters below the water surface; clamp above-surface motion to zero."""
    if not math.isfinite(z) or not math.isfinite(surface_z):
        raise ValueError('ROV and surface heights must be finite')
    return max(0.0, surface_z-z)


class OdomToDepth(Node):
    def __init__(self):
        super().__init__('odom_to_depth')
        self.declare_parameter('source_topic', '/odometry/gz')
        self.declare_parameter('depth_topic', '/rov/depth')
        self.declare_parameter('surface_z', 0.0)
        source = self.get_parameter('source_topic').value
        self.surface_z = float(self.get_parameter('surface_z').value)
        self.publisher = self.create_publisher(
            Float32, self.get_parameter('depth_topic').value, 10)
        self.subscription = self.create_subscription(
            Odometry, source, self._odometry_callback, qos_profile_sensor_data)
        self.get_logger().info(
            f'Publishing positive-down depth on {self.get_parameter("depth_topic").value} '
            f'from {source}; water surface z={self.surface_z:.3f} m')

    def _odometry_callback(self, message):
        try:
            depth = depth_from_z(message.pose.pose.position.z, self.surface_z)
        except ValueError as error:
            self.get_logger().warning(str(error), throttle_duration_sec=2.0)
            return
        output = Float32()
        output.data = float(depth)
        self.publisher.publish(output)


def main():
    rclpy.init()
    node = OdomToDepth()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
