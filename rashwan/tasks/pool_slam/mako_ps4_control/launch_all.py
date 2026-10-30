#!/usr/bin/env python3
"""Supervise Mako simulation, RGB-D mapping, RViz, QGC and PS4 motion."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

PACKAGE = Path(__file__).resolve().parent
MAPPING_PACKAGE = PACKAGE.parent/'mako_pool_mapping'
STOP = False


def stop_requested(_signum, _frame):
    global STOP
    STOP = True


def run(command, timeout=15):
    return subprocess.run(command, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def resolve_qgc(explicit=None):
    config = PACKAGE / 'launcher-config.json'
    saved = json.loads(config.read_text()).get('qgroundcontrol') if config.exists() else None
    choices = [explicit, os.environ.get('MAKO_QGROUNDCONTROL'), saved,
               shutil.which('QGroundControl'), shutil.which('qgroundcontrol')]
    choices.extend(sorted((PACKAGE/'apps').glob('*.AppImage')))
    for directory in [Path.home(), Path.home()/'Downloads', Path.home()/'Applications',
                      Path.home()/'Desktop', Path('/opt')]:
        choices.extend(sorted(directory.glob('*[Qq][Gg]round*[Aa]pp[Ii]mage')))
    for choice in choices:
        if choice:
            path = Path(choice).expanduser().resolve()
            if path.is_file() and os.access(path, os.X_OK):
                if explicit:
                    config.write_text(json.dumps({'qgroundcontrol':str(path)}, indent=2)+'\n')
                return path
            if explicit and str(choice)==explicit:
                raise RuntimeError(f'QGroundControl is missing or not executable: {path}')
    raise RuntimeError('QGroundControl executable not found. Run with --qgroundcontrol /absolute/path/to/QGroundControl.AppImage; this path will be remembered.')


class Session:
    def __init__(self, args):
        self.args = args
        self.container = os.environ.get('MAKO_CONTAINER_NAME', 'mako-sim')
        self.container_id = None
        self.processes = []
        self.logs = []
        self.env = os.environ.copy()
        self.env.update(ROS_DOMAIN_ID=os.environ.get('ROS_DOMAIN_ID','42'),
                        RMW_IMPLEMENTATION='rmw_fastrtps_cpp')
        self.folder = PACKAGE/'runs'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        self.env['ROS_LOG_DIR']=str(self.folder/'ros-host')
        self.mapping_enabled=not getattr(args,'no_mapping',False)
        if self.mapping_enabled:
            self.env.update(POOL_CONTAINER_NAME=self.container,
                            POOL_OUTPUT_DIR=str(self.folder/'mapping'),
                            POOL_IMAGE=self.env.get('POOL_IMAGE','marinexperts/mako-pool-mapping:boda'))

    def inside(self, *args):
        return ['docker','exec',self.container,'/bin/bash','/entrypoint.sh',*args]

    def preflight(self):
        self.qgc = resolve_qgc(self.args.qgroundcontrol)
        for executable in ['docker','bash','flock','xauth']:
            if not shutil.which(executable):
                raise RuntimeError(f'Missing host command: {executable}')
        if not self.env.get('DISPLAY'):
            raise RuntimeError('Run from your Ubuntu desktop terminal: DISPLAY is missing.')
        if not (self.args.repo/'docker/run.sh').is_file():
            raise RuntimeError(f'Cannot find docker/run.sh in {self.args.repo}')
        if self.mapping_enabled and not (MAPPING_PACKAGE/'scripts/run.sh').is_file():
            raise RuntimeError(f'Mapping package missing: {MAPPING_PACKAGE}. Keep both package folders together, or use --no-mapping.')
        if not Path('/opt/ros/humble/lib/joy/game_controller_node').exists():
            raise RuntimeError('Host ROS Humble joy/game_controller_node is missing.')
        result = run(['docker','info','--format','{{json .Runtimes}}'])
        if result.returncode or 'nvidia' not in json.loads(result.stdout):
            raise RuntimeError('Docker NVIDIA runtime is not available: '+result.stdout)
        existing = run(['docker','container','inspect',self.container])
        if existing.returncode==0:
            raise RuntimeError(f'Container {self.container} already exists. Stop your previous simulation before launching. It has not been changed.')
        if self.mapping_enabled:
            other=run(['docker','inspect','--format','{{.State.Running}}','mako-pool-sim'])
            if other.returncode==0 and other.stdout.strip()=='true':
                raise RuntimeError('The standalone mako-pool-sim is running. Stop it before starting the combined launcher.')
        image = self.env['POOL_IMAGE'] if self.mapping_enabled else self.env.get('MAKO_IMAGE','marinexperts/mako:boda')
        if run(['docker','image','inspect',image]).returncode:
            raise RuntimeError(f'Docker image {image} is missing. '+
                               (f'Run: bash {MAPPING_PACKAGE}/scripts/install.sh' if self.mapping_enabled else 'Build the original image first.'))

    def start(self, name, command, env=None):
        self.folder.mkdir(parents=True, exist_ok=True)
        log = (self.folder/(name+'.log')).open('w')
        self.logs.append(log)
        process = subprocess.Popen(command, env=env or self.env, cwd=self.args.repo,
                                   stdin=subprocess.DEVNULL, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        self.processes.append((name,process))
        print(f'Starting {name}: {self.folder/(name+".log")}', flush=True)
        return process

    def check_processes(self):
        if STOP:
            raise KeyboardInterrupt
        for name, process in self.processes:
            if process.poll() is not None:
                raise RuntimeError(f'{name} exited ({process.returncode}). See {self.folder/(name+".log")}')

    def wait_container(self):
        deadline = time.monotonic()+60
        while time.monotonic()<deadline:
            result = run(['docker','inspect','--format','{{.Id}} {{.State.Running}}',self.container])
            if result.returncode==0:
                fields=result.stdout.strip().split()
                self.container_id=fields[0]
                if len(fields)==2 and fields[1]=='true':
                    return
            self.check_processes()
            time.sleep(0.5)
        raise RuntimeError('Timed out waiting for simulation container.')

    def wait_mavros(self):
        print('Waiting for connected MAVROS (up to 120 seconds)...', flush=True)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            self.check_processes()
            try:
                result=run(self.inside('timeout','6s','ros2','topic','echo','/mavros/state','--once'),timeout=8)
                if result.returncode==0 and 'connected: true' in result.stdout:
                    return
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.5)
        raise RuntimeError('MAVROS connection timed out. Check gazebo.log.')

    def launch(self):
        if self.mapping_enabled:
            command=['bash',str(MAPPING_PACKAGE/'scripts/run.sh'),'--world',self.args.world]
            if getattr(self.args,'record_mapping',False):command.append('--record')
        else:
            command=['bash',str(self.args.repo/'docker/run.sh'),'--nvidia','--world',self.args.world]
        self.start('gazebo',command)
        self.wait_container()
        self.wait_mavros()
        build=self.start('build',['bash',str(PACKAGE/'build_in_sim.sh')])
        while build.poll() is None:
            if STOP:
                raise KeyboardInterrupt
            for name,process in self.processes:
                if name!='build' and process.poll() is not None:
                    raise RuntimeError(f'{name} exited while building controller.')
            time.sleep(0.2)
        self.processes=[(n,p) for n,p in self.processes if p is not build]
        if build.returncode:
            raise RuntimeError(f'Controller build/tests failed. See {self.folder/"build.log"}')
        if self.mapping_enabled:
            print('Waiting for the first RTAB-Map node...',flush=True)
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                self.check_processes()
                try:
                    result=run(self.inside('timeout','6s','ros2','topic','echo',
                        '/pool_mapping/info','--once','--field','ref_id'),timeout=8)
                    if result.returncode==0 and any(line.strip().isdigit() and int(line)>0 for line in result.stdout.splitlines()):
                        break
                except subprocess.TimeoutExpired:
                    pass
                time.sleep(.5)
            else:raise RuntimeError('RTAB-Map did not produce a map node; check mapping logs.')
            print('RTAB-Map live. Database and map will be saved in '+str(self.folder/'mapping'),flush=True)
        self.start('rviz',self.inside('ros2','launch','robot_description','view_tf.launch.py'))
        qgc_env=self.env.copy()
        # AppImage supports this fallback without a FUSE mount or host changes.
        if self.qgc.suffix.lower()=='.appimage':
            qgc_env['APPIMAGE_EXTRACT_AND_RUN']='1'
        if self.args.qgc_software:
            qgc_env['QT_QUICK_BACKEND']='software'
        self.start('qgroundcontrol',[str(self.qgc)],env=qgc_env)
        self.start('ps4',['bash',str(PACKAGE/'run_joy_host.sh')])
        self.start('motion',['bash',str(PACKAGE/'run_motion.sh'),'-p','invert_lateral:=false'])
        print('Running. Options = arm/disarm. Ctrl+C stops this session. Logs: '+str(self.folder),flush=True)
        while True:
            self.check_processes()
            time.sleep(0.3)

    def cleanup(self):
        if not self.processes:
            return
        print('Stopping this session...',flush=True)
        if self.container_id:
            try:
                # Never target a replacement container that reuses the name.
                result=run(['docker','exec',self.container_id,'/bin/bash','/entrypoint.sh',
                            'ros2','service','call','/mavros/cmd/arming',
                            'mavros_msgs/srv/CommandBool','{value: false}'],timeout=5)
                if result.returncode or 'success: true' not in result.stdout:
                    print('Disarm was not confirmed; stopping the owned simulation.',flush=True)
            except (subprocess.TimeoutExpired,OSError):
                pass
        # Stop controller/driver and GUI processes before stopping their simulation.
        for name,process in reversed(self.processes):
            if name=='gazebo':
                continue
            self.stop_process(process)
        saved=False
        if self.mapping_enabled and self.container_id:
            print('Saving RTAB-Map database and exporting the 3D cloud. Please wait...',flush=True)
            try:
                result=run(['docker','kill','--signal=SIGINT',self.container_id])
                if result.returncode==0:
                    simulator=next((p for n,p in self.processes if n=='gazebo'),None)
                    if simulator is not None:
                        simulator.wait(timeout=180)
                        saved=True
                        print('Mapping session finished. Saved outputs: '+str(self.folder/'mapping'),flush=True)
            except (subprocess.TimeoutExpired,OSError):
                print('Graceful map save timed out; inspect the mapping logs.',flush=True)
        if self.container_id and not saved:
            try:
                run(['docker','stop','--time','15',self.container_id],timeout=22)
            except (subprocess.TimeoutExpired,OSError):
                pass
        for name,process in self.processes:
            if name=='gazebo':
                self.stop_process(process)
        for log in self.logs:
            log.close()

    @staticmethod
    def stop_process(process):
        for sig,timeout in [(signal.SIGINT,3),(signal.SIGTERM,2),(signal.SIGKILL,1)]:
            try:
                os.killpg(process.pid,sig)
            except ProcessLookupError:
                return
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                continue
            # Group children can outlive the group leader; finish group cleanup.
            try:
                os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            return


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path.home()/'MarineXperts-Season-2027')
    parser.add_argument('--world',choices=['pool.world','ocean.world'],default='pool.world')
    parser.add_argument('--qgroundcontrol',help='QGroundControl executable/AppImage (remembered)')
    parser.add_argument('--check',action='store_true',help='Validate prerequisites without launching')
    parser.add_argument('--qgc-software',action='store_true',help='Use software drawing only for QGroundControl; Gazebo still uses NVIDIA')
    parser.add_argument('--no-mapping',action='store_true',help='Original five-component session without RTAB-Map')
    parser.add_argument('--record-mapping',action='store_true',help='Also record the mapping RViz window')
    args=parser.parse_args()
    if args.no_mapping and args.record_mapping:parser.error('--record-mapping requires mapping')
    args.repo=args.repo.expanduser().resolve()
    signal.signal(signal.SIGINT,stop_requested)
    signal.signal(signal.SIGTERM,stop_requested)
    with (PACKAGE/'.launch.lock').open('w') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print('This launcher is already running.',file=sys.stderr)
            return 1
        session=Session(args)
        try:
            session.preflight()
            if args.check:
                print('Prerequisites ready. QGroundControl: '+str(session.qgc))
            else:
                session.launch()
            return 0
        except KeyboardInterrupt:
            return 0
        except (RuntimeError,OSError,ValueError,subprocess.TimeoutExpired) as error:
            print('ERROR: '+str(error),file=sys.stderr)
            return 1
        finally:
            session.cleanup()


if __name__=='__main__':
    sys.exit(main())
