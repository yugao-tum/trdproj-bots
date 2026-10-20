import unittest
from decimal import Decimal, localcontext
from formula import *

class FormulaTests(unittest.TestCase):
    def test_short_mark_gain(self): self.assertEqual(isolated_short_equity(100,2,50,40),D(120))
    def test_short_mark_loss(self): self.assertEqual(isolated_short_equity(100,2,50,60),D(80))
    def test_mm_deduction(self): self.assertEqual(maintenance_margin(10,26000,'.01',1300),D(1300))
    def test_unknown_not_zero(self):
        with self.assertRaises(ValueError): maintenance_margin(1,100,'.004',None)
    def test_unknown_liq_not_zero(self):
        with self.assertRaises(ValueError): short_equality_price(100,1,100,'.004',None)
    def test_equality_short(self):
        with localcontext() as c:
            c.prec=60
            p=short_equality_price(1250,'.5',2300,'.004',0)
            self.assertLess(abs(margin_buffer(1250,'.5',2300,p,'.004',0)),D('1e-50'))
    def test_equality_cost_reserve(self):
        with localcontext() as c:
            c.prec=60
            p=short_equality_price(1250,'.5',2300,'.004',0,'.003')
            self.assertLess(abs(margin_buffer(1250,'.5',2300,p,'.004',0,'.003')),D('1e-50'))
    def test_cost_lowers_short_threshold(self): self.assertLess(short_equality_price(100,1,100,'.004',0,'.003'),short_equality_price(100,1,100,'.004',0))
    def test_funding_credit_increases_threshold(self): self.assertGreater(short_equality_price(110,1,100,'.004',0),short_equality_price(100,1,100,'.004',0))
    def test_zero_deduction_is_conservative_if_actual_nonnegative(self): self.assertGreaterEqual(maintenance_margin(1,100,'.01',0),maintenance_margin(1,100,'.01','.3'))
    def test_tier_cap_inclusive(self): self.assertTrue(in_tier(1,300000,0,300000))
    def test_next_tier_needed(self): self.assertFalse(in_tier(1,300001,0,300000))
    def test_external_cash_not_added(self): self.assertEqual(isolated_short_equity(100,1,100,150),D(50))
    def test_invalid_quantity(self):
        with self.assertRaises(ValueError): short_equality_price(100,0,100,'.004',0)

if __name__=='__main__': unittest.main()
