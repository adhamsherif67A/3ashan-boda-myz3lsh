"""Team RGB-D mapper, using the running simulation's validated odometry."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from robot_mapping.runtime import configure_runtime


def setup(context):
    runtime = configure_runtime('rtabmap_slam')
    actions = [SetEnvironmentVariable(key, value) for key, value in runtime.items()]
    share = Path(get_package_share_directory('robot_mapping'))
    params = [str(share / 'config/rtabmap.yaml'), {
        'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
        'database_path': LaunchConfiguration('database_path'),
    }]
    topics = [('rgb/image', LaunchConfiguration('rgb_topic')),
              ('depth/image', LaunchConfiguration('depth_topic')),
              ('rgb/camera_info', LaunchConfiguration('camera_info_topic')),
              ('odom', LaunchConfiguration('odom_topic'))]
    actions.append(Node(package='rtabmap_slam', executable='rtabmap',
                        name='rtabmap', namespace='rtabmap',
                        parameters=params, remappings=topics,
                        additional_env={'OMP_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '1'},
                        output='screen'))
    actions.append(Node(package='rtabmap_viz', executable='rtabmap_viz',
                        name='rtabmap_viz', namespace='rtabmap',
                        parameters=params, remappings=topics,
                        condition=IfCondition(LaunchConfiguration('slam_viz')),
                        output='screen'))
    actions.append(Node(package='rviz2', executable='rviz2', name='mapping_rviz',
                        arguments=['-d', str(share/'rviz/pool_mapping.rviz')],
                        parameters=[{'use_sim_time': ParameterValue(
                            LaunchConfiguration('use_sim_time'), value_type=bool)}],
                        condition=IfCondition(LaunchConfiguration('rviz')), output='screen'))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('database_path',
                              default_value=str(Path.home()/'.ros/mako_mapping.db')),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('slam_viz', default_value='false'),
        DeclareLaunchArgument('rgb_topic', default_value='/zed2i/rgbd/left/image_rect_color'),
        DeclareLaunchArgument('depth_topic', default_value='/zed2i/rgbd/left/depth/image_raw'),
        DeclareLaunchArgument('camera_info_topic', default_value='/zed2i/rgbd/left/camera_info'),
        DeclareLaunchArgument('odom_topic', default_value='/mavros/odometry/out'),
        OpaqueFunction(function=setup),
    ])
