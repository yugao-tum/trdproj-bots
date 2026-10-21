import json, urllib.request, time, sys, re
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f:
                return json.load(f)
        except Exception as e:
            print('retry',u,e,file=sys.stderr); time.sleep(2)
    return None
def tsec(s):
    if not s: return None
    m=re.match(r'^(?:(\d+):)?(\d+):(\d+\.?\d*)$',s)
    if m: return int(m.group(1) or 0)*3600+int(m.group(2))*60+float(m.group(3))
    m=re.match(r'^(\d+):(\d+\.?\d*)$',s)
    if m: return int(m.group(1))*60+float(m.group(2))
    return None
raw={}
for season in range(2014,2027):
    for kind in ('qualifying','results'):
        rows=[];off=0
        while True:
            d=get(f'https://api.jolpi.ca/ergast/f1/{season}/{kind}.json?limit=100&offset={off}')
            if not d: break
            mr=d['MRData']; tot=int(mr['total']); rows.extend(mr['RaceTable']['Races']); off+=100
            if off>=tot: break
        raw[f'{season}_{kind}']=rows
json.dump(raw,open('_cache/ergast_raw.json','w'))
races={}
for season in range(2014,2027):
    q={int(x['round']):x for x in raw[f'{season}_qualifying']}
    r={int(x['round']):x for x in raw[f'{season}_results']}
    for rnd,rd in r.items():
        loc=rd['Circuit'].get('Location',{})
        rec={'season':season,'round':rnd,'name':rd['raceName'],'date':rd['date'],'time':rd.get('time'),
             'circuit':rd['Circuit']['circuitId'],'country':loc.get('country'),'locality':loc.get('locality')}
        qq=q.get(rnd)
        if qq:
            qual=[]
            for x in qq.get('QualifyingResults',[]):
                best=None
                for kk in ('Q3','Q2','Q1'):
                    v=tsec(x.get(kk))
                    if v is not None and (best is None or v<best): best=v
                qual.append({'d':x['Driver']['driverId'],'pos':int(x['position']),'best':best})
            qual.sort(key=lambda z:z['pos'])
            if qual:
                rec['pole']=qual[0]['d']; rec['pole_best']=qual[0]['best']
                rec['margin']=round(qual[1]['best']-qual[0]['best'],3) if len(qual)>1 and qual[0]['best'] and qual[1]['best'] else None
        res=rd.get('Results',[])
        if res:
            w=min(res,key=lambda x:int(x['position']))
            rec['winner']=w['Driver']['driverId']
        races[f'{season}-{rnd}']=rec
json.dump(races,open('_cache/races.json','w'),indent=0)
print('races',len(races),'with time',sum(1 for v in races.values() if v.get('time')))
