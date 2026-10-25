"""MarineXperts Operation MX desktop pilot station."""
import os
import shutil
from pathlib import Path
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from PyQt5.QtCore import Qt,QTimer,pyqtSignal,QRectF,QProcess,QLockFile,QStandardPaths,QProcessEnvironment,QSettings
from PyQt5.QtGui import QColor,QFont,QImage,QPainter,QPixmap,QIcon
from PyQt5.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QLabel,QPushButton,QComboBox,QFrame,QGridLayout,QProgressBar,QPlainTextEdit,
    QSizePolicy,QMessageBox,QShortcut,QFileDialog)
from .simulation import WORKSPACE,DOMAIN,SessionThread
from .ros_worker import RosWorker

NAVY='#071321';PANEL='#0e2134';BORDER='#243b51';GOLD='#d6ae79';SILVER='#e6edf4';MUTED='#94a8ba'
STYLE=f'''
QWidget {{ background:{NAVY}; color:{SILVER}; font-family:'DejaVu Sans'; font-size:13px; }}
QFrame#card {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:12px; }}
QLabel {{ background:transparent; border:none; }}
QLabel#caption {{ color:{MUTED}; font-size:11px; }}
QLabel#metric {{ color:{SILVER}; font-size:32px; font-weight:600; }}
QPushButton {{ background:{PANEL}; color:{SILVER}; border:1px solid {BORDER}; border-radius:8px; padding:11px 14px; font-weight:600; }}
QPushButton:hover {{ border-color:{GOLD}; background:#1b3449; }}
QPushButton:disabled {{ color:#607284; background:#102030; border-color:#1d3040; }}
QPushButton#primary,QPushButton:checked {{ background:{GOLD}; color:{NAVY}; border-color:{GOLD}; }}
QPushButton#primary:disabled {{ background:#102030; color:#607284; border-color:#1d3040; }}
QPushButton#danger {{ color:#f1a5a5; border-color:#674a52; }}
QPushButton#danger:disabled {{ color:#607284; border-color:#1d3040; }}
QComboBox {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:7px; padding:10px; }}
QComboBox QAbstractItemView {{ background:{PANEL}; color:{SILVER}; selection-background-color:#38506a; }}
QProgressBar {{ border:none; background:#071320; border-radius:3px; height:6px; }}
QProgressBar::chunk {{ background:{GOLD}; border-radius:3px; }}
QPlainTextEdit {{ background:#091726; color:{MUTED}; border:1px solid {BORDER}; border-radius:8px; font-family:'DejaVu Sans Mono'; font-size:11px; }}
'''


def label(text,kind=None):
    widget=QLabel(text)
    if kind:widget.setObjectName(kind)
    return widget


def card():
    frame=QFrame();frame.setObjectName('card')
    layout=QVBoxLayout(frame);layout.setContentsMargins(18,16,18,16);layout.setSpacing(12)
    return frame,layout


class CameraCanvas(QWidget):
    def __init__(self,title,parent=None):
        super().__init__(parent)
        self.title=title;self.image=None;self.stamp=0;self.fps=0
        self.setMinimumSize(220,125);self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

    def set_frame(self,frame):
        if frame:self.image,self.stamp,self.fps=frame
        else:self.image=None;self.stamp=0;self.fps=0
        self.update()

    def paintEvent(self,event):
        painter=QPainter(self);painter.fillRect(self.rect(),QColor('#06101b'))
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        live=self.image is not None and time.monotonic()-self.stamp<1.5
        if live:
            size=self.image.size().scaled(self.size(),Qt.KeepAspectRatio)
            rect=QRectF((self.width()-size.width())/2,(self.height()-size.height())/2,size.width(),size.height())
            painter.drawImage(rect,self.image)
        else:
            painter.setPen(QColor(BORDER))
            for x in range(0,self.width(),48):painter.drawLine(x,0,x,self.height())
            for y in range(0,self.height(),48):painter.drawLine(0,y,self.width(),y)
            painter.setPen(QColor(MUTED));painter.setFont(QFont('DejaVu Sans',13))
            painter.drawText(self.rect(),Qt.AlignCenter,'Waiting for '+self.title.lower()+'\nStart a simulation to connect')
        painter.fillRect(0,0,self.width(),34,QColor(7,19,33,220))
        painter.setPen(QColor(SILVER));painter.setFont(QFont('DejaVu Sans',10,QFont.DemiBold))
        painter.drawText(12,23,self.title.upper())
        painter.setPen(QColor('#72d6b3' if live else MUTED))
        painter.setPen(QColor(GOLD if self.title=='Bottom camera' else BORDER));painter.drawRect(self.rect().adjusted(0,0,-1,-1))
        painter.setPen(QColor('#72d6b3' if live else MUTED))
        painter.drawText(self.width()-150,23,f'LIVE  ·  {self.fps:.0f} FPS' if live else 'NO SIGNAL')


