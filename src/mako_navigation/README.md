# Mako navigation

Nav2 Humble servers for **horizontal navigation at a separately held depth**.
This package owns planning, costmaps and planar controller configuration. The
team dependency direction remains `mako_bringup -> mako_navigation`; model/world
assets stay in `robot_description`, perception in `mako_vision`, and all MAVROS
actuation belongs in `mako_control`.

## Start

Start the simulation with `odometry_source:=vision slam:=true`, survey the scene,
then in the same ROS domain (42 for Operation MX):

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ROS_DOMAIN_ID=42 ros2 launch mako_navigation navigation.launch.py
```

Alternatively add `navigation:=true` to `mako_bringup simulation.launch.py`.
Requires an OccupancyGrid on `/rtabmap/map`, `map -> odom -> rov_base_link`,
validated odometry on `/mavros/odometry/out` and a running `/clock`.
`map_topic:=/your_map` selects a different OccupancyGrid publisher. Nav2 does not
start AMCL or publish a competing map/odom transform.

The full planner/controller/BT/behavior/smoother/waypoint servers are started.
`/compute_path_to_pose` supports planning tests; `/navigate_to_pose` drives only
the isolated `/mako/navigation/cmd_vel` Twist output (raw controller output is
`/mako/navigation/cmd_vel_raw`). It does **not** move or arm the ROV. A controlled,
explicitly enabled adapter in **mako_control** is required before piloting with
Nav2: convert bow-frame velocities to MAVROS, hold depth, arbitrate with the
pilot and missions, check fresh localization/FCU mode, and stop on lost commands.
Without that adapter a NavigateToPose goal eventually fails its progress check.

The conservative circular footprint is 0.5 m with 0.7 m inflation and 0.25 m/s
axis limits. Unknown cells are not traversable. These values require water tests.
Costmaps deliberately use the supplied map rather than fictitious laser scans.
RTAB-Map's whole-height floor-inclusive 3D projection is **not automatically a
safe navigation map**: prepare a free-water horizontal occupancy slice at the
chosen depth, remove floor/ceiling returns, and preserve walls and obstacles.
No 3D cave/overhang clearance or depth planning is provided by this planar stack.

```bash
colcon test --base-paths src --packages-select mako_navigation
colcon test-result --verbose
```

Verified locally: all five ROS packages build; 53 package tests and 28 desktop
tests pass. A synthetic free-water map/TF test activates Nav2 and returns a
55-pose path without connecting to the vehicle. Run it in an unused domain:

```bash
ROS_DOMAIN_ID=157 python3 src/mako_navigation/test/check_planner.py
```

This checks lifecycle/plugin loading and command-topic isolation, not underwater
collision avoidance or end-to-end autonomous flight.
