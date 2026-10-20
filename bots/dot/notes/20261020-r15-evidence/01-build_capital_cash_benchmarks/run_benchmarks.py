import csv,json,hashlib,pathlib,datetime
from capital_account import CapitalAccount
P=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path('retained-inputs/workers/data-probe/data/history/spot_daily.csv')
expected='a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a'
assert hashlib.sha256(DATA.read_bytes()).hexdigest()==expected
rows=[r for r in csv.DictReader(DATA.open()) if r['symbol']=='BTCUSDT' and '2024-01-01'<=r['open_time_utc'][:10]<='2026-09-30']
assert len(rows)==1004 and len(set(r['open_time_utc'][:10] for r in rows))==1004
assert all((datetime.date.fromisoformat(b['open_time_utc'][:10])-datetime.date.fromisoformat(a['open_time_utc'][:10])).days==1 for a,b in zip(rows,rows[1:]))
summary=[]
for kind in ['cash','BTC']:
 for fee in [.003,.006]:
  for wf,delay in [(0,0),(1,1)]:
   name=f'{kind}_fee{fee}_withdraw{wf}_delay{delay}'
   a=CapitalAccount(fee=fee,withdrawal_fee=wf,delay_opens=delay);ledger=[]
   for i,r in enumerate(rows):
    day=r['open_time_utc'][:10];op={'BTCUSDT':float(r['open'])};cl={'BTCUSDT':float(r['close'])};hi={'BTCUSDT':float(r['high'])}
    a.begin_day(day,op);a.sweep(op)
    if i==0 and kind=='BTC':a.rebalance(op,{'BTCUSDT':1100})
    ledger.append(a.snapshot(cl,hi))
   with (P/(name+'-ledger.csv')).open('w') as f:
    w=csv.DictWriter(f,fieldnames=ledger[0].keys());w.writeheader();w.writerows(ledger)
   s={'scenario':name,'kind':kind,'fee':fee,'withdrawal_fee':wf,'delay_opens':delay,'days':len(rows),'ending_equity':ledger[-1]['total_equity'],'net_pnl':ledger[-1]['net_pnl'],'net_liquidation_equity':ledger[-1]['net_liquidation_equity'],'return_total5000':ledger[-1]['net_pnl']/5000,'annualized_total5000':(ledger[-1]['total_equity']/5000)**(365.25/len(rows))-1,'return_initialvenue1250':ledger[-1]['net_pnl']/1250,'trade_fees':a.fees,'withdrawal_fees':a.withdrawal_costs,'withdrawal_count':len(a.transfers),'net_withdrawn':a.withdrawn,'final_in_transit':a.transit(),'max_open_pre':max(x['open_pre'] for x in ledger),'max_close':max(x['close_venue'] for x in ledger),'max_high_upper':max(x['high_upper_venue'] for x in ledger),'open_breach_days':sum(x['open_breach'] for x in ledger),'close_breach_days':sum(x['close_breach'] for x in ledger),'high_upper_exceed_days':sum(x['high_upper_exceeds'] for x in ledger),'max_conservation_residual':max(abs(x['conservation_residual']) for x in ledger),'independent_risk_episodes':int(kind=='BTC'),'all_day_cap_verified':False,'classification':'historical-price conditional execution assumption'}
   assert abs(sum(x['daily_pnl'] for x in ledger)-s['net_pnl'])<1e-7
   summary.append(s)
   (P/(name+'-transfers.json')).write_text(json.dumps(a.transfers,indent=2))
(P/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (P/'summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=summary[0].keys());w.writeheader();w.writerows(summary)
print(json.dumps(summary,indent=2))
