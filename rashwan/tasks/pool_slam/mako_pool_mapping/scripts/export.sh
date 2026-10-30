#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 ]] || { echo 'Usage: bash export.sh /absolute/path/to/result-folder';exit 1; }
folder="$(cd "$1" && pwd)"
[[ -s "$folder/pool.db" ]] || { echo 'pool.db is missing';exit 1; }
docker run --rm -v "$folder:/data:rw" marinexperts/mako-pool-mapping:boda \
  rtabmap-export --cloud --poses --opt 2 --max_range 14 --voxel .05 \
  --output pool_optimized --output_dir /data /data/pool.db
