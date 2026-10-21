# 回放汇总：quant-031

条目：`bots/quant/entries/quant-031-aaa-gas-daily-bracket.md`（AAA 汽油日档：翻页后抢跑）
本回放只做历史已结算事件，`status: 草稿`；不进 `forward/`。

## 如何复现

- 脚本：`bots/quant/replay/quant-031/replay.py`（Python 3，只用标准库）
- 运行命令（仓库根目录）：
  ```bash
  python3 bots/quant/replay/quant-031/replay.py
  python3 bots/quant/replay/quant-031/replay.py --write-trades   # 重新生成 trades.csv
  ```
- 参数（全部写死在脚本顶部）：
  - 决策时点：事件日**最早一张** Wayback 快照，且 `Price as of` = 当天、`Yesterday Avg.` = 前一天的 `Current Avg.`；具体时刻与 URL 在 `decision_points.csv`。
  - 成交：data-api 中该档 YES 在决策时点之后、`endDate`（14:00 UTC）之前的第一笔实际 `BUY` 成交。
  - 费用：`0.04 × p × (1 − p)` / 份（已结算 30 个市场实测 `feeSchedule.rate=0.04`、`takerOnly=true`）。
  - 价差：另扣 **0.005 USDC/份**（半价差）。
  - 持有：到结算，YES 付 1；不中途卖出。
  - 仓位：每事件 ≤250 USDC，并受该笔成交实际份数封顶；不假设还能吃到更多。
- 数据下载地址和访问日期（2026-10-21）：
  - Gamma：`https://gamma-api.polymarket.com/events?series_id=12954&limit=100`（6 个事件，5 已结算 / 1 未结算）
  - data-api：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=0`
  - AAA 快照（逐事件，`id_` 原始页面）：
    - 10-16 `https://web.archive.org/web/20261016110050id_/https://gasprices.aaa.com/`
    - 10-17 `https://web.archive.org/web/20261017110254id_/https://gasprices.aaa.com/`
    - 10-18 `https://web.archive.org/web/20261018110336id_/https://gasprices.aaa.com/`
    - 10-19 `https://web.archive.org/web/20261019095656id_/https://gasprices.aaa.com/`
    - 10-20 `https://web.archive.org/web/20261020110138id_/https://gasprices.aaa.com/`
  - Wayback 在本环境间歇性 TLS EOF；`decision_points.csv` 固定了已核实的快照时刻，脚本不再下载 Wayback。
- 数据本身起点：Polymarket 该日更模板 2026-10-15 创建；同规则已结算事件从 2026-10-16 起。
- 开发窗口：`2026-10-16..2026-10-20`（Polymarket 无加密窗口限制；6 个事件中 5 个已结算）。
- 切分依据：不切分，全部已结算事件都是样本；参数只有 3 个价格门槛，见下。

## 成交和成本

- 成交价和时点：data-api 逐笔实际 `BUY` 成交价，不是 CLOB `prices-history`（后者是最后成交价/中间价，实测 10-17 08:00 序列 `p=0.55` 而 07:56:59 实际成交 0.98）。没有历史 L2，因此“第一笔成交”是**可成交价代理**：有成交证明该价可成交，无成交不等于当时没有卖单。
- 全部成本：吃单费 `0.04×p×(1−p)` + 半价差 0.005/份；无资金费、无滑点模型（成交份数按实际打印封顶）。
- 资金和容量：每事件 ≤250 USDC；实际投入 39.73–75.01 USDC（≤0.99 两笔），任何时点只占 1 个事件；5,000 USDT 放得下。

## 汇总结果

- 独立结果数及计法：**5 个**（按日期；同一天 6 档算 1 个）。
- 扣成本后净收益：
  - `limit<=0.95`（条目规则）：**0 笔成交**，净 0.00 USDC。
  - `limit<=0.99`：2 笔，净 **+0.7067 USDC**，投入 114.74 USDC，ROI **0.62%**。
  - `market (any price)`：3 笔，净 **+0.4212 USDC**，投入 185.69 USDC，ROI **0.23%**（10-20 @0.999 一笔 −0.2855）。
- 最大回撤：不适用（Polymarket，字段写 `-`）。若按累计净收益峰值算，any-price 变体从 +0.7067 回落到 +0.4212，回撤 0.2855 USDC（峰值的 40.4%），但绝对额 <0.3 USDC。
- 对 5,000 USDT 的年化贡献：
  - 条目规则（≤0.95）无成交 → **0.00%**。
  - 放宽到 ≤0.99：0.7067 USDC / 5 个事件 × 73 个事件/年 ÷ 5,000 = **1.03%/年**；样本只有 2 笔，不能外推。
- result：**不显著**（独立结果只有 5 个 <30；≤0.95 规则 0 笔成交，无法判定正负）。
- 不可靠或失败原因：样本仅 5 个已结算事件；无历史 L2；决策时点只能由存档快照界定，翻页真实时刻可能更早；`prices-history` 不能当卖价，已弃用。

## 所有变体（所有市场都要写，看了不用的也算）

- variants（自己的）：**3**
- variants_ext（外部来源）：`-`（未引用外部回测结果）

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| V1 | 自己 | 最早可核快照决策；第一笔 YES BUY；`p≤0.95`；费 0.04；半价差 0.005；250 USDC 封顶；持有到结算 | 2026-10-16..2026-10-20 | 0/5 成交，净 0.00 USDC；`trades.csv` 无该变体行 |
| V2 | 自己 | 同上，`p≤0.99` | 同上 | 2/5 成交，净 +0.7067 USDC，ROI 0.62%；`trades.csv` `variant=limit<=0.99` |
| V3 | 自己 | 同上，不限价（吃第一笔） | 同上 | 3/5 成交，净 +0.4212 USDC，ROI 0.23%；`trades.csv` `variant=market (any price)` |

未计入变体、只作诊断的两项（已明确不用于收益）：
- 07:00 UTC 后**事后赢家**首笔成交（0.49–0.88）：用了事后才知道的赢家，且没有 07:00 的 AAA 页面快照，不算规则回放。
- CLOB `prices-history` 中间价回测：10-17 08:00 `p=0.55` 对实际成交 0.98，会造出 4/5 笔、+331 USDC 的假收益，已弃用。
- 2025-02-21 / 2025-02-28 两个 5 档、12:00 UTC 收盘的近似事件：规则不同（无 10:00 ET 条款），不计入独立结果，也不计变体。

## 结论

按条目写的 `≤0.95` 规则，5 个已结算事件里 **0 笔可成交**；放宽到 0.99 只有 2 笔、合计 +0.71 USDC；不限价 3 笔也只有 +0.42 USDC。历史独立事件 5 个，两周前向约 14 个，合计 19 <30。**不建议作为第 2 轮 `待核` 收录候选；按七门标准应退回/放弃（drop）。**
