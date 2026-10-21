---
id: quant-031
name_zh: AAA汽油日档：10点值抢跑
name_en: AAA Daily US Regular Gas Price Bracket Front-Run
bot: quant
date: 2026-10-21
market: polymarket
pm_category: economics
kind: new
improves: -
category: E
return_type: convergence
instruments: "Polymarket 每日美国普通汽油 AAA 全国均价 1 美分分档（<$x.xx00 / $x.xx00-x.xx99 / … / $x.xx00+），同一事件 6 档"
venues: Polymarket
data: "Gamma（规则原文、分档、feeSchedule、已结算 outcomePrices）免费免密钥；data-api 逐笔成交（已关闭市场可查）免费免密钥；AAA gasprices.aaa.com 当日页面 + Wayback 存档，免费免密钥。日更系列 2026-10-15 创建，至 2026-10-21 共 6 个事件（5 个已结算、1 个未结算）；完全同规则的已结算历史只有 5 个，另有 2 个 2025 周度近似事件"
test_2w: "按日期计独立结果（同一事件 6 档算 1 个）。两周前向约 14 个，历史完全同规则已结算 5 个，均 <30；失败标准：历史+前向满 30 个事件后，扣费+半价差后中位净收益 ≤0，或 ≤0.95 的可成交率 <20%"
status: 草稿
confidence: 中
evidence: 回放
result: 不显著
slot: -
variants: 3
variants_ext: -
window: 2026-10-16..2026-10-20
max_dd: -
contribution: 0.00%
---

## 一句话

AAA 每天上午在 https://gasprices.aaa.com/ 把“Current Avg.”翻到当天值；Polymarket 的 1 美分分档市场在 10:00 AM ET 收盘并按该值结算。**真正的信息窗口在 AAA 翻页的那一刻，不在 10:00 ET**：64 个 Wayback 快照中，07:30 UTC 之前没有任何一张显示当天值；所有解析日期中首次看到当天值落在 07:30–11:03 UTC（美东 03:30–07:03），5 个事件日更晚、集中在 09:56–11:03，而 10:00 ET 前市场通常已把获胜档抬到 0.99 附近。拟定规则是：从 04:00 UTC 起每 2 分钟读一次 AAA 页面，确认“Price as of”已是当天且“Yesterday Avg.”是前一天后，买入与 Regular/Current Avg. 对应的那一档 YES，仅当可成交卖价 ≤0.95；持有到结算，否则不交易。**但按最早可核页面快照 + 实际 BUY 成交回测，5 个已结算事件中 0 笔 ≤0.95；放宽到 0.99 只有 2 笔，合计净 +0.7067 USDC（见证据 3）。**

## 钱从哪里来

付钱的是 **AAA 翻页后仍挂着旧价格的对手方**。每天 00:00 UTC 时，市场还没有当天 AAA 值，只能按昨天值（如 4.3344）和其他信息猜测今天落在哪一档；AAA 在凌晨（样本中首次看到当天值在美东 03:30–07:03）把当天值放上网页后，哪一档会赢就变成确定事实。谁在翻页后仍按旧盘口报价，谁就把这段确定性让给先读到页面的人。

这笔钱能否持续，取决于三点，本文只证实了前两点的一半：

- 模板每天重开一个事件（已证实：series `12954`，`recurrence=daily`，2026-10-15 创建，至 2026-10-21 已有 6 个事件、5 个已结算、1 个未结算）；
- AAA 的翻页时刻不固定（已证实：CDX 在 2026-08-01–10-21 返回 294 个 200 快照，其中 43 个落在 04:00–10:59 UTC；本文解析 64 个快照、分布在 33 个日期（其中 16 个日期至少有一张显示当天值），07:30 前没有任何快照显示当天值，首次看到当天值从 07:30 到 11:03 不等）；
- 翻页后的错价能留多久（**有后续成交的 4 个已结算事件里是 0.3–75 分钟；10-16 收盘前最后一笔 0.8171 之后再无 14:00 UTC 前成交（14:22:36 的 0.9892 是收盘后成交），无法判断是否可买**；盘口极薄，10:00 ET 前价格已收敛，见“证据”）。

因此本条不是“10 点值抢跑”，而是“AAA 凌晨翻页后的短窗口抢跑”。把进场时间设在 10:00 ET 的版本在 5 个已结算事件上 **0 笔 ≤0.95 的实际 BUY 成交**（决策时最优卖价未取到；见证据），不成立。

## 规则

### 市场模板与示例

- 模板：`Gas prices on <month> <day>?`；同一天一个 event，6 个互斥分档，每档宽 1 美分：
  - `<$4.3100`、`$4.3100-4.3199`、`$4.3200-4.3299`、`$4.3300-4.3399`、`$4.3400-4.3499`、`$4.3500+`（2026-10-16 实例）。
  - 档位随前一日价格平移；10-20 的档位是 `<$4.2800`、`$4.2800-4.2899`、…、`$4.3200+`。
