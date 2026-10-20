# quant-012 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

| URL | HTTP 结果 | 取用的小片段/数字 |
|---|---|---|
| `gamma-api.polymarket.com/public-search?q=earthquake&limit_per_type=50&events_status=all` | 200，JSON（截断到 6000 字符内） | 事件 slug 清单；`earthquake-7pt0-or-above-by-august-31-698` vol 309781.34；`how-many-6pt5-...october-19-october-25`；tags 含 `weather`,`earthquake`,`recurring` |
| `gamma-api.polymarket.com/public-search?q=magnitude&limit_per_type=50` | 200 | `how-many-7pt0-or-above-earthquakes-in-2026` vol 1477696.9；`will-there-be-an-earthquake-of-magnitude-4pt5-or-higher-in-the-conterminous-us-by-december-31st` vol 53318.4 |
| `gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25` | 200 | 规则原文（ET 周界、USGS 源、48h 迟报、24h 修订、lowest bracket 兜底）；`startDate=2026-10-16T14:23:50Z`、`endDate=2026-10-26T03:59:00Z`、`volume=1467.663831`、`liquidity=5469.92364`；七档 bid/ask；`feeSchedule={'exponent':1,'rate':0.05,'takerOnly':True,'rebateRate':0.25}`；`clobRewards` 日率 11/6/2/1/—/—/—；`rewardsMinSize=20`、`rewardsMaxSpread=5.5`（部分 4.5）；`orderPriceMinTickSize` 0.01（4/5/>5 档 0.001）；`orderMinSize=5`；`negRisk=true` |
| `earthquake.usgs.gov/fdsnws/event/1/query?format=csv&...minmagnitude=6.4` | 200，1,513 行 CSV | 表头确认 `mag`、`magType`、`type`、`status` 字段；`mag≥6.5` 计数 1,216（我自己筛） |
| `earthquake.usgs.gov/fdsnws/event/1/count?...minmagnitude=6.5`（2015-01-01..2026-01-01） | 200 | `{"count":462,"maxAllowed":20000}` |
| 同上 `minmagnitude=7.0` | 200 | `{"count":153,"maxAllowed":20000}` |
| 同上 `minmagnitude=5.5` | 首次 502 Bad Gateway（nginx），复核 200 | `{"count":5031,"maxAllowed":20000}` |
| `earthquake.usgs.gov/fdsnws/event/1/query?format=text&starttime=2026-10-12&endtime=2026-10-19&minmagnitude=6.5` | 200 | 3 行：`us6000u2mq 2026-10-16T03:35:31.925 6.9 mww`、`us6000u214 2026-10-13T12:23:07.248 6.8`、`us6000u1z5 2026-10-13T05:44:46.919 6.7` |
| `earthquake.usgs.gov/earthquakes/search/` | 200 HTML | `<title>Search Earthquake Catalog</title>` |
| `gamma-api.polymarket.com/events?slug=how-many-6pt5-...october-12-october-18` | 200 | `closed False`、vol 15189.73；七档 prices `0.0035/0.0025/0.004/0.95/0.05/0.025/0.0245` |
| `gamma-api.polymarket.com/events?tag_slug=earthquake&limit=500&closed=true&order=endDate&ascending=false` | 200 | 69 个事件，`endDate` 2024-09-30..2026-10-19，成交合计 5,869,975；分类 37/17/12/3；月份 2026-07:9 2026-08:10 2026-09:9 2026-10:5 |
| `clob.polymarket.com/prices-history?market=<0 档 token>&interval=max&fidelity=60` | 200 | `{"t":1792162843,"p":0.345}` … `{"t":1792270842,"p":0.475}` |
| `clob.polymarket.com/prices-history?market=<3 档 token>&interval=max&fidelity=60` | 200 | 首值 `p=0.225`，后段 `0.055–0.225` |
| `clob.polymarket.com/prices-history?market=1015199930...`（2025-08-31 事件 token） | 200 | `{"history":[]}` → 已关闭市场无历史报价 |
| `gamma-api.polymarket.com/markets?slug=how-many-6pt5-...october-19-october-25` | 200，`[]` | 空数组；改走 `events?slug=` 才拿到市场对象 |
| `gamma-api.polymarket.com/tags?limit=100` | 200 | 用于确认 tag 体系（`weather` id 84、`science` id 74 等） |

