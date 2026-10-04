"""Agent X 2.0: single-user, local-first authenticated SQLite application."""
import argparse
from contextlib import contextmanager
import datetime as dt
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

WEB = Path(__file__).parent / 'web'
KINDS = {'project', 'task', 'note', 'fact', 'document', 'event'}
MODULES = {'lounge', 'library', 'economics', 'health', 'laboratory', 'crew', 'projects', 'systems'}
STATUSES = {'open', 'active', 'blocked', 'done', 'archived'}
EVIDENCE = {'confirmed', 'estimated', 'review'}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
              body TEXT NOT NULL, module TEXT NOT NULL, status TEXT NOT NULL, due TEXT NOT NULL,
              project_id TEXT NOT NULL, source TEXT NOT NULL, evidence TEXT NOT NULL, observed TEXT NOT NULL,
              tags TEXT NOT NULL, url TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY, action TEXT NOT NULL, record_id TEXT, ts TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires REAL NOT NULL);
            ''')
        os.chmod(self.path, 0o600)
    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()
    def configured(self):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM config WHERE key='password'").fetchone() is not None
    def set_password(self, password):
        if len(password) < 12:
            raise ValueError('Passwort muss mindestens 12 Zeichen enthalten.')
        salt = secrets.token_hex(16)
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO config VALUES (?,?)', ('password', json.dumps([salt, password_hash(password, salt)])))
            db.execute('DELETE FROM sessions')
    def login(self, password):
        with self.connect() as db:
            row = db.execute("SELECT value FROM config WHERE key='password'").fetchone()
            if not row:
                return None
            salt, digest = json.loads(row[0])
            if not hmac.compare_digest(password_hash(password, salt), digest):
                return None
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires < ?', (time.time(),))
            db.execute('INSERT INTO sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), csrf, time.time()+43200))
            return token, csrf
    def session(self, token):
        with self.connect() as db:
            row = db.execute('SELECT csrf FROM sessions WHERE token=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            return row[0] if row else None
    def records(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM records ORDER BY updated DESC,id')]
    def validate(self, data, db, record_id):
        if not isinstance(data, dict):
            raise ValueError('Eintrag muss ein Objekt sein.')
        limits = {'title':200, 'body':20000, 'source':1000, 'tags':1000, 'url':2000, 'project_id':100, 'due':10, 'observed':10, 'kind':20, 'module':20, 'status':20, 'evidence':20}
        values = {}
        for key, limit in limits.items():
            value = data.get(key, '')
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError('Ungültiges Feld: '+key)
            values[key] = value.strip()
        if values['kind'] not in KINDS or values['module'] not in MODULES or values['status'] not in STATUSES or values['evidence'] not in EVIDENCE:
            raise ValueError('Ungültiger Typ oder Status.')
        if not values['title'] or not values['source'] or not values['observed']:
            raise ValueError('Titel, Quelle und Datum sind erforderlich.')
        for key in ('due','observed'):
            if values[key]:
                if dt.date.fromisoformat(values[key]).isoformat() != values[key]:
                    raise ValueError('Datum muss YYYY-MM-DD entsprechen.')
        if values['url'] and urlsplit(values['url']).scheme not in ('https','http'):
            raise ValueError('Nur HTTP(S)-Links sind zulässig.')
        parent = values['project_id']
        if parent:
            if parent == record_id or not db.execute("SELECT 1 FROM records WHERE id=? AND kind='project'", (parent,)).fetchone():
                raise ValueError('Projektverknüpfung existiert nicht.')
        return values
    def save(self, data, record_id=None):
        record_id_new = record_id or secrets.token_hex(16)
        with self.connect() as db:
            old = db.execute('SELECT * FROM records WHERE id=?', (record_id_new,)).fetchone()
            if record_id and not old:
                raise LookupError('Eintrag nicht gefunden.')
            values = self.validate(data, db, record_id_new)
            if old and old['kind']=='project' and values['kind']!='project' and db.execute('SELECT 1 FROM records WHERE project_id=?', (record_id_new,)).fetchone():
                raise ValueError('Verknüpftes Projekt kann nicht umgewandelt werden.')
            values.update(id=record_id_new, created=old['created'] if old else now(), updated=now())
            keys = list(values)
            db.execute('INSERT OR REPLACE INTO records ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')', [values[k] for k in keys])
            db.execute('INSERT INTO activity(action,record_id,ts) VALUES (?,?,?)', ('updated' if old else 'created',record_id_new,now()))
            return values
    def delete(self, record_id):
        with self.connect() as db:
            if db.execute('DELETE FROM records WHERE id=?', (record_id,)).rowcount != 1:
                raise LookupError('Eintrag nicht gefunden.')
            db.execute("UPDATE records SET project_id='',updated=? WHERE project_id=?", (now(),record_id))
            db.execute('INSERT INTO activity(action,record_id,ts) VALUES (?,?,?)', ('deleted',record_id,now()))
    def activity(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM activity ORDER BY id DESC LIMIT 100')]
    def restore(self, payload):
        if not isinstance(payload,dict) or payload.get('schema_version') != 1 or not isinstance(payload.get('records'),list) or len(payload['records'])>10000:
            raise ValueError('Ungültiges Agent-X-Backup.')
        records = payload['records']
        seen = set()
        with self.connect() as db:
            if db.execute('SELECT 1 FROM records LIMIT 1').fetchone():
                raise ValueError('Wiederherstellung ist nur in einen leeren Datenbestand möglich.')
            for r in sorted(records,key=lambda r: 0 if isinstance(r,dict) and r.get('kind')=='project' else 1):
                if not isinstance(r,dict) or not isinstance(r.get('id'),str) or len(r['id'])!=32 or any(c not in '0123456789abcdef' for c in r['id']) or r['id'] in seen:
                    raise ValueError('Ungültige oder doppelte ID.')
                seen.add(r['id'])
                values=self.validate(r,db,r['id'])
                # Restore provenance timestamps, but validate them first.
                for key in ('created','updated'):
                    dt.datetime.fromisoformat(r[key])
                    values[key]=r[key]
                values['id']=r['id']
                keys=list(values)
                db.execute('INSERT INTO records ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')',[values[k] for k in keys])
            db.execute('INSERT INTO activity(action,record_id,ts) VALUES (?,?,?)',('restored','',now()))
        return len(records)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass # do not log personal titles, cookies, or request contents
    def send(self, code, payload, content_type='application/json; charset=utf-8', cookie=None):
        content = json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload,(dict,list)) else payload
        self.send_response(code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(content)))
        self.send_header('Cache-Control','no-store' if self.path.startswith('/api/') else 'no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if self.server.secure:
            self.send_header('Strict-Transport-Security','max-age=31536000')
        if cookie:
            self.send_header('Set-Cookie',cookie)
        self.end_headers()
        self.wfile.write(content)
    def body(self):
        size = int(self.headers.get('Content-Length','0'))
        if size <= 0 or size > 2_000_000:
            raise ValueError('Ungültige Anfragegröße.')
        return json.loads(self.rfile.read(size))
    def token(self):
        cookie=SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie',''))
            return cookie['agentx'].value if 'agentx' in cookie else ''
        except Exception:
            return ''
    def cookie(self, token, age=43200):
        return 'agentx='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age='+str(age)+('; Secure' if self.server.secure else '')
    def auth(self, mutate=False):
        csrf = self.server.store.session(self.token())
        if not csrf:
            self.send(401, {'error':'Bitte anmelden.'}); return False
        if mutate and not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),csrf):
            self.send(403, {'error':'Ungültiger Sicherheitstoken.'}); return False
        return True
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/session':
            csrf=self.server.store.session(self.token())
            self.send(200,{'authenticated':bool(csrf),'csrf':csrf,'configured':self.server.store.configured()});return
        if path.startswith('/api/'):
            if not self.auth(): return
            if path=='/api/records': self.send(200,self.server.store.records())
            elif path=='/api/export': self.send(200,{'schema_version':1,'exported_at':now(),'records':self.server.store.records()})
            elif path=='/api/system': self.send(200,{'storage':'SQLite · gespeichert auf diesem Server','activity':self.server.store.activity(),'integrations':[{'name':n,'status':'not_configured','last_success':None,'error':None} for n in ['Google Drive','Gmail','Google Kalender','GitHub']],'jobs':{'status':'inactive','last_success':None},'online':self.server.secure})
            else: self.send(404,{'error':'Nicht gefunden.'})
            return
        allowed={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/manifest.webmanifest':'manifest.webmanifest','/sw.js':'sw.js','/icon.svg':'icon.svg'}
        if path not in allowed:
            self.send(404,{'error':'Nicht gefunden.'});return
        types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.webmanifest':'application/manifest+json','.svg':'image/svg+xml'}
        file=WEB/allowed[path]
        self.send(200,file.read_bytes(),types[file.suffix])
    def do_POST(self): self.mutate('POST')
    def do_PUT(self): self.mutate('PUT')
    def do_DELETE(self): self.mutate('DELETE')
    def mutate(self, method):
        path=urlsplit(self.path).path
        # Reject cross-origin requests, including login CSRF. Proxy deployment pins origin.
        origin=self.headers.get('Origin')
        expected=self.server.origin or ('http://'+self.headers.get('Host',''))
        if origin and origin!=expected:
            self.send(403,{'error':'Fremder Ursprung blockiert.'});return
        try:
            if path=='/api/login' and method=='POST':
                ip=self.client_address[0]
                with self.server.lock:
                    attempts=[t for t in self.server.attempts.get(ip,[]) if t>time.time()-900]
                    if len(attempts)>=5:
                        self.send(429,{'error':'Zu viele Versuche. Bitte in 15 Minuten erneut versuchen.'});return
                    attempts.append(time.time()); self.server.attempts[ip]=attempts
                data=self.body()
                password=data.get('password') if isinstance(data,dict) else None
                if not isinstance(password,str) or len(password)>1024: raise ValueError('Ungültiges Passwort.')
                result=self.server.store.login(password)
                if result:
                    with self.server.lock: self.server.attempts.pop(ip,None)
                    self.send(200,{'csrf':result[1]},cookie=self.cookie(result[0]))
                else: self.send(401,{'error':'Anmeldung fehlgeschlagen.'})
                return
            if not self.auth(True): return
            if path=='/api/logout' and method=='POST':
                with self.server.store.connect() as db: db.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(self.token().encode()).hexdigest(),))
                self.send(200,{'ok':True},cookie=self.cookie('',0))
            elif path=='/api/records' and method=='POST': self.send(201,self.server.store.save(self.body()))
            elif path.startswith('/api/records/') and method in ('PUT','DELETE'):
                record_id=path.split('/')[-1]
                if method=='PUT': self.send(200,self.server.store.save(self.body(),record_id))
                else: self.server.store.delete(record_id); self.send(200,{'ok':True})
            elif path=='/api/restore' and method=='POST': self.send(200,{'restored':self.server.store.restore(self.body())})
            else: self.send(404,{'error':'Nicht gefunden.'})
        except (ValueError, TypeError, KeyError) as e: self.send(400,{'error':str(e)})
        except LookupError as e: self.send(404,{'error':str(e)})
        except Exception:
            self.send(500,{'error':'Interner Fehler. Datenbestand und Server prüfen.'})

def make_server(store,host='127.0.0.1',port=8765,origin=''):
    server=ThreadingHTTPServer((host,port),Handler)
    server.store=store;server.origin=origin;server.secure=origin.startswith('https://')
    server.attempts={}; server.lock=threading.Lock()
    return server

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['init','serve','backup'])
    p.add_argument('--data',default=str(Path.home()/'.local/share/agent-x-2/data.sqlite3'))
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8765)
    p.add_argument('--origin',default='');p.add_argument('--output')
    args=p.parse_args();store=Store(args.data)
    if args.command=='init':
        password=getpass.getpass('Neues Passwort (mindestens 12 Zeichen): ')
        if password!=getpass.getpass('Passwort wiederholen: '): raise SystemExit('Passwörter stimmen nicht überein.')
        store.set_password(password);print('Zugang eingerichtet. Bestehende Sitzungen beendet.')
    elif args.command=='backup':
        if not args.output: raise SystemExit('--output ist erforderlich; außerhalb des Repositorys speichern.')
        target=Path(args.output)
        with sqlite3.connect(target) as dest,store.connect() as source: source.backup(dest)
        os.chmod(target,0o600);print('SQLite-Sicherung erstellt. Enthält private Daten und Zugangskonfiguration.')
    else:
        if not store.configured(): raise SystemExit('Zuerst python app/server.py init ausführen.')
        if args.host not in ('127.0.0.1','localhost','::1') and not args.origin.startswith('https://'):
            raise SystemExit('Netzwerkbetrieb benötigt --origin https://… und einen vorgeschalteten HTTPS-Proxy.')
        if args.origin and (urlsplit(args.origin).scheme!='https' or urlsplit(args.origin).path not in ('','/')):
            raise SystemExit('--origin muss der exakte HTTPS-Ursprung sein, ohne Pfad.')
        server=make_server(store,args.host,args.port,args.origin.rstrip('/'))
        print(f'Agent X erreichbar: {args.origin or "http://127.0.0.1:"+str(args.port)}',flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()
if __name__=='__main__': main()
