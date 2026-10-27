#include <chrono>
#include <memory>
#include <string>
#include <algorithm>
#include <cmath>
#include <array>
#include <mavros_msgs/msg/state.hpp>
#include <rcl_interfaces/msg/set_parameters_result.hpp>
#include "RealJoy/pilot_axes.hpp"

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>

#include <mavros_msgs/msg/manual_control.hpp>
#include <mavros_msgs/srv/command_bool.hpp>
#include <mavros_msgs/srv/set_mode.hpp>

#include "RealJoy/manual.hpp"
#include "RealJoy/keelDepth.hpp"
#include "RealJoy/modes.hpp"
#include <std_srvs/srv/trigger.hpp>

using namespace std::chrono_literals;

class RealJoyNode : public rclcpp::Node
{
public:
  RealJoyNode()
  : Node("realjoy_node")
  {
    joy_topic_ = this->declare_parameter<std::string>("joy_topic", "/joy");

    publish_rate_hz_ = this->declare_parameter<double>("publish_rate_hz", 60.0);
    joy_timeout_s_   = this->declare_parameter<double>("joy_timeout_s", 0.5);

    arm_button_index_ = this->declare_parameter<int>("arm_button_index", 6);
    arm_mode_ = this->declare_parameter<std::string>("arm_mode", "MANUAL");

    alt_hold_button_index_ = this->declare_parameter<int>("alt_hold_button_index", 3);
    alt_hold_mode_         = this->declare_parameter<std::string>("alt_hold_mode", "ALT_HOLD");

    cfg_.axis_forward   = this->declare_parameter<int>("axis_forward", 1);
    cfg_.axis_lateral   = this->declare_parameter<int>("axis_lateral", 0);
    cfg_.axis_vertical  = this->declare_parameter<int>("axis_vertical", 3);
    cfg_.axis_yaw_left  = this->declare_parameter<int>("axis_yaw_left", 4);
    cfg_.axis_yaw_right = this->declare_parameter<int>("axis_yaw_right", 5);

    // Pilot stick directions: forward inverted, heave uses the native axis.
    cfg_.invert_forward  = this->declare_parameter<bool>("invert_forward", true);
    cfg_.invert_lateral  = this->declare_parameter<bool>("invert_lateral", false);
    cfg_.invert_yaw      = this->declare_parameter<bool>("invert_yaw", true);
    cfg_.invert_vertical = this->declare_parameter<bool>("invert_vertical", false);

    cfg_.deadzone_forward  = static_cast<float>(this->declare_parameter<double>("deadzone_forward", 0.08));
    cfg_.deadzone_lateral  = static_cast<float>(this->declare_parameter<double>("deadzone_lateral", 0.08));
    cfg_.deadzone_vertical = static_cast<float>(this->declare_parameter<double>("deadzone_vertical", 0.08));

    cfg_.expo_forward  = static_cast<float>(this->declare_parameter<double>("expo_forward", 0.3));
    cfg_.expo_lateral  = static_cast<float>(this->declare_parameter<double>("expo_lateral", 0.3));
    cfg_.expo_yaw      = static_cast<float>(this->declare_parameter<double>("expo_yaw", 0.3));
    cfg_.expo_vertical = static_cast<float>(this->declare_parameter<double>("expo_vertical", 0.2));

    deadzone_yaw_ = declare_parameter<double>("deadzone_yaw", 0.05);
    for (size_t i=0; i<axis_names_.size(); ++i)
      sensitivity_[i] = declare_parameter<double>("sensitivity_"+axis_names_[i], 1.0);
    smoothing_tau_ = declare_parameter<double>("smoothing_tau", 0.08);
    autopilot_topic_ = declare_parameter<std::string>("autopilot_topic", "/mako/autopilot/manual_control");
    autopilot_timeout_s_ = declare_parameter<double>("autopilot_timeout_s", 0.3);

    manual_pub_ = this->create_publisher<mavros_msgs::msg::ManualControl>(

      "/mavros/manual_control/send", 10);

    // Operation MX tasks send commands here; centred sticks let them through.
    autopilot_sub_ = create_subscription<mavros_msgs::msg::ManualControl>(autopilot_topic_, 10,
      [this](const mavros_msgs::msg::ManualControl::SharedPtr msg) {
        autopilot_cmd_ = *msg; autopilot_time_ = Clock::now(); have_autopilot_ = true;
      });

    joy_sub_ = this->create_subscription<sensor_msgs::msg::Joy>(
      joy_topic_, rclcpp::SensorDataQoS(),
      std::bind(&RealJoyNode::on_joy, this, std::placeholders::_1));

    state_sub_ = create_subscription<mavros_msgs::msg::State>("/mavros/state", rclcpp::SensorDataQoS(),
      [this](const mavros_msgs::msg::State::SharedPtr msg) {
        state_ = *msg; have_state_ = true; state_time_ = Clock::now();
        mode_switcher_->set_current_mode(state_.mode);
        if (!pending_mode_.empty() && state_.mode == pending_mode_) {
          RCLCPP_INFO(get_logger(), "Mode confirmed by FCU: %s", state_.mode.c_str());
          pending_mode_.clear();
          if (arm_after_mode_) { arm_after_mode_ = false; request_arm(true); }
        }
      });

    arm_client_      = this->create_client<mavros_msgs::srv::CommandBool>("/mavros/cmd/arming");
    set_mode_client_ = this->create_client<mavros_msgs::srv::SetMode>("/mavros/set_mode");

    PressureToDepthCm::Params dp;
    dp.rel_alt_topic        = this->declare_parameter<std::string>("rel_alt_topic", "/mavros/global_position/rel_alt");
    dp.depth_cm_topic        = this->declare_parameter<std::string>("depth_cm_topic", "/depth_cm");
    dp.keel_offset_cm        = this->declare_parameter<double>("keel_offset_cm", 0.0);
    dp.enabled_by_default    = this->declare_parameter<bool>("depth_always_enabled", true);
    dp.use_zero_reference     = this->declare_parameter<bool>("use_zero_reference", false);

    depth_ = std::make_unique<PressureToDepthCm>(this, dp);

    depth_zero_button_index_ = this->declare_parameter<int>("depth_zero_button_index", 0);
    depth_zero_client_ = this->create_client<std_srvs::srv::Trigger>("/set_zero_depth");

    // Initialize mode switcher for Circle and Square buttons
    mode_switcher_ = std::make_unique<realjoy::ModeSwitcher>(this, [this](const std::string& mode) {
      this->request_mode(mode);
    });

    parameters_callback_ = add_on_set_parameters_callback(
      std::bind(&RealJoyNode::update_parameters, this, std::placeholders::_1));
    // Validate launch-time overrides with the same rules as live updates.
    std::vector<rclcpp::Parameter> initial;
    for (const auto& name : list_parameters({}, 1).names)
      if (name.rfind("axis_",0)==0 || name.rfind("invert_",0)==0 || name.rfind("expo_",0)==0 ||
          name.rfind("deadzone_",0)==0 || name.rfind("sensitivity_",0)==0 || name=="smoothing_tau" ||
          name=="joy_timeout_s" || name=="publish_rate_hz") initial.push_back(get_parameter(name));
    const auto validation = update_parameters(initial);
    if (!validation.successful) throw std::invalid_argument(validation.reason);
    last_joy_time_ = last_tick_ = Clock::now();

    RCLCPP_INFO(this->get_logger(), "RealJoy started (ManualControl + ALT_HOLD toggle on button %d)", alt_hold_button_index_);
  }

private:
  static int safe_button(const sensor_msgs::msg::Joy & joy, int idx)
  {
    if (idx < 0 || idx >= static_cast<int>(joy.buttons.size())) return 0;
    return joy.buttons[idx];
  }

