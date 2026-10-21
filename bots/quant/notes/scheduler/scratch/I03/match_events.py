import json,re,collections,datetime as dt
E=json.load(open('_cache/closed_events.json'))
R=json.load(open('_cache/races.json'))
win=[]
for e in E:
    t=e.get('title','')
    if re.search(r'Winner',t,re.I) and not re.search(r'Pole|Podium|Sprint|Constructor|Safety|Red Flag|Head',t,re.I):
        if 'indycar' in e['slug'].lower() or 'indy' in t.lower(): continue
        if not e['slug'].startswith('f1-') and not e['slug'].endswith('-winner') and 'grand-prix' not in e['slug']: continue
        win.append(e)
races=[v for v in R.values() if v.get('pole') and v.get('winner') and v['season']>=2024]
rows=[]
for e in win:
    m=re.search(r'(\d{4}-\d{2}-\d{2})',e['slug'])
    d=dt.date.fromisoformat(m.group(1)) if m else dt.date.fromisoformat(e['endDate'][:10])
    best=None
    for r in races:
        rd=dt.date.fromisoformat(r['date'])
        diff=abs((rd-d).days)
        if diff<=7 and (best is None or diff<best[0]): best=(diff,r)
    if best: rows.append({'event':e,'race':best[1],'diff':best[0]})
print('matched',len(rows),'of',len(win))
print('diff dist',collections.Counter(x['diff'] for x in rows))
# dedupe per race keep most markets
by={}
for x in rows:
    k=f"{x['race']['season']}-{x['race']['round']}"
    if k not in by or len(x['event']['markets'])>len(by[k]['event']['markets']): by[k]=x
print('deduped',len(by))
print(collections.Counter(x['race']['season'] for x in by.values()))
for k,x in sorted(by.items()):
    print(k,x['race']['name'],x['race']['date'],x['diff'],x['event']['slug'],len(x['event']['markets']))
json.dump({k:{'event_slug':x['event']['slug'],'event_id':x['event']['id'],'race':x['race'],'diff':x['diff']} for k,x in by.items()},open('_cache/winner_map.json','w'),indent=0)
