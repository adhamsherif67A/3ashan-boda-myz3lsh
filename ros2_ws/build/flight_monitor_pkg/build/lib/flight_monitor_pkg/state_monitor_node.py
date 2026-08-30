import rclpy
from rclpy.node import Node
from mavros_msgs.msg import State

class FlightStateMonitorNode(Node):
    def __init__(self):
        super().__init__('flight_state_monitor')

        # 1. الاشتراك في التوبيك /mavros/state
        self.state_sub = self.create_subscription(
            State,
            '/mavros/state',
            self.state_callback,
            10
        )

        # متغيرات لحفظ الحالة السابقة لمنع التكرار واكتشاف التغييرات
        self.prev_connected = None
        self.prev_armed = None
        self.prev_mode = None

        self.get_logger().info('Flight State Monitor Node has been started.')

    def state_callback(self, msg: State):
        # التحقق هل حصل أي تغيير في (الاتصال، التسليح، أو المود)
        has_changed = (
            msg.connected != self.prev_connected or
            msg.armed != self.prev_armed or
            msg.mode != self.prev_mode
        )

        if has_changed:
            # تحديث القيم المحفوظة
            self.prev_connected = msg.connected
            self.prev_armed = msg.armed
            self.prev_mode = msg.mode

            # تنسيق الحالات لقراءة بشرية واضحة ومباشرة
            conn_status = "CONNECTED" if msg.connected else "DISCONNECTED"
            arm_status = "ARMED" if msg.armed else "DISARMED"
            mode_status = msg.mode if msg.mode else "UNKNOWN"

            # طباعة الملخص
            summary = (
                f"\n{'='*45}\n"
                f" [FLIGHT STATE UPDATE]\n"
                f"  - Connection : {conn_status}\n"
                f"  - Armed State: {arm_status}\n"
                f"  - Flight Mode: {mode_status}\n"
                f"{'='*45}"
            )
            self.get_logger().info(summary)

def main(args=None):
    rclpy.init(args=args)
    node = FlightStateMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
