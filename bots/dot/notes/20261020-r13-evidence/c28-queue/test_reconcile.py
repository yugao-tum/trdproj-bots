"""Synthetic unit tests only, not historical observations."""
import unittest
from reconcile import claimable, gas_wei, reconcile, E27
class Tests(unittest.TestCase):
 def test_cap(self): self.assertEqual(claimable(100,80,2*E27),100)
 def test_haircut(self): self.assertEqual(claimable(100,80,E27),80)
 def test_rounding(self): self.assertEqual(claimable(101,80,E27),80)
 def test_integer_rate_branch(self): self.assertEqual(claimable(1,3*E27,1),1)
 def test_gas(self): self.assertEqual(gas_wei({'gasUsed':21000,'effectiveGasPrice':10**9}),21000*10**9)
 def test_unknown_gas(self): self.assertIsNone(gas_wei(None))
 def test_missing(self): self.assertIsNone(reconcile({})['elapsed_seconds'])
 def test_range_and_unknown_profit(self):
  x={'request_id':1,'request':{'timestamp':1,'amount_steth_wei':100,'shares':100},'finalization':{'from':1,'to':2,'timestamp':2,'max_share_rate':E27},'claim':{'timestamp':3,'amount_eth_wei':100},'historical_implementation':'synthetic-only'}
  self.assertIsNone(reconcile(x)['profit_wei']);self.assertEqual(reconcile(x)['elapsed_seconds'],2)
  x['request_id']=0
  with self.assertRaises(AssertionError):reconcile(x)
if __name__=='__main__':unittest.main()
