# quant-014 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

所有抓取都在 2026-10-20 用 `curl -sL --max-time 30` 或 `urllib`（UA `Mozilla/5.0`），全部为公开 GET，无密钥、无登录、未付费。

| # | URL | 结果 | 取用的内容 |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/public-search?q=S%26P%20500&limit_per_type=10&events_status=all` | HTTP 200，257,518 B | 确认 finance 板块有 SPX 模板（`bitcoin-vs-gold-vs-sp-500-in-2026` 的规则原文里 S&P 结算源是 Yahoo `^SPX`） |
| 2 | `https://gamma-api.polymarket.com/public-search?q=SPX&limit_per_type=20&events_status=all` | HTTP 200，358,131 B | 模板清单与 slug；`spx-up-or-down-on-october-20-2026` closed=False vol 9536.468243；`spx-hit-dec-2026` vol 425,924.998727 |
| 3 | `https://gamma-api.polymarket.com/events?slug=spx-up-or-down-on-october-20-2026` | HTTP 200，9,356 B | 规则全文（WSJ 源、相等 50-50、四舍五入到分、无官方收盘时的兜底）；`endDate=2026-10-20T20:00:00Z`；`outcomePrices=["0.625","0.375"]`；bid 0.62 / ask 0.63；`feeSchedule={"exponent":1,"rate":0.04,"takerOnly":true,"rebateRate":0.25}`；`umaBond='250'`、`umaReward='0.6'`、`rewardsMinSize=100`、`orderPriceMinTickSize=0.01`、`orderMinSize=5`；`series.id=10383`、`slug=spx-daily-up-or-down`、`restricted=true`、`volume24hr=165331.75444` |
| 4 | `https://gamma-api.polymarket.com/events?slug=spx-close-dec-2026` | HTTP 200，26,265 B | 6 档 `groupItemTitle` 与 `outcomePrices`/bid/ask（见正文表）；「falls exactly between two brackets → higher range bracket」；Yahoo `^GSPC` 结算源；`volume=48152.545224999994` |
| 5 | `https://gamma-api.polymarket.com/events?series_id=10383&limit=100&closed=true&order=endDate&ascending=false` | HTTP 200，882,011 B | 返回 100 个已关闭 event（limit 打满）；月份计数 `2026-05:3, 06:21, 07:21, 08:21, 09:21, 10:13`；`volume` 合计 10,779,504.351358；单 event：10-19 164,019.449316、10-16 43,470.214666、10-15 37,722.581945、10-13 68,932.028859 |
| 6 | `https://gamma-api.polymarket.com/public-search?q=NVDA&limit_per_type=10&events_status=active` | HTTP 200，514,152 B | `what-price-will-nvda-hit-in-october-2026` vol 94,705.683728；`nvda-up-or-down-on-october-20-2026` vol 140.165956；`nvda-above-in-october-2026` vol 714.92525 |
| 7 | `https://gamma-api.polymarket.com/events?slug=nvda-close-above-on-october-20-2026` | HTTP 200，26,796 B | 5 档 $210/$215/$220/$225/$230；「Closing prices will be used exactly as published by Pyth, without rounding」；相等判 No；`feeSchedule.rate=0.04`；`volume=1224.392` |
| 8 | `https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=5y&interval=1d` | HTTP 200，128,733 B | 1,254 根日线，first 2021-10-20 4536.19，last 2026-10-19 7690.73；`meta.timezone=EDT`、`gmtoffset=-14400`、`regularMarketPrice=7690.73` |
| 9 | `https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=1y&interval=1d` | HTTP 200，26,492 B | 先确认接口可用（本条数字用 #8 的 5y 版） |
| 10 | `https://stooq.com/q/d/l/?s=^spx&i=d`（加 `-A "Mozilla/5.0"` 再试一次） | **失败**：两次都返回 JS 挑战页（`This site requires JavaScript to verify your browser`），3 行 HTML，无 CSV | 未使用，正文已写明 |
| 11 | `https://clob.polymarket.com/prices-history?market=65910031205497258743984808565459409789230065676431430659652385723065905489576&interval=max&fidelity=60`（10-20 活市场 YES） | HTTP 200，466 B | `{"history":[{"t":1792414822,"p":0.53},...]}`，日内从 0.51 到 0.59+ 漂移 |
| 12 | `...prices-history?market=37867517699597038332707589432698261528449111760519164430714310172860137405315...`（2026-10-16 已关闭 YES） | HTTP 200（urllib 直连该主机时曾返回 **403 Forbidden**，改用 curl + UA 后 200） | 已关闭市场**有**历史价格 → 21 个 event 的 `p6` 由此而来 |
| 13 | `...prices-history?market=<2026-09-18/17/16/15 event YES token>...`（4 次抽样） | HTTP 200，内容 `{"history":[]}` | 更早的已关闭市场无价格历史；100 个里只有 21 个可用 |

