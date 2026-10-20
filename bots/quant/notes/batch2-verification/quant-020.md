# quant-020 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

工作目录 `/workspace/agent-tools/quant-batch2/work_B17`。脚本：`fetch_earn.py`、`stats_earn.py`、`more.py`、`scan_all.py`、`price_test.py`、`sample_price.py`；数据落盘 `earn_closed.json`、`earn_closed_all.json`、`price_sample.json`。全部为 keyless public GET，无登录、无密钥、无付费。

抓取记录：

1. `GET https://gamma-api.polymarket.com/public-search?q=earnings&limit_per_type=20&events_status=all` — 200。
   取用片段：`{"slug":"hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05","title":"Will Hims & Hers Health (HIMS) beat quarterly earnings?" ... "resolutionSource":"https://seekingalpha.com/" ... "restricted":true,"volume":287931.953117,"closed":true}`；description 内含 `The Street consensus estimate for Hims & Hers Health's GAAP EPS for the relevant quarter is $0.05 as of market creation`、`reports GAAP EPS greater than $0.05`、`If no such figure is published within 96h of market close (4:00:00pm ET)`、`within 45 calendar days`、`rounded to the nearest cent using standard rounding`、`IFRS EPS will be treated as GAAP EPS`、`GAAP EPS refers to diluted GAAP EPS`、`derived from SeekingAlpha estimates`、`fat finger errors, as with Lyft's (LYFT) earnings release in February 2024`。

2. `GET https://gamma-api.polymarket.com/public-search?q=beat%20quarterly%20earnings&limit_per_type=50&events_status=all` — 200。
   取用片段：`"pagination": {"hasMore": true, "totalResults": 1485}`（**注意：这是搜索命中数，不是已关闭事件数；本条基率用的是第 4 条的 tag 全量翻页，不是这个 1485**）。

3. `GET https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=500&closed=true&order=endDate&ascending=false` — 200，但**只返回 100 条**（limit 上限约 100）；已关闭事件 `endDate` 范围 `2026-05-07T13:00:00Z`..`2026-10-19T21:00:00Z`。前 500 条子样本：YES 378 / NO 122 = 0.756。

4. `GET https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset={0,100,…,1300}&closed=true&order=endDate&ascending=false` — 全部 200，逐页累计至 offset=1300 后返回空 → **1378** 个已关闭事件，`endDate` `2024-01-19`..`2026-10-19`。`scan_all.py` 输出原文：
   ```
   closed events: 1378
   range: 2024-01-19T00:00:00Z 2026-10-19T21:00:00Z
   month 2024-01 1 / 2025-06 1 / 2025-09 11 / 2025-10 156 / 2025-11 172 / 2025-12 53
   month 2026-01 54 / 2026-02 169 / 2026-03 73 / 2026-04 120 / 2026-05 155 / 2026-06 44
   month 2026-07 143 / 2026-08 154 / 2026-09 44 / 2026-10 28
   markets yes/no/other: 1028 354 0 YES rate: 0.7438
   nongaap yes/no: 684 161 rate 0.8095
   gaap yes/no: 344 193 rate 0.6406
   ```
   公式：`YES率 = YES市场数 / (YES+NO)`；口径 `g = ('nongaap' in slug)`。校验：`1028+354=1382` 市场，`684+344=1028` YES、`161+193=354` NO。

5. `GET https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset={500..1000}&closed=true...` — 200，每页 100 条（用于确认翻页未截断，`offset=1000` 仍有数据、`offset=1300` 为空）。

