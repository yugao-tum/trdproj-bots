import json,urllib.request,time,os,datetime as dt,statistics as st,math
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f: return json.load(f)
        except Exception as e:
            err=e; time.sleep(1.5*(a+1))
    return {'_err':str(err)}
M=json.load(open('_cache/winner_map.json'))
def modelA(m):
    if m is None: return 0.333
    return 0.408 if m<0.05 else 0.458 if m<0.20 else 0.508 if m<0.50 else 0.720
def fee(p): return 0.05*p*(1-p) if 0<=p<=1 else 0
def vwap(fills,cap):
    q=0.0;c=0.0
    for t in fills:
        take=min(t['size'],cap-q)
        if take<=0: break
        c+=take*t['price']; q+=take
        if q>=cap-1e-9: break
    return (c/q if q else None,q)
rows=[]
for key,x in sorted(M.items()):
    j=json.load(open(f'_cache/trades/{key}.json'))
    cut,start=j['cut'],j['start']; tok=j['yes_token']
    tr=[t for t in j['trades'] if t['asset']==tok]
    pre=sorted([t for t in tr if t['timestamp']<=cut],key=lambda z:z['timestamp'])
    post=[t for t in tr if cut<t['timestamp']<start]
    buys=sorted([t for t in post if t['side']=='BUY'],key=lambda z:z['timestamp'])
    sells=sorted([t for t in post if t['side']=='SELL'],key=lambda z:z['timestamp'])
    p_api=pre[-1]['price'] if pre else None
    ts_api=pre[-1]['timestamp'] if pre else None
    # prices-history last point at cutoff
    u=f"https://clob.polymarket.com/prices-history?market={tok}&startTs={cut-3*86400}&endTs={cut}&fidelity=60"
    h=get(u)
    hist=h.get('history') if isinstance(h,dict) else None
    p_hist=hist[-1]['p'] if hist else None
    first=buys[0] if buys else None
    e20,q20=vwap(buys,20); e100,q100=vwap(buys,100)
    eall,qall=vwap(buys,10**9)
    y=None
    try:
        op=json.loads(j['mkt']['outcomePrices']); y=float(op[0])
    except Exception: pass
    m=modelA(x['race'].get('margin'))
    rows.append({'key':key,'race':x['race']['name'],'season':x['race']['season'],'round':x['race']['round'],
      'pole':j['pole'],'margin':x['race'].get('margin'),'modelA':m,'y':y,
      'p_api':p_api,'p_hist':p_hist,'n_pre':len(pre),'n_post_buy':len(buys),'n_post_sell':len(sells),
      'first_buy_price':first['price'] if first else None,'first_buy_size':first['size'] if first else None,
      'first_buy_dt':first['timestamp']-cut if first else None,
      'exec20':e20,'q20':q20,'exec100':e100,'q100':q100,'execall':eall,'qall':qall,
      'buy_shares_pre':sum(t['size'] for t in buys),'sell_shares_pre':sum(t['size'] for t in sells)})
    print(key,j['race'] if False else x['race']['name'],'hist',p_hist,'api',p_api,'buys',len(buys),'e20',e20,'e100',e100,'q100',round(q100,1),flush=True)
json.dump(rows,open('_cache/analysis_rows.json','w'),indent=1)
# summary
miss=[r for r in rows if r['first_buy_price'] is None]
print('rows',len(rows),'no_buy',len(miss),[r['key'] for r in miss])
up=[r['exec100']-r['p_hist'] for r in rows if r['exec100'] is not None and r['p_hist'] is not None]
print('exec100-p_hist: n',len(up),'mean',round(st.mean(up),4),'median',round(st.median(up),4),'min',round(min(up),4),'max',round(max(up),4))
