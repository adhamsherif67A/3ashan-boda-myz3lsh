"""Build the ocean search cave and three photographic-reference target meshes.

Meters, Z up. Deterministic; running this script never changes a world file.
Requires numpy, trimesh, matplotlib and reportlab (design tools only).
"""
from pathlib import Path
import json
import math
import numpy as np
import trimesh
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[1] / "worlds/assets/search_survey"
MESHES = ASSETS / "meshes"
MESHES.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(2027)
MODEL = ET.Element("sdf", version="1.9")
ROOT = ET.SubElement(MODEL, "model", name="search_survey_cave")
ET.SubElement(ROOT, "static").text = "true"
LINK = ET.SubElement(ROOT, "link", name="cave_and_targets")
PREVIEW = []
MANIFEST = {}


def shifted(mesh, position):
    mesh.apply_translation(position)
    return mesh


def rod(a, b, radius, sections=16):
    a, b = np.asarray(a), np.asarray(b)
    tf = trimesh.geometry.align_vectors([0, 0, 1], b-a)
    tf[:3, 3] = (a+b)/2
    return trimesh.creation.cylinder(radius, np.linalg.norm(b-a), sections=sections,
                                     transform=tf)


def torus(radius, tube, position, vertical=False):
    mesh = trimesh.creation.torus(radius, tube, major_sections=40, minor_sections=12)
    if vertical:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0]))
    return shifted(mesh, position)


def add(name, meshes, color, pose=(0, 0, 0, 0, 0, 0), collision=True, metallic=0):
    mesh = trimesh.util.concatenate(meshes) if isinstance(meshes, list) else meshes
    mesh.fix_normals()
    assert mesh.is_watertight, name
    assert np.isfinite(mesh.vertices).all(), name
    mesh.export(MESHES / f"{name}.stl")
    # STL has no component topology. Reloading merges coincident vertices;
    # verify that the exported artifact, as consumed by Gazebo, stays closed.
    assert trimesh.load(MESHES / f"{name}.stl", force="mesh").is_watertight, name
    uri = f"model://robot_description/worlds/assets/search_survey/meshes/{name}.stl"
    for kind in (["visual", "collision"] if collision else ["visual"]):
        node = ET.SubElement(LINK, kind, name=f"{name}_{kind}")
        ET.SubElement(node, "pose").text = " ".join(map(str, pose))
        shape = ET.SubElement(ET.SubElement(node, "geometry"), "mesh")
        ET.SubElement(shape, "uri").text = uri
        if kind == "visual":
            material = ET.SubElement(node, "material")
            rgba = " ".join(map(str, (*color, 1)))
            ET.SubElement(material, "ambient").text = rgba
            ET.SubElement(material, "diffuse").text = rgba
            ET.SubElement(material, "specular").text = "0.18 0.18 0.18 1"
            metal = ET.SubElement(ET.SubElement(material, "pbr"), "metal")
            ET.SubElement(metal, "metalness").text = str(metallic)
            ET.SubElement(metal, "roughness").text = str(.55 if metallic else .96)
    display = mesh.copy()
    display.apply_transform(trimesh.transformations.euler_matrix(*pose[3:]))
    display.apply_translation(pose[:3])
    PREVIEW.append((name, display, color))
    MANIFEST[name] = {"triangles": len(mesh.faces), "watertight": True,
                      "local_bounds_m": mesh.bounds.tolist(), "pose": list(pose)}
    return mesh


# A hollow arch shell assembled from individual closed rock wedges. Each wedge
# gets its own collision: there is deliberately no hull across the cave opening.
# Mouth faces +Y (towards spawn); inside dimensions 4.6 W x 3.8 D x 1.95 H.
outer = (2.85, 2.45)
inner = (2.30, 1.95)
for row, (front, back) in enumerate(zip([-1.9, -.65, .65], [-.65, .65, 1.9])):
    for segment in range(14):
        # Closed flanks prevent finding the chamber targets from outside.
        a, b = np.pi * np.array([segment, segment+1]) / 14
        vertices = []
        for y in (front, back):
            for theta, scale in ((a, inner), (b, inner), (b, outer), (a, outer)):
                # Preserve smooth inner clearance; weather only the outer skin.
                jitter = RNG.uniform(-.07, .07) if scale is outer else 0
                vertices.append(((scale[0]+jitter)*np.cos(theta), y,
                                 (scale[1]+jitter)*np.sin(theta)))
        rock = trimesh.convex.convex_hull(np.asarray(vertices))
        shade = RNG.uniform(.87, 1.12)
        add(f"arch_{row:02}_{segment:02}", rock,
            tuple(np.clip(np.array([.36, .40, .37])*shade, 0, 1)))


def boulder(name, position, scale, color=(.35, .39, .35)):
    rock = trimesh.creation.icosphere(subdivisions=1, radius=1)
    rock.vertices *= RNG.uniform(.90, 1.10, (len(rock.vertices), 1))
    rock.apply_scale(scale)
    # Convex rocks keep the contact shape predictable and inexpensive.
    return add(name, rock.convex_hull, color, (*position, 0, 0, 0))


