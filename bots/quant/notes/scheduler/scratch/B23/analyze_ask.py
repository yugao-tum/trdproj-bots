import json, csv, datetime as dt
from collections import defaultdict
CACHE='_cache'
ev=json.load(open(f'{CACHE}/events_closed0.json'))
tr=json.load(open(f'{CACHE}/trades_all.json'))['trades']
# map event slug->endDate
ends={e['slug']:e['endDate'] for e in ev}
def yes_ask_from_trade(t):
    # returns (yes_ask_proxy or None, yes_bid_proxy or None)
    p=t['price']; o=t['outcome']; s=t['side']
    if o=='Yes' and s=='BUY': return p,None
    if o=='No' and s=='SELL': return 1-p,None
    if o=='Yes' and s=='SELL': return None,p
    if o=='No' and s=='BUY': return None,1-p
    return None,None
rows=[]
for e in ev:
    if not e['slug'].startswith('state-d4-drought-'): continue
    slug=e['slug']; week=slug.split('state-d4-drought-')[1]
    end=dt.datetime.fromisoformat(e['endDate'].replace('Z','+00:00'))
    cutoff=(end-dt.timedelta(hours=13,minutes=1)).timestamp()
    for m in e['markets']:
        st=m['slug'].split('-')[-1].upper()
        op=json.loads(m['outcomePrices'])
        res=float(op[0])>0.5
        asked=[];bid=[];anyt=[]
        for t in tr.get(m['slug'],[]):
            if t['timestamp']<=cutoff:
                ya,yb=yes_ask_from_trade(t)
                if ya is not None: asked.append((t['timestamp'],ya,t['size']))
                if yb is not None: bid.append((t['timestamp'],yb,t['size']))
                anyt.append((t['timestamp'],t['price'] if t['outcome']=='Yes' else 1-t['price'],t['size'],t['side'],t['outcome']))
        last_ask=max(asked) if asked else None
        last_bid=max(bid) if bid else None
        last_any=max(anyt) if anyt else None
        rows.append({'week':week,'state':st,'res':res,
            'ask':last_ask[1] if last_ask else None,'ask_age':(cutoff-last_ask[0])/3600 if last_ask else None,'ask_size':last_ask[2] if last_ask else None,
            'bid':last_bid[1] if last_bid else None,'bid_age':(cutoff-last_bid[0])/3600 if last_bid else None,'bid_size':last_bid[2] if last_bid else None,
            'any':last_any[1] if last_any else None,'any_age':(cutoff-last_any[0])/3600 if last_any else None,
            'any_side':last_any[3] if last_any else None,'any_outcome':last_any[4] if last_any else None})
json.dump(rows,open('ask_quotes.json','w'))
print('n',len(rows),'ask<=72h',sum(1 for r in rows if r['ask'] is not None and r['ask_age']<=72),
      'bid<=72h',sum(1 for r in rows if r['bid'] is not None and r['bid_age']<=72))
# print all rows with ask-side quote <=72h
for r in sorted(rows,key=lambda x:(x['week'],x['state'])):
    if r['ask'] is not None and r['ask_age']<=72:
        print(f"{r['week']} {r['state']} ask {r['ask']:.3f} age {r['ask_age']:.1f} sz {r['ask_size']} res {r['res']}")
