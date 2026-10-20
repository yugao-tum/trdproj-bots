import gzip, json, csv, datetime as dt
from collections import Counter
ev=json.load(gzip.open('_cache/events_closed0.json.gz','rt'))
def d4(st,md):
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f):
            if r['MapDate']==md: return float(r['D4'])
    return None
c=Counter(); n=0
for e in ev:
    if not e['slug'].startswith('state-d4-drought-'): continue
    wk=e['slug'].split('state-d4-drought-')[1]; md=wk.replace('-','')
    prior=(dt.date.fromisoformat(wk)-dt.timedelta(days=7)).strftime('%Y%m%d')
    for m in e['markets']:
        st=m['slug'].split('-')[-1].upper()
        p=d4(st,prior); cur=d4(st,md)
        if p is None or cur is None: continue
        n+=1
        if p==0: c['zero']+=1; c['entry']+=(cur>=0.05)
        elif p<0.05: c['tiny']+=1; c['tiny_entry']+=(cur>=0.05)
        else: c['d4']+=1; c['stay']+=(cur>=0.05)
print('roster state-weeks',n,dict(c))
print('zero entry rate', c['entry']/c['zero'])
print('d4 persist', c['stay']/c['d4'])
