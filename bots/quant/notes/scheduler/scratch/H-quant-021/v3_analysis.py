import json,urllib.request,time,statistics as st,random,math,datetime as dt
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f: return json.load(f)
        except Exception as e:
            err=e; time.sleep(1.2*(a+1))
    return {'_err':str(err)}
M=json.load(open('_cache/winner_map.json')); RACES=json.load(open('_cache/races.json'))
CUTS={x['key']:x for x in json.load(open('_cache/v3_cuts.json'))}
def fee(p,rate=0.05): return rate*p*(1-p)
def net(y,p,rate=0.05,half=0.01): return y-p-fee(p,rate)-half
def vwap(fills,cap):
    q=0.0;c=0.0
    for t in fills:
        take=min(t['size'],cap-q)
        if take<=0: break
        c+=take*t['price']; q+=take
        if q>=cap-1e-9: break
    return (c/q if q>1e-12 else None, q)
BINS=[(0,0.05),(0.05,0.20),(0.20,0.50),(0.50,99)]
fit=[r for r in RACES.values() if 2014<=r['season']<=2023 and r.get('pole') and r.get('winner')]
rates=[]; fitn=[]
for lo,hi in BINS:
    sub=[r for r in fit if r.get('margin') is not None and lo<=r['margin']<hi]
    w=sum(1 for r in sub if r['pole']==r['winner']); fitn.append(len(sub)); rates.append((w+1)/(len(sub)+2))
P0=sum(1 for r in fit if r['pole']==r['winner'])/len(fit)
def mA(m):
    if m is None: return 0.333
    for (lo,hi),p in zip(BINS,rates):
        if lo<=m<hi: return p
    return 0.333
rows=[]
for key,x in sorted(M.items()):
    j=json.load(open(f'_cache/trades/{key}.json')); cut=CUTS[key]['cut']; start=CUTS[key]['start']; tok=j['yes_token']
    tr=[t for t in j['trades'] if t['asset']==tok]
    pre=sorted([t for t in tr if t['timestamp']<=cut],key=lambda z:z['timestamp'])
    post=sorted([t for t in tr if cut<t['timestamp']<start],key=lambda z:z['timestamp'])
    buys=[t for t in post if t['side']=='BUY']
    u=f"https://clob.polymarket.com/prices-history?market={tok}&startTs={cut-3*86400}&endTs={cut}&fidelity=60"
    h=get(u); hist=h.get('history') if isinstance(h,dict) else None
    p_hist=hist[-1]['p'] if hist else None
    p_api=pre[-1]['price'] if pre else None
    first=buys[0]['price'] if buys else None
    e20,q20=vwap(buys,20); e100,q100=vwap(buys,100)
    # execution-delay scenarios: discard fills before cut+delay
    def delayed(dh):
        b=[t for t in buys if t['timestamp']>=cut+dh*3600]
        f=b[0]['price'] if b else None
        e,qq=vwap(b,100)
        return f,e,qq
    f1,e1,q1=delayed(1); f3,e3,q3=delayed(3)
    try: y=float(json.loads(j['mkt']['outcomePrices'])[0])
    except Exception: y=None
    m=mA(x['race'].get('margin'))
    rows.append(dict(key=key,race=x['race']['name'],season=x['race']['season'],round=x['race']['round'],
        pole=j['pole'],margin=x['race'].get('margin'),modelA=m,y=y,p_hist=p_hist,p_api=p_api,
        first=first,exec20=e20,exec100=e100,q100=q100,first1=f1,exec100_1h=e1,q100_1h=q1,first3=f3,exec100_3h=e3,q100_3h=q3,
        n_buy=len(buys),n_pre=len(pre),pole_win=x['race'].get('pole')==x['race'].get('winner'),
        pm_ergast_ok=(x['race'].get('winner')==j.get('ergast_winner')) if j.get('ergast_winner') else None))
    print(f"{key:>8} {x['race']['name'][:26]:26} p_hist={p_hist} first={first} e100={e100} q100={q100 and round(q100,1)} nbuy={len(buys)}",flush=True)
json.dump(rows,open('_cache/v3_rows.json','w'),indent=0)
print('\n=== model fit 2014-2023 ===')
for (lo,hi),p,n in zip(BINS,rates,fitn): print(f'  [{lo},{hi}) n={n} p={p:.4f}')
print(f'  constant {sum(1 for r in fit if r["pole"]==r["winner"])}/{len(fit)} = {P0:.4f}')
print('\n=== sample ===')
print('events',len(rows),'pole wins PM',sum(1 for r in rows if r['y']==1),'mean p_hist',round(st.mean([r['p_hist'] for r in rows if r['p_hist'] is not None]),4),
      'mean modelA',round(st.mean([r['modelA'] for r in rows]),4))
