#!/usr/bin/env bash
set -euo pipefail
image="${MAKO_IMAGE:-marinexperts/mako:latest}"
jobs="${BUILD_JOBS:-2}"
sim_uid="$(id -u)";sim_gid="$(id -g)"
if [[ "$sim_uid" == 0 ]]; then sim_uid=1000;sim_gid=1000;fi
rebuild=false
while (($#)); do
  case "$1" in
    --rebuild) rebuild=true;shift ;;
    --jobs) jobs="${2:?Provide a job count}";shift 2 ;;
    --help) echo 'Usage: docker/build.sh [--rebuild] [--jobs 2]';exit 0 ;;
    *) echo "Unknown option: $1" >&2;exit 2 ;;
  esac
done
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || { echo 'BUILD_JOBS must be a positive integer' >&2;exit 2; }
command -v docker >/dev/null || { echo 'Docker is missing. See README.md, section 4 (Docker setup).' >&2;exit 1; }
docker info >/dev/null || { echo 'Docker daemon is unavailable or your user cannot access it.' >&2;exit 1; }
if ! $rebuild && docker image inspect "$image" >/dev/null 2>&1; then
  image_uid="$(docker image inspect "$image" --format '{{index .Config.Labels "org.marinexperts.user-id"}}')"
  [[ "$image_uid" == "$sim_uid" ]] || { echo "Existing image has a different/old user configuration. Use --rebuild." >&2;exit 1; }
  echo "Image already installed: $image. Use --rebuild after source changes."
  exit 0
fi
root="$(docker info --format '{{.DockerRootDir}}')"
if [[ -d "$root" ]]; then
  free_kb="$(df -Pk "$root" | awk 'END {print $4}')"
  required_kb=$(( ${MAKO_MIN_FREE_GB:-20} * 1024 * 1024 ))
  if ((free_kb < required_kb)); then
    echo 'At least 20 GiB free Docker storage is required for a fresh source build.' >&2
    echo "Docker storage: $root. No images or files have been removed." >&2
    exit 1
  fi
fi
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# Support installations which do not have the optional buildx plugin.
if ! docker buildx version >/dev/null 2>&1; then export DOCKER_BUILDKIT=0;fi
exec docker build --pull --build-arg "SIM_UID=$sim_uid" --build-arg "SIM_GID=$sim_gid" --build-arg "BUILD_JOBS=$jobs" -t "$image" "$repo"
