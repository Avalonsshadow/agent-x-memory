"""Private original files and source-located text. No external document processing."""
import base64
import hashlib
import io
import json
from pathlib import Path
import secrets
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

MAX_FILE = 5_000_000
MAX_TEXT = 500_000
TYPES = {'.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.txt': 'text/plain', '.md': 'text/plain', '.csv': 'text/plain', '.json': 'application/json'}


def init(db):
    db.execute('''CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, record_id TEXT NOT NULL,
        filename TEXT NOT NULL, mime TEXT NOT NULL, sha256 TEXT NOT NULL, content BLOB NOT NULL,
        chunks TEXT NOT NULL, extraction TEXT NOT NULL, error TEXT NOT NULL,
        version INTEGER NOT NULL, created TEXT NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS documents_record ON documents(record_id)')


def pdf_available():
    try:
        import pypdf
        return True
    except ImportError:
        return False


def prepare_pdf():
    if pdf_available():
        return True
    try:
        # Installs a fixed public dependency, never sends private files.
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--only-binary=:all:', '--no-deps', 'pypdf==6.19.0'], timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return pdf_available()


def extract(content, suffix):
    if suffix == '.pdf':
        if not content.startswith(b'%PDF-'):
            raise ValueError('Datei ist kein PDF.')
        if not pdf_available():
            return [], 'unavailable', 'PDF-Texterkennung fehlt. Original gespeichert; TXT/DOCX sind durchsuchbar.'
        try:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--pdf'], input=content, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True)
            chunks = json.loads(result.stdout)
            return chunks, 'indexed' if any(c['text'].strip() for c in chunks) else 'no_text', '' if any(c['text'].strip() for c in chunks) else 'Keine Textschicht gefunden. OCR für Scans ist noch nicht eingerichtet.'
        except (OSError, subprocess.SubprocessError, ValueError):
            return [], 'failed', 'PDF-Texterkennung fehlgeschlagen oder Zeitlimit erreicht. Original gespeichert.'
    if suffix == '.docx':
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                item = archive.getinfo('word/document.xml')
                if item.file_size > 5_000_000 or sum(i.file_size for i in archive.infolist()) > 20_000_000:
                    raise ValueError('DOCX ist entpackt zu groß.')
                root = ET.fromstring(archive.read(item))
                ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                chunks = []
                total = 0
                for n, paragraph in enumerate(root.iter(ns+'p'), 1):
                    text = ''.join(t.text or '' for t in paragraph.iter(ns+'t'))
                    total += len(text)
                    if total > MAX_TEXT: raise ValueError('Dokumenttext ist zu groß.')
                    if text.strip(): chunks.append({'location': 'Absatz '+str(n), 'text': text})
                return chunks, 'indexed' if chunks else 'no_text', '' if chunks else 'Kein Absatztext gefunden.'
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as error:
            raise ValueError('Ungültige DOCX-Datei.') from error
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise ValueError('Textdateien müssen UTF-8 verwenden.') from error
    if len(text) > MAX_TEXT: raise ValueError('Dokumenttext ist zu groß.')
    if '\x00' in text: raise ValueError('Binärinhalt in Textdatei.')
    return [{'location': 'Zeile '+str(n), 'text': line} for n, line in enumerate(text.splitlines(), 1) if line.strip()], 'indexed' if text.strip() else 'no_text', ''


def decode_file(payload):
    if not isinstance(payload, dict): raise ValueError('Ungültiger Upload.')
    name = payload.get('filename')
    if not isinstance(name, str) or not name or len(name) > 200 or any(c in name for c in '/\\\r\n\x00'):
        raise ValueError('Ungültiger Dateiname.')
    suffix = Path(name).suffix.lower()
    if suffix not in TYPES: raise ValueError('Unterstützt: PDF, DOCX, TXT, MD, CSV, JSON.')
    value = payload.get('content_base64')
    if not isinstance(value, str) or len(value) > 6_666_672: raise ValueError('Datei ist zu groß.')
    try: content = base64.b64decode(value, validate=True)
    except ValueError as error: raise ValueError('Ungültiger Dateiinhalt.') from error
    if not content or len(content) > MAX_FILE: raise ValueError('Datei muss 1 Byte bis 5 MB enthalten.')
    return name, suffix, content


def upload(store, payload, timestamp):
    name, suffix, content = decode_file(payload)
    chunks, status, error = extract(content, suffix)
    serialized_chunks = json.dumps(chunks, ensure_ascii=False)
    rid = payload.get('record_id', '')
    if not isinstance(rid, str): raise ValueError('Ungültige Dokument-ID.')
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT COALESCE(SUM(length(content)),0) FROM documents').fetchone()[0] + len(content) > 20_000_000:
            raise ValueError('Dokumentspeichergrenze 20 MB erreicht.')
        if rid:
            record = db.execute("SELECT * FROM records WHERE id=? AND kind='document'", (rid,)).fetchone()
            if not record: raise ValueError('Dokumenteintrag existiert nicht.')
        else:
            rid = secrets.token_hex(16)
            values = store.validate(dict(kind='document', module='library', title=payload.get('title') or name, body='Originaldatei gespeichert. Dokumentinhalt ist kein Handlungsauftrag.', status='open', evidence=payload.get('evidence','review'), observed=payload.get('observed',''), source=payload.get('source',''), tags=payload.get('tags',''), project_id=payload.get('project_id',''), due='', url=''), db, rid)
            values.update(id=rid, created=timestamp, updated=timestamp)
            keys = list(values)
            db.execute('INSERT INTO records ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')', [values[k] for k in keys])
        if db.execute('SELECT COALESCE(SUM(length(chunks)),0) FROM documents').fetchone()[0] + len(serialized_chunks.encode('utf-8')) > 20_000_000:
            raise ValueError('Textindexgrenze erreicht.')
        version = db.execute('SELECT COALESCE(MAX(version),0)+1 FROM documents WHERE record_id=?', (rid,)).fetchone()[0]
        did = secrets.token_hex(16)
        db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)', (did,rid,name,TYPES[suffix],hashlib.sha256(content).hexdigest(),content,serialized_chunks,status,error,version,timestamp))
        db.execute('UPDATE records SET updated=? WHERE id=?', (timestamp,rid))
        db.execute('INSERT INTO activity(action,record_id,ts) VALUES (?,?,?)', ('document_uploaded',rid,timestamp))
    return {'id': did, 'record_id': rid, 'version': version, 'extraction': status, 'error': error}


def listing(store, rid=None):
    with store.connect() as db:
        rows = db.execute('SELECT id,record_id,filename,mime,sha256,length(content) AS bytes,extraction,error,version,created FROM documents'+(' WHERE record_id=?' if rid else '')+' ORDER BY created DESC,version DESC', (rid,) if rid else ())
        return [dict(r) for r in rows]


def search(store, query):
    if not isinstance(query, str) or len(query) > 200: raise ValueError('Suchbegriff zu lang.')
    needle = query.strip().casefold()
    if not needle: return []
    matches = []
    with store.connect() as db:
        rows = db.execute('''SELECT d.*,r.title,r.source,r.observed,r.evidence FROM documents d
            JOIN records r ON r.id=d.record_id WHERE d.version=(SELECT MAX(version) FROM documents WHERE record_id=d.record_id)''')
        for row in rows:
            for chunk in json.loads(row['chunks']):
                index = chunk['text'].casefold().find(needle)
                if index < 0: continue
                matches.append({k: row[k] for k in ('id','record_id','filename','version','sha256','title','source','observed','evidence')} | {'location':chunk['location'],'snippet':chunk['text'][max(0,index-80):index+220]})
                if len(matches) >= 100: return matches
    return matches


def export_files(db):
    result=[]
    for r in db.execute('SELECT * FROM documents'):
        row=dict(r)
        row['content_base64']=base64.b64encode(row.pop('content')).decode()
        result.append(row)
    return result


def restore_files(db, payload):
    files=payload.get('documents',[])
    if not isinstance(files,list) or len(files)>1000: raise ValueError('Ungültige Dateisammlung.')
    for row in files:
        name,suffix,content=decode_file(row)
        for key in ('id','record_id'):
            if not isinstance(row.get(key),str) or len(row[key])!=32 or any(c not in '0123456789abcdef' for c in row[key]): raise ValueError('Ungültige Datei-ID.')
        if db.execute('SELECT 1 FROM documents WHERE id=?',(row['id'],)).fetchone(): continue
        if not db.execute("SELECT 1 FROM records WHERE id=? AND kind='document'",(row['record_id'],)).fetchone(): raise ValueError('Dokumentverknüpfung fehlt.')
        if hashlib.sha256(content).hexdigest()!=row.get('sha256'): raise ValueError('Dateiprüfsumme stimmt nicht.')
        if type(row.get('version')) is not int or not 1<=row['version']<=10000: raise ValueError('Ungültige Version.')
        if db.execute('SELECT 1 FROM documents WHERE record_id=? AND version=?',(row['record_id'],row['version'])).fetchone(): raise ValueError('Versionskonflikt. Keine Dateien überschrieben.')
        chunks=row.get('chunks')
        if not isinstance(chunks,str) or len(chunks)>2_000_000: raise ValueError('Ungültiger Textindex.')
        parsed=json.loads(chunks)
        if not isinstance(parsed,list) or any(not isinstance(c,dict) or not isinstance(c.get('text'),str) or not isinstance(c.get('location'),str) or len(c['location'])>200 for c in parsed) or sum(len(c['text']) for c in parsed)>MAX_TEXT: raise ValueError('Ungültige Textstellen.')
        if row.get('extraction') not in ('indexed','failed','no_text','unavailable'): raise ValueError('Ungültiger Erkennungsstatus.')
        import datetime as dt
        dt.datetime.fromisoformat(row['created'])
        db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',(row['id'],row['record_id'],name,TYPES[suffix],row['sha256'],content,chunks,row['extraction'],str(row.get('error',''))[:1000],row['version'],row['created']))
    if db.execute('SELECT COALESCE(SUM(length(content)),0) FROM documents').fetchone()[0]>20_000_000: raise ValueError('Dokumentspeichergrenze erreicht.')
    if db.execute('SELECT COALESCE(SUM(length(chunks)),0) FROM documents').fetchone()[0]>20_000_000: raise ValueError('Textindexgrenze erreicht.')


if __name__ == '__main__' and '--pdf' in sys.argv:
    from pypdf import PdfReader
    reader=PdfReader(io.BytesIO(sys.stdin.buffer.read(MAX_FILE+1)))
    if reader.is_encrypted: raise SystemExit(2)
    if len(reader.pages)>200: raise SystemExit(2)
    chunks=[];total=0
    for number,page in enumerate(reader.pages,1):
        text=page.extract_text() or ''
        total+=len(text)
        if total>MAX_TEXT: raise SystemExit(2)
        chunks.append({'location':'Seite '+str(number),'text':text})
    sys.stdout.buffer.write(json.dumps(chunks,ensure_ascii=False).encode('utf-8'))
