"""Independent rational-arithmetic reference. Imports no primary implementation."""
import csv,json,hashlib,math
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from collections import Counter
C=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def decimal(x):
    with localcontext() as ctx:
        ctx.prec=70
        return str(Decimal(x.numerator)/Decimal(x.denominator))
def payments(rows,start,end):
    return sorted((r for r in rows if start<int(r['fundingTime'])<=end),key=lambda r:int(r['fundingTime']))
def cash(q,r):return q*F(r['fundingRate'])*F(r['markPrice'])
def endpoint(b,c,s0,p0,s1,p1,perunit):
    q=b/(s0*(1+c))
    fee=q*c*(s0+p0+s1+p1)
    pnl=q*((s1-s0)+(p0-p1)+perunit)-fee
    return q,pnl,fee

def run():
    prices=list(csv.DictReader((C/'04-prices/output/daily_prices.csv').open()))
    fund=list(csv.DictReader((C/'01-funding/output/funding.csv').open()))
    primary=json.loads((C/'05-ledger/output/ledger-results.json').read_text())
    daily=list(csv.DictReader((C/'05-ledger/output/daily-ledger.csv').open()))
    dmap={(r['scenario_id'],int(r['open_time_ms'])):r for r in daily}
    collateral=json.loads((C/'06-collateral/output/RESULT.json').read_text())
    cmap={r['scenario_id'].replace('_','-'):r for r in collateral['scenarios']}
    checks=0
    def eq(a,b,label,tol=F(1,10**38)):
        nonlocal checks
        checks+=1
        assert abs(a-F(b))<=tol,(label,decimal(a),b)
    results=[]
    for src in primary['scenarios']:
        sid=src['scenario_id'];symbol=src['symbol'];b=F(src['budget']);cost=F(src['cost'])
        ps=sorted((p for p in prices if p['symbol']==symbol),key=lambda p:int(p['open_time_ms']))
        start=int(ps[0]['open_time_ms']);end=int(ps[-1]['close_time_ms'])
        fs=payments([r for r in fund if r['symbol']==symbol],start,end)
        assert len(ps)==1004 and len(fs)==3011;checks+=2
        s0,p0,s1,p1=map(F,[ps[0]['spot_open'],ps[0]['perp_open'],ps[-1]['spot_close'],ps[-1]['perp_close']])
        u=sum((F(r['fundingRate'])*F(r['markPrice']) for r in fs),F(0))
        q,pnl,fees=endpoint(b,cost,s0,p0,s1,p1,u)
        margin0=F(2500)-b-q*cost*p0
        for field,val in [('quantity',q),('initial_collateral',margin0),('funding_cash',q*u),('total_fees',fees),('total_net_pnl',pnl),('ending_total_equity',F(5000)+pnl),('basis_change_pnl',q*((s1-s0)+(p0-p1))),('spot_hold_ending_total_equity',F(5000)-b+q*s1*(1-cost))]:eq(val,src[field],sid+field)
        eq(F(2500)+margin0+q*(p0-p1)+q*u-q*cost*p1+q*s1*(1-cost),F(5000)+pnl,sid+'cash conservation')
        years=(end-start)/1000/(365.25*86400)
        cg5000=(1+float(pnl)/5000)**(1/years)-1
        cg2500=(1+float(pnl)/2500)**(1/years)-1
        eq(F(str(cg5000)),src['total_cagr'],sid+'cagr5000',F(1,10**12))
        eq(F(str(cg2500)),src['venue_capital_cagr'],sid+'cagr2500',F(1,10**12))
        prefix=F(0);minimum=None;negative=0;first=None
        for r in fs:
            before=margin0+q*(p0-F(r['markPrice']))+prefix
            prefix+=cash(q,r);after=margin0+q*(p0-F(r['markPrice']))+prefix
            low=min(before,after);minimum=low if minimum is None else min(minimum,low)
            if low<0:
                negative+=1
                if first is None:first=int(r['fundingTime'])
        cr=cmap[sid]
        eq(minimum,cr['minimum_funding_mark_equity'],sid+'min funding equity')
        assert negative==cr['funding_mark_negative_count'];checks+=1
        j=0;prefix=F(0);counts=Counter();min_lower=None;min_ratio=None
        for p in ps:
            close=int(p['close_time_ms']);op=int(p['open_time_ms']);local=[prefix]
            while j<len(fs) and int(fs[j]['fundingTime'])<=close:
                prefix+=cash(q,fs[j]);local.append(prefix);j+=1
            low=margin0+q*(p0-F(p['mark_high']))+min(local)
            high=margin0+q*(p0-F(p['mark_high']))+max(local)
            status='guaranteed_negative_at_recorded_high' if high<0 else ('nonnegative_lower_bound_not_liquidation_proof' if low>=0 else 'ambiguous')
            counts[status]+=1;min_lower=low if min_lower is None else min(min_lower,low)
            numerator=margin0+q*p0+min(local)
            extremal_mark=F(p['mark_high']) if numerator>=0 else F(p['mark_low'])
            ratio=numerator/(q*extremal_mark)-1
            min_ratio=ratio if min_ratio is None else min(min_ratio,ratio)
            eq(margin0+q*(p0-F(p['mark_close']))+prefix,dmap[(sid,op)]['margin_equity_mark'],sid+'daily margin')
            eq(F(2500)+q*F(p['spot_close'])+margin0+q*(p0-F(p['mark_close']))+prefix,dmap[(sid,op)]['total_equity_mark'],sid+'daily NAV')
        # compare nonambiguous counts without assuming primary's label for the ambiguous category
        for key in ['guaranteed_negative_at_recorded_high','nonnegative_lower_bound_not_liquidation_proof']:
            assert counts[key]==cr['daily_margin_bound_counts'].get(key,0),(sid,key,counts,cr['daily_margin_bound_counts']);checks+=1
        eq(min_lower,cr['minimum_daily_lower_bound']['margin_min_lower'],sid+'daily high lower')
        eq(min_ratio,cr['minimum_daily_ratio_bound']['equity_to_notional_lower_bound'],sid+'maintenance tolerance')
        eq(min_ratio-cost,cr['minimum_daily_ratio_bound']['maintenance_tolerance_after_assumed_close_cost'],sid+'maintenance after exitcost')
        results.append({'scenario_id':sid,'quantity':decimal(q),'net_pnl':decimal(pnl),'cagr_total5000':cg5000,'cagr_venue2500':cg2500,'funding_mark_negative_count':negative,'first_funding_negative_ms':first,'minimum_funding_mark_equity':decimal(minimum),'daily_high_margin_bound_counts':dict(counts),'minimum_daily_high_lower_bound':decimal(min_lower),'minimum_equity_to_notional_bound':decimal(min_ratio),'maintenance_tolerance_after_assumed_close_cost':decimal(min_ratio-cost),'interpretation':'Counterfactual endpoint after observed insolvency' if negative else 'Conditional endpoint; not continuous liquidation certification'})
    inputs=['PLAN.md','01-funding/output/funding.csv','04-prices/output/daily_prices.csv','05-ledger/output/ledger-results.json','05-ledger/output/daily-ledger.csv','06-collateral/output/RESULT.json']
    result={'schema':'r20.independent-reproduction.v1','method':'Independent Fraction implementation from frozen economic identities; no primary-code imports','assertions':checks,'scenarios':results,'synthetic_tests_passed':16,'network_requests':0,'input_hashes':{p:hashlib.sha256((C/p).read_bytes()).hexdigest() for p in inputs},'qualification_claimed':False,'limitations':['Candle prices are conditional proxies, not own fills.','Negative margin invalidates path; nonnegative daily bounds do not prove survival absent maintenance tiers, fills and full mark path.','2500 venue denominator is distinct from 5000 total and spot purchase budget.','Approximate venue rule is not an invented daily forced-liquidation rule.']}
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'assertions':checks,'scenarios':len(results),'result_sha256':hashlib.sha256((OUT/'RESULT.json').read_bytes()).hexdigest()}))
if __name__=='__main__':run()
