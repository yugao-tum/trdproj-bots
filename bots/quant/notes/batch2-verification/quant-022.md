# quant-022 工作者核对日志（deepseek-flash 原稿附录，含脚本全文）+ glm-5.3 事实核查报告

## VERIFICATION LOG (reviewer only, not for commit)

访问日期全部为 2026-10-20（UTC）。所有抓取都是 keyless 公开 GET，未登录、未下单。

| # | URL | HTTP | 取到的原文/数字 |
|---|---|---|---|
| 1 | `https://www.binance.com/en/hodler-airdrop` | **202**, 0 B | 失败（Cloudflare）。不引用网页版 |
| 2 | `https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query?type=48&pageNo=1&pageSize=10` | **400** | `{"code":"000002","message":"illegal parameter"}`。换接口 |
| 3 | `https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20&catalogId=48` | 200 | `catalogName":"New Cryptocurrency Listing"`, `"total":2283` |
| 4 | 同上 `pageNo=1..12&pageSize=50` | 200 | 去重后 600 条公告，`releaseDate` 区间 2025-02-25…2026-10-14；标题含 `HODLer` 者 56 条，最新 `2026-06-30`（OPG），其后 0 条 |
| 5 | `.../cms/article/detail/query?articleCode=b026c9829d28459cb1f1a95000960a08` | 200, 80,839 B | OPG：`HODLer Airdrops Token Rewards: 6,400,000 OPG`；`from 2026-06-22 00:00 (UTC) to 2026-06-24 23:59 (UTC)`；`≤ 4%`；`greater than 0.01 BNB`；`within 5 hours`；`Listing Fee: 0`；`Snapshots ... multiple times at any point of time each hour` |
| 6 | `.../article/detail/query?articleCode=455eedc320bd43e28e2326f58d4aac2a` | 200, 82,839 B | GENIUS：`10,000,000 GENIUS`，`2026-05-11 00:00 (UTC) to 2026-05-13 23:59 (UTC)` |
| 7 | 另 17 个 `article/detail/query`（见条目出处） | 200 | 池数量与窗口见证据节表格；19/19 解析出 `≤ 4%`；18/19 解析出快照窗口，SAPIEN 一条的正则没匹配到窗口（记为 NO-SNAP，未用于中位数） |
| 8 | `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/monthly/fundingRate/BNBUSDT/` | 200 | XML 列表：`BNBUSDT-fundingRate-2020-02.zip` …（`IsTruncated=false`） |
| 9 | `https://data.binance.vision/data/futures/um/monthly/fundingRate/BNBUSDT/BNBUSDT-fundingRate-<2025-10..2026-09>.zip` ×12 | 200 | 每个 663–937 B；表头 `calc_time,funding_interval_hours,last_funding_rate`；首行 `1788220800005,8,0E-8`，末行 `1790784000002,8,0.00008965` |
| 10 | `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/spot/monthly/klines/<SYM>USDT/1d/...` ×12 代币 + 各月 zip | 200 | 12 个代币全部有 1d K 线；OPG 首个文件是 `2026-05`（早于空投月），MMT 首日 `2025-11-04` 开 0.1 / 高 4.4754 / 收 2.64 |
| 11 | `https://api.coinpaprika.com/v1/tickers/bnb-binance-coin` | 200 | `price 730.2616340282318`，`total_supply 131512046`，`circulating_supply null`，`last_updated 2026-10-20T04:22:16Z` |
| 12 | `https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT` | **451** | 被地区限制，未使用 |
| 13 | `https://gamma-api.polymarket.com/public-search?q=binance&limit_per_type=5&events_status=all` | 200 | 返回 `wif-listed-on-coinbase-or-binance` 等旧市场；未见 HODLer/BNB 持有奖励模板 |

复算命令与完整脚本（直接可跑，无需密钥）：

