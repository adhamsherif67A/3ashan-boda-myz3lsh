# Mako pool RGB-D mapping (ROS 2 Humble)

This is an independent `ament_python` package. Nothing is added to or modified
in `robot_description`. The existing Mako image and simulator are reused, and a
separate image installs RTAB-Map SLAM, synchronization, map export, and recording
dependencies. The build does not rebuild ArduPilot or Gazebo from source.

## Install and start

For the integrated original desktop workflow (Gazebo, robot RViz, mapping RViz,
QGroundControl and the PS4 C++ controller), run the sibling launcher instead:

```bash
bash ../mako_ps4_control/launch_all.sh --qgc-software
# Add --record-mapping to record the mapping RViz window.
```

That mode uses manual PS4 control and automatically saves/exports maps on shutdown.
Its outputs are in the PS4 package's `runs/<timestamp>/mapping/` directory. The
standalone commands below remain available for the autonomous demonstration.

Prerequisites: working `marinexperts/mako:boda` image, NVIDIA driver and Container
Toolkit, Docker permissions, Ubuntu X11/XWayland, `xauth`, and free disk space for
maps/video. Stop the original `mako-sim` session first: both simulations use the
same SITL ports. Do not run another joystick/manual-control publisher during the
autonomous demo.

From this package directory on the Ubuntu host:

```bash
bash scripts/install.sh
bash scripts/run.sh
```

The install step has already been completed on this machine. `run.sh` starts
NVIDIA Gazebo, builds only this independent package, and opens its mapping RViz.
Visual odometry starts after a 15-second simulator settling period, rather than
anchoring its first frame while the vehicle and IMU are still initializing.
The active container is named `mako-pool-sim`. The database is incrementally
recorded, then flushed and exported when you press Ctrl+C. Results are on the
host in the sibling `pool_mapping_results/<timestamp>/` directory and survive
container removal. `POOL_OUTPUT_DIR=/absolute/path` selects another output folder.
Use a fresh output folder for a fresh map; an existing `pool.db` is deliberately
not deleted or overwritten by a delete-on-start option.

## Autonomous simulator demo and video

```bash
bash scripts/run.sh --demo --record --size 1.5 --laps 2
```

This is simulation-only. It waits for live visual odometry and MAVROS, selects
MANUAL, waits for successful normal arming (no force-arm or bypass of prearm
checks), uses manual-control directions previously measured on this Mako model,
then follows a short closed rectangle twice with ground-truth position feedback.
The ROS driver also supports `--calibrate` for changed vehicle models; calibration
is omitted from the normal recorded route to preserve a clean initial SLAM anchor.
It maintains a pool safety envelope, detects divergence and disarms at the end.
Calibration, reached waypoints, errors, and safety stops are logged. Speed depends
on simulator dynamics and its real-time factor. Larger rectangles can be requested
with `--size 3` after the initial run. Manual driving is also possible using your
existing PS4 node, with `MAKO_CONTAINER_NAME=mako-pool-sim` for its build/run scripts.
Do not start that node while `--demo` is driving.

Ground truth is **only** used by the autonomous driving controller and the
independent evaluation logger. The RTAB-Map SLAM and visual-odometry nodes receive
no `/odometry/gz` or MAVROS pose input. They estimate their own
6-DoF RGB-D odometry. No artificial odometry drift, forced loop links, teleports,
database edits or fabricated closure events are used.

The recorder captures only the RViz window identified by `pool_mapping.rviz`,
not the entire desktop. Keep that window open at a fixed size while recording.
The session ends after the route, saves/exports the map, and validates artifacts.
If a closure is not detected, `validation.json` says so: a completed route alone
is not proof of successful loop closure.

## ROS launch without the session wrapper

Inside a running mapping container (or any workspace with this package built):

```bash
source /opt/ros/humble/setup.bash
source /tmp/pool_mapping_ws/install/setup.bash
ros2 launch mako_pool_mapping pool_mapping.launch.py output_dir:=/data rviz:=true
```

The simulator and camera topics must already be running. Export the same `GZ_PARTITION` as Gazebo: the mapping launch bridges the RGB-D sensor color and CameraInfo itself. Do not launch a second
SLAM instance into the same namespace/database. `rviz:=false` disables RViz.
`use_sim_time` is enabled throughout; use the same domain and middleware as the
simulation (domain 42 / Fast DDS by default).

## Data flow and frame ownership

