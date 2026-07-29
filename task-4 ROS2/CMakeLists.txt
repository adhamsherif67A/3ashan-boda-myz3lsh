cmake_minimum_required(VERSION 3.8)
project(marine_xperts_depth)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(depth_simulator src/rov_depth_simulator.cpp)
ament_target_dependencies(depth_simulator rclcpp std_msgs)

add_executable(depth_monitor src/rov_depth_monitor.cpp)
ament_target_dependencies(depth_monitor rclcpp std_msgs)

install(TARGETS
  depth_simulator
  depth_monitor
  DESTINATION lib/${PROJECT_NAME})

ament_package()