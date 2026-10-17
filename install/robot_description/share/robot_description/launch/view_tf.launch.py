"""Inspect the running simulation's TF without publishing any transforms."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    package_share = Path(get_package_share_directory('robot_description'))
    return LaunchDescription([
        DeclareLaunchArgument('view', default_value='model_tf.rviz', choices=['model_tf.rviz', 'pilot_views.rviz']),
        Node(
            package='rviz2', executable='rviz2', name='rviz_tf',
            arguments=['-d', PathJoinSubstitution([str(package_share / 'config'), LaunchConfiguration('view')])],
            parameters=[{'use_sim_time': True}], output='screen',
        ),
    ])
