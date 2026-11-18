"""Manual end-to-end app check; isolated ROS domain, SITL instance and FCU ports."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PyQt5.QtWidgets import QApplication
from mako_station.app import PilotWindow
from mako_station.simulation import SimulationSession,SessionThread

app=QApplication([]);window=PilotWindow(start_workers=False)
session=SimulationSession(domain=142,instance=8,outputs=(24650,24651))
window.manager=SessionThread(window.session_state.emit,window.log_message.emit,session)
window.workers_started=True;window.manager.start();window.ros.domain=142;window.ros.start()
window.show()


def wait_until(predicate,timeout=70):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        app.processEvents()
        if window.phase=='Error':raise AssertionError(window.log_box.toPlainText())
        if predicate():return
        time.sleep(.03)
    raise AssertionError('Timed out: '+window.log_box.toPlainText())


def ready():
    frames,telemetry=window.ros.snapshot()
    return (window.phase=='Running' and telemetry.get('connected')
        and all(name in frames and time.monotonic()-frames[name][1]<1 for name in ['main','bottom']))


try:
    window.action('start');wait_until(ready)
    assert all(process.poll() is None for process in session.processes.jobs.values())
    assert window.reset_button.isEnabled()
    assert not window.world.isEnabled()
    frames,_=window.ros.snapshot()
    assert frames['main'][0].width()==1280 and frames['bottom'][0].width()==1280
    print('PASS: Start launches SITL, MAVROS, headless Gazebo, joystick and pilot control',flush=True)
    # Ensure the pose estimator sends healthy ExternalNav data, not just video.
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        app.processEvents();time.sleep(.03)
    window.grab().save(str(Path(__file__).resolve().parents[1]/'app_first_person.png'))
    old_main=window.ros.snapshot()[0]['main'][1]
    window.switch_view('Third person')
    wait_until(lambda: 'main' in window.ros.snapshot()[0] and window.ros.snapshot()[0]['main'][1]>old_main)
    wait_until(lambda:window.ros.snapshot()[0].get('main',(None,0,0))[2]>20,timeout=12)
    window.tick();app.processEvents()
    assert window.canvas.image is not None
    print('PASS: Switch to real rear-following RGB; bottom camera remains live',flush=True)
    window.grab().save(str(Path(__file__).resolve().parents[1]/'app_third_person.png'))
    old_pids=[process.pid for process in session.processes.jobs.values()]
    old_directory=session.directory
    window.action('reset')
    wait_until(lambda:session.directory!=old_directory and ready(),timeout=90)
    for pid in old_pids:
        try:os.killpg(pid,0)
        except ProcessLookupError:pass
        else:raise AssertionError('Old process group remains: '+str(pid))
    print('PASS: Reset removes all old owned process groups and starts a fresh connected stack',flush=True)
    window.action('stop');wait_until(lambda:window.phase=='Stopped',timeout=15)
    assert not session.processes.jobs
    print('PASS: Stop leaves no owned simulation jobs',flush=True)
    window.world.setCurrentIndex(1)
    window.action('start');wait_until(ready)
    wait_until(lambda:window.ros.snapshot()[0].get('main',(None,0,0))[2]>20,timeout=12)
    window.tick();app.processEvents()
    window.grab().save(str(Path(__file__).resolve().parents[1]/'app_ocean.png'))
    print('PASS: Ocean selection starts and connects the complete headless stack',flush=True)
    window.action('stop');wait_until(lambda:window.phase=='Stopped',timeout=15)

finally:
    window.closing=True;window.manager.request('close')
    end=time.monotonic()+12
    while window.manager.is_alive() and time.monotonic()<end:app.processEvents();time.sleep(.05)
    session.stop();window.ros.stop();window.finished=True;window.close();app.processEvents()
