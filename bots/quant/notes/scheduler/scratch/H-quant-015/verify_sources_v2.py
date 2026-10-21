#!/usr/bin/env python3
"""Verify every source cited in quant-015 (2026-10-21 hardening).
Checks HTTP status, bytes, sha1 and the exact claim text after (a) collapsing
whitespace, (b) removing '#' comment leaders, (c) stripping HTML tags for the
GISTEMP updates page. Writes nothing except stdout; run from this directory.
"""
import csv, hashlib, json, os, re, time, urllib.request
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
CACHE='_cache'; UA={'User-Agent':'Mozilla/5.0'}
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']

def get(url,timeout=90,tries=4):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.status,r.read()
        except Exception as e:
            last=e; time.sleep(2*(i+1))
    raise last

def norm(s,html=False):
    s=re.sub(r'(?m)^\s*#\s?','',s)
    if html:
        s=re.sub(r'<[a-zA-Z/!][^>]*>',' ',s)
        s=s.replace('&nbsp;',' ').replace('&amp;','&')
    return re.sub(r'\s+',' ',s).strip()

def check(name,url,needles,html=False):
    try:
        st,b=get(url); txt=b.decode('utf-8','ignore'); flat=norm(txt,html=html)
        miss=[n for n in needles if norm(n) not in flat]
        print(f'[{"OK" if not miss else "MISMATCH"}] {name}: HTTP {st}, {len(b)} bytes, sha1={hashlib.sha1(b).hexdigest()[:12]}')
        for n in needles:
            print(f'   {"FOUND" if norm(n,html=html) in flat else "MISSING"}: {n[:130]!r}')
        return st,b,txt
    except Exception as e:
        print(f'[FAIL] {name}: {e!r}'); return None,None,''

print('=== quant-015 cited-source verification v2, 2026-10-21 UTC ===')
st,b,_=check('Gamma Sept event','https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c',[
 'September 2026 Temperature Increase','The brackets are mutually exclusive and collectively exhaustive',
 'GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius',
 'regardless of whether the figure for September 2026 is later revised',
 'this market will resolve to the lowest range bracket','"rate":0.05','"rebateRate":0.25'])
if b:
    e=json.loads(b)[0]
    print(f'   parsed: closed={e.get("closed")} start={e.get("startDate")} end={e.get("endDate")} '
          f'volume={e.get("volume")} OI={e.get("openInterest")} markets={len(e["markets"])} negRisk={e.get("negRisk")} restricted={e.get("restricted")}')
    print('   labels',[m['groupItemTitle'] for m in e['markets']])
    print('   outcomePrices',[m['outcomePrices'] for m in e['markets']])
    print('   all resolved',all(m.get('umaResolutionStatus')=='resolved' for m in e['markets']))

st,b,_=check('Gamma Aug main event','https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489',['August 2026 Temperature Increase','>1.29'])
if b:
    e=json.loads(b)[0]; print('   labels',[m['groupItemTitle'] for m in e['markets']]); print('   outcomePrices',[m['outcomePrices'] for m in e['markets']])
st,b,_=check('Gamma Aug higher-strikes event','https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-higher-strikes',['August 2026 Temperature Increase','1.38'])
if b:
    e=json.loads(b)[0]; print('   labels',[m['groupItemTitle'] for m in e['markets']]); print('   outcomePrices',[m['outcomePrices'] for m in e['markets']])

st,b,_=check('Gamma public-search','https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all',['events'])
if b:
    ev=json.loads(b)['events']; months=set()
    for e in ev:
        t=e.get('title','')
        for i,mn in enumerate(MONTHS):
            if mn in t:
                p=t.replace('(ºC)','').replace('(HIGHER STRIKES)','').replace('(Lower strikes)','').replace('(Lower Ranges)','').split()
                for j,q in enumerate(p):
                    if q==mn and j+1<len(p):
                        try: months.add((int(p[j+1]),i+1)); break
                        except ValueError: pass
    print(f'   events={len(ev)} closed={sum(bool(x.get("closed")) for x in ev)} open={sum(not x.get("closed") for x in ev)} '
          f'YES_tokens={sum(len(x.get("markets",[])) for x in ev)} distinct_months={len(months)} closed_months=29')
    print('   months',sorted(months))
    print('   july-2025 note:',[(x['slug'],x['title']) for x in ev if x['slug'] in ('july-2025-temperature-increase-c-513','july-2025-temperature-increase-c-394')])

