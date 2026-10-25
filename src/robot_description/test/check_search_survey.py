"""Isolated Gazebo cave clearance / collision and optional RGB rendering check.

Usage (ROS/Gazebo environment sourced):
  python3 src/robot_description/test/check_search_survey.py [--render]
Does not connect to the running simulation or to SITL. Views go to /tmp.
"""
import argparse
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
import numpy as np

ARGS = argparse.ArgumentParser()
ARGS.add_argument('--render', action='store_true')
args = ARGS.parse_args()
ROOT = Path(__file__).resolve().parents[1]
os.environ['GZ_PARTITION'] = 'mx-survey-' + uuid.uuid4().hex
os.environ['GZ_SIM_RESOURCE_PATH'] = str(ROOT.parent)
from gz.transport13 import Node
from gz.msgs10.odometry_pb2 import Odometry
from gz.msgs10.twist_pb2 import Twist
from gz.msgs10.image_pb2 import Image

tree = ET.parse(ROOT/'worlds/ocean.world')
world = tree.find('world')
for plugin in list(world.findall('plugin')):
    if plugin.get('name') not in (['gz::sim::systems::Physics'] +
            (['gz::sim::systems::Sensors'] if args.render else [])):
        world.remove(plugin)
# Ripples are unnecessary for a stationary camera / cave contact check.
for model in list(world.findall('model')):
    if model.get('name', '').startswith('pool_ripple_'):
        world.remove(model)
world.append(ET.fromstring('''<model name="clearance_probe"><pose>0 -0.9 -3.0 0 0 0</pose>
<link name="body"><gravity>false</gravity><inertial><mass>5</mass>
<inertia><ixx>.30</ixx><iyy>.40</iyy><izz>.50</izz></inertia></inertial>
<collision name="body_collision"><geometry><box><size>.85 .65 .55</size></box></geometry></collision>
</link><plugin filename="gz-sim-velocity-control-system" name="gz::sim::systems::VelocityControl">
<topic>/survey_probe/cmd_vel</topic></plugin>
<plugin filename="gz-sim-odometry-publisher-system" name="gz::sim::systems::OdometryPublisher">
<dimensions>3</dimensions><odom_topic>/survey_probe/odom</odom_topic>
<odom_publish_frequency>20</odom_publish_frequency></plugin></model>'''))
node = Node()
poses = []
images = {}
node.subscribe(Odometry, '/survey_probe/odom', lambda m: poses.append((m.pose.position.x, m.pose.position.y, m.pose.position.z)))
publisher = node.advertise('/survey_probe/cmd_vel', Twist)
command = Twist(); command.linear.y = -.50
if args.render:
    for name, eye, target in [
        ('entrance', (0, -.4, -2.6), (0, -4.0, -3.1)),
        ('bell', (-1.43, -4.65, -3.15), (-1.43, -3.55, -3.68)),
        ('bottom', (1.43, -3.58, -3.0), (1.43, -3.58, -3.985)),
        ('rear_survey', (0, -5.05, -2.9), (0, -5.05, -3.93)),
    ]:
        delta = np.asarray(target)-eye
        yaw = math.atan2(delta[1], delta[0])
        pitch = math.atan2(-delta[2], np.linalg.norm(delta[:2]))
        world.append(ET.fromstring(f'''<model name="view_{name}"><static>true</static>
          <pose>{eye[0]} {eye[1]} {eye[2]} 0 {pitch} {yaw}</pose><link name="camera">
          <sensor name="rgb" type="camera"><always_on>true</always_on><update_rate>5</update_rate>
          <topic>/survey_view/{name}</topic><camera><horizontal_fov>1.45</horizontal_fov>
          <image><width>960</width><height>640</height><format>R8G8B8</format></image>
          <clip><near>.05</near><far>25</far></clip></camera></sensor></link></model>'''))
        node.subscribe(Image, f'/survey_view/{name}', lambda m, n=name: images.update({n: m}))

with tempfile.TemporaryDirectory(prefix='mx-survey-check-') as tmp:
    path = Path(tmp)/'world.sdf'; tree.write(path)
    with open('/tmp/mx-survey-check.log', 'w') as log:
        cmd = ['gz', 'sim', '-s', '-r']
        if args.render:
            cmd.append('--headless-rendering')
        process = subprocess.Popen(cmd+[str(path)], stdout=log, stderr=log, start_new_session=True)
        try:
            deadline = time.monotonic()+60
            while time.monotonic() < deadline:
                publisher.publish(command)
                if len(poses) > 100 and poses[-1][1] < -4.9 and (not args.render or len(images) == 4):
                    # Push against the rear wall for a few more physics steps.
                    if len(poses) > 270:
                        break
                time.sleep(.05)
            assert len(poses) > 100, 'No Gazebo physics observations; inspect /tmp/mx-survey-check.log'
            trajectory = np.array(poses)
            assert trajectory[:, 1].min() < -4.9, ('Cave entry blocked', trajectory[-1])
            assert trajectory[:, 1].min() > -5.65, ('Back-wall collision missing', trajectory[-1])
            # An irregular rear wall can deflect the body on contact. Check
            # clearance while travelling through the passage, before that contact.
            passage = trajectory[trajectory[:, 1] > -4.5]
            assert np.max(np.abs(passage[:, 0])) < .05, ('Passage deflects probe', trajectory[-1])
            assert np.max(np.abs(passage[:, 2]+3)) < .05, ('Unexpected floor/roof contact', trajectory[-1])
            print('PASS: 0.85 x 0.65 x 0.55m body enters cave and stops at the rear rock wall:', trajectory[-1])
            if args.render:
                from PIL import Image as PILImage
                assert len(images) == 4, ('Missing rendered camera views', list(images))
                out = Path('/tmp/mx-survey-views'); out.mkdir(exist_ok=True)
                for name, message in images.items():
                    pixels = np.frombuffer(message.data, dtype=np.uint8).reshape(message.height, message.step)
                    pixels = pixels[:, :message.width*3].reshape(message.height, message.width, 3)
                    assert pixels.std() > 8, (name, 'Blank camera image')
                    PILImage.fromarray(pixels).save(out/f'{name}.png')
                print('PASS: four nonblank camera views saved to', out)
        finally:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
