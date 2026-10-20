# quant-009 历史可成交价回测（data-api 成交 + 走前基准率）

访问日期：**2026-10-20**。分支 `quant-review/q009-hist`。脚本 `q009_hist.py`。本文数字全部来自同目录 `run_output.txt`；逐市场明细见 `markets.csv`。

## 判定

**INSUFFICIENT（样本不足）**，且按条目字面“少于 30 个独立事件即失败”的标准同时记 **FAIL**。

- 枚举出 **37 个候选 event / 95 个 market（按 conditionId 去重）**，合并为 **27 个独立簇**（同 token+venue 的不同截止日算一簇；`next coin` 多选 event 按 event 算 1 个结果）。**27 < 30**。
- 固定进场时点 `endDate − 7d` 下，只有 **17/95 个 market 有窗口内成交、来自 10 个簇**；其中 **5 个簇触发 11 笔**（YES 10、NO 1）。
- 触发子样本每簇中位净损益 **−0.019237/份**，均值 **+0.005535/份**（被 PNUT 的 +0.120187 拉起；10000 次簇 bootstrap 95% CI `[−0.026675, +0.063828]`），命中率 **1/11 = 0.091**，合计 **−0.163467** / 投入 **1.137606** = 每美元 **−0.143694**。
- 敏感性 `endDate − 3d`：触发 7 笔 / 2 个簇，中位与均值均 **−0.013987**，命中率 **0/7**，每美元 **−1.069069**。
- 走前模型 Brier **0.003467** vs 市场 **0.001712**（差 **+0.001755**）；log loss **0.058913** vs **0.029309**（差 **+0.029603**）。17 个有价市场全部结算 No，模型有 15 个比市场差（符号检验 p=0.0023）。

## 数据来源

全部免费、免密钥，2026-10-20 抓取，原始文件缓存在 `_cache/`（已 gitignore）。

- Gamma `public-search`：`https://gamma-api.polymarket.com/public-search?q=<query>&limit_per_type=50`。固定 22 条查询（`listed on binance/coinbase/robinhood/upbit`、`binance list`、`coinbase list`、`next coin on coinbase/robinhood`、`spot listed`、`will be listed on`、`listed for trading` 等），按 `pagination.hasMore` 翻页；并集 **75 个 event**。
- Gamma 事件字段（`event.closed`、`market.conditionId`、`startDate`、`endDate`、`closedTime`、`outcomes`、`outcomePrices`、`clobTokenIds`）直接取自 public-search 返回。
- data-api 真实成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N&start=<ts>&end=<ts>`；`start/end` 为 Unix 秒，只取进场窗口，返回 `side/price/size/timestamp/outcome`，`outcome="No"` 时 YES 价 = 1 − price。
- 费率：GUIDE 第 8 节 crypto **0.07**；示例市场 `feeSchedule=null`，与 entry 一致。

## 口径（脚本头部预先写死，先于看盈亏）

- **纳入**：`closed=true` 的二元上币截止日市场，问题/标题含 `list/listed/listing` 且含 Binance/Coinbase/Robinhood/Upbit 之一；`endDate` 在过去（提前结算的市场即使 `endDate` 在未来也纳入枚举）。
- **排除**：`within 30 days of TGE`（相对 TGE 的模板，`endDate` 只是占位）、`announces ... listing` / `listing announcement`（公告≠现货上线）、`another Pump.fun coin`（无单一 token）、`Binance or Bybit` 及 Hyperliquid/Bybit/Kraken/OKX 等条目范围外场所、`which exchange`/代币化股票/政治名单误命中。
- **独立结果**：一个 token-venue-deadline = 一个 market 结果；同 token+venue 不同截止日合并为一簇；`next coin` / `first coin` 多选 event 按 event 算 1 个结果（簇内多笔触发取均值，等份）。
- **模型**：`p_model = 1 − exp(−λ·T)`，进场时 `T = 7` 天（敏感性 `T = 3`）。`λ` 只用 `closedTime < 进场时刻` 的市场：`λ = #Yes / Σ exposure_days`，`exposure_days = min(closedTime, endDate) − startDate`。最低历史：**≥8 个已结算 token-venue 市场、≥1 个 Yes、累计暴露 ≥365 天**；不满足则跳过。
- **公告分支**：`p_model=1 when already announced` **未实现**。Coinbase/Robinhood/Upbit 没有免密钥、可机读的历史公告时间；只对 Binance 子集用 CMS 会变成另一条未预先声明的规则。
- **进场价**：`[endDate−9d, endDate−7d]` 内最后一笔 data-api 成交换算成 YES 价；`ask = trade + 0.01`、`bid = trade − 0.01`。
- **触发**：`p_model − ask ≥ 0.01 + p_model(1−p_model)·0.07` 买 YES；`bid − p_model ≥` 同式买 NO；两边都满足取边际大者。费 `= 0.07 × 成交价 × (1−成交价)`；持到 Gamma 结算，不提前平仓。

## 关键结果（`run_output.txt` 原样）

