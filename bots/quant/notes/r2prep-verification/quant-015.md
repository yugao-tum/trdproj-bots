# quant-015 第2轮准备：加强版核对日志（deepseek-flash）+ glm-5.3 事实核查

## VERIFICATION LOG (reviewer only, not for commit)

All fetches were made on 2026-10-20 UTC with `curl -sL -A "Mozilla/5.0" --max-time 30` (data CSV: `--max-time 60`), or with Python `urllib` where noted. No keys, no trading, no write under `/workspace/trdproj-bots`.

### A. URLs fetched, HTTP result, snippet

| URL | HTTP | bytes | snippet / result |
|---|---:|---:|---|
| `https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c` | 200 | 26,352 | `closed=true`, `endDate=2026-11-02T04:59:00Z`, `negRisk=true`, `volume=11127.859859`, `openInterest=8452.463409`; description: “resolve according to the value reported by the Global Land-Ocean Temperature Index for September 2026 … regardless of whether the figure … is later revised”; source table `GLB.Ts+dSST.txt`; fallback resolves lowest bracket. |
| `https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489` | 200 | 25,839 | `closed=true`; first market `<1.10ºC`; description source column “Aug”; `volume=15901.867726`, `openInterest=6722.919473`. |
| `https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all` | 200 | 829,034 | 33 events: 32 closed, 1 open; 29 distinct calendar months. |
| `https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset=0..400&closed=true&order=endDate&ascending=false` | 200 (5 pages) | 5,799,056 / 6,090,103 / 6,129,222 / 5,880,758 / 6,132,565 | 500 closed weather events scanned; title/slug matching `temperature increase|how hot will` = only 1 (`september-2026-temperature-increase-c`). Tag coverage is incomplete; event counting uses public-search. |
| `https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv` | 200 | 1,198,225 | Header: “daily global mean near-surface (2m) air temperature data from ERA5 from 1940 to 2026 … anomalies relative to the 1991-2020 reference period”; “5-day delay (120 hours)” and “typically 3 days behind real-time”; last line `2026-10-17,15.303,14.409,0.894,PRELIMINARY`; `# Last updated: 19 Oct 2026`. 31,721 lines. |
| `https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json` | 200 | 63 | `{"daily":20261017,"monthly":202609,"annual":2025}` |
| `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | 200 | 17,039 | Header `GHCN-v4 1880-09/2026 + SST: ERSST v5 1880-09/2026`; 2026 row: `108 123 130 116 113 117 124 142 138 **** **** ****`. |
| `https://data.giss.nasa.gov/gistemp/updates_v4/` | 200 | 19,967 | “Graphs and tables are updated around the <a href="../release_dates.html">middle of every month</a> using the current data files provided by NOAA/NCEI (GHCN v4: meteorological stations, ERSST v5: ocean).” |
| `https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6` | 200 | 16,974 | 82 snapshot rows; first rows `20240104180327`, `20240215015543`, …; this is the first-release proxy source. |
| `https://archive.org/wayback/available?url=data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts%2BdSST.txt&timestamp=20200101` | 200 | — | `{"archived_snapshots":{"closest":{"status":"200","available":true,"url":"http://web.archive.org/web/20191230210128/...","timestamp":"20191230210128"}}}` |
| `https://web.archive.org/web/20200101000000id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | 200 | 16,198 | Snapshot body starts `GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius   base period: 1951-1980`. |
| `https://web.archive.org/web/20251112105542id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | 200 | 16,934 | 2025 row `137 125 136 123 107 105 101 114 **** **** **** ****` (Sep–Dec not yet in that snapshot). |
| `https://clob.polymarket.com/prices-history?market=9561250571098553460692263040980922664627749350602993898138030564733182354111&interval=max&fidelity=60` | 200 | 12,380 | 468 points; first `{t:1789884015,p:0.47}`, last `{t:1791561623,p:0.905}`. |
| `https://clob.polymarket.com/prices-history?market=31526494328582472005344062829052355933834544315779172775974673665982329881652&interval=max&fidelity=60` (january-2025 first token) | 200 | 15 | `{"history":[]}` |
| 191 YES-token URLs of the form `https://clob.polymarket.com/prices-history?market=<token>&interval=max&fidelity=60` | 200 (all; no ERR in script) | — | only 2 events non-empty (`september-2026`: 6/6 tokens; `october-2026`: 6/6); all other 31 events all tokens `history=[]`. Full per-event counts in section C. |

Failed / superseded attempts, recorded so they are not mistaken for success:

- `http://web.archive.org/web/20191230210128id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` — HTTP 000, TLS/connection error; `https://` works (above).
- `https://archive.ph/newest/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` — HTTP 000, `TLS connect error: ... unexpected eof while reading`.
- First unencoded Wayback CDX query — HTTP 000; re-issued with percent-encoded `url=...` (above) — HTTP 200.
- `https://data.giss.nasa.gov/gistemp/tabledata_v4/` — HTTP 200 but an empty HTML shell; no directory listing, so it was not used.
- A first concurrent `urllib` snapshot fetch had 14 transient `SSL: UNEXPECTED_EOF_WHILE_READING` errors; the final run used `curl --retry 3 --retry-all-errors` for all 45 snapshots (2023-01 onward) and parsed all 45. The final first-release script/output below is the authoritative one.

### B. Scripts and exact outputs

#### B1. `walkforward.py` (main walk-forward; output `walkforward.out`)

