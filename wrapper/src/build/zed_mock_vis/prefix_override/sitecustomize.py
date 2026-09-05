import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ibrahim/Desktop/rov/adhamsherif67A-MarineXperts-Season-2027/wrapper/src/install/zed_mock_vis'
