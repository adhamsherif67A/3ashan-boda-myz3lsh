import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import xacro
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnShutdown
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def prepare_world(world_path, robot_description, output_directory):
    """Include Mako in Gazebo's initial state so world reset retains it."""
    output_directory = Path(output_directory)
    urdf_path = output_directory / 'mako.urdf'
    urdf_path.write_text(robot_description)
    converted = subprocess.run(
        ['gz', 'sdf', '-p', str(urdf_path)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    model = ET.fromstring(converted.stdout).find('model')
    if model is None:
        raise RuntimeError('URDF conversion produced no Gazebo model')
    model.set('name', 'mako')
    pose = model.find('pose')
    if pose is None:
        pose = ET.SubElement(model, 'pose')
    pose.text = '0 0 -1 0 0 0'
    world = ET.parse(world_path)
    world.find('world').append(model)
    generated_world = output_directory / f'{Path(world_path).stem}_with_mako.sdf'
    world.write(generated_world, encoding='utf-8', xml_declaration=True)
    return generated_world


def launch_setup(context):
    package_name = 'robot_description'
    package_share = Path(get_package_share_directory(package_name))

    # Path to the parent share directory so Gazebo finds 'model://robot_description'
    pkg_share_parent = str(package_share.parent)

    source_world = package_share / 'worlds' / LaunchConfiguration('world').perform(context)
    world_name = ET.parse(source_world).find('world').get('name')
    vision = LaunchConfiguration('odometry_source').perform(context) == 'vision'
    slam = LaunchConfiguration('slam').perform(context) == 'true'
    if slam and not vision:
        raise RuntimeError('SLAM mapping requires odometry_source:=vision')
    publish_map_tf = (
        LaunchConfiguration('publish_map_tf').perform(context) == 'true' and not slam
    )
    urdf_path = package_share / 'urdf' / 'robot_description.urdf'
    
    # ==========================================================
    # COMPILE XACRO: This dynamically injects your separate 
    # ardupilot.xacro file into the URDF before launching.
    # ==========================================================
    profile = LaunchConfiguration('performance_profile').perform(context)
    profile_settings = {
        'maximum_fps': ('640', '360', '10', '15'),
        'balanced': ('960', '540', '12', '20'),
        'vision_quality': ('1280', '720', '15', '24'),
        'full_sensors': ('1280', '720', '15', '30'),
    }
    if profile not in profile_settings:
        raise ValueError(f'Unknown performance_profile: {profile}')
    profile_values = profile_settings[profile]
    camera_settings = {
        'camera_width': LaunchConfiguration('camera_width').perform(context),
        'camera_height': LaunchConfiguration('camera_height').perform(context),
        'camera_fps': LaunchConfiguration('camera_fps').perform(context),
        'pilot_fps': LaunchConfiguration('pilot_fps').perform(context),
        'sitl_port_in': LaunchConfiguration('sitl_port_in').perform(context),
        'sitl_port_out': LaunchConfiguration('sitl_port_out').perform(context),
    }
    for name, value in zip(('camera_width', 'camera_height', 'camera_fps', 'pilot_fps'), profile_values):
        if camera_settings[name] == 'profile':
            camera_settings[name] = value
    if any(int(camera_settings[name]) <= 0 for name in ('camera_width', 'camera_height')):
        raise ValueError('Camera dimensions must be positive integers')
    if float(camera_settings['camera_fps']) <= 0:
        raise ValueError('camera_fps must be positive')
    if float(camera_settings['pilot_fps']) <= 0:
        raise ValueError('pilot_fps must be positive')
    gpu_actions = gpu_environment(LaunchConfiguration('render_gpu').perform(context))
    if gpu_actions and LaunchConfiguration('headless').perform(context) == 'true':
        nvidia_egl = Path('/usr/share/glvnd/egl_vendor.d/10_nvidia.json')
        if nvidia_egl.exists():
            gpu_actions.append(SetEnvironmentVariable('__EGL_VENDOR_LIBRARY_FILENAMES', str(nvidia_egl)))
    doc = xacro.process_file(str(urdf_path), mappings=camera_settings)
    robot_description = doc.toxml()

    # Runtime-spawned entities disappear when Gazebo restores its initial ECM.
    # Generate the complete starting world using the same configured URDF as RSP.
    world_directory = tempfile.TemporaryDirectory(prefix='mako-gazebo-')
    try:
        world_path = prepare_world(
            source_world, robot_description,
            world_directory.name,
        )
    except Exception:
        world_directory.cleanup()
        raise
    ros_gz_sim_share = Path(get_package_share_directory('ros_gz_sim'))
    slam_actions = []
    if slam:
        rtabmap_share = Path(get_package_share_directory('rtabmap_launch'))
        database_path = LaunchConfiguration('slam_database_path').perform(context)
        slam_actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(rtabmap_share / 'launch' / 'rtabmap.launch.py')),
            launch_arguments={
                'use_sim_time': 'true',
                'visual_odometry': 'false',
                'rgb_topic': '/zed2i/rgbd/left/image_rect_color',
                'depth_topic': '/zed2i/rgbd/left/depth/image_raw',
                'camera_info_topic': '/zed2i/rgbd/left/camera_info',
                'odom_topic': '/zed2i/vo/odometry',
                'frame_id': 'base_link',
                'map_frame_id': 'map',
                'publish_tf_map': 'true',
                'approx_sync': 'true',
                'approx_sync_max_interval': '0.025',
                'qos': '1',
                'topic_queue_size': '3',
                'sync_queue_size': '8',
                'wait_for_transform': '0.2',
                'args': '--ros-args -p RGBD/LinearUpdate:=0.03 -p RGBD/AngularUpdate:=0.03 -p RGBD/NeighborLinkRefining:=true -p Reg/Strategy:=1 -p Reg/Force3DoF:=false -p Grid/RangeMax:=8.0 -p Odom/ResetCountdown:=3',
                'database_path': database_path,
                'rtabmap_viz': LaunchConfiguration('slam_viz').perform(context),
                'rviz': 'false',
            }.items(),
        ))

    # Environment variable for Gazebo Harmonic resources
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            pkg_share_parent,
            ':' + os.environ.get('GZ_SIM_RESOURCE_PATH', '')
        ]
    )

    return [
        RegisterEventHandler(OnShutdown(
            on_shutdown=lambda event, context: world_directory.cleanup(),
        )),
        gz_resource_path,
        SetEnvironmentVariable(
            name='GZ_SIM_SYSTEM_PLUGIN_PATH',
            value=str(package_share.parent.parent / 'lib') + ':' +
                  os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '') + ':' +
                  str(Path(os.environ.get('MAKO_ARDUPILOT_GAZEBO', str(Path.home() / 'ardupilot' / 'ardupilot_gazebo'))) / 'build'),
        ),

        *gpu_actions,
        # Start Gazebo Harmonic
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(ros_gz_sim_share / 'launch' / 'gz_sim.launch.py')),
            launch_arguments={'gz_args': ('-r -s --headless-rendering ' if LaunchConfiguration('headless').perform(context) == 'true' else '-r ') + str(world_path)}.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package_share / 'launch' / 'zed_vo.launch.py')),
            condition=IfCondition('true' if vision else 'false'),
        ),
        *slam_actions,

        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': True,
                'ignore_timestamp': False,
            }],
        ),

        # ==========================================================
        # ROS-Gazebo Bridge
        # ==========================================================
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/mako/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
                # Keep an Odometry message available for localization / Nav2
                # integration.  Its child frame is base_link.
                '/model/mako/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                
                # Bridge Mako's joint states using your exact SDF world name
                f'/world/{world_name}/model/mako/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
                
                # Thrusters (Updated to match URDF's 't1_joint' naming)
                '/model/mako/joint/t1_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
                '/model/mako/joint/t2_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
                '/model/mako/joint/t3_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
                '/model/mako/joint/t4_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
                '/model/mako/joint/t5_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
                '/model/mako/joint/t6_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',

            ],
            remappings=[
                # Remap to standard ROS 2 topics for RViz
                ('/model/mako/odometry', '/odometry/gz'),
                ('/mako/imu', '/imu/data'),
                (f'/world/{world_name}/model/mako/joint_state', '/joint_states'),
                
            ],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        # Publish the ROV's positive-down depth as a dedicated simulation topic.
        # This is ground-truth depth; it does not replace visual odometry or SLAM.
        Node(
            package='robot_description',
            executable='odom_to_depth.py',
            name='odom_to_depth',
            parameters=[{'use_sim_time': True,
                         'source_topic': '/odometry/gz',
                         'depth_topic': '/rov/depth',
                         'surface_z': 0.0}],
            output='screen',
        ),

        # The transect controller is idle until explicitly enabled from the UI.
        # Arming remains a manual operator action.
        Node(
            package='robot_description',
            executable='fly_transect_mission.py',
            name='fly_transect_mission',
            parameters=[{'use_sim_time': True,
                         'world': LaunchConfiguration('world').perform(context)}],
            output='screen',
        ),

        # Feed the selected body-frame odometry to ArduPilot through MAVROS. The
        # MAVROS ROS-to-FCU endpoint is /mavros/odometry/out; EKF3
        # uses this ExternalNav stream instead of the invalid air-pressure
        # value produced by the non-hydrostatic Gazebo pressure sensor.
        Node(
            package='robot_description',
            executable='gz_odom_to_mavros.py',
            name='gz_odom_to_mavros',
            parameters=[{'use_sim_time': True,
                         'source_topic': '/zed2i/vo/odometry' if vision else '/odometry/gz',
                         'require_covariance': vision, 'reset_on_clock_jump': vision,
                         'max_linear_speed': 2.0 if vision else 0.0,
                         'max_angular_speed': 3.0 if vision else 0.0,
                         'publish_tf': vision and LaunchConfiguration('publish_odom_tf').perform(context) == 'true'}],
            output='screen',
        ),

        # MAVROS is started separately because its FCU URL is deployment
        # specific.  Once it exposes the parameter service, configure EKF3 to
        # use the Gazebo odometry ExternalNav stream and disable unsuitable
        # simulated-sensor behaviour.  The helper exits harmlessly if MAVROS
        # has not appeared within the timeout.
        TimerAction(
            condition=IfCondition(LaunchConfiguration("configure_ardusub")),
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', package_name, 'fix_ardusub_params.py',
                        '--non-interactive', '--wait-for-mavros', '90',
                    ],
                    output='screen',
                ),
            ],
        ),

        # MAVROS ODOMETRY requires a NED companion for the message's parent frame.
        Node(package='tf2_ros', executable='static_transform_publisher',
             name='tf_odom_ned',
             arguments=['--frame-id','odom','--child-frame-id','odom_ned',
                        '--roll','3.141592653589793','--pitch','0','--yaw','1.570796326794897'],
             parameters=[{'use_sim_time':True}], output='screen'),

        # Ground-truth mode aligns map with odom. SLAM mode leaves map -> odom
        # to RTAB-Map and suppresses this placeholder publisher.
        Node(
            package='tf2_ros', executable='static_transform_publisher',
            name='tf_sim_map_odom',
            condition=IfCondition('true' if publish_map_tf else 'false'),
            arguments=['--frame-id', 'map', '--child-frame-id', 'odom'],
            parameters=[{'use_sim_time': True}], output='screen',
        ),

        # Only one node may own odom -> base_link.
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ground_truth_tf_bridge',
            condition=IfCondition('false' if vision else LaunchConfiguration('publish_odom_tf')),
            arguments=['/model/mako/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'],
            remappings=[('/model/mako/tf', '/tf')],
            parameters=[{'use_sim_time': True}],
            output='screen',
        ),

        Node(
            package='robot_description', executable='cloud_frame_relay.py',
            name='cloud_frame_relay', parameters=[{'use_sim_time': True}],
            output='screen',
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='zed2i_bridge',
            parameters=[{'config_file': str(package_share / 'config' / 'zed2i_bridge.yaml'),
                         'use_sim_time': True}],
            output='screen',
        ),

        # Visual odometry and SLAM need color, depth, and calibration from the
        # same RGB-D sensor. Keep this matched triplet active only in vision mode.
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='zed2i_rgbd_bridge',
            condition=IfCondition('true' if vision else 'false'),
            parameters=[{'config_file': str(package_share / 'config' / 'zed2i_rgbd_bridge.yaml'),
                         'use_sim_time': True}],
            output='screen',
        ),
    ]


