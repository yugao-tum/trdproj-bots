import json, os, datetime as dt, statistics
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
events=json.load(open(os.path.join(CACHE,'events_index.json')))
FEE=0.04; HALF=0.005
aaa={'us-gas-price-on-october-16-2026':('4.3271','20261016110050'),
     'us-gas-price-on-october-17-2026':('4.3085','20261017110254'),
     'us-gas-price-on-october-18-2026':('4.2988','20261018110336'),
     'us-gas-price-on-october-19-2026':('4.2953','20261019110151'),
     'us-gas-price-on-october-20-2026':('4.2786','20261020110138')}
def bracket_for(g,val):
    g=g.replace('<','').replace('+','').replace('$','').replace(',','')
    if g.startswith('') and False: pass
    return None
def is_win(group,val):
    g=group.replace('<','').replace('+','').replace('$','').replace(',','')
    if group.startswith('<'): return float(val)<float(g)
    if group.endswith('+'): return float(val)>=float(g)
    a,b=g.split('-'); return float(a)<=float(val)<=float(b)+1e-9
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
print('EVENT STUDY (ex post winner; diagnostic only)')
for s,e in events.items():
    if s not in aaa: continue
    val,snap=aaa[s]; day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date()
    win=[m for m in e['markets'] if is_win(m['groupItemTitle'],val)][0]
    tr=[x for x in json.load(open(os.path.join(CACHE,'trades_'+win['conditionId']+'.json'))) if x.get('outcome')=='Yes']
    tr.sort(key=lambda x:x['timestamp'])
    end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
    pre=[x for x in tr if x['timestamp']<=end]
    cut=dt.datetime(day.year,day.month,day.day,7,0,tzinfo=dt.timezone.utc).timestamp()
    after=[x for x in pre if x['timestamp']>=cut]
    first=after[0] if after else None
    reach=[x for x in pre if x['price']>=0.95]
    mins=round((reach[0]['timestamp']-first['timestamp'])/60,1) if (first and reach) else None
    print(s,'AAA',val,'bracket',win['groupItemTitle'],'first07',iso(first['timestamp']) if first else None,
          'p',round(first['price'],4) if first else None,'first95',iso(reach[0]['timestamp']) if reach else None,
          'mins_to_95',mins,'last_pre',iso(pre[-1]['timestamp']) if pre else None,
          'last_p',round(pre[-1]['price'],4) if pre else None,'closed',e.get('closed'))
print('\nRULE AT SNAPSHOT TIME (11:00-11:03 UTC, page verified): buy matching bracket YES if BUY fill <= threshold; fee .04*p*(1-p); +0.5c half-spread; hold to settlement')
for th in (0.95,0.99):
    fills=[]
    for s,e in events.items():
        if not e.get('closed') or s not in aaa: continue
        val,snap=aaa[s]; day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date()
        win=[m for m in e['markets'] if is_win(m['groupItemTitle'],val)][0]
        tr=[x for x in json.load(open(os.path.join(CACHE,'trades_'+win['conditionId']+'.json'))) if x.get('outcome')=='Yes']
        end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
        # snapshot UTC time from filename yyyymmddHHMMSS
        st=dt.datetime.strptime(snap,'%Y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc).timestamp()
        cand=[x for x in tr if st<=x['timestamp']<=end and x['side']=='BUY' and x['price']<=th]
        cand.sort(key=lambda x:x['timestamp'])
        if cand:
            x=cand[0]; p=x['price']; fee=FEE*p*(1-p); net=1-p-fee-HALF
            fills.append((s,iso(x['timestamp']),round(p,6),round(x['size'],4),round(fee,6),round(net,6),round(net*x['size'],4)))
    print('threshold',th,'fills',len(fills))
    for f in fills: print('  ',f)
    if fills:
        print('   median_net_per_share',round(statistics.median([f[5] for f in fills]),6),'total_net_usd',round(sum(f[6] for f in fills),4))
