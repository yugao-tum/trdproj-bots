import json,requests,time
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0'
alle={}
for off in range(0,1300,100):
    r=S.get("https://gamma-api.polymarket.com/events",params={'tag_slug':'cricket','closed':'true','limit':100,'offset':off},timeout=30)
    if r.status_code!=200: print("ERR",off,r.status_code); break
    d=r.json()
    if not d: break
    for e in d: alle[e['slug']]=e
    print(off,len(d),len(alle),flush=True)
    time.sleep(0.15)
json.dump(list(alle.values()),open('/tmp/opencode/cricket_events.json','w'))
print("total",len(alle))
from collections import Counter
c=Counter(e['slug'].split('-')[0] for e in alle.values())
print(c.most_common(20))
# how many markets per event
print(Counter(len(e.get('markets',[])) for e in alle.values()).most_common())
