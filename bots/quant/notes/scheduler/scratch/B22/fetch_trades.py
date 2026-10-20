import json, os, time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
UA={"User-Agent":"Mozilla/5.0 (research)"}
os.makedirs("_cache/trades",exist_ok=True)
rows=json.load(open('_cache/classified.json'))
cids=sorted(set(r['conditionId'] for r in rows))
def fetch(cid):
    fn=f"_cache/trades/{cid}.json"
    if os.path.exists(fn): return cid,'cached',os.path.getsize(fn)
    for k in range(3):
        try:
            r=requests.get(f"https://data-api.polymarket.com/trades?market={cid}&limit=1000",headers=UA,timeout=30)
            if r.status_code==200:
                open(fn,'w').write(r.text); return cid,'ok',len(r.content)
            time.sleep(1+k)
        except Exception as e:
            time.sleep(1+k)
    return cid,'fail',0
res=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    futs=[ex.submit(fetch,c) for c in cids]
    for i,f in enumerate(as_completed(futs)):
        res.append(f.result())
        if (i+1)%200==0: print(i+1,'done',flush=True)
from collections import Counter
print(Counter(x[1] for x in res), 'files',len(cids))
for x in res:
    if x[1]=='fail': print('FAIL',x)