```python
#!/usr/bin/env python3
import csv, math, re, statistics as st
from datetime import date

# ---------- parse GISTEMP monthly table (current, revised values) ----------
g={}
for line in open('gistemp.txt', errors='ignore'):
    m=re.match(r'^\s*(\d{4})\s+(.*)$', line)
    if not m: continue
    yr=int(m.group(1)); toks=m.group(2).split()
    if len(toks)<12: continue
    for mo in range(1,13):
        v=toks[mo-1]
        if v.startswith('*'): continue
        try: g[(yr,mo)]=int(v)/100.0
        except ValueError: pass

# ---------- parse ERA5 daily CSV, monthly mean of ano_91-20 ----------
days={}; stat={}
with open('era5.csv', errors='ignore') as f:
    rows=(ln for ln in f if not ln.startswith('#'))
    rd=csv.DictReader(rows)
    for r in rd:
        try:
            y,mo,d=map(int,r['date'].split('-')); a=float(r['ano_91-20'])
        except Exception: continue
        days.setdefault((y,mo),[]).append(a)
        stat[(y,mo)]=r['status']
def ndays(y,m):
    return (date(y+(m==12), (m%12)+1, 1)-date(y,m,1)).days
era={k:sum(v)/len(v) for k,v in days.items() if len(v)>=28}
full={k for k,v in days.items() if len(v)==ndays(*k)}

def ols(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    b=sxy/sxx; a=my-b*mx
    resid=[y-(a+b*x) for x,y in zip(xs,ys)]
    sig=math.sqrt(sum(r*r for r in resid)/(n-2))
    return a,b,sig,resid

def ncdf(z): return 0.5*(1+math.erf(z/math.sqrt(2)))
def nll(p): return -math.log(max(p,1e-12))
def bracket_idx(x): return math.floor((x+0.005)/0.05)

targets=[]
y,m=2000,1
while (y,m)<=(2026,9):
    if (y,m) in g and (y,m) in full: targets.append((y,m))
    m+=1
    if m==13: y+=1; m=1
allmonths=sorted(k for k in g if k in full and k<=(2026,9))

def run(mode, win):
    out=[]; skipped=0
    for t in targets:
        prior=[]
        if mode=='rolling':
            yy,mm=t[0],t[1]; k=0
            while len(prior)<win and k<win*3:
                k+=1; mm-=1
                if mm==0: mm=12; yy-=1
                if (yy,mm) in g and (yy,mm) in full: prior.append((yy,mm))
                else: prior=[]; break
            prior=list(reversed(prior))
        else:  # expanding: all complete overlapping months before target
            prior=[p for p in allmonths if p<t]
        if mode=='rolling' and len(prior)<win: skipped+=1; continue
        if len(prior)<24: skipped+=1; continue
        xs=[era[p] for p in prior]; ys=[g[p] for p in prior]
        a,b,sig,_=ols(xs,ys)
        pred=a+b*era[t]; actual=g[t]
        # persistence point: last observed GISTEMP month before target
        yy,mm=t[0],t[1]-1
        if mm==0: mm=12; yy-=1
        while (yy,mm) not in g and (yy,mm)>=(1880,1):
            mm-=1
            if mm==0: mm=12; yy-=1
        pprev=g[(yy,mm)]
        pr=[]
        for p in prior:
            yy2,mm2=p[0],p[1]-1
            if mm2==0: mm2=12; yy2-=1
            if (yy2,mm2) in g: pr.append(g[p]-g[(yy2,mm2)])
        psig=st.stdev(pr) if len(pr)>2 else sig
        # common 8-outcome partition anchored at persistence point (ex ante):
        # 6 interior 0.05C bins from pprev-0.15 to pprev+0.15, plus 2 pooled tails
        edges=[pprev-0.15+i*0.05 for i in range(7)]
        def probs(mu,s):
            ps=[ncdf((edges[0]-mu)/s)]
            for i in range(6):
                ps.append(ncdf((edges[i+1]-mu)/s)-ncdf((edges[i]-mu)/s))
            ps.append(1-ncdf((edges[-1]-mu)/s))
            return ps
        pm=probs(pred,sig); pp=probs(pprev,psig); pu=[1/8]*8
        if actual<edges[0]: oi=0
        elif actual>=edges[-1]: oi=7
        else: oi=1+next(i for i in range(6) if edges[i]<=actual<edges[i+1])
        out.append(dict(t=t,a=a,b=b,sig=sig,pred=pred,actual=actual,pprev=pprev,psig=psig,
                        llm=nll(pm[oi]),llp=nll(pp[oi]),llu=nll(pu[oi]),
                        hit=int(bracket_idx(pred)==bracket_idx(actual)),
                        phit=int(bracket_idx(pprev)==bracket_idx(actual)),
                        pit=ncdf((actual-pred)/sig), z=(actual-pred)/sig, oi=oi,
                        pm=pm, edges=edges, era=era[t], status=stat[t]))
    return out,skipped

def block(lbl,out):
    n=len(out); pits=sorted(r['pit'] for r in out)
    ks=max(abs(pits[i]-(i+1)/n) for i in range(n))
    print(f' {lbl}: n={n} hit={sum(r["hit"] for r in out)}/{n}={sum(r["hit"] for r in out)/n:.4f} '
          f'persist_hit={sum(r["phit"] for r in out)}/{n}={sum(r["phit"] for r in out)/n:.4f} '
          f'LL_model={sum(r["llm"] for r in out)/n:.4f} LL_persist={sum(r["llp"] for r in out)/n:.4f} '
          f'LL_uniform={sum(r["llu"] for r in out)/n:.4f} '
          f'cov50={sum(abs(r["z"])<=0.67449 for r in out)/n:.4f} '
          f'cov80={sum(abs(r["z"])<=1.28155 for r in out)/n:.4f} '
          f'cov90={sum(abs(r["z"])<=1.64485 for r in out)/n:.4f} KS={ks:.4f}')

def summarize(name,out,skipped):
    print(f'=== {name}: n={len(out)}, skipped={skipped}, span={out[0]["t"]}..{out[-1]["t"]} ===')
    n=len(out); pits=sorted(r['pit'] for r in out)
    mean=sum(pits)/n; sd=math.sqrt(sum((x-mean)**2 for x in pits)/(n-1))
    ks=max(abs(pits[i]-(i+1)/n) for i in range(n))
    print(f' PIT: mean={mean:.4f} sd={sd:.4f} KS_vs_U(0,1)={ks:.4f}')
    dec=[0]*10
    for r in out: dec[min(9,int(r['pit']*10))]+=1
    print(' PIT deciles:',dec)
    for lbl,sel in [('ALL',out),('2000-2012',[r for r in out if r['t'][0]<=2012]),
                    ('2013-2026',[r for r in out if r['t'][0]>=2013]),
                    ('2020-2026',[r for r in out if r['t'][0]>=2020]),
                    ('2024-2026',[r for r in out if r['t']>=(2024,1)]),
                    ('2024-04..2026-09',[r for r in out if r['t']>=(2024,4)])]:
        if sel: block(lbl,sel)
    print(' tail outcomes (outside +/-0.15 of persistence):',sum(1 for r in out if r['oi'] in (0,7)))

out120,sk120=run('rolling',120)
outexp,ske=run('expanding',0)
out60,sk60=run('rolling',60)
summarize('MAIN rolling 120 months',out120,sk120)
summarize('ROBUSTNESS expanding (all prior from 1940)',outexp,ske)
summarize('ROBUSTNESS rolling 60 months',out60,sk60)

r=out120[-1]; mi=bracket_idx(r['pred'])
print('=== latest target',r['t'],'ERA5',round(r['era'],4),'pred',round(r['pred'],4),'actual',r['actual'],'sigma',round(r['sig'],4))
print(' latest OLS a,b,sigma',round(r['a'],6),round(r['b'],6),round(r['sig'],6))
for j in range(mi-2,mi+4):
    lo=j*0.05-0.005; hi=lo+0.05
    p=ncdf((hi-r['pred'])/r['sig'])-ncdf((lo-r['pred'])/r['sig'])
    print(f'  [{lo:.2f},{hi:.2f}) p={p:.4f} market-style label {lo+.005:.2f}-{hi-.005:.2f}')
```

Exact output (`python3 walkforward.py`):

