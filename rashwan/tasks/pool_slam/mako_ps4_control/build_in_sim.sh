#!/usr/bin/env bash
set -eo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
container="${MAKO_CONTAINER_NAME:-mako-sim}"
[[ "$(docker inspect -f '{{.State.Running}}' "$container")" == true ]] || {
  echo 'Start the pool simulation first: ./docker/run.sh --world pool.world' >&2; exit 1;
}
docker exec "$container" mkdir -p /tmp/mako_ps4_ws/src/mako_ps4_control
# Copy source only, never launcher logs or the bundled QGroundControl AppImage.
for item in CMakeLists.txt package.xml include src test; do
  docker cp "$package_dir/$item" "$container:/tmp/mako_ps4_ws/src/mako_ps4_control/"
done
docker exec "$container" /bin/bash /entrypoint.sh bash -c '
  set -e
  cd /tmp/mako_ps4_ws
  colcon build --packages-select mako_ps4_control --executor sequential \
    --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
  colcon test --packages-select mako_ps4_control --event-handlers console_direct+
  colcon test-result --verbose
'
echo 'Built controller inside the active simulation. The image has not been rebuilt.'
