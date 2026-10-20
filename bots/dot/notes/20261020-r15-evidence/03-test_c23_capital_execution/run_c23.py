"""Fixed signal C23 capital execution experiment; no network or trading."""
import csv,json,hashlib,datetime,statistics,sys
from pathlib import Path
from prepare import D,O,load,write
MODULE=O.parent.parent/'01-build_capital_cash_benchmarks/output/capital_account.py'

def csvwrite(name,rows):
 if not rows:return
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def signals(m,bars,dates):
 closes=[b.close for b in bars['SOLUSDT']];active=False;entry=None;events={};cluster=0;in_cluster=False;entryclusters={}
 for i,d in enumerate(dates):
  if not m.SIM_START<=d<=m.SIM_END:continue
  r=m.simple_rsi(closes[:i],14)
  if r>50:in_cluster=False
  if r<30 and not in_cluster:cluster+=1;in_cluster=True
  if active:
   if r>50 or (d-entry).days>=14:events[d]='exit';active=False
  elif r<30:events[d]='entry';active=True;entry=d;entryclusters[d]=cluster
 return events,entryclusters

def run(m,Account,bars,dates,events,cost,wfee,delay,strategy):
 a=Account(fee=cost,withdrawal_fee=wfee,delay_opens=delay);rows=[];last=None;entry=None;rounds=[];entry_total=None
 for i,d in enumerate(dates):
  if not m.SIM_START<=d<=m.SIM_END:continue
  op={s:bars[s][i].open for s in m.SYMBOLS};cl={s:bars[s][i].close for s in m.SYMBOLS};hi={s:bars[s][i].high for s in m.SYMBOLS}
  a.begin_day(d,op);a.sweep(op)
  if strategy=='C23':
   ev=events.get(d)
   if ev=='entry':
    entry=d;entry_total=a.total(op);a.rebalance(op,{'SOLUSDT':min(1100,.9*a.venue(op))})
   elif ev=='exit':
    a.rebalance(op,{});rounds.append(dict(entry=str(entry),exit=str(d),days=(d-entry).days,pnl=a.total(op)-entry_total));entry=None
  elif strategy!='cash' and d==m.SIM_START:a.rebalance(op,{strategy:1100})
  row=a.snapshot(cl,hi)
  if d==m.SIM_END:
   oldtotal=a.total(cl);oldfees=a.fees;terminal=a.liquidate_after_snapshot(cl)
   assert abs(oldtotal-a.total(cl)-(a.fees-oldfees))<1e-8
   row.update(venue_cash=a.cash,position_value=0.,total_equity=a.total(cl),net_pnl=a.total(cl)-5000,net_liquidation_equity=a.total(cl),trade_fees=a.fees,daily_pnl=row['daily_pnl']-(a.fees-oldfees),final_liquidation_fee=a.fees-oldfees,final_venue_cash=a.cash,final_position_value=0)
   if entry is not None:rounds.append(dict(entry=str(entry),exit=str(d),days=(d-entry).days,pnl=a.total(cl)-entry_total))
  else:row.update(final_liquidation_fee=0.,final_venue_cash=None,final_position_value=None)
  row.update(strategy=strategy,cost=cost,withdrawal_fee=wfee,withdrawal_delay_days=delay);rows.append(row)
 return rows,a.trades,a.transfers,rounds

