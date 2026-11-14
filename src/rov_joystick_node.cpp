#include "rov_joystick/rov_joystick_node.hpp"

RovJoystickNode::RovJoystickNode() : Node("rov_joystick_node"), vehicle_armed_(false), active_flight_mode_("") {
    sub_joy_ = this->create_subscription<sensor_msgs::msg::Joy>(
        "/joy", 10, std::bind(&RovJoystickNode::joy_callback, this, std::placeholders::_1));
        
  pub_vel_ = this->create_publisher<mavros_msgs::msg::ManualControl>(
    "/mavros/manual_control/send", 10);
        
    client_arm_ = this->create_client<mavros_msgs::srv::CommandBool>("/mavros/cmd/arming");
    client_mode_ = this->create_client<mavros_msgs::srv::SetMode>("/mavros/set_mode");

    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(50), 
        std::bind(&RovJoystickNode::publish_manual_control, this));

    RCLCPP_INFO(this->get_logger(), "ROV Joystick Node initialized.");
}

void RovJoystickNode::joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg) {
    // Update stored variables instead of publishing directly
    current_x_ = msg->axes[AXIS_SURGE] * -1000.0; 
    current_y_ = msg->axes[AXIS_SWAY] * 1000.0;
    current_r_ = msg->axes[AXIS_YAW] * 1000.0;
    current_z_ = (msg->axes[AXIS_HEAVE] + 1.0) * 500.0;  

    if (msg->buttons[BTN_ARM] == 1 && !vehicle_armed_) {
        send_arming_command(true);
    } else if (msg->buttons[BTN_DISARM] == 1 && vehicle_armed_) {
        send_arming_command(false);
    }

    if (msg->buttons[BTN_STABILIZE] == 1 && active_flight_mode_ != "STABILIZE") {
        send_mode_command("STABILIZE");
    }
     else if (msg->buttons[BTN_DEPTH_HOLD] == 1 && active_flight_mode_ != "ALT_HOLD") {
        send_mode_command("ALT_HOLD"); 
        }
      else if (msg->buttons.size() > BTN_MANUAL && msg->buttons[BTN_MANUAL] == 1 && active_flight_mode_ !="MANUAL") {
        send_mode_command("MANUAL");
       } 
}

// ADD THIS NEW METHOD RIGHT BELOW joy_callback:
void RovJoystickNode::publish_manual_control() {
    mavros_msgs::msg::ManualControl mc_msg;
    mc_msg.header.stamp = this->get_clock()->now();
    mc_msg.x = current_x_;
    mc_msg.y = current_y_;
    mc_msg.z = current_z_;
    mc_msg.r = current_r_;
    mc_msg.buttons = 0;

    pub_vel_->publish(mc_msg);
}

void RovJoystickNode::send_arming_command(bool arm_vehicle) {
    auto req = std::make_shared<mavros_msgs::srv::CommandBool::Request>();
    req->value = arm_vehicle;
    
    client_arm_->async_send_request(req, 
        [this, arm_vehicle](rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedFuture future) {
            if (future.get()->success) {
                this->vehicle_armed_ = arm_vehicle;
                RCLCPP_INFO(this->get_logger(), "ROV %s successful", arm_vehicle ? "Armed" : "Disarmed");
            }
        });
}

void RovJoystickNode::send_mode_command(const std::string& target_mode) {
    auto req = std::make_shared<mavros_msgs::srv::SetMode::Request>();
    req->custom_mode = target_mode;

    client_mode_->async_send_request(req,
        [this, target_mode](rclcpp::Client<mavros_msgs::srv::SetMode>::SharedFuture future) {
            if (future.get()->mode_sent) {
                this->active_flight_mode_ = target_mode;
                RCLCPP_INFO(this->get_logger(), "Flight mode set to: %s", target_mode.c_str());
            }
        });
}

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<RovJoystickNode>());
    rclcpp::shutdown();
    return 0;
}
