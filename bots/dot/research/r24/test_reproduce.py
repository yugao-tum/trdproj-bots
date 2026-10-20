import unittest,os,tempfile,shutil,json,subprocess
from pathlib import Path
from fractions import Fraction as F
from reproduce import cap,endpoint
class IndependentChecks(unittest.TestCase):
 def test_cap_and_retain(self):
  for b in [625,1250]:
   q0=F(b,100);q,g=cap(q0,F(100),F(100),F(100),F(0));self.assertLessEqual(q,q0);self.assertGreaterEqual(g,0)
 def test_quantity_quantum(self):
  q,g=cap(F(1250,100),F(100),F(100),F(100),F(3,1000));self.assertEqual((q*10**24).denominator,1)
 def test_cash_identity_four_fees(self):
  e=endpoint(F(2),F(1,100),F(100),F(101),{'spot_close':'110','perp_close':'111'},F(5));self.assertEqual(e['fees'],F(844,100));self.assertEqual(e['pnl'],F(5)-F(844,100));self.assertEqual(e['return2500'],2*e['return5000'])
 def test_endpoint_not_reopen(self):
  a=endpoint(F(2),F(1,100),F(100),F(101),{'spot_close':'110','perp_close':'111'},F(5));b=endpoint(F(2),F(1,100),F(100),F(101),{'spot_close':'120','perp_close':'121'},F(7));self.assertEqual(b['pnl']-a['pnl'],F(8,5))
 @unittest.skipUnless(os.environ.get('R24_SOURCE_ROOT'), 'Set R24_SOURCE_ROOT for four-CSV clean-fixture portability replay')
 def test_four_csv_portability(self):
  here=Path(__file__).resolve().parent;source=Path(os.environ['R24_SOURCE_ROOT'])
  contract=json.loads((here/'inputs-parameters-hashes.json').read_text())
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);bundle=base/'bundle';bundle.mkdir();root=base/'sources';root.mkdir()
   for name in ['reproduce.py','inputs-parameters-hashes.json','compact-results.json']:
    shutil.copy2(here/name,bundle/name)
   for relative in list(contract['sha256'])[:4]:
    target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/relative,target)
   self.assertEqual(len([p for p in root.rglob('*') if p.is_file()]),4)
   for check in [False,True]:
    output=base/('checked' if check else 'independent')
    cmd=['python',str(bundle/'reproduce.py'),'--workers',str(root),'--output',str(output)]
    if check:cmd+=['--crosscheck',str(bundle/'compact-results.json')]
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    self.assertEqual(json.loads((output/'compact-results.json').read_text())['cases'],json.loads((bundle/'compact-results.json').read_text())['cases'])
if __name__=='__main__':unittest.main()