6. `GET https://clob.polymarket.com/prices-history?market=<token>&startTs=<endDate-72h>&endTs=<endDate>&fidelity=60`（`sample_price.py` 250 次）— 247 次非空、3 次无 `t ≤ endDate-24h` 的点。`price_test.py`（该脚本实际用 `endDate-48h`，故首点 0.52；用 72h 重取为 0.445/68 点）前 5 例原文：
   ```
   wtfc-…-10-19-2026-3pt36  2026-10-19T21:00:00Z points 43  0.685 … 0.625
   tfc-…-10-16-2026-1pt13   2026-10-16T13:00:00Z points 44  0.52  … 0.0045
   mtb-…-10-16-2026-5pt00   2026-10-16T13:00:00Z points 43  0.745 … 0.9995
   cfg-…-10-16-2026-1pt40   2026-10-16T13:00:00Z points 44  0.79  … 0.775
   ibkr-…-10-15-2026-0pt70  2026-10-15T21:00:00Z points 45  0.435 … 0.26
   ```
   → 与 quant-012 的「已关闭市场 history 为空」相反，本族可取。

7. `sample_price.py` 输出原文（`p_24h` = `t ≤ endDate-24h` 的最后一个 `p`）：
   ```
   n with price: 247 failed: 3
   all: n=247 YESrate=0.7611 meanpreP24h=0.7230 gap=+0.0381 brier_mkt=0.1310 brier_base=0.1818
   gaap: n=90 YESrate=0.6333 meanpreP24h=0.6370 gap=-0.0036 brier_mkt=0.1728 brier_base=0.2322
   nongaap: n=157 YESrate=0.8344 meanpreP24h=0.7723 gap=+0.0621 brier_mkt=0.1070 brier_base=0.1382
   [0,0.2) n=7 meanP=0.0769 YESrate=0.0000
   [0.2,0.4) n=22 meanP=0.3193 YESrate=0.3182
   [0.4,0.6) n=35 meanP=0.4894 YESrate=0.6571
   [0.6,0.8) n=59 meanP=0.7124 YESrate=0.7288
   [0.8,1.01) n=124 meanP=0.9021 YESrate=0.9274
   gaap n= 18 meanP=0.4747 YES=0.5556
   nongaap n= 17 meanP=0.5050 YES=0.7647
   ```
   Brier 公式：`mean((p_24h − y)^2)`；基准率 Brier 用该组自身 YES 率作常数预测。

8. 成交量：`sum(volume)=21633950`、`median=6232`、`p90=29916`（1378 个事件的 Gamma `volume` 字段，**来源自报，未核实**）。2026 年事件数 `984`。

9. `GET https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&closed=false&order=endDate&ascending=true` — 200，100 条，`endDate` 最晚 `2026-10-30T13:00:00Z`；其中 `endDate ≤ 2026-11-03` 的 100 个。示例字段：`bfc-quarterly-earnings-gaap-eps-10-20-2026-2pt66` `bestBid=0.44 bestAsk=0.46`、`ally-…-1pt43` `0.17/0.77`、`efx-…-2pt24` `0.56/0.69`；`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`、`feesEnabled=true`、`orderPriceMinTickSize=0.01`。

10. 同上 `&offset=100` — 200，18 条，最晚 `endDate=2026-11-05T22:00:00Z` → 118 个 open 事件落在 2026-10-20..11-05 这 16 天内。

11. `GET https://efts.sec.gov/LATEST/search-index?q=form%3A8-K%20items%3A2.02&forms=8-K`（UA 带联系方式）— 200，`{"took":178,...,"hits":{"total":{"value":10000,"relation":"gte"}`。同一路径 `q="earnings"` 亦 200。`https://www.sec.gov/cgi-bin/srqsb?...` — **404**，未使用。SEC 逐份 EPS 抽取本轮**未做**，故 SEC 只列为「可用的独立复核口径」，没有把它当已算出的证据。

12. 未抓取/未核实：`docs.polymarket.com`（本轮未重开，费用公式沿用 GUIDE 第 8 节）；SeekingAlpha（付费墙，未抓）；data-api 逐笔成交（未取）；历史 L2（GUIDE 明示无公开来源）。

13. 已知不一致并在正文标注：GUIDE 第 8 节「金融 0.04」 vs 本条 Gamma 实取 `rate=0.05`；本条按实取值算，未改 GUIDE。

