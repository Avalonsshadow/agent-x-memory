"""Check the authorized development branch, update app atomically, start locally."""
import ast
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.request
from urllib.parse import urlsplit
import zipfile
import datetime as dt

ROOT = Path(__file__).resolve().parent
STATE = Path.home() / '.local/share/agent-x-2'
REPO = 'Avalonsshadow/agent-x-memory'
BRANCH = 'agent-x-2/milestone-1'
MAX_ARCHIVE = 8_000_000


def fetch(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent': 'Agent-X-Local-Updater', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=8) as response:
        if urlsplit(response.url).hostname not in ('api.github.com', 'codeload.github.com'):
            raise ValueError('Unerwartete Downloadadresse.')
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Download ist zu groß.')
        return data


def unpack_app(data, destination):
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            parts = PurePosixPath(item.filename).parts
            if len(parts) < 3 or parts[1] != 'app' or item.is_dir():
                continue
            relative = PurePosixPath(*parts[2:])
            if '..' in parts or '\\' in item.filename or relative.is_absolute() or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsicherer Archivpfad.')
            total += item.file_size
            if total > 20_000_000:
                raise ValueError('Entpacktes Update ist zu groß.')
            target = destination / str(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    for required in ('server.py', 'automation.py', 'web/app.js', 'web/index.html', 'web/style.css'):
        if not (destination / required).is_file():
            raise ValueError('Update ist unvollständig.')
    for source in destination.rglob('*.py'):
        ast.parse(source.read_text(encoding='utf-8'))


def update(root=ROOT, state=STATE, fetcher=fetch):
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    report_path = state / 'update-status.json'
    report = {'status': 'checking', 'last_check': dt.datetime.now(dt.timezone.utc).isoformat(), 'last_success': None, 'error': None}
    try:
        previous = json.loads(report_path.read_text())
        report['last_success'] = previous.get('last_success')
    except (OSError, ValueError):
        previous = {}
    try:
        commits = json.loads(fetcher('https://api.github.com/repos/' + REPO + '/commits?sha=agent-x-2%2Fmilestone-1&per_page=1', 100_000))
        sha = commits[0]['sha']
        if len(sha) != 40 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('Ungültige Versionskennung.')
        report['revision'] = sha
        if previous.get('revision') == sha and previous.get('status') in ('updated', 'current'):
            report['status'] = 'current'
            report['last_success'] = report['last_check']
        else:
            if (root / 'app/private').exists() or any(p.suffix in ('.db', '.sqlite', '.sqlite3') for p in (root / 'app').rglob('*')):
                raise ValueError('Private Daten im App-Ordner müssen vor einem Codeupdate getrennt werden.')
            data = fetcher('https://codeload.github.com/' + REPO + '/zip/' + sha, MAX_ARCHIVE)
            with tempfile.TemporaryDirectory(prefix='.agent-x-update-', dir=root) as temp:
                staged = Path(temp) / 'app'
                staged.mkdir()
                unpack_app(data, staged)
                old = root / 'app'
                backup = state / 'code-backups' / report['last_check'].replace(':', '-') / 'app'
                shutil.copytree(old, backup, ignore=shutil.ignore_patterns('__pycache__', 'private', '*.sqlite*', '*.db'))
                retired = Path(temp) / 'previous-app'
                old.rename(retired)
                try:
                    staged.rename(old)
                except Exception:
                    retired.rename(old)
                    raise
            report['status'] = 'updated'
            report['last_success'] = report['last_check']
    except Exception:
        report['status'] = 'error'
        report['error'] = 'Update nicht verfügbar oder ungültig. Vorhandene App wird weiterverwendet.'
    temp = report_path.with_suffix('.tmp')
    temp.write_text(json.dumps(report, ensure_ascii=False))
    os.chmod(temp, 0o600)
    temp.replace(report_path)
    return report


def main():
    with socket.socket() as sock:
        sock.settimeout(1)
        if sock.connect_ex(('127.0.0.1', 8765)) == 0:
            print('Port 8765 ist bereits belegt. Laufende App zuerst mit Strg+C stoppen.')
            return
    report = update()
    print('Update: ' + report['status'] + (' · ' + report['error'] if report['error'] else ''), flush=True)
    # Back up data before starting potentially changed code.
    database = STATE / 'data.sqlite3'
    if database.exists():
        import sqlite3
        backup_dir = STATE / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = backup_dir / ('startup-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.sqlite3')
        with sqlite3.connect(database) as source, sqlite3.connect(target) as dest:
            source.backup(dest)
        os.chmod(target, 0o600)
    subprocess.run([sys.executable, str(ROOT / 'app/server.py'), 'serve', '--automate'], cwd=ROOT)


if __name__ == '__main__':
    main()
