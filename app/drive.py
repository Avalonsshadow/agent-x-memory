"""Local desktop OAuth/PKCE and read-only Drive synchronization. No write API."""
import base64
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import threading
import time
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import documents
from automation import snapshot

SCOPE='https://www.googleapis.com/auth/drive.readonly'
def stamp(): return dt.datetime.now(dt.timezone.utc).isoformat()

def request(url, data=None, token=None, limit=5_000_000):
    headers={'User-Agent':'Agent-X-Drive'}
    if token: headers['Authorization']='Bearer '+token
    if data is not None: headers['Content-Type']='application/x-www-form-urlencoded'
    try:
        with urlopen(Request(url,data=urlencode(data).encode() if data is not None else None,headers=headers),timeout=20) as response:
            raw=response.read(limit+1)
            if len(raw)>limit: raise ValueError('Google-Datei überschreitet die Größenbegrenzung.')
            return raw
    except HTTPError as error:
        raise ValueError('Google-Anfrage fehlgeschlagen (HTTP '+str(error.code)+'). Berechtigung, API-Aktivierung oder Verbindung prüfen.') from None
    except URLError: raise ValueError('Google ist nicht erreichbar. Verbindung prüfen.') from None

class Drive:
    scope=SCOPE
    def __init__(self,store,transport=request):
        self.store=store;self.transport=transport;self.lock=threading.RLock();self.pending={}
        self.path=store.path.parent/'google-drive-private.json'
        self.state={}
        try: self.state=json.loads(self.path.read_text())
        except (OSError,ValueError): pass
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS drive_links(file_id TEXT PRIMARY KEY,record_id TEXT NOT NULL,modified TEXT NOT NULL,sha256 TEXT NOT NULL)')
    def save(self):
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.state));os.chmod(temp,0o600);temp.replace(self.path)
    def status(self):
        with self.lock:
            return {'name':'Google Drive','status':'connected' if self.state.get('refresh_token') else 'configured' if self.state.get('client_id') else 'not_configured','last_success':self.state.get('last_success'),'last_check':self.state.get('last_check'),'error':self.state.get('error'),'scope':self.scope,'selected':self.state.get('selected',[]),'sync_interval':900,'local_only':True}
    def configure(self,payload):
        client=payload.get('installed') if isinstance(payload,dict) else None
        if not isinstance(client,dict) or not re.fullmatch(r'[A-Za-z0-9_-]+\.apps\.googleusercontent\.com',client.get('client_id','')) or not isinstance(client.get('client_secret'),str) or not 1<=len(client['client_secret'])<=1000:
            raise ValueError('Google-OAuth-JSON vom Typ Desktop-App erforderlich.')
        with self.lock:
            self.state={'client_id':client['client_id'],'client_secret':client['client_secret'],'selected':[]};self.pending.clear();self.save()
        return self.status()
    def begin(self,redirect,session):
        with self.lock:
            if not self.state.get('client_id'): raise ValueError('Zuerst Desktop-OAuth-Konfiguration einlesen.')
            self.pending={k:v for k,v in self.pending.items() if v['expires']>time.time()}
            state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
            self.pending[state]={'verifier':verifier,'redirect':redirect,'session':session,'expires':time.time()+600}
            challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
            return {'url':'https://accounts.google.com/o/oauth2/v2/auth?'+urlencode({'client_id':self.state['client_id'],'redirect_uri':redirect,'response_type':'code','scope':self.scope,'state':state,'code_challenge':challenge,'code_challenge_method':'S256','access_type':'offline','prompt':'consent'})}
    def complete(self,state,code,error=''):
        with self.lock:
            pending=self.pending.pop(state,None)
            if not pending or pending['expires']<time.time() or not self.store.session(pending['session']): raise ValueError('Anmeldung abgelaufen oder ungültig. In Agent X erneut verbinden.')
            if error: raise ValueError('Google-Anmeldung abgebrochen oder verweigert.')
            if not isinstance(code,str) or not 1<=len(code)<=4096: raise ValueError('Ungültiger Google-Code.')
            result=json.loads(self.transport('https://oauth2.googleapis.com/token',{'client_id':self.state['client_id'],'client_secret':self.state['client_secret'],'code':code,'code_verifier':pending['verifier'],'redirect_uri':pending['redirect'],'grant_type':'authorization_code'}))
            if self.scope not in result.get('scope','').split() or not result.get('refresh_token') or not result.get('access_token'): raise ValueError('Google hat den benötigten Lesezugriff nicht erteilt.')
            self.state.update(refresh_token=result['refresh_token'],access_token=result['access_token'],expires=time.time()+int(result.get('expires_in',3600))-60,error=None);self.save()
    def token(self):
        if not self.state.get('refresh_token'): raise ValueError('Google Drive ist noch nicht verbunden.')
        if self.state.get('expires',0)<=time.time():
            result=json.loads(self.transport('https://oauth2.googleapis.com/token',{'client_id':self.state['client_id'],'client_secret':self.state['client_secret'],'refresh_token':self.state['refresh_token'],'grant_type':'refresh_token'}))
            if not result.get('access_token'): raise ValueError('Google-Anmeldung erneuern.')
            self.state.update(access_token=result['access_token'],expires=time.time()+int(result.get('expires_in',3600))-60);self.save()
        return self.state['access_token']
    def get(self,path): return json.loads(self.transport('https://www.googleapis.com/drive/v3/'+path,token=self.token()))
    def files(self,page=''):
        if page and (not isinstance(page,str) or len(page)>2000): raise ValueError('Ungültige Seitennummer.')
        with self.lock:
            try:
                result=self.get('files?'+urlencode({'q':'trashed = false','pageSize':100,'pageToken':page,'fields':'nextPageToken,files(id,name,mimeType,modifiedTime,size)','orderBy':'modifiedTime desc'}))
                self.state.update(last_check=stamp(),last_success=stamp(),error=None);self.save();return result
            except ValueError as e: self.state.update(last_check=stamp(),error=str(e));self.save();raise
    def select(self,ids):
        if not isinstance(ids,list) or len(ids)>50 or any(not isinstance(i,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',i) for i in ids): raise ValueError('Maximal 50 gültige Dateien auswählen.')
        with self.lock: self.state['selected']=list(dict.fromkeys(ids));self.save()
        return self.status()
    def sync(self):
        with self.lock:
            self.state['last_check']=stamp();added=0;errors=[]
            for fid in self.state.get('selected',[]):
                try:
                    meta=self.get('files/'+quote(fid,safe='')+'?fields=id,name,mimeType,modifiedTime,trashed,size')
                    if meta.get('trashed'): raise ValueError('Quelldatei liegt im Google-Papierkorb; lokale Kopie bleibt erhalten.')
                    with self.store.connect() as db: old=db.execute('SELECT * FROM drive_links WHERE file_id=?',(fid,)).fetchone();existing=db.execute('SELECT 1 FROM records WHERE id=?',(old['record_id'],)).fetchone() if old else None
                    if old and not existing:
                        self.state['selected']=[i for i in self.state.get('selected',[]) if i!=fid]
                        with self.store.connect() as db: db.execute('DELETE FROM drive_links WHERE file_id=?',(fid,))
                        continue
                    if old and existing and old['modified']==meta.get('modifiedTime',''): continue
                    mime=meta['mimeType'];name=meta['name']
                    if mime=='application/vnd.google-apps.document': name+='.txt';path='files/'+fid+'/export?mimeType=text%2Fplain'
                    elif mime=='application/vnd.google-apps.spreadsheet': name+='.csv';path='files/'+fid+'/export?mimeType=text%2Fcsv'
                    elif mime=='application/vnd.google-apps.presentation': name+='.pdf';path='files/'+fid+'/export?mimeType=application%2Fpdf'
                    else:
                        if int(meta.get('size',0))>documents.MAX_FILE: raise ValueError('Quelldatei ist größer als 5 MB.')
                        path='files/'+fid+'?alt=media'
                    name=re.sub(r'[\\/\x00-\x1f]','_',name)[-200:]
                    raw=self.transport('https://www.googleapis.com/drive/v3/'+path,token=self.token());digest=hashlib.sha256(raw).hexdigest()
                    if old and existing and old['sha256']==digest:
                        with self.store.connect() as db: db.execute('UPDATE drive_links SET modified=? WHERE file_id=?',(meta.get('modifiedTime',''),fid))
                        continue
                    snapshot(self.store,self.store.path.parent/'backups')
                    result=documents.upload(self.store,{'filename':name,'content_base64':base64.b64encode(raw).decode(),'title':meta['name'][:200],'source':'Google Drive · https://drive.google.com/file/d/'+fid+'/view','observed':stamp()[:10],'record_id':old['record_id'] if old and existing else ''},stamp())
                    with self.store.connect() as db: db.execute('INSERT OR REPLACE INTO drive_links VALUES (?,?,?,?)',(fid,result['record_id'],meta.get('modifiedTime',''),digest))
                    added+=1
                except (ValueError,KeyError,TypeError) as e: errors.append(fid+': '+(str(e) if isinstance(e,ValueError) else 'Ungültige Google-Antwort.'))
            self.state['error']='; '.join(errors)[:2000] or None
            if not errors: self.state['last_success']=stamp()
            self.save();return {'added_versions':added,'errors':errors,'status':self.status()}
    def disconnect(self):
        with self.lock:
            self.state={};self.pending.clear();self.save()
        return self.status()

class Worker:
    def __init__(self,drive,interval=900): self.drive=drive;self.interval=interval;self.stop=threading.Event();self.thread=threading.Thread(target=self.run,daemon=True)
    def start(self): self.thread.start()
    def run(self):
        while not self.stop.wait(self.interval):
            if self.drive.status()['status']=='connected':
                try: self.drive.sync()
                except Exception:
                    with self.drive.lock: self.drive.state.update(error='Synchronisation fehlgeschlagen. Verbindung prüfen.',last_check=stamp());self.drive.save()
    def close(self): self.stop.set();self.thread.join()
