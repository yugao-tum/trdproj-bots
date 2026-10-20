import json,requests
S=requests.Session();S.headers['User-Agent']='Mozilla/5.0'
slugs=['ipl-rcb-rr-2025-04-24','usa-vs-india-cricket-t20-world-cup','crint-gbr-nzl-2026-02-27','intt20-aus-ind-2025-10-29','crint-mex-arg-2026-03-14','asia-cup-india-vs-pakistan-2025-09-14']
out=[]
for s in slugs:
    r=S.get('https://gamma-api.polymarket.com/events',params={'slug':s},timeout=30)
    d=r.json()
    if not d: out.append({'slug':s,'error':r.status_code}); continue
    e=d[0]; m=[x for x in e.get('markets',[]) if (x.get('question') or '')==(e.get('title') or '')]
    m=m[0] if m else e.get('markets',[{}])[0]
    out.append({'slug':s,'url':'https://gamma-api.polymarket.com/events?slug='+s,'event_end':e.get('endDate'),
      'volume':e.get('volume'),'question':m.get('question'),'description':m.get('description'),
      'resolutionSource':m.get('resolutionSource'),'feeSchedule':m.get('feeSchedule'),'feesEnabled':m.get('feesEnabled'),
      'outcomes':m.get('outcomes'),'outcomePrices':m.get('outcomePrices'),'closedTime':m.get('closedTime')})
json.dump(out,open('rules.json','w'),indent=1)
for o in out:
    print('\n====',o['slug'],'| fee',o.get('feeSchedule'),o.get('feesEnabled'),'| src',repr(o.get('resolutionSource')))
    print(o.get('description','')[:700])
