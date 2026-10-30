"""Log genuine RTAB-Map loop IDs and graph corrections; render evidence in RViz."""
import json
import math
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry
from rtabmap_msgs.msg import Info, MapGraph, OdomInfo
from visualization_msgs.msg import Marker, MarkerArray


class Evidence(Node):
    def __init__(self):
        super().__init__('loop_evidence')
        self.folder=Path(self.declare_parameter('output_dir','/data').value)
        self.folder.mkdir(parents=True,exist_ok=True)
        self.events=(self.folder/'loop_events.jsonl').open('a',buffering=1)
        self.reference=(self.folder/'evaluation_ground_truth.txt').open('a',buffering=1)
        self.last_reference=-1.0
        self.loops=set();self.last_correction=None;self.correction=0.0
        self.tracking_seen=False;self.tracking_frames=0;self.tracking_lost_frames=0
        self.lost_start=None;self.longest_loss=0.;self.recoveries=0;self.inliers=0
        self.raw=[];self.graph=MapGraph();self.last_info=None
        self.pub=self.create_publisher(MarkerArray,'evidence_markers',
            QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.create_subscription(Info,'info',self.info,10)
        self.create_subscription(MapGraph,'mapGraph',self.map_graph,10)
        self.create_subscription(Odometry,'odom',self.odom,10)
        self.create_subscription(Odometry,'/odometry/gz',self.ground_truth,qos_profile_sensor_data)
        self.create_subscription(OdomInfo,'odom_info',self.tracking,10)
        self.create_timer(1.0,self.render)

    def info(self,msg):
        self.last_info=msg
        if msg.loop_closure_id>0:
            key=(msg.ref_id,msg.loop_closure_id)
            if key not in self.loops:
                self.loops.add(key)
                event={'ref_id':msg.ref_id,'loop_closure_id':msg.loop_closure_id,
                       'sim_time':msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
                       'proximity_detection_id':msg.proximity_detection_id,
                       'statistics':dict(zip(msg.stats_keys,msg.stats_values))}
                self.events.write(json.dumps(event)+'\n')
                self.get_logger().info(f'GENUINE LOOP CLOSURE: {key}')

    def map_graph(self,msg):
        self.graph=msg
        t=msg.map_to_odom.translation
        q=msg.map_to_odom.rotation
        current=(t.x,t.y,t.z,q.x,q.y,q.z,q.w)
        delta=0.0 if self.last_correction is None else math.dist(current[:3],self.last_correction[:3])
        self.correction=math.sqrt(t.x*t.x+t.y*t.y+t.z*t.z)
        if delta>0.001:
            self.events.write(json.dumps({'type':'graph_correction','sim_time':msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
              'map_to_odom':current,'translation_change_m':delta,'loop_count':len(self.loops)})+'\n')
        self.last_correction=current
        self.summary()

    def odom(self,msg):
        p=msg.pose.pose.position
        if not all(math.isfinite(x) for x in (p.x,p.y,p.z)):return
        if not self.raw or math.dist((p.x,p.y,p.z),(self.raw[-1].x,self.raw[-1].y,self.raw[-1].z))>0.05:
            self.raw.append(Point(x=p.x,y=p.y,z=p.z))

    def summary(self):
        data={'nodes':len(self.graph.poses_id),'links':len(self.graph.links),
              'global_loop_closures':len(self.loops),'loop_pairs':sorted(self.loops),
              'map_to_odom_translation_m':self.correction,
              'note':'Only positive RTAB-Map loop_closure_id values count as global closures. No artificial drift is injected.'}
        temp=self.folder/'summary.tmp'
        temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(self.folder/'summary.json')

    def tracking(self,msg):
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        self.inliers=msg.inliers
        if not self.tracking_seen and not msg.lost:self.tracking_seen=True
        if self.tracking_seen:
            self.tracking_frames+=1
            if msg.lost:
                self.tracking_lost_frames+=1
                if self.lost_start is None:self.lost_start=stamp
                self.longest_loss=max(self.longest_loss,stamp-self.lost_start)
            elif self.lost_start is not None:
                self.recoveries+=1;self.lost_start=None
        if self.tracking_frames%15==0:
            (self.folder/'tracking_health.json').write_text(json.dumps({
              'frames_after_initialization':self.tracking_frames,'lost_frames':self.tracking_lost_frames,
              'longest_loss_s':self.longest_loss,'recoveries':self.recoveries,
              'currently_lost':msg.lost,'inliers':msg.inliers},indent=2)+'\n')

    def ground_truth(self,msg):
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        if stamp-self.last_reference<.04:return
        self.last_reference=stamp;p=msg.pose.pose.position;q=msg.pose.pose.orientation
        self.reference.write(' '.join(map(str,[stamp,p.x,p.y,p.z,q.x,q.y,q.z,q.w]))+'\n')

    def marker(self,id,kind,color):
        m=Marker();m.header.frame_id='pool_map';m.header.stamp=self.get_clock().now().to_msg()
        m.ns='pool_mapping';m.id=id;m.type=kind;m.action=Marker.ADD;m.pose.orientation.w=1.0
        m.color.r,m.color.g,m.color.b,m.color.a=color
        return m

    def render(self):
        trajectory=self.marker(0,Marker.LINE_STRIP,(0.1,1.0,0.3,1.0));trajectory.scale.x=.04
        trajectory.points=[p.position for p in self.graph.poses]
        raw=self.marker(1,Marker.LINE_STRIP,(1.0,.3,.2,.8));raw.scale.x=.025;raw.points=self.raw
        edges=self.marker(2,Marker.LINE_LIST,(1.0,.9,.1,1.0));edges.scale.x=.08
        poses=dict(zip(self.graph.poses_id,self.graph.poses))
        for link in self.graph.links:
            if link.type==1 and link.from_id in poses and link.to_id in poses:
                edges.points.extend([poses[link.from_id].position,poses[link.to_id].position])
        text=self.marker(3,Marker.TEXT_VIEW_FACING,(1.0,1.0,1.0,1.0));text.scale.z=.35
        text.pose.position.z=3.0
        status='LOST - stop and revisit' if self.lost_start is not None else 'TRACKING'
        text.text=f'Nodes: {len(self.graph.poses_id)} | Global loops: {len(self.loops)}\n{status} | Inliers: {self.inliers} | Map/odom: {self.correction:.3f} m\nGreen: optimized | Red: raw visual odometry | Yellow: loop links'
        self.pub.publish(MarkerArray(markers=[trajectory,raw,edges,text]))

    def destroy_node(self):
        self.summary();self.events.close();self.reference.close();return super().destroy_node()


def main(args=None):
    rclpy.init(args=args);node=Evidence()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()
