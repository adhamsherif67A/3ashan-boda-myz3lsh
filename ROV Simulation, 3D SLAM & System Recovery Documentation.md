# **ROV Simulation, 3D SLAM & System Recovery Documentation**

**Author:** Ziad Selim  
**Date:** November 14, 2026  
**Project / Team:** MATE ROV Competition (EXPLORER Class) — Underwater Vehicle Simulation & 3D Mapping Stack  
System Environment: Ubuntu 22.04 LTTS \| ROS 2 Humble \| Gazebo Harmonic \| ArduSub SITL \| MAVROS \| QGroundControl v4.4.3 \| Stereolabs ZED2i \| RTAB-Map (rtabmap\_slam) \| RViz2  
\|---\|---\|---\|---\|---\|---\|---\|

# **Overview**

This document consolidates the terminal commands, configuration fixes, error diagnostics, and verified resolutions across the end-to-end ROV simulation, teleoperation, 3D SLAM mapping, and Ubuntu storage recovery workflows. It serves as an engineering reference and standard operating procedure for launching the Gazebo–ArduSub–MAVROS control pipeline, executing ZED2i visual SLAM with RTAB-Map, exporting 3D point cloud deliverables, and resolving system-level SQLite and URDF asset failures.  
**Unified Launch & SITL Outcome:** Although `delayed_sitl` initially failed to start inside `full_rov_sim.launch.py`, running ArduSub SITL inside the unified launch file **worked eventually** after isolating `PYTHONPATH`, setting the ArduSub working directory (`cwd`), wrapping execution in `gnome-terminal`, and tuning `TimerAction` startup delays—eliminating the need to launch SITL in a separate terminal.  
**RTAB-Map & RViz2 Launch Outcome:** After registering the `rviz/RTABmap.rviz` configuration in `setup.py` and rebuilding the `RTAB` package, RViz2 opened automatically upon launching `RTAB.launch.py`.  
**Storage Difficulty Summary:** A significant storage difficulty encountered throughout the workflow was that limited free space on the Ubuntu root partition (on a dual-boot setup) was rapidly exhausted by high-frequency ZED2i RGB-D frame commits into `~/.ros/rtabmap.db`, Docker images, and system caches. This caused repeated SQLite `COMMIT` disk-full crashes (`database or disk is full`) during 3D SLAM sessions and `[Errno 28] No space left on device` errors until caches were pruned and the Ubuntu partition was expanded via GParted Live USB.

# **1\. ArduSub SITL, Gazebo & ROS 2 Teleoperation Stack**

## **1.1 Key Commands**

**Build Teleoperation Package (`rov_joystick`) & Source Workspace:**

```
cd ~/joys_vov_ws
colcon build --packages-select rov_joystick
source install/setup.bash
```

**Launch Full Integrated ROV Simulation Stack (Gazebo \+ ArduSub SITL \+ MAVROS \+ Teleop Nodes):**  
**Verified Integration Outcome:** Running ArduSub SITL inside `full_rov_sim.launch.py` **worked eventually** after resolving `PYTHONPATH` pollution, TTY console allocation, and startup timing delays; launching ArduSub SITL in a separate terminal is no longer required.

```
ros2 launch rov_joystick full_rov_sim.launch.py
```

**Standalone ArduSub SITL Execution (Legacy / Isolated Debug Reference Only):**

```
sim_vehicle.py -v ArduSub -f vectored --model=JSON -l 31.312000,30.067222,0,0 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551 --console
```

## **1.2 Errors & Resolutions**

