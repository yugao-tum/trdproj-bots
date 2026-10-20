"""Independent standard-library replay. No other role's code is imported.
python reproduce.py --workers PATH_TO_WORKERS --output PATH_TO_RESULTS
"""
import argparse,csv,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext

def decimal(x):
    with localcontext() as c:
        c.prec=85
        return str(Decimal(x.numerator)/Decimal(x.denominator))
def rows(p):
    with p.open() as f: return list(csv.DictReader(f))
def cap(q0,S,P,M,c):
    A=max(F(10015,10000)*P,M,P);D=max(M-P,0)
    K=S*(1+c)+c*P+A+D
    q=q0 if q0*K<=2500 else F((min(q0,F(2500)/K)*10**24).__floor__(),10**24)
    return q,F(2500)-q*K

def endpoint(q,c,S,P,price,funding):
    s,p=F(price['spot_close']),F(price['perp_close'])
    fees=q*c*(S+P+s+p)
    basis=q*(s-S+P-p)
    pnl=funding+basis-fees
    collateral=2500-q*S*(1+c)-q*c*P
    cash=collateral+funding+q*(P-p)-q*c*p+q*s*(1-c)
    assert cash-2500==pnl
    return {'pnl':pnl,'funding':funding,'fees':fees,'basis':basis,'return5000':pnl/5000,'return2500':pnl/2500}

def replay(root, contract_path=None, crosscheck=None):
    contract=json.loads((contract_path or Path(__file__).with_name('inputs-parameters-hashes.json')).read_text())
    paths=['r20-proposal/04-prices/output/daily_prices.csv','r24-proposal/04-prices/output/daily_prices.csv','r20-proposal/01-funding/output/funding.csv','r24-proposal/03-funding/output/funding.csv']
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}
    for name,digest in hashes.items(): assert digest==contract['sha256'][name], 'Input hash mismatch: '+name
    prices=rows(root/paths[0])+rows(root/paths[1]);funds=rows(root/paths[2])+rows(root/paths[3])
    matrix=contract['cases']
    result=[]
    for case in matrix:
        symbol=case['symbol']; ps=sorted([x for x in prices if x['symbol']==symbol],key=lambda x:x['date_utc'])
        entry=int(ps[0]['open_time_ms']); fs=sorted([x for x in funds if x['symbol']==symbol and int(x['fundingTime'])>entry],key=lambda x:int(x['fundingTime']))
        assert len(ps)==1023 and len({x['date_utc'] for x in ps})==1023
        assert len(fs)==3068 and len({x['fundingTime'] for x in fs})==3068
        S,P,M=[F(ps[0][f]) for f in ['spot_open','perp_open','mark_open']];c=F(case['cost']);B=F(case['budget']);q0=F(case['q0'])
        assert abs(q0-B/(S*(1+c)))<F(1,10**45)
        q,gap=cap(q0,S,P,M,c)
        assert q<=q0 and gap>=0
        collateral=2500-q*S*(1+c)-q*c*P
        cumulative=F(0);first_funding=None;first_daily=None;minimum=None;ep={};i=0
        for day in ps:
            prefixes=[cumulative]
            while i<len(fs) and int(fs[i]['fundingTime'])<=int(day['close_time_ms']):
                event=fs[i]; mark=F(event['markPrice']); before=collateral+cumulative+q*(P-mark)
                cumulative+=q*F(event['fundingRate'])*mark
                after=collateral+cumulative+q*(P-mark)
                if min(before,after)<0 and first_funding is None: first_funding=event['fundingTime']
                prefixes.append(cumulative);i+=1
            upper=collateral+max(prefixes)+q*(P-F(day['mark_high']))
            lower=collateral+min(prefixes)+q*(P-F(day['mark_high']))
            minimum=lower if minimum is None else min(minimum,lower)
            if upper<0 and first_daily is None:first_daily=day['date_utc']
            if day['date_utc'] in ['2026-09-30','2026-10-19']: ep[day['date_utc']]=endpoint(q,c,S,P,day,cumulative)
        record={'scenario_id':case['scenario_id'],'quantity':decimal(q),'retained':q==q0,'opening_gap':decimal(gap),'funding_events':len(fs),'daily_rows':len(ps),'first_negative_funding_ms':first_funding,'first_guaranteed_negative_day':first_daily,'minimum_equity_lower':decimal(minimum),'endpoints':{d:{k:decimal(v) for k,v in e.items()} for d,e in ep.items()},'october_endpoint_increment':decimal(ep['2026-10-19']['pnl']-ep['2026-09-30']['pnl']),'september_cap_minus_original':decimal(ep['2026-09-30']['pnl']*(1-q0/q))}
        result.append(record)
    assert sum(x['retained'] for x in result)==6
    if crosscheck is not None:
        baseline=json.loads(crosscheck.read_text())
        assert result==baseline['cases'], 'Exact all-case baseline mismatch'
    return {'schema':'r24.independent-integration.v1','cases':result,'input_sha256':contract['sha256'],'assertions':'All exact opening, cash identity, source hash/shape and quantity checks passed. Historical peer reconciliations are recorded in the report; optional --crosscheck compares every case field exactly.'}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--workers',required=True,type=Path);a.add_argument('--output',required=True,type=Path);a.add_argument('--contract',type=Path);a.add_argument('--crosscheck',type=Path);args=a.parse_args();r=replay(args.workers,args.contract,args.crosscheck);args.output.mkdir(parents=True,exist_ok=True);(args.output/'compact-results.json').write_text(json.dumps(r,indent=2)+'\n');print('12 cases independently replayed; requested checks passed.')
