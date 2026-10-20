"""Local frozen-rule robustness. No networking, trading, or tuning."""
import sys,csv,json,hashlib,importlib.util,statistics
from pathlib import Path
from datetime import date,datetime,timezone,timedelta
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent
R=next(p for p in O.parents if (p/'plans/spot_screen.py').exists())
W=O.parents[1]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x): (O/n).write_text(json.dumps(x,indent=2,default=str)+'\n')
def csvwrite(n,rs):
 with (O/n).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
CAP=W/'01-build_capital_cash_benchmarks/output/capital_account.py'
assert sha(CAP)=='814528b5a1a70ea13e6aa258ce13b12c64516c8683d12456ec60e3df368a8c7c'
S=load('original_spot',R/'plans/spot_screen.py');C=load('original_c40',R/'workers/operator-c40/c40_screen.py');A=load('capital_account',CAP).CapitalAccount
START=date(2024,1,1);END=date(2026,9,30)
B,DS,Q=S.load_and_precheck(S.CSV_PATH);F,_=C.load_funding(C.FUND)
checks=0

def events(strategy,sym,start):
 ev={};active=False;entry=None;closes=[b.close for b in B[sym]]
 for i,d in enumerate(DS):
  if not start<=d<=END:continue
  if strategy=='C23':
   r=S.simple_rsi(closes[:i],14);ent=r<30;ext=r>50;maxdays=14
  else:ent,ext=C.signal(B[sym],i,F[sym][d-timedelta(days=1)]);maxdays=7
  if active:
   if ext or (d-entry).days>=maxdays:ev[d]='exit';active=False
  elif ent:ev[d]='entry';entry=d;active=True
 return ev

def run(strategy,sym,rate,wfee,delay,start,skip=None):
 global checks
 start=max(start,C.START) if strategy=='C40' else start
 a=A(fee=rate,withdrawal_fee=wfee,delay_opens=delay);ev=events(strategy,sym,start);rows=[];eps=[];entry=None;initial=None
 for i,d in enumerate(DS):
  if not start<=d<=END:continue
  b=B[sym][i];op={sym:b.open};cl={sym:b.close};hi={sym:b.high}
  a.begin_day(d,op);a.sweep(op)
  if ev.get(d)=='entry' and d!=skip:
   entry=d;initial=a.total(op);a.rebalance(op,{sym:min(1100,.9*a.venue(op))})
  elif ev.get(d)=='exit' and entry is not None:
   a.rebalance(op,{});eps.append(dict(entry=str(entry),exit=str(d),pnl=a.total(op)-initial));entry=None
  row=a.snapshot(cl,hi)
  if d==END and entry is not None:
   before=a.total(cl);a.liquidate_after_snapshot(cl);fee=before-a.total(cl)
   row.update(venue_cash=a.cash,position_value=0,total_equity=a.total(cl),net_pnl=a.total(cl)-5000,daily_pnl=row['daily_pnl']-fee,trade_fees=a.fees)
   eps.append(dict(entry=str(entry),exit=str(d),pnl=a.total(cl)-initial));entry=None
  assert abs(row['total_equity']-sum(row[k] for k in ['venue_cash','position_value','external_cash','in_transit']))<1e-7
  assert row['venue_cash']>=-1e-7 and row['external_cash']>=3750-1e-7
  assert abs(row['net_pnl']-(row['total_equity']-5000))<1e-7
  checks+=3;rows.append(row)
 assert abs(sum(x['daily_pnl'] for x in rows)-(rows[-1]['total_equity']-5000))<1e-7;checks+=1
 for t in a.trades:assert abs(t['fee']-t['notional']*rate)<1e-8;checks+=1
 assert abs(sum(e['pnl'] for e in eps)-(a.total(cl)-5000))<1e-7;checks+=1
 return rows,eps

def periods(rows,meta):
 out=[]
 for name,lo,hi in [('full',str(START),str(END)),('2024','2024-01-01','2024-12-31'),('2025','2025-01-01','2025-12-31'),('2026JanSep','2026-01-01','2026-09-30')]:
  selected=[r for r in rows if lo<=r['day']<=hi]
  if not selected:continue
  first=rows.index(selected[0]);initial=rows[first-1]['total_equity'] if first else 5000;last=selected[-1]['total_equity'];pnl=last-initial;n=len(selected)
  out.append(dict(**meta,period=name,first=selected[0]['day'],last=selected[-1]['day'],days=n,initial_equity=initial,end_equity=last,pnl=pnl,return_period_initial=pnl/initial,return_fixed5000=pnl/5000,cagr_period_initial=(last/initial)**(365/n)-1,simple_annual_fixed5000=pnl/5000*365/n))
 return out

