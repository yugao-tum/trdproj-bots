import csv, json, datetime as dt
from collections import defaultdict
STATES=['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
data={}
for st in STATES:
    rows=[]
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f): rows.append((r['MapDate'],float(r['D4'])))
    rows.sort(); data[st]=rows
def bucket(x):
    if x==0: return '0'
    if x<0.05: return '(0,.05)'
    if x<0.25: return '[.05,.25)'
    if x<1: return '[.25,1)'
    if x<5: return '[1,5)'
    return '>=5'
# all transitions with next date
trans=[]
for st,rows in data.items():
    for i in range(len(rows)-1):
        d0,x=rows[i]; d1,y=rows[i+1]
        if (dt.date(int(d1[:4]),int(d1[4:6]),int(d1[6:]))-dt.date(int(d0[:4]),int(d0[4:6]),int(d0[6:]))).days!=7: continue
        trans.append((d1,bucket(x),y>=0.05))
trans.sort()
rows=json.load(open('ask_quotes.json'))
ds=list(csv.DictReader(open('dataset.csv')))
prior={}
for r in ds:
    if r['kind']=='state': prior[(r['week'],r['state'])]=float(r['prior_d4'])
for r in rows: r['prior']=prior.get((r['week'],r['state']))
def p_bucket(b, before):
    sel=[t for t in trans if t[0]<before and t[1]==b]
    n=len(sel); k=sum(1 for t in sel if t[2])
    return (k+1)/(n+2), n, k
def run(margin=0.05, age=72, slip=0.01, rate=0.05, side='YES', verbose=False):
    ts=[]
    for r in rows:
        p=r['prior']
        if p is None: continue
        week=r['week']; prior_date=(dt.date.fromisoformat(week)-dt.timedelta(days=7)).strftime('%Y%m%d')
        if side=='YES':
            if p<0.05: continue
            q=r['ask']
            if q is None or r['ask_age']>age: continue
            pb,n,k=p_bucket(bucket(p),prior_date)
            if q>pb-margin: continue
            fill=q+slip; payoff=1 if r['res'] else 0; fee=rate*fill*(1-fill)
        else:
            if p!=0: continue
            if r['bid'] is None or r['bid_age']>age: continue
            noask=1-r['bid']; pb,n,k=p_bucket('0',prior_date)
            if noask>(1-pb)-margin: continue
            fill=noask+slip; payoff=0 if r['res'] else 1; fee=rate*fill*(1-fill)
        if fill>=1: continue
        pnl=payoff-fill-fee
        ts.append((r,pnl,fill+fee,fill,pb,n,k))
    if not ts: print('no trades'); return []
    pnl=sum(t[1] for t in ts); cap=sum(t[2] for t in ts)
    print(f'margin {margin} side {side} n {len(ts)} wins {sum(1 for t in ts if t[1]>0)} pnl {pnl:+.4f} cap {cap:.4f} ROI {pnl/cap:+.3%} weeks {len(set(t[0]["week"] for t in ts))}')
    if verbose:
        for r,pnl,cost,fill,pb,n,k in ts:
            print(f"  {r['week']} {r['state']} prior {r['prior']:.2f} ask {r['ask'] if side=='YES' else 1-r['bid']:.3f} age {r['ask_age'] if side=='YES' else r['bid_age']:.1f} pb {pb:.3f} (n={n}) res {r['res']} pnl {pnl:+.4f}")
    return ts
print('Bucket persistence (all history, unadjusted):')
for b in ['0','(0,.05)','[.05,.25)','[.25,1)','[1,5)','>=5']:
    tt=[t for t in trans if t[1]==b]; print(b, len(tt), sum(1 for t in tt if t[2])/len(tt))
print()
for m in [0.03,0.05,0.08,0.10]:
    run(m,side='YES')
print()
for m in [0.03,0.05,0.08,0.10]:
    run(m,side='NO')
print('\nPrimary margin .05 YES details:')
run(0.05,side='YES',verbose=True)
print('\nPrimary margin .05 NO details:')
run(0.05,side='NO',verbose=True)
