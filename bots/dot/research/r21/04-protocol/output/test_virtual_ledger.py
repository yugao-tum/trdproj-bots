import unittest
from copy import deepcopy
from decimal import Decimal as D
import virtual_ledger as v

def book(t=1700000001000, bid='99', ask='100', size='100'):
    return {'symbol':'ETHUSDT','request_start_ms':t,'response_end_ms':t+100,
            'exchange_time_ms':None,'bids':[[bid,size]],'asks':[[ask,size]]}
def filt(step='0.001'):
    return {'symbol':'ETHUSDT','qty_step':step,'min_qty':'0.001','max_qty':'10000','min_notional':'5'}
def lock():
    return {'authorized_by':'root','entry_authorized':True,'locked_at_ms':1700000000900,'protocol_sha256':v.canonical_hash(v.CONFIG),'synthetic_test_only':True}
def state():
    return v.initialize_virtual(book(),book(1700000001200),filt('.0001'),filt(),lock(),1700000001400)
def payment(ts=1700000002000,rate='.001',mark='100'):
    return {'symbol':'ETHUSDT','fundingTime':ts,'fundingRate':rate,'markPrice':mark}
class Tests(unittest.TestCase):
    def test_common_grid(self):
        self.assertEqual(v.common_step('.0001','.001'),D('.001'))
        self.assertEqual(v.common_step('.002','.003'),D('.006'))
        self.assertEqual(v.floor_grid('1.2349','.001'),D('1.234'))
    def test_lock_required(self):
        for l in ({},dict(lock(),protocol_sha256='bad'),dict(lock(),entry_authorized=False)):
            with self.assertRaises(ValueError):v.initialize_virtual(book(),book(),filt(),filt(),l,1700000001400)
    def test_prelock_rejected(self):
        with self.assertRaises(ValueError):v.initialize_virtual(book(1700000000800),book(),filt(),filt(),lock(),1700000001400)
    def test_crossed_book(self):
        with self.assertRaises(ValueError):v.validate_pair(book(bid='101'),book(),1700000001400)
    def test_unsorted_and_duplicate(self):
        for asks in ([['101','1'],['100','1']],[['100','1'],['100','2']]):
            b=book();b['asks']=asks
            with self.assertRaises(ValueError):v.validate_pair(b,book(),1700000001400)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):v.dec('NaN')
        with self.assertRaises(ValueError):v.notional(book(size='0'),'asks','1')
    def test_stale_and_skew(self):
        with self.assertRaises(ValueError):v.validate_pair(book(),book(),1700000007000)
        with self.assertRaises(ValueError):v.validate_pair(book(1700000001000),book(1700000006000),1700000006100)
    def test_event_timestamp(self):
        b=book();b['exchange_time_ms']=-5000
        with self.assertRaises(ValueError):v.validate_pair(b,book(),1700000001400)
        self.assertTrue(v.validate_pair(book(),book(),1700000001400))
    def test_quantity_budget(self):
        s=state();q=D(s['entry']['quantity'])
        self.assertEqual(q,D('12.462'))
        self.assertLessEqual(D(s['accounts']['.003' if '.003' in s['accounts'] else '0.003']['spot_entry_cost']),D(1250))
        self.assertGreater((q+D('.001'))*100*D('1.003'),D(1250))
    def test_depth_sweep(self):
        b=book();b['asks']=[['100','1'],['102','100']]
        q,sn,pn,step=v.choose_quantity(b,book(),filt(),filt())
        self.assertEqual(sn,100+(q-1)*102)
        self.assertLessEqual(sn*D('1.003'),1250)
        self.assertGreater(v.notional(b,'asks',q+step)*D('1.003'),1250)
    def test_no_shallow_rescue(self):
        with self.assertRaises(ValueError):v.choose_quantity(book(size='1'),book(),filt(),filt())
        with self.assertRaises(ValueError):v.choose_quantity(book(),book(size='1'),filt(),filt())
    def test_minimum_filter(self):
        f=filt();f['min_notional']='2000'
        with self.assertRaises(ValueError):v.choose_quantity(book(),book(),f,filt())
    def test_entry_conservation_and_same_quantity(self):
        s=state();q=D(s['entry']['quantity']);pn=D(s['entry']['perp_notional'])
        for c,a in s['accounts'].items():
            self.assertEqual(D(a['spot_entry_cost'])+D(a['perp_entry_fee'])+D(a['initial_collateral']),2500)
            self.assertEqual(D(a['perp_entry_fee']),pn*D(c))
        self.assertEqual(q,D('12.462'));self.assertFalse(s['position_is_real'])
    def test_funding_strict_entry(self):
        s=state();t=s['entry']['entry_time_ms'];out,r=v.apply_funding(s,[payment(t),payment(t+1)],t+1)
        self.assertEqual(r['accepted'],1);self.assertEqual(r['excluded_at_or_before_entry'],1)
        self.assertEqual(D(out['accounts']['0.003']['funding_cash']),D(s['entry']['quantity'])*D('.1'))
    def test_funding_idempotence_and_millisecond_preservation(self):
        a,r=v.apply_funding(state(),[payment(1700000002001),payment(1700000002002)],1700000003000)
        b,r=v.apply_funding(a,[payment(1700000002001),payment(1700000002002)],1700000003000)
        self.assertEqual(a,b);self.assertEqual(r['duplicates'],2)
        self.assertIn('ETHUSDT:1700000002001',b['funding_events'])
    def test_funding_atomic_conflict(self):
        s,r=v.apply_funding(state(),[payment(1700000002000)],1700000003000);old=deepcopy(s)
        with self.assertRaises(ValueError):v.apply_funding(s,[payment(1700000002100),payment(1700000002000,rate='.002')],1700000003000)
        self.assertEqual(s,old)
    def test_future_funding_rejected(self):
        with self.assertRaises(ValueError):v.apply_funding(state(),[payment(1700000003001)],1700000003000)
    def test_negative_funding(self):
        s,r=v.apply_funding(state(),[payment(rate='-.001')],1700000003000)
        self.assertLess(D(s['accounts']['0.003']['funding_cash']),0)
    def test_missing_exit_quotes_null(self):
        x=v.valuation(state(),'100','100')
        self.assertIsNone(x['accounts']['0.003']['hypothetical_exit_equity'])
    def test_close_conservation(self):
        s=state();x=v.valuation(s,'100','100',book(1700000001400),book(1700000001500),1700000001700)
        q=D(s['entry']['quantity']);sn=D(s['entry']['spot_notional']);pn=D(s['entry']['perp_notional'])
        for c,a in s['accounts'].items():
            cost=D(c);manual=D(5000)+q*99-sn+pn-q*100-cost*(sn+pn+q*99+q*100)
            self.assertEqual(D(x['accounts'][c]['hypothetical_exit_equity']),manual)
    def test_stale_exit_null_not_retrofill(self):
        x=v.valuation(state(),'100','100',book(),book(),1700000010000)
        self.assertIsNone(x['accounts']['0.003']['hypothetical_exit_equity'])
    def test_no_short_window_annualization(self):
        x=v.valuation(state(),'100','100',book(1700000001400),book(1700000001500),1700000001700)['accounts']['0.003']
        self.assertIsNone(x['forecast_break_even_days']); self.assertIsNone(x['short_window_annualized_return'])
        self.assertEqual(D(x['remaining_funding_shortfall_at_current_quotes']),D(5000)-D(x['hypothetical_exit_equity']))
    def test_distinct_price_cost_funding_identity(self):
        s,_=v.apply_funding(state(),[payment()],1700000003000)
        x=v.valuation(s,'100','100',book(1700000003000),book(1700000003100),1700000003300)['accounts']['0.003']
        net=D(x['actual_recorded_funding_conditional_cash'])+D(x['nonfunding_price_pnl'])-D(x['full_assumed_entry_exit_cost'])
        self.assertEqual(net,D(x['hypothetical_exit_equity'])-D(5000))
    def test_cost_recovery_and_quote_time_are_distinct(self):
        s,_=v.apply_funding(state(),[payment()],1700000003000)
        x=v.valuation(s,'100','100',book(1700000003000),book(1700000003100),1700000003300)['accounts']['0.003']
        self.assertEqual(x['quote_valuation_time_ms'],1700000003200)
        self.assertEqual(D(x['funding_only_cost_recovery_gap']),max(D(0),D(x['full_assumed_entry_exit_cost'])-D(x['actual_recorded_funding_conditional_cash'])))
        self.assertNotEqual(x['funding_only_cost_recovery_gap'],x['remaining_funding_shortfall_at_current_quotes'])
    def test_timestamp_units_types(self):
        for bad in (1700000000, 1700000000000.0, "1700000000000", True, -1):
            with self.assertRaises(ValueError): v.epoch_ms(bad)
            b=book(); b['request_start_ms']=bad
            with self.assertRaises(ValueError): v.validate_pair(b,book(),1700000001400)
            l=lock(); l['locked_at_ms']=bad
            with self.assertRaises(ValueError): v.initialize_virtual(book(),book(),filt(),filt(),l,1700000001400)
            with self.assertRaises(ValueError): v.apply_funding(state(),[payment(bad)],1700000003000)
    def test_unknown_side_rejected(self):
        b=book(); b['other']=[['100','100']]
        with self.assertRaises(ValueError): v.notional(b,'other','1')
    def test_no_network_surface(self):
        import inspect
        code=inspect.getsource(v)
        for module in ('import requests','import urllib','import socket','import subprocess'):
            self.assertNotIn(module,code)
if __name__=='__main__':unittest.main()
