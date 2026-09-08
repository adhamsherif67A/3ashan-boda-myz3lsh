# 1. نسخ سكريبت المحاكاة جوه مجلد الحزمة
PACKAGE_DIR=$(ros2 pkg prefix --share zed_robot_integration)
SRC_LAUNCH_DIR=$(dirname $(find ~/ros2_ws/src/zed-ros2-examples -name "view_mono_zed.launch.py" | head -n 1))
mkdir -p "$SRC_LAUNCH_DIR/scripts"
cp ~/ros2_ws/zed_sim_feed.py "$SRC_LAUNCH_DIR/scripts/zed_sim_feed.py"
chmod +x "$SRC_LAUNCH_DIR/scripts/zed_sim_feed.py"

# 2. تعديل view_mono_zed.launch.py ليقوم بتشغيل نود المحاكاة مع RViz والروبوت
LAUNCH_FILE="$SRC_LAUNCH_DIR/view_mono_zed.launch.py"
cat << 'EOF' > "$LAUNCH_FILE"
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('zed_robot_integration')
    default_rviz_config = os.path.join(pkg_share, 'rviz2', 'view_config.rviz')
    default_xacro = os.path.join(pkg_share, 'urdf', 'zed_robot_mono.urdf.xacro')

    camera_name = LaunchConfiguration('camera_name')
    camera_model = LaunchConfiguration('camera_model')
    use_zed_localization = LaunchConfiguration('use_zed_localization')

    declare_camera_name = DeclareLaunchArgument('camera_name', default_value='zed')
    declare_camera_model = DeclareLaunchArgument('camera_model', default_value='zed2i')
    declare_use_zed_localization = DeclareLaunchArgument('use_zed_localization', default_value='true')

    robot_description = Command([
        'xacro ', default_xacro,
        ' camera_name:=', camera_name,
        ' camera_model:=', camera_model,
        ' use_zed_localization:=', use_zed_localization
    ])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='scoutm_robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='scoutm_joint_state_publisher',
        output='screen'
    )

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', default_rviz_config]
    )

    # تشغيل سكريبت محاكاة الكاميرا والـ Point Cloud تلقائياً
    sim_cam_node = ExecuteProcess(
        cmd=['python3', os.path.expanduser('~/ros2_ws/zed_sim_feed.py')],
        output='screen'
    )

    return LaunchDescription([
        declare_camera_name,
        declare_camera_model,
        declare_use_zed_localization,
        robot_state_publisher,
        joint_state_publisher,
        sim_cam_node,
        rviz2_node
    ])
EOF

# 3. إعادة بناء وتثبيت الحزمة
cd ~/ros2_ws
colcon build --symlink-install --packages-select zed_robot_integration
source install/setup.bash
