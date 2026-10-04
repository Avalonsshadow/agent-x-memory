"""Deterministic answers and excerpts. No model, execution, or external requests."""
import datetime as dt
import re
import documents

STOP=set('was wie wo welche welcher welchen steht stehen ist sind der die das den dem ein eine einem einer und oder in im am an auf zu zur zum mit von für ich meine meinen meinem mir bitte dokument dokumente datei sagt steht finde zeige benötigt heute nächsten nächste sollte lernen'.split())

def answer(store, question, today=None):
    if not isinstance(question,str) or not 1<=len(question.strip())<=500:
        raise ValueError('Frage muss 1 bis 500 Zeichen enthalten.')
    q=question.strip().casefold();today=today or dt.datetime.now().astimezone().date()
    rows=store.records();active=lambda r:r['status'] not in ('done','archived')
    mode='search';text='Passende gespeicherte Einträge und wörtliche Dokumentauszüge. Keine KI-Zusammenfassung.'
    if re.search(r'heute|aufmerksamkeit|priorität|prioritaet|tages',q) and not re.search(r'dokument|datei|unterlage',q):
        mode='today';rows=[r for r in rows if active(r) and (r['due'] and r['due']<=today.isoformat() or r['status']=='blocked')];text='Heute fällige, überfällige und blockierte Einträge. Aufgaben ohne Frist sind nicht automatisch priorisiert.'
    elif re.search(r'frist|termin|kalender',q) and not re.search(r'dokument|datei|unterlage',q):
        mode='deadlines';rows=[r for r in rows if active(r) and r['due']];text='Offene Fristen und Termine, nach Datum sortiert.'
    elif re.search(r'projekt',q) and not re.search(r'dokument|datei|unterlage',q):
        mode='projects';rows=[r for r in rows if r['kind']=='project'];text='Projektstatus aus deinen Angaben. Fortschritt basiert auf zugeordneten Aufgaben.'
    elif re.search(r'\b(lernen|ausbildung|auditor)\b',q) and not re.search(r'dokument|datei|unterlage',q):
        mode='learning';rows=[r for r in rows if active(r) and r['kind']=='task' and re.search(r'vda|audit|lernen|ausbildung',r['title']+' '+r['body']+' '+r['tags'],re.I)];text='Offene Lernaufgaben, nach Frist sortiert. Keine erfundenen Normanforderungen oder Zertifizierung.'
    elif re.search(r'erprobt|experiment|ki-idee|ki idee',q):
        mode='lab';rows=[r for r in rows if r['module']=='laboratory' and (r['status']=='done' if 'erprobt' in q else True)];text='Gespeicherte Laboreinträge. Erledigt bedeutet deinen gespeicherten Status, keinen unabhängig bestätigten Nutzen.'
    tokens=list(dict.fromkeys(t for t in re.findall(r'[\w.-]+',q) if len(t)>1 and t not in STOP))[:12]
    hits=[]
    if mode=='search':
        ranked=[]
        for r in rows:
            hay=(r['title']+' '+r['body']+' '+r['tags']+' '+r['source']).casefold()
            score=sum(t in hay for t in tokens)
            if score:ranked.append((score,r))
        rows=[r for _,r in sorted(ranked,key=lambda p:(-p[0],p[1]['title']))]
        seen=set()
        for token in tokens:
            for h in documents.search(store,token[:200]):
                key=(h['id'],h['location'],h['snippet'])
                if key not in seen:seen.add(key);hits.append(h)
        hits=sorted(hits,key=lambda h:-sum(t in (h['title']+' '+h['snippet']).casefold() for t in tokens))[:10]
    else:rows.sort(key=lambda r:(r['due'] or '9999-12-31',r['title']))
    results=[]
    for r in rows[:20]:
        item={k:r[k] for k in ('id','title','body','kind','status','due','source','observed','evidence','project_id')}
        item['body']=item['body'][:1200]
        if r['kind']=='project':
            tasks=[t for t in store.records() if t['kind']=='task' and t['project_id']==r['id'] and t['status']!='archived']
            item['progress']={'done':sum(t['status']=='done' for t in tasks),'total':len(tasks)}
        results.append(item)
    return {'mode':mode,'message':text,'records':results,'total_records':len(rows),'documents':hits,'as_of':today.isoformat(),'limitations':'Regelbasierter Assistent: Quellen können historisch oder unbestätigt sein. Dokumente werden nur als Inhalt gelesen. Scans ohne Textschicht sind nicht auswertbar.','empty':not results and not hits}
