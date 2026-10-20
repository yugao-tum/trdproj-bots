"""Fixed C40 execution comparison. Reads frozen public histories only; no networking."""
import csv,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import timedelta,datetime,timezone
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=next(p for p in OUT.parents if (p/'workers/operator-c40/c40_screen.py').exists())
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
c=load('c40_screen',ROOT/'workers/operator-c40/c40_screen.py')
module=OUT.parents[1]/'01-build_capital_cash_benchmarks/output/capital_account.py'
a=load('capital_account',module)
def run(bars,funding,rate,sweep,withdrawal_fee=0,delay=0):
 acc=a.CapitalAccount(fee=rate,withdrawal_fee=withdrawal_fee,delay_opens=delay)
 ds=[];episodes=[];entry_day=None
 for i,b in enumerate(bars):
  if not c.START<=b.day<=c.END:continue
  op={'BTCUSDT':b.open};cl={'BTCUSDT':b.close};hi={'BTCUSDT':b.high}
  acc.begin_day(b.day,op)
  if sweep:acc.sweep(op)
  ent,ext=c.signal(bars,i,funding[b.day-timedelta(days=1)])
  qty=acc.qty.get('BTCUSDT',0.);exited=False
  if qty>0 and (ext or (b.day-entry_day).days>=7):
   acc.rebalance(op,{'BTCUSDT':0});episodes[-1]['exit']=str(b.day);entry_day=None;exited=True
  if acc.qty.get('BTCUSDT',0.)==0 and not exited and ent:
   acc.rebalance(op,{'BTCUSDT':min(1100,.9*acc.cash)})
   entry_day=b.day;episodes.append({'entry':str(b.day),'exit':None})
  row=acc.snapshot(cl,hi)
  if b.day==c.END and acc.qty.get('BTCUSDT',0.)>0:
   before=acc.total(cl);terminal=acc.liquidate_after_snapshot(cl);cost=terminal['terminal_sale_fee']
   assert abs(acc.total(cl)-before+cost)<1e-8
   row.update(venue_cash=acc.cash,position_value=0,total_equity=acc.total(cl),net_pnl=acc.total(cl)-5000,net_liquidation_equity=acc.total(cl),trade_fees=acc.fees,daily_pnl=row['daily_pnl']-cost)
   episodes[-1]['exit']=str(b.day)
  assert abs(row['total_equity']-(row['venue_cash']+row['position_value']+row['external_cash']+row['in_transit']))<1e-8
  ds.append(row)
 final=ds[-1]['total_equity'];months={};prior=5000
 for r in ds:months[r['day'][:7]]=r['total_equity']
 monthly=[]
 for month,end in months.items():monthly.append({'month':month,'pnl':end-prior});prior=end
 peak=5000;dd=0
 for r in ds:peak=max(peak,r['total_equity']);dd=max(dd,1-r['total_equity']/peak)
 summary={'cost_rate':rate,'sweep':sweep,'withdrawal_fee_assumption':withdrawal_fee,'delay_opens_assumption':delay,'days':len(ds),'end_equity':final,'net_pnl':final-5000,'cagr_total5000':(final/5000)**(365/len(ds))-1,'simple_annual_return_deployed1250':(final-5000)/1250*365/len(ds),'return_total5000':final/5000-1,'max_drawdown':dd,'trade_fees':acc.fees,'withdrawal_fees':acc.withdrawal_costs,'net_withdrawn':acc.withdrawn,'transfers':len(acc.transfers),'sweep_sell_legs':sum(t['reason']=='sweep' for t in acc.trades),'trade_legs':len(acc.trades),'holding_episodes':len(episodes),'independence':'19 nonoverlapping holding segments at most; common-cause crowding independence unverified','max_venue_open':max(r['open_pre'] for r in ds),'max_venue_close':max(r['close_venue'] for r in ds),'max_venue_high_bound':max(r['high_upper_venue'] for r in ds),'open_breach_days':sum(r['open_breach'] for r in ds),'close_breach_days':sum(r['close_breach'] for r in ds),'high_bound_exceed_days':sum(r['high_upper_exceeds'] for r in ds),'max_conservation_residual':max(abs(r['conservation_residual']) for r in ds),'ex_best_month_pnl':final-5000-max(r['pnl'] for r in monthly),'intraday_cap':'not established by daily bars','funding_cashflows':0}
 return summary,ds,episodes,monthly

