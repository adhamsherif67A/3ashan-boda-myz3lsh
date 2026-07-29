FROM ros:humble

WORKDIR /ros2_ws

COPY . /ros2_ws/src/marine_xperts_depth/

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

CMD ["/bin/bash"]