import unittest
from capital_account import CapitalAccount
class LedgerTests(unittest.TestCase):
 def test_cash(self):
  a=CapitalAccount();a.begin_day('2024-01-01',{});r=a.snapshot({},{});self.assertEqual(r['total_equity'],5000)
 def test_trade_fees(self):
  a=CapitalAccount();a.begin_day('2024-01-01',{'B':100});a.rebalance({'B':100},{'B':1100});r=a.snapshot({'B':110},{'B':115});self.assertAlmostEqual(r['net_pnl'],110-3.3)
 def test_delay(self):
  a=CapitalAccount(withdrawal_fee=1,delay_opens=1);a.begin_day('2024-01-01',{'B':100});a.rebalance({'B':100},{'B':1100});a.snapshot({'B':100})
  a.begin_day('2024-01-02',{'B':200});before=a.total({'B':200});a.sweep({'B':200});self.assertEqual(a.external,3750);self.assertGreater(a.transit(),0);self.assertAlmostEqual(a.venue({'B':200}),1250)
  r=a.snapshot({'B':200});self.assertAlmostEqual(before-r['total_equity'],a.fees-3.3+1)
  tr=a.transit();a.begin_day('2024-01-03',{'B':200});self.assertEqual(a.transit(),0);self.assertAlmostEqual(a.external,3750+tr)
 def test_gap_not_erased(self):
  a=CapitalAccount();a.begin_day('2024-01-01',{'B':100});a.rebalance({'B':100},{'B':1100});a.snapshot({'B':100});a.begin_day('2024-01-02',{'B':300});a.sweep({'B':300});r=a.snapshot({'B':300},{'B':310});self.assertTrue(r['open_breach']);self.assertFalse(r['close_breach'])
 def test_cash_deficit(self):
  a=CapitalAccount();a.begin_day('2024-01-01',{'B':100});scale=a.rebalance({'B':100},{'B':5000});self.assertLess(scale,1);self.assertAlmostEqual(a.cash,0);self.assertEqual(a.external,3750);a.snapshot({'B':100})
 def test_multiasset(self):
  a=CapitalAccount();p={'B':100,'E':10};a.begin_day('2024-01-01',p);a.rebalance(p,{'B':500,'E':500});a.snapshot(p)
  p={'B':200,'E':20};a.begin_day('2024-01-02',p);a.sweep(p);self.assertAlmostEqual(a.qty['E']/a.qty['B'],10);a.snapshot(p,p)
 def test_terminal(self):
  a=CapitalAccount();a.begin_day('2024-01-01',{'B':100});a.rebalance({'B':100},{'B':1100});r=a.snapshot({'B':110});t=a.liquidate_after_snapshot({'B':110});self.assertAlmostEqual(t['terminal_equity'],r['net_liquidation_equity']);self.assertAlmostEqual(t['terminal_sale_fee'],3.63)
 def test_skip_fee_larger_transfer(self):
  a=CapitalAccount(withdrawal_fee=1,venue_cash=1250.5,external_cash=3749.5);a.begin_day('2024-01-01',{});self.assertEqual(a.sweep({}),0);a.snapshot({})
 def test_high_bound(self):
  a=CapitalAccount();a.begin_day('2024-01-01',{'B':100});a.rebalance({'B':100},{'B':1100});r=a.snapshot({'B':100},{'B':300});self.assertTrue(r['high_upper_exceeds']);self.assertFalse(r['close_breach'])
if __name__=='__main__':unittest.main()
