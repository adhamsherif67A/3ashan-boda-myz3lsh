"""ZED RGB-D visual odometry (RTAB-Map rgbd_odometry) -> /zed2i/vo/odometry.

Inputs are the synchronized ZED left RGB-D topics; no ground-truth or bottom-camera
input is used. The same topics come from the Gazebo bridge in simulation or from the
ZED wrapper on the real ROV (remap them there).
"""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import OpaqueFunction, SetEnvironmentVariable
from launch_ros.actions import Node
from mako_vision.runtime import configure_runtime


def setup(context):
    share=Path(get_package_share_directory('mako_vision'))
    environment=[SetEnvironmentVariable(key,value)
                 for key,value in configure_runtime('rtabmap_odom').items()]
    return environment+[
        Node(package='rtabmap_odom',executable='rgbd_odometry',name='zed_rgbd_odometry',
             parameters=[str(share/'config/zed_vo.yaml')],
             additional_env={'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'1'},
             remappings=[('imu','/zed2i/zed_node/imu/data'),
                         ('rgb/image','/zed2i/rgbd/left/image_rect_color'),
                         ('depth/image','/zed2i/rgbd/left/depth/image_raw'),
                         ('rgb/camera_info','/zed2i/rgbd/left/camera_info'),
                         ('odom','/zed2i/vo/odometry'),('odom_info','/zed2i/vo/odom_info')],output='screen'),
    ]


def generate_launch_description():
    return LaunchDescription([OpaqueFunction(function=setup)])
