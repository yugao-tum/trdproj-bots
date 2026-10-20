import csv,json,unittest,hashlib
from pathlib import Path
import reproduce as r
O=Path(__file__).resolve().parent
M=json.loads((O/'source-manifest.json').read_text());E=r.load_engine(M['inputs'][0]['path'])
class Checks(unittest.TestCase):
 def test_initial(self):
  self.assertEqual(r.decision(dict.fromkeys(E.SYMBOLS,0),2500,dict.fromkeys(E.SYMBOLS,1),E),'initial')
 def test_exact_band_no_trigger(self):
  # Assets=2500,target=2200; one asset underweight exactly125=5pp.
  q=dict(zip(E.SYMBOLS,[2200/3-125,2200/3,2200/3]))
  self.assertEqual(r.decision(q,425,dict.fromkeys(E.SYMBOLS,1),E),'skip')
 def test_above_band(self):
  q=dict(zip(E.SYMBOLS,[2200/3-126,2200/3,2200/3]))
  self.assertEqual(r.decision(q,426,dict.fromkeys(E.SYMBOLS,1),E),'weight_band')
 def test_cap_priority(self):
  self.assertEqual(r.decision(dict.fromkeys(E.SYMBOLS,740),280,dict.fromkeys(E.SYMBOLS,1),E),'position_cap')
 def test_preserved_sources(self):
  for x in M['inputs']:self.assertEqual(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest(),x['sha256'])
 def test_independent_ledger(self):
  prices={}
  for x in csv.DictReader(Path(M['inputs'][1]['path']).read_text().splitlines()):prices[(x['open_time_utc'][:10],x['symbol'])]=float(x['close'])
  result=json.loads((O/'results.json').read_text())
  for cost in [.003,.006]:
   for mode in ['baseline','band_5pp']:
    prefix=f'{mode}-{cost:.3f}';cash=2500.;q=dict.fromkeys(E.SYMBOLS,0.)
    trades=list(csv.DictReader((O/(prefix+'-trades.csv')).read_text().splitlines()));days=list(csv.DictReader((O/(prefix+'-daily.csv')).read_text().splitlines()))
    fee=0.;gross=0.;prior_values=0.
    for day in days:
     d=day['date'];today=[t for t in trades if t['day']==d]
     for t in today:
      qty=float(t['qty']);price=float(t['price']);notional=qty*price;f=notional*cost;fee+=f
      self.assertAlmostEqual(f,float(t['fee']),places=9)
      if t['side']=='BUY':cash-=notional+f;q[t['symbol']]+=qty
      else:cash+=notional-f;q[t['symbol']]-=qty
      self.assertGreaterEqual(cash,-1e-8);self.assertGreaterEqual(q[t['symbol']],-1e-8)
      self.assertAlmostEqual(cash,float(t['cash_after']),places=8)
     holdings=sum(q[s]*prices[(d,s)] for s in E.SYMBOLS)
     self.assertAlmostEqual(cash+holdings+2500,float(day['total_equity']),places=8)
    p=result['details'][prefix]['periods']['full']
    self.assertAlmostEqual(cash-2500,p['net_pnl_usdt'],places=8)
    self.assertAlmostEqual(fee,p['fees_usdt'],places=8)
    self.assertTrue(all(abs(x)<1e-9 for x in q.values()))
    self.assertEqual(len(result['details'][prefix]['episodes']),1)
if __name__=='__main__':unittest.main()
