import unittest,json,csv
from pathlib import Path
from fractions import Fraction as F
from verify_sma import returns,monthly,correlation
P=Path(__file__).resolve().parent
class Supplement(unittest.TestCase):
 def test_return_denominator(self):
  self.assertEqual(returns([F(5100),F(5200)]),[F(1,50),F(1,51)])
  self.assertEqual(returns([F(2600)],2500),[F(1,25)])
 def test_month_compounding(self):
  self.assertEqual(monthly(['2026-09-29','2026-09-30','2026-10-01'],[F(1,10),F(-1,10),F(1,5)]),{'2026-09':F(-1,100),'2026-10':F(1,5)})
 def test_counts_labels_and_endpoint_views(self):
  rows=list(csv.DictReader((P/'correlation-summary.csv').open()));self.assertEqual(len(rows),288);self.assertEqual(len({r['scenario_id'] for r in rows}),36);self.assertEqual(sum('counterfactual' in r['classification'] for r in rows),64)
  for r in rows:self.assertEqual(int(r['n']),33 if r['frequency']=='monthly_complete33' else (1004 if r['view'].startswith('september') else 1023))
  partial=list(csv.DictReader((P/'october-partial.csv').open()));self.assertEqual(len(partial),72);self.assertTrue(all(r['days']=='19' for r in partial))
 def test_independent_comparison(self):
  j=json.loads((P/'comparison.json').read_text());self.assertEqual(j['mismatches'],[]);self.assertTrue(j['all_288_correlations_pass_1e10']);self.assertTrue(j['all_labels_and_observation_counts_match'])
 def test_same_gross_benchmark(self):
  rows=list(csv.DictReader((P/'benchmark-endpoints.csv').open()));self.assertEqual(len(rows),2);self.assertAlmostEqual(float(F(rows[0]['pnl5000'])),4340.44974769017,places=8);self.assertAlmostEqual(float(F(rows[1]['pnl5000'])),4152.219081768021,places=8)
if __name__=='__main__':unittest.main()
