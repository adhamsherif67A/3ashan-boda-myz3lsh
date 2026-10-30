"""Reuse the original process supervisor with the independent mapping launch."""
import importlib.util
import sys
spec=importlib.util.spec_from_file_location('mako_simulation','/opt/mako_ws/docker/simulation.py')
simulation=importlib.util.module_from_spec(spec);spec.loader.exec_module(simulation)
original_plan=simulation.plan
def plan(*args,**kwargs):
    jobs=original_plan(*args,**kwargs)
    for name,command in jobs:
        if name=='Gazebo':command[2:4]=['mako_pool_mapping','mapping_sim.launch.py']
    return jobs
simulation.plan=plan
if __name__=='__main__':sys.exit(simulation.main())
