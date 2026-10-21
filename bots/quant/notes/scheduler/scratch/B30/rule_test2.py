import json, os, datetime as dt, statistics
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
events=json.load(open(os.path.join(CACHE,'events_index.json')))
FEE=0.04; HALF=0.005; THRESH=0.95
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def tod(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc)
aaa={'us-gas-price-on-october-16-2026':('4.3271','20261016110050'),
     'us-gas-price-on-october-17-2026':('4.3085','20261017110254'),
     'us-gas-price-on-october-18-2026':('4.2988','20261018110336'),
     'us-gas-price-on-october-19-2026':('4.2953','20261019110151'),
     'us-gas-price-on-october-20-2026':('4.2786','20261020110138')}
def bracket_for(group,val):
    g=group.replace('<','').replace('+','').replace('$','').replace(',','')
    if group.startswith('<'): return float(val)<float(g)
    if group.endswith('+'): return float(val)>=float(g)
    a,b=g.split('-'); return float(a)<=float(val)<=float(b)+1e-9
print('EVENT STUDY: winning bracket first YES trade after 07:00 UTC (descriptive, winner known ex post)')
for s,e in events.items():
    if s not in aaa: continue
    val,tsnap=aaa[s]; day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date()
    win=[m for m in e['markets'] if bracket_for(m['groupItemTitle'],val)][0]
    tr=[x for x in json.load(open(os.path.join(CACHE,'trades_'+win['conditionId']+'.json'))) if x.get('outcome')=='Yes']
    tr.sort(key=lambda x:x['timestamp'])
    end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
    pre=[x for x in tr if x['timestamp']<=end]
    cutoff=dt.datetime(day.year,day.month,day.day,7,0,tzinfo=dt.timezone.utc).timestamp()
    after=[x for x in pre if x['timestamp']>=cutoff]
    first=after[0] if after else None
    reach=[x for x in pre if x['price']>=0.95]
    print(s,'AAA',val,'bracket',win['groupItemTitle'],
          '| first>=07:00',(iso(first['timestamp'])+' p='+str(round(first['price'],4))) if first else None,
          '| last<=end',(iso(pre[-1]['timestamp'])+' p='+str(round(pre[-1]['price'],4))) if pre else None,
          '| first>=0.95',iso(reach[0]['timestamp']) if reach else None,'closed',e.get('closed'))
print('\nPRE-REGISTERED RULE: at HH:00 UTC read AAA page; if Price as of=today and Yesterday=prior, buy the matching bracket YES if executable BUY trade price <= 0.95; fee=0.04*p*(1-p); extra 0.5c half-spread buffer; hold to settlement.')
for hh in (7,9,11):
    fills=[]
    for s,e in events.items():
        if not e.get('closed') or s not in aaa: continue
        val,tsnap=aaa[s]; day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date()
        win=[m for m in e['markets'] if bracket_for(m['groupItemTitle'],val)][0]
        tr=[x for x in json.load(open(os.path.join(CACHE,'trades_'+win['conditionId']+'.json'))) if x.get('outcome')=='Yes']
        end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
        cut=dt.datetime(day.year,day.month,day.day,hh,0,tzinfo=dt.timezone.utc).timestamp()
        cand=[x for x in tr if cut<=x['timestamp']<=end and x['side']=='BUY' and x['price']<=THRESH]
        cand.sort(key=lambda x:x['timestamp'])
        if cand:
            x=cand[0]; p=x['price']; fee=FEE*p*(1-p); net=1-p-fee-HALF
            fills.append((s,iso(x['timestamp']),p,x['size'],fee,net,net*x['size']))
    print(f'-- decision {hh:02d}:00 UTC: fills {len(fills)}/4')
    for f in fills: print('   ',f)
    if fills: print('    median net/share',round(statistics.median([f[5] for f in fills]),6),'total net $',round(sum(f[6] for f in fills),4))
