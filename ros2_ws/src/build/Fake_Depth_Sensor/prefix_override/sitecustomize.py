import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ibrahim/Desktop/rov/adhamsherif67A-MarineXperts-Season-2027/ros2_ws/src/install/Fake_Depth_Sensor'
