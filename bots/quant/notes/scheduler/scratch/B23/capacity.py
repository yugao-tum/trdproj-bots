import json,csv,datetime as dt
tr=json.load(open('_cache/trades_all.json'))['trades']
rows=json.load(open('ask_quotes.json'))
ds=list(csv.DictReader(open('dataset.csv')))
prior={}
for r in ds:
    if r['kind']=='state': prior[(r['week'],r['state'])]=float(r['prior_d4'])
for r in rows: r['prior']=prior.get((r['week'],r['state']))
def vol(slug,before=None):
    ts=[t for t in tr.get(slug,[]) if before is None or t['timestamp']<=before]
    return sum(t['size']*t['price'] for t in ts), len(ts), sum(t['size'] for t in ts)
# qualifying YES under primary margin rule (recompute)
import importlib.util
# just hardcode use ask<=pb-.05 approximated by same list from walkforward: recompute quickly
def bucket(x):
    if x==0: return '0'
    if x<0.05: return '(0,.05)'
    if x<0.25: return '[.05,.25)'
    if x<1: return '[.25,1)'
    if x<5: return '[1,5)'
    return '>=5'
STATES=['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
data={}
for st in STATES:
    a=[]
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f): a.append((r['MapDate'],float(r['D4'])))
    a.sort(); data[st]=a
trans=[]
for st,a in data.items():
    for i in range(len(a)-1):
        d0,x=a[i]; d1,y=a[i+1]
        if (dt.date(int(d1[:4]),int(d1[4:6]),int(d1[6:]))-dt.date(int(d0[:4]),int(d0[4:6]),int(d0[6:]))).days==7:
            trans.append((d1,bucket(x),y>=0.05))
def pb(b,before):
    sel=[t for t in trans if t[0]<before and t[1]==b]
    return (sum(1 for t in sel if t[2])+1)/(len(sel)+2)
ev={e['slug']:e for e in json.load(open('_cache/events_closed0.json'))}
qs=[]
for r in rows:
    p=r['prior']
    if p is None or p<0.05 or r['ask'] is None or r['ask_age']>72: continue
    pd=(dt.date.fromisoformat(r['week'])-dt.timedelta(days=7)).strftime('%Y%m%d')
    if r['ask']<=pb(bucket(p),pd)-0.05:
        slug=f"state-d4-drought-{r['week']}-{r['state'].lower()}"
        end=dt.datetime.fromisoformat(ev[f'state-d4-drought-{r["week"]}']['endDate'].replace('Z','+00:00'))
        cut=(end-dt.timedelta(hours=13,minutes=1)).timestamp()
        v0,n0,s0=vol(slug,cut); v1,n1,s1=vol(slug)
        qs.append((r,slug,v0,n0,s0,v1,n1,s1))
print('n',len(qs))
print('last ask share sum',sum(r['ask_size'] for r,_,_,_,_,_,_,_ in qs))
print('notional at ask sum',sum(r['ask_size']*r['ask'] for r,_,_,_,_,_,_,_ in qs))
for r,slug,v0,n0,s0,v1,n1,s1 in qs:
    print(f"{r['week']} {r['state']} ask {r['ask']:.3f} lastsz {r['ask_size']:.1f} preCutVol ${v0:.0f} ({n0} trades, {s0:.0f} sh) allVol ${v1:.0f} ({n1} trades, {s1:.0f} sh)")
