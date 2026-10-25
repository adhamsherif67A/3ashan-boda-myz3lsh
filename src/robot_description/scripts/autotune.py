#!/usr/bin/env python3
"""Request the onboard ArduSub AUTOTUNE mode through MAVROS; never auto-arm."""
import argparse
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from mavros_msgs.msg import State, StatusText
from mavros_msgs.srv import ParamPull, SetMode, VehicleInfoGet
from rcl_interfaces.srv import GetParameters
from rcl_interfaces.msg import ParameterType


class AutoTuneClient(Node):
    def __init__(self, namespace="/mavros", timeout=8.0):
        super().__init__("ardusub_autotune")
        self.timeout = timeout
        self.state = None
        self.state_at = 0.0
        self.last_text = ""
        prefix = namespace.rstrip("/")
        self.create_subscription(State, prefix+"/state", self.on_state, qos_profile_sensor_data)
        self.create_subscription(StatusText, prefix+"/statustext/recv", self.on_text, qos_profile_sensor_data)
        self.mode_client = self.create_client(SetMode, prefix+"/set_mode")
        self.param_client = self.create_client(GetParameters, prefix+"/param/get_parameters")
        self.pull_client = self.create_client(ParamPull, prefix+"/param/pull")
        self.info_client = self.create_client(VehicleInfoGet, prefix+"/vehicle_info_get")

    def on_state(self, msg):
        self.state = msg
        self.state_at = time.monotonic()

    def on_text(self, msg):
        if "AutoTune" in msg.text or "mode" in msg.text.lower():
            self.last_text = msg.text
            self.get_logger().info(msg.text)

    def wait(self, condition, message):
        deadline = time.monotonic()+self.timeout
        while rclpy.ok() and time.monotonic() < deadline:
            if condition():
                return
            rclpy.spin_once(self, timeout_sec=.05)
        raise RuntimeError(message + ("; FCU: "+self.last_text if self.last_text else ""))

    def call(self, client, request):
        if not client.wait_for_service(timeout_sec=self.timeout):
            raise RuntimeError("Unavailable MAVROS service: "+client.srv_name)
        future = client.call_async(request)
        self.wait(future.done, "Service timeout: "+client.srv_name)
        return future.result()

    def connected(self):
        self.wait(lambda: self.state is not None and self.state.connected and
                  time.monotonic()-self.state_at < 2, "No fresh connected FCU heartbeat")

    def request(self, target):
        self.connected()
        response = self.call(self.mode_client, SetMode.Request(custom_mode=target))
        if not response.mode_sent:
            raise RuntimeError("MAVROS rejected mode request "+target)
        # mode_sent means sent, not accepted: require a subsequent FCU heartbeat.
        sent_at = time.monotonic()
        self.wait(lambda: self.state.connected and self.state_at > sent_at and
                  self.state.mode == target, "FCU did not enter "+target)
        self.get_logger().info("Confirmed FCU mode: "+target)

    def start(self):
        self.connected()
        info = self.call(self.info_client, VehicleInfoGet.Request())
        if not info.success or len(info.vehicles) != 1 or info.vehicles[0].type != 12:
            raise RuntimeError("AUTOTUNE client requires an identified ArduSub submarine")
        if info.vehicles[0].autopilot != 3:
            raise RuntimeError("Expected ArduPilot firmware")
        self.connected()
        if not self.state.armed:
            raise RuntimeError("Arm manually in DepthHold first; this client never arms the ROV")
        if self.state.mode not in ("STABILIZE", "ALT_HOLD", "POSHOLD"):
            raise RuntimeError("Start only from STABILIZE, ALT_HOLD or POSHOLD")
        pull = self.call(self.pull_client, ParamPull.Request(force_pull=False))
        if not pull.success:
            raise RuntimeError("Could not read FCU parameters")
        axes = self.call(self.param_client, GetParameters.Request(names=["AUTOTUNE_AXES"]))
        if not axes.values or axes.values[0].type == ParameterType.PARAMETER_NOT_SET:
            raise RuntimeError("Firmware has no AUTOTUNE_AXES; install the patched ArduSub firmware first")
        self.get_logger().info("Requesting onboard AutoTune; mode changes abort and restore original gains")
        self.request("AUTOTUNE")

    def stop(self):
        self.connected()
        if self.state.mode != "AUTOTUNE":
            self.get_logger().info("Already outside AUTOTUNE; preserving pilot-selected mode "+self.state.mode)
            return
        self.request("ALT_HOLD")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("--namespace", default="/mavros")
    parser.add_argument("--timeout", type=float, default=8.0)
    args, ros_args = parser.parse_known_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    rclpy.init(args=ros_args)
    node = AutoTuneClient(args.namespace, args.timeout)
    code = 0
    try:
        if args.action == "start":
            node.start()
        elif args.action == "stop":
            node.stop()
        else:
            node.connected()
            node.get_logger().info(f"connected={node.state.connected} armed={node.state.armed} mode={node.state.mode}")
    except (RuntimeError, KeyboardInterrupt) as error:
        node.get_logger().error(str(error) or "Interrupted; check FCU mode before continuing")
        code = 1
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
