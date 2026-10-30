#include <chrono>
#include <cstdint>
#include <csignal>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <mavros_msgs/msg/manual_control.hpp>
#include <mavros_msgs/msg/state.hpp>
#include <mavros_msgs/srv/command_bool.hpp>
#include "mako_ps4_control/controls.hpp"

using namespace std::chrono_literals;
volatile std::sig_atomic_t stop_requested=0;
void stop_handler(int) { stop_requested=1; }
class PS4Motion : public rclcpp::Node {
  using Clock=std::chrono::steady_clock;
  using Arm=mavros_msgs::srv::CommandBool;
public:
  PS4Motion() : Node("mako_ps4_motion") {
    mapping_.forward=declare_parameter<int>("axis_forward",1);
    mapping_.lateral=declare_parameter<int>("axis_lateral",0);
    mapping_.vertical=declare_parameter<int>("axis_vertical",3);
    mapping_.yaw=declare_parameter<int>("axis_yaw",2);
    mapping_.options=declare_parameter<int>("options_button",6);
    mapping_.forward_sign=declare_parameter<bool>("invert_forward",true)?-1:1;
    mapping_.lateral_sign=declare_parameter<bool>("invert_lateral",false)?-1:1;
    mapping_.vertical_sign=declare_parameter<bool>("invert_vertical",false)?-1:1;
    mapping_.yaw_sign=declare_parameter<bool>("invert_yaw",true)?-1:1;
    mapping_.deadzone=declare_parameter<double>("deadzone",0.08);
    mapping_.gain=declare_parameter<double>("gain",0.5);
    timeout_=declare_parameter<double>("joy_timeout",0.5);
    for(int i : {mapping_.forward,mapping_.lateral,mapping_.vertical,mapping_.yaw,mapping_.options})
      if(i<0 || i>63) throw std::invalid_argument("Mapping indices must be 0..63");
    if(!std::isfinite(mapping_.gain) || mapping_.gain<0 || mapping_.gain>1 ||
       !std::isfinite(mapping_.deadzone) || mapping_.deadzone<0 || mapping_.deadzone>=0.95 ||
       !std::isfinite(timeout_) || timeout_<0.05 || timeout_>5)
      throw std::invalid_argument("Invalid gain, deadzone or joy_timeout");
    pub_=create_publisher<mavros_msgs::msg::ManualControl>("/mavros/manual_control/send",10);
    arm_=create_client<Arm>("/mavros/cmd/arming");
    state_sub_=create_subscription<mavros_msgs::msg::State>("/mavros/state",rclcpp::SensorDataQoS(),
      [this](mavros_msgs::msg::State::SharedPtr msg){
        state_=*msg; state_time_=Clock::now(); have_state_=true;
        if(pending_ && state_.armed==desired_) {
          finish_pending();
          RCLCPP_INFO(get_logger(),"FCU confirmed %s",state_.armed?"ARMED":"DISARMED");
        }
      });
    joy_sub_=create_subscription<sensor_msgs::msg::Joy>("/joy",rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::Joy::SharedPtr msg){
        const auto now=Clock::now();
        if(!have_joy_ || seconds(now-joy_time_)>timeout_) edge_.reset();
        joy_=*msg; have_joy_=true; joy_time_=now;
        if(static_cast<size_t>(mapping_.options)>=joy_.buttons.size()) { edge_.reset(); return; }
        if(edge_.update(joy_.buttons[mapping_.options]!=0)) toggle();
      });
    timer_=create_wall_timer(20ms,[this]{tick();});
    RCLCPP_INFO(get_logger(),"PS4: Options toggles arm; left=surge/sway, right=heave/yaw. Gain %.2f",mapping_.gain);
  }
  void neutral() { publish({}); }
