import unittest,json
from pathlib import Path
from decimal import Decimal as D
from reproduce import prefixes,bounds
class IndependentTests(unittest.TestCase):
    def test_negative_prefix(self): self.assertEqual(prefixes(D(0),[D(-50),D(50)]),(D(-50),D(0),D(0)))
    def test_high_bounds(self):
        lo,hi=bounds(D(100),D(1),D(10),D(40),D(-5),D(3));self.assertEqual((lo,hi),(D(65),D(73)))
    def test_low_mark_ratio_exception(self):
        self.assertLess(D(-10)/D(2)-1,D(-10)/D(5)-1)
    def test_regression(self):
        xs=json.loads((Path(__file__).parent/'INDEPENDENT.json').read_text())['configs'];self.assertEqual(len(xs),12)
        for x in xs:
            high='b1250' in x['id'];self.assertEqual(D(x['entry_1x_unbuffered_gap'])<0,high)
            if x['id'].startswith('ETH'):
                self.assertIsNone(x['first_proven_zero_day']);self.assertIsNone(x['first_conditional_mmr_fail_day'])
                self.assertEqual(x['minute_day']['lower'],x['minute_day']['upper']);self.assertEqual(x['minute_day']['minute_start_ms'],1756062720000)
                self.assertLess(D(x['max_mark_notional']),50000)
            elif high:
                self.assertEqual(x['first_proven_zero_day'],'2024-11-13' if x['id'].startswith('BTC') else '2024-11-11')
                self.assertEqual(x['first_conditional_mmr_fail_day'],'2024-11-13' if x['id'].startswith('BTC') else '2024-03-18')
            else:self.assertIsNone(x['first_proven_zero_day']);self.assertIsNone(x['first_conditional_mmr_fail_day'])
        x=next(x for x in xs if x['id']=='ETHUSDT-b1250-c0.003')
        self.assertLess(abs(D(x['minute_day']['lower'])-D('76.94860895189675526135')),D('1e-18'))
        self.assertLess(abs(D(x['worst_daily_bound']['lower'])-D('76.16588088988504')),D('1e-12'))
if __name__=='__main__':unittest.main(verbosity=2)
