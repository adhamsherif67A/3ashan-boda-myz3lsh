"""Nav2 servers using existing map/TF; output isolated from vehicle control."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from launch_ros.parameter_descriptions import ParameterValue
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    own = Path(get_package_share_directory('mako_navigation'))
    params = ParameterFile(RewrittenYaml(
        source_file=LaunchConfiguration('params_file'), root_key='',
        param_rewrites={'map_topic': LaunchConfiguration('map_topic'),
                        'use_sim_time': LaunchConfiguration('use_sim_time')},
        convert_types=True), allow_substs=True)
    servers = [
        ('nav2_controller', 'controller_server'),
        ('nav2_smoother', 'smoother_server'),
        ('nav2_planner', 'planner_server'),
        ('nav2_behaviors', 'behavior_server'),
        ('nav2_bt_navigator', 'bt_navigator'),
        ('nav2_waypoint_follower', 'waypoint_follower'),
        ('nav2_velocity_smoother', 'velocity_smoother'),
    ]
    nodes = []
    for package, executable in servers:
        remaps = []
        if executable in ('controller_server', 'behavior_server'):
            remaps = [('cmd_vel', '/mako/navigation/cmd_vel_raw')]
        elif executable == 'velocity_smoother':
            remaps = [('cmd_vel', '/mako/navigation/cmd_vel_raw'),
                      ('cmd_vel_smoothed', '/mako/navigation/cmd_vel')]
        nodes.append(Node(package=package, executable=executable, name=executable,
                          parameters=[params], remappings=remaps, output='screen'))
    nodes.append(Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen', parameters=[{
            'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
            'autostart': ParameterValue(LaunchConfiguration('autostart'), value_type=bool),
            'node_names': [name for _, name in servers],
        }]))
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('map_topic', default_value='/rtabmap/map'),
        DeclareLaunchArgument('params_file', default_value=str(own/'config/nav2.yaml')),
        *nodes,
    ])
