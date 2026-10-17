#!/usr/bin/env python3
"""
Fix ArduSub SITL parameters so thrusters stop cleanly after motion and on disarm.

Run with MAVROS active:
    python3 /home/boda/mako_ws/src/robot_description/scripts/fix_ardusub_params.py
"""

import argparse
import subprocess
import time
import sys

# rcl_interfaces/msg/ParameterType values.  ParamSetV2 does not infer a
# parameter's MAVLink type from double_value: enum / integer parameters must
# be sent as PARAMETER_INTEGER or ArduPilot rejects the write.
PARAMETER_INTEGER = 2
PARAMETER_DOUBLE = 3


# Parameters to set for clean thruster stop on neutral stick / disarm.
# Values are (value, ROS ParameterValue type).
PARAMS = {
    # MAVROS apm.launch sends as system 1. ArduSub 4.7 accepts
    # MANUAL_CONTROL only from its configured GCS system ID.
    "MAV_GCS_SYSID": (1, PARAMETER_INTEGER),

    # ── EKF3 STATE ESTIMATION ───────────────────────────────────────────────
    # Gazebo's air-pressure sensor is atmospheric, not hydrostatic, and its
    # value is invalid for an underwater vehicle. The launch selects visual
    # or ground-truth odometry for /mavros/odometry/out; source 6 makes EKF3 use that
    # MAVLink ExternalNav stream for a consistent XYZ pose, velocity, and yaw.
    "VISO_TYPE":      (3, PARAMETER_INTEGER),
    "VISO_POS_X":     (0.0, PARAMETER_DOUBLE),
    "VISO_POS_Y":     (0.0, PARAMETER_DOUBLE),
    "VISO_POS_Z":     (0.0, PARAMETER_DOUBLE),
    "EK3_SRC1_POSXY":  (6, PARAMETER_INTEGER),
    "EK3_SRC1_POSZ":   (6, PARAMETER_INTEGER),
    "EK3_SRC1_VELXY":  (6, PARAMETER_INTEGER),
    "EK3_SRC1_VELZ":   (6, PARAMETER_INTEGER),
    # The Gazebo odometry stream is used for position and velocity.  Its yaw
    # convention is not suitable as an EKF3 yaw source for this model; it
    # creates a wrapped heading error and saturates the horizontal thrusters
    # in Depth Hold.  The URDF IMU is physically FLU -> FRD rotated, so use
    # its stable simulated gyro yaw instead.
    "EK3_SRC1_YAW":    (1, PARAMETER_INTEGER),

    # ── FRAME / MIXER ───────────────────────────────────────────────────────
    # This URDF has four vectored horizontal and two vertical thrusters.  Its
    # Gazebo channel routing implements ArduSub's six-thruster VECTORED frame.
    "FRAME_CONFIG":    (1, PARAMETER_INTEGER),
    "MOT_PWM_MIN": (1240, PARAMETER_INTEGER),
    "MOT_PWM_MAX": (1760, PARAMETER_INTEGER),
    # Preserve the Gazebo mixer polarity for upward heave and restoring roll.
    "MOT_5_DIRECTION": (1, PARAMETER_INTEGER),
    "MOT_6_DIRECTION": (1, PARAMETER_INTEGER),

    # ── THRUSTER SPIN-ARM (KEY FIX) ──────────────────────────────────────────
    # T200 thrusters are bidirectional – no minimum spin needed when armed.
    # Without this, ArduSub commands ~10% thrust (PWM ~1580) on ALL motors
    # when armed at neutral stick, which shakes the model.
    "MOT_SPIN_ARM":     (0.0, PARAMETER_DOUBLE),  # was 0.1 → thrusters now spin only when commanded

    # ── MINIMUM SPIN FLOOR ────────────────────────────────────────────────────
    # Also zero for the same reason (T200 works from 0 thrust bidirectionally).
    "MOT_SPIN_MIN":     (0.0, PARAMETER_DOUBLE),  # was 0.15 → no forced minimum spin

    # ── DISARM BEHAVIOR ───────────────────────────────────────────────────────
    # 0 = on disarm, ArduSub outputs 1500 µs (neutral = 0 N with our deadband)
    # 1 = on disarm, outputs MOT_PWM_MIN, which commands reverse thrust instead of neutral!
    "MOT_SAFE_DISARM":  (0, PARAMETER_INTEGER),   # keep 0 (already correct in mav.parm)

    # ── SPOOL TIME ────────────────────────────────────────────────────────────
    # T200 electronic speed controllers have no spin-up spool time.
    # Keeping 0.5s spool means thrusters ramp up slowly, giving the impression
    # of momentum after a command – looks like they keep spinning.
    "MOT_SPOOL_TIME":   (0.0, PARAMETER_DOUBLE),  # was 0.5s → instant response like real T200

    # ── GCS FAILSAFE ──────────────────────────────────────────────────────────
    # In simulation, MAVROS connection can lag. With FS_GCS_ENABLE=2, ArduSub
    # activates "hold position" failsafe after 5s of no heartbeat, which issues
    # non-zero thrust commands to maintain depth. This looks like motors spinning.
    "FS_GCS_ENABLE":    (0, PARAMETER_INTEGER),   # was 2 → disable in simulation

    # ── PILOT FAILSAFE TIMEOUT ────────────────────────────────────────────────
    "FS_PILOT_TIMEOUT": (10.0, PARAMETER_DOUBLE), # was 3s → increase for simulation

    # ── THROTTLE DEADZONE ─────────────────────────────────────────────────────
    # Keep at 100: this 100-µs deadzone around 1500 µs matches the Gazebo
    # thruster deadband of 0.5 N. At neutral stick, PWM stays in [1400,1600].
    "THR_DZ":           (100, PARAMETER_INTEGER), # keep as-is
}


