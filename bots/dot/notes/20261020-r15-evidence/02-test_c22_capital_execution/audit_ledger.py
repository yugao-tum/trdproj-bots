"""Independent replay of persisted trades and transfers, not capital_account calls."""
import csv,json,collections
from pathlib import Path
O=Path(__file__).resolve().parent
rows=list(csv.DictReader(open(O/'daily-accounting.csv')));trades=list(csv.DictReader(open(O/'trades.csv')));transfers=list(csv.DictReader(open(O/'transfers.csv')))
market={(r['symbol'],r['open_time_utc'][:10]):float(r['close']) for r in csv.DictReader(open('retained-inputs/workers/data-probe/data/history/spot_daily.csv'))}
maxerr=0.;n=0
for cost in [.003,.006]:
 for scenario in ['no_withdrawal','optimistic','engineering_stress']:
  cash=1250.;external=3750.;qty=collections.defaultdict(float);pending=[]
  rr=[r for r in rows if float(r['cost'])==cost and r['scenario']==scenario]
  tt=[r for r in trades if float(r['cost'])==cost and r['scenario']==scenario]
  xx=[r for r in transfers if float(r['cost'])==cost and r['scenario']==scenario]
  for r in rr:
   day=r['day'];remaining=[]
   for due,v in pending:
    if due<=day:external+=v
    else:remaining.append((due,v))
   pending=remaining
   for t in tt:
    if t['day']!=day:continue
    delta=float(t['quantity_delta']);price=float(t['price']);fee=float(t['fee']);cash-=delta*price+fee;qty[t['symbol']]+=delta
    assert abs(fee-abs(delta)*price*cost)<1e-8
   for t in xx:
    if t['day']!=day:continue
    cash-=float(t['gross']);net=float(t['net'])
    if t['due']<=day:external+=net
    else:pending.append((t['due'],net))
   transit=sum(x[1] for x in pending);position=sum(q*market[s,day] for s,q in qty.items());equity=cash+external+transit+position
   checks={'venue_cash':cash,'external_cash':external,'in_transit':transit,'position_value':position,'total_equity':equity,'net_pnl':equity-5000}
   for k,v in checks.items():
    err=abs(v-float(r[k]));maxerr=max(err,maxerr);assert err<1e-7,(scenario,day,k,v,r[k]);n+=1
# Same-signal no-sweep exposure is exactly half original; verifies sizing and fees against frozen independent implementation.
old=json.load(open(O/'original-reproduction.json'));new=json.load(open(O/'summary.json'))
for x in old:
 y=next(s for s in new if s['cost']==x['cost'] and s['scenario']=='no_withdrawal');assert abs(y['pnl']-x['pnl']/2)<1e-8;assert abs(y['trading_fees']-x['fees']/2)<1e-8
out={'assertions':n,'rows':len(rows),'max_absolute_error':maxerr,'independent_trade_transfer_replay':True,'no_sweep_exact_half_original_pnl_and_fees':True}
(O/'independent-ledger-audit.json').write_text(json.dumps(out,indent=2));print(out)