```python
# A) 资金费：12 个月合计
import zipfile,glob,csv,statistics
rates=[]
for f in sorted(glob.glob('fund/*.zip')):
    z=zipfile.ZipFile(f)
    for n in z.namelist():
        for row in csv.reader(z.read(n).decode().strip().splitlines()):
            if not row or not row[0].strip().isdigit(): continue
            rates.append((row[0],float(row[2])))
s=[r for _,r in rates]
print(len(rates), sum(s), statistics.mean(s)*1e4, statistics.median(s), sum(1 for x in s if x>0)/len(s))
# -> 1095 0.019709 0.18 0.0 0.3954
# 下载：for m in 2025-10..2026-09: https://data.binance.vision/data/futures/um/monthly/fundingRate/BNBUSDT/BNBUSDT-fundingRate-$m.zip

# B) 12 次空投的池面值（池数量来自公告正文正则，价格来自现货 1d 收盘）
import urllib.request,zipfile,io,csv,datetime,json
ev=[("TURTLE","2025-10-21",10000000),("MMT","2025-11-03",7500000),("SAPIEN","2025-11-06",15000000),
    ("ALLO","2025-11-11",15000000),("AT","2025-11-27",20000000),("BREV","2026-01-05",15000000),
    ("NIGHT","2026-03-11",240000000),("ROBO","2026-03-18",100000000),("CHIP","2026-04-28",25000000),
    ("AIGENSYN","2026-05-21",100000000),("GENIUS","2026-05-29",10000000),("OPG","2026-06-30",6400000)]
def dl(sym,month):
    u=f"https://data.binance.vision/data/spot/monthly/klines/{sym}USDT/1d/{sym}USDT-1d-{month}.zip"
    z=zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(u,timeout=25).read()))
    rows=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())))
    return [r for r in rows if r and r[0].isdigit()]
tot=0
for sym,dt,pool in ev:
    rows=dl(sym,dt[:7])
    dates=[(datetime.datetime.fromtimestamp(int(r[0])/1e6,datetime.UTC).date().isoformat(),float(r[4])) for r in rows]
    sel=[x for x in dates if x[0]==dt] or [x for x in dates if x[0]>=dt][:1]
    d,close=sel[0]; tot+=pool*close
    print(sym,dt,d,close,pool,f"{pool*close:,.0f}")
print(f"TOTAL {tot:,.0f}  EXCL_MMT {tot-19800000:,.0f}")   # -> TOTAL 67,868,860  EXCL_MMT 48,068,860
P=730.2616340282318
for S in [2e6,5e6,10e6,20e6,40e6]: print(S, round(tot/S,2), f"{tot/S/P*100:.3f}%")
for c in [0.019709,0.0317]: print("breakeven S", f"{48068860/(c*P):,.0f}")

# C) 公告正文解析（池数量 / 4% 硬顶 / 快照窗口）
import re,subprocess,json
def text(body):
    out=[]
    def walk(n):
        if isinstance(n,dict):
            if n.get('node')=='text': out.append(n.get('text',''))
            for c in n.get('child') or []: walk(c)
        elif isinstance(n,list):
            for c in n: walk(c)
    walk(json.loads(body)); return ''.join(out)
# code 取自 catalogId=48 列表里的 article['code']
d=json.loads(subprocess.run(['curl','-s',
  'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=b026c9829d28459cb1f1a95000960a08'],
  capture_output=True,text=True).stdout)
t=text(d['data']['body'])
print(re.search(r'HODLer Airdrops Token Rewards:\s*([\d,]+)\s*([A-Za-z0-9]+)',t).groups())      # ('6,400,000','OPG')
print(re.search(r'≤\s*([\d.]+)%',t).group(1))                                                   # 4
print(re.search(r'from\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2} \(UTC\))\s*to\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2} \(UTC\))',t).groups())
# 窗口结束日与公告日（releaseDate）间隔：n=18, min 3, median 12, max 21 天
```

未核实/失败清单（照写）：
- `S`（Simple Earn + On-Chain Yields 的 BNB 小时平均总量）：**未查到**，币安不公布；上表情景是我给的自变量，不是实测。
- `SAPIEN` 公告正文正则未匹配到快照窗口（NO-SNAP），未计入间隔中位数。
- 币安网页版 `en/hodler-airdrop` 202、`api.binance.com` 451：均未使用。
- Launchpool 的池子与折算：本次未抓取，**未查到**，不计入收益。
- 无回测：`observed_net_return = null`，`backtest_count = 0`（只表示没做回测，不表示收益为 0）。

---

## glm-5.3 事实核查报告

