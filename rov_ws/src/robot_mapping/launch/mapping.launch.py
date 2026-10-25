import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    pkg_share = get_package_share_directory('robot_mapping')
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'mapping_config.rviz')

    # 1. Gazebo Bridges (توصيل جميع الكاميرات والعمق والـ Odom)
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/zed2i/sim/left/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/zed2i/sim/left/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/zed2i/sim/left/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/bottom_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image'
        ],
        output='screen'
    )

    # 2. RTAB-Map SLAM Node (مظبوط لإنشاء وتوفير الـ Map & MapGraph)
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'subscribe_depth': True,
            'frame_id': 'base_link',
            'map_frame_id': 'map',
            'odom_frame_id': 'odom',
            'approx_sync': True,
            'queue_size': 30,
            'qos_image': 1,
            'qos_depth': 1,
            # تفعيل إنشاء الـ Grid Map والـ Graph لـ RViz2
            'Grid/FromDepth': 'true',
            'RGBD/CreateOccupancyGrid': 'true',
            'RGBD/NeighborLinkRefining': 'true',
            'RGBD/ProximityBySpace': 'true',
            'Reg/Strategy': '0',
            'Reg/Force3DoF': 'false',
            'Mem/Reconstruct3D': 'true',
            'RTABmap/DetectionRate': '2.0',
        }],
        remappings=[
            ('rgb/image', '/zed2i/sim/left/image'),
            ('depth/image', '/zed2i/sim/left/depth_image'),
            ('rgb/camera_info', '/zed2i/sim/left/camera_info'),
            ('odom', '/odometry/gz')
        ],
        arguments=['-d']
    )

    # 3. RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gz_bridge,
        rtabmap_node,
        rviz_node
    ])
