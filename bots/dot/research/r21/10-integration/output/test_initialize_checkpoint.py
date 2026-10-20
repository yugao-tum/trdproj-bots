"""Synthetic temporary-state tests. Never initialize the saved public observation."""
import unittest, tempfile, pathlib, json, shutil, importlib.util, time, hashlib
from datetime import datetime, timezone
B=pathlib.Path(__file__).resolve().parents[2]
REQUIRED=['04-protocol/output/virtual_ledger.py','04-protocol/output/protocol-config.json','05-quotes/output/quote_audit.py','06-scheduler/output/scheduler.py','08-criteria/output/criteria.json','08-criteria/output/criteria.py','10-integration/output/initialize_checkpoint.py']
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class InitTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.b=pathlib.Path(self.tmp.name)
  hashes={}
  for rel in REQUIRED:
   dest=self.b/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/rel,dest);hashes[rel]=hashlib.sha256(dest.read_bytes()).hexdigest()
  self.m=self.b/'manifest.json';self.m.write_text(json.dumps({'schema':'r21.forward-artifact-manifest.v1','sha256':hashes}))
  self.I=load(self.b/REQUIRED[-1],'test_initializer');self.S=load(self.b/REQUIRED[3],'test_scheduler_init');self.L=load(self.b/REQUIRED[0],'test_ledger_init')
  self.now=time.time_ns()//1000000
  c=self.S.lock_protocol(self.S.new_checkpoint(),self.L.canonical_hash(self.L.CONFIG),self.now-1000,hashlib.sha256(self.m.read_bytes()).hexdigest())
  self.c=self.b/'checkpoint.json';self.c.write_text(json.dumps(self.S.reserve_request(c,'quote_pair','synthetic',self.now-900)))
  self.interface={'schema':'r21.public-quote-interface.v1','symbol':'ETHUSDT','spot_status':'TRADING','futures_status':'TRADING','spot_lot_size':{'minQty':'0.0001','maxQty':'9000','stepSize':'0.0001'},'spot_market_lot_size':{'minQty':'0','maxQty':'3000','stepSize':'0'},'futures_lot_size':{'minQty':'0.001','maxQty':'2000','stepSize':'0.001'},'futures_market_lot_size':{'minQty':'0.001','maxQty':'2000','stepSize':'0.001'},'spot_notional_filter':{'minNotional':'5'},'futures_min_notional':{'notional':'20'},'books':{}}
  for name in ['spot','perp']:
   self.interface['books'][name]={'request_utc':datetime.fromtimestamp((self.now-500)/1000,timezone.utc).isoformat(),'response_utc':datetime.fromtimestamp((self.now-400)/1000,timezone.utc).isoformat(),'exchange_event_time_ms':None,'bids':[['1999','10']],'asks':[['2000','10']],'lastUpdateId':1}
  self.f=self.b/'synthetic-interface.json';self.save()
 def save(self):self.f.write_text(json.dumps(self.interface))
 def tearDown(self):self.tmp.cleanup()
 def call(self):return self.I.initialize(self.b,self.c,self.f,self.m,'synthetic')
 def test_success_and_no_replacement(self):
  r=self.call();self.assertEqual(r['funding_events'],0);self.assertEqual(r['entry']['quantity'],'0.623');before=self.c.read_bytes()
  with self.assertRaises(ValueError):self.call()
  self.assertEqual(before,self.c.read_bytes())
 def test_stale_invalid_persisted(self):
  self.interface['books']['spot']['response_utc']='2026-01-01T00:00:00+00:00';self.save()
  with self.assertRaises(ValueError):self.call()
  c=json.loads(self.c.read_text());self.assertIsNone(c['entry']);self.assertIsNone(c['source_status']['quote_pair']['inflight']);self.assertEqual(c['source_status']['quote_pair']['last_outcome'],'invalid')
 def test_malformed_decimal_invalid_persisted(self):
  self.interface['books']['spot']['asks'][0][0]='garbage';self.save()
  with self.assertRaises(ValueError):self.call()
  c=json.loads(self.c.read_text());self.assertIsNone(c['entry']);self.assertIsNone(c['source_status']['quote_pair']['inflight']);self.assertEqual(c['source_status']['quote_pair']['last_outcome'],'invalid')
 def test_code_tamper_no_mutation(self):
  before=self.c.read_bytes();p=self.b/REQUIRED[0];p.write_text(p.read_text()+'\n# changed\n')
  with self.assertRaises(ValueError):self.call()
  self.assertEqual(before,self.c.read_bytes())
 def test_manifest_tamper(self):
  before=self.c.read_bytes();self.m.write_text(self.m.read_text()+' ')
  with self.assertRaises(ValueError):self.call()
  self.assertEqual(before,self.c.read_bytes())
 def test_missing_reservation(self):
  c=json.loads(self.c.read_text());c['source_status']['quote_pair']['inflight']=None;self.c.write_text(json.dumps(c));before=self.c.read_bytes()
  with self.assertRaises(ValueError):self.call()
  self.assertEqual(before,self.c.read_bytes())
if __name__=='__main__':unittest.main()
