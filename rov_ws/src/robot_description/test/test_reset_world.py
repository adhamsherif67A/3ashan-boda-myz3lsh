"""Ensure the launch-generated world retains its robot in the reset snapshot."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import xacro

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mako_gazebo_launch', ROOT / 'launch/gazebo.launch.py')
launch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch_module)


class ResetWorld(unittest.TestCase):
    def test_world_tasks_are_separate_and_logos_match_spawn(self):
        for filename, task_names, depth in [
            ('pool.world', {'crab_target', 'pvc_coral_garden', 'fly_transect'}, 3),
            ('ocean.world', {'shipwreck_1', 'reef_rock_arch', 'broken_seabed_pipe',
                             'east_coral_reef', 'west_coral_reef', 'south_coral_reef',
                             'sunken_boundary_freighter'}, 4),
        ]:
            world = ET.parse(ROOT / 'worlds' / filename).find('world')
            self.assertEqual({item.findtext('name') for item in world.findall('include')}, task_names)
            logos = world.findall("model/link/visual[@name='mako_team_floor_logo']")
            self.assertEqual(len(logos), 1)
            pose = list(map(float, logos[0].findtext('pose').split()))
            self.assertEqual(pose[:2], [0, 0])
            self.assertAlmostEqual(pose[2], -depth + .006)
            self.assertAlmostEqual(pose[5], -1.5707963267948966)
        self.assertEqual((ROOT / 'worlds/pool.world').resolve(),
                         (ROOT / 'worlds/pool.sdf').resolve())

    def test_ocean_start_snapshot_retains_robot_and_depth(self):
        description = xacro.process_file(str(ROOT / 'urdf/robot_description.urdf')).toxml()
        with tempfile.TemporaryDirectory(prefix='mako-ocean-test-') as directory:
            path = launch_module.prepare_world(ROOT / 'worlds/ocean.world', description, directory)
            world = ET.parse(path).find('world')
            self.assertEqual(world.get('name'), 'OceanWorld')
            self.assertEqual(world.findtext("model[@name='mako']/pose"), '0 0 -1 0 0 0')
            self.assertEqual(float(world.findtext("plugin[@name='mako::PoolWaves']/water_depth")), 4)
            floor = world.find("model[@name='ocean_seabed']/link/collision")
            z = float(floor.findtext('pose').split()[2])
            thickness = float(floor.findtext('geometry/box/size').split()[2])
            self.assertLess(z + thickness/2, -4)
            patches = world.findall("model[@name='ocean_seabed']/link/collision")
            self.assertEqual(len(patches), 289)

    def test_initial_world_contains_configured_robot(self):
        description = xacro.process_file(
            str(ROOT / 'urdf/robot_description.urdf'),
            mappings={'camera_width': '320', 'camera_height': '180', 'camera_fps': '10'},
        ).toxml()
        with tempfile.TemporaryDirectory(prefix='mako-reset-test-') as directory:
            path = launch_module.prepare_world(ROOT / 'worlds/pool.sdf', description, directory)
            world = ET.parse(path).find('world')
            self.assertEqual(world.get('name'), 'CompetitionWorld2025')
            models = world.findall("model[@name='mako']")
            self.assertEqual(len(models), 1)
            robot = models[0]
            self.assertEqual(robot.findtext('pose'), '0 0 -1 0 0 0')
            self.assertEqual(len(robot.findall("joint[@type='revolute']")), 6)
            self.assertIsNotNone(world.find("model[@name='swimming_pool']"))
            cameras = robot.findall("link/sensor[@type='rgbd_camera']")
            self.assertEqual(len(cameras), 2)
            for sensor in cameras:
                self.assertEqual(sensor.findtext('camera/image/width'), '320')
                self.assertEqual(sensor.findtext('camera/image/height'), '180')
                self.assertEqual(float(sensor.findtext('update_rate')), 10)
            pilots = [sensor for sensor in robot.findall("link/sensor[@type='camera']")
                      if sensor.get('name', '').endswith('_pilot')]
            self.assertEqual(len(pilots), 2)
            for sensor in pilots:
                self.assertEqual(sensor.findtext('camera/image/width'), '320')
                self.assertEqual(sensor.findtext('camera/image/height'), '180')
                self.assertEqual(float(sensor.findtext('update_rate')), 30)
            self.assertTrue(any('ArduPilot' in plugin.get('name', '')
                                for plugin in robot.findall('plugin')))
