#!/usr/bin/env bash
set -e
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$package_dir/launch_all.py" "$@"
