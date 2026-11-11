#!/usr/bin/env python3
"""Real ROV: relay the ZED wrapper pose (/zed/zed_node/pose) to MAVROS vision pose and odometry."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry


class ZedToMavros(Node):

    def __init__(self):
        super().__init__('zed_to_mavros_pose')

        self.sub = self.create_subscription(
            PoseStamped,
            '/zed/zed_node/pose',
            self.callback,
            10
        )

        self.pub = self.create_publisher(
            PoseStamped,
            '/mavros/vision_pose/pose',
            10
        )
        self.odom_pub = self.create_publisher(
            Odometry,
            '/mavros/odometry/in',
            10
        )

        self.get_logger().info("ZED → MAVROS bridge started (vision_pose + odometry/in)")

    def callback(self, msg):
        # Keep pose topic for compatibility.
        pose_msg = PoseStamped()
        pose_msg.header = msg.header
        pose_msg.header.frame_id = "map"
        pose_msg.pose = msg.pose
        self.pub.publish(pose_msg)

        # Feed MAVROS odometry input, which is more robust for EKF fusion.
        odom_msg = Odometry()
        odom_msg.header = msg.header
        odom_msg.header.frame_id = "map"
        odom_msg.child_frame_id = "base_link"
        odom_msg.pose.pose = msg.pose
        odom_msg.twist.twist.linear.x = 0.0
        odom_msg.twist.twist.linear.y = 0.0
        odom_msg.twist.twist.linear.z = 0.0
        odom_msg.twist.twist.angular.x = 0.0
        odom_msg.twist.twist.angular.y = 0.0
        odom_msg.twist.twist.angular.z = 0.0
        self.odom_pub.publish(odom_msg)


def main():
    rclpy.init()
    node = ZedToMavros()
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
