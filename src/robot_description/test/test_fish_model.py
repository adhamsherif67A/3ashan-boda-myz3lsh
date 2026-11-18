"""CAD preservation, buoyancy and six-axis control geometry contracts."""
import json, math
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
import xacro

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parents[1]
def robot():return E.fromstring(xacro.process_file(str(ROOT/'urdf/robot_description.urdf')).toxml())

def test_cad_motor_positions_and_axes_are_preserved():
    cad=E.parse(WORKSPACE/'reference/fifish_urdf/urdf/fifish_urdf.urdf').getroot()
    adapted=robot()
    for i in range(1,7):
        old=cad.find(f"joint[@name='t{i}_joint']");new=adapted.find(f"joint[@name='t{i}_joint']")
        assert new.find('origin').attrib==old.find('origin').attrib
        assert new.find('axis').attrib==old.find('axis').attrib
        assert new.find('parent').get('link')=='base_link'

def test_neutral_freshwater_displacement():
    r=robot();mass=sum(float(m.get('value')) for m in r.findall('link/inertial/mass'))
    box=r.find("link[@name='buoyancy_link']/collision/geometry/box")
    assert math.isclose(math.prod(map(float,box.get('size').split()))*998,mass,abs_tol=1e-8)

def test_full_rank_mixer_has_no_ideal_cross_axis_force():
    data=json.loads((WORKSPACE/'firmware/allocation.json').read_text())
    B=np.array(data['physical_wrench_matrix']);M=np.array(data['mixer'])
    assert np.linalg.matrix_rank(B)==6
    W=B@M
    # Each control column produces just its intended signed physical wrench.
    for col,row,sign in [(0,3,1),(1,4,-1),(2,5,-1),(3,2,1),(4,0,1),(5,1,-1)]:
        assert W[row,col]*sign>0
        assert np.linalg.norm(np.delete(W[:,col],row))<1e-8

def test_direct_motor_channel_routing_and_frd_imu():
    r=robot();plugin=r.find("gazebo/plugin[@filename='libArduPilotPlugin.so']")
    assert [c.findtext('jointName') for c in plugin.findall('control')]==[f't{i}_joint' for i in range(1,7)]
    assert all(float(c.findtext('multiplier'))>0 for c in plugin.findall('control'))
    angles=list(map(float,r.find("joint[@name='imu_joint']/origin").get('rpy').split()))
    assert np.allclose(angles,[math.pi,0,0])
    assert r.find("joint[@name='base_to_rov_base']/origin").get('rpy')=='0 0 0'

def test_only_dedicated_fish_volume_is_buoyant():
    import importlib.util,tempfile
    spec=importlib.util.spec_from_file_location('fish_gazebo',ROOT/'launch/gazebo.launch.py')
    launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
    with tempfile.TemporaryDirectory() as directory:
        world=E.parse(launch.prepare_world(ROOT/'worlds/pool.world',E.tostring(robot(),encoding='unicode'),directory))
        p=next(p for p in world.findall('world/plugin') if 'buoyancy-system' in p.get('filename',''))
        names=[x.text for x in p.findall('enable')]
        assert 'mako::buoyancy_link' in names and 'mako' not in names


def test_simulation_mass_trim_aligns_forward_thrust_with_combined_com():
    data=json.loads((WORKSPACE/'firmware/allocation.json').read_text())
    pair=np.array([m['position_flu_m'] for m in data['motors'] if m['motor'] in (5,6)])
    assert np.allclose(data['com_flu_m'][1:],pair.mean(axis=0)[1:],atol=1e-10)
    # Mass is unchanged by the inertial-center trim; geometry test above also
    # ensures this is not implemented by moving the motor joints.
    original=E.parse(WORKSPACE/'reference/fifish_urdf/urdf/fifish_urdf.urdf').getroot()
    adapted=robot()
    for old in original.findall('link'):
        name='base_link' if old.get('name')=='rov_body' else old.get('name')
        assert adapted.find(f"link[@name='{name}']/inertial/mass").attrib==old.find('inertial/mass').attrib
    assert max(abs(row[4]) for row in data['mixer'][:4])<1e-4


def test_sub_newton_motor_compensation_is_not_discarded():
    r=robot()
    thrusters=[p for p in r.findall('gazebo/plugin') if p.get('filename')=='gz-sim-thruster-system']
    assert len(thrusters)==6
    # One microsecond PWM step is 103 / (1900 - 1100) N in this bridge.
    assert all(0<float(p.findtext('deadband'))<103/800 for p in thrusters)


def test_drag_frame_and_buoyancy_are_consistent_with_actual_mass_center():
    r=robot();com=np.array(json.loads((WORKSPACE/'firmware/allocation.json').read_text())['com_flu_m'])
    hydro=r.find("gazebo/plugin[@filename='gz-sim-hydrodynamics-system']")
    assert hydro.findtext('link_name')=='hydrodynamics_link'
    drag=np.fromstring(r.find("joint[@name='hydrodynamics_joint']/origin").get('xyz'),sep=' ')
    buoy=np.fromstring(r.find("joint[@name='buoyancy_joint']/origin").get('xyz'),sep=' ')
    assert np.allclose(drag,com,atol=1e-12)
    assert np.allclose(buoy-com,[0,0,.015],atol=1e-12)


def test_repeated_calibration_does_not_accumulate_ballast_shift(tmp_path):
    import hashlib,shutil,subprocess,sys
    (tmp_path/'tools').mkdir();(tmp_path/'firmware').mkdir()
    (tmp_path/'reference/fifish_urdf/urdf').mkdir(parents=True)
    shutil.copytree(ROOT/'urdf',tmp_path/'src/robot_description/urdf')
    shutil.copy2(WORKSPACE/'reference/fifish_urdf/urdf/fifish_urdf.urdf',tmp_path/'reference/fifish_urdf/urdf/fifish_urdf.urdf')
    script=tmp_path/'tools/calibrate_allocation.py'
    shutil.copy2(WORKSPACE/'tools/calibrate_allocation.py',script)
    tracked=[tmp_path/'src/robot_description/urdf/robot_description.urdf',tmp_path/'firmware/custom_frame_cad.cpp',tmp_path/'firmware/allocation.json']
    subprocess.run([sys.executable,str(script)],check=True,capture_output=True)
    first=[hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked]
    subprocess.run([sys.executable,str(script)],check=True,capture_output=True)
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked]==first
