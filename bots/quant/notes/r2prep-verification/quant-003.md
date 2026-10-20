# quant-003 第2轮准备：加强版核对日志（deepseek-flash）+ glm-5.3 事实核查

## VERIFICATION LOG (reviewer only, not for commit)

Working dir: `/workspace/agent-tools/quant-r2prep/work_R003` (R003). Repo `/workspace/trdproj-bots` read-only, never modified. Nothing under it was written. No keys, no trading, no payment; only public GETs. Date of all work: 2026-10-20 UTC. Time budget ~35 min.

### A. Files read in the repo (this session)

- `/workspace/trdproj-bots/GUIDE.md` — sections 2, 7, 8, 10, 11 read (plus 3–6, 9 for context). Key rules used: 7 gates, entry front-matter, 0.30%/side crypto cost, no fabrication, independent outcomes by event.
- `/workspace/trdproj-bots/templates/ENTRY.md` — read; front-matter fields preserved.
- `/workspace/trdproj-bots/bots/quant/entries/quant-003-three-coin-breadth-gate.md` — read; copied to `quant-003-orig.md`; same `id`/`date`, status kept `草稿`.
- `/workspace/trdproj-bots/bots/quant/notes/xqt-migration/reproduce.py` — read in full (the original 3-coin/4-fold script).
- `/workspace/trdproj-bots/bots/quant/notes/xqt-migration/results.csv` — read; original numbers M2_PAA_breadth 0.0030: compound +202.9%, CAGR 33.97%, path_dd −19.07%, mean_sharpe 1.376, folds [77.9, 30.1, 13.7, 15.1]; ETH_tsmom30 0.0030: +184.5%, 31.78%, −45.29%, 0.814, [35.1, 1.6, 93.2, 7.3].

### B. URLs spot-checked this session with `curl -sL -A "Mozilla/5.0" --max-time 30`, HTTP result + snippet

The 10-symbol bulk download was done by `build_universe.py` / `prefetch.py` below (Python urllib, same public URLs, no keys). The curl checks below verify the endpoints and the data end date.

