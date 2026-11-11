#!/usr/bin/env python3
"""Start and supervise the complete simulation, without the desktop app."""
import argparse,os,shlex,signal,socket,subprocess,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path


def parse_commands(path):
    lines=[shlex.split(line,comments=True) for line in path.read_text().replace('\\\n',' ').splitlines() if line.strip()]
    sitl=next(args for args in lines if args and Path(args[0]).name=='sim_vehicle.py')
    mavros=next(args for args in lines if args[:4]==['ros2','launch','mavros','apm.launch'])
    return list(sitl),list(mavros)


def plan(workspace,autopilot,world,odometry,headless,rate,instance=0,slam=False,pilot=False,gamepad=True,profile='balanced'):
    sitl,mavros=parse_commands(workspace/'commands.txt')
    sitl[0]=str(autopilot/'Tools/autotest/sim_vehicle.py')
    if instance:
        sitl+=['-I',str(instance)]
        for old,new in [(14550,14550+10*instance),(14551,14551+10*instance)]:
            sitl=[arg.replace('127.0.0.1:'+str(old),'127.0.0.1:'+str(new)) for arg in sitl]
            mavros=[arg.replace('127.0.0.1:'+str(old),'127.0.0.1:'+str(new)) for arg in mavros]
    sitl+=['--add-param-file',str(workspace/'src/mako_control/config/ardusub_external_nav.parm'),
           '--mavproxy-args=--non-interactive','--no-extra-ports']
    if slam:odometry='vision'
    gazebo=['ros2','launch','mako_bringup','simulation.launch.py',
            'world:='+world,'odometry_source:='+odometry,'configure_ardusub:=false',
            'headless:='+str(headless).lower(),'pilot_fps:='+str(rate),
            'performance_profile:='+profile,'slam:='+str(slam).lower(),
            'sitl_port_in:='+str(9002+10*instance),'sitl_port_out:='+str(9003+10*instance)]
    jobs=[('SITL',sitl),('MAVROS',mavros),('Gazebo',gazebo)]
    if pilot:
        jobs.append(('Pilot',['ros2','launch','mako_control','pilot.launch.py','joystick:='+str(gamepad).lower()]))
    return jobs


def stop(jobs):
    for sig,timeout in [(signal.SIGINT,5),(signal.SIGTERM,3),(signal.SIGKILL,1)]:
        for process in jobs:
            try:os.killpg(process.pid,sig)
            except ProcessLookupError:pass
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            alive=False
            for process in jobs:
                process.poll()
                try:os.killpg(process.pid,0);alive=True
                except ProcessLookupError:pass
            if not alive:break
            time.sleep(.1)
    for process in jobs:
        try:process.wait(timeout=1)
        except subprocess.TimeoutExpired:pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world',choices=['pool.world','ocean.world'],default='pool.world')
    parser.add_argument('--odometry-source',choices=['ground_truth','vision'],default='ground_truth')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--pilot-fps',type=int,choices=[30,60],default=30)
    parser.add_argument('--performance-profile',choices=['maximum_fps','balanced','vision_quality','full_sensors'],default='balanced',
                        help='Camera resolution/rate profile')
    parser.add_argument('--slam',action='store_true',help='RTAB-Map SLAM (implies --odometry-source vision)')
    parser.add_argument('--pilot',action='store_true',help='Start realjoy_node and the gamepad driver so a gamepad flies the ROV')
    parser.add_argument('--no-gamepad',action='store_true',help='With --pilot, start realjoy_node without the joy gamepad driver')
    parser.add_argument('--log-dir',type=Path)
    parser.add_argument('--instance',type=int,default=0,choices=range(11),help='Separate SITL/UDP port offset for concurrent tests')
    parser.add_argument('--dry-run',action='store_true',help='Print commands without starting processes')
    args=parser.parse_args()
    workspace=Path(os.environ.get('MAKO_WORKSPACE','/opt/mako_ws'))
    autopilot=Path(os.environ.get('MAKO_ARDUPILOT','/opt/ardupilot'))
    jobs=plan(workspace,autopilot,args.world,args.odometry_source,args.headless,args.pilot_fps,args.instance,
              slam=args.slam,pilot=args.pilot,gamepad=not args.no_gamepad,profile=args.performance_profile)
    if args.dry_run:
        for name,command in jobs:print(name+': '+shlex.join(command))
        return 0
    if not args.headless and not os.environ.get('DISPLAY'):
        parser.error('Gazebo GUI needs DISPLAY. Use docker/run.sh or --headless.')
    for port,kind in [(9002+10*args.instance,socket.SOCK_DGRAM),(9003+10*args.instance,socket.SOCK_DGRAM),(14551+10*args.instance,socket.SOCK_DGRAM),(5760+10*args.instance,socket.SOCK_STREAM)]:
        with socket.socket(socket.AF_INET,kind) as probe:
            if kind==socket.SOCK_STREAM:probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            try:probe.bind(('127.0.0.1',port))
            except OSError:parser.error(f'Port {port} is occupied. Stop the existing SITL/MAVROS session.')
    folder=args.log_dir or Path.home()/'mako-runs'/datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    folder.mkdir(parents=True,exist_ok=True)
    sitl_folder=folder/'sitl';sitl_folder.mkdir()
    jobs[0][1].extend(['--use-dir',str(sitl_folder)])
    env=os.environ.copy();env.setdefault('GZ_PARTITION','mako_'+uuid.uuid4().hex)
    env['ROS_LOG_DIR']=str(folder/'ros')
    sitl_env=env.copy()
    for key in ['DISPLAY','WAYLAND_DISPLAY','TMUX','STY','ZELLIJ']:sitl_env.pop(key,None)
    sitl_env.update(SITL_RITW_TERMINAL='/bin/bash',TMPDIR=str(sitl_folder))
    import psutil  # Required by sim_vehicle to scope cleanup to its own session.
    stopping=False;processes=[]
    def request_stop(signum,frame):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGINT,request_stop);signal.signal(signal.SIGTERM,request_stop)
    code=0
    print('Logs:',folder,flush=True)
    try:
        for name,command in jobs:
            if stopping:break
            print('Starting '+name+': '+shlex.join(command),flush=True)
            processes.append(subprocess.Popen(command,cwd=folder,env=sitl_env if name=='SITL' else env,start_new_session=True))
        while not stopping:
            for (name,_),process in zip(jobs,processes):
                if process.poll() is not None:
                    print(f'{name} exited with code {process.returncode}; stopping session',file=sys.stderr,flush=True)
                    code=process.returncode or 1;stopping=True;break
            time.sleep(.25)
    finally:stop(processes)
    return code

if __name__=='__main__':sys.exit(main())
