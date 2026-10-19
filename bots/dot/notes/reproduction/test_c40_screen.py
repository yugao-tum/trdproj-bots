import copy
import csv
import tempfile
import unittest
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import c40_screen as c

@dataclass
class Bar:
    day: date
    open: float
    high: float
    low: float
    close: float

def fixture():
    bars=[Bar(date(2024,12,1)+timedelta(days=i),100,101,99,100) for i in range(60)]
    bars[14]=Bar(bars[14].day,100,101,98,98)
    funding={b.day:[-.001,-.001,-.001] for b in bars}
    return bars,funding

class TestC40(unittest.TestCase):
    def test_flat_round_trip_manual(self):
        bars,f=fixture();sim=c.simulate('BTCUSDT',bars,f,.003,date(2024,12,25),date(2024,12,30))
        self.assertEqual(len(sim['trades']),2)
        self.assertAlmostEqual(sim['daily'][-1]['equity'],4993.4)
        self.assertAlmostEqual(sum(t['fee'] for t in sim['trades']),6.6)
        self.assertEqual(sim['trades'][-1]['reason'],'final close liquidation')
    def test_stress_manual(self):
        bars,f=fixture();sim=c.simulate('BTCUSDT',bars,f,.006,date(2024,12,25),date(2024,12,30))
        self.assertAlmostEqual(sim['daily'][-1]['equity'],4986.8)
    def test_seven_day_open_exit(self):
        bars,f=fixture();sim=c.simulate('BTCUSDT',bars,f,.003,date(2024,12,25),date(2025,1,3))
        self.assertEqual(sim['trades'][1]['date'],'2025-01-01')
        self.assertEqual(sim['trades'][1]['reason'],'entry plus seven calendar days')
        self.assertEqual(sim['episodes'][0]['calendar_holding_days'],7)
        self.assertEqual(sum(t['date']=='2025-01-01' for t in sim['trades']),1)
    def test_prior_funding_exit(self):
        bars,f=fixture();f[date(2024,12,26)]=[-.001,0,.001]
        sim=c.simulate('BTCUSDT',bars,f,.003,date(2024,12,25),date(2024,12,30))
        self.assertEqual(sim['trades'][1]['date'],'2024-12-27')
    def test_strict_three_negative_entry(self):
        bars,f=fixture()
        self.assertTrue(c.signal(bars,24,[-1,-1,-1])[0])
        for rates in ([0,-1,-1],[-1,0,-1],[-1,-1,0]): self.assertFalse(c.signal(bars,24,rates)[0])
    def test_current_and_future_prices_do_not_change_signal(self):
        bars,f=fixture();original=c.signal(bars,24,f[bars[23].day])
        for b in bars[24:]: b.open*=10;b.high*=10;b.low*=10;b.close*=10
        self.assertEqual(c.signal(bars,24,f[bars[23].day]),original)
    def test_future_funding_not_used_for_current_entry(self):
        bars,f=fixture();start=date(2024,12,25);end=date(2024,12,30)
        a=c.simulate('BTCUSDT',bars,f,.003,start,end)
        for d in f:
            if d>=start: f[d]=[1,1,1]
        b=c.simulate('BTCUSDT',bars,f,.003,start,end)
        self.assertEqual(a['trades'][0],b['trades'][0])
        self.assertEqual(a['daily'][0]['entry_signal'],b['daily'][0]['entry_signal'])
        self.assertEqual(b['trades'][1]['date'],'2024-12-26')
    def test_oos_carry_and_fee_dates(self):
        bars,f=fixture();sim=c.simulate('BTCUSDT',bars,f,.003,date(2024,12,28),date(2025,1,4))
        oos=c.period_metrics(sim,'2025-01-01','2025-01-04')
        self.assertEqual(oos['episodes_started'],0)
        self.assertEqual(oos['carry_in_qty'],11)
        self.assertAlmostEqual(oos['start_equity'],4996.7)
        self.assertAlmostEqual(oos['net_pnl'],-3.3)
        self.assertAlmostEqual(oos['fees'],3.3)
        self.assertEqual(oos['calendar_days'],4)
    def test_open_breach_before_sell_fee(self):
        bars,f=fixture();bars[25]=Bar(bars[25].day,250,251,249,250)
        f[bars[24].day]=[0,0,0]
        sim=c.simulate('BTCUSDT',bars,f,.003,date(2024,12,25),date(2024,12,30))
        self.assertTrue(sim['daily'][1]['open_breach'])
        self.assertTrue(all(r['cash']>=0 and r['qty']>=0 for r in sim['daily']))
    def test_no_trade_cash_and_null_independence(self):
        bars,f=fixture();f={d:[0,0,0] for d in f}
        sim=c.simulate('BTCUSDT',bars,f,.003,date(2024,12,25),date(2024,12,30))
        self.assertEqual(sim['trades'],[])
        self.assertEqual(sim['daily'][-1]['equity'],5000)
    def test_missing_prior_day_rejected(self):
        bars,f=fixture();del f[date(2024,12,24)]
        with self.assertRaises(KeyError): c.simulate('BTCUSDT',bars,f,.003,date(2024,12,25),date(2024,12,30))
    def test_bad_rates_rejected(self):
        bars,f=fixture()
        with self.assertRaises(ValueError): c.simulate('BTCUSDT',bars,f,0,date(2024,12,25),date(2024,12,30))

class TestFundingLoader(unittest.TestCase):
    def make_file(self,path,mode=None):
        fields=['symbol','calc_time_utc','calc_time_raw','calc_time_raw_utc','funding_interval_hours','last_funding_rate','jitter_ms']
        with path.open('w',newline='') as out:
            w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
            for s in c.SYMBOLS:
                for i in range(3012):
                    t=datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(hours=8*i)
                    row=dict(symbol=s,calc_time_utc=t.isoformat(),calc_time_raw=str(int(t.timestamp()*1000)),
                             calc_time_raw_utc=t.isoformat(),funding_interval_hours='8',last_funding_rate='-.0001',jitter_ms='0')
                    if s==c.SYMBOLS[0] and i==0:
                        if mode=='missing': continue
                        if mode=='nan': row['last_funding_rate']='nan'
                        if mode=='raw': row['calc_time_raw']=str(int(t.timestamp()*1000)+1)
                        if mode=='jitter': row['jitter_ms']='1'
                        if mode=='duplicate': w.writerow(row)
                    w.writerow(row)
    def test_complete_and_bad_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'funding.csv';self.make_file(p)
            daily,q=c.load_funding(p);self.assertEqual(q['rows'],9036);self.assertEqual(len(daily['BTCUSDT']),1004)
            for mode in ['missing','nan','raw','jitter','duplicate']:
                self.make_file(p,mode)
                with self.subTest(mode=mode),self.assertRaises(ValueError):c.load_funding(p)

if __name__=='__main__': unittest.main()
