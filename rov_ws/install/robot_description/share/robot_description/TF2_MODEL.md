# Mako TF2 model

This step prepares TF2 only. No SLAM or localization algorithm is launched.

## Frames and owners

```text
map                                     ground-truth simulation reference
├── map_ned                             MAVROS ENU/NED convention transform
└── odom                                identity, tf_sim_map_odom
└── base_link                           dynamic, Gazebo OdometryPublisher
    ├── center_body_link                fixed, original CAD frame
    │   ├── t1_link ... t6_link          rotating thruster joints
    │   ├── bar30_link                  fixed pressure-sensor mount
    │   └── camera_dome_link            fixed transparent visual only
    ├── imu_link                        fixed, ArduSub FRD IMU (+X, -Y, -Z)
    └── rov_base_link                   fixed, 180 degree yaw
        ├── imu_ros_link                fixed, ROS-facing IMU
        └── zed2i_camera_link            fixed camera mount
            └── zed2i_camera_center
                ├── zed2i_left_camera_frame
                │   └── zed2i_left_camera_frame_optical
                └── zed2i_right_camera_frame
                    └── zed2i_right_camera_frame_optical
```

`base_link` retains the existing simulation / ArduSub control orientation. The camera-facing bow lies along its negative X axis. Changing this historical frame in isolation would change the SITL IMU and motor conventions. `rov_base_link` supplies the physical bow-facing convention for perception: X forward toward the camera, Y left, Z up. Both frames have the same origin. To express body velocities from one in the other, negate X and Y; Z is unchanged. Do not assume forward in rov_base_link means positive surge in the legacy control interface.

The camera mounting joint is expressed in rov_base_link coordinates and places zed2i_camera_center 36.384607519 mm forward along the acrylic sphere centerline. Optical frames use X right, Y down, Z forward; optical +Z coincides with rov_base_link +X. The upstream camera model uses a 12 cm baseline and a -5 mm eye offset in camera-center X.

Robot state publisher alone owns every fixed body/sensor transform and publishes thruster transforms from `/joint_states`. Gazebo alone owns `odom -> base_link` in the default simulation. Full 3D odometry is explicitly enabled, including depth, roll and pitch. Its TF topic is explicitly `/model/mako/tf`; the ROS bridge forwards it to `/tf`.

In ground-truth simulation, `tf_sim_map_odom` publishes an identity `map -> odom` transform. `publish_map_tf:=false` disables this placeholder when a global localization node takes ownership of that edge. MAVROS owns its `map -> map_ned` ENU/NED convention transform; the simulation does not duplicate it. Without MAVROS, map_ned is not published. Both `map` and `odom` can be used as the RViz fixed frame in the default simulation. No base_footprint is invented for this freely moving underwater vehicle.

The original `imu_sensor` used by ArduSub remains unchanged. A second, co-located Gazebo IMU provides `/imu/data` in `imu_ros_link`, aligned with rov_base_link. This avoids mislabelling FRD vectors as ROS FLU vectors. Its gyro/acceleration noise matches the original simulated IMU; orientation remains a simulated observation, not a calibrated hardware estimate.

