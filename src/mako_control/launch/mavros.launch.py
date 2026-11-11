"""MAVROS for ArduSub with a selectable FCU connection.

Simulation (default): udp://127.0.0.1:14551@  (the second SITL output in commands.txt)
Real Pixhawk over USB: fcu_url:=/dev/ttyACM0:115200
Companion computer over UDP: fcu_url:=udp://0.0.0.0:14550@
"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    apm = Path(get_package_share_directory('mavros')) / 'launch' / 'apm.launch'
    return LaunchDescription([
        DeclareLaunchArgument('fcu_url', default_value='udp://127.0.0.1:14551@',
                              description='MAVLink connection to the autopilot.'),
        DeclareLaunchArgument('gcs_url', default_value='',
                              description='Optional ground-station relay, e.g. udp://@127.0.0.1:14560.'),
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(str(apm)),
            launch_arguments={'fcu_url': LaunchConfiguration('fcu_url'),
                              'gcs_url': LaunchConfiguration('gcs_url')}.items(),
        ),
    ])
