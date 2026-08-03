# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target fake_depth_interfaces::fake_depth_interfaces
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${fake_depth_interfaces_TARGETS}.
if(fake_depth_interfaces_TARGETS AND NOT TARGET fake_depth_interfaces::fake_depth_interfaces)
  add_library(fake_depth_interfaces::fake_depth_interfaces INTERFACE IMPORTED)
  set_target_properties(fake_depth_interfaces::fake_depth_interfaces PROPERTIES
    INTERFACE_LINK_LIBRARIES "${fake_depth_interfaces_TARGETS}")
endif()
