import json,urllib.request,time,re,datetime as dt,os,concurrent.futures as cf
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f: return json.load(f)
        except Exception as e:
            err=e; time.sleep(1.5*(a+1))
    raise RuntimeError(str(err)+' '+u)
E={e['slug']:e for e in json.load(open('_cache/closed_events.json'))}
M=json.load(open('_cache/winner_map.json'))
jobs=[]
for key,x in sorted(M.items()):
    ev=E[x['event_slug']]; pole=x['race']['pole']; sur=pole.split('_')[-1].lower()
    cand=[m for m in ev['markets'] if m.get('groupItemTitle') and sur in m['groupItemTitle'].lower().replace('-',' ')]
    if len(cand)!=1:
        print('WARN candidate',key,pole,[m.get('groupItemTitle') for m in cand]); 
        if not cand: continue
    m=cand[0]
    toks=json.loads(m['clobTokenIds']); outs=json.loads(m['outcomes'])
    yi=outs.index('Yes'); tok=toks[yi]
    rd=x['race']['date']; tm=x['race'].get('time') or '00:00:00Z'
    cut=int(dt.datetime.fromisoformat(rd+'T00:00:00+00:00').timestamp())
    start=int(dt.datetime.fromisoformat(rd+'T'+tm.replace('Z','+00:00')).timestamp())
    if start<=cut: start=cut+15*3600
    jobs.append({'key':key,'slug':x['event_slug'],'pole':pole,'driver_title':m['groupItemTitle'],
                 'conditionId':m['conditionId'],'yes_token':tok,'cut':cut,'start':start,
                 'mkt':{k:m.get(k) for k in ['question','outcomePrices','volume','liquidity']}})
def work(j):
    cid=j['conditionId']; rows=[]; off=0
    while off<20000:
        r=get(f'https://data-api.polymarket.com/trades?limit=1000&offset={off}&market={cid}&takerOnly=true')
        if not r: break
        rows.extend(r)
        oldest=min(t['timestamp'] for t in r[-50:]) if len(r)>=1000 else r[-1]['timestamp']
        if r[-1]['timestamp'] <= j['cut']-86400: break
        if len(r)<1000: break
        off+=1000
    j['n_all']=len(rows)
    j['oldest']=min((t['timestamp'] for t in rows),default=None)
    j['trades']=[{k:t[k] for k in ['timestamp','side','price','size','asset','outcome','outcomeIndex']} for t in rows if t['timestamp']<=j['start']+3600]
    return j
out=[]
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for j in ex.map(work,jobs):
        json.dump(j,open(f"_cache/trades/{j['key']}.json",'w'))
        out.append(j)
        print(j['key'],j['driver_title'],'all',j['n_all'],'kept',len(j['trades']),'oldest',j['oldest'],flush=True)
json.dump([{k:v for k,v in j.items() if k!='trades'} for j in out],open('_cache/trade_meta.json','w'),indent=0)
print('events',len(out))
