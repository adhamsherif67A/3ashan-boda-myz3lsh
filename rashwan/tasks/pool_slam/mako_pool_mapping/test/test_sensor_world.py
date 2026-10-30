import sys
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mako_pool_mapping.sensor_world import repair_depth_cover
class SensorWorldTests(unittest.TestCase):
    def test_cover_repair_preserves_physics_and_camera_extrinsics(self):
        xml='''<sdf><world name="pool"><model name="mako"><link name="base_link">
        <inertial><mass>12</mass></inertial><collision name="camera_dome_collision"/>
        <visual name="base_camera_dome_link_visual_5"/><visual name="frame"/>
        <sensor name="zed2i_left_rgbd"><pose>-.18 -.06 0 0 0 3.14159</pose></sensor>
        </link></model><model name="pool"><link name="wall"><visual name="tiles"/></link></model></world></sdf>'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'world.sdf';p.write_text(xml)
            before=ET.fromstring(xml)
            repair_depth_cover(p);after=ET.parse(p).getroot()
            for tag in ('inertial','collision','sensor'):
                self.assertEqual(ET.tostring(before.find('.//'+tag)),ET.tostring(after.find('.//'+tag)))
            self.assertEqual([v.get('name') for v in after.findall('.//visual')],['frame','tiles'])
if __name__=='__main__':unittest.main()