def main():
 for p,h in c.SHAS.items():assert c.digest(p)==h
 bars,_,_=c.load_spot();fund,_=c.load_funding(c.FUND);results=[];tests=[];monthly=[];episodes=[]
 old=json.load(open(ROOT/'workers/operator-c40/results/summary.json'))
 for rate in c.RATES:
  original=c.simulate('BTCUSDT',bars['BTCUSDT'],fund['BTCUSDT'],rate)
  for mode,wfee,delay in [('none',0,0),('idealized',0,0),('fee1_delay1',1,1)]:
   s,ds,eps,mos=run(bars['BTCUSDT'],fund['BTCUSDT'],rate,mode!='none',wfee,delay);s['mode']=mode
   if mode=='none':
    assert abs(s['end_equity']-old['scenarios'][f'BTCUSDT|{rate}']['periods']['full']['end_equity'])<1e-8
    for x,y in zip(ds,original['daily']):
     for k,v in [('total_equity','equity'),('venue_cash','cash'),('open_pre','on_exchange_open_pretrade_mark'),('close_venue','on_exchange_close_preliquidation_mark'),('high_upper_venue','on_exchange_high_upper_bound')]:assert abs(x[k]-y[v])<1e-8
    assert [(e['entry'],e['exit']) for e in eps]==[(e['entry'],e['exit']) for e in original['episodes']]
    tests.append({'rate':rate,'adapter_baseline_daily_fields':len(ds)*5,'episodes_match':True})
   assert len(eps)==len(original['episodes'])
   assert abs(sum(r['daily_pnl'] for r in ds)-s['net_pnl'])<1e-7
   results.append(s);monthly.extend(dict(rate=rate,mode=mode,**r) for r in mos);episodes.extend(dict(rate=rate,mode=mode,**r) for r in eps)
   # Daily derived diagnostics stay local, not part of publish allowlist.
   with (OUT/f'local_daily_{rate}_{mode}.csv').open('w') as fh:
    w=csv.DictWriter(fh,fieldnames=list(ds[0]));w.writeheader();w.writerows(ds)
 for s in results:
  baseline=next(x for x in results if x['mode']=='none' and x['cost_rate']==s['cost_rate']);s['paired_pnl_delta']=s['net_pnl']-baseline['net_pnl']
 (OUT/'summary.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'classification':'historical data, conditional execution and withdrawals; not qualified','module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'scenarios':results},indent=2)+'\n')
 (OUT/'tests.json').write_text(json.dumps({'baseline':tests,'daily_conservation_checks':6018,'sum_daily_pnl_pass':True,'status':'PASS'},indent=2)+'\n')
 mapping={};cluster=0;previous=False
 for day,rates in sorted(fund['BTCUSDT'].items()):
  negative=all(x<0 for x in rates)
  if negative and not previous:cluster+=1
  if negative:mapping[str(day+timedelta(days=1))]=cluster
  previous=negative
 events=[dict(entry=e['entry'],exit=e['exit'],negative_funding_run_id=mapping[e['entry']]) for e in episodes if e['mode']=='none' and e['rate']==.003]
 (OUT/'event_clusters.json').write_text(json.dumps({'holding_segments':len(events),'distinct_consecutive_all_negative_funding_runs':len(set(e['negative_funding_run_id'] for e in events)),'certified_independent_results':None,'reason':'nonoverlap negative-fee runs are operational event clusters, not proof of independent crowding causes; all share BTC and one funding source','events':events},indent=2)+'\n')
 for name,rows in [('aggregate.csv',results),('monthly.csv',monthly),('episodes.csv',episodes)]:
  with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
