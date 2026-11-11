# MarineXperts 2027 | Mako ROV software

<p align="center">
  <img src="https://img.shields.io/badge/Team-MarineXperts-00B8D9?style=for-the-badge" />
  <img src="https://img.shields.io/badge/ROS-2_Humble-22314E?style=for-the-badge&logo=ros" />
  <img src="https://img.shields.io/badge/Gazebo-Harmonic-00A6C8?style=for-the-badge" />
  <img src="https://img.shields.io/badge/ArduSub-SITL-003B5C?style=for-the-badge" />
</p>

Simulation, vehicle control, vision and the **Operation MX** pilot station for the
MarineXperts Mako ROV. Everything a team member needs is in this repository: one
ROS 2 workspace, one Docker image, one app. Everyone builds the same packages and
opens the same Operation MX window.

## Contents

1. [Architecture](#1-architecture)
2. [Quick start](#2-quick-start)
3. [Native setup (Ubuntu 22.04)](#3-native-setup-ubuntu-2204)
4. [Docker setup](#4-docker-setup)
5. [Running: every option](#5-running-every-option)
6. [ROS interfaces: topics, publishers and subscribers](#6-ros-interfaces-topics-publishers-and-subscribers)
7. [Testing](#7-testing)
8. [Troubleshooting](#8-troubleshooting)
9. [Contributing](#9-contributing)
10. [Known issues](#10-known-issues)
11. [Upstream projects](#11-upstream-projects)

---

## 1. Architecture

### Packages

The workspace is split by responsibility. Each package builds and launches on its own;
`mako_bringup` composes them.

| Package | Responsibility | Main contents |
| --- | --- | --- |
| [`robot_description`](src/robot_description) | **The robot and its world.** No control or vision logic. | URDF/xacro model, meshes, Gazebo Harmonic worlds (pool, ocean) and task assets, pool-waves Gazebo plugin, ROS↔Gazebo bridge config, simulated depth and point-cloud relays, `gazebo.launch.py`, RViz views |
| [`mako_control`](src/mako_control) | **Driving the vehicle.** Everything between sensors/pilot and ArduSub. | `realjoy_node` (gamepad + Operation MX keyboard → MAVROS), ExternalNav odometry relay, ArduSub parameter file and helper, autotune client, waypoint and fly-transect missions, `control/pilot/mavros` launch files |
| [`mako_vision`](src/mako_vision) | **Seeing.** Camera processing that does not depend on control. | ZED RGB-D odometry with onboard IMU assistance, SLAM compatibility launch, bottom-camera transect detector (`mako_vision.transect_detector`), real-ROV ZED pose relay |
| [`robot_mapping`](src/robot_mapping) | **Mapping.** Team RTAB-Map backend imported from ibrahim-amr. | Matched RGB-D, validated odometry, 3D mapping and RViz view |
| [`mako_navigation`](src/mako_navigation) | **Planning.** Optional planar Nav2 servers with isolated controller output. | Costmaps, planner, controller, BT navigator; depth control remains in mako_control |
| [`mako_bringup`](src/mako_bringup) | **Putting it together.** | `simulation.launch.py`: world + robot, vision (optional) and control in one command |
| [`gui/`](gui) | **Operation MX** pilot station (PyQt5) | Starts SITL, MAVROS, Gazebo and pilot control for you; cameras, telemetry, arming/modes, keyboard pilot, recording |

Dependency direction: `mako_bringup → {robot_description, mako_vision, mako_control, mako_navigation}`,
`mako_control → mako_vision` (the transect mission imports the detector), and
`mako_vision → robot_mapping` for the mapping backend/runtime. `robot_description`
and `robot_mapping` do not depend on another Mako package.

### How the pieces talk

```text
                 ┌───────────────── Operation MX (gui/) ─────────────────┐
                 │ cameras · telemetry · arm/mode · keyboard pilot        │
                 └──┬───────────────▲──────────────────────────┬──────────┘
   /mako/autopilot/manual_control   │ images, /mavros/state,   │ starts the processes
                    │               │ /mavros/rc/out, /odometry/gz
 gamepad ─/joy─► realjoy_node (mako_control) ─/mavros/manual_control/send─► MAVROS ◄─UDP 14551─► ArduSub SITL
                                                                             ▲   │                 ▲  │
 Gazebo (robot_description)                                                  │   └─ /mavros/state  │  │ UDP 9002/9003
  ├─ ros_gz_bridge ─► /clock /odometry/gz /imu/data /joint_states            │      /mavros/rc/out │  │ (ArduPilot JSON)
  ├─ ros_gz_bridge ─► ZED, bottom and chase camera topics                    │                     │  ▼
  └─ odom_to_depth ─► /rov/depth                                             │            ArduPilot Gazebo plugin
                                                                             │            (thrusters, IMU in Gazebo)
 /odometry/gz (ground truth) ─┐                                              │
 /zed2i/vo/odometry (mako_vision VO) ─┴─► gz_odom_to_mavros (mako_control) ─/mavros/odometry/out─┘ → EKF3 ExternalNav
```

* **ArduSub SITL** is the flight controller (the same firmware as the Pixhawk). Gazebo's
  ArduPilot plugin exchanges motor commands and vehicle state with it over UDP (JSON).
* **MAVROS** bridges ROS 2 and MAVLink. Everything that commands the vehicle goes through it.
* **ExternalNav**: Gazebo's pressure sensor is not hydrostatic, so ArduSub's EKF3 gets its
  position from `/mavros/odometry/out`, fed by ground truth (default) or ZED visual odometry.

### Repository layout

```text
.
├── src/
│   ├── robot_description/   model, worlds, Gazebo launch          (ROS package)
│   ├── mako_control/        realjoy_node, MAVROS relay, missions  (ROS package)
│   ├── mako_vision/         RGB-D + IMU odometry, detectors        (ROS package)
│   ├── robot_mapping/       team RTAB-Map backend, mapping RViz    (ROS package)
│   ├── mako_navigation/     optional planar Nav2 servers           (ROS package)
│   └── mako_bringup/        complete simulation launch            (ROS package)
├── gui/                     Operation MX pilot station + desktop installer/updater
├── docker/                  build/run helpers, simulation supervisor, doctor
├── firmware/ardusub-autotune/  ArduSub AUTOTUNE mode patch
├── tools/                   desktop release packaging
├── commands.txt             SITL and MAVROS commands used by the app and Docker
├── Dockerfile, entrypoint.sh
└── install_geographiclib_datasets.sh
```

---

## 2. Quick start

**Docker** (nothing but Docker on the host):

```bash
git clone https://github.com/adhamsherif67A/3ashan-boda-myz3lsh.git MarineXperts
cd MarineXperts
./docker/build.sh            # once (20–60 min)
./docker/run.sh --gui        # Operation MX → choose a world → Start simulation
```

**Native** (Ubuntu 22.04 with ROS 2 Humble, Gazebo Harmonic, MAVROS and ArduSub
installed as in [section 3](#3-native-setup-ubuntu-2204)):

```bash
cd ~/MarineXperts
colcon build --symlink-install --base-paths src
gui/run_mako_gui.sh          # Operation MX
```

---

## 3. Native setup (Ubuntu 22.04)

Run ROS natively when you develop packages and want fast rebuilds. Use
[Docker](#4-docker-setup) if you only want to run the simulation.

### 3.1 Prerequisites overview

| Component | Version | Where it ends up |
| --- | --- | --- |
| Ubuntu | 22.04 (Jammy), x86-64 | |
| ROS 2 | Humble | `/opt/ros/humble` |
| Gazebo | Harmonic (gz-sim 8) + `ros-humble-ros-gzharmonic` | system |
| MAVROS | `ros-humble-mavros` + GeographicLib EGM96 geoid | system |
| RTAB-Map | `ros-humble-rtabmap-ros` | system |
| ArduSub SITL | ArduPilot source build | `~/ardupilot` |
| ArduPilot Gazebo plugin | source build for Harmonic | `~/ardupilot/ardupilot_gazebo/build` |
| Python | PyQt5, numpy, psutil, cryptography | system |

### 3.2 ROS 2 Humble

Follow the [official guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html). In short:

```bash
sudo apt update && sudo apt install -y software-properties-common curl
sudo add-apt-repository -y universe
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update && sudo apt install -y ros-humble-desktop ros-dev-tools
```

> **"Unable to locate package ros-humble-…"** usually means the old ROS apt key (it
> expired in June 2025). Installing `ros2-apt-source` as above replaces it.

### 3.3 Gazebo Harmonic and the Harmonic ROS bridge

```bash
sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update && sudo apt install -y gz-harmonic libgz-sim8-dev ros-humble-ros-gzharmonic
```

Do **not** also install the Fortress bridge (`ros-humble-ros-gz`): it conflicts with
`ros-humble-ros-gzharmonic`. See [Gazebo's Humble + Harmonic notes](https://gazebosim.org/docs/harmonic/ros_installation/).

### 3.4 MAVROS, RTAB-Map and the other ROS/Python dependencies

```bash
sudo apt install -y \
  ros-humble-mavros ros-humble-mavros-extras ros-humble-rtabmap-ros ros-humble-joy \
  ros-humble-xacro ros-humble-robot-state-publisher ros-humble-joint-state-publisher-gui \
  ros-humble-ament-cmake-pytest ros-humble-navigation2 ros-humble-nav2-bringup \
  geographiclib-tools \
  python3-pyqt5 python3-numpy python3-psutil python3-cryptography python3-yaml python3-pytest \
  ffmpeg xauth
# MAVROS needs the EGM96 geoid:
sudo bash install_geographiclib_datasets.sh      # from the repository root (after cloning, 3.7)
```

### 3.5 ArduSub SITL

```bash
git clone https://github.com/ArduPilot/ardupilot.git ~/ardupilot
cd ~/ardupilot
git checkout 375cef5813bbd4ea99a67d9f046833e1c492f439   # the revision the Docker image uses
git submodule update --init --recursive
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile
./waf configure --board sitl
./waf sub
```

`sim_vehicle.py` must then exist at `~/ardupilot/Tools/autotest/sim_vehicle.py`.

### 3.6 ArduPilot Gazebo plugin (Harmonic)

```bash
sudo apt install -y rapidjson-dev libopencv-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl
git clone https://github.com/ArduPilot/ardupilot_gazebo.git ~/ardupilot/ardupilot_gazebo
cd ~/ardupilot/ardupilot_gazebo
git checkout 082a0fe231f6e63bc8d1598f1cba461d9e2ea7f5          # the revision the Docker image uses
export GZ_VERSION=harmonic
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4
```

The launch files find the plugin in `~/ardupilot/ardupilot_gazebo/build` (override with
`MAKO_ARDUPILOT_GAZEBO`).

### 3.7 Clone and build this workspace

```bash
git clone https://github.com/adhamsherif67A/3ashan-boda-myz3lsh.git ~/MarineXperts
cd ~/MarineXperts
source /opt/ros/humble/setup.bash
sudo rosdep init 2>/dev/null; rosdep update
rosdep install --from-paths src --ignore-src -r -y \
  --skip-keys "ros_gz_sim ros_gz_bridge gz-sim8 gz-plugin2 gz-transport13"   # keep the Harmonic bridge
colcon build --symlink-install --base-paths src
```

After pulling source updates, stop simulation and close Operation MX, then rebuild:

```bash
git pull --ff-only origin main
source /opt/ros/humble/setup.bash
colcon build --symlink-install --base-paths src
source install/setup.bash
gui/run_mako_gui.sh
```

Gazebo and ROS load files from `install/`; running Python processes retain their
old code and parameters until restarted. Docker users instead rebuild the image
with `./docker/build.sh --rebuild`. Pushing `main` updates source code; signed
desktop users receive updates when a new versioned release is published, as
explained in [gui/UPDATES.md](gui/UPDATES.md).

### 3.8 Environment (`~/.bashrc`)

```bash
cat >> ~/.bashrc <<'EOF'
source /opt/ros/humble/setup.bash
source ~/MarineXperts/install/setup.bash
export MAKO_ARDUPILOT=$HOME/ardupilot                         # default; change if elsewhere
export MAKO_ARDUPILOT_GAZEBO=$HOME/ardupilot/ardupilot_gazebo  # default; change if elsewhere
EOF
```

Open a new terminal and check:

```bash
for pkg in robot_description mako_control mako_vision robot_mapping mako_navigation mako_bringup; do
  ros2 pkg prefix "$pkg"
done   # all under ~/MarineXperts/install
```

> Source **only one** copy of `robot_description`. Remove old lines such as
> `source ~/mako_ws/install/setup.bash` from `~/.bashrc`; otherwise an old world or model
> can be loaded. Software2026 is no longer needed: `realjoy_node` is built here in `mako_control`.

### 3.9 Optional: desktop shortcut

```bash
gui/install_shortcut.sh      # adds "Operation MX" to the app menu and the desktop
```

Managed desktop installs with signed private updates are described in
[gui/UPDATES.md](gui/UPDATES.md).

---

## 4. Docker setup

The image contains ROS 2 Humble, Gazebo Harmonic, MAVROS, RTAB-Map, pinned ArduSub and
ArduPilot Gazebo plugin builds, all six ROS packages and Operation MX.

### 4.1 Host requirements

* Linux x86-64 with [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) and
  your user in the `docker` group ([post-install](https://docs.docker.com/engine/install/linux-postinstall/)).
* An X11/XWayland desktop and `xauth` for windows (`sudo apt install xauth`).
* ≥ 16 GB RAM, ≥ 20 GiB free Docker storage for the first build.
* NVIDIA GPU (optional): host driver + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
  Intel/AMD `/dev/dri` devices are passed through automatically.

### 4.2 Build

```bash
./docker/build.sh                    # skips if the image already exists
./docker/build.sh --rebuild          # after pulling new code
./docker/build.sh --rebuild --jobs 4 # more parallel compile jobs (more RAM)
```

The image is `marinexperts/mako:latest` (`MAKO_IMAGE` overrides the tag). The helper
always pulls a fresh `ros:humble-ros-base-jammy`, so the ROS apt key is current, and
matches the container user to your UID/GID.

### 4.3 Check the image

```bash
./docker/run.sh --doctor             # ends with "RESULT: ready"
```

### 4.4 Run

| Command | What you get |
| --- | --- |
| `./docker/run.sh --gui` | **Operation MX**. Choose a world and press *Start simulation* (recommended) |
| `./docker/run.sh` | Simulation with the Gazebo window, team pool, no app |
| `./docker/run.sh --world ocean.world` | Ocean course |
| `./docker/run.sh --pilot` | Simulation + `realjoy_node` + gamepad driver (fly with a gamepad, no app) |
| `./docker/run.sh --headless` | No Gazebo window (cameras still render), for servers |
| `./docker/run.sh --odometry-source vision` | ZED visual odometry feeds ArduSub |
| `./docker/run.sh --slam` | RTAB-Map SLAM (implies visual odometry) |
| `./docker/run.sh --nvidia …` | Use the NVIDIA GPU |
| `./docker/run.sh --shell` | Bash inside the container with ROS sourced |
| `docker exec -it mako-sim /bin/bash /entrypoint.sh shell` | Second terminal in a running container |

All `docker/run.sh` options are listed in [section 5.6](#56-docker-supervisor-dockerrunsh--dockersimulationpy).
Gamepads are passed through (`/dev/input`); disable with `--no-joystick`. App runs,
captures and recordings are saved on the host in `~/mako-data` (`MAKO_DATA_DIR` overrides).

### 4.5 Talk to the container from the host

The container uses host networking. With ROS on the host:

```bash
export ROS_DOMAIN_ID=42 RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic list
```

### 4.6 Stop and logs

Ctrl+C in the terminal, or `docker stop mako-sim`. The supervisor prints its log folder.
Copy it before the container is removed: `docker cp mako-sim:/home/sim/mako-runs ./mako-runs`.

---

## 5. Running: every option

### 5.1 Operation MX (recommended)

```bash
gui/run_mako_gui.sh            # native
./docker/run.sh --gui          # Docker
```

1. Choose **Team pool** or **Ocean · 4 m**, the odometry source (**ZED RGB-D + IMU** or ground truth), and optional **Enable SLAM mapping**.
2. Press **Start simulation**. The app starts ArduSub SITL, MAVROS, headless Gazebo
   (`mako_bringup/simulation.launch.py`), the gamepad driver and `realjoy_node`.
3. **Arm**, choose a mode (MANUAL / STABILIZE / ALT_HOLD) and fly.

| Control | Action |
| --- | --- |
| Gamepad | Fly; see [`src/mako_control/JOYSTICK.md`](src/mako_control/JOYSTICK.md) for axes and tuning |
| **Keyboard pilot** + W/S, A/D, Q/E or ←/→, ↑/↓, Shift | Forward/back, sideways, turn, up/down, full power. A gamepad stick has priority |
| **First person / Third person**, **V** | ZED left eye or rear chase camera |
| **Camera only**, **H** | Hide the panels so the camera fills the window |
| **Full screen**, **F11** | Toggle full screen (`--windowed` starts in a normal window) |
| Drag the bottom view's corner, **[** / **]** | Resize the bottom-camera view |
| **C** / **R** | Capture a frame / record the session |
| **RViz**, **QGroundControl** | Open the TF/odometry viewer or QGC (UDP 14550) |
| **Reset** / **Stop simulation** | Restart / stop every process the app started |

The app uses ROS domain **42** (`MAKO_SIM_ROS_DOMAIN_ID` overrides). Environment
variables it reads:

| Variable | Default | Meaning |
| --- | --- | --- |
| `MAKO_WORKSPACE` | the repository the app is in (if built), else `~/mako_ws` | Workspace with `install/` and `commands.txt` |
| `MAKO_ARDUPILOT` | `~/ardupilot` | ArduPilot checkout with `Tools/autotest/sim_vehicle.py` |
| `MAKO_ARDUPILOT_GAZEBO` | `~/ardupilot/ardupilot_gazebo` | Plugin checkout (`build/libArduPilotPlugin.so`) |
| `MAKO_DATA_DIR` | `<workspace>/gui` | Where `runs/`, captures and recordings are saved |
| `MAKO_SOFTWARE_WORKSPACE` | unset | Optional extra overlay (no longer required) |
| `MAKO_QGROUNDCONTROL` | asked once | Path to QGroundControl |

### 5.2 Complete simulation from the command line

ArduSub SITL and MAVROS are separate processes. Start them in this order, in three
terminals, each with the workspace sourced and `export ROS_DOMAIN_ID=42`:

```bash
# 1. Gazebo + robot + vision + control
ros2 launch mako_bringup simulation.launch.py world:=pool.world configure_ardusub:=false
# 2. ArduSub SITL (after Gazebo is up)
cd ~/ardupilot && Tools/autotest/sim_vehicle.py -v ArduSub -f vectored --model=JSON \
  -l 31.312000,30.067222,0,0 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551 \
  --add-param-file=$HOME/MarineXperts/src/mako_control/config/ardusub_external_nav.parm
# 3. MAVROS
ros2 launch mako_control mavros.launch.py
```

Add `pilot:=true` to step 1 to fly with a gamepad, or start
`ros2 launch mako_control pilot.launch.py` separately. QGroundControl connects on UDP 14550.
(`commands.txt` holds the exact SITL and MAVROS commands the app and Docker use.)

#### `mako_bringup simulation.launch.py` arguments

| Argument | Default | Choices | Description |
| --- | --- | --- | --- |
| `world` | `pool.world` | `pool.world`, `pool.sdf`, `ocean.world` | Team pool tasks, legacy pool, or the 4 m ocean course (shipwreck, pipe, arch, search-and-survey cave) |
| `headless` | `false` | `true`, `false` | Run Gazebo without its window; cameras still render |
| `odometry_source` | `ground_truth` | `ground_truth`, `vision` | Odometry sent to ArduSub and owning `odom → base_link`: Gazebo ground truth, or ZED visual odometry (starts `mako_vision` VO) |
| `slam` | `false` | `true`, `false` | RTAB-Map SLAM; requires `odometry_source:=vision`; RTAB-Map then owns `map → odom` |
| `slam_database_path` | `~/.ros/mako_slam.db` | path | RTAB-Map database (reused, never deleted) |
| `slam_viz` | `false` | `true`, `false` | Open the RTAB-Map viewer |
| `navigation` | `false` | `true`, `false` | Start the optional planar Nav2 servers. Requires a navigation-ready occupancy map; outputs remain isolated from MAVROS |
| `publish_odom_tf` | `true` | `true`, `false` | Publish `odom → base_link`; disable to use your own estimator |
| `publish_map_tf` | `true` | `true`, `false` | Static `map → odom` when SLAM is off |
| `configure_ardusub` | `true` | `true`, `false` | Set ArduSub parameters through MAVROS 5 s after start. Use `false` when SITL loads `ardusub_external_nav.parm` (the app and Docker do) |
| `transect_mission` | `true` | `true`, `false` | Start the idle fly-transect mission node |
| `pilot` | `false` | `true`, `false` | Also start `realjoy_node` (+ gamepad driver) |
| `joystick` | `true` | `true`, `false` | With `pilot:=true`, start the `joy` gamepad driver |
| `performance_profile` | `balanced` | `maximum_fps` (640×360, 10/15 Hz), `balanced` (960×540, 12/20 Hz), `vision_quality` (1280×720, 15/24 Hz), `full_sensors` (1280×720, 15/30 Hz) | Camera resolution and RGB-D / pilot rates |
| `camera_width`, `camera_height` | `profile` | integer | Override the profile's camera resolution |
| `camera_fps` | `profile` | number | RGB-D, depth and bottom camera rate |
| `pilot_fps` | `profile` | number | Pilot (ZED left/right RGB) rate |
| `sitl_port_in`, `sitl_port_out` | `9002`, `9003` | port | ArduPilot JSON ports (change for a second simulation) |
| `render_gpu` | `auto` | `auto`, `nvidia`, `default` | NVIDIA PRIME offload when available (`nvidia` fails without a working NVIDIA GPU) |

### 5.3 Package launch files (each runs on its own)

**`robot_description`**

| Launch file | Starts | Arguments |
| --- | --- | --- |
| `gazebo.launch.py` | Gazebo + robot, `robot_state_publisher`, all ROS↔Gazebo bridges, `odom_to_depth`, `cloud_frame_relay`, `map → odom` | `world`, `headless`, `performance_profile`, `camera_*`, `pilot_fps`, `sitl_port_in/out`, `render_gpu` (as above); `publish_odom_tf` (ground-truth `odom → base_link`, default `true`); `publish_map_tf` (default `true`); `rgbd_bridge` (bridge the synchronized ZED RGB-D triplet for VO/SLAM, default `false`) |
| `display.launch.py` | RViz for a running simulation; with `standalone:=true` also a joint slider GUI and `robot_state_publisher` (model only, no Gazebo) | `standalone` (`false`) |
| `view_tf.launch.py` | RViz only | `view`: `model_tf.rviz` (default) or `pilot_views.rviz` |

**`mako_control`**

| Launch file | Starts | Arguments |
| --- | --- | --- |
| `control.launch.py` | `gz_odom_to_mavros`, `odom → odom_ned` static TF, `fly_transect_mission`, (optional) `fix_ardusub_params.py` | `odometry_source` (`ground_truth`), `publish_odom_tf` (`true`, vision mode only), `configure_ardusub` (`true`), `transect_mission` (`true`), `world` (`pool.world`) |
| `pilot.launch.py` | `joy/game_controller_node` + `realjoy_node` | `joystick` (`true`), `use_sim_time` (`false`) |
| `mavros.launch.py` | MAVROS (`apm.launch`) | `fcu_url`: `udp://127.0.0.1:14551@` (SITL, default), `/dev/ttyACM0:115200` (Pixhawk USB), `udp://0.0.0.0:14550@` (companion); `gcs_url` (empty) |

**`mako_vision`**

| Launch file | Starts | Arguments |
| --- | --- | --- |
| `visual_odometry.launch.py` | RTAB-Map `rgbd_odometry` as `zed_rgbd_odometry` → `/zed2i/vo/odometry` (config `config/zed_vo.yaml`) | none (`MAKO_VO_PREFIX` points at a local RTAB-Map install if it is not from apt) |
| `slam.launch.py` | Delegates to `robot_mapping` using matched ZED RGB-D and validated `/mavros/odometry/out` | `slam_database_path`, `slam_viz` (`false`), `use_sim_time` (`true`) |

**`robot_mapping`**

| Launch file | Starts | Arguments |
| --- | --- | --- |
| `mapping.launch.py` | One RTAB-Map mapper; optional RViz and RTAB-Map viewer | `database_path` (preserved), `use_sim_time` (`true`), `rviz`/`slam_viz` (`false`), `rgb_topic`, `depth_topic`, `camera_info_topic`, `odom_topic` |

**`mako_navigation`**

| Launch file | Starts | Arguments |
| --- | --- | --- |
| `navigation.launch.py` | Planner, holonomic controller, BT navigator, behaviors, smoothers, waypoint follower and lifecycle manager | `use_sim_time`/`autostart` (`true`), `params_file`, `map_topic` (`/rtabmap/map`) |

### 5.4 Executables (`ros2 run …`)

| Command | What it does |
| --- | --- |
| `ros2 run mako_control realjoy_node` | Pilot control. Parameters (axes, inversion, dead zones, expo, sensitivity, smoothing, timeouts, buttons) in [JOYSTICK.md](src/mako_control/JOYSTICK.md); change live with `ros2 param set /realjoy_node …` |
| `ros2 run mako_control gz_odom_to_mavros.py` | ExternalNav relay. Parameters: `source_topic` (`/odometry/gz`), `target_topic` (`/mavros/odometry/out`), `max_age` (0.75 s), `require_covariance` (false), `max_variance` (1.0), `reset_on_clock_jump` (false), `max_linear_speed` / `max_angular_speed` (0 = unlimited; 2 m/s and 3 rad/s in vision mode), `publish_tf` (false) |
| `ros2 run mako_control fix_ardusub_params.py [--non-interactive] [--wait-for-mavros S]` | Write the ArduSub parameters (PWM limits, motor directions, EKF3 ExternalNav sources) through `/mavros/param/set` |
| `ros2 run mako_control autotune.py start\|stop\|status [--namespace /mavros] [--timeout 8]` | ArduSub AUTOTUNE mode client (needs the firmware patch in `firmware/ardusub-autotune`) |
| `ros2 run mako_control local_waypoint_mission.py --waypoint X,Y,DEPTH [--waypoint …] [--xy-tolerance 0.25] [--depth-tolerance 0.15] [--dwell 1.0] [--max-xy-error 2.0]` | Fly local waypoints in GUIDED mode (depth in metres, positive down) |
| `ros2 run mako_control fly_transect_mission.py` | Pool fly-transect mission (started idle by `control.launch.py`); enable with `ros2 service call /fly_transect/enable std_srvs/srv/SetBool "{data: true}"` after arming |
| `ros2 run mako_vision zed_to_mavros_pose.py` | Real ROV: ZED wrapper pose → MAVROS vision pose |
| `ros2 run robot_description odom_to_depth.py` | Simulated depth: `/odometry/gz` → `/rov/depth` (parameters `source_topic`, `depth_topic`, `surface_z`) |
| `ros2 run robot_description cloud_frame_relay.py` | Simulated point clouds with the correct camera frames |
| `ros2 run robot_description check_sim_tf.py [--timeout 30]` | Check the TF tree of a running simulation |

### 5.5 Real ROV (hardware)

On the ROV/companion computer, with the Pixhawk connected:

```bash
ros2 launch mako_control mavros.launch.py fcu_url:=/dev/ttyACM0:115200
ros2 launch mako_control pilot.launch.py            # gamepad on the station computer
ros2 run mako_vision zed_to_mavros_pose.py          # if the ZED wrapper runs
```

Do not load the simulation parameter file on the real vehicle.

### 5.6 Docker supervisor (`docker/run.sh` / `docker/simulation.py`)

`docker/run.sh` options:

| Option | Description |
| --- | --- |
| `--gui` | Run Operation MX instead of the command-line supervisor |
| `--doctor` | Read-only dependency check |
| `--shell` | Bash inside the container (extra arguments go to bash) |
| `--nvidia` | Pass the NVIDIA GPU (`--gpus all`) |
| `--no-joystick` | Do not share `/dev/input` |
| `--headless` | No Gazebo window |
| `--help` | Show the options |

Simulation options (passed to `docker/simulation.py`):

| Option | Default | Description |
| --- | --- | --- |
| `--world pool.world\|ocean.world` | `pool.world` | World |
| `--odometry-source ground_truth\|vision` | `ground_truth` | Odometry sent to ArduSub |
| `--slam` | off | RTAB-Map SLAM (forces `vision`) |
| `--pilot` | off | Start `realjoy_node` and the gamepad driver |
| `--no-gamepad` | off | With `--pilot`, skip the `joy` driver (keyboard via the app only) |
| `--pilot-fps 30\|60` | `30` | Pilot camera rate |
| `--performance-profile …` | `balanced` | Camera profile (see 5.2) |
| `--instance N` | `0` | Offset all ports by 10×N to run a second simulation |
| `--log-dir DIR` | `~/mako-runs/<time>` | Session log folder |
| `--dry-run` | off | Print the commands without starting them |

Environment: `ROS_DOMAIN_ID` (42), `MAKO_IMAGE`, `MAKO_CONTAINER_NAME` (`mako-sim`),
`MAKO_DATA_DIR` (`~/mako-data`), `LIBGL_ALWAYS_SOFTWARE=1` (software rendering).

### 5.7 Mapping and RViz

Operation MX's SLAM option starts one mapper through
`mako_bringup → mako_vision/slam.launch.py → robot_mapping`. The team package was
imported from `ibrahim-amr`, commit `e33f072`, with provenance in
[robot_mapping/UPSTREAM.md](src/robot_mapping/UPSTREAM.md).

The desktop SLAM profile uses **640×360 RGB-D at 30 Hz**, **30 Hz pilot video**
and the **ZED onboard IMU at 100 Hz**. Camera odometry uses inertial rotation
hints; the mapper processes selected frames independently at a configured 6 Hz
ceiling. Delivered rates depend on GPU/CPU load. This is full 3D mapping, while
the default RViz view shows its top-down 2D occupancy projection.

With SITL and MAVROS running as in section 5.2:

```bash
ROS_DOMAIN_ID=42 ros2 launch mako_bringup simulation.launch.py \
  odometry_source:=vision slam:=true configure_ardusub:=false \
  camera_width:=640 camera_height:=360 camera_fps:=30 pilot_fps:=30 \
  slam_database_path:=$HOME/.ros/mako_slam.db
```

Docker `--gui` uses the desktop profile above; the CLI `--slam` supervisor
retains its selected performance profile. Use the explicit ROS camera arguments
above when reproducing the 30 Hz yaw regression.

Click **RViz** in the app to open the mapping view. The grid is published on
**`/rtabmap/map`**; **3D point cloud (optional)** displays `/rtabmap/cloud_map`.
Existing databases are not erased. The app creates a separate `rtabmap.db` in
each session directory. Direct launches reuse the specified database.

For standalone mapping, launch the simulation with `slam:=false`,
`odometry_source:=vision`, `publish_map_tf:=false`, and the camera settings above,
then launch `ros2 launch robot_mapping mapping.launch.py rviz:=true` in domain 42.
Run one mapper and one owner of `map → odom` at a time.

The validator alone owns `odom → base_link` in camera mode. Lost or rejected
tracking pauses pose updates even when pilot video remains clear; the app reports
this state. It does not substitute ground truth or repeat stale poses. See
[ZED odometry](src/mako_vision/ZED_VO.md) for calibration, dome clipping, runtime
setup and validation limits.

The source-branch screenshot, documentation and optional sample-map references
are retained. Files in `robot_mapping/pool_mapping_data` are **Git LFS pointers**;
obtain the actual objects from that branch before opening the saved example.
Live mapping does not require those examples. The upstream package's license
metadata still needs its author to choose a license.

### 5.8 Nav2 development

`mako_navigation` is optional and starts with `navigation:=true` in bringup, or:

```bash
ROS_DOMAIN_ID=42 ros2 launch mako_navigation navigation.launch.py
```

It consumes an occupancy map and existing TF; it does not start another
localization or map/odom transform publisher. A 0.5 m circular footprint,
conservative speed limits and sideways motion are configured. Unknown map cells
are not traversable. See its [package guide](src/mako_navigation/README.md).

**Nav2 does not yet drive the ROV.** Its final Twist output is isolated on
`/mako/navigation/cmd_vel`; a depth-holding adapter, command arbitration and
vehicle-mode checks belong in `mako_control` and are still required. This planar
stack does not plan depth or cave/overhang clearance. RTAB-Map's floor-inclusive
projection needs a free-water horizontal slice before navigation; use
`map_topic:=/your_navigation_map` to provide one.

---

## 6. ROS interfaces: topics, publishers and subscribers

All simulation nodes use `/clock` (`use_sim_time`). "Bridge" means `ros_gz_bridge
parameter_bridge` started by `robot_description/gazebo.launch.py`. Camera bridges are
**lazy** for pilot/auxiliary feeds; the matched RGB-D and IMU bridge stays active in vision mode.

### 6.1 Simulation core (`robot_description`)

| Topic | Type | Publisher | Subscribers | Notes |
| --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/Clock` | Bridge | every node | Simulation time |
| `/odometry/gz` | `nav_msgs/Odometry` | Bridge (Gazebo `/model/mako/odometry`) | `gz_odom_to_mavros` (ground truth), `odom_to_depth`, Operation MX | Ground-truth pose/twist, child frame `base_link` |
| `/imu/data` | `sensor_msgs/Imu` | Bridge (Gazebo `/mako/imu`) | none (for your nodes) | ArduSub uses its own IMU through the ArduPilot plugin |
| `/joint_states` | `sensor_msgs/JointState` | Bridge | `robot_state_publisher` | Thruster joints |
| `/model/mako/joint/t1_joint/cmd_thrust` … `t6_joint` | `std_msgs/Float64` | none by default | Bridge → Gazebo | Manual thruster tests; ArduSub drives thrusters through the plugin |
| `/robot_description` | `std_msgs/String` | `robot_state_publisher` | RViz | URDF |
| `/tf_static` | `tf2_msgs/TFMessage` | `robot_state_publisher`, `tf_sim_map_odom` (`map → odom`), `tf_odom_ned` (`odom → odom_ned`) | all | |
| `/tf` | `tf2_msgs/TFMessage` | `robot_state_publisher`; `ground_truth_tf_bridge` (`odom → base_link`, ground truth); `gz_odom_to_mavros` (`odom → base_link`, vision); RTAB-Map (`map → odom`, SLAM) | all | Only one owner of each edge, selected by the launch arguments |
| `/rov/depth` | `std_msgs/Float32` | `odom_to_depth` | `fly_transect_mission` | Metres below the surface, positive down |

### 6.2 Cameras (`robot_description` bridges)

| Topic | Type | Publisher | Subscribers |
| --- | --- | --- | --- |
| `/zed2i/zed_node/left/image_rect_color`, `…/left/camera_info` | `Image`, `CameraInfo` | `zed2i_bridge` | Operation MX (First person), RViz |
| `/zed2i/zed_node/right/image_rect_color`, `…/right/camera_info` | `Image`, `CameraInfo` | `zed2i_bridge` | RViz |
| `/zed2i/zed_node/rgb/image_rect_color`, `…/rgb/camera_info` | `Image`, `CameraInfo` | `zed2i_bridge` | (ZED-wrapper-style alias of left) |
| `/zed2i/zed_node/left/depth/image_raw`, `…/right/depth/image_raw` | `Image` (32FC1) | `zed2i_bridge` | your nodes |
| `/zed2i/zed_node/depth/depth_registered`, `…/depth/camera_info` | `Image`, `CameraInfo` | `zed2i_bridge` | your nodes |
| `/zed2i/sim_ros/left/points_raw`, `…/right/points_raw` | `PointCloud2` | `zed2i_bridge` | `cloud_frame_relay` |
| `/zed2i/zed_node/left/points`, `…/right/points`, `/zed2i/zed_node/point_cloud/cloud_registered` | `PointCloud2` | `cloud_frame_relay` | RViz, your nodes |
| `/zed2i/rgbd/left/image_rect_color`, `…/depth/image_raw`, `…/camera_info` | `Image`, `Image`, `CameraInfo` | `zed2i_rgbd_bridge`; simulated calibration corrected by `sim_rgbd_camera_info` | `zed_rgbd_odometry`, RTAB-Map |
| `/bottom_camera/image_raw`, `/bottom_camera/camera_info` | `Image`, `CameraInfo` | `zed2i_bridge` | Operation MX (bottom view), `fly_transect_mission` |
| `/third_person_camera/image_raw`, `/third_person_camera/camera_info` | `Image`, `CameraInfo` | `zed2i_bridge` | Operation MX (Third person) |

The simulated ZED onboard inertial stream is `/zed2i/zed_node/imu/data`
(`sensor_msgs/Imu`), bridged from `/zed2i/sim/imu` at 100 Hz. CameraInfo correction
preserves exact RGB-D timestamps and optical frames and applies only to Gazebo,
not the physical ZED wrapper's calibration.

### 6.3 Vision and mapping (`mako_vision`, `robot_mapping`)

| Topic / service | Type | Publisher / server | Subscribers / clients |
| --- | --- | --- | --- |
| `/zed2i/vo/odometry` | `nav_msgs/Odometry` | `zed_rgbd_odometry` | `gz_odom_to_mavros` (validation; mapper consumes the accepted output) |
| `/zed2i/vo/odom_info` | `rtabmap_msgs/OdomInfo` | `zed_rgbd_odometry` | diagnostics |
| `/zed_rgbd_odometry/reset_odom_to_pose` (service) | `rtabmap_msgs/ResetPose` | `zed_rgbd_odometry` | `gz_odom_to_mavros` (after a simulation reset) |
| `/rtabmap/map` | `nav_msgs/OccupancyGrid` | RTAB-Map | RViz, optional Nav2 |
| `/rtabmap/cloud_map`, `/rtabmap/octomap_occupied_space` | `sensor_msgs/PointCloud2` | RTAB-Map | optional 3D displays |
| `/zed/zed_node/pose` (real ROV) | `geometry_msgs/PoseStamped` | ZED ROS wrapper | `zed_to_mavros_pose` |
| `/mavros/vision_pose/pose` (real ROV) | `geometry_msgs/PoseStamped` | `zed_to_mavros_pose` | MAVROS → ArduSub |

### 6.4 Vehicle control (`mako_control`) and MAVROS

| Topic / service | Type | Publisher / server | Subscribers / clients |
| --- | --- | --- | --- |
| `/joy` | `sensor_msgs/Joy` | `game_controller_node` | `realjoy_node` |
| `/mako/autopilot/manual_control` | `mavros_msgs/ManualControl` | Operation MX keyboard pilot | `realjoy_node` (forwarded while sticks are centred and commands are fresher than 0.3 s) |
| `/mavros/manual_control/send` | `mavros_msgs/ManualControl` | `realjoy_node` | MAVROS → MAVLink MANUAL_CONTROL |
| `/mavros/odometry/out` | `nav_msgs/Odometry` | `gz_odom_to_mavros` | MAVROS → MAVLink ODOMETRY → EKF3 ExternalNav; RViz "Validated odometry" |
| `/mavros/state` | `mavros_msgs/State` | MAVROS | `realjoy_node`, Operation MX, `fly_transect_mission`, `local_waypoint_mission`, `autotune.py` |
| `/mavros/rc/out` | `mavros_msgs/RCOut` | MAVROS | Operation MX (thruster bars) |
| `/mavros/local_position/odom`, `/mavros/local_position/pose` | `Odometry`, `PoseStamped` | MAVROS | `fly_transect_mission`, `local_waypoint_mission` |
| `/mavros/setpoint_position/local` | `geometry_msgs/PoseStamped` | `fly_transect_mission`, `local_waypoint_mission` | MAVROS (GUIDED) |
| `/mavros/setpoint_velocity/cmd_vel` | `geometry_msgs/TwistStamped` | `fly_transect_mission` | MAVROS (GUIDED) |
| `/mavros/global_position/rel_alt` | `std_msgs/Float64` | MAVROS | `realjoy_node` (depth readout) |
| `/depth_cm` | `std_msgs/Float32` | `realjoy_node` | your nodes (depth in cm, keel offset applied) |
| `/mavros/statustext/recv` | `mavros_msgs/StatusText` | MAVROS | `autotune.py` |
| `/fly_transect/status`, `/fly_transect/vision_status` | `std_msgs/String` | `fly_transect_mission` | operator / your nodes |
| `/mavros/cmd/arming` (service) | `mavros_msgs/CommandBool` | MAVROS | `realjoy_node`, Operation MX |
| `/mavros/set_mode` (service) | `mavros_msgs/SetMode` | MAVROS | `realjoy_node`, Operation MX, missions, `autotune.py` |
| `/mavros/param/set`, `/mavros/param/get_parameters`, `/mavros/param/pull` (services) | MAVROS param | MAVROS | `fix_ardusub_params.py`, `autotune.py` |
| `/fly_transect/enable` (service) | `std_srvs/SetBool` | `fly_transect_mission` | operator |
| `/set_zero_depth` (service) | `std_srvs/Trigger` | `realjoy_node` | `realjoy_node` (gamepad button), operator |

Nav2 publishes intermediate `/mako/navigation/cmd_vel_raw` and smoothed
`/mako/navigation/cmd_vel` (`geometry_msgs/Twist`). Neither is connected to MAVROS.

### 6.5 TF tree

```text
map ─(static, or RTAB-Map with SLAM)─► odom ─(ground truth or VO relay)─► base_link ─► rov_base_link
                                        └─(static)─► odom_ned               ├─► imu_link, imu_ros_link, bar30_link
                                                                            ├─► t1_link … t6_link (thrusters)
                                                                            ├─► zed2i_camera_link ─► zed2i_{left,right}_camera_frame[_optical]
                                                                            ├─► bottom_camera_link ─► bottom_camera_optical_frame
                                                                            └─► third_person_camera_link ─► third_person_camera_optical_frame
```

Details: [src/robot_description/TF2_MODEL.md](src/robot_description/TF2_MODEL.md).

### 6.6 Network ports (not ROS)

| Port | Between | Purpose |
| --- | --- | --- |
| UDP 9002 / 9003 | Gazebo ArduPilot plugin ↔ ArduSub SITL | Motor outputs / vehicle state (JSON) |
| UDP 14550 | SITL → QGroundControl | Ground station |
| UDP 14551 | SITL → MAVROS | MAVLink for ROS |
| TCP 5760 | SITL | Serial 0 (MAVProxy) |

A second simulation (`--instance N`) shifts each port by 10×N.

---

## 7. Testing

Install optional imported-package lint tools before running the complete suite:

```bash
sudo apt install ros-humble-ament-flake8 ros-humble-ament-pep257 ros-humble-ament-copyright
```

```bash
source install/setup.bash
colcon test --base-paths src && colcon test-result --verbose          # package unit tests
python3 -m unittest discover -s gui/tests -q         # Operation MX tests (offscreen: QT_QPA_PLATFORM=offscreen)
python3 -m unittest docker/test_setup.py             # Docker supervisor
```

Live checks (start their own isolated SITL/Gazebo on other ports and domains):

| Script | Checks |
| --- | --- |
| `python3 src/mako_control/test/check_joystick.py` | `realjoy_node` against fake MAVROS: bounds, tuning, timeouts, arming, autopilot forwarding |
| `python3 src/mako_control/test/check_control_modes.py [--odometry-source vision]` | STABILIZE and ALT_HOLD in the full simulation |
| `ROS_DOMAIN_ID=158 python3 src/mako_control/test/check_odometry_runtime.py` | Vision relay runtime, validated odometry and TF startup |
| `python3 src/mako_control/test/check_autotune.py` | AUTOTUNE client (patched firmware) |
| `python3 src/mako_vision/test/check_zed_vo.py` | RGB-D + IMU odometry, physical motion, validated TF, fast yaw and reset into MAVROS ExternalNav |
| `python3 src/robot_description/test/check_rgbd_headings.py` | Valid depth across full yaw headings with the dome retained |
| `ROS_DOMAIN_ID=159 python3 src/robot_mapping/test/check_mapping.py` | Synthetic RGB-D input produces a nonempty 3D map |
| `ROS_DOMAIN_ID=157 python3 src/mako_navigation/test/check_planner.py` | Nav2 lifecycle, planned path and isolated command topics |
| `python3 src/robot_description/test/check_gazebo_reset.py` | World reset keeps the ROV and buoyancy |
| `python3 src/robot_description/test/check_search_survey.py [--render]` | Ocean search-and-survey cave collisions |
| `python3 gui/tests/check_application.py` | Operation MX start/reset/stop with screenshots |

Extended yaw regression with SLAM:

```bash
VO_TEST_WIDTH=640 VO_TEST_HEIGHT=360 VO_TEST_FPS=30 PILOT_TEST_FPS=30 \
VO_TEST_DEEP_YAW=1 VO_TEST_YAW_SECONDS=15 VO_TEST_SLAM=1 \
python3 src/mako_vision/test/check_zed_vo.py
```

Local validation on the development laptop: six packages build; 55 checks in the
five CMake packages and 29 desktop tests pass. The imported mapping package's
optional ROS lint suite needs the tools above and was not completed on this host;
its live RGB-D map test passed. The extended physical test reached about 1.46 rad/s
(~84°/s) at 2.1 m depth for 15 seconds with fresh validated TF, a live occupancy
grid and about 0.11 m maximum accepted position error. Both pilot feeds delivered
30 Hz and reset recovery passed. These short simulation measurements do not
validate long-duration drift, autonomous control or real-water performance.
The revised Docker image still needs a fresh build on a host with enough storage.

---

## 8. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Unable to locate package ros-humble-…` | Install `ros2-apt-source` (section 3.2), then `sudo apt update`. In Docker, `./docker/build.sh --rebuild` pulls a fresh base image |
| `Port 9002 is busy` | A Gazebo server is still running (it shows up as `ruby`): `pkill -f "gz sim"`, or `sudo ss -lunp \| grep 9002` then `kill -9 <pid>` |
| New models or worlds missing | Rebuild (`colcon build --symlink-install --base-paths src`) and make sure only this workspace is sourced (`ros2 pkg prefix robot_description`) |
| Operation MX uses an old simulation | Start it with `gui/run_mako_gui.sh` from this repository; unset `MAKO_WORKSPACE` if it points elsewhere |
| Operation MX closes at once ("already open") | `pkill -f rov_gui_gst.py` |
| Keyboard pilot on but the ROV does not move | Arm first; rebuild so `realjoy_node` comes from `mako_control`; restart the simulation |
| `Package 'mako_bringup' not found` | `source install/setup.bash` in that terminal |
| Gazebo window does not open (Docker) | Check `DISPLAY`, `/tmp/.X11-unix` and `xauth`; or use `--headless` |
| Black or slow camera images | Use a GPU (`--nvidia`), a lighter `performance_profile`, or `LIBGL_ALWAYS_SOFTWARE=1` as a last resort |
| MAVROS exits immediately | The EGM96 geoid is missing: `sudo bash install_geographiclib_datasets.sh` (native) or `./docker/run.sh --doctor` |
| Video is clear but RViz robot freezes during yaw | Check the app tracking status, ZED IMU and 30 Hz RGB-D settings. Pull, rebuild and fully restart the app to load the current model/calibration. The validator rejects bad poses; reset the session if tracking does not recover |
| SLAM or vision launch cannot find RTAB-Map / rtabmap_msgs | Install ROS Humble RTAB-Map dependencies or set MAKO_VO_PREFIX to a complete bundled runtime; source the rebuilt workspace |
| Grid view receives no map | Use `/rtabmap/map` with Reliable / Transient Local QoS; start mapping and establish valid camera tracking first |
| `rosdep` wants to install `ros-humble-ros-gz-*` | Use the `--skip-keys` line from section 3.7; keep `ros-humble-ros-gzharmonic` |

---

## 9. Contributing

* Branch from `main` (`git checkout -b yourname/feature`), commit, push and open a pull
  request into `main`. Do not commit `build/`, `install/`, `log/` or `gui/runs/`.
* Put code in the package that owns it: model/world → `robot_description`, anything
  that commands the vehicle → `mako_control`, camera odometry/detectors → `mako_vision`, mapping → `robot_mapping`,
  Nav2 configuration → `mako_navigation`, launch combinations → `mako_bringup`,
  pilot UI → `gui/`.
* Run the tests in section 7 before opening the pull request.
* Operation MX desktop releases are tagged `vX.Y.Z` and built by
  `.github/workflows/desktop-release.yml` ([gui/UPDATES.md](gui/UPDATES.md)).

---

## 10. Known issues

* `zed_to_mavros_pose.py` (real ROV) also publishes on `/mavros/odometry/in`, which is
  MAVROS's own FCU-to-ROS topic. ExternalNav input belongs on `/mavros/odometry/out`;
  check this before flying with it.
* Visual odometry is not full SLAM; loop closure and relocalisation need `slam:=true`.
* The Docker setup targets Linux. Windows/macOS Docker Desktop GUI and device forwarding
  are not covered.

---

## 11. Upstream projects

[ROS 2 Humble](https://docs.ros.org/en/humble/) ·
[Gazebo Harmonic](https://gazebosim.org/docs/harmonic/) ·
[ArduPilot / ArduSub](https://github.com/ArduPilot/ardupilot) ·
[ArduPilot Gazebo plugin](https://github.com/ArduPilot/ardupilot_gazebo) ·
[MAVROS](https://github.com/mavlink/mavros) ·
[RTAB-Map ROS](https://github.com/introlab/rtabmap_ros) ·
[Stereolabs ZED ROS 2 wrapper](https://github.com/stereolabs/zed-ros2-wrapper) (topic/frame conventions) ·
[BlueROV2 Gazebo model](https://github.com/clydemcqueen/bluerov2_gz) (appearance references)

Upstream components keep their own licenses; check per-asset README files before
redistributing meshes, textures or team artwork.
