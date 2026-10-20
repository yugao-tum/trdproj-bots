import unittest
from copy import deepcopy
from quote_audit import *
T=1792497600000

def book(): return {'symbol':'ETHUSDT','request_start_ms':T,'response_end_ms':T+500,'exchange_time_ms':None,'bids':[['1999','1'],['1998','2']],'asks':[['2000','1'],['2002','2']]}
F={'stepSize':'0.001','minQty':'0.001','maxQty':'100','minNotional':'20'}
class Tests(unittest.TestCase):
    def test_lcm_decimal_grid(self): self.assertEqual(common_step('.002','.003'),D('.006'))
    def test_unequal_precision(self): self.assertEqual(common_step('.0001','.001'),D('.001'))
    def test_floor_never_roundup(self): self.assertEqual(floor_quantity('.546999','.001'),D('.546'))
    def test_invalid_step(self):
        with self.assertRaises(QuoteError): common_step('0','.001')
    def test_ask_vwap(self): self.assertEqual(vwap(book(),'asks','2')['notional'],D('4002'))
    def test_bid_orientation(self): self.assertEqual(vwap(book(),'bids','2')['notional'],D('3997'))
    def test_partial_depth_reject(self):
        with self.assertRaises(QuoteError): vwap(book(),'asks','4')
    def test_crossed_book(self):
        b=book();b['bids'][0][0]='2000'
        with self.assertRaises(QuoteError): validate_book(b)
    def test_unsorted_book(self):
        b=book();b['asks'].reverse()
        with self.assertRaises(QuoteError): validate_book(b)
    def test_duplicate_level(self):
        b=book();b['asks'][1][0]='2000'
        with self.assertRaises(QuoteError): validate_book(b)
    def test_nonfinite_price(self):
        b=book();b['asks'][0][0]='NaN'
        with self.assertRaises(QuoteError): validate_book(b)
    def test_budget_cost_floor(self): self.assertEqual(budget_quantity(book(),'1250','.003','.001'),D('.623'))
    def test_no_capacity_resize(self):
        b=book();b['asks']=[['2000','.2']]
        with self.assertRaises(QuoteError): budget_quantity(b,'1250','.003','.001')
    def test_pair_fresh_event_unknown(self):
        r=check_pair(book(),book(),T+1000,T);self.assertFalse(r['event_freshness_fully_observable']);self.assertFalse(r['own_fill_proven'])
    def test_exact_five_seconds(self):
        b=book();b['response_end_ms']=T+5000
        self.assertEqual(check_pair(book(),b,T+5000,T)['interval_envelope_ms'],5000)
    def test_skew_too_large(self):
        b=book();b['request_start_ms']=T+5001;b['response_end_ms']=T+5100
        with self.assertRaises(QuoteError): check_pair(book(),b,T+5100,T)
    def test_stale_response(self):
        with self.assertRaises(QuoteError): check_pair(book(),book(),T+6000,T)
    def test_stale_exchange_time(self):
        b=book();b['exchange_time_ms']=T-5001
        with self.assertRaises(QuoteError): check_pair(book(),b,T+1000,T)
    def test_seconds_mistake(self):
        b=book();b['request_start_ms']=T//1000
        with self.assertRaises(QuoteError): check_pair(book(),b,T+1000,T)
    def test_pre_lock_reject(self):
        with self.assertRaises(QuoteError): check_pair(book(),book(),T+1000,T+1)
    def test_future_response(self):
        with self.assertRaises(QuoteError): check_pair(book(),book(),T,T)
    def test_min_notional(self):
        with self.assertRaises(QuoteError): validate_leg_filters('.001','2',F)
    def test_off_grid(self):
        with self.assertRaises(QuoteError): validate_leg_filters('.0105','21',F)
    def test_valid_filter(self): self.assertTrue(validate_leg_filters('.02','40',F))
    def test_missing_filter(self):
        f=F.copy();del f['minNotional']
        with self.assertRaises(QuoteError): validate_leg_filters('.02','40',f)
if __name__=='__main__':unittest.main()
