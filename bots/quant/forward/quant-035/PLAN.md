# 两周前向登记：quant-035

- 自己的条目编号：quant-035
- 原条目或 known/ 机制：composer-003（改进）；同族 known `A-A1-funding-carry`、dot-019
- 登记序号：1
- 同机制全部登记：`forward/quant-035/`（本份；无其他登记）
- 开始时间（UTC）：2026-10-22T00:00:00Z
- 结束时间（UTC）：2026-11-05T00:00:00Z

本登记在开始前推送；登记后不改规则。规则要改就另起 `forward/quant-035-2/`，旧的照样记完。只读公开数据、纸面记账，不下单、不连钱包、不使用任何密钥。

## 市场范围和选择规则

固定五币，不按行情挑选：

| 币 | 现货腿 | 永续腿 | 每个 sleeve 目标名义 | sleeve 预算（现货+保证金+费） |
|---|---|---|---:|---:|
| SOL | Binance SOLUSDT 现货 | Binance SOLUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| XRP | Binance XRPUSDT 现货 | Binance XRPUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| ADA | Binance ADAUSDT 现货 | Binance ADAUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| AVAX | Binance AVAXUSDT 现货 | Binance AVAXUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| HYPE | Hyperliquid 现货 `@107`（HYPE/USDC） | Hyperliquid `HYPE` 永续 | 1,200 USDT | 2,450 USDT |

- Binance 四个 sleeve 合计预算 2,400 USDT；Hyperliquid HYPE sleeve 预算 2,450 USDT；总占用 ≤4,850 USDT，留 ≥150 USDT 缓冲。总资本 5,000 USDT。
- 单场所占用上限约 2,500 USDT：Binance 2,400、Hyperliquid 2,450。
- 不加杠杆、不借币、不做空现货；永续只做 1x 空头对冲同币现货。两腿数量相同（同一 `q`）。
- 数据：Binance 公开 REST（免密钥）；Hyperliquid 公开 `/info`（免密钥）。见“记录和推送”。

## 进出场、仓位和风控

### 信号（每 14 天，按时间而不是按条数）

对每个币，在每个资金费时间戳 `t`（Binance 通常 8h，Hyperliquid 1h；以交易所实际 `fundingTime` 为准）：

```
window(t) = 所有 fundingTime > t - 14*24h 且 <= t 的资金费率
mean14(t) = mean(window(t))
```

- 必须已有完整 14 天观测：`window(t)` 中最早一条的 `fundingTime <= t - 14*24h`。预热不足时该币空仓，不发信号。预热从 2026-10-08T00:00:00Z 起读；开始前不记录。
- 资金费率为交易所公开的已实现/结算费率：Binance `fundingRate` 字段；Hyperliquid `fundingHistory.fundingRate`。不预测、不用 premium 代替。

### 开仓

- 若该币当前空仓，且 `mean14(t) > 0`，在 `t` 之后的下一个 1 小时 K 线开盘成交。
- 两腿同时成交：现货买入 `q`，永续卖出 `q`。
- 数量：
  ```
  q = min(target / spot_price, budget / ((spot_price + perp_price) * (1 + 0.003)))
  ```
  `target` 为该 sleeve 的目标名义（Binance 300，HYPE 1,200）；`budget` 为 600 或 2,450。`spot_price`、`perp_price` 取成交时点的第一笔公开成交价（见“成本和成交判定”）。
- 费用：
  ```
  entry_fee = 0.003 * q * (spot_price + perp_price)
  capital = q * (spot_price + perp_price) + entry_fee
  ```
- 现金账：`cash -= entry_fee`；`capital` 计入该场所占用，不得超过上表预算。

### 持有和资金费

- 持仓期间每个资金费时间戳 `t`，若 `entry_time < t`，按空头方向收付：
  ```
  funding_cash = q * mark_price(t) * funding_rate(t)
  ```
  正费率收正现金，负费率付出现金。`mark_price(t)`：Binance 取 `markPriceKlines` 在 `t` 所在小时的 1h 开盘价；Hyperliquid 取 `HYPE` 1h K 线在 `t` 所在小时的开盘价。取不到时用同小时永续 1h 开盘价并在 note 标注。
- 不设止损、不止盈；唯一平仓条件是信号转负。资金费为负时继续持有到下一次信号判断，接受负费。
- 不换币、不 switching；五个 sleeve 各自独立，A 币平仓不影响 B 币。若同一小时多个币都满足条件，各 sleeve 都开（不是选一个）。

### 平仓

