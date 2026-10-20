# quant-009 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

抓取均在 2026-10-20 本会话内用 curl（无密钥、未登录）完成，工作目录 `/workspace/agent-tools/quant-batch1/work_B06`。

1. `https://gamma-api.polymarket.com/events?slug=will-xrp-be-listed-on-binance-by-june-30` → 200，返回 `[]`（该 slug 不存在，仅用于试接口，未引用）。
2. `https://gamma-api.polymarket.com/public-search?q=listed%20on%20binance&limit_per_type=10` → 200，10 个 event；含 `hyperliquid-listed-on-binance-by`、`penguin-listed-on-binance-by-march-31`。
3. `https://gamma-api.polymarket.com/public-search?q=listed%20on%20coinbase&limit_per_type=20` → 200，20 个 event；含 `will-coinbase-list-hype-in-2025`、`yzy-listed-on-coinbase-in-2025`、`hyperliquid-listed-on-coinbase-before-2027`、`next-coin-on-coinbase`(10 markets)、`first-coin-listed-before-2025`(9 markets)。
4. `https://gamma-api.polymarket.com/events?slug=will-coinbase-list-hype-in-2025` → 200；`outcomes=["Yes","No"]`、`outcomePrices=["0","1"]`、`endDate=2025-12-31T23:59:59.999Z`、`fee/feeSchedule/takerBaseFee=null`、description 原文见正文「规则」节。
5. `https://gamma-api.polymarket.com/events?slug=hyperliquid-listed-on-coinbase-before-2027` → 200；`outcomePrices=["1","0"]`、`volume=47799.358913`、deadline "December 31, 2026, 11:59 PM ET"。
6. `https://gamma-api.polymarket.com/markets?slug=will-coinbase-list-hype-in-2025&closed=true` → 200，1 条；`closedTime=2026-01-01 09:29:27+00`、`umaResolutionStatus=resolved`、`volumeNum=239725.347892`、`feeSchedule=null` → 因此费用改用 GUIDE 表 crypto 0.07。
7. 四个 public-search（各 `limit_per_type=50`）→ 均 200，events 数分别 18 / 26 / 4 / 27；并集 53；标题匹配 `listed on (binance|coinbase|robinhood)` 24 个 event / 40 market，全部 closed；单市场 event 21 个，Yes 3 个（`wif-listed-on-coinbase-or-binance-in-march`、`wif-spot-listed-on-coinbase-in-2024`、`hyperliquid-listed-on-coinbase-before-2027`）→ 3/21=14.29%；按代币合并 12 簇，含 Yes 的簇 2 个（WIF、HYPE）→ 2/12=16.67%。多选事件：`hyperliquid-listed-on-binance-by` 2 markets/1 Yes、`next-coin-listed-on-binance` 8/1、`first-coin-listed-before-2025` 9/1。
8. `https://gamma-api.polymarket.com/public-search?q=upbit&limit_per_type=20` → 200，7 个 event 全是 `*-listed-on-within-30-days-of-tge` 型，无 upbit 专属上币 event（正文据此写「未查到」）。
9. `https://www.coinbase.com/blog/listing` → **403**，正文 `<title>Just a moment...</title>`（Cloudflare）；`https://www.coinbase.com/blog/rss` → 403 同上；`https://www.coinbase.com/rss/blog?category=listing` → 404 `<title>404 Page Not Found | Coinbase</title>`。
10. `https://archive.org/wayback/available?url=www.coinbase.com/blog/listing` → 200，`{"archived_snapshots": {}}`；`https://web.archive.org/web/2025id_/https://www.coinbase.com/blog/listing` → 000（未取得）；`http://web.archive.org/cdx/search/cdx?...` → 000（未取得）。
11. `https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20` → 200，28179 bytes；`catalogs`：`48 New Cryptocurrency Listing total 2283`、`49 Latest Binance News total 4455`、`161 Delisting total 441`；articles 中 `Binance Will List Hyperliquid (HYPE) with Seed Tag Applied` 的 `releaseDate` 解析为 `2026-09-24 07:30`（UTC）。
12. `https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=d49de208bb6d4a26b02677d7c3d89b5d` → 200，61153 bytes；正文文本含 "Binance will list Hyperliquid (HYPE) and open trading for the following spot trading pairs at 2026-09-24 11:00 (UTC)"、"Withdrawals will open at 2026-09-25 11:00 (UTC)"。→ 07:30→11:00 = 3h30m（我的算术，单样本）。
13. `https://clob.polymarket.com/prices-history?market=<HYPE-2025 YES tokenId>&startTs=1750000000&endTs=1767225600&fidelity=1440` → **400** `{"error":"invalid filters: 'startTs' and 'endTs' interval is too long"}`；改 31 天（1764547200–1767225600）→ 400；改 6 天（1766707200–1767225600，fidelity=60）→ **200**，3924 bytes，首点 `{"t":1766707211,"p":0.011}`；改 1 天（1767139200–1767225600）→ **200**，677 bytes，首点 `{"t":1767139214,"p":0.002}`。
14. 未做的部分：Coinbase roadmap 与 @CoinbaseAssets 原文、Upbit 公告、任何盈亏回测、L2 盘口历史、24 个 event 的逐个价格拼接。正文已相应写「未查到」/「未验证」/`backtest_count=0`。

