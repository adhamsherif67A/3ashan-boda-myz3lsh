"""Live isolated SITL/Gazebo AUTOTUNE regression; never touches real hardware.

Requires ROS + workspace setup. Builds no firmware. Uses a separate DDS domain,
Gazebo partition, SITL instance, EEPROM directory and UDP endpoints.
"""
import os
import sys
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
os.environ['ROS_DOMAIN_ID'] = '147'
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE/'gui'))
from mako_station.simulation import SimulationSession
import rclpy
from mavros_msgs.msg import State, ManualControl, StatusText
from mavros_msgs.srv import CommandBool, SetMode, ParamPull, ParamSetV2
from rcl_interfaces.msg import ParameterValue, ParameterType
from rcl_interfaces.srv import GetParameters
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data

rclpy.init()
node = rclpy.create_node('isolated_autotune_check')
state, pose, texts = {}, {}, []
node.create_subscription(State, '/mavros/state', lambda m: state.update(mode=m.mode, armed=m.armed, connected=m.connected), 10)
node.create_subscription(Odometry, '/odometry/gz', lambda m: pose.update(z=m.pose.pose.position.z), qos_profile_sensor_data)
node.create_subscription(StatusText, '/mavros/statustext/recv', lambda m: texts.append(m.text), qos_profile_sensor_data)
pub = node.create_publisher(ManualControl, '/mavros/manual_control/send', 10)
command = ManualControl(); command.z = 500.0
arm = node.create_client(CommandBool, '/mavros/cmd/arming')
mode = node.create_client(SetMode, '/mavros/set_mode')
get = node.create_client(GetParameters, '/mavros/param/get_parameters')
pull = node.create_client(ParamPull, '/mavros/param/pull')
put = node.create_client(ParamSetV2, '/mavros/param/set')


def pump(seconds):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        pub.publish(command); rclpy.spin_once(node, timeout_sec=.025)


def wait(predicate, timeout=15):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        if predicate(): return
        pump(.1)
    raise AssertionError((state, pose, texts[-10:]))


def call(client, request):
    assert client.wait_for_service(timeout_sec=15), client.srv_name
    future = client.call_async(request); wait(future.done, 30)
    result = future.result()
    assert getattr(result, 'success', getattr(result, 'mode_sent', True)), result
    return result


def select(name):
    call(mode, SetMode.Request(custom_mode=name))


def parameter(name):
    value = call(get, GetParameters.Request(names=[name])).values[0]
    assert value.type != ParameterType.PARAMETER_NOT_SET, name
    return value


def axes(mask):
    call(put, ParamSetV2.Request(param_id='AUTOTUNE_AXES', value=ParameterValue(
        type=ParameterType.PARAMETER_INTEGER, integer_value=mask)))


def run_client(action):
    process = subprocess.Popen([sys.executable, str(WORKSPACE/'src/mako_control/scripts/autotune.py'),
                                action, '--timeout', '15'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait(lambda: process.poll() is not None, 50)
        output = process.communicate()[0]
        assert process.returncode == 0, output
        print('CLIENT', action, output.strip(), flush=True)
    finally:
        if process.poll() is None:
            process.terminate(); process.wait(timeout=5)


with tempfile.TemporaryDirectory(prefix='mx-autotune-test-') as folder:
    root = Path(folder)
    (root/'install').symlink_to(WORKSPACE/'install'); (root/'src').symlink_to(WORKSPACE/'src')
    # Prevent sim_vehicle from rebuilding over the firmware under test.
    commands = (WORKSPACE/'commands.txt').read_text().replace('sim_vehicle.py ', 'sim_vehicle.py --no-rebuild ')
    (root/'commands.txt').write_text(commands)
    session = SimulationSession(workspace=root, domain=147, instance=11, outputs=(24950, 24951))
    spawn = session.processes.spawn
    def sim_only(name, *args):
        if name not in ('Joystick', 'Pilot control'): return spawn(name, *args)
    session.processes.spawn = sim_only
    try:
        session.start(odometry='ground_truth', notify=lambda s: print(s, flush=True))
        print('LOGS', session.directory, flush=True)
        wait(lambda: state.get('connected') and bool(pose), 100); pump(15)
        call(pull, ParamPull.Request(force_pull=False))
        assert parameter('AUTOTUNE_AXES').integer_value == 4
        select('ALT_HOLD'); wait(lambda: state.get('mode') == 'ALT_HOLD')
        select('AUTOTUNE'); pump(2)
        assert state['mode'] == 'ALT_HOLD' and not state['armed'], state
        print('PASS: disarmed AUTOTUNE entry rejected', flush=True)
        call(arm, CommandBool.Request(value=True)); wait(lambda: state.get('armed')); pump(10)
        before = {name: parameter(name).double_value for name in
                  ['ATC_RAT_YAW_P', 'ATC_RAT_YAW_I', 'ATC_RAT_YAW_D', 'ATC_RAT_YAW_FLTE']}
        axes(7); select('AUTOTUNE'); pump(2)
        assert state['mode'] == 'ALT_HOLD', state
        print('PASS: unsupported pitch axis rejected for VECTORED', flush=True)
        axes(4); run_client('start'); wait(lambda: state.get('mode') == 'AUTOTUNE'); pump(12)
        print('PASS: AUTOTUNE accepted and running; depth', pose['z'], flush=True)
        run_client('stop'); wait(lambda: state.get('mode') == 'ALT_HOLD'); pump(2)
        call(pull, ParamPull.Request(force_pull=True))
        for name, original in before.items():
            assert abs(parameter(name).double_value-original) < 1e-5, (name, original)
        print('PASS: pilot mode exit restores original yaw gains', flush=True)
        select('AUTOTUNE'); wait(lambda: state.get('mode') == 'AUTOTUNE'); pump(3)
        axes(1); wait(lambda: state.get('mode') == 'ALT_HOLD'); pump(2)
        call(pull, ParamPull.Request(force_pull=True))
        for name, original in before.items():
            assert abs(parameter(name).double_value-original) < 1e-5, (name, original)
        axes(4)
        print('PASS: changing AXES mid-tune restores the originally selected gains', flush=True)
        select('AUTOTUNE'); wait(lambda: state.get('mode') == 'AUTOTUNE'); pump(2)
        command.x = 500.0; pump(2); command.x = 0.0
        wait(lambda: state.get('mode') == 'ALT_HOLD')
        pump(1)  # FCU must receive neutral before starting the next session.
        print('PASS: translation input aborts tuning into DepthHold', flush=True)
        select('AUTOTUNE'); wait(lambda: state.get('mode') == 'AUTOTUNE'); pump(2)
        call(arm, CommandBool.Request(value=False)); wait(lambda: not state.get('armed')); pump(2)
        select('ALT_HOLD'); wait(lambda: state.get('mode') == 'ALT_HOLD')
        call(pull, ParamPull.Request(force_pull=True))
        for name, original in before.items():
            assert abs(parameter(name).double_value-original) < 1e-5, (name, original)
        print('PASS: disarming an incomplete tune preserves original gains', flush=True)
    finally:
        session.stop()
        print('Final FCU messages:', texts[-15:], flush=True)
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()
