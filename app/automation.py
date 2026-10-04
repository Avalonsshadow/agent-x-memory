"""Local import worker. JSON is data; never execute imported instructions."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading


def snapshot(store, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.sqlite3')
    with store.connect() as source, sqlite3.connect(path) as dest:
        source.backup(dest)
    os.chmod(path, 0o600)
    return path


class ImportWorker:
    def __init__(self, store, interval=15):
        self.store = store
        self.directory = store.path.parent / 'imports'
        self.backups = store.path.parent / 'backups'
        for folder in ('inbox', 'processed', 'failed'):
            (self.directory / folder).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state_path = self.directory / 'status.json'
        self.interval = interval
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.previous = {}
        self.state = {'status': 'active', 'last_check': None, 'last_success': None, 'error': None, 'last_result': None}
        try:
            self.state.update(json.loads(self.state_path.read_text()))
        except (OSError, ValueError):
            pass
        self.state['status'] = 'active'

    def status(self):
        with self.lock:
            return dict(self.state, inbox=str(self.directory / 'inbox'), backup_directory=str(self.backups))

    def write_state(self, **changes):
        with self.lock:
            self.state.update(changes)
            temp = self.state_path.with_suffix('.tmp')
            temp.write_text(json.dumps(self.state, ensure_ascii=False))
            os.chmod(temp, 0o600)
            temp.replace(self.state_path)

    def scan(self):
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        self.write_state(last_check=stamp)
        current = {}
        for path in sorted((self.directory / 'inbox').glob('*.json')):
            if path.is_symlink() or not path.is_file():
                continue
            stat = path.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
            current[str(path)] = signature
            # Require two unchanged scans so unfinished copies are not imported.
            if self.previous.get(str(path)) != signature:
                continue
            digest = hashlib.sha256(path.name.encode()).hexdigest()[:12]
            try:
                if stat.st_size > 50_000_000:
                    raise ValueError('Import ist größer als 50 MB.')
                payload = json.loads(path.read_text(encoding='utf-8-sig'))
                plan = self.store.import_records(payload, preview=True)
                if plan['added'] or plan.get('files_added', 0):
                    snapshot(self.store, self.backups)
                result = self.store.import_records(payload)
                path.replace(self.directory / 'processed' / (stamp.replace(':', '-') + '-' + digest + '.json'))
                self.write_state(last_success=stamp, error=None, last_result=result)
            except (OSError, ValueError, TypeError, KeyError):
                # Do not expose imported contents or sensitive file names in errors.
                self.write_state(error='Import fehlgeschlagen. Paket im Ordner failed prüfen; bestehende Einträge bleiben erhalten.')
                try:
                    path.replace(self.directory / 'failed' / (stamp.replace(':', '-') + '-' + digest + '.json'))
                except OSError:
                    pass
        self.previous = current

    def run(self):
        while not self.stop.is_set():
            try:
                self.scan()
            except Exception:
                self.write_state(error='Importprüfung fehlgeschlagen. Privaten Datenordner und Dateirechte prüfen.')
            self.stop.wait(self.interval)

    def start(self):
        self.thread = threading.Thread(target=self.run, name='agent-x-import', daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=3)
