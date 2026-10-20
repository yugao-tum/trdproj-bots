#!/usr/bin/env python3
"""Read-only attribution, independent of A/B engine functions. No network."""
import argparse, json, hashlib
from pathlib import Path
import pandas as pd
import numpy as np

def run(base,out):
 out.mkdir(parents=True,exist_ok=True)
 sp=base/'02-frozen-signals/output/signals.csv'; ap=base/'03-daily-target-cash/output'; bp=base/'04-frozen-shares-cash/output'
 s=pd.read_csv(sp); a=pd.read_csv(ap/'daily_equity.csv'); b=pd.read_csv(bp/'portfolio_daily.csv'); assets=pd.read_csv(ap/'daily_account.csv'); aa=pd.read_csv(ap/'aggregate.csv'); ba=pd.read_csv(bp/'aggregate.csv')
 original=pd.read_csv(base/'02-frozen-signals/output/original_returns.csv')
 max_o=0.; summaries=[]; first=[]; daily=[]; categorized=[]
 for (fold,var),full in s.groupby(['fold_id','variant'],sort=True):
  full=full.sort_values('date_utc').copy(); w=full[[x+'_weight' for x in ('BTC','ETH','SOL')]].to_numpy(); rr=full[[x+'_asset_return' for x in ('BTC','ETH','SOL')]].to_numpy()
  calcg=(w*rr).sum(axis=1); calct=np.r_[0.,np.abs(np.diff(w,axis=0)).sum(axis=1)]
  assert np.max(np.abs(calcg-full.gross_return))<1e-12
  assert np.max(np.abs(calct-full.original_turnover))<1e-12
  rs=full[full.is_test].reset_index(drop=True)
  for cost in [0.,.003,.006]:
   A=a[(a.fold_id==fold)&(a.variant==var)&(a.cost_side==cost)].sort_values('utc_date').reset_index(drop=True)
   B=b[(b.fold_id==fold)&(b.variant==var)&(b.cost_side==cost)].sort_values('utc_date').reset_index(drop=True)
   assert list(A.utc_date)==list(B.utc_date)==list(rs.date_utc)
   AS=assets[(assets.fold_id==fold)&(assets.variant==var)&(assets.cost_side==cost)]
   ov=2500.; contributions={k:0. for k in ['entry_vs_warmup','drift_vs_target_delta','self_financing_notional','fee_before_return']}; priorA=2500.; local=[]
   for i,r in rs.iterrows():
    ar=A.iloc[i];br=B.iloc[i];g=float(r.gross_return);t=float(r.original_turnover);fac=1+g-cost*t
    aq=AS[AS.utc_date==r.date_utc]
    ideal=sum(abs(priorA*aq.target_weight-aq.drifted_value)); actual=ar.trade_notional
    inc={k:0. for k in contributions};inc['entry_vs_warmup' if i==0 else 'drift_vs_target_delta']=cost*(priorA*t-ideal);inc['self_financing_notional']=cost*(ideal-actual);inc['fee_before_return']=-ar.fee*g
    for k in contributions:contributions[k]=contributions[k]*fac+inc[k]
    prevO=ov;ov*=fac
    assert abs(ar.venue_value-ov-sum(contributions.values()))<1e-7
    assert abs(ar.gross_pnl-(priorA-ar.fee)*g)<1e-7
    assert abs(ar.fee-cost*actual)<1e-7
    row=dict(fold_id=fold,variant=var,cost_side=cost,date_utc=r.date_utc,O_total=2500+ov,A_total=ar.total_equity,B_total=br.total_equity,A_minus_O=ar.venue_value-ov,B_minus_A=br.total_equity-ar.total_equity,B_reason=br.reason,A_turnover=actual,B_turnover=br.trade_notional,O_target_turnover_dollars=prevO*t,A_prefee_ideal_turnover=ideal,gross_B_minus_A=br.gross_pnl-ar.gross_pnl,fee_A_minus_B=ar.fee-br.fee)
    local.append(row);priorA=ar.venue_value
   daily.extend(local)
   for pair in ['A_minus_O','B_minus_A']:
    hit=next((x for x in local if abs(x[pair])>1e-8),None)
    first.append(dict(fold_id=fold,variant=var,cost_side=cost,pair=pair,first_difference=hit))
   if cost==0: assert max(abs(x['A_minus_O']) for x in local)<1e-7
   for reason,df in pd.DataFrame(local).groupby('B_reason'):
    categorized.append(dict(fold_id=fold,variant=var,cost_side=cost,B_reason=reason,days=len(df),gross_B_minus_A=df.gross_B_minus_A.sum(),fee_A_minus_B=df.fee_A_minus_B.sum(),net_difference_contribution=(df.gross_B_minus_A+df.fee_A_minus_B).sum(),A_turnover=df.A_turnover.sum(),B_turnover=df.B_turnover.sum()))
   assert abs(sum(x['gross_B_minus_A']+x['fee_A_minus_B'] for x in local)-(B.iloc[-1].total_equity-A.iloc[-1].total_equity))<1e-7
   old=original[(original.fold_id==fold)&(original.variant==var)&(original.fee_per_side==cost)&(original.is_test)]
   if len(old):
    err=abs(2500*float(old.iloc[-1].test_nav)-ov);max_o=max(max_o,err);assert err<1e-7
   ag=aa[(aa.fold_id==fold)&(aa.variant==var)&(aa.cost_side==cost)].iloc[0];bg=ba[(ba.fold_id==fold)&(ba.variant==var)&(ba.cost_side==cost)].iloc[0]
   summaries.append(dict(fold_id=fold,variant=var,cost_side=cost,days=len(rs),O_target_signal_return=ov/2500-1,O_capital_conditional_return=ov/5000-.5,A_return=ar.total_equity/5000-1,B_return=br.total_equity/5000-1,O_final=2500+ov,A_final=ar.total_equity,B_final=br.total_equity,A_minus_O=ar.venue_value-ov,B_minus_A=br.total_equity-ar.total_equity,**contributions,A_fee=A.fee.sum(),B_fee=B.fee.sum(),A_terminal_fee=ag.hypothetical_final_liquidation_fee,B_terminal_fee=bg.hypothetical_final_liquidation_fee,A_cap_breach_days=int(ag.venue_close_limit_breach_days),B_cap_breach_days=int(bg.venue_close_limit_breach_days)))
 df=pd.DataFrame(summaries)
 for idx,row in df.iterrows():
  zero=df[(df.fold_id==row.fold_id)&(df.variant==row.variant)&(df.cost_side==0)].iloc[0]
  for m in ['A','B']:
   drag=zero[m+'_final']-row[m+'_final'];df.loc[idx,m+'_total_cost_path_drag']=drag;df.loc[idx,m+'_lost_gross_pnl_from_fee_path']=drag-row[m+'_fee']
 df.to_csv(out/'aggregate.csv',index=False);(out/'aggregate.json').write_text(df.to_json(orient='records',indent=2))
 pd.DataFrame(daily).to_csv(out/'daily_attribution_local_only.csv',index=False)
 pd.DataFrame(categorized).to_csv(out/'event_attribution.csv',index=False)
 (out/'first_differences.json').write_text(json.dumps(first,indent=2))
 inputs=[sp,ap/'daily_equity.csv',ap/'daily_account.csv',bp/'portfolio_daily.csv',ap/'aggregate.csv',bp/'aggregate.csv',base/'02-frozen-signals/output/original_returns.csv']
 (out/'manifest.json').write_text(json.dumps({'inputs':{str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'runs':len(df),'daily_rows':len(daily),'original_O_max_dollar_residual':max_o,'zero_fee_A_equals_O':True,'A_O_exact_propagated_attribution':True,'A_B_exact_gross_minus_fee_attribution':True,'tolerance_dollars':1e-7,'daily_attribution_publish':False,'evidence':'conditional simulation, not real execution or qualified result'},indent=2))
 print(df[df.variant.isin(['VM_base','VM_BTC_SMA50'])][['fold_id','variant','cost_side','A_minus_O','B_minus_A','A_return','B_return']].to_string(index=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.base,a.out)
