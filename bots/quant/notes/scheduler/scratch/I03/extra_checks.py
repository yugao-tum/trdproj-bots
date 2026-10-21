import json,statistics as st
R=json.load(open('_cache/analysis_rows.json')); D={x['key']:x for x in json.load(open('_cache/diag.json'))}
def fee(p): return 0.05*p*(1-p)
def net(y,p): return y-p-fee(p)-0.01
trig=[r for r in R if r['p_hist'] is not None and r['p_hist']<=r['modelA']-0.05]
print('triggers',len(trig))
from collections import Counter
print('last pre side among triggers',Counter(D[r['key']]['last_pre_side'] for r in trig))
print('trigger t100_h median',round(st.median([D[r['key']]['t100_h'] for r in trig]),2),'max',round(max(D[r['key']]['t100_h'] for r in trig),2))
print('trigger buy_shares_pre min',round(min(D[r['key']]['buy_shares_pre'] for r in trig),1),'median',round(st.median([D[r['key']]['buy_shares_pre'] for r in trig]),1))
for side in ('BUY','SELL'):
    sub=[r for r in trig if D[r['key']]['last_pre_side']==side]
    if sub: print(side,'n',len(sub),'mean first-p_hist',round(st.mean([r['first_buy_price']-r['p_hist'] for r in sub]),4),'net first',round(sum(net(r['y'],r['first_buy_price']) for r in sub),4))
# break-even uniform uplift
base=sum(net(r['y'],r['p_hist']) for r in trig)
for u in [i/1000 for i in range(0,501)]:
    s=sum(r['y']-(r['p_hist']+u)-fee(min(r['p_hist']+u,0.999))-0.01 for r in trig)
    if s<=0:
        print('break-even uplift',u,'base sum',round(base,4)); break
else: print('no break-even <=0.5')
# first buy size>=10, and buys within 2h
for label,cond in [('first buy size>=10',lambda t:t['size']>=10),('first buy within 2h',lambda t:t['timestamp']-cut<=7200)]:
    pass
def first_fill(r,min_size=0,max_h=None):
    j=json.load(open(f"_cache/trades/{r['key']}.json")); tok=j['yes_token']; cut,start=j['cut'],j['start']
    ts=sorted([t for t in j['trades'] if t['asset']==tok and t['side']=='BUY' and cut<t['timestamp']<start],key=lambda z:z['timestamp'])
    for t in ts:
        if t['size']<min_size: continue
        if max_h is not None and t['timestamp']-cut>max_h*3600: break
        return t['price']
    return None
for lab,ms,mh in [('size>=10',10,None),('size>=25',25,None),('<=2h',0,2),('<=4h',0,4)]:
    vals=[(r['y'],first_fill(r,ms,mh)) for r in trig]; vals=[v for v in vals if v[1] is not None]
    print(lab,'n',len(vals),'sum',round(sum(net(y,p) for y,p in vals),4),'mean',round(sum(net(y,p) for y,p in vals)/len(vals),4))
# VWAP 100 shares within first 2h/4h
def vwap_window(r,max_h,cap=100):
    j=json.load(open(f"_cache/trades/{r['key']}.json")); tok=j['yes_token']; cut,start=j['cut'],j['start']
    ts=sorted([t for t in j['trades'] if t['asset']==tok and t['side']=='BUY' and cut<t['timestamp']<start and t['timestamp']-cut<=max_h*3600],key=lambda z:z['timestamp'])
    q=c=0
    for t in ts:
        take=min(t['size'],cap-q)
        if take<=0: break
        c+=take*t['price']; q+=take
        if q>=cap: break
    return (c/q if q>=cap else None,q)
for mh in (2,4):
    vals=[(r['y'],vwap_window(r,mh)) for r in trig]; vals=[(y,v[0]) for y,v in vals if v[0] is not None]
    print('vwap100 <=%dh'%mh,'n',len(vals),'sum',round(sum(net(y,p) for y,p in vals),4))
