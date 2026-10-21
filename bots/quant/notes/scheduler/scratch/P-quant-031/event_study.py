import json,os,datetime as dt
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
ev=json.load(open(os.path.join(CACHE,'series_events.json')))
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def win(g,val):
    s=g.replace('<','').replace('+','').replace('$','').replace(',','')
    if g.startswith('<'): return val<float(s)
    if g.endswith('+'): return val>=float(s)
    a,b=s.split('-'); return float(a)<=val<=float(b)+1e-9
aaa={'us-gas-price-on-october-16-2026':4.3271,'us-gas-price-on-october-17-2026':4.3085,
     'us-gas-price-on-october-18-2026':4.2988,'us-gas-price-on-october-19-2026':4.2953,
     'us-gas-price-on-october-20-2026':4.2786}
print('EVENT STUDY (ex post winner; diagnostic only)')
for e in sorted(ev,key=lambda x:x['endDate']):
    if e['slug'] not in aaa: continue
    day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date(); val=aaa[e['slug']]
    m=[x for x in e['markets'] if win(x['groupItemTitle'],val)][0]
    tr=json.load(open(os.path.join(CACHE,'trades_'+m['conditionId']+'.json')))
    end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
    pre=[x for x in tr if x['timestamp']<=end and x.get('outcome')=='Yes']; pre.sort(key=lambda x:x['timestamp'])
    cut=dt.datetime(day.year,day.month,day.day,7,0,tzinfo=dt.timezone.utc).timestamp()
    after=[x for x in pre if x['timestamp']>=cut]
    first=after[0] if after else None
    reach=[x for x in pre if x['price']>=0.95 and (first is None or x['timestamp']>=first['timestamp'])]
    mins=round((reach[0]['timestamp']-first['timestamp'])/60,1) if (first and reach) else None
    print(e['slug'],'AAA',val,'bracket',m['groupItemTitle'],
          'first07',iso(first['timestamp']) if first else None,'p',round(first['price'],4) if first else None,
          'first95',iso(reach[0]['timestamp']) if reach else None,
          'mins_to_95',mins,'last_pre',iso(pre[-1]['timestamp']) if pre else None,
          'last_p',round(pre[-1]['price'],4) if pre else None,
          'n_yes',len([x for x in tr if x.get('outcome')=='Yes']),'closed',e.get('closed'))
