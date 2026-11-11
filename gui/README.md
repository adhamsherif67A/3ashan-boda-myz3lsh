# MarineXperts Operation MX

Private desktop releases, GitHub access, the one-time installer and rollback are
documented in [UPDATES.md](UPDATES.md). Versioned installations download signed
updates while idle and activate them between sessions.

Desktop application: **Operation MX**. Build the repository once
(`colcon build --symlink-install --base-paths src` at the repository root), then run
`gui/run_mako_gui.sh`, or install a menu/desktop shortcut with `gui/install_shortcut.sh`.
In Docker: `./docker/run.sh --gui`. The full setup is in the root `README.md`.

Choose Team pool or Ocean, then **Start simulation**. This runs the commands from
`commands.txt` (repository root) for ArduSub and MAVROS, together with headless
Gazebo (`ros2 launch mako_bringup simulation.launch.py`), the joy driver and
`realjoy_node` from `mako_control`. No terminal emulators,
Gazebo GUI, RViz, MAVProxy map or console windows open. ROS camera sensors still
render on NVIDIA EGL when the driver is available; headless does not disable video.

**Enable SLAM mapping** is optional and off by default. It selects ZED visual
odometry, uses a reduced camera resolution and saves a fresh `rtabmap.db` in the
session folder. Managed installations keep those sessions under the stable
application data directory so maps survive updates.

The launch also adds the working Harmonic ArduPilot plugin build directory
`~/ardupilot/ardupilot_gazebo/build`, so Desktop startup does not rely on a terminal
export or the incompatible Gazebo 11 plugin in `/usr/local/lib`.

**RViz** opens the validated odometry/TF viewer in the simulation's ROS domain
with simulation time enabled; start the simulation to enable this button.
**QGroundControl** opens its executable or AppImage. If it is not found, select
it once in the file picker; the application remembers that path. You can also
set `MAKO_QGROUNDCONTROL` to its executable path. The desktop and window icon
use the supplied Operation MX artwork.

SITL loads the complete simulation parameter file with `--add-param-file` before
its first motor output. This includes PWM limits 1240–1760 and vertical motor
directions. The app disables the delayed MAVROS parameter helper, so startup
does not change motor polarity while piloting. Joystick directions are configured in `joystick.cpp`: forward inversion is
enabled and heave inversion disabled. The app applies no direction overrides.

**Reset simulation** stops every process group owned by the current app session,
waits for shutdown, and starts all five jobs afresh. **Stop simulation** and closing
the app perform the same owned-process cleanup. An existing manually launched
simulation must be stopped once before starting the application because it uses
the same standard SITL/MAVROS ports. The app reports occupied ports and preserves
unrelated terminal windows and processes.

The application opens full screen. **F11** or **Full screen** toggles it; start it
with `--windowed` for a normal window. **Camera only** (**H**) hides the side panels
so the pilot view fills the screen. Resize the bottom-camera view by dragging its
top-left corner, or with **[** and **]**; the size is remembered.
The mission timer is also shown at the top of the camera view.

**Keyboard pilot** (next to Capture frame) lets you fly without a gamepad once the
vehicle connects: W/S forward/backward, A/D sideways, Q/E or ←/→ turn, ↑/↓ up/down,
hold Shift for full power instead of half. Commands ramp up over about 0.4 s and
return to neutral when the keys are released, the window loses focus, or the button
is switched off; a gamepad stick still has priority. The app publishes on
`/mako/autopilot/manual_control`, which `realjoy_node` forwards to MAVROS while the
sticks are centred (`src/mako_control/src/joystick.cpp`).

First person uses the ZED left eye. Third person uses a real 720p/30 Hz RGB sensor
1.45 m behind and 0.62 m above the ROV, looking forward/down. It is rigidly attached
to the bow-facing frame, following vehicle translation and rotation. It has no
mass or contact geometry. The bottom camera remains visible in the small inset.
Only the selected main camera and bottom camera are subscribed by the UI. Image
queues are bounded to one, and the GUI paints the latest frame without queuing
per-frame Qt signals. Frame-age monitoring marks stalled streams offline.

The palette follows the team's original navy/silver/gold logo. Vehicle connection,
arming, mode, depth, heading, speed, motor PWM and mission time are displayed.
Heading is compass-style, clockwise from world north (+Y). Gamepad controls use
the existing RealJoy mappings. Arming buttons stay disabled until the managed
session is running and MAVROS has a recent connected state. Camera capture saves
PNG files; the optional recorder requires ffmpeg and an X11 desktop.

Simulation uses ROS domain **42** to separate it from hardware-control sessions.
The simulation sets `MAV_GCS_SYSID=1` to accept joystick movement from the standard MAVROS sender ID. ArduSub otherwise ignores movement while still accepting mode and arming services.

To inspect it from a shell, set `ROS_DOMAIN_ID=42` before using ROS commands.
Override `MAKO_SIM_ROS_DOMAIN_ID` to select another domain. Logs and recordings:
`gui/runs/` (or `$MAKO_DATA_DIR/runs`). The original GUI and launch files are backed
up in `gui/backups/`.

The URDF preserves the FRD IMU link during Gazebo conversion and uses a single
IMU pose conversion. The horizontal channel order is M1=t3, M2=t4, M3=t1,
M4=t2; this makes heading corrections produce torque with the correct sign.

Checks:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash          # repository root, after colcon build
python3 -m unittest discover -s gui/tests -q
python3 gui/tests/check_application.py
python3 src/mako_control/test/check_control_modes.py
python3 src/mako_control/test/check_control_modes.py --odometry-source vision
```

The live test uses ArduSub instance 8, ROS domain 142, and alternate UDP ports.
It checks Start, both main views, the bottom feed, complete Reset, Stop, and Ocean
selection without taking over the normal instance. Application screenshots are
saved as `gui/app_first_person.png`, `gui/app_third_person.png` and `gui/app_ocean.png`.

The control-mode checks use instance 9, ROS domain 143 and alternate ports.
They test STABILIZE after yaw input and ALT_HOLD after vertical input, using
neutral pilot commands and no physical joystick. Logs are preserved under
`gui/runs/control_checks/`.

Joystick reliability and live tuning: see `src/mako_control/JOYSTICK.md`.
