"""Create local sand and distinct reef/freighter boundary assets in meters."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageFilter
import trimesh
import xml.etree.ElementTree as ET

ASSETS = Path(__file__).resolve().parents[1]/'worlds/assets'
RNG = np.random.default_rng(2026)


def export_model(name, pieces):
    folder = ASSETS/name
    (folder/'meshes').mkdir(parents=True,exist_ok=True)
    root = ET.Element('sdf',version='1.10')
    model = ET.SubElement(root,'model',name=name)
    ET.SubElement(model,'static').text='true'
    link = ET.SubElement(model,'link',name='structure')
    for i,(mesh,rgb) in enumerate(pieces):
        mesh.fix_normals()
        assert mesh.is_watertight and mesh.volume > 0
        file = f'part_{i:03}.stl'
        mesh.export(folder/'meshes'/file)
        for tag in ['visual','collision']:
            item=ET.SubElement(link,tag,name=f'{tag}_{i:03}')
            geometry=ET.SubElement(ET.SubElement(item,'geometry'),'mesh')
            ET.SubElement(geometry,'uri').text=f'model://robot_description/worlds/assets/{name}/meshes/{file}'
            if tag=='visual':
                material=ET.SubElement(item,'material')
                for channel in ['ambient','diffuse']:
                    ET.SubElement(material,channel).text=' '.join(map(str,rgb))+' 1'
                ET.SubElement(material,'specular').text='0.08 0.08 0.08 1'
    ET.indent(root)
    ET.ElementTree(root).write(folder/'model.sdf',encoding='utf-8',xml_declaration=True)
    (folder/'model.config').write_text(f'<model><name>{name}</name><version>1.0</version><sdf version="1.10">model.sdf</sdf></model>\n')
    combined=trimesh.util.concatenate([m for m,_ in pieces])
    combined.export(folder/f'{name}.stl')
    print(name,len(pieces),'solids; bounds',combined.bounds.tolist())


def cylinder(a,b,radius):
    a,b=np.asarray(a),np.asarray(b)
    transform=trimesh.geometry.align_vectors([0,0,1],b-a)
    transform[:3,3]=(a+b)/2
    return trimesh.creation.cylinder(radius=radius,height=np.linalg.norm(b-a),sections=8,transform=transform)


reef=[]
for y in [-4.8,-2.4,0,2.4,4.8]:
    # Uneven tall rock outcrops provide visible physical boundaries, not hidden walls.
    z=RNG.uniform(1.05,1.35)
    rock=trimesh.creation.icosphere(subdivisions=2)
    rock.vertices*=RNG.uniform(.85,1.1,(len(rock.vertices),1))
    rock.vertices*=[.72,1.43,z]
    rock.vertices+=[RNG.uniform(-.1,.1),y,z]
    rock.vertices[:,2]=np.maximum(rock.vertices[:,2],0)
    reef.append((rock.convex_hull,(.31,.40,.34)))
    # Branching staghorn coral, with muted warm and olive colors.
    for offset in [-.65,.60]:
        base=[-.40,y+offset,.25]
        tip=[-.47,y+offset,1.3+RNG.uniform(0,.4)]
        rgb=(.58,.38,.24) if offset<0 else (.42,.47,.28)
        reef.append((cylinder(base,tip,.065),rgb))
        for level in [.55,.85,1.1]:
            for sign in [-1,1]:
                a=[-.43,y+offset,level]
                b=[-.80,y+offset+sign*.25,level+.30]
                reef.append((cylinder(a,b,.04),rgb))
export_model('ocean_reef_boundary',reef)


def panel(points, thickness=.06):
    p=np.asarray(points,float)
    n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
    vertices=np.vstack((p,p+thickness*n))
    faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
           [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
    return trimesh.Trimesh(vertices=vertices,faces=faces)


ship=[]
rust=(.39,.24,.15);dark=(.23,.29,.29)
stations=[(-4.9,.05),(-4.25,.70),(-3,.90),(0,.90),(3,.90),(4.6,.68)]
for (a,wa),(b,wb) in zip(stations[:-1],stations[1:]):
    ship.append((panel([(a,-wa*.6,0),(b,-wb*.6,0),(b,wb*.6,0),(a,wa*.6,0)]),dark))
    for side in [-1,1]:
        ship.append((panel([(a,side*wa*.6,0),(b,side*wb*.6,0),
                            (b,side*wb,.65),(a,side*wa,.65)]),rust))
        ship.append((panel([(a,side*wa,.65),(b,side*wb,.65),
                            (b,side*wb,2.25),(a,side*wa,2.25)]),rust))
    ship.append((panel([(a,-wa,2.25),(b,-wb,2.25),(b,wb,2.25),(a,wa,2.25)]),dark))
ship.append((panel([(4.6,-.68,.1),(4.6,.68,.1),(4.6,.68,2.25),(4.6,-.68,2.25)]),rust))
for center,size,color in [([2.9,0,2.65],[1.5,1.30,.8],(.47,.43,.34)),
                          ([-1.7,0,2.42],[1.8,1.10,.34],(.29,.37,.31)),
                          ([.55,0,2.42],[1.7,1.10,.34],(.40,.29,.20))]:
    transform=np.eye(4);transform[:3,3]=center
    ship.append((trimesh.creation.box(size,transform),color))
export_model('sunken_freighter_boundary',ship)

# Generate the light sand texture and matching shallow terrain contacts.
import runpy
runpy.run_path(str(Path(__file__).with_name('create_sand_terrain.py')))
