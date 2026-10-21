import json, os, datetime as dt
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
events=json.load(open(os.path.join(CACHE,'events_index.json')))
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
for s,e in events.items():
    if not e.get('closed'): continue
    end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
    print('\n===',s,'end',e['endDate'])
    for m in e['markets']:
        tr=json.load(open(os.path.join(CACHE,'trades_'+m['conditionId']+'.json')))
        yes=[x for x in tr if x.get('outcome')=='Yes']
        yes.sort(key=lambda x:x['timestamp'])
        win=m['outcomePrices'].strip('[]').replace('"','').split(',')[0]=='1'
        if not yes:
            print('  ',m.get('groupItemTitle'),'WIN' if win else '   ','no YES trades'); continue
        before=[x for x in yes if x['timestamp']<=end]
        last=before[-1] if before else None
        print('  ',m.get('groupItemTitle'),'WIN' if win else '   ','nYes',len(yes),
              '| first',iso(yes[0]['timestamp']),yes[0]['side'],yes[0]['price'],
              '| last<=end',(iso(last['timestamp'])+' '+last['side']+' '+str(last['price'])) if last else None)
        if win:
            for x in yes:
                print('       ',iso(x['timestamp']),x['side'],round(x['price'],6),round(x['size'],4))
