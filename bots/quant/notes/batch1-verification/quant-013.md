# quant-013 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

抓取时间：2026-10-20（Coinbase 响应头 `date: Tue, 20 Oct 2026 04:01:47 GMT`）。全部为 keyless 公共 GET，未使用任何密钥、未登录、未交易、未付费。

1. `https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start=2026-09-01T00:00:00Z&end=2026-09-06T00:00:00Z`
   - 结果：HTTP/2 200，`content-type: application/json`。
   - 取用：`[[1788652800,79250,80564.24,79833.86,80339.13,2000.39186862],[1788566400,79458.74,...],[1788220800,76366.12,79195.32,78562.74,77398.69,7523.97854815]]` → 首行时间戳 1788652800 = 2026-09-06；收盘 80339.13、成交量 2000.39186862。数组顺序为新→旧，字段序为 `[time, low, high, open, close, volume]`。

2. `https://api.exchange.coinbase.com/products/USDT-USD/candles?granularity=86400&start=2026-08-01T00:00:00Z&end=2026-08-05T00:00:00Z`
   - 结果：HTTP/2 200。
   - 取用：`[[1785888000,0.99872,0.99925,0.9991,0.99897,36442192.25],...]` → 1785888000 = 2026-08-05，收盘 0.99897，量 36,442,192.25。

3. `https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-08.zip`
   - 结果：HTTP 200，size=2185，zip 内 `BTCUSDT-1d-2026-08.csv`，31 行。
   - 取用：首行 `1785542400000000,62887.88000000,63150.00000000,62275.00000000,62823.64000000,7563.08904000,...`；末行 `1788134400000000,77682.00000000,79250.00000000,77392.00000000,78581.29000000,15303.90602000,...,4354737,...` → 2026-08-01 开盘 62,887.88；2026-08-31 开盘 77,682.00、收盘 78,581.29、成交量 15,303.90602 BTC。

4. Binance 月度 zip 批量下载（脚本内循环，无异常输出即全部 200）：`https://data.binance.vision/data/spot/monthly/klines/{BTCUSDT|SOLUSDT}/1d/{SYM}-1d-{2025-08 … 2026-09}.zip`
   - 结果：14 个月 × 2 个合约全部成功（脚本对失败会打印 `miss`，未出现）；解析后 `BTCUSDT days 426 2025-08-01 2026-09-30`、`SOLUSDT days 426 2025-08-01 2026-09-30`。

5. Coinbase 分页拉取（脚本 `cb()`，两窗口各 ≤300 根）：
   - `.../BTC-USD/candles?...start=2025-08-01&end=2026-02-20` 与 `...start=2026-02-20&end=2026-10-20`
   - `.../USDT-USD/candles?...` 同上两窗口
   - 结果：均 200；`coinbase btc days 446 usdt days 446 2025-08-01 2026-10-20`。

6. 自算（脚本，仅用上列收盘价，无外部数字）：`p_t=(C_t/(B_t·U_t)−1)·10000`；`z_t` 用前 30 日 `pstdev`。
   - 输出：`premium bps: n=412 mean=-0.44 median=-0.39 sd=1.26 min=-3.54 max=3.86`
   - `episodes z>=1.0: 29`，起点列表 2025-09-30 … 2026-09-25。
   - `BTCUSDT episode-entry hold 3d net of 0.60%: n=29 mean=0.79% median=-0.41% hit=48%`；`SOLUSDT ... n=29 mean=1.43% median=-0.23% hit=48%`。
   - `BTCUSDT unconditional 3d net=-0.83% (n=409)`；`SOLUSDT unconditional 3d net=-0.81% (n=409)`。
   - `BTCUSDT long/flat z>=1 exit z<0, exec next open, cost0.30%/side: trades=39 equity=1.3269 (32.69%), mean/trade=1.42%, hit=54%, median=0.51%`；`SOLUSDT ... trades=39 equity=1.3025 (30.25%)`。
   - `buy&hold BTCUSDT window: -28.74%`（117342.1 → 83623.6）。
   - 敏感性：`th 1.5 episodes 20` → BTC 3d `mean=-0.49%`、SOL `mean=-1.30%`；`th 2.0 episodes 10` → BTC `mean=-0.01%`、SOL `mean=-1.63%`。

