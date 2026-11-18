"""Create a meter-scale shipwreck STL and review images; never edit the world."""
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = Path(__file__).resolve().parent
parts = []
RUST = '#965939'
IRON = '#414d50'
DECK = '#6a5945'


def keep(mesh, color):
    mesh.fix_normals()
    parts.append((mesh, color))


def beam(a, b, width, color=IRON, depth=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    transform = trimesh.geometry.align_vectors([0, 0, 1], b-a)
    transform[:3, 3] = (a+b)/2
    keep(trimesh.creation.box([width, depth or width, np.linalg.norm(b-a)], transform), color)


def panel(points, thickness=.035, color=RUST):
    p = np.asarray(points, float)
    normal = np.cross(p[1]-p[0], p[2]-p[0])
    normal /= np.linalg.norm(normal)
    vertices = np.vstack((p, p + normal*thickness))
    faces = [[0,2,1],[0,3,2],[4,5,6],[4,6,7],
             [0,1,5],[0,5,4],[1,2,6],[1,6,5],
             [2,3,7],[2,7,6],[3,0,4],[3,4,7]]
    keep(trimesh.Trimesh(vertices=vertices, faces=faces, process=True), color)


def width(x):
    # Pointed bow, broad working hull, tapered stern.
    return float(np.interp(x, [-2.4,-2.05,-1.5,-.45,.45,1.6,2.25],
                           [.06,.45,.85,.90,.90,.84,.67]))


for stations in ([-2.4,-2.05,-1.65,-1.25,-.85,-.45], [.45,.85,1.25,1.65,2.25]):
    for index,(a,b) in enumerate(zip(stations[:-1],stations[1:])):
        wa,wb = width(a),width(b)
        # Flat keel floor and inclined bilges keep a recognizable boat silhouette.
        panel([(a,-wa*.52,.08),(b,-wb*.52,.08),
               (b,wb*.52,.08),(a,wa*.52,.08)], color=DECK)
        for side in [-1,1]:
            panel([(a,side*wa*.52,.08),(b,side*wb*.52,.08),
                   (b,side*wb,.43),(a,side*wa,.43)])
            # Missing outer plates expose ribs and imply corrosion / impact damage.
            missing = (a == -.85 and side == -1) or (a == .85 and side == 1)
            if not missing:
                top_a = .82 if a not in [-.85,.45] else .66
                top_b = .82 if b not in [-.45,.85] else .60
                panel([(a,side*wa,.43),(b,side*wb,.43),
                       (b,side*wb,top_b),(a,side*wa,top_a)])
            beam((a,side*wa,.83),(b,side*wb,.83),.055)
    for x in stations[1:]:
        w = width(x)
        for side in [-1,1]:
            beam((x,side*w*.52,.12),(x,side*w,.46),.055)
            beam((x,side*w,.46),(x,side*w,.83),.055)
        beam((x,-w*.52,.12),(x,w*.52,.12),.055)

# Jagged cut ends at the 0.90 m-wide split, with no bar across the practice gap.
for side in [-1,1]:
    panel([(-.45,side*.90,.43),(-.65,side*.90,.43),
           (-.57,side*.90,.69),(-.45,side*.90,.56)])
    panel([(.45,side*.90,.43),(.62,side*.90,.43),
           (.56,side*.90,.73),(.45,side*.90,.54)])

# Remaining forward deck and narrow aft perimeter deck; hold stays open from above.
panel([(-2.30,-.12,.83),(-1.65,-.73,.83),(-1.65,.73,.83),(-2.30,.12,.83)],color=DECK)
for side in [-1,1]:
    panel([(.5,side*.73,.84),(2.2,side*.56,.84),
           (2.2,side*.68,.84),(.5,side*.90,.84)],color=DECK)
panel([(2.05,-.67,.43),(2.25,-.67,.43),(2.25,.67,.43),(2.05,.67,.43)])

# Ruined wheelhouse: large empty windows, broken roof and a short tilted mast.
for x in [.85,1.95]:
    for y in [-.55,.55]:
        beam((x,y,.85),(x,y,1.65),.065)
for y in [-.55,.55]:
    beam((.85,y,1.65),(1.95,y,1.65),.065)
    beam((.85,y,.85),(1.95,y,.85),.065)
for x in [.85,1.95]:
    beam((x,-.55,1.65),(x,.55,1.65),.065)
panel([(1.65,-.56,1.66),(1.96,-.56,1.66),(1.96,.56,1.66),(1.65,.56,1.66)],color=RUST)
panel([(.84,-.56,1.66),(1.12,-.56,1.66),(1.03,-.15,1.66),(.84,-.15,1.66)],color=RUST)
beam((1.92,.45,1.68),(2.13,.50,2.02),.055)

# Two detached pieces at the split, kept outside its central traversable lane.
beam((-.33,1.15,.045),(.40,1.42,.045),.07,DECK,.17)
panel([(-.25,-1.17,.02),(.22,-1.30,.02),(.37,-1.11,.09),(-.10,-.97,.09)])

combined = trimesh.util.concatenate([mesh for mesh,_ in parts])
combined.export(OUT/'broken_shipwreck.stl')
for name,color in [('hull',RUST),('ribs',IRON),('deck',DECK)]:
    trimesh.util.concatenate([mesh for mesh,c in parts if c==color]).export(OUT/f'{name}.stl')
assert np.isfinite(combined.vertices).all()
assert all(mesh.is_watertight and mesh.volume > 0 for mesh,_ in parts)

fig = plt.figure(figsize=(16,10),facecolor='#edf4f6')
fig.suptitle('MAKO | BROKEN SHIPWRECK',fontsize=24,fontweight='bold',color='#203945',y=.97)
fig.text(.5,.922,'Design proposal • ~4.7 m hull • ~1.9 m beam • open hold, exposed ribs and ruined wheelhouse',
         ha='center',fontsize=12,color='#46606b')


def draw(ax, elev, azim):
    for mesh,color in parts:
        ax.add_collection3d(Poly3DCollection(mesh.triangles,facecolors=color,
            edgecolors='#28373c',linewidths=.16,alpha=1))
    ax.set_xlim(-2.65,2.65);ax.set_ylim(-1.7,1.7);ax.set_zlim(0,2.25)
    ax.set_box_aspect((5.3,3.4,2.25), zoom=1.30);ax.view_init(elev=elev,azim=azim)
    ax.set_facecolor('#edf4f6');ax.set_axis_off()


ax=fig.add_axes([.02,.27,.68,.63],projection='3d');draw(ax,28,-58)
ax=fig.add_axes([.70,.51,.28,.37],projection='3d');draw(ax,90,-90)
ax.set_title('TOP VIEW / MANEUVERING ROUTES',fontsize=11,color='#203945')
ax=fig.add_axes([.70,.14,.28,.37],projection='3d');draw(ax,8,-90)
ax.set_title('SIDE VIEW / BROKEN PROFILE',fontsize=11,color='#203945')
fig.text(.055,.20,'01  CROSS THE BREAK',fontsize=13,fontweight='bold',color='#203945')
fig.text(.055,.16,'~0.85 m clear gap between bow and stern.\nApproach, yaw, and pass between the broken sections.',fontsize=11,color='#46606b')
fig.text(.055,.10,'02  DESCEND INTO THE HOLD',fontsize=13,fontweight='bold',color='#203945')
fig.text(.055,.06,'Open upper hull for camera-guided descent and exit.\nOrbit the ribs and wheelhouse for close-control practice.',fontsize=11,color='#46606b')
fig.text(.71,.06,'Weathered steel + dark ribs + old deck boards\nSTL geometry in meters · proposal only',fontsize=10,color='#46606b')
fig.savefig(OUT/'design_preview.png',dpi=150,facecolor=fig.get_facecolor())
print(f'Exported {len(parts)} closed solid pieces, {len(combined.faces)} triangles.')
print('Bounding box (m):',combined.bounds.tolist())
