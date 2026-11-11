"""Pilot control: gamepad driver plus realjoy_node, which sends MANUAL_CONTROL to MAVROS.

realjoy_node also forwards /mako/autopilot/manual_control (Operation MX keyboard
pilot and autopilot tasks) while every stick is centred.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    return LaunchDescription([
        DeclareLaunchArgument('joystick', default_value='true', choices=['true', 'false'],
                              description='Start the joy game_controller_node gamepad driver.'),
        DeclareLaunchArgument('use_sim_time', default_value='false', choices=['true', 'false'],
                              description='Use /clock (simulation) instead of wall time.'),
        Node(package='joy', executable='game_controller_node', name='game_controller_node',
             condition=IfCondition(LaunchConfiguration('joystick')),
             parameters=[{'use_sim_time': use_sim_time}], output='screen'),
        Node(package='mako_control', executable='realjoy_node', name='realjoy_node',
             parameters=[{'use_sim_time': use_sim_time}], output='screen'),
    ])
