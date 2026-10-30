"""Run simulation + standalone mapping, optionally drive and record a real demo."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
import uuid

STOP=False
def stop(_sig,_frame):
    global STOP
    STOP=True

def stop_group(p):
    for sig,timeout in [(signal.SIGINT,30),(signal.SIGTERM,3),(signal.SIGKILL,2)]:
        try:
            if sig==signal.SIGINT:p.send_signal(sig)
            else:os.killpg(p.pid,sig)
        except ProcessLookupError:return
        try:p.wait(timeout=timeout);return
        except subprocess.TimeoutExpired:pass

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true',help='Drive two closed loops in simulation')
    parser.add_argument('--record',action='store_true',help='Record only the mapping RViz window')
    parser.add_argument('--size',type=float,default=2.)
    parser.add_argument('--laps',type=int,default=2)
    parser.add_argument('--no-rviz',action='store_true')
    parser.add_argument('--world',choices=['pool.world','ocean.world'],default='pool.world')
    parser.add_argument('--route',choices=['rectangle','yaw','coverage'],default='rectangle')
    args=parser.parse_args()
    if args.record and args.no_rviz:parser.error('Recording requires RViz')
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    output=Path('/data');output.mkdir(exist_ok=True)
    (output/'session_metadata.json').write_text(json.dumps({
        'arguments':vars(args),'ros_domain_id':os.environ.get('ROS_DOMAIN_ID'),
        'middleware':os.environ.get('RMW_IMPLEMENTATION'),
        'slam_odometry':'independent RGB-D visual odometry; no ground truth input',
        'reference':'Gazebo odometry is used only for driving/evaluation',
        'sensor_overlay':'Remove only camera_dome visual in generated world; collisions and sensor poses unchanged'},indent=2)+'\n')
    shutil.copyfile('/mapping_package/launch/pool_mapping.launch.py',output/'configuration.launch.py')
    shutil.copyfile('/mapping_package/launch/mapping_sim.launch.py',output/'configuration.simulation.launch.py')
    shutil.copyfile('/mapping_package/mako_pool_mapping/sensor_world.py',output/'configuration.sensor_world.py')
    ws=Path('/tmp/pool_mapping_ws');(ws/'src').mkdir(parents=True,exist_ok=True)
    shutil.copytree('/mapping_package',ws/'src/mako_pool_mapping',dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    with (output/'build.log').open('w') as log:
        subprocess.run(['colcon','build','--base-paths','src','--packages-select','mako_pool_mapping'],
                       cwd=ws,stdout=log,stderr=subprocess.STDOUT,check=True)
    env=os.environ.copy();env.setdefault('GZ_PARTITION','mako_mapping_'+uuid.uuid4().hex);env['ROS_LOG_DIR']=str(output/'ros')
    processes=[];logs=[]
    def start(name,command):
        log=(output/(name+'.log')).open('w');logs.append(log)
        p=subprocess.Popen(command,cwd=ws,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        processes.append((name,p));print('Started '+name,flush=True);return p
    def overlay(command):
        return ['bash','-c','source /tmp/pool_mapping_ws/install/setup.bash; exec "$@"','bash',*command]
    simulation=mapping=video=driver=None
    try:
        simulation=start('simulation',overlay(['python3','/mapping_package/scripts/simulation_overlay.py','--world',args.world]))
        print('Waiting 15 seconds for simulator/IMU/buoyancy initialization before starting visual odometry.',flush=True)
        settle_until=time.monotonic()+15
        while time.monotonic()<settle_until:
            if STOP:return
            if simulation.poll() is not None:raise RuntimeError('Simulation exited during initialization')
            time.sleep(.2)
        mapping=start('mapping',overlay(['ros2','launch','mako_pool_mapping','pool_mapping.launch.py',
                                        'output_dir:=/data','rviz:='+str(not args.no_rviz).lower()]))
        if args.record:
            deadline=time.monotonic()+60;window=None
            while not STOP and time.monotonic()<deadline:
                result=subprocess.run(['xwininfo','-root','-tree'],capture_output=True,text=True)
                for line in result.stdout.splitlines():
                    if 'pool_mapping.rviz' in line:
                        match=re.search(r'0x[0-9a-fA-F]+',line)
                        if match:window=match.group();break
                if window:break
                if mapping.poll() is not None:raise RuntimeError('Mapping launch exited; check mapping.log')
                time.sleep(.5)
            if not window:raise RuntimeError('Mapping RViz window not found for recording')
            video=start('recording',['ffmpeg','-y','-f','x11grab','-framerate','15','-window_id',window,
              '-i',env['DISPLAY'],'-vf','scale=1280:-2','-c:v','libx264','-preset','veryfast',
              '-pix_fmt','yuv420p','/data/loop_closure_demo.mp4'])
        if args.demo:
            driver=start('drive',overlay(['ros2','run','mako_pool_mapping','drive_pool_loop',
              '--size',str(args.size),'--laps',str(args.laps),'--route',args.route,
              '--ros-args','-p','use_sim_time:=true']))
        print('Mapping is live. Outputs: /data. Ctrl+C saves database and exports map.',flush=True)
        while not STOP:
            if simulation.poll() is not None or mapping.poll() is not None:
                raise RuntimeError('Simulation/mapping process exited; inspect logs')
            if video is not None and video.poll() is not None:raise RuntimeError('Video recorder exited; inspect recording.log')
            if driver is not None and driver.poll() is not None:
                if driver.returncode:raise RuntimeError('Demo failed; inspect drive.log')
                break
            time.sleep(.5)
    finally:
        # Stop driver first (it requests disarm), then flush RTAB-Map's database.
        if driver is not None:stop_group(driver)
        if mapping is not None:stop_group(mapping)
        if video is not None:stop_group(video)
        if simulation is not None:stop_group(simulation)
        for log in logs:log.close()
        if (output/'pool.db').exists():
            with (output/'export.log').open('w') as log:
                result=subprocess.run(['rtabmap-export','--cloud','--poses','--opt','2',
                  '--max_range','14','--voxel','.05','--output','pool_optimized',
                  '--output_dir','/data','/data/pool.db'],stdout=log,stderr=subprocess.STDOUT)
            print('Map export exit code: '+str(result.returncode),flush=True)
            with (output/'export_raw.log').open('w') as log:
                subprocess.run(['rtabmap-export','--poses','--opt','3','--output','pool_raw',
                  '--output_dir','/data','/data/pool.db'],stdout=log,stderr=subprocess.STDOUT)
            subprocess.run(['python3','/mapping_package/scripts/validate.py','/data'],check=False)
            if (output/'pool_optimized_cloud.ply').exists():
                subprocess.run(['python3','/mapping_package/scripts/coverage.py','/data'],check=False)
        if (output/'summary.json').exists():print((output/'summary.json').read_text(),flush=True)

if __name__=='__main__':main()
