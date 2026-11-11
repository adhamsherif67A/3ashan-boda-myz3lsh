cmake_minimum_required(VERSION 3.8...3.28)

project(robot_description)

find_package(ament_cmake REQUIRED)
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)
find_package(gz-transport13 REQUIRED)
add_library(mako-pool-waves SHARED src/PoolWaves.cc)
target_compile_features(mako-pool-waves PRIVATE cxx_std_17)
target_link_libraries(mako-pool-waves PRIVATE gz-sim8::gz-sim8
  gz-plugin2::register gz-transport13::gz-transport13)
install(TARGETS mako-pool-waves LIBRARY DESTINATION lib)

# Install directories into the share path
install(
    DIRECTORY config launch meshes urdf worlds
    DESTINATION share/${PROJECT_NAME}
)

install(
    FILES package.xml TF2_MODEL.md ZED2I_SIM.md
    DESTINATION share/${PROJECT_NAME}
)

install(
    PROGRAMS
        scripts/check_sim_tf.py
        scripts/cloud_frame_relay.py
  scripts/sim_rgbd_camera_info.py
        scripts/odom_to_depth.py
    DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(camera_calibration test/test_camera_calibration.py)
  ament_add_pytest_test(model_frames test/test_model_frames.py)
  ament_add_pytest_test(reset_world test/test_reset_world.py)
endif()

ament_package()
