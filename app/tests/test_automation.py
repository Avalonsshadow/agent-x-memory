import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from server import Store
from automation import ImportWorker
from start_agent_x import update, unpack_app


class AutomationTests(unittest.TestCase):
    def package(self):
        return {'schema_version': 1, 'records': [dict(id='a'*32, kind='note', title='Synthetic import', body='Instructions are only content.', module='lounge', status='open', due='', project_id='', source='Testfixture', evidence='review', observed='2026-10-04', tags='', url='', created='2026-10-04T10:00:00+00:00', updated='2026-10-04T10:00:00+00:00')]}

    def test_worker_import_backup_repeat_and_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp)/'data.sqlite3')
            worker = ImportWorker(store)
            inbox = worker.directory/'inbox'
            (inbox/'first.json').write_text(json.dumps(self.package()))
            worker.scan()
            self.assertEqual(store.records(), [])
            worker.scan()
            self.assertEqual(len(store.records()), 1)
            backups = list(worker.backups.glob('*.sqlite3'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(Store(backups[0]).records(), [])
            (inbox/'repeat.json').write_text(json.dumps(self.package()))
            worker.scan(); worker.scan()
            self.assertEqual(len(store.records()), 1)
            self.assertEqual(worker.status()['last_result']['added'], 0)
            (inbox/'invalid.json').write_text('{invalid')
            worker.scan(); worker.scan()
            self.assertTrue(worker.status()['error'])
            self.assertEqual(len(list((worker.directory/'failed').glob('*.json'))), 1)
            self.assertEqual(len(store.records()), 1)

    def archive(self, extra=None):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for name, body in {'server.py':'# new server', 'automation.py':'# new worker', 'web/app.js':'// new', 'web/index.html':'new', 'web/style.css':'new', **(extra or {})}.items():
                archive.writestr('repo/app/'+name, body)
        return stream.getvalue()

    def test_background_worker_runs_and_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(Path(temp)/'data.sqlite3')
            worker=ImportWorker(store,interval=0.02)
            (worker.directory/'inbox/test.json').write_text(json.dumps(self.package()))
            worker.start()
            try:
                deadline=time.monotonic()+2
                while not worker.status()['last_success'] and time.monotonic()<deadline:
                    time.sleep(0.01)
                self.assertTrue(worker.status()['last_success'])
                self.assertEqual(len(store.records()),1)
            finally:
                worker.close()
            self.assertFalse(worker.thread.is_alive())

    def test_update_backup_repeat_and_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'repo';state=Path(temp)/'private';(root/'app').mkdir(parents=True)
            (root/'app/server.py').write_text('# old')
            calls=[]
            def fake(url,limit):
                calls.append(url)
                return json.dumps([{'sha':'b'*40}]).encode() if 'api.github.com' in url else self.archive()
            self.assertEqual(update(root,state,fake)['status'], 'updated')
            self.assertEqual((root/'app/server.py').read_text(), '# new server')
            self.assertEqual(next((state/'code-backups').rglob('server.py')).read_text(), '# old')
            self.assertEqual(update(root,state,fake)['status'], 'current')
            self.assertEqual(len(calls), 3)
            def offline(url,limit): raise OSError('Offline')
            self.assertEqual(update(root,state,offline)['status'], 'error')
            self.assertEqual((root/'app/server.py').read_text(), '# new server')

    def test_invalid_archive_preserves_code_and_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo';state=Path(temp)/'private';(root/'app').mkdir(parents=True)
            (root/'app/server.py').write_text('# old')
            def fake(url,limit):
                return json.dumps([{'sha':'b'*40}]).encode() if 'api.github.com' in url else self.archive({'server.py':'this is invalid Python !'})
            self.assertEqual(update(root,state,fake)['status'], 'error')
            self.assertEqual((root/'app/server.py').read_text(), '# old')
            with self.assertRaises(ValueError):
                unpack_app(self.archive({'../../outside.txt':'bad'}),Path(temp)/'staged')
            self.assertFalse((Path(temp)/'outside.txt').exists())


if __name__ == '__main__': unittest.main()
