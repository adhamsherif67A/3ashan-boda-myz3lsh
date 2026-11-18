#!/usr/bin/env bash
set -euo pipefail
workspace=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
container=${FISH_CONTAINER_NAME:-fish-omni-six}
[[ -n "${DISPLAY:-}" ]] || { echo 'Launch from the Ubuntu desktop.' >&2; exit 1; }
auth_copy=$(mktemp)
auth_result=$(mktemp)
trap 'rm -f "$auth_copy" "$auth_result" "$auth_copy"-c "$auth_copy"-l "$auth_result"-c "$auth_result"-l' EXIT
cp "${XAUTHORITY:-$HOME/.Xauthority}" "$auth_copy"
xauth -f "$auth_copy" nlist "$DISPLAY" | sed 's/^..../ffff/' | xauth -f "$auth_result" nmerge -
[[ -s "$auth_result" ]] || { echo 'Desktop X11 authentication is unavailable.' >&2; exit 1; }
cat "$auth_result" > "$workspace/.runtime/mako.xauth"
chmod 600 "$workspace/.runtime/mako.xauth"
if ! docker inspect "$container" >/dev/null 2>&1; then
  echo 'Create the runtime first: python3 tools/setup_container.py --build' >&2
  exit 1
fi
if [[ $(docker inspect -f '{{.State.Running}}' "$container") != true ]]; then docker start "$container" >/dev/null; fi
docker exec --env "DISPLAY=$DISPLAY" --env ROS_DOMAIN_ID=73 --env MAKO_SIM_ROS_DOMAIN_ID=73 \
  --env MAKO_PERFORMANCE_PROFILE=maximum_fps --env MAKO_PILOT_FPS=60 --env MAKO_CAMERA_FPS=30 \
  --env MAKO_PILOT_WIDTH=1280 --env MAKO_PILOT_HEIGHT=720 --env MAKO_JOYSTICK_SMOOTHING=0.02 \
  --env MAKO_GPU_VIDEO=1 --env __GLX_VENDOR_LIBRARY_NAME=nvidia --env __NV_PRIME_RENDER_OFFLOAD=1 \
  --env QT_OPENGL=desktop --env FASTRTPS_DEFAULT_PROFILES_FILE=/opt/mako_ws/gui/mako_station/assets/fastdds_hd.xml \
  "$container" bash -c 'source /opt/ros/humble/setup.bash && source /opt/mako_ws/install/setup.bash && exec python3 /opt/mako_ws/gui/rov_gui_gst.py "$@"' bash "$@"
