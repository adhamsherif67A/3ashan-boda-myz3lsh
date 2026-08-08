# 1. النسخة الأساسية بتاعة ROS 2 Humble
FROM ros:humble

# 2. بنسطب RViz2 عشان الدوكر يقدر يفتحه
RUN apt-get update && apt-get install -y ros-humble-rviz2 && rm -rf /var/lib/apt/lists/*

# 3. بنعمل فولدر الشغل
WORKDIR /ros2_ws

# 4. بننسخ الشغل بتاعك لجوه الدوكر
COPY ./src ./src

# 5. بنطبخ الكود
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# 6. بنحط السورس في الـ bashrc عشان أي تيرمينال يفتح يبقى جاهز
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

# 7. السطر الأخير: بيعمل سورس ويشغل اللانش فايل اللي هيقوم الكود والـ RViz مع بعض
CMD ["/bin/bash", "-c", "source /ros2_ws/install/setup.bash && ros2 launch mock_sensor_pkg mock_launch.py"]
