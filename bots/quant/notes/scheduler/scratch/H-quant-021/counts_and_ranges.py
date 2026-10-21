import json,re,statistics as st
E=json.load(open('_cache/closed_events.json'))
sel=[e for e in E if re.search(r'Winner|Pole|Podium',e.get('title',''),re.I)]
print('unique events',len({e['id'] for e in E}))
print('selected Winner/Pole/Podium events',len(sel),'markets',sum(len(e['markets']) for e in sel))
grp={}
for e in sel:
    t=e['title']; k='Pole' if re.search('Pole Position',t,re.I) else 'Podium' if re.search('Podium',t,re.I) else 'Winner'
    grp.setdefault(k,[]).append(len(e['markets']))
for k,v in grp.items(): print(k,'events',len(v),'markets min/median/max',min(v),st.median(v),max(v))
M=json.load(open('_cache/winner_map.json')); by={e['slug']:e for e in E}
v=[len(by[x['event_slug']]['markets']) for x in M.values()]
print('49 matched events markets min/median/max',min(v),st.median(v),max(v))
vol=sorted(float(by[x['event_slug']]['volume']) for x in M.values() if by[x['event_slug']].get('volume'))
print('49 matched event volume: n',len(vol),'min',round(vol[0],2),'median',round(st.median(vol),2),'max',round(vol[-1],2))
