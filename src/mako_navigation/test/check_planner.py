#!/usr/bin/env python3
"""Manual integration check: isolated synthetic map/TF, never connects to MAVROS."""
import os, subprocess, signal, time
os.environ.setdefault("ROS_DOMAIN_ID", "157")
if os.environ["ROS_DOMAIN_ID"] in ("0", "42"):
    raise SystemExit("Use an isolated ROS_DOMAIN_ID, e.g. 157")
os.environ.setdefault("ROS_LOG_DIR", "/tmp/mx-nav-fixture")
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, Odometry
from nav2_msgs.action import ComputePathToPose
from lifecycle_msgs.srv import GetState
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
rclpy.init(); node=Node("navigation_fixture")
tf=StaticTransformBroadcaster(node)
trans=[]
for parent,child in [("map","odom"),("odom","rov_base_link")]:
 t=TransformStamped();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;t.header.stamp=node.get_clock().now().to_msg();trans.append(t)
tf.sendTransform(trans)
q=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
pub=node.create_publisher(OccupancyGrid,"/rtabmap/map",q)
m=OccupancyGrid();m.header.frame_id="map";m.info.resolution=.05;m.info.width=120;m.info.height=120;m.info.origin.position.x=-3.;m.info.origin.position.y=-3.;m.info.origin.orientation.w=1.;m.data=[0]*14400
odompub=node.create_publisher(Odometry,"/mavros/odometry/out",10)
def update():
 m.header.stamp=node.get_clock().now().to_msg();pub.publish(m)
 o=Odometry();o.header=m.header;o.header.frame_id="odom";o.child_frame_id="rov_base_link";o.pose.pose.orientation.w=1.;odompub.publish(o)
node.create_timer(.1,update)
log=open("/tmp/mx-nav2-fixture.log","w")
p=subprocess.Popen(["ros2","launch","mako_navigation","navigation.launch.py","use_sim_time:=false"],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
 client=ActionClient(node,ComputePathToPose,"/compute_path_to_pose")
 deadline=time.monotonic()+25
 while not client.server_is_ready() and time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.1)
 assert client.server_is_ready(),"Planner action unavailable"
 state=node.create_client(GetState,"/planner_server/get_state")
 assert state.wait_for_service(timeout_sec=10)
 while time.monotonic()<deadline:
  ready=state.call_async(GetState.Request());rclpy.spin_until_future_complete(node,ready,timeout_sec=2)
  if ready.result() and ready.result().current_state.id==3:break
  rclpy.spin_once(node,timeout_sec=.2)
 else:raise AssertionError("Planner failed to activate")
 for _ in range(20):rclpy.spin_once(node,timeout_sec=.1)
 goal=ComputePathToPose.Goal();goal.start.header.frame_id="map";goal.start.pose.orientation.w=1.;goal.goal.header.frame_id="map";goal.goal.pose.position.x=1.;goal.goal.pose.position.y=1.;goal.goal.pose.orientation.w=1.;goal.use_start=True;goal.planner_id="GridBased"
 future=client.send_goal_async(goal)
 rclpy.spin_until_future_complete(node,future,timeout_sec=10);handle=future.result();assert handle and handle.accepted,"Goal rejected"
 future=handle.get_result_async();rclpy.spin_until_future_complete(node,future,timeout_sec=10)
 result=future.result();assert result and result.status==4,result
 assert len(result.result.path.poses)>5
 print("PASS: lifecycle planner computed path:",len(result.result.path.poses),"poses")
 topics=dict(node.get_topic_names_and_types())
 assert "/cmd_vel" not in topics
 assert "/mako/navigation/cmd_vel_raw" in topics
 print("Command topics:",[(name,types) for name,types in node.get_topic_names_and_types() if "cmd_vel" in name])
finally:
 os.killpg(p.pid,signal.SIGINT)
 try:p.wait(timeout=8)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 node.destroy_node();rclpy.shutdown();log.close()
