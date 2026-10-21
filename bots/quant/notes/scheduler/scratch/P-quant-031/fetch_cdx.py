import json, os, urllib.request, time
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
os.makedirs(CACHE,exist_ok=True)
UA={'User-Agent':'Mozilla/5.0 (research; quant-bot)'}
URL=('https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com'
     '&from=20260801&to=20261021&output=json&filter=statuscode:200&fl=timestamp,digest')
def get(u,tries=6):
    last=None
    for i in range(tries):
        try:
            r=urllib.request.Request(u,headers=UA)
            with urllib.request.urlopen(r,timeout=60) as f:
                return f.read()
        except Exception as e:
            last=e; print('retry',i,u,e); time.sleep(2+2*i)
    raise RuntimeError(str(last))
raw=get(URL)
open(os.path.join(CACHE,'cdx_aug_oct.json'),'wb').write(raw)
d=json.loads(raw)
print('CDX_ROWS',len(d)-1,'FIRST',d[1][0],'LAST',d[-1][0])
