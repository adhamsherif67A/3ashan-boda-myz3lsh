import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    rviz_config_path = os.path.join(
        get_package_share_directory('RTAB'),
        'rviz',
        'RTABmap.rviz',
    )

    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        arguments=['-d'],
        parameters=[{
            'use_sim_time': True,
            'frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'map_frame_id': 'map',
            'subscribe_depth': True,
            'approx_sync': True,
            'queue_size': 100,
            'qos_image': 1,
            'qos_camera_info': 1,
            'qos_odom': 1,
            'Reg/Strategy': '1',
            'Reg/Force3DoF': 'false',
            'Vis/MinInliers': '15',
            'RGBD/OptimizeMaxError': '0.1',
            'RGBD/OptimizeFromLastNode': 'true',
            'Grid/CellSize': '0.05',
            'Grid/DepthDecimation': '2',
            'Grid/RangeMax': '3.5',
            'Grid/RangeMin': '0.4',
            'Grid/NoiseFilteringRadius': '0.1',
            'Grid/NoiseFilteringMinNeighbors': '5',
            'Rtabmap/DetectionRate': '1.0',
            'RGBD/LinearUpdate': '0.15',
            'RGBD/AngularUpdate': '0.1',
            'Grid/FromDepth': 'true',
            'RGBD/CreateOccupancyGrid': 'true',
            'RGBD/NeighborLinkRefining': 'true',
            'Mem/Reconstruct3D': 'true',
        }],
        remappings=[
            ('rgb/image', '/zed2i/zed_node/rgb/image_rect_color'),
            ('depth/image', '/zed2i/zed_node/depth/depth_registered'),
            ('rgb/camera_info', '/zed2i/zed_node/rgb/camera_info'),
            ('odom', '/odometry/gz'),
        ],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        rtabmap_node,
        rviz_node,
    ])