  using Clock = std::chrono::steady_clock;

  bool state_ready() const {
    return have_state_ && state_.connected &&
      std::chrono::duration<double>(Clock::now()-state_time_).count() < 3.0;
  }

  void request_mode(const std::string& mode) {
    if (!state_ready() || !set_mode_client_->service_is_ready()) {
      RCLCPP_WARN(get_logger(), "Mode request skipped: autopilot unavailable"); arm_after_mode_=false; return;
    }
    if (!pending_mode_.empty()) { RCLCPP_WARN(get_logger(), "Waiting for previous mode confirmation"); return; }
    pending_mode_=mode; mode_deadline_=Clock::now()+5s;
    auto req=std::make_shared<mavros_msgs::srv::SetMode::Request>();req->custom_mode=mode;
    auto pending=set_mode_client_->async_send_request(req,
      [this,mode](rclcpp::Client<mavros_msgs::srv::SetMode>::SharedFuture future) {
        mode_request_id_=0;
        try {
          if (!future.get()->mode_sent) {
            RCLCPP_WARN(get_logger(), "Mode request rejected: %s", mode.c_str());
            pending_mode_.clear();arm_after_mode_=false;
          } else RCLCPP_INFO(get_logger(), "Mode request sent: %s; awaiting FCU state",mode.c_str());
        } catch (const std::exception& e) {
          RCLCPP_ERROR(get_logger(), "Mode service failed: %s",e.what());pending_mode_.clear();arm_after_mode_=false;
        }
      });
    mode_request_id_=pending.request_id;
  }

