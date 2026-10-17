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
        // --- إعدادات الزراير ---
        this->declare_parameter<int>("btn_triangle", 3);
        this->declare_parameter<int>("btn_circle", 1);
        this->declare_parameter<int>("btn_x", 0);
        this->declare_parameter<int>("btn_square", 2);
        this->declare_parameter<int>("btn_start", 6);

        // --- إعدادات الأنالوج ---
        this->declare_parameter<int>("axis_sway", 0);
        this->declare_parameter<int>("axis_surge", 1);
        this->declare_parameter<int>("axis_heave", 3);
        this->declare_parameter<int>("axis_yaw", 2);

        btn_triangle_ = this->get_parameter("btn_triangle").as_int();
        btn_circle_   = this->get_parameter("btn_circle").as_int();
        btn_x_        = this->get_parameter("btn_x").as_int();
        btn_square_   = this->get_parameter("btn_square").as_int();
        btn_start_    = this->get_parameter("btn_start").as_int();

        axis_sway_  = this->get_parameter("axis_sway").as_int();
        axis_surge_ = this->get_parameter("axis_surge").as_int();
        axis_heave_ = this->get_parameter("axis_heave").as_int();
        axis_yaw_   = this->get_parameter("axis_yaw").as_int();

        // --- QoS متوافق مع MAVROS ---
        auto mavros_qos = rclcpp::SystemDefaultsQoS();
        auto sensor_qos = rclcpp::SensorDataQoS();

        joy_sub_ = this->create_subscription<sensor_msgs::msg::Joy>(
            "/joy", sensor_qos, std::bind(&ROVControllerNode::joy_callback, this, std::placeholders::_1));

        state_sub_ = this->create_subscription<mavros_msgs::msg::State>(
            "/mavros/state", mavros_qos, std::bind(&ROVControllerNode::state_callback, this, std::placeholders::_1));

        manual_pub_ = this->create_publisher<mavros_msgs::msg::ManualControl>(
            "/mavros/manual_control/send", mavros_qos);

        arm_client_  = this->create_client<mavros_msgs::srv::CommandBool>("/mavros/cmd/arming");
        mode_client_ = this->create_client<mavros_msgs::srv::SetMode>("/mavros/set_mode");

        timer_ = this->create_wall_timer(
            50ms, std::bind(&ROVControllerNode::publish_control, this));

        RCLCPP_INFO(this->get_logger(), "ROV Controller Initialized (Corrected Mapping: Axes 0,1,2,3 - Buttons 0,1,2,3,9)");
    }

