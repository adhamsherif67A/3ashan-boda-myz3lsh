FROM marinexperts/mako:boda
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-rtabmap ros-humble-rtabmap-slam ros-humble-rtabmap-sync \
    ros-humble-rtabmap-util ros-humble-cv-bridge ros-humble-sensor-msgs-py \
    python3-opencv ffmpeg x11-utils \
    && rm -rf /var/lib/apt/lists/*
USER sim
WORKDIR /opt/pool_mapping_ws
