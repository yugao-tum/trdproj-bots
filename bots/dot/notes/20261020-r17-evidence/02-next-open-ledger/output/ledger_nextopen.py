#!/usr/bin/env python3
"""r17 preregistered conditional next-open continuous B account; no network."""
import csv,json,hashlib,argparse,datetime,math
from pathlib import Path
S=('BTC','ETH','SOL')
def truth(x): return str(x).lower() in ('true','1','1.0')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def writecsv(p,rs):
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def rebalance(q,cash,prices,weights,fee):
    assert all(math.isfinite(v) and v>=0 for v in q+weights+[cash,fee])
    assert all(math.isfinite(v) and v>0 for v in prices)
    assert sum(weights)<=1+1e-12 and fee<1
    values=[a*b for a,b in zip(q,prices)];equity=cash+sum(values)
    lo,hi=0.,equity
    # Unique root Epost + fee*sum(abs(w*Epost-oldvalue)) = Epre.
    for _ in range(100):
        mid=(lo+hi)/2
        if mid+fee*sum(abs(w*mid-v) for w,v in zip(weights,values))>equity: hi=mid
        else: lo=mid
    post=(lo+hi)/2
    nq=[post*w/p for w,p in zip(weights,prices)]
    delta=[(a-b)*p for a,b,p in zip(nq,q,prices)]
    fees=[fee*abs(d) for d in delta]
    ncash=cash-sum(delta)-sum(fees)
    assert ncash>=-1e-9
    # Numerical roundoff only; record raw residual, never economic funding.
    ncash=max(0.,ncash)
    assert abs(ncash+sum(a*b for a,b in zip(nq,prices))-(equity-sum(fees)))<1e-8
    return nq,ncash,delta,fees

