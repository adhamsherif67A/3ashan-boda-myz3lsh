from pathlib import Path
import yaml

P = Path(__file__).parents[1]

def test_planar_contract():
    p = yaml.safe_load((P/'config/nav2.yaml').read_text())
    assert p['bt_navigator']['ros__parameters']['robot_base_frame'] == 'rov_base_link'
    assert not p['planner_server']['ros__parameters']['GridBased']['allow_unknown']
    f = p['controller_server']['ros__parameters']['FollowPath']
    assert f['min_vel_y'] < 0 < f['max_vel_y']
    for key in ['local_costmap', 'global_costmap']:
        c = p[key][key]['ros__parameters']
        assert c['robot_radius'] >= .5
        assert c['plugins'] == ['static_layer', 'inflation_layer']

def test_isolated_commands():
    s = (P/'launch/navigation.launch.py').read_text()
    assert '/mako/navigation/cmd_vel' in s
    assert '/mavros/setpoint' not in s
