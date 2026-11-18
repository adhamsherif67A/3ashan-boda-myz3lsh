# ZED 2i simulation

The previous zed_link, zed_joint, single sensor, and zed_link.STL have been replaced by the Stereolabs ZED 2i mesh and camera frame tree. The camera mounts to rov_base_link at x=0.186469391519 m, y=-0.000223754166 m, z=-0.0150005512922 m with zero rotation. This places zed2i_camera_center 36.384607519 mm ahead of the acrylic sphere center, on the same centerline. The camera model adds 15 mm in Z between the mount and center; the mount position accounts for this. The fixed base_link -> rov_base_link joint rotates 180 degrees about Z. Official eye offsets are x=-5 mm and y=+/-60 mm relative to the camera center. Optical frames use X right, Y down, Z forward.

Two dedicated RGB cameras provide pilot images and CameraInfo at `pilot_fps`. Two RGB-D sensors provide color, registered depth in meters, and point clouds at `camera_fps`, with 110 degree horizontal field of view and 0.2–15 m clipping. These are ideal simulated cameras, not calibrated real-camera measurements or ZED SDK stereo depth. Field of view and clipping can be edited in urdf/zed2i_sim.urdf.xacro.

Build and launch from the workspace:

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src/robot_description --packages-select robot_description --symlink-install
source install/setup.bash
ros2 launch mako_bringup simulation.launch.py
```

The explicit base path avoids the duplicate robot_description package in legacy/.

Topics under /zed2i/zed_node/:

- left/image_rect_color and right/image_rect_color, plus left/right camera info,
  are the dedicated pilot RGB streams
- left/depth/image_raw and right/depth/image_raw (additional per-eye depth)
- in vision mode, synchronized RGB-D inputs are also published on
  `/zed2i/rgbd/left/image_rect_color`, `/zed2i/rgbd/left/depth/image_raw`, and
  `/zed2i/rgbd/left/camera_info`; visual odometry and SLAM use this triplet
- left/camera_info and right/camera_info
- left/depth/image_raw and right/depth/image_raw (additional simulated per-eye depth)
- left/points and right/points
- rgb/image_rect_color and rgb/camera_info (left-eye aliases)
- depth/depth_registered and depth/camera_info (left-eye aliases)
- point_cloud/cloud_registered (left-eye alias)

Frames are zed2i_camera_link, zed2i_camera_center, zed2i_left_camera_frame, zed2i_right_camera_frame and their _optical children. Robot state publisher owns all camera transforms. Images and CameraInfo publish optical frame IDs; Public point clouds publish camera-body frame IDs because their coordinates are X-forward. The main simulation bridge publishes /clock for use_sim_time.

Use fixed frame odom in RViz and add the registered point-cloud topic. Do not launch the hardware ZED wrapper concurrently with these topics and transforms. No ZED SDK dependency is required. This implements camera streams and frame conventions, not wrapper tracking, mapping, services or hardware IMU outputs.

Upstream model provenance and license: meshes/ZED_SOURCE.md and meshes/ZED_LICENSE.

Pilot, chase, bottom, and point-cloud bridges use on-demand forwarding (`lazy: true`). The synchronized left RGB-D triplet uses a dedicated bridge in vision mode so Gazebo supplies matching image, depth, and CameraInfo stamps to visual odometry and SLAM. Subscribe in RViz or with `ros2 topic echo/hz` to inspect streams.

## ROV depth topic

The simulation also publishes the vehicle's ground-truth depth on `/rov/depth`
as `std_msgs/msg/Float32`, in meters, positive downward from the world water
surface at `z = 0`. Above-surface values are clamped to zero. This is separate
from the ZED depth images and point clouds; those camera topics and the SLAM
inputs are unchanged. Check the stream with `ros2 topic echo /rov/depth`.

## Fly transect autonomy

In the Operation MX app, start the Team Pool simulation, connect and manually
arm the ROV, then press **Start transect**. The controller approaches the
known start side, waits until both saturated blue rails are detected without a
red rail intruding between them. Low-saturation cyan/grey pool tiles are
rejected, and detection is temporally filtered so a missed camera frame does
not reset the mission,
then commands forward motion through MAVROS while following the fixed
centerline between the two blue rails. Crossing is anchored to the prop's
known world corridor (`x=1.0` to `x=4.0`, `y=-3.5`) so it cannot drift onto
the pool tiles. it commands a sustained 0.60 m/s local-X velocity through
`/mavros/setpoint_velocity/cmd_vel`, with 0.75 m progress markers for
diagnostics. This avoids relying on the ineffective moving
`PoseStamped` target path in the ArduSub simulation. A motion watchdog faults
and holds if it produces less than 0.10 m of measured forward progress for
2.5 s.
The red rails are not steering targets after crossing starts. If the blue pair
is lost, forward thrust is stopped immediately; after a 1.0 s camera-loss
hold, it stops at the current position and holds. **Cancel** returns to
ALT_HOLD; the mission never arms the vehicle. It is available only in
`pool.world`.

The default is 1280x720 pilot RGB at 30 Hz, with depth and bottom RGB at 15 Hz. Resolution and frame rate are launch arguments:

```bash
ros2 launch mako_bringup simulation.launch.py camera_width:=1280 camera_height:=720 pilot_fps:=30 camera_fps:=15
```

For faster simulation, use a performance profile. The profiles change camera
rendering and transport workload without changing the transect controller:

```bash
ros2 launch mako_bringup simulation.launch.py performance_profile:=maximum_fps
```

Available profiles:

- `maximum_fps`: 640x360, RGB-D/bottom 10 Hz, pilot RGB 15 Hz
- `balanced`: 960x540, RGB-D/bottom 12 Hz, pilot RGB 20 Hz
- `vision_quality`: 1280x720, RGB-D/bottom 15 Hz, pilot RGB 24 Hz
- `full_sensors`: 1280x720, RGB-D/bottom 15 Hz, pilot RGB 30 Hz

Individual `camera_width`, `camera_height`, `camera_fps`, and `pilot_fps`
arguments override their profile values. SLAM runs use a dedicated 960x540,
15 Hz RGB-D profile with a 20 Hz pilot stream. Visual odometry uses more
features, a higher inlier threshold, tighter RGB-D synchronization, and an
8 m useful depth range so far-wall depth noise does not dominate the map.
Operation MX reports tracking quality, feature count, inliers, loop closures,
and RGB-D rate.
After three consecutive correspondence failures, visual odometry resets its
short-term reference automatically. This lets tracking recover from a
temporary low-texture or synchronization outage instead of leaving RTAB-Map
permanently without odometry or allowing a failed motion guess to grow
without bound.

`pilot_fps:=60` requests 60 Hz RGB while leaving depth at 15 Hz. It is an optional setting, not a guaranteed workstation rate. Keeping `camera_fps:=15` avoids doubling the expensive depth/cloud generation. Subscribe only to the eye topics you use; RGB aliases add another transported image stream.

Point-cloud alignment: Gazebo RGB-D cloud coordinates are X forward, Y left, Z up. Their headers use zed2i_left_camera_frame / zed2i_right_camera_frame. Image, depth-image and CameraInfo headers remain in the corresponding _optical frames. RViz applies the appropriate TF for each; do not relabel clouds as optical without rotating XYZ.

The cloud_frame_relay node corrects the Gazebo cloud header after transport, because this Harmonic sensor version uses optical_frame_id for the cloud without rotating XYZ. Raw clouds are internal /zed2i/sim_ros/{left,right}/points_raw; public clouds keep their existing topic names and use the camera body frame. The relay only subscribes while public cloud consumers are present. XYZ, RGB, point layout and capture timestamps remain unchanged.

## Bottom RGB camera

A compact RGB camera is mounted 50 mm below `zed2i_camera_center`, inside the
acrylic dome. `bottom_camera_link` has X downward; its lens is 14 mm in front
of the housing. `bottom_camera_optical_frame` uses optical Z downward and is
connected to the existing TF tree. RGB output uses that optical frame ID.

ROS topics: `/bottom_camera/image_raw` (`sensor_msgs/Image`) and
`/bottom_camera/camera_info` (`sensor_msgs/CameraInfo`). Gazebo topics are
`/bottom_camera/sim/image` and `/bottom_camera/sim/camera_info`. Both ROS
bridges are lazy with bounded queues. The camera shares camera_width,
camera_height and camera_fps launch settings (default 1280×720 at 15 Hz),
with 90° horizontal FOV and 0.1–15 m clipping. The near clip excludes the
nearby enclosing dome from the image.

The 50 g camera mass is allocated from the modeled body payload budget.
Body ballast is rebalanced to retain the existing complete-model COM and
neutral freshwater displacement. The camera has a visible housing and lens;
its collision is covered by the existing body/dome enclosure.

## GPU and pilot-view continuity

`render_gpu:=auto` selects NVIDIA PRIME offload when a working NVIDIA GPU is detected;
`render_gpu:=default` keeps the system renderer. `render_gpu:=nvidia` requires a working
NVIDIA driver. Ogre2 already renders cameras on the selected GPU. This does not move
RTAB-Map SIFT/optical-flow computation or ROS serialization onto CUDA.

The dedicated RGB sensors avoid black geometry observed in this workstation's
RGB-D color output with NVIDIA rendering. RGB and depth share eye pose, resolution,
FOV and clipping. Visual odometry pairs the 30 Hz RGB with 15 Hz depth using
approximate synchronization limited to 25 ms. Public image and depth topic names
are preserved; their rates differ.

For piloting, use the TF-independent Image displays:

```bash
ros2 launch robot_description view_tf.launch.py view:=pilot_views.rviz
```

A Camera display projects using the fixed-frame TF and can disappear when visual
odometry loses tracking. The Image displays keep rendering arriving frames, using
Best Effort, Keep Last, depth 1. They do not change the vehicle's TF or estimator.

Validation on this workstation (RTX 4050): simultaneous 720p eye feeds delivered
about 29 Hz at the requested 30 Hz. A 3-second yaw maneuver reached approximately
84 degrees/second; both eyes delivered nonblank images, with a worst observed
inter-frame gap of 66 ms. Camera bridge plus its ROS launcher peaked at ~98 MiB
RSS during the isolated test, with both pilot eyes and left depth/VO active.
This is bridge memory, not total Gazebo/GUI memory, and excludes subscribed clouds.
Surge, sway, heave, MAVLink output and simulation-reset recovery also passed.
The 60 Hz option has not been performance-validated.

NVIDIA environment settings follow the official PRIME offload documentation:
https://download.nvidia.com/XFree86/Linux-x86_64/570.181/README/primerenderoffload.html

## Rear-following virtual RGB camera

`/third_person_camera/image_raw` and `/third_person_camera/camera_info` expose a
720p RGB chase view at `pilot_fps` (default 30 Hz). The massless camera frame is
1.45 m behind and 0.62 m above `rov_base_link`, pitching down by 0.36 rad. It follows
the vehicle's translation and rotation without changing inertia or collisions.
`headless:=true` starts only the Gazebo server, with EGL-rendered camera feeds.
MarineXperts Mako Pilot integrates this view with the ZED left eye and bottom inset.
Application setup and session ownership: ../../../gui/README.md in the workspace.
# Vehicle depth topic

The simulation publishes the ROV's ground-truth depth on `/rov/depth` as
`std_msgs/msg/Float32`, in meters, positive downward from the water surface
(world `z = 0`). Values above the surface are clamped to zero. This vehicle
depth estimate is separate from the ZED per-pixel depth images and point cloud;
the camera topics and RTAB-Map inputs are unchanged.

RGB-D camera near clipping is 0.30 m so the enclosing acrylic dome is excluded
at every heading. The pilot RGB camera keeps its separate clip configuration.
At 0.20 m the Ogre2 RGB-D image can become blank with all-NaN depth during yaw,
which stops validated odometry and freezes the RViz robot. The shell geometry
and opacity are unchanged. Check the regression with:

```bash
python3 src/robot_description/test/check_rgbd_headings.py
```
