import json, requests
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0 (research; quant bot)'
out={}
for off in range(0,3000,100):
    r=S.get('https://gamma-api.polymarket.com/events',params={'tag_slug':'nfl','closed':'true','limit':100,'offset':off},timeout=40)
    r.raise_for_status(); d=r.json()
    if not d: break
    for e in d: out[e['slug']]=e
json.dump(list(out.values()),open('bots/quant/notes/scheduler/scratch/B21/_cache/nfl_events_all.json','w'))
print('events',len(out))