1. `https://data.binance.vision/?prefix=data/spot/monthly/klines/ETHUSDT/1d/` → HTTP 200, 2712 bytes. Snippet: `<!DOCTYPE html><html><head><title>Binance Data Collection</title>` … `Market Data`.
2. `https://data.binance.vision/?prefix=data/spot/monthly/klines/GRTUSDT/1d/` → HTTP 200, 2712 bytes. Same page title `Binance Data Collection` (the HTML page is JS-driven; actual files were fetched directly).
3. `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/` → HTTP 200, 83664 bytes. Snippet: `<?xml version="1.0" encoding="UTF-8"?><ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>data.binance.vision</Name><Prefix>data/spot/monthly/klines/</Prefix>…<NextMarker>data/spot/monthly/klines/DGBUSDT/</NextMarker><MaxKeys>1000</MaxKeys>`.
4. `https://data.binance.vision/data/spot/monthly/klines/GRTUSDT/1d/GRTUSDT-1d-2020-12.zip` → HTTP 200, 1061 bytes.
5. `https://data.binance.vision/data/spot/monthly/klines/XLMUSDT/1d/XLMUSDT-1d-2020-12.zip` → HTTP 200, 1987 bytes.
6. `https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-09.zip` → HTTP 200, 2112 bytes. Last 3 CSV rows: `1790553600000000,84472.01,84999.00,82563.00,83500.01,…,792415046.49894150,0` / `1790640000000000,83500.01,84563.99,82775.94,83663.66,…` / `1790726400000000,83663.66,85649.95,82956.11,83623.60,…`.
7. `https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-19.zip` → HTTP 200, 238 bytes.
8. `https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-20.zip` → HTTP 404, 350 bytes (file not yet published; sample ends 2026-10-19).
9. `https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-18.zip` → HTTP 200, 237 bytes (checked while locating the data end).
10. `https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-17.zip` → HTTP 200, 238 bytes; `…-2026-10-13.zip` → HTTP 200, 237 bytes (sanity checks against the original script's end date).

No `api.binance.com` call was made (it returns 451); only `data.binance.vision`, as instructed. No source-reported performance numbers are used in the entry; all performance numbers are self-computed from the downloaded public klines.

### C. Pre-specification (written before any new-universe result was computed)

Full text of `PRESPEC_R003.md` (timestamped `Tue Oct 20 04:52:52 UTC 2026`, before `build_universe.py` was run):

```markdown
# R003 pre-specification (written BEFORE any result was computed)

Written 2026-10-20 (UTC), before downloading any kline beyond the three cached files
(BTC/ETH/SOL). No backtest output for the new universe had been seen at the time of writing.

## Fixed universe rule (ex ante, never re-ranked after 2020-12)
Candidate set: all Binance **spot USDT** pairs present in data.binance.vision monthly klines
with a `2020-12` file (i.e. listed on or before 2020-12), excluding stablecoin bases
{USDC, BUSD, TUSD, USDT, DAI, PAX, UST, SUSD, FDUSD, EUR} and excluding leveraged tokens
(names ending UP/DOWN/BULL/BEAR). Rank candidates by **total quote volume in 2020-12**
(sum of daily quote volume from the 2020-12 monthly 1d klines). Take the top 10. The universe
is frozen; no survivorship-based re-selection in later years (delisted/gapped coins stay in,
and if a coin stops trading it simply drops out of the panel from its last date).

## Strategy variants (all pre-specified)
Momentum lookback L=60 calendar days: mom = close_t / close_{t-60} - 1.
Breadth count B_t = number of the N (<=10) coins with mom > 0 on day t.
Gate: if B_t >= k, hold equal weight in the coins with mom > 0; else hold cash.
Portfolio vol target = 30% annualised from 60d realised vol of the basket, cap 1x, no leverage.
Rebalance every 5 trading days, weights lag-1 (decided on close t-1, earn day t).
Cost 0.30% per side on |delta weight|.
k grid: k = 1..N. k=1 is the control ("hold all positive-momentum coins", i.e. no breadth gate).
Headline gate: majority k = floor(N/2)+1 (6 if N=10). No parameter search; all k reported.

## Baselines
B1: plain per-coin time-series momentum, 30d lookback, long when close/close_30-1>0, same
    5-day rebalance and 30% vol target, equal weight across the same universe (isolates
    the breadth gate; this is the "plain T-T2-tsmom basket").
B2: plain per-coin tsmom 60d basket (matches gate lookback), same construction.
B3: ETH-only tsmom 30d (the baseline used in the original draft).
B4: equal-weight buy-and-hold, same 5-day rebalance (no vol target).
Per-coin tsmom 30d is also reported individually for every coin in the universe.

## Walk-forward folds (yearly, OOS, fixed rules, 250-day warm-up before each fold)
2021, 2022, 2023, 2024, 2025, 2026 (2026-01-01 to last available day).
No parameter is fitted inside a fold; only trailing data is used for vol targeting.

## Pre-declared decision rule
The breadth gate is judged to BEAT plain tsmom out of sample only if the headline majority
gate (k=6) has (a) higher mean per-fold Sharpe than B1 in at least 4 of 6 folds, (b) lower
full-path max drawdown than B1, and (c) compound return not more than 10 percentage points
below B1. Otherwise -> ABANDON (recommend abandoning the breadth-gate claim), while still
reporting all k variants honestly.

## Metrics
Per fold: net return, annualised Sharpe, max drawdown, mean gross exposure.
Full path: compounded return, CAGR, path max drawdown, worst fold, folds positive.
```

### D. Universe construction script and exact output

`build_universe.py` (full):

```python
#!/usr/bin/env python3
"""List Binance spot USDT monthly-kline symbols, keep those with a 2020-12 file,
rank by 2020-12 total quote volume, take top 10 (pre-specified rule)."""
import io, zipfile, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
BASE = "https://data.binance.vision/data/spot/monthly/klines"
STABLE = {"USDC","BUSD","TUSD","USDT","DAI","PAX","UST","SUSD","FDUSD","EUR"}

def list_prefix(prefix):
    keys, marker = [], ""
    while True:
        q = urllib.parse.urlencode({"delimiter": "/", "prefix": prefix, "marker": marker})
        with urllib.request.urlopen(f"{S3}?{q}", timeout=60) as r:
            root = ET.fromstring(r.read())
        ns = {"s3": root.tag.split("}")[0].strip("{")}
        keys += [cp.text for cp in root.findall("s3:CommonPrefixes/s3:Prefix", ns)]
        if root.findtext("s3:IsTruncated", "false", ns) != "true":
            break
        marker = root.findtext("s3:NextMarker", "", ns)
    return keys

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()

prefixes = list_prefix("data/spot/monthly/klines/")
syms = []
for p in prefixes:
    s = p.rstrip("/").split("/")[-1]
    if s.endswith("USDT"):
        base = s[:-4]
        if base in STABLE or base.endswith(("UP","DOWN","BULL","BEAR")):
            continue
        syms.append(s)
print("USDT spot symbols on data.binance.vision (after exclusions):", len(syms))

def dec(s):
    u = f"{BASE}/{s}/1d/{s}-1d-2020-12.zip"
    try:
        z = zipfile.ZipFile(io.BytesIO(get(u)))
    except Exception:
        return None
    df = pd.read_csv(z.open(z.namelist()[0]), header=None)
    return {"symbol": s, "base": s[:-4], "days": len(df),
            "dec2020_quote_vol": float(df[7].astype(float).sum())}

with ThreadPoolExecutor(max_workers=32) as ex:
    rows = [r for r in ex.map(dec, syms) if r]
u = pd.DataFrame(rows).sort_values("dec2020_quote_vol", ascending=False)
print("with 2020-12 file:", len(u))
print(u.head(20).to_string(index=False))
top = u.head(10)
print("\nTOP10 (frozen universe):", ", ".join(top.symbol))
top.to_csv("universe_top10.csv", index=False)
```

Exact stdout (`python3 build_universe.py`, 18.9 s):

```text
USDT spot symbols on data.binance.vision (after exclusions): 696
with 2020-12 file: 182
   symbol  base  days  dec2020_quote_vol
  BTCUSDT   BTC    31       5.574865e+10
  ETHUSDT   ETH    31       1.911940e+10
  XRPUSDT   XRP    31       1.621421e+10
  LTCUSDT   LTC    31       6.957457e+09
  GRTUSDT   GRT    15       4.785324e+09
  BCHUSDT   BCH    31       3.013389e+09
 LINKUSDT  LINK    31       2.793631e+09
  BNBUSDT   BNB    31       2.652010e+09
  ADAUSDT   ADA    31       2.580882e+09
  XLMUSDT   XLM    31       1.846158e+09
  DOTUSDT   DOT    31       1.834213e+09
  YFIUSDT   YFI    31       1.727264e+09
  EOSUSDT   EOS    31       1.608873e+09
  ZILUSDT   ZIL    31       1.266867e+09
SUSHIUSDT SUSHI    31       1.181077e+09
  TRXUSDT   TRX    31       1.087515e+09
  UNIUSDT   UNI    31       8.900502e+08
  VETUSDT   VET    31       8.503954e+08
THETAUSDT THETA    31       7.587577e+08
 AAVEUSDT  AAVE    31       7.451638e+08

TOP10 (frozen universe): BTCUSDT, ETHUSDT, XRPUSDT, LTCUSDT, GRTUSDT, BCHUSDT, LINKUSDT, BNBUSDT, ADAUSDT, XLMUSDT
```

`universe_top10.csv` (exact):

```csv
symbol,base,days,dec2020_quote_vol
BTCUSDT,BTC,31,55748654003.597725
ETHUSDT,ETH,31,19119402122.69965
XRPUSDT,XRP,31,16214213587.29052
LTCUSDT,LTC,31,6957456546.267643
GRTUSDT,GRT,15,4785323630.282074
BCHUSDT,BCH,31,3013388964.0919003
LINKUSDT,LINK,31,2793631117.263482
BNBUSDT,BNB,31,2652009559.3901796
ADAUSDT,ADA,31,2580882228.387686
XLMUSDT,XLM,31,1846158265.8724208
```

### E. Data prefetch script and exact output

`prefetch.py` (full):

```python
#!/usr/bin/env python3
"""Parallel-prefetch daily klines for the fixed top-10 universe into _data/*.csv."""
import io, zipfile, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent; DATA = HERE/"_data"; DATA.mkdir(exist_ok=True)
START, END = "2020-12-17", "2026-10-19"
SYMS = ["BTCUSDT","ETHUSDT","XRPUSDT","LTCUSDT","GRTUSDT","BCHUSDT","LINKUSDT","BNBUSDT","ADAUSDT","XLMUSDT"]
BASE = "https://data.binance.vision/data/spot"
def get(u):
    with urllib.request.urlopen(u, timeout=60) as r: return r.read()
def build(sym):
    cache = DATA/f"{sym}_1d.csv"
    if cache.exists(): return sym, "cached"
    months = pd.period_range("2020-12","2026-09",freq="M")
    urls = [f"{BASE}/monthly/klines/{sym}/1d/{sym}-1d-{m}.zip" for m in months]
    urls += [f"{BASE}/daily/klines/{sym}/1d/{sym}-1d-{d.date()}.zip"
             for d in pd.date_range("2026-10-01", END)]
    def fetch(u):
        z = zipfile.ZipFile(io.BytesIO(get(u)))
        return pd.read_csv(z.open(z.namelist()[0]), header=None).iloc[:, :8]
    with ThreadPoolExecutor(max_workers=16) as ex:
        frames = list(ex.map(fetch, urls))
    raw = pd.concat(frames)
    t = raw[0].astype("int64"); t = np.where(t > 10**14, t//1000, t)
    df = pd.DataFrame({"open":raw[1].values,"high":raw[2].values,"low":raw[3].values,
                       "close":raw[4].values,"volume":raw[5].values,
                       "quote_volume":raw[7].values},
                      index=pd.to_datetime(t, unit="ms")).sort_index()
    df = df[~df.index.duplicated()].loc[START:END].astype(float)
    df.to_csv(cache); return sym, f"{len(df)} rows {df.index[0].date()}..{df.index[-1].date()}"
with ThreadPoolExecutor(max_workers=10) as ex:
    for sym, msg in ex.map(build, SYMS): print(sym, msg)
```

Exact stdout (first run downloaded the missing XLM cache; the rest were already cached from the timed-out sequential loader, which had downloaded 9/10):

```text
BTCUSDT cached
ETHUSDT cached
XRPUSDT cached
LTCUSDT cached
GRTUSDT cached
BCHUSDT cached
LINKUSDT cached
BNBUSDT cached
ADAUSDT cached
XLMUSDT 2133 rows 2020-12-17..2026-10-19
```

(Note: an earlier sequential version of the loader hit the 300 s/600 s tool timeout after caching 9 symbols; `prefetch.py` was then used with a 16-way thread pool. The cached CSVs are the same data. The exact data range is 2020-12-17..2026-10-19, 2133 rows per symbol.)

### F. Backtest script and exact output

`run_backtest.py` (full):

```python
#!/usr/bin/env python3
"""R003: breadth-gated 60d momentum on a frozen ex-ante top-10 USDT universe.
Data: data.binance.vision spot daily klines (free, keyless). Costs 0.30%/side.
Rules frozen in PRESPEC_R003.md before this was run."""
import io, zipfile, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "_data"; DATA.mkdir(exist_ok=True)
START, END = "2020-12-17", "2026-10-19"
TOP10 = ["BTCUSDT","ETHUSDT","XRPUSDT","LTCUSDT","GRTUSDT","BCHUSDT","LINKUSDT","BNBUSDT","ADAUSDT","XLMUSDT"]
FEE = 0.003
REBAL, LOOK = 5, 250
FOLDS = [("2021-01-01","2021-12-31"),("2022-01-01","2022-12-31"),
         ("2023-01-01","2023-12-31"),("2024-01-01","2024-12-31"),
         ("2025-01-01","2025-12-31"),("2026-01-01",END)]
BASE = "https://data.binance.vision/data/spot"

def _get(u):
    with urllib.request.urlopen(u, timeout=60) as r: return r.read()

def one(urls):
    frames = []
    for u in urls:
        z = zipfile.ZipFile(io.BytesIO(_get(u)))
        frames.append(pd.read_csv(z.open(z.namelist()[0]), header=None).iloc[:, :8])
    raw = pd.concat(frames)
    t = raw[0].astype("int64"); t = np.where(t > 10**14, t // 1000, t)
    df = pd.DataFrame({"open":raw[1].values,"high":raw[2].values,"low":raw[3].values,
                       "close":raw[4].values,"volume":raw[5].values,
                       "quote_volume":raw[7].values},
                      index=pd.to_datetime(t, unit="ms")).sort_index()
    return df[~df.index.duplicated()].loc[START:END].astype(float)

def load(sym):
    cache = DATA / f"{sym}_1d.csv"
    if cache.exists(): return pd.read_csv(cache, index_col=0, parse_dates=True)
    months = pd.period_range("2020-12","2026-09",freq="M")
    urls = [f"{BASE}/monthly/klines/{sym}/1d/{sym}-1d-{m}.zip" for m in months]
    urls += [f"{BASE}/daily/klines/{sym}/1d/{sym}-1d-{d.date()}.zip"
             for d in pd.date_range("2026-10-01", END)]
    df = one(urls); df.to_csv(cache); return df

def freeze(w): return w.reindex(w.index[::REBAL]).reindex(w.index, method="ffill")

def apply(w, px):
    r = px.pct_change().fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    return (w*r).sum(axis=1) - turn*FEE

def mom_w(px, lb, k, vt=True):
    mom = px/px.shift(lb) - 1.0
    pos = (mom > 0).astype(float)
    sel = pos.mul((pos.sum(axis=1) >= k).astype(float), axis=0)
    w0 = sel.div(sel.sum(axis=1).replace(0,np.nan), axis=0).fillna(0.0)
    if vt:
        vols = px.pct_change().rolling(60).std()*np.sqrt(365)
        avg = (w0*vols).sum(axis=1)/w0.sum(axis=1).replace(0,np.nan)
        w0 = w0.mul((0.30/avg.replace(0,np.nan)).clip(0,1), axis=0)
    return freeze(w0).shift(1).fillna(0.0)

def tsmom1(c, lb):
    pos = (c/c.shift(lb)-1 > 0).astype(float).shift(1).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    return pos*c.pct_change().fillna(0.0) - turn*FEE, pos

def met(te, w):
    eq = (1+te).cumprod()
    return {"ret_pct": (eq.iloc[-1]-1)*100,
            "sharpe": te.mean()/te.std()*np.sqrt(365) if te.std()>0 else np.nan,
            "mdd_pct": (eq/eq.cummax()-1).min()*100,
            "expo": w.loc[te.index].sum(axis=1).mean()}

panels = {s: load(s) for s in TOP10}
for s in TOP10:
    print(s, panels[s].index[0].date(), panels[s].index[-1].date(), len(panels[s]))
px = pd.DataFrame({s: panels[s]["close"] for s in TOP10}).dropna()
print("common panel:", px.index[0].date(), px.index[-1].date(), len(px))

strat = {}
for k in range(1, 11):
    strat[f"GATE_k{k}"] = mom_w(px, 60, k)
strat["B1_tsmom30_basket"] = mom_w(px, 30, 1)
strat["B2_tsmom60_basket"] = mom_w(px, 60, 1)
ew = pd.DataFrame(1/len(TOP10), index=px.index, columns=px.columns)
strat["B4_EW_hold"] = freeze(ew).shift(1).fillna(0.0)
coin_net = {}
for s in TOP10:
    coin_net[s], _ = tsmom1(panels[s]["close"].reindex(px.index).dropna(), 30)
    coin_net[s] = coin_net[s].reindex(px.index).fillna(0.0)

rows = []
for name, w in strat.items():
    net = apply(w, px)
    full = met(net, w)
    rec = {"name": name, "full_ret_pct": full["ret_pct"],
           "cagr_pct": ((1+full["ret_pct"]/100)**(365/len(net))-1)*100,
           "path_mdd_pct": full["mdd_pct"], "sharpe": full["sharpe"],
           "expo": full["expo"]}
    for i,(a,b) in enumerate(FOLDS, 1):
        m = met(net.loc[a:b], w)
        rec[f"f{i}_ret"] = m["ret_pct"]; rec[f"f{i}_sh"] = m["sharpe"]; rec[f"f{i}_dd"] = m["mdd_pct"]
    rows.append(rec)
res = pd.DataFrame(rows)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 50)
print("\n=== portfolio variants ===")
print(res.round(2).to_string(index=False))
res.to_csv("results_gate.csv", index=False, float_format="%.4f")

# per-coin plain tsmom 30d
rows2 = []
for s in TOP10:
    net = coin_net[s]; w = pd.DataFrame({"pos": (net!=0).astype(float)})
    rec = {"coin": s, "full_ret_pct": (1+net).prod()*100-100,
           "cagr_pct": ((1+net).prod()**(365/len(net))-1)*100,
           "path_mdd_pct": ((1+net).cumprod()/(1+net).cumprod().cummax()-1).min()*100,
           "sharpe": net.mean()/net.std()*np.sqrt(365) if net.std()>0 else np.nan}
    for i,(a,b) in enumerate(FOLDS,1):
        te = net.loc[a:b]; eq=(1+te).cumprod()
        rec[f"f{i}_ret"] = (eq.iloc[-1]-1)*100
        rec[f"f{i}_sh"] = te.mean()/te.std()*np.sqrt(365) if te.std()>0 else np.nan
    rows2.append(rec)
res2 = pd.DataFrame(rows2)
print("\n=== per-coin plain tsmom30 (long/flat, no vol target, 0.30%/side) ===")
print(res2.round(2).to_string(index=False))
res2.to_csv("results_percoin.csv", index=False, float_format="%.4f")

# count independent "risk-off" segments for GATE_k6 (breadth < 6) and k2 on 3-coin
def segments(mask):
    m = mask.astype(int).values; n=0; prev=0
    for v in m:
        if v==1 and prev==0: n+=1
        prev=v
    return n
mom = px/px.shift(60)-1; pos=(mom>0)
for k in (6,):
    off = (pos.sum(axis=1) < k)
    print(f"\nGATE_k{k}: risk-off days={int(off.sum())}, risk-off segments={segments(off)}, total days={len(off)}")
```

Exact stdout (`python3 run_backtest.py`, 0.30%/side):

```text
BTCUSDT 2020-12-17 2026-10-19 2133
ETHUSDT 2020-12-17 2026-10-19 2133
XRPUSDT 2020-12-17 2026-10-19 2133
LTCUSDT 2020-12-17 2026-10-19 2133
GRTUSDT 2020-12-17 2026-10-19 2133
BCHUSDT 2020-12-17 2026-10-19 2133
LINKUSDT 2020-12-17 2026-10-19 2133
BNBUSDT 2020-12-17 2026-10-19 2133
ADAUSDT 2020-12-17 2026-10-19 2133
XLMUSDT 2020-12-17 2026-10-19 2133
common panel: 2020-12-17 2026-10-19 2133

=== portfolio variants ===
             name  full_ret_pct  cagr_pct  path_mdd_pct  sharpe  expo  f1_ret  f1_sh  f1_dd  f2_ret  f2_sh  f2_dd  f3_ret  f3_sh  f3_dd  f4_ret  f4_sh  f4_dd  f5_ret  f5_sh  f5_dd  f6_ret  f6_sh  f6_dd
          GATE_k1         33.56      5.08        -42.03    0.33  0.32    5.84   0.36 -14.68  -29.98  -1.53 -34.42   60.32   2.00 -12.03   43.37   1.48 -20.49  -11.61  -0.40 -20.77  -11.30  -0.51 -30.94
          GATE_k2         39.97      5.92        -41.82    0.37  0.27   10.07   0.54 -14.33  -32.75  -1.86 -35.40   56.84   1.98  -9.70   27.02   1.11 -27.89    2.09   0.20 -14.24   -7.03  -0.30 -25.06
          GATE_k3         66.11      9.07        -39.28    0.52  0.23   10.64   0.58 -12.09  -29.55  -1.75 -34.56   53.25   1.93  -9.70   32.85   1.37 -24.58    0.86   0.14 -17.22    3.79   0.33 -13.98
          GATE_k4         69.91      9.50        -29.55    0.55  0.21   10.64   0.58 -12.09  -18.27  -1.21 -24.08   36.00   1.47  -9.70   37.92   1.60 -19.98   -2.30  -0.04 -16.28    2.55   0.25 -15.01
          GATE_k5         69.13      9.41        -29.55    0.55  0.20    9.55   0.53 -12.09  -18.27  -1.21 -24.08   34.02   1.42  -9.70   46.18   1.90 -15.19   -5.10  -0.20 -16.28    1.61   0.20 -15.78
          GATE_k6         99.35     12.53        -31.83    0.72  0.18   -0.09   0.10 -18.47  -13.90  -0.92 -20.02   25.64   1.16 -11.51   49.35   2.02 -13.35    3.57   0.31 -11.32   19.25   1.32  -6.08
          GATE_k7         86.16     11.22        -25.85    0.71  0.14    0.53   0.12 -18.59  -10.31  -1.26 -13.55   29.79   1.33  -9.70   35.49   1.69 -10.73    1.07   0.15 -13.07   16.16   1.14  -6.08
          GATE_k8         53.59      7.62        -26.37    0.56  0.12    0.53   0.12 -18.59   -9.21  -1.27 -12.07   27.05   1.45  -9.70   28.25   1.47  -8.89    1.20   0.15 -12.96    2.05   0.27  -8.21
          GATE_k9         40.21      5.95        -23.46    0.49  0.10   11.79   0.79 -14.51   -9.45  -1.87 -10.59   15.70   0.96 -10.23   26.82   1.54  -8.57   -3.85  -0.23 -13.43   -1.82  -0.17 -10.65
         GATE_k10         -4.49     -0.78        -31.13   -0.01  0.07    5.39   0.46 -12.12   -9.45  -1.87 -10.59  -11.06  -0.75 -16.16   32.98   1.91  -7.18   -9.01  -0.89 -13.77   -7.00  -1.09 -10.27
B1_tsmom30_basket         94.91     12.10        -35.86    0.59  0.32   14.27   0.70 -13.42  -18.14  -0.68 -25.38   61.17   1.99 -14.43   29.91   1.17 -23.82    3.43   0.26 -20.60   -3.79  -0.10 -24.73
B2_tsmom60_basket         33.56      5.08        -42.03    0.33  0.32    5.84   0.36 -14.68  -29.98  -1.53 -34.42   60.32   2.00 -12.03   43.37   1.48 -20.49  -11.61  -0.40 -20.77  -11.30  -0.51 -30.94
       B4_EW_hold        277.42     25.52        -82.56    0.68  1.00  275.95   1.78 -62.59  -69.35  -1.13 -71.08  128.18   1.83 -28.09  104.75   1.45 -42.12  -24.85  -0.09 -47.75  -19.32  -0.22 -50.64

=== per-coin plain tsmom30 (long/flat, no vol target, 0.30%/side) ===
    coin  full_ret_pct  cagr_pct  path_mdd_pct  sharpe  f1_ret  f1_sh  f2_ret  f2_sh  f3_ret  f3_sh  f4_ret  f4_sh  f5_ret  f5_sh  f6_ret  f6_sh
 BTCUSDT        125.62     14.94        -50.03    0.56   44.80   0.99  -43.28  -1.75  153.75   2.64   28.59   0.80   -7.62  -0.20   -8.87  -0.26
 ETHUSDT        416.45     32.44        -50.37    0.79  167.29   1.60  -27.93  -0.37   34.51   0.94    2.04   0.27   93.19   1.63    1.11   0.24
 XRPUSDT         28.52      4.39        -79.07    0.40  206.09   1.46  -21.86  -0.29  -41.32  -1.00  209.09   1.85  -40.74  -0.84  -50.00  -1.99
 LTCUSDT        -90.60    -33.27        -95.78   -0.37    1.53   0.49  -45.35  -1.00  -51.00  -1.44  -11.80   0.14  -54.24  -1.15  -14.31  -0.36
 GRTUSDT         50.43      7.24        -85.09    0.45   91.30   1.09  -35.42  -0.71  163.76   1.42   30.94   0.72  -51.68  -1.40  -27.04  -0.36
 BCHUSDT        -48.01    -10.59        -85.53    0.18   71.79   1.03  -47.57  -1.07   85.47   1.26  -13.87   0.23  -23.11  -0.25  -53.00  -2.43
LINKUSDT        -71.20    -19.18        -93.96    0.03   36.93   0.84  -84.67  -3.04   62.17   1.06   19.84   0.59  -10.61   0.06  -21.03  -0.39
 BNBUSDT       1712.41     64.18        -60.06    1.06 1195.11   2.53  -31.19  -0.77    0.82   0.20   64.95   1.24   24.61   0.75   -1.85   0.07
 ADAUSDT         32.55      4.94        -89.34    0.40  456.86   2.09  -50.65  -1.50  128.92   1.75    8.23   0.44  -65.18  -1.78  -44.09  -1.29
 XLMUSDT        -25.33     -4.88        -82.69    0.27   65.10   1.01  -47.77  -1.70   11.65   0.45  195.61   1.51  -24.73  -0.29  -65.14  -1.95

GATE_k6: risk-off days=1193, risk-off segments=75, total days=2133
```

### G. Post-hoc diagnostics script and exact output

`diagnostics.py` (full; explicitly exploratory, NOT in the pre-spec — used only to separate breadth from lookback):

```python
#!/usr/bin/env python3
"""POST-HOC diagnostics (NOT in the pre-spec; labelled exploratory):
- breadth gate with 30d lookback (to separate breadth from lookback vs B1)
- per-fold Sharpe/return comparison table
- daily return difference t-stat for GATE_k6 vs B1_tsmom30_basket
Reuses cached _data/*.csv; same rules/costs as run_backtest.py."""
import pathlib, numpy as np, pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
TOP10 = ["BTCUSDT","ETHUSDT","XRPUSDT","LTCUSDT","GRTUSDT","BCHUSDT","LINKUSDT","BNBUSDT","ADAUSDT","XLMUSDT"]
FEE=0.003; REBAL=5
FOLDS=[("2021-01-01","2021-12-31"),("2022-01-01","2022-12-31"),("2023-01-01","2023-12-31"),
       ("2024-01-01","2024-12-31"),("2025-01-01","2025-12-31"),("2026-01-01","2026-10-19")]
px=pd.DataFrame({s:pd.read_csv(HERE/"_data"/f"{s}_1d.csv",index_col=0,parse_dates=True)["close"] for s in TOP10}).dropna()
def freeze(w): return w.reindex(w.index[::REBAL]).reindex(w.index,method="ffill")
def apply(w,px):
    r=px.pct_change().fillna(0.0); turn=w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    return (w*r).sum(axis=1)-turn*FEE
def mom_w(px,lb,k):
    mom=px/px.shift(lb)-1; pos=(mom>0).astype(float)
    sel=pos.mul((pos.sum(axis=1)>=k).astype(float),axis=0)
    w0=sel.div(sel.sum(axis=1).replace(0,np.nan),axis=0).fillna(0.0)
    vols=px.pct_change().rolling(60).std()*np.sqrt(365)
    avg=(w0*vols).sum(axis=1)/w0.sum(axis=1).replace(0,np.nan)
    w0=w0.mul((0.30/avg.replace(0,np.nan)).clip(0,1),axis=0)
    return freeze(w0).shift(1).fillna(0.0)
W={"GATE_k6_L60":mom_w(px,60,6),"GATE_k6_L30_POSTHOC":mom_w(px,30,6),
   "GATE_k1_L60":mom_w(px,60,1),"B1_tsmom30":mom_w(px,30,1),"GATE_k4_L60":mom_w(px,60,4),"GATE_k7_L60":mom_w(px,60,7)}
N={k:apply(w,px) for k,w in W.items()}
print("=== post-hoc: breadth gate with 30d lookback vs B1 (same lookback) ===")
for row in ["GATE_k6_L30_POSTHOC","B1_tsmom30"]:
    n=N[row]; eq=(1+n).cumprod()
    print(f"{row:24s} full={eq.iloc[-1]-1:+.2%} cagr={eq.iloc[-1]**(365/len(n))-1:+.2%} "
          f"mdd={(eq/eq.cummax()-1).min():.2%} sharpe={n.mean()/n.std()*np.sqrt(365):.2f}")
print("\nper-fold Sharpe (post-hoc table):")
hdr="fold      "+"".join(f"{k:>22s}" for k in W)
print(hdr)
for i,(a,b) in enumerate(FOLDS,1):
    line=f"f{i} {a[:4]}  "
    for k in W:
        te=N[k].loc[a:b]; line+=f"{te.mean()/te.std()*np.sqrt(365):>22.2f}"
    print(line)
print("\nper-fold return %:")
print(hdr)
for i,(a,b) in enumerate(FOLDS,1):
    line=f"f{i} {a[:4]}  "
    for k in W:
        te=N[k].loc[a:b]; line+=f"{((1+te).prod()-1)*100:>22.1f}"
    print(line)
d=N["GATE_k6_L60"]-N["B1_tsmom30"]
d=d.loc["2021-01-01":]
t=d.mean()/(d.std()/np.sqrt(len(d)))
print(f"\nGATE_k6 - B1 daily return: mean={d.mean()*365:+.2%}/yr, ann.vol={d.std()*np.sqrt(365):.2%}, t={t:.2f}, n={len(d)}")
print("corr(GATE_k6,B1) daily =", round(N["GATE_k6_L60"].corr(N["B1_tsmom30"]),3))
# fold-level win counts pre-declared criterion
wins=sum(N["GATE_k6_L60"].loc[a:b].mean()/N["GATE_k6_L60"].loc[a:b].std()
         > N["B1_tsmom30"].loc[a:b].mean()/N["B1_tsmom30"].loc[a:b].std() for a,b in FOLDS)
print("fold Sharpe wins GATE_k6 vs B1:", wins, "/6")
```

Exact stdout (`python3 diagnostics.py`):

```text
=== post-hoc: breadth gate with 30d lookback vs B1 (same lookback) ===
GATE_k6_L30_POSTHOC      full=+89.16% cagr=+11.52% mdd=-32.08% sharpe=0.71
B1_tsmom30               full=+94.91% cagr=+12.10% mdd=-35.86% sharpe=0.59

per-fold Sharpe (post-hoc table):
fold                 GATE_k6_L60   GATE_k6_L30_POSTHOC           GATE_k1_L60            B1_tsmom30           GATE_k4_L60           GATE_k7_L60
f1 2021                    0.10                  1.97                  0.36                  0.70                  0.58                  0.12
f2 2022                   -0.92                 -1.76                 -1.53                 -0.68                 -1.21                 -1.26
f3 2023                    1.16                  1.66                  2.00                  1.99                  1.47                  1.33
f4 2024                    2.02                  1.62                  1.48                  1.17                  1.60                  1.69
f5 2025                    0.31                  0.74                 -0.40                  0.26                 -0.04                  0.15
f6 2026                    1.32                 -0.99                 -0.51                 -0.10                  0.25                  1.14

per-fold return %:
fold                 GATE_k6_L60   GATE_k6_L30_POSTHOC           GATE_k1_L60            B1_tsmom30           GATE_k4_L60           GATE_k7_L60
f1 2021                    -0.1                  37.8                   5.8                  14.3                  10.6                   0.5
f2 2022                   -13.9                 -25.8                 -30.0                 -18.1                 -18.3                 -10.3
f3 2023                    25.6                  35.3                  60.3                  61.2                  36.0                  29.8
f4 2024                    49.4                  39.3                  43.4                  29.9                  37.9                  35.5
f5 2025                     3.6                  11.0                 -11.6                   3.4                  -2.3                   1.1
f6 2026                    19.2                 -11.6                 -11.3                  -3.8                   2.5                  16.2

GATE_k6 - B1 daily return: mean=-0.81%/yr, ann.vol=16.33%, t=-0.12, n=2118
corr(GATE_k6,B1) daily = 0.743
fold Sharpe wins GATE_k6 vs B1: 3 /6
```

### H. Fold table extraction (exact)

`python3 - <<'PY'` reading `results_gate.csv` and printing the table used in the entry:

```text
             name  full_ret_pct  cagr_pct  path_mdd_pct  sharpe  expo  f1_ret  f1_sh  f2_ret  f2_sh  f3_ret  f3_sh  f4_ret  f4_sh  f5_ret  f5_sh  f6_ret  f6_sh
          GATE_k1         33.56      5.08        -42.03    0.33  0.32    5.84   0.36  -29.98  -1.53   60.32   2.00   43.37   1.48  -11.61  -0.40  -11.30  -0.51
          GATE_k2         39.97      5.92        -41.82    0.37  0.27   10.07   0.54  -32.75  -1.86   56.84   1.98   27.02   1.11    2.09   0.20   -7.03  -0.30
          GATE_k3         66.11      9.07        -39.28    0.52  0.23   10.64   0.58  -29.55  -1.75   53.24   1.93   32.85   1.37    0.86   0.14    3.79   0.33
          GATE_k4         69.91      9.49        -29.55    0.55  0.21   10.64   0.58  -18.27  -1.21   36.00   1.47   37.92   1.60   -2.30  -0.04    2.55   0.25
          GATE_k5         69.13      9.41        -29.55    0.55  0.20    9.55   0.53  -18.27  -1.21   34.02   1.42   46.18   1.90   -5.10  -0.20    1.61   0.20
          GATE_k6         99.35     12.53        -31.83    0.72  0.18   -0.09   0.10  -13.90  -0.92   25.64   1.16   49.35   2.02    3.57   0.31   19.25   1.32
          GATE_k7         86.16     11.22        -25.85    0.71  0.14    0.53   0.12  -10.31  -1.26   29.79   1.33   35.49   1.69    1.07   0.15   16.16   1.14
          GATE_k8         53.59      7.62        -26.37    0.56  0.12    0.53   0.12   -9.21  -1.27   27.05   1.45   28.25   1.47    1.20   0.15    2.05   0.27
          GATE_k9         40.21      5.95        -23.46    0.49  0.10   11.79   0.79   -9.45  -1.87   15.70   0.96   26.82   1.54   -3.85  -0.23   -1.82  -0.17
         GATE_k10         -4.49     -0.78        -31.13   -0.01  0.07    5.39   0.46   -9.45  -1.87  -11.06  -0.75   32.98   1.91   -9.01  -0.89   -7.00  -1.09
B1_tsmom30_basket         94.91     12.10        -35.86    0.59  0.32   14.27   0.70  -18.14  -0.68   61.17   1.99   29.91   1.17    3.43   0.26   -3.79  -0.10
B2_tsmom60_basket         33.56      5.08        -42.03    0.33  0.32    5.84   0.36  -29.98  -1.53   60.32   2.00   43.37   1.48  -11.61  -0.40  -11.30  -0.51
       B4_EW_hold        277.42     25.52        -82.56    0.68  1.00  275.95   1.78  -69.35  -1.13  128.18   1.83  104.75   1.45  -24.85  -0.09  -19.32  -0.22
```

### I. Checks / honesty notes

- Pre-spec was written before the universe ranking and before any 10-coin backtest. The k grid (1..10), the headline k=6, the 60-day lookback, the 30% vol target, the 5-day rebalance, 0.30%/side, the six yearly folds, and the three-part decision rule were all fixed in `PRESPEC_R003.md`.
- Ambiguity disclosed: the pre-spec wording for criterion (a) was “higher mean per-fold Sharpe than B1 in at least 4 of 6 folds”. The intended reading was the fold-count reading (≥4/6 folds); under that reading k=6 fails 3/6. Under the alternative “mean of the 6 fold Sharpes” reading it passes (0.663 vs 0.558). Both numbers and both readings are reported in the entry; the recommendation of ABANDON does not rely on hiding the looser reading.
- All variants tried are reported: k=1..10, B1 (30d), B2 (60d = k=1), B4 (EW hold), per-coin 30d tsmom for all 10 coins, plus one clearly-labelled post-hoc 30d gate. No variant was dropped.
- The headline result fails the pre-declared criterion (a): k=6 per-fold Sharpe beats B1 in only 3/6 folds (2024, 2025, 2026). Criteria (b) and (c) pass, but (a) is necessary, so the pre-declared verdict is “does not beat plain tsmom out of sample” → recommendation ABANDON.
- The post-hoc 30d gate also wins only 3/6 folds and has lower full-period return than B1 (+89.2% vs +94.9%), reinforcing that the 60d gate’s advantage is mostly lower exposure/DD, not a robust breadth edge.
- 2021 fold is penalised by the data start: the common 10-coin panel begins 2020-12-17 (GRT listing), so the 60d signal is not fully warmed up until ~Feb 2021. This affects k=6 and k=1/B2 equally; B1 (30d) warms up sooner, which is one reason 2021 favours B1. This is disclosed, not corrected after the fact.
- The universe rule is “listed by 2020-12, ranked by 2020-12 quote volume, top 10”. It is not “top 10 by listing date” in the sense of oldest listings; the ranking variable is explicitly 2020-12 total quote volume. The rule and the resulting list are stated in the entry so a reviewer can reproduce or reject the definition.
- No number in the entry is presented as source-reported. The only external factual claims are data availability/URLs (verified above). The original draft's 3-coin numbers are labelled as the repo's own prior self-computed results and are not re-used as new evidence.
- Data files are not committed; they live in `_data/` in the working dir (10 CSVs, ~1.3 MB total), with download URLs in the scripts. No file exceeds 1 MB.

---

## glm-5.3 事实核查报告

**Fact-check report — R003 (quant-003, breadth-gated 10-coin momentum)**

**URL re-fetch (all live, 2026-10-20 UTC):**
- data.binance.vision GRT/ETH listing pages → 200, 2712 B, title "Binance Data Collection" ✓
- S3 XML klines listing → 200; I independently paginated: 757 USDT pairs, **696 after the stated exclusions — VERIFIED** (matches log/entry)
- GRTUSDT-1d-2020-12.zip → 200, 1061 B, **15 rows, first ts 2020-12-17 — VERIFIED** ("15 天" ✓)
- XLMUSDT 2020-12 → 200, 1987 B ✓; BTCUSDT 2026-09 → last 3 closes **83500.01 / 83663.66 / 83623.60 — VERIFIED** exactly
- BTCUSDT 2026-10-19 daily → 200, 238 B ✓; **2026-10-20 → 404 ✓** (sample legitimately ends 10-19)
- Critical tight margin re-checked live: 2020-12 quote volume XLM 1,846,158,266 > DOT 1,834,212,752 → top-10 cutoff VERIFIED

**Numbers (entry vs my re-run):** I copied `run_backtest.py` + `diagnostics.py` from the log into rev_R003 and re-ran both (exit 0, using cached `_data`, last row 2026-10-19). Output matches the entry **exactly**: GATE k=6 +99.35%/12.53%/−31.83%/0.72/expo 0.18; per-fold Sharpe 0.10/−0.92/1.16/2.02/0.31/1.32 (3/6 wins vs B1); B1 +94.91%/12.10%/−35.86%/0.59; full k-grid (k=1..10) identical; B4 +277.4%/−82.6%; per-coin table identical (e.g. BNB +1712.4%/1.06); risk-off 1193 days / **75 segments** / 2133 days; t=−0.12, n=2118, corr 0.743, −0.81%/yr; 30d post-hoc gate +89.16%/−32.08%/0.71, 3/6. Original 3-coin figures (+202.9%/34.0%/−19.1%; ETH +184.5%/−45.3%) match `results.csv` (M2_PAA_breadth 0.0030: 202.8956/33.9746/−19.0681; ETH_tsmom30: 184.5161/−45.2934) ✓. PRESPEC mtime 04:52:52 UTC confirmed, precedes backtest artifacts.

**Rule compliance:** front-matter complete, all values legal; `kind: supplement`, `improves: T-T2-tsmom` correct (variant, not new mechanism); all performance numbers explicitly self-computed, no 来源自报 used; no keys/paid data/trading; 门槛自查 honest (declares ABANDON, discloses 3/6 and the looser mean-reading 0.663 vs 0.558); no unrun backtests claimed. Not duplicative: own quant-003 update (CLAIMS M2), distinct from dot-021/quant-001.

**Problems (minor):**
1. Filename slug stale: existing file `quant-003-three-coin-breadth-gate.md` but content is now 10-coin ("十币广度闸门时序动量"). Fix: keep id quant-003 but rename slug (e.g. `quant-003-breadth-gate-10coin.md`) or note the rename in LOG.md.
2. Log item B.8 says 404 body "350 bytes"; live refetch gives 330 bytes. Log-only nit, no entry number affected.
3. `name_zh` "十币广度闸门时序动量" is 10 chars — fine; no action.

No fabricated or mismatched facts found; all checkable numbers reproduce bit-for-bit.

VERDICT: KEEP — every cited URL, price, count and self-computed statistic re-verified live and by re-running the logged scripts, with honest negative conclusions disclosed.
GATES_PASSING: 6/7 (1,2,3,6,7 clear; 4 passes only as a declared supplement/variant; 5: literal 8% bar passes at 12.5% CAGR but the pre-registered superiority test failed, which the entry itself flags)
