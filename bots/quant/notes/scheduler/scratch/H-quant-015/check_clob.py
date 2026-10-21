#!/usr/bin/env python3
import json, os, time, urllib.request
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D); CACHE='_cache'
d=json.load(open(os.path.join(CACHE,'search.json')))
rows=[]; total=0; nonempty=[]
for e in d['events']:
    counts=[]; toks=[]
    for m in e.get('markets',[]):
        try: toks.append(json.loads(m['clobTokenIds'])[0])
        except Exception: pass
    for tok in toks:
        total+=1
        u=f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60'
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
            j=json.load(urllib.request.urlopen(req,timeout=20))
            h=j.get('history',[]) if isinstance(j,dict) else []
            counts.append(len(h))
        except Exception as ex:
            counts.append('ERR')
        time.sleep(0.03)
    rows.append((e['slug'],bool(e.get('closed')),counts))
    if any(isinstance(x,int) and x>0 for x in counts): nonempty.append((e['slug'],counts))
for r in rows:
    if any(isinstance(x,int) and x>0 for x in r[2]): print(r)
print('YES tokens queried:',total)
print('events with any nonempty:',len(nonempty))
print('total nonempty token histories:',sum(sum(1 for x in c if isinstance(x,int) and x>0) for _,c in nonempty))
