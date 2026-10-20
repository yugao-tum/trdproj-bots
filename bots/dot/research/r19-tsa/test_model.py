import unittest
from copy import deepcopy
from datetime import date,timedelta
from model import predict

class Tests(unittest.TestCase):
    def setUp(self):
        self.m = dict(ticker='test',target_date='2021-10-25',split='holdout',decision_ts='2021-10-25T01:00:00Z',operator='gt',strike=100,time_eligible=True,exclusion_reasons=[])
        self.labels = [dict(target_date=(date(2021,10,25)-timedelta(days=7*i)).isoformat(), passenger_count=100+i%2,settlement_ts='2021-10-24T00:00:00Z',label_eligible=True) for i in range(1,11)]
    def test_latest8(self):
        p=predict(self.m,self.labels)['main']; self.assertEqual((p['n'],p['k'],p['p']),(8,4,.5)); self.assertEqual(p['feature_dates'][0],'2021-10-18')
    def test_threshold(self):
        m={**self.m,'operator':'gte'}; self.assertEqual(predict(m,self.labels)['main']['p'],8.5/9)
    def test_current_future_invariance(self):
        original=predict(self.m,self.labels)
        for day in ('2021-10-25','2021-10-26','2030-01-01'):
            bad=dict(target_date=day,passenger_count='bad',settlement_ts='bad',label_eligible=True)
            self.assertEqual(original,predict(self.m,self.labels+[bad]))
    def test_settlement_strictness(self):
        rows=deepcopy(self.labels[:4]); rows[0]['settlement_ts']=self.m['decision_ts']; p=predict(self.m,rows); self.assertEqual(p['main']['n'],3); self.assertIsNone(p['main']['p'])
    def test_seven_day_lag(self):
        r=dict(target_date='2021-10-19',passenger_count=500,settlement_ts='2021-10-20T00:00:00Z',label_eligible=True)
        self.assertEqual(predict(self.m,self.labels),predict(self.m,self.labels+[r]))
    def test_future_settlement_invariance(self):
        rows=deepcopy(self.labels); rows[0]['settlement_ts']='2021-10-26T00:00:00Z'; base=predict(self.m,rows); rows[0]['passenger_count']=999999; self.assertEqual(base,predict(self.m,rows))
    def test_market_fail_closed(self):
        p=predict({**self.m,'time_eligible':False},self.labels); self.assertFalse(p['model_eligible']); self.assertIsNone(p['main']['p'])
    def test_label_fail_closed(self):
        rows=deepcopy(self.labels); rows[0]['label_eligible']=False; self.assertEqual(predict(self.m,rows)['main']['n'],8)
    def test_no_history(self):
        p=predict(self.m,[]); self.assertIsNone(p['main']['p']);self.assertIsNone(p['baseline_28']['p'])
    def test_duplicate(self):
        with self.assertRaises(ValueError): predict(self.m,self.labels+self.labels[:1])

if __name__ == '__main__': unittest.main()
