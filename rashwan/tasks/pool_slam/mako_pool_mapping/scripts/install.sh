#!/usr/bin/env bash
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
docker build -t marinexperts/mako-pool-mapping:boda -f "$package_dir/Dockerfile" "$package_dir"
