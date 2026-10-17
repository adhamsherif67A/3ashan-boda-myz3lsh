"""ZED RGB-D visual odometry; no ground-truth input or bottom-camera input."""
import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory, get_package_prefix, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import OpaqueFunction, SetEnvironmentVariable
from launch_ros.actions import Node


def setup(context):
    share=Path(get_package_share_directory('robot_description'))
    environment=[]
    try:get_package_prefix('rtabmap_odom')
    except PackageNotFoundError:
        candidates=[Path(os.environ.get('MAKO_VO_PREFIX','/nonexistent'))]
        candidates += [p/'.deps/rtabmap/root/opt/ros/humble' for p in share.resolve().parents]
        candidates += [p/'.deps/rtabmap/root/opt/ros/humble' for p in share.parents]
        prefix=next((p for p in candidates if (p/'lib/rtabmap_odom/rgbd_odometry').exists()),None)
        if prefix is None:
            raise RuntimeError('RTAB-Map odometry missing. Install ros-humble-rtabmap-odom or set MAKO_VO_PREFIX to the local prefix.')
        root=prefix.parents[2]
        paths={'AMENT_PREFIX_PATH':str(prefix),
               'LD_LIBRARY_PATH':':'.join(map(str,[prefix/'lib',prefix/'lib/x86_64-linux-gnu',root/'usr/lib/x86_64-linux-gnu',root/'usr/lib'])),
               'PYTHONPATH':str(prefix/'local/lib/python3.10/dist-packages')+':'+str(prefix/'lib/python3.10/site-packages')}
        for key,value in paths.items():
            os.environ[key]=value+':'+os.environ.get(key,'')
            environment.append(SetEnvironmentVariable(key,os.environ[key]))
    return environment+[
        Node(package='rtabmap_odom',executable='rgbd_odometry',name='zed_rgbd_odometry',
             parameters=[str(share/'config/zed_vo.yaml')],
             remappings=[('rgb/image','/zed2i/zed_node/left/image_rect_color'),
                         ('depth/image','/zed2i/zed_node/left/depth/image_raw'),
                         ('rgb/camera_info','/zed2i/zed_node/left/camera_info'),
                         ('odom','/zed2i/vo/odometry'),('odom_info','/zed2i/vo/odom_info')],output='screen'),
    ]


def generate_launch_description():
    return LaunchDescription([OpaqueFunction(function=setup)])
