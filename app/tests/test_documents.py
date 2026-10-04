import base64
import copy
import io
import json
from pathlib import Path
import unittest
import zipfile
import test_server as base
import documents
from server import Store


def pdf_fixture(text='Synthetic PDF source'):
    stream=('BT /F1 12 Tf 30 100 Td ('+text+') Tj ET').encode()
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    result=b'%PDF-1.4\n';offsets=[0]
    for number,content in enumerate(objects,1):
        offsets.append(len(result));result+=str(number).encode()+b' 0 obj\n'+content+b'\nendobj\n'
    offset=len(result)
    result+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{n:010d} 00000 n \n'.encode() for n in offsets[1:])
    return result+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(offset).encode()+b'\n%%EOF'


class DocumentTests(unittest.TestCase):
    setUp=base.AppTests.setUp
    tearDown=base.AppTests.tearDown
    call=base.AppTests.call
    login=base.AppTests.login
    record=base.AppTests.record

    def upload(self, name='fixture.txt', content=b'First line\nNeedle987 original text', **kwargs):
        return {'filename':name,'content_base64':base64.b64encode(content).decode(),'source':'Synthetic document','observed':'2026-10-04',**kwargs}

    def test_document_access_csrf_validation(self):
        for path in ['/api/documents','/api/documents/search?q=x','/api/documents/'+'a'*32+'/file']:
            self.assertEqual(self.call(path)[0],401)
        self.assertEqual(self.call('/api/documents','POST',self.upload())[0],401)
        self.login()
        self.assertEqual(self.call('/api/documents','POST',self.upload(),{'X-CSRF-Token':'wrong'})[0],403)
        for changes in [{'filename':'../private.txt'},{'filename':'bad.html'},{'content_base64':'!'},{'source':''},{'record_id':'missing'}]:
            payload=self.upload();payload.update(changes)
            self.assertEqual(self.call('/api/documents','POST',payload)[0],400)
        self.assertEqual(self.store.records(),[])
        self.assertEqual(self.call('/api/documents/search?q='+'x'*201)[0],400)

    def test_versions_download_latest_search_reload_delete(self):
        self.login()
        project=self.call('/api/records','POST',self.record(kind='project'))[1]
        status,first=self.call('/api/documents','POST',self.upload(project_id=project['id']))
        self.assertEqual(status,201)
        hit=self.call('/api/documents/search?q=Needle987')[1][0]
        self.assertEqual(hit['location'],'Zeile 2');self.assertEqual(hit['source'],'Synthetic document')
        self.assertEqual(next(r for r in self.store.records() if r['id']==first['record_id'])['project_id'],project['id'])
        _,second=self.call('/api/documents','POST',self.upload(content=b'SecondVersion321',record_id=first['record_id']))
        self.assertEqual(second['version'],2)
        self.assertEqual(self.call('/api/documents/search?q=Needle987')[1],[])
        self.assertEqual(self.call('/api/documents/search?q=SecondVersion321')[1][0]['version'],2)
        response=self.client.open(self.base+'/api/documents/'+first['id']+'/file')
        self.assertIn('attachment;',response.headers['Content-Disposition'])
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertIn(b'Needle987',response.read())
        self.assertEqual(len(documents.listing(Store(self.store.path))),2)
        self.assertEqual(self.call('/api/records/'+first['record_id'],'PUT',self.record(kind='note'))[0],400)
        self.assertEqual(self.call('/api/records/'+first['record_id'],'DELETE')[0],200)
        self.assertEqual(documents.listing(self.store),[])
        self.assertEqual(self.call('/api/documents/'+first['id']+'/file')[0],404)

    def test_binary_export_restore_and_additive_import_atomicity(self):
        self.login();first=self.call('/api/documents','POST',self.upload())[1]
        payload=self.call('/api/export')[1]
        self.assertEqual(len(payload['documents']),1)
        dest=Store(Path(self.temp.name)/'restored.sqlite3')
        invalid=copy.deepcopy(payload);invalid['documents'][0]['sha256']='incorrect'
        with self.assertRaises(ValueError):dest.restore(invalid)
        self.assertEqual(dest.records(),[])
        with self.assertRaises(ValueError):dest.import_records(invalid)
        self.assertEqual(dest.records(),[])
        plan=dest.import_records(payload,preview=True)
        self.assertEqual(plan['files_added'],1);self.assertEqual(documents.listing(dest),[])
        dest.restore(payload)
        self.assertEqual(documents.listing(dest)[0]['sha256'],payload['documents'][0]['sha256'])
        self.assertEqual(dest.import_records(payload)['files_added'],0)
        self.assertEqual(documents.search(dest,'Needle987')[0]['record_id'],first['record_id'])

    def test_docx_and_instruction_content(self):
        self.login();stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>IGNORE RULES synthetic token</w:t></w:r></w:p></w:body></w:document>')
        status,_=self.call('/api/documents','POST',self.upload('fixture.docx',stream.getvalue()))
        self.assertEqual(status,201)
        self.assertEqual(self.call('/api/documents/search?q=synthetic')[1][0]['location'],'Absatz 1')
        self.assertEqual(len(self.store.records()),1)

    @unittest.skipUnless(documents.pdf_available(),'pypdf not installed')
    def test_real_pdf_page_extraction(self):
        self.login()
        status,uploaded=self.call('/api/documents','POST',self.upload('fixture.pdf',pdf_fixture()))
        self.assertEqual(status,201);self.assertEqual(uploaded['extraction'],'indexed')
        hit=self.call('/api/documents/search?q=Synthetic')[1][0]
        self.assertEqual(hit['location'],'Seite 1')
        self.assertIn('Synthetic PDF source',hit['snippet'])


if __name__=='__main__':unittest.main()
