import json, os, time, urllib.request
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
UA={'User-Agent':'Mozilla/5.0 (research; quant-bot)'}
def get(url,tries=4,timeout=60):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last=e; print('retry',i,url,e); time.sleep(2+2*i)
    raise RuntimeError('failed '+url+' :: '+str(last))
def jget(url): return json.loads(get(url))
def save(name,obj):
    p=os.path.join(CACHE,name)
    if isinstance(obj,(dict,list)): json.dump(obj,open(p,'w'))
    else: open(p,'wb').write(obj)
    return p
# 1 series events
ev=jget('https://gamma-api.polymarket.com/events?series_id=12954&limit=100')
save('series_events.json',ev)
print('SERIES_EVENTS',len(ev))
for e in ev:
    print(' ',e['slug'],'closed',e.get('closed'),'end',e.get('endDate'),'mkts',len(e.get('markets',[])),'vol',e.get('volume'))
    save('event_'+e['slug']+'.json',e)
# 2 per market price history + trades
for e in ev:
    for m in e['markets']:
        cid=m['conditionId']; toks=json.loads(m['clobTokenIds']) if isinstance(m['clobTokenIds'],str) else m['clobTokenIds']
        yes=toks[0]
        # price history (YES token)
        ph=jget('https://clob.polymarket.com/prices-history?market='+yes+'&interval=max&fidelity=1')
        save('ph_'+cid+'.json',ph)
        # trades
        alltr=[]; off=0
        while True:
            tr=jget('https://data-api.polymarket.com/trades?market='+cid+'&limit=1000&offset='+str(off))
            if not isinstance(tr,list) or not tr: break
            alltr+=tr
            if len(tr)<1000: break
            off+=1000; time.sleep(0.2)
            if off>20000: break
        save('trades_'+cid+'.json',alltr)
        print('  MKT',m.get('groupItemTitle'),'ph',len(ph.get('history',[])),'tr',len(alltr),'closed',m.get('closed'),'prices',m.get('outcomePrices'))
        time.sleep(0.15)
