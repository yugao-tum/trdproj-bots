# quant-021 第2轮准备：加强版核对日志 + glm-5.3 事实核查（已按核查修正 +0.263→+0.303 等）

## VERIFICATION LOG (reviewer only, not for commit)

All fetches with `curl -sL -A "Mozilla/5.0" --max-time 30` or Python `urllib` with the same UA. Session date 2026-10-20 (UTC). Working dir `/workspace/agent-tools/quant-r2prep/work_R021`. Repo `/workspace/trdproj-bots` read-only, untouched.

### V0. Repo inputs read

```
$ sed -n '/^## 2\./,/^## 3\./p' GUIDE.md      # 七条门槛 (read in full)
$ awk '/^## 7\./,/^## 9\./' GUIDE.md          # 条目格式 + Polymarket 要点
$ awk '/^## 10\./,/^## 12\./' GUIDE.md        # 红线 + 分类
$ cat templates/ENTRY.md                      # front-matter 与正文章节
$ cat bots/quant/entries/quant-021-f1-pole-winner-base-rate.md   # 原件 20,935 bytes, 已复制为 work_R021/orig.md
```
HTTP: n/a (local files). Snippets used are quoted in the entry above.

### V1. Gamma: closed F1 events (pagination)

```
$ for o in 0 100 200 300 400; do curl -sL -A "Mozilla/5.0" --max-time 30 \
   "https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset=$o" \
   -o g$o.json -w "offset=$o http=%{http_code} bytes=%{size_download}\n"; done
offset=0 http=200 bytes=5894415
offset=100 http=200 bytes=7071034
offset=200 http=200 bytes=6930957
offset=300 http=200 bytes=6798285
offset=400 http=200 bytes=8479
```
Script `an1.py` (full):
```python
import json,glob,re,collections
ev={}
for f in sorted(glob.glob('g*.json')):
    d=json.load(open(f))
    for e in d:
        ev[e['id']]=e
print("unique events", len(ev))
cats=collections.Counter()
for e in ev.values():
    t=e.get('title','')
    if re.search(r'Pole Position',t,re.I): c='Pole'
    elif re.search(r'Podium',t,re.I): c='Podium'
    elif re.search(r'Winner',t,re.I): c='Winner'
    elif re.search(r'Sprint',t,re.I): c='Sprint/other'
    else: c='Other: '+t[:40]
    cats[c]+=1
for k,v in cats.most_common(30): print(v,k)
```
Exact output (first lines):
```
unique events 401
84 Winner
45 Pole
21 Other: Will there be a safety car during the 20
20 Podium
18 Other: Will there be a red flag during the 2026
4 Other: F1 British Grand Prix: Which Constructor
...
```
(After excluding the 19 Sprint/Constructor-ish winners by title in `mk_cands.py`: `149 {'Winner': 65, 'Sprint/Other': 19, 'Pole': 45, 'Podium': 20}`, `markets total 3433`.)

### V2. CLOB prices-history: parameter discovery

