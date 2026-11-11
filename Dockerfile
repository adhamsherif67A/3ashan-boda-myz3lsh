# ROS 2 Humble + Gazebo Harmonic + ArduSub SITL + the Mako ROS packages and Operation MX.
# Build with docker/build.sh and run with docker/run.sh (see README.md, "Docker setup").
ARG BASE_IMAGE=ros:humble-ros-base-jammy
FROM ${BASE_IMAGE}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG BUILD_JOBS=2
ARG SIM_UID=1000
ARG SIM_GID=1000
# These are the upstream revisions used by the validated local simulation.
ARG ARDUPILOT_REF=375cef5813bbd4ea99a67d9f046833e1c492f439
ARG ARDUPILOT_GAZEBO_REF=082a0fe231f6e63bc8d1598f1cba461d9e2ea7f5
LABEL org.marinexperts.user-id="${SIM_UID}"
ENV DEBIAN_FRONTEND=noninteractive GZ_VERSION=harmonic \
    MAKO_WORKSPACE=/opt/mako_ws MAKO_ARDUPILOT=/opt/ardupilot \
    MAKO_ARDUPILOT_GAZEBO=/opt/ardupilot_gazebo \
    ROS_DOMAIN_ID=42 RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    PATH=/opt/ardupilot/Tools/autotest:/usr/local/bin:$PATH
COPY docker/install-apt.sh docker/install-python.py /usr/local/lib/mako/
RUN bash /usr/local/lib/mako/install-apt.sh ca-certificates curl gnupg git \
    build-essential cmake pkg-config python3-pip python3-dev python3-colcon-common-extensions \
    python3-rosdep python3-empy python3-future python3-lxml python3-serial \
    python3-pexpect python3-psutil python3-numpy python3-yaml python3-pyparsing \
    libxml2-dev libxslt1-dev geographiclib-tools rapidjson-dev libopencv-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gawk ccache \
    libgl1-mesa-dri libegl1 mesa-utils \
    python3-pyqt5 python3-cryptography python3-yaml python3-pytest ffmpeg x11-utils \
    && curl -fsSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/gazebo.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gazebo.asc] https://packages.osrfoundation.org/gazebo/ubuntu-stable jammy main" > /etc/apt/sources.list.d/gazebo-stable.list \
    && bash /usr/local/lib/mako/install-apt.sh gz-harmonic libgz-sim8-dev \
    ros-humble-ros-gzharmonic ros-humble-mavros ros-humble-mavros-extras \
    ros-humble-rviz2 ros-humble-xacro ros-humble-robot-state-publisher ros-humble-joy \
    ros-humble-joint-state-publisher-gui ros-humble-tf2-ros \
    ros-humble-rtabmap-odom ros-humble-rtabmap-launch ros-humble-rtabmap-slam \
    ros-humble-navigation2 ros-humble-nav2-bringup \
    ros-humble-rtabmap-viz ros-humble-ament-cmake-pytest \
    ros-humble-ament-flake8 ros-humble-ament-pep257 ros-humble-ament-copyright \
    && python3 /usr/local/lib/mako/install-python.py MAVProxy==1.8.74 pymavlink==2.4.49 dronecan==1.0.27 geocoder==1.38.1 \
    && rm -rf /var/lib/apt/lists/*
COPY install_geographiclib_datasets.sh /usr/local/lib/mako/
RUN bash /usr/local/lib/mako/install_geographiclib_datasets.sh \
    && groupadd --non-unique --gid ${SIM_GID} sim \
    && useradd --create-home --uid ${SIM_UID} --gid ${SIM_GID} --shell /bin/bash sim \
    && usermod -aG video,input sim \
    && mkdir -p /opt/ardupilot /opt/ardupilot_gazebo /opt/mako_ws /data \
    && chown -R sim:sim /opt/ardupilot /opt/ardupilot_gazebo /opt/mako_ws /data
# The official ArduPilot prerequisite script rejects root. Dependencies above
# are installed explicitly; source compilation and runtime use an ordinary user.
USER sim
WORKDIR /opt/ardupilot
RUN git init . && git remote add origin https://github.com/ArduPilot/ardupilot.git \
    && git fetch --depth 1 origin ${ARDUPILOT_REF} && git checkout --detach FETCH_HEAD \
    && git submodule update --init --recursive --depth 1 \
    && ./waf configure --board sitl && ./waf sub -j${BUILD_JOBS}
WORKDIR /opt/ardupilot_gazebo
RUN git init . && git remote add origin https://github.com/ArduPilot/ardupilot_gazebo.git \
    && git fetch --depth 1 origin ${ARDUPILOT_GAZEBO_REF} && git checkout --detach FETCH_HEAD \
    && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --parallel ${BUILD_JOBS}
WORKDIR /opt/mako_ws
# All ROS packages: robot_description, mako_control, mako_vision, mako_bringup.
COPY --chown=sim:sim src src
COPY --chown=sim:sim commands.txt commands.txt
RUN source /opt/ros/humble/setup.bash \
    && MAKEFLAGS=-j${BUILD_JOBS} CMAKE_BUILD_PARALLEL_LEVEL=${BUILD_JOBS} colcon build --base-paths src --symlink-install --executor sequential \
       --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
    && test -f /opt/ardupilot_gazebo/build/libArduPilotPlugin.so
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/mako_ws/install/robot_description/lib:/opt/ardupilot_gazebo/build \
    GZ_SIM_RESOURCE_PATH=/opt/mako_ws/install/robot_description/share:/opt/ardupilot_gazebo/models:/opt/ardupilot_gazebo/worlds
COPY --chown=sim:sim docker /opt/mako_ws/docker
# Operation MX pilot station (started with: docker/run.sh --gui).
COPY --chown=sim:sim gui/rov_gui_gst.py gui/rov_gui_gst.py
COPY --chown=sim:sim gui/mako_station gui/mako_station
COPY entrypoint.sh /entrypoint.sh
ENV MAKO_DATA_DIR=/data
RUN bash -n /entrypoint.sh && python3 -m py_compile docker/simulation.py docker/doctor.py gui/rov_gui_gst.py
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["simulation"]
