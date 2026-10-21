import json, os, csv, datetime as dt, statistics
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
FEE=0.04; HALF=0.005; BUDGET=250.0
events=json.load(open(os.path.join(CACHE,'series_events.json')))
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def day_tag(d): return d.strftime('%-m/%-d/%y')
def bracket_win(g,val):
    s=g.replace('<','').replace('+','').replace('$','').replace(',','')
    if g.startswith('<'): return val < float(s)
    if g.endswith('+'): return val >= float(s)
    a,b=s.split('-'); return float(a)-1e-9 <= val <= float(b)+1e-9
snaps=[]
for r in csv.DictReader(open(os.path.join(BASE,'aaa_snapshots_all.csv'))):
    ts=dt.datetime.strptime(r['snapshot_utc'],'%Y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc)
    snaps.append(dict(ts=ts,tag=r['snapshot_utc'],asof=r['price_as_of'],cur=r['current_regular'],yest=r['yesterday_regular']))
print('VERIFIED DECISION TIME = earliest Wayback snapshot on event day whose Price as of == event day and Yesterday Avg == prior day Current Avg')
rows=[]
for e in sorted(events,key=lambda x:x['endDate']):
    if not e.get('closed'): continue
    day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date()
    prior=[s for s in snaps if s['asof']==day_tag(day-dt.timedelta(days=1))]
    pv=prior[-1]['cur'] if prior else None
    cand=[s for s in snaps if s['ts'].date()==day and s['asof']==day_tag(day) and pv and s['yest']==pv]
    if not cand:
        print('NO_VERIFIED_SNAPSHOT',e['slug'],day); continue
    cand.sort(key=lambda s:s['ts']); s=cand[0]; val=float(s['cur'])
    aaawin=[m['groupItemTitle'] for m in e['markets'] if bracket_win(m['groupItemTitle'],val)]
    if len(aaawin)!=1: print('BRACKET_MISMATCH',e['slug'],val,aaawin); continue
    win=[m for m in e['markets'] if m['groupItemTitle']==aaawin[0]][0]
    outwin=None
    for m in e['markets']:
        op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
        if float(op[0])>0.5: outwin=m['groupItemTitle']
    print(e['slug'],'AAA',val,'winner_from_page',win['groupItemTitle'],'winner_from_outcome',outwin,'decision',iso(s['ts'].timestamp()),'vol',e.get('volume'))
    rows.append((e,day,val,win,s))
print('\nTRADABLE-PRINT BACKTEST: buy winner YES at first actual data-api BUY print at/after decision; fee .04*p*(1-p); +0.5c half-spread; hold to settlement; 250 USDC/event')
for th,label in [(0.95,'limit<=0.95'),(0.99,'limit<=0.99'),(1.0001,'market (first print, any price)')]:
    fills=[]; skipped=[]
    for e,day,val,w,s in rows:
        tr=json.load(open(os.path.join(CACHE,'trades_'+w['conditionId']+'.json')))
        end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).timestamp()
        cand=[x for x in tr if x.get('outcome')=='Yes' and x.get('side')=='BUY' and s['ts'].timestamp()<=x['timestamp']<=end and x['price']<=th]
        cand.sort(key=lambda x:x['timestamp'])
        if not cand:
            skipped.append(e['slug']); continue
        x=cand[0]; p=x['price']; cost=p+HALF; fee=FEE*p*(1-p); net=1-cost-fee
        shares=min(BUDGET/cost, x['size']); usd=net*shares
        fills.append(dict(slug=e['slug'],day=str(day),entry=iso(x['timestamp']),p=p,size=x['size'],fee=fee,cost=cost,net=net,shares=shares,usd=usd))
    print('\n',label,'fills',len(fills),'of',len(rows),'skipped',len(skipped))
    for f in fills:
        print(' ',f['day'],f['slug'],'entry',f['entry'],'p',round(f['p'],6),'print_size',round(f['size'],2),
              'fee/sh',round(f['fee'],6),'net/sh',round(f['net'],6),'shares',round(f['shares'],2),'net$',round(f['usd'],4))
    if fills:
        print('  median_net/sh',round(statistics.median([f['net'] for f in fills]),6),
              'mean_net/sh',round(statistics.mean([f['net'] for f in fills]),6),
              'total_net$',round(sum(f['usd'] for f in fills),4),
              'budget$',round(sum(f['cost']*f['shares'] for f in fills),2),
              'ROI%',round(100*sum(f['usd'] for f in fills)/sum(f['cost']*f['shares'] for f in fills),4))
    print('  skipped_slugs',skipped)
