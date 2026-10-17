#include <chrono>
#include <cmath>
#include <algorithm>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include "mavros_msgs/msg/manual_control.hpp"
#include "mavros_msgs/msg/state.hpp"
#include "mavros_msgs/srv/command_bool.hpp"
#include "mavros_msgs/srv/set_mode.hpp"

using namespace std::chrono_literals;

double clamp(double value, double low, double high) {
    return std::max(low, std::min(high, value));
}

class ROVControllerNode : public rclcpp::Node {
public:
    ROVControllerNode() : Node("rov_controller_node") {
        // Declaring parameters for button and axis mapping (Easy to tune via Launch file)
        this->declare_parameter<int>("btn_triangle", 0);
        this->declare_parameter<int>("btn_circle", 1);
        this->declare_parameter<int>("btn_x", 2);
        this->declare_parameter<int>("btn_square", 3);
        this->declare_parameter<int>("btn_start", 9);

        this->declare_parameter<int>("axis_sway", 0);
        this->declare_parameter<int>("axis_surge", 1);
        this->declare_parameter<int>("axis_heave", 4); // Defaulted to 4 (Common Right Stick Y)
        this->declare_parameter<int>("axis_yaw", 3);

        // Fetch Parameters
        btn_triangle_ = this->get_parameter("btn_triangle").as_int();
        btn_circle_   = this->get_parameter("btn_circle").as_int();
        btn_x_        = this->get_parameter("btn_x").as_int();
        btn_square_   = this->get_parameter("btn_square").as_int();
        btn_start_    = this->get_parameter("btn_start").as_int();

        axis_sway_  = this->get_parameter("axis_sway").as_int();
        axis_surge_ = this->get_parameter("axis_surge").as_int();
        axis_heave_ = this->get_parameter("axis_heave").as_int();
        axis_yaw_   = this->get_parameter("axis_yaw").as_int();

        // ROS 2 Subscriptions & Publishers
        joy_sub_ = this->create_subscription<sensor_msgs::msg::Joy>(
            "/joy", 10, std::bind(&ROVControllerNode::joy_callback, this, std::placeholders::_1));

        state_sub_ = this->create_subscription<mavros_msgs::msg::State>(
            "/mavros/state", 10, std::bind(&ROVControllerNode::state_callback, this, std::placeholders::_1));

        manual_pub_ = this->create_publisher<mavros_msgs::msg::ManualControl>(
            "/mavros/manual_control/send", 10);

        // Service Clients
        arm_client_  = this->create_client<mavros_msgs::srv::CommandBool>("/mavros/cmd/arming");
        mode_client_ = this->create_client<mavros_msgs::srv::SetMode>("/mavros/set_mode");

        // Timer: Continuous control publishing at 20 Hz (50 ms)
        timer_ = this->create_wall_timer(
            50ms, std::bind(&ROVControllerNode::publish_control, this));

        RCLCPP_INFO(this->get_logger(), "ROV Controller Node (C++) initialized [20Hz Loop]...");
    }

private:
    void state_callback(const mavros_msgs::msg::State::SharedPtr msg) {
        is_armed_ = msg->armed;
        current_mode_ = msg->mode;
    }

