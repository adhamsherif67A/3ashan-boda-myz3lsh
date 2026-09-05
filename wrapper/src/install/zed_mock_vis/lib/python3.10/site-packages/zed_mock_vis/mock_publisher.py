import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField
from geometry_msgs.msg import TransformStamped
import tf2_ros
import numpy as np
import struct

class ZedMockPublisher(Node):
    def __init__(self):
        super().__init__('zed_mock_publisher')

        # 1. Topic Publishers
        self.img_pub = self.create_publisher(Image, '/zed/zed_node/rgb/image_rect_color', 10)
        self.pc_pub = self.create_publisher(PointCloud2, '/zed/zed_node/point_cloud/cloud_registered', 10)

        # 2. Static TF Broadcaster: base_link -> camera_link
        self.tf_broadcaster = tf2_ros.StaticTransformBroadcaster(self)
        self.broadcast_tf()

        # Timer (10 Hz)
        self.timer = self.create_timer(0.1, self.publish_streams)
        self.get_logger().info("ZED Mock Vision Node with TF2 started successfully.")

    def broadcast_tf(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'camera_link'

        # إحداثيات تثبيت الكاميرا: قدام 20 سم وفوق 15 سم بالنسبة لشاسيه الروبوت
        t.transform.translation.x = 0.20
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.15
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform(t)

    def publish_streams(self):
        now = self.get_clock().now().to_msg()

        # بث صورة ملونة وهمية (RGB8)
        img = Image()
        img.header.stamp = now
        img.header.frame_id = 'camera_link'
        img.height = 240
        img.width = 320
        img.encoding = 'rgb8'
        img.step = 320 * 3
        img_array = np.full((240, 320, 3), [30, 144, 255], dtype=np.uint8)
        img.data = img_array.tobytes()
        self.img_pub.publish(img)

        # بث سحابة نقط ثلاثية الأبعاد (PointCloud2)
        pc = PointCloud2()
        pc.header.stamp = now
        pc.header.frame_id = 'camera_link'
        pc.height = 1
        num_points = 200
        pc.width = num_points
        pc.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        pc.is_bigendian = False
        pc.point_step = 12
        pc.row_step = 12 * num_points
        pc.is_dense = True

        points = []
        for i in range(num_points):
            x = 0.5 + (i % 20) * 0.05
            y = -0.5 + (i // 20) * 0.1
            z = 0.1 * np.sin(x * 5)
            points.extend([x, y, z])

        pc.data = struct.pack(f'{len(points)}f', *points)
        self.pc_pub.publish(pc)

def main(args=None):
    rclpy.init(args=args)
    node = ZedMockPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
