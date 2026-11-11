# ZED RGB-D and onboard-IMU odometry for ArduSub

The camera estimator uses synchronized ZED RGB, depth, CameraInfo and the ZED's
onboard IMU orientation to assist rotation tracking. RTAB-Map still estimates
translation from the images/depth. This is IMU-assisted RGB-D odometry, not a
validated full inertial-navigation system. Gazebo odometry is used for regression
comparison only and is not fed into the camera estimator.

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/setup.bash
ROS_DOMAIN_ID=42 ros2 launch mako_bringup simulation.launch.py \
  odometry_source:=vision camera_width:=640 camera_height:=360 camera_fps:=30 pilot_fps:=30
```

SITL and MAVROS must also be running (Operation MX starts them). The desktop
SLAM profile selects 640×360 RGB-D at 30 Hz, pilot video at 30 Hz and mapping at
its independent lower rate. A clear pilot image alone is not evidence that
odometry is tracking: those were previously independent 30 Hz and 10 Hz feeds.

## Inputs and calibration

- `/zed2i/rgbd/left/image_rect_color`, `/depth/image_raw`, `/camera_info` use one
  Gazebo RGB-D sensor and exact timestamps (full prefix applies to all three).
- `/zed2i/zed_node/imu/data` is the simulated onboard ZED IMU at 100 Hz, with its
  own `zed2i_camera_center` frame. No ArduSub orientation/position is recycled as
  a camera-estimator input.
- The simulation description owns the IMU and bridges. Its
  `sim_rgbd_camera_info.py` relay converts Gazebo RGB-D texture-center intrinsics
  to integer-index image pixels. Native XYZ measurements showed a 0.5-pixel
  principal-point offset in the installed Harmonic renderer. The relay preserves
  image timestamps and optical frames; `pixel_center_offset:=0.0` can disable it
  in a renderer where calibration already matches. Physical ZED calibration is
  not passed through this simulation-only relay.
- RGB-D near clipping is 0.30 m to exclude the enclosing acrylic dome at all yaw
  headings. The dome's geometry and appearance stay intact.

`config/zed_vo.yaml` uses GFTT/ORB features, optical flow, metric 3D registration
and IMU motion hints. `wait_imu_to_init` requires the onboard stream before
tracking starts. On a real camera, provide the matching ZED IMU topic and TF;
these changes have been tested in simulation, not on the real ROV.

## Odometry and TF ownership

RTAB-Map publishes raw `/zed2i/vo/odometry`. `mako_control` validates covariance,
finite values, timestamps, frame IDs and motion continuity, then publishes
`/mavros/odometry/out` and the sole `odom -> base_link` transform. Rejected poses
are not re-stamped, forwarded or replaced with ground truth. Tracking loss pauses
map and robot-pose updates; Operation MX reports that state separately from video.

The initial pose `(0, 0, -1)` matches the simulation spawn. Without mapping, the
simulation publishes a static `map -> odom`; with SLAM, robot_mapping owns that
transform. No competing odometry or map TF publisher is started.

MAVROS handles ENU/FLU to NED/FRD conversion. The relay supplies `odom_ned`, while
MAVROS supplies the body FRD companion. Pose already refers to base_link, so
ArduSub VISO position offsets remain zero. Do not load simulation parameters on
the real vehicle. The experimental camera estimator does not replace FCU arming,
mode checks, EKF origin or appropriate real-water validation.

## Mapping and saved runs

Enable **SLAM mapping** in Operation MX, or add `slam:=true` to the launch above.
`mako_vision/slam.launch.py` delegates to the team's `robot_mapping` package.
Each app session saves a separate rtabmap.db; existing databases are preserved.
The RViz button selects its occupancy-grid view, with an optional 3D cloud.

## Runtime

Install ROS Humble RTAB-Map packages normally, or use the bundled runtime under
`.deps/rtabmap/root`. The shared runtime resolver covers both vision and mapping
launches; `MAKO_VO_PREFIX` selects another bundled prefix. The control relay also
requires `rtabmap_msgs` for the reset service. Rebuild and restart the app after
source changes; already-running nodes keep their old parameters and model.

## Regression checks

The physical regression uses a separate ROS/Gazebo domain and a mock FCU. It
checks actual thruster motion, accepted odometry versus independent Gazebo truth,
TF continuity and reset recovery. Run the extended deep-yaw + SLAM check with:

```bash
VO_TEST_WIDTH=640 VO_TEST_HEIGHT=360 VO_TEST_FPS=30 PILOT_TEST_FPS=30 \
VO_TEST_DEEP_YAW=1 VO_TEST_YAW_SECONDS=15 VO_TEST_SLAM=1 \
python3 src/mako_vision/test/check_zed_vo.py
```

Unlike a short yaw check, it requires enough accepted poses throughout rotation
and a fresh final TF, plus a live SLAM grid. Native pilot feeds remain 30 Hz.
The 15-second thruster-driven run reached about 1.46 rad/s at 2.1 m depth;
maximum accepted position error was about 0.11 m with the SLAM grid active. These are
short simulation results, not a guarantee of long-duration drift or real-water
performance. Distinct landmarks remain preferable to identical pool tiles.
