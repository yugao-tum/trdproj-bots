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
ROWS={r['key']:r for r in json.load(open('_cache/v3_rows.json'))}
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
# --- 1. qualifying timing vs cutoff ---
slacks=[]
for k,x in sorted(M.items()):
    c=CUTS[k]
    slacks.append((c['cut']-c['cut_q'])/3600)
print('=== qualifying-end (start+2h) vs cutoff (race-day 00:00 UTC) ===')
print('n',len(slacks),'min slack h',round(min(slacks),3),'median',round(st.median(slacks),3),'max',round(max(slacks),3),'all cut_q<=cut',all(s>=0 for s in slacks))
# --- 2. PM vs Ergast disagreement ---
dis=[r for r in ROWS.values() if r['y'] is not None and r['pole_win']!=bool(r['y']==1)]
print('PM pole outcome vs Ergast pole-won mismatch:',len(dis),'of',len(ROWS),dis)
# --- 3. timing + volume for triggered A ---
def trig(rows,model='A',cushion=0.05,fill='exec100'):
    return [r for r in rows if r['p_hist'] is not None and r[fill] is not None and r['p_hist']<=(mA(r['margin']) if model=='A' else P0)-cushion]
base=trig(list(ROWS.values()))
fd=[];td=[];vols=[];q100t=[]
for r in base:
    j=json.load(open(f"_cache/trades/{r['key']}.json")); cut=CUTS[r['key']]['cut']; start=CUTS[r['key']]['start']; tok=j['yes_token']
    tr=sorted([t for t in j['trades'] if t['asset']==tok and cut<t['timestamp']<start and t['side']=='BUY'],key=lambda z:z['timestamp'])
    fd.append((tr[0]['timestamp']-cut)/3600)
    vols.append(sum(t['size'] for t in tr))
    q=0
    for t in tr:
        q+=t['size']
        if q>=100: q100t.append((t['timestamp']-cut)/3600); break
print('=== triggered A (n=%d): execution timing & volume ==='%len(base))
for lab,d in (('first BUY delay h',fd),('100-share completion h',q100t)):
    print(f'  {lab}: median {st.median(d):.2f} max {max(d):.2f} min {min(d):.2f}')
print(f'  window BUY volume shares: min {min(vols):.0f} median {st.median(vols):.0f} max {max(vols):.0f}')
# --- 4. alternative cutoff: qualifying end +2h (actual implementation) ---
alt={}
for k,x in sorted(M.items()):
    c=CUTS[k]; cut=c['cut_q']; start=c['start']; j=json.load(open(f"_cache/trades/{k}.json")); tok=j['yes_token']
    tr=[t for t in j['trades'] if t['asset']==tok]
    pre=sorted([t for t in tr if t['timestamp']<=cut],key=lambda z:z['timestamp'])
    buys=sorted([t for t in tr if cut<t['timestamp']<start and t['side']=='BUY'],key=lambda z:z['timestamp'])
    h=get(f"https://clob.polymarket.com/prices-history?market={tok}&startTs={cut-3*86400}&endTs={cut}&fidelity=60")
    hist=h.get('history') if isinstance(h,dict) else None
    p=hist[-1]['p'] if hist else None
    e100,q=vwap(buys,100); f=buys[0]['price'] if buys else None
    alt[k]={'p_hist_q':p,'exec100_q':e100,'first_q':f,'y':ROWS[k]['y'],'margin':ROWS[k]['margin'],'season':ROWS[k]['season'],'nbuy':len(buys)}
json.dump(alt,open('_cache/v3_altq.json','w'),indent=0)
print('\n=== rule A/B with cutoff = qualifying end +2h ===')
print('p_hist_q available',sum(1 for v in alt.values() if v['p_hist_q'] is not None),'exec100_q',sum(1 for v in alt.values() if v['exec100_q'] is not None))
def s2(name,rr,fill):
    v=[net(r['y'],r[fill]) for r in rr]
    print(f'{name:34s} n={len(rr):2d} wins={sum(1 for r in rr if r["y"]==1):2d} sum={sum(v):+8.4f} mean={(st.mean(v) if v else 0):+8.4f} sd={(st.pstdev(v) if len(v)>1 else 0):.4f}')
    return v
for model in ('A','B'):
    for fill in ('first_q','exec100_q'):
        rr=[v for k,v in alt.items() if v['p_hist_q'] is not None and v[fill] is not None and v['p_hist_q']<=(mA(v['margin']) if model=='A' else P0)-0.05]
        s2(f'{model} {fill}',rr,fill)
    for sn in (2024,2025,2026):
        fill='exec100_q'
        rr=[v for k,v in alt.items() if v['season']==sn and v['p_hist_q'] is not None and v[fill] is not None and v['p_hist_q']<=(mA(v['margin']) if model=='A' else P0)-0.05]
        s2(f'{model} {sn} {fill}',rr,fill)
# gap between q-cutoff price and midnight price
d=[alt[k]['p_hist_q']-ROWS[k]['p_hist'] for k in alt if alt[k]['p_hist_q'] is not None and ROWS[k]['p_hist'] is not None]
print(f'p_hist_q - p_hist(midnight): n={len(d)} mean={st.mean(d):+.4f} median={st.median(d):+.4f} min={min(d):+.4f} max={max(d):+.4f}')
# --- 5. binomial test 32/49 vs 110/204 ---
try:
    from math import comb
    n=49; k=32; p0=110/204
    def binom_cdf(k,n,p): return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(0,k+1))
    # two-sided exact-ish: 2*min(P(X>=k),P(X<=k))
    pg=1-binom_cdf(k-1,n,p0); pl=binom_cdf(k,n,p0)
    print(f'\n32/49 vs 110/204: P(X>=32|p0)={pg:.4f} two-sided~{min(1,2*min(pg,pl)):.4f}')
except Exception as e: print(e)
