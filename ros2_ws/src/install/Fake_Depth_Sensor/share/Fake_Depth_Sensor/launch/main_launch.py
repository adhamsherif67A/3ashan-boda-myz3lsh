from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # تشغيل النود بتاعة السنسور (اللي فيها البابلشر والسيرفيس والأكشن)
        Node(
            package='Fake_Depth_Sensor',
            executable='sensor_pub',
            name='fake_depth_publisher',
            output='screen'
        ),
        # تشغيل النود بتاعة المراقبة (السبسكرايبر)
        Node(
            package='Fake_Depth_Sensor',
            executable='sensor_sub',
            name='fake_depth_subscriber',
            output='screen'
        )
    ])
