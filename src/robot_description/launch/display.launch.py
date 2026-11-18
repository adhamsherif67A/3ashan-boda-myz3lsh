"""View an existing simulation; standalone model publishers are opt-in."""
from pathlib import Path
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory('robot_description'))
    model = xacro.process_file(str(package_share / 'urdf' / 'robot_description.urdf')).toxml()
    standalone = LaunchConfiguration('standalone')
    view = ['-d', str(package_share / 'config' / 'model_tf.rviz')]
    return LaunchDescription([
        DeclareLaunchArgument(
            'standalone', default_value='false', choices=['true', 'false'],
            description='Publish a standalone model only when Gazebo is stopped.'),
        Node(
            package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
            name='model_joint_state_publisher', condition=IfCondition(standalone),
        ),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            name='model_state_publisher', condition=IfCondition(standalone),
            parameters=[{'robot_description': model, 'use_sim_time': False}],
        ),
        Node(
            package='tf2_ros', executable='static_transform_publisher',
            name='tf_display_odom_base', condition=IfCondition(standalone),
            arguments=['--frame-id', 'odom', '--child-frame-id', 'base_link'],
        ),
        Node(
            package='rviz2', executable='rviz2', name='rviz_tf',
            condition=UnlessCondition(standalone), arguments=view,
            parameters=[{'use_sim_time': True}],
        ),
        Node(
            package='rviz2', executable='rviz2', name='rviz_model',
            condition=IfCondition(standalone), arguments=view,
            parameters=[{'use_sim_time': False}],
        ),
    ])
