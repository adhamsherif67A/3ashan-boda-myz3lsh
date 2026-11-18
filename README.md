# Fish Omni Six — Rashwan simulation

Independent Fish ROV simulation using the MarineXperts Pool/Ocean scenes, water physics, cameras, ROS 2, ArduSub SITL, joystick control and RGB-D SLAM. This branch contains the current Fish project. It does not require a local copy of MarineXperts or a private Docker image.

## First-time setup

Validated on Ubuntu 22.04 with an NVIDIA GPU, Docker Engine, NVIDIA Container Toolkit, an X11/XWayland desktop and host `xauth`. Docker must be usable by your account. Building ROS/Gazebo and ArduPilot needs internet access and several GB of free disk space.

From this repository:

```bash
docker build --build-arg SIM_UID="$(id -u)" --build-arg SIM_GID="$(id -g)" -t fish-omni-six:local .
python3 tools/setup_container.py --build
./run-fish.sh
```

The image builds pinned ArduPilot and Gazebo-plugin revisions and applies the Fish CUSTOM mixer and the retained MANUAL-to-depth-hold correction. The setup command creates the independent `fish-omni-six` container, builds the bind-mounted ROS workspace and generates its simulation executable. Source changes persist in this repository; maps, recordings and settings go into ignored `data/`.

Normal launches only need `./run-fish.sh`. Select **Team pool** or **Ocean**, optionally enable **SLAM**, then click **Start simulation**. Use **RViz** for the live map. Visual navigation is the default; ground-truth navigation is available for physics diagnostics.

Optional desktop shortcut:

```bash
python3 tools/install_fish_desktop.py
```

The GPU/runtime setup is designed for NVIDIA Linux desktops. Other graphics configurations have not been validated. Run one Fish simulation at a time: ROS domain 73, SITL instance 12, JSON ports 9122/9123 and MAVLink outputs 24850/24851. A ground station can listen on UDP 24850. No Pixhawk hardware is needed or flashed.

## Controls

| Input | Action |
|---|---|
| Left stick up/down | Forward/backward |
| Left stick left/right | Lateral motion |
| Right stick left/right | Roll |
| Right stick up/down | Heave |
| Hold R1 + right stick up/down | Pitch |
| Release R1 | Return vertical stick to heave |
| Options/Start | Arm/disarm |
| Triangle | Depth-hold toggle |
| Square | Stabilize toggle |

Roll/pitch input preserves the selected flight mode. D-pad Up has no automatic return/leveling action. The temporary continuous-turn replay and automatic ALT_HOLD switching were removed. MANUAL uses direct attitude thrust; STABILIZE uses its normal attitude limits; select ALT_HOLD explicitly when required.

## Project contents

- `src/`: ROS packages, adapted CAD vehicle, pool/ocean scenes, hydrodynamics, simulated cameras, visual navigation and SLAM.
- `gui/`: Fish desktop pilot station and tests.
- `firmware/`: CUSTOM allocation, mass/force calculation, ArduSub source review copies and its upstream license. Linux SITL binaries are generated locally; these are not Pixhawk firmware images.
- `reference/`: supplied CAD URDF/meshes and the Marine model reference required to regenerate the adapted model.
- `tools/`: runtime setup, model/allocation generation, firmware build and physical simulation checks.
- `docs/`: physical-model assumptions and saved validation results.

The model retains the CAD thruster poses. Its allocation is derived from those poses, with the documented COM/buoyancy trim. Drag/thrust coefficients and simulated sensors are assumptions rather than calibration of a real Fifish. See [model and validation notes](docs/FISH_MODEL_AND_VALIDATION.md).

## Validation

The current local Fish runtime passed 74 targeted unit/geometry tests and all six physical motion directions through joystick → MAVROS → ArduSub → Gazebo. Tests also verified R1 switching, stale-input neutralization, D-pad Up doing nothing and roll/pitch retaining MANUAL mode. The vehicle was disarmed after testing. [Saved control results](docs/validation/restored-controls-summary.json) describe the tested configuration.

After setup, run the same targeted unit suite:

```bash
docker exec fish-omni-six bash -c 'source /opt/ros/humble/setup.bash; source /opt/mako_ws/install/setup.bash; cd /opt/mako_ws; python3 -m pytest -q gui/tests src/robot_description/test/test_fish_model.py src/robot_description/test/test_camera_calibration.py src/mako_control/test src/mako_vision/test'
```

The published source compiled all six ROS packages and rebuilt the Fish SITL in an isolated container using the prepared dependency image; all 74 targeted tests passed there. Three runtime-setup checks also passed (`python3 -m unittest discover -s tests`). A complete fresh Docker image build was not repeated during publication because the publishing machine had less than 1 GB free; the build recipe and setup wiring were checked separately. Historical notes may contain paths from the original development PC; use the relative commands in this README to run this checkout.

Generated builds, Docker images, local credentials/settings, recordings, simulator logs and map databases are not stored in Git. Each teammate builds their runtime and generates maps locally.