private:
  template<class Duration> static double seconds(Duration dt) { return std::chrono::duration<double>(dt).count(); }
  bool connected() const {
    return have_state_ && state_.connected && seconds(Clock::now()-state_time_)<3;
  }
  bool fresh_joy() const { return have_joy_ && seconds(Clock::now()-joy_time_)<=timeout_; }
  void finish_pending() {
    if(request_id_) arm_->remove_pending_request(request_id_);
    request_id_=0; pending_=false; ++generation_;
  }
  void toggle() {
    if(!connected()) { RCLCPP_WARN(get_logger(),"No fresh connected MAVROS state"); return; }
    if(pending_) { RCLCPP_WARN(get_logger(),"Waiting for previous arm/disarm confirmation"); return; }
    const bool desired=!state_.armed;
    if(desired && (state_.mode!="MANUAL" || !mako::centered(joy_.axes,mapping_))) {
      RCLCPP_WARN(get_logger(),"To arm: select MANUAL and center both sticks"); return;
    }
    if(!arm_->service_is_ready()) { RCLCPP_WARN(get_logger(),"Arming service unavailable"); return; }
    neutral(); desired_=desired; pending_=true; deadline_=Clock::now()+5s;
    const auto generation=++generation_;
    auto request=std::make_shared<Arm::Request>(); request->value=desired;
    auto pending=arm_->async_send_request(request,[this,generation](rclcpp::Client<Arm>::SharedFuture future){
      if(generation!=generation_) return;
      request_id_=0;
      try {
        auto reply=future.get();
        if(!reply->success) {
          RCLCPP_WARN(get_logger(),"FCU rejected %s (result %u)",desired_?"arm":"disarm",static_cast<unsigned>(reply->result));
          finish_pending();
        } else RCLCPP_INFO(get_logger(),"Request accepted; waiting for MAVROS state confirmation");
      } catch(const std::exception& e) {
        RCLCPP_ERROR(get_logger(),"Arming service: %s",e.what()); finish_pending();
      }
    });
    request_id_=pending.request_id;
  }
  void tick() {
    if(pending_ && Clock::now()>deadline_) {
      finish_pending(); RCLCPP_WARN(get_logger(),"Arm/disarm confirmation timed out; check /mavros/state");
    }
    if(!fresh_joy()) edge_.reset();
    const bool enabled=connected() && state_.armed && state_.mode=="MANUAL" && fresh_joy() && !pending_;
    publish(mako::map(joy_.axes,mapping_,enabled));
  }
  void publish(const mako::Command& command) {
    mavros_msgs::msg::ManualControl msg{}; msg.header.stamp=now();
    msg.x=command.x; msg.y=command.y; msg.z=command.z; msg.r=command.r;
    pub_->publish(msg);
  }
  mako::Mapping mapping_;
  mako::PressEdge edge_;
  double timeout_{0.5};
  bool have_state_{false},have_joy_{false},pending_{false},desired_{false};
  int64_t request_id_{0}; uint64_t generation_{0};
  Clock::time_point state_time_{},joy_time_{},deadline_{};
  sensor_msgs::msg::Joy joy_;
  mavros_msgs::msg::State state_;
  rclcpp::Publisher<mavros_msgs::msg::ManualControl>::SharedPtr pub_;
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
  rclcpp::Subscription<mavros_msgs::msg::State>::SharedPtr state_sub_;
  rclcpp::Client<Arm>::SharedPtr arm_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc,char** argv) {
  rclcpp::init(argc,argv,rclcpp::InitOptions(),rclcpp::SignalHandlerOptions::None);
  std::signal(SIGINT,stop_handler); std::signal(SIGTERM,stop_handler);
  auto node=std::make_shared<PS4Motion>();
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  while(rclcpp::ok() && !stop_requested) {
    executor.spin_some(); std::this_thread::sleep_for(5ms);
  }
  if(rclcpp::ok()) {
    for(int i=0;i<5;++i) { node->neutral(); std::this_thread::sleep_for(20ms); }
  }
  rclcpp::shutdown();
  return 0;
}
