import json, os, csv, datetime as dt, statistics
BASE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(BASE,'_cache')
FEE=0.04; HALF=0.005; BUDGET=250.0
events=json.load(open(os.path.join(CACHE,'series_events.json')))
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def bracket_win(g,val):
    s=g.replace('<','').replace('+','').replace('$','').replace(',','')
    if g.startswith('<'): return val < float(s)
    if g.endswith('+'): return val >= float(s)
    a,b=s.split('-'); return float(a)-1e-9 <= val <= float(b)+1e-9
# verified AAA snapshots
snaps=[]
for r in csv.DictReader(open(os.path.join(BASE,'aaa_snapshots_all.csv'))):
    ts=dt.datetime.strptime(r['snapshot_utc'],'%Y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc)
    snaps.append(dict(ts=ts,tag=r['snapshot_utc'],asof=r['price_as_of'],cur=r['current_regular'],yest=r['yesterday_regular']))
def prev_day(d): return (d-dt.timedelta(days=1)).strftime('%-m/%-d/%y')
def day_tag(d): return d.strftime('%-m/%-d/%y')
print('EVENT WINNER + EARLIEST VERIFIED CURRENT PAGE')
rows=[]
for e in sorted(events,key=lambda x:x['endDate']):
    if not e.get('closed'): continue
    day=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00')).date()
    val=None; w=None
    for m in e['markets']:
        op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
        if float(op[0])>0.5: w=m
    # AAA value from last snapshot for that day
    prior=[s for s in snaps if s['asof']==day_tag(day-dt.timedelta(days=1))]
    prior_val=prior[-1]['cur'] if prior else None
    cand=[s for s in snaps if s['ts'].date()==day and s['asof']==day_tag(day) and prior_val is not None and s['yest']==prior_val]
    if not cand: continue
    cand.sort(key=lambda s:s['ts']); s=cand[0]; val=float(s['cur'])
    print(e['slug'],'day',day,'winner_by_outcome',w['groupItemTitle'] if w else None,
          'aaa',val,'winner_by_aaa',[m['groupItemTitle'] for m in e['markets'] if bracket_win(m['groupItemTitle'],val)],
          'decision',s['ts'].isoformat(),'tag',s['tag'])
    rows.append((e,day,val,w,s))
print('\nHISTORICAL PRICE BACKTEST: buy winning bracket at first CLOB price <= threshold at/after earliest verified current-page snapshot; hold to settlement')
for th in (0.90,0.95,0.99):
    fills=[]
    for e,day,val,w,s in rows:
        cid=w['conditionId']; hist=json.load(open(os.path.join(CACHE,'ph_'+cid+'.json')))['history']
        cand=[x for x in hist if x['t']>=s['ts'].timestamp() and x['p']<=th]
        cand.sort(key=lambda x:x['t'])
        if not cand: continue
        x=cand[0]; p=x['p']; cost=p+HALF; fee=FEE*p*(1-p); net=1-cost-fee
        shares=BUDGET/cost
        fills.append(dict(slug=e['slug'],day=str(day),entry=iso(x['t']),p=p,fee=fee,cost=cost,net=net,shares=shares,usd=net*shares,budget=BUDGET))
    print('\nTHRESHOLD',th,'fills',len(fills),'of',len(rows))
    for f in fills:
        print(' ',f['day'],f['slug'],'entry',f['entry'],'p',round(f['p'],4),'fee',round(f['fee'],6),
              'net/sh',round(f['net'],6),'shares',round(f['shares'],2),'net$',round(f['usd'],2))
    if fills:
        print(' median_net_per_share',round(statistics.median([f['net'] for f in fills]),6),
              'total_net_usd',round(sum(f['usd'] for f in fills),2),
              'total_budget',round(sum(f['budget'] for f in fills),2),
              'roi_pct',round(100*sum(f['usd'] for f in fills)/sum(f['budget'] for f in fills),3))
    else:
        print('  no fills')
print('\nDIAGNOSTIC (ex post): CLOB price at/after 07:00 UTC on event day, winning bracket, first <= thresholds')
for th in (0.95,0.99):
    fills=[]
    for e,day,val,w,s in rows:
        hist=json.load(open(os.path.join(CACHE,'ph_'+w['conditionId']+'.json')))['history']
        cut=dt.datetime(day.year,day.month,day.day,7,0,tzinfo=dt.timezone.utc).timestamp()
        cand=[x for x in hist if x['t']>=cut and x['p']<=th]; cand.sort(key=lambda x:x['t'])
        if cand:
            x=cand[0]; p=x['p']; cost=p+HALF; fee=FEE*p*(1-p); net=1-cost-fee
            fills.append((e['slug'],iso(x['t']),p,net))
    print(' th',th,'n',len(fills)); [print('  ',f) for f in fills]
