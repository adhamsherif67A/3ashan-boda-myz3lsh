FROM ros:humble

# 1. تحديث وتسطيب الأدوات المطلوبة (RViz2 + MAVROS + MAVROS Messages)
RUN apt-get update && apt-get install -y \
    ros-humble-rviz2 \
    ros-humble-mavros \
    ros-humble-mavros-msgs \
    && rm -rf /var/lib/apt/lists/*

# 2. إنشاء فولدر الورك سبيس
WORKDIR /ros2_ws

# 3. نسخ الكود المصدري من جهازك للدوكر
COPY ./src ./src

# 4. بناء الورك سبيس بالكامل
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# 5. تجهيز السورس تلقائياً في الـ bashrc
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

# 6. أمر التشغيل الافتراضي: تشغيل نود مراقبة الحالة (State Monitor)
CMD ["/bin/bash", "-c", "source /ros2_ws/install/setup.bash && ros2 run flight_monitor_pkg state_monitor_node"]
