

#ifndef REALJOY_MODES_HPP
#define REALJOY_MODES_HPP

#include <memory>
#include <string>
#include <functional>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <mavros_msgs/srv/set_mode.hpp>

namespace realjoy
{

class ModeSwitcher
{
public:
  using SetModeCallback = std::function<void(const std::string&)>;

  ModeSwitcher(rclcpp::Node* node, SetModeCallback callback)
  : node_(node), set_mode_callback_(callback)
  {
    circle_button_index_ = node_->declare_parameter<int>("circle_button_index", 1);
    circle_mode_ = node_->declare_parameter<std::string>("circle_mode", "CIRCLE");

    square_button_index_ = node_->declare_parameter<int>("square_button_index", 2);
    square_mode_ = node_->declare_parameter<std::string>("square_mode", "STABILIZE");

    default_mode_ = node_->declare_parameter<std::string>("default_mode", "MANUAL");

    RCLCPP_INFO(node_->get_logger(), "ModeSwitcher initialized - Circle (btn %d): %s, Square (btn %d): %s, Default: %s",
                circle_button_index_, circle_mode_.c_str(), square_button_index_, square_mode_.c_str(), default_mode_.c_str());
  }

  void set_current_mode(const std::string& mode) { current_mode_ = mode; }

  void process_joy(const sensor_msgs::msg::Joy& joy)
  {
    bool circle_pressed = safe_button(joy, circle_button_index_) != 0;
    if (circle_pressed && !circle_button_prev_) {
      toggle_circle_mode();
    }
    circle_button_prev_ = circle_pressed;

    bool square_pressed = safe_button(joy, square_button_index_) != 0;
    if (square_pressed && !square_button_prev_) {
      toggle_square_mode();
    }
    square_button_prev_ = square_pressed;
  }

private:
  static int safe_button(const sensor_msgs::msg::Joy& joy, int idx)
  {
    if (idx < 0 || idx >= static_cast<int>(joy.buttons.size())) return 0;
    return joy.buttons[idx];
  }

  void toggle_circle_mode()
  {
    set_mode_callback_(current_mode_ == circle_mode_ ? default_mode_ : circle_mode_);
  }

  void toggle_square_mode()
  {
    set_mode_callback_(current_mode_ == square_mode_ ? default_mode_ : square_mode_);
  }

  rclcpp::Node* node_;
  SetModeCallback set_mode_callback_;

  int circle_button_index_{1};
  std::string circle_mode_{"CIRCLE"};
  bool circle_button_prev_{false};


  int square_button_index_{2};
  std::string square_mode_{"STABILIZE"};
  bool square_button_prev_{false};
  std::string current_mode_;

  std::string default_mode_{"MANUAL"};
};

}  // namespace realjoy

#endif  // REALJOY_MODES_HPP

