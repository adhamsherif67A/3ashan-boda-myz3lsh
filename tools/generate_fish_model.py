"""Adapt the untouched CAD export to the inherited Gazebo/ROS interfaces."""
from pathlib import Path
import copy, shutil, xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
DESCRIPTION=ROOT/'src/robot_description'
CAD=ROOT/'reference/fifish_urdf'
X='http://www.ros.org/wiki/xacro'
E.register_namespace('xacro',X)
source=E.parse(CAD/'urdf/fifish_urdf.urdf').getroot()
out=E.Element('robot',{'name':'fish_omni_six'})
for name in ['ardusub.urdf.xacro','zed2i_sim.urdf.xacro']:
 E.SubElement(out,'{'+X+'}include',{'filename':name})
for item in source:
 node=copy.deepcopy(item)
 if node.tag=='link' and node.get('name')=='rov_body':node.set('name','base_link')
 for parent in node.findall('parent'):
  if parent.get('link')=='rov_body':parent.set('link','base_link')
 for mesh in node.findall('.//mesh'):
  mesh.set('filename',mesh.get('filename').replace('package://fifish_urdf/meshes/','package://robot_description/meshes/fish_omni_six/'))
 # Friction/damping of a driven propeller must not act as a permanent brake.
 if node.tag=='joint':
  node.find('dynamics').set('damping','0.00001');node.find('dynamics').set('friction','0')
 out.append(node)
def xml(text):out.append(E.fromstring(text))
xml('''<link name="rov_base_link"/>''')
xml('''<joint name="base_to_rov_base" type="fixed"><parent link="base_link"/><child link="rov_base_link"/><origin xyz="0 0 0" rpy="0 0 0"/></joint>''')
xml('''<link name="imu_link"><inertial><mass value="0.01"/><inertia ixx="0.00001" ixy="0" ixz="0" iyy="0.00001" iyz="0" izz="0.00001"/></inertial></link>''')
xml('''<joint name="imu_joint" type="fixed"><parent link="base_link"/><child link="imu_link"/><origin xyz="0 0 0" rpy="3.141592653589793 0 0"/></joint>''')
xml('''<gazebo reference="imu_joint"><preserveFixedJoint>true</preserveFixedJoint></gazebo>''')
xml('''<link name="imu_ros_link"/>''')
xml('''<joint name="imu_ros_joint" type="fixed"><parent link="base_link"/><child link="imu_ros_link"/></joint>''')
# A separate primitive displacement volume avoids treating the CAD mesh hull
# or its propellers as sealed water volume. Its final size/pose is calibrated
# from the complete expanded model by calibrate_allocation.py.
xml('''<link name="buoyancy_link"><inertial><mass value="0.0001"/><inertia ixx="0.000001" ixy="0" ixz="0" iyy="0.000001" iyz="0" izz="0.000001"/></inertial><collision name="sealed_displacement"><geometry><box size="0.32 0.20 0.1104"/></geometry></collision></link>''')
xml('''<joint name="buoyancy_joint" type="fixed"><parent link="base_link"/><child link="buoyancy_link"/><origin xyz="0 0 0.015" rpy="0 0 0"/></joint>''')
xml('''<gazebo reference="buoyancy_joint"><preserveFixedJoint>true</preserveFixedJoint></gazebo>''')
E.SubElement(out,'{'+X+'}zed2i_sim')
xml('''<joint name="zed2i_mount_joint" type="fixed"><parent link="rov_base_link"/><child link="zed2i_camera_link"/><origin xyz="0.255 0 0.015" rpy="0 0 0"/></joint>''')
for name in ['bottom_camera.urdf.xacro','third_person_camera.urdf.xacro']:
 E.SubElement(out,'{'+X+'}include',{'filename':name})
xml('<link name="hydrodynamics_link"><inertial><mass value="0.0001"/><inertia ixx="0.000001" ixy="0" ixz="0" iyy="0.000001" iyz="0" izz="0.000001"/></inertial></link>')
xml('<joint name="hydrodynamics_joint" type="fixed"><parent link="base_link"/><child link="hydrodynamics_link"/><origin xyz="0 0 0" rpy="0 0 0"/></joint>')
xml('<gazebo reference="hydrodynamics_joint"><preserveFixedJoint>true</preserveFixedJoint></gazebo>')
# Reuse MarineXperts sensor noise, hydrodynamics, odometry and rotor plugins.
marine=E.parse(ROOT/'reference/marine_robot_description.urdf').getroot()
for g in marine.findall('gazebo'):
 ref=g.get('reference')
 if ref in ['imu_link','imu_ros_link']:
  out.append(copy.deepcopy(g))
 for p in g.findall('plugin'):
  filename=p.get('filename','')
  if any(t in filename for t in ['hydrodynamics','odometry-publisher','thruster','joint-state-publisher']):
   plugin=copy.deepcopy(p)
   if 'hydrodynamics' in filename:plugin.find('link_name').text='hydrodynamics_link'
   if 'thruster' in filename:plugin.find('deadband').text='0.05'
   E.SubElement(out,'gazebo').append(plugin)
meshes=DESCRIPTION/'meshes/fish_omni_six';meshes.mkdir(exist_ok=True)
for path in (CAD/'meshes').glob('*'):shutil.copy2(path,meshes/path.name)
E.indent(out)
E.ElementTree(out).write(DESCRIPTION/'urdf/robot_description.urdf',encoding='utf-8',xml_declaration=True)

# Motor index maps directly to the equally numbered CAD joint. The CAD axes
# themselves define thrust direction; no fake forces or pose teleporting.
p=DESCRIPTION/'urdf/ardusub.urdf.xacro'
c=E.parse(p);root=c.getroot();plugin=root.find('gazebo/plugin')
for i,control in enumerate(plugin.findall('control'),1):
 control.find('jointName').text=f't{i}_joint'
 control.find('cmd_topic').text=f'/model/robot_description/joint/t{i}_joint/cmd_thrust'
 control.find('multiplier').text='103.0'
E.indent(root);c.write(p,encoding='utf-8',xml_declaration=True)
print('Generated Fish CAD model with MarineXperts water/sensor plugins')
