"""Rebuild this container's ArduSub with the generated Fish CUSTOM allocation."""
from pathlib import Path
import subprocess, shutil

workspace=Path(__file__).resolve().parents[1]
source=Path('/opt/ardupilot/libraries/AP_Motors/AP_Motors6DOF.cpp')
if not Path('/.dockerenv').exists():raise SystemExit('Run this tool inside the Fish container.')
text=source.read_text();start=text.index('    case SUB_FRAME_CUSTOM:')
end=text.index('        break;',start)+len('        break;')
text=text[:start]+(workspace/'firmware/custom_frame_cad.cpp').read_text().rstrip()+text[end:]
# Keep zero-centered sub-newton compensation symmetric about neutral PWM.
old='    return 1500 + thrust_in * (thrust_in > 0 ? range_up : range_down);'
new='''    if ((sub_frame_t)_active_frame_class == SUB_FRAME_CUSTOM) {
        return 1500 + int16_t(lroundf(thrust_in * (thrust_in > 0 ? range_up : range_down)));
    }
'''+old
if 'return 1500 + int16_t(lroundf(' not in text:
    if old not in text:raise RuntimeError('Unexpected thrust-to-PWM implementation')
    text=text.replace(old,new)
source.write_text(text)
# MANUAL bypassed the attitude controller's throttle bookkeeping, leaving
# its last disarmed value (zero) to initialize the next depth controller.
# Route the identical throttle through set_throttle_out so ALT_HOLD starts
# from the actual bidirectional neutral/current throttle instead.
manual_source=Path('/opt/ardupilot/ArduSub/mode_manual.cpp')
manual=manual_source.read_text()
old_manual='    sub.motors.set_throttle((channel_throttle->norm_input() + 1.0f) / 2.0f);'
new_manual='    attitude_control->set_throttle_out((channel_throttle->norm_input() + 1.0f) / 2.0f, false, g.throttle_filt);'
if old_manual in manual:manual_source.write_text(manual.replace(old_manual,new_manual))
elif new_manual not in manual:raise RuntimeError('Unexpected MANUAL throttle implementation')
shutil.copy2(manual_source,workspace/'firmware/mode_manual.cpp')
subprocess.run(['./waf','sub','-j3'],cwd='/opt/ardupilot',check=True)
import shutil
shutil.copy2('/opt/ardupilot/build/sitl/bin/ardusub',workspace/'firmware/ardusub-fish-cad-sitl')

shutil.copy2(source,workspace/'firmware/AP_Motors6DOF.cpp')
