# Mako PS4 C++ controller

Standalone ROS 2 Humble package for the existing `mako-sim` simulation.

## Start everything with one command

```bash
bash launch_all.sh
```

Run from an Ubuntu desktop terminal with the PS4 connected. The default session
now integrates the separate sibling `mako_pool_mapping` package with the original
stack: NVIDIA Gazebo, original robot/TF RViz, mapping RViz, QGroundControl, host
PS4 driver and the existing C++ motion node. It builds both packages, waits for
connected MAVROS and the first RTAB-Map node, then enables the motion node.
No autonomous route or automatic arming is started. Options toggles arm/disarm;
drive the ROV yourself and revisit earlier views to generate loop closures.
Keep this terminal open; press Ctrl+C to request disarm, flush the RTAB-Map
database, export the cloud and then remove this session's container.
Closing one of the managed GUI applications also ends the session.
Stop your previously launched simulation and driver first; the launcher does not
take over an existing `mako-sim`. It refuses a second simultaneous launcher.
This launcher is for the Docker simulation; it is not a ROS XML/Python launch file.

QGroundControl is found in the bundled `apps/` directory, PATH or common download
folders. A custom executable can be selected once and remembered:

```bash
bash launch_all.sh --qgroundcontrol /absolute/path/to/QGroundControl.AppImage
bash launch_all.sh --check
bash launch_all.sh --qgc-software  # QGC graphics fallback; Gazebo still uses NVIDIA
bash launch_all.sh --qgc-software --record-mapping  # record mapping RViz too
bash launch_all.sh --qgc-software --no-mapping     # original session without SLAM
```

QGroundControl v5.0.8 is downloaded from the official release:
https://github.com/mavlink/qgroundcontrol/releases/tag/v5.0.8
The 5.0 documentation lists Ubuntu 22.04 support:
https://docs.qgroundcontrol.com/Stable_V5.0/en/qgc-user-guide/getting_started/download_and_install.html
Keep QGroundControl's own joystick control disabled while using this C++ node,
so two independent controllers do not send movement commands.
Logs are preserved under `runs/<timestamp>/`, separately for each component.
Mapping outputs are persistent host files in `runs/<timestamp>/mapping/`:
`pool.db`, `pool_optimized_cloud.ply`, optimized/raw poses, evidence and validation
JSON, and (with `--record-mapping`) `loop_closure_demo.mp4`. Keep the terminal open
during the save/export message; do not force-close Docker before it finishes.
The mapping image `marinexperts/mako-pool-mapping:boda` is already installed here.
On another machine, put `mako_pool_mapping/` and `mako_ps4_control/` side by side,
then run `bash ../mako_pool_mapping/scripts/install.sh` once. The combined archive
`mako_simulation_bundle.zip` contains both folders and QGroundControl.
`MAKO_CONTAINER_NAME` still selects the active container (default `mako-sim`),
so existing `docker exec mako-sim ...` commands continue to work.
The separate autonomous mapping demo remains available through the mapping
package's `scripts/run.sh --demo --record`; do not run it concurrently.
`--repo /absolute/path` selects another checkout; `--world ocean.world` selects
the ocean. The default is `~/MarineXperts-Season-2027`, pool, domain 42.

| PS4 input | Action |
|---|---|
| Options press | Toggle arm/disarm using confirmed `/mavros/state` |
| Left stick vertical | Forward/backward (`ManualControl.x`) |
| Left stick horizontal | Strafe (`ManualControl.y`) |
| Right stick vertical | Up/down (`ManualControl.z`, neutral 500) |
| Right stick horizontal | Yaw (`ManualControl.r`) |

Uses `joy/game_controller_node` with SDL's standardized mapping: axes 0/1/2/3,
Options/Start button 6. Do not substitute `joy_node` without checking its mapping.
Reference: https://github.com/ros-drivers/joystick_drivers/blob/ros2/joy/README.md

## Run, one step at a time