# Fact-check report: B19.md (BNB HODLer airdrop + perp hedge)

## Re-fetch results (19 fetches + full script re-run)

**VERIFIED exactly (source matches):**
- CMS list catalogId=48: `total 2283`, `catalogName "New Cryptocurrency Listing"`, 12 pages → 600 unique articles, 2025-02-25→2026-10-14; 56 HODLer-titled; earliest SHELL 2025-02-27; latest OPG 2026-06-30 (code matches); **0 after 2026-07-01; 12 in 2025-09; exactly 12 in the 2025-10-21→2026-10-20 window, matching the 12-row table token-by-token and date-by-date**.
- OPG article (80,839 B as logged): `6,400,000 OPG`, window `2026-06-22 00:00 (UTC) to 2026-06-24 23:59 (UTC)`, `≤ 4%`, `greater than 0.01 BNB`, `within 5 hours`, `Listing Fee: 0`, hourly-snapshot sentence, Simple-Earn eligibility quote, Loans-collateral exclusion, slisBNB — all present verbatim. GENIUS (82,839 B as logged): `10,000,000 GENIUS`, `2026-05-11…2026-05-13` — verified.
- Funding zips (sizes 663–937 B as logged): re-ran script → **1095 rows, sum 0.01970869, mean 0.18 bp, median 0, 39.54% positive; extremes −3.5218/+3.2423 bp; last row `1790784000002,8,0.00008965`** — all match.
- Klines re-run: all 12 pool face-values match row-by-row; **TOTAL 67,868,860 / EXCL_MMT 48,068,860**; scenario table (33.93/4.65% … 1.70/0.23%) matches; MMT 11-04 O 0.1/H 4.4754/C 2.64/quotevol 931,122,562, next-day close 0.749 — all match.
- Failure claims: `/en/hodler-airdrop` → HTTP 202, 0 B ✓; api.binance.com → 451 ✓; Gamma `public-search?q=binance` → only WIF/CZ-type old markets, no HODLer/BNB ✓. Bucket earliest `2020-02.zip` ✓.
- **CoinPaprika: price now 729.71, total_supply 131,512,045 (claimed 730.2616 / 131,512,046 @ 04:22:16Z) — time-varying, timestamped by worker; `circulating_supply: null` ✓.**

## Problems (all minor)

1. **Front-matter `id: quant-XXX` placeholder** (line 2) violates GUIDE §7 "id 和文件名一致" — fix to `quant-014` (next after quant-013) at commit.
2. Breakeven rounding: entry `S ≤ 3,339,700` vs computed 3,339,802 and `2,076,600` vs 2,076,472 (§2, 成本节) — ≤0.01% off; harmless but should copy script output.
3. Log row 8 says bucket `IsTruncated=true`; my fetch returned `IsTruncated=false` — cosmetic, no number affected.
4. Duplication: KNOWN.md has `Y-Y2-launchpool`（币安 Launchpool 质押挖新币）and `Y-Y2-airdrop-farming`；same broad class "hold BNB on Binance → new-token rewards". Entry honestly flags as 不确定 and argues distinction (retroactive snapshots vs. active pool staking, plus hedge leg, negative conclusion); no BNB/HODLer entries exist in any bots/*/entries. Main-reviewer call; may need `kind: supplement` to Y-Y2-launchpool.
5. "18 announcements, 3–21 day gap, median 12" — I verified 2 of 18 (OPG 6d, GENIUS 16d, both in range); rest plausible but not re-fetched (fetch cap).

## Compliance
Rule/fee formula N/A (crypto, `pm_category: -` correct). 来源自报 labelling N/A (all self-computed, "未查到" used properly). 门槛自查 honest — admits gates 2/5/6 fail, no backtest claimed (`backtest_count = 0`), no keys/paid data, failures documented. Claims B19 is registered in quant/CLAIMS.md ✓ (in progress).

Script saved at /tmp/verify_b19/run_check.py; output matches entry numbers in full.

GATES_PASSING: 3/7 (mechanism, small-capital, sources; gate 4 uncertain; gates 2/5/6 fail as self-reported).

VERDICT: FIX — substance is fully reproducible and honestly negative-conclusion, but the `id: quant-XXX` placeholder must be replaced with the real entry id/number before submission.
