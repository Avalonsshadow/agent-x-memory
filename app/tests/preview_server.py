"""Disposable test-only server. Never use this fixture database for personal data."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Store,make_server
folder=tempfile.TemporaryDirectory(prefix='agent-x-demo-')
store=Store(Path(folder.name)/'test.sqlite3')
store.set_password('Demo-only-password-42!')
base={'kind':'project','title':'Beispiel · Lernplan strukturieren','body':'Ausschließlich Beispieldaten: Lernziele festlegen und verfügbare Unterlagen verknüpfen. Keine Normtexte oder Zertifizierung.','module':'projects','status':'active','due':'','project_id':'','source':'Isolierte Testfixture','evidence':'review','observed':'2026-10-04','tags':'Beispiel, Ausbildung','url':''}
p=store.save(base)
store.save({**base,'kind':'task','title':'Beispiel · Lernunterlagen sichten','project_id':p['id'],'due':'2026-10-04','body':'Nächsten Lernschritt anhand eigener verfügbarer Quellen festhalten.'})
store.save({**base,'kind':'task','title':'Beispiel · Lernziel formuliert','project_id':p['id'],'status':'done','body':''})
store.save({**base,'kind':'note','title':'Beispiel · KI-Experiment','module':'laboratory','body':'Problem: verstreute Aufgaben. Ziel: konsolidierte Übersicht. Datenbedarf: Testaufgaben. Ansatz: regelbasierte Filter. Ergebnis: noch offen. Nutzen: Übersicht. Nächster Schritt: testen.'})
print('Isolierte Testvorschau: http://127.0.0.1:8765',flush=True)
make_server(store,port=8765).serve_forever()
