cmake_minimum_required(VERSION 3.8)
project(mako_vision)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Importable helpers, e.g. from mako_vision.transect_detector import detect_transect
ament_python_install_package(${PROJECT_NAME})

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})
install(FILES ZED_VO.md DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/zed_to_mavros_pose.py DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(transect_detector test/test_transect_detector.py)
endif()

ament_package()
