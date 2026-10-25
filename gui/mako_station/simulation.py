"""Manage only the simulation session launched by this application."""
import fcntl
import os
from pathlib import Path
import queue
import shlex
import signal
import socket
import subprocess
import threading
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo


WORKSPACE = Path(os.environ.get('MAKO_WORKSPACE', Path.home()/'mako_ws'))
SOFTWARE = Path(os.environ.get('MAKO_SOFTWARE_WORKSPACE', Path.home()/'Software2026'))
ARDUPILOT = Path(os.environ.get('MAKO_ARDUPILOT', Path.home()/'ardupilot'))
DOMAIN = int(os.environ.get('MAKO_SIM_ROS_DOMAIN_ID', '42'))


def commands_from_file(path):
    """Read the two user-specified commands as arguments, never eval shell text."""
    text=Path(path).read_text().replace('\\\n',' ')
    lines=[shlex.split(line,comments=True) for line in text.splitlines() if line.strip()]
    lines=[line for line in lines if line]
    sitl=next((line for line in lines if Path(line[0]).name=='sim_vehicle.py'),None)
    mavros=next((line for line in lines if line[:4]==['ros2','launch','mavros','apm.launch']),None)
    if not sitl or not mavros:
        raise RuntimeError('commands.txt must contain sim_vehicle.py and ros2 launch mavros apm.launch')
    return list(sitl),list(mavros)


def source_environment(workspace=WORKSPACE,software=SOFTWARE):
    sources=[Path('/opt/ros/humble/setup.bash'),workspace/'install/setup.bash',software/'install/local_setup.bash']
    missing=[str(p) for p in sources if not p.exists()]
    if missing:raise RuntimeError('Missing ROS workspace setup: '+', '.join(missing))
    command='\n'.join('source '+shlex.quote(str(p)) for p in sources)+'\nenv -0'
    result=subprocess.run(['bash','-c',command],capture_output=True,check=True,timeout=15)
    return dict(item.split('=',1) for item in result.stdout.decode().split('\0') if '=' in item)


