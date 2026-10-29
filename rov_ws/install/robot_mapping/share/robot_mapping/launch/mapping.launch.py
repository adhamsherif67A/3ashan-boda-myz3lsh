from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        arguments=['-d'],  # بيمسح الخريطة القديمة ويبدأ نضيف من الصفر
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

            # --- 1. حل مشكلة عوج الخريطة والطبقات المزدوجة (ICP Alignment) ---
            'Reg/Strategy': '1',                  # تحويل المطابقة لـ (Visual + ICP) لتطبيق الأسطح هندسياً
            'Reg/Force3DoF': 'false',             # حركة 3D كاملة للغواصة
            'Vis/MinInliers': '15',               # رفعت شرط التطابق لـ 15 نقطة لمنع الـ Loop Closure الوهمي
            'RGBD/OptimizeMaxError': '0.1',       # رفض أي تعديل عشوائي يلوى الخريطة
            'RGBD/OptimizeFromLastNode': 'true',

            # --- 2. دمج الطبقات وتنظيف الـ Point Cloud ---
            'Grid/CellSize': '0.05',             # تجميع النقط في دقة 5 سم يدمج الطبقات المزدوجة ببعضها
            'Grid/DepthDecimation': '2',
            'Grid/RangeMax': '3.5',              # قطع الأبعاد البعيدة جداً لمنع نويز الماية
            'Grid/RangeMin': '0.4',
            'Grid/NoiseFilteringRadius': '0.1',   # إزالة النقط العشوائية المطرطشة
            'Grid/NoiseFilteringMinNeighbors': '5',

            # --- 3. استقرار الأداء ومنع التهنيج ---
            'Rtabmap/DetectionRate': '1.0',       # معالجة فريم واحد بالثانية لملاءمة Gazebo
            'RGBD/LinearUpdate': '0.15',          # تحديث الخريطة كل 15 سم حركة
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

    return LaunchDescription([
        rtabmap_node
    ])