7. `https://export.arxiv.org/api/query?search_query=all:%22coinbase+premium%22&max_results=10`
   - 结果：HTTP 200（https）。返回内容只有 feed 级 `<title>arXiv Query: search_query=all:"coinbase premium"</title>`，**无 entry** → 0 条结果。
   - 注：同一查询的 http 版 `http://export.arxiv.org/...` 连接超时（curl 28），改用 https 成功。

8. `https://export.arxiv.org/api/query?search_query=abs:%22Coinbase%22+AND+abs:%22Bitcoin%22&max_results=10`
   - 结果：HTTP 200。标题：Deep Learning for Digital Asset Limit Order Books / Periodicity in Cryptocurrency Volatility and Liquidity / Modelling Bitcoin in Agda / Understanding Cryptocoins Trends Correlations / NeuCoin… / Bitcoin Mempool Linearization / The Loop-Gain Matrix… → 无溢价预测研究，引用为“未查到”。

9. `https://api.crossref.org/works?query.bibliographic=coinbase+premium+bitcoin&rows=8&select=title,DOI,issued,abstract`
   - 结果：HTTP 200。返回 8 条，例如 `10.1016/j.frl.2020.101505` "Kimchi premium and speculative trading in bitcoin"（2021-01，韩国溢价，**不是** Coinbase 溢价）、`10.2139/ssrn.6734402` "Issuing Into the Premium… MicroStrategy…"（与本题无关）、其余为新闻/无关条目 → 无 Coinbase 溢价预测研究。

10. `https://api.semanticscholar.org/graph/v1/paper/search?query=coinbase%20premium%20bitcoin&fields=title,year,abstract,externalIds,url&limit=8`
    - 结果：**HTTP 429**（限流），未取得任何内容，因此不作为证据来源。

11. `https://html.duckduckgo.com/html/?q=coinbase+premium+bitcoin+predictive+returns+study`
    - 结果：HTTP 200，size=34594。结果链接含 `crypto.news/what-is-the-coinbase-premium-index/`、`ainvest.com/news/coinbase-premium-doesn-measure-anymore-2606/`、`guavy.com/wire/...` 等。只打开并引用了 crypto.news 一条；ainvest/guavy 等**未打开，不引用**。

12. `https://crypto.news/what-is-the-coinbase-premium-index/`
    - 结果：HTTP 200，size=360731；署名 `By Olivia Stephanie Jul 6, 2026 at 11:22 AM UTC`。
    - 取用原文片段（逐字）：
      - "The magnitudes are tiny by design, usually hundredths of a percent, because arbitrage desks compress any persistent gap within minutes"
      - "A single positive print means nothing; a premium that holds positive for days or weeks means the American, regulated, dollar-funded side of the market keeps out-bidding the world"
      - "The 14-day streak in April was tradeable partly because it was still early in the indicator's mainstream fame; each subsequent cycle prices it faster."
      - "The index is not a buy or sell light; it is one witness in a lineup"
      - "When large wallets absorbed more than 270,000 BTC in two weeks while the premium stayed below zero" / "the premium prints -0.02%" / "shrinks toward -0.005%"
      - 失效模式段："institutional flows increasingly route through over-the-counter desks that never touch the public order book at all" / "Large arbitrage flows around ETF creation windows, USDT price drift, exchange outages, and even fee changes can push the number around without any change in real demand."
    - 定性：媒体科普，**来源自报，未核实**；该文未给出任何量化命中率、样本期或回测成本假设，因此不能当“已发表的可预测性证据”。

13. 未做但已声明：正式历史回测（2018→今）未跑；2025-08 之前的 Binance 月度 zip 与 Coinbase 早期日线可用性未验证；未取任何盘口/逐秒数据。

---

## glm-5.3 事实核查报告

# Fact-check report — B10.md (Coinbase-vs-Binance premium as direction signal)

## Re-fetch results (13 fetches, 2026-10-20 same-day)

