# MarineXperts — Mako ROV Simulation

<img src="src/robot_description/worlds/assets/team_logo/team_logo.png" alt="MarineXperts team logo" width="110">

ROS 2 Humble, Gazebo Harmonic and ArduSub SITL simulation for the MarineXperts Mako
ROV. Train pilots in the team pool or ocean course, inspect camera/depth data,
and develop underwater perception and visual odometry.

**Clone the `boda` branch.** Build the Docker image once, then start the complete
simulation with one command. ROS, Gazebo, ArduPilot and MAVROS run inside
the container.

## Features

### Vehicle and physics

- Six Blue Robotics T200 thrusters in the ArduSub **VECTORED** configuration.
- Black/charcoal body, colored thrusters, acrylic camera dome and landing-frame
  collision geometry for contact with the floor, walls and obstacles.
- Freshwater neutral buoyancy, aligned mass/buoyancy centers, hydrodynamic drag,
  rotational damping and gentle pool/ocean surface disturbances.
- Corrected thruster allocation and a preserved FRD IMU link for consistent
  Gazebo/ArduSub attitude feedback. STABILIZE and ALT_HOLD have live regression
  checks after yaw and vertical inputs.
- Startup motor settings are loaded **before** the first pilot command:
  `MOT_PWM_MIN=1240`, `MOT_PWM_MAX=1760`, neutral PWM **1500**.

- Gazebo reset handling restores the model and buoyancy configuration.

### Worlds

| World | Environment | Tasks and obstacles |
| --- | --- | --- |
| `pool.world` | 14 × 12 m swimming pool, 3 m deep, tiled floor/walls and one open wall | Mirrored PVC coral garden with eight red targets, colored fly transect, crabs |
| `ocean.world` | 18 × 16 m seabed, 4 m water depth, pale sand relief and reef/ship scenery | Shipwreck, broken submerged pipe, rock arch, and a far-side search cave with three survey targets |

Both worlds contain the team logo below the ROV spawn. World assets and textures
are installed locally with the package; the courses do not require Fuel downloads.
The ROV starts near `(0, 0, -1)` in Gazebo's ENU coordinates.

The ocean search-and-survey task asks pilots to find a ship's bell, an Admiralty
anchor and a four-blade propeller using the ZED or bottom RGB camera. Give pilots
the [real-photo briefing](src/robot_description/designs/search_survey/briefing/pilot_photo_briefing.pdf);
it contains no target positions. The [mission guide](src/robot_description/designs/search_survey/README.md)
contains the instructor map, STL paths and regeneration instructions.

### Cameras, TF and navigation

Experimental onboard ArduSub AUTOTUNE is available through MAVROS after
applying the [firmware port](firmware/ardusub-autotune/README.md). It defaults to
yaw tuning and includes depth hold and original-gain restoration on abort.
The port builds for SITL and FMUv3; real-water validation is still required.

- Simulated ZED 2i left/right RGB eyes, registered depth, camera calibration topics
  and aligned point clouds, using ROS topic names familiar from the ZED wrapper.
- Pilot RGB defaults to **1280 × 720 at 30 Hz**; 60 Hz is optional. Depth and
  bottom-camera processing default to 15 Hz. Actual rates depend on GPU/load.
- Downward RGB camera inside the dome and a rear-following third-person RGB camera.
- Bounded, lazy image bridges reduce traffic when a feed is unused.
- Connected TF tree with body, thruster, sensor and optical frames; simulation
  nodes use `/clock`.
- Ground-truth odometry for deterministic testing, or ZED RGB-D visual odometry
  through RTAB-Map. Validated odometry is sent to ArduSub through MAVROS ExternalNav.
- **Visual odometry is not full SLAM.** Map building, loop closure and global
  relocalization are not enabled by this workflow.

## 1. Host requirements

Supported setup: **Linux x86-64 with Docker Engine**. Ubuntu 22.04/24.04 with
an X11 or XWayland session is the intended desktop setup. Host ROS/Gazebo/ArduPilot
installations are unnecessary. Windows/macOS Docker Desktop GUI and device
forwarding are not covered by these instructions.

Recommended resources:

- 16 GB RAM; build parallelism defaults to two jobs to limit memory use.
- At least **20 GiB free in Docker storage** for the first build; 40 GiB provides
  more room for source trees, layers and subsequent rebuilds.
- A working graphics device for smooth camera rendering. Intel/AMD `/dev/dri`
  devices are passed through by the run helper. NVIDIA requires the host driver
  and NVIDIA Container Toolkit.
- Internet access for the first image build: apt packages, Python packages,
  ArduPilot and its submodules are downloaded then.

Check Docker and Git:

```bash
docker --version
docker info
git --version
```

If Docker is missing, follow the [Docker Engine installation guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
For a permission error, follow Docker's [Linux post-installation instructions](https://docs.docker.com/engine/install/linux-postinstall/),
then log out and back in before continuing. Docker must be running and accessible
to your current user.

For GUI display forwarding, check `xauth` and install it only if missing:

```bash
command -v xauth >/dev/null || { sudo apt-get update && sudo apt-get install -y xauth; }
```

For NVIDIA, follow the [NVIDIA Container Toolkit installation/configuration guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
Confirm that `nvidia-smi` works on the host. A container cannot install or replace
its host's graphics driver.

## 2. Clone the correct branch

```bash
git clone --branch boda --single-branch \
  https://github.com/adhamsherif67A/3ashan-boda-myz3lsh.git \
  MarineXperts-Season-2027
cd MarineXperts-Season-2027
git branch --show-current
```

The last command must print `boda`. Authenticate with GitHub if access to the
repository is restricted.

## 3. Build the environment once

```bash
./docker/build.sh
```

The image tag is **`marinexperts/mako:boda`**. The build helper matches the
container user UID/GID to your Linux account for device and shared-memory access. The first build downloads and
compiles dependencies, so its duration depends on your network and machine.
Once successful, no additional package installation is needed inside the container.

What the Docker build prepares:

1. Ubuntu 22.04 / ROS 2 Humble base.
2. Gazebo Harmonic and the **Harmonic-compatible** Humble `ros_gz` packages.
3. MAVROS, RViz, RTAB-Map odometry and ROS build tools.
4. The GeographicLib EGM96 geoid required by MAVROS.
5. Pinned ArduPilot/ArduSub and ArduPilot Gazebo plugin source builds.
6. This repository's vehicle, worlds, custom water/reset plugin.

Installation is checked before it runs: the apt helper queries `dpkg`, the Python
helper checks pinned package versions and the dataset installer checks its geoid
file. Already installed items are skipped. Docker layers are reused on subsequent
builds. These checks concern packages **inside the image**: Docker does not reuse
or inspect unrelated ROS installations on your host.

`./docker/build.sh` also skips an already-existing image. After source changes,
explicitly rebuild it:

```bash
./docker/build.sh --rebuild
# Optional: choose source-build parallelism.
./docker/build.sh --rebuild --jobs 4
```

`BUILD_JOBS` controls both the ArduPilot/plugin builds and workspace compilation.
The Dockerfile pins upstream source revisions; apt packages/base-image updates
are not locked byte-for-byte. Avoid installing the normal Humble Fortress
`ros-humble-ros-gz` packages alongside the Harmonic bridge. See the
[Gazebo Humble/Harmonic installation guidance](https://gazebosim.org/docs/harmonic/ros_installation/).

## 4. Check the image

```bash
docker run --rm marinexperts/mako:boda doctor
```

The check verifies ROS packages, Python imports, ArduSub, the Gazebo plugin and
its linked libraries, the geoid dataset and both worlds. It should finish with
`RESULT: ready`. Missing items cause a nonzero exit; runtime does not silently
install packages.

## 5. Start the simulation

### Team pool with the Gazebo GUI

```bash
./docker/run.sh --world pool.world
```

This starts **ArduSub SITL + MAVProxy + MAVROS + Gazebo + ROS sensor/TF bridges**.
The wrapper handles display cookies, host networking/shared memory and available `/dev/dri`
devices. It does not require a broad `xhost +` grant.

### Ocean course

```bash
./docker/run.sh --world ocean.world
```

### NVIDIA GPU

```bash
./docker/run.sh --nvidia --world pool.world
```

### Headless server, with cameras still rendered

```bash
./docker/run.sh --headless --world pool.world
# Optional software rendering for a machine without an accessible graphics device.
LIBGL_ALWAYS_SOFTWARE=1 ./docker/run.sh --headless --world pool.world
```

Headless removes the Gazebo GUI; it does not disable RGB/depth sensors. Software
rendering can be much slower than a GPU.

### ZED-only visual odometry

```bash
./docker/run.sh --world pool.world --odometry-source vision
```

Use the default `ground_truth` source for repeatable physics/control debugging.
Use `vision` to test camera-based pose estimation; it does not consume Gazebo
pose as an estimator input. Textured, visible scenes and sufficient image rate
are necessary for visual tracking.

In vision mode, the validation relay owns `odom -> base_link` and forwards
only accepted poses to ArduSub. It rejects position/orientation jumps using
limits of 2 m/s and 3 rad/s, in addition to timestamp and covariance checks.
The comparison window is capped at 0.2 seconds so a tracking outage cannot
authorize a larger jump. Rapid yaw over repetitive pool tiles can still lose
tracking; rejected poses do not update TF or ExternalNav. If tracking cannot
recover, reset the simulation to reset its pose and the visual estimator together.

### Optional 60 Hz pilot feed

```bash
./docker/run.sh --nvidia --pilot-fps 60
```

This changes the pilot RGB rate. Depth/odometry processing remains independently
configured; setting 60 does not guarantee 60 delivered frames on every GPU.

## 6. Inspect ROS topics

Open another terminal while `mako-sim` is running. Execute commands through the
image entrypoint so ROS/workspace setup is sourced:

```bash
docker exec -it mako-sim /bin/bash /entrypoint.sh bash
```

Inside that shell:

```bash
ros2 topic list
ros2 topic echo /mavros/state --once
ros2 topic echo /mavros/rc/out --once
ros2 topic hz /zed2i/zed_node/left/image_rect_color
ros2 run robot_description check_sim_tf.py
```

Useful topics:

| Topic | Data |
| --- | --- |
| `/clock` | Gazebo simulation time |
| `/tf`, `/tf_static`, `/joint_states` | Robot and sensor transforms |
| `/odometry/gz` | Gazebo reference pose/twist |
| `/zed2i/zed_node/left/image_rect_color` | First-person RGB |
| `/zed2i/zed_node/right/image_rect_color` | Right-eye RGB |
| `/zed2i/zed_node/left/depth/image_raw` | Left registered depth |
| `/zed2i/zed_node/point_cloud/cloud_registered` | Aligned point cloud |
| `/bottom_camera/image_raw` | Downward RGB |
| `/third_person_camera/image_raw` | Rear-following RGB |
| `/zed2i/vo/odometry` | Camera-based odometry, when `vision` is enabled |
| `/mavros/state` | Connection, actual mode and arming state |
| `/mavros/manual_control/send` | Pilot movement commands |
| `/mavros/odometry/out` | Selected ExternalNav stream to ArduSub |

Camera bridges are lazy: subscribing activates the relevant feeds. Use simulated
time for your own ROS nodes and RViz. With GUI forwarding enabled, launch RViz from this shell, for
example `ros2 launch robot_description view_tf.launch.py`.

The model viewer includes a **Validated odometry** display on
`/mavros/odometry/out`, with fixed frame `odom` and Best Effort subscription
QoS. This works with either selected odometry source. Raw visual odometry
can contain invalid tracking-loss poses and should not be used for this display.

The default ROS domain is **42**. To inspect from host ROS tools, source your ROS
installation and set `ROS_DOMAIN_ID=42` and `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`.
Set `ROS_DOMAIN_ID` before `docker/run.sh` to select another domain.

For the default simulation domain, open the host viewer with:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ROS_DOMAIN_ID=42 RMW_IMPLEMENTATION=rmw_fastrtps_cpp ros2 launch robot_description view_tf.launch.py
```

## 7. Stop, reset and retain logs

Press **Ctrl+C** in the launch terminal or run:

```bash
docker stop mako-sim
```

The supervisor stops its process groups; the run helper uses `--rm`, so the
container is removed after shutdown. A complete reset is stop followed by the
same `docker/run.sh` command. This restarts SITL, MAVROS and sensors.
The Gazebo reset button resets world state, but does not restart the flight
controller or every ROS process.

The supervisor prints its session log directory inside the container, under
`/home/sim/mako-runs/`. ROS/MAVProxy files are stored there; process output appears
in the Docker terminal. Before stopping, save logs to the host:

```bash
docker logs mako-sim > simulation.log 2>&1
docker cp mako-sim:/home/sim/mako-runs ./simulation-runs
```

## Troubleshooting

| Symptom | Check / action |
| --- | --- |
| Image already exists but changes are absent | Run `./docker/build.sh --rebuild`. |
| Build refuses to start / disk fills | Free Docker storage; the helper requires 20 GiB. It never prunes images automatically. |
| Docker socket permission denied | Finish Docker's post-installation setup and log in again. |
| GUI cannot open | Check `DISPLAY`, `/tmp/.X11-unix` and `xauth`; try `--headless`. |
| NVIDIA runtime error | Install/configure the host NVIDIA Container Toolkit; verify the host driver. |
| Black/slow images | Check GPU access, subscribe to the image topic, reduce rendering load or pilot rate. Software EGL is a fallback. |
| MAVROS exits immediately | Run `doctor`; confirm the EGM96 geoid exists. |
| Port is occupied | Stop another SITL/MAVROS instance. Default ports are 9002/9003, 5760 and 14550/14551. |
| MAVROS invisible from host terminal | Use the same ROS domain and middleware; avoid a second MAVROS instance. |
| Movement changes direction after startup | Rebuild the image; the complete parameter file must load before SITL starts. The container disables delayed parameter rewriting. |
| ALT_HOLD/STABILIZE spins or flips | Check the corrected URDF motor mapping, preserved IMU link and startup motor directions. |
| TF old-data warning after reset | Restart your viewer with `use_sim_time=true`; use a full session restart when estimator time/history must reset. |
| Visual odometry loses tracking | Inspect `/zed2i/vo/odom_info`, textures, depth visibility and image rate. Use ground truth to separate perception from physics problems. |

The mounted Bar30 position currently uses a Gazebo atmospheric `air_pressure`
sensor, **not a calibrated hydrostatic depth sensor**. ArduSub depth estimation
uses the selected ExternalNav source. Water motion is a lightweight disturbance
model, not a full computational fluid dynamics solver. The simulated ZED topics
are produced by Gazebo/ROS bridges; the physical ZED SDK/wrapper is not required.

## Development and checks

The container has the source and build tools. For a development shell:

```bash
docker run --rm -it marinexperts/mako:boda bash
```

Sources are under `/opt/mako_ws/src`; ArduPilot and its plugin are under
`/opt/ardupilot` and `/opt/ardupilot_gazebo`. Modify host sources and rebuild the
image to distribute changes. Source-build parallelism can be limited with
`MAKEFLAGS=-j2` and `./docker/build.sh --jobs 2`.

Useful verification commands inside the container:

```bash
python3 -m unittest discover -s /opt/mako_ws/src/robot_description/test -q
python3 /opt/mako_ws/docker/simulation.py --dry-run --headless
python3 -m unittest discover -s /opt/mako_ws/docker -p "test_*.py" -q
```

Validation status: model/frame checks and simulation setup tests have passed locally. Container scripts have syntax/command checks and a cached-image smoke test
with a read-only known-working Humble/Harmonic overlay verified connected MAVROS
and 1280×720 pilot/bottom images. This is runtime validation, not a fresh-image
build. A fresh build
of the complete replacement Dockerfile still needs validation on a machine with
sufficient Docker storage; it is not claimed as a certified clean-image build.

## Repository structure

```text
Dockerfile                         Complete simulation environment
entrypoint.sh                      Sources ROS/workspace and selects a command
docker/
  build.sh                         Build once / explicitly rebuild
  run.sh                           Display and GPU forwarding
  simulation.py                    SITL + MAVROS + Gazebo supervisor
  doctor.py                        Read-only installed-environment check
  install-apt.sh                   Install only missing apt packages
  install-python.py                Check/install pinned Python packages
commands.txt                       Base SITL and MAVROS commands
src/robot_description/
  urdf/                            ROV, thrusters, sensors and ArduPilot mapping
  worlds/                          Pool, ocean and local task assets
  config/                          Bridges, odometry and startup parameters
  launch/                          Gazebo, TF/RViz and visual odometry
  scripts/                         Cloud/pose relays and simulation diagnostics
  test/                            Frame, physics/configuration and live checks
```

Generated `build/`, `install/`, logs and machine-specific runtime files are not
needed in a clean clone. `.dockerignore` excludes them from the image context.

## Upstream projects and assets

- [ROS 2 Humble](https://docs.ros.org/en/humble/)
- [Gazebo Harmonic](https://gazebosim.org/docs/harmonic/)
- [ArduPilot / ArduSub](https://github.com/ArduPilot/ardupilot)
- [ArduPilot Gazebo plugin](https://github.com/ArduPilot/ardupilot_gazebo)
- [MAVROS](https://github.com/mavlink/mavros)
- [RTAB-Map ROS](https://github.com/introlab/rtabmap_ros)
- [Stereolabs ZED ROS 2 wrapper](https://github.com/stereolabs/zed-ros2-wrapper), for topic/frame conventions
- [BlueROV2 Gazebo model](https://github.com/clydemcqueen/bluerov2_gz), for appearance references

Upstream components retain their own licenses. Check the per-asset README files
and package metadata before redistributing meshes, textures or team artwork.

## Native setup (without Docker) and Operation MX

This section describes running the same simulation directly on Ubuntu 22.04,
without the Docker image, and starting it from the Operation MX application.
Everything above still applies to the Docker workflow.

### Prerequisites

| Component | How to install | Expected location |
| --- | --- | --- |
| Ubuntu 22.04 + ROS 2 Humble desktop | [ROS 2 Humble install guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html), plus `sudo apt install python3-colcon-common-extensions python3-rosdep` (then `sudo rosdep init && rosdep update`) | `/opt/ros/humble` |
| Gazebo Harmonic + ROS bridge | Add the [OSRF Gazebo apt repository](https://gazebosim.org/docs/harmonic/install_ubuntu), then `sudo apt install gz-harmonic ros-humble-ros-gzharmonic` | system |
| Simulation dependencies | `sudo apt install ros-humble-xacro ros-humble-robot-state-publisher ros-humble-joint-state-publisher-gui ros-humble-rviz2 ros-humble-tf2-ros ros-humble-rtabmap-ros ros-humble-joy python3-pyqt5 python3-numpy python3-psutil` | system |
| MAVROS | If `apt install ros-humble-mavros ros-humble-mavros-extras` is unavailable, build MAVROS from source in its own workspace, and install the GeographicLib datasets (`install_geographiclib_datasets.sh` in this repository) | `~/mavros_ws` |
| ArduPilot SITL (ArduSub) | Clone [ArduPilot](https://github.com/ArduPilot/ardupilot), run `Tools/environment_install/install-prereqs-ubuntu.sh`, then `./waf configure --board sitl && ./waf sub`. The Dockerfile pins the tested revision in `ARDUPILOT_REF`. | `~/ardupilot` |
| ArduPilot Gazebo plugin | Clone [ardupilot_gazebo](https://github.com/ArduPilot/ardupilot_gazebo) and build it with `GZ_VERSION=harmonic` (`cmake -S . -B build && cmake --build build`) | `~/ardupilot/ardupilot_gazebo/build` |
| `realjoy_node` (pilot control) | Built from the `real_joy` package of the Software2026 workspace. Copy `gui/joystick_update/joystick.cpp` into `Software2026/src/real_joy/src/` and run `colcon build --packages-select real_joy` there. This version forwards Operation MX keyboard commands. | any folder, set by `MAKO_SOFTWARE_WORKSPACE` |
| QGroundControl (optional) | [QGroundControl AppImage](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html) | any folder; Operation MX asks for it once |

`gazebo.launch.py` finds the plugin through `MAKO_ARDUPILOT_GAZEBO` (default
`~/ardupilot/ardupilot_gazebo`). Operation MX finds ArduPilot through
`MAKO_ARDUPILOT` (default `~/ardupilot`).

### Build this repository

Use a terminal that does **not** source another copy of `robot_description`,
such as an older `~/mako_ws`. Otherwise Gazebo can load old worlds and models.

```bash
source /opt/ros/humble/setup.bash
source ~/mavros_ws/install/setup.bash
cd ~/MarineXperts-main                  # this repository
colcon build --symlink-install --base-paths src
```

Run `colcon build` again after every `git pull`. Gazebo loads worlds and models
from `install/`, so new or changed assets appear only after a rebuild.

### Environment

Add these lines to `~/.bashrc` once, then open a new terminal:

```bash
export MAKO_WORKSPACE=$HOME/MarineXperts-main                     # this repository (commands.txt + install/)
export MAKO_SOFTWARE_WORKSPACE=$HOME/MarineXperts-Boda/Software2026  # workspace with realjoy_node built
```

Check with `echo $MAKO_WORKSPACE`. If it is unset, Operation MX falls back to
`~/mako_ws`, and `echo $AMENT_PREFIX_PATH` must not list another
`robot_description`.

### Run with Operation MX

```bash
source /opt/ros/humble/setup.bash
cd ~/MarineXperts-main/gui && python3 rov_gui_gst.py
```

Choose **Team pool** or **Ocean · 4 m**, then **Start simulation**. The app starts
ArduSub SITL, MAVROS, headless Gazebo, the joystick driver and `realjoy_node`,
and saves each session's logs in `gui/runs/`. Start it from a terminal: the
desktop shortcut does not read `~/.bashrc`.

Pilot view controls:

| Control | Action |
| --- | --- |
| **F11** / **Full screen** | Toggle full screen. The app opens full screen; `--windowed` starts a normal window. |
| **H** / **Camera only** | Hide the side panels so the camera fills the window. |
| Drag the bottom view's top-left corner, or **[** / **]** | Resize the bottom-camera view. The size is remembered. |
| **MISSION** timer | Shown at the top of the camera view while the simulation runs. |
| **Keyboard pilot** | Fly without a gamepad: W/S forward/back, A/D sideways, Q/E or ←/→ turn, ↑/↓ up/down, hold Shift for full power. A gamepad stick has priority. |
| **V** / **C** / **R** | Change view, capture a frame, record the session. |

The ocean search-and-survey cave is on the sea floor about 4 m south of the
spawn point, with its opening facing the spawn. See
`src/robot_description/designs/search_survey/README.md`.

### Run manually (Gazebo window)

In each of three terminals:

```bash
source /opt/ros/humble/setup.bash
source ~/MarineXperts-main/install/setup.bash
export ROS_DOMAIN_ID=42
```

1. Gazebo: `ros2 launch robot_description gazebo.launch.py world:=ocean.world` (or `pool.world`)
2. ArduSub SITL, after Gazebo is open:
   ```bash
   cd ~/ardupilot
   Tools/autotest/sim_vehicle.py -v ArduSub -f vectored --model=JSON \
     -l 31.312000,30.067222,0,0 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551 \
     --add-param-file=$HOME/MarineXperts-main/src/robot_description/config/ardusub_external_nav.parm
   ```
3. MAVROS: `ros2 launch mavros apm.launch fcu_url:="udp://127.0.0.1:14551@"`

QGroundControl connects automatically on UDP 14550. Stop the manual session
with Ctrl+C in each terminal before starting Operation MX. Closing only the
Gazebo window can leave its server running.

### Native troubleshooting

| Symptom | Fix |
| --- | --- |
| `Port 9002 is busy` | A Gazebo server is still running (it shows as `ruby`). Find it with `sudo ss -lunp \| grep 9002`, then `kill -9 <pid>`, or run `pkill -f "gz sim"`. |
| New models or worlds missing in the app but present in a manual launch | Operation MX is using another workspace. Set `MAKO_WORKSPACE` to this repository, remove old `source ~/mako_ws/...` lines from `~/.bashrc`, open a new terminal and restart the app. |
| New assets missing everywhere after `git pull` | Rebuild with `colcon build --symlink-install --base-paths src`. |
| Operation MX closes immediately ("already open") | Another copy is running: `pkill -f rov_gui_gst.py`. |
| Keyboard pilot on but the ROV does not move | Rebuild `realjoy_node` with `gui/joystick_update/joystick.cpp`, then restart the simulation. |
| `Package 'robot_description' not found` | Source `~/MarineXperts-main/install/setup.bash` in that terminal. |