| Error / Symptom | Root Cause | Verified Resolution |
| :---- | :---- | :---- |
| **`delayed_sitl` fails to start inside `full_rov_sim.launch.py`** | Relying on interactive bash aliases (`sim_vehicle.py` missing from non-interactive `PATH`), absence of a TTY for the MAVProxy console, incorrect working directory (`cwd`), and ROS 2 `PYTHONPATH` polluting ArduPilot Python dependencies. | Wrapped `sim_vehicle.py` inside `gnome-terminal` via `ExecuteProcess`, explicitly ran `unset PYTHONPATH` prior to execution, set `cwd` to the ArduSub directory, and sequenced startup with `TimerAction`. **Outcome:** ArduSub SITL inside `full_rov_sim.launch.py` **worked eventually** with these fixes in place, running reliably inside the single unified launch file. |
| **MAVROS connection timeout or drop on startup** | MAVROS launched before ArduSub SITL finished initializing its UDP telemetry ports (`14550` and `14551`). | Staggered MAVROS and controller node launch delays using `TimerAction` so ArduSub SITL binds UDP sockets first. |
| **ArduSub rejects ROS 2 `manual_control` / RC override commands** | Ground Control Station system ID mismatch and failsafe checks blocking external MAVROS control messages. | Configured ArduSub parameter `SYSID_MYGCS` to match the MAVROS system ID, configured `FS_GCS_ENABLE` appropriately, and implemented a continuous publishing loop with corrected surge, sway, heave, and yaw axis scaling. |
| **`rov_joystick_node.cpp` / `keyboard_joy_node.cpp` compilation failure** | Placeholder text left in header definitions instead of valid integer axis indices, along with missing package references in build configuration. | Replaced placeholder definitions with valid integer constants (e.g., `AXIS_SURGE = 1`), verified package dependencies, and rebuilt cleanly with `colcon build --packages-select rov_joystick`. |

# **2\. RTAB-Map 3D SLAM, RViz2 & Mapping Deliverables**

## **2.1 Key Commands**

**Rebuild RTAB-Map Package with Symlink Install:**

```
cd ~/joys_vov_ws
colcon build --packages-select RTAB --symlink-install
source install/setup.bash

Launch RTAB-Map 3D SLAM & RViz2 Visualization:
Verified Visualization Outcome: RViz2 opened automatically with the RTABmap.rviz layout upon launching RTAB.launch.py.
ros2 launch RTAB RTAB.launch.py

```

**Archive & Rename SLAM Database Deliverable:**

```
mkdir -p ~/rtabmap_deliverables
cp ~/.ros/rtabmap.db ~/rtabmap_deliverables/pool_map.db
```

**Verify Database Integrity & Node / Loop-Closure Statistics:**

```
rtabmap-info ~/rtabmap_deliverables/pool_map.db
```

**Export 3D Point Cloud Map (`.ply`):**

```
rtabmap-export --output_dir ~/rtabmap_deliverables ~/rtabmap_deliverables/pool_map.db
```

## **2.2 Errors & Resolutions**

| Error / Symptom | Root Cause | Verified Resolution |
| :---- | :---- | :---- |
| **RViz2 fails to load `RTABmap.rviz` when launching RTAB-Map** | The `rviz/` directory and configuration file were not registered in `setup.py`, preventing `colcon` from installing `RTABmap.rviz` into `share/RTAB/rviz`. | Added `(os.path.join('share', package_name, 'rviz'), ['rviz/RTABmap.rviz'])` to `data_files` in `setup.py` and rebuilt with `colcon build --packages-select RTAB --symlink-install`. **Outcome:** RViz2 opened automatically upon launching `RTAB.launch.py` once `RTABmap.rviz` was registered and installed. |
| **Empty point cloud or TF / sensor desynchronization in RViz2** | Topic remapping mismatch between simulated ZED2i stereo topics and `rtabmap_slam` inputs, or premature node startup before simulation `/clock` stabilized. | Aligned ZED2i RGB, depth, and `camera_info` topic remappings in the Python launch file and synchronized `use_sim_time` across all nodes. |

# **3\. Ubuntu Disk Exhaustion, SQLite Crashes & ZED2i URDF Meshes**

## **3.0 Storage Difficulty Overview**

During the workflow, a critical storage bottleneck occurred due to limited headroom on the dual-boot Ubuntu root partition. High-frequency ZED2i stereo and depth frame logging rapidly grew `~/.ros/rtabmap.db` to several gigabytes. Combined with accumulated ROS 2 build artifacts, Docker containers, and systemd journal logs, available disk space was completely exhausted. This resulted in system-wide `[Errno 28] No space left on device` errors and fatal `DBDriverSqlite3.cpp` SQLite disk-full crashes until aggressive cache cleanup was conducted and the Ubuntu partition was expanded using GParted via a Live USB.

