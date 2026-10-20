#!/usr/bin/env python3
"""A daily-target self-financing ledger. Frozen signals only; no signal recomputation."""
import argparse,csv,hashlib,json,math
from pathlib import Path
COINS=('BTC','ETH','SOL')
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def solve(q,c,p,w,rate):
    assert 0<=rate<1 and all(x>=0 for x in w) and sum(w)<=1+1e-12
    assert all(x>0 and math.isfinite(x) for x in p) and c>=-1e-8 and all(x>=0 for x in q)
    v=[a*b for a,b in zip(q,p)]; before=c+sum(v)
    def f(e): return e+rate*sum(abs(e*x-y) for x,y in zip(w,v))-before
    lo,hi=0.,before
    for _ in range(100):
        mid=(lo+hi)/2
        if f(mid)>0: hi=mid
        else: lo=mid
    equity=(lo+hi)/2
    after=[equity*x/y for x,y in zip(w,p)]
    trades=[(a-b)*z for a,b,z in zip(after,q,p)]
    fees=[rate*abs(x) for x in trades]
    cash=c-sum(trades)-sum(fees)
    assert cash>=-1e-8,(cash,w)
    assert abs(cash-c+sum(trades)+sum(fees))<1e-8
    for j in range(len(q)):
        assert abs(after[j]-q[j]-trades[j]/p[j])<1e-8
        assert abs(after[j]*p[j]-equity*w[j])<1e-8
    assert abs(cash+sum(a*b for a,b in zip(after,p))+sum(fees)-before)<1e-7
    return after,cash,trades,fees

def tests():
    results=[]
    for name,q,c,p,w,r in [
      ('initial_full_investment',[0,0],2500,[10,20],[.5,.5],.003),
      ('no_trade',[50,25],0,[10,20],[.5,.5],.006),
      ('liquidation',[50,25],0,[10,20],[0,0],.003),
      ('zero_fee',[0,0],1000,[10,20],[.2,.4],0),
      ('constant_target_drift',[50,25],0,[20,20],[.5,.5],.003),
      ('all_cash',[0,0],2500,[10,20],[0,0],.006)]:
        nq,nc,t,f=solve(q,c,p,w,r)
        residual=nc+sum(a*b for a,b in zip(nq,p))+sum(f)-c-sum(a*b for a,b in zip(q,p))
        assert abs(residual)<1e-8
        if name=='constant_target_drift': assert sum(abs(x) for x in t)>499
        if name=='no_trade': assert sum(abs(x) for x in t)<1e-8
        results.append(dict(name=name,pass_test=True,trade_notional=sum(abs(x) for x in t),fee=sum(f),cash=nc,residual=residual))
    return results

