#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from mavros_msgs.msg import ManualControl, State
from mavros_msgs.srv import CommandBool, SetMode


def clamp(value, low, high):
    return max(low, min(high, value))


class ROVControllerNode(Node):
    def __init__(self):
        super().__init__('rov_controller_node')

        self.is_armed = False
        self.current_mode = ""

        # --- Digital Buttons Mapping ---
        self.BTN_TRIANGLE = 0   # Depth Hold (ALT_HOLD)
        self.BTN_CIRCLE = 1     # Guided Mode
        self.BTN_X = 2          # Manual Mode
        self.BTN_SQUARE = 3     # Stabilize Mode
        self.BTN_START = 9      # Arm / Disarm Toggle

        # Edge Detection Memory
        self.prev_start_btn = 0
        self.prev_triangle_btn = 0
        self.prev_circle_btn = 0
        self.prev_x_btn = 0
        self.prev_square_btn = 0

        # --- Analog Axes Mapping ---
        self.AXIS_SWAY = 0    # Left Stick Left/Right (-1.0 to 1.0)
        self.AXIS_SURGE = 1   # Left Stick Up/Down (-1.0 to 1.0)
        self.AXIS_HEAVE = 2   # Right Stick Up/Down (-1.0 to 1.0)
        self.AXIS_YAW = 3     # Right Stick Left/Right (-1.0 to 1.0)

        # Control States (-1.0 to 1.0)
        self.target_surge = 0.0
        self.target_sway = 0.0
        self.target_heave = 0.0
        self.target_yaw = 0.0

        # ROS 2 Subscriptions & Publishers
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        self.state_sub = self.create_subscription(State, '/mavros/state', self.state_callback, 10)
        self.manual_pub = self.create_publisher(ManualControl, '/mavros/manual_control/send', 10)

        # Service Clients
        self.arm_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')

        # Timer: Continuous control publishing at 20 Hz (50 ms)
        self.timer = self.create_timer(0.05, self.publish_control)

        self.get_logger().info('ROV Controller Node initialized [Normalized -1000 to 1000]...')

    def state_callback(self, msg: State):
        self.is_armed = msg.armed
        self.current_mode = msg.mode

    def joy_callback(self, msg: Joy):
        num_buttons = len(msg.buttons)
        required_buttons = max(self.BTN_START, self.BTN_TRIANGLE, self.BTN_CIRCLE, self.BTN_X, self.BTN_SQUARE)
        
        if num_buttons > required_buttons:
            self.handle_arming(msg.buttons)
            self.handle_flight_modes(msg.buttons)

        num_axes = len(msg.axes)
        if self.AXIS_SURGE < num_axes:
            self.target_surge = float(msg.axes[self.AXIS_SURGE])
        if self.AXIS_SWAY < num_axes:
            self.target_sway = float(msg.axes[self.AXIS_SWAY])
        if self.AXIS_HEAVE < num_axes:
            self.target_heave = float(msg.axes[self.AXIS_HEAVE])
        if self.AXIS_YAW < num_axes:
            self.target_yaw = float(msg.axes[self.AXIS_YAW])

    def publish_control(self):
        msg = ManualControl()
        msg.header.stamp = self.get_clock().now().to_msg()

        # MAVROS manual_control/send يتوقع أعداد من (-1000.0 إلى 1000.0)
        # Note: معظم الـ Joysticks بتعطي -1.0 للأمام، عشان كده بنعكس إشارة Surge
        msg.x = float(clamp(-self.target_surge * 1000.0, -1000.0, 1000.0))  # Surge
        msg.y = float(clamp(self.target_sway * 1000.0, -1000.0, 1000.0))   # Sway
        msg.z = float(clamp(self.target_heave * 1000.0, -1000.0, 1000.0))  # Heave
        msg.r = float(clamp(self.target_yaw * 1000.0, -1000.0, 1000.0))    # Yaw

        msg.buttons = 0  # Bitmask للأزرار لتجنب الـ Uninitialized field

        self.manual_pub.publish(msg)

    def handle_arming(self, buttons):
        current_start = buttons[self.BTN_START]
        if current_start == 1 and self.prev_start_btn == 0:
            req = CommandBool.Request()
            req.value = not self.is_armed
            
            if self.arm_client.wait_for_service(timeout_sec=1.0):
                future = self.arm_client.call_async(req)
                future.add_done_callback(self.arm_response_callback)
            else:
                self.get_logger().warn('Arming service (/mavros/cmd/arming) unavailable!')
                
        self.prev_start_btn = current_start

    def arm_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info('Arming/Disarming command executed successfully.')
            else:
                self.get_logger().error('Arming request was rejected!')
        except Exception as e:
            self.get_logger().error(f'Arming service call failed: {e}')

    def handle_flight_modes(self, buttons):
        if buttons[self.BTN_TRIANGLE] == 1 and self.prev_triangle_btn == 0:
            self.set_mode('ALT_HOLD')
        elif buttons[self.BTN_CIRCLE] == 1 and self.prev_circle_btn == 0:
            self.set_mode('GUIDED')
        elif buttons[self.BTN_X] == 1 and self.prev_x_btn == 0:
            self.set_mode('MANUAL')
        elif buttons[self.BTN_SQUARE] == 1 and self.prev_square_btn == 0:
            self.set_mode('STABILIZE')

        self.prev_triangle_btn = buttons[self.BTN_TRIANGLE]
        self.prev_circle_btn = buttons[self.BTN_CIRCLE]
        self.prev_x_btn = buttons[self.BTN_X]
        self.prev_square_btn = buttons[self.BTN_SQUARE]

    def set_mode(self, custom_mode: str):
        req = SetMode.Request()
        req.custom_mode = custom_mode
        
        if self.mode_client.wait_for_service(timeout_sec=1.0):
            self.mode_client.call_async(req)
            self.get_logger().info(f'Requested flight mode change to: {custom_mode}')
        else:
            self.get_logger().warn('SetMode service (/mavros/set_mode) unavailable!')


def main(args=None):
    rclpy.init(args=args)
    node = ROVControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
