# quant-008 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

抓取方式：`curl -sL --max-time 25~30`，全部 GET，除 Hyperliquid `/info`（官方接口只接受 POST body，无鉴权、无密钥、无账户，仍是公开只读）。除 CoinGecko 用 `-w 'HTTP:%{http_code}'` 记录了状态行外，其余只用 curl 退出码 0 + 返回体能否解析来判断成功；**未逐条记录 HTTP 状态行**，这是本日志的已知不足。

| # | URL | 结果 | 取用的原文片段 / 数字 |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/public-search?q=FDV&limit_per_type=20` | 退出码 0，有效 JSON | `"slug":"papertrade-fdv-above-one-day-after-launch"`；规则原文 `The FDV will be determined using the total token supply multiplied by the token price.` / `"1 day after launch" is defined as 4:00 PM ET on the calendar day following launch.` / `The resolution source for this market is the most liquid price source available.` / `December 31, 2027, 11:59 PM ET`；`liquidity:184039.1655`、`volume:282854.88727` |
| 2 | `https://gamma-api.polymarket.com/markets?closed=false&limit=5&order=volume24hr&ascending=false` | 退出码 0，有效 JSON | 仅用于确认 Gamma markets 端点可用；**未在条目中引用任何数字** |
| 3 | `POST https://api.hyperliquid.xyz/info` body `{"type":"metaAndAssetCtxs"}` | 退出码 0，71978 字节 | `n_universe=234`；universe 条目字段只有 `szDecimals/maxLeverage/marginTableId/name`（无 hyperp 标志）；`LIT markPx=3.1991 dayNtlVlm=11255511.5961000081`；`MEGA 0.043709`、`MON 0.021201`、`MET 0.3407`；ctx 字段 `funding/openInterest/prevDayPx/dayNtlVlm/premium/oraclePx/markPx/midPx/impactPxs/dayBaseVlm` |
| 4 | `POST https://api.hyperliquid.xyz/info` body `{"type":"perpDexs"}` | 退出码 0 | 10 个 HIP-3 dex：`xyz, flx(Felix Exchange), vntl(Ventuals), hyna(HyENA), km(Markets by Kinetiq), abcd(ABCDEx), cash(dreamcash), para(Paragon), mkts, io(EntropyIO)`；`hyna` 含 `hyna:LIGHTER`、`hyna:BASED` |
| 5 | `https://gamma-api.polymarket.com/public-search?q=one%20day%20after%20launch&limit_per_type=20` | 退出码 0 | 20 个同模板事件 slug（`papertrade` 8 档 282854.88727、`predictfun` 11 档 7094078.5254110005、`opensea` 8 档 6917874.490895、`allox` 6 档 7492.984083 等） |
| 6 | `https://gamma-api.polymarket.com/public-search?q=FDV%20above%20one%20day%20after%20launch&limit_per_type=50` | 退出码 0 | `pagination={"hasMore": true, "totalResults": 149}`；`n_events=50`，`n_markets=428`；前 50 条中 46 条为本模板；`closed=False` 44 条；`closed=True` 6 条：`onefootball-club`(2026-03-27, vol 429321)、`fuse-energy`(2026-03-31, vol 0)、`edgex`(2025-11-05, vol 15216729)、`zama`(2025-11-19, vol 5919140)、`usdai`(2025-11-18, vol 5556947)、`lighter`(2025-12-29, vol 5357897)；creationDate 最早 `2025-09-30`，最晚 `2026-10-06` |
| 7 | `https://hyperliquid.gitbook.io/hyperliquid-docs/trading/hyperps` | 退出码 0，414153 字节 HTML → 去标签 | `Hyperps (Hyperliquid-only perps) trade like vanilla perpetual contracts, but do not require an underlying spot or index oracle price.` / `shortly after when ABC/USDT is listed on Binance, OKX, or Bybit spot trading, ABC-USD will convert to a normal ABC-USD perp.` / `The mark price of hyperps are capped at 3x the 8-hour mark price EMA.` / `mark price capped to 1.5x the median external perp price` / `oracle price is also restricted to be at most 4 times the one month average mark price` / `Last updated 2 months ago` |
| 8 | `https://gamma-api.polymarket.com/events?slug=metamask-fdv-above-one-day-after-launch` | 退出码 0 | `closed=false`、`volume=3357165.6675400003`、`endDate=2027-01-01T05:00:00Z`；8 档 `outcomePrices`：`$100M=0.045`、`$300M=0.04`、`$500M=0.041`、`$700M=0.04`、`$1B=0.045`、`$2B=0.0265`、`$3B=0.019`、`$4B=0.0185`；每档 `feeSchedule={"exponent":1,"rate":0.07,"takerOnly":true,"rebateRate":0.2}`、`makerBaseFee=1000`、`takerBaseFee=1000`、`feesEnabled=true`、`feeType="crypto_fees_v2"` |
| 9 | `https://gamma-api.polymarket.com/events?slug=edgex-fdv-above-one-day-after-launch` | 退出码 0 | 11 档全部 `closed=true`、`umaResolutionStatus=resolved`；`>$500M`=["1","0"]、`>$600M`=["1","0"]、`>$700M`=["0","1"] → 落在 (600M, 700M]；`feesEnabled=False`（已结算市场字段） |
| 10 | `https://gamma-api.polymarket.com/events?slug=lighter-fdv-above-one-day-after-launch` | 退出码 0 | 6 档：`>$1B`=1、`>$2B`=1、`>$3B`=0、`>$4B`=0、`>$5B`=0、`>$6B`=0 → 落在 (2B, 3B]；`volume=5357897` |
| 11 | `https://gamma-api.polymarket.com/events?slug=zama-fdv-above-one-day-after-launch` | 退出码 0 | 9 档：`>$300M`=1、`>$400M`=0 → 落在 (300M, 400M] |
| 12 | `https://gamma-api.polymarket.com/events?slug=usdai-fdv-above-one-day-after-launch` | 退出码 0 | 14 档：`>$1B`=1、`>$2B`=0 → 落在 (1B, 2B] |
| 13 | `POST https://api.hyperliquid.xyz/info` body `{"type":"meta","dex":"vntl"/"hyna"/"para"/"flx"}` | 退出码 0，4 次 | `vntl` 15 个（SPACEX/OPENAI/ANTHROPIC/…，非代币）；`hyna` 25 个含 `LIGHTER/BASED`；`para` 39 个股票/指数；`flx` 16 个股票/商品 → 只有 `hyna:LIGHTER` 与 46 个事件代币相关 |
| 14 | `POST https://api.hyperliquid.xyz/info` body `{"type":"spotMeta"}` | 退出码 0 | `n_spot_tokens=508`；`LIT`、`MEGA`、`CHIP`、`CASHCAT`、`PONS`、`USELESS`、`MET` 均不在现货代币名列表；`MON`、`STABLE`、`HYPE` 在 → 只作为「可能仍是 hyperp」的间接线索，条目中明确写「不下结论」 |
| 15 | `https://clob.polymarket.com/book?token_id=<Metamask $100M YES>` | 退出码 0 | `bestBid 0.04 / bestAsk 0.05`，`n_bids=4, n_asks=24` |
| 16 | `https://clob.polymarket.com/book?token_id=<Metamask $700M YES>` | 退出码 0 | `bestBid 0.034 / bestAsk 0.046`，`n_bids=23, n_asks=46` |
| 17 | `https://clob.polymarket.com/book?token_id=<Metamask $1B YES>` | 退出码 0 | `bestBid 0.04 / bestAsk 0.05`，`n_bids=4, n_asks=20` |
| 18 | `https://api.coingecko.com/api/v3/coins/lighter?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false` | **HTTP:200** | `"name":"Lighter","symbol":"lit"`；`total_supply=1000000000.0`、`circulating_supply=250000000.0`、`current_price.usd=3.19`、`fully_diluted_valuation.usd=3192043356`、`market_cap.usd=798010839`、`last_updated=2026-10-20T04:01:53.000Z` |
| 19 | `POST https://api.hyperliquid.xyz/info` body `{"type":"meta","dex":"km"}` | 退出码 0 | 23 个股票/指数资产（US500/NVDA/…），无代币 → 未引用 |