## Build, launch and check

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src/robot_description --packages-select robot_description --symlink-install --cmake-args -DBUILD_TESTING=ON
source install/setup.bash
ros2 launch robot_description gazebo.launch.py
```

In a second sourced terminal, inspect the live model without adding any TF publishers:

```bash
ros2 launch robot_description view_tf.launch.py
```

Then check TF:

```bash
ros2 run robot_description check_sim_tf.py --timeout 30 --ros-args -p use_sim_time:=true
ros2 run tf2_ros tf2_echo odom rov_base_link
ros2 run tf2_ros tf2_echo rov_base_link zed2i_left_camera_frame_optical
```

The checker verifies all model frames, conflicting TF parents, camera axes, sensor frame IDs, transforms at actual sensor timestamps and an advancing simulated clock. It requires the default ground-truth TF mode and all simulation sensor bridges. It observes data; it does not command the robot.

`/odometry/gz` still describes `odom -> base_link` and remains available to the existing MAVROS ExternalNav relay. `/clock` is now bridged by the main simulation bridge, so robot timing is independent of the camera bridge. Camera streams retain their ZED-style topic names.

When an estimator is eventually added, start with:

```bash
ros2 launch robot_description gazebo.launch.py publish_odom_tf:=false publish_map_tf:=false
```

The estimator must then publish `odom -> base_link`; the Gazebo odometry message stays available for evaluation. Avoid also publishing `odom -> rov_base_link`, since rov_base_link already has a fixed parent. A node estimating rov_base_link must transform its result back to base_link before broadcasting TF. MAVROS local-position / odometry TF publication must also remain disabled whenever another node owns the same edge. `display.launch.py` now defaults to viewing the running simulation and publishes no transforms or joint states. For a standalone model with Gazebo stopped, explicitly use `display.launch.py standalone:=true`.

If RViz received wall-clock TF from a standalone model publisher alongside simulation-time TF, close that publisher and restart RViz to discard the contaminated TF buffer. The simulation uses `ignore_timestamp=false`; bypassing the gate does not fix competing publishers.

Camera bridges advertise all ZED topics but use `lazy=true` and one-message publisher/subscriber queues. A bridge starts forwarding each stream when a ROS subscriber requests it. This avoids forwarding unused streams. The default 640x360 at 15 Hz also limits bandwidth when streams are actively subscribed. Adjust camera_width, camera_height and camera_fps in gazebo.launch.py when needed.

## Validation

Geometry tests check a single connected tree, bow-facing optical axes, 12 cm left/right ordering, camera placement on the acrylic sphere centerline, distinct IMU conventions and six-axis odometry configuration:

```bash
colcon test --base-paths src/robot_description --packages-select robot_description
colcon test-result --verbose
```

Validation completed: all five geometry tests passed, the generated SDF is valid, and an isolated headless Gazebo/ROS session passed the live checker for body/thruster frames, camera and IMU headers, sensor-time transform lookup and simulated clock. A tilted test model confirmed that odometry preserves z=-1 m and roll=0.15, pitch=0.1, yaw=0.2 rad. Closed-loop ArduSub motion and future estimator performance were not part of this TF validation.

References: [ROS frame ownership (REP 105)](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst) and [Gazebo Harmonic OdometryPublisher parameters](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1OdometryPublisher.html).

Additional camera/TF regression check: all 13 camera mappings ran under sustained subscriptions for 45 seconds at 640x360/15 Hz, with over 600 messages received per stream and monotonic timestamps for every thruster transform. Bridge RSS was sampled at about 65 MB during the run. The former 1280x720/30 Hz stress case consumed multiple gigabytes and triggered the kernel OOM killer on this workstation.

Point-cloud alignment: Gazebo RGB-D cloud coordinates are X forward, Y left, Z up. Their headers use zed2i_left_camera_frame / zed2i_right_camera_frame. Image, depth-image and CameraInfo headers remain in the corresponding _optical frames. RViz applies the appropriate TF for each; do not relabel clouds as optical without rotating XYZ.

The cloud_frame_relay node corrects the Gazebo cloud header after transport, because this Harmonic sensor version uses optical_frame_id for the cloud without rotating XYZ. Raw clouds are internal /zed2i/sim_ros/{left,right}/points_raw; public clouds keep their existing topic names and use the camera body frame. The relay only subscribes while public cloud consumers are present. XYZ, RGB, point layout and capture timestamps remain unchanged.

## Contact frames and neutral buoyancy

The body has two chamfered side-guard collision frames, including lower landing
rails. Their primitive bars follow the CAD perimeter and leave the openings clear.
The rails reach CAD Y=-0.212473 m (approximately base Z=-0.212473 m); the guards
reach CAD X=-0.22003 / +0.21997 m. These surfaces make first contact with the
floor and side walls.

Total modeled mass, including ZED2i, IMU and six thrusters, is 20.7642249711 kg.
The combined primitive collision volume is 0.0208058366444 m³, displacing exactly
that mass at freshwater density 998 kg/m³. The central sealed-body collision box
is trimmed to account for the side-frame volume. Combined horizontal center of
buoyancy aligns with total center of mass; buoyancy remains 54 mm above
COM for passive roll/pitch stability. Recalculate displacement and balance if
payload masses or collision dimensions change; the mass/volume regression test
checks the neutral-buoyancy contract. Wave currents still produce gentle motion.

## Gazebo Reset

`gazebo.launch.py` converts the configured URDF and adds Mako to a temporary
copy of the pool world before starting Gazebo. The model is part of the initial
world snapshot, so the Gazebo Reset button restores it at (0, 0, -1) rather than
removing a dynamically spawned model. Robot State Publisher uses the same URDF,
including the selected camera settings. Temporary files are cleaned on shutdown.

The world also loads `mako::ResetBuoyancy` to rebuild primitive Volume and
CenterOfVolume metadata removed by reset. Gazebo's stock graded buoyancy system
uses this metadata to resume normal forces; without it, retained startup models
can sink after reset. PoolWaves resets its cached entities, update time and current.

Manual reset regression (after building and sourcing the workspace):
`python3 src/robot_description/test/check_gazebo_reset.py`. It runs an isolated
headless world, moves Mako away from spawn, performs three full resets, checks
camera/odometry recovery and confirms neutral depth afterward. It omits the
external ArduPilot connection; it does not affect a running simulation.

## Movement stability

Complete vehicle COM is aligned with the thruster-array center at CAD
(-0.00003, -0.054, 0.01981) m. Ballast placement includes the camera, IMU,
pressure sensor, rotors and the 1 g hydrodynamic reference link. Horizontal COB
is aligned with COM, with a 54 mm vertical separation for passive stability.
`hydrodynamics_link` is a preserved fixed link at complete vehicle COM so drag
and added-mass forces do not act through the elevated base_link origin.
Roll/pitch linear damping is 3.5 N·m·s/rad, with quadratic damping retained.
Total mass and displacement remain unchanged. The model regression checks
neutral displacement, force-center alignment and translation allocation torque.

Counter-rotating propeller handedness uses Ct=+0.019 for t1/t3/t5 and -0.019
for t2/t4/t6. Gazebo force-command polarity is unchanged; coefficient sign
controls rotor angular velocity and cancels spin-up/spin-down reaction during
surge, sway and heave. Unsupported `torque_coefficient` tags were removed.