  void request_arm(bool armed) {
    if (!state_ready() || !arm_client_->service_is_ready()) {
      RCLCPP_WARN(get_logger(), "Arming request skipped: autopilot unavailable");return;
    }
    if (arm_request_id_) { RCLCPP_WARN(get_logger(), "Waiting for arming response");return; }
    auto req=std::make_shared<mavros_msgs::srv::CommandBool::Request>();req->value=armed;
    arm_deadline_=Clock::now()+5s;
    auto pending=arm_client_->async_send_request(req,
      [this,armed](rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedFuture future) {
        arm_request_id_=0;
        try {
          const auto reply=future.get();
          if (reply->success) RCLCPP_INFO(get_logger(), "%s accepted by FCU",armed?"Arming":"Disarming");
          else RCLCPP_WARN(get_logger(), "%s rejected by FCU (MAVLink result %u)",armed?"Arming":"Disarming",reply->result);
        } catch (const std::exception& e) { RCLCPP_ERROR(get_logger(), "Arming service failed: %s",e.what()); }
      });
    arm_request_id_=pending.request_id;
  }

  void toggle_arm() {
    if (!state_ready()) { RCLCPP_WARN(get_logger(), "No recent connected autopilot state");return; }
    if (state_.armed) { arm_after_mode_=false;request_arm(false);publish_neutral_manual(); }
    else if (state_.mode==arm_mode_) request_arm(true);
    else { arm_after_mode_=true;request_mode(arm_mode_); }
  }

  static mavros_msgs::msg::ManualControl bounded_autopilot(const mavros_msgs::msg::ManualControl& in) {
    mavros_msgs::msg::ManualControl mc{};
    mc.x=realjoy::bipolar_command(in.x/1000.0);mc.y=realjoy::bipolar_command(in.y/1000.0);
    mc.z=realjoy::heave_command((in.z-500.0)/500.0);mc.r=realjoy::bipolar_command(in.r/1000.0);
    return mc;
  }

  void publish_neutral_manual() {
    filtered_.fill(0.0);
    manual_pub_->publish(realjoy::create_neutral_manual_control());
  }

  void toggle_alt_hold_() {
    request_mode(state_.mode==alt_hold_mode_ ? arm_mode_ : alt_hold_mode_);
  }