---

## glm-5.3 事实核查报告

# Fact-check report — B06.md (quant, listing-deadline base-rate pricing)

## Re-fetch results (16 fetches, all reproduced today)

**VERIFIED — exact matches:** query event counts 18/26/4/27, union 53; 24 matched events/40 markets/all closed; 21 singles with exactly the 3 claimed Yes (`wif-…-in-march`, `wif-spot-…-2024`, `hyperliquid-…-before-2027`) → 3/21=14.29%; 12 clusters/2 Yes → 16.67%; multi events 2/1, 8/1, 9/1 Yes; all six cited volumes to the cent (239725.347892, 47799.358913, 224358.0798…, 14832.369719, 278645.142524, 2009956.351265); rule-text quotes (spot wording, ET 23:59, resolution-source sentence, PENGUIN contract address, "Robinhood U.S.", 2026 deadline); `closedTime=2026-01-01 09:29:27+00`, `umaResolutionStatus=resolved`, fee fields null; CLOB first points t=1766707211/p=0.011 and t=1767139214/p=0.002, 31-day window → 400 "interval is too long"; Coinbase 403/403/404, wayback `{"archived_snapshots": {}}`; upbit query 7 `*-within-30-days-of-tge` events; XRP slug → `[]`; Binance catalogs 48/49/161 = 2283/4455/441, HYPE releaseDate 2026-09-24 07:30:38 UTC, open-trading 11:00 UTC, withdrawals 09-25 11:00, RWUSD 10-13 03:30, byte sizes 28179/61153. Fee math per GUIDE §8 (1.47/0.63 USDC, 32.5% breakeven) all correct.

## Problems

1. **MISMATCH (only real numeric error)** — 证据/两周节：「`next-coin-on-robinhood-3-7-2025`、`next-coin-on-robinhood-03132025`…volume 分别约 2.0M/0.99M」。Actual volumes: **98,601.89 (~0.099M)** and **246,413.65 (~0.25M)** — off ~10×. The 2.0M/0.99M belong to `first-coin-listed-before-2025` (2,009,956) and `next-coin-listed-on-binance` (986,718). Fix: correct slug→volume pairing.
2. **Placeholder id** — front matter `id: quant-XXX`; GUIDE §7 requires id match filename (e.g. `quant-006`) before commit.
3. **Internal inconsistency** — 进场 rule uses half-spread 0.005 (`p_model − ask ≥ 0.005 + …`) while 成本 assumes 1¢/份. Fix: align (use 0.01 to match the conservative cost math).
4. Trivial: source uses curly quotes ("Yes"); entry normalizes to straight — acceptable, not flagged.

## Rule compliance

Front matter complete, all values legal (polymarket/crypto/new/S/direction/草稿/低)；fee formula matches GUIDE §8 with feeSchedule=null justification; 门槛自查 honest (admits backtest_count=0, observed_net_return=null, Coinbase 403, 12 clusters < 30); no fabricated backtests; no keys/paid data; 来源自报 n/a (self-computed from raw data, correctly labeled). Duplication: none — KNOWN's E-E1-listing-chase/short/upbit-pump-short are spot/perp; A-A3-poly-cross-market is cross-market arb; dot's C10/C35 adjacent but different variables; claimed in bots/quant/CLAIMS.md; REVIEWS.csv empty.

VERDICT: FIX — a single misattributed volume pair (real numbers, wrong slugs) plus placeholder id/inconsistent spread constant must be corrected, but every other number, quote, and honest-gap claim reproduced exactly.
GATES_PASSING: 5/7
