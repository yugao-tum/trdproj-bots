#!/usr/bin/env python3
import json, os, re, urllib.request, hashlib
from datetime import datetime, timezone
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D); CACHE='_cache'
UA={'User-Agent':'Mozilla/5.0'}
def get(url,timeout=60,tries=3):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.status,r.read()
        except Exception as e: last=e
    raise last
def check(name,url,needles=(),timeout=60):
    try:
        st,b=get(url,timeout=timeout); txt=b.decode('utf-8','ignore')
        flat=re.sub(r'\s+',' ',txt)
        miss=[n for n in needles if n not in flat]
        print(f'[{"OK" if not miss else "MISMATCH"}] {name}: HTTP {st}, {len(b)} bytes, sha1={hashlib.sha1(b).hexdigest()[:12]}')
        for n in needles: print(f'   needle {"FOUND" if n in flat else "MISSING"}: {n[:120]!r}')
        if miss: print('   MISSING COUNT',len(miss))
        return st,b,txt
    except Exception as e:
        print(f'[FAIL] {name}: {e}'); return None,None,''

print('=== fetch/verify cited sources, 2026-10-21 UTC ===')
st,b,txt=check('Gamma Sept event','https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c',
    ['September 2026 Temperature Increase','The brackets are mutually exclusive and collectively exhaustive',
     'GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius','regardless of whether the figure for September 2026 is later revised',
     'this market will resolve to the lowest range bracket','"rate":0.05','"rebateRate":0.25','"negRisk":true','"restricted":true'])
if b:
    e=json.loads(b)[0]
    print('   parsed: closed',e.get('closed'),'start',e.get('startDate'),'end',e.get('endDate'),
          'volume',e.get('volume'),'OI',e.get('openInterest'),'markets',len(e['markets']))
    print('   labels',[m['groupItemTitle'] for m in e['markets']])
    print('   outcomes',[m['outcomePrices'] for m in e['markets']])
    print('   all resolved:',all(m.get('umaResolutionStatus')=='resolved' for m in e['markets']))
st,b,txt=check('Gamma Aug event','https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489',
    ['August 2026 Temperature Increase','>1.29'])
if b:
    e=json.loads(b)[0]; print('   labels',[m['groupItemTitle'] for m in e['markets']])
    print('   outcomes',[m['outcomePrices'] for m in e['markets']])
st,b,txt=check('Gamma public-search','https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all',['events'])
if b:
    d=json.loads(b); ev=d['events']
    print('   events',len(ev),'closed',sum(bool(x.get('closed')) for x in ev),'open',sum(not x.get('closed') for x in ev),
          'YES tokens',sum(len(x.get('markets',[])) for x in ev))
    MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']
    months=set()
    for x in ev:
        t=x.get('title','')
        for i,mn in enumerate(MONTHS):
            if mn in t:
                p=t.split()
                for j,q in enumerate(p):
                    if q==mn and j+1<len(p):
                        try: months.add((int(p[j+1]),i+1)); break
                        except ValueError: pass
    print('   distinct calendar months by title:',len(months),sorted(months))
    print('   July 2025 slugs:',[x['slug'] for x in ev if 'july-2025' in x['slug']])
    print('   2025-08 titles:',[(x['slug'],x.get('title')) for x in ev if '2025' in (x.get('title') or '') and 'August' in (x.get('title') or '')])
st,b,txt=check('ERA5 daily CSV','https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv',
    ['This file contains daily global mean near-surface (2m) air temperature data from ERA5',
     'updated with a 5-day delay (120 hours)','typically 3 days behind real-time'])
if txt:
    lines=txt.splitlines(); print('   lines',len(lines),'last data line',lines[-1]); print('   last-updated comment',[l for l in lines if 'Last updated' in l][:1])
st,b,txt=check('Pulse status JSON','https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json',['daily','monthly','annual'])
if txt: print('   parsed',json.loads(txt))
st,b,txt=check('GISTEMP monthly table','https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt',
    ['GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius','2026'])
if txt:
    row=[l for l in txt.splitlines() if re.match(r'^\s*2026\s',l)]
    print('   2026 row',row[:1])
st,b,txt=check('GISTEMP updates page','https://data.giss.nasa.gov/gistemp/updates_v4/',
    ['Graphs and tables are updated around the middle of every month'])
st,b,txt=check('Wayback CDX','https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6',['timestamp'])
if b:
    rows=json.loads(b); print('   CDX rows',len(rows)-1,'first',rows[1][1] if len(rows)>1 else None,'rows since 202301',sum(1 for r in rows[1:] if r[1]>='202301'))
st,b,txt=check('Wayback snapshot 20251112105542','https://web.archive.org/web/20251112105542id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt',['2025'])
if txt:
    row=[l for l in txt.splitlines() if re.match(r'^\s*2025\s',l)]
    print('   2025 row',row[:1])
# specific CLOB token for Sept 1.35-1.39
tok='9561250571098553460692263040980922664627749350602993898138030564733182354111'
st,b,txt=check('CLOB Sept 1.35-1.39 token','https://clob.polymarket.com/prices-history?market='+tok+'&interval=max&fidelity=60',['history'])
if txt:
    h=json.loads(txt).get('history',[])
    print('   points',len(h),'first',h[:1],'last',h[-1:] if h else None)
# tag scan pages 0..400
print('=== Gamma weather tag pages (cited as 5 pages, 500 closed events) ===')
tot=0; matches=[]
for off in range(0,500,100):
    u=f'https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset={off}&closed=true&order=endDate&ascending=false'
    try:
        st,tb=get(u,timeout=90); ev=json.loads(tb); tot+=len(ev)
        for x in ev:
            s=(x.get('slug','')+' '+(x.get('title') or ''))
            if re.search(r'temperature increase|how hot will',s,re.I): matches.append(x.get('slug'))
        print(f'  offset {off}: HTTP {st}, {len(tb)} bytes, {len(ev)} events')
    except Exception as ex: print(f'  offset {off}: FAIL {ex}')
print('  total scanned',tot,'matches',matches)
