import json, os

def point_in_ring(pt, ring):
    x,y=pt; inside=False; n=len(ring)
    j=n-1
    for i in range(n):
        xi,yi=ring[i][:2]; xj,yj=ring[j][:2]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi)+xi):
            inside=not inside
        j=i
    return inside

def in_polygon(pt, geom):
    t=geom['type']; c=geom['coordinates']
    if t=='Polygon':
        if not c: return False
        if not point_in_ring(pt,c[0]): return False
        return not any(point_in_ring(pt,h) for h in c[1:])
    if t=='MultiPolygon':
        return any(in_polygon(pt,{'type':'Polygon','coordinates':p}) for p in c)
    return False

def load(fn):
    d=json.load(open(fn)); feats=[]
    for f in d.get('features',[]):
        try: lab=float(f['properties'].get('LABEL','0'))
        except: lab=0.0
        if lab>=0.02-1e-9: feats.append(f['geometry'])
    return feats

def classify(lat,lon,feats):
    return any(in_polygon((lon,lat),g) for g in feats)

ev=json.load(open('_cache/events_meta.json'))
rows=[]; mismatch_final=0
for r in ev:
    cache={}
    for tag,date in [('final',r['next']),('2000',r['prev']),('1630',r['prev'])]:
        hh='0100' if tag=='final' else tag
        cache[tag]=load(f"_cache/geojson/{date}_{hh}_torn.nolyr.geojson")
    for m in r['markets']:
        op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
        out=op[0]=='1'
        c={t:classify(m['lat'],m['lon'],fs) for t,fs in cache.items()}
        if c['final']!=out: mismatch_final+=1
        rows.append({**m,'date':r['date'],'event':r['slug'],**{f'yes_{k}':v for k,v in c.items()},'outcome':out})
json.dump(rows,open('_cache/classified.json','w'),indent=0)
n=len(rows)
print('markets',n,'final mismatch',mismatch_final)
yes=sum(r['outcome'] for r in rows)
print('YES rate',yes,n,round(yes/n,4))
for t in ['final','2000','1630']:
    tp=sum(1 for r in rows if r['yes_'+t] and r['outcome'])
    fp=sum(1 for r in rows if r['yes_'+t] and not r['outcome'])
    fn=sum(1 for r in rows if (not r['yes_'+t]) and r['outcome'])
    tn=n-tp-fp-fn
    print(t,'tp fp fn tn',tp,fp,fn,tn,'acc',round((tp+tn)/n,4),'flip_vs_final',sum(1 for r in rows if r['yes_'+t]!=r['yes_final']))
# per-event YES counts
from collections import Counter
cnt=Counter((r['date'],r['yes_final']) for r in rows)
print('events with >=1 yes',len(set(d for (d,y) in cnt if y)),'of',len(ev))
print('total yes days distribution',Counter(sum(1 for r in rows if r['date']==e['date'] and r['outcome']) for e in ev))