我自己做的算术（条目中标注了公式）：
- `3.1991 × 1_000_000_000 = 3,199,100,000`；`3.1991 / 3.192043356 − 1 = 0.2212%`（对比 CoinGecko FDV）。
- 费率占投入 `0.07 × (1 − p)`：p=0.045 → 6.685%；p=0.60 → 2.80%；每份费 `0.07×0.045×0.955=0.0030083`、`0.07×0.6×0.4=0.0168`。
- 半价差占投入 `0.005/0.045 = 11.11%`；两腿吃单费 `0.0030083 + 0.0030 ≈ 0.006`/份 vs 中间价错位 0.005。
- 事件频率 `46 / 371 × 30.44 = 3.77` 个/月（2025-09-30 → 2026-10-06 共 371 天）。
- 锁仓年化 `3% × 365/73 = 15.0%`；`3% × 365/438 = 2.5%`。

未查到 / 未做：
- 46 个事件代币在 HL（主盘 + 214 个 HIP-3 资产）中的盘前 perp 匹配：主盘命中 0、HIP-3 命中 1（`hyna:LIGHTER`，事件已结算）→ 当前无可交易配对。
- LIT 上线当日（2025-12-29 前后）的历史价格来源未抓到，故「外部价格能否复现 (2B,3B] 结算」这一步**未做**。
- 历史 CLOB 盘口、逐事件成交、`public-search` 的 149 条全集（未翻页）均未取得。
- 无回测：`backtest_count=0`、`observed_net_return=null`。

