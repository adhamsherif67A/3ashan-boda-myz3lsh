#!/usr/bin/env python3
"""Check vision relay startup and TF with the same runtime as control.launch.py."""
import importlib.util, os, signal, subprocess, time
os.environ.setdefault("ROS_DOMAIN_ID", "158")
if os.environ["ROS_DOMAIN_ID"] in ("0", "42"):
    raise SystemExit("Use an isolated ROS_DOMAIN_ID, e.g. 158")
from pathlib import Path
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import Buffer, TransformListener
from rclpy.time import Time
spec=importlib.util.spec_from_file_location("control_launch",Path(__file__).resolve().parents[1]/"launch/control.launch.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
env=dict(os.environ,**module.odometry_runtime_environment())
log=open("/tmp/mx-odom-runtime-check.log","w")
p=subprocess.Popen(["ros2","run","mako_control","gz_odom_to_mavros.py","--ros-args","-p","reset_on_clock_jump:=true","-p","require_covariance:=true","-p","publish_tf:=true","-p","source_topic:=/test/vision"],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
rclpy.init();node=Node("odom_runtime_fixture");pub=node.create_publisher(Odometry,"/test/vision",10)
buf=Buffer();listener=TransformListener(buf,node)
received=[];node.create_subscription(Odometry,"/mavros/odometry/out",lambda m:received.append(m),10)
try:
 end=time.monotonic()+8
 while time.monotonic()<end:
  assert p.poll() is None,"Relay crashed: see /tmp/mx-odom-runtime-check.log"
  m=Odometry();m.header.frame_id="odom";m.child_frame_id="base_link";m.header.stamp=node.get_clock().now().to_msg();m.pose.pose.position.z=-1.;m.pose.pose.orientation.w=1.
  for i in range(6):m.pose.covariance[i*7]=.001;m.twist.covariance[i*7]=.01
  pub.publish(m);rclpy.spin_once(node,timeout_sec=.1)
  if received and buf.can_transform("odom","base_link",Time()):
   tf=buf.lookup_transform("odom","base_link",Time());assert abs(tf.transform.translation.z+1)<1e-6
   print("PASS: bundled ResetPose imported, validated odometry received, odom -> base_link TF present")
   break
 else:raise AssertionError("No validated odometry or TF")
finally:
 os.killpg(p.pid,signal.SIGINT);p.wait(timeout=5);node.destroy_node();rclpy.shutdown();log.close()
