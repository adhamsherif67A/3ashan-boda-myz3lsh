// generated from rosidl_typesupport_c/resource/idl__type_support.cpp.em
// with input from fake_depth_interfaces:action/Dive.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "fake_depth_interfaces/action/detail/dive__struct.h"
#include "fake_depth_interfaces/action/detail/dive__type_support.h"
#include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/message_type_support_dispatch.h"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_c/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_Goal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_Goal_type_support_ids_t;

static const _Dive_Goal_type_support_ids_t _Dive_Goal_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_Goal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_Goal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_Goal_type_support_symbol_names_t _Dive_Goal_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_Goal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_Goal)),
  }
};

typedef struct _Dive_Goal_type_support_data_t
{
  void * data[2];
} _Dive_Goal_type_support_data_t;

static _Dive_Goal_type_support_data_t _Dive_Goal_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_Goal_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_Goal_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_Goal_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_Goal_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_Goal_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_Goal_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_Goal)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_Goal_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_Result_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_Result_type_support_ids_t;

static const _Dive_Result_type_support_ids_t _Dive_Result_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_Result_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_Result_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_Result_type_support_symbol_names_t _Dive_Result_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_Result)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_Result)),
  }
};

typedef struct _Dive_Result_type_support_data_t
{
  void * data[2];
} _Dive_Result_type_support_data_t;

static _Dive_Result_type_support_data_t _Dive_Result_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_Result_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_Result_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_Result_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_Result_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_Result_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_Result_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_Result)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_Result_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_Feedback_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_Feedback_type_support_ids_t;

static const _Dive_Feedback_type_support_ids_t _Dive_Feedback_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_Feedback_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_Feedback_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_Feedback_type_support_symbol_names_t _Dive_Feedback_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_Feedback)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_Feedback)),
  }
};

typedef struct _Dive_Feedback_type_support_data_t
{
  void * data[2];
} _Dive_Feedback_type_support_data_t;

static _Dive_Feedback_type_support_data_t _Dive_Feedback_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_Feedback_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_Feedback_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_Feedback_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_Feedback_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_Feedback_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_Feedback_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_Feedback)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_Feedback_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_SendGoal_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_SendGoal_Request_type_support_ids_t;

static const _Dive_SendGoal_Request_type_support_ids_t _Dive_SendGoal_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_SendGoal_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_SendGoal_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_SendGoal_Request_type_support_symbol_names_t _Dive_SendGoal_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_SendGoal_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_SendGoal_Request)),
  }
};

typedef struct _Dive_SendGoal_Request_type_support_data_t
{
  void * data[2];
} _Dive_SendGoal_Request_type_support_data_t;

static _Dive_SendGoal_Request_type_support_data_t _Dive_SendGoal_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_SendGoal_Request_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_SendGoal_Request_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_SendGoal_Request_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_SendGoal_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_SendGoal_Request_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_SendGoal_Request_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_SendGoal_Request)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_SendGoal_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_SendGoal_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_SendGoal_Response_type_support_ids_t;

static const _Dive_SendGoal_Response_type_support_ids_t _Dive_SendGoal_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_SendGoal_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_SendGoal_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_SendGoal_Response_type_support_symbol_names_t _Dive_SendGoal_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_SendGoal_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_SendGoal_Response)),
  }
};

typedef struct _Dive_SendGoal_Response_type_support_data_t
{
  void * data[2];
} _Dive_SendGoal_Response_type_support_data_t;

static _Dive_SendGoal_Response_type_support_data_t _Dive_SendGoal_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_SendGoal_Response_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_SendGoal_Response_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_SendGoal_Response_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_SendGoal_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_SendGoal_Response_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_SendGoal_Response_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_SendGoal_Response)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_SendGoal_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/service_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_SendGoal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_SendGoal_type_support_ids_t;

static const _Dive_SendGoal_type_support_ids_t _Dive_SendGoal_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_SendGoal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_SendGoal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_SendGoal_type_support_symbol_names_t _Dive_SendGoal_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_SendGoal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_SendGoal)),
  }
};

typedef struct _Dive_SendGoal_type_support_data_t
{
  void * data[2];
} _Dive_SendGoal_type_support_data_t;

static _Dive_SendGoal_type_support_data_t _Dive_SendGoal_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_SendGoal_service_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_SendGoal_service_typesupport_ids.typesupport_identifier[0],
  &_Dive_SendGoal_service_typesupport_symbol_names.symbol_name[0],
  &_Dive_SendGoal_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t Dive_SendGoal_service_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_SendGoal_service_typesupport_map),
  rosidl_typesupport_c__get_service_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_SendGoal)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_SendGoal_service_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_GetResult_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_GetResult_Request_type_support_ids_t;

static const _Dive_GetResult_Request_type_support_ids_t _Dive_GetResult_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_GetResult_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_GetResult_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_GetResult_Request_type_support_symbol_names_t _Dive_GetResult_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_GetResult_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_GetResult_Request)),
  }
};

