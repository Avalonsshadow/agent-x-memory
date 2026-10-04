"""Separate Calendar OAuth, read-only bounded full-window synchronization."""
import datetime as dt
import hashlib
import json
from urllib.parse import urlencode, quote
import drive
from automation import snapshot

SCOPE='https://www.googleapis.com/auth/calendar.readonly'

class Calendar(drive.Drive):
    scope=SCOPE
    def __init__(self,store,transport=drive.request):
        super().__init__(store,transport)
        self.path=store.path.parent/'google-calendar-private.json';self.state={}
        try:self.state=json.loads(self.path.read_text())
        except (OSError,ValueError):pass
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS calendar_links(calendar_id TEXT,event_id TEXT,record_id TEXT,source_hash TEXT,PRIMARY KEY(calendar_id,event_id))')
    def configure_from_drive(self,d):
        if not self.state.get('client_id'):
            with d.lock:
                if not d.state.get('client_id'):raise ValueError('Zuerst Desktop-OAuth-JSON für Drive einlesen oder Kalender konfigurieren.')
                self.configure({'installed':{k:d.state[k] for k in ('client_id','client_secret')}})
    def status(self):
        result=super().status();result.update(name='Google Kalender',scope=SCOPE,window='30 Tage zurück / 180 Tage voraus',writes=False)
        return result
    def get(self,path):return json.loads(self.transport('https://www.googleapis.com/calendar/v3/'+path,token=self.token()))
    def calendars(self):
        with self.lock:
            items=[];page=''
            for _ in range(20):
                result=self.get('users/me/calendarList?'+urlencode({'maxResults':100,'pageToken':page}))
                items.extend({k:i.get(k,'') for k in ('id','summary','timeZone','accessRole')} for i in result.get('items',[]))
                page=result.get('nextPageToken','')
                if not page:return {'items':items}
            raise ValueError('Zu viele Kalenderseiten. Auswahl konnte nicht vollständig geladen werden.')
    def select(self,ids):
        if not isinstance(ids,list) or len(ids)>10 or any(not isinstance(i,str) or not i or len(i)>500 or any(ord(c)<32 for c in i) for i in ids):raise ValueError('Maximal 10 gültige Kalender auswählen.')
        with self.lock:self.state['selected']=list(dict.fromkeys(ids));self.save()
        return self.status()
    def sync(self):
        with self.lock:
            added=0;errors=[];self.state['last_check']=drive.stamp()
            instant=dt.datetime.now(dt.timezone.utc);low=instant-dt.timedelta(days=30);high=instant+dt.timedelta(days=180)
            for cid in self.state.get('selected',[]):
                try:
                    events=[];page=''
                    for _ in range(50):
                        data=self.get('calendars/'+quote(cid,safe='')+'/events?'+urlencode({'timeMin':low.isoformat(),'timeMax':high.isoformat(),'singleEvents':'true','showDeleted':'true','maxResults':250,'pageToken':page}))
                        events.extend(data.get('items',[]));page=data.get('nextPageToken','')
                        if not page:break
                    if page:raise ValueError('Kalender ist zu groß; keine Teilübernahme vorgenommen.')
                    # Validate the complete calendar before writing; failure retains previous data.
                    prepared=[]
                    for e in events:
                        eid=e['id'];cancelled=e.get('status')=='cancelled';start=e.get('start',{});when=start.get('dateTime') or start.get('date','')
                        if not isinstance(eid,str) or len(eid)>1000:raise ValueError('Ungültige Ereignis-ID.')
                        if not cancelled:
                            due=(dt.datetime.fromisoformat(when.replace('Z','+00:00')).astimezone().date().isoformat() if start.get('dateTime') else dt.date.fromisoformat(when).isoformat())
                        else:due=''
                        link=e.get('htmlLink','');link=link if link.startswith('https://') else ''
                        prepared.append((eid,e,cancelled,when,link,due))
                    if prepared:snapshot(self.store,self.store.path.parent/'backups')
                    with self.store.connect() as db:
                        for eid,e,cancelled,when,link,due in prepared:
                            old=db.execute('SELECT * FROM calendar_links WHERE calendar_id=? AND event_id=?',(cid,eid)).fetchone()
                            digest=hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()
                            if old and old['source_hash']==digest:
                                if due and due<instant.astimezone().date().isoformat():db.execute("UPDATE records SET status='done',updated=? WHERE id=? AND status='open'",(drive.stamp(),old['record_id']))
                                continue
                            rid=old['record_id'] if old else hashlib.sha256(('calendar:'+cid+':'+eid).encode()).hexdigest()[:32]
                            existing=db.execute('SELECT * FROM records WHERE id=?',(rid,)).fetchone()
                            if not existing and (cancelled or old):continue
                            body=('Beginn: '+when+'\nEnde: '+str(e.get('end',{}).get('dateTime') or e.get('end',{}).get('date',''))+'\nZeitzone: '+str(start.get('timeZone','Quellzeit mit Offset'))+'\nOrt: '+str(e.get('location',''))+'\n\n'+str(e.get('description','')))[:20000]
                            record={'kind':'event','title':str(e.get('summary') or (existing['title'] if existing else 'Termin ohne Titel'))[:200],'body':body,'module':existing['module'] if existing else 'lounge','status':'archived' if cancelled else 'done' if due<instant.astimezone().date().isoformat() else 'open','due':existing['due'] if cancelled and existing else due,'project_id':existing['project_id'] if existing else '', 'source':('Google Kalender · '+cid+' · Ereignis '+eid)[:1000],'evidence':'review','observed':instant.date().isoformat(),'tags':existing['tags'] if existing else 'Google Kalender','url':link}
                            values=self.store.validate(record,db,rid);values.update(id=rid,created=existing['created'] if existing else drive.stamp(),updated=drive.stamp())
                            keys=list(values);db.execute('INSERT OR REPLACE INTO records ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')',[values[k] for k in keys])
                            db.execute('INSERT OR REPLACE INTO calendar_links VALUES (?,?,?,?)',(cid,eid,rid,digest))
                            db.execute('INSERT INTO activity(action,record_id,ts) VALUES (?,?,?)',('calendar_synced',rid,drive.stamp()));added+=1
                except (ValueError,KeyError,TypeError) as e:errors.append(str(e) if isinstance(e,ValueError) else 'Ungültige Kalenderantwort.')
            self.state['error']='; '.join(errors)[:2000] or None
            if not errors:self.state['last_success']=drive.stamp()
            self.save();return {'updated_events':added,'errors':errors,'status':self.status()}