    void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg) {
        // 1. Safe Button Handling
        size_t num_buttons = msg->buttons.size();
        size_t max_btn_req = static_cast<size_t>(
            std::max({btn_start_, btn_triangle_, btn_circle_, btn_x_, btn_square_}));

        if (num_buttons > max_btn_req) {
            handle_arming(msg->buttons);
            handle_flight_modes(msg->buttons);
        }

        // 2. Safe Axis Handling
        size_t num_axes = msg->axes.size();
        if (static_cast<size_t>(axis_surge_) < num_axes) target_surge_ = msg->axes[axis_surge_];
        if (static_cast<size_t>(axis_sway_) < num_axes)  target_sway_  = msg->axes[axis_sway_];
        if (static_cast<size_t>(axis_heave_) < num_axes) target_heave_ = msg->axes[axis_heave_];
        if (static_cast<size_t>(axis_yaw_) < num_axes)   target_yaw_   = msg->axes[axis_yaw_];
    }

    void publish_control() {
        auto msg = mavros_msgs::msg::ManualControl();
        msg.header.stamp = this->get_clock()->now();

        // MAVROS manual_control/send expects (-1000.0 to 1000.0)
        msg.x = static_cast<float>(clamp(-target_surge_ * 1000.0, -1000.0, 1000.0)); // Surge
        msg.y = static_cast<float>(clamp(target_sway_ * 1000.0, -1000.0, 1000.0));   // Sway
        msg.z = static_cast<float>(clamp(target_heave_ * 1000.0, -1000.0, 1000.0));  // Heave
        msg.r = static_cast<float>(clamp(target_yaw_ * 1000.0, -1000.0, 1000.0));    // Yaw

        msg.buttons = 0; // Bitmask

        manual_pub_->publish(msg);
    }

    void handle_arming(const std::vector<int32_t> &buttons) {
        int current_start = buttons[btn_start_];

        // Edge Detection
        if (current_start == 1 && prev_start_btn_ == 0) {
            auto req = std::make_shared<mavros_msgs::srv::CommandBool::Request>();
            req->value = !is_armed_;

            if (arm_client_->wait_for_service(1s)) {
                arm_client_->async_send_request(
                    req, std::bind(&ROVControllerNode::arm_response_callback, this, std::placeholders::_1));
            } else {
                RCLCPP_WARN(this->get_logger(), "Arming service (/mavros/cmd/arming) unavailable!");
            }
        }
        prev_start_btn_ = current_start;
    }

    void arm_response_callback(rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedFuture future) {
        try {
            auto response = future.get();
            if (response->success) {
                RCLCPP_INFO(this->get_logger(), "Arming/Disarming command executed successfully.");
            } else {
                RCLCPP_ERROR(this->get_logger(), "Arming request was rejected!");
            }
        } catch (const std::exception &e) {
            RCLCPP_ERROR(this->get_logger(), "Arming service call failed: %s", e.what());
        }
    }

    void handle_flight_modes(const std::vector<int32_t> &buttons) {
        if (buttons[btn_triangle_] == 1 && prev_triangle_btn_ == 0) {
            set_mode("ALT_HOLD");
        } else if (buttons[btn_circle_] == 1 && prev_circle_btn_ == 0) {
            set_mode("GUIDED");
        } else if (buttons[btn_x_] == 1 && prev_x_btn_ == 0) {
            set_mode("MANUAL");
        } else if (buttons[btn_square_] == 1 && prev_square_btn_ == 0) {
            set_mode("STABILIZE");
        }

        prev_triangle_btn_ = buttons[btn_triangle_];
        prev_circle_btn_   = buttons[btn_circle_];
        prev_x_btn_        = buttons[btn_x_];
        prev_square_btn_   = buttons[btn_square_];
    }

    void set_mode(const std::string &custom_mode) {
        auto req = std::make_shared<mavros_msgs::srv::SetMode::Request>();
        req->custom_mode = custom_mode;

        if (mode_client_->wait_for_service(1s)) {
            mode_client_->async_send_request(req);
            RCLCPP_INFO(this->get_logger(), "Requested flight mode change to: %s", custom_mode.c_str());
        } else {
            RCLCPP_WARN(this->get_logger(), "SetMode service (/mavros/set_mode) unavailable!");
        }
    }

    // States & Internal variables
    bool is_armed_{false};
    std::string current_mode_{""};

    int btn_triangle_{0}, btn_circle_{1}, btn_x_{2}, btn_square_{3}, btn_start_{9};
    int prev_start_btn_{0}, prev_triangle_btn_{0}, prev_circle_btn_{0}, prev_x_btn_{0}, prev_square_btn_{0};

    int axis_sway_{0}, axis_surge_{1}, axis_heave_{4}, axis_yaw_{3};
    double target_surge_{0.0}, target_sway_{0.0}, target_heave_{0.0}, target_yaw_{0.0};

    // ROS 2 Interfaces
    rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
    rclcpp::Subscription<mavros_msgs::msg::State>::SharedPtr state_sub_;
    rclcpp::Publisher<mavros_msgs::msg::ManualControl>::SharedPtr manual_pub_;
    rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedPtr arm_client_;
    rclcpp::Client<mavros_msgs::srv::SetMode>::SharedPtr mode_client_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<ROVControllerNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
