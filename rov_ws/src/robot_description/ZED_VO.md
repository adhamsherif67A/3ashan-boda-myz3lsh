# ZED-only RGB-D visual odometry for ArduSub

Build and source the workspace, then restart the simulation with:

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src/robot_description --packages-select robot_description --symlink-install
source install/setup.bash
ros2 launch robot_description gazebo.launch.py odometry_source:=vision
```

The existing MAVROS and ArduSub SITL must be running with their normal FCU URL.
The pipeline uses ZED left RGB, left registered depth and left CameraInfo;
it does not use the bottom camera, IMU fusion, Gazebo odometry as an estimate,
or SLAM loop closure. RGB-D depth supplies metric scale. Gazebo ground truth
remains on /odometry/gz for evaluation only.

RTAB-Map publishes /zed2i/vo/odometry (nav_msgs/Odometry), /zed2i/vo/odom_info,
and the sole odom -> base_link TF. The existing robot TF tree transforms camera
measurements into base_link coordinates, including the backward control-frame
axis. Initial pose (0,0,-1) matches the known spawn pose. map -> odom remains
an identity placeholder; no mapping is started. Vision mode automatically
suppresses Gazebo's odom TF regardless of publish_odom_tf.

The ExternalNav adapter selects only /zed2i/vo/odometry and forwards accepted
messages to /mavros/odometry/out. It validates frame IDs, finite pose/twist,
normalized orientation, timestamps, pose/twist covariance and monotonic stamps.
It never changes frame names or repeats old poses. Tracking failure or missing
updates therefore stop the feed. A backwards simulation clock resets RTAB-Map
to the starting pose and gates forwarding until that reset completes.

MAVROS converts ENU/FLU to MAVLink NED/FRD. The simulation supplies odom_ned;
MAVROS supplies base_link_frd. Do not manually convert the visual pose to NED.
ArduSub helper settings select ExternalNav XY/Z position and velocity, keep
compass yaw, and set VISO_TYPE=3. VISO_POS offsets are zero because the pose
already refers to base_link. EKF origin must be available before non-GPS
navigation works. Confirm FCU connection and EKF health before position control.

Default pilot RGB is 1280x720 at 30 Hz; depth and visual odometry run at 15 Hz.
RGB, depth and CameraInfo use the same native resolution and eye pose.
Approximate synchronization permits at most 25 ms between paired RGB/depth stamps. For computers that
cannot sustain this rate, launch with `camera_width:=640 camera_height:=360`. Frame-to-frame RGB-D odometry uses
SIFT features and optical-flow correspondences to handle the tiled pool scene. Odometry must sustain at least 4 Hz
for ArduPilot ExternalNav. Input settings and reliability are in config/zed_vo.yaml.
The regular pool tile grid can cause ambiguous visual matches; evaluate motion,
tracking loss and pose error using the distinct coral/crab targets as landmarks.
This first stage is visual odometry, not visual-inertial odometry.

## Runtime dependency

The normal dependency is ros-humble-rtabmap-odom. On this workstation a sudo-free
runtime was unpacked in .deps/rtabmap/root. zed_vo.launch.py discovers that local
prefix automatically; MAKO_VO_PREFIX can override the prefix location. These
third-party binaries are excluded from Git. Other workstations should install
the ROS package with apt. ROS interfaces remain standard in either case.

Sources: https://github.com/introlab/rtabmap_ros and
https://github.com/ArduPilot/ardupilot_wiki/blob/master/dev/source/docs/mavlink-nongps-position-estimation.rst

## Verified integration

`python3 src/robot_description/test/check_zed_vo.py` runs an isolated Gazebo/ROS
simulation with the production odometry settings and a mock FCU UDP endpoint.
The real MAVROS process converts and transmits MAVLink ODOMETRY to that endpoint.
Tests cover forward, sideways and vertical thruster motion, pose displacement
against independent Gazebo truth, and Reset recovery. The tested feed sustained
approximately 15 Hz; displacement errors were approximately 0.4–1.2 cm over the
short test motions. This does not measure long-duration drift or validate the
ArduSub EKF/controller on a connected vehicle. MAVROS and SITL must be connected
for EKF fusion; use the configured ExternalNav source and establish EKF origin.