我自己算的中间量（公式已写在正文）：`1216/1395=0.8717`；分布 663/440/178/70/29/5/7/1/1/1 共 1,395；`114/1395=0.0817`；`15/1395=0.0108`；卖价和 `1.218`、买价和 `0.924`、中价和 `1.071`；≥3 的四档中价 `0.075+0.035+0.0055+0.0105=0.126`，经验基率 `0.0502+0.0208+0.0036+0.0072≈0.0817`，比值 `0.126/0.0817=1.54`；吃单费 `0.05×0.11×0.89=0.0049`。

---

## glm-5.3 事实核查报告

## Fact-check report — B09.md (14 URLs re-fetched of ~15 cited; cap respected)

**VERIFIED (exact match):** USGS CSV 1,513 lines incl. header / 1,216 mag≥6.5 / 1,395 bins / distribution 663-440-178-70-29-5-7-1-1-1 / mean 0.8717 / segments 434@40.38, 243@42.28, 42@42.03 per yr; counts 462 & 153; all 8 quoted rule-text phrases found verbatim (ET window, USGS source, 48h/24h, lowest bracket, anywhere on Earth); event fields startDate/endDate/volume 1467.663831/negRisk/feeSchedule {1, 0.05, takerOnly, 0.25}/fees 1000-1000/orderMinSize 5/ticks 0.01 & 0.001/clobRewards 11-6-2-1, rewardsAmount 0, minSize 20, spread 5.5/4.5; brackets 0/3/4/5/>5 bid-ask-mid exact; 10-12 event closed=false, vol 15189.73, bracket-3 0.95 & vol 1930.25; USGS 10-12…10-19 exactly 3 events (ids/times/mags match); tag scan 69 events/$5,869,975/37-17-12-3/monthly counts; CLOB t=1792162843 p=0.345 and t=1792270842 p=0.475 exact, bracket-3 first 0.225; closed-market token returns `{"history":[]}`; public-search vols 1477696.9/1941867.7/309781.3; page title; 2026-10-19 is Monday.

**Problems:**
1. **MISMATCH (arithmetic):** 「P(≥3) = (70+29+5+7+1+1+1)/1395 = **107**/1395 = **0.0767**」 — the sum is **114**; correct is 114/1395 = **0.0817**. Consequently 「P(≥3) **7.67%** vs **5.66%**」 should read 8.17% vs 5.83%. The correct 0.0817 appears elsewhere (tail base rate), so the conclusion survives, but fix both lines.
2. **Stale claim:** M5.5 `/count` now returns HTTP 200 `{"count":5031,...}` — the worker's 502 was transient. Honest as written, but 「M5.5 序列的基率未查到」 should be re-fetched and filled in.
3. **Mislabel:** 「尾部**三**档中价 0.126」 sums **four** brackets (3/4/5/>5 = 0.075+0.035+0.0055+0.0105); occurs in body, 门槛自查 #1, and LOG. Say 「≥3 的四档」. Also 0.0817 vs 0.0818 rounding inconsistency body/LOG.
4. **Time-varying (acceptable, timestamped 2026-10-20):** bracket-1 ask 0.34→0.33, bracket-2 ask 0.17→0.18, liquidity 5469.92→4863.38; derived 1.218/0.924/1.071 and EV table are snapshot arithmetic (internally consistent). Bracket-3 rewards startDate is 10-19, not all 10-20 (trivial).
5. **Format:** `id: quant-XXX` placeholder must match filename and live under `bots/<bot>/entries/` (GUIDE §5/§7). Minor: bracket-3 price band 「0.065–0.12」 is approximate (actual 0.055–0.225 range post-drop).

**Compliance:** fee formula `份数×费率×p×(1−p)` used correctly with fetched `feeSchedule`; volume/liquidity properly flagged 「来源自报，未核实」; explicitly states 「没有做回测」, `backtest_count=0`, `observed_net_return=null` — no fabricated backtests; no keys/paid data; gate #6 honestly failed → 待选区. **Duplication:** no earthquake/USGS entries in KNOWN.md (135) or dot entries; distinct from V-V2-poly-longshot, M-M4-poly-rewards/dot-032 (distinction addressed in-text). Novel mechanism/variable.

VERDICT: FIX — one genuine arithmetic error (107→114/0.0767→0.0817), a now-stale 502 claim, and a placeholder id, but every checkable source and number otherwise verifies exactly.

GATES_PASSING: 5/7
