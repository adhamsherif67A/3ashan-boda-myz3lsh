# 1. بنسحب النسخة الأساسية بتاعة ROS 2 Humble
FROM ros:humble

# 2. بنعمل فولدر جوه الدوكر نشتغل فيه ونسميه ros2_ws
WORKDIR /ros2_ws

# 3. بننسخ فولدر src كله (اللي جواه الباكدج بتاعتنا والواجهات) من جهازك لجوه الدوكر
COPY ./src ./src

# 4. بنعمل Build للأكواد كلها جوه الدوكر
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# 5. الأمر اللي هيشتغل أول ما الكونتينر يقوم (هيشغل اللانش فايل اللي بيجمع كل حاجة)
CMD ["/bin/bash", "-c", "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && ros2 launch Fake_Depth_Sensor main_launch.py"]
