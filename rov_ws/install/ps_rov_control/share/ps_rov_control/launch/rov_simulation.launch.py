import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    # 1. تشغيل Gazebo Simulation والموديل
    robot_description_dir = get_package_share_directory('robot_description')
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_description_dir, 'launch', 'gazebo.launch.py')
        )
    )

    # 2. تشغيل عقدة قراءة دراع التحكم (joy_node)
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

    # 3. تشغيل عقدة التحكم المخصصة للغواصة
    rov_controller_node = Node(
        package='ps_rov_control', 
        executable='rov_controller',
        name='rov_controller_node',
        output='screen'
    )

    # 4. تشغيل MAVROS للربط مع SITL (بيسمع على بورت 14551)
    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        output='screen',
        parameters=[{
            'fcu_url': 'udp://127.0.0.1:14551@14555',
            'system_id': 255,
            'target_system_id': 1,
            'target_component_id': 1,
            'fcu_protocol': 'v2.0',
        }]
    )

    return LaunchDescription([
        gazebo_launch,
        joy_node,
        rov_controller_node,
        mavros_node,
    ])
