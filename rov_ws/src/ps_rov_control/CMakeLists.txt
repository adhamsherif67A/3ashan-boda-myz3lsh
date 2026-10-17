cmake_minimum_required(VERSION 3.8)
project(ps_rov_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(mavros_msgs REQUIRED)

# -----------------------------------------------------------------------------
# Executable Build
# -----------------------------------------------------------------------------
add_executable(game_controller src/game_controller.cpp)

target_compile_features(game_controller PUBLIC c_std_99 cxx_std_17)

ament_target_dependencies(game_controller
  rclcpp
  sensor_msgs
  mavros_msgs
)

# -----------------------------------------------------------------------------
# Installation Rules
# -----------------------------------------------------------------------------
install(TARGETS
  game_controller
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
