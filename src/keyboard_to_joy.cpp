#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <cctype>

class KeyboardJoyNode : public rclcpp::Node {
public:
    KeyboardJoyNode() : Node("keyboard_joy_node") {
        pub_ = this->create_publisher<sensor_msgs::msg::Joy>("/joy", 10);
        
        tcgetattr(STDIN_FILENO, &oldt_);
        newt_ = oldt_;
        newt_.c_lflag &= ~(ICANON | ECHO);
        tcsetattr(STDIN_FILENO, TCSANOW, &newt_);
        oldf_ = fcntl(STDIN_FILENO, F_GETFL, 0);
        fcntl(STDIN_FILENO, F_SETFL, oldf_ | O_NONBLOCK);

        RCLCPP_INFO(this->get_logger(), "\n--- ROV Keyboard Controller ---");
        RCLCPP_INFO(this->get_logger(), "Movement: w/s (Surge), a/d (Sway), i/k (Heave), j/l (Yaw)");
        RCLCPP_INFO(this->get_logger(), "STOP ALL MOVEMENT: Spacebar");
        RCLCPP_INFO(this->get_logger(), "Buttons: 1 (Arm), 2 (Disarm), 3 (Stabilize), 4 (Depth Hold), 5 (Manual)");
        RCLCPP_INFO(this->get_logger(), "Press Ctrl+C to quit\n");

        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&KeyboardJoyNode::timer_callback, this));
    }

    ~KeyboardJoyNode() {
        tcsetattr(STDIN_FILENO, TCSANOW, &oldt_);
        fcntl(STDIN_FILENO, F_SETFL, oldf_);
    }

private:
    void timer_callback() {
        sensor_msgs::msg::Joy joy_msg;
        joy_msg.buttons.resize(5, 0);

        char c = 0;
        if (read(STDIN_FILENO, &c, 1) > 0) {
            c = std::tolower(c); // Handle Caps Lock automatically
            switch (c) {
                case 'w': current_axes_[1] = 1.0; break;
                case 's': current_axes_[1] = -1.0; break;
                case 'a': current_axes_[0] = 1.0; break;
                case 'd': current_axes_[0] = -1.0; break;
                case 'i': current_axes_[4] = 1.0; break;
                case 'k': current_axes_[4] = -1.0; break;
                case 'j': current_axes_[3] = 1.0; break;
                case 'l': current_axes_[3] = -1.0; break;
                case ' ': // Spacebar stops the ROV
                    current_axes_ = {0.0, 0.0, 0.0, 0.0, 0.0}; 
                    break;
                case '1': joy_msg.buttons[0] = 1; break;
                case '2': joy_msg.buttons[1] = 1; break;
                case '3': joy_msg.buttons[2] = 1; break;
                case '4': joy_msg.buttons[3] = 1; break;
                case '5': joy_msg.buttons[4] = 1; break;
                case '\x03': 
                    rclcpp::shutdown(); 
                    return;
            }
        }
        
        joy_msg.axes = current_axes_;
        pub_->publish(joy_msg);
    }

    rclcpp::Publisher<sensor_msgs::msg::Joy>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr timer_;
    struct termios oldt_, newt_;
    int oldf_;
    
    // Persistent state so the ROV keeps moving until Spacebar is pressed
    std::vector<float> current_axes_ = {0.0, 0.0, 0.0, 0.0, 0.0};
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<KeyboardJoyNode>());
    rclcpp::shutdown();
    return 0;
}
