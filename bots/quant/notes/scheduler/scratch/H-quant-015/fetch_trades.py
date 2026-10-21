#!/usr/bin/env python3
import json, os, time, urllib.request, urllib.error, calendar
from datetime import datetime, timezone, timedelta

D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
CACHE='_cache'; UA={'User-Agent':'Mozilla/5.0'}
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']

def get(url, timeout=45, tries=4):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.status, r.read()
        except Exception as e:
            last=e; time.sleep(1.5*(i+1))
    raise last

def month_of(e):
    t=e.get('title','')
    for i,mn in enumerate(MONTHS):
        if mn in t and str(2000+int(t.split(mn)[1].strip().split()[0])) in t:
            pass
    # title like "July 2025 Temperature Increase (ºC)"
    tok=t.replace('(ºC)','').replace('(ºC)','').replace('(HIGHER STRIKES)','').replace('(Lower strikes)','').replace('(Lower Ranges)','').strip()
    parts=tok.split()
    for i in range(len(parts)-1):
        if parts[i] in MONTHS:
            try: return int(parts[i+1]), MONTHS.index(parts[i])+1
            except ValueError: pass
    raise ValueError(t)

def decision_ts(y,m):
    # 5th of following month 00:00 UTC
    yy,mm=(y+1,1) if m==12 else (y,m+1)
    return int(datetime(yy,mm,5,tzinfo=timezone.utc).timestamp())

evs=[]
for fn in sorted(os.listdir(CACHE)):
    if fn.startswith('ev_') and fn.endswith('.json'):
        e=json.load(open(os.path.join(CACHE,fn)))[0]
        if not e.get('closed'): continue
        y,m=month_of(e); evs.append((y,m,e))

print('closed events',len(evs),'distinct months',len(set((y,m) for y,m,_ in evs)))
monthly={}
for y,m,e in sorted(evs,key=lambda x:(x[0],x[1])):
    monthly.setdefault((y,m),[]).append(e)

for (y,m),group in sorted(monthly.items()):
    dec=decision_ts(y,m)
    for e in group:
        slug=e['slug']
        out=[]
        for mk in e['markets']:
            cid=mk.get('conditionId')
            if not cid: continue
            trades=[]; off=0
            while True:
                u=(f'https://data-api.polymarket.com/trades?market={cid}'
                   f'&start={dec-10*86400}&end={dec+8*86400}&limit=500&offset={off}')
                st,b=get(u)
                try: j=json.loads(b)
                except Exception: j=[]
                if not isinstance(j,list): j=[]
                trades.extend(j)
                if len(j)<500 or off>=10000: break
                off+=500; time.sleep(0.05)
            out.append({'label':mk.get('groupItemTitle'),'conditionId':cid,
                        'outcomePrices':mk.get('outcomePrices'),'trades':trades})
            time.sleep(0.03)
        rec={'slug':slug,'title':e.get('title'),'month':[y,m],'decision_ts':dec,
             'markets':out}
        json.dump(rec,open(os.path.join(CACHE,'tr_'+slug+'.json'),'w'))
        print(slug,y,m,'markets',len(out),'trades',sum(len(x['trades']) for x in out))
