#!/usr/bin/env python3
"""Run a conservative local-frame waypoint mission through MAVROS.

Waypoints use Gazebo / ROS ENU coordinates: ``x,y,depth``.  Depth is positive
down for convenience, and is converted to ROS ``z=-depth`` before publishing.
The node never arms the vehicle.  It publishes the first setpoint before asking
ArduSub to enter GUIDED, then publishes continuously until every waypoint is
within tolerance.  It returns to ALT_HOLD when the mission completes.
"""

import argparse
import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import SetMode
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy


def parse_waypoint(value: str) -> tuple[float, float, float]:
    try:
        x, y, depth = (float(item.strip()) for item in value.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            'waypoint must be x,y,depth (for example: 1.0,0.0,0.8)') from exc
    return x, y, depth


class LocalWaypointMission(Node):
    def __init__(self, waypoints, xy_tolerance, depth_tolerance, dwell, max_xy_error):
        super().__init__('local_waypoint_mission')
        sensor_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.waypoints = waypoints
        self.xy_tolerance = xy_tolerance
        self.depth_tolerance = depth_tolerance
        self.dwell = dwell
        self.max_xy_error = max_xy_error
        self.odom = None
        self.state = None
        self.index = 0
        self.reached_at = None
        self.setpoint_pub = self.create_publisher(
            PoseStamped, '/mavros/setpoint_position/local', 10)
        self.create_subscription(
            Odometry, '/mavros/local_position/odom', self._odom_callback, sensor_qos)
        self.create_subscription(State, '/mavros/state', self._state_callback, sensor_qos)
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')

    def _odom_callback(self, message):
        self.odom = message

    def _state_callback(self, message):
        self.state = message

    def target_message(self):
        x, y, depth = self.waypoints[self.index]
        message = PoseStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'map'
        message.pose.position.x = x
        message.pose.position.y = y
        message.pose.position.z = -depth  # ROS ENU z; command depth is positive down.
        message.pose.orientation.w = 1.0
        return message

    def publish_target(self):
        self.setpoint_pub.publish(self.target_message())

    def request_mode(self, mode):
        if not self.mode_client.wait_for_service(timeout_sec=5.0):
            raise RuntimeError('/mavros/set_mode is unavailable')
        request = SetMode.Request()
        request.custom_mode = mode
        future = self.mode_client.call_async(request)
        while not future.done():
            self.publish_target()
            rclpy.spin_once(self, timeout_sec=0.05)
        if not future.result().mode_sent:
            raise RuntimeError(f'ArduSub rejected {mode}')

    def at_target(self):
        if self.odom is None:
            return False, math.inf, math.inf
        target = self.target_message().pose.position
        position = self.odom.pose.pose.position
        xy_error = math.hypot(position.x - target.x, position.y - target.y)
        depth_error = abs(position.z - target.z)
        return xy_error <= self.xy_tolerance and depth_error <= self.depth_tolerance, xy_error, depth_error

    def run(self):
        deadline = time.monotonic() + 10.0
        while self.odom is None and time.monotonic() < deadline:
            self.publish_target()
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.odom is None:
            raise RuntimeError('no /mavros/local_position/odom received')
        arm_deadline = time.monotonic() + 5.0
        while (self.state is None or not self.state.armed) and time.monotonic() < arm_deadline:
            self.publish_target()
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.state is None or not self.state.armed:
            raise RuntimeError('vehicle must be armed before starting a waypoint mission')

        # PX4 requires a stream before mode switch; ArduSub accepts it too.
        for _ in range(20):
            self.publish_target()
            rclpy.spin_once(self, timeout_sec=0.05)
        self.request_mode('GUIDED')
        self.get_logger().info(f'GUIDED: starting {len(self.waypoints)} local waypoint(s)')

        next_report = 0.0
        while self.index < len(self.waypoints):
            self.publish_target()
            rclpy.spin_once(self, timeout_sec=0.05)
            reached, xy_error, depth_error = self.at_target()
            if xy_error > self.max_xy_error:
                raise RuntimeError(
                    f'position error {xy_error:.2f} m exceeded safety limit '
                    f'{self.max_xy_error:.2f} m')
            now = time.monotonic()
            if now >= next_report:
                x, y, depth = self.waypoints[self.index]
                self.get_logger().info(
                    f'wp {self.index + 1}/{len(self.waypoints)} target=({x:.2f}, {y:.2f}, depth {depth:.2f}) '
                    f'xy_error={xy_error:.2f} depth_error={depth_error:.2f}')
                next_report = now + 1.0
            if reached:
                if self.reached_at is None:
                    self.reached_at = now
                elif now - self.reached_at >= self.dwell:
                    self.get_logger().info(f'waypoint {self.index + 1} reached')
                    self.index += 1
                    self.reached_at = None
            else:
                self.reached_at = None

        self.get_logger().info('mission complete; switching to ALT_HOLD')
        self.request_mode('ALT_HOLD')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--waypoint', action='append', type=parse_waypoint, required=True,
                        help='repeatable x,y,depth waypoint; depth is metres positive down')
    parser.add_argument('--xy-tolerance', type=float, default=0.25)
    parser.add_argument('--depth-tolerance', type=float, default=0.15)
    parser.add_argument('--dwell', type=float, default=1.0,
                        help='seconds within tolerance before advancing')
    parser.add_argument('--max-xy-error', type=float, default=2.0,
                        help='abort and return to ALT_HOLD above this horizontal error (metres)')
    args = parser.parse_args()

    rclpy.init()
    node = LocalWaypointMission(args.waypoint, args.xy_tolerance,
                                args.depth_tolerance, args.dwell, args.max_xy_error)
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().warning('mission cancelled; requesting ALT_HOLD')
        try:
            node.request_mode('ALT_HOLD')
        except Exception as error:
            node.get_logger().error(str(error))
    except Exception as error:
        node.get_logger().error(str(error))
        try:
            node.request_mode('ALT_HOLD')
        except Exception as mode_error:
            node.get_logger().error(f'could not switch to ALT_HOLD: {mode_error}')
        raise
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
