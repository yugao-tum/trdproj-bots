import json, statistics as st
R=json.load(open('_cache/analysis_rows.json')); RACES=json.load(open('_cache/races.json'))
D={x['key']:x for x in json.load(open('_cache/diag.json'))}
for r in R: r.update({k:v for k,v in D[r['key']].items() if k not in ('key','race','cut','start','p_hist','first_buy_price','first_buy_size','buy_shares_pre')})
BINS=[(0,0.05),(0.05,0.20),(0.20,0.50),(0.50,99)]
fit=[r for r in RACES.values() if 2014<=r['season']<=2023 and r.get('pole') and r.get('winner')]
rates=[]
for lo,hi in BINS:
    sub=[r for r in fit if r.get('margin') is not None and lo<=r['margin']<hi]
    w=sum(1 for r in sub if r['pole']==r['winner']); rates.append((w+1)/(len(sub)+2))
P0=sum(1 for r in fit if r['pole']==r['winner'])/len(fit)
def mA(m):
    if m is None: return 0.333
    for (lo,hi),rr in zip(BINS,rates):
        if lo<=m<hi: return rr
    return 0.333
print('=== champion grid distribution (269) ===')
import collections
c=collections.Counter()
for r in RACES.values():
    g=r.get('grid')
    if g is None: continue
    c[int(g)]+=1
for k in sorted(c): print(k,c[k])
print('grid=1',c[1],'grid missing',sum(1 for r in RACES.values() if r.get('grid') is None))
print('\n=== trigger diagnostics ===')
tr=[r for r in R if r['p_hist'] is not None and r['exec100'] is not None and r['p_hist']<=mA(r['margin'])-0.05]
print('n',len(tr))
print('last pre side',collections.Counter(r.get('last_pre_side') for r in tr))
print('buy_shares_pre min/median',min(r['buy_shares_pre'] for r in tr),st.median([r['buy_shares_pre'] for r in tr]))
print('t100 min/median/max',min(r['t100_h'] for r in tr),round(st.median([r['t100_h'] for r in tr]),2),round(max(r['t100_h'] for r in tr),2))
print('first buy dt h min/median/max',round(min(r['first_buy_dt'] for r in tr)/3600,2),round(st.median([r['first_buy_dt'] for r in tr])/3600,2),round(max(r['first_buy_dt'] for r in tr)/3600,2))
print('first size median',st.median([r['first_buy_size'] for r in tr]),'>=100:',sum(1 for r in tr if r['first_buy_size']>=100),'of',len(tr))
print('\n=== all 49: first buy timing ===')
print('min/median/max h',round(min(r['first_buy_dt'] for r in R)/3600,2),round(st.median([r['first_buy_dt'] for r in R])/3600,2),round(max(r['first_buy_dt'] for r in R)/3600,2))
print('\n=== per-trade net A exec100 and cumulative ===')
v=[(r['key'],r['y']-r['exec100']-0.05*r['exec100']*(1-r['exec100'])-0.01) for r in sorted(tr,key=lambda z:z['key'])]
print('sum',round(sum(x[1] for x in v),4),'mean',round(st.mean([x[1] for x in v]),4))
print('\n=== total profit at 100 shares/trade ===')
print('USD',round(100*sum(x[1] for x in v),2),'over 2024-09..2026-10')
print('\n=== what if 200 shares (2x100) per trigger ===')
print('USD',round(200*sum(x[1] for x in v),2))
print('\n=== estimate annualized on 5000 ===')
print('~25 months -> per year USD',round(100*sum(x[1] for x in v)/25*12,2),'=',round(100*sum(x[1] for x in v)/25*12/5000*100,2),'%')
print('\n=== rule A if constant p0 used with exec100 ===')
tr2=[r for r in R if r['p_hist'] is not None and r['exec100'] is not None and r['p_hist']<=P0-0.05]
print('n',len(tr2),'wins',sum(1 for r in tr2 if r['y']==1),'sum',round(sum(r['y']-r['exec100']-0.05*r['exec100']*(1-r['exec100'])-0.01 for r in tr2),4))
