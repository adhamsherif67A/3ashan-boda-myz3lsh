# Fish model and retained fixes

The original CAD export is in `reference/fifish_urdf`; the adapted Gazebo description is `src/robot_description/urdf/robot_description.urdf`. CAD thruster poses, axes, meshes, masses and inertia tensors are retained. The main-body inertial origin was trimmed about 4.5 mm upward and less than 0.1 mm laterally to align the combined COM with the forward-thruster plane. This is simulation ballast trim, not a measurement of the real vehicle.

## Allocation and physics

ArduSub retains CUSTOM / FRAME_CONFIG=7. `firmware/custom_frame_original.cpp` is the supplied matrix; `firmware/custom_frame_cad.cpp` is the active allocation derived from the six CAD thrust axes and their moment arms about the combined COM. M1–M6 map directly to Gazebo t1–t6. The wrench matrix has rank six. Full values, coordinate conventions and trim calculations are in `firmware/allocation.json`.

Combined mass is approximately 7.052 kg. Drag acts through the combined COM. A separate sealed primitive supplies neutral displacement in 998 kg/m³ water, with COB 15 mm above COM. CAD contact meshes are not treated as sealed buoyant volumes. Thrust/drag coefficients, the 51.5 N thruster limits and virtual payload derive from the MarineXperts simulation baseline and are not physical Fifish calibration.

The inherited 0.5 N thruster deadband was reduced to 0.05 N so small allocation corrections reach the model. CUSTOM PWM offsets round symmetrically around 1500. MANUAL updates throttle bookkeeping before a transition to ALT_HOLD, preventing initialization from a stale disarmed throttle value. Depth tuning and climb/acceleration limits are in `src/mako_control/config/ardusub_external_nav.parm`.

The temporary body-rate ALT_HOLD patch, automatic mode switching on roll/pitch, D-pad return and turn-history recording were removed. The active restored controls are described in the root README. STABILIZE retains its normal attitude limits; depth hold is selected explicitly.

## Cameras and mapping

The project includes pilot, bottom and third-person cameras, ZED RGB-D/IMU visual navigation and optional SLAM. HD mapping retains undecimated keyframes, PNG color and RVL depth compression. RViz uses 5 mm MapCloud voxels / 6 mm squares, and the occupancy grid uses 2 cm cells. These are display/sampling sizes, not a localization-accuracy guarantee.

Physical motion tests use ground-truth navigation only as estimator input and measurement. Motion comes from SITL PWM through Gazebo thruster forces; no pose teleporting drives the model. Separate visual-navigation tests use camera/IMU odometry and live SLAM. Saved results are bounded simulation cases.

## Regeneration

Inside the Fish container, after deliberate CAD edits:

```bash
python3 tools/generate_fish_model.py
python3 tools/calibrate_allocation.py
colcon build --symlink-install --base-paths src --parallel-workers 3
python3 tools/build_fish_firmware.py
```

The generated executable is Linux SITL, not a Pixhawk firmware image. Original host ArduPilot and previous Pixhawk/QGroundControl artifacts are separate from this runtime.

## Saved validation

- [Restored controls](validation/restored-controls-summary.json): six physical directions, R1 switching, stale-input neutralization, no D-pad mode action and no automatic mode changes; disarmed afterward.
- [Visual navigation/depth](validation/depth-final-vision.json): depth transition, forward motion and climb with live visual navigation and SLAM.
- [Depth summary](validation/depth-stability-summary.json): measured scope of the COM and depth corrections.

Source compilation and targeted tests for the published snapshot are described in the root README.
