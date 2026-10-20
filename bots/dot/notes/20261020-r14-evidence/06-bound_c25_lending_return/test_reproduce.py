import json, unittest, hashlib
from decimal import Decimal as D
from reproduce import calculate, ROOT

class BoundTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((ROOT/'fixed-inputs.json').read_text()); self.r=calculate(self.c)
    def test_exact_365_days(self): self.assertEqual(self.c['seconds'],31536000)
    def test_frozen_gross(self): self.assertLess(abs(D(self.r['gross_index_pct'])-D('3.57379060760452075967270127578666047')),D('1e-33'))
    def test_leg_fails(self): self.assertLess(D(self.r['net_leg_pct_at_zero_gas']),D(3))
    def test_total_fails_even_without_cost(self): self.assertLess(D(self.r['zero_cost_total_capital_pct']),D(3))
    def test_factor_two_denominator(self): self.assertEqual(D(self.r['net_total_pct_loose_cap'])*2,D(self.r['net_leg_pct_at_zero_gas']))
    def test_full_allocation_violates_end_cap(self): self.assertFalse(self.r['gas_sensitivity'][0]['terminal_cap_pass'])
    def test_end_cap(self): self.assertLess(abs(D(self.r['endpoint_cap_case']['terminal_venue_units'])-D(2500)),D('1e-60'))
    def test_gas_monotone(self):
        vals=[D(x['conditional_net_interest_cash']) for x in self.r['gas_sensitivity']];self.assertEqual(vals,sorted(vals,reverse=True))
    def test_zero_interest_loses(self):
        self.c['end_index']=self.c['start_index'];self.assertEqual(D(calculate(self.c)['net_leg_pct_at_zero_gas']),D('-0.5991'))
    def test_zero_cost_matches(self):
        self.c['entry_cost_fraction']=self.c['exit_cost_fraction']='0';r=calculate(self.c);self.assertEqual(r['net_leg_pct_at_zero_gas'],r['gross_index_pct'])
    def test_cash_identity(self):
        for row in self.r['gas_sensitivity']:
            expected=D(row['terminal_venue_units'])-D(row['exit_cost'])-D(row['initial_cash_budget'])-D(row['gas_assumption'])
            self.assertLess(abs(expected-D(row['conditional_net_interest_cash'])),D('1e-60'))
    def test_inputs_unchanged(self):
        for f in json.loads((ROOT/'source-manifest.json').read_text())['files']:
            self.assertEqual(hashlib.sha256(__import__('pathlib').Path(f['path']).read_bytes()).hexdigest(),f['sha256'])
if __name__=='__main__': unittest.main()