```
$ T=28558391061191296576456870322949545965070312914289181555918414954825561771030
$ for q in "interval=max&fidelity=60" "interval=max&fidelity=1" "interval=max&fidelity=10" \
           "interval=max" "fidelity=60&startTs=1790900000&endTs=1791150000" \
           "startTs=1790900000&endTs=1791150000&fidelity=10"; do
    echo "== $q"; curl -sL -A "Mozilla/5.0" --max-time 30 \
      "https://clob.polymarket.com/prices-history?market=$T&$q" -w "\nHTTP=%{http_code} bytes=%{size_download}\n" | head -c 400; done
== interval=max&fidelity=60
{"history":[{"t":1791028820,"p":0.495},{"t":1791032419,"p":0.495},...
HTTP=200
== interval=max&fidelity=1 / fidelity=10 / (none)
{"history":[{"t":1791028218,"p":0.495},...
HTTP=200
== fidelity=60&startTs=1790900000&endTs=1791150000
{"history":[{"t":1791028820,"p":0.495},...
HTTP=200      # <-- startTs/endTs WORKS (contradicts the previous draft's "HTTP 400" claim)
== startTs=1790900000&endTs=1791150000&fidelity=10
{"history":[{"t":1791028218,"p":0.495},...
HTTP=200
```
Span limit test (token 810874737554…, endTs=1725321600):
```
span=5 days:  {"history":[{... HTTP=200
span=10 days: {"history":[{... HTTP=200
span=14 days: {"history":[{... HTTP=200
span=15 days: {"history":[{... HTTP=200
span=20 days: {"error":"invalid filters: 'startTs' and 'endTs' interval is too long"} HTTP=400
span=30 days: same 400
span=45 days: same 400
```
Old-market availability test (3 probes): 2024-08-29 Italian GP token, 2025-07 Hungarian, 2026-03 Australian — all returned non-empty series starting well before the race. Example 2024 token:
```
$ curl -sL -A "Mozilla/5.0" --max-time 30 "https://clob.polymarket.com/prices-history?market=81087473755442291139898883521219964217456950730026946273855666781746498030841&startTs=1724544000&endTs=1725321600&fidelity=60" -w "\nHTTP=%{http_code}\n"
{"history":[{"t":1724947202,"p":0.5},{"t":1724950802,"p":0.255},...
HTTP=200
```
First bulk attempt with a 45-day span → **all 3,433 requests failed 400** (proof that the span limit, not availability, was the blocker):
```
$ python3 bulk.py   # span 45d, 24 threads
jobs 3433
0 1 0
400 401 0
...
total 3433 nonempty 0 events_with_any 0
$ python3 -c "import json,collections;o=json.load(open('ph.json'));print(collections.Counter(str(r['err'])[:120] for r in o).most_common(5))"
[('HTTP Error 400: Bad Request', 3432), ('The read operation timed out', 1)]
```
Rerun with 14-day spans (`bulk.py`, full):
```python
import json,re,os,concurrent.futures as cf,urllib.request,time
E=json.load(open('events.json'))
H={'User-Agent':'Mozilla/5.0'}
def get(u):
    for a in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30))
        except Exception as e:
            err=str(e); time.sleep(1.2)
    return {'_err':err}
jobs=[]
for ev in E:
    m=re.search(r'(\d{4}-\d{2}-\d{2})',ev['slug'])
    if m: d=m.group(1)
    elif ev['endDate']: d=ev['endDate'][:10]
    else: d=None
    ev['racedate']=d
    if not d: continue
    import datetime as dt
    rd=dt.date.fromisoformat(d)
    s=int(dt.datetime(rd.year,rd.month,rd.day,tzinfo=dt.timezone.utc).timestamp())
    ev['ts']=s
    for mk in ev['markets']:
        if mk['token']: jobs.append((ev['slug'],mk['slug'],mk['token'],s-12*86400,s+2*86400))
print("jobs",len(jobs))
def work(j):
    evslug,mkslug,tok,s,e=j
    u=f"https://clob.polymarket.com/prices-history?market={tok}&startTs={s}&endTs={e}&fidelity=60"
    r=get(u)
    h=r.get('history') if isinstance(r,dict) else None
    return {'ev':evslug,'mk':mkslug,'tok':tok,'n':len(h) if h else 0,'err':r.get('_err') if isinstance(r,dict) else 'x',
            'h':h if h else []}
out=[]
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    for i,r in enumerate(ex.map(work,jobs)):
        out.append(r)
        if i%400==0: print(i,len(out),r['n'],flush=True)
json.dump(out,open('ph.json','w'))
json.dump(E,open('events2.json','w'),indent=0)
nz=[r for r in out if r['n']>0]
print("total",len(out),"nonempty",len(nz),"events_with_any",len({r['ev'] for r in nz}))
```
Exact output:
```
jobs 3433
0 1 77
400 401 250
800 801 124
1200 1201 186
1600 1601 50
2000 2001 314
2400 2401 310
2800 2801 316
3200 3201 49
total 3433 nonempty 2818 events_with_any 146
```
Follow-up: `markets 3433 nonempty 2818 events any 146 / total points 611137`

### V3. Ergast fetch (script + output)

