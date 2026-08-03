// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from fake_depth_interfaces:action/Dive.idl
// generated code does not contain a copyright notice

#ifndef FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__BUILDER_HPP_
#define FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "fake_depth_interfaces/action/detail/dive__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_Goal_target_depth
{
public:
  Init_Dive_Goal_target_depth()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::fake_depth_interfaces::action::Dive_Goal target_depth(::fake_depth_interfaces::action::Dive_Goal::_target_depth_type arg)
  {
    msg_.target_depth = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_Goal msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_Goal>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_Goal_target_depth();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_Result_success
{
public:
  Init_Dive_Result_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::fake_depth_interfaces::action::Dive_Result success(::fake_depth_interfaces::action::Dive_Result::_success_type arg)
  {
    msg_.success = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_Result msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_Result>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_Result_success();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_Feedback_current_depth
{
public:
  Init_Dive_Feedback_current_depth()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::fake_depth_interfaces::action::Dive_Feedback current_depth(::fake_depth_interfaces::action::Dive_Feedback::_current_depth_type arg)
  {
    msg_.current_depth = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_Feedback msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_Feedback>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_Feedback_current_depth();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_SendGoal_Request_goal
{
public:
  explicit Init_Dive_SendGoal_Request_goal(::fake_depth_interfaces::action::Dive_SendGoal_Request & msg)
  : msg_(msg)
  {}
  ::fake_depth_interfaces::action::Dive_SendGoal_Request goal(::fake_depth_interfaces::action::Dive_SendGoal_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_SendGoal_Request msg_;
};

class Init_Dive_SendGoal_Request_goal_id
{
public:
  Init_Dive_SendGoal_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Dive_SendGoal_Request_goal goal_id(::fake_depth_interfaces::action::Dive_SendGoal_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_Dive_SendGoal_Request_goal(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_SendGoal_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_SendGoal_Request>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_SendGoal_Request_goal_id();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_SendGoal_Response_stamp
{
public:
  explicit Init_Dive_SendGoal_Response_stamp(::fake_depth_interfaces::action::Dive_SendGoal_Response & msg)
  : msg_(msg)
  {}
  ::fake_depth_interfaces::action::Dive_SendGoal_Response stamp(::fake_depth_interfaces::action::Dive_SendGoal_Response::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_SendGoal_Response msg_;
};

class Init_Dive_SendGoal_Response_accepted
{
public:
  Init_Dive_SendGoal_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Dive_SendGoal_Response_stamp accepted(::fake_depth_interfaces::action::Dive_SendGoal_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_Dive_SendGoal_Response_stamp(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_SendGoal_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_SendGoal_Response>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_SendGoal_Response_accepted();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_GetResult_Request_goal_id
{
public:
  Init_Dive_GetResult_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::fake_depth_interfaces::action::Dive_GetResult_Request goal_id(::fake_depth_interfaces::action::Dive_GetResult_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_GetResult_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_GetResult_Request>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_GetResult_Request_goal_id();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_GetResult_Response_result
{
public:
  explicit Init_Dive_GetResult_Response_result(::fake_depth_interfaces::action::Dive_GetResult_Response & msg)
  : msg_(msg)
  {}
  ::fake_depth_interfaces::action::Dive_GetResult_Response result(::fake_depth_interfaces::action::Dive_GetResult_Response::_result_type arg)
  {
    msg_.result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_GetResult_Response msg_;
};

class Init_Dive_GetResult_Response_status
{
public:
  Init_Dive_GetResult_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Dive_GetResult_Response_result status(::fake_depth_interfaces::action::Dive_GetResult_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_Dive_GetResult_Response_result(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_GetResult_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_GetResult_Response>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_GetResult_Response_status();
}

}  // namespace fake_depth_interfaces


namespace fake_depth_interfaces
{

namespace action
{

namespace builder
{

class Init_Dive_FeedbackMessage_feedback
{
public:
  explicit Init_Dive_FeedbackMessage_feedback(::fake_depth_interfaces::action::Dive_FeedbackMessage & msg)
  : msg_(msg)
  {}
  ::fake_depth_interfaces::action::Dive_FeedbackMessage feedback(::fake_depth_interfaces::action::Dive_FeedbackMessage::_feedback_type arg)
  {
    msg_.feedback = std::move(arg);
    return std::move(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_FeedbackMessage msg_;
};

class Init_Dive_FeedbackMessage_goal_id
{
public:
  Init_Dive_FeedbackMessage_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Dive_FeedbackMessage_feedback goal_id(::fake_depth_interfaces::action::Dive_FeedbackMessage::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_Dive_FeedbackMessage_feedback(msg_);
  }

private:
  ::fake_depth_interfaces::action::Dive_FeedbackMessage msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::fake_depth_interfaces::action::Dive_FeedbackMessage>()
{
  return fake_depth_interfaces::action::builder::Init_Dive_FeedbackMessage_goal_id();
}

}  // namespace fake_depth_interfaces

#endif  // FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__BUILDER_HPP_
