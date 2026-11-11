#!/usr/bin/env python3
"""Vision-controlled, controlled-speed fly-transect mission for Team Pool.

The mission is idle until /fly_transect/enable receives SetBool(true). The ROV
must already be connected and manually armed. It approaches the known start
end of the pool transect, confirms the black start bar and both blue rails in
the bottom camera, starts when the blue rails are visible without red rails,
drives forward while both blue rails remain visible, and holds when the blue
rails disappear. It never arms the vehicle.
"""
import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped, TwistStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import SetMode
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, qos_profile_sensor_data
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, String
from std_srvs.srv import SetBool

from mako_vision.transect_detector import detect_transect


class FlyTransectMission(Node):
    # Pool model origin and task geometry, metres in map/ENU coordinates.
    START_X = 1.0
    FINISH_X = 4.0
    CENTER_Y = -3.5
    APPROACH_X = 0.62
    APPROACH_DEPTH = 2.55
    NARROW_VIEW_DEPTH = 2.60
    MIN_FLOOR_CLEARANCE = 0.28
    FLOOR_Z = -3.0
    # Smooth position-target ramps sized for a ~5-6 s clean pool run.
    # Red-rail correction or lost detections deliberately pauses the clock.
    MAX_FORWARD_SPEED = 1.50
    WAYPOINT_STEP = 0.75
    FORWARD_SPEED = 0.60
    MOTION_TIMEOUT = 2.5
    MIN_MOTION_PROGRESS = 0.10
    APPROACH_SPEED = 1.40
    DEPTH_SPEED = 0.80
    ALIGN_SPEED = 0.60
    ALIGN_DEPTH_SPEED = 0.25
    IMAGE_TIMEOUT = 1.0
    ODOM_TIMEOUT = 1.0
    BLUE_LOSS_HOLD = 1.0
    BLUE_START_HOLD = 1.5
    BLUE_START_CONFIRM = 2

    def __init__(self):
        super().__init__('fly_transect_mission')
        self.declare_parameter('world', 'pool.world')
        self.declare_parameter('control_rate', 10.0)
        self.world = self.get_parameter('world').value
        self.odom = None
        self.odom_time = 0.0
        self.depth = None
        self.depth_time = 0.0
        self.state = None
        self.observation = None
        self.image_time = 0.0
        self.image_width = 0
        self.image_height = 0
        self.lane_y = None
        self.phase = 'IDLE'
        self.target = None
        self.target_yaw = 0.0
        self.last_tick = time.monotonic()
        self.last_status = ''
        self.start_confirm = 0
        self.finish_confirm = 0
        self.good_lane_confirm = 0
        self.bad_lane_since = None
        self.blue_seen_until = 0.0
        self.last_blue_seen = 0.0
        self.motion_started_at = None
        self.motion_start_x = None
        self.motion_target_x = None
        self.prestream_ticks = 0
        self.mode_future = None
        self.cancel_ticks = 0
        self.position_pub = self.create_publisher(
            PoseStamped, '/mavros/setpoint_position/local', 10)
        self.velocity_pub = self.create_publisher(
            TwistStamped, '/mavros/setpoint_velocity/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/fly_transect/status', 10)
        self.vision_pub = self.create_publisher(String, '/fly_transect/vision_status', 10)
        sensor_qos = qos_profile_sensor_data
        odom_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT,
                              history=HistoryPolicy.KEEP_LAST)
        self.create_subscription(Image, '/bottom_camera/image_raw', self._image_callback, sensor_qos)
        self.create_subscription(Odometry, '/mavros/local_position/odom', self._odom_callback, odom_qos)
        self.create_subscription(Float32, '/rov/depth', self._depth_callback, sensor_qos)
        self.create_subscription(State, '/mavros/state', self._state_callback, sensor_qos)
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.enable_service = self.create_service(SetBool, '/fly_transect/enable', self._enable_callback)
        self.timer = self.create_timer(1.0 / float(self.get_parameter('control_rate').value), self._tick)
        self._status('Idle — manually arm, then press Start Transect to approach the Team Pool course.')

    def _image_callback(self, message):
        try:
            self.observation = detect_transect(message)
            self.image_time = time.monotonic()
            self.image_width = int(message.width)
            self.image_height = int(message.height)
            if self.observation['blue_pair']:
                self.last_blue_seen = self.image_time
            self._vision_status(
                self.observation,
                moving=self.phase == 'CROSS' and self.observation['blue_pair'])
        except (ValueError, IndexError) as error:
            self.observation = None
            self._status(f'Camera image rejected: {error}')

    def _odom_callback(self, message):
        self.odom = message
        self.odom_time = time.monotonic()

    def _depth_callback(self, message):
        value = float(message.data)
        if math.isfinite(value) and value >= 0:
            self.depth = value
            self.depth_time = time.monotonic()

    def _state_callback(self, message):
        self.state = message

    def _status(self, value):
        if value == self.last_status:
            return
        self.last_status = value
        message = String()
        message.data = value
        self.status_pub.publish(message)
        self.get_logger().info(value)

    def _vision_status(self, observation, moving=False):
        if observation is None:
            value = 'BLUE=0 RED=0 STATE=NO_IMAGE FORWARD=0'
        else:
            value = (
                f"BLUE={int(observation['blue_pair'])} "
                f"BLUE_LINES={observation['blue_count']} "
                f"RED={int(observation['red_seen'])} "
                f"STATE={'DETECTED' if observation['blue_pair'] else 'LOST'} "
                f"FORWARD={int(moving)} "
                f"TARGET_X={self.motion_target_x if self.motion_target_x is not None else 0.0:.2f} "
                f"PHASE={self.phase}"
            )
        message = String()
        message.data = value
        self.vision_pub.publish(message)

    def _enable_callback(self, request, response):
        if request.data:
            if self.world != 'pool.world':
                response.success = False
                response.message = 'Fly transect autonomy is available only in Team Pool (pool.world).'
                return response
            now = time.monotonic()
            if self.state is None or not self.state.connected or not self.state.armed:
                response.success = False
                response.message = 'Connect and arm the ROV manually before starting the transect.'
                return response
            if self.odom is None or now - self.odom_time > self.ODOM_TIMEOUT:
                response.success = False
                response.message = 'Waiting for fresh MAVROS local odometry.'
                return response
            if self.depth is None or now - self.depth_time > self.ODOM_TIMEOUT:
                response.success = False
                response.message = 'Waiting for the simulated /rov/depth topic.'
                return response
            if self.observation is None or now - self.image_time > self.IMAGE_TIMEOUT:
                response.success = False
                response.message = 'Waiting for a live bottom-camera image.'
                return response
            if self.phase not in ('IDLE', 'CANCELLED', 'COMPLETE', 'FAULT'):
                response.success = False
                response.message = f'Transect mission is already {self.phase.lower()}.'
                return response
            p = self.odom.pose.pose.position
            self.target = [p.x, p.y, p.z]
            q = self.odom.pose.pose.orientation
            self.target_yaw = math.atan2(
                2.0 * (q.w * q.z + q.x * q.y),
                1.0 - 2.0 * (q.y * q.y + q.z * q.z))
            self.phase = 'PRESTREAM'
            self.prestream_ticks = 0
            self.mode_future = None
            self.start_confirm = self.finish_confirm = self.good_lane_confirm = 0
            self.bad_lane_since = None
            self.lane_y = None
            self.last_blue_seen = 0.0
            self.motion_started_at = None
            self.motion_start_x = None
            self.motion_target_x = None
            response.success = True
            response.message = 'Accepted. Holding position, streaming setpoints, then approaching the first black marker.'
            self._status('Starting — holding current position before GUIDED mode.')
            return response

        if self.phase in ('IDLE', 'CANCELLED'):
            response.success = True
            response.message = 'No active transect mission.'
            return response
        p = self.odom.pose.pose.position if self.odom is not None else None
        if p is not None:
            self.target = [p.x, p.y, p.z]
            self.cancel_ticks = 10
            self.phase = 'CANCEL_HOLD'
            self._status('Cancelling — holding the current position, then returning to ALT_HOLD.')
        else:
            self.phase = 'CANCELLED'
            response.message = 'Cancelled; no current odometry was available for a position hold.'
        response.success = True
        response.message = 'Cancel accepted.'
        return response

    def _pose_target(self, x, y, depth, yaw=None):
        if yaw is None:
            yaw = self.target_yaw
        message = PoseStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'map'
        message.pose.position.x = float(x)
        message.pose.position.y = float(y)
        message.pose.position.z = -float(depth)
        message.pose.orientation.z = math.sin(yaw * 0.5)
        message.pose.orientation.w = math.cos(yaw * 0.5)
        self.position_pub.publish(message)

    def _publish_velocity(self, x=0.0):
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.twist.linear.x = float(x)
        self.velocity_pub.publish(message)

    def _publish_hold(self):
        self._publish_velocity()
        if self.target is not None:
            # Preserve current ENU height. In guided mode the autopilot holds
            # this target if the mission aborts or the image stream is lost.
            self._pose_target(self.target[0], self.target[1], -self.target[2])

    def _request_mode(self, mode):
        if self.mode_future is not None or not self.mode_client.service_is_ready():
            return
        request = SetMode.Request()
        request.custom_mode = mode
        self.mode_future = self.mode_client.call_async(request)

    def _approach_step(self, goal, dt, xy_speed=None, z_speed=None):
        xy_speed = self.APPROACH_SPEED if xy_speed is None else xy_speed
        z_speed = self.DEPTH_SPEED if z_speed is None else z_speed
        if self.target is None:
            p = self.odom.pose.pose.position
            self.target = [p.x, p.y, p.z]
        dx, dy = goal[0] - self.target[0], goal[1] - self.target[1]
        distance = math.hypot(dx, dy)
        if distance > 1e-6:
            step = min(distance, xy_speed * dt)
            self.target[0] += dx / distance * step
            self.target[1] += dy / distance * step
        dz = goal[2] - self.target[2]
        self.target[2] += max(-z_speed * dt, min(z_speed * dt, dz))

    def _set_forward_waypoint(self, current_x):
        target_x = min(self.FINISH_X + 0.35, current_x + self.WAYPOINT_STEP)
        self.target = [target_x, self.CENTER_Y, -self.NARROW_VIEW_DEPTH]
        self.motion_target_x = target_x
        self.motion_started_at = time.monotonic()
        self.motion_start_x = current_x
        self._status(
            f'Forward waypoint set — target x={target_x:.2f}; '
            f'current x={current_x:.2f}.'
        )

    def _vehicle_is_progressing(self, now, current_x):
        if self.motion_started_at is None or self.motion_start_x is None:
            return True
        if current_x - self.motion_start_x >= self.MIN_MOTION_PROGRESS:
            self.motion_started_at = now
            self.motion_start_x = current_x
            return True
        if now - self.motion_started_at > self.MOTION_TIMEOUT:
            self._fail(
                f'forward waypoint not moving vehicle '
                f'(target x={self.motion_target_x:.2f}, current x={current_x:.2f})'
            )
            return False
        return True

    def _at_goal(self, goal, xy=0.16, depth=0.12):
        if self.odom is None:
            return False
        p = self.odom.pose.pose.position
        return (math.hypot(p.x - goal[0], p.y - goal[1]) <= xy and
                abs(p.z - goal[2]) <= depth)

    def _fail(self, reason):
        if self.odom is not None:
            p = self.odom.pose.pose.position
            self.target = [p.x, p.y, p.z]
        self.phase = 'FAULT'
        self._status('FAULT — holding position: ' + reason)

    def _tick(self):
        now = time.monotonic()
        dt = min(0.2, max(0.0, now - self.last_tick))
        self.last_tick = now
        if self.phase in ('IDLE', 'CANCELLED'):
            return
        if self.phase in ('COMPLETE', 'FAULT'):
            self._publish_hold()
            return
        if self.state is None or not self.state.connected or not self.state.armed:
            self._fail('autopilot disconnected or disarmed')
            return
        if self.odom is None or now - self.odom_time > self.ODOM_TIMEOUT:
            self._fail('local odometry became stale')
            return
        if self.phase in ('PRESTREAM', 'WAIT_GUIDED', 'CANCEL_HOLD'):
            self._publish_hold()
            if self.phase == 'PRESTREAM':
                self.prestream_ticks += 1
                if self.prestream_ticks >= 10:
                    self._request_mode('GUIDED')
                    self.phase = 'WAIT_GUIDED'
                    self._status('Requesting GUIDED mode.')
            elif self.phase == 'WAIT_GUIDED':
                if self.state.mode != 'GUIDED':
                    self._request_mode('GUIDED')
                if self.mode_future is not None and self.mode_future.done():
                    try:
                        response = self.mode_future.result()
                    except Exception as error:
                        self._fail(f'GUIDED request failed: {error}')
                        return
                    self.mode_future = None
                    if not response.mode_sent:
                        self._fail('autopilot rejected GUIDED mode')
                        return
                if self.state.mode == 'GUIDED':
                    self.phase = 'SEEK_START'
                    self._status('GUIDED active — waiting for two blue rails with no red rail between them.')
            elif self.phase == 'CANCEL_HOLD':
                if self.cancel_ticks > 0:
                    self.cancel_ticks -= 1
                    return
                if self.state.mode == 'ALT_HOLD':
                    self.phase = 'CANCELLED'
                    self._status('Cancelled — ALT_HOLD requested.')
                else:
                    self._request_mode('ALT_HOLD')
                    if self.mode_future is not None and self.mode_future.done():
                        try:
                            response = self.mode_future.result()
                        except Exception as error:
                            self.mode_future = None
                            self._status(f'Waiting to switch to ALT_HOLD: {error}')
                            return
                        self.mode_future = None
                        if not response.mode_sent:
                            self._status('Waiting for the autopilot to accept ALT_HOLD.')
            return

        if self.state.mode != 'GUIDED':
            self._fail('operator changed flight mode; autonomous motion stopped')
            return

        max_safe_depth = -self.FLOOR_Z - self.MIN_FLOOR_CLEARANCE
        if self.depth is not None and self.depth > max_safe_depth:
            self._fail('depth limit reached; refusing to continue toward the pool floor')
            return
        image_fresh = self.observation is not None and now - self.image_time <= self.IMAGE_TIMEOUT
        if not image_fresh:
            self._publish_hold()
            self._status('Paused — waiting for a fresh bottom-camera frame.')
            if not hasattr(self, 'image_lost_since'):
                self.image_lost_since = now
            elif now - self.image_lost_since > 2.5:
                self._fail('bottom-camera feed lost for more than 2.5 seconds')
            return
        self.image_lost_since = None
        observation = self.observation
        if self.phase == 'APPROACH':
            self.phase = 'SEEK_START'
            self._status('Vision active — waiting for both blue rails with no red rail between them.')
            return

        if self.phase == 'SEEK_START':
            self._publish_hold()
            blue_active = (
                observation['blue_pair'] or
                now - self.last_blue_seen <= self.BLUE_START_HOLD
            )
            if blue_active:
                self.blue_seen_until = now + self.BLUE_LOSS_HOLD
                self.start_confirm += 1
                self._status('Two blue rails detected — starting the autonomous crossing.')
                if self.start_confirm >= self.BLUE_START_CONFIRM:
                    p = self.odom.pose.pose.position
                    self.target = [
                        max(p.x, self.START_X),
                        self.CENTER_Y,
                        -self.NARROW_VIEW_DEPTH,
                    ]
                    self.phase = 'CROSS'
                    self._set_forward_waypoint(max(p.x, self.START_X))
                    self.good_lane_confirm = 0
                    self._status('Following the centerline between the two blue rails.')
            else:
                self.start_confirm = 0
                if observation['blue_pair']:
                    self._status('Blue rails found, but red rails are visible — holding before crossing.')
                else:
                    self._status('Searching at the start area — waiting for both blue rails.')
            return

        if self.phase == 'CROSS':
            blue_active = (
                observation['blue_pair'] or
                now - self.last_blue_seen <= self.BLUE_LOSS_HOLD
            )
            self._vision_status(observation, moving=observation['blue_pair'])
            if observation['blue_pair']:
                self.blue_seen_until = now + self.BLUE_LOSS_HOLD
            if blue_active:
                self.good_lane_confirm += 1
                self.bad_lane_since = None
                p = self.odom.pose.pose.position
                if not self._vehicle_is_progressing(now, p.x):
                    return
                if self.motion_target_x is None or p.x >= self.motion_target_x - 0.12:
                    self._set_forward_waypoint(p.x)
                self._publish_velocity(self.FORWARD_SPEED)
            else:
                self.good_lane_confirm = 0
                if self.bad_lane_since is None:
                    self.bad_lane_since = now
                # Stop thrust immediately on a lost pair. The short hold only
                # filters a transient frame drop before declaring completion.
                p = self.odom.pose.pose.position
                if now - self.bad_lane_since <= self.BLUE_LOSS_HOLD:
                    self._publish_velocity()
                    self._pose_target(
                        self.target[0], self.target[1],
                        -self.target[2])
                    self._status('Vision reacquiring — continuing the last confirmed forward path.')
                else:
                    self.target = [p.x, p.y, p.z]
                    self.phase = 'COMPLETE'
                    self._publish_hold()
                    self._status('Transect complete — blue rails are no longer visible; holding position.')
                    return
            p = self.odom.pose.pose.position


def main():
    rclpy.init()
    node = FlyTransectMission()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok() and node.phase not in ('IDLE', 'CANCELLED'):
            for _ in range(5):
                node._publish_hold()
                time.sleep(0.05)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
