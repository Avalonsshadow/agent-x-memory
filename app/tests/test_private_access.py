import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import private_access
class PrivateAccessTests(unittest.TestCase):
    def test_pinned_origin(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private-access.json'
            self.assertEqual(private_access.request_origin(d,'pc.tail.ts.net'),'')
            p.write_text(json.dumps({'origin':'https://pc.tail.ts.net'}))
            self.assertEqual(private_access.request_origin(d,'pc.tail.ts.net'),'https://pc.tail.ts.net')
            self.assertEqual(private_access.request_origin(d,'evil.example'),'')
            self.assertEqual(private_access.request_origin(d,'pc.tail.ts.net.evil.example'),'')
            p.write_text(json.dumps({'origin':'https://evil.example'}))
            self.assertEqual(private_access.configured_origin(d),'')
    def test_invalid_names(self):
        for name in ['http://pc.tail.ts.net','https://pc.tail.ts.net/path','https://pc.tail.ts.net:443',None,'https://pc.tail.ts.net@evil.example']:
            self.assertFalse(private_access.valid_origin(name))
