import json,urllib.request,time,re,collections
H={'User-Agent':'research/1.0'}
def get(u):
    last=None
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f: return f.status,json.load(f)
        except urllib.error.HTTPError as e:
            return e.code,None
        except Exception as e:
            last=e; time.sleep(1.2*(a+1))
    return None,{'_err':str(last)}
E=json.load(open('_cache/closed_events.json'))
print('=== Gamma closed F1 events ===')
print('events fetched',len(E),'unique',len({e['id'] for e in E}))
sel=[e for e in E if re.search(r'Winner|Pole|Podium',e.get('title',''),re.I)]
print('title Winner/Pole/Podium events',len(sel),'markets',sum(len(e['markets']) for e in sel))
print('by kind',{w:sum(1 for e in E if re.search(w,e.get('title',''),re.I)) for w in ('Winner','Pole','Podium')})
M=json.load(open('_cache/winner_map.json'))
ms=[len(x['event_slug']) for x in M.values()]
print('49 winner events: markets min/median/max',min(len(x['event_slug']) for x in M.values()),'')
lens=sorted(len(next(e for e in E if e['slug']==x['event_slug'])['markets']) for x in M.values())
print('49 winner event market counts min/median/max',min(lens),lens[len(lens)//2],max(lens))
print('\n=== example events: rules / fees / volume ===')
for slug in ('f1-united-states-grand-prix-winner-2026-10-25','f1-united-states-grand-prix-driver-pole-position-2026-10-24','f1-united-states-grand-prix-driver-podium-2026-10-25','f1-singapore-grand-prix-winner-2026-10-11'):
    sc,d=get('https://gamma-api.polymarket.com/events?slug='+slug)
    if not d: print(slug,'HTTP',sc); continue
    e=d[0]
    desc=e.get('description','') or ''
    print(f'\n-- {slug} HTTP {sc} markets={len(e["markets"])} negRisk={e.get("negRisk")} restricted={e.get("restricted")} volume={e.get("volume")} liquidity={e.get("liquidity")}')
    print('   resolutionSource',e.get('resolutionSource'))
    for key in ('FIA','Final Classification','fastest time','regardless','top three','50-50','Other','Nov 1'):
        if key.lower() in desc.lower():
            i=desc.lower().index(key.lower()); print('   ...',desc[max(0,i-110):i+220].replace('\n',' '))
    fs=set(json.dumps(m.get('feeSchedule'),sort_keys=True) for m in e['markets'])
    print('   feeSchedules',fs)
    if 'singapore' in slug:
        ys=[(m.get('groupItemTitle'),m.get('outcomePrices')) for m in e['markets'] if m.get('outcomePrices')=='["1", "0"]' or m.get('outcomePrices')=='["1","0"]']
        print('   resolved YES:',ys)
print('\n=== CLOB prices-history limits ===')
tok=json.load(open('_cache/trades/2026-17.json'))['yes_token']
for span in (14,15,20):
    end=int(time.time()); start=end-span*86400
    sc,d=get(f'https://clob.polymarket.com/prices-history?market={tok}&startTs={start}&endTs={end}&fidelity=60')
    print(f'  span={span}d HTTP {sc} points={len(d.get("history",[])) if d else None} err={d.get("error") if d else None}')
sc,d=get(f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60')
print('  interval=max HTTP',sc,'points',len(d.get('history',[])) if d else None)
sc,d=get(f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&startTs={int(time.time())-14*86400}&endTs={int(time.time())}&fidelity=60')
print('  interval=max + start/end HTTP',sc,'points',len(d.get('history',[])) if d else None)
print('\n=== data-api trades fields ===')
cid=next(m['conditionId'] for m in next(e for e in E if e['slug']==M['2026-17']['event_slug'])['markets'] if m.get('groupItemTitle')=='Oscar Piastri')
cid=json.load(open('_cache/trades/2026-17.json'))['conditionId']
sc,d=get(f'https://data-api.polymarket.com/trades?market={cid}&limit=3&offset=0&takerOnly=true')
print('  HTTP',sc,'n',len(d) if d else None,'keys',sorted(d[0].keys()) if d else None)
