#!/usr/bin/env python3
"""Frozen-share B ledger. Only consumes signals, never generates them."""
import csv,json,hashlib,argparse,math
from pathlib import Path
from collections import defaultdict
S=('BTC','ETH','SOL')
def truth(x): return str(x).lower() in ('true','1','1.0')
def solve(values,cash,w,fee):
    equity=cash+sum(values)
    assert min(w)>=0 and sum(w)<=1+1e-10
    lo,hi=0.,equity
    for _ in range(90):
        mid=(lo+hi)/2
        f=mid+fee*sum(abs(mid*a-v) for a,v in zip(w,values))-equity
        if f>0: hi=mid
        else: lo=mid
    post=(lo+hi)/2
    target=[post*a for a in w]
    delta=[a-v for a,v in zip(target,values)]
    costs=[fee*abs(d) for d in delta]
    new_cash=cash-sum(delta)-sum(costs)
    assert new_cash>=-1e-8
    return target,delta,costs,max(0.,new_cash)
def step(q,cash,p0,p1,w,fee,rebalance):
    vals=[a*b for a,b in zip(q,p0)]; before=cash+sum(vals)
    if rebalance: target,delta,costs,after=solve(vals,cash,w,fee)
    else: target,delta,costs,after=vals,[0.]*3,[0.]*3,cash
    nq=[v/p for v,p in zip(target,p0)]
    end=after+sum(a*b for a,b in zip(nq,p1))
    pnl=sum(a*(b-c) for a,b,c in zip(nq,p1,p0))
    error=end-(before+pnl-sum(costs))
    assert abs(error)<1e-7 and min(nq)>=0 and after>=0
    assert abs(after-(cash-sum(delta)-sum(costs)))<1e-7
    return nq,after,delta,costs,end,pnl,error

def tests():
    q,c,d,f,e,p,err=step([0]*3,2500,[10]*3,[11,9,10],[.5,.5,0],.003,True)
    assert abs(e-(2500-sum(f)))<1e-8
    q2,c2,d2,f2,*_=step(q,c,[11,9,10],[12,8,10],[.5,.5,0],.003,False)
    assert q2==q and d2==[0]*3 and f2==[0]*3
    q3,c3,d3,f3,*_=step(q2,c2,[12,8,10],[12,8,10],[0,0,0],.003,True)
    assert q3==[0]*3 and c3>0 and sum(f3)>0
    q4,c4,d4,f4,*_=step(q3,c3,[12,8,10],[12,8,10],[.5,.5,0],.003,True)
    assert sum(q4)>0 and sum(f4)>0 and c4>=0
    q5,c5,d5,f5,*_=step(q4,c4,[12,8,10],[12,8,10],[.2,.3,.1],.003,True)
    assert c5>0
    return {'passed':5,'tests':['self_financing_entry','off_cycle_constant_shares','off_cycle_gate_liquidation','off_cycle_gate_reentry','scheduled_base_rebalance'],'conservation_tolerance':1e-7}
