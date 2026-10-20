import json, urllib.request, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
ev=json.load(open('_cache/events_closed0.json'))
markets=[]
for e in ev:
    for m in e.get('markets') or []:
        markets.append({'event':e['slug'],'slug':m['slug'],'conditionId':m['conditionId'],
                        'outcomes':m.get('outcomes'),'outcomePrices':m.get('outcomePrices'),
                        'question':m.get('question'),'endDate':e.get('endDate')})
print('markets',len(markets))
def get(m):
    url=f"https://data-api.polymarket.com/trades?market={m['conditionId']}&limit=1000"
    for k in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            return json.loads(urllib.request.urlopen(req,timeout=60).read())
        except Exception as e:
            if k==2: return {'error':str(e)}
            time.sleep(1)
out={}
with ThreadPoolExecutor(max_workers=10) as ex:
    futs={ex.submit(get,m):m for m in markets}
    for f in as_completed(futs):
        m=futs[f]
        r=f.result()
        if isinstance(r,dict) and 'error' in r:
            print('ERR',m['slug'],r['error'])
            out[m['slug']]=[]
        else:
            out[m['slug']]=r
json.dump({'markets':markets,'trades':out},open('_cache/trades_all.json','w'))
print('written',os.path.getsize('_cache/trades_all.json'))
cnt=sum(len(v) for v in out.values())
print('total trades',cnt)
print('markets with trades',sum(1 for v in out.values() if v))