```text
Gazebo RGB-D sensor: RGB + aligned metric depth + RGB CameraInfo (identical stamps)
  -> /pool_mapping/rgbd_sync
  -> /pool_mapping/rgbd_image
     -> /pool_mapping/visual_odometry -> /pool_mapping/odom
     -> /pool_mapping/rtabmap (RGB-D + visual odometry)
        -> optimized cloud/mapGraph/info and pool.db
        -> loop_evidence -> RViz markers + JSON evidence
```

Inputs:

| Topic | Purpose |
|---|---|
| `/pool_mapping/camera/rgb` | RGB from the same RGB-D sensor, 1280x720/15 Hz |
| `/zed2i/zed_node/left/depth/image_raw` | Registered simulated depth, meters, 15 Hz |
| `/pool_mapping/camera/info` | Same RGB-D sensor pinhole intrinsics |
| `/tf`, `/tf_static` | Existing base_link-to-camera extrinsics only |

SLAM uses `pool_map` and visual odometry uses `pool_odom`. Visual odometry does
**not** publish TF, so it cannot replace the simulator's `odom -> base_link`.
RTAB-Map publishes `pool_map -> pool_odom`. Its `odom_frame_id` is empty so the
odometry message is used, and `odom_sensor_sync=false` prevents a second request
for an unavailable `pool_odom -> base_link` TF. Existing simulator `map -> odom`
and flight-control odometry remain untouched. The independent mapping RViz uses
`pool_map` and displays the already transformed cloud and markers; it does not
add a second RobotModel using the unrelated simulator world frame.

## Main configuration

The complete configuration is in `launch/pool_mapping.launch.py`.

| Setting | Value/reason |
|---|---|
| RGB-D sync | Exact RGB-D synchronization, reliable QoS, bounded queues |
| Visual odometry | F2M (`Odom/Strategy=0`), SIFT contrast 0.01 / max 2000 features, optical-flow correspondences, 3D–3D RANSAC (3 cm inlier distance); IMU initialization, reset after 15 failed frames |
| Loop geometry verification | At least 100 inliers, distribution >=0.01; graph error ratio <=1.0 |
| Odometry image decimation | 2, to reduce processing cost |
| SLAM rate | 2 Hz |
| New-node motion threshold | 0.15 m or 0.15 rad |
| Short-term memory | 10 nodes; recent frames are not counted as global revisits |
| Appearance loop threshold | 0.11; geometric verification remains enabled |
| Spatial proximity closures | Disabled to isolate appearance-based global loop detection |
| Optimization anchor | First graph node (`RGBD/OptimizeFromGraphEnd=false`) |
| Map | 3D RGB-D grid, 5 cm voxels, 14 m maximum range |

Pool tiles are repetitive. Move slowly, preserve overlapping views, include
distinctive pool markings, and revisit the initial area with a similar view.
Do not lower geometric verification thresholds merely to force an accepted loop.

## RViz and evidence

RViz displays the optimized colored 3D cloud, RGB feed, optimized trajectory
(green), raw visual-odometry trajectory in the initial mapping coordinate system
(red), global loop links (yellow), and a text counter for real loop detections.
Raw odometry is never moved with the changing map correction, so divergence from
the optimized graph remains visible. The display labels the map/odom correction;
that value is not itself an absolute ground-truth accuracy measurement.

`loop_evidence` only increments its global-loop counter for positive
`rtabmap_msgs/Info.loop_closure_id`. Proximity events are not silently substituted.
`loop_events.jsonl` contains actual IDs/timestamps/statistics and graph corrections.
`summary.json` contains the live counts. Offline `validation.json` independently
checks the SQLite database, `Link.type=1` edges, exported points, video duration,
and the loop-edge translation/rotation residual before and after optimization.
An evaluation-only Gazebo trajectory independently checks loop transformations
(<0.3 m and <8 degrees) and measures raw versus optimized position RMSE using
both first-pose alignment and standard rigid SE(3)-aligned ATE. Neither permits
scale adjustment. This reference is not supplied to the SLAM nodes.
A strict success flag requires an actual global loop, a measured reduction
in at least one >1 cm raw loop-constraint error, all checked loop transforms
within those reference bounds, and lower optimized SE(3)-aligned ATE below 0.5 m. Retained
inactive/rehearsal links whose nodes are absent from the active optimized graph
are counted separately, not presented as independently validated global revisits.
Successful discovery of a place
and successful correction are reported separately.

