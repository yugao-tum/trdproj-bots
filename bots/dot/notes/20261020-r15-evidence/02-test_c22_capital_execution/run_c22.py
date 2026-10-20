"""Frozen C22 signals, shared capital adapter, six prespecified execution scenarios."""
import csv,hashlib,importlib.util,json,math,sys,statistics
from pathlib import Path
from datetime import datetime,timezone
O=Path(__file__).resolve().parent;R=Path('retained-inputs')
CAP=O.parent.parent/'01-build_capital_cash_benchmarks/output/capital_account.py'
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
m=load('original_spot',R/'plans/spot_screen.py');c=load('shared_capital',CAP)
def dump(name,x):(O/name).write_text(json.dumps(x,indent=2,default=str)+'\n')
def write_csv(name,rows):
 with (O/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def corr(a,b):
 return statistics.correlation(a,b) if len(a)>2 and statistics.pstdev(a)>0 and statistics.pstdev(b)>0 else None
bars,dates,quality=m.load_and_precheck(m.CSV_PATH);closes={s:[b.close for b in bars[s]] for s in m.SYMBOLS}
idx=[i for i,d in enumerate(dates) if m.SIM_START<=d<=m.SIM_END]
SCENARIOS=[('no_withdrawal',False,0.,0),('optimistic',True,0.,0),('engineering_stress',True,1.,1)]
def simulate(cost,scenario,strategy):
 name,sweep,fee,delay=scenario;a=c.CapitalAccount(fee=cost,withdrawal_fee=fee,delay_opens=delay)
 rows=[];events=[];active=None;evstart=None;prev_end=5000.;gross_market=0.
 for n,i in enumerate(idx):
  d=dates[i];op={s:bars[s][i].open for s in m.SYMBOLS};cp={s:bars[s][i].close for s in m.SYMBOLS};hp={s:bars[s][i].high for s in m.SYMBOLS}
  a.begin_day(str(d),op)
  if sweep:a.sweep(op)
  if strategy=='C22' and d.weekday()==0:
   target=m.c22_target(closes,i);notional=min(1100.,.9*a.venue(op));a.rebalance(op,{target:notional} if target else {})
  elif strategy=='BTC' and n==0:a.rebalance(op,{'BTCUSDT':1100.})
  invested=any(q>1e-10 for q in a.qty.values())
  if invested and active is None: active=len(events)+1;evstart=d
  if not invested and active is not None:events.append({'episode':active,'start':str(evstart),'end':str(d),'closure':'cash signal'});active=None
  row=a.snapshot(cp,hp);row.update({'strategy':strategy,'scenario':name,'cost':cost,'episode':active or 0,'final_exit_fee':0.})
  if n==len(idx)-1:
   fees_before=a.fees;before=a.total(cp);terminal=a.liquidate_after_snapshot(cp)
   exit_fee=a.fees-fees_before;assert abs(a.total(cp)-(before-exit_fee))<1e-8
   row.update({'venue_cash':a.cash,'position_value':0.,'total_equity':a.total(cp),'net_pnl':a.total(cp)-5000,'net_liquidation_equity':a.total(cp),'trade_fees':a.fees,'daily_pnl':row['daily_pnl']-exit_fee,'final_exit_fee':exit_fee})
   if active is not None:events.append({'episode':active,'start':str(evstart),'end':str(d),'closure':'terminal liquidation'});active=None
  assert abs(row['venue_cash']+row['position_value']+row['external_cash']+row['in_transit']-row['total_equity'])<1e-7
  assert abs(row['daily_pnl']-(row['total_equity']-prev_end))<1e-7
  assert row['external_cash']>=3750.-1e-7
  assert row['venue_cash']>=-1e-7
  prev_end=row['total_equity'];rows.append(row)
 return rows,events,a
summary=[];daily=[];events_all=[];trade_all=[];transfer_all=[]
for cost in [.003,.006]:
 for sc in SCENARIOS:
  rows,events,a=simulate(cost,sc,'C22');br,be,ba=simulate(cost,sc,'BTC')
  r=rows[-1];days=len(rows);pnl=r['net_pnl'];nliquid=r['total_equity'];tradefees=a.fees;wfees=a.withdrawal_costs
  ret=[rows[0]['total_equity']/5000-1]+[b['total_equity']/p['total_equity']-1 for p,b in zip(rows,rows[1:])]
  bret=[br[0]['total_equity']/5000-1]+[b['total_equity']/p['total_equity']-1 for p,b in zip(br,br[1:])]
  market=[bars['BTCUSDT'][i].close/bars['BTCUSDT'][i-1].close-1 for i in idx]
  s={'cost':cost,'scenario':sc[0],'days':days,'pnl':pnl,'gross_mark_gain_before_all_costs':pnl+tradefees+wfees,'trading_fees':tradefees,'sweep_sale_fees':sum(t['fee'] for t in a.trades if t['reason']=='sweep'),'withdrawal_fees':wfees,'net_withdrawn':a.withdrawn,'withdrawals':len(a.transfers),'trades':len(a.trades),'cagr_total5000':(nliquid/5000)**(365/days)-1,'cagr_deployed1250':((1250+pnl)/1250)**(365/days)-1 if pnl>-1250 else None,'return_total5000':pnl/5000,'return_deployed1250':pnl/1250,'risk_episodes':len(events),'proven_independent_results':0,'btc_same_capital_pnl':br[-1]['net_pnl'],'daily_corr_btc_same_capital':corr(ret,bret),'daily_corr_btc_price':corr(ret,market),'open_breach_days':sum(x['open_breach'] for x in rows),'close_breach_days':sum(x['close_breach'] for x in rows),'high_upper_exceed_days':sum(x['high_upper_exceeds'] for x in rows),'max_open_pre':max(x['open_pre'] for x in rows),'max_open_conservative':max(x['open_pre_conservative'] for x in rows),'max_close':max(x['close_venue'] for x in rows),'max_high_upper':max(x['high_upper_venue'] for x in rows),'max_conservation_residual':max(abs(x['conservation_residual']) for x in rows),'pending_at_end':r['in_transit'],'external_at_end':r['external_cash'],'end_venue_cash':r['venue_cash'],'final_exit_fee':r['final_exit_fee']}
  s['pass_8pct_total']=s['cagr_total5000']>=.08;s['pass_3pct_total']=s['cagr_total5000']>=.03
  s['pass_3pct_deployed']=s['cagr_deployed1250'] is not None and s['cagr_deployed1250']>=.03
  summary.append(s);daily.extend(rows)
  events_all.extend(dict(e,cost=cost,scenario=sc[0]) for e in events)
  trade_all.extend(dict(t,cost=cost,scenario=sc[0]) for t in a.trades)
  transfer_all.extend(dict(t,cost=cost,scenario=sc[0]) for t in a.transfers)
for s in summary:
 base=next(x for x in summary if x['cost']==s['cost'] and x['scenario']=='no_withdrawal')
 s['pnl_difference_vs_samecapital_no_withdrawal']=s['pnl']-base['pnl']
 s['market_exposure_difference']=s['gross_mark_gain_before_all_costs']-base['gross_mark_gain_before_all_costs']
 s['trading_fee_difference']=s['trading_fees']-base['trading_fees']
 assert abs(s['pnl_difference_vs_samecapital_no_withdrawal']-(s['market_exposure_difference']-s['trading_fee_difference']-s['withdrawal_fees']))<1e-7
write_csv('summary.csv',summary);dump('summary.json',summary);write_csv('daily-accounting.csv',daily);write_csv('risk-episodes.csv',events_all);write_csv('trades.csv',trade_all);write_csv('transfers.csv',transfer_all)
dump('run-tests.json',{'completed_at_utc':datetime.now(timezone.utc).isoformat(),'runs':6,'btc_reference_runs':6,'daily_rows_checked':len(daily)*2,'conservation_and_daily_pnl_assertions':True,'no_reserve_replenishment':True,'decomposition_assertions':6,'module_sha256':hashlib.sha256(CAP.read_bytes()).hexdigest(),'no_new_network_requests':True})
print(json.dumps(summary,indent=2))