def gpu_environment(mode):
    """Select PRIME offload without changing system-wide graphics settings."""
    if mode == 'default':
        return []
    try:
        available = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                   capture_output=True, text=True, timeout=3).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        available = False
    if not available:
        if mode == 'nvidia':
            raise RuntimeError('NVIDIA rendering requested but nvidia-smi cannot access a working GPU')
        return []
    return [SetEnvironmentVariable(key, value) for key, value in {
        '__NV_PRIME_RENDER_OFFLOAD': '1',
        '__GLX_VENDOR_LIBRARY_NAME': 'nvidia',
        '__VK_LAYER_NV_optimus': 'NVIDIA_only',
    }.items()]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('configure_ardusub', default_value='true', choices=['true', 'false'],
                              description='Apply parameters through MAVROS; disable when SITL loaded them at startup.'),
        DeclareLaunchArgument('sitl_port_in', default_value='9002', description='Gazebo ArduPilot JSON servo input port'),
        DeclareLaunchArgument('sitl_port_out', default_value='9003', description='ArduPilot JSON state port'),
        DeclareLaunchArgument('headless', default_value='false', choices=['true', 'false'], description='Run the Gazebo server and rendered sensors without its GUI'),
        DeclareLaunchArgument('world', default_value='pool.world', choices=['pool.world', 'pool.sdf', 'ocean.world'], description='Select team pool tasks or ocean maneuvering course'),
        DeclareLaunchArgument('odometry_source', default_value='ground_truth',
                              choices=['ground_truth', 'vision'],
                              description='Select the sole TF and MAVROS odometry source.'),
        DeclareLaunchArgument('slam', default_value='false', choices=['true', 'false'],
                              description='Enable RTAB-Map visual SLAM; requires ZED visual odometry.'),
        DeclareLaunchArgument('slam_database_path',
                              default_value=str(Path.home() / '.ros' / 'mako_slam.db'),
                              description='RTAB-Map database path. Existing databases are reused, not deleted.'),
        DeclareLaunchArgument('slam_viz', default_value='true', choices=['true', 'false'],
                              description='Open the RTAB-Map viewer when SLAM is enabled.'),
        DeclareLaunchArgument(
            'publish_odom_tf', default_value='true', choices=['true', 'false'],
            description='Let Gazebo own odom -> base_link. Disable for an external estimator.'),
        DeclareLaunchArgument(
            'publish_map_tf', default_value='true', choices=['true', 'false'],
            description='Align map with odom for ground-truth simulation. Disable when SLAM owns this edge.'),
        DeclareLaunchArgument('camera_width', default_value='profile', description='Native RGB/depth width; profile or explicit integer'),
        DeclareLaunchArgument('camera_height', default_value='profile', description='Native RGB/depth height; profile or explicit integer'),
        DeclareLaunchArgument('camera_fps', default_value='profile', description='RGB-D/depth and bottom camera rate; profile or explicit number'),
        DeclareLaunchArgument('pilot_fps', default_value='profile', description='Pilot RGB rate; profile or explicit number'),
        DeclareLaunchArgument(
            'performance_profile', default_value='balanced',
            choices=['maximum_fps', 'balanced', 'vision_quality', 'full_sensors'],
            description='Camera/rendering profile; explicit camera_* arguments override profile values'),
        DeclareLaunchArgument('render_gpu', default_value='auto', choices=['auto', 'nvidia', 'default'], description='Use NVIDIA PRIME offload when available'),
        OpaqueFunction(function=launch_setup),
    ])