def simulate(rows,initial,reserve,fee,scenario):
    q=[0.,0.,0.];cash=float(initial);prevclose=None;oldgate=None
    equity=float(initial+reserve);accounts=[];trades=[]
    for i,r in enumerate(rows):
        d=r['date_utc'];op=[float(r[s+'_open']) for s in S];cl=[float(r[s+'_close']) for s in S];hi=[float(r[s+'_high']) for s in S]
        assert all(h>=max(o,c) for h,o,c in zip(hi,op,cl))
        gate=int(float(r['gate_lagged']));w=[float(r[s+'_weight']) for s in S]
        assert gate in (0,1) and (gate or sum(w)==0)
        oldq=q[:];oldcash=cash;pre=cash+sum(a*b for a,b in zip(q,op));before=equity
        overnight=0. if prevclose is None else sum(a*(b-c) for a,b,c in zip(q,op,prevclose))
        changed=oldgate is not None and gate!=oldgate
        event=i==0 or truth(r['base_rebalance_day']) or changed
        reason='initial' if i==0 else 'gate_change' if changed else 'base' if event else 'hold'
        if event:q,cash,delta,fees=rebalance(q,cash,op,w,fee)
        else:delta,fees=[0.]*3,[0.]*3
        assert event or q==oldq
        post=cash+sum(a*b for a,b in zip(q,op))
        for j,s in enumerate(S):
            if delta[j]!=0:
                trades.append(dict(scenario_id=scenario,date_utc=d,event_phase='open',symbol=s,qty_before=oldq[j],qty_delta=q[j]-oldq[j],qty_after=q[j],reference_price=op[j],signed_notional=delta[j],fee=fees[j],cash_before_event=oldcash,cash_after_event=cash))
        intraday=sum(a*(b-c) for a,b,c in zip(q,cl,op));vc=cash+sum(a*b for a,b in zip(q,cl));upper=cash+sum(a*b for a,b in zip(q,hi))
        termfees=0.;termnotional=0.;cashafteropen=cash;qafter=q[:]
        if i==len(rows)-1:
            termcash=cash;notionals=[a*b for a,b in zip(q,cl)];termfees=fee*sum(notionals);termnotional=sum(notionals);cash+=termnotional-termfees
            for j,s in enumerate(S):
                if q[j]!=0:trades.append(dict(scenario_id=scenario,date_utc=d,event_phase='terminal_close',symbol=s,qty_before=q[j],qty_delta=-q[j],qty_after=0.,reference_price=cl[j],signed_notional=-notionals[j],fee=fee*notionals[j],cash_before_event=termcash,cash_after_event=cash))
            q=[0.,0.,0.]
        equity=cash+sum(a*b for a,b in zip(q,cl))+reserve
        err=equity-(before+overnight+intraday-sum(fees)-termfees)
        assert abs(err)<1e-7 and cash>=0 and min(q)>=0
        row=dict(scenario_id=scenario,date_utc=d,initial_venue=initial,reserve=reserve,cost_side=fee,gate=gate,reason=reason,venue_cash_before_open=oldcash,venue_cash_after_open=cashafteropen)
        for j,s in enumerate(S):row['qty_'+s+'_before']=oldq[j];row['qty_'+s+'_after']=qafter[j];row['qty_'+s+'_end']=q[j]
        row.update(venue_cash_end=cash,venue_pretrade_open=pre,venue_posttrade_open=post,venue_close_before_terminal=vc,venue_high_upper_bound=upper,total_equity_before_terminal=vc+reserve,total_equity_end=equity,overnight_pnl=overnight,intraday_pnl=intraday,open_fees=sum(fees),terminal_fees=termfees,trade_notional=sum(abs(x) for x in delta)+termnotional,conservation_error=err)
        accounts.append(row);prevclose=cl;oldgate=gate
    peak=initial+reserve;mdd=0.
    for r in accounts:peak=max(peak,r['total_equity_end']);mdd=min(mdd,r['total_equity_end']/peak-1)
    obs=['venue_pretrade_open','venue_posttrade_open','venue_close_before_terminal']
    breach=[r['date_utc'] for r in accounts if max(r[k] for k in obs)>2500+1e-8]
    bound=[r['date_utc'] for r in accounts if r['venue_high_upper_bound']>2500+1e-8]
    totalfees=sum(t['fee'] for t in trades);turn=sum(abs(t['signed_notional']) for t in trades)
    assert abs(equity-(initial+reserve+sum(r['overnight_pnl']+r['intraday_pnl'] for r in accounts)-totalfees))<1e-7
    metrics=dict(scenario_id=scenario,variant='VM_BTC_SMA50',evidence_level='conditional_simulation',start=rows[0]['date_utc'],end=rows[-1]['date_utc'],days=len(rows),initial_venue=initial,reserve=reserve,initial_equity=initial+reserve,cost_side=fee,final_equity=equity,total_return=equity/(initial+reserve)-1,cagr=(equity/(initial+reserve))**(365/len(rows))-1,mdd=mdd,fees=totalfees,open_fees=sum(r['open_fees'] for r in accounts),terminal_fees=sum(r['terminal_fees'] for r in accounts),turnover_notional=turn,turnover_div_initial_equity=turn/(initial+reserve),max_conservation_error=max(abs(r['conservation_error']) for r in accounts),max_observed_venue=max(r[k] for r in accounts for k in obs),max_high_upper_bound=max(r['venue_high_upper_bound'] for r in accounts),observable_breach_days=len(breach),first_observable_breach=breach[0] if breach else None,upper_bound_exceed_days=len(bound),capital_status='observable_breach' if breach else 'not_conservatively_certified' if bound else 'historical_conditional_upper_bound_within_limit',terminal_inventory=q,rebalance_days=sum(r['reason']!='hold' for r in accounts),gate_change_days=sum(r['reason']=='gate_change' for r in accounts))
    return accounts,trades,metrics

