import json,urllib.request,time,statistics as st
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f: return json.load(f)
        except Exception as e:
            err=e; time.sleep(1.2*(a+1))
    return {'_err':str(err)}
M=json.load(open('_cache/winner_map.json')); CUTS={x['key']:x for x in json.load(open('_cache/v3_cuts.json'))}
ROWS={r['key']:r for r in json.load(open('_cache/v3_rows.json'))}
RACES=json.load(open('_cache/races.json'))
BINS=[(0,0.05),(0.05,0.20),(0.20,0.50),(0.50,99)]
fit=[r for r in RACES.values() if 2014<=r['season']<=2023 and r.get('pole') and r.get('winner')]
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
def fee(p,rate=0.05): return rate*p*(1-p)
def net(y,p,rate=0.05,half=0.01): return y-p-fee(p,rate)-half
def vwap(fills,cap):
    q=0.0;c=0.0
    for t in fills:
        take=min(t['size'],cap-q)
        if take<=0: break
        c+=take*t['price']; q+=take
        if q>=cap-1e-9: break
    return (c/q if q>1e-12 else None,q)
out={}
for k,x in sorted(M.items()):
    c=CUTS[k]; tok=json.load(open(f'_cache/trades/{k}.json'))['yes_token']
    rec={'season':ROWS[k]['season'],'margin':ROWS[k]['margin'],'y':ROWS[k]['y']}
    for lab,cut in (('mid',c['cut']),('q',c['cut_q'])):
        h=get(f"https://clob.polymarket.com/prices-history?market={tok}&startTs={cut-3*86400}&endTs={cut}&fidelity=60")
        hist=h.get('history') if isinstance(h,dict) else None
        if hist:
            rec[f'p_{lab}']=hist[-1]['p']; rec[f'age_{lab}_h']=(cut-hist[-1]['t'])/3600
        else:
            rec[f'p_{lab}']=None; rec[f'age_{lab}_h']=None
    out[k]=rec
json.dump(out,open('_cache/v3_stale.json','w'),indent=0)
for lab in ('mid','q'):
    a=[v[f'age_{lab}_h'] for v in out.values() if v[f'age_{lab}_h'] is not None]
    print(f'age of last prices-history point at {lab} cutoff (h): n={len(a)} median={st.median(a):.2f} p90={sorted(a)[int(.9*len(a))-1]:.2f} max={max(a):.2f} <=1h={sum(1 for x in a if x<=1):d} <=3h={sum(1 for x in a if x<=3):d} <=6h={sum(1 for x in a if x<=6):d}')
# trigger&fill with executable price only (cutoff=qual end)
alt=json.load(open('_cache/v3_altq.json'))
print('\n=== trigger AND fill at executable price, cutoff=q ===')
for model in ('A','B'):
    for fill,key in (('first_q','first_q'),('exec100_q','exec100_q')):
        rr=[v for v in alt.values() if v[fill] is not None and v[fill]<=(mA(v['margin']) if model=='A' else P0)-0.05]
        vv=[net(v['y'],v[fill]) for v in rr]
        print(f'  {model} {fill}: n={len(rr):2d} wins={sum(1 for v in rr if v["y"]==1):2d} sum={sum(vv):+.4f} mean={(st.mean(vv) if vv else 0):+.4f}')
print('\n=== trigger AND fill at executable price, cutoff=midnight ===')
for model in ('A','B'):
    for fill in ('first','exec100'):
        rr=[r for r in ROWS.values() if r[fill] is not None and r[fill]<=(mA(r['margin']) if model=='A' else P0)-0.05]
        vv=[net(r['y'],r[fill]) for r in rr]
        print(f'  {model} {fill}: n={len(rr):2d} wins={sum(1 for r in rr if r["y"]==1):2d} sum={sum(vv):+.4f} mean={(st.mean(vv) if vv else 0):+.4f}')
