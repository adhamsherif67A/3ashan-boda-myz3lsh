FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y locales \
    && locale-gen en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG en_US.UTF-8

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

WORKDIR /root/ros2_ws

CMD ["bash"]
