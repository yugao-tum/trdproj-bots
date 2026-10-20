import unittest
from fractions import Fraction as F
from analyze import margin_bound, funding_prefix_bounds
class BoundsTests(unittest.TestCase):
 def args(self): return [F(100),F(2),F(10),F(20),F(-3),F('.004'),F('.003')]
 def test_equity(self): self.assertEqual(margin_bound(*self.args())['equity_lower'],F(77))
 def test_maintenance(self): self.assertEqual(margin_bound(*self.args())['maintenance'],F('.16'))
 def test_close_reserve(self): self.assertEqual(margin_bound(*self.args())['close_reserve'],F('.12'))
 def test_surplus(self): self.assertEqual(margin_bound(*self.args())['surplus_after_maintenance_and_close'],F('76.72'))
 def test_deduction_condition(self):
  a=margin_bound(*self.args()); b=margin_bound(*self.args(),deduction=F(5)); self.assertEqual(b['surplus_after_maintenance']-a['surplus_after_maintenance'],5)
 def test_negative_deduction_not_conservative(self):
  a=margin_bound(*self.args());b=margin_bound(*self.args(),deduction=F(-5));self.assertLess(b['surplus_after_maintenance'],a['surplus_after_maintenance'])
 def test_rate_comparison(self):
  a=self.args();b=a.copy();b[5]=F('.005');self.assertEqual(margin_bound(*a)['surplus_after_maintenance']-margin_bound(*b)['surplus_after_maintenance'],F('.04'))
 def test_ratio_identity(self):
  a=margin_bound(*self.args());self.assertEqual(a['ratio_headroom_after_maintenance_and_close'],a['surplus_after_maintenance_and_close']/a['notional'])
 def test_chronological_prefix(self): self.assertEqual(funding_prefix_bounds(F(10),[F(5),F(-20),F(8)]),(F(-5),F(15),F(3)))
 def test_empty_day(self): self.assertEqual(funding_prefix_bounds(F(10),[]),(F(10),F(10),F(10)))
 def test_negative_equity_kept(self):
  a=self.args();a[0]=F(0);self.assertLess(margin_bound(*a)['surplus_after_maintenance_and_close'],0)
 def test_bad_quantity(self):
  a=self.args();a[1]=F(0)
  with self.assertRaises(ValueError):margin_bound(*a)
 def test_high_monotonicity(self):
  a=self.args();b=a.copy();b[3]=F(25);self.assertLess(margin_bound(*b)['surplus_after_maintenance_and_close'],margin_bound(*a)['surplus_after_maintenance_and_close'])
 def test_exact_rational(self):
  a=self.args();a[1]=F(1,3);self.assertIsInstance(margin_bound(*a)['surplus_after_maintenance_and_close'],F)
if __name__=='__main__':unittest.main()