typedef struct _Dive_GetResult_Request_type_support_data_t
{
  void * data[2];
} _Dive_GetResult_Request_type_support_data_t;

static _Dive_GetResult_Request_type_support_data_t _Dive_GetResult_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_GetResult_Request_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_GetResult_Request_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_GetResult_Request_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_GetResult_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_GetResult_Request_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_GetResult_Request_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_GetResult_Request)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_GetResult_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_GetResult_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_GetResult_Response_type_support_ids_t;

static const _Dive_GetResult_Response_type_support_ids_t _Dive_GetResult_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_GetResult_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_GetResult_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_GetResult_Response_type_support_symbol_names_t _Dive_GetResult_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_GetResult_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_GetResult_Response)),
  }
};

typedef struct _Dive_GetResult_Response_type_support_data_t
{
  void * data[2];
} _Dive_GetResult_Response_type_support_data_t;

static _Dive_GetResult_Response_type_support_data_t _Dive_GetResult_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_GetResult_Response_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_GetResult_Response_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_GetResult_Response_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_GetResult_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_GetResult_Response_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_GetResult_Response_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_GetResult_Response)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_GetResult_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/service_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_GetResult_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_GetResult_type_support_ids_t;

static const _Dive_GetResult_type_support_ids_t _Dive_GetResult_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_GetResult_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_GetResult_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_GetResult_type_support_symbol_names_t _Dive_GetResult_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_GetResult)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_GetResult)),
  }
};

typedef struct _Dive_GetResult_type_support_data_t
{
  void * data[2];
} _Dive_GetResult_type_support_data_t;

static _Dive_GetResult_type_support_data_t _Dive_GetResult_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_GetResult_service_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_GetResult_service_typesupport_ids.typesupport_identifier[0],
  &_Dive_GetResult_service_typesupport_symbol_names.symbol_name[0],
  &_Dive_GetResult_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t Dive_GetResult_service_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_GetResult_service_typesupport_map),
  rosidl_typesupport_c__get_service_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_GetResult)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_GetResult_service_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__struct.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace fake_depth_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _Dive_FeedbackMessage_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _Dive_FeedbackMessage_type_support_ids_t;

static const _Dive_FeedbackMessage_type_support_ids_t _Dive_FeedbackMessage_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _Dive_FeedbackMessage_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _Dive_FeedbackMessage_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _Dive_FeedbackMessage_type_support_symbol_names_t _Dive_FeedbackMessage_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, fake_depth_interfaces, action, Dive_FeedbackMessage)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, fake_depth_interfaces, action, Dive_FeedbackMessage)),
  }
};

typedef struct _Dive_FeedbackMessage_type_support_data_t
{
  void * data[2];
} _Dive_FeedbackMessage_type_support_data_t;

static _Dive_FeedbackMessage_type_support_data_t _Dive_FeedbackMessage_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _Dive_FeedbackMessage_message_typesupport_map = {
  2,
  "fake_depth_interfaces",
  &_Dive_FeedbackMessage_message_typesupport_ids.typesupport_identifier[0],
  &_Dive_FeedbackMessage_message_typesupport_symbol_names.symbol_name[0],
  &_Dive_FeedbackMessage_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t Dive_FeedbackMessage_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_Dive_FeedbackMessage_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace fake_depth_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, fake_depth_interfaces, action, Dive_FeedbackMessage)() {
  return &::fake_depth_interfaces::action::rosidl_typesupport_c::Dive_FeedbackMessage_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

#include "action_msgs/msg/goal_status_array.h"
#include "action_msgs/srv/cancel_goal.h"
#include "fake_depth_interfaces/action/dive.h"
// already included above
// #include "fake_depth_interfaces/action/detail/dive__type_support.h"

static rosidl_action_type_support_t _fake_depth_interfaces__action__Dive__typesupport_c;

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_action_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__ACTION_SYMBOL_NAME(
  rosidl_typesupport_c, fake_depth_interfaces, action, Dive)()
{
  // Thread-safe by always writing the same values to the static struct
  _fake_depth_interfaces__action__Dive__typesupport_c.goal_service_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_c, fake_depth_interfaces, action, Dive_SendGoal)();
  _fake_depth_interfaces__action__Dive__typesupport_c.result_service_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_c, fake_depth_interfaces, action, Dive_GetResult)();
  _fake_depth_interfaces__action__Dive__typesupport_c.cancel_service_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_c, action_msgs, srv, CancelGoal)();
  _fake_depth_interfaces__action__Dive__typesupport_c.feedback_message_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c, fake_depth_interfaces, action, Dive_FeedbackMessage)();
  _fake_depth_interfaces__action__Dive__typesupport_c.status_message_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c, action_msgs, msg, GoalStatusArray)();

  return &_fake_depth_interfaces__action__Dive__typesupport_c;
}

#ifdef __cplusplus
}
#endif