`fetch_erg.py` (full):
```python
import json,urllib.request,time,sys
H={'User-Agent':'Mozilla/5.0'}
def get(u):
    for a in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))
        except Exception as e:
            print("retry",u,e,file=sys.stderr); time.sleep(2)
    return None
out={}
for season in range(2014,2027):
    for kind in ('qualifying','results'):
        allrows=[];off=0
        while True:
            u=f"https://api.jolpi.ca/ergast/f1/{season}/{kind}.json?limit=100&offset={off}"
            d=get(u)
            if not d: break
            mr=d['MRData']; tot=int(mr['total']); rows=mr['RaceTable']['Races']
            allrows.extend(rows); off+=100
            if off>=tot: break
        out[f"{season}_{kind}"]=allrows
        print(season,kind,"total",tot,"fetched_races",len(allrows),file=sys.stderr)
json.dump(out,open('erg/raw.json','w'))
```
Output (tail):
```
2024 qualifying total 479 fetched_races 28
2024 results total 479 fetched_races 28
2025 qualifying total 479 fetched_races 24
2025 results total 479 fetched_races 27
2026 qualifying total 369 fetched_races 20
2026 results total 374 fetched_races 20
```
(`fetched_races` > rounds because pagination windows split races mid-race; dedupe by `round` below.)

### V4. Base rates — correction of the previous draft

`build2.py` (full):
```python
import json,re,collections
raw=json.load(open('erg/raw.json'))
def tsec(s):
    if not s: return None
    m=re.match(r'^(?:(\d+):)?(\d+):(\d+\.?\d*)$',s)
    if m: return int(m.group(1) or 0)*3600+int(m.group(2))*60+float(m.group(3))
    m=re.match(r'^(\d+):(\d+\.?\d*)$',s)
    if m: return int(m.group(1))*60+float(m.group(2))
    return None
races={}
for season in range(2014,2027):
    q={int(x['round']):x for x in raw[f"{season}_qualifying"]}
    r={int(x['round']):x for x in raw[f"{season}_results"]}
    for rnd,rd in r.items():
        loc=rd['Circuit'].get('Location',{})
        rec={'season':season,'round':rnd,'name':rd['raceName'],'date':rd['date'],
             'circuit':rd['Circuit']['circuitId'],
             'country':loc.get('country'),'locality':loc.get('locality')}   # final5.py 的 event→比赛 匹配需要 country/locality
        qq=q.get(rnd)
        if qq:
            qual=[]
            for x in qq.get('QualifyingResults',[]):
                best=None
                for kk in ('Q3','Q2','Q1'):
                    v=tsec(x.get(kk))
                    if v is not None and (best is None or v<best): best=v
                qual.append({'d':x['Driver']['driverId'],'pos':int(x['position']),'best':best})
            qual.sort(key=lambda z:z['pos'])
            if qual:
                rec['pole']=qual[0]['d']; rec['pole_best']=qual[0]['best']
                rec['p2']=qual[1]['d'] if len(qual)>1 else None
                rec['p2_best']=qual[1]['best'] if len(qual)>1 else None
                a,b=qual[0]['best'],rec['p2_best']
                rec['margin']=round(b-a,3) if (a and b) else None
        res=rd.get('Results',[])
        if res:
            w=min(res,key=lambda x:int(x['position']))
            rec['winner']=w['Driver']['driverId']; rec['winner_pos']=int(w['position'])
            rec['grid']={x['Driver']['driverId']:int(x['grid']) for x in res}
            rec['finpos']={x['Driver']['driverId']:int(x['position']) for x in res}
            rec['status']={x['Driver']['driverId']:x.get('status') for x in res}
        races[f"{season}-{rnd}"]=rec
json.dump(races,open('races.json','w'),indent=0)
print("races",len(races))
tot=sum(1 for v in races.values() if v.get('pole') and v.get('winner'))
pw=sum(1 for v in races.values() if v.get('pole') and v.get('winner') and v['pole']==v['winner'])
print("pole wins",pw,"/",tot,round(pw/tot,4))
by=collections.defaultdict(lambda:[0,0])
for v in races.values():
    if not (v.get('pole') and v.get('winner')): continue
    s=v['season']; by[s][1]+=1
    if v['pole']==v['winner']: by[s][0]+=1
print({s:(by[s][0],by[s][1],round(by[s][0]/by[s][1],3)) for s in sorted(by)})
print("2022-2026",sum(by[s][0] for s in range(2022,2027)),"/",sum(by[s][1] for s in range(2022,2027)))
print("2014-2023",sum(by[s][0] for s in range(2014,2024)),"/",sum(by[s][1] for s in range(2014,2024)))
print("2026",by[2026])
b=collections.Counter()
for v in races.values():
    m=v.get('margin')
    if m is None: continue
    k='[0,.05)' if m<0.05 else '[.05,.2)' if m<0.2 else '[.2,.5)' if m<0.5 else '>=.5'
    b[k]+=1
print("margins",dict(b),"total",sum(b.values()))
g=collections.Counter()
for v in races.values():
    w=v.get('winner')
    if w and w in v.get('grid',{}): g[v['grid'][w]]+=1
print("winner grid dist",dict(sorted(g.items())))
```
Exact output:
```
races 269
pole wins 137 / 269 0.5093
{2014: (6, 19, 0.316), 2015: (11, 19, 0.579), 2016: (11, 21, 0.524), 2017: (9, 20, 0.45), 2018: (10, 21, 0.476), 2019: (6, 21, 0.286), 2020: (10, 17, 0.588), 2021: (12, 22, 0.545), 2022: (10, 22, 0.455), 2023: (15, 22, 0.682), 2024: (13, 24, 0.542), 2025: (13, 24, 0.542), 2026: (11, 17, 0.647)}
2022-2026 62 / 109
2014-2023 100 / 204
2026 [11, 17]
margins {'[0,.05)': 60, '[.2,.5)': 83, '>=.5': 28, '[.05,.2)': 96} total 267
winner grid dist {1: 140, 2: 62, 3: 27, 4: 9, 5: 3, 6: 7, 7: 3, 8: 1, 9: 3, 10: 4, 13: 2, 14: 2, 15: 1, 16: 1, 17: 1, 19: 1, 20: 1, 22: 1}
```
Discrepancy check vs previous draft (extra variant run, `chk3.py`, output):
```
n 267
B pole(fastest lap) wins 134 / 267 0.5019
B margin buckets {'b': 106, 'a': 54, 'c': 81, 'd': 26}
```
→ neither 137/269 nor 134/267 reproduces the previous draft's 150/269 = 0.5576, and neither margin distribution matches its 50/95/93/30. Cause **未查到**.

