import csv, statistics as st
from collections import Counter

path='bots/quant/notes/q006-hist/matches.csv'
rows=list(csv.DictReader(open(path,newline='')))
print('rows',len(rows))
priced=[r for r in rows if r['price_a'] not in ('','None') and r['price_b'] not in ('','None')]
print('priced_main',len(priced))
trig=[r for r in priced if r['triggered']=='True']
print('triggered_main',len(trig))
nets=[float(r['net_pnl']) for r in trig]
print('n',len(nets),'median',f'{st.median(nets):+.6f}','mean',f'{st.mean(nets):+.6f}')
hit=sum(1 for r in trig if float(r['payout'])>=0.999)
print('hit',hit,'/',len(trig),f'{hit/len(trig):.3f}')
tot=sum(nets); print('total_net',f'{tot:+.6f}')
asks=sum(float(r['entry_ask']) for r in trig)
fees=sum(float(r['fee']) for r in trig)
print('staked_notional',f'{asks:.6f}','fees',f'{fees:.6f}','per_$staked',f'{tot/asks:+.6f}')
print('resolved',dict(Counter(r['resolved_prices'] for r in trig)))
aa=[float(r['entry_ask']) for r in trig]
print('entry_ask min/median/max',f'{min(aa):.4f}',f'{st.median(aa):.4f}',f'{max(aa):.4f}')
# verify formulas at 1e-6 (matches.csv is rounded to 6 dp)
bad_fee=[]; bad_net=[]
for r in trig:
    a=float(r['entry_ask']); f=float(r['fee']); p=float(r['payout']); n=float(r['net_pnl'])
    if abs(f-0.05*a*(1-a))>2e-6: bad_fee.append((r['event_slug'],a,f))
    if abs(n-(p-a-f))>2e-6: bad_net.append((r['event_slug'],a,f,p,n))
print('fee_formula_mismatch_gt_2e-6',len(bad_fee),'net_formula_mismatch_gt_2e-6',len(bad_net))
# sensitivity: same definition as q006_hist.py -> triggered_sens within priced(main)
trs=[r for r in priced if r['triggered_sens']=='True']
nets2=[float(r['net_pnl_sens']) for r in trs]
print('sens_n',len(nets2),'median',f'{st.median(nets2):+.6f}','mean',f'{st.mean(nets2):+.6f}')
# date lag subset
sub=[r for r in priced if r['triggered']=='True' and r['date_lag_days'] not in ('','None') and int(r['date_lag_days'])<=2]
print('lag_le2_n',len(sub),'median',f'{st.median([float(r["net_pnl"]) for r in sub]):+.6f}','mean',f'{st.mean([float(r["net_pnl"]) for r in sub]):+.6f}')
# bands, REPORT thresholds
def band(r):
    a=float(r['entry_ask'])
    return 'ask<0.3' if a<0.3 else ('0.3-0.7' if a<=0.7 else 'ask>0.7')
for name in ['ask<0.3','0.3-0.7','ask>0.7']:
    b=[float(r['net_pnl']) for r in trig if band(r)==name]
    print('band',name,'n',len(b),'median',f'{st.median(b):+.6f}','mean',f'{st.mean(b):+.6f}')
# zero-cost: drop 1c half-spread and fee -> payout - (ask-0.01)
zs=[float(r['payout'])-(float(r['entry_ask'])-0.01) for r in trig]
print('zero_spread_and_fee_n',len(zs),'median',f'{st.median(zs):+.6f}','mean',f'{st.mean(zs):+.6f}')
print('CRITERION triggered>=30 and median<=0 ->', 'FAIL' if (len(trig)>=30 and st.median(nets)<=0) else 'not FAIL')