**我自己的算术（正文所有非引用的数字都在这里）**

- σ：`stdev(log returns[-n:]) * sqrt(252)`，n=20/60/252 → 0.0904 / 0.1100 / 0.1271；样本 1,253 个收益。
- 上涨日占比 `sum(r>0)/len(r)` = 664/1253 = 0.5299；最近 100 根 = 47/100。
- t 值 = `mean(r)/(stdev(r)/sqrt(1253))` = 1.40。
- 剩余交易日 n=51：从 2026-10-19 到 2026-12-31 逐日数，`weekday()<5` 且不在 {2026-11-26, 2026-12-25}；T=51/252=0.2024。
- 档位概率 = `Φ(d2(lo)) − Φ(d2(hi))`，`d2(K)=(ln(S/K) − 0.5σ²T)/(σ√T)`，S=7690.73，μ=0。
- 隐含 σ：在 [0.30,1.20] 上对 `p_above(8000,σ)` 二分 80 次使 `P=0.40`，结果顶在上界 1.20（说明 mid 0.40 不可用）。
- bid 之和 0.812、ask 之和 1.601、mid(`outcomePrices`) 之和 1.2065（逐档相加）。
- 吃单费 `0.04×0.625×0.375=0.009375`；`0.04×0.39×0.61=0.009516`；半价差 `(0.63−0.62)/2=0.005`、`(0.39−0.14)/2=0.125`；合计 `0.0144`（=2.30% of 0.625）与 `0.134516`（=34.5% of 0.39）。
- 模型缺口：`0.5636 − 0.39 = 0.1736`；`0.1736 − 0.009516 − 0.125 = 0.0391` ≈ 4.0¢/份。
- 校准：`p6` = `endDate − 6h` 之前最后一条 60 分钟价；Brier `mean((p−y)²)`；log loss `−mean(y·ln p + (1−y)·ln(1−p))`；吃单子集 `|p6−0.5| ≥ 0.10`，按 `p6` 侧付 `p6` 或 `1−p6`，赢则收 1.000，得每份毛损益。
- 21 个 event 的 `p6` 逐条存于 `spx_calib_rows.json`（可复算）。

**脚本 1：`spx_lognormal.py`（全文）**