def merge_clusters(eps):
 groups=[]
 for e in sorted(eps,key=lambda e:(e['entry'],e['exit'])):
  if not groups or e['entry']>groups[-1]['end']:groups.append({'start':e['entry'],'end':e['exit'],'members':[]})
  groups[-1]['end']=max(groups[-1]['end'],e['exit']);groups[-1]['members'].append(e)
 return groups

def main():
 prereg=json.loads((O/'PRE-REGISTRATION.json').read_text());assert sha(O/'PRE-REGISTRATION.json')==(O/'PRE-REGISTRATION.sha256').read_text().strip()
 summary=[];aggregate=[];episodes=[];daily=[];all_series={};qual=[]
 for strategy in ['C23','C40']:
  for sym in ['BTCUSDT','ETHUSDT','SOLUSDT']:
   for rate in [.003,.006]:
    for wfee,delay in [(0,0),(1,1)]:
     for start in [START,date(2025,1,1)]:
      mode='inherited_2024_start' if start==START else 'cash_reset_2025_start'
      meta=dict(strategy=strategy,symbol=sym,cost=rate,withdrawal_fee=wfee,delay_opens=delay,mode=mode)
      rows,eps=run(strategy,sym,rate,wfee,delay,start);metrics=periods(rows,meta);aggregate+=metrics
      best=max(eps,key=lambda x:x['pnl']) if eps else None
      dropped,_=run(strategy,sym,rate,wfee,delay,start,date.fromisoformat(best['entry']) if best else None)
      full=metrics[0]
      record=dict(**meta,pnl=full['pnl'],cagr_total5000=full['cagr_period_initial'],simple_annual_deployed1250=full['pnl']/1250*365/full['days'],holding_segments=len(eps),max_episode_pnl=best['pnl'] if best else 0,dropped_episode_entry=best['entry'] if best else None,ex_best_episode_rerun_pnl=dropped[-1]['net_pnl'],ex_best_episode_rerun_cagr=(dropped[-1]['total_equity']/5000)**(365/len(dropped))-1,open_breach_days=sum(r['open_breach'] for r in rows),close_breach_days=sum(r['close_breach'] for r in rows),high_upper_exceed_days=sum(r['high_upper_exceeds'] for r in rows),max_open=max(r['open_pre_conservative'] for r in rows),max_close=max(r['close_venue']+r['in_transit'] for r in rows),max_high_upper=max(r['high_upper_venue']+r['in_transit'] for r in rows),intraday_cap_proven=False,qualified=False)
      summary.append(record);episodes.extend(dict(**meta,**e) for e in eps)
      daily.extend(dict(**meta,**r) for r in rows)
      if start==START:all_series[(strategy,sym,rate,wfee)]=[r['daily_pnl'] for r in rows]
 correlations=[]
 for strategy in ['C23','C40']:
  for rate in [.003,.006]:
   for wfee in [0,1]:
    for s1,s2 in [('BTCUSDT','ETHUSDT'),('BTCUSDT','SOLUSDT'),('ETHUSDT','SOLUSDT')]:
     correlations.append(dict(strategy=strategy,cost=rate,withdrawal_fee=wfee,symbol1=s1,symbol2=s2,daily_pnl_correlation=statistics.correlation(all_series[(strategy,s1,rate,wfee)],all_series[(strategy,s2,rate,wfee)])))
 base=[e for e in episodes if e['cost']==.003 and e['withdrawal_fee']==0 and e['mode']=='inherited_2024_start']
 clusters=merge_clusters(base)
 write('event_clusters.json',dict(raw_segments=len(base),overlap_merged_temporal_clusters=len(clusters),certified_independent_results=None,reason='Temporal overlap merged across assets AND rules. Disjoint clusters can still share macro causes; no claim of independence or 30 verified outcomes.',clusters=clusters))
 csvwrite('aggregate.csv',aggregate);csvwrite('summary.csv',summary);write('summary.json',summary);csvwrite('episodes.csv',episodes);csvwrite('correlations.csv',correlations);csvwrite('local_daily.csv',daily)
 write('tests.json',dict(passed=True,assertions=checks,scenarios=len(summary),ex_best_episode_reruns=len(summary),new_mechanisms=0,actual_model='native OpenAI / ID not exposed',frozen_module_sha=sha(CAP),daily_rows=len(daily)))
 print(json.dumps({'assertions':checks,'scenarios':len(summary),'clusters':len(clusters),'baseline':[x for x in summary if x['cost']==.003 and x['withdrawal_fee']==0 and x['mode']=='inherited_2024_start']},indent=2))
if __name__=='__main__':main()