```
candidate events: 37  markets (deduped by conditionId): 95
  binance              events= 8 markets=15
  coinbase             events=20 markets=43
  robinhood            events= 4 markets=32
  upbit                events= 0 markets= 0
  binance+coinbase     events= 5 markets= 5
date span (endDate): 2021-11-18 .. 2027-01-01
independent clusters (token+venue; next/first-coin event = 1): 27

markets with valid walk-forward lambda: 79/95
skipped for <8 resolved markets / <1 Yes / <365d exposure: 16
lambda/day: min=0.00506713 median=0.00549687 max=0.01017263
unpriced breakdown: no walk-forward lambda=16, no fill in 2d window=62 (of which already resolved before entry=62), no resolution price=0

-- primary_7d
   markets priced=17/95  clusters priced=10
   triggered trades=11  clusters/events=5  YES=10 NO=1
   median net/share=-0.019237  mean net/share=+0.005535
   cluster bootstrap 95% CI of mean: [-0.026675, +0.063828]
   hit rate=1/11 = 0.091
   total net=-0.163467 on staked=1.137606 -> per $ staked=-0.143694
-- sensitivity_3d
   markets priced=16/95  clusters priced=10
   triggered trades=7  clusters/events=2  YES=7 NO=0
   median net/share=-0.013987  mean net/share=-0.013987
   cluster bootstrap 95% CI of mean: [-0.014076, -0.013898]
   hit rate=0/7 = 0.000
   total net=-0.098354 on staked=0.092000 -> per $ staked=-1.069069

-- primary_7d: n=17 market-YES=0
   Brier  model=0.003467  market=0.001712  diff=+0.001755
   LogLoss model=0.058913  market=0.029309  diff=+0.029603
   model lower Brier on 2, market lower on 15, ties 0, sign p=0.0023
   mean |p_model - market|=0.038057
```

触发簇明细：

```
DEGEN|binance                  1 笔  mean_net=-0.019237
FARTCOIN|coinbase              1 笔  mean_net=-0.022851
PNUT|coinbase                  1 笔  mean_net=+0.120187
YZY|binance+coinbase           1 笔  mean_net=-0.018567
next-coin-listed-on-binance    7 笔  mean_net=-0.031857  pnl=-0.222998
```

## 对 gate 5 / gate 6 的含义

- **gate 6（两周内可检验）**：data-api 确实能取到已关闭市场的真实成交，方法可行；但按条目固定的 `endDate − 7d` 进场，**95 个 market 里有 62 个在进场前就已经结算**（多为提前结算的 Yes/No 或 `next coin` 已分出胜负），只剩 17 个有窗口内成交、10 个独立簇。**即使把 Gamma 能枚举的该模板全部拉进来，也凑不到 30 个“进场时仍活着”的独立簇**。因此 gate 6 不能因本轮升级；要继续只能前向记录，或重新设计进场时点（例如市场创建后固定天数/公告事件驱动），那不是本条已冻结的规则。
- **gate 5（扣成本后够用）**：可用子样本在费+1¢ 半价差后仍为负，且走前基准率的 Brier/log loss 都差于市场末笔成交价，没有证据支持“模型稳定领先 2.5pp”。按条目自己的标准，这一项仍不通过。
- **不修改** `bots/quant/entries/quant-009-*.md`、INDEX、LOG、CLAIMS 等文件；本目录只提供历史证据。

## 局限

- **样本小且集中**：触发只有 5 个簇、11 笔；`next-coin-listed-on-binance` 一个 event 占 7 笔（互斥选项，相关性高），bootstrap CI 很宽。
- **提前结算**：固定 `endDate−7d` 对提前结算市场没有进场机会；这不是“没成交”，而是市场已关闭，脚本单独计数。
- **成交价不是订单簿**：用窗口内最后一笔成交 + 1¢ 近似 ask，真实盘口可能更差；没有 L2 历史。
- **λ 为常数风险率**：用 `#Yes / 暴露天数` 估计，把多选 event 的多个互斥选项也计入暴露；可能高估/低估真实到达率。最低历史门槛（8 个市场、365 天）是预先写死的，不是调参结果。
- **公告分支未实现**：没有全场所的免密钥历史公告时间，所有交易只用基准率分支。
- **枚举不保证全量**：Gamma public-search 有返回上限；22 条查询并集 75 个 event，仍可能漏掉未被索引的 slug。
- **结算口径**：用 Gamma `outcomePrices`；ENS 的 0.9999988 按 >0.5 记为 Yes。没有处理 UMA 争议或 50-50。
- **费用**：固定 0.07，未计 maker 返佣，也未建模滑点与资金占用年化。

## 复现

```bash
cd bots/quant/notes/q009-hist
python3 q009_hist.py > run_output.txt
```

脚本优先读 `_cache/`。本次从缓存连续重跑两次，`run_output.txt` 与 `markets.csv` 均**逐字节一致**（`diff` 退出码 0，`markets.csv` sha256 `e11b63405ba1e503e58b30efa55097351a786c12ca4f274d2bcfc97c4e37d324`）。

Lint：`python3 tools/check.py lint` 仍因仓库既有 `bots/muse/entries/muse-700-*.md`、`muse-701-*.md` 缺字段而失败（`KeyError: 'id'`），与本次改动无关；原始输出见 `lint_output.txt`。