```python
#!/usr/bin/env python3
# Reproducible check for B11: lognormal pricing of Polymarket SPX markets
# Inputs, both keyless public:
#   https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=5y&interval=1d  (daily closes)
#   https://gamma-api.polymarket.com/events?slug=spx-close-dec-2026              (bracket bids/asks/outcomePrices)
# Run: python3 spx_lognormal.py
import json, math, statistics, datetime as dt

# ---------- 1. realized vol and up-day base rate from Yahoo daily closes ----------
raw = json.load(open("yahoo_spx5y.json"))["chart"]["result"][0]
ts = raw["timestamp"]
cl = raw["indicators"]["quote"][0]["close"]
rows = [(dt.datetime.utcfromtimestamp(t).date(), c) for t, c in zip(ts, cl) if c]
rows.sort()
dates = [r[0] for r in rows]
closes = [r[1] for r in rows]
print("bars=%d  first=%s %.2f  last=%s %.2f" % (len(closes), dates[0], closes[0], dates[-1], closes[-1]))

lr = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
ann = math.sqrt(252)


def rv(n):
    w = lr[-n:]
    return statistics.stdev(w) * ann


print("realized vol 20d = %.4f (%d obs, %s..%s)" % (rv(20), 20, dates[-20], dates[-1]))
print("realized vol 60d = %.4f" % rv(60))
print("realized vol 252d = %.4f" % rv(252))

up = sum(1 for x in lr if x > 0)
print("up-day share, full sample: %d/%d = %.4f" % (up, len(lr), up / len(lr)))
u100 = sum(1 for x in lr[-100:] if x > 0)
print("up-day share, last 100 bars: %d/100 = %.4f" % (u100, u100 / 100))

# ---------- 2. lognormal bracket probabilities for spx-close-dec-2026 ----------
S = closes[-1]
# trading days left: count NYSE weekdays + skip the 2026 US market holidays that fall in window
hol = {dt.date(2026, 11, 26), dt.date(2026, 12, 25)}  # Thanksgiving, Christmas
d0 = dates[-1]
d1 = dt.date(2026, 12, 31)
n = 0
d = d0
while d < d1:
    d += dt.timedelta(days=1)
    if d.weekday() < 5 and d not in hol:
        n += 1
T = n / 252.0
print("\nspot S=%.2f  expiry=2026-12-31  trading days left n=%d  T=n/252=%.4f" % (S, n, T))


def Phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def p_above(K, sig, mu=0.0):
    # P(S_T > K) under dS/S = mu dt + sig dW  ->  N(d2), d2=(ln(S/K)+(mu-sig^2/2)T)/(sig sqrtT)
    if K <= 0:
        return 1.0
    d2 = (math.log(S / K) + (mu - 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    return Phi(d2)


sig20, sig60 = rv(20), rv(60)
sig_used = sig20
print("using sigma = 20d realized = %.4f (mu=0)" % sig_used)

brk = [("<6000", 0, 6000), ("6000-6500", 6000, 6500), ("6500-7000", 6500, 7000),
       ("7000-7500", 7000, 7500), ("7500-8000", 7500, 8000), (">8000", 8000, None)]
mid_p = {"<6000": 0.0315, "6000-6500": 0.08, "6500-7000": 0.145,
         "7000-7500": 0.285, "7500-8000": 0.265, ">8000": 0.40}
print("\n%-10s %8s %8s %8s %8s" % ("bracket", "model20", "model60", "mkt_mid", "diff20"))
for name, lo, hi in brk:
    p20 = p_above(lo, sig20) - (p_above(hi, sig20) if hi else 0.0)
    p60 = p_above(lo, sig60) - (p_above(hi, sig60) if hi else 0.0)
    print("%-10s %8.4f %8.4f %8.4f %+8.4f" % (name, p20, p60, mid_p[name], mid_p[name] - p20))
print("sum of market mids   = %.4f" % sum(mid_p.values()))
print("sum of model(20d)    = %.4f" % sum(p_above(lo, sig20) - (p_above(hi, sig20) if hi else 0.0) for _, lo, hi in brk))

# implied sigma: sigma that makes model P(>8000) equal market mid 0.40
lo, hi = 0.30, 1.20
for _ in range(80):
    m = (lo + hi) / 2
    if p_above(8000, m) < 0.40:
        lo = m
    else:
        hi = m
print("sigma implied by market mid of '>8000' (0.40) = %.4f" % ((lo + hi) / 2))

# ---------- 3. daily market: model vs market for 2026-10-20 ----------
print("\n1-day: sigma_1d = %.4f; driftless lognormal gives P(up)=0.5000" % (sig20 / ann))
mu = statistics.mean(lr)
t = mu / (statistics.stdev(lr) / math.sqrt(len(lr)))
print("mean daily log return %.6f  t-stat over %d bars = %.2f" % (mu, len(lr), t))
print("market mid for spx-up-or-down-on-october-20-2026 = 0.625 (outcomePrices 0.625/0.375)")
```

