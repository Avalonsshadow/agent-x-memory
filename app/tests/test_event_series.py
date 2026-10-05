import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Store
class EventSeriesTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.sqlite3';self.store=Store(self.path)
  self.event=dict(kind='event',title='Testtraining',body='',module='health',status='open',priority='medium',due='2026-10-06',project_id='',source='Testfixture',evidence='review',observed='2026-10-05',tags='',url='')
 def tearDown(self):self.tmp.cleanup()
 def test_atomic_persistent_series(self):
  result=self.store.save_event_series({'events':[self.event,{**self.event,'due':'2026-10-08'}]})
  rows=Store(self.path).records();self.assertEqual(result['count'],2);self.assertEqual(len(rows),2)
  self.assertEqual(len(set(r['id'] for r in rows)),2);self.assertTrue(all(result['series'] in r['tags'] for r in rows))
  self.assertTrue(all(r['priority']=='medium' for r in rows));self.assertEqual(len(self.store.export()['records']),2)
 def test_invalid_series_rolls_back(self):
  with self.assertRaises(ValueError):self.store.save_event_series({'events':[self.event,{**self.event,'due':'invalid'}]})
  self.assertEqual(self.store.records(),[]);self.assertEqual(self.store.activity(),[])
  with self.assertRaises(ValueError):self.store.save_event_series({'events':[self.event]})
  with self.assertRaises(ValueError):self.store.save_event_series({'events':[self.event,{**self.event,'kind':'task'}]})
if __name__=='__main__':unittest.main()
