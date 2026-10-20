# quant-011 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

按本会话内实际执行的 curl 顺序。除注明外全部 keyless GET，无登录、无密钥。

1. `GET https://gamma-api.polymarket.com/events?slug=arsenal-vs-leeds-united-2025-08-23`
   → HTTP 200，body 为 `[]`（3 字节）。**猜测的 slug 不存在，未据此引用任何内容。**
2. `GET https://gamma-api.polymarket.com/events?tag_slug=soccer&limit=5&closed=false`
   → HTTP 200，951,092 字节。取用：event 列表结构（`ballon-dor-winner-2026` 有 89 个市场等）。**未用作数字来源。**
3. `GET https://gamma-api.polymarket.com/events?tag_slug=soccer&limit=20&order=startDate&ascending=false`
   → HTTP 200，3,102,711 字节。取用：`epl-new-eve-2026-11-02`（3 个市场）、`sea-ata-par-2026-11-02`（3 个市场）；event `startDate/endDate`、`negRisk=true`、tags `sports,games,soccer,premier-league,EPL`；三个市场均为 `outcomes:["Yes","No"]`、`feeSchedule = {"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`、`takerBaseFee=1000`；`sea` 三个 Yes 价 `["0.66"],["0.195"],["0.17"]`，`epl-new-eve` 三个均 `["0.5","0.5"]`；draw 市场 `liquidity=141.1829`。
   规则原文（同一响应，`-draw` 市场 description）："This market refers only to the outcome within the first 90 minutes of regular play plus stoppage time."；"If the game is canceled entirely, with no make-up game, this market will resolve \"Yes\"."（主胜/客胜市场同一句写作 `"No"`）；主源为官方统计，2 小时后 Flashscore → Sofascore → consensus；赛后改判不追溯。
4. `GET https://docs.polymarket.com/trading/fees`
   → HTTP 200，397,457 字节（正文去标签后 5,595 字符）。原文取用："fee = C × feeRate × p × (1 - p) "；"Makers are never charged fees. Only takers pay fees."；费率表 "Sports 0.05 0 15%"（Taker/Maker/Rebate）、"Crypto 0.07"、"Finance 0.04"、"Geopolitics 0"、"Combos 0.05"。
5. `GET https://gamma-api.polymarket.com/events?slug=epl-new-eve-2026-11-02`
   → **HTTP 200 但 body 为 `[]`（3 字节）**。slug 直查不可用；event 数据取自上面第 3 项标签列表响应。**此处如实记录为失败查询。**
6. `GET https://www.football-data.co.uk/mmz4281/{2223,2324,2425,2526}/E0.csv`
   → 全部 HTTP 200，176,180 / 172,196 / 197,110 / 203,438 字节；每个文件 381 行（含表头）＝380 场。表头含 `Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HTHG,HTAG,HTR,...,B365H,B365D,B365A,BWH,BWD,BWA,BFH,BFD,BFA,PSH,PSD,PSA,WHH,WHD,WHA,1XBH...`。
7. `GET https://www.football-data.co.uk/mmz4281/{2223,2324,2425,2526}/I1.csv`
   → 全部 HTTP 200，171,573 / 167,015 / 191,722 / 196,217 字节；同样 380 场/季。
   自算（脚本只用上述 CSV 行）：`qD=(1/B365D)/(1/B365H+1/B365D+1/B365A)`；英超 0.18–0.22 桶 n=238、mean qD=0.2037、实际 0.2479、ROI(按 B365D)+0.1509；意甲同桶 n=184、0.2021、0.1848、−0.1378；合并同桶 n=422、0.2030、0.2204、+0.0250。整体平局率 E0 0.2408 / I1 0.2757 / 合并 0.2582（N=1520/1520/3040）。日期范围 E0 05/08/2022–24/05/2026，I1 13/08/2022–24/05/2026。
8. `GET https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&limit=400&start_date_min=2026-10-19&start_date_max=2026-10-26`
   → HTTP 200，9,405,737 字节，**只返回 100 个 event**（limit 被截到 100）；纯三向 slug 正则匹配得 16 个。说明该日期过滤未严格生效（见第 9 项）。
9. 分页 `offset=0,100,200,300,400,500`（同 URL）→ 每页 HTTP 200，9.4–14.3 MB，各 100 个 event；解析后纯三向比赛 event **111 个**，比赛日期计数：10-20:6、10-21:1、10-22:1、10-23:3、10-24:12、10-25:5、10-26:6、11-01:69、11-02:8。**日期过滤无效，600 个 event 只是 open soccer 的一部分，全平台 open soccer event 总数未查到**；文中“约 60 场/周”仅为这 111 个 event 跨 13 天的算术（111/13×7≈60）。
10. `GET https://gamma-api.polymarket.com/markets?slug=sea-ata-par-2026-11-02-draw`
    → HTTP 200，6,133 字节。原文取用：`bestBid=0.09`、`bestAsk=0.30`、`spread=0.21`、`orderPriceMinTickSize=0.01`、`orderMinSize=5`、`startDate=2026-10-19T23:00:31Z`、`endDate=2026-11-02T19:45:00Z`、`feeSchedule.rate=0.05`、`takerBaseFee=1000`；description 全 1,294 字符，末句原文 "If no acceptable data is available within 24 hours of the event's conclusion, this market will resolve 50-50, or to \"Draw\" where applicable."