**脚本 1 的完整输出（原样）**

```
bars=1254  first=2021-10-20 4536.19  last=2026-10-19 7690.73
realized vol 20d = 0.0904 (20 obs, 2026-09-22..2026-10-19)
realized vol 60d = 0.1100
realized vol 252d = 0.1271
up-day share, full sample: 664/1253 = 0.5299
up-day share, last 100 bars: 47/100 = 0.4700

spot S=7690.73  expiry=2026-12-31  trading days left n=51  T=n/252=0.2024
using sigma = 20d realized = 0.0904 (mu=0)

bracket     model20  model60  mkt_mid   diff20
<6000        0.0000   0.0000   0.0315  +0.0315
6000-6500    0.0000   0.0004   0.0800  +0.0800
6500-7000    0.0109   0.0298   0.1450  +0.1341
7000-7500    0.2643   0.2844   0.2850  +0.0207
7500-8000    0.5636   0.4798   0.2650  -0.2986
>8000        0.1612   0.2056   0.4000  +0.2388
sum of market mids   = 1.2065
sum of model(20d)    = 1.0000
sigma implied by market mid of '>8000' (0.40) = 1.2000

1-day: sigma_1d = 0.0057; driftless lognormal gives P(up)=0.5000
mean daily log return 0.000421  t-stat over 1253 bars = 1.40
market mid for spx-up-or-down-on-october-20-2026 = 0.625 (outcomePrices 0.625/0.375)
```

**脚本 2：`spx_calibration.py`（全文，依赖 `series_closed.json`）**

```python
#!/usr/bin/env python3
# B11 step 2: calibration of resolved Polymarket SPX "Up or Down" daily markets
import json, math, time, urllib.request, datetime as dt, statistics

ev = json.load(open("series_closed.json"))
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=30))


rows = []
for e in ev:
    m = e["markets"][0]
    op = json.loads(m["outcomePrices"])
    if op not in (["1", "0"], ["0", "1"]):
        continue
    y = 1 if op == ["1", "0"] else 0          # 1 = Up
    tok = json.loads(m["clobTokenIds"])[0]     # YES token
    hist = []
    for attempt in range(3):
        try:
            hist = get("https://clob.polymarket.com/prices-history?market=%s&interval=max&fidelity=60" % tok).get("history", [])
            break
        except Exception:
            time.sleep(1.5)
    if not hist:
        continue
    end = dt.datetime.strptime(e["endDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()
    cut = end - 6 * 3600                       # price 6h before the 16:00 ET close
    pre = [h for h in hist if h["t"] <= cut]
    if not pre:
        continue
    p6 = pre[-1]["p"]
    rows.append({"slug": e["slug"], "end": e["endDate"], "y": y, "p6": p6,
                 "n_hist": len(hist), "p_last": hist[-1]["p"]})
    time.sleep(0.15)

print("events with outcome + history + a 6h-before-close quote: %d" % len(rows))
if not rows:
    raise SystemExit
base = sum(r["y"] for r in rows) / len(rows)
print("up-share in this sample: %d/%d = %.4f" % (sum(r["y"] for r in rows), len(rows), base))

def logloss(ps, ys):
    eps = 1e-9
    return -sum(math.log(max(eps, min(1 - eps, p if y else 1 - p))) for p, y in zip(ps, ys)) / len(ys)

mk = [r["p6"] for r in rows]
ys = [r["y"] for r in rows]
print("mean market price 6h before close = %.4f" % statistics.mean(mk))
print("mean |p6-0.5| = %.4f ; share of events with p6 outside 0.45-0.55 = %.4f"
      % (statistics.mean(abs(p - .5) for p in mk), sum(1 for p in mk if p < .45 or p > .55) / len(mk)))
print("Brier  market(p6)      = %.5f" % statistics.mean((p - y) ** 2 for p, y in zip(mk, ys)))
print("Brier  constant 0.50   = %.5f" % statistics.mean((0.5 - y) ** 2 for y in ys))
print("Brier  constant base   = %.5f" % statistics.mean((base - y) ** 2 for y in ys))
print("logloss market(p6)     = %.5f" % logloss(mk, ys))
print("logloss constant 0.50  = %.5f" % logloss([0.5] * len(ys), ys))
sel = [r for r in rows if r["p6"] >= 0.60 or r["p6"] <= 0.40]
if sel:
    pnl = []
    for r in sel:
        if r["p6"] >= 0.60:
            cost = r["p6"]; win = r["y"] == 1
        else:
            cost = 1 - r["p6"]; win = r["y"] == 0
        pnl.append((1.0 if win else 0.0) - cost)
    print("taker subset |p6-0.5|>=0.10: n=%d  mean gross pnl/share=%+.4f  hit rate=%.3f"
          % (len(sel), statistics.mean(pnl), sum(1 for x in pnl if x > 0) / len(pnl)))
band = [r for r in rows if 0.55 <= r["p6"] <= 0.75]
print("events with p6 in [0.55,0.75] (the range of the 2026-10-20 live quote 0.625): %d" % len(band))
if band:
    print("  of those, YES won %d = %.3f" % (sum(r["y"] for r in band), sum(r["y"] for r in band) / len(band)))

print("median number of 60-min observations per market = %d" % statistics.median([r["n_hist"] for r in rows]))
print("mean |p_last - p6| = %.4f" % statistics.mean(abs(r["p_last"] - r["p6"]) for r in rows))
json.dump(rows, open("spx_calib_rows.json", "w"))
```

