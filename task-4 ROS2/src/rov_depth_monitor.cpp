#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64.hpp"

class RovDepthMonitor : public rclcpp::Node {
public:
    RovDepthMonitor() : Node("rov_depth_monitor") {
        subscription_ = this->create_subscription<std_msgs::msg::Float64>(
            "depth_data", 10, std::bind(&RovDepthMonitor::topic_callback, this, std::placeholders::_1));
    }

private:
    void topic_callback(const std_msgs::msg::Float64::SharedPtr msg) const {
        double threshold = 8.0; // الحد الأقصى للعمق 8 متر
        
        if (msg->data > threshold) {
            RCLCPP_WARN(this->get_logger(), "ROV WARNING! Depth crossed threshold: %.2f meters", msg->data);
        } else {
            RCLCPP_INFO(this->get_logger(), "ROV Depth is safe: %.2f meters", msg->data);
        }
    }
    rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr subscription_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<RovDepthMonitor>());
    rclcpp::shutdown();
    return 0;
}