#!/usr/bin/env bash
# Run the Mako image. Modes:
#   docker/run.sh [simulation options]   simulation without the app (Gazebo GUI unless --headless)
#   docker/run.sh --gui                  Operation MX pilot station; start the simulation from the app
#   docker/run.sh --doctor               read-only dependency check
#   docker/run.sh --shell                bash inside the container (ROS environment sourced)
# Common options: --nvidia (NVIDIA GPU), --no-joystick (do not pass /dev/input)
set -euo pipefail
image="${MAKO_IMAGE:-marinexperts/mako:latest}"
name="${MAKO_CONTAINER_NAME:-mako-sim}"
data="${MAKO_DATA_DIR:-$HOME/mako-data}"
mode=simulation;headless=false;nvidia=false;joystick=true
arguments=()
for argument in "$@"; do
  case "$argument" in
    --gui) mode=gui ;;
    --doctor) mode=doctor;headless=true ;;
    --shell) mode=shell ;;
    --nvidia) nvidia=true ;;
    --no-joystick) joystick=false ;;
    --headless) headless=true ;;
    --help|-h)
      sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'
      echo 'Simulation options: [--world pool.world|ocean.world] [--headless] [--odometry-source ground_truth|vision]'
      echo '  [--slam] [--pilot] [--no-gamepad] [--pilot-fps 30|60] [--performance-profile maximum_fps|balanced|vision_quality|full_sensors]'
      echo '  [--instance N] [--log-dir DIR] [--dry-run]'
      exit 0 ;;
    *) arguments+=("$argument") ;;
  esac
done
command -v docker >/dev/null || { echo 'Install Docker first; see README.md.' >&2;exit 1; }
docker image inspect "$image" >/dev/null 2>&1 || { echo 'Run ./docker/build.sh first.' >&2;exit 1; }
mkdir -p "$data"
options=(--rm --init --name "$name" --network host --ipc host --stop-timeout 15
         --env "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-42}" --env RMW_IMPLEMENTATION=rmw_fastrtps_cpp
         --volume "$data:/data:rw")
if [[ -n "${LIBGL_ALWAYS_SOFTWARE:-}" ]]; then options+=(--env LIBGL_ALWAYS_SOFTWARE);fi
if [[ -t 0 && -t 1 ]]; then options+=(-it);fi
for device in /dev/dri/card* /dev/dri/renderD*; do
  [[ -c "$device" ]] || continue
  options+=(--device "$device" --group-add "$(stat -c '%g' "$device")")
done
# Gamepads: share /dev/input (character major 13) so a controller plugged in later also works.
if $joystick && [[ -d /dev/input ]]; then
  options+=(--volume /dev/input:/dev/input:ro --device-cgroup-rule 'c 13:* rmw')
  for device in /dev/input/js0 /dev/input/event0; do
    [[ -c "$device" ]] && { options+=(--group-add "$(stat -c '%g' "$device")");break; }
  done
fi
if $nvidia; then options+=(--gpus all --env NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute);fi
cookie=''
cleanup() { if [[ -n "$cookie" ]]; then rm -f -- "$cookie";fi; }
trap cleanup EXIT
if ! $headless; then
  [[ -n "${DISPLAY:-}" && -d /tmp/.X11-unix ]] || { echo 'An X11/XWayland display is required; use --headless on servers.' >&2;exit 1; }
  command -v xauth >/dev/null || { echo 'Install host package xauth for GUI access, or use --headless.' >&2;exit 1; }
  cookie="$(mktemp)";chmod 644 "$cookie"
  xauth nlist "$DISPLAY" | sed 's/^..../ffff/' | xauth -f "$cookie" nmerge -
  [[ -s "$cookie" ]] || { echo 'No X11 authentication cookie found for DISPLAY.' >&2;exit 1; }
  options+=(--env DISPLAY --env QT_X11_NO_MITSHM=1 --env XAUTHORITY=/tmp/mako.xauth
            --volume /tmp/.X11-unix:/tmp/.X11-unix:rw --volume "$cookie:/tmp/mako.xauth:ro")
fi
case "$mode" in
  simulation) if $headless; then arguments=(--headless "${arguments[@]}"); fi
              exec_args=(simulation "${arguments[@]}") ;;
  gui) exec_args=(gui "${arguments[@]}") ;;
  doctor) exec_args=(doctor) ;;
  shell) exec_args=(shell "${arguments[@]}") ;;
esac
docker run "${options[@]}" "$image" "${exec_args[@]}"
