"""Synthetic unit fixtures only; actual evidence tested separately."""
import unittest,json,pathlib
from reconstruct import normalize,nxm,unique_rows

def fixture(kind,**p):
 return {'block_number':1,'index':2,'transaction_hash':'0xabc','address':{'hash':'0xdef'},'decoded':{'method_call':kind+'()','parameters':[{'name':k,'value':str(v)} for k,v in p.items()]}}
class SignedTests(unittest.TestCase):
 def test_deposit(self):
  r=normalize(fixture('StakeDeposited',amount=123));self.assertEqual((r['pool_principal_delta_base'],r['holder_principal_cash_base']),('123','-123'))
 def test_burn_not_cash(self):
  r=normalize(fixture('StakeBurned',amount=55));self.assertEqual(r['pool_principal_delta_base'],'-55');self.assertIsNone(r['holder_principal_cash_base'])
 def test_reward_only(self):
  r=normalize(fixture('Withdraw',tokenId=3,amountStakeWithdrawn=0,amountRewardsWithdrawn=17));self.assertEqual(r['holder_reward_cash_base'],'17')
 def test_manager_separate(self):
  r=normalize(fixture('Withdraw',tokenId=0,amountStakeWithdrawn=0,amountRewardsWithdrawn=17));self.assertEqual(r['manager_reward_cash_base'],'17');self.assertIsNone(r['holder_reward_cash_base'])
 def test_withdraw_sign(self):
  r=normalize(fixture('Withdraw',tokenId=3,amountStakeWithdrawn=5,amountRewardsWithdrawn=2));self.assertEqual(r['pool_principal_delta_base'],'-5');self.assertEqual(r['holder_principal_cash_base'],'5')
 def test_extension_topup_only(self):
  r=normalize(fixture('DepositExtended',topUpAmount=7));self.assertEqual(r['holder_principal_cash_base'],'-7')
 def test_precision(self): self.assertEqual(nxm(10467512119445769616653),'10467.512119445769616653')
 def test_negative_precision(self): self.assertEqual(nxm(-1),'-0.000000000000000001')
 def test_duplicate(self):
  x=fixture('StakeBurned',amount=1);self.assertEqual(len(unique_rows([x,x])),1)
 def test_conflict(self):
  with self.assertRaises(ValueError):unique_rows([fixture('StakeBurned',amount=1),fixture('StakeBurned',amount=2)])
 def test_actual_burn(self):
  rows=unique_rows(json.loads((pathlib.Path(__file__).parent/'raw/pool1-logs-p1.json').read_text())['items']); burns=[r for r in rows if r['event']=='StakeBurned'];self.assertEqual(len(rows),50);self.assertEqual(len(burns),1);self.assertEqual(burns[0]['pool_principal_delta_base'],'-10467512119445769616653')
 def test_actual_no_withdraw(self):
  rows=unique_rows(json.loads((pathlib.Path(__file__).parent/'raw/pool1-logs-p1.json').read_text())['items']);self.assertFalse(any(r['event']=='Withdraw' for r in rows))
if __name__=='__main__':unittest.main(verbosity=2)
