"""Synthetic unit fixtures only; actual-input assertions are separately labelled."""
import copy,json,unittest
from pathlib import Path
from decimal import Decimal as D
from reconcile_native import dedup,summarize,START,END,TOL

def fixture(**kw):
    r=dict(coin='@107',tid=1,time=START,side='B',dir='Buy',sz='1',px='2.5',startPosition='10',fee='0',feeToken='HYPE',hash='0x'+'0'*64);r.update(kw);return r
class Synthetic(unittest.TestCase):
    def test_exact_duplicate(self): self.assertEqual(dedup([[fixture()],[fixture()]])[1],1)
    def test_conflicting_identity(self):
        with self.assertRaises(ValueError):dedup([[fixture(),fixture(sz='2')]])
    def test_tie_order(self):
        rows,_=dedup([[fixture(tid=2,startPosition='11'),fixture()]]);self.assertEqual(rows[0]['tid'],1);self.assertEqual(summarize(rows)['max_abs_edge_residual_HYPE'],'0')
    def test_halfopen_start_included(self):self.assertEqual(summarize([fixture()])['raw_quantity_HYPE'],'1')
    def test_halfopen_end_excluded(self):
        with self.assertRaises(ValueError):summarize([fixture(time=END)])
    def test_before_start(self):
        with self.assertRaises(ValueError):summarize([fixture(time=START-1)])
    def test_quote_fee_cash(self):self.assertEqual(summarize([fixture(feeToken='USDC',fee='0.1')])['cash_debit_USDC'],'2.6')
    def test_base_fee_units(self):
        s=summarize([fixture(fee='0.1')]);self.assertEqual(s['net_acquired_HYPE'],'0.9');self.assertEqual(s['cash_debit_USDC'],'2.5')
    def test_other_fee_rejected(self):
        with self.assertRaises(ValueError):summarize([fixture(feeToken='OTHER')])
    def test_sell_rejected(self):
        with self.assertRaises(ValueError):summarize([fixture(side='A')])
    def test_gap_visible(self):self.assertEqual(summarize([fixture(),fixture(tid=2,time=START+1,startPosition='12')])['edges_exceeding_one_base_unit'],1)
    def test_decimal_exact_not_float(self):self.assertEqual(summarize([fixture(sz='0.1',px='0.2')])['execution_notional_USDC'],'0.02')
class ActualRetainedInput(unittest.TestCase):
    def test_actual_reconciliation(self):
        raw=Path(__file__).resolve().parents[1]/'raw';rows,n=dedup([json.loads((raw/f'fills_part_{i:02}.json').read_text()) for i in range(1,5)])
        s=summarize(rows);self.assertEqual((len(rows),n),(6653,6));self.assertEqual(D(s['execution_notional_USDC']),D('12644608.32880'));self.assertEqual(D(s['raw_quantity_HYPE']),D('156264.38'));self.assertEqual(s['edges_exceeding_one_base_unit'],0);self.assertEqual(D(s['inventory_bridge_residual_HYPE']),D('0.0000000006'))
if __name__=='__main__':unittest.main(verbosity=2)
