# 两周前向登记：composer-011

先填完、推送到 `main`，再开始记录。登记后不改规则；要改另起 `forward/composer-011-2/`。

- 自己的条目编号：**composer-011**
- 原条目或 known/ 机制：**M-M4-poly-rewards**（`kind: supplement`）
- 登记序号：**1**
- 同机制全部登记：`forward/composer-011/`（本目录）
- 开始时间（UTC）：**2026-10-21T06:00:00Z**（须晚于本文件推送到达 `main` 的时间）
- 结束时间（UTC）：**2026-11-04T23:59:59Z**（≥14 天）

## 市场范围和选择规则

**场所**：Polymarket CLOB（只读公开接口 + 纸面记账，不下单）。

**每日 06:00 UTC 刷新候选**（脚本或手工均可，规则固定）：

1. 拉 Gamma：`GET https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=liquidity&ascending=false`
2. 保留同时满足：
   - `enableOrderBook == true`（或等价可 CLOB 交易字段为真）；
   - `clobRewards` 非空且 **`rewardsDailyRate` > 0**（USDC 计价，取数组首元素）；
   - `rewardsMinSize`、`rewardsMaxSpread` 可读（用于合规报价宽度）；
   - 板块 `pm_category` ∈ {`politics`, `crypto`, `finance`}（高奖励池优先，主项目易核对）。
3. 按 **`rewardsDailyRate` 降序**取前 **3** 个 market（`event_id` = Gamma `conditionId`；`market` 列写 `slug`）。
4. **排除**：5min/15min 加密涨跌微市场（slug 含 `updown-5m` / `updown-15m`）；`endDate` 距 UTC 现在 **<48h** 的市场。
5. 若不足 3 个满足条件，则当日只报有奖励的市场；**独立结果仍按 event 计**（同一 event 多 market 算 1 个）。

**价格与盘口来源**：CLOB `GET https://clob.polymarket.com/book?token_id=<token_id>`（Gamma `clobTokenIds` 中 **Yes** 侧 token）；成交核对用 data-api `https://data-api.polymarket.com/trades?market=<conditionId>`。

## 进出场、仓位和风控

**策略（纸面）**：在每个选中 market 的 **Yes token** 上 **双边挂单** 赚 spread + 流动性奖励 + maker 返佣（不押方向，库存接近中性）。

**报价规则**（每个 market，每 **60 分钟** 或 **mid 变动 ≥0.01** 时重算）：

1. 读 book：`best_bid`, `best_ask`；若 spread `< 0.02` → **当日该 market 不报价**（记 `action=撤` + note=spread_too_tight）。
2. 目标报价（Yes 价格 p∈(0,1)）：
   - **买价** `bid_quote = min(best_bid + 0.001, mid - rewardsMaxSpread/100/2)`（遵守奖励最大 spread；`rewardsMaxSpread` 为 Gamma 百分数，如 4.5 表示 ±4.5c）
   - **卖价** `ask_quote = max(best_ask - 0.001, mid + rewardsMaxSpread/100/2)` 对称
   - 四舍五入到 **0.001**；若 `ask_quote - bid_quote < 0.01` → 不报价。
3. **份数**：每边 `size = max(rewardsMinSize, 200)` 份（上限 **400** 份/边，保证 ≤2,500 USDT：400×1≈400 USDT 名义/边）。
4. **并发**：最多 **3** market × 双边；总占用 ≤ **5,000 USDT**（按 `size × mid` 估算 Yes 库存 + 挂单单边名义之和，取较大者盯市）。
5. **库存**：净 Yes 份数 **|net| ≤ 500**；超限时下一周期只挂减仓侧。
6. **撤单**：endDate 前 **24h** 起不再新挂；结算后 `action=结算` 一行。

**event_id**：Gamma `conditionId`（每个 market 一条 event_id；同一 event 下多 market 仍按 GUIDE 只计 1 个——本规则每日最多 3 market 来自不同 condition，若 collision 则只保留 reward 最高的一条）。

## 成本和成交判定

- **吃单**：若纸面被迫 taker 对冲，费 = `size × feeRate × p × (1-p)`（Gamma `feeSchedule` / `takerBaseFee`；缺省 politics **0.04**）。
- **挂单**：taker 费 **0**；maker 返佣按 **对手 taker 费的 20%** 计入（保守；官方区间 15–25%）。
- **价差成本**：模拟成交时扣 **半个 spread**（=(ask-bid)/2 × size）。
- **奖励**：按 Gamma `clobRewards.rewardsDailyRate` **× 当日得分占比**；纸面假设得分 = 若满足 minSize 且在 maxSpread 内则得 **1 单位**；每日奖励 = `rate × (1单位 / 3 market)` 均分（保守，不假设全池）。
- **成交判定（悲观）**：
  - 仅当 data-api 出现 **`price` 等于我们的挂单价** 且 **`side` 与我们的被动侧相反** 的 trade，记 `action=成交`；
  - **排队**：若该价位当日 trade 量 **< our size**，只记 **成交量 = trade 量**（部分成交）；
  - 价格源：`price_source=data-api:<trade_hash>` 或 `book:<snapshot_iso>`。
- **快照时间**：吃单 hypothetically 用决策后 **+60s 内** 第一条 book/trade。

## 独立结果和失败标准

- **event_id**：`conditionId`；**独立结果** = 登记期内每个 **distinct conditionId** 至少完成 **1 次完整报价日**（06:00 刷新并至少 1 次挂/撤记录）且该 event 已 **结算或登记结束**。
- **预计独立结果数**：≥ **30**（14 天 × 每日最多 3 market，且 politics/crypto 奖励池 event 充足）。
- **失败标准**（机械）：
  1. 登记期扣成本后 **累计净 PnL（含奖励+返佣−价差−taker）≤ 0**；或
  2. 可计 **独立结果 < 30**；或
  3. 连续 **5** 天无法选到任一 `rewardsDailyRate>0` 市场（记 note，仍继续登记至结束）。

## 记录和推送

- 明细：`forward/composer-011/ledger.csv`
- **至少每日 UTC 06:30** 推送当日刷新与挂单行；**成交/结算行**在对应事件 **结算前** 推送。
- 表头：

```csv
time_utc,event_id,market,action,side,price,price_source,size,fee,pnl,note
```

- 结束写 `RESULT.md`，并将 composer-011 的 `evidence` 改为 `前向`、`result` 据实；`LOG.md` 申请核对。
