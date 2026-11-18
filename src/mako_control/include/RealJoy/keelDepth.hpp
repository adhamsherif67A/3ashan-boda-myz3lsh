#pragma once

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>
#include "RealJoy/rel_alt.hpp"
#include <std_srvs/srv/trigger.hpp>

#include <string>

class PressureToDepthCm
{
public:
  struct Params
  {
    std::string rel_alt_topic{"/mavros/altitude/rel_alt"};
    std::string depth_cm_topic{"/depth_cm"};

    double keel_offset_cm{0.0};       // + means keel deeper than sensor
    bool enabled_by_default{true};    // if true, auto-enable on construction
    bool use_zero_reference{false};
  };

  PressureToDepthCm(rclcpp::Node* node, const Params& p)
  : node_(node), p_(p)
  {
    if (!node_) {
      throw std::runtime_error("PressureToDepthCm: node is null");
    }

    depth_pub_ = node_->create_publisher<std_msgs::msg::Float32>(p_.depth_cm_topic, rclcpp::QoS(10));

    rel_alt_sub_ = node_->create_subscription<std_msgs::msg::Float64>(
      p_.rel_alt_topic,
      rclcpp::SensorDataQoS(),
      std::bind(&PressureToDepthCm::onRelAlt, this, std::placeholders::_1)
    );

    zero_service_ = node_->create_service<std_srvs::srv::Trigger>(
      "set_zero_depth",
      std::bind(&PressureToDepthCm::onSetZeroDepth, this, std::placeholders::_1, std::placeholders::_2)
    );

    RCLCPP_INFO(node_->get_logger(),
      "PressureToDepthCm component created: '%s' -> '%s'",
      p_.rel_alt_topic.c_str(),
      p_.depth_cm_topic.c_str());

    if (p_.enabled_by_default) {
      RCLCPP_INFO(node_->get_logger(), "PressureToDepthCm: auto-enabling");
      enable();
    } else {
      RCLCPP_INFO(node_->get_logger(), "PressureToDepthCm: disabled by default");
    }
  }

  void enable()
  {
    enabled_ = true;
    have_depth_ = false;
    RCLCPP_INFO(node_->get_logger(), "PressureToDepthCm enabled");
  }

  void disable()
  {
    enabled_ = false;
    RCLCPP_INFO(node_->get_logger(), "PressureToDepthCm disabled");
  }

  bool enabled() const { return enabled_; }

  bool ready() const { return enabled_ && have_depth_; }

  double depth_cm() const { return depth_cm_; }

  void setZeroReference(double alt_m)
  {
    zero_alt_m_ = alt_m;
    has_zero_reference_ = true;
    RCLCPP_INFO(node_->get_logger(), "Depth zero reference set to %.2fm (depth=0 at rel_alt=%.2fm)", alt_m, alt_m);
  }

  void recalibrate_surface()
  {
    // No calibration needed - using rel_alt from flight controller
    RCLCPP_INFO(node_->get_logger(), "PressureToDepthCm: recalibrate_surface called (no-op, using rel_alt)");
  }

private:
  void onRelAlt(const std_msgs::msg::Float64::SharedPtr msg)
  {
    if (!enabled_) return;

    last_rel_alt_ = msg->data;

    if (has_zero_reference_) {
      // Depth relative to zero reference point
      depth_cm_ = (zero_alt_m_ - msg->data) * 100.0 + p_.keel_offset_cm;
    } else {
      // Default: relative to surface (rel_alt=0)
      depth_cm_ = -msg->data * 100.0 + p_.keel_offset_cm;
    }
    have_depth_ = true;

    std_msgs::msg::Float32 out;
    out.data = static_cast<float>(depth_cm_);
    depth_pub_->publish(out);
  }

  void onSetZeroDepth(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> /*req*/,
    std::shared_ptr<std_srvs::srv::Trigger::Response> res)
  {
    setZeroReference(last_rel_alt_);
    res->success = true;
    res->message = "Depth zero reference set using current rel_alt=" + std::to_string(last_rel_alt_) + "m";
    RCLCPP_INFO(node_->get_logger(), "%s", res->message.c_str());
  }

private:
  rclcpp::Node* node_{nullptr};
  Params p_;

  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr rel_alt_sub_;
  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr depth_pub_;

  // Zero reference state
  double zero_alt_m_{0.0};
  bool has_zero_reference_{false};
  double last_rel_alt_{0.0};

  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr zero_service_;

  bool enabled_{false};

  // Depth state
  bool have_depth_{false};
  double depth_cm_{0.0};
};

// ------------------------------------------------------------------
// Factory function for creating depth component

namespace realjoy
{

inline std::unique_ptr<PressureToDepthCm> create_depth_component(rclcpp::Node* node)
{
  PressureToDepthCm::Params p;
  
  p.rel_alt_topic = node->declare_parameter<std::string>("rel_alt_topic", p.rel_alt_topic);
  p.depth_cm_topic = node->declare_parameter<std::string>("depth_cm_topic", p.depth_cm_topic);
  p.keel_offset_cm = node->declare_parameter<double>("keel_offset_cm", p.keel_offset_cm);
  p.enabled_by_default = node->declare_parameter<bool>("depth_enabled_by_default", p.enabled_by_default);
  p.use_zero_reference = node->declare_parameter<bool>("use_zero_reference", p.use_zero_reference);
  
  return std::make_unique<PressureToDepthCm>(node, p);
}

}  // namespace realjoy
