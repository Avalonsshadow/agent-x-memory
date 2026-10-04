"""Check pinned repository; restart only after requests/workers finish and backup."""
import importlib.util
import json
from pathlib import Path
import threading
import sys
import os
from automation import snapshot

class Updates:
    def __init__(self,server,interval=900):
        self.server=server;self.interval=interval;self.stop=threading.Event();self.restart=False;self.error=None
        root=Path(__file__).resolve().parent.parent
        spec=importlib.util.spec_from_file_location('agentx_updater',root/'start_agent_x.py')
        self.updater=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.updater)
        self.thread=threading.Thread(target=self.run,daemon=True)
    def start(self): self.thread.start()
    def check(self):
        state=self.server.store.path.parent
        try:
            remote=json.loads(self.updater.fetch('https://api.github.com/repos/'+self.updater.REPO+'/commits?sha=agent-x-2%2Fmilestone-1&per_page=1',100000))[0]['sha']
            if len(remote)!=40 or any(c not in '0123456789abcdef' for c in remote): raise ValueError('Ungültiger Commit.')
            report=json.loads((state/'update-status.json').read_text())
            if remote!=report.get('revision'):
                self.restart=True;self.server.shutdown()
            self.error=None
        except Exception: self.error='Updateprüfung fehlgeschlagen. App bleibt verfügbar.'
    def run(self):
        while not self.stop.wait(self.interval): self.check()
    def close(self): self.stop.set();self.thread.join()
    def apply(self):
        snapshot(self.server.store,self.server.store.path.parent/'backups')
        self.updater.update(root=Path(__file__).resolve().parent.parent,state=self.server.store.path.parent)
        os.execv(sys.executable,[sys.executable,str(Path(__file__).resolve().parent/'server.py'),*sys.argv[1:]])