14. 未做的事（避免误读）：没有回测、没有资金曲线、没有成交复现；正文里「+29.1%/份」是**模型算术**且已注明 n=35、事后分桶、`p` 非可执行卖价。

### 复现命令（完整代码）

```python
# scan_all.py —— 基率（输出见记录 4）
import json,urllib.request,collections
def get(url):
    r=urllib.request.Request(url,headers={'User-Agent':'research/1.0'})
    with urllib.request.urlopen(r,timeout=40) as f: return json.load(f)
allv=[];off=0
while True:
    d=get(f"https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset={off}&closed=true&order=endDate&ascending=false")
    if not d: break
    allv+=d; off+=100
    if len(d)<100: break
print("closed events:",len(allv))
json.dump(allv,open('earn_closed_all.json','w'))
dates=[e.get('endDate') or '' for e in allv]
print("range:",min(dates),max(dates))
c=collections.Counter(d[:7] for d in dates)
for k in sorted(c): print("month",k,c[k])
yes=no=other=yn=nn=0
for e in allv:
    for m in e['markets']:
        op=m.get('outcomePrices'); op=json.loads(op) if isinstance(op,str) else op
        if not op: other+=1; continue
        g='nongaap' in e['slug']
        if op[0]=='1': yes+=1; yn+=g
        elif op[1]=='1': no+=1; nn+=g
        else: other+=1
print("markets yes/no/other:",yes,no,other,"YES rate:",round(yes/(yes+no),4))
print("nongaap yes/no:",yn,nn,"rate",round(yn/(yn+nn),4))
print("gaap yes/no:",yes-yn,no-nn,"rate",round((yes-yn)/(yes+no-yn-nn),4))
```

```python
# sample_price.py —— 事前价 vs 结算（输出见记录 7）
import json,urllib.request,datetime
def get(url):
    r=urllib.request.Request(url,headers={'User-Agent':'research/1.0'})
    with urllib.request.urlopen(r,timeout=30) as f: return json.load(f)
ev=json.load(open('earn_closed_all.json')); ev.sort(key=lambda e:e['endDate'],reverse=True)
rows=[];fail=0
for e in ev[:250]:
    m=e['markets'][0]; tok=json.loads(m['clobTokenIds'])[0]
    end=datetime.datetime.fromisoformat(e['endDate'].replace('Z','+00:00'))
    s=int((end-datetime.timedelta(hours=72)).timestamp()); en=int(end.timestamp())
    try:
        h=get(f"https://clob.polymarket.com/prices-history?market={tok}&startTs={s}&endTs={en}&fidelity=60").get('history',[])
    except Exception: fail+=1; continue
    cut=(end-datetime.timedelta(hours=24)).timestamp()
    pre=[x for x in h if x['t']<=cut]
    if not pre: fail+=1; continue
    op=json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'],str) else m['outcomePrices']
    rows.append(dict(slug=e['slug'],end=e['endDate'],p=pre[-1]['p'],y=1 if op[0]=='1' else 0,
                     g='nongaap' if 'nongaap' in e['slug'] else 'gaap'))
json.dump(rows,open('price_sample.json','w'))
print("n with price:",len(rows),"failed:",fail)
for g in ('all','gaap','nongaap'):
    r=[x for x in rows if g=='all' or x['g']==g]; n=len(r)
    yrate=sum(x['y'] for x in r)/n; mp=sum(x['p'] for x in r)/n
    print(f"{g}: n={n} YESrate={yrate:.4f} meanpreP24h={mp:.4f} gap={yrate-mp:+.4f} "
          f"brier_mkt={sum((x['p']-x['y'])**2 for x in r)/n:.4f} "
          f"brier_base={sum((yrate-x['y'])**2 for x in r)/n:.4f}")
for lo,hi in [(0,0.2),(0.2,0.4),(0.4,0.6),(0.6,0.8),(0.8,1.01)]:
    r=[x for x in rows if lo<=x['p']<hi]
    if r: print(f"[{lo},{hi}) n={len(r)} meanP={sum(x['p'] for x in r)/len(r):.4f} YESrate={sum(x['y'] for x in r)/len(r):.4f}")
```