11. `GET https://clob.polymarket.com/prices-history?market=115347507753485536976403009642719279973942206992108120088763998979109693996472&interval=max&fidelity=60`
    → HTTP 200，176 字节，`history` 共 6 点：`{"t":1792454444,"p":0.315}`，`1792458023/1792461623/1792465235/1792468825/1792468942` 均为 `p=0.195`。
12. `GET https://gamma-api.polymarket.com/markets?slug=epl-liv-ars-2026-11-01-draw`
    → HTTP 200，6,379 字节。`bestBid=0.25`、`bestAsk=0.27`、`spread=0.02`、`outcomePrices=["0.26","0.74"]`、`liquidity=3469.4498`、`orderPriceMinTickSize=0.01`、`endDate=2026-11-01T16:30:00Z`、`feeSchedule.rate=0.05`。
13. 本地 `grep -ril "soccer|draw|football-data|足球" bots/ known/` 与 `grep -n -i "soccer|draw|B08|平局" bots/quant/CLAIMS.md`（只读）→ 仓库内无足球平局条目；`bots/quant/CLAIMS.md:17` 有 B08 认领行。

未取的证据（如实记录）：Polymarket 历史平局成交价/盘口（公开接口无）、逐场 Polymarket 结算记录、任何关于 draw bias 的论文（本稿**未引用**任何文献，只用自己算的 CSV 基准率）。

---

## glm-5.3 事实核查报告

# Fact-check report — B08 (足球三向盘平局基准率检验)

## Refetch results (17 fetches: 8 CSVs, 5 Gamma, 1 CLOB, 1 docs, 2 event lists)

- **football-data CSVs (8 files)**: all 381 lines (=380 matches), byte sizes identical to log. **Every self-computed stat reproduces exactly**: E0 0.18–0.22 n=238/qD 0.2037/draw 0.2479/ROI +15.09%; E0 0.22–0.26 n=513/−7.17%; E0 0.26–0.30 n=548/−8.94%; I1 184/0.1848/−13.78%, 322/−8.61%, 696/+3.56%; combined 422/+2.50%, 835/−7.72%, 0.15–0.30 n=2675 (=1409+1266); overall 0.2408/0.2757/0.2582 (N=1520/1520/3040); date ranges; 380/282d=9.4/wk, 380/274d=9.7/wk. All VERIFIED.
- **`epl-liv-ars-2026-11-01-draw`**: bid 0.25/ask 0.27/spread 0.02/outcomePrices ["0.26","0.74"]/tick 0.01/endDate/feeSchedule{rate 0.05, rebate 0.15} all VERIFIED; liquidity now 3465.52 vs cited 3469.4498 — time-varying (timestamped), OK.
- **`sea-ata-par-2026-11-02-draw`**: 0.09/0.30/0.21, orderMinSize 5, endDate, rate 0.05 — all VERIFIED.
- **Rule text**: all six quotes verbatim VERIFIED (90-minute clause; postponed; canceled→"Yes" for draw and →"No" for home-win market — both re-fetched; official-stats→Flashscore→Sofascore→consensus + 2h; "Revisions…not accounted"; "resolve 50-50, or to 'Draw' where applicable").
- **Event structure**: sea three Yes 0.66/0.195/0.17 (sum 1.025) ✓; epl-new-eve 3×0.5/0.5 (sum 1.5) ✓; negRisk=true ✓; tags `sports,games,soccer,premier-league,EPL` ✓; Newcastle question ✓.
- **CLOB prices-history**: 6 points, first t=1792454444 p=0.315, rest 0.195 — VERIFIED (last timestamp drifts, trivial).
- **docs/trading/fees**: formula, "Makers are never charged fees. Only takers pay fees.", Sports 0.05/0/15%, Crypto 0.07, Finance 0.04, Geopolitics 0, Combos 0.05 — all VERIFIED.
- **600-event sample**: page-1 recount gives 17 three-way slugs (worker: 16); date filter confirmed non-functional (11-01 events under max=10-26). Full 111/600 count not re-verifiable within fetch cap, but entry explicitly hedges it ("总数未查到"). Arithmetic 111/13×7≈60 ✓.

## Problems

1. **`id: quant-XXX`** — placeholder violates GUIDE §7 (id must match filename, e.g. `quant-008`). Fix before commit.
2. 门槛自查 #5 says combined net "−0.06%" but 成本与容量 gives −0.0006 USDC/份 ≈ **−0.3% of 0.20 cost** (−0.06% is per-$1 notional). Basis slip; relabel.
3. Log item 5 (`events?slug=` returned `[]`) not reproducible — API returned the event fine; harmless since 出处 doesn't cite it, but note it.

## Compliance

Front-matter values otherwise valid (market/pm_category/kind/category S/return_type/status/confidence/name_zh ≤18字); no third-party self-reported results (all 自算 with formula, no papers cited — nothing needs 来源自报 tag); fee formula applied correctly incl. per-market feeSchedule; honest 自查 (admits gate 5 fails, opposite signs, no backtest claimed, `observed_net_return=null`); all fetches keyless/free; no trading. **Duplication**: distinct from KNOWN V-V2-poly-longshot / A-A3/A-A5-poly-* and dot-009 (key variable = draw base-rate bucket vs ask); dot's C12 is an unproduced claim only; quant CLAIMS.md B08 line present. No conflict.

VERDICT: FIX — every number and quote verified against sources, but the `id: quant-XXX` placeholder (and one %-basis slip) must be corrected before submission; content itself is fabrication-free.
GATES_PASSING: 4/7
