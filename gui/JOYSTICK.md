# Joystick controller

The controller is implemented in `Software2026/src/real_joy/src/joystick.cpp`.
It uses confirmed `/mavros/state` for arming and mode toggles, rather than local
flags. When arming requires MANUAL, it waits for the FCU to confirm that mode
before sending the arming request. Service rejections and five-second response
or mode-confirmation timeouts appear in `pilot_control.log`.

Joystick age uses a monotonic clock. A joystick timeout, disconnected autopilot
or stale autopilot state immediately sends neutral: X/Y/R=0 and Z=500. The
smoothing filter resets at the same time. Simulation clock resets cannot keep
an old motion command active.

Forward inversion is enabled and vertical inversion disabled, preserving the
latest pilot direction adjustments. Live updates take effect without rebuilding
or restarting the controller. Parameters are validated as a batch; an invalid
update does not partially change the mapping. Live values last until node restart.

| Parameters | Default | Valid range |
| --- | --- | --- |
| `deadzone_forward`, `deadzone_lateral`, `deadzone_vertical` | 0.08 | 0–0.95 |
| `deadzone_yaw` | 0.05 | 0–0.95 |
| `expo_forward`, `expo_lateral`, `expo_yaw` | 0.3 | 0–1 |
| `expo_vertical` | 0.2 | 0–1 |
| `sensitivity_forward`, `sensitivity_lateral`, `sensitivity_vertical`, `sensitivity_yaw` | 1.0 | 0–1 |
| `smoothing_tau` | 0.08 seconds | 0–1; zero disables smoothing |
| `joy_timeout_s` | 0.5 seconds | 0.05–5 |
| `publish_rate_hz` | 60.0 | 1–200 |

`invert_forward`, `invert_lateral`, `invert_vertical`, `invert_yaw` are booleans.
Axis mapping parameters accept indices -1 (disabled) through 63. Heave uses the
`vertical` parameters. Dead zones are continuous: motion starts at zero at the
edge of the dead zone and reaches full scale at the end of the stick. Expo
reduces sensitivity near the center while retaining full-scale travel. Sensitivity
limits the maximum commanded movement. Forward, lateral and yaw are clamped to
-1000…1000; heave is clamped to 0…1000, with neutral at 500. Nonfinite input is neutral.

Operation MX's keyboard pilot publishes `mavros_msgs/ManualControl` on
`/mako/autopilot/manual_control` (parameter `autopilot_topic`). While those
commands are fresh (`autopilot_timeout_s`, default 0.3 s) and every stick is
inside its dead zone, the controller forwards them, bounded to the same ranges.
Any stick outside its dead zone has priority. When the commands stop, joystick
control resumes; without a gamepad, one neutral command is sent.

Examples for the application simulation:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 param set /realjoy_node sensitivity_forward 0.65
ros2 param set /realjoy_node expo_forward 0.4
ros2 param set /realjoy_node smoothing_tau 0.08
```

Restart Mako Pilot's simulation once after installing a new controller binary.
To run the isolated integration test without controlling the ROV:

```bash
source /opt/ros/humble/setup.bash
source /home/boda/Software2026/install/local_setup.bash
python3 /home/boda/Software2026/src/real_joy/test/check_joystick.py
```

The test uses ROS domain 144, synthetic joystick/state messages and fake MAVROS
services. It checks command bounds, nonfinite input, live parameter updates,
rejected atomic updates, smoothing, clock-reset timeout, external state changes,
rejected requests, and arming only after actual mode confirmation.
