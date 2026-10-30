#!/usr/bin/env bash
set -eo pipefail
# Run on the Ubuntu host: SDL needs /dev/input/event*, not just /dev/input/js0.
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
exec ros2 run joy game_controller_node --ros-args \
  -p device_id:="${PS4_DEVICE_ID:-0}" -p deadzone:=0.0 \
  -p autorepeat_rate:=50.0 -p sticky_buttons:=false "$@"
