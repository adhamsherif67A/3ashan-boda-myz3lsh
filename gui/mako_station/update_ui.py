"""Background release downloads. Activation belongs to the stable launcher."""
import json
import os
from pathlib import Path
import threading

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QLabel, QPushButton, QInputDialog, QLineEdit
from .updater import current_version, latest, download, queue_update, save_github_token


class UpdateController(QObject):
    message = pyqtSignal(str)
    done = pyqtSignal(bool)

    def __init__(self, window, layout, enabled=True):
        super().__init__(window)
        self.window = window
        self.busy = False
        self.root = Path(os.environ['OPERATION_MX_INSTALL_ROOT']) if os.environ.get('OPERATION_MX_INSTALL_ROOT') else None
        self.automatic = QCheckBox('Auto updates')
        self.automatic.setChecked(window.settings.value('automatic_updates', True, type=bool))
        self.automatic.toggled.connect(lambda value: window.settings.setValue('automatic_updates', value))
        self.button = QPushButton('Check updates')
        self.button.clicked.connect(lambda: self.check(manual=True))
        self.access = QPushButton('GitHub access')
        self.access.clicked.connect(self.configure_access)
        layout.addWidget(QLabel('v'+current_version()))
        layout.addWidget(self.automatic)
        layout.addWidget(self.button)
        layout.addWidget(self.access)
        self.message.connect(window.log)
        self.done.connect(self.finished)
        if self.root is None:
            self.button.setEnabled(False)
            self.automatic.setEnabled(False)
            self.access.setEnabled(False)
            self.button.setToolTip('Install the versioned desktop release to enable online updates')
        self.timer = QTimer(self)
        self.timer.setInterval(15*60*1000)
        self.timer.timeout.connect(self.automatic_check)
        if self.root and enabled:
            self.timer.start()
            QTimer.singleShot(5000, self.automatic_check)

    def configure_access(self):
        if self.busy or self.window.phase not in ('Stopped', 'Error'):
            self.window.log('Stop the simulation before changing update access.')
            return
        token, accepted = QInputDialog.getText(self.window, 'Private GitHub updates',
            'GitHub token with read access to this repository. Blank removes saved access.', QLineEdit.Password)
        if accepted:
            try:
                save_github_token(token)
                self.window.log('GitHub access saved. Tokens stay on this computer; use Check updates to verify access.'
                                if token.strip() else 'Saved GitHub access removed.')
            except (OSError, ValueError) as error:
                self.window.log('Could not save GitHub access: '+str(error))

    def automatic_check(self):
        if self.automatic.isChecked():
            self.check()

    def check(self, manual=False):
        if not self.root or self.busy:
            return
        if self.window.phase not in ('Stopped', 'Error'):
            if manual:
                self.window.log('Updates wait until the simulation is stopped.')
            return
        if (self.root/'pending.json').exists():
            self.window.log('A verified update is ready. Close and reopen Operation MX to install it.')
            self.button.setText('Update on next launch')
            return
        self.busy = True
        self.button.setEnabled(False)
        self.button.setText('Checking…')
        # Downloading does not execute release code or touch the active version.
        threading.Thread(target=self.work, args=(manual,), daemon=True).start()

    def work(self, manual):
        ready = False
        try:
            result = latest(self.root/'update_public_key.pem', current_version())
            if result is None:
                if manual:
                    self.message.emit('Operation MX is up to date.')
            else:
                manifest, raw, signature, url = result
                failed_path = self.root/'failed-updates.json'
                failed = json.loads(failed_path.read_text()) if failed_path.exists() else []
                if manifest['version'] in failed and not manual:
                    return
                self.message.emit('Downloading verified update '+manifest['version']+' in the background…')
                target = self.root/'cache'/manifest['archive']['name']
                download(url, target, manifest)
                queue_update(self.root, raw, signature, target)
                ready = True
                self.message.emit('Update '+manifest['version']+' is ready. It will install when you close and reopen the application.')
        except Exception as error:
            # No update server, a missing release or a bad download never blocks piloting.
            self.message.emit('Update check unavailable; keeping the installed version. '+str(error)+
                              ' For private releases, configure GitHub access and check token permissions/expiration.')
        finally:
            self.done.emit(ready)

    def finished(self, ready):
        self.busy = False
        self.button.setEnabled(True)
        self.button.setText('Update on next launch' if ready else 'Check updates')