def tests():
    def row(i,op,cl,gate=1,base=False):
        r=dict(date_utc=f'2024-01-{i:02d}',gate_lagged=gate,base_rebalance_day=base)
        for s in S:r.update({s+'_open':op,s+'_close':cl,s+'_high':max(op,cl),s+'_weight':float(gate and s=='BTC')})
        return r
    passed=[]
    for initial in (1250.,2500.):
      for fee in (.003,.006):
        q,c,d,f=rebalance([0.]*3,initial,[10.]*3,[1.,0.,0.],fee)
        assert abs(q[0]-initial/(1+fee)/10)<1e-10 and c<1e-9
        a,t,m=simulate([row(1,10,11),row(2,12,13),row(3,14,14,0),row(4,15,16,1),row(5,17,18)],initial,5000-initial,fee,'synthetic')
        assert a[1]['reason']=='hold' and a[1]['open_fees']==0 and a[1]['qty_BTC_after']==a[0]['qty_BTC_after']
        assert abs(a[1]['overnight_pnl']-q[0])<1e-8 and abs(a[1]['intraday_pnl']-q[0])<1e-8
        assert a[2]['qty_BTC_after']==0 and a[3]['qty_BTC_after']>0
        assert a[-1]['terminal_fees']>0 and m['terminal_inventory']==[0.]*3
        expected=initial/(1+fee)/10*14*(1-fee)/(1+fee)/15*18*(1-fee)+5000-initial
        assert abs(m['final_equity']-expected)<1e-8
        passed.append({'initial_venue':initial,'fee':fee,'hand_computed_final_equity':expected,'actual':m['final_equity'],'passed':True})
    # A partial-weight rebalance charges signed buys AND sells and preserves cash.
    nq,c,d,f=rebalance([10.,5.,0.],100.,[10.]*3,[.2,.5,0.],.006)
    assert d[0]<0<d[1] and c>0 and abs(sum(f)-.006*sum(abs(x) for x in d))<1e-12
    return dict(passed=True,parameter_cases=passed,coverage=['fee funded entry','unchanged shares/zero hold turnover','overnight gap versus intraday PnL','off-cycle gate exit and reentry','charged terminal liquidation/zero inventory','two capital allocations/two fees','mixed signed buy/sell partial cash'],tests_completed_before_actual_run=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--signals');p.add_argument('--panel');p.add_argument('--opens');p.add_argument('--out',default=str(Path(__file__).parent));p.add_argument('--test-only',action='store_true');a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    dump(out/'synthetic-tests.json',tests())
    if a.test_only: print('Synthetic tests passed');return
    inputs={k:{'path':v,'sha256':sha(v)} for k,v in [('signals',a.signals),('panel',a.panel),('opens',a.opens)]}
    assert inputs['signals']['sha256']=='44b7657912ee8cde461a3d0eec1eb8b4079a564b5b104afd1dc2ca54a70090c0'
    causal=Path(a.signals).with_name('causal-tests.json');assert json.loads(causal.read_text())['status']=='PASS'
    inputs['signal_causal_tests']={'path':str(causal),'sha256':sha(causal)}
    assert inputs['panel']['sha256']=='a3b601644697f778990fcfdcc2ff1143140d5373c33d871ff81536d493891f79'
    assert inputs['opens']['sha256']=='ad044b15871eea467cb8750efbb3855f22fd65addce3b2424f67a57fe772183a'
    panel={r['date_utc'][:10]:r for r in csv.DictReader(open(a.panel))};opens={r['date_utc'][:10]:r for r in csv.DictReader(open(a.opens))}
    signals=[r for r in csv.DictReader(open(a.signals)) if truth(r['is_test'])];
    for r in signals:
        for k in ('date_utc','decision_date_utc','execution_date_utc'):
            dt=datetime.datetime.fromisoformat(r[k].replace('Z','+00:00'))
            assert dt.hour==dt.minute==dt.second==0 and (dt.utcoffset() is None or dt.utcoffset()==datetime.timedelta(0))
            r[k]=dt.date().isoformat()
    signals.sort(key=lambda r:r['date_utc'])
    assert len(signals)==1004 and signals[0]['date_utc']=='2024-01-01' and signals[-1]['date_utc']=='2026-09-30'
    rows=[]
    for i,r in enumerate(signals):
        d=datetime.date.fromisoformat(r['date_utc']);assert r['execution_date_utc']==str(d) and r['decision_date_utc']==str(d-datetime.timedelta(days=1));assert d==datetime.date(2024,1,1)+datetime.timedelta(days=i)
        assert r['variant']=='VM_BTC_SMA50';rows.append({**panel[str(d)],**opens[str(d)],**r})
    accounts=[];trades=[];metrics=[]
    for name,initial in [('original_2500',2500.),('buffer_1250',1250.)]:
      for fee in (.003,.006):
        ac,tr,me=simulate(rows,initial,5000-initial,fee,name+'_fee'+str(fee));accounts+=ac;trades+=tr;metrics.append(me)
    writecsv(out/'accounts.csv',accounts);writecsv(out/'trades.csv',trades);dump(out/'metrics.json',metrics)
    dump(out/'manifest.json',dict(actual_model='unknown',inputs=inputs,code_sha256=sha(__file__),outputs={f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name not in ('manifest.json',Path(__file__).name)},historical_data_only=True,new_mechanisms=0))
    print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