**脚本 2 的完整输出（原样）**

```
events with outcome + history + a 6h-before-close quote: 21
up-share in this sample: 9/21 = 0.4286
mean market price 6h before close = 0.5593
mean |p6-0.5| = 0.2293 ; share of events with p6 outside 0.45-0.55 = 1.0000
Brier  market(p6)      = 0.17370
Brier  constant 0.50   = 0.25000
Brier  constant base   = 0.24490
logloss market(p6)     = 0.51161
logloss constant 0.50  = 0.69315
taker subset |p6-0.5|>=0.10: n=16  mean gross pnl/share=-0.0288  hit rate=0.750
events with p6 in [0.55,0.75] (the range of the 2026-10-20 live quote 0.625): 5
  of those, YES won 1 = 0.200
median number of 60-min observations per market = 34
mean |p_last - p6| = 0.3574
```

**未做到/未核实的（照写）**

- stooq CSV 未取到（JS 挑战页），改走 Yahoo；两者都不是 Polymarket 的结算源（WSJ / Yahoo `^GSPC` / Pyth），模型输入与结算源之间还有一处口径差，未量化。
- 未取 VIX 或 SPX 期权隐含波动率（没有找到本次可用的免密钥日线接口，**未查到**），所以「已实现 vs 隐含」的对照缺失。
- 未取逐笔成交，未做盘口深度估计，`ask 0.39` 的可得量未知。
- `public-search?q=SPX` 只翻到 20 条（`limit_per_type=20`），「每月多少个 SPX 相关 event」只用 `series_id=10383`（日频涨跌）数过，`spx-hit-*` / `spx-close-*` 的月频未逐月数。

---

## glm-5.3 事实核查报告

# Fact-check report — B11.md (SPX realized-vol lognormal pricing)

**Fetches (12 explicit + 2 script re-runs): every cited URL live.** No fabrication found.