Note also: `results[0]` is **not** reliably the winner in this feed (21 races list a non-winner first); `build2.py` uses `min(position)` instead. That was a real bug found while reproducing.

### V5. Event→race matching and final model/market test

`match2.py` matched 140 of 149 events (9 unmatched: 7 Brazilian-GP slug variants lacking a keyword in my synonym map, 2 IndyCar events which I then excluded). Date-diff distribution: `[(0, 72), (1, 50), (2, 14), (175, 2), (176, 2)]` — the 4 far-off ones are duplicate listings for the 2026 Bahrain race, dropped by the `>10 days` guard. After dedupe (one event per race+category, keeping the one with most priced markets): **103 events = Winner 49 / Pole 35 / Podium 19**.

`final5.py` full script and exact output are in `work_R021/final5.py` and reproduced below (key sections):

```
events matched/deduped: 103 {'Winner': 49, 'Pole': 35, 'Podium': 19}

[FIT 2014-2023] n=204 polewins=100 rate=0.4902 const=0.4903
   [0,.05)   p=0.4082 (19/47)
   [.05,.2)  p=0.4583 (32/70)
   [.2,.5)   p=0.5077 (32/63)
   >=.5      p=0.7200 (17/23)
   na        p=0.3333 (0/1)

[OOS 2024-2026 all races] n=65 wins=37 rate=0.5692
   A logloss=0.7236 brier=0.2641 | B logloss=0.6960 brier=0.2514
   >=.5      realised 1/5=0.200 predA=0.720
   [.05,.2)  realised 15/26=0.577 predA=0.458
   [.2,.5)   realised 15/20=0.750 predA=0.508
   [0,.05)   realised 6/13=0.462 predA=0.408
   na        realised 0/1=0.000 predA=0.333

[CONSISTENCY] Ergast winner == Polymarket resolved winner: 41/49
   disagreeing races: [('2024-16', 'piastri', ['charlesleclerc']), ('2024-21', 'ocon', ['maxverstappen']), ('2025-11', 'piastri', ['landonorris']), ('2025-16', 'norris', ['maxverstappen']), ('2025-21', 'antonelli', ['landonorris']), ('2026-5', 'bortoleto', ['kimiantonelli']), ('2026-10', 'max_verstappen', ['kimiantonelli']), ('2026-14', 'albon', ['kimiantonelli'])]

[MARKET] Winner events with pole price: n=49
   2024-16   mkt=0.140 modelA=0.408 y=0 margin=0.004
   2024-17   mkt=0.475 modelA=0.508 y=0 margin=0.321
   2024-18   mkt=0.575 modelA=0.458 y=1 margin=0.155
   2024-19   mkt=0.275 modelA=0.408 y=0 margin=0.031
   2024-21   mkt=0.535 modelA=0.458 y=0 margin=0.173
   2024-22   mkt=0.095 modelA=0.458 y=1 margin=0.098
   2024-23   mkt=0.255 modelA=0.458 y=1 margin=0.055
   2024-24   mkt=0.565 modelA=0.508 y=1 margin=0.209
   2025-1    mkt=0.360 modelA=0.458 y=1 margin=0.084
   2025-2    mkt=0.500 modelA=0.458 y=1 margin=0.082
   2025-3    mkt=0.280 modelA=0.408 y=1 margin=0.012
   2025-4    mkt=0.710 modelA=0.458 y=1 margin=0.168
   2025-5    mkt=0.370 modelA=0.408 y=0 margin=0.01
   2025-6    mkt=0.355 modelA=0.333 y=0 margin=None
   2025-7    mkt=0.635 modelA=0.408 y=0 margin=0.034
   2025-8    mkt=0.560 modelA=0.458 y=1 margin=0.109
   2025-9    mkt=0.570 modelA=0.508 y=1 margin=0.209
   2025-10   mkt=0.220 modelA=0.458 y=1 margin=0.16
   2025-11   mkt=0.685 modelA=0.720 y=1 margin=0.521
   2025-12   mkt=0.375 modelA=0.458 y=0 margin=0.103
   2025-13   mkt=0.425 modelA=0.458 y=0 margin=0.064
   2025-14   mkt=0.185 modelA=0.408 y=0 margin=-0.431
   2025-15   mkt=0.605 modelA=0.408 y=1 margin=0.012
   2025-16   mkt=0.305 modelA=0.458 y=1 margin=0.077
   2025-17   mkt=0.665 modelA=0.508 y=1 margin=0.478
   2025-18   mkt=0.385 modelA=0.458 y=1 margin=0.182
   2025-19   mkt=0.610 modelA=0.508 y=1 margin=0.291
   2025-20   mkt=0.685 modelA=0.508 y=1 margin=0.262
   2025-21   mkt=0.705 modelA=0.458 y=1 margin=0.174
   2025-22   mkt=0.465 modelA=0.508 y=0 margin=0.323
   2025-23   mkt=0.585 modelA=0.458 y=0 margin=0.108
   2025-24   mkt=0.715 modelA=0.508 y=1 margin=0.201
   2026-1    mkt=0.715 modelA=0.508 y=1 margin=0.293
   2026-2    mkt=0.265 modelA=0.508 y=1 margin=0.222
   2026-3    mkt=0.585 modelA=0.508 y=1 margin=0.298
   2026-4    mkt=0.405 modelA=0.458 y=1 margin=0.166
   2026-5    mkt=0.002 modelA=0.720 y=0 margin=0.658
   2026-6    mkt=0.590 modelA=0.408 y=1 margin=0.043
   2026-7    mkt=0.525 modelA=0.458 y=0 margin=0.064
   2026-8    mkt=0.365 modelA=0.508 y=1 margin=0.236
   2026-9    mkt=0.650 modelA=0.458 y=0 margin=0.175
   2026-10   mkt=0.075 modelA=0.408 y=0 margin=0.026
   2026-11   mkt=0.347 modelA=0.408 y=1 margin=0.012
   2026-13   mkt=0.059 modelA=0.458 y=0 margin=0.06
   2026-14   mkt=0.001 modelA=0.720 y=0 margin=0.525
   2026-12   mkt=0.365 modelA=0.458 y=1 margin=0.102
   2026-15   mkt=0.645 modelA=0.720 y=1 margin=0.837
   2026-16   mkt=0.605 modelA=0.508 y=1 margin=0.298
   2026-17   mkt=0.650 modelA=0.458 y=1 margin=0.054
   mean mkt=0.443 mean modelA=0.480 realised=0.633
   calibration by mkt price bucket:
      mkt~0.1  1/7=0.143
      mkt~0.2  4/5=0.800
      mkt~0.4  8/14=0.571
      mkt~0.6  14/19=0.737
      mkt~0.8  4/4=1.000
   RULE A(margin): trades=21  sum_net/sh=+7.2107  mean=+0.3434  winrate=13/21
      2024-16   mkt=0.140 model=0.408 y=0 net/sh=-0.1560
      2024-19   mkt=0.275 model=0.408 y=0 net/sh=-0.2950
      2024-22   mkt=0.095 model=0.458 y=1 net/sh=+0.8912
      2024-23   mkt=0.255 model=0.458 y=1 net/sh=+0.7255
      2025-1    mkt=0.360 model=0.458 y=1 net/sh=+0.6185
      2025-3    mkt=0.280 model=0.408 y=1 net/sh=+0.6999
      2025-10   mkt=0.220 model=0.458 y=1 net/sh=+0.7614
      2025-12   mkt=0.375 model=0.458 y=0 net/sh=-0.3967
      2025-14   mkt=0.185 model=0.408 y=0 net/sh=-0.2025
      2025-16   mkt=0.305 model=0.458 y=1 net/sh=+0.6744
      2025-18   mkt=0.385 model=0.458 y=1 net/sh=+0.5932
      2026-2    mkt=0.265 model=0.508 y=1 net/sh=+0.7153
      2026-4    mkt=0.405 model=0.458 y=1 net/sh=+0.5730
      2026-5    mkt=0.002 model=0.720 y=0 net/sh=-0.0116
      2026-8    mkt=0.365 model=0.508 y=1 net/sh=+0.6134
      2026-10   mkt=0.075 model=0.408 y=0 net/sh=-0.0885
      2026-11   mkt=0.347 model=0.408 y=1 net/sh=+0.6312
      2026-13   mkt=0.059 model=0.458 y=0 net/sh=-0.0723
      2026-14   mkt=0.001 model=0.720 y=0 net/sh=-0.0105
      2026-12   mkt=0.365 model=0.458 y=1 net/sh=+0.6134
      2026-15   mkt=0.645 model=0.720 y=1 net/sh=+0.3336
   RULE B(const): trades=23  sum_net/sh=+5.6619  mean=+0.2462  winrate=12/23
      (23 lines, same format; see work_R021/final5.py output)
   BASELINE always buy pole: n=49 net/sh sum=+8.2887 mean=+0.1692

[FAVOURITE] n=49 mean=0.522 realised=0.551 sum_net/sh=+0.3736
      (49 lines; sample)
      2024-16   fav=0.625 won=0 (landonorris)
      2025-24   fav=0.715 won=1 (maxverstappen)
      2026-17   fav=0.650 won=1 (maxverstappen)

[PRICE SUM per event] [1.066, 1.0, 1.092, 1.568, 1.04, 1.028, 1.058, 1.019, 1.022, 1.044, 1.053, 1.077, 1.03, 0.99, 1.048, 1.036, 1.028, 1.262, 1.042, 1.085, 1.004, 1.018, 1.05, 1.044, 1.018, 1.039, 1.104, 1.169, 1.049, 1.131, 1.099, 1.037, 1.027, 1.025, 1.022, 1.049, 1.013, 1.049, 1.036, 1.041, 1.038, 1.04, 1.065, 1.067, 1.046, 1.031, 1.042, 1.11, 1.04]
```

