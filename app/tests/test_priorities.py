import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Store
class PriorityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'data.sqlite3';self.store=Store(self.path)
        self.record=dict(kind='task',title='Test',body='',module='lounge',status='open',due='',project_id='',source='Test',evidence='confirmed',observed='2026-10-04',tags='',url='')
    def tearDown(self):self.temp.cleanup()
    def test_persist_export_and_legacy_edit(self):
        r=self.store.save({**self.record,'priority':'high'})
        self.assertEqual(Store(self.path).export()['records'][0]['priority'],'high')
        restored=Store(Path(self.temp.name)/'restored.sqlite3');restored.restore(self.store.export());self.assertEqual(restored.export()['records'][0]['priority'],'high')
        self.assertEqual(self.store.save(self.record,r['id'])['priority'],'high')
        self.assertEqual(self.store.save({**self.record,'priority':''},r['id'])['priority'],'')
    def test_reject_invalid_and_default(self):
        self.assertEqual(self.store.save(self.record)['priority'],'')
        for value in ['urgent','<script>',123]:
            with self.assertRaises(ValueError):self.store.save({**self.record,'priority':value})
    def test_migration_preserves_existing_records(self):
        r=self.store.save(self.record)
        with sqlite3.connect(self.path) as db:db.execute('ALTER TABLE records DROP COLUMN priority')
        migrated=Store(self.path).export()['records'][0]
        self.assertEqual(migrated['id'],r['id']);self.assertEqual(migrated['title'],'Test');self.assertEqual(migrated['priority'],'')
