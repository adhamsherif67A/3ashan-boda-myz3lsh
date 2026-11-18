"""Compatibility launch: the team robot_mapping package owns SLAM."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('slam_database_path', default_value=str(Path.home()/'.ros/mako_slam.db')),
        DeclareLaunchArgument('slam_viz', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(
            Path(get_package_share_directory('robot_mapping'))/'launch/mapping.launch.py')),
            launch_arguments={
                'database_path': LaunchConfiguration('slam_database_path'),
                'slam_viz': LaunchConfiguration('slam_viz'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'rviz': 'false',
            }.items()),
    ])