  rcl_interfaces::msg::SetParametersResult update_parameters(const std::vector<rclcpp::Parameter>& parameters) {
    auto cfg=cfg_;auto sensitivity=sensitivity_;
    double yaw_deadzone=deadzone_yaw_,tau=smoothing_tau_,timeout=joy_timeout_s_,rate=publish_rate_hz_;
    rcl_interfaces::msg::SetParametersResult result;result.successful=false;
    try {
      for (const auto& p:parameters) {
        const auto& name=p.get_name();
        if (name.rfind("axis_",0)==0) {
          const int64_t value=p.as_int();
          if(value < -1 || value > 63) throw std::invalid_argument(name+" must be -1..63");
          if(name=="axis_forward") cfg.axis_forward=value;
          else if(name=="axis_lateral") cfg.axis_lateral=value;
          else if(name=="axis_vertical") cfg.axis_vertical=value;
          else if(name=="axis_yaw_left") cfg.axis_yaw_left=value;
          else if(name=="axis_yaw_right") cfg.axis_yaw_right=value;
          else throw std::invalid_argument("Unknown axis");
        } else if(name.rfind("invert_",0)==0) {
          bool value=p.as_bool();
          if(name=="invert_forward") cfg.invert_forward=value;
          else if(name=="invert_lateral") cfg.invert_lateral=value;
          else if(name=="invert_vertical") cfg.invert_vertical=value;
          else if(name=="invert_yaw") cfg.invert_yaw=value;
          else throw std::invalid_argument("Unknown inversion");
        } else if(name.rfind("expo_",0)==0 || name.rfind("deadzone_",0)==0 || name.rfind("sensitivity_",0)==0) {
          double value=p.as_double();
          const double upper=name.rfind("deadzone_",0)==0 ? 0.95 : 1.0;
          if(!std::isfinite(value) || value < 0.0 || value > upper) throw std::invalid_argument(name+" is outside its valid range");
          if(name=="expo_forward") cfg.expo_forward=value;
          else if(name=="expo_lateral") cfg.expo_lateral=value;
          else if(name=="expo_vertical") cfg.expo_vertical=value;
          else if(name=="expo_yaw") cfg.expo_yaw=value;
          else if(name=="deadzone_forward") cfg.deadzone_forward=value;
          else if(name=="deadzone_lateral") cfg.deadzone_lateral=value;
          else if(name=="deadzone_vertical") cfg.deadzone_vertical=value;
          else if(name=="deadzone_yaw") yaw_deadzone=value;
          else {
            bool found=false;
            for(size_t i=0;i<axis_names_.size();++i) if(name=="sensitivity_"+axis_names_[i]) {sensitivity[i]=value;found=true;}
            if(!found) throw std::invalid_argument("Unknown shaping parameter");
          }
        } else if(name=="smoothing_tau" || name=="joy_timeout_s" || name=="publish_rate_hz") {
          double value=p.as_double();
          if(!std::isfinite(value)) throw std::invalid_argument(name+" must be finite");
          if(name=="smoothing_tau") {if(value<0 || value>1) throw std::invalid_argument("smoothing_tau must be 0..1 seconds");tau=value;}
          if(name=="joy_timeout_s") {if(value<0.05 || value>5) throw std::invalid_argument("joy_timeout_s must be 0.05..5 seconds");timeout=value;}
          if(name=="publish_rate_hz") {if(value<1 || value>200) throw std::invalid_argument("publish_rate_hz must be 1..200");rate=value;}
        } else if(name!="use_sim_time") throw std::invalid_argument(name+" requires a node restart");
      }
    } catch(const std::exception& e) {result.reason=e.what();return result;}
    const bool recreate=!timer_ || rate!=publish_rate_hz_;
    cfg_=cfg;sensitivity_=sensitivity;deadzone_yaw_=yaw_deadzone;smoothing_tau_=tau;joy_timeout_s_=timeout;publish_rate_hz_=rate;
    filtered_.fill(0.0);
    if(recreate) {
      if(timer_) timer_->cancel();
      timer_=create_wall_timer(std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::duration<double>(1.0/rate)),std::bind(&RealJoyNode::on_timer,this));
    }
    result.successful=true;return result;
  }

  void on_joy(const sensor_msgs::msg::Joy::SharedPtr msg)
  {
    last_joy_time_ = Clock::now();
    last_joy_ = *msg;
    have_joy_ = true;

    bool arm_pressed = (safe_button(*msg, arm_button_index_) != 0);
    if (arm_pressed && !arm_button_prev_) toggle_arm();
    arm_button_prev_ = arm_pressed;

    bool hold_pressed = (safe_button(*msg, alt_hold_button_index_) != 0);
    if (hold_pressed && !alt_hold_button_prev_) {
      toggle_alt_hold_();
    }
    alt_hold_button_prev_ = hold_pressed;

    bool zero_pressed = (safe_button(*msg, depth_zero_button_index_) != 0);
    if (zero_pressed && !depth_zero_button_prev_) {
      if (depth_->ready() && depth_zero_client_ && depth_zero_client_->service_is_ready()) {
        auto req = std::make_shared<std_srvs::srv::Trigger::Request>();
        depth_zero_client_->async_send_request(req);
        RCLCPP_INFO(this->get_logger(), "Depth zero reference set (button %d)", depth_zero_button_index_);
      } else {
        RCLCPP_WARN(this->get_logger(), "Depth zero service not ready or depth not enabled");
      }
    }
    depth_zero_button_prev_ = zero_pressed;

    // Process Circle and Square button mode switches
    mode_switcher_->process_joy(*msg);
  }

  void on_timer() {
    const auto now=Clock::now();
    if((!pending_mode_.empty() || mode_request_id_) && now>mode_deadline_) {
      if(mode_request_id_) set_mode_client_->remove_pending_request(mode_request_id_);
      mode_request_id_=0;pending_mode_.clear();arm_after_mode_=false;
      RCLCPP_WARN(get_logger(), "Mode service response or FCU confirmation timed out");
    }
    if(arm_request_id_ && now>arm_deadline_) {
      arm_client_->remove_pending_request(arm_request_id_);arm_request_id_=0;
      RCLCPP_WARN(get_logger(), "Arming response timed out");
    }
    const double dt=std::clamp(std::chrono::duration<double>(now-last_tick_).count(),0.0,0.1);
    last_tick_=now;
    const bool autopilot=have_autopilot_ &&
      std::chrono::duration<double>(now-autopilot_time_).count()<autopilot_timeout_s_;
    if(!have_joy_ && !autopilot) {
      // Without a gamepad, leave the vehicle with a neutral command when a task stops.
      if(autopilot_engaged_) {RCLCPP_INFO(get_logger(), "Autopilot commands released");autopilot_engaged_=false;publish_neutral_manual();}
      return;
    }
    const bool joy_fresh=have_joy_ &&
      std::chrono::duration<double>(now-last_joy_time_).count()<=joy_timeout_s_;
    if(!state_ready() || (!joy_fresh && !autopilot)) {
      if(!input_lost_) RCLCPP_WARN(get_logger(), "Joystick input or autopilot state expired; sending neutral");
      input_lost_=true;publish_neutral_manual();return;
    }
    input_lost_=false;
    std::array<double,4> target{};
    if(joy_fresh) {
      auto axis=[this](int index,bool invert,float expo,float deadzone,double sensitivity) {
        return realjoy::shape_pilot_axis(realjoy::safe_axis(last_joy_,index),invert,expo,deadzone,sensitivity);
      };
      const double left=realjoy::safe_axis(last_joy_,cfg_.axis_yaw_left);
      const double right=realjoy::safe_axis(last_joy_,cfg_.axis_yaw_right);
      target={
        axis(cfg_.axis_forward,cfg_.invert_forward,cfg_.expo_forward,cfg_.deadzone_forward,sensitivity_[0]),
        axis(cfg_.axis_lateral,cfg_.invert_lateral,cfg_.expo_lateral,cfg_.deadzone_lateral,sensitivity_[1]),
        axis(cfg_.axis_vertical,cfg_.invert_vertical,cfg_.expo_vertical,cfg_.deadzone_vertical,sensitivity_[2]),
        realjoy::shape_pilot_axis(right-left,cfg_.invert_yaw,cfg_.expo_yaw,deadzone_yaw_,sensitivity_[3])};
    }
    // Any stick outside its dead zone takes priority over autopilot commands.
    const bool pilot_active=std::any_of(target.begin(),target.end(),[](double v){return v!=0.0;});
    if(autopilot && !pilot_active) {
      if(!autopilot_engaged_) RCLCPP_INFO(get_logger(), "Autopilot commands engaged");
      autopilot_engaged_=true;filtered_.fill(0.0);
      manual_pub_->publish(bounded_autopilot(autopilot_cmd_));return;
    }
    if(autopilot_engaged_) RCLCPP_INFO(get_logger(), autopilot ? "Pilot override: joystick has priority" : "Autopilot commands released");
    autopilot_engaged_=false;
    const double alpha=smoothing_tau_>0 ? 1.0-std::exp(-dt/smoothing_tau_) : 1.0;
    for(size_t i=0;i<target.size();++i) filtered_[i]+=alpha*(target[i]-filtered_[i]);
    mavros_msgs::msg::ManualControl mc{};
    mc.x=realjoy::bipolar_command(filtered_[0]);mc.y=realjoy::bipolar_command(filtered_[1]);
    mc.z=realjoy::heave_command(filtered_[2]);mc.r=realjoy::bipolar_command(filtered_[3]);
    manual_pub_->publish(mc);
  }