- **Coinbase BTC-USD candles URL**: VERIFIED — live first row `[1788652800,79250,80564.24,79833.86,80339.13,2000.39186862]` matches byte-for-byte; ts=2026-09-06; `[time,low,high,open,close,volume]`, new→old; a 446-day single request is rejected by the API, consistent with the 300-candle cap; 2025-08-01 availability confirmed.
- **Coinbase USDT-USD URL**: VERIFIED — `[[1785888000,0.99872,0.99925,0.9991,0.99897,36442192.25],...]` exact match, 2026-08-05 close 0.99897.
- **Binance BTCUSDT-1d-2026-08.zip**: VERIFIED — 2,185 bytes, 31 rows, first row open 62,887.88 (2026-08-01), last row 2026-08-31 open 77,682.00 / close 78,581.29 / vol 15,303.90602 BTC / 4,354,737 trades, all exact. SOLUSDT zip same format, VERIFIED.
- **crypto.news article**: VERIFIED — all quoted strings verbatim, incl. "usually hundredths of a percent", "A single positive print means nothing", "Read streaks, not prints.", "The 14-day streak in April…", "The index is not a buy or sell light", "270,000 BTC", "-0.02%", "-0.005%", "The signal decays with fame.", OTC/ETF-drift failure modes, byline "Olivia Stephanie Jul 6, 2026". Correctly labelled 来源自报，未核实.
- **arXiv `"coinbase premium"`**: VERIFIED — 0 entries. **Crossref**: VERIFIED (8 rows incl. Kimchi-premium FRL paper & MicroStrategy SSRN; none on Coinbase premium). **Semantic Scholar**: VERIFIED — HTTP 429 reproduced. **DDG**: VERIFIED (crypto.news/ainvest/guavy links present; size 34,933 vs logged 34,594 — time-varying, trivial).
- Self-computed stats (n=412, −0.39 bp median, 29 events, +32.69% etc.) not recomputed (fetch cap); arithmetic internally consistent (412 = 2025-08-15→09-30 count; 409=412−3; −28.74%=83,623.60/117,342.10; 2.1 events/月=29/13.5) and honestly hedged as in-sample.

## Problems (exact excerpts → fixes)

1. **MISMATCH (arXiv count)**: 证据 `"abs:\"Coinbase\" AND abs:\"Bitcoin\" 返回 10 条"` and 出处 `"HTTP 200，10 条标题，均与溢价预测无关"`; log item 8 says "10 条标题" yet lists only 7. Live re-fetch: `totalResults>7`, 7 entries. Fix: change 10→7 in both places (worker likely conflated `max_results=10` param with result count; conclusion unaffected).
2. **Front-matter**: `id: quant-XXX` placeholder violates GUIDE §7 ("和文件名一致，例如 grok-001"). Fix: `id: quant-010`, filename `quant-010-coinbase-premium-zscore.md`.
3. **name_zh** "Coinbase对币安溢价作BTC方向信号" ≈21 chars > 18-char limit (GUIDE §7). Fix: shorten, e.g. "Coinbase溢价z分数方向信号".
4. Minor: `category: S` debatable (signal is computed purely from prices; closer to T or `?`); log's DDG size differs (time-varying, no action).

## Compliance & duplication

来源自报 labels: correct throughout. Polymarket fee formula: N/A (crypto). Honest 门槛自查: exemplary — admits gate 5 fails by its own pre-registered median test, gates 4/6 uncertain, explicitly states the formal backtest was NOT run (`backtest_count=1` in-sample only). No keys, no paid data, no trading, files within limits. Duplication: no overlap with KNOWN.md (nearest: A-A3-kimchi, A-A3-cross-venue, S-S3-etf-flow — entry distinguishes: direction vs convergence, and defers gate 4 to reviewer); dot's 49 claims/entries contain no Coinbase-premium topic; quant CLAIMS.md shows B10 duly claimed.

VERDICT: FIX — all cited data, prices, and quotes verify exactly, but the arXiv "10 条" mismatch (actual 7) and the `quant-XXX`/overlong-name placeholders must be corrected before submission to avoid a fabrication ding.
GATES_PASSING: 6/7
