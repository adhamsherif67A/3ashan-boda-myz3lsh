"""MAVROS client must fail closed and confirm actual heartbeat transitions."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import time
import pytest
from rcl_interfaces.msg import ParameterType

path = Path(__file__).resolve().parents[1]/'scripts/autotune.py'
spec = importlib.util.spec_from_file_location('autotune_client', path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class Harness(module.AutoTuneClient):
    def __init__(self):
        self.state = NS(mode='ALT_HOLD', connected=True, armed=True)
        self.state_at = time.monotonic()
        self.mode_client, self.info_client, self.param_client, self.pull_client = range(4)
        self.info = NS(success=True, vehicles=[NS(type=12, autopilot=3)])
        self.axes = NS(values=[NS(type=ParameterType.PARAMETER_INTEGER, integer_value=4)])
        self.requests = []
        self.sent = True

    def connected(self): pass
    def get_logger(self): return NS(info=lambda _: None)
    def call(self, client, request):
        if client == self.info_client: return self.info
        if client == self.pull_client: return NS(success=True)
        if client == self.param_client: return self.axes
        return NS(mode_sent=self.sent)
    def request(self, target): self.requests.append(target)


def test_valid_sub_requests_onboard_autotune():
    h = Harness(); h.start(); assert h.requests == ['AUTOTUNE']


@pytest.mark.parametrize('field,value', [('armed', False), ('mode', 'MANUAL')])
def test_entry_preconditions_do_not_send_mode(field, value):
    h = Harness(); setattr(h.state, field, value)
    with pytest.raises(RuntimeError): h.start()
    assert h.requests == []


def test_wrong_vehicle_is_rejected():
    h = Harness(); h.info.vehicles[0].type = 2
    with pytest.raises(RuntimeError, match='submarine'): h.start()
    assert h.requests == []


def test_stock_firmware_without_autotune_is_rejected():
    h = Harness(); h.axes.values[0].type = ParameterType.PARAMETER_NOT_SET
    with pytest.raises(RuntimeError, match='patched ArduSub'): h.start()
    assert h.requests == []


def test_stop_preserves_an_external_pilot_mode_change():
    h = Harness(); h.state.mode = 'STABILIZE'; h.stop(); assert h.requests == []
    h.state.mode = 'AUTOTUNE'; h.stop(); assert h.requests == ['ALT_HOLD']


def test_sent_mode_request_is_not_treated_as_acceptance():
    h = Harness()
    def wait(condition, message):
        assert not condition()
        raise RuntimeError(message)
    h.wait = wait
    with pytest.raises(RuntimeError, match='did not enter'):
        module.AutoTuneClient.request(h, 'AUTOTUNE')


def test_heartbeat_confirms_mode_acceptance():
    h = Harness()
    def wait(condition, message):
        h.state.mode = 'AUTOTUNE'; h.state_at = time.monotonic()+.001
        assert condition()
    h.wait = wait
    module.AutoTuneClient.request(h, 'AUTOTUNE')


def test_mavros_rejection_fails_immediately():
    h = Harness(); h.sent = False
    with pytest.raises(RuntimeError, match='rejected'):
        module.AutoTuneClient.request(h, 'AUTOTUNE')
