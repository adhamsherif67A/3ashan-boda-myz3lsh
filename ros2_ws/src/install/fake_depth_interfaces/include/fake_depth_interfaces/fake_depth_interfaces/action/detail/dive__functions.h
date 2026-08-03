// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from fake_depth_interfaces:action/Dive.idl
// generated code does not contain a copyright notice

#ifndef FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__FUNCTIONS_H_
#define FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "fake_depth_interfaces/msg/rosidl_generator_c__visibility_control.h"

#include "fake_depth_interfaces/action/detail/dive__struct.h"

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_Goal
 * )) before or use
 * fake_depth_interfaces__action__Dive_Goal__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Goal__init(fake_depth_interfaces__action__Dive_Goal * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Goal__fini(fake_depth_interfaces__action__Dive_Goal * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_Goal__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_Goal *
fake_depth_interfaces__action__Dive_Goal__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Goal__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Goal__destroy(fake_depth_interfaces__action__Dive_Goal * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Goal__are_equal(const fake_depth_interfaces__action__Dive_Goal * lhs, const fake_depth_interfaces__action__Dive_Goal * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Goal__copy(
  const fake_depth_interfaces__action__Dive_Goal * input,
  fake_depth_interfaces__action__Dive_Goal * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_Goal__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Goal__Sequence__init(fake_depth_interfaces__action__Dive_Goal__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Goal__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Goal__Sequence__fini(fake_depth_interfaces__action__Dive_Goal__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_Goal__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_Goal__Sequence *
fake_depth_interfaces__action__Dive_Goal__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Goal__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Goal__Sequence__destroy(fake_depth_interfaces__action__Dive_Goal__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Goal__Sequence__are_equal(const fake_depth_interfaces__action__Dive_Goal__Sequence * lhs, const fake_depth_interfaces__action__Dive_Goal__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Goal__Sequence__copy(
  const fake_depth_interfaces__action__Dive_Goal__Sequence * input,
  fake_depth_interfaces__action__Dive_Goal__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_Result
 * )) before or use
 * fake_depth_interfaces__action__Dive_Result__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Result__init(fake_depth_interfaces__action__Dive_Result * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Result__fini(fake_depth_interfaces__action__Dive_Result * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_Result__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_Result *
fake_depth_interfaces__action__Dive_Result__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Result__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Result__destroy(fake_depth_interfaces__action__Dive_Result * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Result__are_equal(const fake_depth_interfaces__action__Dive_Result * lhs, const fake_depth_interfaces__action__Dive_Result * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Result__copy(
  const fake_depth_interfaces__action__Dive_Result * input,
  fake_depth_interfaces__action__Dive_Result * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_Result__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Result__Sequence__init(fake_depth_interfaces__action__Dive_Result__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Result__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Result__Sequence__fini(fake_depth_interfaces__action__Dive_Result__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_Result__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_Result__Sequence *
fake_depth_interfaces__action__Dive_Result__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Result__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Result__Sequence__destroy(fake_depth_interfaces__action__Dive_Result__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Result__Sequence__are_equal(const fake_depth_interfaces__action__Dive_Result__Sequence * lhs, const fake_depth_interfaces__action__Dive_Result__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Result__Sequence__copy(
  const fake_depth_interfaces__action__Dive_Result__Sequence * input,
  fake_depth_interfaces__action__Dive_Result__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_Feedback
 * )) before or use
 * fake_depth_interfaces__action__Dive_Feedback__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Feedback__init(fake_depth_interfaces__action__Dive_Feedback * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Feedback__fini(fake_depth_interfaces__action__Dive_Feedback * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_Feedback__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_Feedback *
fake_depth_interfaces__action__Dive_Feedback__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Feedback__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Feedback__destroy(fake_depth_interfaces__action__Dive_Feedback * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Feedback__are_equal(const fake_depth_interfaces__action__Dive_Feedback * lhs, const fake_depth_interfaces__action__Dive_Feedback * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Feedback__copy(
  const fake_depth_interfaces__action__Dive_Feedback * input,
  fake_depth_interfaces__action__Dive_Feedback * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_Feedback__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Feedback__Sequence__init(fake_depth_interfaces__action__Dive_Feedback__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Feedback__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Feedback__Sequence__fini(fake_depth_interfaces__action__Dive_Feedback__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_Feedback__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_Feedback__Sequence *
fake_depth_interfaces__action__Dive_Feedback__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_Feedback__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_Feedback__Sequence__destroy(fake_depth_interfaces__action__Dive_Feedback__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Feedback__Sequence__are_equal(const fake_depth_interfaces__action__Dive_Feedback__Sequence * lhs, const fake_depth_interfaces__action__Dive_Feedback__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_Feedback__Sequence__copy(
  const fake_depth_interfaces__action__Dive_Feedback__Sequence * input,
  fake_depth_interfaces__action__Dive_Feedback__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_SendGoal_Request
 * )) before or use
 * fake_depth_interfaces__action__Dive_SendGoal_Request__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Request__init(fake_depth_interfaces__action__Dive_SendGoal_Request * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Request__fini(fake_depth_interfaces__action__Dive_SendGoal_Request * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_SendGoal_Request__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_SendGoal_Request *
fake_depth_interfaces__action__Dive_SendGoal_Request__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_SendGoal_Request__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Request__destroy(fake_depth_interfaces__action__Dive_SendGoal_Request * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Request__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Request * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Request * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Request__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Request * input,
  fake_depth_interfaces__action__Dive_SendGoal_Request * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_SendGoal_Request__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__init(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_SendGoal_Request__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__fini(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence *
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__destroy(fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * input,
  fake_depth_interfaces__action__Dive_SendGoal_Request__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_SendGoal_Response
 * )) before or use
 * fake_depth_interfaces__action__Dive_SendGoal_Response__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Response__init(fake_depth_interfaces__action__Dive_SendGoal_Response * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Response__fini(fake_depth_interfaces__action__Dive_SendGoal_Response * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_SendGoal_Response__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_SendGoal_Response *
fake_depth_interfaces__action__Dive_SendGoal_Response__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_SendGoal_Response__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Response__destroy(fake_depth_interfaces__action__Dive_SendGoal_Response * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Response__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Response * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Response * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Response__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Response * input,
  fake_depth_interfaces__action__Dive_SendGoal_Response * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_SendGoal_Response__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__init(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_SendGoal_Response__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__fini(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence *
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__destroy(fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__are_equal(const fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * lhs, const fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence__copy(
  const fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * input,
  fake_depth_interfaces__action__Dive_SendGoal_Response__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_GetResult_Request
 * )) before or use
 * fake_depth_interfaces__action__Dive_GetResult_Request__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Request__init(fake_depth_interfaces__action__Dive_GetResult_Request * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Request__fini(fake_depth_interfaces__action__Dive_GetResult_Request * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_GetResult_Request__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_GetResult_Request *
fake_depth_interfaces__action__Dive_GetResult_Request__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_GetResult_Request__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Request__destroy(fake_depth_interfaces__action__Dive_GetResult_Request * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Request__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Request * lhs, const fake_depth_interfaces__action__Dive_GetResult_Request * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Request__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Request * input,
  fake_depth_interfaces__action__Dive_GetResult_Request * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_GetResult_Request__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__init(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_GetResult_Request__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__fini(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence *
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__destroy(fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * lhs, const fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Request__Sequence__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * input,
  fake_depth_interfaces__action__Dive_GetResult_Request__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_GetResult_Response
 * )) before or use
 * fake_depth_interfaces__action__Dive_GetResult_Response__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Response__init(fake_depth_interfaces__action__Dive_GetResult_Response * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Response__fini(fake_depth_interfaces__action__Dive_GetResult_Response * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_GetResult_Response__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_GetResult_Response *
fake_depth_interfaces__action__Dive_GetResult_Response__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_GetResult_Response__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Response__destroy(fake_depth_interfaces__action__Dive_GetResult_Response * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Response__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Response * lhs, const fake_depth_interfaces__action__Dive_GetResult_Response * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Response__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Response * input,
  fake_depth_interfaces__action__Dive_GetResult_Response * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_GetResult_Response__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__init(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_GetResult_Response__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__fini(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence *
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__destroy(fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__are_equal(const fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * lhs, const fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_GetResult_Response__Sequence__copy(
  const fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * input,
  fake_depth_interfaces__action__Dive_GetResult_Response__Sequence * output);

/// Initialize action/Dive message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * fake_depth_interfaces__action__Dive_FeedbackMessage
 * )) before or use
 * fake_depth_interfaces__action__Dive_FeedbackMessage__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_FeedbackMessage__init(fake_depth_interfaces__action__Dive_FeedbackMessage * msg);

/// Finalize action/Dive message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_FeedbackMessage__fini(fake_depth_interfaces__action__Dive_FeedbackMessage * msg);

/// Create action/Dive message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * fake_depth_interfaces__action__Dive_FeedbackMessage__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_FeedbackMessage *
fake_depth_interfaces__action__Dive_FeedbackMessage__create();

/// Destroy action/Dive message.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_FeedbackMessage__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_FeedbackMessage__destroy(fake_depth_interfaces__action__Dive_FeedbackMessage * msg);

/// Check for action/Dive message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_FeedbackMessage__are_equal(const fake_depth_interfaces__action__Dive_FeedbackMessage * lhs, const fake_depth_interfaces__action__Dive_FeedbackMessage * rhs);

/// Copy a action/Dive message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_FeedbackMessage__copy(
  const fake_depth_interfaces__action__Dive_FeedbackMessage * input,
  fake_depth_interfaces__action__Dive_FeedbackMessage * output);

/// Initialize array of action/Dive messages.
/**
 * It allocates the memory for the number of elements and calls
 * fake_depth_interfaces__action__Dive_FeedbackMessage__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__init(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array, size_t size);

/// Finalize array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_FeedbackMessage__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__fini(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array);

/// Create array of action/Dive messages.
/**
 * It allocates the memory for the array and calls
 * fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence *
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__create(size_t size);

/// Destroy array of action/Dive messages.
/**
 * It calls
 * fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
void
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__destroy(fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * array);

/// Check for action/Dive message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__are_equal(const fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * lhs, const fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * rhs);

/// Copy an array of action/Dive messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_fake_depth_interfaces
bool
fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence__copy(
  const fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * input,
  fake_depth_interfaces__action__Dive_FeedbackMessage__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // FAKE_DEPTH_INTERFACES__ACTION__DETAIL__DIVE__FUNCTIONS_H_
