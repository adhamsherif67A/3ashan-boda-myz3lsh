#!/usr/bin/env bash
set -euo pipefail
# MAVROS needs the EGM96 geoid. Gravity/magnetic datasets are not needed here.
if [[ -f /usr/share/GeographicLib/geoids/egm96-5.pgm || -f /usr/local/share/GeographicLib/geoids/egm96-5.pgm ]]; then
  echo 'GeographicLib egm96-5 already installed'
else
  command -v geographiclib-get-geoids >/dev/null || { echo 'Install geographiclib-tools first' >&2; exit 1; }
  geographiclib-get-geoids egm96-5
  [[ -f /usr/share/GeographicLib/geoids/egm96-5.pgm || -f /usr/local/share/GeographicLib/geoids/egm96-5.pgm ]]
fi
