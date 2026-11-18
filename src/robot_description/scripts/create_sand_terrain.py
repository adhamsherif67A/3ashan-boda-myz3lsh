"""Generate pale sand and a shallow, physically collidable seabed surface."""
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageFilter
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'worlds/assets/ocean'
COLLISIONS = FOLDER/'terrain_collision'
COLLISIONS.mkdir(exist_ok=True)
rng = np.random.default_rng(84)

# Fine pale grains with subtle tonal variation; avoid the old heavy brown ripples.
noise = rng.uniform(0,255,(512,512)).astype(np.uint8)
soft = np.asarray(Image.fromarray(noise).filter(ImageFilter.GaussianBlur(8)),float)-127
y,x = np.mgrid[0:512,0:512]
subtle_ripples = .65*np.sin(y*.10 + 1.1*np.sin(x*.023))
grains = rng.normal(0,2.2,(512,512))
rgb = np.clip(np.array([222,219,203]) + soft[:,:,None]*.35
              +(subtle_ripples+grains)[:,:,None],0,255).astype(np.uint8)
Image.fromarray(rgb).save(FOLDER/'sand.png')

# Low dunes, just centimeters high, fading to a flat pad beneath the floor logo.
xs = np.linspace(-9,9,13)
ys = np.linspace(-8,8,13)
xx,yy = np.meshgrid(xs,ys)
fade = np.clip((np.hypot(xx,yy)-2.5)/1.5,0,1)
height = .022 + .011*np.sin(xx*.85+yy*.32) + .010*np.cos(yy*.80-xx*.24)
zz = -3.999 + fade*height
vertices = np.column_stack((xx.ravel(),yy.ravel(),zz.ravel()))
faces=[]
for row in range(len(ys)-1):
    for col in range(len(xs)-1):
        a=row*len(xs)+col; b=a+1; c=a+len(xs); d=c+1
        faces += [[a,b,d],[a,d,c]]
faces=np.asarray(faces)
mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
mesh.export(FOLDER/'seabed_surface.stl')
np.savez(FOLDER/'terrain.npz',vertices=vertices,faces=faces)

# The render and contact surfaces share exactly the same top triangles.
ns={'c':'http://www.collada.org/2005/11/COLLADASchema'}
ET.register_namespace('',ns['c'])
dae=ET.parse(ROOT/'worlds/assets/pool/floor.dae')
dae.find('.//c:library_images/c:image/c:init_from',ns).text='sand.png'
uv=np.column_stack(((xx.ravel()+9),(yy.ravel()+8)))
for name,array,stride in [('positions',vertices,3),('uv',uv,2),('normals',mesh.vertex_normals,3)]:
    element=dae.find(f".//c:source[@id='{name}']",ns)
    values=element.find('c:float_array',ns)
    values.set('count',str(array.size));values.text=' '.join(f'{v:.8f}' for v in array.ravel())
    element.find('c:technique_common/c:accessor',ns).set('count',str(len(array)))
triangles=dae.find('.//c:triangles',ns);triangles.set('count',str(len(faces)))
triangles.find('c:p',ns).text=' '.join(str(i) for face in faces for index in face for i in [index,index,index])
dae.find('.//c:ambient/c:color',ns).text='0.45 0.45 0.45 1'
dae.find('.//c:specular/c:color',ns).text='0.015 0.015 0.015 1'
dae.find('.//c:shininess/c:float',ns).text='1'
dae.write(FOLDER/'seabed.dae',encoding='utf-8',xml_declaration=True)

world_path=ROOT/'worlds/ocean.world'
tree=ET.parse(world_path)
link=tree.find("world/model[@name='ocean_seabed']/link")
sand = link.find("visual[@name='sand']")
transparency = sand.find('transparency')
if transparency is None:
    transparency = ET.SubElement(sand, 'transparency')
transparency.text = '0.4'  # 60 percent opacity.
for item in list(link.findall('collision')):
    if item.get('name')!='seabed_collision':link.remove(item)
base=link.find("collision[@name='seabed_collision']")
base.find('pose').text='0 0 -4.22 0 0 0'
for index,face in enumerate(faces):
    top=vertices[face]
    bottom=top.copy();bottom[:,2]=-4.12
    solid=trimesh.Trimesh(vertices=np.vstack((top,bottom)),
        faces=[[0,1,2],[5,4,3],[0,3,4],[0,4,1],[1,4,5],[1,5,2],[2,5,3],[2,3,0]])
    solid.fix_normals()
    assert solid.is_watertight and solid.volume>0
    filename=f'patch_{index:03}.stl';solid.export(COLLISIONS/filename)
    collision=ET.SubElement(link,'collision',name=f'sand_patch_{index:03}')
    geometry=ET.SubElement(ET.SubElement(collision,'geometry'),'mesh')
    ET.SubElement(geometry,'uri').text=f'model://robot_description/worlds/assets/ocean/terrain_collision/{filename}'
    surface=ET.SubElement(collision,'surface')
    ode=ET.SubElement(ET.SubElement(surface,'friction'),'ode')
    ET.SubElement(ode,'mu').text='.8';ET.SubElement(ode,'mu2').text='.8'
    bounce=ET.SubElement(surface,'bounce');ET.SubElement(bounce,'restitution_coefficient').text='0'
ET.indent(tree);tree.write(world_path,encoding='utf-8',xml_declaration=True)
(FOLDER/'README.md').write_text('''Pale ivory sand with subtle grains and restrained ripple contrast.
Sand visual opacity is 60 percent (SDF transparency 0.4).
The ocean floor is nominally 4 m deep; gentle dune crests rise by up to 4.3 cm.
A flat 2.5 m-radius center pad keeps the logo visible beneath the spawn.
The textured DAE and 288 closed convex collision patches share identical top
triangles. Physical contact uses friction and zero restitution; lower box is a
backup base below the terrain. No loose-grain solver or erosion is simulated.
Obstacle bases are slightly buried; the pipe bore and arch opening remain clear.
Recreate terrain with scripts/create_sand_terrain.py.
''')
print('Terrain:',len(faces),'closed collision patches; relief',zz.max()-zz.min(),'m')