# Back wall, with alcoves in front of it. No slab or invisible collision floor.
for column in range(7):
    x = (column-3)*.70
    for level in range(2):
        max_z = inner[1]*np.sqrt(max(0, 1-(x/inner[0])**2))
        z = (.37 if level == 0 else 1.10)
        if z < max_z:
            boulder(f"back_{column}_{level}", (x, -1.92, z), (.49, .37, .48))
for i, (x, y, z, sx, sy, sz) in enumerate([
        (-2.65, 1.65, .20, .55, .55, .33), (2.62, 1.7, .22, .50, .58, .35),
        (-2.5, -.6, .22, .48, .55, .35), (2.6, -1.4, .24, .55, .58, .38)]):
    boulder(f"outcrop_{i}", (x, y, z), (sx, sy, sz))

# Roof-height partitions form two blind side galleries. Their access is at the
# REAR, so pilots enter centrally, turn left/right, then double back to inspect.
# Central clearance is 1.5m; rear turn space is 1.2m deep. Closed convex pieces
# have identical visible/contact surfaces; there are no invisible barriers.
for side, label in [(-1, "west"), (1, "east")]:
    for section, (ya, yb) in enumerate([(-.25, .30), (.30, .90), (.90, 1.48)]):
        x = side*.86
        vertices = [[x+dx, y, z] for dx in (-.11, .11)
                    for y in (ya, yb) for z in (-.03, 2.02)]
        add(f"{label}_gallery_wall_{section}", trimesh.convex.convex_hull(vertices),
            (.33+.015*section, .37+.015*section, .34+.015*section))
    cap = [[side*x, y, z] for x in (.75, 2.55)
           for y in (1.40, 1.64) for z in (-.03, 2.02)]
    add(f"{label}_gallery_front_cap", trimesh.convex.convex_hull(cap), (.35, .39, .36))
    # Empty recesses provide search choices, without extra matching targets.
    boulder(f"{label}_empty_recess", (side*1.78, 1.40, .35), (.34, .28, .42))

# A low rock sill hides the rear floor target from horizontal forward views;
# its 0.63m height still allows the ROV to survey it from above.
sill = [[x, y, z] for x in (-.74, .74) for y in (-.55, -.30)
        for z in (-.03, .64)]
add("rear_survey_sill", trimesh.convex.convex_hull(sill), (.38, .40, .35))

# Bell, an open hollow skirt with a crown loop and visible internal clapper.
profile = np.array([
    [.190, .015], [.198, .035], [.185, .065], [.145, .115],
    [.112, .205], [.090, .285], [.073, .315], [.040, .327],
    [.0, .327], [.0, .304], [.047, .304], [.070, .282],
    [.092, .200], [.125, .110], [.164, .060], [.173, .035], [.173, .015],
    [.190, .015]])
bell = trimesh.creation.revolve(profile, sections=64)
bell_parts = [bell, torus(.043, .011, [0, 0, .365], vertical=True),
              rod([0, 0, .30], [0, 0, .09], .008),
              shifted(trimesh.creation.icosphere(subdivisions=2, radius=.026), [0, 0, .085]),
              torus(.184, .006, [0, 0, .044]), torus(.101, .004, [0, 0, .230])]
# A shelf keeps the upright bell in a side alcove, visible from a forward view.
boulder("bell_ledge", (-1.43, .45, .055), (.35, .33, .10), (.39, .40, .35))
add("01_ships_bell", bell_parts, (.43, .31, .14), (-1.43, .45, .145, 0, 0, -.2), metallic=.65)

# Admiralty anchor: crown and flukes, straight shank, cross-stock and top ring.
# Built flat in XY so a bottom camera sees the complete distinctive silhouette.
anchor = [rod([0, -.37, .045], [0, .40, .045], .032),
          rod([-.32, .28, .055], [.32, .28, .055], .025),
          torus(.057, .012, [0, .445, .045])]
for side in (-1, 1):
    curve = np.array([[0, -.37, .045], [side*.13, -.35, .045],
                      [side*.25, -.26, .045], [side*.30, -.12, .045]])
    # Slightly varying the forging radius avoids coincident cap edges at the
    # joined bends after STL import merges vertices; each rod stays closed.
    anchor += [rod(a, b, .027 + j*.0004 + side*.00005)
               for j, (a, b) in enumerate(zip(curve[:-1], curve[1:]))]
    # Closed triangular fluke prisms, tips face back towards the shank ring.
    triangle = np.array([[side*.30, -.06], [side*.19, -.21], [side*.36, -.20]])
    pts = [[x, y, z] for z in (.025, .080) for x, y in triangle]
    anchor.append(trimesh.convex.convex_hull(np.array(pts)))
# Terrain here is approximately 5.4cm above the cave origin; keep the shank
# above that relief rather than burying the thin anchor in the visual sand.
add("02_admiralty_anchor", anchor, (.22, .18, .14), (1.43, .42, .055, 0, 0, .12), metallic=.55)

