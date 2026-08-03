// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from fake_depth_interfaces:action/Dive.idl
// generated code does not contain a copyright notice

#ifndef FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__STRUCT_H_
#define FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_Goal
{
  float target_depth;
} fake_depth_interfaces__action__Dive_Goal;

// Struct for a sequence of fake_depth_interfaces__action__Dive_Goal.
typedef struct fake_depth_interfaces__action__Dive_Goal__Sequence
{
  fake_depth_interfaces__action__Dive_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_Goal__Sequence;


// Constants defined in the message

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_Result
{
  bool success;
} fake_depth_interfaces__action__Dive_Result;

// Struct for a sequence of fake_depth_interfaces__action__Dive_Result.
typedef struct fake_depth_interfaces__action__Dive_Result__Sequence
{
  fake_depth_interfaces__action__Dive_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_Result__Sequence;


// Constants defined in the message

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_Feedback
{
  float current_depth;
} fake_depth_interfaces__action__Dive_Feedback;

// Struct for a sequence of fake_depth_interfaces__action__Dive_Feedback.
typedef struct fake_depth_interfaces__action__Dive_Feedback__Sequence
{
  fake_depth_interfaces__action__Dive_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_Feedback__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "fake_depth_interfaces/action/detail/dive__struct.h"

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  fake_depth_interfaces__action__Dive_Goal goal;
} fake_depth_interfaces__action__Dive_SendGoal_Request;

// Struct for a sequence of fake_depth_interfaces__action__Dive_SendGoal_Request.
typedef struct fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence
{
  fake_depth_interfaces__action__Dive_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} fake_depth_interfaces__action__Dive_SendGoal_Response;

// Struct for a sequence of fake_depth_interfaces__action__Dive_SendGoal_Response.
typedef struct fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence
{
  fake_depth_interfaces__action__Dive_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} fake_depth_interfaces__action__Dive_GetResult_Request;

// Struct for a sequence of fake_depth_interfaces__action__Dive_GetResult_Request.
typedef struct fake_depth_interfaces__action__Dive_GetResult_Request__Sequence
{
  fake_depth_interfaces__action__Dive_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_GetResult_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_GetResult_Response
{
  int8_t status;
  fake_depth_interfaces__action__Dive_Result result;
} fake_depth_interfaces__action__Dive_GetResult_Response;

// Struct for a sequence of fake_depth_interfaces__action__Dive_GetResult_Response.
typedef struct fake_depth_interfaces__action__Dive_GetResult_Response__Sequence
{
  fake_depth_interfaces__action__Dive_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_GetResult_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"

/// Struct defined in action/Dive in the package fake_depth_interfaces.
typedef struct fake_depth_interfaces__action__Dive_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  fake_depth_interfaces__action__Dive_Feedback feedback;
} fake_depth_interfaces__action__Dive_FeedbackMessage;

// Struct for a sequence of fake_depth_interfaces__action__Dive_FeedbackMessage.
typedef struct fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence
{
  fake_depth_interfaces__action__Dive_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__STRUCT_H_
