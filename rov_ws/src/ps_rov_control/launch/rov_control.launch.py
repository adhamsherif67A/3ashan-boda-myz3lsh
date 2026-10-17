import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    # 1. Gazebo Simulation
    gazebo_launch = ExecuteProcess(
        cmd=['ros2', 'launch', 'robot_description', 'gazebo.launch.py'],
        output='screen'
    )

    # Clock Bridge (عشان الوقت ميتجمدش)
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # 2. ArduSub SITL (Delay: 3 seconds)
    sitl_cmd = ExecuteProcess(
        cmd=[
            'sim_vehicle.py', '-v', 'ArduSub', '-f', 'vectored', '--model=JSON',
            '-l', '31.312000,30.067222,0,0',
            '--out=udp:127.0.0.1:14550', '--out=udp:127.0.0.1:14551', '--console'
        ],
        output='screen'
    )
    delayed_sitl = TimerAction(period=3.0, actions=[sitl_cmd])

    # 3. MAVROS (Delay: 5 seconds)
    mavros_cmd = ExecuteProcess(
        cmd=['ros2', 'launch', 'mavros', 'apm.launch', 'fcu_url:=udp://127.0.0.1:14551@'],
        output='screen'
    )
    delayed_mavros = TimerAction(period=5.0, actions=[mavros_cmd])

    # 4. PS5 Game Controller Node (زي ما طلبت بالظبط)
    ps5_controller_node = Node(
        package='joy',
        executable='game_controller_node',  # الـ Executable المخصص للـ PS5
        name='ps5_joy_node',                # اسم مميز عشان ميتعارضش مع الكود بتاعك
        output='screen'
    )

    # 5. ROV Controller Custom Node (Delay: 6 seconds)
    custom_rov_controller = Node(
        package='ps_rov_control', 
        executable='game_controller',
        name='rov_controller_node',
        output='screen'
    )
    delayed_controller = TimerAction(period=6.0, actions=[custom_rov_controller])

    return LaunchDescription([
        gazebo_launch,
        clock_bridge,
        ps5_controller_node,
        delayed_sitl,
        delayed_mavros,
        delayed_controller
    ])
