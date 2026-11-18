#!/usr/bin/env bash
# Start Operation MX from this repository, so every team member runs the same app.
# Build the workspace first: colcon build --symlink-install --base-paths src (repository root).
set -e
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export MAKO_WORKSPACE="${MAKO_WORKSPACE:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
source "${MAKO_ROS_SETUP:-/opt/ros/humble/setup.bash}"
[[ -f "$MAKO_WORKSPACE/install/setup.bash" ]] || { echo "Build first: cd $MAKO_WORKSPACE && colcon build --symlink-install --base-paths src" >&2; exit 1; }
source "$MAKO_WORKSPACE/install/setup.bash"
# Optional extra overlay (no longer required: realjoy_node is built from mako_control).
if [[ -n "${MAKO_SOFTWARE_WORKSPACE:-}" && -f "$MAKO_SOFTWARE_WORKSPACE/install/local_setup.bash" ]]; then
  source "$MAKO_SOFTWARE_WORKSPACE/install/local_setup.bash"
fi
exec python3 "$SCRIPT_DIR/rov_gui_gst.py" "$@"
