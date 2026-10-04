import json
import time
import unittest
from urllib.parse import urlsplit,parse_qs
from unittest.mock import Mock,patch
import test_server as base
import drive
from live_updates import Updates

CLIENT={'installed':{'client_id':'test.apps.googleusercontent.com','client_secret':'synthetic-secret'}}
class DriveTests(unittest.TestCase):
    setUp=base.AppTests.setUp
    tearDown=base.AppTests.tearDown
    call=base.AppTests.call
    login=base.AppTests.login
    def test_access_configuration_and_csrf(self):
        for p in ['/api/drive/status','/api/drive/files']: self.assertEqual(self.call(p)[0],401)
        self.login()
        self.assertEqual(self.call('/api/drive/configure','POST',CLIENT,{'X-CSRF-Token':'bad'})[0],403)
        self.assertEqual(self.call('/api/drive/configure','POST',CLIENT)[0],200)
        status=self.call('/api/drive/status')[1]
        self.assertNotIn('secret',json.dumps(status));self.assertEqual(status['status'],'configured')
        self.assertEqual(self.call('/api/drive/select','POST',{'ids':['../../bad']})[0],400)
        self.assertEqual(self.call('/api/drive/configure','POST',{'web':CLIENT['installed']})[0],400)
    def test_oauth_pkce_single_use_expiry_and_scope(self):
        d=self.server.drive;d.configure(CLIENT);session=self.store.login('Test-only-password-42!')[0]
        query=parse_qs(urlsplit(d.begin(self.base+'/api/google/callback',session)['url']).query)
        self.assertEqual(query['code_challenge_method'],['S256']);self.assertEqual(query['scope'],[drive.SCOPE])
        token={'scope':drive.SCOPE,'refresh_token':'fixture-refresh','access_token':'fixture-access','expires_in':3600}
        transport=Mock(return_value=json.dumps(token).encode());d.transport=transport
        d.complete(query['state'][0],'fixture-code');self.assertEqual(d.status()['status'],'connected')
        self.assertIn('code_verifier',transport.call_args.args[1])
        with self.assertRaises(ValueError): d.complete(query['state'][0],'replayed')
        q=parse_qs(urlsplit(d.begin(self.base+'/api/google/callback',session)['url']).query);d.pending[q['state'][0]]['expires']=0
        with self.assertRaises(ValueError):d.complete(q['state'][0],'expired')
        q=parse_qs(urlsplit(d.begin(self.base+'/api/google/callback',session)['url']).query)
        transport.return_value=json.dumps({'scope':'wrong','access_token':'bad'}).encode()
        with self.assertRaises(ValueError):d.complete(q['state'][0],'wrongscope')
        reopened=drive.Drive(self.store);self.assertEqual(reopened.state['refresh_token'],'fixture-refresh')
        self.assertNotIn('fixture-refresh',json.dumps(self.store.export()))
    def test_selected_sync_versions_errors_refresh_and_disconnect(self):
        d=self.server.drive;d.configure(CLIENT);d.state.update(refresh_token='refresh',expires=0)
        content=[b'First drive source text'];modified=['2026-10-04T13:00:00Z'];calls=[]
        def transport(url,data=None,token=None,limit=5000000):
            calls.append((url,data,token))
            if data:return json.dumps({'access_token':'renewed','expires_in':3600}).encode()
            if 'alt=media' in url:return content[0]
            return json.dumps({'id':'file1','name':'example.txt','mimeType':'text/plain','size':len(content[0]),'modifiedTime':modified[0]}).encode()
        d.transport=transport;d.select(['file1']);self.assertEqual(d.sync()['added_versions'],1)
        rid=self.store.records()[0]['id'];self.assertEqual(d.sync()['added_versions'],0)
        content[0]=b'Second source';modified[0]='2026-10-04T14:00:00Z';self.assertEqual(d.sync()['added_versions'],1)
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM documents').fetchone()[0],2)
        self.assertEqual(self.store.records()[0]['id'],rid);self.assertTrue(any(data for _,data,_ in calls))
        d.transport=Mock(side_effect=ValueError('Google-Anfrage fehlgeschlagen (HTTP 403).'))
        result=d.sync();self.assertTrue(result['errors']);self.assertIn('403',d.status()['error'])
        self.assertTrue(list((self.store.path.parent/'backups').glob('*.sqlite3')))
        d.disconnect();self.assertEqual(d.status()['status'],'not_configured');self.assertEqual(len(self.store.records()),1)
    def test_listing_failure_and_automatic_worker(self):
        d=self.server.drive;d.state.update(refresh_token='refresh',access_token='access',expires=time.time()+1000)
        d.transport=Mock(return_value=json.dumps({'files':[{'id':'abc','name':'fixture.txt'}],'nextPageToken':'page2'}).encode())
        self.assertEqual(d.files()['nextPageToken'],'page2')
        d.transport=Mock(side_effect=ValueError('Offline'))
        with self.assertRaises(ValueError):d.files()
        self.assertEqual(d.status()['error'],'Offline')
        d.sync=Mock(return_value={});worker=drive.Worker(d,interval=.01);worker.start();time.sleep(.04);worker.close();self.assertGreater(d.sync.call_count,0)
    def test_live_update_check_restart_and_failure(self):
        state=self.store.path.parent;(state/'update-status.json').write_text(json.dumps({'revision':'a'*40}))
        u=Updates(self.server);u.server=Mock(store=self.store);u.updater.fetch=Mock(return_value=json.dumps([{'sha':'a'*40}]).encode());u.check();u.server.shutdown.assert_not_called()
        u.updater.fetch.return_value=json.dumps([{'sha':'b'*40}]).encode();u.check();u.server.shutdown.assert_called_once();self.assertTrue(u.restart)
        u.updater.update=Mock(return_value={'status':'updated'})
        with patch('live_updates.os.execv') as restart:u.apply();restart.assert_called_once()
        self.assertTrue(list((state/'backups').glob('*.sqlite3')))
        u.restart=False;u.updater.fetch=Mock(side_effect=ValueError('offline'));u.check();self.assertFalse(u.restart);self.assertIn('fehlgeschlagen',u.error)
