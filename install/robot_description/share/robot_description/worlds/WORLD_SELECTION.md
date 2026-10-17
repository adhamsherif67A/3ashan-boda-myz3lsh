# Team pool and ocean

Default: `ros2 launch robot_description gazebo.launch.py`
Team pool: `ros2 launch robot_description gazebo.launch.py world:=pool.world`
Ocean: `ros2 launch robot_description gazebo.launch.py world:=ocean.world`
Add `odometry_source:=vision` to either command to use ZED-only visual odometry.
Pilot RGB defaults to 720p/30 Hz, depth 15 Hz, automatic NVIDIA offload.

pool.world is an alias for pool.sdf: 14 x 12 m, 3 m depth, open negative-X side,
and ONLY coral garden, fly transect and crab task assets.
ocean.world is 18 x 16 m with a 4 m seabed, local sand texture, three reef borders
and one distinct 9.6 m sunken freighter forming the remaining scenic boundary.
Its maneuvering tasks are one broken shipwreck, one hollow concrete pipe and
one rock arch. Boundaries use visible solid scenery, with natural gaps rather
than invisible enclosure walls.

Both spawn Mako at (0,0,-1), with the original transparent floor logo at (0,0),
yaw -pi/2 after rotating both markings 180 degrees: the artwork top points +X. Markings sit 5 mm
above each textured floor. World reset retains the robot and scene assets.
Launch derives joint-state bridge topics from the selected world name:
CompetitionWorld2025 or OceanWorld, keeping the same public ROS topics.

Water retains the existing 998 kg/m3 calibration to preserve neutral buoyancy.
Ocean waves use 0.025 m amplitude with depth-aware currents down to the seabed.
Saltwater density, refraction and volumetric fluid flow are not simulated.

Ocean sand now has pale fine-grain texture and matching low-relief collision terrain.
The obstacle bases are buried by approximately 4–10 cm, depending on local relief.