**VERIFIED exactly:** Rule text (WSJ source, tie→50-50, nearest-cent, "higher range bracket", Yahoo `^GSPC` for Dec ladder, Pyth no-rounding + equal→No for NVDA); `endDate=2026-10-20T20:00:00Z`, `startDate=2026-10-19T12:00:52Z`; tags incl. `indicies`; series 10383 / `spx-daily-up-or-down` / daily / restricted; `umaBond=250`, `umaReward=0.6`, `rewardsMinSize=100`, `orderMinSize=5`, tick 0.01, `feeSchedule rate=0.04/rebate 0.25/takerOnly`, `takerBaseFee=1000`; NVDA strikes $210–$230, negRisk=false, vol 1224.392; series month counts 05:3/06:21/07:21/08:21/09:21/10:13, total vol $10,779,504.35, per-event vols (164,019.45 / 43,470.21 / 37,722.58 / 68,932.03); `spx-hit-dec-2026` 425,924.998727; NVDA search vols 94,705.68 / 140.17 / 714.93 / 29,917.22 / 11,820.45; Yahoo 1,254 bars 4536.19→7690.73, EDT/−14400; stooq JS-challenge page (reproduced); CLOB live history literally opens `{"t":1792414822,"p":0.53}`; key leg $7,500–$8,000: mid 0.265 / bid 0.14 / ask 0.39 / vol 4,727.16 — unchanged.

**TIME-VARYING (worker dated 2026-10-20; acceptable):** daily event 0.625→0.595, bid/ask 0.62/0.63→0.59/0.60, vol 9,536→9,950; three Dec-ladder mids moved (0.08→0.16, 0.145→0.245, 0.285→0.26), mid sum 1.2065→1.3615, ask sum 1.601→1.921 (no complete-set arb either snapshot); `regularMarketChangePercent −49.898→0.409` (intraday field, worker correctly refused to use it).

**Scripts:** saved & re-run both. Script 1 output byte-for-byte matches claimed output (σ 0.0904/0.1100/0.1271, 664/1253, n=51, T=0.2024, implied σ capped at 1.20, t=1.40). Script 2 (live CLOB re-fetch of 100 events → 21 with history) matches exactly: Brier 0.17370/0.25000/0.24490, logloss 0.51161, taker subset n=16 mean −0.0288 hit 0.750, band 5 events YES 1/5, median 34 obs, |p_last−p6|=0.3574.

**Problems:**
1. Front-matter `id: quant-XXX` is a placeholder; GUIDE §7 requires id matching filename (next would be `quant-014`). Fix before commit.
2. Minor: 门槛自查 #4 cites "`grep -ril "SPX|S&P|lognormal|已实现波动"` … 只命中 dot-048 与 quant-008" — my grep also hits quant's own CLAIMS.md line 20 (the B11 claim itself); harmless, wording could say "other bots' files".
3. Ladder table snapshot ages fast (3 of 6 mids moved intraday); consider labeling the table "snapshot 2026-10-20, refresh before use" — the entry already timestamps sources, so optional.

**Compliance:** required fields all present/valid except id; fee formula = GUIDE §8 exactly (0.04×0.625×0.375=0.009375 ✓, 0.04×0.39×0.61=0.009516 ✓, gap 17.4¢−0.95¢−12.5¢=4.0¢ ✓); volumes honestly over-labeled 来源自报； honest negative-result disclosure on the daily leg; no unrun-backtest claims; no keys/paid data; failures (stooq, 79 empty histories) disclosed. **Duplication:** claimed in `bots/quant/CLAIMS.md` (B11, 进行中); distinct from dot-018 (Deribit BTC implied, crypto), dot-048 (dispersion), quant-005 (mentions counts), quant-008 (FDV ladder), KNOWN.md A-A3/S-S1 — new variable (free-daily realized vol on index close brackets).

VERDICT: FIX — every number, quote, script output and failed fetch reproduced exactly; only the `id: quant-XXX` placeholder (and optionally a snapshot-refresh label) needs fixing before commit.

GATES_PASSING: 5/7 (2,3,4,6,7 pass — gate 2/6 via the explicit "record-forward only" disclosure; gate 1 persistence evidence and gate 5 ask-fill economics remain unproven, matching the entry's own 待选区 self-assessment).
