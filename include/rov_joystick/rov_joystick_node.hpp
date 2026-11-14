#ifndef ROV_JOYSTICK_NODE_HPP
#define ROV_JOYSTICK_NODE_HPP

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <mavros_msgs/msg/manual_control.hpp>
#include <mavros_msgs/srv/command_bool.hpp>
#include <mavros_msgs/srv/set_mode.hpp>

class RovJoystickNode : public rclcpp::Node {
public:
    RovJoystickNode();

private:
    void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg);
    void send_arming_command(bool arm_vehicle);
    void send_mode_command(const std::string& target_mode);
    void publish_manual_control();

    rclcpp::TimerBase::SharedPtr timer_;
    float current_x_ = 0.0;
    float current_y_ = 0.0;
    float current_z_ = 500.0;
    float current_r_ = 0.0;

    rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr sub_joy_;
    rclcpp::Publisher<mavros_msgs::msg::ManualControl>::SharedPtr pub_vel_;
    rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedPtr client_arm_;
    rclcpp::Client<mavros_msgs::srv::SetMode>::SharedPtr client_mode_;

    bool vehicle_armed_;
    std::string active_flight_mode_;
    
    static constexpr int AXIS_SURGE = 1;
    static constexpr int AXIS_SWAY = 0;
    static constexpr int AXIS_HEAVE = 4;
    static constexpr int AXIS_YAW = 3;
    
    static constexpr int BTN_ARM = 0;
    static constexpr int BTN_DISARM = 1;
    static constexpr int BTN_STABILIZE = 2;
    static constexpr int BTN_DEPTH_HOLD = 3;
    // Add button index 4 for MANUAL mode
    static constexpr int BTN_MANUAL = 4;
};

#endif
