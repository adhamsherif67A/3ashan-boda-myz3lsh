# Whole-pool SLAM regression and survey — 2026-10-30

The autonomous survey completed all 54 waypoints, including full 360° scans at
the center and four offset positions, then returned to the center for loop closure.
The database and exported cloud are actual RTAB-Map outputs from this run.

## Verified results

- Pool floor: **100%** observed 25 cm cells (2688/2688).
- East inner wet wall: **100%** (576/576).
- North and south inner wet walls: **100%** each (672/672 each).
- Scope: 14×12 m floor, three walls from z=-3 to z=0. The original world has an
  open west side. A cell needs a real exported point within 25 cm of its plane;
  this is coverage at that resolution, not a claim that every 5 cm voxel is filled.
- **0 lost tracking frames** in the final logged health snapshot (5880 frames).
- **26 active, independently checked global loop constraints**; a further inactive
  retained/rehearsal link is reported separately in `validation.json`.
- All checked loop transforms agree with the independent simulator reference:
  worst translation error **1.61 cm**, worst rotation error **0.70°**.
- Median loop-constraint translation residual: **16.83 cm → 0.56 cm**.
- Position RMSE with the first pose pinned: **28.33 cm → 6.31 cm**.
- Standard rigid SE(3)-aligned ATE, without scale: **8.38 cm → 3.01 cm**.
- SQLite integrity: OK. 832 database nodes; 289,236 exported colored points.
- Full real-time RViz recording: 546 seconds. `loop_closure_excerpt.mp4` is the
  continuous, real-time 491–536 second excerpt (45 seconds), showing the final
  revisits and closure counter. No trajectory, loop count or drift was fabricated.

`coverage.png` shows the measured cells. `preview.png` is a frame from the recording.
Raw and optimized poses, RGB-D keyframes, event logs, reference trajectory,
launch snapshots and detailed validation are retained next to this report.

## Diagnosis and repair

The old run stopped around a 25–30° yaw: pilot RGB was valid while the entire
raw depth frame and raw point cloud returned negative infinity. The translucent
camera dome was being rendered as a near obstacle by the RGB-D sensor. The
independent package removes **only the dome visual mesh in the temporary generated
world**. Collisions, inertias, sensor poses, TF and the source robot_description
package are preserved.

A separate regression exposed tile-correspondence drift during rotation. The
final odometry uses F2M, optical-flow correspondences and 3D–3D RANSAC (3 cm
inlier distance), with SIFT contrast 0.01, max 2000 features and a 10,000-point
local map. RGB, depth and CameraInfo now come from the same RGB-D sensor and
are synchronized exactly. IMU initialization is enabled. The existing pilot
camera and manual-control topics remain available.

Gazebo ground-truth odometry is used only by the simulation route controller
and independent evaluation logger. RTAB-Map receives RGB-D and IMU sensor data;
it receives no Gazebo or MAVROS position input. The map is not filled with known
world geometry. The original world and robot source files were not edited.

## Reproduce

See [the submission README](../README.md) for portable commands, the pinned
simulator dependency, image installation, autonomous coverage scan, and combined
Gazebo/RViz/QGroundControl/PS4 launch. Exact configuration snapshots and measured
validation are included alongside this report.
