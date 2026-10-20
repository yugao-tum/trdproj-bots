"""Independent stdlib reconstruction. No other role implementation is imported.
Required raw inputs are deliberately not distributed; see INPUTS.md.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from decimal import Decimal as D,getcontext
from datetime import datetime,timezone
getcontext().prec=50
START=1704067200000; END=1790812799999; DAY=86400000

def prefixes(start,changes):
    values=[start]
    for change in changes: values.append(values[-1]+change)
    return min(values),max(values),values[-1]

def bounds(cash,q,p,high,fmin,fmax):
    return cash+q*(p-high)+fmin,cash+q*(p-high)+fmax

def run(root,out):
    r20=root/'continuation-20261020/workers/r20-proposal'; r23=root/'continuation-20261020/workers/r23-proposal'
    hashes={}
    def load(p):
        hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
        return json.loads(p.read_text())
    def bars(p): return load(p)['response']['structuredContent']['result']
    spotpath=root/'workers/data-probe/data/history/spot_daily.csv'
    hashes[str(spotpath.relative_to(root))]=hashlib.sha256(spotpath.read_bytes()).hexdigest()
    spots={}
    for r in csv.DictReader(spotpath.open()):
        # Original spot capture mixes millisecond/microsecond epochs after 2025.
        t=int(r['open_time_raw']); t=t//1000 if t>10**14 else t
        if START<=t<=END: spots[r['symbol'],t]=r
    minute_payload=load(r23/'05-minute-data/output/raw-mark1m-tool.json')
    minute=minute_payload['structuredContent']['result']
    assert json.loads(minute_payload['content'][0]['text'])['result']==minute
    assert len(minute)==1440 and [int(b[0]) for b in minute]==list(range(1755993600000,1756080000000,60000))
    old=load(r20/'05-ledger/output/ledger-results.json')
    old={x['scenario_id']:x for x in old['scenarios']}
    results=[]
    for symbol,mmr in [('BTCUSDT',D('.004')),('ETHUSDT',D('.004')),('SOLUSDT',D('.005'))]:
        mark=bars(r20/f'04-prices/raw/{symbol}-mark.json'); perp=bars(r20/f'04-prices/raw/{symbol}-perp.json')
        assert len(mark)==len(perp)==1004
        assert [int(x[0]) for x in mark]==list(range(START,END,DAY))
        events=[]
        for pth in sorted((r20/'01-funding/raw').glob(symbol+'-page*.json')): events+=load(pth)['structured_response']['result']
        assert len(events)==len({e['fundingTime'] for e in events})==3012
        events=sorted([e for e in events if START<e['fundingTime']<=END],key=lambda e:e['fundingTime'])
        assert len(events)==3011
        for budget in [D(1250),D(625)]:
            for cost in [D('.003'),D('.006')]:
                sid=f'{symbol}-b{budget}-c{cost}'; s=D(spots[symbol,START]['open']); p=D(perp[0][1]); q=budget/(s*(1+cost)); cash=2500-budget-q*p*cost
                grouped={}
                for e in events: grouped.setdefault((e['fundingTime']//DAY)*DAY,[]).append(e)
                f=D(0); daily=[]; firstzero=None; firstmm=None
                for b in mark:
                    t=int(b[0]); es=grouped.get(t,[]); lo,hi,f=prefixes(f,[q*D(e['markPrice'])*D(e['fundingRate']) for e in es]); el,eu=bounds(cash,q,p,D(b[2]),lo,hi); n=q*D(b[2]); date=datetime.fromtimestamp(t/1000,timezone.utc).date().isoformat()
                    assert cash+q*p+lo>0, 'Ratio lower bound requires sign branch; frozen case invariant failed'
                    daily.append({'date':date,'lower':el,'upper':eu,'notional':n,'mmr_max_lower':el/n,'stress_mmr_max_lower':el/n-cost})
                    if eu<=0 and firstzero is None:firstzero=date
                    if eu-n*mmr<=0 and firstmm is None:firstmm=date
                sx=D(spots[symbol,int(mark[-1][0])]['close']); px=D(perp[-1][4]); endpoint=2500+q*sx*(1-cost)+cash+q*(p-px)+f-q*px*cost
                assert abs(endpoint-D(old[sid]['ending_total_equity']))<D('1e-40')
                low=min(daily,key=lambda d:d['lower']); basegap=cash-q*p
                result={'id':sid,'quantity':q,'cash':cash,'entry_1x_unbuffered_gap':basegap,'mark_guard_gap_not_rule':cash-q*D(mark[0][1]),'current_15bp_buffer_gap':cash-q*p*D('1.0015')-max(D(0),q*(D(mark[0][1])-p)),'first_proven_zero_day':firstzero,'first_conditional_mmr_fail_day':firstmm,'worst_daily_bound':low,'endpoint_counterfactual_if_failed':endpoint,'first_conditional_failure_witness':next((d for d in daily if d['date']==firstmm),None),'max_mark_notional':max(d['notional'] for d in daily),'min_mmr_ceiling':min(d['mmr_max_lower'] for d in daily),'minimum_conditional_gap':min(d['lower']-d['notional']*mmr for d in daily)}
                if symbol=='ETHUSDT':
                    begin=int(minute[0][0]); fm=sum((q*D(e['markPrice'])*D(e['fundingRate']) for e in events if e['fundingTime']<begin),D(0)); ms=[]
                    for b in minute:
                        changes=[q*D(e['markPrice'])*D(e['fundingRate']) for e in grouped.get(begin,[]) if int(b[0])<=e['fundingTime']<=int(b[6])]
                        lo,hi,fm=prefixes(fm,changes); el,eu=bounds(cash,q,p,D(b[2]),lo,hi); ms.append((el,eu,int(b[0]),q*D(b[2])))
                    ml=min(ms); result['minute_day']={'lower':min(x[0] for x in ms),'upper':min(x[1] for x in ms),'minute_start_ms':ml[2],'mmr_ceiling':ml[0]/ml[3],'conditional_stress_gap':ml[0]-ml[3]*(mmr+cost)}
                results.append(result)
    out.mkdir(parents=True,exist_ok=True)
    (out/'INDEPENDENT.json').write_text(json.dumps({'claim':'8a8f7ffd','configs':results},default=str,indent=2)+'\n')
    (out/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    return results
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,default=Path('.'));a=ap.parse_args();run(a.root,a.out)
