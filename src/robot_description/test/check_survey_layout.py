"""Check hidden targets, inspection sightlines and gallery clearance, in meters."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/'worlds/assets/search_survey/model.sdf'
rocks, targets = [], {}
for node in ET.parse(MODEL).findall('.//visual'):
    name = node.get('name')
    path = ROOT.parent/node.findtext('geometry/mesh/uri').removeprefix('model://')
    mesh = trimesh.load(path, force='mesh')
    pose = list(map(float, node.findtext('pose').split()))
    mesh.apply_transform(trimesh.transformations.euler_matrix(*pose[3:]))
    mesh.apply_translation(pose[:3])
    if name[:2] in ('01', '02', '03'):
        targets[name[:2]] = mesh.vertices[::max(1, len(mesh.vertices)//160)]
    else:
        rocks.append((name, ConvexHull(mesh.vertices).equations))


def blocked(eye, points):
    """Clip finite sightline segments against closed convex rock polyhedra."""
    eye = np.asarray(eye)
    directions = points-eye
    result = np.zeros(len(points), dtype=bool)
    for _, planes in rocks:
        slopes = directions@planes[:, :3].T
        offsets = planes[:, :3]@eye+planes[:, 3]
        with np.errstate(divide='ignore', invalid='ignore'):
            crossing = -offsets[None, :]/slopes
        lo = np.max(np.where(slopes < -1e-10, crossing, -np.inf), axis=1)
        hi = np.min(np.where(slopes > 1e-10, crossing, np.inf), axis=1)
        outside_parallel = np.any((np.abs(slopes) <= 1e-10) & (offsets > 1e-8), axis=1)
        result |= (np.maximum(lo, 1e-5) < np.minimum(hi, .995)) & ~outside_parallel
    return result


for x in (-.6, 0, .6):
    for z in (.5, 1.0, 1.6):
        for name, points in targets.items():
            visible = (~blocked((x, 2.2, z), points)).sum()
            assert visible == 0, ('Target exposed at mouth', name, x, z, visible)
print('PASS: all three targets concealed from nine entrance viewpoints')

for name, eye in [('01', (-1.43, -.65, .89)), ('02', (1.43, .42, 1.04)),
                  ('03', (0, -1.05, 1.14))]:
    fraction = (~blocked(eye, targets[name])).mean()
    assert fraction > .50, ('Target inaccessible to inspection camera', name, fraction)
    print(f'PASS: target {name} inspection sightline visible samples {fraction:.0%}')

# Sample vehicle volumes, not just a centerline: both main passage and the
# rear access / side galleries must accommodate a .65W x .85L x .55H body.
offsets = np.array(np.meshgrid(np.linspace(-.325, .325, 5),
                              np.linspace(-.425, .425, 5),
                              np.linspace(-.275, .275, 5))).reshape(3, -1).T
route = [(0, y, 1.04) for y in np.linspace(2.2, -.95, 20)]
for side in (-1, 1):
    route += [(x, -.95, 1.04-.19*max(0, (abs(x)-1.10)/.33))
              for x in np.linspace(0, side*1.43, 12)]
    route += [(side*1.43, y, .85) for y in np.linspace(-.95, -.35 if side < 0 else .42, 12)]
for position in route:
    points = offsets+position
    for name, planes in rocks:
        inside = np.all(points@planes[:, :3].T+planes[:, 3] < -1e-6, axis=1)
        assert not inside.any(), ('ROV volume intersects rock', position, name)
print('PASS: sampled ROV volumes clear main passage and both gallery approaches')
