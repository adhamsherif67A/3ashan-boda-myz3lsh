// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from fake_depth_interfaces:action/Dive.idl
// generated code does not contain a copyright notice

#ifndef FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__TRAITS_HPP_
#define FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "fake_depth_interfaces/action/detail/dive__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_Goal & msg,
  std::ostream & out)
{
  out << "{";
  // member: target_depth
  {
    out << "target_depth: ";
    rosidl_generator_traits::value_to_yaml(msg.target_depth, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_Goal & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: target_depth
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "target_depth: ";
    rosidl_generator_traits::value_to_yaml(msg.target_depth, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_Goal & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_Goal & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_Goal & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_Goal>()
{
  return "fake_depth_interfaces::action::Dive_Goal";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_Goal>()
{
  return "fake_depth_interfaces/action/Dive_Goal";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_Goal>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_Goal>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_Goal>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_Result & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_Result & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_Result & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_Result & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_Result & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_Result>()
{
  return "fake_depth_interfaces::action::Dive_Result";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_Result>()
{
  return "fake_depth_interfaces/action/Dive_Result";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_Result>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_Result>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_Result>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_Feedback & msg,
  std::ostream & out)
{
  out << "{";
  // member: current_depth
  {
    out << "current_depth: ";
    rosidl_generator_traits::value_to_yaml(msg.current_depth, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_Feedback & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: current_depth
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "current_depth: ";
    rosidl_generator_traits::value_to_yaml(msg.current_depth, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_Feedback & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_Feedback & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_Feedback & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_Feedback>()
{
  return "fake_depth_interfaces::action::Dive_Feedback";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_Feedback>()
{
  return "fake_depth_interfaces/action/Dive_Feedback";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_Feedback>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_Feedback>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_Feedback>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__traits.hpp"
// Member 'goal'
#include "fake_depth_interfaces/action/detail/dive__traits.hpp"

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_SendGoal_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal_id
  {
    out << "goal_id: ";
    to_flow_style_yaml(msg.goal_id, out);
    out << ", ";
  }

  // member: goal
  {
    out << "goal: ";
    to_flow_style_yaml(msg.goal, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_SendGoal_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_id:\n";
    to_block_style_yaml(msg.goal_id, out, indentation + 2);
  }

  // member: goal
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal:\n";
    to_block_style_yaml(msg.goal, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_SendGoal_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_SendGoal_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_SendGoal_Request & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_SendGoal_Request>()
{
  return "fake_depth_interfaces::action::Dive_SendGoal_Request";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_SendGoal_Request>()
{
  return "fake_depth_interfaces/action/Dive_SendGoal_Request";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_SendGoal_Request>
  : std::integral_constant<bool, has_fixed_size<fake_depth_interfaces::action::Dive_Goal>::value && has_fixed_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_SendGoal_Request>
  : std::integral_constant<bool, has_bounded_size<fake_depth_interfaces::action::Dive_Goal>::value && has_bounded_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_SendGoal_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_SendGoal_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: accepted
  {
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << ", ";
  }

  // member: stamp
  {
    out << "stamp: ";
    to_flow_style_yaml(msg.stamp, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_SendGoal_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: accepted
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << "\n";
  }

  // member: stamp
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "stamp:\n";
    to_block_style_yaml(msg.stamp, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_SendGoal_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_SendGoal_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_SendGoal_Response & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_SendGoal_Response>()
{
  return "fake_depth_interfaces::action::Dive_SendGoal_Response";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_SendGoal_Response>()
{
  return "fake_depth_interfaces/action/Dive_SendGoal_Response";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_SendGoal_Response>
  : std::integral_constant<bool, has_fixed_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_SendGoal_Response>
  : std::integral_constant<bool, has_bounded_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_SendGoal_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_SendGoal>()
{
  return "fake_depth_interfaces::action::Dive_SendGoal";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_SendGoal>()
{
  return "fake_depth_interfaces/action/Dive_SendGoal";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_SendGoal>
  : std::integral_constant<
    bool,
    has_fixed_size<fake_depth_interfaces::action::Dive_SendGoal_Request>::value &&
    has_fixed_size<fake_depth_interfaces::action::Dive_SendGoal_Response>::value
  >
{
};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_SendGoal>
  : std::integral_constant<
    bool,
    has_bounded_size<fake_depth_interfaces::action::Dive_SendGoal_Request>::value &&
    has_bounded_size<fake_depth_interfaces::action::Dive_SendGoal_Response>::value
  >
{
};

template<>
struct is_service<fake_depth_interfaces::action::Dive_SendGoal>
  : std::true_type
{
};

template<>
struct is_service_request<fake_depth_interfaces::action::Dive_SendGoal_Request>
  : std::true_type
{
};

template<>
struct is_service_response<fake_depth_interfaces::action::Dive_SendGoal_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__traits.hpp"

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_GetResult_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal_id
  {
    out << "goal_id: ";
    to_flow_style_yaml(msg.goal_id, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_GetResult_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_id:\n";
    to_block_style_yaml(msg.goal_id, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_GetResult_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_GetResult_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_GetResult_Request & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_GetResult_Request>()
{
  return "fake_depth_interfaces::action::Dive_GetResult_Request";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_GetResult_Request>()
{
  return "fake_depth_interfaces/action/Dive_GetResult_Request";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_GetResult_Request>
  : std::integral_constant<bool, has_fixed_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_GetResult_Request>
  : std::integral_constant<bool, has_bounded_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_GetResult_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'result'
// already included above
// #include "fake_depth_interfaces/action/detail/dive__traits.hpp"

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_GetResult_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << ", ";
  }

  // member: result
  {
    out << "result: ";
    to_flow_style_yaml(msg.result, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_GetResult_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }

  // member: result
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "result:\n";
    to_block_style_yaml(msg.result, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_GetResult_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_GetResult_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_GetResult_Response & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_GetResult_Response>()
{
  return "fake_depth_interfaces::action::Dive_GetResult_Response";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_GetResult_Response>()
{
  return "fake_depth_interfaces/action/Dive_GetResult_Response";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_GetResult_Response>
  : std::integral_constant<bool, has_fixed_size<fake_depth_interfaces::action::Dive_Result>::value> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_GetResult_Response>
  : std::integral_constant<bool, has_bounded_size<fake_depth_interfaces::action::Dive_Result>::value> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_GetResult_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_GetResult>()
{
  return "fake_depth_interfaces::action::Dive_GetResult";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_GetResult>()
{
  return "fake_depth_interfaces/action/Dive_GetResult";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_GetResult>
  : std::integral_constant<
    bool,
    has_fixed_size<fake_depth_interfaces::action::Dive_GetResult_Request>::value &&
    has_fixed_size<fake_depth_interfaces::action::Dive_GetResult_Response>::value
  >
{
};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_GetResult>
  : std::integral_constant<
    bool,
    has_bounded_size<fake_depth_interfaces::action::Dive_GetResult_Request>::value &&
    has_bounded_size<fake_depth_interfaces::action::Dive_GetResult_Response>::value
  >
{
};

template<>
struct is_service<fake_depth_interfaces::action::Dive_GetResult>
  : std::true_type
{
};

template<>
struct is_service_request<fake_depth_interfaces::action::Dive_GetResult_Request>
  : std::true_type
{
};

template<>
struct is_service_response<fake_depth_interfaces::action::Dive_GetResult_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__traits.hpp"
// Member 'feedback'
// already included above
// #include "fake_depth_interfaces/action/detail/dive__traits.hpp"

namespace fake_depth_interfaces
{

namespace action
{

inline void to_flow_style_yaml(
  const Dive_FeedbackMessage & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal_id
  {
    out << "goal_id: ";
    to_flow_style_yaml(msg.goal_id, out);
    out << ", ";
  }

  // member: feedback
  {
    out << "feedback: ";
    to_flow_style_yaml(msg.feedback, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Dive_FeedbackMessage & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal_id:\n";
    to_block_style_yaml(msg.goal_id, out, indentation + 2);
  }

  // member: feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "feedback:\n";
    to_block_style_yaml(msg.feedback, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Dive_FeedbackMessage & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace action

}  // namespace fake_depth_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use fake_depth_interfaces::action::to_block_style_yaml() instead")]]
inline void to_yaml(
  const fake_depth_interfaces::action::Dive_FeedbackMessage & msg,
  std::ostream & out, size_t indentation = 0)
{
  fake_depth_interfaces::action::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use fake_depth_interfaces::action::to_yaml() instead")]]
inline std::string to_yaml(const fake_depth_interfaces::action::Dive_FeedbackMessage & msg)
{
  return fake_depth_interfaces::action::to_yaml(msg);
}

template<>
inline const char * data_type<fake_depth_interfaces::action::Dive_FeedbackMessage>()
{
  return "fake_depth_interfaces::action::Dive_FeedbackMessage";
}

template<>
inline const char * name<fake_depth_interfaces::action::Dive_FeedbackMessage>()
{
  return "fake_depth_interfaces/action/Dive_FeedbackMessage";
}

template<>
struct has_fixed_size<fake_depth_interfaces::action::Dive_FeedbackMessage>
  : std::integral_constant<bool, has_fixed_size<fake_depth_interfaces::action::Dive_Feedback>::value && has_fixed_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct has_bounded_size<fake_depth_interfaces::action::Dive_FeedbackMessage>
  : std::integral_constant<bool, has_bounded_size<fake_depth_interfaces::action::Dive_Feedback>::value && has_bounded_size<unique_identifier_msgs::msg::UUID>::value> {};

template<>
struct is_message<fake_depth_interfaces::action::Dive_FeedbackMessage>
  : std::true_type {};

}  // namespace rosidl_generator_traits


namespace rosidl_generator_traits
{

template<>
struct is_action<fake_depth_interfaces::action::Dive>
  : std::true_type
{
};

template<>
struct is_action_goal<fake_depth_interfaces::action::Dive_Goal>
  : std::true_type
{
};

template<>
struct is_action_result<fake_depth_interfaces::action::Dive_Result>
  : std::true_type
{
};

template<>
struct is_action_feedback<fake_depth_interfaces::action::Dive_Feedback>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits


#endif  // FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__TRAITS_HPP_