## Saved outputs

| File | Contents |
|---|---|
| `pool.db` | RTAB-Map database, RGB-D keyframes, graph and optimized poses |
| `pool_optimized_cloud.ply` | Colored, optimized 3D point cloud at 5 cm resolution |
| `pool_optimized_poses.txt` | Optimized trajectory, timestamp + pose + node ID |
| `pool_raw_poses.txt` | Unoptimized visual-odometry trajectory for comparison |
| `loop_closure_demo.mp4` | Real RViz recording when `--record` is enabled |
| `loop_events.jsonl`, `summary.json`, `validation.json` | Measured evidence |
| `drive.jsonl`, `*.log`, `ros/` | Reproduction and troubleshooting logs |
| `evaluation_ground_truth.txt` | Evaluation-only timestamped simulator poses |

The exported cloud includes observed surfaces. It is not a guarantee that every
part of the pool has been seen; use longer coverage routes for a complete survey.
The mapping origin is the first successful visual-odometry pose, not a surveyed
global reference or the simulator's world origin.

To re-export a saved database after the simulator closes:

```bash
bash scripts/export.sh /absolute/path/to/result-folder
```

## Troubleshooting

- Empty map: check RGB/depth topics and matching CameraInfo, then mapping.log for sync warnings.
- No loops: complete a genuine revisit after more than 10 keyframes; inspect view overlap and feature inliers.
- Failed odometry: slow down; do not feed ground truth into SLAM to hide the problem.
- GUIDED mode is not required: the demo uses MANUAL feedback control, as in the validated PS4 setup.
- Driver prearm rejection: it retries normal arming for 60 seconds while SITL initializes; inspect FCU messages if it still fails.
- Container conflict: stop the old simulation; the package never deletes someone else's container automatically.
- Low frame rate: check NVIDIA renderer, avoid extra video subscribers, and retain default image decimation.

## Sources and verification

- RTAB-Map ROS 2: https://github.com/introlab/rtabmap_ros/tree/ros2
- Upstream launch: https://github.com/introlab/rtabmap_ros/blob/ros2/rtabmap_launch/launch/rtabmap.launch.py
- Message definitions: https://github.com/introlab/rtabmap_ros/tree/ros2/rtabmap_msgs/msg
- Exporter: `rtabmap-export --help` in the installed image (options were verified locally).
- Exact installed package versions are listed in `installed_versions.txt`.

Core metric tests can be run on a Python installation with NumPy:

```bash
python3 -m unittest discover -s test -v
```

## Depth dropout repair and whole-pool survey

The original sensor can return an entire `-inf` depth frame when yawing past
roughly 25–30 degrees. In the regression test the pilot RGB remained valid,
while both the raw Gazebo depth image and point cloud failed. The translucent
protective camera dome was rendered as a near obstacle by the RGB-D sensor.
`mapping_sim.launch.py` reuses the original simulator launch and removes only
that dome's **visual mesh from the generated temporary world**. It retains all
collisions, inertias, sensor poses, optical frames, lighting and pool geometry.
The original repository and installed `robot_description` files are unchanged. The color input comes from the same RGB-D sensor instead of pairing depth with the separate pilot camera; synchronization is exact. Pilot-camera topics and the PS4 view are unchanged.
The mapping session uses this overlay automatically, including the combined
Gazebo/RViz/QGroundControl/PS4 launcher. Restart the session to apply it.

```bash
# Simulator-only regression: rotate 360 degrees, return to original view.
bash scripts/run.sh --demo --record --route yaw --laps 1
# Survey the central view and four offset views, then revisit the start.
bash scripts/run.sh --demo --record --route coverage --laps 1
```

The driver stops motion immediately on visual tracking loss and aborts/disarms
if recovery takes more than 15 seconds. `tracking_health.json` reports actual
lost frames, recoveries and longest loss. `coverage.json` measures occupied
25 cm cells on the actual exported cloud near the 14×12 m floor and the three
wet inner walls. This world has an open west side, not a fourth wall. Each
surface must reach 95% to pass the coverage target; missing cells are not
interpolated or filled from known world geometry. Ground truth aligns the first
map pose solely for this offline evaluation. Coverage and map accuracy must
both be checked; a dense but distorted cloud is not a successful pool map.

The image dependencies are already installed on this machine. Launcher/config
updates are mounted from this package and rebuilt automatically at session start;
rebuilding the original simulator image is unnecessary.
