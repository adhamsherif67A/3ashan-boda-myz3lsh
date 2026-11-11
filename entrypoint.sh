#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source "${MAKO_WORKSPACE:-/opt/mako_ws}/install/setup.bash"
case "${1:-simulation}" in
  simulation) if (($#)); then shift; fi; exec python3 "${MAKO_WORKSPACE:-/opt/mako_ws}/docker/simulation.py" "$@" ;;
  gui) shift; exec python3 "${MAKO_WORKSPACE:-/opt/mako_ws}/gui/rov_gui_gst.py" "$@" ;;
  doctor) shift; exec python3 "${MAKO_WORKSPACE:-/opt/mako_ws}/docker/doctor.py" "$@" ;;
  shell) shift; exec bash "$@" ;;
  *) exec "$@" ;;
esac
