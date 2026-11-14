import os
from launch import LaunchDescription
from launch.actions import TimerAction, ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    ardupilot_dir = os.path.expanduser('~/ardupilot')
    ardusub_dir = os.path.join(ardupilot_dir, 'ArduSub')
    sim_vehicle_path = os.path.join(ardupilot_dir, 'Tools', 'autotest', 'sim_vehicle.py')

    # Clean environment so ROS 2 PYTHONPATH does not conflict with MAVProxy/pymavlink
    sitl_env = os.environ.copy()
    sitl_env.pop('PYTHONPATH', None)

    # 1. Gazebo Simulation
    gazebo_launch = ExecuteProcess(
        cmd=['ros2', 'launch', 'robot_description', 'gazebo.launch.py'],
        output='screen'
    )

    # Clock Bridge
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # 2. ArduSub SITL (Delay: 4 seconds)
    sitl_cmd = ExecuteProcess(
        cmd=[
            'gnome-terminal',
            f'--working-directory={ardusub_dir}',
            '--',
            'python3', sim_vehicle_path,
            '-v', 'ArduSub',
            '-f', 'vectored',
            '--model=JSON',
            '-l', '31.312000,30.067222,0,0',
            '--out=udp:127.0.0.1:14550',
            '--out=udp:127.0.0.1:14551',
            '--console'
        ],
        env=sitl_env,
        output='screen'
    )
    delayed_sitl = TimerAction(period=4.0, actions=[sitl_cmd])

    # 3. MAVROS (Delay: 9 seconds, after SITL opens port 14551)
    mavros_cmd = ExecuteProcess(
        cmd=['ros2', 'launch', 'mavros', 'apm.launch', 'fcu_url:=udp://127.0.0.1:14551@'],
        output='screen'
    )
    delayed_mavros = TimerAction(period=9.0, actions=[mavros_cmd])

    # 4. Keyboard Teleop Node
    keyboard_joy_node = Node(
        package='rov_joystick',
        executable='keyboard_to_joy_node',
        name='keyboard_joy_node',
        prefix='gnome-terminal --',
        output='screen'
    )

    # 5. ROV Joystick Translator Node (Delay: 10 seconds)
    rov_joystick_node = Node(
        package='rov_joystick',
        executable='rov_joystick_node',
        name='rov_joystick_node',
        output='screen'
    )
    delayed_controller = TimerAction(period=10.0, actions=[rov_joystick_node])

    return LaunchDescription([
        gazebo_launch,
        clock_bridge,
        keyboard_joy_node,
        delayed_sitl,
        delayed_mavros,
        delayed_controller
    ])
