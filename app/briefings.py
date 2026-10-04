"""Persist in-app reminders and today's briefing while the server is running."""
import datetime as dt
import json
import threading
import assistant

class Briefings:
    def __init__(self,store,interval=60):
        self.store=store;self.interval=interval;self.stop=threading.Event();self.thread=threading.Thread(target=self.run,daemon=True);self.error=None;self.last_success=None
        with store.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS briefings(day TEXT PRIMARY KEY,payload TEXT NOT NULL,updated TEXT NOT NULL)')
    def tick(self):
        today=dt.datetime.now().astimezone().date();payload=assistant.answer(self.store,'Was benötigt heute meine Aufmerksamkeit?',today)
        payload['upcoming']=assistant.answer(self.store,'Welche Fristen stehen an?',today)['records']
        self.last_success=dt.datetime.now(dt.timezone.utc).isoformat()
        with self.store.connect() as db:db.execute('INSERT OR REPLACE INTO briefings VALUES (?,?,?)',(today.isoformat(),json.dumps(payload),self.last_success))
        self.error=None
    def start(self):self.thread.start()
    def run(self):
        while not self.stop.is_set():
            try:self.tick()
            except Exception:self.error='Tagesübersicht konnte nicht aktualisiert werden.'
            self.stop.wait(self.interval)
    def status(self):return {'status':'active','last_success':self.last_success,'error':self.error,'delivery':'in_app','interval':self.interval}
    def close(self):self.stop.set();self.thread.join()
