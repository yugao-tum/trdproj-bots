import json, os, time, urllib.request, urllib.parse
BASE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(BASE,'_cache')
UA={'User-Agent':'Mozilla/5.0 (research; quant-bot)'}
def get(url, tries=4, timeout=40):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print('retry',i,url,e)
            time.sleep(2+2*i)
    raise RuntimeError('failed '+url)
def jget(url):
    return json.loads(get(url))
slugs=['us-gas-price-on-october-16-2026','us-gas-price-on-october-17-2026',
       'us-gas-price-on-october-18-2026','us-gas-price-on-october-19-2026',
       'us-gas-price-on-october-20-2026','average-us-gas-prices-on-february-21',
       'average-us-gas-prices-on-february-28']
events={}
for s in slugs:
    p=os.path.join(CACHE,'event_'+s+'.json')
    if os.path.exists(p):
        d=json.load(open(p))
    else:
        d=jget('https://gamma-api.polymarket.com/events?slug='+s)
        json.dump(d,open(p,'w'))
        time.sleep(0.4)
    e=d[0] if isinstance(d,list) and d else d
    events[s]=e
    print('EVENT',s,e['id'],e.get('closed'),e.get('endDate'),'mkts',len(e.get('markets',[])))
# trades per market
for s,e in events.items():
    for m in e['markets']:
        cid=m['conditionId']
        p=os.path.join(CACHE,'trades_'+cid+'.json')
        if os.path.exists(p):
            tr=json.load(open(p))
        else:
            alltr=[]; off=0
            while True:
                url=('https://data-api.polymarket.com/trades?market='+cid+
                     '&limit=1000&offset='+str(off))
                tr=jget(url)
                if not isinstance(tr,list) or not tr: break
                alltr+=tr
                if len(tr)<1000: break
                off+=1000
                time.sleep(0.25)
                if off>20000: break
            json.dump(alltr,open(p,'w'))
            tr=alltr
            time.sleep(0.25)
        print('TRADES',s,m.get('groupItemTitle'),cid[:10],len(tr))
json.dump(events,open(os.path.join(CACHE,'events_index.json'),'w'))
