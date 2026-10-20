#!/usr/bin/env python3
"""B22: SPC tornado-risk daily markets - rule validation and update-lag test.
Inputs (keyless, cached under _cache/):
  _cache/events_meta.json       - 62 Gamma events, 25 city markets each, coords from rules
  _cache/geojson/*.geojson      - archived SPC Day-1 tornado probability polygons
  _cache/trades/<conditionId>.json - Polymarket data-api trades
  _cache/last_modified.csv      - HTTP Last-Modified of each archived GeoJSON (fetch_headers.py)
Outputs: prints the numbers cited in quant-025.
"""
import json, csv, datetime, statistics
from collections import defaultdict

CACHE="_cache"; FEE=0.05; BUF=0.01; THRESH=0.25

def point_in_ring(pt, ring):
    x,y=pt; inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i][:2]; xj,yj=ring[j][:2]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi)+xi): inside=not inside
        j=i
    return inside

def in_polygon(pt, geom):
    t=geom['type']; c=geom['coordinates']
    if t=='Polygon':
        return bool(c) and point_in_ring(pt,c[0]) and not any(point_in_ring(pt,h) for h in c[1:])
    if t=='MultiPolygon':
        return any(in_polygon(pt,{'type':'Polygon','coordinates':p}) for p in c)
    return False

def load_probs(fn):
    d=json.load(open(fn)); out=[]
    for f in d.get('features',[]):
        try: lab=float(f['properties'].get('LABEL','0'))
        except Exception: lab=0.0
        if lab>=0.02-1e-9: out.append(f['geometry'])
    return out

def classify(lat,lon,feats): return any(in_polygon((lon,lat),g) for g in feats)

def load_trades(cid):
    t=json.load(open(f'{CACHE}/trades/{cid}.json'))
    for z in t: z['yespx']=z['price'] if z['outcome']=='Yes' else 1-z['price']
    return sorted(t,key=lambda z:z['timestamp'])

def ts(d,h,m):
    y,mo,dd=map(int,d.split('-')); return datetime.datetime(y,mo,dd,h,m,tzinfo=datetime.timezone.utc).timestamp()
def nextts(d,h,m):
    dd=datetime.date.fromisoformat(d)+datetime.timedelta(days=1)
    return datetime.datetime(dd.year,dd.month,dd.day,h,m,tzinfo=datetime.timezone.utc).timestamp()

