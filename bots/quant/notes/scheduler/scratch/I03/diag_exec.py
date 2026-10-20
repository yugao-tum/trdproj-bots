import json,statistics as st,datetime as dt,csv
R=json.load(open('_cache/analysis_rows.json'))
out=[]
for r in R:
    j=json.load(open(f"_cache/trades/{r['key']}.json")); tok=j['yes_token']; cut,start=j['cut'],j['start']
    tr=sorted([t for t in j['trades'] if t['asset']==tok],key=lambda z:z['timestamp'])
    pre=[t for t in tr if t['timestamp']<=cut]; post=[t for t in tr if cut<t['timestamp']<start]
    buys=[t for t in post if t['side']=='BUY']; sells=[t for t in post if t['side']=='SELL']
    # time to accumulate 100 shares of buys
    q=0; t100=None
    for t in buys:
        q+=t['size']
        if q>=100: t100=t['timestamp']; break
    first=buys[0] if buys else None
    last=pre[-1] if pre else None
    out.append({'key':r['key'],'race':r['race'],'cut':cut,'start':start,
      'oldest':j['oldest'],'covers_cut':bool(j['oldest'] and j['oldest']<=cut),
      'p_hist':r['p_hist'],'last_pre_price':last['price'] if last else None,'last_pre_side':last['side'] if last else None,
      'last_pre_dt':(cut-last['timestamp'])/3600 if last else None,
      'first_buy_price':first['price'] if first else None,'first_buy_size':first['size'] if first else None,
      'first_buy_dt_h':(first['timestamp']-cut)/3600 if first else None,
      't100_h':(t100-cut)/3600 if t100 else None,
      'buy_shares_pre':sum(t['size'] for t in buys),'sell_shares_pre':sum(t['size'] for t in sells),
      'n_buy_pre':len(buys),'n_sell_pre':len(sells),
      'race_window_h':(start-cut)/3600,
      'first_buy_le_start':bool(first and first['timestamp']<start),
      'max_buy_price':max((t['price'] for t in buys),default=None),
      'min_buy_price':min((t['price'] for t in buys),default=None)})
json.dump(out,open('_cache/diag.json','w'),indent=1)
with open('exec_diag.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('covers_cut',sum(x['covers_cut'] for x in out),'/',len(out))
print('first_buy<=start',sum(x['first_buy_le_start'] for x in out),'/',len(out))
print('first_buy_dt_h: median',round(st.median([x['first_buy_dt_h'] for x in out]),2),'p90',round(sorted([x['first_buy_dt_h'] for x in out])[44],2),'max',round(max(x['first_buy_dt_h'] for x in out),2))
print('t100_h: median',round(st.median([x['t100_h'] for x in out]),2),'p90',round(sorted([x['t100_h'] for x in out])[44],2),'max',round(max(x['t100_h'] for x in out),2))
print('buy_shares_pre median',round(st.median([x['buy_shares_pre'] for x in out]),1),'min',round(min(x['buy_shares_pre'] for x in out),1))
print('events buy_shares_pre<100',sum(x['buy_shares_pre']<100 for x in out),[x['key'] for x in out if x['buy_shares_pre']<100])
print('last_pre_side', {s:sum(1 for x in out if x['last_pre_side']==s) for s in ('BUY','SELL',None)})
lastbuy=[x for x in out if x['last_pre_side']=='BUY']; lastsell=[x for x in out if x['last_pre_side']=='SELL']
print('last pre is BUY: n',len(lastbuy),'mean first_buy-last_pre',round(st.mean([x['first_buy_price']-x['last_pre_price'] for x in lastbuy]),4))
print('last pre is SELL: n',len(lastsell),'mean first_buy-last_pre',round(st.mean([x['first_buy_price']-x['last_pre_price'] for x in lastsell]),4))
print('spread proxy (first post BUY - last pre trade): mean',round(st.mean([x['first_buy_price']-x['last_pre_price'] for x in out if x['last_pre_price'] is not None]),4),
      'median',round(st.median([x['first_buy_price']-x['last_pre_price'] for x in out if x['last_pre_price'] is not None]),4))
print('first_buy_dt by race window: max t100_h < window?',all(x['t100_h'] is not None and x['t100_h']<x['race_window_h'] for x in out))