class PilotCanvas(CameraCanvas):
    def __init__(self):
        super().__init__('ZED left eye')
        self.bottom=CameraCanvas('Bottom camera',self)
        self.bottom.setStyleSheet('border:2px solid '+GOLD)

    def resizeEvent(self,event):
        width=min(330,max(220,self.width()//3))
        height=int(width*9/16)+34
        self.bottom.setGeometry(self.width()-width-18,self.height()-height-18,width,height)
        super().resizeEvent(event)


class PilotWindow(QMainWindow):
    session_state=pyqtSignal(str)
    log_message=pyqtSignal(str)

    def __init__(self,start_workers=True):
        super().__init__()
        self.setWindowTitle('Operation MX')
        # Bound the window icon: the original logo exceeds X11 property limits.
        icon = QPixmap(str(Path(__file__).resolve().parent/'assets/operation_mx_icon.png'))
        self.setWindowIcon(QIcon(icon.scaled(256,256,Qt.KeepAspectRatio,Qt.SmoothTransformation)))
        self.setMinimumSize(1120,740);self.resize(1500,950);self.setStyleSheet(STYLE)
        self.phase='Stopped';self.closing=False;self.finished=False;self.started_at=None
        self.ros=RosWorker()
        self.ros.message.connect(self.log)
        self.manager=SessionThread(self.session_state.emit,self.log_message.emit)
        self.session_state.connect(self.on_phase);self.log_message.connect(self.log)
        self.recorder=QProcess(self);self.recorder.finished.connect(self.recording_finished)
        self.recorder.errorOccurred.connect(lambda error:self.log('Screen recorder could not start.'))
        self.external_tools={}
        self.settings=QSettings('MarineXperts','Operation MX')
        self.record_started=None
        central=QWidget();self.setCentralWidget(central)
        root=QVBoxLayout(central);root.setContentsMargins(24,18,24,16);root.setSpacing(18)

        header=QHBoxLayout();header.setSpacing(18)
        logo_path=WORKSPACE/'src/robot_description/worlds/assets/team_logo/team_logo.png'
        emblem=QLabel();emblem.setFixedSize(64,78)
        if logo_path.exists():emblem.setPixmap(QPixmap(str(logo_path)).scaled(64,78,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        header.addWidget(emblem)
        titles=QVBoxLayout();brand=label('MARINEXPERTS');brand.setStyleSheet(f'color:{GOLD};font-size:12px;font-weight:600;')
        title=label('Operation MX');title.setStyleSheet('font-size:30px;font-weight:600;')
        titles.addWidget(brand);titles.addWidget(title);titles.addWidget(label('UNDERWATER SIMULATION STATION','caption'));header.addLayout(titles);header.addStretch()
        self.phase_label=label('●  SIMULATION STOPPED');self.phase_label.setStyleSheet(f'color:{MUTED};font-weight:600;')
        header.addWidget(self.phase_label);header.addSpacing(22)
        self.clock=label('');header.addWidget(self.clock)
        root.addLayout(header)

        body=QHBoxLayout();body.setSpacing(18)
        sidebar=QWidget();sidebar.setFixedWidth(310)
        side=QVBoxLayout(sidebar);side.setContentsMargins(0,0,0,0);side.setSpacing(14)
        session,sl=card();sl.addWidget(label('SIMULATION','caption'))
        self.world=QComboBox();self.world.addItem('Team pool','pool.world');self.world.addItem('Ocean · 4 m','ocean.world')
        sl.addWidget(self.world)
        self.odometry=QComboBox();self.odometry.addItem('ZED visual odometry','vision');self.odometry.addItem('Ground-truth pose','ground_truth');sl.addWidget(self.odometry)
        self.start_button=QPushButton('▶  Start simulation');self.start_button.setObjectName('primary');self.start_button.clicked.connect(lambda:self.action('start'))
        self.reset_button=QPushButton('↻  Reset simulation');self.reset_button.clicked.connect(lambda:self.action('reset'))
        self.stop_button=QPushButton('■  Stop simulation');self.stop_button.clicked.connect(lambda:self.action('stop'))
        sl.addWidget(self.start_button);sl.addWidget(self.reset_button);sl.addWidget(self.stop_button)
        self.session_hint=label('Choose a world, then start.','caption');self.session_hint.setWordWrap(True);sl.addWidget(self.session_hint)
        side.addWidget(session)

        telemetry,tl=card();tl.addWidget(label('VEHICLE','caption'))
        self.connection=label('Autopilot offline');tl.addWidget(self.connection)
        metrics=QGridLayout();self.metrics={}
        for i,(name,unit) in enumerate([('Depth','m'),('Heading','°'),('Speed','m/s'),('Mission','')]):
            box=QVBoxLayout();box.addWidget(label(name.upper(),'caption'))
            value=label('—','metric');self.metrics[name]=value;box.addWidget(value);box.addWidget(label(unit,'caption'))
            metrics.addLayout(box,0,i)
        controls=QHBoxLayout();self.arm_button=QPushButton('Arm');self.arm_button.clicked.connect(lambda:self.arm(True))
        self.disarm_button=QPushButton('Disarm');self.disarm_button.setObjectName('danger');self.disarm_button.clicked.connect(lambda:self.arm(False))
        controls.addWidget(self.arm_button);controls.addWidget(self.disarm_button);tl.addLayout(controls)
        self.mode=QComboBox();self.mode.addItems(['MANUAL','STABILIZE','ALT_HOLD']);self.mode.activated[str].connect(lambda mode:self.ros.request_mode(mode));tl.addWidget(self.mode)
        tl.addWidget(label('Gamepad steering enabled','caption'))
        side.addWidget(telemetry)

        thrusters,ml=card();ml.addWidget(label('THRUSTER OUTPUT','caption'));self.thrusters=[]
        for i in range(6):
            row=QHBoxLayout();name=label(f'T{i+1}');name.setFixedWidth(24);row.addWidget(name)
            bar=QProgressBar();bar.setRange(0,400);bar.setTextVisible(False);row.addWidget(bar)
            value=label('—','caption');value.setFixedWidth(42);row.addWidget(value)
            ml.addLayout(row);self.thrusters.append((bar,value))
        side.addWidget(thrusters);side.addStretch();body.addWidget(sidebar)

        video_column=QVBoxLayout();video_column.setSpacing(12)
        metric_strip,metric_layout=card();metric_layout.addLayout(metrics)
        video_column.addWidget(metric_strip)
        views=QHBoxLayout();views.addWidget(label('PILOT VIEW','caption'));views.addStretch()
        self.view_buttons={}
        for name in ['First person','Third person']:
            button=QPushButton(name);button.setCheckable(True);button.setChecked(name=='First person')
            button.clicked.connect(lambda checked,name=name:self.switch_view(name));views.addWidget(button);self.view_buttons[name]=button
        self.rviz_button=QPushButton('RViz');self.rviz_button.clicked.connect(self.open_rviz);views.addWidget(self.rviz_button)
        self.qground_button=QPushButton('QGroundControl');self.qground_button.clicked.connect(self.open_qground);views.addWidget(self.qground_button)
        video_column.addLayout(views)
        self.canvas=PilotCanvas();video_column.addWidget(self.canvas,1)
        tools=QHBoxLayout();self.view_description=label('ZED left eye · bottom view always visible','caption');tools.addWidget(self.view_description);tools.addStretch()
        capture=QPushButton('Capture frame');capture.clicked.connect(self.capture);tools.addWidget(capture)
        self.record_button=QPushButton('Record session');self.record_button.clicked.connect(self.toggle_recording);tools.addWidget(self.record_button)
        video_column.addLayout(tools)
        self.log_box=QPlainTextEdit();self.log_box.setReadOnly(True);self.log_box.setMaximumBlockCount(120);self.log_box.setFixedHeight(78);video_column.addWidget(self.log_box)
        body.addLayout(video_column,1);root.addLayout(body,1)
        footer=QHBoxLayout();footer.addWidget(label('MARINEXPERTS  /  NAVY · SILVER · GOLD','caption'));footer.addStretch()
        footer.addWidget(label('V  change view     C  capture     R  record','caption'));root.addLayout(footer)
        QShortcut('V',self,activated=self.cycle_view);QShortcut('C',self,activated=self.capture);QShortcut('R',self,activated=self.toggle_recording)
        self.refresh=QTimer(self);self.refresh.timeout.connect(self.tick);self.refresh.start(33)
        self.on_phase('Stopped')
        if start_workers:self.manager.start();self.ros.start()
        self.workers_started=start_workers

    def launch_tool(self,name,program,arguments,ros=False):
        process=self.external_tools.get(name)
        if process and process.state()!=QProcess.NotRunning:
            self.log(name+' is already open.');return
        process=QProcess(self)
        environment=QProcessEnvironment.systemEnvironment()
        if ros:
            environment.insert('ROS_DOMAIN_ID',str(DOMAIN))
            environment.insert('RMW_IMPLEMENTATION','rmw_fastrtps_cpp')
        else:
            # AppImages provide their own Qt libraries and plugins.
            for key in ('QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','QML2_IMPORT_PATH','LD_LIBRARY_PATH'):
                environment.remove(key)
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(lambda:process.readAllStandardOutput())
        process.errorOccurred.connect(lambda error:self.log(name+' could not start: '+process.errorString()))
        process.finished.connect(lambda code,status:self.log(name+' closed'+(' (exit '+str(code)+')' if code else '')+'.'))
        self.external_tools[name]=process
        process.start(str(program),arguments)
        self.log('Opening '+name+'…')

    def open_rviz(self):
        if self.phase!='Running':
            self.log('Start simulation before opening RViz.');return
        program=Path('/opt/ros/humble/lib/rviz2/rviz2')
        config=WORKSPACE/'install/robot_description/share/robot_description/config/model_tf.rviz'
        if not program.is_file() or not config.is_file():
            self.log('RViz or its simulation configuration was not found.');return
        self.launch_tool('RViz',program,['-d',str(config),'--ros-args','-r','__node:=operation_mx_rviz','-p','use_sim_time:=true'],ros=True)

    def open_qground(self):
        process=self.external_tools.get('QGroundControl')
        if process and process.state()!=QProcess.NotRunning:
            self.log('QGroundControl is already open.');return
        saved=self.settings.value('qground_executable','',type=str)
        candidates=[Path(saved)] if saved else []
        configured=os.environ.get('MAKO_QGROUNDCONTROL','')
        if configured:candidates.insert(0,Path(configured))
        for name in ('QGroundControl','qgroundcontrol'):
            executable=shutil.which(name)
            if executable:candidates.append(Path(executable))
        for folder in (Path.home()/'Applications',Path.home()/'Downloads',Path.home()):
            for pattern in ('*QGround*.AppImage','*qground*.AppImage','*qgc*.AppImage'):
                candidates.extend(sorted(folder.glob(pattern)))
        executable=next((path for path in candidates if path.is_file() and os.access(path,os.X_OK)),None)
        if executable is None:
            selected,_=QFileDialog.getOpenFileName(self,'Select QGroundControl executable or AppImage',str(Path.home()),'Applications (*.AppImage);;All files (*)')
            if not selected:return
            executable=Path(selected)
            if not os.access(executable,os.X_OK):
                self.log('The selected QGroundControl file is not executable. Enable its execute permission first.');return
        self.settings.setValue('qground_executable',str(executable))
        self.launch_tool('QGroundControl',executable,[])

    def action(self,action):
        if action in ['reset','stop']:
            self.stop_recording();self.ros.clear_session()
        self.on_phase({'start':'Starting','reset':'Resetting','stop':'Stopping'}[action])
        self.manager.request(action,self.world.currentData(),self.odometry.currentData())

    def on_phase(self,phase):
        self.phase=phase
        self.rviz_button.setEnabled(phase=='Running')
        self.rviz_button.setToolTip('Open simulation odometry and TF' if phase=='Running' else 'Start simulation to enable RViz')
        active=phase=='Running';idle=phase in ['Stopped','Error']
        self.start_button.setEnabled(idle);self.reset_button.setEnabled(active);self.stop_button.setEnabled(active)
        self.world.setEnabled(idle);self.odometry.setEnabled(idle)
        self.arm_button.setEnabled(False);self.disarm_button.setEnabled(False);self.mode.setEnabled(False)
        self.phase_label.setText('●  SIMULATION '+phase.upper())
        color='#72d6b3' if active else ('#f1a5a5' if phase=='Error' else GOLD)
        self.phase_label.setStyleSheet(f'color:{color};font-weight:600;')
        self.session_hint.setText({'Running':'Headless simulation active.','Starting':'Starting the simulation stack…',
            'Resetting':'Restarting the complete session…','Stopping':'Stopping the session…',
            'Stopped':'Choose a world, then start.','Error':'Start failed. See the message below.'}[phase])
        if active:self.started_at=time.monotonic()
        if idle:self.started_at=None
        if self.closing and idle:
            self.finished=True;QTimer.singleShot(0,self.close)

    def arm(self,armed):
        if self.phase=='Running':self.ros.request_arm(armed)

    def switch_view(self,name):
        for view,button in self.view_buttons.items():button.setChecked(view==name)
        self.ros.set_view(name)
        self.canvas.set_frame(None)
        self.canvas.title='ZED left eye' if name=='First person' else 'Rear-following camera'
        self.view_description.setText(self.canvas.title+' · bottom view always visible')

    def cycle_view(self):self.switch_view('Third person' if self.view_buttons['First person'].isChecked() else 'First person')

    def tick(self):
        frames,telemetry=self.ros.snapshot();now=time.monotonic()
        self.canvas.set_frame(frames.get('main'));self.canvas.bottom.set_frame(frames.get('bottom'))
        self.clock.setText(datetime.now(ZoneInfo('Africa/Cairo')).strftime('%d %b  ·  %H:%M:%S'))
        fresh=now-telemetry.get('state_time',0)<3
        connected=fresh and telemetry.get('connected',False) and self.phase=='Running'
        armed=connected and telemetry.get('armed',False)
        self.connection.setText(('Armed' if armed else 'Disarmed')+'  ·  '+telemetry.get('mode','—') if connected else 'Autopilot offline')
        self.connection.setStyleSheet('color:'+('#72d6b3' if connected else MUTED))
        self.arm_button.setEnabled(connected and not armed);self.disarm_button.setEnabled(connected and armed);self.mode.setEnabled(connected)
        nav=now-telemetry.get('nav_time',0)<1.5 and self.phase=='Running'
        for name,key,pattern in [('Depth','depth','{:.2f}'),('Heading','heading','{:.0f}'),('Speed','speed','{:.2f}')]:
            self.metrics[name].setText(pattern.format(telemetry[key]) if nav and key in telemetry else '—')
        elapsed=int(now-self.started_at) if self.started_at else 0
        self.metrics['Mission'].setText(f'{elapsed//60:02d}:{elapsed%60:02d}')
        for i,(bar,value) in enumerate(self.thrusters):
            channels=telemetry.get('pwm',[])
            pwm=int(channels[i]) if connected and i<len(channels) else None
            bar.setValue(min(400,abs(pwm-1500)) if pwm else 0);value.setText(str(pwm) if pwm else '—')
        if self.recorder.state()!=QProcess.NotRunning and self.record_started:
            self.record_button.setText(f'Stop recording · {int(now-self.record_started)}s')

    def capture(self):
        frames,_=self.ros.snapshot();frame=frames.get('main')
        if not frame or time.monotonic()-frame[1]>1.5:self.log('No live pilot frame to capture.');return
        folder=WORKSPACE/'gui/runs/captures';folder.mkdir(parents=True,exist_ok=True)
        path=folder/(datetime.now(ZoneInfo('Africa/Cairo')).strftime('%Y%m%d_%H%M%S_%f')+'.png')
        if frame[0].save(str(path)):self.log('Frame saved: '+str(path))

    def toggle_recording(self):
        if self.recorder.state()!=QProcess.NotRunning:self.stop_recording();return
        if not os.environ.get('DISPLAY'):self.log('Screen recording requires an X11 desktop display.');return
        folder=WORKSPACE/'gui/runs/recordings';folder.mkdir(parents=True,exist_ok=True)
        path=folder/(datetime.now(ZoneInfo('Africa/Cairo')).strftime('%Y%m%d_%H%M%S')+'.mp4')
        screen=QApplication.primaryScreen().geometry()
        self.recorder.setStandardErrorFile(str(path.with_suffix('.log')))
        self.recorder.start('ffmpeg',['-y','-f','x11grab','-framerate','30','-video_size',f'{screen.width()}x{screen.height()}',
            '-i',os.environ['DISPLAY'],'-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',str(path)])
        self.record_started=time.monotonic();self.log('Recording desktop session: '+str(path))

    def stop_recording(self):
        if self.recorder.state()!=QProcess.NotRunning:
            self.recorder.write(b'q\n')
            pid=self.recorder.processId()
            QTimer.singleShot(2500,lambda:self.recorder.kill() if self.recorder.state()!=QProcess.NotRunning and self.recorder.processId()==pid else None)

    def recording_finished(self,*args):
        self.record_button.setText('Record session');self.record_started=None
        if self.closing and self.finished:QTimer.singleShot(0,self.close)

    def log(self,text):
        self.log_box.appendPlainText(text)

    def closeEvent(self,event):
        for process in self.external_tools.values():
            if process.state()!=QProcess.NotRunning:process.terminate()
        if not self.workers_started:event.accept();return
        if self.finished and self.recorder.state()!=QProcess.NotRunning:
            event.ignore();return
        if self.finished:
            self.ros.stop();self.manager.join(timeout=2);event.accept();return
        event.ignore()
        if not self.closing:
            self.closing=True;self.stop_recording();self.manager.request('close');self.on_phase('Stopping')


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling,True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,True)
    smoke_test='--smoke-test' in sys.argv
    app=QApplication(sys.argv);app.setApplicationName('Operation MX');app.setOrganizationName('MarineXperts')
    app.setDesktopFileName('operation-mx')
    lock=QLockFile(QStandardPaths.writableLocation(QStandardPaths.TempLocation)+f'/Orca-pilot-{os.getuid()}.lock')
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(None,'Operation MX','Operation MX is already open.');return 0
    window=PilotWindow()
    available=app.primaryScreen().availableGeometry()
    window.resize(min(1500,available.width()-40),min(950,available.height()-60))
    window.show()
    if smoke_test:QTimer.singleShot(500,window.close)
    result=app.exec_();lock.unlock();return result
