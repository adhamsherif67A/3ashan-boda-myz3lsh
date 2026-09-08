# 1. إيقاف أي عمليات RViz معلقة
killall -9 rviz2 robot_state_publisher 2>/dev/null || true

# 2. تحديد ونسخ مجسمات Scout الأصلية بدقة
DAE_DIR=$(dirname $(find ~/ros2_ws/src -name "*wheel*.dae" | head -n 1))
echo "Found meshes in: $DAE_DIR"

SCOUT_SHARE=$(ros2 pkg prefix --share scout_description)
mkdir -p "$SCOUT_SHARE/meshes"
cp -f "$DAE_DIR"/* "$SCOUT_SHARE/meshes/" 2>/dev/null || true

# التأكد من وجود scout_mini_base_link.dae و wheel.dae
if [ ! -f "$SCOUT_SHARE/meshes/scout_mini_base_link.dae" ]; then
    BASE_DAE=$(find "$DAE_DIR" -name "*base*.dae" | head -n 1)
    cp "$BASE_DAE" "$SCOUT_SHARE/meshes/scout_mini_base_link.dae" 2>/dev/null || true
fi
if [ ! -f "$SCOUT_SHARE/meshes/wheel.dae" ]; then
    WHEEL_DAE=$(find "$DAE_DIR" -name "*wheel*.dae" | head -n 1)
    cp "$WHEEL_DAE" "$SCOUT_SHARE/meshes/wheel.dae" 2>/dev/null || true
fi

# 3. توفير مجسمات ZED في zed_msgs
sudo mkdir -p /opt/ros/humble/share/zed_msgs/meshes
sudo find /home/ibrahim -name "zed*.stl" -exec cp {} /opt/ros/humble/share/zed_msgs/meshes/ \; 2>/dev/null || true
if [ ! -f /opt/ros/humble/share/zed_msgs/meshes/zedx.stl ]; then
    ZED2I_STL=$(find /opt/ros/humble/share/zed_msgs/meshes -name "zed2i.stl" | head -n 1)
    if [ -n "$ZED2I_STL" ]; then sudo cp "$ZED2I_STL" /opt/ros/humble/share/zed_msgs/meshes/zedx.stl; fi
fi

# 4. كتابة zed_robot_mono.urdf.xacro كامل ومغلق سليم
FILE=$(find ~/ros2_ws/src/zed-ros2-examples -name "zed_robot_mono.urdf.xacro" | head -n 1)
cat << 'EOF' > "$FILE"
<?xml version="1.0"?>
<robot xmlns:xacro="http://ros.org/wiki/xacro" name="scout_mini_zed">

  <xacro:arg name="camera_name"           default="zed" />
  <xacro:arg name="camera_model"          default="zed2i" />
  <xacro:arg name="use_zed_localization"  default="true" />

  <!-- Base link بالشاسيه الأصلي -->
  <link name="base_link">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0" />
      <geometry>
        <mesh filename="package://scout_description/meshes/scout_mini_base_link.dae" />
      </geometry>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0" />
      <geometry>
        <mesh filename="package://scout_description/meshes/scout_mini_base_link.dae" />
      </geometry>
    </collision>
  </link>

  <!-- العجلات الأربعة الأصلية -->
  <xacro:macro name="scout_wheel" params="wheel_prefix x_offset y_offset">
    <link name="${wheel_prefix}_wheel_link">
      <visual>
        <origin xyz="0 0 0" rpy="0 0 0" />
        <geometry>
          <mesh filename="package://scout_description/meshes/wheel.dae" />
        </geometry>
      </visual>
    </link>
    <joint name="${wheel_prefix}_wheel_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${wheel_prefix}_wheel_link"/>
      <origin xyz="${x_offset} ${y_offset} -0.1" rpy="0 0 0"/>
      <axis xyz="0 1 0"/>
    </joint>
  </xacro:macro>

  <xacro:scout_wheel wheel_prefix="front_left" x_offset="0.231" y_offset="0.245" />
  <xacro:scout_wheel wheel_prefix="front_right" x_offset="0.231" y_offset="-0.245" />
  <xacro:scout_wheel wheel_prefix="rear_left" x_offset="-0.231" y_offset="0.245" />
  <xacro:scout_wheel wheel_prefix="rear_right" x_offset="-0.231" y_offset="-0.245" />

  <!-- ZED Camera Macro -->
  <xacro:include filename="$(find zed_wrapper)/urdf/zed_macro.urdf.xacro" />
  <xacro:zed_camera name="$(arg camera_name)" model="$(arg camera_model)">
    <origin xyz="0 0 0" rpy="0 0 0" />
  </xacro:zed_camera>

  <!-- Joint ZED to Base Link -->
  <xacro:if value="$(arg use_zed_localization)">
    <joint name="$(arg camera_name)_joint" type="fixed">
      <parent link="$(arg camera_name)_camera_link"/>
      <child link="base_link"/>
      <origin xyz="-0.12 0.0 -0.25" rpy="0 0 0"/>
    </joint>
  </xacro:if>

  <xacro:unless value="$(arg use_zed_localization)">
    <joint name="$(arg camera_name)_joint" type="fixed">
      <parent link="base_link"/>
      <child link="$(arg camera_name)_camera_link"/>
      <origin xyz="0.12 0.0 0.25" rpy="0 0 0"/>
    </joint>
  </xacro:unless>

</robot>
EOF

# 5. تعديل ملف الـ launch لإجبار camera_model على zed2i
LAUNCH_FILE=$(find ~/ros2_ws/src/zed-ros2-examples -name "view_mono_zed.launch.py" | head -n 1)
sed -i 's/"camera_model", default_value="[^"]*"/"camera_model", default_value="zed2i"/g' "$LAUNCH_FILE"
sed -i "s/'camera_model', default_value='[^']*'/'camera_model', default_value='zed2i'/g" "$LAUNCH_FILE"

# 6. تجهيز Dummy Camera Publisher لبث فيديو تجريبي
cat << 'EOF' > /tmp/dummy_cam.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
import numpy as np

class DummyCam(Node):
    def __init__(self):
        super().__init__('dummy_cam')
        self.pub_img = self.create_publisher(Image, '/zed/zed_node/left/image_rect_color', 10)
        self.pub_info = self.create_publisher(CameraInfo, '/zed/zed_node/left/camera_info', 10)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.c = 0

    def timer_callback(self):
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'zed_left_camera_frame_optical'
        msg.height, msg.width = 360, 640
        msg.encoding = 'bgr8'
        msg.step = 640 * 3
        self.c = (self.c + 4) % 255
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        frame[:, :, 0] = self.c
        frame[:, :, 1] = 150
        frame[:, :, 2] = 255 - self.c
        msg.data = frame.tobytes()
        self.pub_img.publish(msg)

        info = CameraInfo()
        info.header = msg.header
        info.height, info.width = 360, 640
        info.k = [350.0, 0.0, 320.0, 0.0, 350.0, 180.0, 0.0, 0.0, 1.0]
        self.pub_info.publish(info)

def main():
    rclpy.init()
    rclpy.spin(DummyCam())
EOF

# 7. بناء الحزمة والتشغيل
cd ~/ros2_ws
colcon build --symlink-install --packages-select zed_robot_integration
source install/setup.bash

python3 /tmp/dummy_cam.py &
ros2 launch zed_robot_integration view_mono_zed.launch.py camera_model:=zed2i use_zed_localization:=true
