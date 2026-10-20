"""Offline verification. Pass the retained r13 output directory. Never downloads or trades."""
import json,sys,hashlib
from pathlib import Path
from decimal import Decimal as D

def classify(row):
    # A positive-volume candle supports a venue-reported low, not a fill at that low.
    v=D(row['volume']); low=D(row['low'])
    if v < 0: raise ValueError('negative volume')
    return {'eligible_low_print':v>0 and low<=D('0.99'),
            'new_trade_evidence':v>0, 'exact_low_quantity':None,
            'executable_entry':False, 'pnl':None,
            'zero_volume_carry':v==0}

def verify(p):
    raw=(p/'raw/minute-response.json').read_bytes(); rows=json.loads(raw)['data']['ohlc'];f=json.loads((p/'frozen-window.json').read_text());checks=[]
    def ck(name,v):
        if not v: raise AssertionError(name)
        checks.append(name)
    ck('raw fingerprint',hashlib.sha256(raw).hexdigest()=='22bd444a5f33bd149a6af5984dbbc66379030810e716b51eac83a4c43c4074a9')
    ck('180 consecutive unique minutes',[int(r['timestamp']) for r in rows]==list(range(f['start'],f['end_exclusive'],60)))
    ck('nonnegative volume and OHLC ordering',all(D(r['volume'])>=0 and D(r['low'])<=min(D(r['open']),D(r['close']))<=max(D(r['open']),D(r['close']))<=D(r['high']) for r in rows))
    ck('157 zero-volume rows',sum(D(r['volume'])==0 for r in rows)==157)
    for h in f['hourly_rows']:
        rs=[r for r in rows if h['timestamp']<=int(r['timestamp'])<h['timestamp']+3600]
        ck(str(h['timestamp'])+' high low close volume',max(D(r['high']) for r in rs)==D(h['high']) and min(D(r['low']) for r in rs)==D(h['low']) and D(rs[-1]['close'])==D(h['close']) and sum(D(r['volume']) for r in rs)==D(h['volume']))
        ck(str(h['timestamp'])+' positive-volume open',D(next(r for r in rs if D(r['volume'])>0)['open'])==D(h['open']))
    ck('open mismatch preserved',D(rows[0]['open'])-D(f['hourly_rows'][0]['open'])==D('-0.00012'))
    qualifying=[r for r in rows if classify(r)['eligible_low_print']]
    ck('one qualifying positive-volume minute',len(qualifying)==1 and int(qualifying[0]['timestamp'])==1769013780 and D(qualifying[0]['low'])==D('0.98558') and D(qualifying[0]['volume'])==D('237069.11760'))
    ck('no candle implies exact low quantity or entry',all(classify(r)['exact_low_quantity'] is None and not classify(r)['executable_entry'] and classify(r)['pnl'] is None for r in rows))
    # Explicit regression against treating a stale low as a fresh event.
    synthetic=dict(rows[0],volume='0',low='0.98')
    ck('synthetic zero-volume low not new print',not classify(synthetic)['eligible_low_print'])
    return {'pass_count':len(checks),'checks':checks,'real_minutes':180,'zero_volume_minutes':157,'positive_volume_minutes':23,'qualifying_low_minutes':1,'independent_profit_results':0,'new_mechanisms':0,'real_backtests':0,'conditional_simulations':0,'qualified':0,'network_requests':0,'synthetic_test_note':'One constructed zero-volume regression fixture; not market data.'}
if __name__=='__main__': print(json.dumps(verify(Path(sys.argv[1])),ensure_ascii=False,indent=2))
