// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from fake_depth_interfaces:action/Dive.idl
// generated code does not contain a copyright notice
#include "fake_depth_interfaces/action/detail/dive__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
fake_depth_interfaces__action__Dive_Goal__init(fake_depth_interfaces__action__Dive_Goal * msg)
{
  if (!msg) {
    return false;
  }
  // target_depth
  return true;
}

void
fake_depth_interfaces__action__Dive_Goal__fini(fake_depth_interfaces__action__Dive_Goal * msg)
{
  if (!msg) {
    return;
  }
  // target_depth
}

bool
fake_depth_interfaces__action__Dive_Goal__are_equal(const fake_depth_interfaces__action__Dive_Goal * lhs, const fake_depth_interfaces__action__Dive_Goal * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // target_depth
  if (lhs->target_depth != rhs->target_depth) {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_Goal__copy(
  const fake_depth_interfaces__action__Dive_Goal * input,
  fake_depth_interfaces__action__Dive_Goal * output)
{
  if (!input || !output) {
    return false;
  }
  // target_depth
  output->target_depth = input->target_depth;
  return true;
}

fake_depth_interfaces__action__Dive_Goal *
fake_depth_interfaces__action__Dive_Goal__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Goal * msg = (fake_depth_interfaces__action__Dive_Goal *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_Goal), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_Goal));
  bool success = fake_depth_interfaces__action__Dive_Goal__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_Goal__destroy(fake_depth_interfaces__action__Dive_Goal * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_Goal__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_Goal__Sequence__init(fake_depth_interfaces__action__Dive_Goal__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Goal * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_Goal *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_Goal), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_Goal__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_Goal__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_Goal__Sequence__fini(fake_depth_interfaces__action__Dive_Goal__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_Goal__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_Goal__Sequence *
fake_depth_interfaces__action__Dive_Goal__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Goal__Sequence * array = (fake_depth_interfaces__action__Dive_Goal__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_Goal__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_Goal__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_Goal__Sequence__destroy(fake_depth_interfaces__action__Dive_Goal__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_Goal__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_Goal__Sequence__are_equal(const fake_depth_interfaces__action__Dive_Goal__Sequence * lhs, const fake_depth_interfaces__action__Dive_Goal__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_Goal__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_Goal__Sequence__copy(
  const fake_depth_interfaces__action__Dive_Goal__Sequence * input,
  fake_depth_interfaces__action__Dive_Goal__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_Goal);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_Goal * data =
      (fake_depth_interfaces__action__Dive_Goal *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_Goal__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_Goal__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_Goal__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
fake_depth_interfaces__action__Dive_Result__init(fake_depth_interfaces__action__Dive_Result * msg)
{
  if (!msg) {
    return false;
  }
  // success
  return true;
}

void
fake_depth_interfaces__action__Dive_Result__fini(fake_depth_interfaces__action__Dive_Result * msg)
{
  if (!msg) {
    return;
  }
  // success
}

bool
fake_depth_interfaces__action__Dive_Result__are_equal(const fake_depth_interfaces__action__Dive_Result * lhs, const fake_depth_interfaces__action__Dive_Result * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_Result__copy(
  const fake_depth_interfaces__action__Dive_Result * input,
  fake_depth_interfaces__action__Dive_Result * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  return true;
}

fake_depth_interfaces__action__Dive_Result *
fake_depth_interfaces__action__Dive_Result__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Result * msg = (fake_depth_interfaces__action__Dive_Result *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_Result), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_Result));
  bool success = fake_depth_interfaces__action__Dive_Result__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_Result__destroy(fake_depth_interfaces__action__Dive_Result * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_Result__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_Result__Sequence__init(fake_depth_interfaces__action__Dive_Result__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Result * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_Result *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_Result), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_Result__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_Result__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_Result__Sequence__fini(fake_depth_interfaces__action__Dive_Result__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_Result__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_Result__Sequence *
fake_depth_interfaces__action__Dive_Result__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Result__Sequence * array = (fake_depth_interfaces__action__Dive_Result__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_Result__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_Result__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_Result__Sequence__destroy(fake_depth_interfaces__action__Dive_Result__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_Result__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_Result__Sequence__are_equal(const fake_depth_interfaces__action__Dive_Result__Sequence * lhs, const fake_depth_interfaces__action__Dive_Result__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_Result__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_Result__Sequence__copy(
  const fake_depth_interfaces__action__Dive_Result__Sequence * input,
  fake_depth_interfaces__action__Dive_Result__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_Result);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_Result * data =
      (fake_depth_interfaces__action__Dive_Result *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_Result__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_Result__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_Result__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
fake_depth_interfaces__action__Dive_Feedback__init(fake_depth_interfaces__action__Dive_Feedback * msg)
{
  if (!msg) {
    return false;
  }
  // current_depth
  return true;
}

void
fake_depth_interfaces__action__Dive_Feedback__fini(fake_depth_interfaces__action__Dive_Feedback * msg)
{
  if (!msg) {
    return;
  }
  // current_depth
}

bool
fake_depth_interfaces__action__Dive_Feedback__are_equal(const fake_depth_interfaces__action__Dive_Feedback * lhs, const fake_depth_interfaces__action__Dive_Feedback * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // current_depth
  if (lhs->current_depth != rhs->current_depth) {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_Feedback__copy(
  const fake_depth_interfaces__action__Dive_Feedback * input,
  fake_depth_interfaces__action__Dive_Feedback * output)
{
  if (!input || !output) {
    return false;
  }
  // current_depth
  output->current_depth = input->current_depth;
  return true;
}

fake_depth_interfaces__action__Dive_Feedback *
fake_depth_interfaces__action__Dive_Feedback__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Feedback * msg = (fake_depth_interfaces__action__Dive_Feedback *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_Feedback), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_Feedback));
  bool success = fake_depth_interfaces__action__Dive_Feedback__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_Feedback__destroy(fake_depth_interfaces__action__Dive_Feedback * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_Feedback__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_Feedback__Sequence__init(fake_depth_interfaces__action__Dive_Feedback__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Feedback * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_Feedback *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_Feedback), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_Feedback__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_Feedback__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_Feedback__Sequence__fini(fake_depth_interfaces__action__Dive_Feedback__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_Feedback__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_Feedback__Sequence *
fake_depth_interfaces__action__Dive_Feedback__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_Feedback__Sequence * array = (fake_depth_interfaces__action__Dive_Feedback__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_Feedback__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_Feedback__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_Feedback__Sequence__destroy(fake_depth_interfaces__action__Dive_Feedback__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_Feedback__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_Feedback__Sequence__are_equal(const fake_depth_interfaces__action__Dive_Feedback__Sequence * lhs, const fake_depth_interfaces__action__Dive_Feedback__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_Feedback__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_Feedback__Sequence__copy(
  const fake_depth_interfaces__action__Dive_Feedback__Sequence * input,
  fake_depth_interfaces__action__Dive_Feedback__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_Feedback);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_Feedback * data =
      (fake_depth_interfaces__action__Dive_Feedback *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_Feedback__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_Feedback__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_Feedback__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
#include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `goal`
// already included above
// #include "fake_depth_interfaces/action/detail/dive__functions.h"

bool
fake_depth_interfaces__action__Dive_SendGoal_Request__init(fake_depth_interfaces__action__Dive_SendGoal_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    fake_depth_interfaces__action__Dive_SendGoal_Request__fini(msg);
    return false;
  }
  // goal
  if (!fake_depth_interfaces__action__Dive_Goal__init(&msg->goal)) {
    fake_depth_interfaces__action__Dive_SendGoal_Request__fini(msg);
    return false;
  }
  return true;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Request__fini(fake_depth_interfaces__action__Dive_SendGoal_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // goal
  fake_depth_interfaces__action__Dive_Goal__fini(&msg->goal);
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Request__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Request * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // goal
  if (!fake_depth_interfaces__action__Dive_Goal__are_equal(
      &(lhs->goal), &(rhs->goal)))
  {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Request__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Request * input,
  fake_depth_interfaces__action__Dive_SendGoal_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // goal
  if (!fake_depth_interfaces__action__Dive_Goal__copy(
      &(input->goal), &(output->goal)))
  {
    return false;
  }
  return true;
}

fake_depth_interfaces__action__Dive_SendGoal_Request *
fake_depth_interfaces__action__Dive_SendGoal_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_SendGoal_Request * msg = (fake_depth_interfaces__action__Dive_SendGoal_Request *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_SendGoal_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_SendGoal_Request));
  bool success = fake_depth_interfaces__action__Dive_SendGoal_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Request__destroy(fake_depth_interfaces__action__Dive_SendGoal_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_SendGoal_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__init(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_SendGoal_Request * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_SendGoal_Request *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_SendGoal_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_SendGoal_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_SendGoal_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__fini(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_SendGoal_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence *
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array = (fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__destroy(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_SendGoal_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * input,
  fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_SendGoal_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_SendGoal_Request * data =
      (fake_depth_interfaces__action__Dive_SendGoal_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_SendGoal_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_SendGoal_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_SendGoal_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
fake_depth_interfaces__action__Dive_SendGoal_Response__init(fake_depth_interfaces__action__Dive_SendGoal_Response * msg)
{
  if (!msg) {
    return false;
  }
  // accepted
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    fake_depth_interfaces__action__Dive_SendGoal_Response__fini(msg);
    return false;
  }
  return true;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Response__fini(fake_depth_interfaces__action__Dive_SendGoal_Response * msg)
{
  if (!msg) {
    return;
  }
  // accepted
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Response__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Response * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // accepted
  if (lhs->accepted != rhs->accepted) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Response__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Response * input,
  fake_depth_interfaces__action__Dive_SendGoal_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // accepted
  output->accepted = input->accepted;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

fake_depth_interfaces__action__Dive_SendGoal_Response *
fake_depth_interfaces__action__Dive_SendGoal_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_SendGoal_Response * msg = (fake_depth_interfaces__action__Dive_SendGoal_Response *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_SendGoal_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_SendGoal_Response));
  bool success = fake_depth_interfaces__action__Dive_SendGoal_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Response__destroy(fake_depth_interfaces__action__Dive_SendGoal_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_SendGoal_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__init(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_SendGoal_Response * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_SendGoal_Response *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_SendGoal_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_SendGoal_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_SendGoal_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__fini(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_SendGoal_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence *
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array = (fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__destroy(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_SendGoal_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * input,
  fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_SendGoal_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_SendGoal_Response * data =
      (fake_depth_interfaces__action__Dive_SendGoal_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_SendGoal_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_SendGoal_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_SendGoal_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"

bool
fake_depth_interfaces__action__Dive_GetResult_Request__init(fake_depth_interfaces__action__Dive_GetResult_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    fake_depth_interfaces__action__Dive_GetResult_Request__fini(msg);
    return false;
  }
  return true;
}

void
fake_depth_interfaces__action__Dive_GetResult_Request__fini(fake_depth_interfaces__action__Dive_GetResult_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
}

bool
fake_depth_interfaces__action__Dive_GetResult_Request__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Request * lhs, const fake_depth_interfaces__action__Dive_GetResult_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_GetResult_Request__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Request * input,
  fake_depth_interfaces__action__Dive_GetResult_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  return true;
}

fake_depth_interfaces__action__Dive_GetResult_Request *
fake_depth_interfaces__action__Dive_GetResult_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_GetResult_Request * msg = (fake_depth_interfaces__action__Dive_GetResult_Request *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_GetResult_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_GetResult_Request));
  bool success = fake_depth_interfaces__action__Dive_GetResult_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_GetResult_Request__destroy(fake_depth_interfaces__action__Dive_GetResult_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_GetResult_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__init(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_GetResult_Request * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_GetResult_Request *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_GetResult_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_GetResult_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_GetResult_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__fini(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_GetResult_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_GetResult_Request__Sequence *
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array = (fake_depth_interfaces__action__Dive_GetResult_Request__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__destroy(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * lhs, const fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_GetResult_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * input,
  fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_GetResult_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_GetResult_Request * data =
      (fake_depth_interfaces__action__Dive_GetResult_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_GetResult_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_GetResult_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_GetResult_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `result`
// already included above
// #include "fake_depth_interfaces/action/detail/dive__functions.h"

bool
fake_depth_interfaces__action__Dive_GetResult_Response__init(fake_depth_interfaces__action__Dive_GetResult_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  // result
  if (!fake_depth_interfaces__action__Dive_Result__init(&msg->result)) {
    fake_depth_interfaces__action__Dive_GetResult_Response__fini(msg);
    return false;
  }
  return true;
}

void
fake_depth_interfaces__action__Dive_GetResult_Response__fini(fake_depth_interfaces__action__Dive_GetResult_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
  // result
  fake_depth_interfaces__action__Dive_Result__fini(&msg->result);
}

bool
fake_depth_interfaces__action__Dive_GetResult_Response__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Response * lhs, const fake_depth_interfaces__action__Dive_GetResult_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  // result
  if (!fake_depth_interfaces__action__Dive_Result__are_equal(
      &(lhs->result), &(rhs->result)))
  {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_GetResult_Response__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Response * input,
  fake_depth_interfaces__action__Dive_GetResult_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  output->status = input->status;
  // result
  if (!fake_depth_interfaces__action__Dive_Result__copy(
      &(input->result), &(output->result)))
  {
    return false;
  }
  return true;
}

fake_depth_interfaces__action__Dive_GetResult_Response *
fake_depth_interfaces__action__Dive_GetResult_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_GetResult_Response * msg = (fake_depth_interfaces__action__Dive_GetResult_Response *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_GetResult_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_GetResult_Response));
  bool success = fake_depth_interfaces__action__Dive_GetResult_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_GetResult_Response__destroy(fake_depth_interfaces__action__Dive_GetResult_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_GetResult_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__init(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_GetResult_Response * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_GetResult_Response *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_GetResult_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_GetResult_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_GetResult_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__fini(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_GetResult_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_GetResult_Response__Sequence *
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array = (fake_depth_interfaces__action__Dive_GetResult_Response__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__destroy(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * lhs, const fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_GetResult_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * input,
  fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_GetResult_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_GetResult_Response * data =
      (fake_depth_interfaces__action__Dive_GetResult_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_GetResult_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_GetResult_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_GetResult_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `feedback`
// already included above
// #include "fake_depth_interfaces/action/detail/dive__functions.h"

bool
fake_depth_interfaces__action__Dive_FeedbackMessage__init(fake_depth_interfaces__action__Dive_FeedbackMessage * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    fake_depth_interfaces__action__Dive_FeedbackMessage__fini(msg);
    return false;
  }
  // feedback
  if (!fake_depth_interfaces__action__Dive_Feedback__init(&msg->feedback)) {
    fake_depth_interfaces__action__Dive_FeedbackMessage__fini(msg);
    return false;
  }
  return true;
}

void
fake_depth_interfaces__action__Dive_FeedbackMessage__fini(fake_depth_interfaces__action__Dive_FeedbackMessage * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // feedback
  fake_depth_interfaces__action__Dive_Feedback__fini(&msg->feedback);
}

bool
fake_depth_interfaces__action__Dive_FeedbackMessage__are_equal(const fake_depth_interfaces__action__Dive_FeedbackMessage * lhs, const fake_depth_interfaces__action__Dive_FeedbackMessage * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // feedback
  if (!fake_depth_interfaces__action__Dive_Feedback__are_equal(
      &(lhs->feedback), &(rhs->feedback)))
  {
    return false;
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_FeedbackMessage__copy(
  const fake_depth_interfaces__action__Dive_FeedbackMessage * input,
  fake_depth_interfaces__action__Dive_FeedbackMessage * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // feedback
  if (!fake_depth_interfaces__action__Dive_Feedback__copy(
      &(input->feedback), &(output->feedback)))
  {
    return false;
  }
  return true;
}

fake_depth_interfaces__action__Dive_FeedbackMessage *
fake_depth_interfaces__action__Dive_FeedbackMessage__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_FeedbackMessage * msg = (fake_depth_interfaces__action__Dive_FeedbackMessage *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_FeedbackMessage), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(fake_depth_interfaces__action__Dive_FeedbackMessage));
  bool success = fake_depth_interfaces__action__Dive_FeedbackMessage__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
fake_depth_interfaces__action__Dive_FeedbackMessage__destroy(fake_depth_interfaces__action__Dive_FeedbackMessage * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    fake_depth_interfaces__action__Dive_FeedbackMessage__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__init(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_FeedbackMessage * data = NULL;

  if (size) {
    data = (fake_depth_interfaces__action__Dive_FeedbackMessage *)allocator.zero_allocate(size, sizeof(fake_depth_interfaces__action__Dive_FeedbackMessage), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = fake_depth_interfaces__action__Dive_FeedbackMessage__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        fake_depth_interfaces__action__Dive_FeedbackMessage__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__fini(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      fake_depth_interfaces__action__Dive_FeedbackMessage__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence *
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array = (fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence *)allocator.allocate(sizeof(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__destroy(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__are_equal(const fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * lhs, const fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_FeedbackMessage__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__copy(
  const fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * input,
  fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(fake_depth_interfaces__action__Dive_FeedbackMessage);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    fake_depth_interfaces__action__Dive_FeedbackMessage * data =
      (fake_depth_interfaces__action__Dive_FeedbackMessage *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!fake_depth_interfaces__action__Dive_FeedbackMessage__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          fake_depth_interfaces__action__Dive_FeedbackMessage__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!fake_depth_interfaces__action__Dive_FeedbackMessage__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
