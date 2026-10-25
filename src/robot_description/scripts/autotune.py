#!/usr/bin/env python3
"""
mavros_autotune.py — external step-response auto-tuner for ArduSub via MAVROS.

Why external: ArduSub firmware has no AC_AutoTune (unlike Copter). This node
replicates the idea outside the flight controller using MAVROS:
  1. Arm + GUIDED mode
  2. Send a step setpoint (velocity or attitude rate)
  3. Log the response (velocity_local / imu)
  4. Score it (overshoot + settle time)
  5. Adjust one gain (twiddle-style hill-climb), push via /mavros/param/set
  6. Repeat until converged

Tunable target params reuse ArduSub's AC_PosControl/AC_AttitudeControl names:
  PSC_VELXY_P/I   -> horizontal velocity control
  ATC_RAT_RLL_P/I/D -> roll rate control (same idea for PIT/YAW)
"""

import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.logging import LoggingSeverity
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import Imu
from mavros_msgs.srv import ParamSetV2, CommandBool, SetMode
from mavros_msgs.msg import ParamValue


class MavrosAutoTune(Node):
    def __init__(self):
        super().__init__('mavros_autotune')

        # ---- config ----
        self.param_name = 'PSC_VELXY_P'   # or ATC_RAT_RLL_P, etc.
        self.axis = 'vx'                  # 'vx','vy' for velocity; 'rollrate' for attitude
        self.step_cmd = 0.3               # m/s or rad/s
        self.step_time_s = 3.0
        self.gain = 1.0                   # starting value, read real value first
        self.delta = 0.3                  # twiddle step
        self.max_iters = 15
        self.best_score = None
        self.debug = True             # toggle verbose tracing
        self.cb_log_every = 20        # throttle high-rate callback logs (every N msgs)
        self._vel_cb_count = 0
        self._imu_cb_count = 0

        if self.debug:
            self.get_logger().set_level(LoggingSeverity.DEBUG)

        self.vel = TwistStamped()
        self.imu = Imu()

        self.vel_pub = self.create_publisher(TwistStamped, '/mavros/setpoint_velocity/cmd_vel', 10)
        self.create_subscription(TwistStamped, '/mavros/local_position/velocity_local',
                                  self._vel_cb, qos_profile_sensor_data)
        self.create_subscription(Imu, '/mavros/imu/data', self._imu_cb, qos_profile_sensor_data)

        self.arm_cli = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.mode_cli = self.create_client(SetMode, '/mavros/set_mode')
        self.param_cli = self.create_client(ParamSetV2, '/mavros/param/set')
        self.get_logger().debug(
            f'init: param={self.param_name} axis={self.axis} step={self.step_cmd} '
            f'gain0={self.gain} delta0={self.delta} max_iters={self.max_iters}')

    def _vel_cb(self, msg):
        self.vel = msg
        self._vel_cb_count += 1
        if self.debug and self._vel_cb_count % self.cb_log_every == 0:
            self.get_logger().debug(
                f'vel_cb #{self._vel_cb_count}: vx={msg.twist.linear.x:.3f} '
                f'vy={msg.twist.linear.y:.3f} vz={msg.twist.linear.z:.3f}')

    def _imu_cb(self, msg):
        self.imu = msg
        self._imu_cb_count += 1
        if self.debug and self._imu_cb_count % self.cb_log_every == 0:
            self.get_logger().debug(
                f'imu_cb #{self._imu_cb_count}: wx={msg.angular_velocity.x:.3f} '
                f'wy={msg.angular_velocity.y:.3f} wz={msg.angular_velocity.z:.3f}')

    def _call(self, client, req):
        self.get_logger().debug(f'-> calling {client.srv_name} req={req}')
        client.wait_for_service()
        try:
            resp = client.call(req)  # blocking; fine for a one-off tuning script
        except Exception as e:
            self.get_logger().error(f'service call to {client.srv_name} raised: {e}')
            raise
        self.get_logger().debug(f'<- {client.srv_name} resp={resp}')
        return resp

    def set_guided_armed(self):
        self.get_logger().info('switching to GUIDED and arming')
        mode_resp = self._call(self.mode_cli, SetMode.Request(custom_mode='GUIDED'))
        if not getattr(mode_resp, 'mode_sent', True):
            self.get_logger().warn('set_mode(GUIDED) not acknowledged as sent')
        arm_resp = self._call(self.arm_cli, CommandBool.Request(value=True))
        if not getattr(arm_resp, 'success', True):
            self.get_logger().error('arming request failed')
        time.sleep(1.0)

    def push_gain(self, value):
        self.get_logger().debug(f'pushing param {self.param_name} = {value:.4f}')
        req = ParamSetV2.Request()
        req.param_id = self.param_name
        req.value = ParamValue(real=float(value))
        resp = self._call(self.param_cli, req)
        if not getattr(resp, 'success', True):
            self.get_logger().error(f'param set failed for {self.param_name}={value:.4f}')

    def step_response_score(self):
        """Send step, sample response, return simple overshoot+settle score (lower=better)."""
        self.get_logger().debug(f'step_response_score: target={self.step_cmd} duration={self.step_time_s}s')
        t0 = time.time()
        samples = []
        while time.time() - t0 < self.step_time_s:
            cmd = TwistStamped()
            cmd.twist.linear.x = self.step_cmd
            self.vel_pub.publish(cmd)
            samples.append(self.vel.twist.linear.x)
            rclpy.spin_once(self, timeout_sec=0.05)

        # stop
        self.vel_pub.publish(TwistStamped())

        if not samples:
            self.get_logger().warn('step_response_score: no samples captured — check velocity_local topic')

        target = self.step_cmd
        overshoot = max(0.0, max(samples, default=0.0) - target)
        settle_err = abs(samples[-1] - target) if samples else 1.0
        score = overshoot + settle_err
        self.get_logger().debug(
            f'step_response_score: n_samples={len(samples)} '
            f'min={min(samples, default=0):.3f} max={max(samples, default=0):.3f} '
            f'last={samples[-1] if samples else float("nan"):.3f} '
            f'overshoot={overshoot:.3f} settle_err={settle_err:.3f} score={score:.3f}')
        return score

    def safe_shutdown(self):
        self.get_logger().info('Emergency Stop triggered! Halting ROV and reverting to MANUAL...')
        
        # 1. Send absolute zero velocity to kill momentum
        stop_cmd = TwistStamped()
        self.vel_pub.publish(stop_cmd)
        
        # Force the DDS network to flush the published message before the node dies
        rclpy.spin_once(self, timeout_sec=0.1)
        
        # 2. Switch back to MANUAL mode
        try:
            req = SetMode.Request(custom_mode='MANUAL')
            self._call(self.mode_cli, req)
            self.get_logger().info('Successfully switched to MANUAL mode.')
        except Exception as e:
            self.get_logger().error(f'Failed to switch to MANUAL during shutdown: {e}')

    def run(self):
        self.get_logger().info('=== autotune run start ===')
        self.set_guided_armed()
        self.push_gain(self.gain)
        self.best_score = self.step_response_score()
        self.get_logger().info(f'start gain={self.gain:.3f} score={self.best_score:.3f}')

        for i in range(self.max_iters):
            trial = self.gain + self.delta
            self.get_logger().debug(f'iter {i}: trying gain={trial:.4f} (delta={self.delta:.4f})')
            self.push_gain(trial)
            score = self.step_response_score()

            if score < self.best_score:
                self.get_logger().debug(f'iter {i}: improved ({score:.3f} < {self.best_score:.3f}) — accept')
                self.gain = trial
                self.best_score = score
                self.delta *= 1.1
            else:
                self.get_logger().debug(f'iter {i}: worse ({score:.3f} >= {self.best_score:.3f}) — reverse+shrink')
                self.delta *= -0.5  # reverse & shrink (classic twiddle)

            self.get_logger().info(f'iter {i}: gain={self.gain:.3f} score={self.best_score:.3f} delta={self.delta:.4f}')
            if abs(self.delta) < 0.01:
                self.get_logger().debug('delta below threshold — stopping')
                break

        self.push_gain(self.gain)
        self.get_logger().info(f'DONE — {self.param_name} = {self.gain:.3f}')


def main():
    rclpy.init()
    node = MavrosAutoTune()
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().warn('Autotune interrupted by user (Ctrl+C).')
    except Exception:
        node.get_logger().error('autotune run crashed', exc_info=True)
    finally:
        # Guarantee the ROV stops and switches modes before the node is destroyed
        node.safe_shutdown()
        
        node.get_logger().info('=== autotune run end ===')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()