```text
=== MAIN rolling 120 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5003 sd=0.2893 KS_vs_U(0,1)=0.0372
 PIT deciles: [31, 29, 41, 25, 40, 36, 33, 21, 23, 42]
 ALL: n=321 hit=123/321=0.3832 persist_hit=42/321=0.1308 LL_model=1.3638 LL_persist=2.0608 LL_uniform=2.0794 cov50=0.5016 cov80=0.7726 cov90=0.8816 KS=0.0372
 2000-2012: n=156 hit=73/156=0.4679 persist_hit=19/156=0.1218 LL_model=1.2976 LL_persist=2.0580 LL_uniform=2.0794 cov50=0.5705 cov80=0.8077 cov90=0.9231 KS=0.0913
 2013-2026: n=165 hit=50/165=0.3030 persist_hit=23/165=0.1394 LL_model=1.4264 LL_persist=2.0634 LL_uniform=2.0794 cov50=0.4364 cov80=0.7394 cov90=0.8424 KS=0.0882
 2020-2026: n=81 hit=25/81=0.3086 persist_hit=11/81=0.1358 LL_model=1.4649 LL_persist=2.0675 LL_uniform=2.0794 cov50=0.4815 cov80=0.7901 cov90=0.8642 KS=0.1026
 2024-2026: n=33 hit=12/33=0.3636 persist_hit=4/33=0.1212 LL_model=1.7819 LL_persist=2.0789 LL_uniform=2.0794 cov50=0.5455 cov80=0.7273 cov90=0.8485 KS=0.1592
 2024-04..2026-09: n=30 hit=11/30=0.3667 persist_hit=4/30=0.1333 LL_model=1.7697 LL_persist=2.0740 LL_uniform=2.0794 cov50=0.5667 cov80=0.7667 cov90=0.8667 KS=0.1380
 tail outcomes (outside +/-0.15 of persistence): 71
=== ROBUSTNESS expanding (all prior from 1940): n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.6061 sd=0.2068 KS_vs_U(0,1)=0.2279
 PIT deciles: [1, 7, 16, 33, 45, 51, 53, 50, 38, 27]
 ALL: n=321 hit=99/321=0.3084 persist_hit=42/321=0.1308 LL_model=1.5173 LL_persist=2.0618 LL_uniform=2.0794 cov50=0.6822 cov80=0.9128 cov90=0.9720 KS=0.2279
 2000-2012: n=156 hit=41/156=0.2628 persist_hit=19/156=0.1218 LL_model=1.5226 LL_persist=2.0609 LL_uniform=2.0794 cov50=0.6987 cov80=0.9231 cov90=0.9744 KS=0.2912
 2013-2026: n=165 hit=58/165=0.3515 persist_hit=23/165=0.1394 LL_model=1.5123 LL_persist=2.0626 LL_uniform=2.0794 cov50=0.6667 cov80=0.9030 cov90=0.9697 KS=0.1998
 2020-2026: n=81 hit=26/81=0.3210 persist_hit=11/81=0.1358 LL_model=1.5227 LL_persist=2.0666 LL_uniform=2.0794 cov50=0.6790 cov80=0.9012 cov90=0.9630 KS=0.1919
 2024-2026: n=33 hit=13/33=0.3939 persist_hit=4/33=0.1212 LL_model=1.7241 LL_persist=2.0791 LL_uniform=2.0794 cov50=0.6364 cov80=0.8485 cov90=0.9394 KS=0.2789
 2024-04..2026-09: n=30 hit=13/30=0.4333 persist_hit=4/30=0.1333 LL_model=1.7141 LL_persist=2.0736 LL_uniform=2.0794 cov50=0.6667 cov80=0.8667 cov90=0.9333 KS=0.2577
 tail outcomes (outside +/-0.15 of persistence): 71
=== ROBUSTNESS rolling 60 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5039 sd=0.2949 KS_vs_U(0,1)=0.0511
 PIT deciles: [36, 30, 28, 28, 41, 37, 30, 27, 15, 49]
 ALL: n=321 hit=125/321=0.3894 persist_hit=42/321=0.1308 LL_model=1.3669 LL_persist=2.0635 LL_uniform=2.0794 cov50=0.5171 cov80=0.7352 cov90=0.8598 KS=0.0511
 2000-2012: n=156 hit=74/156=0.4744 persist_hit=19/156=0.1218 LL_model=1.3014 LL_persist=2.0593 LL_uniform=2.0794 cov50=0.5769 cov80=0.7821 cov90=0.8910 KS=0.0565
 2013-2026: n=165 hit=51/165=0.3091 persist_hit=23/165=0.1394 LL_model=1.4289 LL_persist=2.0674 LL_uniform=2.0794 cov50=0.4606 cov80=0.6909 cov90=0.8303 KS=0.0744
 2020-2026: n=81 hit=24/81=0.2963 persist_hit=11/81=0.1358 LL_model=1.4674 LL_persist=2.0697 LL_uniform=2.0794 cov50=0.4815 cov80=0.6543 cov90=0.8272 KS=0.1126
 2024-2026: n=33 hit=13/33=0.3939 persist_hit=4/33=0.1212 LL_model=1.7956 LL_persist=2.0782 LL_uniform=2.0794 cov50=0.5455 cov80=0.6970 cov90=0.7879 KS=0.2041
 2024-04..2026-09: n=30 hit=13/30=0.4333 persist_hit=4/30=0.1333 LL_model=1.7546 LL_persist=2.0730 LL_uniform=2.0794 cov50=0.5667 cov80=0.7333 cov90=0.8333 KS=0.1798
 tail outcomes (outside +/-0.15 of persistence): 71
=== latest target (2026, 9) ERA5 0.8191 pred 1.3861 actual 1.38 sigma 0.0563
 latest OLS a,b,sigma 0.591262 0.970383 0.056299
  [1.25,1.30) p=0.0467 market-style label 1.25-1.29
  [1.30,1.35) p=0.1799 market-style label 1.30-1.34
  [1.35,1.40) p=0.3301 market-style label 1.35-1.39
  [1.40,1.45) p=0.2895 market-style label 1.40-1.44
  [1.45,1.50) p=0.1212 market-style label 1.45-1.49
  [1.50,1.55) p=0.0242 market-style label 1.50-1.54
```

#### B2. `pm_histcheck.py` (191 CLOB token checks; output `pm_histcheck.out`)

```python
import json,urllib.request,time
d=json.load(open('pm_search.json'))
rows=[]
for e in d['events']:
    toks=[]
    for m in e.get('markets',[]):
        try: toks.append(json.loads(m['clobTokenIds'])[0])
        except Exception: pass
    counts=[]
    for tok in toks:
        u=f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60'
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
            j=json.load(urllib.request.urlopen(req,timeout=30))
            h=j.get('history',[]); counts.append(len(h))
        except Exception as ex:
            counts.append('ERR')
        time.sleep(0.05)
    rows.append((e['slug'],e.get('closed'),counts))
for r in rows: print(r)
print('events with any nonempty:',sum(1 for _,_,c in rows if any(isinstance(x,int) and x>0 for x in c)))
```

Exact output:

```text
('september-2026-temperature-increase-c', True, [466, 468, 469, 466, 465, 466])
('october-2026-temperature-increase-c-20260928t160000000z', False, [454, 460, 454, 460, 460, 458])
('january-2025-temperature-increase-c', True, [0, 0, 0, 0, 0])
('february-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('march-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('november-2024-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('december-2024-temperature-increase-c', True, [0, 0, 0, 0, 0])
('september-2024-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('september-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('july-2025-temperature-increase-c-513', True, [0, 0, 0, 0, 0, 0])
('august-2024-temperature-increase-c', True, [0, 0, 0, 0, 0])
('january-2026-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('april-2025-temperature-increase-c4', True, [0, 0, 0, 0, 0, 0])
('november-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('october-2024-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('december-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('july-2025-temperature-increase-c-394', True, [0, 0, 0, 0, 0, 0])
('may-2024-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('march-2026-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('june-2025-temperature-increase-c-549', True, [0, 0, 0, 0, 0, 0])
('april-2026-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('may-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('how-hot-will-april-2024-be', True, [0, 0, 0, 0, 0])
('october-2025-temperature-increase-c-577', True, [0, 0, 0, 0, 0, 0])
('october-2025-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('february-2026-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('may-2026-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('june-2024-temperature-increase-c', True, [0, 0, 0, 0, 0])
('june-2026-temperature-increase-c', True, [0, 0, 0, 0, 0, 0])
('april-2025-temperature-increase-c-lower-ranges', True, [0, 0, 0, 0])
('july-2026-temperature-increase-c-20260608140824583', True, [0, 0, 0, 0, 0, 0])
('august-2026-temperature-increase-c-higher-strikes', True, [0, 0, 0, 0, 0, 0])
('august-2026-temperature-increase-c-20260728155540489', True, [0, 0, 0, 0, 0, 0])
events with any nonempty: 2
```

#### B3. `pm_count.py` (event count; output `pm_count.out`)

```python
import json,re
d=json.load(open('pm_search.json'))
ev=d['events']
pref=['january','february','march','april','may','june','july','august','september','october','november','december']
def monthkey(e):
    s=e['slug'].lower()
    m=re.match(r'(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{4})',s)
    if m: return (int(m.group(2)),pref.index(m.group(1))+1)
    if 'april-2024' in s: return (2024,4)
    return None
keys={}
for e in ev:
    k=monthkey(e)
    keys.setdefault(k,[]).append(e['slug'])
print('search events:',len(ev),'closed:',sum(bool(e.get('closed')) for e in ev),'open:',sum(not e.get('closed') for e in ev))
print('distinct calendar months:',len([k for k in keys if k]))
for k in sorted(keys, key=lambda x:(x is None,x or (0,0))):
    print(k,keys[k])
```

Exact output:

```text
search events: 33 closed: 32 open: 1
distinct calendar months: 29
(2024, 4) ['how-hot-will-april-2024-be']
(2024, 5) ['may-2024-temperature-increase-c']
(2024, 6) ['june-2024-temperature-increase-c']
(2024, 8) ['august-2024-temperature-increase-c']
(2024, 9) ['september-2024-temperature-increase-c']
(2024, 10) ['october-2024-temperature-increase-c']
(2024, 11) ['november-2024-temperature-increase-c']
(2024, 12) ['december-2024-temperature-increase-c']
(2025, 1) ['january-2025-temperature-increase-c']
(2025, 2) ['february-2025-temperature-increase-c']
(2025, 3) ['march-2025-temperature-increase-c']
(2025, 4) ['april-2025-temperature-increase-c4', 'april-2025-temperature-increase-c-lower-ranges']
(2025, 5) ['may-2025-temperature-increase-c']
(2025, 6) ['june-2025-temperature-increase-c-549']
(2025, 7) ['july-2025-temperature-increase-c-513', 'july-2025-temperature-increase-c-394']
(2025, 9) ['september-2025-temperature-increase-c']
(2025, 10) ['october-2025-temperature-increase-c-577', 'october-2025-temperature-increase-c']
(2025, 11) ['november-2025-temperature-increase-c']
(2025, 12) ['december-2025-temperature-increase-c']
(2026, 1) ['january-2026-temperature-increase-c']
(2026, 2) ['february-2026-temperature-increase-c']
(2026, 3) ['march-2026-temperature-increase-c']
(2026, 4) ['april-2026-temperature-increase-c']
(2026, 5) ['may-2026-temperature-increase-c']
(2026, 6) ['june-2026-temperature-increase-c']
(2026, 7) ['july-2026-temperature-increase-c-20260608140824583']
(2026, 8) ['august-2026-temperature-increase-c-higher-strikes', 'august-2026-temperature-increase-c-20260728155540489']
(2026, 9) ['september-2026-temperature-increase-c']
(2026, 10) ['october-2026-temperature-increase-c-20260928t160000000z']
```

#### B4. `pm_model_market.py` (n=1 model-vs-market on 2026-09; output `pm_model_market.out`)

```python
import json,urllib.request,time,math,re
from datetime import datetime,timezone
d=json.load(open('pm_search.json'))
e=next(x for x in d['events'] if x['slug']=='september-2026-temperature-increase-c')
rows=[]
for m in e['markets']:
    lab=m['groupItemTitle']
    tok=json.loads(m['clobTokenIds'])[0]
    u=f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60'
    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    h=json.load(urllib.request.urlopen(req,timeout=30)).get('history',[])
    rows.append((lab,h))
    time.sleep(0.05)
# model from walkforward output rerun import
import walkforward as W
r=W.out120[-1]
pred,sig=r['pred'],r['sig']
def ncdf(z): return 0.5*(1+math.erf(z/math.sqrt(2)))
def bounds(lab):
    lab=lab.replace('ºC','').strip()
    if lab.startswith('<'): return (-9,float(lab[1:])+0.005)
    if lab.startswith('>'): return (float(lab[1:])-0.005,9)
    a,b=re.split('[–-]',lab); return (float(a)-0.005,float(b)+0.005)
def ts(s): return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
for T in ['2026-10-05T00:00:00Z','2026-10-09T16:00:00Z']:
    t=ts(T); prices={}; last=[]
    for lab,h in rows:
        ph=[x for x in h if x['t']<=t]
        prices[lab]=ph[-1]['p'] if ph else None
        if ph: last.append(ph[-1]['t'])
    s=sum(prices.values())
    print('time',T,'sum raw',round(s,4),'last points',sorted(set(last)))
    actual=next(lab for lab,h in rows if lab.startswith('1.35'))
    for lab,h in rows:
        lo,hi=bounds(lab)
        pm=ncdf((hi-pred)/sig)-ncdf((lo-pred)/sig) if hi<9 else 1-ncdf((lo-pred)/sig)
        if lo<-8: pm=ncdf((hi-pred)/sig)
        print(f'  {lab}: model={pm:.4f} market_raw={prices[lab]:.4f} market_norm={prices[lab]/s:.4f}')
    lo,hi=bounds(actual); pm=ncdf((hi-pred)/sig)-ncdf((lo-pred)/sig)
    print(f'  actual {actual}: model_LL={-math.log(pm):.4f} market_LL={-math.log(prices[actual]/s):.4f}')
```