print('pole won per PM:',sum(1 for r in rows if r['y']==1),'of',len(rows),'; PM pole outcome vs Ergast pole-won mismatch:',sum(1 for r in rows if r['pole_win']!=bool(r['y']==1)))
print('p_hist available',sum(1 for r in rows if r['p_hist'] is not None),'first',sum(1 for r in rows if r['first'] is not None),
      'exec100',sum(1 for r in rows if r['exec100'] is not None),'exec100_1h',sum(1 for r in rows if r['exec100_1h'] is not None),'exec100_3h',sum(1 for r in rows if r['exec100_3h'] is not None))
def sel(model,cushion=0.05,fill='exec100'):
    out=[]
    for r in rows:
        m=mA(r['margin']) if model=='A' else P0
        if r['p_hist'] is not None and r[fill] is not None and r['p_hist']<=m-cushion: out.append(r)
    return out
def s(name,rr,fill='exec100',rate=0.05,half=0.01,show=True):
    v=[net(r['y'],r[fill],rate,half) for r in rr]
    if show: print(f'{name:48s} n={len(rr):2d} wins={sum(1 for r in rr if r["y"]==1):2d} sum={sum(v):+8.4f} mean={(st.mean(v) if v else 0):+8.4f} sd={(st.pstdev(v) if len(v)>1 else 0):.4f}')
    return v
print('\n=== rules: fill basis (event-day 00:00 UTC cutoff) ===')
for fill in ('p_hist','first','exec20','exec100','exec100_1h','exec100_3h','first1','first3'):
    for model in ('A','B'):
        s(f'rule {model} {fill}',sel(model,fill=fill),fill)
print('\n=== rule A by season, exec100 / delayed ===')
for sn in (2024,2025,2026):
    for fill in ('exec100','exec100_1h','exec100_3h'):
        s(f'A {sn} {fill}',[r for r in sel('A',fill=fill) if r['season']==sn],fill)
print('\n=== unconditional all pole sitters ===')
for fill in ('exec100','exec100_3h'):
    s(f'all pole {fill}',[r for r in rows if r[fill] is not None],fill)
print('\n=== exec price gap vs p_hist ===')
for fill in ('first','exec100','exec100_1h','exec100_3h'):
    d=[r[fill]-r['p_hist'] for r in rows if r[fill] is not None and r['p_hist'] is not None]
    print(f'  {fill}-p_hist n={len(d)} mean={st.mean(d):+.4f} median={st.median(d):+.4f} min={min(d):+.4f} max={max(d):+.4f}')
print('\n=== break-even uniform gap for rule A exec100 ===')
base=sel('A')
for u in [x/1000 for x in range(0,401,10)]:
    tot=sum(net(r['y'],r['exec100']+u) for r in base)
    if tot<=0: print('  break-even gap',u); break
else: print('  >0.40')
print('\n=== cost sensitivity rule A exec100 ===')
for rate in (0.03,0.05,0.07):
    for half in (0.0,0.01,0.02,0.05):
        v=[net(r['y'],r['exec100'],rate,half) for r in base]
        print(f'  fee={rate:.2f} half={half:.2f} mean={st.mean(v):+.4f}')
print('\n=== cushion sensitivity rule A exec100 ===')
for c in (0.0,0.02,0.05,0.08,0.10,0.15):
    s(f'A cushion {c:.2f}',sel('A',cushion=c))
print('\n=== bootstrap rule A exec100 ===')
for lab,fill in (('exec100','exec100'),('exec100_1h','exec100_1h'),('exec100_3h','exec100_3h')):
    rr=sel('A',fill=fill); v=[net(r['y'],r[fill]) for r in rr]
    random.seed(20261021); n=len(v); bs=sorted(st.mean([v[random.randrange(n)] for _ in range(n)]) for _ in range(20000))
    print(f'  {lab}: n={n} mean={st.mean(v):+.4f} sd={st.pstdev(v):.4f} t={st.mean(v)/(st.pstdev(v)/math.sqrt(n)):.2f} CI95=[{bs[500]:+.4f},{bs[19499]:+.4f}] P(mean<=0)={sum(1 for x in bs if x<=0)/len(bs):.4f}')
print('\n=== timing (triggered A, n=%d) ==='%len(base))
fd=[];q100t=[];vols=[]
for r in base:
    j=json.load(open(f"_cache/trades/{r['key']}.json")); cut=CUTS[r['key']]['cut']; start=CUTS[r['key']]['start']; tok=j['yes_token']
    tr=sorted([t for t in j['trades'] if t['asset']==tok and cut<t['timestamp']<start and t['side']=='BUY'],key=lambda z:z['timestamp'])
    fd.append((tr[0]['timestamp']-cut)/3600); vols.append(sum(t['size'] for t in tr))
    q=0
    for t in tr:
        q+=t['size']
        if q>=100: q100t.append((t['timestamp']-cut)/3600); break
print('  first BUY delay h: median',round(st.median(fd),2),'max',round(max(fd),2),'min',round(min(fd),2))
print('  100-share completion h: median',round(st.median(q100t),2),'max',round(max(q100t),2),'min',round(min(q100t),2))
print('  window BUY volume: min',round(min(vols)),'median',round(st.median(vols)),'max',round(max(vols)))
