#!/usr/bin/env python3
"""Match Gazebo RGB-D pixel-center calibration to its native XYZ depth geometry."""
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo


def correct_pixel_centers(message, offset=0.5):
    """Translate native texture-center intrinsics to integer-index image pixels."""
    k = list(message.k)
    p = list(message.p)
    k[2] -= offset
    k[5] -= offset
    p[2] -= offset
    p[6] -= offset
    message.k = k
    message.p = p
    return message


class SimRgbdCameraInfo(Node):
    """Preserve timestamps and optical frames while correcting simulated metadata."""

    def __init__(self):
        super().__init__('sim_rgbd_camera_info')
        self.offset = self.declare_parameter('pixel_center_offset', 0.5).value
        self.publisher = self.create_publisher(
            CameraInfo, '/zed2i/rgbd/left/camera_info', 1)
        self.create_subscription(
            CameraInfo, '/zed2i/rgbd/left/camera_info_raw', self.forward,
            qos_profile_sensor_data)

    def forward(self, message):
        self.publisher.publish(correct_pixel_centers(message, self.offset))


def main():
    rclpy.init()
    node = SimRgbdCameraInfo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
