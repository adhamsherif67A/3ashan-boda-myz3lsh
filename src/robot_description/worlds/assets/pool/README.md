Pool footprint: X=-7..7 m, Y=-6..6 m, floor Z=-3 m, waterline Z=0 m.
The camera-facing negative-X side is open: its wall visual and collision were removed. The remaining structural walls are 0.15 m thick and extend 0.15 m above water. Floor thickness is 0.2 m. Tile surfaces are offset 1 mm inward to avoid z-fighting.
Tile textures are locally generated original ceramic patterns with grout, subtle variation and a normal map. The 512 px atlas covers 0.5 m, making each tile 0.125 m square. DAE meshes supply UV repetition and embedded ceramic diffuse textures with glossy specular highlights. A generated tile normal map is also supplied for future PBR tuning.
Lane paint and water surface are visual-only. This is a bright pool environment with existing Gazebo buoyancy and ROV hydrodynamics; optical refraction, caustics and turbidity are not simulated.
World name remains CompetitionWorld2025 for the existing joint-state bridge. No red obstacle models or large water-volume visual remain. Robot spawn stays at (0,0,-1).

The opening is at X=-7 m. The camera at its default spawn pose looks along negative world X. Tile repetition was increased to retain the 12.5 cm tile size across the enlarged pool.

## Water and gentle waves

Freshwater fills the pool to world Z=0 (floor Z=-3), using the existing
998 kg/m³ graded buoyancy and the ROV hydrodynamics system. The water has no
solid collision surface, so the ROV can pass through the waterline.

`mako::PoolWaves` animates 56 translucent surface strips at 30 Hz in simulation
time and publishes `/model/mako/ocean_current` (Gazebo `gz.msgs.Vector3d`).
The ROV hydrodynamics subscribes using namespace `mako`, so this is a physical
water velocity disturbance, not a command to move the vehicle.

The default primary wave amplitude is 0.018 m, wavelength 12 m and period
approximately 2.77 s. A secondary wave adds 30% amplitude: the surface displacement
is bounded by ±2.34 cm. Orbital currents follow the same phases and decay
exponentially with depth, reaching approximately 0.032 m/s at 1 m depth.
Currents stop outside the 14 × 12 × 3 m pool bounds. Animation and disturbances
pause and restart with the Gazebo simulation clock.

Change `amplitude` and `wavelength` in the world `mako::PoolWaves` plugin to tune
the ripples; amplitude zero gives calm water. `robot_model` must match the spawned
model and its hydrodynamics namespace. Build the package and launch through
`gazebo.launch.py` so `GZ_SIM_SYSTEM_PLUGIN_PATH` includes the installed library.
For direct `gz sim` use, add `install/robot_description/lib` to that environment
variable.

This is a lightweight linear-wave approximation coupled to drag. It does not
solve fluid volume, refraction, breaking waves, or a wave-varying buoyancy surface;
buoyancy still uses the mean waterline Z=0.