- 若该币持仓，且 `mean14(t) < 0`，在 `t` 之后的下一个 1 小时 K 线开盘平仓：卖出全部现货 `q`，买回全部永续 `q`。
- 平仓费用 `exit_fee = 0.003 * q * (spot_exit + perp_exit)`。
- 该 episode 净损益：
  ```
  pnl = q*((spot_exit - spot_entry) + (perp_entry - perp_exit))
        + funding_cash_sum - entry_fee - exit_fee
  ```
- 窗口结束（2026-11-05T00:00:00Z）仍未平仓的，按 2026-11-05T00:00:00Z 之后第一根可用 1h K 线开盘价强制平仓并计 `exit_fee`，note 写 `reason=window_end`；不把浮盈当已实现。结束时间之后不再开新仓。
- 风控：若某腿成交价或数量导致 `capital > budget`，按上式缩小 `q`；若缩小后仍超，放弃该次开仓并在 note 记 `skip=budget`。若交易所公开数据缺失超过 2 小时，保持现有仓位、不新开，等数据恢复后按规则补算；不猜价格。

## 成本和成交判定

- **手续费/价差/滑点**：每腿每边 0.30%，即开仓 `0.003*q*(spot+perp)`、平仓同样；一个完整往返为名义的 1.2%。资金费另计实际收付。
- **成交价**：决策在资金费时间戳 `t`；成交时点 `fill_time` = `t` 之后的下一个整点 1h K 线开盘（`floor(t/1h)*1h + 1h`）。
  - 现货腿：取 `[fill_time, fill_time+120s]` 内第一笔公开成交（Binance `aggTrades` 的 `T >= fill_time`；Hyperliquid `recentTrades` 的 `time >= fill_time`）。`price_source` 写该成交的 id 和时间。
  - 永续腿：同一规则取永续第一笔公开成交。
  - 任一腿在 120 秒内取不到逐笔成交，或成交时间超出该窗口，退回 `fill_time` 的 1h K 线开盘价，`price_source` 写 `kline_open:<timestamp>`；这是数据缺失时的次优口径，note 必须标注。
- **资金费 mark**：见上；`price_source` 写 `mark_open:<timestamp>`（Binance 和 Hyperliquid 都用该前缀，时间戳为该小时 K 线的开盘时间）。
- **资金占用**：现货买入金额 + 永续 1x 保证金 + 开仓费。永续保证金按 `q*perp_price` 计；现货和永续在同一场所，假设可按组合保证金/手动划转使用，但单场所总占用不超过 2,500 USDT。
- **容量**：单笔 Binance 300 USDT、HYPE 1,200 USDT 名义，远低于这些合约的日常盘口深度；一个月机会数不预设，按信号实际发生。

## 独立结果和失败标准

- **event_id**：每个 episode 一个，`q035-<SYMBOL>-<entry_fill_time_ms>`；每个资金费行用 `<episode_id>-F<funding_time_ms>`。
- **独立结果计法（GUIDE 第 2、13 节）**：
  - 资金费类一次建仓到平仓算 1 个；同一 episode 的多个资金费结算不重复计。
  - 同一时刻、同一信号、同向的新开仓只算 1 个；本计划五个 sleeve 若在同一小时开仓，合并计 1 个。不同币、不同时间的 episode 分别计。
  - 对冲的两条腿算 1 个。
- **预计独立结果数**：14 天窗口内预计 **0–2 个**新 episode。原因是 14 天均值闸门是有状态的 regime 过滤器，2022–2024 回放中单币平均持有约 59 天、中位约 15 天；两周内通常只有 0–2 次新开仓。**因此本前向记录远少于 30 个独立结果，不能单独满足 GUIDE 第 2 节的 30 个结果门槛，也不能据此申请“通过快速筛选”；它只作为规则在真实公开数据上的描述性前向记录。** 这一点在登记时写明，不事后修改。
- **失败标准**（事先固定）：
  1. 结束时（2026-11-05T00:00:00Z）扣全部成本后的合并净损益 ≤0；或
  2. 任一时刻某场所占用 >2,500 USDT 或总占用 >5,000 USDT（按登记预算应不发生；发生即记失败）；或
  3. 规则要求的开仓/平仓漏记、或明细与公开数据对不上且无法用 `更正` 行解释；或
  4. 出现未登记的参数改动（另起 `-2` 登记除外）。
- 因独立结果 <30，上述失败标准只作描述性记录；即使净收益为正，也不自动等于“通过快速筛选”。

## 记录和推送

- 明细文件：`forward/quant-035/ledger.csv`，表头只允许：

```csv
time_utc,event_id,market,action,side,price,price_source,size,fee,pnl,note
```

