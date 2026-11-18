"""Vehicle-control side of the simulation: everything between the sensors and ArduSub.

Starts the ExternalNav odometry relay to MAVROS, the odom -> odom_ned frame MAVROS
needs, the (idle) fly-transect mission and, optionally, the ArduSub parameter helper.
MAVROS itself is started separately (see mavros.launch.py or commands.txt) because
its FCU URL depends on the deployment.
"""
import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def odometry_runtime_environment():
    """Expose bundled RTAB-Map message bindings to the independent control node.

    Vision launches are scoped by GroupAction; their environment does not reach
    this sibling launch. Native apt installations need no overrides.
    """
    try:
        get_package_share_directory('rtabmap_msgs')
        return {}
    except LookupError:
        pass
    share = Path(get_package_share_directory('mako_control'))
    candidates = [Path(os.environ.get('MAKO_VO_PREFIX', '/nonexistent'))]
    candidates += [p / '.deps/rtabmap/root/opt/ros/humble'
                   for p in list(share.parents) + list(share.resolve().parents)]
    prefix = next((p for p in candidates if (p / 'share/rtabmap_msgs').is_dir()), None)
    if prefix is None:
        raise RuntimeError('Vision odometry reset requires rtabmap_msgs. Install '
                           'ros-humble-rtabmap-msgs or set MAKO_VO_PREFIX to the bundled runtime prefix.')
    root = prefix.parents[2]
    paths = {
        'AMENT_PREFIX_PATH': [prefix],
        'PYTHONPATH': [prefix / 'local/lib/python3.10/dist-packages',
                       prefix / 'lib/python3.10/site-packages'],
        'LD_LIBRARY_PATH': [prefix / 'lib', prefix / 'lib/x86_64-linux-gnu',
                            root / 'usr/lib/x86_64-linux-gnu', root / 'usr/lib'],
    }
    return {key: ':'.join(map(str, values)) + ':' + os.environ.get(key, '')
            for key, values in paths.items()}


def launch_setup(context):
    vision = LaunchConfiguration('odometry_source').perform(context) == 'vision'
    publish_odom_tf = LaunchConfiguration('publish_odom_tf').perform(context) == 'true'
    return [
        # Feed the selected body-frame odometry to ArduPilot through MAVROS. The
        # MAVROS ROS-to-FCU endpoint is /mavros/odometry/out; EKF3 uses this
        # ExternalNav stream instead of the invalid air-pressure value produced
        # by the non-hydrostatic Gazebo pressure sensor.
        Node(
            package='mako_control',
            executable='gz_odom_to_mavros.py',
            name='gz_odom_to_mavros',
            additional_env=odometry_runtime_environment() if vision else {},
            parameters=[{'use_sim_time': True,
                         'source_topic': '/zed2i/vo/odometry' if vision else '/odometry/gz',
                         'require_covariance': vision, 'reset_on_clock_jump': vision,
                         'max_linear_speed': 2.0 if vision else 0.0,
                         'max_angular_speed': 3.0 if vision else 0.0,
                         'publish_tf': vision and publish_odom_tf}],
            output='screen',
        ),

        # MAVROS ODOMETRY requires a NED companion for the message's parent frame.
        Node(package='tf2_ros', executable='static_transform_publisher',
             name='tf_odom_ned',
             arguments=['--frame-id', 'odom', '--child-frame-id', 'odom_ned',
                        '--roll', '3.141592653589793', '--pitch', '0', '--yaw', '1.570796326794897'],
             parameters=[{'use_sim_time': True}], output='screen'),

        # The transect controller is idle until explicitly enabled through
        # /fly_transect/enable. Arming remains a manual operator action.
        Node(
            package='mako_control',
            executable='fly_transect_mission.py',
            name='fly_transect_mission',
            condition=IfCondition(LaunchConfiguration('transect_mission')),
            parameters=[{'use_sim_time': True,
                         'world': LaunchConfiguration('world').perform(context)}],
            output='screen',
        ),

        # MAVROS is started separately because its FCU URL is deployment
        # specific. Once it exposes the parameter service, configure EKF3 to
        # use the ExternalNav stream and disable unsuitable simulated-sensor
        # behaviour. The helper exits harmlessly if MAVROS has not appeared
        # within the timeout.
        TimerAction(
            condition=IfCondition(LaunchConfiguration('configure_ardusub')),
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'mako_control', 'fix_ardusub_params.py',
                        '--non-interactive', '--wait-for-mavros', '90',
                    ],
                    output='screen',
                ),
            ],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('odometry_source', default_value='ground_truth',
                              choices=['ground_truth', 'vision'],
                              description='ground_truth relays /odometry/gz; vision relays /zed2i/vo/odometry.'),
        DeclareLaunchArgument('publish_odom_tf', default_value='true', choices=['true', 'false'],
                              description='In vision mode, let the relay publish odom -> base_link.'),
        DeclareLaunchArgument('configure_ardusub', default_value='true', choices=['true', 'false'],
                              description='Apply ArduSub parameters through MAVROS; disable when SITL loaded them at startup.'),
        DeclareLaunchArgument('transect_mission', default_value='true', choices=['true', 'false'],
                              description='Start the idle fly-transect mission node.'),
        DeclareLaunchArgument('world', default_value='pool.world',
                              description='World name passed to the fly-transect mission.'),
        OpaqueFunction(function=launch_setup),
    ])