## **3.1 Key Commands**

**Check Disk Usage Across Partitions:**

```
df -h
```

**Reclaim System Space (Docker, APT Cache, Journal Logs, Stale SLAM DB):**

```
docker system prune -a --volumes
sudo apt autoremove --purge -y && sudo apt clean
sudo journalctl --vacuum-time=2d
rm -f ~/.ros/rtabmap.db
```

**Batch-Fix Broken ZED2i Mesh Paths in URDF / Xacro Files:**

```
find ~/joys_vov_ws/src -type f \( -name "*.urdf" -o -name "*.xacro" \) -exec sed -i 's|old_mesh_prefix|package://zed_wrapper/meshes|g' {} +
```

## **3.2 Errors & Resolutions**

| Error / Symptom | Root Cause | Verified Resolution |
| :---- | :---- | :---- |
| **`DBDriverSqlite3.cpp:525::executeNoResultQuery() Condition (rc == SQLITE_OK) not met! [DB error: database or disk is full, the query is COMMIT;]`** | The root Ubuntu partition exhausted all available free blocks during high-frequency ZED2i RGB-D frame commits to `~/.ros/rtabmap.db`. | Freed immediate storage by pruning unused Docker images/volumes, purging APT caches, trimming systemd journal logs, and removing stale `~/.ros/rtabmap.db` files; expanded the Ubuntu partition permanently using GParted via a Live USB. |
| **Missing ZED2i / ROV visual meshes in Gazebo & RViz2** | Hardcoded or invalid `package://` URI paths in URDF/Xacro definitions and missing mesh install rules in `CMakeLists.txt`. | Audited and batch-patched mesh paths using `find` and `sed`, added `meshes/` directory install rules to `CMakeLists.txt`, and performed a clean workspace rebuild. |
| **ZED SDK / ROS 2 wrapper build permission and artifact errors** | Incomplete ZED SDK installation permissions and stale `build/` and `install/` workspace caches. | Re-ran the ZED SDK installer with `sudo`, cleared stale `build/` and `install/` artifacts, and rebuilt the workspace cleanly. |

# **4\. Consolidated End-to-End Standard Operating Procedure (SOP)**

1. **Pre-Flight Disk & Workspace Check:**  
   * Run `df -h` to confirm at least 5–10 GB of free disk space on `/` before recording a new 3D SLAM session.  
   * Back up or remove any leftover `~/.ros/rtabmap.db` from prior test runs to prevent database bloat or unintentional map merging.  
   * Ensure `~/joys_vov_ws` is freshly built and sourced (`source ~/joys_vov_ws/install/setup.bash`).  
2. **Simulation & Teleoperation Startup:**  
   * Launch the integrated stack with `ros2 launch rov_joystick full_rov_sim.launch.py` (which launches ArduSub SITL directly inside the launch file alongside Gazebo, MAVROS, and the teleoperation nodes).  
   * Confirm the ArduSub SITL terminal initializes cleanly, MAVROS establishes a heartbeat over UDP `14550`/`14551`, and joystick/keyboard inputs actuate surge, sway, heave, and yaw smoothly.  
3. **3D SLAM Mapping Session:**  
   * Launch the RTAB-Map \+ RViz2 stack via `ros2 launch RTAB RTAB.launch.py`, confirming that RViz2 opens automatically with `RTABmap.rviz` loaded.  
   * Navigate the ROV through the pool environment, verifying real-time point cloud accumulation and loop-closure detections in RViz2.  
   * Terminate `rtabmap_slam` cleanly using `Ctrl+C` so SQLite flushes and finalizes the database `COMMIT`.  
4. **Deliverable Packaging & Verification:**  
   * Copy `~/.ros/rtabmap.db` into `~/rtabmap_deliverables/pool_map.db`.  
   * Run `rtabmap-info ~/rtabmap_deliverables/pool_map.db` to validate node count, loop closures, and database integrity.  
   * Generate the 3D point cloud file (`pool_cloud.ply`) using `rtabmap-export --output_dir ~/rtabmap_deliverables ~/rtabmap_deliverables/pool_map.db`.

