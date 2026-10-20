import json, csv
rows=json.load(open('ask_quotes.json'))
# prior d4 from dataset
ds=list(csv.DictReader(open('dataset.csv')))
prior={}
for r in ds:
    if r['kind']=='state':
        prior[(r['week'],r['state'])]=float(r['prior_d4'])
for r in rows: r['prior']=prior.get((r['week'],r['state']))
def run(side, thr, age=72, spread=0.0, rate=0.05):
    ts=[]
    for r in rows:
        p=r['prior']
        if p is None: continue
        if side=='YES':
            if p<0.05: continue
            q=r['ask']
            if q is None or r['ask_age']>age or q>thr: continue
            fill=q+spread; payoff=1 if r['res'] else 0
        else:
            if p!=0: continue
            # no ask = 1 - yes bid
            if r['bid'] is None or r['bid_age']>age: continue
            noask=1-r['bid']
            if (1-noask)<thr: continue  # yes price >= thr
            fill=noask+spread; payoff=0 if r['res'] else 1
        if fill>=1: continue
        fee=rate*fill*(1-fill)
        pnl=payoff-fill-fee
        ts.append((r,pnl,fill+fee,fill,fee))
    if not ts: return
    pnl=sum(t[1] for t in ts); cap=sum(t[2] for t in ts)
    print(f'side {side} thr {thr} n {len(ts)} wins {sum(1 for t in ts if t[1]>0)} pnl {pnl:+.4f} cap {cap:.4f} ROI {pnl/cap:+.3%}')
    return ts
for thr in [0.99,0.97,0.95,0.93,0.90,0.85,0.80]:
    run('YES',thr)
print()
for thr in [0.05,0.10,0.15,0.20,0.30]:
    run('NO',thr)
print('\nPrimary YES thr .95 details:')
ts=run('YES',0.95)
for r,pnl,cost,fill,fee in ts:
    print(f"{r['week']} {r['state']} prior {r['prior']:.2f} ask {r['ask']:.3f} age {r['ask_age']:.1f} sz {r['ask_size']} res {r['res']} pnl {pnl:+.4f}")
print('\nPrimary NO thr .10 details:')
ts=run('NO',0.10)
for r,pnl,cost,fill,fee in ts:
    print(f"{r['week']} {r['state']} prior {r['prior']:.2f} yesbid {r['bid']:.3f} age {r['bid_age']:.1f} sz {r['bid_size']} res {r['res']} pnl {pnl:+.4f}")
