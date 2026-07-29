#include <chrono>
#include <memory>
#include <cmath>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64.hpp"

using namespace std::chrono_literals;

class RovDepthSimulator : public rclcpp::Node {
public:
    RovDepthSimulator() : Node("rov_depth_simulator"), count_(0) {
        publisher_ = this->create_publisher<std_msgs::msg::Float64>("depth_data", 10);
        timer_ = this->create_wall_timer(
            1s, std::bind(&RovDepthSimulator::timer_callback, this));
    }

private:
    void timer_callback() {
        auto message = std_msgs::msg::Float64();
        // معادلة بتطلع قرايات عمق بتزيد وتقل بين 0 و 10 متر
        message.data = 5.0 + 5.0 * std::sin(count_ * 0.5);
        
        RCLCPP_INFO(this->get_logger(), "ROV Depth Simulator: Publishing '%.2f' meters", message.data);
        publisher_->publish(message);
        count_++;
    }
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr publisher_;
    size_t count_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<RovDepthSimulator>());
    rclcpp::shutdown();
    return 0;
}