def run(panel_path,signal_path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    panel=list(csv.DictReader(open(panel_path))); index={r['date_utc']:i for i,r in enumerate(panel)}
    groups={}
    for row in csv.DictReader(open(signal_path)):
        if row['is_test'].lower()=='true': groups.setdefault((row['fold_id'],row['variant']),[]).append(row)
    daily=[];assets=[];aggregates=[]
    for (fold,var),rows in sorted(groups.items()):
      for rate in (0.,.003,.006):
        qty=[0.]*3;cash=2500.;reserve=2500.;prev_total=5000.;peak=5000.;dd=0.;fees_total=0.;turnover=0.;gross=0.;peakvenue=2500.;breachdays=0;peak_high_bound=2500.;maxres=0.
        for row in rows:
            i=index[row['date_utc']];prev=panel[i-1];current=panel[i]
            p=[float(prev[x+'_close']) for x in COINS];end=[float(current[x+'_close']) for x in COINS]
            weights=[float(row[x+'_weight']) for x in COINS]
            oldqty=qty[:];oldcash=cash;before=cash+sum(a*b for a,b in zip(qty,p))
            assert abs(before+reserve-prev_total)<1e-6
            qty,cash,trades,fees=solve(qty,cash,p,weights,rate)
            pnl=sum(a*(b-c) for a,b,c in zip(qty,end,p));cost=sum(fees)
            venue=cash+sum(a*b for a,b in zip(qty,end));total=venue+reserve
            residual=total-prev_total-pnl+cost;maxres=max(maxres,abs(residual))
            assert abs(residual)<1e-7
            peak=max(peak,total);dd=min(dd,total/peak-1);peakvenue=max(peakvenue,venue,before)
            highbound=cash+sum(a*float(current[x+'_high']) for a,x in zip(qty,COINS));peak_high_bound=max(peak_high_bound,highbound)
            breachdays+=int(venue>2500+1e-8);fees_total+=cost;gross+=pnl;turnover+=sum(abs(x) for x in trades)
            common=dict(fold_id=fold,variant=var,accounting_mode='A_daily_target_close_to_close_conditional',cost_side=rate,utc_date=row['date_utc'])
            daily.append(dict(**common,cash_before=oldcash,venue_before=before,fee=cost,trade_notional=sum(abs(x) for x in trades),gross_pnl=pnl,cash_after=cash,venue_value=venue,reserve=reserve,total_equity=total,conservation_residual=residual,venue_close_limit_breach=venue>2500+1e-8,venue_high_upper_bound=highbound))
            for j,x in enumerate(COINS):
                assets.append(dict(**common,symbol=x,qty_before=oldqty[j],price_before=p[j],drifted_value=oldqty[j]*p[j],target_weight=weights[j],trade_qty=qty[j]-oldqty[j],trade_notional=trades[j],fee=fees[j],qty_after=qty[j],cash_after=cash,venue_value=venue,reserve=reserve,total_equity=total))
            prev_total=total
        liquidation_fee=rate*sum(a*b for a,b in zip(qty,end))
        aggregates.append(dict(fold_id=fold,variant=var,accounting_mode='A_daily_target_close_to_close_conditional',cost_side=rate,start=rows[0]['date_utc'],end=rows[-1]['date_utc'],days=len(rows),input_hash=digest(panel_path),signals_hash=digest(signal_path),initial_equity=5000.,initial_venue=2500.,initial_reserve=2500.,final_equity=prev_total,gross_pnl=gross,costs=fees_total,net_pnl=prev_total-5000,cagr=(prev_total/5000)**(365/len(rows))-1,drawdown=dd,turnover=turnover,turnover_div_initial_equity=turnover/5000,peak_venue_value=peakvenue,venue_close_limit_breach_days=breachdays,venue_2500_limit_pass=peakvenue<=2500+1e-8,peak_daily_high_upper_bound=peak_high_bound,max_conservation_residual=maxres,ending_inventory_liquidation_assumption='mark to final close; liquidation NOT included',hypothetical_final_liquidation_fee=liquidation_fee,final_equity_after_hypothetical_liquidation=prev_total-liquidation_fee,evidence_level='conditional_simulation_not_real_execution',next_open_status='not_verified'))
    for name,data in [('daily_account.csv',assets),('daily_equity.csv',daily),('aggregate.csv',aggregates)]:
        with open(out/name,'w') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    (out/'aggregate.json').write_text(json.dumps(aggregates,indent=2))
    (out/'synthetic_tests.json').write_text(json.dumps(tests(),indent=2))
    (out/'manifest.json').write_text(json.dumps(dict(engine='A daily target',panel_sha256=digest(panel_path),signals_sha256=digest(signal_path),initial_total=5000,venue_initial=2500,reserve_fixed=2500,signal_recalculation=False,execution='Previous close rebalancing with already lagged frozen target for current close-to-close return. Same-close signal/execute is an unverified conditional fill.',fold_initialization='Independent cash reset at each first test day; warmup informs frozen signal only. Entry fees included. No warmup holdings inherited.',cost_sides=[0,.003,.006],capital='No withdrawals or fake second venue; dynamic venue excess is a failed constraint, not corrected ex post.',high_bound='Sum of per-asset daily highs is a conservative upper bound, not simultaneous observed intraday portfolio value.',next_open='Not replayed. No open prices in frozen panel. No executable return claim.',daily_account_cash='cash_after/reserve/venue/total repeated per symbol for interface only; never sum these across symbols; use daily_equity.csv',tests_passed=len(tests()),runs=len(aggregates)),indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--panel',required=True);p.add_argument('--signals',required=True);p.add_argument('--out',required=True);a=p.parse_args();tests();run(a.panel,a.signals,a.out)
