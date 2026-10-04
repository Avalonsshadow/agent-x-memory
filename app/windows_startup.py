"""Current-user startup, no admin privileges. Writes only Agent X files."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

def paths(state, appdata=None):
    base=Path(appdata or os.environ.get('APPDATA',''))
    return base/'Microsoft/Windows/Start Menu/Programs/Startup/Agent-X-2.vbs',Path(state)/'autostart-runner.py'

def install(state,root,executable=None,appdata=None):
    if os.name!='nt' and appdata is None:return {'status':'unsupported','error':'Autostart nur unter Windows verfügbar.'}
    link,runner=paths(state,appdata);link.parent.mkdir(parents=True,exist_ok=True)
    python=Path(executable or sys.executable)
    windowless=python.with_name('pythonw.exe')
    if windowless.exists():python=windowless
    # JSON quoting yields Python string literals, including Windows backslashes.
    runner.write_text('import runpy,sys\nfrom pathlib import Path\nroot=Path('+json.dumps(str(Path(root).resolve()))+')\nsys.path.insert(0,str(root/"app"))\nrunpy.run_path(str(root/"app"/"windows_startup.py"),run_name="__main__")\n',encoding='utf-8')
    command='"'+str(python)+'" "'+str(runner)+'"'
    link.write_text('Set shell = CreateObject("WScript.Shell")\nshell.Run "'+command.replace('"','""')+'", 0, False\n',encoding='utf-16')
    report={'status':'installed','installed_at':time.time(),'entry':str(link),'runner':str(runner),'root':str(Path(root).resolve()),'runtime_verified':False,'error':None}
    (Path(state)/'autostart-status.json').write_text(json.dumps(report),encoding='utf-8')
    return report

def status(state):
    try:
        report=json.loads((Path(state)/'autostart-status.json').read_text(encoding='utf-8'))
        if report.get('status') in ('installed','running') and not Path(report.get('entry','')).is_file():report.update(status='missing',runtime_verified=False,error='Autostarteintrag fehlt.')
        return report
    except (OSError,ValueError):return {'status':'not_installed' if os.name=='nt' else 'unsupported','runtime_verified':False,'error':None}

def remove(state):
    report=status(state)
    link=report.get('entry')
    if link and Path(link).name=='Agent-X-2.vbs':Path(link).unlink(missing_ok=True)
    (Path(state)/'autostart-status.json').write_text(json.dumps({'status':'removed','runtime_verified':False,'error':None}),encoding='utf-8')
    return status(state)

def run():
    root=Path(__file__).resolve().parent.parent
    state=Path.home()/'.local/share/agent-x-2';state.mkdir(parents=True,exist_ok=True)
    # Keep a Windows file lock throughout the supervisor to avoid duplicate launches.
    import msvcrt
    with (state/'autostart.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:return
        # A foreground instance may still own the port. Wait for it, never kill it.
        with (state/'autostart-runtime.log').open('a',encoding='utf-8') as log:
            while status(state).get('status') not in ('removed','missing'):
                with socket.socket() as sock:
                    sock.settimeout(1);occupied=sock.connect_ex(('127.0.0.1',8765))==0
                if occupied:time.sleep(10);continue
                time.sleep(3)
                with socket.socket() as sock:
                    sock.settimeout(1)
                    if sock.connect_ex(('127.0.0.1',8765))==0:continue
                child=subprocess.Popen([sys.executable,str(root/'app/server.py'),'serve','--automate','--managed-start'],cwd=root,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                child.wait();time.sleep(10)

if __name__=='__main__':run()
