FROM osrf/ros:humble-desktop-full

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-numpy \
    ros-humble-tf2-ros \
    ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wrapper

COPY . /wrapper/src/zed_mock_vis

RUN . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /wrapper/install/setup.bash" >> ~/.bashrc

CMD ["bash", "-c", "source /opt/ros/humble/setup.bash && source /wrapper/install/setup.bash && ros2 launch zed_mock_vis visualize.launch.py"]
