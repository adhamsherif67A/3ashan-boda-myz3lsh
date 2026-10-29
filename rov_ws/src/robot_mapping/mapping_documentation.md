# 3D Pool Mapping & Loop Closure using RTAB-Map ROS 2

## 1. Project Overview

This package integrates **RTAB-Map ROS 2** into a Gazebo ROV simulation to generate a high-density 3D point cloud map of an underwater swimming pool environment. It is configured specifically for **6-DoF underwater vehicle motion** and addresses challenges related to low-texture visual environments (e.g., uniform pool tiles and floor) through combined **Visual and ICP (Iterative Closest Point)** registration techniques.

## 2. Topic & Frame Architecture

### Reference Frames

| Frame Name | Identification | Description | 
| ----- | ----- | ----- | 
| **Map Frame** | `map` | Global fixed reference frame for the 3D SLAM map | 
| **Odometry Frame** | `odom` | Continuous local odometry reference frame | 
| **Robot Frame** | `base_link` | ROV center-of-mass frame for full 6-DoF rigid body motion | 

### Topic Remappings

* **RGB Image**: `/zed2i/zed_node/rgb/image_rect_color` (`sensor_msgs/msg/Image`)
* **Depth Image**: `/zed2i/zed_node/depth/depth_registered` (`sensor_msgs/msg/Image`)
* **Camera Info**: `/zed2i/zed_node/rgb/camera_info` (`sensor_msgs/msg/CameraInfo`)
* **Odometry**: `/odometry/gz` (`nav_msgs/msg/Odometry`)

## 3. ROS 2 Launch File (`mapping.launch.py`)

The complete launch script handles time synchronization, parameter tuning, topic remappings, automated database clearing, and launches RViz2 pre-configured with `pool_mapping.rviz`.

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    # 1. Custom RViz Configuration Path
    pkg_share = get_package_share_directory('robot_mapping')
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'pool_mapping.rviz')

    # 2. RTAB-Map SLAM Node
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        arguments=['-d'],  # Reset database on startup for clean mapping session
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

            # --- 1. Registration Strategy & 6-DoF Motion (ICP Alignment) ---
            'Reg/Strategy': '1',                  # 1 = Visual + ICP Registration for robust surface matching
            'Reg/Force3DoF': 'false',             # Disabled 3DoF restriction to allow full 6-DoF underwater movement
            'Vis/MinInliers': '15',               # Minimum visual inliers to accept loop closures
            'RGBD/OptimizeMaxError': '0.1',       # Reject loop closure links that cause severe trajectory distortion
            'RGBD/OptimizeFromLastNode': 'true',

            # --- 2. Grid & Depth Filtering (Layer Merging & Noise Reduction) ---
            'Grid/CellSize': '0.05',              # 5 cm voxel size to smooth point layers and merge walls
            'Grid/DepthDecimation': '2',          # Downsample depth map for performance efficiency
            'Grid/RangeMax': '3.5',               # Cutoff maximum depth to eliminate underwater scattering noise
            'Grid/RangeMin': '0.4',
            'Grid/NoiseFilteringRadius': '0.1',   # Filter floating noise artifacts
            'Grid/NoiseFilteringMinNeighbors': '5',

            # --- 3. Performance & Stability Optimization ---
            'Rtabmap/DetectionRate': '1.0',       # Process 1 Hz to match Gazebo simulation RTF
            'RGBD/LinearUpdate': '0.15',          # Add new graph node after moving 15 cm
            'RGBD/AngularUpdate': '0.1',          # Add new graph node after rotating 0.1 rad
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

    # 3. RViz2 Node with Custom Configuration
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        rtabmap_node,
        rviz_node,
    ])
```

## 4. Key Parameter Tuning Breakdown

1. **`Reg/Force3DoF: 'false'`**:
   * Critical for underwater vehicles. Unlocks full 6-DoF motion (roll, pitch, yaw, heave) instead of forcing flat 2D planar movement.

2. **`Reg/Strategy: '1'`**:
   * Activates **ICP (Iterative Closest Point)** refinement on top of visual feature matching. This fixes map twisting and double-layer ghosting caused by repetitive pool tiles.

3. **`Vis/MinInliers: '15'` & `RGBD/OptimizeMaxError: '0.1'`**:
   * Requires a minimum threshold of 15 matching visual keypoints and strict geometric error bounds to accept loop closures, eliminating false positive links.

4. **`Grid/RangeMax: '3.5'`**:
   * Cuts off depth data beyond 3.5 meters to remove aquatic light distortion and noise points.

5. **`Rtabmap/DetectionRate: '1.0'`**:
   * Throttles execution rate to 1 Hz, avoiding CPU bottlenecks and maintaining time synchronization with Gazebo.

## 5. Step-by-Step Execution & Workflow

### Prerequisites: Launch ROV Control & Simulation

Before running the mapping node, ensure the ROV simulation and sensor streams (camera & odometry topics) are active. In **Terminal 1**:

```bash
cd ~/ros2_ws  # or your workspace path
source install/setup.bash
ros2 launch ps_rov_control rov_control.launch.py
```

### Step 1: Launch 3D Mapping & RViz2

Once the ROV controller is active, execute the mapping node in **Terminal 2**:

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch robot_mapping mapping.launch.py
```

### Step 2: Perform Loop Closure & Save Database

Drive the ROV in a complete circuit around the pool and return to the starting area. Terminate the process using `Ctrl + C`. RTAB-Map automatically saves the session to `~/.ros/rtabmap.db`. Save a backup copy:

```bash
cp ~/.ros/rtabmap.db ~/pool_3d_map.db
```

### Step 3: Export 3D Point Cloud (.PLY File)

Convert the stored database into a `.ply` 3D point cloud file for inspection:

```bash
rtabmap-export --ply ~/pool_3d_map.db
```

### Step 4: Load and Display Map on Another Machine

To display the generated 3D map in RViz2 on another system without re-running SLAM:

```bash
ros2 run rtabmap_slam rtabmap --ros-args \
  -p database_path:=~/pool_3d_map.db \
  -p Mem/IncrementalMemory:=false \
  -p use_sim_time:=false
```

In RViz2:
* Set **Fixed Frame** to `map`.
* Add **PointCloud2** subscribed to topic `/cloud_map`.
* Set **Style** to `Flat Squares` and **Size (m)** to `0.05`.

## 6. Note on Large Map Files (Git LFS)

The 3D map database and mesh files (`pool_3d_map.db` and `pool_3d_map.ply`) are managed using **Git LFS** due to GitHub file size limits.

If you clone this repository and find that the map files are only a few bytes in size (pointer files), ensure `git-lfs` is installed and run the following command to download the complete binary files:

```bash
sudo apt install git-lfs
git lfs install
git lfs pull
```

## 7. Project Deliverables Checklist

* [x] **Saved Database File**: `pool_3d_map.db`
* [x] **Exported 3D Map File**: `pool_3d_map.ply`
* [x] **3D Mapping Demonstration Screenshots**: High-resolution RViz screenshots demonstrating the final 3D map reconstruction and loop closure verification. *(Provided in place of a video recording to prevent extreme CPU/GPU lag and system freezing caused by simultaneously running Gazebo simulation, RViz2, RTAB-Map, and screen recording software, as well as to keep repository media lightweight).*
* [x] **Documentation & Launch Configuration**: `mapping.launch.py` and `mapping_documentation.md`.
