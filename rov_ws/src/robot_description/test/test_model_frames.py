"""Check frame geometry and the simulated six-axis odometry contract."""
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import xacro


ROOT = Path(__file__).resolve().parents[1]


def product(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def pose(origin):
    xyz = [float(v) for v in origin.get('xyz', '0 0 0').split()]
    r, p, y = [float(v) for v in origin.get('rpy', '0 0 0').split()]
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [[cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr, xyz[0]],
            [sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr, xyz[1]],
            [-sp, cp*sr, cp*cr, xyz[2]], [0, 0, 0, 1]]


class ModelFrames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.robot = ET.fromstring(xacro.process_file(str(ROOT / 'urdf/robot_description.urdf')).toxml())
        cls.links = [e.get('name') for e in cls.robot.findall('link')]
        cls.parents = {}
        for joint in cls.robot.findall('joint'):
            child = joint.find('child').get('link')
            if child in cls.parents:
                raise AssertionError('Multiple parents for ' + child)
            cls.parents[child] = (joint.find('parent').get('link'), pose(joint.find('origin')))

    def transform(self, reference, child):
        if reference == child:
            return [[int(i == j) for j in range(4)] for i in range(4)]
        parent, matrix = self.parents[child]
        return product(self.transform(reference, parent), matrix)

    def test_freshwater_displacement_matches_complete_mass(self):
        mass = sum(float(e.get('value')) for e in self.robot.findall('link/inertial/mass'))
        volume = 0.0
        # Gazebo graded buoyancy supports these primitives; camera mesh is not
        # part of the displacement calculation. Include every contact frame bar.
        for geometry in self.robot.findall('link/collision/geometry'):
            box = geometry.find('box')
            sphere = geometry.find('sphere')
            cylinder = geometry.find('cylinder')
            if box is not None:
                volume += math.prod(float(v) for v in box.get('size').split())
            elif sphere is not None:
                volume += 4 * math.pi * float(sphere.get('radius'))**3 / 3
            elif cylinder is not None:
                volume += math.pi * float(cylinder.get('radius'))**2 * float(cylinder.get('length'))
        self.assertAlmostEqual(volume * 998.0, mass, places=8)

    def test_force_centers_are_aligned(self):
        total_mass = 0.0
        weighted = [0.0]*3
        volume = 0.0
        buoyancy = [0.0]*3
        for link in self.robot.findall('link'):
            transform = self.transform('base_link', link.get('name'))
            inertial = link.find('inertial')
            if inertial is not None:
                mass = float(inertial.find('mass').get('value'))
                origin = inertial.find('origin')
                local = pose(origin) if origin is not None else [[int(i == j) for j in range(4)] for i in range(4)]
                center = product(transform, local)
                total_mass += mass
                for i in range(3): weighted[i] += mass * center[i][3]
            for collision in link.findall('collision'):
                box = collision.find('geometry/box')
                if box is None: continue  # Pool graded buoyancy ignores camera mesh.
                displaced = math.prod(float(v) for v in box.get('size').split())
                center = product(transform, pose(collision.find('origin')))
                volume += displaced
                for i in range(3): buoyancy[i] += displaced * center[i][3]
        com = [v/total_mass for v in weighted]
        cob = [v/volume for v in buoyancy]
        hydro = self.transform('base_link', 'hydrodynamics_link')
        for i in range(3): self.assertAlmostEqual(com[i], hydro[i][3], places=9)
        for i in range(2): self.assertAlmostEqual(com[i], cob[i], places=9)
        self.assertAlmostEqual(cob[2]-com[2], 0.054, places=6)
        # Pure translation allocation should not apply significant roll/pitch/yaw.
        for allocation in [(-1,-1,1,1,0,0), (1,-1,1,-1,0,0), (0,0,0,0,1,1)]:
            torque = [0.0]*3
            for index, command in enumerate(allocation, 1):
                frame = self.transform('base_link', f't{index}_link')
                arm = [frame[i][3]-com[i] for i in range(3)]
                force = [command * frame[i][2] for i in range(3)]
                torque[0] += arm[1]*force[2]-arm[2]*force[1]
                torque[1] += arm[2]*force[0]-arm[0]*force[2]
                torque[2] += arm[0]*force[1]-arm[1]*force[0]
            for value in torque: self.assertLess(abs(value), 1e-5)

    def test_horizontal_mixer_matches_frd_yaw_and_lateral_axes(self):
        plugin = self.robot.find("gazebo/plugin[@filename='libArduPilotPlugin.so']")
        controls = plugin.findall('control')[:4]
        for weights, expected in [([1,-1,-1,1], 'yaw'), ([1,-1,1,-1], 'right')]:
            force = [0.0]*3
            torque = 0.0
            for control, weight in zip(controls, weights):
                joint = self.robot.find(f"joint[@name='{control.findtext('jointName')}']")
                frame = self.transform('base_link', joint.find('child').get('link'))
                thrust = weight * float(control.findtext('multiplier'))
                f = [thrust*frame[i][2] for i in range(3)]
                for i in range(3): force[i] += f[i]
                torque += frame[0][3]*f[1] - frame[1][3]*f[0]
            if expected == 'yaw':
                self.assertLess(torque, 0, 'Positive FRD yaw requires negative FLU Z torque')
                self.assertLess(math.sqrt(sum(v*v for v in force)), .01)
            else:
                self.assertLess(force[1], 0, 'Positive lateral command must move right')

    def test_gazebo_conversion_keeps_the_sensor_parent_in_frd(self):
        import shutil,subprocess,tempfile
        if not shutil.which('gz'):self.skipTest('Gazebo CLI unavailable')
        with tempfile.NamedTemporaryFile(suffix='.urdf',mode='w') as file:
            file.write(ET.tostring(self.robot,encoding='unicode'));file.flush()
            converted=subprocess.run(['gz','sdf','-p',file.name],capture_output=True,text=True,check=True)
        model=ET.fromstring(converted.stdout).find('model')
        imu=model.find("link[@name='imu_link']")
        self.assertIsNotNone(imu, 'Fixed-joint reduction must not merge the FRD IMU link')
        self.assertIsNotNone(imu.find("sensor[@name='imu_sensor']"))
        self.assertEqual(model.findtext("plugin[@filename='libArduPilotPlugin.so']/modelXYZToAirplaneXForwardZDown"), '0 0 0 0 0 0')

    def test_plugin_pose_and_sensor_samples_share_the_same_frd_frame(self):
        plugin = self.robot.find("gazebo/plugin[@filename='libArduPilotPlugin.so']")
        conversion = plugin.findtext('modelXYZToAirplaneXForwardZDown').split()
        offset = pose(ET.Element('origin', xyz=' '.join(conversion[:3]), rpy=' '.join(conversion[3:])))
        actual = product(self.transform('base_link', 'imu_link'), offset)
        for i, expected in enumerate([1,-1,-1]):
            self.assertAlmostEqual(actual[i][i], expected, places=7)

    def test_vertical_mixer_produces_upward_heave_and_positive_frd_roll(self):
        import runpy
        params = runpy.run_path(str(ROOT / 'scripts/fix_ardusub_params.py'))['PARAMS']
        plugin = next(p for p in self.robot.findall('gazebo/plugin')
                      if p.get('filename') == 'libArduPilotPlugin.so')
        controls = {int(c.get('channel')): c for c in plugin.findall('control')}
        heave = roll = 0.0
        for motor, roll_mix in [(5, 1), (6, -1)]:
            control = controls[motor - 1]
            direction = params[f'MOT_{motor}_DIRECTION'][0]
            gain = float(control.findtext('multiplier')) * direction
            joint = self.robot.find(f"joint[@name='{control.findtext('jointName')}']")
            frame = self.transform('base_link', joint.find('child').get('link'))
            # VECTORED uses -1 heave and +1/-1 roll for its vertical pair.
            heave += -gain * frame[2][2]
            roll += roll_mix * gain * (frame[1][3]*frame[2][2] - frame[2][3]*frame[1][2])
        self.assertGreater(heave, 0, 'Positive heave must lift the ROV')
        self.assertGreater(roll, 0, 'Positive FRD roll must produce positive X torque')
        self.assertEqual(params['MOT_PWM_MIN'][0] + params['MOT_PWM_MAX'][0], 3000)

    def test_translation_rotor_momentum_cancels(self):
        coefficients = {}
        for plugin in self.robot.findall('gazebo/plugin'):
            if plugin.get('filename') == 'gz-sim-thruster-system':
                coefficients[plugin.findtext('joint_name')] = float(plugin.findtext('thrust_coefficient'))
        for allocation in [(-1,-1,1,1,0,0), (1,-1,1,-1,0,0), (0,0,0,0,1,1)]:
            momentum = [0.0]*3
            for index, command in enumerate(allocation, 1):
                frame = self.transform('base_link', f't{index}_link')
                coefficient = coefficients[f't{index}_joint']
                spin = command * math.copysign(1, coefficient)
                for i in range(3): momentum[i] += spin * frame[i][2]
            for value in momentum: self.assertLess(abs(value), 1e-5)

    def test_bottom_camera_points_down_inside_dome(self):
        body = self.transform('zed2i_camera_center', 'bottom_camera_link')
        self.assertAlmostEqual(body[2][3], -0.05)
        optical = self.transform('rov_base_link', 'bottom_camera_optical_frame')
        for i, expected in enumerate([0, 0, -1]):
            self.assertAlmostEqual(optical[i][2], expected, places=8)
        # All housing corners and the lens tip fit inside the inner acrylic sphere.
        cad = self.transform('base_link', 'center_body_link')
        inverse = [[cad[j][i] for j in range(3)] +
                   [-sum(cad[j][i]*cad[j][3] for j in range(3))] for i in range(3)]
        inverse.append([0, 0, 0, 1])
        housing = product(inverse, self.transform('base_link', 'bottom_camera_link'))
        dome = [-0.000223202874, 0, 0.150084785]
        for x in [-0.0125, 0.015]:
            for y in [-0.0175, 0.0175]:
                for z in [-0.0125, 0.0125]:
                    point = [housing[i][3] + sum(housing[i][j]*v for j, v in enumerate([x,y,z])) for i in range(3)]
                    self.assertLess(math.dist(point, dome), 0.10000003804)
        sensor = self.robot.find("gazebo[@reference='bottom_camera_link']/sensor")
        self.assertEqual(sensor.get('type'), 'camera')
        self.assertEqual(sensor.findtext('camera/optical_frame_id'), 'bottom_camera_optical_frame')

    def test_one_connected_tree(self):
        self.assertEqual(len(self.links), len(set(self.links)))
        self.assertEqual(set(self.links) - self.parents.keys(), {'base_link'})
        for name in self.links:
            self.transform('base_link', name)

    def test_camera_stays_on_dome_centerline(self):
        t = self.transform('rov_base_link', 'zed2i_camera_center')
        expected = [0.186469391519, -0.000223754166, -0.0000005512922]
        for got, want in zip([t[0][3], t[1][3], t[2][3]], expected):
            self.assertAlmostEqual(got, want, places=8)
        body = self.transform('base_link', 'zed2i_left_camera_frame')
        self.assertAlmostEqual(body[0][0], -1.0)

    def test_optical_axes_and_stereo_baseline(self):
        for eye in ['left', 'right']:
            t = self.transform('rov_base_link', 'zed2i_' + eye + '_camera_frame_optical')
            # optical Z forward = body X, optical X right = -body Y,
            # optical Y down = -body Z.
            expected = [[0, 0, 1], [-1, 0, 0], [0, -1, 0]]
            for i in range(3):
                for j in range(3):
                    self.assertAlmostEqual(t[i][j], expected[i][j])
        left = self.transform('rov_base_link', 'zed2i_left_camera_frame')
        right = self.transform('rov_base_link', 'zed2i_right_camera_frame')
        self.assertAlmostEqual(left[1][3] - right[1][3], 0.12)

    def test_imu_frames_are_distinct(self):
        ros = self.transform('rov_base_link', 'imu_ros_link')
        fcu = self.transform('base_link', 'imu_link')
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(ros[i][j], int(i == j))
        for i, expected in enumerate([1, -1, -1]):
            self.assertAlmostEqual(fcu[i][i], expected)

    def test_chase_camera_is_massless_behind_bow_and_looks_at_vehicle(self):
        link = self.robot.find("link[@name='third_person_camera_link']")
        self.assertIsNone(link.find('inertial'))
        self.assertIsNone(link.find('collision'))
        camera = self.transform('rov_base_link', 'third_person_camera_optical_frame')
        self.assertAlmostEqual(camera[0][3], -1.45)
        self.assertAlmostEqual(camera[2][3], .62)
        # Optical Z ray must point forward and downward toward the body.
        self.assertGreater(camera[0][2], .9)
        self.assertLess(camera[2][2], -.3)
        ray_height = camera[2][3] + 1.45 * camera[2][2] / camera[0][2]
        self.assertLess(abs(ray_height), .1)

    def test_odometry_is_six_axis(self):
        plugin = next(p for p in self.robot.findall('./gazebo/plugin')
                      if p.get('name') == 'gz::sim::systems::OdometryPublisher')
        self.assertEqual(plugin.findtext('dimensions'), '3')
        self.assertEqual(plugin.findtext('robot_base_frame'), 'base_link')
        self.assertEqual(plugin.findtext('tf_topic'), '/model/mako/tf')


if __name__ == '__main__':
    unittest.main()
