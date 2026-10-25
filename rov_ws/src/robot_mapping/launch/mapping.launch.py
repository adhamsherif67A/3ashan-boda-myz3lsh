import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    # 1. Gazebo Camera Bridges (بيربط الكاميرا اللي قايمة في السيميوليشن مع ROS 2)
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'
        ],
        output='screen'
    )

    # 2. RTAB-Map SLAM Node
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
            'qos_image': 1,
            'qos_depth': 1,
            'RGBD/NeighborLinkRefining': 'true',
            'RGBD/ProximityBySpace': 'true',
            'Reg/Strategy': '0',               # 0 = Visual SLAM
            'Reg/Force3DoF': 'false',          # 6DOF للحركة تحت المية
            'Mem/Reconstruct3D': 'true',
            'RTABmap/DetectionRate': '1.0',
        }],
        remappings=[
            ('rgb/image', '/camera/image_raw'),
            ('depth/image', '/camera/depth/image_raw'),
            ('rgb/camera_info', '/camera/camera_info'),
            ('odom', '/mavros/local_position/odom')  # بياخد الـ Odometry من MAVROS المفتوح في التيرمينال التاني
        ],
        arguments=['-d']  # يمسح الـ DB القديمة يبدأ خريطة جديدة
    )

    # 3. RViz2 العرض
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gz_bridge,
        rtabmap_node,
        rviz_node
    ])
