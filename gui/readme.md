
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