### V6. Bugs / false starts found during this round (report, don't hide)

1. First `price_at` used the slug/`endDate`-derived date as the cut → for events whose `endDate` is the market close (e.g. `bahrain-grand-prix-winner`, `endDate=2025-04-14T12:00Z`, race 2025-04-13), the "pre-race" price was actually the **post-resolution** price (fav = 1.000). Fixed by cutting on the **Ergast race date 00:00 UTC**. Symptom before fix: favourites showed `won=0` for nearly all events and rules A/B both made +6.6/share.
2. A 45-day window (both in bulk and in the first probes) makes **every** request 400. This is the most likely reason the previous draft concluded "only ~1 month of history".
3. `results[0]` is not the winner in 21 of 269 races in this feed (list not sorted by position); must use `min(position)`.
4. Driver-name matching: market questions sometimes use family name only (`verstappen`) or the Ergast driverId is `max_verstappen`; the first version matched only full normalised strings and silently dropped 47/49 pole-sitter prices (n=2). Fixed with family-name/code containment.

### V7. Numbers NOT verified this session (declared 未查到)

- Exact maximum `startTs/endTs` span (only bounded: 15 d OK, 20 d 400) — 未查到精确值.
- Historical bid/ask for these markets — 无公开来源，未查到.
- Why the previous draft's 150/269 and its margin buckets can't be reproduced — 未查到.
- Why Ergast and Polymarket disagree on the winner in 8/49 races — 未查到 (mapping error vs source disagreement).
- `umaBond` / `liveness` for the F1 events — 未查到.
- OpenF1 fields / coverage — 未取，未查到.

