# Experimental onboard ArduSub AUTOTUNE

This patch adds **AUTOTUNE, custom mode 15**, to ArduSub using ArduPilot's
existing `AC_AutoTune_Multi` library. The control and gain-search loops run on
the flight controller at the vehicle loop rate, not over ROS or the tether.
The same implementation builds for SITL and FMUv3 (Pixhawk 2.4.8 / STM32F427).

MAVROS already maps ArduSub mode 15 to `AUTOTUNE`. No MAVROS fork, MAVLink dialect
change or Copter firmware is required. Stock ArduSub does not implement this
mode; requesting it without the patched firmware will be rejected.

## Version and hardware scope

- The patch base is recorded in [BASE_COMMIT](BASE_COMMIT): the local ArduPilot
  checkout identifies itself as **ArduSub 4.7.0-dev**.
- The official stable FMUv3 download checked during implementation reports
  **ArduSub 4.7.2**. This build is **not** that stock image and the patch has not
  been validated against that stable source revision.
- The generated `dist/firmware/ardusub-fmuv3-autotune-4.7.0-dev.apj` is an
  experimental **FMUv3** image (board ID 9), with build metadata and SHA-256 in
  `dist/firmware/BUILD_INFO.json`. Nothing is flashed automatically.
- A successful cross-build verifies compilation and flash size, not behavior in
  water. Real thruster signs, sensor calibration and dynamics still require a
  supervised hardware validation. Back up the real vehicle parameters before
  evaluating a custom image. Do not copy a SITL tune onto the real ROV.

## What is tuned

`AUTOTUNE_AXES` defaults to **4: yaw only**.

| FRAME_CONFIG | Supported mask | Physical axes |
| --- | --- | --- |
| 1: six-thruster VECTORED | 1, 4 or 5 | Roll and/or yaw; **no pitch authority** |
| 2 / 3: VECTORED_6DOF / 90DEG | 1 through 7 | Selected roll, pitch and/or yaw |
| Other/custom frames | Rejected | No unverified mixer assumptions |

Yaw is the initial default. Roll and pitch selections use the existing library
but require their own vehicle validation. The mode tunes attitude/rate gains;
it does **not** tune heave/depth, surge/sway velocity, buoyancy or thruster PWM
limits. `PSC_*` depth gains and all motor directions/limits remain unchanged.

## ROV-specific behavior

- Enter from STABILIZE, ALT_HOLD or POSHOLD, already armed, healthy and level
  within 10 degrees. Arming while in AUTOTUNE is disallowed.
- Keep more than 20cm below `SURFACE_DEPTH` (30cm below the surface with the
  default -10cm surface threshold), with no detected bottom contact.
- The surface check uses the same fused Z reference as Depth Hold. This avoids
  a boot-calibrated simulator pressure reference disagreeing with ExternalNav.
  The real vehicle must have a correctly referenced depth estimate too.
- Depth hold runs during the attitude twitches. Translation output is zero.
  POSHOLD entry does not imply horizontal station keeping: this first port uses
  depth hold and requires open water clear of the cave, walls, tether and people.
- Angular/depth pilot input pauses the library and restores original gains;
  releasing those sticks allows its normal resume behavior.
- Forward/lateral input exits into ALT_HOLD. Selecting another mode also exits.
- Sensor/failsafe indications, bottom contact, shallow depth, more than 0.5m of
  depth deviation, more than 35 degrees of roll/pitch, a library failure, an AXES
  change, or a ten-minute session timeout abort the tune and restore originals.
- Axes are frozen internally during a run so changing AXES cannot accidentally
  leave the originally tuned axis at a temporary gain.
- Disarming before the entire selected tune completes restores originals and
  saves **nothing**, including when only one of several axes has completed.
- On `AutoTune: Success`, the mode continues with original gains. Disarm while
  still in AUTOTUNE to explicitly save the completed tune. Exiting the mode
  instead discards it. Successful gains are persisted using the library's normal
  parameter storage. No automatic arming or disarming is performed.

## Apply and build

Keep existing unrelated ArduPilot changes. Against the recorded base:

