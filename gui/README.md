# MarineXperts Operation MX

Desktop application: **Operation MX**, installed in Software2026 and the application menu.
Double-click `/home/boda/Desktop/OperationMX.desktop`, or run
`/home/boda/Software2026/run_mako_gui.sh`.

Choose Team pool or Ocean, then **Start simulation**. This runs the commands from
`mako_ws/commands.txt` for ArduSub and MAVROS, together with headless Gazebo,
the joy driver, and the existing RealJoy pilot-control node. No terminal emulators,
Gazebo GUI, RViz, MAVProxy map or console windows open. ROS camera sensors still
render on NVIDIA EGL when the driver is available; headless does not disable video.
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
`mako_ws/gui/runs/`. The original GUI and launch files are backed up in `gui/backups/`;
the previous hardware launch is available with `hardware:=true` and the legacy GUI.

The URDF preserves the FRD IMU link during Gazebo conversion and uses a single
IMU pose conversion. The horizontal channel order is M1=t3, M2=t4, M3=t1,
M4=t2; this makes heading corrections produce torque with the correct sign.

Checks:

```bash
source /opt/ros/humble/setup.bash
source /home/boda/mako_ws/install/setup.bash
python3 -m unittest discover -s gui/tests -q
python3 gui/tests/check_application.py
python3 src/robot_description/test/check_control_modes.py
python3 src/robot_description/test/check_control_modes.py --odometry-source vision
```

The live test uses ArduSub instance 8, ROS domain 142, and alternate UDP ports.
It checks Start, both main views, the bottom feed, complete Reset, Stop, and Ocean
selection without taking over the normal instance. Application screenshots are
saved as `gui/app_first_person.png`, `gui/app_third_person.png` and `gui/app_ocean.png`.

The control-mode checks use instance 9, ROS domain 143 and alternate ports.
They test STABILIZE after yaw input and ALT_HOLD after vertical input, using
neutral pilot commands and no physical joystick. Logs are preserved under
`gui/runs/control_checks/`.

Joystick reliability and live tuning: see `JOYSTICK.md` (installed in Software2026
as `JOYSTICK.md`).
