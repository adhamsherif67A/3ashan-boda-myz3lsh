"""Generate distinct underwater course assets, with open collision passages."""
from pathlib import Path
import math
import numpy as np
import trimesh
import xml.etree.ElementTree as ET

ASSETS = Path(__file__).resolve().parents[1] / 'worlds/assets'
RNG = np.random.default_rng(42)


def write_model(name, pieces, description):
    folder = ASSETS/name
    (folder/'meshes').mkdir(parents=True, exist_ok=True)
    sdf = ET.Element('sdf', version='1.10')
    model = ET.SubElement(sdf, 'model', name=name)
    ET.SubElement(model, 'static').text = 'true'
    link = ET.SubElement(model, 'link', name='structure')
    for i,(mesh,color) in enumerate(pieces):
        mesh.fix_normals()
        assert mesh.is_watertight and mesh.volume > 0
        filename = f'part_{i:03}.stl'
        mesh.export(folder/'meshes'/filename)
        for tag in ['visual','collision']:
            element = ET.SubElement(link,tag,name=f'{tag}_{i:03}')
            geometry = ET.SubElement(ET.SubElement(element,'geometry'),'mesh')
            ET.SubElement(geometry,'uri').text = f'model://robot_description/worlds/assets/{name}/meshes/{filename}'
            if tag == 'visual':
                material = ET.SubElement(element,'material')
                rgba = ' '.join(str(c) for c in color)+' 1'
                ET.SubElement(material,'ambient').text = rgba
                ET.SubElement(material,'diffuse').text = rgba
                ET.SubElement(material,'specular').text = '0.04 0.04 0.04 1'
                metal = ET.SubElement(ET.SubElement(material,'pbr'),'metal')
                ET.SubElement(metal,'metalness').text = '0'
                ET.SubElement(metal,'roughness').text = '0.95'
    ET.indent(sdf)
    ET.ElementTree(sdf).write(folder/'model.sdf',encoding='utf-8',xml_declaration=True)
    (folder/'model.config').write_text(f'<model><name>{name}</name><version>1.0</version><sdf version="1.10">model.sdf</sdf><description>{description}</description></model>\n')
    combined = trimesh.util.concatenate([mesh for mesh,_ in pieces])
    combined.export(folder/f'{name}.stl')
    (folder/'README.md').write_text(description+'\n\nUnits: meters. Static solid-part collisions retain the central opening.\nRecreate with scripts/create_underwater_obstacles.py.\n')
    print(name, 'closed pieces:',len(pieces),'bounds:',combined.bounds.tolist())


def rock(center, scale):
    mesh = trimesh.creation.icosphere(subdivisions=1)
    mesh.vertices *= RNG.uniform(.89,1.10,(len(mesh.vertices),1))
    mesh.vertices *= scale
    mesh.vertices += center
    mesh.vertices[:,2] = np.maximum(mesh.vertices[:,2],0)
    # Convex rocks are appropriate for efficient individual static contacts.
    return mesh.convex_hull


stones = []
for side in [-1,1]:
    for z in [.28,.62]:
        stones.append((rock([0,side*1.0,z],[.58,.42,.34]),[.34,.39,.32]))
for i,angle in enumerate(np.linspace(0,math.pi,11)):
    center = [.04*math.sin(3*angle), math.cos(angle),1.0+.9*math.sin(angle)]
    stones.append((rock(center,[.55,.34,.31]),[.38+.025*(i%3),.40+.02*(i%2),.34]))
write_model('reef_rock_arch',stones,
    'Irregular submerged rock arch: approximately 1.1 m clear central width and 1.5 m height; swim through or orbit the rock formation.')


def pipe_wedge(a,b,x0,x1,outer=.80,inner=.62):
    vertices = []
    for x in [x0,x1]:
        for r,t in [(inner,a),(outer,a),(outer,b),(inner,b)]:
            vertices.append([x,r*math.cos(t),.80+r*math.sin(t)])
    faces = [[0,2,1],[0,3,2],[4,5,6],[4,6,7],
             [0,1,5],[0,5,4],[1,2,6],[1,6,5],
             [2,3,7],[2,7,6],[3,0,4],[3,4,7]]
    return trimesh.Trimesh(vertices=vertices,faces=faces)


pipes = []
count = 32
for i in range(count):
    a,b = i*2*math.pi/count,(i+1)*2*math.pi/count
    # Chipped irregular mouth, with a few absent upper end pieces.
    x1 = .83 + .09*math.sin(i*2.3)
    if 5 <= i <= 9:
        x1 = .48 + .08*math.sin(i)
    pipes.append((pipe_wedge(a,b,-.90,x1),[.43,.48,.43] if i%4 else [.29,.37,.27]))
    # Raised rear concrete collar, broken on its upper quarter.
    if not 6 <= i <= 10:
        pipes.append((pipe_wedge(a,b,-.92,-.79,outer=.86),[.49,.51,.46]))
write_model('broken_seabed_pipe',pipes,
    'Abandoned concrete seabed pipe: 1.24 m nominal bore, roughly 1.8 m long, chipped mouth and broken rear collar. Tunnel is genuinely hollow for ROV passage.')
