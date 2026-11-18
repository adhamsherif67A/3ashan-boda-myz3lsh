"""Install a desktop launcher for this Fish checkout."""
from pathlib import Path
import os

root = Path(__file__).resolve().parents[1]
launcher = root / 'run-fish.sh'
launcher.chmod(launcher.stat().st_mode | 0o111)
text = ('[Desktop Entry]\nType=Application\nName=Fish Omni Six\n'
        'Comment=Fish ROV simulation station\n'
        f'Exec="{launcher}"\nPath={root}\nTerminal=false\n'
        'Icon=applications-science\nCategories=Education;Science;\n')
applications = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'applications'
applications.mkdir(parents=True, exist_ok=True)
target = applications / 'fish-omni-six.desktop'
target.write_text(text)
target.chmod(0o755)
desktop = Path.home() / 'Desktop'
if desktop.is_dir():
    shortcut = desktop / target.name
    shortcut.write_text(text)
    shortcut.chmod(0o755)
print(f'Installed {target}. On the desktop, select Allow Launching if Ubuntu requests it.')
