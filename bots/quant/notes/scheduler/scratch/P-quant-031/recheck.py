import json, os, csv, datetime as dt, urllib.request
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
UA={'User-Agent':'Mozilla/5.0 (research; quant-bot)'}
def jget(u):
    r=urllib.request.Request(u,headers=UA)
    return json.load(urllib.request.urlopen(r,timeout=60))

cdx=json.load(open(os.path.join(CACHE,'cdx_aug_oct.json')))[1:]
cand=[r for r in cdx if '0400'<=r[0][8:12]<='1059']
print('CDX_ROWS',len(cdx),'WINDOW_0400_1059',len(cand))

rows=list(csv.DictReader(open(os.path.join(BASE,'aaa_snapshots_all.csv'))))
print('PARSED_SNAPSHOTS',len(rows),'DATES',len(set(r['snapshot_utc'][:8] for r in rows)))
first={}
for r in rows:
    d=r['snapshot_utc'][:8]
    if r['price_as_of']==dt.datetime.strptime(d,'%Y%m%d').strftime('%-m/%-d/%y'):
        first.setdefault(d,r)
print('FIRST_CURRENT_BY_DATE')
for d in sorted(first):
    print(' ',d,first[d]['snapshot_utc'][8:12],first[d]['current_regular'])
print('EARLIEST_FIRST_HHMM',min(first[d]['snapshot_utc'][8:12] for d in first))
print('BEFORE_0730_SHOWING_TODAY',[d for d in first if first[d]['snapshot_utc'][8:12]<'0730'])

ev=json.load(open(os.path.join(CACHE,'series_events.json')))
sizes=[]; winning={}
for e in ev:
    if not e.get('closed'): continue
    for m in e['markets']:
        op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
        if float(op[0])>0.5:
            tr=json.load(open(os.path.join(CACHE,'trades_'+m['conditionId']+'.json')))
            for x in tr:
                if x.get('outcome')=='Yes': sizes.append(x['size'])
            winning[e['slug']]=m['groupItemTitle']
print('WINNING_BRACKET_YES_SIZE_MIN_MAX',round(min(sizes),4),round(max(sizes),4),'N',len(sizes))

for slug in ['average-us-gas-prices-on-february-21','average-us-gas-prices-on-february-28']:
    e=jget('https://gamma-api.polymarket.com/events?slug='+slug)[0]
    print('\n2025',slug,'markets',len(e['markets']))
    for m in e['markets']:
        op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
        tr=jget('https://data-api.polymarket.com/trades?market='+m['conditionId']+'&limit=1000')
        y=[x for x in tr if x.get('outcome')=='Yes']
        print(' ',m['groupItemTitle'],'outcome',op,'YES',len(y),'all',len(tr),'lastYES', (dt.datetime.fromtimestamp(max(x['timestamp'] for x in y),dt.timezone.utc).isoformat() if y else None),
              'lastYES_px',(sorted(y,key=lambda x:x['timestamp'])[-1]['price'] if y else None))