Exact output (the first block repeats the walk-forward summary because the script imports `walkforward`; the market comparison is at the end):

```text
=== MAIN rolling 120 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5003 sd=0.2893 KS_vs_U(0,1)=0.0372
 PIT deciles: [31, 29, 41, 25, 40, 36, 33, 21, 23, 42]
 ALL: n=321 hit=123/321=0.3832 persist_hit=42/321=0.1308 LL_model=1.3638 LL_persist=2.0608 LL_uniform=2.0794 cov50=0.5016 cov80=0.7726 cov90=0.8816 KS=0.0372
 2000-2012: n=156 hit=73/156=0.4679 persist_hit=19/156=0.1218 LL_model=1.2976 LL_persist=2.0580 LL_uniform=2.0794 cov50=0.5705 cov80=0.8077 cov90=0.9231 KS=0.0913
 2013-2026: n=165 hit=50/165=0.3030 persist_hit=23/165=0.1394 LL_model=1.4264 LL_persist=2.0634 LL_uniform=2.0794 cov50=0.4364 cov80=0.7394 cov90=0.8424 KS=0.0882
 2020-2026: n=81 hit=25/81=0.3086 persist_hit=11/81=0.1358 LL_model=1.4649 LL_persist=2.0675 LL_uniform=2.0794 cov50=0.4815 cov80=0.7901 cov90=0.8642 KS=0.1026
 2024-2026: n=33 hit=12/33=0.3636 persist_hit=4/33=0.1212 LL_model=1.7819 LL_persist=2.0789 LL_uniform=2.0794 cov50=0.5455 cov80=0.7273 cov90=0.8485 KS=0.1592
 2024-04..2026-09: n=30 hit=11/30=0.3667 persist_hit=4/30=0.1333 LL_model=1.7697 LL_persist=2.0740 LL_uniform=2.0794 cov50=0.5667 cov80=0.7667 cov90=0.8667 KS=0.1380
 tail outcomes (outside +/-0.15 of persistence): 71
=== ROBUSTNESS expanding (all prior from 1940): n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.6061 sd=0.2068 KS_vs_U(0,1)=0.2279
 PIT deciles: [1, 7, 16, 33, 45, 51, 53, 50, 38, 27]
 ALL: n=321 hit=99/321=0.3084 persist_hit=42/321=0.1308 LL_model=1.5173 LL_persist=2.0618 LL_uniform=2.0794 cov50=0.6822 cov80=0.9128 cov90=0.9720 KS=0.2279
 2000-2012: n=156 hit=41/156=0.2628 persist_hit=19/156=0.1218 LL_model=1.5226 LL_persist=2.0609 LL_uniform=2.0794 cov50=0.6987 cov80=0.9231 cov90=0.9744 KS=0.2912
 2013-2026: n=165 hit=58/165=0.3515 persist_hit=23/165=0.1394 LL_model=1.5123 LL_persist=2.0626 LL_uniform=2.0794 cov50=0.6667 cov80=0.9030 cov90=0.9697 KS=0.1998
 2020-2026: n=81 hit=26/81=0.3210 persist_hit=11/81=0.1358 LL_model=1.5227 LL_persist=2.0666 LL_uniform=2.0794 cov50=0.6790 cov80=0.9012 cov90=0.9630 KS=0.1919
 2024-2026: n=33 hit=13/33=0.3939 persist_hit=4/33=0.1212 LL_model=1.7241 LL_persist=2.0791 LL_uniform=2.0794 cov50=0.6364 cov80=0.8485 cov90=0.9394 KS=0.2789
 2024-04..2026-09: n=30 hit=13/30=0.4333 persist_hit=4/30=0.1333 LL_model=1.7141 LL_persist=2.0736 LL_uniform=2.0794 cov50=0.6667 cov80=0.8667 cov90=0.9333 KS=0.2577
 tail outcomes (outside +/-0.15 of persistence): 71
=== ROBUSTNESS rolling 60 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5039 sd=0.2949 KS_vs_U(0,1)=0.0511
 PIT deciles: [36, 30, 28, 28, 41, 37, 30, 27, 15, 49]
 ALL: n=321 hit=125/321=0.3894 persist_hit=42/321=0.1308 LL_model=1.3669 LL_persist=2.0635 LL_uniform=2.0794 cov50=0.5171 cov80=0.7352 cov90=0.8598 KS=0.0511
 2000-2012: n=156 hit=74/156=0.4744 persist_hit=19/156=0.1218 LL_model=1.3014 LL_persist=2.0593 LL_uniform=2.0794 cov50=0.5769 cov80=0.7821 cov90=0.8910 KS=0.0565
 2013-2026: n=165 hit=51/165=0.3091 persist_hit=23/165=0.1394 LL_model=1.4289 LL_persist=2.0674 LL_uniform=2.0794 cov50=0.4606 cov80=0.6909 cov90=0.8303 KS=0.0744
 2020-2026: n=81 hit=24/81=0.2963 persist_hit=11/81=0.1358 LL_model=1.4674 LL_persist=2.0697 LL_uniform=2.0794 cov50=0.4815 cov80=0.6543 cov90=0.8272 KS=0.1126
 2024-2026: n=33 hit=13/33=0.3939 persist_hit=4/33=0.1212 LL_model=1.7956 LL_persist=2.0782 LL_uniform=2.0794 cov50=0.5455 cov80=0.6970 cov90=0.7879 KS=0.2041
 2024-04..2026-09: n=30 hit=13/30=0.4333 persist_hit=4/30=0.1333 LL_model=1.7546 LL_persist=2.0730 LL_uniform=2.0794 cov50=0.5667 cov80=0.7333 cov90=0.8333 KS=0.1798
 tail outcomes (outside +/-0.15 of persistence): 71
=== latest target (2026, 9) ERA5 0.8191 pred 1.3861 actual 1.38 sigma 0.0563
 latest OLS a,b,sigma 0.591262 0.970383 0.056299
  [1.25,1.30) p=0.0467 market-style label 1.25-1.29
  [1.30,1.35) p=0.1799 market-style label 1.30-1.34
  [1.35,1.40) p=0.3301 market-style label 1.35-1.39
  [1.40,1.45) p=0.2895 market-style label 1.40-1.44
  [1.45,1.50) p=0.1212 market-style label 1.45-1.49
  [1.50,1.55) p=0.0242 market-style label 1.50-1.54
time 2026-10-05T00:00:00Z sum raw 0.923 last points [1791154819, 1791154823, 1791154824, 1791154825]
  <1.30ºC: model=0.0749 market_raw=0.1000 market_norm=0.1083
  1.30–1.34ºC: model=0.1799 market_raw=0.0700 market_norm=0.0758
  1.35–1.39ºC: model=0.3301 market_raw=0.6350 market_norm=0.6880
  1.40–1.44ºC: model=0.2895 market_raw=0.0800 market_norm=0.0867
  1.45–1.49ºC: model=0.1212 market_raw=0.0195 market_norm=0.0211
  >1.49ºC: model=0.0395 market_raw=0.0185 market_norm=0.0200
  actual 1.35–1.39ºC: model_LL=1.1083 market_LL=0.3740
time 2026-10-09T16:00:00Z sum raw 0.9075 last points [1791558033, 1791558046, 1791558052, 1791558056, 1791558057]
  <1.30ºC: model=0.0749 market_raw=0.0005 market_norm=0.0006
  1.30–1.34ºC: model=0.1799 market_raw=0.0005 market_norm=0.0006
  1.35–1.39ºC: model=0.3301 market_raw=0.9050 market_norm=0.9972
  1.40–1.44ºC: model=0.2895 market_raw=0.0005 market_norm=0.0006
  1.45–1.49ºC: model=0.1212 market_raw=0.0005 market_norm=0.0006
  >1.49ºC: model=0.0395 market_raw=0.0005 market_norm=0.0006
  actual 1.35–1.39ºC: model_LL=1.1083 market_LL=0.0028
```

