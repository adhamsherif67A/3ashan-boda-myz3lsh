"""RTAB-Map RGB-D SLAM on the ZED left camera, using /zed2i/vo/odometry.

Requires visual_odometry.launch.py (or another source of /zed2i/vo/odometry).
RTAB-Map publishes map -> odom, so do not run another map -> odom publisher.
"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context):
    rtabmap_share = Path(get_package_share_directory('rtabmap_launch'))
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(rtabmap_share / 'launch' / 'rtabmap.launch.py')),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
            'visual_odometry': 'false',
            'rgb_topic': '/zed2i/rgbd/left/image_rect_color',
            'depth_topic': '/zed2i/rgbd/left/depth/image_raw',
            'camera_info_topic': '/zed2i/rgbd/left/camera_info',
            'odom_topic': '/zed2i/vo/odometry',
            'frame_id': 'base_link',
            'map_frame_id': 'map',
            'publish_tf_map': 'true',
            'approx_sync': 'true',
            'approx_sync_max_interval': '0.025',
            'qos': '1',
            'topic_queue_size': '3',
            'sync_queue_size': '8',
            'wait_for_transform': '0.2',
            'args': '--ros-args -p RGBD/LinearUpdate:=0.03 -p RGBD/AngularUpdate:=0.03 -p RGBD/NeighborLinkRefining:=true -p Reg/Strategy:=1 -p Reg/Force3DoF:=false -p Grid/RangeMax:=8.0 -p Odom/ResetCountdown:=3',
            'database_path': LaunchConfiguration('slam_database_path').perform(context),
            'rtabmap_viz': LaunchConfiguration('slam_viz').perform(context),
            'rviz': 'false',
        }.items(),
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('slam_database_path',
                              default_value=str(Path.home() / '.ros' / 'mako_slam.db'),
                              description='RTAB-Map database path. Existing databases are reused, not deleted.'),
        DeclareLaunchArgument('slam_viz', default_value='true', choices=['true', 'false'],
                              description='Open the RTAB-Map viewer.'),
        DeclareLaunchArgument('use_sim_time', default_value='true', choices=['true', 'false'],
                              description='Use /clock (simulation) instead of wall time.'),
        OpaqueFunction(function=launch_setup),
    ])
