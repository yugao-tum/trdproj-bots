import json, urllib.request, re, collections, time
H={'User-Agent':'research/1.0'}
def get(u,raw=False):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f:
                b=f.read(); return (b if raw else json.loads(b))
        except Exception as e:
            print('  ERR',getattr(e,'code',e),u[:110]); time.sleep(1.5*(a+1))
    return None
print('=== A. Gamma closed F1 events pagination (2026-10-21) ===')
E=[]
for off in (0,100,200,300,400):
    d=get(f'https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset={off}')
    print(f'  offset={off} rows={len(d)}'); E.extend(d)
U={e['id']:e for e in E.values()} if False else {e['id']:e for e in E}
print('  unique events',len(U),'markets',sum(len(e.get('markets',[])) for e in U.values()))
cats=collections.Counter()
for e in U.values():
    t=e.get('title','')
    if re.search(r'Pole Position',t,re.I): cats['Pole']+=1
    elif re.search(r'Podium',t,re.I): cats['Podium']+=1
    elif re.search(r'Winner',t,re.I): cats['Winner']+=1
    elif re.search(r'Sprint',t,re.I): cats['Sprint/other']+=1
    else: cats['Other']+=1
print('  title categories',dict(cats))
print('\n=== B. current US GP example events ===')
for slug in ('f1-united-states-grand-prix-winner-2026-10-25',
             'f1-united-states-grand-prix-driver-pole-position-2026-10-24',
             'f1-united-states-grand-prix-driver-podium-2026-10-25'):
    d=get('https://gamma-api.polymarket.com/events?slug='+slug)
    if not d: print('  MISSING',slug); continue
    e=d[0]
    print(f'  {slug}: markets={len(e.get("markets",[]))} negRisk={e.get("negRisk")} volume={e.get("volume")} liquidity={e.get("liquidity")} restricted={e.get("restricted")}')
    print('    resolutionSource=',e.get('resolutionSource'))
    fs=[m.get('feeSchedule') for m in e.get('markets',[]) if m.get('feeSchedule')]
    print('    feeSchedule sample=',fs[0] if fs else None,'distinct=',len({json.dumps(x,sort_keys=True) for x in fs}))
    desc=(e.get('description') or '')[:900].replace('\n',' ')
    print('    description:',desc)
print('\n=== C. Singapore closed Winner event ===')
d=get('https://gamma-api.polymarket.com/events?slug=f1-singapore-grand-prix-winner-2026-10-11')
if d:
    e=d[0]; print('  markets',len(e['markets']),'volume',e.get('volume'),'closed',e.get('closed'))
    for m in e['markets']:
        if str(m.get('outcomePrices')) in ('["1", "0"]','["1","0"]'):
            print('  resolved YES market:',m.get('groupItemTitle'),m.get('outcomePrices'),'volume',m.get('volume')); break
print('\n=== D. CLOB prices-history parameter checks ===')
T='28558391061191296576456870322949545965070312914289181555918414954825561771030'
for q in ('interval=max&fidelity=60','startTs=1790900000&endTs=1791150000&fidelity=60',
          'startTs=1724544000&endTs=1725321600&fidelity=60',
          'startTs=1724544000&endTs=1727136000&fidelity=60',
          'interval=max&startTs=1724544000&endTs=1725321600'):
    b=get('https://clob.polymarket.com/prices-history?market='+T+'&'+q,raw=True)
    s=b.decode()[:160] if b else 'None'
    print(f'  {q[:60]:60s} -> {s}')
print('\n=== E. data-api trades fields (one closed market) ===')
m=json.load(open('_cache/winner_map.json')); k=sorted(m)[0]
ev={e['slug']:e for e in json.load(open('_cache/closed_events.json'))}[m[k]['event_slug']]
pole=m[k]['race']['pole'].split('_')[-1].lower()
cand=[x for x in ev['markets'] if x.get('groupItemTitle') and pole in x['groupItemTitle'].lower().replace('-',' ')]
cid=cand[0]['conditionId']
tr=get(f'https://data-api.polymarket.com/trades?market={cid}&limit=3&offset=0&takerOnly=true')
print('  market',cid,'n_returned',len(tr) if tr else 0)
print('  fields',sorted(tr[0].keys()) if tr else None)
print('  sample',{x:tr[0][x] for x in ('side','price','size','timestamp','asset','outcome')} if tr else None)
print('\n=== F. Ergast counts ===')
q=get('https://api.jolpi.ca/ergast/f1/2024/qualifying.json?limit=5&offset=0')
print('  2024 qualifying limit/total:',q['MRData'].get('limit'),q['MRData'].get('total'))
races=json.load(open('_cache/races.json'))
per=collections.Counter(r['season'] for r in races.values())
print('  races per season:',dict(sorted(per.items())),'total',sum(per.values()))
print('\n=== G. KNOWN / claims cross-check ===')
import os
p='../../../../../../known/KNOWN.md'
print('  known/KNOWN.md exists',os.path.exists(p))
if os.path.exists(p):
    t=open(p).read(); print('  F-F1-bab present',('F-F1-bab' in t),'V-V2-poly-longshot present',('V-V2-poly-longshot' in t))
