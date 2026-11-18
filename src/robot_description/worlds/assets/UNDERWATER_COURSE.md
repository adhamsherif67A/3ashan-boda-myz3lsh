# Underwater maneuvering course

Every course obstacle has its own geometry and underwater theme:

1. Broken shipwreck at (-4.4, 2.0): turn through its ~0.85 m hull break,
   descend into its open hold, or orbit the ruined wheelhouse.
2. Reef rock arch at (0, 3): swim through its roughly 1.1 m-wide opening
   between irregular stone supports. The upper rock formation reaches ~2.23 m.
3. Broken seabed pipe at (4.4, 2.6): line up with a chipped concrete mouth
   and traverse its 1.24 m bore; pipe axis is nearly world X.

Follow west to east, adjusting depth and heading for each opening. Crab, coral garden and fly transect are in the separate team pool.world.
This course is in ocean.world, on its 4 m-deep seabed. Both worlds have the team logo.
All obstacles have solid-part static collision geometry; the openings are not
filled by whole-model collision hulls. Initial world includes preserve obstacles
on Gazebo Reset. Source STL files are supplied in each asset directory.

Obstacle bases are now buried slightly in the pale, low-relief sand terrain.
Sand supports physical contacts using convex terrain patches; loose grains are not simulated.