---

## glm-5.3 事实核查报告

All checks complete. Here is my report.

---

## Fact-check report — R021.md (quant-021, F1 pole/winner)

**URL re-fetches (14): all live, all key fields check out.**
- Gamma `tag_slug=f1&closed=true` (5 pages re-pulled): **401 unique events; Winner 84 / Pole 45 / Podium 20** — VERIFIED.
- 4 event slugs: US-Winner 29 markets, negRisk=true, volume 3,523.28, feeSchedule `{rate:0.05, exponent:1, takerOnly, rebateRate:0.15}`, resolutionSource formula1.com — VERIFIED. Liquidity now 83,874 (entry: 82,670.55) and pole 12,321 (entry: 12,211.34): time-varying same-day drift, worker gave 2026-10-20 timestamp — acceptable. Podium: 23 markets, negRisk=false, vol 202.69 — VERIFIED. Singapore: closed, vol 1,131,293.19, `outcomePrices ["1","0"]` → Verstappen — VERIFIED. All rule-text quotes ("Final Classification…", "regardless of any subsequent penalties…", podium 50-50 cancel, Nov 1 "Other") — VERIFIED verbatim. Verstappen pole bb/ba now 0.24/0.46 (entry 0.25/0.46) — time-varying.
- CLOB: `interval=max&fidelity=60` on cited token → exactly **200 points**; 15-day startTs/endTs → 200; 20-day → 400 with exact error string; 2024 token first point `t=1724947202` (2024-08-29) — all VERIFIED.
- Ergast 2024 qualifying: `limit=100`, `total=479` — VERIFIED.