- 示例：
  - https://polymarket.com/event/us-gas-price-on-october-16-2026
  - https://polymarket.com/event/us-gas-price-on-october-19-2026
  - https://polymarket.com/event/us-gas-price-on-october-20-2026
- 每个 event 的 6 个市场均为二元 YES/NO，`negRisk=true`、`restricted=true`；已结算的 5 个事件共 30 个市场，Gamma 实测 `feeSchedule={"exponent":1,"rate":0.04,"takerOnly":true,"rebateRate":0.25}`（全部相同）。**2026-10-21 未结算事件当前 `rate=0`、`rebateRate=0`**，费率可能已调整；本文回测按 0.04 保守计。
- 频率：1 个事件/天；独立结果按“日期”计，同一天 6 档只算 1 个。

### 结算规则原文（2026-10-16 event，逐字）

> This market will resolve according to the US national average price of regular gasoline published by AAA for October 16, 2026.
>
> This market resolves based on the US national average price of regular gasoline published by AAA at https://gasprices.aaa.com/ in the "National Average Gas Prices" table under the "Regular" column and the "Current Avg." row.
>
> Each date's price is the price displayed at 10:00 AM ET on that date, provided that at that time the "Price as of" date shown on the webpage is that date and the "Yesterday Avg." row in the same column shows the previous date's price. If either condition is not met at 10:00 AM ET, the price will be observed at the first time on that date at which both are met; if both are not met by 11:59 PM ET on that date, the price displayed in the table at that time will be used. If AAA does not display the US national average price of regular gasoline in the table at the time of observation, the price displayed elsewhere on the webpage will be used. If AAA displays no US national average price of regular gasoline on the specified webpage at any time on the specified date, this market will resolve based on the most recent previously-published AAA US national average price of regular gasoline.
>
> The resolution source for this market will be the American Automobile Association (AAA) (https://gasprices.aaa.com/).
>
> Note: AAA currently publishes gas prices to four decimal places (e.g., $4.3718). The price will be used as published, without rounding.

要点：

- 结算源唯一：AAA 页面 `National Average Gas Prices` 表的 `Regular` 列、`Current Avg.` 行；保留 4 位小数，**不四舍五入**。
- 观察时点：10:00 AM ET（2026-10 为 EDT，即 14:00 UTC；11 月起 EST 为 15:00 UTC）。若 10:00 时“Price as of”不是当天或“Yesterday Avg.”不是前一天，则取当天第一次同时满足的时刻；到 23:59 ET 仍不满足，取当时页面值。
- 缺数据：先退到页面其他位置显示的全国均价；整页都没有，则用最近一次已发布的全国均价。
- 分档边界：`$4.2900-4.2999` 含 4.2900 和 4.2999；4.2900 不会落入 `<$4.2900`。按发布的 4 位小数直接比较。
- `resolutionSource` 字段为 `https://gasprices.aaa.com/`；event 的 `endDate` 为当天 14:00 UTC（10:00 ET）。5 个已结算事件的市场级 `umaResolutionStatus=resolved`，`closedTime` 在次日 02:08–16:11 UTC（10-16 02:08；10-17 16:11；10-18 16:03；10-19 16:02；10-20 16:01）。

### 进场、出场、仓位

1. **数据时钟**：从 04:00 UTC 起，每 2 分钟 GET `https://gasprices.aaa.com/`，解析 `Price as of`、`Current Avg.`（Regular）和 `Yesterday Avg.`（Regular）。不使用任何预测模型；只读页面。
2. **触发**：`Price as of` = 当天日期，且 `Yesterday Avg.` = 前一天日期，且 Regular/Current Avg. 为 4 位小数。任一不满足就继续等。
3. **映射**：把当前值直接映射到 6 档之一（含边界按上节）。只买这一档的 YES。
4. **价格门槛**：只挂限价买单，价格 ≤ 0.95；若最优卖价 >0.95 或没有卖单，放弃当天，不追价。参考成交价只用 data-api 的实际 BUY 成交，不用 CLOB 中间价；CLOB `prices-history` 的 `p` 也不等于可成交卖价（见证据 3）。
5. **出场**：买入后持有到 10:00 ET 结算，不中途卖出，避免第二次吃单费。若当天 10:00 ET 前没有触发（页面一直未翻页），放弃。
6. **仓位**：单事件 ≤250 USDC；不超过可见卖单前 3 档总量的 10%；同一时间最多 1 个事件（模板本身每天 1 个）；单场所 ≤2,500 USDC。
7. **风控**：若页面在 10:00 ET 仍未显示当天值，不交易；若 `Current Avg.` 与 `Yesterday Avg.` 同时等于昨天值，视为未翻页；若页面出现两个不同全国均价，按规则原文的“表格优先、其他位置兜底”顺序取，无法判断则放弃。
8. **独立结果**：按日期计；同一天 6 档、同一结算源、同一页面，算 1 个。

## 证据

### 1. AAA 翻页时刻（已核实，网页存档）

用 Wayback CDX 取 `gasprices.aaa.com` 在 2026-08-01 至 2026-10-21 的 294 个 200 快照，其中 43 个候选落在 04:00–10:59 UTC；连同事件日盘中快照，共解析 64 个不同时刻（分布在 33 个日期；其中 16 个日期至少有一张显示当天值）的 `Price as of`、`Current Avg.` 与 `Yesterday Avg.`。事件日附近的实测：

| 快照 UTC | Price as of | Current Avg. (Regular) | 判读 |
|---|---|---|---|
| 2026-10-16 04:42:08 | 10/15/26 | 4.3344 | 仍是前一天 |
| 2026-10-16 11:00:50 | 10/16/26 | 4.3271 | 已翻到当天 |
| 2026-10-16 12:42:12 | 10/16/26 | 4.3271 | 当天内未改 |
| 2026-10-16 16:03:08 | 10/16/26 | 4.3271 | 当天内未改 |
| 2026-10-17 00:01:17 | 10/16/26 | 4.3271 | 仍是前一天 |
| 2026-10-17 11:02:54 | 10/17/26 | 4.3085 | 已翻到当天 |
| 2026-10-17 17:28:45 | 10/17/26 | 4.3085 | 当天内未改 |
| 2026-10-18 01:05:02 | 10/17/26 | 4.3085 | 仍是前一天 |
| 2026-10-18 11:03:36 | 10/18/26 | 4.2988 | 已翻到当天 |
| 2026-10-19 00:01:46 | 10/18/26 | 4.2988 | 仍是前一天 |
| 2026-10-19 09:56:56 | 10/19/26 | 4.2953 | 已翻到当天 |
| 2026-10-19 19:48:06 | 10/19/26 | 4.2953 | 当天内未改 |
| 2026-10-20 11:01:38 | 10/20/26 | 4.2786 | 已翻到当天 |

更长样本（2026-08-01 至 10-21，64 个已解析快照；其中 04:00–10:59 UTC 的候选 43 个）显示：04:04、04:16、04:17、04:19、04:33、04:42、06:06、06:28、06:35、07:02、07:12 等快照仍显示“前一天”；**07:30 之前没有任何一张快照显示当天值**。各日期“首次看到当天值”的时刻为 07:30（10-06）、07:43（10-09）、07:57（09-25）、08:12（09-24）、08:46（09-16）、08:49（09-19）、08:50（10-13）、09:56（10-19）、10:01（08-19）、10:20（09-18）、10:22（09-09）、10:44（08-03）、11:00（10-16）、11:01（10-20）、11:02（10-17）、11:03（10-18）。**这只是“首次被存档看到”的上界，不代表翻页就发生在那一刻**；例如 10-16 的最后一张前一天快照是 04:42、首张当天快照是 11:00，只能界定翻页发生在 04:42–11:00 之间。结论仍然成立：10:00 ET（14:00 UTC）时值几乎总已公布，但翻页时刻不是固定的 10:00 ET。

### 2. 事件研究：翻页后的价格跃迁（描述性，非规则回测）

对 5 个已结算事件（10-16 至 10-20），取获胜档 YES 在当天 07:00 UTC 后的第一笔成交，以及第一次 ≥0.95 的成交：

| 事件 | AAA 当日值 | 获胜档 | 07:00 后首笔 YES 成交 | 首次 ≥0.95 | 到 0.95 用时 | 收盘前最后一笔 |
|---|---:|---|---:|---|---:|---:|
| 10-16 | 4.3271 | $4.3200-4.3299 | 07:27:34 @ 0.8171 | 无 | — | 07:27:34 @ 0.8171 |
| 10-17 | 4.3085 | <$4.3100 | 07:29:00 @ 0.4902 | 07:56:59 | 28.0 分钟 | 07:56:59 @ 0.98 |
| 10-18 | 4.2988 | $4.2900-4.2999 | 07:41:14 @ 0.7624 | 07:41:32 | 0.3 分钟 | 14:00:00 @ 0.997 |
| 10-19 | 4.2953 | $4.2900-4.2999 | 07:30:50 @ 0.8753 | 08:45:53 | 75.0 分钟 | 10:20:54 @ 0.9884 |
| 10-20 | 4.2786 | <$4.2800 | 07:21:50 @ 0.8228 | 07:32:14 | 10.4 分钟 | 13:59:21 @ 0.999 |

**这是事后选赢家的事件研究，不是可执行规则的回测。** 它只说明：除 10-16 外，翻页后赢家档确实曾在 0.49–0.88 成交，并在 0.3–75 分钟内被抬到 0.95 以上；也说明 10:00 ET 前市场已经完成定价。不能把 07:00 的价格当成“当时已知赢家”的证据，因为本文没有 07:00 的 AAA 页面快照。

### 3. 历史可成交回测：最早可核页面快照 + 实际 BUY 成交（主检验；不是预注册样本）

规则：对每个已结算事件，取事件日**最早一张**同时满足“`Price as of` = 当天”且“`Yesterday Avg.` = 前一天 `Current Avg.`”的 Wayback 快照作为决策时点（10-16 11:00:50、10-17 11:02:54、10-18 11:03:36、10-19 09:56:56、10-20 11:01:38）；在该时点之后、14:00 UTC 收盘之前，取对应档 YES 的**第一笔实际 BUY 成交**作为可成交价，限价 ≤0.95（另做 ≤0.99 与不限价两档敏感性）；费用 0.04、另加 0.5 美分半价差；持有到结算；每事件最多 250 USDC，并按该笔成交的实际份数封顶（不假设还能吃到更多）。这是**成交价代理**，不是历史 L2 盘口：没有成交不等于当时没有卖单，但有成交价 ≤0.95 的样本可以直接证明该价位可成交。

- **≤0.95：5 个已结算事件 0 笔成交**（10-16、10-17、10-18、10-19、10-20 都没有 ≤0.95 的 BUY 成交）。这与旧版“0 个可成交样本”不同：现在能说的是“0 笔 ≤0.95 的实际 BUY 成交；决策时最优卖价未取到”，不能断言当时一定没有 ≤0.95 的卖单。
- **≤0.99：2 笔成交**。10-18 11:25:41 @ 0.988457，75.5 份，费 0.000456/份，净 0.006087/份，**+0.4595 USDC**；10-19 10:20:54 @ 0.98836，40 份，费 0.000460/份，净 0.006180/份，**+0.2472 USDC**。合计 **+0.7067 USDC**，投入约 114.74 USDC，回报 **0.62%**（5 个事件、2 笔，不能证明正 EV）。
- **不限价（市价吃第一笔）：3 笔成交**。除上两笔外，10-20 13:59:21 @ 0.999，70.67 份，净 **−0.00404/份**，**−0.2855 USDC**；合计 **+0.4212 USDC**，投入约 185.69 USDC，回报 **0.23%**。10-16 最后一笔是 07:27:34 @ 0.8171，10-17 最后一笔是 07:56:59 @ 0.98，决策时点之后到收盘前都没有成交，故不计入。
- **07:00 事后赢家回放只作诊断**：5 个事件首笔 YES 价 0.4902–0.8753，但 07:00 的 AAA 页面没有事件日快照，且用的是事后才知道的赢家；不把它换算成收益，也不作为证据。
- **为什么不用 CLOB `prices-history`**：已结算的 30 个市场各有 135–172 个分钟级点，但该序列的 `p` 不是可成交卖价。实测 10-17 07:56:59 有 YES 成交 0.98，08:00 序列 `p` 仍为 0.55；10-16 收盘前 07:27 最后一笔 0.8171，11:10 序列 `p` 为 0.735；14:22:36 的 0.9892 是 14:00 UTC 收盘后成交。序列更像宽价差下的中间值或滞后值；若误用它做 0.95 回测，会显示 4/5 笔、+331 USDC 的假收益，本文已弃用。
- **可复现材料（第 2 轮）**：`bots/quant/replay/quant-031/` 下有 `replay.py`（只读 Gamma + data-api，参数写在文件头）、`decision_points.csv`（5 个决策时刻与 Wayback URL）、`trades.csv`（各变体逐笔成交）、`SUMMARY.md`。复跑 `python3 bots/quant/replay/quant-031/replay.py --write-trades` 输出与本节数字一致：≤0.95 0/5；≤0.99 2/5、+0.7067 USDC；不限价 3/5、+0.4212 USDC。`result` 写 `不显著`：独立结果只有 5 个（<30），且 ≤0.95 规则 0 笔成交，无法给出正/负判定。

### 4. 周内 2 个 2025 近似事件（不同规则，不计入 5 个）

- `average-us-gas-prices-on-february-21`（2025-02-21，5 档，close 12:00 UTC，`feeSchedule=null`）：获胜 `$3.16` 档收盘前最后 YES 成交 08:16:08 @ 0.9857。
- `average-us-gas-prices-on-february-28`（2025-02-28，5 档，close 12:00 UTC，`feeSchedule=null`）：获胜 `$3.14 or less` 档 10:26:39 有 SELL @ 0.99。
- 这两个是“某日均价落在第一、二位数字档”，没有 10:00 ET 快照条款，且是周度/一次性事件；只能说明 AAA 分档模板不是 2026-10 才出现，**不能算作同规则的独立结果**。

## 数据

- Gamma（免费、免密钥）：
  - `https://gamma-api.polymarket.com/events?series_id=12954&limit=100`：返回 6 个事件（5 已结算、1 未结算），endDate 2026-10-16 至 2026-10-21。调度侦察记录的是 9 个事件（6 已结算），与本次实抓不一致；本次以 Gamma 实抓为准，`public-search?q=gas%20prices%20on` 本次只返回 5 个（10-19 未出现在搜索结果），未找到另外 3 个事件。
  - `https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-16-2026`：规则原文、6 档、`feeSchedule`、`outcomePrices`、`closedTime`。
  - `https://gamma-api.polymarket.com/public-search?q=gas%20prices%20on`：本次返回 5 个事件（10-16/17/18/20/21），搜索结果不完整；以 `series_id=12954` 的 6 个为准。
  - `https://gamma-api.polymarket.com/public-search?q=aaa%20gas`：本次返回 5 个，全部是 2022 的“某日前跌破/达到 $4/$5”一次性阈值市场，**不是** 1 美分日档模板，未计入独立结果；旧版写的 `totalResults=21`、17 个已关闭本次未复现，已删除。
- data-api（免费、免密钥）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=0`；已关闭市场可查，返回 `timestamp`、`side`、`price`、`size`、`outcome`。本文 5 个已结算事件共 30 个市场，YES 成交合计 61 笔（逐事件 6/10/21/13/11），单个市场 0–12 笔；2025 两个事件 10 个市场共 70 笔（38/32）。**成交不是盘口**：只能证明某一刻有人以该价成交，不能证明决策时点一定有同样卖价。
- AAA（免费、免密钥）：
  - 当日页面 `https://gasprices.aaa.com/`：2026-10-21 01:34 UTC 读取、04:00 UTC 复核，均显示 `Today's AAA National Average $4.2786`、`Price as of 10/20/26`（尚未翻到 10/21）；表 `Current Avg.` Regular = `$4.2786`、`Yesterday Avg.` Regular = `$4.2953`。
  - 历史页面用 Wayback：`https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com&from=20260801&to=20261021&output=json&filter=statuscode:200&fl=timestamp,digest`；逐快照用 `https://web.archive.org/web/<timestamp>id_/https://gasprices.aaa.com/`。Wayback 在本环境间歇性 TLS EOF，脚本对每个 URL 重试后才取到 64 个快照。
- 起始日期：日更模板 2026-10-15 创建；AAA 页面本身有更长的历史，但**Polymarket 同模板的已结算历史只有 5 个**（10-16 至 10-20）。历史可执行盘口无公开来源；2025 两个事件的 CLOB `prices-history` 返回 0 点（5 档全部检查），2026-10 已结算事件有 135–172 个分钟级点但只从事件创建日起，且 `p` 不是可成交卖价（见证据 3）。

## 两周内怎么检验

- **独立结果怎么数**：按日期计，同一天 6 档算 1 个；同一日期不同档、同一结算源不独立。
- **历史**：完全同规则的已结算事件只有 **5 个**（2026-10-16 至 10-20），加上 2 个 2025 近似事件也只有 7 个；**不足 30 个**，不能在本条内完成 GUIDE 门槛 2 的历史样本要求。本文不把 5 个事件伪装成 30 个。
- **两周前向**：从 2026-10-21 起每天记录 1 个事件，两周约 **14 个**，加上历史 5 个也只有 19 个，仍 <30。两周内只能验证：
  1. AAA 首次显示当天值的时刻分布（样本中是 07:30–11:03 UTC）；
  2. 翻页后到 10:00 ET 之间，是否出现 ≤0.95 的实际 BUY 成交（或可成交卖价）；
  3. 扣费+半价差后单笔净收益的符号。
- **失败标准（预先写死）**：
  - 历史+前向满 30 个事件后，扣费+0.5 美分半价差后的**中位净收益 ≤0**；或
  - ≤0.95 的可成交率 <20%（说明翻页后价格已被瞬间抹平，抢不到）；或
  - 超过 20% 的成交发生在 >0.99（说明只剩尾部小钱，不值得占用资金）。
  - 任一触发即判失败，不再前向记录。
- **不做**：不用 07:00 事后赢家回放冒充规则检验；不把同一事件的 6 档算 6 个结果；不把 2025 的 2 个不同规则事件算进 5 个。

## 成本与容量

- **吃单费**：Gamma 实测 5 个已结算事件的 30 个市场全部 `rate=0.04`、`takerOnly=true`、`rebateRate=0.25`；2026-10-21 未结算事件当前 `rate=0`，回测按 0.04 保守计。按 GUIDE 第 8 节：
  - `fee/份 = 0.04 × p × (1−p)`。
  - p=0.82：`0.04×0.82×0.18 = 0.005904/份`，占价格 **0.72%**。
  - p=0.95：`0.0019/份`，占价格 **0.20%**。
  - p=0.99：`0.000396/份`，占价格 **0.04%**。
- **半价差假设**：分档宽度 1 美分，历史盘口无公开来源；按 **0.5 美分/份** 计（即假设 1 美分买卖价差）。p=0.82 时占价格 0.61%，p=0.95 时占 0.53%，p=0.99 时占 0.51%。本文所有净收益都扣了这 0.5 美分；若实际价差更宽，结果更差。
- **粗算**：
  - p=0.82 买入：毛 0.18/份，扣费 0.005904 + 半价差 0.005 = **净 0.169096/份（20.6%）**；但这是事件研究里的价格，不是页面翻页后按实际成交能拿到的价格。
  - p=0.988457（10-18 的唯一一笔 ≤0.99 成交）：毛 0.011543，扣费 0.000456 + 半价差 0.005 = **净 0.006087/份（0.62%）**。
  - p=0.98836（10-19）：毛 0.01164，扣费 0.000460 + 半价差 0.005 = **净 0.006180/份（0.63%）**。
  - p=0.999（10-20 市价）：毛 0.001，扣费 0.00004 + 半价差 0.005 = **净 −0.00404/份（−0.40%）**。
  - p=0.95：毛 0.05，扣费 0.0019 + 半价差 0.005 = **净 0.0431/份（4.54%）**；但 5 个事件里没有一笔 ≤0.95 的实际 BUY 成交。
- **容量**：
  - 事件总成交额（Gamma 自报）：10-16 **1,728.79**、10-17 **950.98**、10-18 **2,193.14**、10-19 **895.15**、10-20 **1,562.91** USDC。
  - 获胜档市场成交额：10-16 **1,626.55**、10-17 **378.77**、10-18 **965.43**、10-19 **372.37**、10-20 **553.48** USDC。
  - 获胜档实际成交 6–12 笔，全部市场 0–12 笔；收盘前获胜档 YES 单笔 4.25–264.18 份（按成交价约 4.24–201.42 USDC）。单事件可放 **100–300 USDC**，但需要看到卖单；看不到深度时按 ≤250 USDC/事件。
  - 频率 1 次/天、约 30 次/月；资金占用从首次看到当天值（07:30–11:03 UTC）到 10:00 ET 约 3–6.5 小时，结算后到账可能到次日 02:00–16:00 UTC，按 **1–2 天**计。
  - 5,000 USDC 放得下（单场所 ≤2,500、单事件 ≤250），但**大部分时间资金闲置**；这是一个小额、低频、容量很小的机会，不适合作为主力收益来源。

## 风险

- **最大风险：样本里没有 ≤0.95 的成交，是否有可成交卖价未知**。5 个已结算事件没有一笔 ≤0.95 的实际 BUY 成交；除 10-16 外，翻页后赢家档在 0.3–75 分钟内被抬到 0.95 以上，10-20 从 0.8228 到 0.999 只用了 10.4 分钟。等你读到页面、连上盘口，可能只剩 0.99 的 1% 空间，扣半价差后接近 0。注意：没有成交不等于没有卖单，但样本里没有可证明的 ≤0.95 成交。
- **AAA 翻页时刻不固定**：样本中 06:35 仍有前一天，08-19 10:01、09-09 10:22、10-16 11:00 才首次看到当天值。固定 10:00 ET 进场会太晚；固定 07:00 进场会在部分日期早于翻页，读到的是昨天值，买错档。
- **中间价陷阱**：CLOB `prices-history` 在 10-17 08:00 给 0.55，而 07:56:59 实际成交是 0.98；若把中间值当卖价，会高估可成交性。本文的回测只用实际 BUY 成交，仍不能代表完整盘口。
- **页面口径风险**：`Price as of` 与 `Yesterday Avg.` 必须同时满足；AAA 可能短时显示旧缓存、双值或缺失。规则给了“其他位置兜底”和“用最近一次已发布值”的兜底，但兜底值可能不是你早上读到的值。
- **边界风险**：4 位小数、1 美分档，4.2900 归 `$4.2900-4.2999` 而不是 `<$4.2900`；按 2 位或四舍五入会买错档。
- **成交/深度风险**：市场极薄（获胜档总成交 372–1,627 USDC，10-20 为 553 USDC），历史只有成交价、没有盘口；250 USDC 也可能吃掉数档或无法成交。data-api 只保留最近约 2 万笔，本文市场成交笔数少，但仍不能保证是全部成交。Gamma 的 `volume`/`outcomePrices` 是平台自报，未用链上收据逐笔核实；AAA 数值是页面原样抄录。
- **结算/平台风险**：Polymarket `restricted=true`、UMA 结算；若 AAA 当天页面异常，规则可能按 23:59 ET 的显示值或最近一次已发布值结算，与你买入时读到的值不同。已结算事件 `closedTime` 在次日 02:08–16:11 UTC，资金实际锁 1–2 天。
- **竞争风险**：07:2x 的成交簇说明已有参与者盯页面；新进入者要赢过他们的轮询和下单速度。
- **样本风险**：只有 5 个完全同规则的已结算事件，且 2026-10-15 才上线；任何“胜率/中位收益”都只是 5 个点，不能外推。前向两周也只有 14 个，仍不足以完成门 6。

## 与最接近条目的区别

- **dot-004（已定事实后的报价收敛）**：最接近的宽口径机制。相同点是“权威事实已公开、买低于 1 的获胜侧”；不同点是 dot-004 是一次性政治官宣、无固定日更节奏、需要解析公告文本；本条是每天固定模板、AAA 页面自动翻页、1 美分分档、10:00 ET 硬截止，且关键变量是“AAA 翻页时刻 vs 市场收盘”。若主审按更宽口径认定二者为同一机制，本条应降为 dot-004 的 `kind: supplement`，`improves: dot-004`；本文按新模板/新关键变量写成 `new`，并在此明示这一判断风险。
- **muse-own-xmkt-resolution-lag（结算窗口时滞折价）**：muse 做的是**收盘后、UMA 正式结算前**的折价（风险是争议/锁仓 4–6 天）；本条是**收盘前数小时**、AAA 页面已翻页但市场未完全跟上的窗口，没有 UMA 争议窗口，风险是抢不到价而不是结算争议。
- **quant-010（周榜日更抢跑）**：quant-010 用日榜**估算**尚未发布的官方周榜；本条不估算——AAA 当天值已经原样发布，只比市场报价快。
- **quant-005（发帖数分档）**：quant-005 用已观测部分计数 + 计数过程模型预测最终档；本条是确定值已发布，无模型。
- **quant-015（全球气温 nowcast）/ dot-003（宏观 nowcast）**：都是模型 nowcast 尚未发布的统计值；本条结算值已在页面上，属于信息时滞而非 nowcast。
- **known/**：135 条中没有汽油/AAA 条目；`bots/quant` 也没有 gas 条目。仓库内 grep `gasoline|gasprices|gas price|AAA` 只命中 dot-047/049 的无关文本。

## 门槛自查

1. **机制说得清**：满足（有条件） — 付款方是 AAA 翻页后仍挂旧价的对手方；机制每天重复，但有后续成交的 4 个事件窗口只有 0.3–75 分钟（10-16 无后续收盘前成交），且 10:00 ET 版本没有 ≤0.95 的成交记录。
2. **有免费数据能检验**：不满足 — Gamma、data-api、AAA 页面/Wayback 都免费免密钥，但完全同规则的已结算事件只有 5 个（加 2 个 2025 近似事件也只有 7 个），不足 30 个；只能前向记录。
3. **小资金能做**：满足（有条件） — 单事件 100–300 USDC、每天 1 次、单场所 ≤2,500，5,000 USDC 放得下；但容量小、大部分时间闲置。
4. **不重复**：不确定 — 仓库无 gas/AAA 条目；但宽口径下可能被视为 dot-004 的变体（见上节）。若判为同一机制，应改为 supplement，而不是 new。
5. **扣成本后粗算够用**：不满足 — 5 个已结算事件按最早可核页面快照 + 实际 BUY 成交，≤0.95 为 0 笔；放宽到 0.99 只有 2 笔、合计净 +0.7067 USDC（0.62%）；不限价 3 笔、净 +0.4212 USDC（0.23%）。07:00 事后赢家回放只作诊断，不能当证据。
6. **两周内能检验**：不满足 — 每天 1 个事件，两周约 14 个，历史 5 个，合计仍 <30；两周只能验证翻页时刻和可成交率，不能完成 30 个独立结果。
7. **出处可查**：满足 — 规则原文、6 档、费率、成交、AAA 页面与 Wayback 快照均有 URL、访问日期和片段；脚本与输出在 `bots/quant/notes/scheduler/scratch/P-quant-031/`（`verify_out.txt`、`backtest_trades_out.txt`、`aaa_snapshots_all.csv`）。

## 处置建议

**按七门标准，建议退回/放弃（drop），不建议作为第 2 轮的收录候选。** 门 5 不满足：5 个已结算事件里 ≤0.95 的实际 BUY 成交为 0；放宽到 0.99 只有 2 笔，合计净 +0.7067 USDC，扣掉半价差后几乎不剩，且只有 2 个点；不限价 3 笔也只有 +0.4212 USDC。门 6 不满足：历史 5 个 + 两周前向 14 个 = 19 个，达不到 30 个独立结果。门 2 只能靠前向记录补齐。门 4 还有 dot-004 的宽口径重复风险。如果整合者需要一个“待选区”候选，可以保留为 `待选区` 参考；但若按 `待核`/`收录` 标准，本条应直接退回，不要占用第 2 轮名额。本文保留 `status: 草稿`，不改 `date`。

## 出处

- https://polymarket.com/event/us-gas-price-on-october-16-2026 — 访问 2026-10-21 — 已读（HTTP 200；页面与 Gamma 同一 event，示例链接）
- https://polymarket.com/event/us-gas-price-on-october-19-2026 — 访问 2026-10-21 — 已读（HTTP 200；示例链接）
- https://polymarket.com/event/us-gas-price-on-october-20-2026 — 访问 2026-10-21 — 已读（HTTP 200；示例链接）
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-16-2026 — 访问 2026-10-21 — 已读（规则原文逐字、6 档、feeSchedule、结算结果）
- https://gamma-api.polymarket.com/events?series_id=12954&limit=100 — 访问 2026-10-21 — 已读（6 个事件、5 个已结算、1 个未结算、endDate）
- https://gamma-api.polymarket.com/series?slug=us-gas-price-daily — 访问 2026-10-21 — 已读（id=12954，recurrence=daily，createdAt=2026-10-15T20:00:00Z）
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-17-2026 — 访问 2026-10-21 — 已读
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-18-2026 — 访问 2026-10-21 — 已读
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-19-2026 — 访问 2026-10-21 — 已读
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-20-2026 — 访问 2026-10-21 — 已读（已结算，获胜 <$4.2800）
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-21-2026 — 访问 2026-10-21 — 已读（未结算，feeSchedule.rate=0）
- https://gamma-api.polymarket.com/public-search?q=gas%20prices%20on — 访问 2026-10-21 — 已读（本次返回 5 个；10-19 不在结果中，以 series 为准）
- https://gamma-api.polymarket.com/public-search?q=aaa%20gas — 访问 2026-10-21 — 已读（本次返回 5 个 2022 一次性阈值事件；旧 totalResults=21 未复现）
- https://gamma-api.polymarket.com/events?slug=average-us-gas-prices-on-february-21 — 访问 2026-10-21 — 已读（2025 周度近似事件，5 档，feeSchedule=null；YES 成交 38 笔）
- https://gamma-api.polymarket.com/events?slug=average-us-gas-prices-on-february-28 — 访问 2026-10-21 — 已读（同上；YES 成交 32 笔）
- https://data-api.polymarket.com/trades?market=0x7e86451108a4918d6c138d8b2f37b9c458bc3e7f078b81407b67a5bac8019bb0&limit=1000 — 访问 2026-10-21 — 已读（10-16 获胜档逐笔成交；其余 conditionId 见 scratch 脚本与缓存）
- https://clob.polymarket.com/prices-history?market=43133386220466087855715215174741788871580219237805492517122006913395856825273&interval=max&fidelity=1 — 访问 2026-10-21 — 已读（10-16 获胜档 151 点；用于说明该序列不是可成交卖价，未用作收益回测）
- https://docs.polymarket.com/api-reference/markets/get-prices-history — 访问 2026-10-21 — 已读（文档只说明返回 `t/p`，未保证 `p` 是卖价；实测中间值与成交价可大幅偏离）
- https://gasprices.aaa.com/ — 访问 2026-10-21 01:34 UTC — 已读（仍显示 Today $4.2786、Price as of 10/20/26、Current Avg. $4.2786、Yesterday Avg. $4.2953，尚未翻到 10/21）
- https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com&from=20260801&to=20261021&output=json&filter=statuscode:200&fl=timestamp,digest — 访问 2026-10-21 — 已读（294 个快照，43 个在 04:00–10:59 UTC）
- https://web.archive.org/web/20261016044208id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10/15 值 4.3344，未翻页）
- https://web.archive.org/web/20261016110050id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10/16 值 4.3271，已翻页）
- https://web.archive.org/web/20261016124212id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（当天内未改）
- https://web.archive.org/web/20261016160308id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（当天内未改）
- https://web.archive.org/web/20261017110254id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10/17 值 4.3085）
- https://web.archive.org/web/20261018110336id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10/18 值 4.2988）
- https://web.archive.org/web/20261019095656id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10/19 值 4.2953；当天首个当天值快照）
- https://web.archive.org/web/20261020110138id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10/20 值 4.2786）
- https://web.archive.org/web/20261009071242id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（07:12 仍是前一天）
- https://web.archive.org/web/20261009074358id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（07:43 已是当天）
- https://web.archive.org/web/20260819060628id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（06:06 仍是前一天）
- https://web.archive.org/web/20260819100105id_/https://gasprices.aaa.com/ — 访问 2026-10-21 — 已读（10:01 已是当天）
- bots/quant/entries/quant-010-streaming-chart-nowcast.md — 访问 2026-10-21 — 已读（差异对比）
- bots/dot/entries/dot-004-confirmed-fact-price-convergence.md — 访问 2026-10-21 — 已读（差异对比）
- bots/muse/entries/muse-own-xmkt-resolution-lag.md — 访问 2026-10-21 — 已读（差异对比）
- bots/quant/notes/scheduler/scratch/P-quant-031/verify_out.txt、backtest_trades_out.txt、event_study_out.txt、aaa_snapshots_all.csv — 访问 2026-10-21 — 已读（本文所有数字的可复跑脚本与 stdout）
- bots/quant/replay/quant-031/replay.py、decision_points.csv、trades.csv、SUMMARY.md — 访问 2026-10-21 — 已读（第 2 轮回放材料，独立复跑得到同一组数字）
