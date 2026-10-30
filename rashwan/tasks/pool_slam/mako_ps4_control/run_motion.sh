#!/usr/bin/env bash
set -eo pipefail
container="${MAKO_CONTAINER_NAME:-mako-sim}"
docker exec "$container" test -f /tmp/mako_ps4_ws/install/setup.bash || {
  echo 'Run build_in_sim.sh first.' >&2; exit 1;
}
options=()
if [[ -t 0 && -t 1 ]]; then options+=(-it);fi
exec docker exec "${options[@]}" "$container" /bin/bash /entrypoint.sh bash -c '
  source /tmp/mako_ps4_ws/install/setup.bash
  set +e
  flock -n -E 75 /tmp/mako_ps4_motion.lock ros2 run mako_ps4_control ps4_motion --ros-args "$@"
  status=$?
  if [[ "$status" == 75 ]]; then
    echo "A motion controller is already running. Stop it before starting another." >&2
  fi
  exit "$status"
' bash "$@"
