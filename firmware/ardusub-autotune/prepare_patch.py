#!/usr/bin/env python3
"""Generate a reviewable ArduSub patch; never edit the external firmware tree."""
from pathlib import Path
import argparse
import difflib
import subprocess

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('ardupilot', type=Path)
p.add_argument('--from-head', action='store_true', help='Regenerate against committed base after applying a prior patch')
args = p.parse_args()
source = args.ardupilot.resolve()
changes = {}


def read(path):
    if args.from_head:
        result = subprocess.run(['git', '-C', str(source), 'show', 'HEAD:'+path], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else ''
    return (source/path).read_text() if (source/path).exists() else ''


def edit(name, old, new):
    path = 'ArduSub/'+name
    text = changes.get(path, read(path))
    if text.count(old) != 1:
        raise SystemExit(f'Expected one matching context in {path}: {old[:70]!r}; wrong base or patch already applied')
    changes[path] = text.replace(old, new, 1)


edit('config.h', '#include "defines.h"', '#include "defines.h"\n\n#ifndef AUTOTUNE_ENABLED\n#define AUTOTUNE_ENABLED 1\n#endif')
edit('Sub.h', '#include "Parameters.h"', '#if AUTOTUNE_ENABLED\n#include <AC_AutoTune/AC_AutoTune_Multi.h>\n#endif\n#include "Parameters.h"')
edit('Sub.h', '    friend class ModeMotordetect;', '    friend class ModeMotordetect;\n    friend class SubAutoTune;\n    friend class ModeAutoTune;')
edit('Sub.h', '    ModeAlthold mode_althold;', '    ModeAlthold mode_althold;\n#if AUTOTUNE_ENABLED\n    ModeAutoTune mode_autotune;\n#endif')
edit('mode.h', '        POSHOLD =      16,', '        AUTOTUNE =     15,  // onboard attitude autotuning\n        POSHOLD =      16,')
changes['ArduSub/mode.h'] += (HERE/'mode_declarations.h.inc').read_text()
edit('mode.cpp', '    case Mode::Number::ALT_HOLD:', '#if AUTOTUNE_ENABLED\n    case Mode::Number::AUTOTUNE:\n        ret = &mode_autotune;\n        break;\n#endif\n    case Mode::Number::ALT_HOLD:')
edit('mode.cpp', '    // stop mission when we leave auto mode', '#if AUTOTUNE_ENABLED\n    if (old_control_mode == Mode::Number::AUTOTUNE) { mode_autotune.stop(); }\n#endif\n    // stop mission when we leave auto mode')
edit('mode.cpp', 'void Sub::exit_mode(Mode *&old_flightmode, Mode *&new_flightmode){', 'void Sub::exit_mode(Mode *&old_flightmode, Mode *&new_flightmode){\n#if AUTOTUNE_ENABLED\n    if (old_flightmode == &mode_autotune) { mode_autotune.stop(); }\n#endif')
edit('Parameters.h', 'class Parameters {', 'class SubAutoTune;\n\nclass Parameters {')
# The pointer lets AP_Param register the existing library parameter group.
edit('Parameters.h', '    ParametersG2(void);', '    ParametersG2(void);\n#if AUTOTUNE_ENABLED\n    SubAutoTune *autotune_ptr;\n#endif')
edit('Parameters.cpp', '    AP_SUBGROUPINFO(actuators, "ACTUATOR", 23, ParametersG2, Actuators),', '    AP_SUBGROUPINFO(actuators, "ACTUATOR", 23, ParametersG2, Actuators),\n#if AUTOTUNE_ENABLED\n    // @Group: AUTOTUNE_\n    // @Path: ../libraries/AC_AutoTune/AC_AutoTune_Multi.cpp\n    AP_SUBGROUPPTR(autotune_ptr, "AUTOTUNE_", 24, ParametersG2, SubAutoTune),\n#endif')
edit('Parameters.cpp', 'ParametersG2::ParametersG2()\n{', 'ParametersG2::ParametersG2()\n#if AUTOTUNE_ENABLED\n    : autotune_ptr(&sub.mode_autotune.autotune)\n#endif\n{')
edit('Parameters.h', '    { "CIRCLE_RATE",         2.0f},', '#if AUTOTUNE_ENABLED\n    { "AUTOTUNE_AXES",       4.0f}, // yaw only by default; vectored has no pitch\n#endif\n    { "CIRCLE_RATE",         2.0f},')
edit('AP_Arming_Sub.cpp', '    sub.motors.armed(false);', '    sub.motors.armed(false);\n#if AUTOTUNE_ENABLED\n    if (sub.control_mode == Mode::Number::AUTOTUNE) { sub.mode_autotune.on_disarm(); }\n#endif')
edit('wscript', "            'AC_AttitudeControl',", "            'AC_AttitudeControl',\n            'AC_AutoTune',")
changes['ArduSub/mode_autotune.cpp'] = (HERE/'mode_autotune.cpp').read_text()
patch = []
for path, new in sorted(changes.items()):
    original = read(path)
    patch.extend(difflib.unified_diff(original.splitlines(True), new.splitlines(True),
                 fromfile='a/'+path if original else '/dev/null', tofile='b/'+path))
(HERE/'ardusub-autotune.patch').write_text(''.join(patch))
(HERE/'BASE_COMMIT').write_text(subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True))
print(HERE/'ardusub-autotune.patch')
