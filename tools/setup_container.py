"""Recreate only the independent Fish runtime from this repository's Docker image."""
import argparse, subprocess, json, os, grp
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',action='store_true',help='Build ROS packages and the Fish SITL firmware after creating the container.')
p.add_argument('--image',default=os.environ.get('FISH_RUNTIME_IMAGE','fish-omni-six:local'))
args=p.parse_args();root=Path(__file__).resolve().parents[1];name=os.environ.get('FISH_CONTAINER_NAME','fish-omni-six')
def run(a,**kw):return subprocess.run(a,check=True,**kw)
exists=subprocess.run(['docker','inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
if exists:
 info=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
 mounts={item['Destination']:item['Source'] for item in info.get('Mounts',[])}
 if Path(mounts.get('/opt/mako_ws','/')).resolve()!=root:
  raise SystemExit('Existing container belongs to another workspace. Set FISH_CONTAINER_NAME to a new name.')
if not exists:
 if subprocess.run(['docker','image','inspect',args.image],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  raise SystemExit('Build the image first: docker build -t '+args.image+' . (see README.md)')
 for d in ['data','.runtime']:(root/d).mkdir(exist_ok=True)
 (root/'.runtime/mako.xauth').touch(exist_ok=True)
 (root/'.runtime/mako.xauth').chmod(0o600)
 # Bind-mounting input nodes alone does not allow opening them. Linux input
 # major 13 also covers gamepads reconnected after the container starts.
 command=['docker','run','-d','--name',name,'--init','--entrypoint','/bin/sleep','--gpus','all','--network','host','--ipc','host','--user',f'{os.getuid()}:{os.getgid()}','--device-cgroup-rule','c 13:* rmw']
 try:command+=['--group-add',str(grp.getgrnam('input').gr_gid)]
 except KeyError:pass
 for source,target,readonly in [(root,'/opt/mako_ws',False),(root/'data','/data',False),('/tmp/.X11-unix','/tmp/.X11-unix',True),(root/'.runtime/mako.xauth','/tmp/mako.xauth',True),('/dev/input','/dev/input',True),('/run/udev','/run/udev',True)]:
  if not Path(source).exists():continue
  command+=['--mount',f'type=bind,source={source},target={target}'+(',readonly' if readonly else '')]
 env={'DISPLAY':os.environ.get('DISPLAY',':1'),'XAUTHORITY':'/tmp/mako.xauth','ROS_DOMAIN_ID':'73','MAKO_SIM_ROS_DOMAIN_ID':'73','MAKO_WORKSPACE':'/opt/mako_ws','MAKO_ARDUPILOT':'/opt/ardupilot','MAKO_ARDUPILOT_GAZEBO':'/opt/ardupilot_gazebo','MAKO_DATA_DIR':'/data','XDG_CONFIG_HOME':'/data/config','XDG_CACHE_HOME':'/data/cache','XDG_DATA_HOME':'/data/share','NVIDIA_DRIVER_CAPABILITIES':'all','__EGL_VENDOR_LIBRARY_FILENAMES':'/usr/share/glvnd/egl_vendor.d/10_nvidia.json','LIBGL_ALWAYS_SOFTWARE':'0','RMW_IMPLEMENTATION':'rmw_fastrtps_cpp','QT_X11_NO_MITSHM':'1'}
 for k,v in env.items():command+=['--env',k+'='+v]
 command+=[args.image,'infinity'];run(command)
run(['docker','start',name],stdout=subprocess.DEVNULL)
vendor={'file_format_version':'1.0.0','ICD':{'library_path':'libEGL_nvidia.so.0'}}
code="from pathlib import Path;Path('/usr/share/glvnd/egl_vendor.d/10_nvidia.json').write_text("+repr(json.dumps(vendor))+')'
run(['docker','exec','--user','0',name,'python3','-c',code])
if args.build:
 run(['docker','exec',name,'bash','-c','source /opt/ros/humble/setup.bash && python3 /opt/mako_ws/tools/calibrate_allocation.py && cd /opt/mako_ws && colcon build --symlink-install --base-paths src --parallel-workers 3 && python3 tools/build_fish_firmware.py'])
print('Fish runtime ready. Run '+str(root/'run-fish.sh'))
