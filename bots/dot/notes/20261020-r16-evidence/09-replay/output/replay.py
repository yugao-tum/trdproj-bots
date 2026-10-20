#!/usr/bin/env python3
"""Offline r16 replay. Inputs read-only; target must not exist. Never executes downloader."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
FILES=['01-freeze-inputs/output/freeze_inputs.py','02-frozen-signals/reproduce_frozen.py','03-daily-target-cash/output/daily_target_cash.py','04-frozen-shares-cash/output/ledger_b.py','05-difference-attribution/output/attribute.py','06-risk-events/output/risk_events.py']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def independent(base,out):
 panel=pd.read_csv(base/'01-freeze-inputs/output/panel_utc.csv').set_index('date_utc');prev=panel.shift(1)
 sig=pd.read_csv(base/'02-frozen-signals/output/signals.csv'); sig=sig[sig.is_test].set_index(['fold_id','variant','date_utc'])
 sample=[];capital=[];maximum=0.;nchecks=0
 frames={m:pd.read_csv(base/f'{f}/output/daily_equity.csv') for m,f in [('A','03-daily-target-cash'),('B','04-frozen-shares-cash')]}
 for mode,folder in [('A','03-daily-target-cash'),('B','04-frozen-shares-cash')]:
  d=frames[mode];a=pd.read_csv(base/folder/'output/daily_account.csv');agg=pd.read_csv(base/folder/'output/aggregate.csv')
  other=frames['B' if mode=='A' else 'A'].set_index(['fold_id','variant','cost_side','utc_date'])
  for key,g in d.groupby(['fold_id','variant','cost_side']):
   fold,var,cost=key;g=g.sort_values('utc_date').reset_index(drop=True);s=sig.loc[(fold,var)].reindex(g.utc_date)
   ag=a[(a.fold_id==fold)&(a.variant==var)&(a.cost_side==cost)].copy()
   bydate={date:x.set_index('symbol').reindex(['BTC','ETH','SOL']) for date,x in ag.groupby('utc_date')}
   gates=s.gate_lagged.to_numpy();flips=np.flatnonzero(gates[1:]!=gates[:-1])+1
   drift=[];fd=[]
   for i,r in g.iterrows():
    x=bydate[r.utc_date];v=x.qty_before.to_numpy()*x.price_before.to_numpy();w=x.target_weight.to_numpy()
    drift.append(float(np.abs(v-r.venue_before*w).sum()))
    fd.append(abs(r.fee-other.loc[(*key,r.utc_date),'fee']))
   selected={0:['first'],len(g)-1:['last']}
   for label,i in [('max_drift',int(np.argmax(drift))),('max_fee_difference',int(np.argmax(fd))),('peak_venue',int(g.venue_value.argmax()))]+([('first_gate_flip',int(flips[0]))] if len(flips) else []):selected.setdefault(i,[]).append(label)
   for i,why in sorted(selected.items()):
    r=g.iloc[i];x=bydate[r.utc_date];coins=['BTC','ETH','SOL'];p0=prev.loc[r.utc_date,[c+'_close' for c in coins]].to_numpy(float);p1=panel.loc[r.utc_date,[c+'_close' for c in coins]].to_numpy(float)
    q0=x.qty_before.to_numpy();q1=x.qty_after.to_numpy();t=(q1-q0)*p0;fees=cost*np.abs(t);previous=g.iloc[i-1].total_equity if i else 5000.
    checks={'price':np.max(np.abs(x.price_before-p0)),'quantity':np.max(np.abs(q1-q0-x.trade_qty)),'trade_notional':np.max(np.abs(t-x.trade_notional)),'fee':np.max(np.abs(fees-x.fee)),'fee_total':abs(fees.sum()-r.fee),'cash':abs(r.cash_after-(r.cash_before-t.sum()-fees.sum())),'venue':abs(r.venue_value-r.cash_after-(q1*p1).sum()),'reserve':abs(r.reserve-2500),'total':abs(r.total_equity-r.venue_value-2500),'pnl':abs(r.gross_pnl-(q1*(p1-p0)).sum()),'conservation':abs(r.total_equity-previous-(q1*(p1-p0)).sum()+fees.sum())}
    if i:checks['cash_continuity']=abs(r.cash_before-g.iloc[i-1].cash_after);checks['qty_continuity']=np.max(np.abs(q0-bydate[g.iloc[i-1].utc_date].qty_after.to_numpy()))
    else:checks['initial_cash']=abs(r.cash_before-2500);checks['initial_qty']=np.max(abs(q0))
    event=mode=='A' or i==0 or bool(s.iloc[i].base_rebalance_day) or gates[i]!=gates[i-1]
    if event:checks['self_financing_target']=np.max(np.abs(q1*p0-x.target_weight.to_numpy()*(r.venue_before-fees.sum())))
    else:checks['held_qty']=np.max(np.abs(q1-q0))
    err=float(max(checks.values()));assert err<1e-7,(mode,key,i,checks);assert r.cash_after>=-1e-8 and min(q1)>=-1e-10
    maximum=max(maximum,err);nchecks+=len(checks);sample.append(dict(mode=mode,fold_id=fold,variant=var,cost_side=cost,date=r.utc_date,selection=why,checks=len(checks),max_absolute_residual=err))
   z=agg[(agg.fold_id==fold)&(agg.variant==var)&(agg.cost_side==cost)].iloc[0];final=g.iloc[-1].total_equity;peak=max(2500.,g.venue_value.max());breaches=int((g.venue_value>2500+1e-8).sum());cagr=(final/5000)**(365/len(g))-1
   assert abs(z.initial_equity-5000)<1e-10 and abs(z.final_equity-final)<1e-7 and abs(z.cagr-cagr)<1e-10 and abs(z.costs-g.fee.sum())<1e-7 and abs(z.peak_venue_value-peak)<1e-7
   assert int(z.venue_close_limit_breach_days)==breaches
   capital.append(dict(mode=mode,fold_id=fold,variant=var,cost_side=cost,days=len(g),total_budget=5000,initial_venue=2500,reserve=2500,final_equity=final,net_return=final/5000-1,cagr=cagr,costs=float(g.fee.sum()),peak_venue=peak,close_limit_breach_days=breaches,limit_pass=breaches==0))
 pd.DataFrame(capital).to_csv(out/'capital_boundaries.csv',index=False)
 (out/'sample_checks.json').write_text(json.dumps(sample,indent=2)+'\n')
 return {'runs':len(capital),'sampled_days':len(sample),'independent_identities':nchecks,'max_residual':maximum,'all_pass':True,'dynamic_venue_limit_failing_runs':sum(not x['limit_pass'] for x in capital),'next_open_verified':False,'evidence':'conditional same-close simulation, not actual execution or qualification'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args();base=args.base.resolve();out=args.out.resolve()
 assert not out.exists(),'Refuse existing output';out.mkdir(parents=True)
 protected=[x for folder in ['01-freeze-inputs','02-frozen-signals','03-daily-target-cash','04-frozen-shares-cash','05-difference-attribution','06-risk-events'] for x in (base/folder).rglob('*') if x.is_file() and '__pycache__' not in str(x)]
 hashes={str(x):sha(x) for x in protected};staging=out/'local_replay';staging.mkdir()
 for f in FILES:
  dest=staging/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/f,dest)
 (staging/'02-frozen-signals/output').mkdir()
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');commands=[]
 def run(f,*argv):
  cmd=[sys.executable,str(staging/f),*map(str,argv)];r=subprocess.run(cmd,capture_output=True,text=True,env=env);commands.append({'stage':f,'returncode':r.returncode,'stdout':r.stdout[-2500:],'stderr':r.stderr[-2500:]});assert r.returncode==0,commands[-1]
 run(FILES[0]);run(FILES[1]);panel=staging/'01-freeze-inputs/output/panel_utc.csv';signals=staging/'02-frozen-signals/output/signals.csv'
 for f in FILES[2:4]:run(f,'--panel',panel,'--signals',signals,'--out',(staging/f).parent)
 for f in FILES[4:]:run(f,'--base',staging,'--out',(staging/f).parent)
 result=independent(staging,out)
 assert all(sha(Path(k))==v for k,v in hashes.items()),'Frozen input changed during replay'
 checks={f:sha(base/f)==sha(staging/f) for f in ['01-freeze-inputs/output/panel_utc.csv','02-frozen-signals/output/signals.csv','03-daily-target-cash/output/daily_account.csv','04-frozen-shares-cash/output/daily_account.csv']};assert all(checks.values()),checks
 result.update(source_files_unchanged=len(hashes),deterministic_file_checks=checks,script_hashes={f:hashes[str(base/f)] for f in FILES})
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(out/'execution_log.json').write_text(json.dumps(commands,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
