import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class DepthSubscriber(Node):
    def __init__(self):
        super().__init__('fake_depth_subscriber')
        # بنعمل سبسكرايبر بيسمع لنفس الموضوع 'depth' اللي بيبعت عليه الفايل الأولاني
        self.subscription = self.create_subscription(
            Float32,
            'depth',
            self.listener_callback,
            10)
            
        self.threshold = 8.0 # الحد الأقصى للعمق (تقدر تغيره براحتك)
        self.get_logger().info('شاشة مراقبة العمق اشتغلت ومستنية القرايات...')

    def listener_callback(self, msg):
        depth = msg.data
        # لو العمق عدى الـ 8 متر، طلع تحذير
        if depth > self.threshold:
            self.get_logger().warning(f'⚠️ تحذير! العمق وصل {depth:.2f} متر، عدينا الحد المسموح!')
        else:
            self.get_logger().info(f'العمق في الأمان: {depth:.2f} متر')

def main(args=None):
    rclpy.init(args=args)
    node = DepthSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
