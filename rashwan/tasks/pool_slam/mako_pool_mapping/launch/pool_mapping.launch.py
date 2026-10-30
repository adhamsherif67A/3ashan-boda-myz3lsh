"""Independent mapping graph; simulator retains its original TF and control odometry."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def configure(context):
    share=Path(get_package_share_directory('mako_pool_mapping'))
    folder=Path(LaunchConfiguration('output_dir').perform(context)).expanduser()
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'rtabmap_work').mkdir(exist_ok=True)
    common={'use_sim_time':True,'frame_id':'base_link','subscribe_rgbd':True,
            'approx_sync':True,'topic_queue_size':5,'sync_queue_size':10,
            'qos':1,'qos_camera_info':1,'wait_for_transform':0.3}
    return [
      Node(package='ros_gz_bridge',executable='parameter_bridge',name='mapping_camera_bridge',
           arguments=['/zed2i/sim/left/image@sensor_msgs/msg/Image[gz.msgs.Image',
                      '/zed2i/sim/left/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'],
           remappings=[('/zed2i/sim/left/image','/pool_mapping/camera/rgb'),
                       ('/zed2i/sim/left/camera_info','/pool_mapping/camera/info')],output='screen'),
      Node(package='rtabmap_sync',executable='rgbd_sync',name='rgbd_sync',namespace='pool_mapping',
           parameters=[{'use_sim_time':True,'approx_sync':False,'approx_sync_max_interval':0.0,
                        'topic_queue_size':5,'sync_queue_size':10,'qos':1,'qos_camera_info':1}],
           remappings=[('rgb/image','/pool_mapping/camera/rgb'),
                       ('depth/image','/zed2i/zed_node/left/depth/image_raw'),
                       ('rgb/camera_info','/pool_mapping/camera/info')],output='screen'),
      Node(package='rtabmap_odom',executable='rgbd_odometry',name='visual_odometry',namespace='pool_mapping',
           parameters=[common,{'odom_frame_id':'pool_odom','publish_tf':False,
             'publish_null_when_lost':True,'wait_imu_to_init':True,
             'Odom/Strategy':'0','Odom/ResetCountdown':'15',
             'Odom/ImageDecimation':'2','Vis/FeatureType':'1','Vis/MaxFeatures':'2000',
             'SIFT/ContrastThreshold':'0.01','OdomF2M/MaxSize':'10000',
             'Vis/EstimationType':'0','Vis/CorType':'1',
             'Vis/CorGuessWinSize':'10','Vis/InlierDistance':'0.03',
             'Vis/MinInliers':'15','Vis/MaxDepth':'14.0','Reg/Force3DoF':'false'}],
           remappings=[('imu','/imu/data')],output='screen'),
      Node(package='rtabmap_slam',executable='rtabmap',name='rtabmap',namespace='pool_mapping',
           parameters=[common,{'database_path':str(folder/'pool.db'),'working_directory':str(folder/'rtabmap_work'),'map_frame_id':'pool_map',
             'odom_frame_id':'','publish_tf':True,'odom_sensor_sync':False,'qos_image':1,'qos_odom':1,
             'subscribe_depth':False,'subscribe_odom_info':False,
             'Rtabmap/DetectionRate':'2.0','Rtabmap/LoopThr':'0.11',
             'Mem/IncrementalMemory':'true','Mem/STMSize':'10','Mem/ImagePreDecimation':'2',
             'RGBD/LinearUpdate':'0.15','RGBD/AngularUpdate':'0.15',
             'RGBD/OptimizeFromGraphEnd':'false','RGBD/ProximityBySpace':'false',
             'Vis/MinInliers':'100','Vis/MinInliersDistribution':'0.01',
             'RGBD/OptimizeMaxError':'1.0','Vis/MaxDepth':'14.0','Grid/Sensor':'1',
             'Grid/3D':'true','Grid/CellSize':'0.05','Grid/RangeMax':'14.0',
             'Grid/NormalsSegmentation':'false','map_always_update':True}],output='screen'),
      Node(package='mako_pool_mapping',executable='loop_evidence',namespace='pool_mapping',
           parameters=[{'use_sim_time':True,'output_dir':str(folder)}],output='screen'),
      Node(package='rviz2',executable='rviz2',name='pool_mapping_rviz',
           arguments=['-d',str(share/'config/pool_mapping.rviz')],
           parameters=[{'use_sim_time':True}],condition=IfCondition(LaunchConfiguration('rviz')),
           output='screen')]


def generate_launch_description():
    return LaunchDescription([
      DeclareLaunchArgument('output_dir',default_value='/data'),
      DeclareLaunchArgument('rviz',default_value='true'),OpaqueFunction(function=configure)])