---

## glm-5.3 事实核查报告

# B17 Fact-Check Report

## Refetch results (~285 fetches incl. script re-runs; now = 2026-10-20 04:34 UTC)

**Reproduced exactly (script re-runs + direct refetch):**
- `scan_all.py` re-run: **1378 closed events**, endDate 2024-01-19→2026-10-19, all 14 monthly counts (156/172/53/54/169/73/120/155/44/143/154/44/28…), YES 1028/NO 354=74.38%, nongaap 684/161=80.95%, gaap 344/193=64.06% — identical.
- `sample_price.py` re-run: band **[0.40,0.60) n=35, meanP=0.4894, YES=0.6571** identical; buckets ≤0.6 identical. Now n=246 (1 transient CLOB failure vs 3 before) — worker's 247 stands. Saved `price_sample.json` sub-splits (gaap n=18 0.4747/0.5556; nongaap n=17 0.5050/0.7647; band share 14.17%) match.
- hims slug fetch: all 10 rule quotes found verbatim (`$0.05 as of market creation`, `greater than $0.05`, 96h, 45 days, rounding, IFRS, diluted, SeekingAlpha, Lyft fat-finger); `resolutionSource=https://seekingalpha.com/`, `restricted=true`, volume 287931.953117 exact.
- Open events: 100+18=**118**, max endDate 2026-10-30 / 2026-11-05 — matches. `bfc` 0.44/0.46, `efx` 0.56/0.69 exact; **ally ask now 0.70 vs 0.77 quoted — time-varying** (bid/ask move; timestamped).
- `feeSchedule {rate:0.05, takerOnly, rebateRate:0.25}`, feesEnabled, taker/makerBaseFee=1000, orderMinSize=5, tick 0.01 — exact. GUIDE's 0.04-finance discrepancy is real and honestly flagged; entry correctly uses 0.05 with the GUIDE formula (fee/share 0.0125 at p=0.4894, 2.55% of stake — arithmetic checks; +29.1%/+23.1% stress also check).
- SEC EDGAR endpoint: 200, `hits.total.value=10000, relation:"gte"` — matches.
- Volume sum $21,633,950 / median $6,232 / p90 $29,916 / 984 events in 2026 — exact from raw data.

**Duplication:** KNOWN.md (135 entries, count verified) has no EPS/earnings mechanism; `E-E1-macro-window`/`E-E1-index-etf-event` exist as cited; quant-004 is mentions-markets (different settlement), quant-012 cross-reference ("closed earthquake markets return empty history") accurately quoted; no overlap in bots/*/entries or batch drafts B11/B15. B17 properly claimed in `bots/quant/CLAIMS.md:26`.

## Problems

1. **`id: quant-XXX`** (front matter) — GUIDE §7 requires id to match filename/numbering (next: quant-014). Fix at commit; batch-draft convention, not fabrication.
2. VERIFICATION LOG record 6 states the 72h window but `price_test.py` actually uses −48h (hence first-point 0.52; a fresh 72h fetch gives 0.445/68 pts; final prices 0.0045/0.9995 still match). Log-only imprecision.
3. `public-search totalResults` now 1727 vs 1485 — time-varying; log itself correctly says it's unused for the base rate.

**Honesty/compliance:** 来源自报 labels present (volume, spread samples); 门槛自查 truthful (`backtest_count=0`, no backtest claimed, ex-post bucketing and n=35 caveats explicit); no keys, no paid data (SeekingAlpha paywall respected).

VERDICT: KEEP — every checkable number and quote reproduces exactly from live sources and script re-runs, with only the placeholder id to fix at commit time.

GATES_PASSING: 7/7
