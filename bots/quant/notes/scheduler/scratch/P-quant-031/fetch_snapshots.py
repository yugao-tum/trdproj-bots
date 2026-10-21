import json, os, re, subprocess, concurrent.futures, time
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
d=json.load(open(os.path.join(CACHE,'cdx_aug_oct.json')))[1:]
ts=set(r[0] for r in d if '0400'<=r[0][8:12]<='1059')
ts |= set(r[0] for r in d if r[0][:8] in ('20261016','20261017','20261018','20261019','20261020','20261021'))
ts=sorted(ts)
print('to fetch',len(ts))
def one(t):
    p=os.path.join(CACHE,'aaa_'+t+'.html')
    if os.path.exists(p) and os.path.getsize(p)>5000:
        return t,'cached'
    url='https://web.archive.org/web/'+t+'id_/https://gasprices.aaa.com/'
    for i in range(8):
        r=subprocess.run(['curl','-sS','-L','--compressed','--max-time','60','-o',p,url],capture_output=True)
        if r.returncode==0 and os.path.exists(p) and os.path.getsize(p)>5000:
            return t,'ok'
        time.sleep(2+i*2)
    return t,'FAIL '+r.stderr.decode()[:120]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for t,st in ex.map(one,ts):
        print(t,st)
