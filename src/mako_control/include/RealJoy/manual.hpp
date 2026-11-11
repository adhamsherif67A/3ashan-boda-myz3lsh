#pragma once

#include <algorithm>
#include <cmath>

#include <sensor_msgs/msg/joy.hpp>
#include <mavros_msgs/msg/manual_control.hpp>
#include <mavros_msgs/srv/command_bool.hpp>
#include <mavros_msgs/srv/set_mode.hpp>
#include <rclcpp/rclcpp.hpp>

namespace realjoy
{

struct ManualConfig
{
  int axis_lateral{0};
  int axis_forward{1};
  int axis_vertical{3};
  int axis_yaw_left{5};
  int axis_yaw_right{4};

  bool invert_forward{true};
  bool invert_lateral{false};
  bool invert_vertical{true};
  bool invert_yaw{true};

  float deadzone_forward{0.08f};
  float deadzone_lateral{0.08f};
  float deadzone_vertical{0.08f};

  float expo_forward{0.4f};
  float expo_lateral{0.4f};
  float expo_vertical{0.3f};
  float expo_yaw{0.3f};

  float vertical_snap_to_zero{0.20f};
};


// ------------------------------------------------------------------

inline float safe_axis(const sensor_msgs::msg::Joy& joy, int idx)
{
  if (idx < 0 || idx >= static_cast<int>(joy.axes.size()))
    return 0.0f;
  return joy.axes[idx];
}

inline float apply_deadzone(float v, float dz)
{
  if (std::fabs(v) < dz) return 0.0f;
  return v;
}

inline float apply_expo(float v, float expo)
{
  float sign = (v >= 0.0f) ? 1.0f : -1.0f;
  float a = std::fabs(v);
  return sign * (a * a * expo + a * (1.0f - expo));
}

struct ManualAxes
{
  float x;
  float y;
  float z;
  float r;
};

inline ManualAxes compute_manual_axes(const sensor_msgs::msg::Joy& joy,
                                      const ManualConfig& cfg)
{
  ManualAxes out{};
  out.x = out.y = out.z = out.r = 0.0f;

  auto read_axis = [&](int idx, float dz) {
    float v = safe_axis(joy, idx);
    v = apply_deadzone(v, dz);
    return std::clamp(v, -1.0f, 1.0f);
  };

  float fb = read_axis(cfg.axis_forward,  cfg.deadzone_forward);
  float lr = read_axis(cfg.axis_lateral,  cfg.deadzone_lateral);
  float ud = read_axis(cfg.axis_vertical, cfg.deadzone_vertical);

  if (cfg.invert_forward)  fb = -fb;
  if (cfg.invert_lateral)  lr = -lr;
  if (cfg.invert_vertical) ud = -ud;

  fb = apply_expo(fb, cfg.expo_forward);
  lr = apply_expo(lr, cfg.expo_lateral);
  ud = apply_expo(ud, cfg.expo_vertical);

  // ===== Snap-to-zero =====
  if (std::fabs(ud) < cfg.vertical_snap_to_zero)
    ud = 0.0f;

  // -------- yaw triggers as analog (0 → -1) --------
  auto read_trigger = [&](int idx) -> float {
    float v = safe_axis(joy, idx);

    // deadzone ثابت 0.03
    if (std::fabs(v) < 0.03f)
      v = 0.0f;

    return v; // سيبه 0 → -1 زي ما هو
  };

  float left  = read_trigger(cfg.axis_yaw_left);
  float right = read_trigger(cfg.axis_yaw_right);

  // تحويل لـ yaw (-1 → 1)
  float yaw = (-right) - (-left);  // = left - right

  if (cfg.invert_yaw) yaw = -yaw;

  yaw = apply_expo(yaw, cfg.expo_yaw);
  yaw = std::clamp(yaw, -1.0f, 1.0f);

  out.x = std::clamp(fb,  -1.0f, 1.0f);
  out.y = std::clamp(lr,  -1.0f, 1.0f);
  out.z = std::clamp(ud,  -1.0f, 1.0f);
  out.r = yaw;

  return out;
}

// ------------------------------------------------------------------

inline mavros_msgs::msg::ManualControl create_neutral_manual_control()
{
  mavros_msgs::msg::ManualControl msg;
  msg.x = 0;
  msg.y = 0;
  msg.z = 500;
  msg.r = 0;
  return msg;
}

inline mavros_msgs::msg::ManualControl create_manual_control(float x, float y, float z, float r)
{
  mavros_msgs::msg::ManualControl msg;
  msg.x = static_cast<int16_t>(x * 1000.0f);
  msg.y = static_cast<int16_t>(y * 1000.0f);
  msg.z = static_cast<int16_t>((z + 1.0f) * 500.0f);
  msg.r = static_cast<int16_t>(r * 1000.0f);
  return msg;
}

inline void request_arm(rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedPtr client, bool arm)
{
  if (!client->wait_for_service(std::chrono::seconds(1))) {
    return;
  }

  auto request = std::make_shared<mavros_msgs::srv::CommandBool::Request>();
  request->value = arm;
  client->async_send_request(request);
}

inline void request_set_mode(rclcpp::Client<mavros_msgs::srv::SetMode>::SharedPtr client,
                             const std::string& mode, rclcpp::Node* node)
{
  if (!client->wait_for_service(std::chrono::seconds(1))) {
    RCLCPP_WARN(node->get_logger(), "SetMode service not available");
    return;
  }

  auto request = std::make_shared<mavros_msgs::srv::SetMode::Request>();
  request->custom_mode = mode;
  client->async_send_request(request);
}

inline ManualConfig load_manual_config(rclcpp::Node* node)
{
  ManualConfig cfg;

  cfg.axis_lateral = node->declare_parameter<int>("axis_lateral", cfg.axis_lateral);
  cfg.axis_forward = node->declare_parameter<int>("axis_forward", cfg.axis_forward);
  cfg.axis_vertical = node->declare_parameter<int>("axis_vertical", cfg.axis_vertical);
  cfg.axis_yaw_left = node->declare_parameter<int>("axis_yaw_left", cfg.axis_yaw_left);
  cfg.axis_yaw_right = node->declare_parameter<int>("axis_yaw_right", cfg.axis_yaw_right);

  cfg.invert_forward = node->declare_parameter<bool>("invert_forward", cfg.invert_forward);
  cfg.invert_lateral = node->declare_parameter<bool>("invert_lateral", cfg.invert_lateral);
  cfg.invert_vertical = node->declare_parameter<bool>("invert_vertical", cfg.invert_vertical);
  cfg.invert_yaw = node->declare_parameter<bool>("invert_yaw", cfg.invert_yaw);

  cfg.deadzone_forward = node->declare_parameter<float>("deadzone_forward", cfg.deadzone_forward);
  cfg.deadzone_lateral = node->declare_parameter<float>("deadzone_lateral", cfg.deadzone_lateral);
  cfg.deadzone_vertical = node->declare_parameter<float>("deadzone_vertical", cfg.deadzone_vertical);

  cfg.expo_forward = node->declare_parameter<float>("expo_forward", cfg.expo_forward);
  cfg.expo_lateral = node->declare_parameter<float>("expo_lateral", cfg.expo_lateral);
  cfg.expo_vertical = node->declare_parameter<float>("expo_vertical", cfg.expo_vertical);
  cfg.expo_yaw = node->declare_parameter<float>("expo_yaw", cfg.expo_yaw);

  cfg.vertical_snap_to_zero = node->declare_parameter<float>("vertical_snap_to_zero", cfg.vertical_snap_to_zero);

  return cfg;

}

} // namespace realjoy