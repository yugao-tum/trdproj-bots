import unittest
from decimal import Decimal as D
from collateral import equity,prefix_bounds,high_time_bounds,venue_bounds

class Tests(unittest.TestCase):
 def test_short_loss(self): self.assertEqual(equity(100,1,100,150),D(50))
 def test_short_gain(self): self.assertEqual(equity(100,1,100,50),D(150))
 def test_funding(self): self.assertEqual(equity(100,1,100,150,-20),D(30))
 def test_prefix_chronological(self): self.assertEqual(prefix_bounds(2,[10,-20,7]),(D(-8),D(12),D(-1)))
 def test_prefix_empty(self): self.assertEqual(prefix_bounds(2,[]),(D(2),)*3)
 def test_negative_guaranteed(self): self.assertEqual(high_time_bounds(10,1,100,125,0,10)[2],'guaranteed_negative_at_recorded_high')
 def test_negative_ambiguous(self): self.assertEqual(high_time_bounds(10,1,100,115,0,10)[2],'ambiguous_negative_possible')
 def test_nonnegative_no_proof(self): self.assertEqual(high_time_bounds(10,1,100,105,0,10)[2],'nonnegative_lower_bound_not_liquidation_proof')
 def test_zero_not_negative(self): self.assertEqual(high_time_bounds(10,1,100,110,0,0)[0],D(0))
 def test_notional_distinct(self):
  self.assertGreater(equity(100,1,100,150),0)
  self.assertLess(high_time_bounds(100,1,100,150,0,0,True)[1],0)
 def test_venue_envelope(self): self.assertEqual(venue_bounds(100,1,100,90,110,80,120,-5,10),(D(165),D(240)))
 def test_decimal(self): self.assertEqual(equity('0.1','0.1','0.3','0.2','0.01'),D('0.12'))
if __name__=='__main__':unittest.main()
