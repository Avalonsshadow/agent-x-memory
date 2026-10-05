"""Disposable test-only server. Never use this fixture database for personal data."""
import sys,tempfile
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Store,make_server
folder=tempfile.TemporaryDirectory(prefix='agent-x-demo-')
store=Store(Path(folder.name)/'test.sqlite3')
store.set_password('Demo-only-password-42!')
base={'kind':'project','title':'Beispiel · Lernplan strukturieren','body':'Ausschließlich Beispieldaten: Lernziele festlegen und verfügbare Unterlagen verknüpfen. Keine Normtexte oder Zertifizierung.','module':'projects','status':'active','due':'','project_id':'','source':'Isolierte Testfixture','evidence':'review','observed':'2026-10-04','tags':'Beispiel, Ausbildung','url':''}
p=store.save(base)
store.save({**base,'kind':'task','title':'Beispiel · Lernunterlagen sichten','project_id':p['id'],'due':'2026-10-04','priority':'high','body':'Nächsten Lernschritt anhand eigener verfügbarer Quellen festhalten.'})
store.save({**base,'kind':'task','title':'Beispiel · Lernziel formuliert','project_id':p['id'],'status':'done','body':''})
store.save({**base,'kind':'note','title':'Beispiel · KI-Experiment','module':'laboratory','body':'Problem: verstreute Aufgaben. Ziel: konsolidierte Übersicht. Datenbedarf: Testaufgaben. Ansatz: regelbasierte Filter. Ergebnis: noch offen. Nutzen: Übersicht. Nächster Schritt: testen.'})
# Populate only this disposable database for reference-layout visual checks.
today=date.today().isoformat()
other=store.save({**base,'title':'Beispiel · Automatisierung','module':'laboratory','body':'Testabläufe mit Beispieldaten prüfen.'})
for title,priority,module in [('Beispiel · Unterlagen prüfen','medium','library'),('Beispiel · Lernziel planen','low','projects')]:
    store.save({**base,'kind':'task','title':title,'priority':priority,'module':module,'project_id':other['id'],'due':today,'body':''})
for title,start,end,module in [('Beispiel · Projektbesprechung','09:30','11:00','projects'),('Beispiel · Mittagspause','12:00','13:00','lounge'),('Beispiel · Bewegung','18:00','19:00','health')]:
    store.save({**base,'kind':'event','title':title,'module':module,'due':today,'body':f'Beginn: {today}T{start}:00\nEnde: {today}T{end}:00','status':'open'})
store.save({**base,'kind':'event','title':'Beispiel · Planung nächste Woche','due':(date.today()+timedelta(days=2)).isoformat(),'body':'','status':'open'})
print('Isolierte Testvorschau: http://127.0.0.1:8765',flush=True)
make_server(store,port=8765).serve_forever()