private:
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
  rclcpp::Subscription<mavros_msgs::msg::ManualControl>::SharedPtr autopilot_sub_;
  mavros_msgs::msg::ManualControl autopilot_cmd_{};
  Clock::time_point autopilot_time_{};
  bool have_autopilot_{false},autopilot_engaged_{false};
  std::string autopilot_topic_;
  double autopilot_timeout_s_{0.3};
  rclcpp::Publisher<mavros_msgs::msg::ManualControl>::SharedPtr manual_pub_;
  rclcpp::Client<mavros_msgs::srv::CommandBool>::SharedPtr arm_client_;
  rclcpp::Client<mavros_msgs::srv::SetMode>::SharedPtr set_mode_client_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Subscription<mavros_msgs::msg::State>::SharedPtr state_sub_;
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr parameters_callback_;
  mavros_msgs::msg::State state_;
  bool have_state_{false},input_lost_{false},arm_after_mode_{false};
  Clock::time_point state_time_{},mode_deadline_{},arm_deadline_{},last_tick_{};
  int64_t mode_request_id_{0},arm_request_id_{0};
  std::string pending_mode_;
  const std::array<std::string,4> axis_names_{"forward","lateral","vertical","yaw"};
  std::array<double,4> sensitivity_{1,1,1,1},filtered_{};
  double deadzone_yaw_{0.05},smoothing_tau_{0.08};
  std::unique_ptr<PressureToDepthCm> depth_;

  int alt_hold_button_index_{0};
  std::string alt_hold_mode_{"ALT_HOLD"};
  bool alt_hold_button_prev_{false};


  int depth_zero_button_index_{0};
  bool depth_zero_button_prev_{false};
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr depth_zero_client_;

  realjoy::ManualConfig cfg_{};
  double publish_rate_hz_{20.0};
  double joy_timeout_s_{0.5};

  Clock::time_point last_joy_time_;
  sensor_msgs::msg::Joy last_joy_{};
  bool have_joy_{false};

  int arm_button_index_{6};
  std::string arm_mode_{"MANUAL"};
  bool arm_button_prev_{false};


  std::string joy_topic_;

  // Mode switcher for Circle and Square buttons
  std::unique_ptr<realjoy::ModeSwitcher> mode_switcher_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<RealJoyNode>());
  rclcpp::shutdown();
  return 0;
}