#### B5. Wayback snapshot fetch and `firstrelease_local.py` (first-release proxy; output `firstrelease_local.out`)

Shell fetch (45 snapshots, 2023-01 onward):

```bash
mkdir -p wbsnaps
python3 - <<'PY'
import json
rows=[r for r in json.load(open('cdx_all.json'))[1:] if r[1]>='20230101']
open('wblist.txt','w').write('\n'.join(r[1] for r in rows))
PY
cat wblist.txt | xargs -P 6 -I{} sh -c 'curl -sS -L --retry 3 --retry-all-errors -A "Mozilla/5.0" --max-time 30 -o wbsnaps/{}.txt "https://web.archive.org/web/{}id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"'
```

`firstrelease_local.py`:

```python
#!/usr/bin/env python3
import json,re,math,glob,os
from datetime import date,timedelta

def parse_table(txt):
    g={}
    for line in txt.splitlines():
        m=re.match(r'^\s*(\d{4})\s+(.*)$',line)
        if not m: continue
        yr=int(m.group(1)); toks=m.group(2).split()
        if len(toks)<12: continue
        for mo in range(1,13):
            v=toks[mo-1]
            if v.startswith('*'): continue
            try: g[(yr,mo)]=int(v)/100.0
            except ValueError: pass
    return g

cur=parse_table(open('gistemp.txt',errors='ignore').read())
snaps=[]
for fn in sorted(glob.glob('wbsnaps/*.txt')):
    ts=os.path.basename(fn)[:14]
    snaps.append((ts,parse_table(open(fn,errors='ignore').read())))
print('snapshots parsed:',len(snaps),'span',snaps[0][0],snaps[-1][0])
first={}
for (y,m) in sorted(k for k in cur if k>=(2024,1) and k<=(2026,9)):
    end=date(y+(m==12),(m%12)+1,1)-timedelta(days=1)
    lo=(end+timedelta(days=14)).strftime('%Y%m%d')
    hi=(end+timedelta(days=55)).strftime('%Y%m%d')
    for ts,g in snaps:
        if lo<=ts[:8]<=hi and (y,m) in g:
            first[(y,m)]=(ts,g[(y,m)]); break
print('months with first-release proxy:',len(first),'/33')
for (y,m) in sorted(first):
    ts,v=first[(y,m)]
    print(f'{y}-{m:02d} snap {ts[:8]} first {v:+.2f} revised {cur[(y,m)]:+.2f} diff {cur[(y,m)]-v:+.2f}')
diffs=[cur[k]-v for k,(ts,v) in first.items()]; n=len(diffs); mean=sum(diffs)/n
print('SUMMARY n=',n,'mean_rev=',round(mean,4),'mean_abs=',round(sum(abs(x) for x in diffs)/n,4),'sd_rev=',round((sum((x-mean)**2 for x in diffs)/(n-1))**0.5,4),'max_abs=',round(max(abs(x) for x in diffs),4))
def bidx(x): return math.floor((x+0.005)/0.05)
same=sum(bidx(cur[k])==bidx(v) for k,(ts,v) in first.items())
print('bracket unchanged:',same,'/',n,'=',round(same/n,4))
print('exact same 0.01:',sum(abs(cur[k]-v)<0.0001 for k,(ts,v) in first.items()),'/',n)
import walkforward as W
sub=[r for r in W.out120 if r['t'] in first]
hf=sum(bidx(r['pred'])==bidx(first[r['t']][1]) for r in sub)
hr=sum(bidx(r['pred'])==bidx(r['actual']) for r in sub)
print('walkforward subset n=',len(sub),'hit_revised=',hr,'hit_first=',hf,'diff=',hf-hr)
for k,(ts,v) in sorted(first.items()):
    if bidx(cur[k])!=bidx(v):
        pred=next(r['pred'] for r in W.out120 if r['t']==k)
        print('  BRACKET CHANGE',k,'first',v,'revised',cur[k],'pred',round(pred,3),'bracket_first',bidx(v),'bracket_rev',bidx(cur[k]),'bracket_pred',bidx(pred))
```

Exact output (again includes the imported walk-forward summary; the first-release table and summary are at the bottom):

