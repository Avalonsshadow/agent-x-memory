"""Create standalone public example-only preview; no backend and no private data."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');args=p.parse_args()
web=Path(__file__).resolve().parents[1]/'web'
html=(web/'index.html').read_text()
css=(web/'style.css').read_text()
js=(web/'app.js').read_text()
start=js.index('async function api(');end=js.index('\nfunction lock()',start)
mock=r'''
const fixture=(id,kind,title,extra={})=>({id,kind,title,body:'Ausschließlich Beispieldaten. Keine persönlichen Angaben eingeben.',module:'projects',status:'open',due:'',project_id:'',source:'Vorschau · Beispieldaten',evidence:'review',observed:today(),tags:'Beispiel',url:'',created:new Date().toISOString(),updated:new Date().toISOString(),...extra});
let demoRecords=[fixture('1'.repeat(32),'project','Beispiel · Lernplan strukturieren',{status:'active',body:'Lernziele festlegen und verfügbare Quellen sammeln. Keine Normtexte oder Zertifizierung.'}),fixture('2'.repeat(32),'task','Beispiel · Lernunterlagen sichten',{due:today(),project_id:'1'.repeat(32)}),fixture('3'.repeat(32),'task','Beispiel · Lernziel formuliert',{status:'done',project_id:'1'.repeat(32)}),fixture('4'.repeat(32),'note','Beispiel · KI-Experiment',{module:'laboratory',body:'Problem: verteilte Aufgaben. Ziel: Übersicht. Datenbedarf: Testeinträge. Ansatz: Filter. Ergebnis: offen. Nutzen: Zeitersparnis prüfen. Nächster Schritt: ausprobieren.'})];
let demoActivity=[];
async function api(path,options={}){
const method=options.method||'GET',body=options.body?JSON.parse(options.body):null;
if(path==='/api/session')return {configured:true,authenticated:true,csrf:'example-only'};
if(path==='/api/login')return {csrf:'example-only'};
if(path==='/api/logout')return {ok:true};
if(path==='/api/records'&&method==='GET')return structuredClone(demoRecords);
if(path==='/api/system')return {online:false,activity:demoActivity,integrations:['Google Drive','Gmail','Google Kalender','GitHub'].map(name=>({name,status:'not_configured',last_success:null,error:null})),jobs:{status:'inactive'}};
if(path==='/api/export')return {schema_version:1,exported_at:new Date().toISOString(),records:demoRecords};
if(path==='/api/restore'){if(demoRecords.length)throw new Error('Nur in leeren Datenbestand importieren.');if(!body||body.schema_version!==1||!Array.isArray(body.records))throw new Error('Ungültiges Backup.');demoRecords=body.records;return {restored:demoRecords.length}}
if(path==='/api/records'&&method==='POST'){const r={...body,id:crypto.randomUUID().replaceAll('-',''),created:new Date().toISOString(),updated:new Date().toISOString()};demoRecords.unshift(r);demoActivity.unshift({action:'created',record_id:r.id,ts:r.updated});return r}
if(path.startsWith('/api/records/')){const id=path.split('/').pop(),old=demoRecords.find(r=>r.id===id);if(!old)throw new Error('Eintrag nicht gefunden.');if(method==='DELETE'){demoRecords=demoRecords.filter(r=>r.id!==id).map(r=>({...r,project_id:r.project_id===id?'':r.project_id}));demoActivity.unshift({action:'deleted',record_id:id,ts:new Date().toISOString()});return {ok:true}}if(method==='PUT'){const r={...old,...body,updated:new Date().toISOString()};demoRecords=demoRecords.map(item=>item.id===id?r:item);demoActivity.unshift({action:'updated',record_id:id,ts:r.updated});return r}}
throw new Error('Nicht in der Vorschau verfügbar.');
}
'''
js=js[:start]+mock+js[end:]
js=js.replace("if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{})",'')
# Clearly distinguish the unprotected, transient preview from the authenticated app.
js=js.replace("heading('Dein Kommando­deck'","heading('Dein Kommando­deck'")
js=js.replace("<strong>SQLite · dauerhafte Speicherung</strong>","<strong>Demo · nur flüchtige Beispieldaten</strong>")
js=js.replace("Einträge liegen auf dem Server, nicht im öffentlichen Repository. Ein Serverumzug benötigt ein Backup.","Diese Vorschau hat keinen Server. Änderungen verschwinden nach Neuladen.")
js=js.replace("<strong>Passwortgeschützter Zugang</strong>","<strong>Vorschau ohne Anmeldung</strong>")
js=js.replace("Serverseitige Sitzung · HttpOnly-Cookie · CSRF-Schutz · Anmeldung begrenzt","Nur die separate Python-App hat Zugriffsschutz. Keine persönlichen Daten eingeben.")
html=html.replace('<link rel="manifest" href="/manifest.webmanifest">','').replace('<link rel="icon" href="/icon.svg">','')
html=html.replace('<link rel="stylesheet" href="/style.css">','<style>'+css+'\n.demo-banner{background:#efad73;color:#111d25;padding:9px 18px;font-size:12px;font-weight:650;position:relative;z-index:10}.workspace header{top:0}</style>')
html=html.replace('<script defer src="/app.js"></script>','')
html=html.replace('<div id="shell" hidden>','<div class="demo-banner">INTERAKTIVE VORSCHAU · Nur Beispiele · Kein Zugriffsschutz · Änderungen nur bis zum Neuladen · Keine persönlichen Daten eingeben</div><div id="shell" hidden>')
html=html.replace('</body>','<script>'+js.replace('</script','<\\/script')+'</script></body>')
Path(args.output).write_text(html)
print('Standalone-Beispielvorschau erstellt.')
