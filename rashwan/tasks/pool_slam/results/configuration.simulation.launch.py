"""Reuse the simulation launch with a sensor-only visibility overlay."""
import importlib.util
from pathlib import Path
from mako_pool_mapping.sensor_world import repair_depth_cover
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    path=Path(get_package_share_directory('robot_description'))/'launch/gazebo.launch.py'
    spec=importlib.util.spec_from_file_location('original_mako_gazebo',path)
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    prepare=original.prepare_world
    def prepare_world(*args,**kwargs):
        path=prepare(*args,**kwargs)
        removed=repair_depth_cover(path)
        print('Mapping depth repair: omitted protective render cover '+', '.join(removed),flush=True)
        return path
    original.prepare_world=prepare_world
    return original.generate_launch_description()
