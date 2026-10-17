Appearance meshes are disjoint connected-component subsets of ../center_body_link.STL. All original triangles are retained in their original CAD coordinates. Visuals only; original STL retained.

- body: frame and main enclosure.
- thruster_housings: six fixed T200 ducts/housings.
- motors: six fixed motor components.
- hardware: detached fasteners.
- dome: original front acrylic shell.

Body/T200 palette follows clydemcqueen/bluerov2_gz's base (vectored) model:
- Body/frame: RGB 53,53,53; bluerov2.dae material 53,53,53.
- T200 housings and motor bodies: RGB 25,25,25; material 25,25,25.
- T200 propellers: RGB 30,107,145; t200_cw_prop.dae / t200_ccw_prop.dae material 30,107,145.
- Hardware: RGB 192,192,192; bluerov2.dae material 192,192,192.

Reference: https://github.com/clydemcqueen/bluerov2_gz/tree/main/models/bluerov2/meshes
Reference commit: 661264b719ffd2dcdd0d0990de80547d6029cc16
Only numeric color values were adopted; no reference geometry is redistributed.

Acrylic outer sphere fit (CAD frame): center (-0.000223202874, 0, 0.150084785) m, radius 0.105000037 m. Acrylic opacity is 0.55 in URDF; Gazebo transparency is 0.45 with a specular highlight.
Camera center advances 0.036384607519 m along the sphere centerline. Including the camera visual's -0.01 m X offset, its farthest vertex touches the 0.10000003804 m inner sphere radius; the opposite end differs by under 0.04 mm.
