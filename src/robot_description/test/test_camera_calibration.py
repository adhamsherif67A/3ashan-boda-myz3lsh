"""Regression for measured Gazebo RGB-D pixel centers and calibration timing."""
import importlib.util
from pathlib import Path
from sensor_msgs.msg import CameraInfo

spec = importlib.util.spec_from_file_location(
    'sim_calibration', Path(__file__).parents[1]/'scripts/sim_rgbd_camera_info.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_native_depth_geometry_and_timestamps():
    message = CameraInfo()
    message.width, message.height = 640, 360
    message.header.frame_id = 'zed2i_left_camera_frame_optical'
    message.header.stamp.sec = 12
    message.header.stamp.nanosec = 34000000
    message.k = [224.0664122733091, 0., 320., 0., 224.0664122733091, 180., 0., 0., 1.]
    message.p = [224.0664122733091, 0., 320., 0., 0., 224.0664122733091, 180., 0., 0., 0., 1., 0.]
    result = module.correct_pixel_centers(message)
    # Measured native XYZ at pixel (500, 300) in a stationary pool frame.
    depth = 1.4500640630722046
    native_right, native_down = 1.16812002658844, .7798255681991577
    assert abs(result.k[0]*native_right/depth+result.k[2]-500) < .001
    assert abs(result.k[4]*native_down/depth+result.k[5]-300) < .001
    assert result.header.frame_id == 'zed2i_left_camera_frame_optical'
    assert result.header.stamp.sec == 12
    assert result.header.stamp.nanosec == 34000000
    assert result.p[2] == result.k[2] and result.p[6] == result.k[5]
