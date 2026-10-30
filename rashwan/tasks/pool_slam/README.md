# Pool SLAM with RTAB-Map — Rashwan

Independent ROS 2 Humble RGB-D mapping and PS4 motion packages for the Mako
Gazebo simulation. The packages remain separate from `robot_description`.

## Deliverables

- `results/pool.db`: saved RTAB-Map database (Git LFS).
- `results/pool_optimized_cloud.ply`: exported colored 3D pool map.
- `results/loop_closure_excerpt.mp4`: 45-second real-time loop-closure video.
- `results/REPORT.md`: diagnosis, configuration and measured results.
- `results/validation.json`, `coverage.json`, poses and reference trajectory:
  independent evidence. Ground truth is used for driving/evaluation only.
- `mako_pool_mapping/README.md`: full mapping configuration and frame ownership.
- `mako_ps4_control/`: C++ PS4 motion controller and combined desktop launcher.

Measured survey: 100% of 25 cm surface cells on the 14×12 m floor and three
wet walls, 26 independently verified active global loop constraints, no tracking
loss, and SE(3)-aligned ATE reduced from 8.38 to 3.01 cm. The world is open on its
west side. These are simulation results at the stated measurement resolution.

## Get the saved database

Install Git LFS, then run `git lfs install` and `git lfs pull` from the repository
root after cloning the `rashwan` branch. The database should be about 1.1 GB;
a small text file containing `version https://git-lfs.github.com/spec/v1` is only
a pointer and means the LFS download has not completed.

## Simulator dependency

The simulator belongs to the same repository's `boda` branch. This submission
uses base commit `3fbdaff606bea0baaca4d286994d17e5eb460221`; the personal `rashwan`
branch contains tasks, so do not use its repository root as the simulator source.
Keep a separate, ignored simulator checkout as follows. Run these commands from
`rashwan/tasks/pool_slam` inside your clone:

```bash
TASK_DIR="$PWD"
git clone --branch boda --single-branch   https://github.com/adhamsherif67A/3ashan-boda-myz3lsh.git simulator
git -C "$TASK_DIR/simulator" checkout --detach 3fbdaff606bea0baaca4d286994d17e5eb460221
```

Prerequisites: Ubuntu 22.04 desktop with X11/XWayland, Docker access, NVIDIA
host driver and NVIDIA Container Toolkit configured for Docker, `xauth`, and
sufficient free Docker storage (the base builder checks for at least 20 GiB).
Follow the pinned simulator's `SIMULATION_READY.md` for host setup. A previously
built `marinexperts/mako:boda` image can be reused; source rebuilding is unnecessary
on the original machine.

For a fresh base build:

```bash
cd "$TASK_DIR/simulator"
# The downloaded Gazebo key is binary GPG; use its matching keyring extension.
sed -i 's|/usr/share/keyrings/gazebo.asc|/usr/share/keyrings/gazebo.gpg|g' Dockerfile
./docker/build.sh
docker run --rm marinexperts/mako:boda doctor
cd "$TASK_DIR"
```

Install mapping dependencies into the separate image:

```bash
bash mako_pool_mapping/scripts/install.sh
```

## Reproduce the autonomous survey and recording

From `rashwan/tasks/pool_slam`:

```bash
bash mako_pool_mapping/scripts/run.sh --demo --record --route coverage --laps 1
```

Stop another simulator or manual-control publisher first: SITL ports are shared.
The simulation-only driver selects MANUAL, normally arms, follows the survey,
disarms, and exports the database/cloud at the end. The simulator reference guides
the route and evaluates the result; it is not an input to visual odometry or SLAM.
New results are saved under `pool_mapping_results/<timestamp>/`, separate from
`results/`, which contains the submitted run. `--route yaw --laps 1` runs the
360-degree depth/tracking regression. Omit `--demo` for manual driving.

## Gazebo + RViz + QGroundControl + PS4 + mapping

This mode additionally requires host ROS Humble and `ros-humble-joy`. For example,
after configuring the official ROS Humble Ubuntu apt repository:

```bash
sudo apt install ros-humble-joy
```

QGroundControl is not committed. Download the official v5.0.8 x86_64 AppImage
from https://github.com/mavlink/qgroundcontrol/releases/tag/v5.0.8,
place it under `mako_ps4_control/apps/`, and make it executable. The release URL
and tested SHA256 are in `mako_ps4_control/apps/SOURCE.txt`. Then run from this
submission directory:

```bash
TASK_DIR="$PWD"
chmod +x mako_ps4_control/apps/*.AppImage
bash mako_ps4_control/launch_all.sh --repo "$TASK_DIR/simulator"   --qgc-software --record-mapping
```

`--qgc-software` applies to QGroundControl only; Gazebo uses NVIDIA. PS4 Options
toggles arm/disarm. Left stick controls forward/back and lateral motion; right
stick controls vertical motion and yaw. Start with a neutral controller. Drive
slowly with overlapping views and revisit previously observed areas with similar
view direction. There is no autonomous arming in the combined interactive mode.

Keep mapping RViz open while recording. Press Ctrl+C in the launcher terminal
and wait for export completion before closing it. Each launch creates a new map
under `mako_ps4_control/runs/<timestamp>/mapping/`; the saved submission is retained.

## Configuration and repair

Only the temporary generated world's camera-dome visual is omitted to avoid
all-negative-infinity RGB-D depth frames during yaw. Physics, collisions, sensor
extrinsics and the source robot description are preserved. RGB/depth/info come
from one RGB-D sensor with exact synchronization. Visual odometry uses F2M,
optical-flow correspondences, SIFT contrast 0.01 / 2000 features, 3D–3D RANSAC
with 3 cm inlier distance, a 10,000-point local map, and IMU initialization.
SLAM uses independent `pool_map` and `pool_odom` frames; flight-control odometry
is unchanged. Exact launch snapshots are in `results/configuration*.py`.

Pure metric, route and sensor-overlay regression tests:

```bash
python3 -m unittest discover -s mako_pool_mapping/test -q
python3 -m unittest discover -s mako_ps4_control/test -p test_launcher.py -q
```