def set_param(name, value, value_type):
    if value_type == PARAMETER_INTEGER:
        value_field = f"integer_value: {value}"
    else:
        value_field = f"double_value: {value}"

    svc_cmd = [
        "ros2", "service", "call",
        "/mavros/param/set",
        "mavros_msgs/srv/ParamSetV2",
        (f"{{force_set: true, param_id: '{name}', "
         f"value: {{type: {value_type}, {value_field}}}}}")
    ]
    try:
        result = subprocess.run(svc_cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and "success=True" in result.stdout:
            print(f"  OK   {name:30s} = {value}")
            return True
        else:
            print(f"  FAIL {name:30s} = {value}")
            if result.stdout:
                print(f"       {result.stdout.strip()[:160]}")
            if result.stderr:
                print(f"       {result.stderr.strip()[:80]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT {name}")
        return False


def mavros_param_service_available() -> bool:
    """Return true only when MAVROS exposes the expected parameter service."""
    try:
        result = subprocess.run(
            ["ros2", "service", "type", "/mavros/param/set"],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return (result.returncode == 0 and
            result.stdout.strip() == "mavros_msgs/srv/ParamSetV2")


def wait_for_mavros(timeout: float) -> bool:
    """Wait for MAVROS instead of failing every parameter call at launch."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if mavros_param_service_available():
            return True
        time.sleep(1.0)
    return mavros_param_service_available()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--non-interactive', action='store_true',
        help='Apply parameters immediately; used by gazebo.launch.py.')
    parser.add_argument(
        '--wait-for-mavros', type=float, default=0.0, metavar='SECONDS',
        help='Wait for /mavros/param/set before applying parameters.')
    args = parser.parse_args()

    print("=" * 60)
    print("  ArduSub SITL Parameter Fix - Clean Thruster Stop")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  1. Gazebo + SITL running: ros2 launch robot_description gazebo.launch.py")
    print("  2. MAVROS running: ros2 launch mavros apm.launch fcu_url:=udp://127.0.0.1:14551@")
    print()
    if args.wait_for_mavros > 0:
        print(f"Waiting up to {args.wait_for_mavros:g}s for MAVROS...")
        if not wait_for_mavros(args.wait_for_mavros):
            print("MAVROS parameter service did not appear; no parameters changed.")
            return 1

    if not args.non_interactive:
        print("Press ENTER to apply parameters (Ctrl-C to abort)...")
        try:
            input()
        except KeyboardInterrupt:
            print("Aborted.")
            return 0

    print()
    ok = fail = 0
    for name, (value, value_type) in PARAMS.items():
        if set_param(name, value, value_type):
            ok += 1
        else:
            fail += 1
        time.sleep(0.3)

    print()
    print(f"Done: {ok} OK, {fail} failed.")
    print()
    if fail > 0:
        print("For failed params, set manually via MAVProxy:")
        print("  param set MOT_SPIN_ARM 0")
        print("  param set MOT_SPIN_MIN 0")
        print("  param set MOT_SPOOL_TIME 0")
        print("  param set FS_GCS_ENABLE 0")
        print("  param set EK3_SRC1_POSXY 6")
        print("  param set EK3_SRC1_POSZ 6")
        print()
    print("Reboot ArduSub SITL to apply (in MAVProxy: reboot)")
    return int(fail > 0)


if __name__ == "__main__":
    sys.exit(main())
