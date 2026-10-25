#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MAKO_WORKSPACE="${MAKO_WORKSPACE:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
MAKO_SOFTWARE_WORKSPACE="${MAKO_SOFTWARE_WORKSPACE:-$HOME/MarineXperts-Boda/Software2026}"
source /opt/ros/humble/setup.bash
source "$MAKO_WORKSPACE/install/setup.bash"
source "$MAKO_SOFTWARE_WORKSPACE/install/local_setup.bash"
export MAKO_WORKSPACE MAKO_SOFTWARE_WORKSPACE
exec python3 "$MAKO_SOFTWARE_WORKSPACE/src/real_joy/src/rov_gui_gst.py" "$@"