st,b,txt=check('ERA5 daily CSV','https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv',[
 'Description: This file contains daily global mean near-surface (2m) air temperature data from ERA5 from 1940 to 2026',
 'updated with a 5-day delay (120 hours)','typically 3 days behind real-time'])
if txt:
    lines=txt.splitlines(); print('   lines',len(lines),'last data line',lines[-1]); print('   last-updated',[l for l in lines if 'Last updated' in l][:1])
st,b,txt=check('Pulse status JSON','https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json',['daily','monthly','annual'])
if txt: print('   parsed',json.loads(txt))
st,b,txt=check('GISTEMP monthly table','https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt',['GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius','2026'])
if txt:
    print('   2026 row',[l for l in txt.splitlines() if re.match(r'^\s*2026\s',l)][:1])
st,b,txt=check('GISTEMP updates page (HTML tags stripped)','https://data.giss.nasa.gov/gistemp/updates_v4/',['Graphs and tables are updated around the middle of every month'],html=True)
st,b,txt=check('Wayback CDX','https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6',['timestamp'])
if b:
    rows=json.loads(b); print('   CDX rows',len(rows)-1,'first',rows[1][1] if len(rows)>1 else None,'since2023',sum(1 for r in rows[1:] if r[1]>='202301'))
st,b,txt=check('Wayback snapshot 20251112105542','https://web.archive.org/web/20251112105542id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt',['2025'])
if txt: print('   2025 row',[l for l in txt.splitlines() if re.match(r'^\s*2025\s',l)][:1])

tok='9561250571098553460692263040980922664627749350602993898138030564733182354111'
st,b,txt=check('CLOB Sept 1.35-1.39 token','https://clob.polymarket.com/prices-history?market='+tok+'&interval=max&fidelity=60',['history'])
if txt:
    h=json.loads(txt).get('history',[]); print('   points',len(h),'first',h[:1],'last',h[-1:])

print('=== weather tag scan cited as 5 pages / 500 closed events ===')
tot=0; matches=[]
for off in range(0,500,100):
    try:
        st,tb=get(f'https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset={off}&closed=true&order=endDate&ascending=false',timeout=120)
        ev=json.loads(tb); tot+=len(ev)
        matches += [x.get('slug') for x in ev if re.search(r'temperature increase|how hot will',(x.get('slug','')+' '+(x.get('title') or '')),re.I)]
        print(f'  offset {off}: HTTP {st}, {len(tb)} bytes, {len(ev)} events')
    except Exception as ex: print(f'  offset {off}: FAIL {ex!r}')
print('  total scanned',tot,'matches',matches)

print('=== data-api + per-month coverage (29 closed months) ===')
tr_files=sorted(f for f in os.listdir(CACHE) if f.startswith('tr_') and f.endswith('.json'))
print('  closed-event trade files',len(tr_files))
rows=list(csv.DictReader(open('primary_months.csv')))
print(f'  primary_months rows={len(rows)} with market_ll={sum(bool(r["market_ll"]) for r in rows)} '
      f'min_trades={min(int(r["n_trades"]) for r in rows)} total_trades={sum(int(r["n_trades"]) for r in rows)}')
sparse=[]
for f in tr_files:
    rec=json.load(open(os.path.join(CACHE,f)))
    if any(len(m.get('trades',[]))==0 for m in rec['markets']): sparse.append(f)
print('  variant files with an empty market (may be unused; primary uses the densest variant):',sparse if sparse else 'none')
# live data-api sample: one conditionId from the first cached month
rec=json.load(open(os.path.join(CACHE,tr_files[0]))); cid=rec['markets'][0]['conditionId']
u=f'https://data-api.polymarket.com/trades?market={cid}&limit=5'
st,b=get(u); j=json.loads(b)
print(f'  live data-api sample {cid}: HTTP {st}, {len(b)} bytes, {len(j)} trades')
