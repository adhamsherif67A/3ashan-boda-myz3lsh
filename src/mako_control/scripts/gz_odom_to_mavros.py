#!/usr/bin/env python3
"""Validate body-frame ROS odometry before forwarding it to MAVROS ExternalNav.
MAVROS performs ENU/FLU -> NED/FRD conversion; this node never relabels frames.
"""
import math
import rclpy
from nav_msgs.msg import Odometry
from rclpy.clock import JumpThreshold
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


def motion_error(message, previous, max_linear_speed=0.0, max_angular_speed=0.0):
    """Reject visual tracking jumps even when the estimator reports low variance.

    Limit extrapolation to 200 ms: an outage must not progressively authorize
    a larger jump. Clock/estimator resets explicitly clear the previous pose.
    """
    if previous is None: return None
    stamp = lambda m: m.header.stamp.sec + m.header.stamp.nanosec*1e-9
    dt = min(max(stamp(message)-stamp(previous), 0.0), 0.2)
    p, old = message.pose.pose, previous.pose.pose
    distance = math.sqrt(sum((getattr(p.position,k)-getattr(old.position,k))**2
                             for k in ('x','y','z')))
    if max_linear_speed > 0 and distance > max_linear_speed*dt + 0.02:
        return 'implausible visual position jump; reset simulation if tracking cannot recover'
    dot = abs(sum(getattr(p.orientation,k)*getattr(old.orientation,k)
                  for k in ('x','y','z','w')))
    angle = 2*math.acos(min(1.0, dot))
    if max_angular_speed > 0 and angle > max_angular_speed*dt + 0.02:
        return 'implausible visual orientation jump'
    return None


def validation_error(message, now_ns, max_age=0.75, require_covariance=False,
                     max_variance=1.0, parent='odom', child='base_link'):
    if message.header.frame_id != parent or message.child_frame_id != child:
        return 'unexpected odometry frames (configure the estimator for odom/base_link)'
    stamp = message.header.stamp.sec*1000000000 + message.header.stamp.nanosec
    age = (now_ns-stamp)/1e9
    if stamp <= 0 or age > max_age or age < -0.1:
        return 'stale, future, or missing timestamp'
    p, q = message.pose.pose.position, message.pose.pose.orientation
    v, w = message.twist.twist.linear, message.twist.twist.angular
    values = [p.x,p.y,p.z,q.x,q.y,q.z,q.w,v.x,v.y,v.z,w.x,w.y,w.z]
    if not all(math.isfinite(x) for x in values): return 'non-finite pose or velocity'
    if abs(sum(x*x for x in [q.x,q.y,q.z,q.w])-1) > 0.01:
        return 'invalid orientation (tracking may be lost)'
    for covariance in [message.pose.covariance, message.twist.covariance]:
        if not all(math.isfinite(x) for x in covariance): return 'non-finite covariance'
        diagonal = [covariance[i*7] for i in range(6)]
        if any(x < 0 or x > max_variance for x in diagonal): return 'unreliable covariance / lost tracking'
        if require_covariance and not any(x > 0 for x in diagonal): return 'missing uncertainty estimate'
    return None


class GazeboOdomToMavros(Node):
    def __init__(self):
        super().__init__('gz_odom_to_mavros')
        for key,value in [('source_topic','/odometry/gz'),('target_topic','/mavros/odometry/out'),
                          ('max_age',0.75),('require_covariance',False),('max_variance',1.0),
                          ('reset_on_clock_jump',False),('max_linear_speed',0.0),
                          ('max_angular_speed',0.0),('publish_tf',False)]:
            self.declare_parameter(key,value)
        source=self.get_parameter('source_topic').value
        self.publisher=self.create_publisher(Odometry,self.get_parameter('target_topic').value,10)
        self.subscription=self.create_subscription(Odometry,source,self._odometry_callback,qos_profile_sensor_data)
        self.last_stamp=None
        self.last_message=None
        if self.get_parameter('publish_tf').value:
            from tf2_ros import TransformBroadcaster
            self.tf_broadcaster=TransformBroadcaster(self)
        self.reset_pending=False
        self.reset_future=None
        self.reset_generation=0
        if self.get_parameter('reset_on_clock_jump').value:
            from rtabmap_msgs.srv import ResetPose
            self.reset_type=ResetPose
            self.reset_client=self.create_client(ResetPose,'/zed_rgbd_odometry/reset_odom_to_pose')
            self.reset_timer=self.create_timer(0.1,self._try_reset)
        self.jump=self.get_clock().create_jump_callback(
            JumpThreshold(min_forward=None,min_backward=Duration(nanoseconds=-1),on_clock_change=True),
            post_callback=self._clock_jump)
        self.get_logger().info(f'ExternalNav source: {source}; expected frames odom -> base_link')

    def _clock_jump(self,jump):
        self.last_stamp=None
        self.last_message=None
        if jump.delta.nanoseconds < 0 and self.get_parameter('reset_on_clock_jump').value:
            self.reset_generation+=1
            self.reset_pending=True
            self.reset_future=None
            self.get_logger().info('Simulation reset: pausing ExternalNav until visual odometry resets')

    def _try_reset(self):
        if not self.reset_pending or self.reset_future is not None or not self.reset_client.service_is_ready():return
        request=self.reset_type.Request();request.z=-1.0
        generation=self.reset_generation
        self.reset_future=self.reset_client.call_async(request)
        def done(future):
            if generation != self.reset_generation:return
            if future.exception() is None:
                self.reset_pending=False
                self.get_logger().info('Visual odometry reset to simulation starting pose')
            else:self.reset_future=None
        self.reset_future.add_done_callback(done)

    def _odometry_callback(self,message):
        if self.reset_pending:return
        error=validation_error(message,self.get_clock().now().nanoseconds,
            self.get_parameter('max_age').value,self.get_parameter('require_covariance').value,
            self.get_parameter('max_variance').value)
        stamp=message.header.stamp.sec*1000000000+message.header.stamp.nanosec
        if not error:
            error=motion_error(message,self.last_message,
                self.get_parameter('max_linear_speed').value,
                self.get_parameter('max_angular_speed').value)
        if error or (self.last_stamp is not None and stamp <= self.last_stamp):
            self.get_logger().warn('ExternalNav rejected: '+(error or 'duplicate/out-of-order timestamp'),throttle_duration_sec=2.0)
            return
        self.last_stamp=stamp
        self.last_message=message
        self.publisher.publish(message)
        if self.get_parameter('publish_tf').value:
            from geometry_msgs.msg import TransformStamped
            transform=TransformStamped()
            transform.header=message.header
            transform.child_frame_id=message.child_frame_id
            p=message.pose.pose.position
            transform.transform.translation.x=p.x
            transform.transform.translation.y=p.y
            transform.transform.translation.z=p.z
            transform.transform.rotation=message.pose.pose.orientation
            self.tf_broadcaster.sendTransform(transform)


def main():
    rclpy.init();node=GazeboOdomToMavros()
    try:rclpy.spin(node)
    except (KeyboardInterrupt,ExternalShutdownException):pass
    except Exception:
        if rclpy.ok():raise
    finally:
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()

if __name__=='__main__':main()
