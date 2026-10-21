import json, urllib.request, time, sys, re, collections
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
        rows=[];off=0;pages=0
        while True:
            d=get(f'https://api.jolpi.ca/ergast/f1/{season}/{kind}.json?limit=100&offset={off}')
            if not d: break
            mr=d['MRData']; tot=int(mr['total']); rows.extend(mr['RaceTable']['Races']); off+=100; pages+=1
            if off>=tot: break
        raw[f'{season}_{kind}']=rows
        print(f'{season} {kind}: pages={pages} total_rows={tot} race_objects={len(rows)} unique_rounds={len({r["round"] for r in rows})}',flush=True)
json.dump(raw,open('_cache/ergast_raw.json','w'))
races={}
for season in range(2014,2027):
    # merge split race objects across pages, dedupe by driverId
    def merge(kind,key):
        by={}
        for r in raw[f'{season}_{kind}']:
            rnd=int(r['round']); by.setdefault(rnd,{'race':r,'rows':[]})
            by[rnd]['rows'].extend(r.get(key,[]))
        out={}
        for rnd,v in by.items():
            seen={}
            for x in v['rows']:
                d=x['Driver']['driverId']
                if d not in seen: seen[d]=x
                else:
                    # keep entry with more useful fields / lower position
                    try:
                        if int(x.get('position',99))<int(seen[d].get('position',99)): seen[d]=x
                    except Exception: pass
            out[rnd]=(v['race'],list(seen.values()))
        return out
    q=merge('qualifying','QualifyingResults'); res=merge('results','Results')
    for rnd in sorted(res):
        rd=rnd and res[rnd][0]
        loc=rd['Circuit'].get('Location',{})
        rec={'season':season,'round':rnd,'name':rd['raceName'],'date':rd['date'],'time':rd.get('time'),
             'circuit':rd['Circuit']['circuitId'],'country':loc.get('country'),'locality':loc.get('locality')}
        if rnd in q:
            qual=[]
            for x in q[rnd][1]:
                best=None
                for kk in ('Q3','Q2','Q1'):
                    v=tsec(x.get(kk))
                    if v is not None and (best is None or v<best): best=v
                qual.append({'d':x['Driver']['driverId'],'pos':int(x['position']),'best':best})
            qual.sort(key=lambda z:z['pos'])
            if qual:
                rec['pole']=qual[0]['d']; rec['pole_best']=qual[0]['best']
                oth=[z['best'] for z in qual[1:] if z['best'] is not None]
                rec['margin']=round(min(oth)-qual[0]['best'],3) if qual[0]['best'] and oth else None
                rec['n_qual']=len(qual)
        rr=res[rnd][1]
        if rr:
            w=min(rr,key=lambda x:int(x['position']))
            rec['winner']=w['Driver']['driverId']; rec['n_res']=len(rr)
            rec['grid']=w.get('grid')
        races[f'{season}-{rnd}']=rec
json.dump(races,open('_cache/races.json','w'),indent=0)
print('races',len(races))
bad=[(k,v.get('n_qual'),v.get('n_res')) for k,v in races.items() if v.get('n_qual',0)<18 or v.get('n_res',0)<18]
print('races with <18 qual or results:',len(bad),bad[:20])
print('with time',sum(1 for v in races.values() if v.get('time')))
