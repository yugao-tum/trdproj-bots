import unittest
from criteria import summarize


def ev(i, cash='1'):
    return {'event_key': f'ETHUSDT:{i}', 'funding_time_ms': i, 'cash_usdt': cash}

class Tests(unittest.TestCase):
    def test_no_data_not_zero_accuracy(self):
        r=summarize([],entry_ms=0)
        self.assertFalse(r['initial_window_complete']); self.assertIsNone(r['negative_funding_share'])
    def test_entry_boundary(self):
        r=summarize([ev(0),ev(1)],entry_ms=0)
        self.assertEqual(r['unique_post_entry_events'],1)
    def test_duplicate_once(self):
        r=summarize([ev(1),ev(1)],entry_ms=0)
        self.assertEqual(r['actual_observed_funding_conditional_cash_usdt'],'1')
    def test_conflict_blocks_verdict(self):
        r=summarize([ev(i) for i in range(1,31)]+[ev(1,'2')],entry_ms=0,no_gaps_confirmed=True)
        self.assertFalse(r['initial_window_complete'])
    def test_thirty_not_gap_proof(self):
        r=summarize([ev(i) for i in range(1,31)],entry_ms=0)
        self.assertFalse(r['initial_window_complete'])
    def test_thirty_review_not_stop(self):
        r=summarize([ev(i) for i in range(1,31)],entry_ms=0,no_gaps_confirmed=True)
        self.assertTrue(r['initial_window_complete']);self.assertFalse(r['initial_window_forces_stop'])
        self.assertFalse(r['qualified']);self.assertIsNone(r['annualized_return'])
    def test_negative_payments_retained(self):
        r=summarize([ev(1,'-2'),ev(2,'1')],entry_ms=0)
        self.assertEqual(r['actual_observed_funding_conditional_cash_usdt'],'-1')
        self.assertEqual(r['negative_funding_share'],'0.5')
    def test_cost_gap_no_amortization(self):
        r=summarize([ev(1,'3')],entry_ms=0,entry_cost='7.5',exit_cost='8')
        self.assertEqual(r['funding_only_cost_recovery_gap_usdt'],'12.5')
        self.assertIsNone(r['break_even_days'])
    def test_missing_exit_cost_null(self):
        r=summarize([ev(1)],entry_ms=0,entry_cost='7.5')
        self.assertIsNone(r['funding_only_cost_recovery_gap_usdt'])
    def test_missing_quotes_no_executable_pnl(self):
        r=summarize([ev(1)],entry_ms=0)
        self.assertIsNone(r['quoted_exit_net_pnl_usdt'])
    def test_denominators(self):
        r=summarize([],entry_ms=0,executable_net_pnl='-10',valuation_time_ms=1)
        self.assertEqual(r['nonannualized_return_total5000'],'-0.002')
        self.assertEqual(r['nonannualized_return_venue2500'],'-0.004')
    def test_zero_margin_invalid(self):
        r=summarize([],entry_ms=0,observed_margin_equity='0')
        self.assertTrue(r['later_values_require_counterfactual_label'])
    def test_positive_margin_not_qualification(self):
        r=summarize([],entry_ms=0,observed_margin_equity='100')
        self.assertFalse(r['feasible_path_invalidated_by_nonpositive_margin']);self.assertFalse(r['qualified'])
    def test_first_window_fixed(self):
        r=summarize([ev(i,'-1' if i<=30 else '999') for i in range(1,32)],entry_ms=0,no_gaps_confirmed=True)
        self.assertEqual(r['actual_observed_funding_conditional_cash_usdt'],'-30')
    def test_errors_block_complete(self):
        r=summarize([ev(i) for i in range(1,31)],entry_ms=0,no_gaps_confirmed=True,data_errors=['missing_record'])
        self.assertFalse(r['initial_window_complete'])
    def test_aliased_event_rejected(self):
        a=ev(1);a['event_key']='fake_alias'
        with self.assertRaises(ValueError): summarize([a],entry_ms=0)
    def test_undated_net_rejected(self):
        with self.assertRaises(ValueError): summarize([],entry_ms=0,executable_net_pnl='1')
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError): summarize([ev(1,'NaN')],entry_ms=0)

if __name__=='__main__': unittest.main()
