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


def _components(mask, width, height):
    """Return connected components as sampled (x, y) grid coordinates."""
    seen = bytearray(len(mask))
    components = []
    for start, active in enumerate(mask):
        if not active or seen[start]:
            continue
        seen[start] = 1
        pending = [start]
        points = []
        while pending:
            index = pending.pop()
            x, y = index % width, index // width
            points.append((x, y))
            if x and mask[index - 1] and not seen[index - 1]:
                seen[index - 1] = 1
                pending.append(index - 1)
            if x + 1 < width and mask[index + 1] and not seen[index + 1]:
                seen[index + 1] = 1
                pending.append(index + 1)
            if y and mask[index - width] and not seen[index - width]:
                seen[index - width] = 1
                pending.append(index - width)
            if y + 1 < height and mask[index + width] and not seen[index + width]:
                seen[index + width] = 1
                pending.append(index + width)
        components.append(points)
    return components


def _line_axis(points):
    """Return centroid, major-axis angle, elongation, and major extent."""
    count = len(points)
    if count < 2:
        return None
    mean_x = sum(point[0] for point in points) / count
    mean_y = sum(point[1] for point in points) / count
    xx = sum((point[0] - mean_x) ** 2 for point in points) / count
    yy = sum((point[1] - mean_y) ** 2 for point in points) / count
    xy = sum((point[0] - mean_x) * (point[1] - mean_y) for point in points) / count
    root = math.sqrt(max(0.0, (xx - yy) ** 2 + 4 * xy * xy))
    major = max(0.0, (xx + yy + root) * 0.5)
    minor = max(0.0, (xx + yy - root) * 0.5)
    angle = 0.5 * math.atan2(2 * xy, xx - yy)
    extent = max(
        abs((point[0] - mean_x) * math.cos(angle) +
            (point[1] - mean_y) * math.sin(angle))
        for point in points
    ) * 2.0
    elongation = math.sqrt(major / max(minor, 0.25))
    return mean_x, mean_y, angle, elongation, extent


def detect_transect(message, stride=6):
    """Detect the two blue rails, red boundary rails, and black end bars."""
    encoding = message.encoding.lower()
    if encoding not in ('rgb8', 'bgr8', 'rgba8', 'bgra8'):
        raise ValueError(f'unsupported bottom-camera encoding: {message.encoding}')
    channels = 4 if 'a8' in encoding else 3
    width, height = int(message.width), int(message.height)
    if width <= 0 or height <= 0 or message.step < width * channels:
        raise ValueError('invalid bottom-camera image dimensions or row stride')
    data = message.data
    if len(data) < message.step * height:
        raise ValueError('incomplete bottom-camera image')
    grid_width = (width + stride - 1) // stride
    grid_height = (height + stride - 1) // stride
    blue = bytearray(grid_width * grid_height)
    red = bytearray(grid_width * grid_height)
    black = bytearray(grid_width * grid_height)
    blue_count = red_count = 0
    rgb_order = encoding.startswith('rgb')
    for gy in range(grid_height):
        row = gy * stride * message.step
        for gx in range(grid_width):
            offset = row + gx * stride * channels
            first, green, third = data[offset], data[offset + 1], data[offset + 2]
            r, b = (first, third) if rgb_order else (third, first)
            index = gy * grid_width + gx
            # Require saturated blue rather than merely a larger blue
            # channel. The pool tiles are cyan/grey and otherwise create
            # long false components that resemble the transect rails.
            if (b > 55 and b > r + 35 and b > green + 25 and
                    b > r * 1.35):
                blue[index] = 1
                blue_count += 1
            if r > 35 and r > green * 1.15 and r > b * 1.15:
                red[index] = 1
                red_count += 1
            if max(r, green, b) < 62:
                black[index] = 1

    blue_lines = []
    for points in _components(blue, grid_width, grid_height):
        stats = _line_axis(points)
        if stats and len(points) >= 5 and stats[3] >= 2.0 and stats[4] >= 6:
            blue_lines.append((len(points), stats))
    blue_lines.sort(key=lambda item: item[0], reverse=True)
    blue_pair = False
    blue_midpoint = None
    if len(blue_lines) >= 2:
        first, second = blue_lines[:2]
        angle_delta = abs((first[1][2] - second[1][2] + math.pi / 2) % math.pi - math.pi / 2)
        delta_x = abs(first[1][0] - second[1][0])
        delta_y = abs(first[1][1] - second[1][1])
        separation = math.hypot(delta_x, delta_y)
        vertical_first = abs((first[1][2] - math.pi / 2 + math.pi / 2) % math.pi - math.pi / 2)
        vertical_second = abs((second[1][2] - math.pi / 2 + math.pi / 2) % math.pi - math.pi / 2)
        # In the bottom view, the longitudinal rails run nearly vertically
        # and are separated across the image. Tile seams can be blue too, but
        # they are short, horizontal, or do not form this pair.
        blue_pair = (
            angle_delta < 0.35 and
            vertical_first < 0.45 and
            vertical_second < 0.45 and
            delta_x >= 8 and
            delta_y <= delta_x * 0.65 and
            separation >= 8
        )
        if blue_pair:
            blue_midpoint = ((first[1][0] + second[1][0]) * 0.5 * stride,
                             (first[1][1] + second[1][1]) * 0.5 * stride)

    red_lines = []
    for points in _components(red, grid_width, grid_height):
        stats = _line_axis(points)
        if stats and len(points) >= 5 and stats[3] >= 2.0 and stats[4] >= 6:
            red_lines.append(stats)
    red_seen = bool(red_lines)
    if blue_pair and red_lines:
        # The outer red rails are expected in the wide bottom-camera view.
        # Only treat a red line as a blocker when it intrudes into the
        # corridor bounded by the two blue rails.
        rail_angle = blue_lines[0][1][2]
        normal_x, normal_y = -math.sin(rail_angle), math.cos(rail_angle)
        blue_projection = [
            line[0] * normal_x + line[1] * normal_y
            for _, line in blue_lines[:2]
        ]
        lower = min(blue_projection) - 0.15 * abs(blue_projection[0] - blue_projection[1])
        upper = max(blue_projection) + 0.15 * abs(blue_projection[0] - blue_projection[1])
        red_seen = any(lower <= stats[0] * normal_x + stats[1] * normal_y <= upper
                       for stats in red_lines)
    black_bar = False
    for points in _components(black, grid_width, grid_height):
        stats = _line_axis(points)
        if not stats or len(points) < 8 or stats[3] < 3.0 or stats[4] < 10:
            continue
        # The transect's black marker crosses the blue rails, so the axes
        # should be close to perpendicular in the bottom-camera image.
        if blue_pair:
            rail_angle = blue_lines[0][1][2]
            cross_angle = abs((stats[2] - rail_angle + math.pi / 2) % math.pi - math.pi / 2)
            if abs(cross_angle - math.pi / 2) > 0.55:
                continue
        black_bar = True
        break
    return {
        'blue_pair': blue_pair,
        'blue_count': len(blue_lines),
        'blue_midpoint': blue_midpoint,
        'red_seen': red_seen,
        'red_count': red_count,
        'black_bar': black_bar,
    }


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