1. Connect the PS4 controller to Ubuntu, preferably USB for the initial check.
   Keep the pool simulation running. In a host terminal, enumerate controllers:

   ```bash
   source /opt/ros/humble/setup.bash
   ros2 run joy joy_enumerate_devices
   ```

2. From this package directory on the host:

   ```bash
   bash build_in_sim.sh
   ```

   This copies and compiles only this package in `/tmp/mako_ps4_ws` inside the
   running container, then runs its tests. It does not rebuild the large image.
   Repeat after edits or whenever `mako-sim` is removed and recreated.
   The persistent source remains here on the host.

3. In a host terminal, start the input driver:

   ```bash
   bash run_joy_host.sh
   ```

   If the correct device ID is not zero: `PS4_DEVICE_ID=1 bash run_joy_host.sh`.
   Driver runs on the host because the current Docker launcher does not forward
   the SDL event devices. The host needs the `ros-humble-joy` package, which was
   present in the inspected installation. No privileged container is required.

4. In the existing container shell, verify the controller data before launching motion:

   ```bash
   ros2 topic echo /joy
   ```

   Centered sticks should be approximately zero. Options should set button 6
   to 1 while held, and back to 0 on release. Stop echo with Ctrl+C.

5. In another host terminal, start the motion node:

   ```bash
   bash run_motion.sh
   ```

   Keep both driver and motion terminals running. Center both sticks, release
   Options once, then press Options to arm. Press and release Options again to
   disarm. Arming requires MANUAL mode; no mode is changed automatically.
   Verify actual `armed` state with `ros2 topic echo /mavros/state --once`.

## Direction check and tuning

Default gain is 0.5 (50% of command range), with a continuous 8% deadzone.
Forward inversion follows the repository's documented Mako correction. Lateral
inversion is disabled following the user's live direction check; yaw inversion
remains enabled. Verify
all four physical directions in the pool separately after the first arm; this
package has not been driven against the live vehicle from the coding sandbox.
An inverted physical direction is corrected by its parameter at startup:

```bash
bash run_motion.sh -p invert_forward:=false
bash run_motion.sh -p invert_lateral:=true
bash run_motion.sh -p invert_vertical:=true
bash run_motion.sh -p invert_yaw:=false
```

Use only one running motion node. Parameters are startup-only. `gain` accepts
0..1, `deadzone` accepts 0..<0.95, and `joy_timeout` accepts 0.05..5 seconds.
Indices `axis_forward`, `axis_lateral`, `axis_vertical`, `axis_yaw`, and
`options_button` are configurable from 0..63.
Host and container must share ROS_DOMAIN_ID (default 42) and Fast DDS middleware.

## Behavior on lost input

The node publishes at 50 Hz using a wall timer. After 0.5 seconds without joystick
input, missing/invalid axes, disconnected/stale MAVROS state, while disarmed,
outside MANUAL, or while an arming request is pending, commands are neutral:
X/Y/R=0, Z=500. This neutralizes input; it does not automatically disarm or
guarantee the vehicle stops drifting. A held button cannot repeatedly toggle.
A held Options button at startup/reconnect must be released before it can toggle.
Arming requires centered sticks; disarming does not. Service rejection, response
timeout and confirmed armed state are logged. State confirmation takes priority
over a service acknowledgement. Ctrl+C sends a short burst of neutral commands
before shutting down the node; motor arming state is not changed by shutdown.
Do not run another publisher on `/mavros/manual_control/send` concurrently.

## Verification

Standalone core tests cover neutral output, each axis in isolation, bounds,
deadzone, invalid/missing axes, and button rising edges. They can run without ROS:

```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic -I include test/test_controls.cpp -o /tmp/test_mako_controls
/tmp/test_mako_controls
```

The ROS executable was compiled and its control-mapping test passed inside the
simulation container against its installed `mavros_msgs`. The full launcher was
also exercised with `--qgc-software`: all five components remained running,
there was one manual-control publisher, and graceful shutdown removed the owned
simulation container. No arming or vehicle motion was performed during this
launcher check. Host ROS lacks `mavros_msgs`, so builds take place in Docker.
