import json, urllib.request, time, concurrent.futures as cf, datetime as dt, csv, sys
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=45) as f: return json.load(f)
        except Exception as e:
            err=e; time.sleep(1.2*(a+1))
    return {'_err':str(err)}
E={e['slug']:e for e in json.load(open('_cache/closed_events.json'))}
M=json.load(open('_cache/winner_map.json'))
jobs=[]
for key,x in sorted(M.items()):
    ev=E[x['event_slug']]; rd=x['race']['date']
    cut=int(dt.datetime.fromisoformat(rd+'T00:00:00+00:00').timestamp())
    pole=x['race']['pole'].split('_')[-1].lower()
    for m in ev['markets']:
        gi=m.get('groupItemTitle')
        if not gi: continue
        try:
            toks=json.loads(m['clobTokenIds']); outs=json.loads(m['outcomes'])
            yi=[o.lower() for o in outs].index('yes'); tok=toks[yi]
            op=json.loads(m.get('outcomePrices') or '[]')
            y=float(op[0]) if op else None
        except Exception:
            continue
        jobs.append({'key':key,'event':x['event_slug'],'driver':gi,'token':tok,
                     'conditionId':m.get('conditionId'),'y':y,'cut':cut,
                     'is_pole':1 if pole in gi.lower().replace('-',' ') else 0})
print('markets',len(jobs),flush=True)
def work(j):
    u=f"https://clob.polymarket.com/prices-history?market={j['token']}&startTs={j['cut']-3*86400}&endTs={j['cut']}&fidelity=60"
    h=get(u); hist=h.get('history') if isinstance(h,dict) else None
    j['p']=hist[-1]['p'] if hist else None
    j['npts']=len(hist) if hist else 0
    return j
out=[]
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for i,j in enumerate(ex.map(work,jobs)):
        out.append(j)
        if i%200==0: print(i,flush=True)
json.dump(out,open('_cache/all_prices.json','w'))
print('done',len(out),'with p',sum(1 for j in out if j['p'] is not None))
