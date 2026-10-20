import unittest
from fractions import Fraction as F
from reproduce import endpoint,payments,cash

class ReferenceTests(unittest.TestCase):
    def test_zero_change_zero_fee(self):
        q,p,fee=endpoint(F(1250),F(0),F(10),F(10),F(10),F(10),F(0));self.assertEqual((q,p,fee),(125,0,0))
    def test_flat_four_costs(self):
        q,p,fee=endpoint(F(1250),F('0.003'),F(10),F(10),F(10),F(10),F(0));self.assertEqual(p,-fee);self.assertEqual(fee,q*F('.003')*40)
    def test_spot_budget_inclusive(self):
        q,_,_=endpoint(F(625),F('.006'),F(7),F(8),F(9),F(10),F(0));self.assertEqual(q*7*(1+F('.006')),625)
    def test_equal_hedge_cancels_price_rise(self):
        _,p,_=endpoint(F(100),F(0),F(10),F(10),F(40),F(40),F(0));self.assertEqual(p,0)
    def test_basis_difference_not_canceled(self):
        q,p,_=endpoint(F(100),F(0),F(10),F(11),F(40),F(42),F(0));self.assertEqual(p,-q)
    def test_funding_sign(self):
        r={'fundingRate':'-0.0001','markPrice':'100'};self.assertEqual(cash(F(2),r),F('-.02'))
    def test_funding_rate_not_percent(self):
        r={'fundingRate':'0.01','markPrice':'100'};self.assertEqual(cash(F(2),r),2)
    def test_cash_scaling(self):
        a=endpoint(F(625),F('.003'),F(10),F(11),F(12),F(13),F(2));b=endpoint(F(1250),F('.003'),F(10),F(11),F(12),F(13),F(2));self.assertEqual(b,tuple(2*x for x in a))
    def test_entry_excluded(self):
        self.assertEqual(payments([{'fundingTime':'1000'}],1000,2000),[])
    def test_one_millisecond_after_entry_included(self):
        self.assertEqual(len(payments([{'fundingTime':'1001'}],1000,2000)),1)
    def test_exit_included(self):
        self.assertEqual(len(payments([{'fundingTime':'2000'}],1000,2000)),1)
    def test_after_exit_excluded(self):
        self.assertEqual(payments([{'fundingTime':'2001'}],1000,2000),[])
    def test_jitter_preserved(self):
        rows=[{'fundingTime':'1026'},{'fundingTime':'1001'}];self.assertEqual([x['fundingTime'] for x in payments(rows,1000,2000)],['1001','1026'])
    def test_endpoint_cash_conservation(self):
        b,c,s,p,s1,p1,u=map(F,['1250','.003','10','11','20','19','3'])
        q,pnl,fees=endpoint(b,c,s,p,s1,p1,u)
        collateral=2500-b-q*c*p
        self.assertEqual(2500+q*s1*(1-c)+collateral+q*(p-p1)+q*u-q*c*p1,5000+pnl)
    def test_fee_no_doublecharge(self):
        b,c,s,p,s1,p1,u=map(F,['625','.006','10','11','20','19','0'])
        q,pnl,fees=endpoint(b,c,s,p,s1,p1,u)
        self.assertEqual(pnl,q*(s1-s+p-p1)-fees)
    def test_two_denominators_differ(self):
        pnl=F(200);self.assertEqual(pnl/2500,2*(pnl/5000));self.assertNotEqual(pnl/2500,pnl/5000)

if __name__=='__main__':unittest.main()
