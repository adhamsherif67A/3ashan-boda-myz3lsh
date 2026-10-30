#!/usr/bin/env bash
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
container="${POOL_CONTAINER_NAME:-mako-pool-sim}"
image="${POOL_IMAGE:-marinexperts/mako-pool-mapping:boda}"
result_dir="${POOL_OUTPUT_DIR:-$(dirname "$package_dir")/pool_mapping_results/$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$result_dir"
result_dir="$(cd "$result_dir" && pwd)"
[[ -n "${DISPLAY:-}" ]] || { echo 'Use an Ubuntu desktop terminal with DISPLAY.' >&2; exit 1; }
docker image inspect "$image" >/dev/null
if docker container inspect "$container" >/dev/null 2>&1; then
  echo "Container $container already exists. Stop the previous mapping session first." >&2;exit 1
fi
# The simulator uses the standard SITL ports; do not run mako-sim concurrently.
if [[ "$(docker inspect -f '{{.State.Running}}' mako-sim 2>/dev/null || true)" == true ]];then
  echo 'Stop your existing mako-sim session first; the SITL ports are shared.' >&2;exit 1
fi
cookie="$(mktemp)"
trap 'rm -f -- "$cookie"' EXIT
chmod 644 "$cookie"
xauth nlist "$DISPLAY" | sed 's/^..../ffff/' | xauth -f "$cookie" nmerge -
[[ -s "$cookie" ]] || { echo 'X11 authentication unavailable.' >&2;exit 1; }
options=(--rm --init --name "$container" --network host --ipc host --gpus all --stop-timeout 40
  -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute -e "DISPLAY=$DISPLAY"
  -e QT_X11_NO_MITSHM=1 -e XAUTHORITY=/tmp/pool.xauth
  -e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-42}" -e RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v "$cookie:/tmp/pool.xauth:ro"
  -v "$package_dir:/mapping_package:ro" -v "$result_dir:/data:rw")
echo "Persistent output folder: $result_dir"
docker run "${options[@]}" "$image" python3 /mapping_package/scripts/container_session.py "$@"
