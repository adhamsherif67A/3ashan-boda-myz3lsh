"""Complete Mako simulation: world + robot, vision and vehicle control.

Composes the independent packages:
  robot_description  gazebo.launch.py      Gazebo world, ROV model, sensors, ROS bridges
  mako_vision        visual_odometry/slam  ZED visual odometry and RTAB-Map SLAM (optional)
  mako_control       control.launch.py     ExternalNav relay, ArduSub parameters, missions
  mako_control       pilot.launch.py       gamepad + realjoy_node (optional, pilot:=true)

ArduSub SITL and MAVROS are separate processes (see commands.txt); Operation MX and
docker/simulation.py start them for you.
"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def include(package, launch_file, arguments):
    path = Path(get_package_share_directory(package)) / 'launch' / launch_file
    return GroupAction([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(path)), launch_arguments=arguments.items())])


def launch_setup(context):
    value = lambda name: LaunchConfiguration(name).perform(context)
    vision = value('odometry_source') == 'vision'
    slam = value('slam') == 'true'
    if slam and not vision:
        raise RuntimeError('SLAM mapping requires odometry_source:=vision')
    publish_odom_tf = value('publish_odom_tf') == 'true'
    publish_map_tf = value('publish_map_tf') == 'true' and not slam
    flag = lambda condition: 'true' if condition else 'false'

    actions = [include('robot_description', 'gazebo.launch.py', {
        'world': value('world'),
        'headless': value('headless'),
        'sitl_port_in': value('sitl_port_in'),
        'sitl_port_out': value('sitl_port_out'),
        'camera_width': value('camera_width'),
        'camera_height': value('camera_height'),
        'camera_fps': value('camera_fps'),
        'pilot_fps': value('pilot_fps'),
        'performance_profile': value('performance_profile'),
        'render_gpu': value('render_gpu'),
        # Gazebo ground truth owns odom -> base_link unless visual odometry does.
        'publish_odom_tf': flag(publish_odom_tf and not vision),
        'publish_map_tf': flag(publish_map_tf),
        'rgbd_bridge': flag(vision),
    })]
    if vision:
        actions.append(include('mako_vision', 'visual_odometry.launch.py', {}))
    if slam:
        actions.append(include('mako_vision', 'slam.launch.py', {
            'slam_database_path': value('slam_database_path'),
            'slam_viz': value('slam_viz'),
            'use_sim_time': 'true',
        }))
    actions.append(include('mako_control', 'control.launch.py', {
        'odometry_source': value('odometry_source'),
        'publish_odom_tf': flag(publish_odom_tf),
        'configure_ardusub': value('configure_ardusub'),
        'transect_mission': value('transect_mission'),
        'world': value('world'),
    }))
    if value('pilot') == 'true':
        actions.append(include('mako_control', 'pilot.launch.py', {
            'joystick': value('joystick'), 'use_sim_time': 'true'}))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='pool.world', choices=['pool.world', 'pool.sdf', 'ocean.world'],
                              description='Team pool tasks (pool.world), legacy pool (pool.sdf) or ocean course (ocean.world).'),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false'],
                              description='Run the Gazebo server and rendered sensors without the Gazebo GUI.'),
        DeclareLaunchArgument('odometry_source', default_value='ground_truth', choices=['ground_truth', 'vision'],
                              description='Odometry sent to ArduSub and owning odom -> base_link: Gazebo ground truth or ZED visual odometry.'),
        DeclareLaunchArgument('slam', default_value='false', choices=['true', 'false'],
                              description='Enable RTAB-Map visual SLAM; requires odometry_source:=vision.'),
        DeclareLaunchArgument('slam_database_path', default_value=str(Path.home() / '.ros' / 'mako_slam.db'),
                              description='RTAB-Map database path. Existing databases are reused, not deleted.'),
        DeclareLaunchArgument('slam_viz', default_value='true', choices=['true', 'false'],
                              description='Open the RTAB-Map viewer when SLAM is enabled.'),
        DeclareLaunchArgument('publish_odom_tf', default_value='true', choices=['true', 'false'],
                              description='Publish odom -> base_link (from ground truth or the VO relay). Disable for an external estimator.'),
        DeclareLaunchArgument('publish_map_tf', default_value='true', choices=['true', 'false'],
                              description='Publish a static map -> odom when SLAM is off.'),
        DeclareLaunchArgument('configure_ardusub', default_value='true', choices=['true', 'false'],
                              description='Apply ArduSub parameters through MAVROS; disable when SITL loaded them at startup.'),
        DeclareLaunchArgument('transect_mission', default_value='true', choices=['true', 'false'],
                              description='Start the idle fly-transect mission node (enable it with /fly_transect/enable).'),
        DeclareLaunchArgument('pilot', default_value='false', choices=['true', 'false'],
                              description='Also start realjoy_node (and the gamepad driver) for piloting without Operation MX.'),
        DeclareLaunchArgument('joystick', default_value='true', choices=['true', 'false'],
                              description='With pilot:=true, start the joy game_controller_node gamepad driver.'),
        DeclareLaunchArgument('sitl_port_in', default_value='9002', description='Gazebo ArduPilot JSON servo input port.'),
        DeclareLaunchArgument('sitl_port_out', default_value='9003', description='ArduPilot JSON state port.'),
        DeclareLaunchArgument('performance_profile', default_value='balanced',
                              choices=['maximum_fps', 'balanced', 'vision_quality', 'full_sensors'],
                              description='Camera/rendering profile; explicit camera_* arguments override it.'),
        DeclareLaunchArgument('camera_width', default_value='profile', description='Native RGB/depth width; profile or an integer.'),
        DeclareLaunchArgument('camera_height', default_value='profile', description='Native RGB/depth height; profile or an integer.'),
        DeclareLaunchArgument('camera_fps', default_value='profile', description='RGB-D/depth and bottom camera rate; profile or a number.'),
        DeclareLaunchArgument('pilot_fps', default_value='profile', description='Pilot RGB rate; profile or a number.'),
        DeclareLaunchArgument('render_gpu', default_value='auto', choices=['auto', 'nvidia', 'default'],
                              description='auto/nvidia: use NVIDIA PRIME offload when available; default: system GPU.'),
        OpaqueFunction(function=launch_setup),
    ])
