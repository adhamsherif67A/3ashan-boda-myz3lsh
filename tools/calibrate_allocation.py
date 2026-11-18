"""Trim the Fish simulation and compute its six-axis allocation from CAD.

The source CAD export and old firmware are preserved. Simulation ballast trim
moves only the main body's inertial center. Drag acts at the combined COM;
buoyancy acts 15 mm above it. Motor geometry and total CAD masses are retained.
"""
from pathlib import Path
import math,json,xml.etree.ElementTree as E
import numpy as np
import xacro
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/robot_description/urdf/robot_description.urdf'
doc=E.fromstring(xacro.process_file(str(path)).toxml())
cad=E.parse(ROOT/'reference/fifish_urdf/urdf/fifish_urdf.urdf').getroot()
body=doc.find("link[@name='base_link']/inertial")
original_origin=np.fromstring(cad.find("link[@name='rov_body']/inertial/origin").get('xyz'),sep=' ')
body.find('origin').set('xyz',' '.join(map(str,original_origin)))
# Reset generated frames before calculating. Repeated calibration is identical.
for name in ['buoyancy_joint','hydrodynamics_joint']:
 doc.find(f"joint[@name='{name}']/origin").set('xyz','0 0 0')
def transform(origin):
 t=np.eye(4)
 if origin is None:return t
 r,p,y=map(float,origin.get('rpy','0 0 0').split())
 cr,sr,cp,sp,cy,sy=math.cos(r),math.sin(r),math.cos(p),math.sin(p),math.cos(y),math.sin(y)
 t[:3,:3]=[[cy*cp,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr],[sy*cp,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr],[-sp,cp*sr,cp*cr]]
 t[:3,3]=list(map(float,origin.get('xyz','0 0 0').split()));return t
poses={'base_link':np.eye(4)};pending=doc.findall('joint')[:]
while pending:
 progress=False
 for j in pending[:]:
  parent=j.find('parent').get('link')
  if parent in poses:
   poses[j.find('child').get('link')]=poses[parent]@transform(j.find('origin'));pending.remove(j);progress=True
 if not progress:raise ValueError('Unconnected model frames')
mass=0.;moment=np.zeros(3)
for link in doc.findall('link'):
 inertial=link.find('inertial')
 if inertial is not None:
  m=float(inertial.find('mass').get('value'));mass+=m
  moment+=m*(poses[link.get('name')]@transform(inertial.find('origin')))[:3,3]
untrimmed=moment/mass
pair=np.array([poses[f't{i}_link'][:3,3] for i in [5,6]])
com=untrimmed.copy();com[1:]=pair.mean(axis=0)[1:]
frame_positions={'hydrodynamics_link':com,'buoyancy_link':com+[0,0,.015]}
frame_moment=sum(float(doc.find(f"link[@name='{name}']/inertial/mass").get('value'))*position for name,position in frame_positions.items())
body_mass=float(body.find('mass').get('value'))
trimmed_origin=original_origin+(mass*com-moment-frame_moment)/body_mass
assert np.allclose((moment+body_mass*(trimmed_origin-original_origin)+frame_moment)/mass,com,atol=1e-12)
B=[];axes=[]
for i in range(1,7):
 j=doc.find(f"joint[@name='t{i}_joint']");T=poses[j.find('child').get('link')]
 force=T[:3,:3]@np.fromstring(j.find('axis').get('xyz'),sep=' ');force/=np.linalg.norm(force)
 position=T[:3,3];B.append(np.r_[force,np.cross(position-com,force)])
 axes.append({'motor':i,'position_flu_m':position.tolist(),'thrust_axis_flu':force.tolist()})
B=np.array(B).T
# ArduSub FRD rotation axes; upward climb, forward, rightward lateral.
D=np.zeros((6,6));D[3,0]=1;D[4,1]=-1;D[5,2]=-1;D[2,3]=1;D[0,4]=1;D[1,5]=-1
M=np.linalg.solve(B,D);scale=np.max(abs(M),axis=0);M/=scale
assert np.linalg.matrix_rank(B)==6
assert np.max(abs(B@M-D/scale))<1e-10
lines=['    case SUB_FRAME_CUSTOM:','        _frame_class_string = "CUSTOM";','        // Fish CAD-calibrated SITL mixer. See firmware/allocation.json.','        //                               roll pitch yaw climb forward lateral test']
for i,row in enumerate(M,1):
 lines.append(f'        add_motor_raw_6dof(AP_MOTORS_MOT_{i}, '+', '.join(f'{v:.9f}f' for v in row)+f', {i});')
lines+=['        break;',''];(ROOT/'firmware/custom_frame_cad.cpp').write_text('\n'.join(lines))
trim={'reason':'Simulation ballast trim aligns COM Y/Z with horizontal thrust pair; drag applied at COM; CAD joints unchanged.', 'original_body_inertial_origin_m':original_origin.tolist(),'trimmed_body_inertial_origin_m':trimmed_origin.tolist(),'untrimmed_combined_com_flu_m':untrimmed.tolist(),'trimmed_combined_com_flu_m':com.tolist()}
(ROOT/'firmware/allocation.json').write_text(json.dumps({'mass_trim':trim,'axis_order':['roll','pitch','yaw','climb','forward','lateral'],'total_mass_kg':mass,'com_flu_m':com.tolist(),'motors':axes,'physical_wrench_matrix':B.tolist(),'mixer':M.tolist(),'wrench_per_axis':(B@M).tolist(),'rank':6,'condition_number':float(np.linalg.cond(B))},indent=2))
tree=E.parse(path);root=tree.getroot()
root.find("link[@name='base_link']/inertial/origin").set('xyz',' '.join(f'{v:.15g}' for v in trimmed_origin))
root.find("link[@name='buoyancy_link']/collision/geometry/box").set('size',f'0.32 0.20 {mass/(998*.32*.20):.12f}')
for name,position in frame_positions.items():
 joint=root.find("joint[@name='"+('buoyancy_joint' if name=='buoyancy_link' else 'hydrodynamics_joint')+"']")
 joint.find('origin').set('xyz',' '.join(f'{v:.15g}' for v in position))
E.register_namespace('xacro','http://www.ros.org/wiki/xacro');E.indent(root);tree.write(path,encoding='utf-8',xml_declaration=True)
print(json.dumps({'mass_kg':mass,'com_flu_m':com.tolist(),'allocation_rank':6,'condition':float(np.linalg.cond(B))}))
