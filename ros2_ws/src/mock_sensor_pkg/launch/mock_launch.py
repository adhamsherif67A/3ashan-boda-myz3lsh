from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. تشغيل كود المُذيع بتاعنا
        Node(
            package='mock_sensor_pkg',
            executable='broadcaster_node',
            name='mock_broadcaster'
        ),
        # 2. تشغيل شاشة الرادار (RViz2)
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2'
        )
    ])
