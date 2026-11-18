#!/usr/bin/env python3
"""Install only missing/mismatched pinned Python packages inside the image."""
import subprocess,sys
from importlib.metadata import PackageNotFoundError,version
missing=[]
for requirement in sys.argv[1:]:
    name,wanted=requirement.split('==',1)
    try: current=version(name)
    except PackageNotFoundError: current=None
    if current==wanted: print('Already installed:',requirement)
    else: missing.append(requirement)
if missing: subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir',*missing],check=True)