class OwnedProcesses:
    """Each command has its own group, including its launch/script descendants."""
    def __init__(self):
        self.jobs={}
        self.logs=[]

    def spawn(self,name,arguments,cwd,env,log_path):
        log=open(log_path,'ab',buffering=0)
        self.logs.append(log)
        process=subprocess.Popen(arguments,cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                                 stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        self.jobs[name]=process
        return process

    def stop(self):
        # Signal groups even if a ros2 launcher exited before its child process.
        for sig,timeout in [(signal.SIGINT,3),(signal.SIGTERM,2),(signal.SIGKILL,1)]:
            for process in self.jobs.values():
                try:os.killpg(process.pid,sig)
                except ProcessLookupError:pass
            end=time.monotonic()+timeout
            while time.monotonic()<end:
                alive=False
                for process in self.jobs.values():
                    process.poll()
                    try:os.killpg(process.pid,0);alive=True
                    except ProcessLookupError:pass
                if not alive:break
                time.sleep(.05)
        for process in self.jobs.values():
            try:process.wait(timeout=.2)
            except subprocess.TimeoutExpired:pass
        self.jobs.clear()
        for log in self.logs:log.close()
        self.logs.clear()


class SimulationSession:
    def __init__(self,workspace=WORKSPACE,software=SOFTWARE,ardupilot=ARDUPILOT,domain=DOMAIN,instance=0,outputs=(14550,14551)):
        self.workspace,self.software,self.ardupilot=map(Path,[workspace,software,ardupilot])
        self.domain=domain;self.instance=instance;self.outputs=outputs
        self.processes=OwnedProcesses()
        self.directory=None
        self.lock=None

    def start(self,world='pool.world',odometry='vision',notify=lambda text:None):
        if self.processes.jobs:raise RuntimeError('Simulation is already running')
        if world not in ['pool.world','ocean.world'] or odometry not in ['vision','ground_truth']:
            raise ValueError('Invalid world or odometry mode')
        runs=self.workspace/'gui/runs';runs.mkdir(parents=True,exist_ok=True)
        self.lock=open(runs/'simulation.lock','a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close();self.lock=None
            raise RuntimeError('Another Mako application is already running a simulation')
        try:
            # Avoid taking over ports belonging to a manually started simulation.
            for port,kind in [(9002+10*self.instance,socket.SOCK_DGRAM),(9003+10*self.instance,socket.SOCK_DGRAM),(self.outputs[1],socket.SOCK_DGRAM),(5760+10*self.instance,socket.SOCK_STREAM)]:
                with socket.socket(socket.AF_INET,kind) as probe:
                    if kind==socket.SOCK_STREAM:probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                    try:probe.bind(('127.0.0.1',port))
                    except OSError as error:
                        raise RuntimeError(f'Port {port} is busy. Stop the existing simulation before starting this session.') from error
            sim,mavros=commands_from_file(self.workspace/'commands.txt')
            script=self.ardupilot/'Tools/autotest/sim_vehicle.py'
            if not script.exists():raise RuntimeError('ArduPilot sim_vehicle.py was not found')
            sim[0]=str(script)
            parameter_file=self.workspace/'src/robot_description/config/ardusub_external_nav.parm'
            if not parameter_file.is_file():raise RuntimeError('SITL startup parameter file was not found')
            sim+=['--add-param-file',str(parameter_file)]
            if self.instance:sim+=['-I',str(self.instance)]
            if self.outputs!=(14550,14551):
                sim=[arg.replace('127.0.0.1:14550','127.0.0.1:'+str(self.outputs[0])).replace('127.0.0.1:14551','127.0.0.1:'+str(self.outputs[1])) for arg in sim]
                mavros=[arg.replace('127.0.0.1:14551','127.0.0.1:'+str(self.outputs[1])) for arg in mavros]
            env=source_environment(self.workspace,self.software)
            env.update(ROS_DOMAIN_ID=str(self.domain),GZ_PARTITION='mako_station_'+uuid.uuid4().hex)
            env['PATH']=str(self.ardupilot/'Tools/autotest')+':'+env.get('PATH','')
            timestamp=datetime.now(ZoneInfo('Africa/Cairo')).strftime('%Y%m%d_%H%M%S')
            self.directory=runs/(timestamp+'_'+uuid.uuid4().hex[:6]);self.directory.mkdir()
            env['ROS_LOG_DIR']=str(self.directory/'ros')
            sitl_dir=self.directory/'sitl';sitl_dir.mkdir()
            sim+=['--use-dir',str(sitl_dir),'--mavproxy-args=--non-interactive','--no-extra-ports']
            # sim_vehicle's terminal helper runs the firmware under a shell in our
            # process group. No terminal emulator, map, console or detached session.
            sitl_env=env.copy()
            for key in ['DISPLAY','WAYLAND_DISPLAY','TMUX','STY','ZELLIJ']:sitl_env.pop(key,None)
            sitl_env['SITL_RITW_TERMINAL']='/bin/bash'
            sitl_env['TMPDIR']=str(sitl_dir)
            # psutil keeps sim_vehicle cleanup scoped to its own session token.
            subprocess.run(['python3','-c','import psutil'],env=sitl_env,check=True,capture_output=True)
            commands=[('SITL',sim,sitl_env),('MAVROS',mavros,env),
                      ('Gazebo',['ros2','launch','robot_description','gazebo.launch.py',
                                 'headless:=true','world:='+world,'odometry_source:='+odometry,
                                 'configure_ardusub:=false',
                                 'sitl_port_in:='+str(9002+10*self.instance),'sitl_port_out:='+str(9003+10*self.instance)],env),
                      ('Joystick',['ros2','run','joy','game_controller_node'],env),
                      ('Pilot control',['ros2','run','real_joy','realjoy_node'],env)]
            for name,argv,environment in commands:
                notify('Starting '+name+'…')
                self.processes.spawn(name,argv,self.directory,environment,self.directory/(name.lower().replace(' ','_')+'.log'))
                time.sleep(.15)
            notify('Connecting cameras and autopilot…')
        except Exception:
            self.stop()
            raise

    def failure(self):
        for name,process in self.processes.jobs.items():
            if process.poll() is not None:
                path=self.directory/(name.lower().replace(' ','_')+'.log')
                tail='\n'.join(path.read_text(errors='replace').splitlines()[-8:])
                return f'{name} stopped (exit {process.returncode}).\n{tail}\nLogs: {self.directory}'
        return None

    def stop(self):
        self.processes.stop()
        if self.lock:
            fcntl.flock(self.lock,fcntl.LOCK_UN);self.lock.close();self.lock=None


class SessionThread(threading.Thread):
    """Nonblocking UI lifecycle; resets fully stop old groups before restarting."""
    def __init__(self,changed,log,session=None):
        super().__init__(name='mako-session',daemon=True)
        self.changed,self.log=changed,log
        self.session=session or SimulationSession()
        self.requests=queue.Queue()
        self.running=False

    def request(self,action,world='pool.world',odometry='vision'):
        self.requests.put((action,world,odometry))

    def run(self):
        while True:
            try:action,world,odometry=self.requests.get(timeout=.25)
            except queue.Empty:
                if self.running:
                    failure=self.session.failure()
                    if failure:
                        self.log(failure);self.session.stop();self.running=False
                        self.changed('Error')
                continue
            try:
                if action in ['stop','reset','close']:
                    self.changed('Resetting' if action=='reset' else 'Stopping')
                    self.session.stop();self.running=False
                if action in ['start','reset']:
                    self.changed('Starting')
                    self.session.start(world,odometry,self.log)
                    self.running=True;self.changed('Running')
                    self.log('Session logs: '+str(self.session.directory))
                else:self.changed('Stopped')
                if action=='close':return
            except Exception as error:
                self.session.stop();self.running=False;self.log(str(error));self.changed('Error')
