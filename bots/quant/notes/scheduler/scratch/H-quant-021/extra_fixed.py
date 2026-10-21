import json, statistics as st, math
R=json.load(open('_cache/analysis_rows.json')); RACES=json.load(open('_cache/races.json')); ALL=json.load(open('_cache/all_prices.json'))
def fee(p): return 0.05*p*(1-p)
def net(y,p,half=0.01): return y-p-fee(p)-half
BINS=[(0,0.05),(0.05,0.20),(0.20,0.50),(0.50,99)]
fit=[r for r in RACES.values() if 2014<=r['season']<=2023 and r.get('pole') and r.get('winner')]
rates=[]; ns=[]
for lo,hi in BINS:
    sub=[r for r in fit if r.get('margin') is not None and lo<=r['margin']<hi]
    w=sum(1 for r in sub if r['pole']==r['winner']); rates.append((w+1)/(len(sub)+2)); ns.append(len(sub))
P0=sum(1 for r in fit if r['pole']==r['winner'])/len(fit)
def mA(m):
    if m is None: return 0.333
    for (lo,hi),rr in zip(BINS,rates):
        if lo<=m<hi: return rr
    return 0.333
print('=== OOS model eval 2024-2026 (65 races), corrected ===')
oos=[r for r in RACES.values() if 2024<=r['season']<=2026 and r.get('pole') and r.get('winner')]
def brier(ps): return sum((p-(1 if r['pole']==r['winner'] else 0))**2 for r,p in zip(oos,ps))/len(oos)
def ll(ps): return -sum(math.log(max(p if r['pole']==r['winner'] else 1-p,1e-12)) for r,p in zip(oos,ps))/len(oos)
pa=[mA(r.get('margin')) for r in oos]; pb=[P0]*len(oos)
print('n',len(oos),'modelA ll',round(ll(pa),4),'brier',round(brier(pa),4))
print('const ll',round(ll(pb),4),'brier',round(brier(pb),4))
print('by margin bin OOS:')
for (lo,hi),rr,n in zip(BINS,rates,ns):
    sub=[r for r in oos if r.get('margin') is not None and lo<=r['margin']<hi]; w=sum(1 for r in sub if r['pole']==r['winner'])
    print(f'  [{lo},{hi}) fit={rr:.3f} n_train={n} oos {w}/{len(sub)}={w/len(sub) if sub else 0:.3f}')
print('\n=== base rate by season and block ===')
for lo,hi in ((2014,2021),(2022,2023),(2024,2026),(2014,2023),(2014,2026)):
    sub=[r for r in RACES.values() if lo<=r['season']<=hi and r.get('pole') and r.get('winner')]
    w=sum(1 for r in sub if r['pole']==r['winner']); print(f'  {lo}-{hi}: {w}/{len(sub)} = {w/len(sub):.4f}')
print('\n=== Ergast vs PM winner agreement in 49 events (corrected) ===')
bad=[]
for r in R:
    k=r['key']; er=RACES[k].get('winner'); pmw=[x for x in ALL if x['key']==k and x['y']==1]
    pm=pmw[0]['driver'] if pmw else None
    if er!=None and pm is not None and er.split('_')[-1].lower() not in pm.lower().replace('-',' '):
        bad.append((k,er,pm))
print('mismatches',len(bad)); [print(' ',x) for x in bad]
print('\n=== calibration buckets of 49 pole markets (p_hist) ===')
def bucket(p):
    for lo,hi,lab in ((0,.1,'~0.1'),(.1,.3,'~0.2'),(.3,.5,'~0.4'),(.5,.7,'~0.6'),(.7,1.01,'~0.8')):
        if lo<=p<hi: return lab
    return '?'
bs={}
for r in R:
    b=bucket(r['p_hist']); bs.setdefault(b,[]).append(r)
for b in ('~0.1','~0.2','~0.4','~0.6','~0.8'):
    g=bs.get(b,[]); print(f'  {b}: n={len(g)} meanp={st.mean([x["p_hist"] for x in g]):.3f} win={sum(1 for x in g if x["y"]==1)}/{len(g)}={(sum(1 for x in g if x["y"]==1)/len(g) if g else 0):.3f}')
print('\n=== break-even uplift, rule A exec100 ===')
tr=[r for r in R if r['p_hist'] is not None and r['exec100'] is not None and r['p_hist']<=mA(r['margin'])-0.05]
for u in [i/1000 for i in range(0,501)]:
    s0=sum(r['y']-(r['exec100']+u)-fee(min(r['exec100']+u,0.999))-0.01 for r in tr)
    if s0<=0: print('  break-even uplift',u,'base sum',round(sum(net(r['y'],r['exec100']) for r in tr),4)); break
print('\n=== measured gap vs p_hist, 49 events ===')
g1=[r['first_buy_price']-r['p_hist'] for r in R]; g2=[r['exec100']-r['p_hist'] for r in R]
print('  first mean',round(st.mean(g1),4),'median',round(st.median(g1),4),'min',round(min(g1),4),'max',round(max(g1),4))
print('  exec100 mean',round(st.mean(g2),4),'median',round(st.median(g2),4),'min',round(min(g2),4),'max',round(max(g2),4))
print('\n=== rule A with first_buy price ===')
for k in ('first_buy_price','exec20','exec100'):
    v=[net(r['y'],r[k]) for r in tr]
    print(f'  A {k}: n={len(tr)} wins={sum(1 for r in tr if r["y"]==1)} sum={sum(v):+.4f} mean={st.mean(v):+.4f}')
print('\n=== capacity: totals ===')
big=[r for r in R if r['buy_shares_pre'] is not None]
print('  pre-race taker BUY shares: min',round(min(r['buy_shares_pre'] for r in big)),'median',round(st.median([r['buy_shares_pre'] for r in big])))
print('\n=== prices sum distribution ===')
sums={}
for x in ALL:
    if x['p'] is not None: sums.setdefault(x['key'],0.0); sums[x['key']]+=x['p']
print(' ',sorted(round(v,3) for v in sums.values() if v>1.17))
