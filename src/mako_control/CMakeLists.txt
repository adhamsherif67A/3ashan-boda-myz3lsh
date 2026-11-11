cmake_minimum_required(VERSION 3.8)
project(mako_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rcl_interfaces REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(mavros_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(std_msgs REQUIRED)

# Pilot control: gamepad /joy (and Operation MX autopilot/keyboard commands)
# to MAVROS MANUAL_CONTROL, arming and flight-mode requests.
add_executable(realjoy_node src/joystick.cpp)
target_include_directories(realjoy_node PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
target_compile_features(realjoy_node PRIVATE cxx_std_17)
ament_target_dependencies(realjoy_node rcl_interfaces rclcpp sensor_msgs mavros_msgs std_srvs std_msgs)
install(TARGETS realjoy_node DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})
install(FILES JOYSTICK.md DESTINATION share/${PROJECT_NAME})

install(
  PROGRAMS
    scripts/autotune.py
    scripts/fix_ardusub_params.py
    scripts/fly_transect_mission.py
    scripts/gz_odom_to_mavros.py
    scripts/local_waypoint_mission.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(external_nav test/test_external_nav.py)
  ament_add_pytest_test(autotune_client test/test_autotune_client.py)
endif()

ament_package()
