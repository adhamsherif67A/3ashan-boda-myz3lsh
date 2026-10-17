import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    # 1. Gazebo simulation launch
    robot_description_dir = get_package_share_directory('robot_description')
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'camera_width': '640',
            'camera_height': '360',
            'camera_fps': '5',
            'pilot_fps': '10',
        }.items()
    )

    # 2. Joystick Node
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[{
            'dev': '/dev/input/js0',
            'deadzone': 0.05,
            'autorepeat_rate': 20.0,
        }]
    )

    # 3. MAVROS Node
    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        output='screen',
        parameters=[{
            'fcu_url': 'udp://127.0.0.1:14551@',
            'target_system_id': 1,
            'target_component_id': 1,
            'fcu_protocol': 'v2.0',
        }]
    )

    delayed_mavros_node = TimerAction(
        period=6.0,
        actions=[mavros_node]
    )

    # 4. ROV C++ Controller Node
    rov_controller_node = Node(
        package='ps_rov_control', 
        executable='game_controller',
        name='game_controller_node',
        output='screen'
    )

    delayed_rov_controller_node = TimerAction(
        period=8.0,
        actions=[rov_controller_node]
    )

    return LaunchDescription([
        gazebo_launch,
        joy_node,
        delayed_mavros_node,
        delayed_rov_controller_node,
    ])