def metrics(rows):
 out={}; start='2024-01-01'
 for name,rr,base in [('full',rows,5000),('2024',[r for r in rows if r['day']<'2025-01-01'],5000),('2025plus',[r for r in rows if r['day']>='2025-01-01'],next(r['total_equity'] for r in rows if r['day']=='2024-12-31'))]:
  pnl=rr[-1]['total_equity']-base;days=len(rr);peak=base;dd=0
  for r in rr:peak=max(peak,r['total_equity']);dd=min(dd,r['total_equity']/peak-1)
  out[name]=dict(pnl=pnl,total_fixed5000_return=pnl/5000,allocated1250_return=pnl/1250,cagr=(rr[-1]['total_equity']/base)**(365.25/days)-1,max_drawdown=dd,days=days)
 out.update(fees=rows[-1]['trade_fees'],withdrawal_fees=rows[-1]['withdrawal_fees'],net_withdrawn=rows[-1]['net_withdrawn'],open_breach_days=sum(r['open_breach'] for r in rows),close_breach_days=sum(r['close_breach'] for r in rows),high_exceed_days=sum(r['high_upper_exceeds'] for r in rows),max_open=max(r['open_pre'] for r in rows),max_close=max(r['close_venue'] for r in rows),max_high=max(r['high_upper_venue'] for r in rows))
 return out

def main():
 m=load('original_c23',D/'plans/spot_screen.py');cap=load('capital_account',MODULE);bars,dates,q=m.load_and_precheck(m.CSV_PATH);events,clusters=signals(m,bars,dates)
 original=m.simulate('C23',bars,dates,.003);original_dates=[(t.day,'entry' if t.side=='BUY' else 'exit') for t in original['trades'] if t.reason in ['C23 entry','C23 exit']];assert list(events.items())==original_dates
 allrows=[];alltrades=[];alltransfers=[];allrounds=[];summary=[];tests=1
 for cost in [.003,.006]:
  for wfee,delay in [(0,0),(1,1)]:
   pair={}
   for strategy in ['C23','SOLUSDT','BTCUSDT','cash']:
    rows,trades,transfers,rounds=run(m,cap.CapitalAccount,bars,dates,events,cost,wfee,delay,strategy);pair[strategy]=rows;meta=dict(strategy=strategy,cost=cost,withdrawal_fee=wfee,withdrawal_delay_days=delay)
    for r in rows:
     assert abs(r['conservation_residual'])<1e-7;assert r['venue_cash']>=-1e-7;assert r['external_cash']>=3750-1e-7;assert abs(r['total_equity']-5000-r['net_pnl'])<1e-7;assert abs(r['venue_cash']+r['position_value']+r['external_cash']+r['in_transit']-r['total_equity'])<1e-7;tests+=5
    for t in trades:
     assert abs(t['fee']-t['notional']*cost)<1e-8;tests+=1
     if t['quantity_delta']>0:assert t['notional']<=1100+1e-8;tests+=1
    if strategy=='C23':
     assert len(rounds)==len(clusters);tests+=1
     for r in rounds:r['oversold_cluster']=clusters[datetime.date.fromisoformat(r['entry'])];assert r['days']<=14;tests+=1
    allrows+=rows;alltrades += [dict(**meta,**t) for t in trades];alltransfers += [dict(**meta,**t) for t in transfers];allrounds += [dict(**meta,**t) for t in rounds];summary.append(dict(**meta,**metrics(rows),roundtrip_count=len(rounds),oversold_clusters=len(set(clusters.values())) if strategy=='C23' else None))
   c=[r['daily_pnl'] for r in pair['C23']]
   for s in ['SOLUSDT','BTCUSDT']:
    r=next(x for x in summary if x['strategy']=='C23' and x['cost']==cost and x['withdrawal_fee']==wfee);r[s+'_daily_pnl_correlation']=statistics.correlation(c,[x['daily_pnl'] for x in pair[s]])
 csvwrite('daily-ledger.csv',allrows);csvwrite('trades.csv',alltrades);csvwrite('withdrawals.csv',alltransfers);csvwrite('roundtrips.csv',allrounds);write('summary.json',summary);write('tests.json',dict(assertions=tests,passed=True,signals_exactly_match_original=True,actual_model='native OpenAI / ID not exposed',unique_new_mechanisms=0));write('dependency-manifest.json',dict(path=str(MODULE),sha256=hashlib.sha256(MODULE.read_bytes()).hexdigest(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));print(json.dumps([r for r in summary if r['strategy']=='C23'],indent=2))
if __name__=='__main__':main()