```text
snapshots parsed: 45 span 20230113003603 20261004120528
months with first-release proxy: 30 /33
2024-01 snap 20240215 first +1.21 revised +1.25 diff +0.04
2024-02 snap 20240411 first +1.44 revised +1.43 diff -0.01
2024-03 snap 20240511 first +1.39 revised +1.39 diff +0.00
2024-04 snap 20240609 first +1.32 revised +1.32 diff +0.00
2024-05 snap 20240707 first +1.14 revised +1.16 diff +0.02
2024-06 snap 20240809 first +1.25 revised +1.23 diff -0.02
2024-07 snap 20240905 first +1.21 revised +1.20 diff -0.01
2024-08 snap 20241007 first +1.30 revised +1.30 diff +0.00
2024-09 snap 20241114 first +1.23 revised +1.21 diff -0.02
2024-10 snap 20241114 first +1.32 revised +1.34 diff +0.02
2024-11 snap 20250103 first +1.31 revised +1.29 diff -0.02
2024-12 snap 20250205 first +1.26 revised +1.26 diff +0.00
2025-01 snap 20250305 first +1.36 revised +1.37 diff +0.01
2025-02 snap 20250401 first +1.26 revised +1.25 diff -0.01
2025-03 snap 20250501 first +1.36 revised +1.36 diff +0.00
2025-04 snap 20250606 first +1.23 revised +1.24 diff +0.01
2025-05 snap 20250709 first +1.07 revised +1.07 diff +0.00
2025-06 snap 20250803 first +1.03 revised +1.06 diff +0.03
2025-07 snap 20250905 first +1.03 revised +1.02 diff -0.01
2025-08 snap 20251023 first +1.14 revised +1.17 diff +0.03
2025-10 snap 20251212 first +1.19 revised +1.18 diff -0.01
2025-11 snap 20260105 first +1.22 revised +1.21 diff -0.01
2025-12 snap 20260203 first +1.05 revised +1.05 diff +0.00
2026-01 snap 20260325 first +1.08 revised +1.08 diff +0.00
2026-02 snap 20260325 first +1.24 revised +1.23 diff -0.01
2026-03 snap 20260420 first +1.28 revised +1.30 diff +0.02
2026-04 snap 20260623 first +1.17 revised +1.16 diff -0.01
2026-05 snap 20260623 first +1.12 revised +1.13 diff +0.01
2026-06 snap 20260802 first +1.18 revised +1.17 diff -0.01
2026-08 snap 20261004 first +1.40 revised +1.42 diff +0.02
SUMMARY n= 30 mean_rev= 0.002 mean_abs= 0.012 sd_rev= 0.0158 max_abs= 0.04
bracket unchanged: 23 / 30 = 0.7667
exact same 0.01: 8 / 30
=== MAIN rolling 120 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5003 sd=0.2893 KS_vs_U(0,1)=0.0372
 PIT deciles: [31, 29, 41, 25, 40, 36, 33, 21, 23, 42]
 ALL: n=321 hit=123/321=0.3832 persist_hit=42/321=0.1308 LL_model=1.3638 LL_persist=2.0608 LL_uniform=2.0794 cov50=0.5016 cov80=0.7726 cov90=0.8816 KS=0.0372
 2000-2012: n=156 hit=73/156=0.4679 persist_hit=19/156=0.1218 LL_model=1.2976 LL_persist=2.0580 LL_uniform=2.0794 cov50=0.5705 cov80=0.8077 cov90=0.9231 KS=0.0913
 2013-2026: n=165 hit=50/165=0.3030 persist_hit=23/165=0.1394 LL_model=1.4264 LL_persist=2.0634 LL_uniform=2.0794 cov50=0.4364 cov80=0.7394 cov90=0.8424 KS=0.0882
 2020-2026: n=81 hit=25/81=0.3086 persist_hit=11/81=0.1358 LL_model=1.4649 LL_persist=2.0675 LL_uniform=2.0794 cov50=0.4815 cov80=0.7901 cov90=0.8642 KS=0.1026
 2024-2026: n=33 hit=12/33=0.3636 persist_hit=4/33=0.1212 LL_model=1.7819 LL_persist=2.0789 LL_uniform=2.0794 cov50=0.5455 cov80=0.7273 cov90=0.8485 KS=0.1592
 2024-04..2026-09: n=30 hit=11/30=0.3667 persist_hit=4/30=0.1333 LL_model=1.7697 LL_persist=2.0740 LL_uniform=2.0794 cov50=0.5667 cov80=0.7667 cov90=0.8667 KS=0.1380
 tail outcomes (outside +/-0.15 of persistence): 71
=== ROBUSTNESS expanding (all prior from 1940): n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.6061 sd=0.2068 KS_vs_U(0,1)=0.2279
 PIT deciles: [1, 7, 16, 33, 45, 51, 53, 50, 38, 27]
 ALL: n=321 hit=99/321=0.3084 persist_hit=42/321=0.1308 LL_model=1.5173 LL_persist=2.0618 LL_uniform=2.0794 cov50=0.6822 cov80=0.9128 cov90=0.9720 KS=0.2279
 2000-2012: n=156 hit=41/156=0.2628 persist_hit=19/156=0.1218 LL_model=1.5226 LL_persist=2.0609 LL_uniform=2.0794 cov50=0.6987 cov80=0.9231 cov90=0.9744 KS=0.2912
 2013-2026: n=165 hit=58/165=0.3515 persist_hit=23/165=0.1394 LL_model=1.5123 LL_persist=2.0626 LL_uniform=2.0794 cov50=0.6667 cov80=0.9030 cov90=0.9697 KS=0.1998
 2020-2026: n=81 hit=26/81=0.3210 persist_hit=11/81=0.1358 LL_model=1.5227 LL_persist=2.0666 LL_uniform=2.0794 cov50=0.6790 cov80=0.9012 cov90=0.9630 KS=0.1919
 2024-2026: n=33 hit=13/33=0.3939 persist_hit=4/33=0.1212 LL_model=1.7241 LL_persist=2.0791 LL_uniform=2.0794 cov50=0.6364 cov80=0.8485 cov90=0.9394 KS=0.2789
 2024-04..2026-09: n=30 hit=13/30=0.4333 persist_hit=4/30=0.1333 LL_model=1.7141 LL_persist=2.0736 LL_uniform=2.0794 cov50=0.6667 cov80=0.8667 cov90=0.9333 KS=0.2577
 tail outcomes (outside +/-0.15 of persistence): 71
=== ROBUSTNESS rolling 60 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5039 sd=0.2949 KS_vs_U(0,1)=0.0511
 PIT deciles: [36, 30, 28, 28, 41, 37, 30, 27, 15, 49]
 ALL: n=321 hit=125/321=0.3894 persist_hit=42/321=0.1308 LL_model=1.3669 LL_persist=2.0635 LL_uniform=2.0794 cov50=0.5171 cov80=0.7352 cov90=0.8598 KS=0.0511
 2000-2012: n=156 hit=74/156=0.4744 persist_hit=19/156=0.1218 LL_model=1.3014 LL_persist=2.0593 LL_uniform=2.0794 cov50=0.5769 cov80=0.7821 cov90=0.8910 KS=0.0565
 2013-2026: n=165 hit=51/165=0.3091 persist_hit=23/165=0.1394 LL_model=1.4289 LL_persist=2.0674 LL_uniform=2.0794 cov50=0.4606 cov80=0.6909 cov90=0.8303 KS=0.0744
 2020-2026: n=81 hit=24/81=0.2963 persist_hit=11/81=0.1358 LL_model=1.4674 LL_persist=2.0697 LL_uniform=2.0794 cov50=0.4815 cov80=0.6543 cov90=0.8272 KS=0.1126
 2024-2026: n=33 hit=13/33=0.3939 persist_hit=4/33=0.1212 LL_model=1.7956 LL_persist=2.0782 LL_uniform=2.0794 cov50=0.5455 cov80=0.6970 cov90=0.7879 KS=0.2041
 2024-04..2026-09: n=30 hit=13/30=0.4333 persist_hit=4/30=0.1333 LL_model=1.7546 LL_persist=2.0730 LL_uniform=2.0794 cov50=0.5667 cov80=0.7333 cov90=0.8333 KS=0.1798
 tail outcomes (outside +/-0.15 of persistence): 71
=== latest target (2026, 9) ERA5 0.8191 pred 1.3861 actual 1.38 sigma 0.0563
 latest OLS a,b,sigma 0.591262 0.970383 0.056299
  [1.25,1.30) p=0.0467 market-style label 1.25-1.29
  [1.30,1.35) p=0.1799 market-style label 1.30-1.34
  [1.35,1.40) p=0.3301 market-style label 1.35-1.39
  [1.40,1.45) p=0.2895 market-style label 1.40-1.44
  [1.45,1.50) p=0.1212 market-style label 1.45-1.49
  [1.50,1.55) p=0.0242 market-style label 1.50-1.54
walkforward subset n= 30 hit_revised= 9 hit_first= 7 diff= -2
  BRACKET CHANGE (2024, 1) first 1.21 revised 1.25 pred 1.253 bracket_first 24 bracket_rev 25 bracket_pred 25
  BRACKET CHANGE (2024, 5) first 1.14 revised 1.16 pred 1.22 bracket_first 22 bracket_rev 23 bracket_pred 24
  BRACKET CHANGE (2024, 6) first 1.25 revised 1.23 pred 1.246 bracket_first 25 bracket_rev 24 bracket_pred 25
  BRACKET CHANGE (2024, 11) first 1.31 revised 1.29 pred 1.294 bracket_first 26 bracket_rev 25 bracket_pred 25
  BRACKET CHANGE (2025, 6) first 1.03 revised 1.06 pred 1.052 bracket_first 20 bracket_rev 21 bracket_pred 21
  BRACKET CHANGE (2025, 8) first 1.14 revised 1.17 pred 1.068 bracket_first 22 bracket_rev 23 bracket_pred 21
  BRACKET CHANGE (2026, 3) first 1.28 revised 1.3 pred 1.107 bracket_first 25 bracket_rev 26 bracket_pred 22
```