---

## glm-5.3 事实核查报告

# Fact-check report — B05.md (quant, FDV ladder off pre-launch perps)

**Fetched 20 URLs (all HTTP 200). Core numbers verify:**

- MetaMask 8 rungs outcomePrices (0.045/0.04/0.041/0.04/0.045/0.0265/0.019/0.0185), `feeSchedule` (rate 0.07, takerOnly, rebateRate 0.2, maker/takerBaseFee 1000, crypto_fees_v2), `endDate 2027-01-01T05:00:00Z` — **VERIFIED** exactly.
- CLOB books for the 3 rung YES tokens: 0.04/0.05, 0.034/0.046, 0.04/0.05, n_bids/n_asks ≈ match — **VERIFIED**.
- Settled brackets edgex (600M,700M], lighter (2B,3B], zama (300M,400M], usdai (1B,2B], all `umaResolutionStatus=resolved`, rung counts 11/6/9/14, volumes — **VERIFIED**.
- public-search `totalResults=149, hasMore=true`, 6 closed events w/ exact slugs+volumes, earliest creationDate 2025-09-30 — **VERIFIED**.
- CoinGecko lighter `total_supply=1e9`, circ 2.5e8; Hyperliquid n_universe=234 with only name/szDecimals/maxLeverage/marginTableId, perpDexs 10 HIP-3 dexes, hyna=25 incl. `hyna:LIGHTER`, LIT not in spot (508 tokens), dex sizes vntl15/para39/flx16/km23; hyperps doc quotes (3× 8h EMA, 1.5× median, 4× 1-mo, vanilla conversion) — **VERIFIED**. Arithmetic (0.22% FDV gap, 6.69%/2.80% fee share, 11.1% half-spread, 73/438 days, 15.0%/2.5% annualized, 3.77/mo) all check out.

**Problems:**

1. **MISMATCH — rule quotes attributed to a "metamask/papertrade 同一模板":** metamask's market description does **not** contain 「The FDV will be determined using the total token supply multiplied by the token price.」nor 「Stablecoins, memecoins, LSTs...」nor 「Only an official token launched by...」(those are only in papertrade/zama/usdai); metamask says 「actively, publicly transferable and tradable」and 「greater than the value specified in the title」. Fix: attribute per-slug, drop "同一模板".
2. **MISMATCH — deadline year:** metamask (also zama/usdai/edgex) says 「December 31, **2026**, 11:59 PM ET」, not 2027 (2027 is papertrade only). Fix the 「没上线怎么办」quote.
3. **Invalid `id: quant-XXX`** — GUIDE §7 requires id matching filename (e.g. quant-005). Fix before commit.
4. Time-varying (worker gave timestamps — acceptable): CG price 3.19→3.20/FDV 3.192B→3.196B (5 min later); LIT markPx 3.1991→3.1861; papertrade liquidity 184039→181734 (volume matches **exactly**); "46 of 50 template events"→now 50/50, creationDate max 2026-10-06→10-15 (new events; 3.77/mo now understated).
5. Minor: 证据3 「按市场自身概率这组价差只值 0.005」— mids imply 0.045−0.045=0.000; the 0.005 is the 1B-vs-700M misalignment. Reword.

**Rule compliance:** front-matter otherwise valid (category S, return_type direction, status 草稿, confidence 低); fee formula per GUIDE §8 correct (crypto 0.07 ✓); 门槛自查 honest (admits fail #5/#6, flags #4); explicitly `backtest_count=0`, no backtest claims; all data free/keyless (HL POST is public read-only, disclosed). **Duplication:** distinct from dot-007 (internal ladder monotonicity arb — B05 only cites the violation and concludes untradable), dot-018 (options), known A-A3-poly-cross-market/V-V2; claimed in quant CLAIMS.md as B05. Not a duplicate.

**VERDICT: FIX** — every quantitative claim and API field verifies honestly, but the rule-text attribution errors (missing clauses on metamask, 2026-vs-2027 deadline) and the placeholder id must be corrected before submission; substance remains a 待选区-grade idea that honestly fails gates 5–6.

GATES_PASSING: 4/7
