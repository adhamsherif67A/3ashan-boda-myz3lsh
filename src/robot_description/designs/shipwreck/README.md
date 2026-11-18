# Broken shipwreck proposal

Design only; this asset has not been inserted into pool.sdf or the launch world.

- A small old vessel split amidships, with missing plates, exposed transverse ribs,
  a pointed bow, partially collapsed wheelhouse roof, snapped mast and detached debris.
- Hull envelope approximately 4.7 m long, 1.9 m wide; highest mast point 2.04 m.
  Detached pieces increase the overall width to 2.81 m.
- The nominal 0.90 m split leaves approximately 0.85 m free clearance after edge ribs.
- Practice routes: cross the split, descend into/exit the open hold, orbit the hull,
  and maneuver around the wheelhouse. Window frames are detail obstacles rather
  than guaranteed ROV passageways.

broken_shipwreck.stl is the complete design, in meters. STL does not carry colors.
hull.stl, ribs.stl and deck.stl preserve the material groups for eventual Gazebo
rust-colored hull, dark metal ribs and aged deck rendering.
The proposal contains 129 closed solid components / 1548 triangles; components
are not boolean-unioned. Future collision geometry must retain the open spaces.

Reproduce the STL and three-view preview with:
`rtk proxy python3 src/robot_description/designs/shipwreck/create_design.py`

The preview is rendered directly from the exported geometry, without an AI image.