### C. What the numbers mean / sanity checks

- `walkforward.py` targets 321 months (2000-01..2026-09). Main parameters are estimated on the prior 120 complete months only; the target-month ERA5 value is the current monthly mean of daily `ano_91-20`. `sigma` is the OLS residual sample sd with denominator `n-2`. The model-anchored bracket table at the end uses boundaries at `k*0.05 - 0.005`, matching the market's “nearest 0.01” wording.
- The 8-outcome log-loss partition is anchored at the previous month's GISTEMP (known ex ante): 6 interior 0.05°C bins from `prev-0.15` to `prev+0.15`, plus lower/upper pooled tails. Both the model and persistence use their own Normal distributions; uniform is 1/8 (`ln 8 = 2.0794`). This is why the uniform baseline is `2.0794`, not `ln 6`.
- `firstrelease_local.py` uses a **proxy**: the earliest Wayback snapshot 14–55 days after month end that already contains the month. It is not NASA's official first-release archive. 30/33 months were covered; 2025-09, 2026-07, 2026-09 were not. The 7 bracket changes and the 7/30 vs 9/30 hit comparison are printed in the output above.
- CLOB history: `pm_histcheck.py` queried every market's first YES token for all 33 events (191 tokens total). `september-2026` is the only closed event with non-empty history. Therefore the pre-specified “≥5 closed events with prices” condition is false, and no statistical model-vs-market log loss is reported. The n=1 comparison is illustrative only.
- No price backtest / no trading: `backtest_count=0` for the market side. The walk-forward test is a forecast-calibration test, not a P&L test.

---

## glm-5.3 事实核查报告

# Fact-check report: R015.md (quant-015)

**Fetches (11):** All cited URLs re-fetched with the prescribed curl flags; every one returned HTTP 200 with matching content. CDX needed `--retry` (first attempt TLS 000 — same transient failure the worker's log itself recorded).

**Numbers/quotes — VERIFIED:**
- Gamma sept-2026: `closed=true`, `volume=11127.859859`, `openInterest=8452.463409`, `negRisk/restricted=true`, `startDate/endDate`, 6 bracket titles, `1.35–1.39` `["1","0"]` + all `umaResolutionStatus=resolved`, `feeSchedule={exponent:1, rate:0.05, takerOnly:true, rebateRate:0.25}` — exact match.
- All rule quotes present verbatim (mutually-exclusive sentence incl. "inclusive of both of its stated endpoints… nearest 0.01ºC", "later revised", Nov 1 11:59 PM ET lowest-bracket fallback, "column \"Sep\"", `GLB.Ts+dSST.txt`).
- GISTEMP 2026 row `108 123 130 116 113 117 124 142 138` (Aug=142, Sep=138), 17,039 bytes; aug-2026 `>1.29` resolved `["1","0"]`; "middle of every month" quote ✓.
- ERA5 CSV: 1,198,225 bytes, 31,721 lines, last line `2026-10-17,15.303,14.409,0.894,PRELIMINARY`, header quotes ✓; status JSON exact ✓.
- CDX: 82 rows, 16,974 bytes, 45 snapshots ≥20230101 ✓; CLOB token: 468 pts, first 2026-09-20 06:00Z p=0.47, last 2026-10-09 16:00Z p=0.905; price at 2026-10-05T00:00Z = 0.635 (→0.6880 norm.), 0.905 (→0.9972) at 10-09 ✓.
- public-search: 33 events / 32 closed / 1 open / 29 months / **191 YES tokens** ✓; volumes 4,925,571.47 / 2,415,315.78 / 2,522.64 / 15,901.87 / aug OI 6722.919473 ✓; weather tag page 0: only 1 matching slug ✓.
- **Script re-run:** saved `walkforward.py` from the log, ran against freshly downloaded data — output matches the entry **exactly** (LL 1.3638/2.0608/2.0794, hit 123/321=0.3832, PIT 0.5003/KS 0.0372, cov80 0.7726, 2024-26 LL 1.7819, both robustness variants, and latest-month a=0.591262/b=0.970383/σ=0.056299, pred=1.3861, bracket probs 0.3301/0.2895/…).

**Problems (all minor):**
1. Log A says CDX "first rows `20240104180327`, `20240215015543`" — actual CDX starts 20190721 (82 rows correct; timestamps present). Log-only ordering slip.
2. Byte counts time-varying: public-search 829,034→829,041; weather page 5,799,056→5,796,581. Worker dated fetches; acceptable.
3. No other mismatches; no fabricated numbers found.

**Guide compliance:** front-matter fields/values all valid; volumes/OI labelled 来源自报； fee formula `rate×p×(1−p)` and %-of-outlay figures (4.5%/3.35%/0.47%) arithmetic correct; 门槛自查 honest (admits gates 2/5/6 unmet, self-routes to 待选区， `backtest_count=0` explicit, walk-forward correctly framed as calibration not P&L); no keys/paid data/trading.

**Duplication:** R015 is a revision of the worker's own claimed quant-015 (CLAIMS.md B12); KNOWN.md has no weather/temp entries; dot-001/002 are city **daily max** temp on NOAA station data — different variable, resolution source, and horizon; quant-005/012 keyword-only. No duplicate.

VERDICT: KEEP — every checkable number, quote, and script output verifies against live sources, and the entry honestly discloses its unproven edge and 待选区 status. GATES_PASSING: 5/7
