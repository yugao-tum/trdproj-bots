import json, statistics as st, random, math
R=json.load(open('_cache/analysis_rows.json'))
ALL=json.load(open('_cache/all_prices.json'))
RACES=json.load(open('_cache/races.json'))
def fee(p,rate=0.05): return rate*p*(1-p) if 0<=p<=1 else 0
def net(y,p,rate=0.05,half=0.01): return y-p-fee(p,rate)-half
BINS=[(0,0.05),(0.05,0.20),(0.20,0.50),(0.50,99)]
fit=[r for r in RACES.values() if 2014<=r['season']<=2023 and r.get('pole') and r.get('winner')]
rates=[]
for lo,hi in BINS:
    sub=[r for r in fit if r.get('margin') is not None and lo<=r['margin']<hi]
    w=sum(1 for r in sub if r['pole']==r['winner'])
    rates.append((w+1)/(len(sub)+2))
P0=sum(1 for r in fit if r['pole']==r['winner'])/len(fit)
print('=== model fit 2014-2023 (corrected Ergast merge) ===')
for (lo,hi),rr in zip(BINS,rates):
    sub=[r for r in fit if r.get('margin') is not None and lo<=r['margin']<hi]
    w=sum(1 for r in sub if r['pole']==r['winner'])
    print(f'  margin [{lo},{hi}) n={len(sub):3d} raw={w}/{len(sub)}={w/len(sub):.4f} laplace={rr:.4f}')
print(f'  constant p0 = {sum(1 for r in fit if r["pole"]==r["winner"])}/{len(fit)} = {P0:.4f}')
def mA(m):
    if m is None: return 0.333
    for (lo,hi),rr in zip(BINS,rates):
        if lo<=m<hi: return rr
    return 0.333
def trig(rows,model='A',fill='exec100',cushion=0.05):
    out=[]
    for r in rows:
        m=mA(r['margin']) if model=='A' else (P0 if model=='B' else model)
        if r['p_hist'] is None or r[fill] is None: continue
        if r['p_hist']<=m-cushion: out.append(r)
    return out
def s(name,rows,fill='exec100',rate=0.05,half=0.01):
    if not rows: print(f'{name:54s} n=0'); return []
    v=[net(r['y'],r[fill],rate,half) for r in rows]
    print(f'{name:54s} n={len(rows):2d} wins={sum(1 for r in rows if r["y"]==1):2d} sum={sum(v):+8.4f} mean={st.mean(v):+8.4f} sd={st.pstdev(v):.4f}')
    return v
print('\n=== sample ===')
print('events',len(R),'seasons',{k:sum(1 for r in R if r['season']==k) for k in (2024,2025,2026)})
print('pole wins (PM settlement)',sum(1 for r in R if r['y']==1),'/',len(R),'mean p_hist',round(st.mean([r['p_hist'] for r in R]),4),'mean modelA',round(st.mean([mA(r['margin']) for r in R]),4))
print('\n=== 1. rule A/B by season (fill=exec100) ===')
for model in ('A','B'):
    for sn in (2024,2025,2026):
        s(f'rule {model} {sn}',trig([r for r in R if r['season']==sn],model))
    s(f'rule {model} all',trig(R,model))
print('\n=== 2. unconditional every pole sitter ===')
for sn in (2024,2025,2026):
    s(f'all pole {sn}',[r for r in R if r['season']==sn and r['exec100'] is not None])
s('all pole',[r for r in R if r['exec100'] is not None])
print('\n=== 3. limit-order semantics: trigger AND fill at executable price ===')
for model in ('A','B'):
    for fill in ('first_buy_price','exec100'):
        rows=[r for r in R if r['p_hist'] is not None and r[fill] is not None and r[fill]<= (mA(r['margin']) if model=='A' else P0)-0.05]
        s(f'{model} trigger&fill {fill}',rows,fill)
