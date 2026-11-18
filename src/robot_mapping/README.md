# Team robot_mapping integration

Imported from Ibrahim's branch; see [UPSTREAM.md](UPSTREAM.md) for provenance.
This guide describes the current workspace integration. The original
[mapping_documentation.md](mapping_documentation.md) describes the older branch
and its topic names, reset-on-launch behavior and slower ICP profile.

Enable SLAM in Operation MX, then Start/Reset simulation. The app starts one mapper
through mako_bringup -> mako_vision/slam.launch.py -> robot_mapping. Its **RViz**
button opens the mapping view. Each session keeps its own rtabmap.db; launch no
longer deletes an existing database. No extra desktop window is opened by default.

For standalone mapping, start the simulation with odometry_source:=vision,
slam:=false and publish_map_tf:=false, then in the same ROS domain:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ROS_DOMAIN_ID=42 ros2 launch robot_mapping mapping.launch.py rviz:=true
```

Do not start a second mapper when the app's SLAM checkbox is already enabled.
Only the mapper publishes map -> odom; the control relay owns odom -> base_link.
Inputs are synchronized /zed2i/rgbd/left RGB, depth and CameraInfo, and accepted
/mavros/odometry/out. Launch topic arguments support remapping for other cameras.
The profile keeps full 3D mapping, 5 cm voxels and bounded queues. Parameters are
in config/rtabmap.yaml. Loop closures depend on scene quality and tracking.

To reuse a database, supply database_path:=/absolute/path/map.db. The sample
pool_mapping_data files are optional Git LFS pointers, not bundled map binaries.
The original screenshot is retained. A navigation-ready horizontal map slice
requires separate preparation before use with mako_navigation.

Validation: all six packages build, desktop unit tests pass, and an isolated
RGB-D fixture produces a nonempty 3D map. Re-run the fixture with:

```bash
ROS_DOMAIN_ID=159 python3 src/robot_mapping/test/check_mapping.py
```

Upstream lint tests additionally require ros-humble-ament-flake8 and
ros-humble-ament-pep257; these optional test tools are not installed on this host.

RViz opens the 2D SLAM occupancy grid on `/rtabmap/map` by default.
Enable **3D point cloud (optional)** in Displays for the 3D reconstruction.
The grid is a projection of the 3D map; it still needs depth-slice/floor filtering
before it can be treated as a safe navigation costmap.
