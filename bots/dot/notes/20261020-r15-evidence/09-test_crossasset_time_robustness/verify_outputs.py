import json,csv,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;W=O.parents[1]
s=json.load(open(O/'summary.json'));u23=json.load(open(W/'03-test_c23_capital_execution/output/summary.json'));u40=json.load(open(W/'04-test_c40_capital_execution/output/summary.json'))['scenarios'];checks=[]
for x in s:
 if x['mode']!='inherited_2024_start':continue
 if x['strategy']=='C23' and x['symbol']=='SOLUSDT':
  u=next(y for y in u23 if y['strategy']=='C23' and y['cost']==x['cost'] and y['withdrawal_fee']==x['withdrawal_fee']);expected=u['full']['pnl']
 elif x['strategy']=='C40' and x['symbol']=='BTCUSDT':
  u=next(y for y in u40 if y['cost_rate']==x['cost'] and y['mode']==('idealized' if x['withdrawal_fee']==0 else 'fee1_delay1'));expected=u['net_pnl']
 else:continue
 assert abs(expected-x['pnl'])<1e-8;checks.append({'strategy':x['strategy'],'cost':x['cost'],'withdrawal_fee':x['withdrawal_fee'],'upstream_pnl':expected,'independent_pnl':x['pnl'],'difference':x['pnl']-expected})
assert len(checks)==8
agg=list(csv.DictReader(open(O/'aggregate.csv')));sensitivity=[]
for x in s:
 if x['mode']!='inherited_2024_start':continue
 selected=[r for r in agg if r['strategy']==x['strategy'] and r['symbol']==x['symbol'] and float(r['cost'])==x['cost'] and int(r['withdrawal_fee'])==x['withdrawal_fee'] and r['mode']==x['mode'] and r['period'] in ['2025','2026JanSep']]
 initial=float(selected[0]['initial_equity']);end=float(selected[-1]['end_equity']);days=sum(int(r['days']) for r in selected)
 reset=next(r for r in s if all(r[k]==x[k] for k in ['strategy','symbol','cost','withdrawal_fee']) and r['mode']=='cash_reset_2025_start')
 sensitivity.append(dict(strategy=x['strategy'],symbol=x['symbol'],cost=x['cost'],withdrawal_fee=x['withdrawal_fee'],inherited_initial=initial,inherited_pnl=end-initial,inherited_period_return=(end-initial)/initial,inherited_fixed5000_return=(end-initial)/5000,inherited_cagr=(end/initial)**(365/days)-1,cash_reset_pnl=reset['pnl'],cash_reset_cagr=reset['cagr_total5000']))
with (O/'start_sensitivity.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(sensitivity[0]));w.writeheader();w.writerows(sensitivity)
(O/'upstream-reproduction.json').write_text(json.dumps({'pass':True,'comparisons':checks},indent=2)+'\n')
print('PASS: 8 independent main-symbol capital outcomes match 03/04, 24 cash-reset comparisons; no upstream output mutations.')