print('\n=== 4. cost sensitivity, rule A exec100 ===')
base=trig(R,'A')
for rate in (0.0,0.03,0.05,0.07):
    for half in (0.0,0.01,0.02,0.05):
        v=[net(r['y'],r['exec100'],rate,half) for r in base]
        print(f'  fee={rate:.2f} half={half:.2f}  sum={sum(v):+8.4f} mean={st.mean(v):+7.4f}')
print('\n=== 5. cushion sensitivity, rule A ===')
for c in (0.0,0.02,0.05,0.08,0.10,0.15):
    s(f'A cushion {c:.2f}',trig(R,'A',cushion=c))
print('\n=== 6. bootstrap mean net/share, rule A exec100 ===')
v=[net(r['y'],r['exec100']) for r in base]
random.seed(20261021); n=len(v); bs=[]
for _ in range(20000):
    bs.append(st.mean([v[random.randrange(n)] for _ in range(n)]))
bs.sort()
print('n',n,'mean',round(st.mean(v),4),'sd',round(st.pstdev(v),4),'t',round(st.mean(v)/(st.pstdev(v)/math.sqrt(n)),2))
print('95% percentile CI',round(bs[500],4),round(bs[19499],4),'P(mean<=0)',round(sum(1 for x in bs if x<=0)/len(bs),5))
print('\n=== 7. bootstrap pole calibration residual y-p_hist (49 events) ===')
d=[r['y']-r['p_hist'] for r in R if r['p_hist'] is not None]
random.seed(7); n=len(d); bs=[st.mean([d[random.randrange(n)] for _ in range(n)]) for _ in range(20000)]; bs.sort()
print('n',n,'mean',round(st.mean(d),4),'95% CI',round(bs[500],4),round(bs[19499],4),'P(<=0)',round(sum(1 for x in bs if x<=0)/len(bs),5))
print('\n=== 8. walk-forward (fit on all races before each season) ===')
byseason={}
for r in RACES.values():
    if r.get('pole') and r.get('winner'): byseason.setdefault(r['season'],[]).append(r)
for S in (2024,2025,2026):
    hist=[r for s0 in range(2014,S) for r in byseason.get(s0,[])]
    p0=sum(1 for r in hist if r['pole']==r['winner'])/len(hist)
    rr=[]
    for lo,hi in BINS:
        sub=[r for r in hist if r.get('margin') is not None and lo<=r['margin']<hi]
        w=sum(1 for r in sub if r['pole']==r['winner']); rr.append((w+1)/(len(sub)+2))
    def wfA(m):
        if m is None: return 0.333
        for (lo,hi),x in zip(BINS,rr):
            if lo<=m<hi: return x
        return 0.333
    print(f'  season {S}: n_hist={len(hist)} p0={p0:.4f} bins={[round(x,3) for x in rr]}')
    for lab,f in (('wfA',wfA),('wfB',lambda m:p0)):
        rows=[r for r in R if r['season']==S and r['p_hist'] is not None and r['exec100'] is not None and r['p_hist']<=f(r['margin'])-0.05]
        vv=[net(r['y'],r['exec100']) for r in rows]
        print(f'    {lab}: n={len(rows):2d} wins={sum(1 for r in rows if r["y"]==1):2d} sum={sum(vv):+.4f} mean={(st.mean(vv) if vv else 0):+.4f}')
