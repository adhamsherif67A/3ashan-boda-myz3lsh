"""Bounded ROS image delivery: overwrite latest frames instead of Qt queues."""
import math
import os
import queue
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from .simulation import DOMAIN

AUTOPILOT_TOPIC='/mako/autopilot/manual_control'
NEUTRAL=(0.,0.,500.,0.)
KEY_RAMP=120     # per 50 ms: keyboard commands reach full scale in about 0.4 s
# The Mako's ArduSub forward/right axes point opposite to the ZED camera's view
# (realjoy uses invert_forward for the same reason). Keyboard commands are in
# camera terms, so forward and lateral are flipped before they are sent.
FORWARD_SIGN=-1
LATERAL_SIGN=-1

VIEWS={'First person':'/zed2i/zed_node/left/image_rect_color',
       'Third person':'/third_person_camera/image_raw'}


def image_to_qimage(message):
    formats={'rgb8':QImage.Format_RGB888,'bgr8':QImage.Format_BGR888,
             'rgba8':QImage.Format_RGBA8888,'mono8':QImage.Format_Grayscale8}
    if message.encoding not in formats:raise ValueError('Unsupported RGB encoding: '+message.encoding)
    if message.width<=0 or message.height<=0 or len(message.data)<message.step*message.height:
        raise ValueError('Incomplete camera image')
    return QImage(bytes(message.data),message.width,message.height,message.step,
                  formats[message.encoding]).copy()


class RosWorker(QThread):
    message=pyqtSignal(str)

    def __init__(self,domain=DOMAIN):
        super().__init__()
        self.domain=domain;self.lock=threading.Lock();self.frames={};self.telemetry={}
        self.requested_view='First person'
        self.commands=queue.Queue();self.stopping=threading.Event()
        # Keyboard target (x, y, z, r) from the UI thread; None when keyboard piloting is off.
        self.keyboard=None;self.keyboard_output=None;self.release_until=0

    def set_view(self,view):
        if view not in VIEWS:raise ValueError('Unknown camera view')
        with self.lock:
            self.requested_view=view;self.frames.pop('main',None)

    def clear_session(self):
        with self.lock:self.frames.clear();self.telemetry.clear()

    def snapshot(self):
        with self.lock:return dict(self.frames),dict(self.telemetry)

    def frame(self,message,name,view=None):
        image=image_to_qimage(message)
        now=time.monotonic()
        with self.lock:
            if name=='main' and view!=self.requested_view:return
            previous=self.frames.get(name)
            period=now-previous[1] if previous else 0
            fps=(.8*previous[2]+.2/period) if previous and period>.001 else 0
            self.frames[name]=(image,now,fps)

    def state(self,message):
        with self.lock:self.telemetry.update(connected=message.connected,armed=message.armed,
                                             mode=message.mode,state_time=time.monotonic())

    def pwm(self,message):
        with self.lock:self.telemetry['pwm']=list(message.channels[:6])

    def odometry(self,message):
        q=message.pose.pose.orientation
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        velocity=message.twist.twist.linear
        with self.lock:self.telemetry.update(depth=max(0,-message.pose.pose.position.z),
            heading=(270-math.degrees(yaw))%360,
            speed=math.sqrt(velocity.x**2+velocity.y**2+velocity.z**2),nav_time=time.monotonic())

    def validated_odometry(self,message):
        with self.lock:self.telemetry['tracking_time']=time.monotonic()

    def request_arm(self,armed):self.commands.put(('arm',armed))
    def request_mode(self,mode):self.commands.put(('mode',mode))
    def set_keyboard(self,target):
        with self.lock:self.keyboard=target

    def next_command(self,now):
        """MANUAL_CONTROL values to publish now, or None to leave the joystick in charge."""
        with self.lock:keyboard=self.keyboard
        if keyboard is None:
            if self.keyboard_output is not None:
                # Keyboard switched off: send neutral briefly, then hand back to the joystick.
                self.keyboard_output=None;self.release_until=now+.5
            return NEUTRAL if now<self.release_until else None
        current=self.keyboard_output or NEUTRAL
        self.keyboard_output=tuple(a+max(-KEY_RAMP,min(KEY_RAMP,b-a)) for a,b in zip(current,keyboard))
        x,y,z,r=self.keyboard_output
        return (FORWARD_SIGN*x,LATERAL_SIGN*y,z,r)

    def run(self):
        node=None;context=None;executor=None
        try:
            os.environ['ROS_DOMAIN_ID']=str(self.domain)
            import rclpy
            from rclpy.context import Context
            from rclpy.node import Node
            from rclpy.executors import SingleThreadedExecutor
            from rclpy.qos import QoSProfile,ReliabilityPolicy,HistoryPolicy
            from rclpy.parameter import Parameter
            from sensor_msgs.msg import Image
            from nav_msgs.msg import Odometry
            from mavros_msgs.msg import State,RCOut,ManualControl
            from mavros_msgs.srv import CommandBool,SetMode
            context=Context();rclpy.init(context=context)
            node=Node('mako_pilot_station',context=context,parameter_overrides=[Parameter('use_sim_time',value=True)])
            executor=SingleThreadedExecutor(context=context);executor.add_node(node)
            qos=QoSProfile(depth=1,history=HistoryPolicy.KEEP_LAST,reliability=ReliabilityPolicy.BEST_EFFORT)
            node.create_subscription(State,'/mavros/state',self.state,qos)
            node.create_subscription(RCOut,'/mavros/rc/out',self.pwm,qos)
            node.create_subscription(Odometry,'/odometry/gz',self.odometry,qos)
            node.create_subscription(Odometry,'/mavros/odometry/out',self.validated_odometry,qos)
            node.create_subscription(Image,'/bottom_camera/image_raw',lambda msg:self.frame(msg,'bottom'),qos)
            arming=node.create_client(CommandBool,'/mavros/cmd/arming')
            mode=node.create_client(SetMode,'/mavros/set_mode')
            autopilot=node.create_publisher(ManualControl,AUTOPILOT_TOPIC,10)
            active_view=None;video=None;last_autopilot=0
            while not self.stopping.is_set():
                with self.lock:view=self.requested_view
                if view!=active_view:
                    if video:node.destroy_subscription(video)
                    video=node.create_subscription(Image,VIEWS[view],lambda msg,view=view:self.frame(msg,'main',view),qos)
                    active_view=view
                try:action,value=self.commands.get_nowait()
                except queue.Empty:pass
                else:
                    client=arming if action=='arm' else mode
                    if not client.service_is_ready():self.message.emit('Autopilot is not ready for this command.')
                    else:
                        request=CommandBool.Request(value=value) if action=='arm' else SetMode.Request(custom_mode=value)
                        future=client.call_async(request)
                        def done(future,action=action,value=value):
                            try:
                                response=future.result()
                                accepted=response.success if action=='arm' else response.mode_sent
                                self.message.emit(f'{action.title()} {value}: '+('accepted' if accepted else 'rejected by autopilot'))
                            except Exception as error:self.message.emit(str(error))
                        future.add_done_callback(done)
                now=time.monotonic()
                command=self.next_command(now) if now-last_autopilot>=.05 else None
                if command is not None:
                    message=ManualControl();message.x,message.y,message.z,message.r=command
                    autopilot.publish(message);last_autopilot=now
                executor.spin_once(timeout_sec=.025)
        except Exception as error:self.message.emit('ROS connection error: '+str(error))
        finally:
            if executor:executor.shutdown(timeout_sec=1)
            if node:node.destroy_node()
            if context and context.ok():context.shutdown()

    def stop(self):
        self.stopping.set();self.wait(2500)