- `time_utc` 用 UTC ISO `YYYY-MM-DDTHH:MM:SSZ`；`action` 只用 `开`、`平`、`结算`、`更正`（挂单类本策略不用；如将来用，按模板加 `挂`、`撤`、`成交`）。
- `market`：`Binance:SOLUSDT`、`Binance:XRPUSDT`、`Binance:ADAUSDT`、`Binance:AVAXUSDT`、`Hyperliquid:HYPE`。
- `side`：开/平写 `对冲`；资金费写 `空`。
- `price`：开/平写现货成交价；资金费写 mark 价。`size`：开/平写币数量 `q`；资金费写 `q*mark` 名义。`fee`：开/平写两腿合计费用；资金费写 0。`pnl`：开仓 0；平仓写该 episode 扣两腿费用后的净损益；资金费写当次现金。
- `note` 用分号分隔的 `key=value`，至少包含：
  - 开：`perp=<价>;qty=<q>;notional=<q*spot>;capital=<现货+保证金+费>;target=<300/1200>;budget=<600/2450>`
  - 平：`perp=<价>;qty=<q>;entry=<entry_time>;entry_fee=<费>;exit_fee=<费>;funding=<累计>;reason=signal|window_end`
  - 结算：`rate=<费率>;mark=<mark>;qty=<q>;episode=<event_id>`
- 只追加，不改旧行；记错另起 `更正` 行，`note` 写 `corrects=<time_utc>|<action>|<event_id>;reason=...`，`pnl` 写差额（无差额写 0）。
- 至少每天推送一次；开仓行和平仓行必须在平仓/结算前推送。`ledger.csv` 单文件不超过 1 MB；超过按周拆 `ledger-2.csv` 等，表头相同。
- `record.py`：
  - 从仓库根目录运行：`python3 bots/quant/forward/quant-035/record.py`；建议每小时一次。
  - 只写 `forward/quant-035/state.json` 和追加 `ledger.csv`；不写其他状态文件。
  - 每次运行重算从 `START` 到 `now` 的应记录行，按 `(time_utc,event_id,action)` 去重后只追加缺失行；同键不同值追加 `更正` 行。这样崩溃/重跑幂等。
  - 网络错误打印原因并以 0 退出，不写半截状态；下次重跑补上。
  - 开始时间前不写任何行。
  - 测试：`FORWARD_DRY_RUN=1 python3 bots/quant/forward/quant-035/record.py`，假定开始时间为当前时刻，只打印将要追加的行，不写 `ledger.csv`、不写 `state.json`。
- 数据 URL（公开、免密钥）：
  - Binance 现货 K 线：`https://data-api.binance.vision/api/v3/klines?symbol=<SYM>&interval=1h&startTime=<ms>&endTime=<ms>&limit=1000`
  - Binance 现货逐笔：`https://data-api.binance.vision/api/v3/aggTrades?symbol=<SYM>&startTime=<ms>&endTime=<ms>&limit=1`
  - Binance 永续资金费：`https://fapi.binance.com/fapi/v1/fundingRate?symbol=<SYM>&startTime=<ms>&endTime=<ms>&limit=1000`
  - Binance 永续 K 线：`https://fapi.binance.com/fapi/v1/klines?symbol=<SYM>&interval=1h&startTime=<ms>&endTime=<ms>&limit=1000`
  - Binance 永续逐笔：`https://fapi.binance.com/fapi/v1/aggTrades?symbol=<SYM>&startTime=<ms>&endTime=<ms>&limit=1`
  - Binance mark：`https://fapi.binance.com/fapi/v1/markPriceKlines?symbol=<SYM>&interval=1h&startTime=<ms>&endTime=<ms>&limit=1000`
  - Hyperliquid：`POST https://api.hyperliquid.xyz/info`，`{"type":"fundingHistory","coin":"HYPE",...}`、`{"type":"candleSnapshot","req":{"coin":"HYPE"|"@107","interval":"1h",...}}`、`{"type":"recentTrades","coin":"HYPE"|"@107"}`
- 如果 Binance 永续 REST 在当前网络不可用，`record.py` 会跳过该币并退出 0；可用时按上表补齐。Hyperliquid 部分独立记录。

## 与回放的口径差异（登记时写明）

- 回放中 HYPE 用 4h K 线成交（Hyperliquid 公开 API 的 2024 年 1h 历史已被裁剪，4h 仍可取），前向按要求统一用 1h K 线。信号窗口仍是 14 天，只有成交粒度不同；回放 `SUMMARY.md` 已注明。
- 回放在 Binance 用月度归档的 1h 开盘价成交；前向用决策后下一根 1h 开盘的第一笔公开成交（或开盘价回退）。成本同为每腿每边 0.30%。
