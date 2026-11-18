#!/usr/bin/env bash
set -euo pipefail
missing=()
for package in "$@"; do
  if [[ "$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)" == "install ok installed" ]]; then
    echo "Already installed: $package"
  else
    missing+=("$package")
  fi
done
if ((${#missing[@]})); then
  apt-get update
  apt-get install --no-install-recommends -y "${missing[@]}"
fi
