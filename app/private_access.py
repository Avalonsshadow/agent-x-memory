"""Private Tailscale Serve setup. Never enables public Funnel or LAN binding."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def valid_origin(value):
    return isinstance(value,str) and bool(re.fullmatch(r'https://[a-z0-9][a-z0-9-]*\.[a-z0-9][a-z0-9-]*\.ts\.net',value))


def configured_origin(state):
    try:
        value=json.loads((Path(state)/'private-access.json').read_text())['origin']
        return value if valid_origin(value) else ''
    except (OSError,ValueError,KeyError,TypeError): return ''


def request_origin(state,host):
    value=configured_origin(state)
    return value if value and host==value.removeprefix('https://') else ''


def setup(state):
    exe=shutil.which('tailscale')
    if not exe and os.name=='nt':
        candidate=Path(os.environ.get('ProgramFiles',r'C:\Program Files'))/'Tailscale/tailscale.exe'
        if candidate.exists():exe=str(candidate)
    if not exe:
        raise SystemExit('Zuerst Tailscale installieren: https://tailscale.com/download/windows und anmelden. Danach diesen Befehl wiederholen.')
    def run(*args):
        return subprocess.run([exe,*args],check=True,capture_output=True,text=True,timeout=60).stdout
    try:
        status=json.loads(run('status','--json'))
        if status.get('BackendState')!='Running':raise ValueError('Tailscale zuerst anmelden und verbinden.')
        origin='https://'+status['Self']['DNSName'].rstrip('.')
        if not valid_origin(origin):raise ValueError('Kein gültiger Tailscale-DNS-Name. MagicDNS/HTTPS prüfen.')
        # Refuse overwriting an existing routing configuration.
        current=json.loads(run('serve','status','--json') or '{}')
        if current.get('TCP') or current.get('Web'):
            raise ValueError('Es gibt bereits eine Serve-Konfiguration. Vorhandene Dienste bleiben unverändert; manuelle Prüfung nötig.')
        run('serve','--bg','--https=443','http://127.0.0.1:8765')
        verified=json.loads(run('serve','status','--json'))
        if verified.get('AllowFunnel') and any(verified['AllowFunnel'].values()):
            raise ValueError('Öffentlicher Funnel erkannt. Privater Zugriff wird nicht aktiviert.')
        if not verified.get('Web'):raise ValueError('Serve-Konfiguration konnte nicht bestätigt werden.')
        state=Path(state);state.mkdir(parents=True,exist_ok=True)
        target=state/'private-access.json';temp=target.with_suffix('.tmp')
        temp.write_text(json.dumps({'origin':origin,'status':'configured','device_verified':False}));os.chmod(temp,0o600);temp.replace(target)
        print('Privater HTTPS-Zugriff eingerichtet: '+origin)
        print('iPhone: Tailscale installieren, mit demselben Konto anmelden, VPN erlauben, URL in Safari öffnen. App-Passwort bleibt erforderlich.')
        print('Endprüfung vom iPhone noch offen. PC und Agent X müssen laufen.')
    except (subprocess.SubprocessError,ValueError,KeyError) as exc:
        raise SystemExit('Einrichtung nicht abgeschlossen. Tailscale-Anmeldung, HTTPS-Freigabe und Administratorrechte prüfen. '+str(exc))
