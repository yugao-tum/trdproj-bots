import json,statistics as st,collections
A=json.load(open('_cache/all_prices.json'))
P=[x for x in A if x['p'] is not None and x['y'] is not None]
def fee(p,rate=0.05): return rate*p*(1-p)
def net(y,p,rate=0.05,half=0.01): return y-p-fee(p,rate)-half
print('markets',len(A),'with p and y',len(P))
sums=collections.defaultdict(float); nms=collections.Counter()
for x in P: sums[x['key']]+=x['p']; nms[x['key']]+=1
ss=sorted(sums.values())
print('events with any priced market',len(ss),'of',len({x['key'] for x in A}))
print('price sum: median',round(st.median(ss),3),'min',round(min(ss),3),'max',round(max(ss),3),'<=1.17',sum(1 for s in ss if s<=1.17),'of',len(ss))
print('events with all markets priced',sum(1 for k in sums if nms[k]==sum(1 for x in A if x['key']==k)))
bins=[(0,0.05),(0.05,0.10),(0.10,0.20),(0.20,0.30),(0.30,0.50),(0.50,0.70),(0.70,1.01)]
print(f'{"bucket":>12} {"n":>4} {"meanp":>7} {"winrate":>8} {"mean_net":>9}  polen polewin  nonpolen nonpolewin')
for lo,hi in bins:
    sub=[x for x in P if lo<=x['p']<hi]
    if not sub: continue
    po=[x for x in sub if x['is_pole']]; no=[x for x in sub if not x['is_pole']]
    print(f'[{lo:.2f},{hi:.2f}) {len(sub):4d} {st.mean([x["p"] for x in sub]):7.3f} {st.mean([x["y"] for x in sub]):8.3f} {st.mean([net(x["y"],x["p"]) for x in sub]):+9.4f}  {len(po):5d} {(st.mean([x["y"] for x in po]) if po else 0):7.3f}  {len(no):7d} {(st.mean([x["y"] for x in no]) if no else 0):9.3f}')
sub=[x for x in P if 0.10<=x['p']<0.50]
for lab,g in (('pole',[x for x in sub if x['is_pole']]),('non-pole',[x for x in sub if not x['is_pole']])):
    print(f'{lab}: n={len(g)} meanp={st.mean([x["p"] for x in g]):.3f} win={st.mean([x["y"] for x in g]):.3f} resid={st.mean([x["y"]-x["p"] for x in g]):+.4f} mean_net={st.mean([net(x["y"],x["p"]) for x in g]):+.4f}')
print('\ncheap-driver strategies:')
for cap in (0.05,0.10,0.15,0.20,0.30):
    g=[x for x in P if x['p']<=cap]
    print(f'  p<={cap:.2f} n={len(g)} wins={sum(1 for x in g if x["y"]==1)} mean_net={st.mean([net(x["y"],x["p"]) for x in g]):+.4f}')
byev=collections.defaultdict(list)
for x in P: byev[x['key']].append(x)
print('\npole vs favorite:')
for lab,cond in (('pole is favorite',lambda po,fav: po['driver']==fav['driver']),('pole not favorite',lambda po,fav: po['driver']!=fav['driver'])):
    g=[]
    for k,arr in byev.items():
        fav=max(arr,key=lambda z:z['p']); po=[z for z in arr if z['is_pole']]
        if po and cond(po[0],fav): g.append(po[0])
    print(f'  {lab}: n={len(g)} meanp={st.mean([x["p"] for x in g]):.3f} win={st.mean([x["y"] for x in g]):.3f} net={st.mean([net(x["y"],x["p"]) for x in g]):+.4f}')
# number of markets per event
print('\nmarkets per event: n events',len(byev),'min',min(len(v) for v in byev.values()),'median',st.median([len(v) for v in byev.values()]),'max',max(len(v) for v in byev.values()))
