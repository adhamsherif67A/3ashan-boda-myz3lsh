// ArduSub wrapper for ArduPilot's AC_AutoTune_Multi (GPL-3.0-or-later).
#include "Sub.h"

#if AUTOTUNE_ENABLED

bool SubAutoTune::init()
{
    // Each entry is a new session. Aborted/partial sessions are never saved.
    reset();
    frozen_axes = configured_axes();
    return init_internals(false, &sub.attitude_control, &sub.pos_control, &sub.ahrs_view);
}

float SubAutoTune::get_desired_climb_rate_ms() const
{
    return sub.get_pilot_desired_climb_rate(sub.channel_throttle->get_control_in()) * 0.01f;
}

void SubAutoTune::get_pilot_desired_rp_yrate_rad(float &roll, float &pitch, float &yaw_rate)
{
    float roll_cd, pitch_cd;
    sub.get_pilot_desired_lean_angles(sub.channel_roll->get_control_in(),
        sub.channel_pitch->get_control_in(), roll_cd, pitch_cd,
        sub.attitude_control.get_althold_lean_angle_max_cd());
    roll = radians(roll_cd * 0.01f);
    pitch = radians(pitch_cd * 0.01f);
    const float yaw_input = sub.channel_yaw->pwm_to_angle_dz_trim(
        sub.channel_yaw->get_dead_zone() * sub.gain, sub.channel_yaw->get_radio_trim());
    yaw_rate = radians(sub.get_pilot_desired_yaw_rate(yaw_input) * 0.01f);
}

void SubAutoTune::init_z_limits()
{
    sub.pos_control.D_set_max_speed_accel_cm(sub.get_pilot_speed_dn(),
        sub.g.pilot_speed_up, sub.g.pilot_accel_z);
    sub.pos_control.D_set_correction_speed_accel_cm(sub.get_pilot_speed_dn(),
        sub.g.pilot_speed_up, sub.g.pilot_accel_z);
}

#if HAL_LOGGING_ENABLED
void SubAutoTune::log_pids()
{
    sub.logger.Write_PID(LOG_PIDR_MSG, sub.attitude_control.get_rate_roll_pid().get_pid_info());
    sub.logger.Write_PID(LOG_PIDP_MSG, sub.attitude_control.get_rate_pitch_pid().get_pid_info());
    sub.logger.Write_PID(LOG_PIDY_MSG, sub.attitude_control.get_rate_yaw_pid().get_pid_info());
}
#endif

bool ModeAutoTune::init(bool ignore_checks)
{
    // An underwater vehicle has neutral throttle at 0.5, not Copter's zero.
    // Do not use Copter's throttle_zero/auto_armed/land_complete prerequisites.
    const auto previous = sub.control_mode;
    if (previous != Number::STABILIZE && previous != Number::ALT_HOLD && previous != Number::POSHOLD) {
        gcs().send_text(MAV_SEVERITY_WARNING, "AutoTune: enter from Stabilize/DepthHold/PosHold");
        return false;
    }
    if (!motors.armed() || !sub.control_check_barometer() || sub.any_failsafe_triggered() ||
        inertial_nav.get_position_z_up_cm() >= g.surface_depth - 20 || sub.ap.at_bottom ||
        fabsf(ahrs.get_roll_rad()) > radians(10) ||
        fabsf(ahrs.get_pitch_rad()) > radians(10)) {
        gcs().send_text(MAV_SEVERITY_WARNING, "AutoTune: need armed, level, healthy, depth >30cm");
        return false;
    }
    // Verify physical control authority. Six-thruster VECTORED cannot pitch.
    uint8_t supported;
    switch (AP_Motors6DOF::sub_frame_t(g.frame_configuration.get())) {
    case AP_Motors6DOF::SUB_FRAME_VECTORED:
        supported = AUTOTUNE_AXIS_BITMASK_ROLL | AUTOTUNE_AXIS_BITMASK_YAW;
        break;
    case AP_Motors6DOF::SUB_FRAME_VECTORED_6DOF:
    case AP_Motors6DOF::SUB_FRAME_VECTORED_6DOF_90DEG:
        supported = AUTOTUNE_AXIS_BITMASK_ROLL | AUTOTUNE_AXIS_BITMASK_PITCH | AUTOTUNE_AXIS_BITMASK_YAW;
        break;
    default:
        gcs().send_text(MAV_SEVERITY_WARNING, "AutoTune: frame not validated");
        return false;
    }
    axes = autotune.axes();
    if (axes == 0 || (axes & ~supported) != 0) {
        gcs().send_text(MAV_SEVERITY_WARNING, "AutoTune: unsupported AXES; use 4 for yaw");
        return false;
    }
    if (!autotune.init()) {
        return false;
    }
    initial_z_cm = inertial_nav.get_position_z_up_cm();
    started_ms = AP_HAL::millis();
    active = true;
    return true;
}

void ModeAutoTune::stop()
{
    if (active) {
        autotune.stop();  // restore original runtime gains on every mode exit
        active = false;
    }
}

void ModeAutoTune::on_disarm()
{
    if (!active) {
        return;
    }
    // Unlike the base library, never persist a partially completed axis set.
    if (autotune.complete()) {
        autotune.save_tuning_gains();
    } else {
        autotune.stop();
    }
    autotune.release_axes();
    active = false;
}

void ModeAutoTune::run()
{
    if (!motors.armed()) {
        // ArduSub's depth-hold safe handling uses neutral bidirectional thrust.
        sub.mode_althold.run();
        return;
    }
    const bool outside_envelope = inertial_nav.get_position_z_up_cm() >= g.surface_depth - 20 || sub.ap.at_bottom ||
        sub.any_failsafe_triggered() || !sub.control_check_barometer() ||
        fabsf(inertial_nav.get_position_z_up_cm() - initial_z_cm) > 50 ||
        fabsf(ahrs.get_roll_rad()) > radians(35) || fabsf(ahrs.get_pitch_rad()) > radians(35) ||
        AP_HAL::millis() - started_ms > 600000U || autotune.configured_axes() != axes;
    // RC_Channel has already applied the configured dead zone. Any remaining
    // translation demand belongs to the pilot, even at a low joystick gain.
    const bool translate = channel_forward->get_control_in() != 0 ||
                           channel_lateral->get_control_in() != 0;
    if (outside_envelope || translate || autotune.failed()) {
        gcs().send_text(MAV_SEVERITY_WARNING, "AutoTune: aborted; restoring original gains");
        // set_mode performs stop() through exit_mode before running DepthHold.
        if (set_mode(Number::ALT_HOLD, ModeReason::FAILSAFE)) {
            sub.mode_althold.run();
        } else {
            stop();
            set_mode(Number::STABILIZE, ModeReason::FAILSAFE);
        }
        return;
    }
    motors.set_forward(0);
    motors.set_lateral(0);
    // Pilot angular/depth input pauses tuning in the library and restores
    // original gains; translation exits instead of silently being ignored.
    autotune.run();
}

#endif
