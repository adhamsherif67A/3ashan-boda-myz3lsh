"""Simulation-only closed-path demo. Ground truth guides control, never SLAM."""
import argparse
import json
import math
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
import numpy as np
from mavros_msgs.msg import ManualControl, State
from mavros_msgs.srv import CommandBool, SetMode
from nav_msgs.msg import Odometry
from rtabmap_msgs.msg import Info, OdomInfo
from .survey_routes import route, wrap


class Driver(Node):
    def __init__(self,args):
        super().__init__('pool_loop_driver');self.args=args
        self.state=None;self.odom=None;self.visual=None;self.info=None
        self.tracking=None;self.tracking_time=0.;self.state_time=0.;self.odom_time=0.
        self.create_subscription(State,'/mavros/state',lambda m:setattr(self,'state',m),qos_profile_sensor_data)
        self.create_subscription(Odometry,'/odometry/gz',lambda m:setattr(self,'odom',m),qos_profile_sensor_data)
        self.create_subscription(Odometry,'/pool_mapping/odom',lambda m:setattr(self,'visual',m),10)
        self.create_subscription(Info,'/pool_mapping/info',lambda m:setattr(self,'info',m),10)
        self.create_subscription(OdomInfo,'/pool_mapping/odom_info',self.tracking_callback,10)
        self.mode=self.create_client(SetMode,'/mavros/set_mode')
        self.arm=self.create_client(CommandBool,'/mavros/cmd/arming')
        self.manual=self.create_publisher(ManualControl,'/mavros/manual_control/send',10)
        self.target=None;self.command=[0.,0.,500.,0.];self.create_timer(.05,self.publish)
        self.log=Path(args.output_dir)/'drive.jsonl';self.log.parent.mkdir(parents=True,exist_ok=True)

    def tracking_callback(self,msg):
        self.tracking=msg;self.tracking_time=time.monotonic()

    def heading(self):
        q=self.odom.pose.pose.orientation
        return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

    def publish(self):
        if self.target is None:return
        x,y,z,r=self.command
        self.manual.publish(ManualControl(x=float(x),y=float(y),z=float(z),r=float(r)))

    def position(self):
        p=self.odom.pose.pose.position
        return np.array([p.x,p.y,p.z])

    def pulse(self,command,duration):
        self.command=command
        until=time.monotonic()+duration
        while time.monotonic()<until:
            rclpy.spin_once(self,timeout_sec=.03)
            p=self.position()
            if abs(p[0])>5.5 or abs(p[1])>4.5 or not -2.6<p[2]<-.35:
                raise RuntimeError('Calibration exceeded pool safety envelope')
        self.command=[0.,0.,500.,0.]

    def calibrate(self):
        columns=[]
        for command in ([300.,0.,500.,0.],[0.,300.,500.,0.]):
            start=self.position()
            self.pulse(command,2.5);self.pulse([0.,0.,500.,0.],1.5)
            delta=(self.position()-start)[:2]
            if np.linalg.norm(delta)<.015:raise RuntimeError('Manual command produced no measurable motion')
            columns.append(delta/np.linalg.norm(delta))
        matrix=np.column_stack(columns)
        if abs(np.linalg.det(matrix))<.3:raise RuntimeError('Lateral/forward control axes not independent')
        self.control_inverse=np.linalg.inv(matrix)
        start=self.position()[2]
        self.pulse([0.,0.,570.,0.],1.5);self.pulse([0.,0.,500.,0.],1.)
        self.vertical_sign=1. if self.position()[2]>start else -1.
        with self.log.open('a') as f:f.write(json.dumps({'type':'calibration','xy_directions':matrix.tolist(),'vertical_sign':self.vertical_sign})+'\n')

    def wait(self,predicate,timeout):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            rclpy.spin_once(self,timeout_sec=.05)
            if predicate():return
        raise RuntimeError('Timed out waiting for simulation/mapping/controller response')

    def call(self,client,request,accepted):
        if not client.wait_for_service(timeout_sec=10):raise RuntimeError('MAVROS service missing')
        future=client.call_async(request);self.wait(future.done,10)
        if not accepted(future.result()):raise RuntimeError('FCU rejected simulation command')

    def run(self):
        self.wait(lambda:self.state is not None and self.state.connected and self.odom is not None
                  and self.visual is not None and self.info is not None and self.info.ref_id>0,90)
        if self.state.armed:raise RuntimeError('Demo requires a disarmed simulator at start')
        if self.manual.get_subscription_count()==0:raise RuntimeError('MAVROS manual subscriber missing')
        self.target=(0.,0.,-1.,0.)
        self.call(self.mode,SetMode.Request(custom_mode='MANUAL'),lambda r:r.mode_sent)
        self.wait(lambda:self.state.mode=='MANUAL',10)
        deadline=time.monotonic()+60
        while not self.state.armed:
            if time.monotonic()>deadline:raise RuntimeError('Simulator did not become ready to arm; check prearm messages')
            try:self.call(self.arm,CommandBool.Request(value=True),lambda r:r.success)
            except RuntimeError as e:self.get_logger().warn(str(e)+'; waiting for simulator initialization')
            until=time.monotonic()+2
            while time.monotonic()<until:rclpy.spin_once(self,timeout_sec=.05)
        # These Mako directions were measured in simulation before this demo.
        # Avoid adding a calibration excursion to the map's initial anchor.
        self.control_inverse=np.diag([1.,-1.]);self.vertical_sign=1.
        if self.args.calibrate:self.calibrate()
        # Keep each leg short; preserve view orientation for reliable revisits.
        a=self.args.size
        targets=route(self.args.route,a)
        for lap in range(self.args.laps):
            for index,target in enumerate(targets):
                self.target=target;deadline=time.monotonic()+180;reached=None
                initial=None;previous=self.position();previous_time=time.monotonic();previous_yaw=self.heading();lost_since=None
                while time.monotonic()<deadline:
                    rclpy.spin_once(self,timeout_sec=.05)
                    if not self.state.connected or not self.state.armed or self.state.mode!='MANUAL':
                        raise RuntimeError('Simulation controller lost MANUAL/armed/connected state')
                    p=self.odom.pose.pose.position
                    if abs(p.x)>5.5 or abs(p.y)>4.5 or not -2.6<p.z<-.35:
                        raise RuntimeError('Simulation safety envelope exceeded')
                    current=self.position();now=time.monotonic()
                    velocity=(current-previous)/max(now-previous_time,.001)
                    yaw=self.heading();yaw_rate=wrap(yaw-previous_yaw)/max(now-previous_time,.001)
                    previous_yaw=yaw
                    previous=current;previous_time=now
                    error_vector=np.array(target[:3])-current
                    rotation=np.array([[math.cos(yaw),math.sin(yaw)],[-math.sin(yaw),math.cos(yaw)]])
                    xy=self.control_inverse @ (rotation @ (220.*error_vector[:2]-650.*velocity[:2]))
                    yaw_error=wrap(target[3]-yaw)
                    self.command=[float(np.clip(xy[0],-280,280)),float(np.clip(xy[1],-280,280)),
                                  500.+self.vertical_sign*float(np.clip(100.*error_vector[2]-180.*velocity[2],-100,100)),
                                  float(np.clip(-500.*yaw_error+500.*yaw_rate,-self.args.yaw_limit,self.args.yaw_limit))]
                    if self.tracking is not None and (self.tracking.lost or now-self.tracking_time>2):
                        lost_since=lost_since or now
                        # Stop the scan immediately; never keep driving through
                        # a blind estimator. Recovery can start a separate map.
                        self.command=[0.,0.,500.,0.]
                        if now-lost_since>15:raise RuntimeError('Visual tracking did not recover within 15 seconds; survey stopped')
                        continue
                    lost_since=None
                    error=float(np.linalg.norm(error_vector))
                    if initial is None:initial=error
                    if error>max(initial+1.2,2*self.args.size+1):raise RuntimeError('Vehicle diverged from waypoint')
                    if error<.3 and abs(yaw_error)<.08:
                        reached=reached or time.monotonic()
                        if time.monotonic()-reached>self.args.dwell:break
                    else:reached=None
                else:raise RuntimeError(f'Waypoint {index} timed out')
                row={'lap':lap,'waypoint':index,'target':target,'actual':[p.x,p.y,p.z],'yaw':yaw,
                     'sim_time':self.get_clock().now().nanoseconds*1e-9}
                with self.log.open('a') as f:f.write(json.dumps(row)+'\n')
                self.get_logger().info(f'Waypoint reached: {row}')
        self.get_logger().info('Closed path completed; waiting for final graph optimization')
        self.command=[0.,0.,500.,0.]
        until=time.monotonic()+8
        while time.monotonic()<until:rclpy.spin_once(self,timeout_sec=.1)

    def stop(self):
        self.command=[0.,0.,500.,0.]
        self.publish()
        if self.state is not None and self.state.armed:
            try:self.call(self.arm,CommandBool.Request(value=False),lambda r:r.success)
            except Exception as e:self.get_logger().error(f'Disarm failed: {e}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size',type=float,default=2.)
    parser.add_argument('--laps',type=int,default=2)
    parser.add_argument('--dwell',type=float,default=3.)
    parser.add_argument('--output-dir',default='/data')
    parser.add_argument('--calibrate',action='store_true',help='Measure axes first (for changed vehicle models)')
    parser.add_argument('--route',choices=['rectangle','yaw','coverage'],default='rectangle')
    parser.add_argument('--yaw-limit',type=float,default=35.,help='Maximum manual yaw command during scanning')
    args,ros_args=parser.parse_known_args()
    if not .5<=args.size<=4 or not 1<=args.laps<=5:parser.error('size .5..4, laps 1..5')
    if not 10<=args.yaw_limit<=250:parser.error('yaw-limit must be 10..250')
    rclpy.init(args=ros_args);node=Driver(args)
    try:node.run()
    except KeyboardInterrupt:pass
    finally:node.stop();node.destroy_node();rclpy.try_shutdown()
