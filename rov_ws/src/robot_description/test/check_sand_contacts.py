"""Isolated manual physics check: spheres rest on visible sand triangles."""
import os
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
data=np.load(ROOT/'worlds/assets/ocean/terrain.npz')
vertices,faces=data['vertices'],data['faces']


def sand_height(x,y):
    for face in faces:
        tri=vertices[face]
        a,b=np.linalg.solve((tri[1:,:2]-tri[0,:2]).T,np.array([x,y])-tri[0,:2])
        if a>=-1e-8 and b>=-1e-8 and a+b<=1+1e-8:
            return float(tri[0,2]+a*(tri[1,2]-tri[0,2])+b*(tri[2,2]-tri[0,2]))
    raise ValueError('Point outside terrain')


os.environ['GZ_PARTITION']='mako-sand-contact-'+uuid.uuid4().hex
os.environ['GZ_SIM_RESOURCE_PATH']=str(ROOT.parent)+':'+os.environ.get('GZ_SIM_RESOURCE_PATH','')
from gz.transport13 import Node
from gz.msgs10.odometry_pb2 import Odometry

tree=ET.parse(ROOT/'worlds/ocean.world');world=tree.find('world')
for plugin in list(world.findall('plugin')):
    if plugin.get('name') not in ['gz::sim::systems::Physics','gz::sim::systems::Buoyancy']:
        world.remove(plugin)
for model in list(world.findall('model')):
    if model.get('name','').startswith('pool_ripple_'):world.remove(model)
points=[(0,0),(5,-3),(-6,-2)]
node=Node();samples={i:[] for i in range(len(points))}
for i,(x,y) in enumerate(points):
    world.append(ET.fromstring(f'''<model name="sand_probe_{i}">
      <pose>{x} {y} -3.3 0 0 0</pose><link name="ball">
      <inertial><mass>5</mass><inertia><ixx>0.0072</ixx><iyy>0.0072</iyy><izz>0.0072</izz></inertia></inertial>
      <collision name="sphere"><geometry><sphere><radius>0.06</radius></sphere></geometry></collision>
      </link><plugin filename="gz-sim-odometry-publisher-system" name="gz::sim::systems::OdometryPublisher">
      <dimensions>3</dimensions><odom_frame>world</odom_frame><robot_base_frame>ball</robot_base_frame>
      <odom_topic>/sand_probe_{i}/odometry</odom_topic><odom_publish_frequency>20</odom_publish_frequency>
      </plugin></model>'''))
    node.subscribe(Odometry,f'/sand_probe_{i}/odometry',lambda m,i=i:samples[i].append((m.pose.position.x,m.pose.position.y,m.pose.position.z)))

with tempfile.TemporaryDirectory(prefix='mako-sand-contact-') as temporary:
    path=Path(temporary)/'world.sdf';tree.write(path)
    with open('/tmp/mako_sand_contacts.log','w') as log:
        process=subprocess.Popen(['gz','sim','-s','-r',str(path)],stdout=log,stderr=log,start_new_session=True)
        try:
            end=time.monotonic()+20
            while time.monotonic()<end:
                if all(len(s)>80 for s in samples.values()):break
                time.sleep(.1)
            for i,(x,y) in enumerate(points):
                assert len(samples[i])>80,('No physics probe samples',i)
                actual=np.array(samples[i][-20:]).mean(axis=0)
                expected=sand_height(actual[0],actual[1])+.06
                assert abs(actual[2]-expected)<.012,(i,actual,expected)
                assert np.ptp(np.array(samples[i][-20:])[:,2])<.006,('Unstable contact',i)
                print('PASS: probe',i,'rests at Z',actual[2],'visible sand + radius',expected,flush=True)
        finally:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