print('\n=== 9. all-driver calibration at cutoff ===')
P=[x for x in ALL if x['p'] is not None and x['y'] is not None]
print('markets with p and y',len(P),'of',len(ALL))
sums={}
for x in P: sums.setdefault(x['key'],0.0); sums[x['key']]+=x['p']
ss=sorted(sums.values()); print('price-sum per event: n',len(ss),'median',round(st.median(ss),3),'min',round(min(ss),3),'max',round(max(ss),3),'<=1.17',sum(1 for x in ss if x<=1.17),'of',len(ss))
bins=[(0,0.05),(0.05,0.10),(0.10,0.20),(0.20,0.30),(0.30,0.50),(0.50,0.70),(0.70,1.01)]
print(f'{"bucket":>12} {"n":>4} {"meanp":>7} {"winrate":>8} {"mean_net":>9}   pole_n pole_win  nonpole_n nonpole_win')
for lo,hi in bins:
    sub=[x for x in P if lo<=x['p']<hi]
    if not sub: continue
    pole=[x for x in sub if x['is_pole']]; non=[x for x in sub if not x['is_pole']]
    print(f'[{lo:.2f},{hi:.2f}) {len(sub):4d} {st.mean([x["p"] for x in sub]):7.3f} {st.mean([x["y"] for x in sub]):8.3f} {st.mean([net(x["y"],x["p"]) for x in sub]):+9.4f}   {len(pole):6d} {st.mean([x["y"] for x in pole]) if pole else 0:8.3f}  {len(non):8d} {st.mean([x["y"] for x in non]) if non else 0:10.3f}')
print('\n=== 10. cheap-driver strategies (all drivers) ===')
for cap in (0.05,0.10,0.15,0.20,0.30):
    sub=[x for x in P if x['p']<=cap]
    print(f'  buy all p<={cap:.2f}: n={len(sub):4d} wins={sum(1 for x in sub if x["y"]==1):3d} mean_net={st.mean([net(x["y"],x["p"]) for x in sub]):+.4f} sum={sum(net(x["y"],x["p"]) for x in sub):+.2f}')
print('\n=== 11. pole vs non-pole, price 0.10-0.50 ===')
sub=[x for x in P if 0.10<=x['p']<0.50]
for lab,g in (('pole',[x for x in sub if x['is_pole']]),('non-pole',[x for x in sub if not x['is_pole']])):
    print(f'  {lab}: n={len(g)} meanp={st.mean([x["p"] for x in g]):.3f} win={st.mean([x["y"] for x in g]):.3f} resid={st.mean([x["y"]-x["p"] for x in g]):+.4f} mean_net={st.mean([net(x["y"],x["p"]) for x in g]):+.4f}')
print('\n=== 12. favorites vs pole ===')
byev={}
for x in P: byev.setdefault(x['key'],[]).append(x)
fav=[];pf=[];pnf=[]
for k,g in byev.items():
    top=max(g,key=lambda z:z['p']); fav.append(top)
    pol=[z for z in g if z['is_pole']]
    if pol:
        (pf if pol[0]['token']==top['token'] else pnf).append(pol[0])
for lab,g in (('favorite',fav),('pole=favorite',pf),('pole!=favorite',pnf)):
    print(f'  {lab}: n={len(g)} meanp={st.mean([x["p"] for x in g]):.4f} win={st.mean([x["y"] for x in g]):.4f} resid={st.mean([x["y"]-x["p"] for x in g]):+.4f} net={st.mean([net(x["y"],x["p"]) for x in g]):+.4f} total={sum(net(x["y"],x["p"]) for x in g):+.4f}')
print('\n=== 13. rule A trade list (exec100) ===')
for r in sorted(base,key=lambda z:z['key']):
    print(f'  {r["key"]:8s} {r["race"][:24]:24s} pole={r["pole"]:16s} margin={str(r["margin"]):>7s} model={mA(r["margin"]):.3f} p_hist={r["p_hist"]:.4f} fill={r["exec100"]:.4f} y={r["y"]:.0f} net={net(r["y"],r["exec100"]):+.4f}')
print('n',len(base),'sum',round(sum(net(r['y'],r['exec100']) for r in base),4))
print('\n=== 14. dust p_hist<0.02 ===')
for r in R:
    if r['p_hist'] is not None and r['p_hist']<0.02:
        print(f'  {r["key"]} {r["race"]} p_hist={r["p_hist"]} first={r["first_buy_price"]} size={r["first_buy_size"]} exec100={r["exec100"]} y={r["y"]} A={r["p_hist"]<=mA(r["margin"])-0.05} B={r["p_hist"]<=P0-0.05}')
