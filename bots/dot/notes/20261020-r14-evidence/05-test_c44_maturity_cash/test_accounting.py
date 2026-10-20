import unittest
from decimal import Decimal as D
from reproduce import run
class CashTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_counts_not_results(self):self.assertEqual(self.r['total_daily_rows'],933);self.assertEqual(self.r['independent_complete_outcomes'],0)
 def test_actual_unknown(self):self.assertIsNone(self.r['actual_executable_cash_pnl'])
 def test_fixed_entry(self):self.assertTrue(self.r['entry_date'].startswith('2023-09-12'))
 def test_no_fill(self):self.assertEqual(D(self.r['entry_daily_volume_usd']),0)
 def test_units(self):self.assertLess(abs(D(self.r['receipt_eusd_per_pt_unit_check'])-1),D('1e-17'))
 def test_fee_budget(self):
  s=self.r['scenarios']['guide_cost_proxy'];self.assertLess(abs(D(s['pt_quantity'])*D(self.r['entry_mark_usd'])*D('1.003')-2500),D('1e-40'))
 def test_cost_monotonicity(self):self.assertLess(D(self.r['scenarios']['guide_cost_proxy']['conditional_pnl_before_gas_usdt']),D(self.r['scenarios']['zero_cost_ceiling']['conditional_pnl_before_gas_usdt']))
 def test_negative_even_no_fee(self):self.assertLess(D(self.r['scenarios']['zero_cost_ceiling']['conditional_pnl_before_gas_usdt']),0)
 def test_denominator(self):
  s=self.r['scenarios']['guide_cost_proxy'];self.assertEqual(D(s['capital_return_before_gas'])*5000,D(s['conditional_pnl_before_gas_usdt']))
 def test_breakeven(self):
  s=self.r['scenarios']['guide_cost_proxy'];self.assertLess(abs(D(s['pt_quantity'])*D(s['breakeven_eusd_usd_before_gas'])*D('.997')-2500),D('1e-40'))
if __name__=='__main__':unittest.main()