def load_lm():
    lm={}
    for r in csv.DictReader(open(f'{CACHE}/last_modified.csv')):
        if r['status']=='200' and r['last_modified']:
            dt=datetime.datetime.strptime(r['last_modified'],'%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=datetime.timezone.utc)
            d=r['date']; d=f'{d[:4]}-{d[4:6]}-{d[6:]}' if len(d)==8 else d
            lm[(r['tag'],d)]=dt.timestamp()
    return lm

def main():
    ev=json.load(open(f'{CACHE}/events_meta.json'))
    lm=load_lm()
    rows=[]; mismatch=0
    for r in ev:
        cache={}
        for tag,date in [('final',r['next']),('2000',r['prev']),('1630',r['prev'])]:
            hh='0100' if tag=='final' else tag
            cache[tag]=load_probs(f'{CACHE}/geojson/{date}_{hh}_torn.nolyr.geojson')
        for m in r['markets']:
            op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
            out=op[0]=='1'
            c={t:classify(m['lat'],m['lon'],fs) for t,fs in cache.items()}
            if c['final']!=out: mismatch+=1
            rows.append({**m,'date':r['date'],'event':r['slug'],**{'yes_'+k:v for k,v in c.items()},'outcome':out})
    n=len(rows); nt=sum(len(load_trades(r['conditionId'])) for r in rows)
    print(f'events={len(ev)} markets={n} trades={nt} final_classification_mismatches={mismatch}')
    print(f'YES settlements={sum(r["outcome"] for r in rows)} / {n}; events with >=1 YES={len(set(r["date"] for r in rows if r["outcome"]))}')
    for a,b in [('1630','2000'),('2000','final'),('1630','final')]:
        print(f'{a}->{b} classification flips={sum(1 for r in rows if r["yes_"+a]!=r["yes_"+b])}')
    inside2000=[r for r in rows if r['yes_2000']]
    survive=sum(1 for r in inside2000 if r['yes_final'])
    print(f'inside at 2000={len(inside2000)}; survive to final={survive} ({survive/len(inside2000):.1%})')
    # signal availability = GeoJSON Last-Modified + 2 min
    for tag in ['1630','2000','final']:
        vals=[datetime.datetime.fromtimestamp(v,datetime.timezone.utc) for (t,d),v in lm.items() if t==tag]
        hm=[v.hour*60+v.minute for v in vals]
        print(f'{tag} Last-Modified time-of-day range: {min(hm)//60:02d}:{min(hm)%60:02d} .. {max(hm)//60:02d}:{max(hm)%60:02d} UTC (n={len(vals)})')
    strict=[]; broad=[]
    for r in rows:
        d=r['date']; evr=next(x for x in ev if x['date']==d)
        lm1630=lm.get(('1630',d)); lm2000=lm.get(('2000',d)); lmfinal=lm.get(('final',evr['next']))
        windows=[]
        if r['yes_1630']:
            windows.append(('1630',(lm1630+120) if lm1630 else ts(d,16,45),(lm2000+120) if lm2000 else ts(d,19,55)))
        if r['yes_2000']:
            windows.append(('2000',(lm2000+120) if lm2000 else ts(d,20,20),(lmfinal+120) if lmfinal else nextts(d,1,15)))
        t=load_trades(r['conditionId'])
        for wname,lo,hi in windows:
            z=next((v for v in t if lo<=v['timestamp']<hi and v['side']=='BUY' and v['outcome']=='Yes'),None)
            if z and z['yespx']<=THRESH:
                win=1 if r['outcome'] else 0
                net=win-z['yespx']-FEE*z['yespx']*(1-z['yespx'])-BUF
                strict.append((wname,d,r['q'],z['yespx'],net,z['size'],r['outcome'],z['timestamp'],z['side'],z['outcome']))
            z2=next((v for v in t if lo<=v['timestamp']<hi and v['yespx']<=THRESH),None)
            if z2:
                win=1 if r['outcome'] else 0
                net=win-z2['yespx']-FEE*z2['yespx']*(1-z2['yespx'])-BUF
                broad.append((wname,d,r['q'],z2['yespx'],net,z2['size'],r['outcome'],z2['timestamp'],z2['side'],z2['outcome']))
    for label,arr in [('strict BUY YES',strict),('broad price proxy',broad)]:
        pnl=sum(x[4]*x[5] for x in arr); cost=sum(x[3]*x[5] for x in arr)
        print(f'\n{label}: trades={len(arr)} events={len(set(x[1] for x in arr))} cost=${cost:.2f} net=${pnl:.2f} '
              f'wins={sum(1 for x in arr if x[4]>0)} losses={sum(1 for x in arr if x[4]<=0)} '
              f'max_single_cost=${max((x[3]*x[5] for x in arr),default=0):.2f}')
        for x in sorted(arr,key=lambda x:x[1]):
            when=datetime.datetime.fromtimestamp(x[7],datetime.timezone.utc).strftime('%m-%d %H:%M:%S')
            print(f'  {x[0]} {x[1]} {x[2][:38]:38s} trade={when} {x[8]}/{x[9]} yespx={x[3]:.3f} net/sh={x[4]:+.3f} size={x[5]:.2f} outcome={x[6]} pnl=${x[4]*x[5]:+.2f}')
    per=defaultdict(float); per_sh=defaultdict(float)
    for x in strict: per[x[1]]+=x[3]*x[5]; per_sh[x[1]]+=x[4]*x[5]
    print(f'\nstrict max event cost=${max(per.values()):.2f}; event PnL: '+', '.join(f'{d}:{v:+.2f}' for d,v in sorted(per_sh.items())))
    print('\nstrict-set buffer sensitivity:')
    for buf in [0.01,0.03,0.05]:
        pnl=0; cost=0
        for x in strict:
            win=1 if x[6] else 0
            net=win-x[3]-FEE*x[3]*(1-x[3])-buf
            pnl+=net*x[5]; cost+=x[3]*x[5]
        print(f'  buffer={buf:.2f} cost=${cost:.2f} net=${pnl:.2f}')

if __name__=='__main__': main()
