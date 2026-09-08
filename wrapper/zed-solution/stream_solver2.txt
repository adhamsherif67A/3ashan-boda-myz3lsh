cat << 'EOF' > ~/ros2_ws/zed_sim_feed.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
import sensor_msgs_py.point_cloud2 as pc2
from std_msgs.msg import Header
import numpy as np

class ZedFullSim(Node):
    def __init__(self):
        super().__init__('zed_full_sim')
        self.pub_img = self.create_publisher(Image, '/zed/zed_node/left/image_rect_color', 10)
        self.pub_info = self.create_publisher(CameraInfo, '/zed/zed_node/left/camera_info', 10)
        self.pub_cloud = self.create_publisher(PointCloud2, '/zed/zed_node/point_cloud/cloud_registered', 10)
        self.timer = self.create_timer(0.1, self.publish_all)

        points = []
        for x in np.linspace(0.5, 3.0, 30):
            for y in np.linspace(-1.0, 1.0, 30):
                points.append([x, y, -0.2])
        for z in np.linspace(-0.2, 0.4, 15):
            for y in np.linspace(-0.3, 0.3, 15):
                points.append([1.5, y, z])
        self.points = points

    def publish_all(self):
        now = self.get_clock().now().to_msg()
        h_frame = 'zed_left_camera_frame_optical'

        header = Header(stamp=now, frame_id='base_link')
        cloud_msg = pc2.create_cloud_xyz32(header, self.points)
        self.pub_cloud.publish(cloud_msg)

        h, w = 360, 640
        frame = np.full((h, w, 3), 180, dtype=np.uint8)
        frame[160:200, 280:360] = [50, 50, 220]
        
        img = Image()
        img.header.stamp = now
        img.header.frame_id = h_frame
        img.height, img.width = h, w
        img.encoding = 'bgr8'
        img.step = w * 3
        img.data = frame.tobytes()
        self.pub_img.publish(img)

        info = CameraInfo()
        info.header = img.header
        info.height, info.width = h, w
        info.distortion_model = 'plumb_bob'
        info.k = [350.0, 0.0, 320.0, 0.0, 350.0, 180.0, 0.0, 0.0, 1.0]
        info.p = [350.0, 0.0, 320.0, 0.0, 0.0, 350.0, 180.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.pub_info.publish(info)

def main():
    rclpy.init()
    rclpy.spin(ZedFullSim())

if __name__ == '__main__':
    main()
EOF
