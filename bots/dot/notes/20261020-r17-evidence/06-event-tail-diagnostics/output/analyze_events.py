from pathlib import Path
import json, hashlib
import pandas as pd
import numpy as np
O=Path(__file__).resolve().parent; R=O.parent.parent
SP=R/'01-continuous-signals/output/signals.csv'; AP=R/'02-next-open-ledger/output/accounts.csv'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
s=pd.read_csv(SP); s=s[s.is_test.astype(str).str.lower()=='true'].copy().reset_index(drop=True)
s['date_utc']=s.date_utc.str[:10]; assert len(s)==1004 and s.date_utc.nunique()==1004
ids=[]; n=0; prev=0
for g in s.gate_lagged.astype(int):
 if g and not prev:n+=1
 ids.append(n if g or prev else 0); prev=g
s['event_id']=ids
s[['date_utc','gate_lagged','event_id']].to_csv(O/'event_map.csv',index=False)
events=[]
for eid,g in s[s.event_id>0].groupby('event_id'):
 on=g[g.gate_lagged==1]
 events.append(dict(event_id=int(eid),gate_start=on.date_utc.iloc[0],last_gate_on=on.date_utc.iloc[-1],pnl_end=g.date_utc.iloc[-1],gate_days=len(on),attribution_days=len(g),cross_year=on.date_utc.iloc[0][:4]!=on.date_utc.iloc[-1][:4]))
pd.DataFrame(events).to_csv(O/'unique_events.csv',index=False)
base={'classification':'conditional_simulation','unique_gate_segments':n,'shared_month_clusters':int(pd.to_datetime(s.date_utc).dt.to_period('M').nunique()),'statistical_independence':'not_established','new_mechanisms':0,'cross_year_segments':sum(x['cross_year'] for x in events)}
inputs={str(SP):sha(SP)}
if not AP.exists():
 dump(O/'event_summary.json',dict(base,ledger_status='pending')); print(json.dumps(base)); raise SystemExit(0)
a=pd.read_csv(AP); inputs[str(AP)]=sha(AP); a['date_utc']=a.date_utc.str[:10]; results=[]; event_rows=[]; years=[]
for sid,x in a.groupby('scenario_id',sort=True):
 x=x.sort_values('date_utc').merge(s[['date_utc','event_id']],on='date_utc',validate='one_to_one'); assert len(x)==1004
 eq=x.total_equity_end.to_numpy(); before=np.r_[5000.,eq[:-1]]; pnl=eq-before; ret=eq/before-1; x['pnl']=pnl; x['daily_return']=ret
 assert np.max(np.abs(pnl-(x.overnight_pnl+x.intraday_pnl-x.open_fees-x.terminal_fees)))<1e-7
 ep=x.groupby('event_id').pnl.sum(); assert abs(ep.get(0,0))<1e-7
 for eid,v in ep.items():
  if eid:event_rows.append(dict(scenario_id=sid,event_id=int(eid),pnl=float(v)))
 pos=np.sort(pnl[pnl>0])[::-1]; epos=np.sort(ep[ep>0].to_numpy())[::-1]; net=float(eq[-1]-5000)
 path=np.r_[5000.,eq]; peaks=np.maximum.accumulate(path); dd=path/peaks-1; trough=int(np.argmin(dd)); peak=int(np.argmax(path[:trough+1])); rec=np.where(path[trough:]>=path[peak])[0]
 date=lambda i: '2024-01-01 pre-open' if i==0 else x.date_utc.iloc[i-1]
 z=dict(scenario_id=sid,final_equity=float(eq[-1]),total_return=net/5000,cagr=float((eq[-1]/5000)**(365/1004)-1),positive_daily_pnl_sum=float(pos.sum()),top10_positive_day_share=float(pos[:10].sum()/pos.sum()) if len(pos) else None,positive_event_pnl_sum=float(epos.sum()),top1_positive_event_share=float(epos[:1].sum()/epos.sum()) if len(epos) else None,top3_positive_event_share=float(epos[:3].sum()/epos.sum()) if len(epos) else None,top1_event_net_pnl_share=float(epos[0]/net) if len(epos) and net else None,best_event_id=int(ep.idxmax()),best_event_pnl=float(ep.max()),net_pnl_without_best_event_attribution_only=net-float(ep.max()),mdd=float(dd[trough]),peak_date=date(peak),trough_date=date(trough),recovery_date=date(trough+int(rec[0])) if len(rec) else None,positive_events=int((ep>0).sum()),negative_events=int((ep<0).sum()),flat_events=int((ep.drop(index=0,errors='ignore')==0).sum()),attribution_reconciliation_error=float(ep.sum()-net))
 z['gate_segments_with_nonzero_inventory']=int(x.loc[x[['qty_BTC_after','qty_ETH_after','qty_SOL_after']].abs().sum(axis=1)>1e-12,'event_id'].nunique())
 results.append(z)
 for yr,g in x.groupby(x.date_utc.str[:4]):
  first=int(g.index[0]); start=before[first]; end=float(g.total_equity_end.iloc[-1]); years.append(dict(scenario_id=sid,year=yr,days=len(g),start_equity=float(start),end_equity=end,account_period_return=end/start-1,pnl_over_initial_5000=(end-start)/5000))
pd.DataFrame(event_rows).to_csv(O/'event_pnl.csv',index=False); pd.DataFrame(years).to_csv(O/'year_metrics.csv',index=False)
dump(O/'event_summary.json',dict(base,ledger_status='complete',scenarios=results))
BP=R/'05-same-budget-benchmarks/output/accounts.csv'
b=pd.read_csv(BP); inputs[str(BP)]=sha(BP); b['date_utc']=b.date_utc.str[:10]; correlations=[]
for sid,x in a.groupby('scenario_id'):
 x=x.sort_values('date_utc'); v=float(x.initial_venue.iloc[0]); c=float(x.cost_side.iloc[0]); sr=x.total_equity_end.to_numpy()/np.r_[5000.,x.total_equity_end.to_numpy()[:-1]]-1
 for bid,y in b.groupby('scenario_id'):
  if float(y.initial_venue.iloc[0])!=v or float(y.cost_side.iloc[0])!=c:continue
  y=y.sort_values('date_utc'); assert list(x.date_utc)==list(y.date_utc)
  br=y.total_equity_end.to_numpy()/np.r_[5000.,y.total_equity_end.to_numpy()[:-1]]-1
  correlations.append(dict(scenario_id=sid,benchmark_id=bid,days=len(y),daily_return_pearson=float(np.corrcoef(sr,br)[0,1]) if np.std(br)>1e-15 else None,qualification='diagnostic_only; independence_not_established'))
dump(O/'benchmark_correlations.json',correlations)
assert all(sha(Path(p))==h for p,h in inputs.items())
dump(O/'tests.json',{'daily_coverage_1004_each':True,'four_scenarios':len(results)==4,'pnl_cashflow_identity_tolerance':1e-7,'idle_segment_pnl_zero_tolerance':1e-7,'event_full_pnl_reconciles':all(abs(z['attribution_reconciliation_error'])<1e-7 for z in results),'source_hashes_unchanged':True,'same_budget_benchmark_pairs':len(correlations),'unique_events_not_multiplied':n})
dump(O/'manifest.json',{'model':'unknown','input_sha256':inputs,'code_sha256':sha(Path(__file__)),'output_sha256':{p.name:sha(p) for p in O.iterdir() if p.is_file() and p.name not in ['manifest.json','analyze_events.py']}})
print(json.dumps(dict(base,scenarios=results),indent=2))