private:
    void state_callback(const mavros_msgs::msg::State::SharedPtr msg) {
        is_armed_ = msg->armed;
        current_mode_ = msg->mode;
    }

    void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg) {
        handle_arming(msg->buttons);
        handle_flight_modes(msg->buttons);

        size_t num_axes = msg->axes.size();
        if (static_cast<size_t>(axis_surge_) < num_axes) target_surge_ = msg->axes[axis_surge_];
        if (static_cast<size_t>(axis_sway_) < num_axes)  target_sway_  = msg->axes[axis_sway_];
        if (static_cast<size_t>(axis_heave_) < num_axes) target_heave_ = msg->axes[axis_heave_];
        if (static_cast<size_t>(axis_yaw_) < num_axes)   target_yaw_   = msg->axes[axis_yaw_];
    }

    void publish_control() {
        auto msg = mavros_msgs::msg::ManualControl();
        msg.header.stamp = this->get_clock()->now();

        auto deadzone = [](double val) { return (std::abs(val) < 0.05) ? 0.0 : val; };

        double surge = deadzone(target_surge_);
        double sway  = deadzone(target_sway_);
        double heave = deadzone(target_heave_);
        double yaw   = deadzone(target_yaw_);

        // تحويل الحركة لنطاق ArduSub (-1000 لـ +1000)
        msg.x = static_cast<float>(clamp(surge * 1000.0, -1000.0, 1000.0));
        msg.y = static_cast<float>(clamp(-sway * 1000.0, -1000.0, 1000.0));
        msg.r = static_cast<float>(clamp(-yaw * 1000.0, -1000.0, 1000.0));

        // الـ Heave لازم يكون 500 في المنتصف عشان الـ Arm يشتغل وميديش خطأ
        msg.z = static_cast<float>(clamp(500.0 + (heave * 500.0), 0.0, 1000.0));

        msg.buttons = 0;
        manual_pub_->publish(msg);
    }

    void handle_arming(const std::vector<int32_t> &buttons) {
        if (buttons.size() > static_cast<size_t>(btn_start_)) {
            int current_start = buttons[btn_start_];
            if (current_start == 1 && prev_start_btn_ == 0) {
                RCLCPP_INFO(this->get_logger(), "Start Button (Index 9) Pressed! Requesting Arm/Disarm...");
                
                auto req = std::make_shared<mavros_msgs::srv::CommandBool::Request>();
                req->value = !is_armed_;

                if (arm_client_->wait_for_service(1s)) {
                    arm_client_->async_send_request(
                        req, std::bind(&ROVControllerNode::arm_response_callback, this, std::placeholders::_1));
                } else {
                    RCLCPP_WARN(this->get_logger(), "Arming service unavailable!");
                }
            }
            prev_start_btn_ = current_start;
        }
    }

    void arm_response_callback(rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedFuture future) {
        try {
            auto response = future.get();
            if (response->success) {
                RCLCPP_INFO(this->get_logger(), "Arming/Disarming command accepted!");
            } else {
                RCLCPP_ERROR(this->get_logger(), "Arming request rejected by ArduSub! (Check if Throttle is at 500)");
            }
        } catch (const std::exception &e) {
            RCLCPP_ERROR(this->get_logger(), "Arming call failed: %s", e.what());
        }
    }

    void handle_flight_modes(const std::vector<int32_t> &buttons) {
        auto check_btn = [&](int idx) { return (buttons.size() > static_cast<size_t>(idx)) && (buttons[idx] == 1); };

        if (check_btn(btn_triangle_) && prev_triangle_btn_ == 0) {
            RCLCPP_INFO(this->get_logger(), "Triangle (Index 0) Pressed -> ALT_HOLD");
            set_mode("ALT_HOLD");
        } else if (check_btn(btn_circle_) && prev_circle_btn_ == 0) {
            RCLCPP_INFO(this->get_logger(), "Circle (Index 1) Pressed -> GUIDED");
            set_mode("GUIDED");
        } else if (check_btn(btn_x_) && prev_x_btn_ == 0) {
            RCLCPP_INFO(this->get_logger(), "X (Index 2) Pressed -> MANUAL");
            set_mode("MANUAL");
        } else if (check_btn(btn_square_) && prev_square_btn_ == 0) {
            RCLCPP_INFO(this->get_logger(), "Square (Index 3) Pressed -> STABILIZE");
            set_mode("STABILIZE");
        }

        prev_triangle_btn_ = check_btn(btn_triangle_);
        prev_circle_btn_   = check_btn(btn_circle_);
        prev_x_btn_        = check_btn(btn_x_);
        prev_square_btn_   = check_btn(btn_square_);
    }

    void set_mode(const std::string &custom_mode) {
        auto req = std::make_shared<mavros_msgs::srv::SetMode::Request>();
        req->custom_mode = custom_mode;

        if (mode_client_->wait_for_service(1s)) {
            mode_client_->async_send_request(req);
        }
    }

    bool is_armed_{false};
    std::string current_mode_{""};

    int btn_triangle_{0}, btn_circle_{1}, btn_x_{2}, btn_square_{3}, btn_start_{9};
    int prev_start_btn_{0}, prev_triangle_btn_{0}, prev_circle_btn_{0}, prev_x_btn_{0}, prev_square_btn_{0};

    int axis_sway_{0}, axis_surge_{1}, axis_heave_{2}, axis_yaw_{3};
    double target_surge_{0.0}, target_sway_{0.0}, target_heave_{0.0}, target_yaw_{0.0};

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