# Four rounded swept blades and an annular hub, matching the Nurek photograph.
propeller = []
for blade_index in range(4):
    # A loft, not a faceted triangle: swept planform and real pitch twist.
    theta = np.linspace(0, 2*np.pi, 48, endpoint=False)
    radial = .205 + .175*np.cos(theta)
    x, y = radial, .105*np.sin(theta) + .10*(radial/.380)**2
    z = .20*y - .055*(radial/.380)
    top, bottom = np.c_[x, y, z+.008], np.c_[x, y, z-.008]
    pts = np.vstack((top, bottom, top.mean(axis=0), bottom.mean(axis=0)))
    faces = []
    for j in range(48):
        k = (j+1) % 48
        faces.extend([[96, j, k], [97, k+48, j+48],
                      [j, j+48, k+48], [j, k+48, k]])
    blade = trimesh.Trimesh(vertices=pts, faces=faces, process=True)
    blade.apply_transform(trimesh.transformations.rotation_matrix(blade_index*np.pi/2, [0, 0, 1]))
    propeller.append(blade)
hub_profile = [[.030, -.055], [.070, -.055], [.080, -.020], [.070, .055],
               [.030, .055], [.030, -.055]]
propeller.append(trimesh.creation.revolve(hub_profile, sections=48))
# Raised 9cm on a low sand-coloured stone so no blade disappears into terrain.
boulder("propeller_rest", (0, -1.05, .025), (.28, .24, .055), (.47, .45, .37))
add("03_four_blade_propeller", propeller, (.28, .225, .14), (0, -1.05, .11, 0, 0, .15), metallic=.7)

# Soft reflected fill. The targets remain ordinary opaque, non-emissive objects.
light = ET.SubElement(LINK, "light", name="cave_reflected_fill", type="point")
for tag, value in [("pose", "0 -0.3 1.65 0 0 0"), ("diffuse", "0.14 0.17 0.20 1"),
                   ("specular", "0.10 0.10 0.10 1"), ("cast_shadows", "false")]:
    ET.SubElement(light, tag).text = value
atten = ET.SubElement(light, "attenuation")
for tag, value in [("range", "4"), ("constant", "1"), ("linear", ".3"), ("quadratic", ".15")]:
    ET.SubElement(atten, tag).text = value
ET.indent(MODEL)
ET.ElementTree(MODEL).write(ASSETS / "model.sdf", encoding="unicode", xml_declaration=True)
(ASSETS / "model.config").write_text('''<?xml version="1.0"?>
<model><name>Ocean search and survey cave</name><version>1.0</version>
<sdf version="1.9">model.sdf</sdf><author><name>MarineXperts</name></author>
<description>Open rock cave with three photographic-reference survey targets. Units: meters.</description></model>
''')
(HERE / "mesh_manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")


def preview():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(14, 8), facecolor="#e7f3f6")
    for index, angle in enumerate(((65, 24), (65, 70))):
        ax = fig.add_subplot(1, 2, index+1, projection="3d")
        for name, mesh, color in PREVIEW:
            # Cutaway is explicitly labelled; actual simulation has the roof.
            if index == 1 and name.startswith("arch_"):
                continue
            illumination = .48 + .52*np.clip(mesh.face_normals @ np.array([.3, .4, .86]), 0, 1)
            colors = np.asarray(color)[None, :] * illumination[:, None]
            poly = Poly3DCollection(mesh.triangles, facecolor=colors, linewidths=0)
            ax.add_collection3d(poly)
        ax.set(xlim=(-3, 3), ylim=(-2.5, 2.5), zlim=(0, 2.7))
        ax.set_box_aspect((6, 5, 2.7))
        ax.view_init(elev=angle[1], azim=angle[0])
        ax.set_title("Cave exterior" if index == 0 else "Instructor cutaway — roof hidden")
        ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
    fig.suptitle("OCEAN SEARCH & SURVEY — SIMULATION DESIGN", fontsize=17, weight="bold")
    fig.tight_layout()
    fig.savefig(HERE / "cave_design.png", dpi=150)
    plt.close(fig)
    fig = plt.figure(figsize=(14, 5), facecolor="#e7f3f6")
    targets = [(n, m, c) for n, m, c in PREVIEW if n[:2] in ("01", "02", "03")]
    for i, (name, mesh, color) in enumerate(targets):
        m = mesh.copy(); m.apply_translation(-m.bounds.mean(axis=0))
        ax = fig.add_subplot(1, 3, i+1, projection="3d")
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolor=color, linewidths=.05,
                                           edgecolor=tuple(np.array(color)*.7)))
        r = max(m.extents)*.58
        ax.set(xlim=(-r, r), ylim=(-r, r), zlim=(-r, r))
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=35 if i == 0 else 62, azim=-65)
        ax.set_title(name[3:].replace("_", " ").title()); ax.set_axis_off()
    fig.suptitle("Three STL targets — simulation models, not photographs", fontsize=16)
    fig.tight_layout(); fig.savefig(HERE / "target_designs.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    preview()
    print(f"Created {len(MANIFEST)} closed meshes in {MESHES}")