```bash
cd /path/to/ardupilot
git apply --check /path/to/mako_ws/firmware/ardusub-autotune/ardusub-autotune.patch
git apply /path/to/mako_ws/firmware/ardusub-autotune/ardusub-autotune.patch
./waf configure --board sitl
./waf sub -j2
```

For a separate FMUv3 build:

```bash
./waf configure --board fmuv3
./waf sub -j2
# Image: build/fmuv3/bin/ardusub.apj
# Restore the normal simulation configuration afterwards:
./waf configure --board sitl
```

The hardware commands only create files; they do not flash a controller. A
different ArduSub version may need a port rather than a blind patch application.
`prepare_patch.py /path/to/ardupilot` regenerates the reviewable patch against an
unpatched compatible tree. Maintainers can use `--from-head` to regenerate after
editing this port against its committed base; do not use that option to
overwrite other people's changes in the firmware tree.

## Use through ROS 2 / MAVROS

Build/source the simulation package normally so `autotune.py` is installed:

```bash
colcon build --symlink-install --packages-select robot_description
source install/setup.bash
ros2 run robot_description autotune.py status
```

Start the simulation or connect MAVROS to the real patched FCU. The client uses
the same MAVROS interface in either case. Select ALT_HOLD, arm manually and move
to a clear submerged test area before requesting:

```bash
ros2 run robot_description autotune.py start
ros2 topic echo /mavros/statustext/recv
# Abort and restore pre-tune gains:
ros2 run robot_description autotune.py stop
```

`--namespace /other/mavros` and `--timeout 15` are available. The client verifies
the submarine/ArduPilot identity and firmware parameter presence, never arms,
never sends motion setpoints or changes gains, and waits for a subsequent FCU
heartbeat confirming mode acceptance. `mode_sent: true` alone is insufficient.
Stopping outside AUTOTUNE preserves the pilot's selected mode.

The direct MAVROS request is also available after installing patched firmware:

```bash
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'AUTOTUNE'}"
```

Check `/mavros/state` for actual mode entry. A stock firmware rejection is
expected, even if MAVROS reports that it sent the request.

The former external `scripts/autotune.py` step-response script has been replaced:
it no longer auto-arms, pushes guessed gains, or sends velocity steps.

## Validation

```bash
python3 -m pytest -q src/robot_description/test/test_autotune_client.py
python3 src/robot_description/test/check_autotune.py
```

The live regression uses isolated DDS/Gazebo domains, SITL instance, UDP ports
and EEPROM directory. It checks disarmed rejection, unsupported pitch rejection,
running the mode, mode-exit gain restoration, AXES-change restoration,
translation abort and incomplete-disarm restoration. It does not connect to
real hardware or certify a full converged tune in water.

Verified on 2026-10-25: SITL and FMUv3 builds passed, all nine client unit tests
passed, and the live regression passed all entry/abort/restoration checks,
including the actual CLI start/stop path and forced FCU parameter refreshes.
FMUv3 uses approximately 1.412MB of flash with approximately 669kB remaining.
A complete converged tune and the completed-tune saving path still need an
extended vehicle validation; these checks exercised cancellation and partial
tunes. The real controller was not connected or flashed.

## Source and licensing

The port and patch adapt ArduPilot's GPL-3.0-or-later vehicle/library integration.
They retain that license. The gain-search algorithm remains in the upstream
`libraries/AC_AutoTune` code rather than being copied into MAVROS.

- [ArduSub mode definitions](https://github.com/ArduPilot/ardupilot/blob/master/ArduSub/mode.h)
- [AC_AutoTune library](https://github.com/ArduPilot/ardupilot/tree/master/libraries/AC_AutoTune)
- [ArduSub tuning documentation](https://ardupilot.org/sub/docs/manual-tuning.html)
- [MAVROS mode mappings](https://github.com/mavlink/mavros/blob/ros2/mavros/src/lib/uas_stringify.cpp)
- [Official stable FMUv3 builds](https://firmware.ardupilot.org/Sub/stable/fmuv3/)
