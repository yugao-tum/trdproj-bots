import unittest
from decimal import Decimal as D
from ledger import run

P=[dict(open_time_ms=0,close_time_ms=1000,spot_open='100',spot_close='100',perp_open='100',perp_close='100',mark_close='100')]
def pay(ts=500,rate='.01',mark='100'): return dict(funding_time_ms=ts,funding_rate=rate,mark_price=mark)
class LedgerTests(unittest.TestCase):
 def test_zero_cost_no_return(self): self.assertEqual(D(run(P,[],cost='0')['summary']['ending_total_equity']),D(5000))
 def test_cost_only_four_fees(self):
  s=run(P,[])['summary']; q=D(s['quantity']); self.assertAlmostEqual(D(s['total_net_pnl']),-q*D(100)*D('.003')*4,places=40)
 def test_spot_budget_inclusive(self):
  s=run(P,[])['summary']; self.assertAlmostEqual(D(s['spot_entry_notional'])+D(s['spot_entry_fee']),D(1250),places=40)
 def test_entry_perp_fee_once(self):
  s=run(P,[])['summary']; self.assertEqual(D(s['initial_collateral']),D(2500)-D(1250)-D(s['perp_entry_fee']))
 def test_positive_funding_short_receives(self): self.assertEqual(D(run(P,[pay()],cost='0')['summary']['funding_cash']),D('12.5'))
 def test_negative_funding_short_pays(self): self.assertEqual(D(run(P,[pay(rate='-.01')],cost='0')['summary']['funding_cash']),D('-12.5'))
 def test_entry_excluded_exit_included(self):
  s=run(P,[pay(0),pay(1000),pay(1001)],cost='0')['summary']; self.assertEqual(s['payment_count'],1); self.assertEqual(s['payments_at_entry_excluded'],1)
 def test_funding_actual_mark(self): self.assertEqual(D(run(P,[pay(mark='120')],cost='0')['summary']['funding_cash']),D(15))
 def test_equal_asset_rise_hedges_price(self):
  p=[dict(P[0],spot_close='200',perp_close='200',mark_close='200')]; self.assertEqual(D(run(p,[],cost='0')['summary']['total_net_pnl']),D(0))
 def test_basis_decomposition(self):
  p=[dict(P[0],spot_close='200',perp_close='210',mark_close='210')]; self.assertEqual(D(run(p,[],cost='0')['summary']['basis_change_pnl']),D(-125))
 def test_insolvency_not_hidden(self):
  p=[dict(P[0],spot_close='400',perp_close='400',mark_close='400')]; s=run(p,[],cost='0')['summary']; self.assertTrue(s['observed_negative_margin']); self.assertEqual(D(s['total_net_pnl']),D(0))
 def test_duplicate_funding_rejected(self):
  with self.assertRaises(ValueError): run(P,[pay(),pay()])
 def test_negative_mark_rejected(self):
  with self.assertRaises(ValueError): run(P,[pay(mark='-1')])
 def test_small_budget(self): self.assertEqual(D(run(P,[],budget='625',cost='0')['summary']['initial_collateral']),D(1875))
 def test_nan_rejected(self):
  with self.assertRaises(ValueError): run(P,[pay(rate='NaN')])
 def test_conservation(self):
  s=run(P,[pay(),pay(600,'-.003','90')],cost='.006')['summary']; self.assertLess(abs(D(s['cash_conservation_residual'])),D('1e-40'))
if __name__=='__main__': unittest.main()
