"""Launch isolated backend and frontend VM test in the same network namespace."""
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
root=Path(__file__).resolve().parents[2]
server=subprocess.Popen([sys.executable,str(root/'app/tests/preview_server.py')],cwd=root)
try:
    for _ in range(50):
        if server.poll() is not None: raise SystemExit('Testserver konnte nicht starten.')
        try:
            with urlopen('http://127.0.0.1:8765/api/session',timeout=.5): pass
            break
        except OSError:time.sleep(.1)
    else:raise SystemExit('Testserver nicht erreichbar.')
    raise SystemExit(subprocess.run(['node',str(root/'app/tests/frontend.cjs')],cwd=root).returncode)
finally:
    server.terminate();server.wait(timeout=5)
