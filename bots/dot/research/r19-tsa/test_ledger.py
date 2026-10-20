import unittest
from ledger import D,fee,choose,simulate
class LedgerTests(unittest.TestCase):
 def test_fee_ceil(self): self.assertEqual(fee(1,D('.5'),D('.07')),D('.02'))
 def test_fee_whole_order(self): self.assertEqual(fee(50,D('.5'),D('.07')),D('.88'))
 def test_capacity(self): self.assertEqual(choose(.9,.5,1500,2500)['quantity'],15)
 def test_cap50(self): self.assertEqual(choose(.9,.5,100000,2500)['quantity'],50)
 def test_no_volume(self): self.assertEqual(choose(.9,.5,99,2500)['status'],'no_trade')
 def test_no_cash(self): self.assertEqual(choose(.9,.5,10000,0)['status'],'no_trade')
 def test_cash_ceiling(self): self.assertLessEqual(choose(.9,.5,10000,1)['cost'],1)
 def test_complement_side(self): self.assertEqual(choose(.1,.5,10000,2500)['side'],'no')
 def test_small_edge(self): self.assertEqual(choose(.5,.5,10000,2500)['status'],'no_trade')
 def test_rounding_edge(self): self.assertEqual(choose(.621,.5,100,2500)['status'],'conditional_trade')
 def test_bad_price_cannot_buy(self): self.assertEqual(choose(.999,.99,10000,2500)['status'],'no_trade')
 def test_conservative_max_quantity_skip(self):
  prob=D('.11583333333333333');observed=D('.01');p=observed+D('.05')
  chosen=choose(prob,observed,300,2500)
  self.assertEqual(chosen['reason'],'rounded_fee_edge_below_0.05')
  self.assertLess(prob-p-fee(3,p,D('.07'))/3,D('.05'))
  self.assertGreaterEqual(prob-p-fee(2,p,D('.07'))/2,D('.05'))
 def test_settle_lock(self):
  rows=[dict(ticker='A',target_date='2021-01-01',decision_ts='2021-01-01T00:00:00Z',anchor_ts='2021-01-01T01:00:00Z',prob=.9,yes_price=.5,window_volume=10000,tape_complete=True,result='yes',settlement_ts='2021-01-04T00:00:00Z'),dict(ticker='B',target_date='2021-01-02',decision_ts='2021-01-02T00:00:00Z',anchor_ts='2021-01-02T01:00:00Z',prob=.9,yes_price=.5,window_volume=10000,tape_complete=True,result='no',settlement_ts='2021-01-05T00:00:00Z')]
  r=simulate(rows);self.assertEqual(r['records'][1]['cash_before'],D('2471.63'));self.assertEqual(r['summary']['max_locked_cost'],D('56.74'));self.assertEqual(r['summary']['net_pnl'],D('-6.74'))
 def test_excluded_retained(self):
  r=simulate([dict(ticker='A',decision_ts='2021-01-01T00:00:00Z',exclusion_reasons=['unknown_timezone'])]);self.assertEqual(len(r['records']),1);self.assertEqual(r['summary']['trades'],0)
if __name__=='__main__':unittest.main()
