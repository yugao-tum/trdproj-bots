import json,math
R=json.load(open('_cache/races.json'))
BINS=[(0,0.05),(0.05,0.20),(0.20,0.50),(0.50,99)]
fit=[r for r in R.values() if 2014<=r['season']<=2023 and r.get('pole') and r.get('winner')]
rates=[]
for lo,hi in BINS:
    sub=[r for r in fit if r.get('margin') is not None and lo<=r['margin']<hi]
    w=sum(1 for r in sub if r['pole']==r['winner']); rates.append((w+1)/(len(sub)+2))
P0=sum(1 for r in fit if r['pole']==r['winner'])/len(fit)
def mA(m):
    if m is None: return 0.333
    for (lo,hi),p in zip(BINS,rates):
        if lo<=m<hi: return p
    return 0.333
test=[r for r in R.values() if 2024<=r['season']<=2026 and r.get('pole') and r.get('winner')]
def ll(ps):
    return -sum(y*math.log(max(p,1e-12))+(1-y)*math.log(max(1-p,1e-12)) for y,p in ps)/len(ps)
def br(ps):
    return sum((y-p)**2 for y,p in ps)/len(ps)
for lab,f in (('A',lambda r:mA(r.get('margin'))),('B',lambda r:P0)):
    ps=[(1 if r['pole']==r['winner'] else 0,f(r)) for r in test]
    print(f'{lab}: n={len(ps)} logloss={ll(ps):.4f} brier={br(ps):.4f}')
print('base rate 2014-2023',round(P0,4),'rates',[round(x,4) for x in rates])
for (lo,hi),p in zip(BINS,rates):
    sub=[r for r in test if r.get('margin') is not None and lo<=r['margin']<hi]
    print(f'  [{lo},{hi}) fit={p:.4f} train_n={sum(1 for r in fit if r.get("margin") is not None and lo<=r["margin"]<hi)} oos={sum(1 for r in sub if r["pole"]==r["winner"])}/{len(sub)}={ (sum(1 for r in sub if r["pole"]==r["winner"])/len(sub)) if sub else 0:.3f}')
print('2024-2026 pole wins',sum(1 for r in test if r['pole']==r['winner']),'/',len(test))
