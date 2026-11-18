#!/usr/bin/env python3
"""Label Gazebo X-forward cloud XYZ with its matching camera body frame.

Some Harmonic RGB-D sensors label unrotated XYZ with optical_frame_id.
Only the header is corrected; point bytes, colors and timestamps are preserved.
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2


class CloudFrameRelay(Node):
    def __init__(self):
        super().__init__('cloud_frame_relay')
        self.qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.publisher_qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)
        self.inputs = {}
        self.outputs = {}
        for eye in ('left', 'right'):
            topics = [f'/zed2i/zed_node/{eye}/points']
            if eye == 'left':
                topics.append('/zed2i/zed_node/point_cloud/cloud_registered')
            self.outputs[eye] = [self.create_publisher(PointCloud2, topic, self.publisher_qos) for topic in topics]
        self.timer = self.create_timer(0.25, self.refresh_subscriptions)

    def refresh_subscriptions(self):
        for eye, publishers in self.outputs.items():
            wanted = any(p.get_subscription_count() for p in publishers)
            if wanted and eye not in self.inputs:
                self.inputs[eye] = self.create_subscription(
                    PointCloud2, f'/zed2i/sim_ros/{eye}/points_raw',
                    lambda msg, e=eye: self.forward(e, msg), self.qos)
            elif not wanted and eye in self.inputs:
                self.destroy_subscription(self.inputs.pop(eye))

    def forward(self, eye, message):
        message.header.frame_id = f'zed2i_{eye}_camera_frame'
        for publisher in self.outputs[eye]:
            if publisher.get_subscription_count():
                publisher.publish(message)


def main():
    rclpy.init()
    node = CloudFrameRelay()
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