**Script re-run (step 3b):** `build2.py` and `final5.py` reproduce **every** headline number exactly: 269 races, 137/269=0.5093, 100/204, 37/65, 11/17; margins 60/96/83/28; grid dist 140/62/27/19/11/10; fit 0.408/0.458/0.508/0.720; OOS logloss 0.7236 vs 0.6960; n=49, mean mkt 0.443, realised 0.633, 31/49; Rule A 21 trades +7.2107/+0.3434; B 23/+5.6619/+0.2462; baseline +8.2887/+0.1692; favourite 0.522/0.551/+0.3736; 41/49 consistency + same 8 races; ph.json 3433/2818/146/611,137 pts. Fee arithmetic (0.01232/0.01097/0.008) all correct.

**Problems found:**
1. **MISMATCH (门槛自查 5):** "把半价差提到 5¢，规则 A 的均值降到约 **+0.263**/份" — recomputation from the trade list gives **+0.303** (+0.263 corresponds to a 9¢ half-spread). Direction is conservative but the number doesn't follow from the stated formula. Fix to ≈+0.303.
2. Minor imprecision (证据 3): "价格之和多数在 1.00–1.09，个别 1.26/1.57" — four events sit at 1.10–1.17 unmentioned; "多数" still true (43/49). Suggest "≤1.17，个别 1.26/1.57".
3. Reproducibility gap in the log: pasted `build2.py` doesn't emit `country/locality` that `final5.py` needs (worker's `races.json` has them); core fields rebuild identically, but the pasted pipeline isn't fully self-contained.
4. Duplication check: no F1 entry anywhere (KNOWN F-F1-* are crypto factors — entry's reading is correct). Nearest neighbors quant-006 (tennis Elo) and KNOWN V-V2-poly-longshot / dot-009; entry flags quant-006 but should also name V-V2-poly-longshot in 门槛自查 4.

**Rule compliance:** front-matter fields all valid (sports, S, direction, 草稿/中, name ≤18 chars); fee formula per GUIDE §8 correct; 来源自报 labelled (Gamma volumes); no unrun backtests claimed (backtest fully reproduced); no keys/paid data; honest 门槛自查 throughout.

VERDICT: FIX — all sources and every material number verify (and scripts reproduce exactly), but the 5¢-sensitivity figure (+0.263 vs actual +0.303) is a genuine arithmetic mismatch that should be corrected before marking 待核.

GATES_PASSING: 7/7
