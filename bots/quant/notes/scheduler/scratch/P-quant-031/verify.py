import json, os, urllib.request, datetime as dt
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
UA={'User-Agent':'Mozilla/5.0 (research; quant-bot)'}
def jget(u):
    r=urllib.request.Request(u,headers=UA); return json.load(urllib.request.urlopen(r,timeout=60))
ev=json.load(open(os.path.join(CACHE,'series_events.json')))
print('SERIES 12954 events',len(ev),'closed',sum(1 for e in ev if e.get('closed')),'open',sum(1 for e in ev if not e.get('closed')))
for e in sorted(ev,key=lambda x:x['endDate']):
    fees=set()
    for m in e['markets']:
        fs=m.get('feeSchedule')
        fees.add(json.dumps(fs,sort_keys=True) if fs else 'null')
    print('\nEVENT',e['slug'],'closed',e.get('closed'),'end',e.get('endDate'),'mkts',len(e['markets']),
          'negRisk',e.get('negRisk'),'restricted',e.get('restricted'),'volume',e.get('volume'),
          'resolutionSource',e.get('resolutionSource'),'closedTime',e.get('closedTime'))
    print(' feeSchedules',fees)
    print(' desc_chars',len(e.get('description') or ''))
    for m in e['markets']:
        tr=json.load(open(os.path.join(CACHE,'trades_'+m['conditionId']+'.json')))
        ytr=[x for x in tr if x.get('outcome')=='Yes']
        op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
        print('  ',m['groupItemTitle'],'outcome',op,'YES_trades',len(ytr),'all_trades',len(tr),'vol',m.get('volume'),
              'closed',m.get('closed'),'uma',m.get('umaResolutionStatus'),'closedTime',m.get('closedTime'))
# rule quote for 10-16
e16=[e for e in ev if e['slug']=='us-gas-price-on-october-16-2026'][0]
print('\nRULE_DESC_10_16_BEGIN')
print(e16.get('description'))
print('RULE_DESC_10_16_END')
# search
for q in ['gas%20prices%20on','aaa%20gas']:
    d=jget('https://gamma-api.polymarket.com/public-search?q='+q)
    print('\nSEARCH',q,'events',len(d.get('events',[])))
    for e in d.get('events',[]): print(' ',e['slug'],e.get('closed'),e.get('endDate'))
# 2025 events
for s in ['average-us-gas-prices-on-february-21','average-us-gas-prices-on-february-28']:
    e=jget('https://gamma-api.polymarket.com/events?slug='+s)[0]
    print('\n2025',s,'closed',e.get('closed'),'mkts',len(e['markets']),'end',e.get('endDate'))
    for m in e['markets']:
        toks=json.loads(m['clobTokenIds']); ph=jget('https://clob.polymarket.com/prices-history?market='+toks[0]+'&interval=max&fidelity=1')
        print('  ',m['groupItemTitle'],'fee',m.get('feeSchedule'),'outcome',m.get('outcomePrices'),'ph_points',len(ph.get('history',[])))
