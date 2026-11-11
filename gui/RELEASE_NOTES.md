Unreleased changes on main

- Import the team robot_mapping backend from ibrahim-amr and add optional mako_navigation Nav2 servers.
- Use ZED onboard IMU rotation assistance, matched 30 Hz RGB-D and corrected simulated pixel-center calibration for yaw tracking.
- Keep strict validated-odometry TF ownership, preserve map databases and fix scoped bundled-runtime startup.
- Open the top-down SLAM grid on /rtabmap/map; retain optional 3D point clouds and disable oversized TF overlays.
- Include both new packages in desktop release archives and document the extended physical yaw/SLAM regression.

These source changes require a rebuild and app restart. A main-branch push alone does not publish a signed desktop update.

Operation MX 1.1.0 adds authenticated private GitHub updates and the harder ocean search-and-survey mission.

- Each user configures their own read-only GitHub access. Tokens are stored locally with owner-only permissions and never sent to asset CDN hosts.
- Signed updates download while idle and activate on the next launch after build/startup checks. A previous working release is retained.
- The ocean search cave now has concealed rear-access galleries and a bottom-camera survey target. Real reference photographs and the instructor guide are included.
- The MAVROS AUTOTUNE client starts and cancels the new experimental onboard ArduSub mode, confirms actual heartbeat acceptance and never auto-arms.
- The ArduSub source patch and build instructions are bundled. App updates do not automatically modify or flash vehicle firmware; AUTOTUNE requires the separately patched firmware. Full real-water tuning remains unvalidated.

Existing 1.0.x installations need the new installer once for private GitHub authentication:

1. Download and extract `operation-mx-installer-1.1.0.tar.gz` while signed into GitHub.
2. Close Operation MX and stop its simulation.
3. Run `python3 install.py --upgrade` inside the extracted installer folder.
4. Open Operation MX → GitHub access, enter a token with Contents: Read access to this repository, then Check updates.

New users run `python3 install.py` without `--upgrade`. The usual ROS/Gazebo/MAVROS/native prerequisites still apply. Each GitHub account must have access to this private repository.
