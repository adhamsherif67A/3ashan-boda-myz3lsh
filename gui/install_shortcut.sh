#!/usr/bin/env bash
# Add Operation MX (this repository's copy) to the application menu and the desktop.
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
entry="$(sed "s#@REPO@#$repo#g" "$repo/gui/OperationMX.desktop")"
mkdir -p "$HOME/.local/share/applications"
printf '%s\n' "$entry" > "$HOME/.local/share/applications/operation-mx.desktop"
chmod +x "$HOME/.local/share/applications/operation-mx.desktop"
desktop="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [[ -d "$desktop" ]]; then
  printf '%s\n' "$entry" > "$desktop/OperationMX.desktop"
  chmod +x "$desktop/OperationMX.desktop"
  command -v gio >/dev/null && gio set "$desktop/OperationMX.desktop" metadata::trusted true 2>/dev/null || true
fi
echo "Operation MX shortcut installed for $repo"
