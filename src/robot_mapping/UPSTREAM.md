# Imported team package

Source: `ibrahim-amr`, commit `e33f0725f8c95f3715cfb1e970ee42a760d6cabb`,
path `rov_ws/src/robot_mapping`, imported into this workspace's `src/`.
Ibrahim's documentation, screenshot, RViz configuration and sample map references
are retained. The upstream package declares its license as TODO; that declaration
has not been replaced with an assumed license.

Integration changes: matching RGB-D topics, validated odometry, configurable
non-destructive database path, headless launch support, shared RTAB-Map runtime
resolution and bounded real-time mapping parameters. `mako_vision/slam.launch.py`
delegates here, so enabling SLAM starts one mapper. No second VO estimator or TF
publisher is introduced. Control remains in mako_control; navigation remains in
mako_navigation.

The `pool_mapping_data` files are Git LFS pointers from the source branch. They
are optional offline examples, not required for live mapping. Obtain their actual
content from that branch with Git LFS before attempting to open them; this import
does not present the pointer text as a usable database or point cloud.