def writecsv(path,rows):
    with open(path,'w',newline='') as f:
        out=csv.DictWriter(f,fieldnames=list(rows[0]));out.writeheader();out.writerows(rows)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(panel,signals,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'synthetic-tests.json').write_text(json.dumps(tests(),indent=2))
    rows=list(csv.DictReader(open(panel))); price={r['date_utc']:r for r in rows}; prev={rows[i]['date_utc']:rows[i-1] for i in range(1,len(rows))}
    groups=defaultdict(list)
    for r in csv.DictReader(open(signals)):
        if truth(r['is_test']): groups[(r['fold_id'],r['variant'])].append(r)
    daily=[]; account=[]; agg=[]
    for (fold,variant),rs in sorted(groups.items()):
      rs.sort(key=lambda r:r['date_utc'])
      for fee in (0.,.003,.006):
        q=[0.]*3;cash=2500.;reserve=2500.;oldgate=None;equity=5000.;peak=equity;mdd=0.;fees=0.;gross=0.;turn=0.;capdays=0;maxvenue=2500.;maxerr=0.;gateevents=0
        for i,r in enumerate(rs):
            date=r['date_utc'];a=prev[date];b=price[date]
            p0=[float(a[s+'_close']) for s in S];p1=[float(b[s+'_close']) for s in S]
            gate=int(float(r['gate_lagged'])); base=truth(r['base_rebalance_day']); change=oldgate is not None and gate!=oldgate
            event=i==0 or base or change;gateevents+=int(change)
            weights=[float(r[s+'_weight']) for s in S]
            for j,s in enumerate(S): assert abs((p1[j]/p0[j]-1)-float(r[s+'_asset_return']))<1e-9
            oldq=q[:];oldcash=cash;before=equity
            q,cash,delta,cost,end,pnl,err=step(q,cash,p0,p1,weights,fee,event)
            equity=end+reserve;fees+=sum(cost);gross+=pnl;turn+=sum(abs(x) for x in delta)
            maxerr=max(maxerr,abs(err),abs(equity-(before+pnl-sum(cost))))
            peak=max(peak,equity);mdd=min(mdd,equity/peak-1);maxvenue=max(maxvenue,end);capdays+=int(end>2500+1e-8)
            reason='initial' if i==0 else 'gate_change' if change else 'base' if base else 'hold'
            account.append(dict(fold_id=fold,variant=variant,accounting_mode='B_frozen_shares_close_to_close_conditional',cost_side=fee,utc_date=date,venue_before=before-reserve,cash_before=oldcash,cash_after=cash,venue_value=end,reserve=reserve,total_equity=equity,gross_pnl=pnl,fee=sum(cost),trade_notional=sum(abs(x) for x in delta),rebalance=event,reason=reason,gate=gate,venue_close_breach=end>2500+1e-8,venue_ohlc_high_upper_bound=cash+sum(q[j]*float(b[s+'_high']) for j,s in enumerate(S)),conservation_error=err))
            for j,s in enumerate(S):
                daily.append(dict(fold_id=fold,variant=variant,accounting_mode='B_frozen_shares_close_to_close_conditional',cost_side=fee,utc_date=date,symbol=s,qty_before=oldq[j],price_before=p0[j],drifted_value=oldq[j]*p0[j],target_weight=weights[j],trade_qty=q[j]-oldq[j],trade_notional=delta[j],fee=cost[j],qty_after=q[j],cash_after=cash,venue_value=end,reserve=reserve,total_equity=equity,price_after=p1[j]))
            oldgate=gate
        assert maxerr<1e-7 and abs(equity-5000-gross+fees)<1e-7
        agg.append(dict(fold_id=fold,variant=variant,accounting_mode='B_frozen_shares_close_to_close_conditional',cost_side=fee,start=rs[0]['date_utc'],end=rs[-1]['date_utc'],days=len(rs),initial_equity=5000,final_equity=equity,gross_pnl=gross,costs=fees,net_pnl=equity-5000,return_pct=100*(equity/5000-1),cagr=(equity/5000)**(365/len(rs))-1,drawdown=mdd,turnover=turn,turnover_div_initial_equity=turn/5000,trade_notional=turn,peak_venue_value=maxvenue,venue_close_breach_days=capdays,gate_transition_count=gateevents,max_conservation_error=maxerr,ending_inventory_liquidation_assumption='marked, not liquidated',additional_terminal_liquidation_fee=fee*sum(q[j]*p1[j] for j in range(3)),evidence_level='conditional_simulation',input_hash=sha(panel),signals_hash=sha(signals)))
    # Single explicit adapter to A's account-level field names, no signal recomputation.
    common=[]
    for r in account:
        z=dict(r)
        z['conservation_residual']=z.pop('conservation_error')
        z['venue_close_limit_breach']=z.pop('venue_close_breach')
        z['venue_high_upper_bound']=z.pop('venue_ohlc_high_upper_bound')
        common.append(z)
    for z in agg:
        z['initial_venue']=2500.;z['initial_reserve']=2500.
        z['venue_close_limit_breach_days']=z['venue_close_breach_days']
        z['venue_2500_limit_pass']=z['venue_close_breach_days']==0
        z['max_conservation_residual']=z['max_conservation_error']
        z['hypothetical_final_liquidation_fee']=z['additional_terminal_liquidation_fee']
        z['final_equity_after_hypothetical_liquidation']=z['final_equity']-z['additional_terminal_liquidation_fee']
    writecsv(out/'daily_account.csv',daily);writecsv(out/'portfolio_daily.csv',account)
    writecsv(out/'daily_equity.csv',common)
    writecsv(out/'aggregate.csv',agg)
    (out/'aggregate.json').write_text(json.dumps(agg,indent=2))
    (out/'output-manifest.json').write_text(json.dumps({'inputs':{'panel':{'path':str(panel),'sha256':sha(panel)},'signals':{'path':str(signals),'sha256':sha(signals)}},'outputs':[{'file':p.name,'sha256':sha(p),'publish':p.suffix!='.csv'} for p in sorted(out.iterdir()) if p.is_file() and p.name!='output-manifest.json']},indent=2))
    print(json.dumps({'runs':len(agg),'rows':len(account),'max_conservation_error':max(x['max_conservation_error'] for x in agg)},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--panel',required=True);p.add_argument('--signals',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.panel,a.signals,a.out)
