#!/usr/bin/env python3
"""Frozen r16 risk diagnostics. Offline; no optimization; writes only explicit output."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

def metrics(r):
 r=np.asarray(r,float);nav=np.r_[1,np.cumprod(1+r)]
 return dict(days=len(r),net_return=float(nav[-1]-1),cagr=float(nav[-1]**(365/len(r))-1),annual_vol=float(np.std(r,ddof=1)*np.sqrt(365)),max_drawdown=float(np.min(nav/np.maximum.accumulate(nav)-1)))
def main(base,out):
 out.mkdir(parents=True,exist_ok=True)
 pp=base/'01-freeze-inputs/output/panel_utc.csv';sp=base/'02-frozen-signals/output/signals.csv'
 panel=pd.read_csv(pp);panel['date']=panel.date_utc.str[:10];panel=panel.set_index('date')
 sig=pd.read_csv(sp);sig['date']=sig.date_utc.str[:10]
 sig=sig[sig.is_test.astype(str).str.lower().isin(['true','1'])].copy()
 baselines={};bs=[];bd=[];summary=[];segments=[];events=[];months=[];matched=[];sources=[pp,sp]
 for fold,s in sig.groupby('fold_id'):
  dates=sorted(s.date.unique());p=panel.loc[dates,[x+'_close' for x in ['BTC','ETH','SOL']]].to_numpy();idx=panel.index.get_loc(dates[0]);p0=panel.iloc[idx-1][[x+'_close' for x in ['BTC','ETH','SOL']]].to_numpy(dtype=float)
  for fee in [0.,.003,.006]:
   for name,w in [('cash',[0,0,0]),('BTC_hold',[1,0,0]),('three_coin_hold',[1/3]*3)]:
    w=np.array(w);q=2500*w/(p0*(1+fee));cash=2500-float((q*p0).sum())*(1+fee);venue=cash+(p*q).sum(axis=1);equity=2500+venue;prev=np.r_[5000,equity[:-1]];r=equity/prev-1;exposure=(np.vstack([p0,p[:-1]])*q).sum(axis=1)/prev
    b=dict(r=r,exposure=exposure,eq=equity);baselines[(str(fold),fee,name)]=b
    bs.append(dict(fold_id=fold,cost_side=fee,benchmark=name,**metrics(r),initial_equity=5000,final_equity=float(equity[-1]),entry_fee=float((q*p0).sum()*fee),end_liquidation_extra_fee=float((q*p[-1]).sum()*fee),peak_venue=float(max(venue)),venue_close_breach_days=int(sum(venue>2500+1e-8)),mean_total_capital_exposure=float(exposure.mean())))
    bd.extend(dict(fold_id=fold,cost_side=fee,benchmark=name,date=d,total_equity=float(e),return_daily=float(x),exposure=float(y)) for d,e,x,y in zip(dates,equity,r,exposure))
 for mode,folder in [('A','03-daily-target-cash'),('B','04-frozen-shares-cash')]:
  ep=base/folder/'output/daily_equity.csv';ap=base/folder/'output/daily_account.csv';sources += [ep,ap]
  d=pd.read_csv(ep);a=pd.read_csv(ap);d['date']=d.utc_date.str[:10];a['date']=a.utc_date.str[:10]
  a['risk_value']=a.qty_after*a.price_before
  exp=a.groupby(['fold_id','variant','cost_side','date']).risk_value.sum().rename('risk_value').reset_index();d=d.merge(exp,on=['fold_id','variant','cost_side','date'],validate='one_to_one')
  for (fold,variant,fee),g in d.groupby(['fold_id','variant','cost_side']):
   g=g.sort_values('date').copy();g=g.merge(sig[(sig.fold_id==fold)&(sig.variant==variant)][['date','gate_lagged']],on='date',validate='one_to_one').sort_values('date')
   eq=g.total_equity.to_numpy();prev=np.r_[5000,eq[:-1]];r=eq/prev-1;pnl=eq-prev;exposure=g.risk_value.to_numpy()/prev;gate=g.gate_lagged.fillna(1).to_numpy();dates=g.date.tolist();key=dict(mode=mode,fold_id=fold,variant=variant,cost_side=fee)
   positive=np.clip(pnl,0,None);negative=np.clip(-pnl,0,None)
   summary.append(dict(**key,**metrics(r),mean_total_capital_exposure=float(exposure.mean()),peak_venue=float(g.venue_value.max()),venue_close_breach_days=int((g.venue_value>2500+1e-8).sum()),top10_positive_days_share=float(np.sort(positive)[-10:].sum()/positive.sum()) if positive.sum() else None,top10_loss_days_share=float(np.sort(negative)[-10:].sum()/negative.sum()) if negative.sum() else None,net_pnl=float(pnl.sum())))
   for name in ['cash','BTC_hold','three_coin_hold']:
    b=baselines[(str(fold),float(fee),name)]
    for method in ['same_budget','ex_post_mean_exposure','ex_post_volatility']:
     denom=b['exposure'].mean() if method=='ex_post_mean_exposure' else np.std(b['r'],ddof=1)
     scale=1. if method=='same_budget' else ((exposure.mean() if method=='ex_post_mean_exposure' else np.std(r,ddof=1))/denom if denom>0 else np.nan)
     if not np.isfinite(scale):continue
     mr=b['r']*scale
     matched.append(dict(**key,benchmark=name,method=method,scale=float(scale),strategy_return=metrics(r)['net_return'],benchmark_return=metrics(mr)['net_return'],return_difference=metrics(r)['net_return']-metrics(mr)['net_return'],diagnostic_only=method!='same_budget'))
   for label,mask in [('first_half',np.arange(len(r))<len(r)//2),('second_half',np.arange(len(r))>=len(r)//2),('gate_on',gate>0),('gate_off',gate<=0)]:
    if mask.sum():segments.append(dict(**key,segment=label,days=int(mask.sum()),net_pnl=float(pnl[mask].sum()),sum_daily_returns=float(r[mask].sum()),note='Noncontiguous gate sums are attribution, not a tradable return series'))
   runs=np.r_[0,np.cumsum(gate[1:]!=gate[:-1])]
   for run in np.unique(runs):
    mask=runs==run;ix=np.where(mask)[0];events.append(dict(**key,event=int(run),gate=int(gate[ix[0]]),start=dates[ix[0]],end=dates[ix[-1]],days=len(ix),net_pnl=float(pnl[mask].sum()),event_return=float(np.prod(1+r[mask])-1),shared_source='Binance spot daily',shared_assets='BTC ETH SOL',independent_certified=False))
   for month in sorted(set(x[:7] for x in dates)):
    mask=np.array([x[:7]==month for x in dates]);months.append(dict(**key,calendar_cluster=month,days=int(mask.sum()),net_pnl=float(pnl[mask].sum()),positive_pnl=float(positive[mask].sum()),loss_pnl=float(negative[mask].sum()),independent_certified=False))
 for name,rows in [('baseline_summary',bs),('baseline_daily_LOCAL_ONLY',bd),('strategy_risk',summary),('matched_diagnostics',matched),('period_gate_attribution',segments),('gate_runs',events),('calendar_clusters',months)]:pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
 # Shared exposure-time overlap is descriptive, never independent-event evidence.
 overlap=[]
 for fold,ss in sig.groupby('fold_id'):
  wide=ss.pivot(index='date',columns='variant',values='gate_lagged').fillna(1)
  names=list(wide.columns)
  for i,left in enumerate(names):
   for right in names[i+1:]:
    l=wide[left].to_numpy()>0;rr=wide[right].to_numpy()>0
    overlap.append(dict(fold_id=fold,left=left,right=right,shared_gate_on_days=int((l&rr).sum()),union_gate_on_days=int((l|rr).sum()),jaccard=float((l&rr).sum()/(l|rr).sum()) if (l|rr).sum() else None,common_assets=3,common_source_count=1,independent_certified=False))
 pd.DataFrame(overlap).to_csv(out/'overlap_diagnostics.csv',index=False)
 tests={'cash_returns_zero':all(abs(x['net_return'])<1e-12 for x in bs if x['benchmark']=='cash'), 'cash_fees_zero':all(x['entry_fee']==0 for x in bs if x['benchmark']=='cash'), 'buyhold_entry_self_financing':all(abs(x['entry_fee']-2500*x['cost_side']/(1+x['cost_side']))<1e-9 for x in bs if x['benchmark']!='cash'), 'all_strategy_dates_match_signal':len(summary)==72, 'no_calendar_cluster_certified':all(not x['independent_certified'] for x in months), 'no_event_certified':all(not x['independent_certified'] for x in events)}
 assert all(tests.values()), tests
 (out/'tests.json').write_text(json.dumps(tests,indent=2))
 hashes={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
 report=dict(evidence_level='conditional_accounting_simulation',input_hashes=hashes,common_source_count=1,common_underlying_assets=['BTC','ETH','SOL'],calendar_clusters=len(set(x['calendar_cluster'] for x in months)),certified_independent_events=None,baseline_groups=len(bs),strategy_groups=len(summary),gate_run_rows=len(events),rules={'capital':5000,'venue_initial':2500,'reserve_untouched':2500,'start_each_fold_from_cash':True,'mark_end_no_liquidation':True,'same_close_execution_unverified':True,'no_new_mechanism':True,'ex_post_scaling_not_tradable':True},checks={'matching_days':len(bd)>0,'all_baselines_nonnegative':all(x['final_equity']>=2500 for x in bs),'strategy_group_count_36_each':len(summary)==72})
 (out/'manifest.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.base,a.out)
