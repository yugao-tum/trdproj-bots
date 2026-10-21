---
id: quant-031
name_zh: AAA汽油日档：10点值抢跑
name_en: AAA Daily US Regular Gas Price Bracket Front-Run
bot: quant
date: 2026-10-20
market: polymarket
pm_category: economics
kind: new
improves: -
category: E
return_type: convergence
instruments: "Polymarket 每日美国普通汽油 AAA 全国均价 1 美分分档（<$x.xx00 / $x.xx00-x.xx99 / … / $x.xx00+），同一事件 6 档"
venues: Polymarket
data: "Gamma（规则原文、分档、feeSchedule、已结算 outcomePrices）免费免密钥；data-api 逐笔成交（已关闭市场可查）免费免密钥；AAA gasprices.aaa.com 当日页面 + Wayback 存档，免费免密钥。日更系列 2026-10-15 创建，至 2026-10-20 共 6 个事件（4 个已结算）；完全同规则的已结算历史只有 4 个，另有 2 个 2025 周度近似事件"
test_2w: "按日期计独立结果（同一事件 6 档算 1 个）。两周前向约 14 个，历史完全同规则已结算 4 个，均 <30；失败标准：30 个事件的可成交样本中，扣费+半价差后中位净收益 ≤0，或 ≤0.95 的可成交率 <20%"
status: 草稿
confidence: 中
---

## 一句话

AAA 每天上午在 https://gasprices.aaa.com/ 把“Current Avg.”翻到当天值；Polymarket 的 1 美分分档市场在 10:00 AM ET 收盘并按该值结算。**真正的信息窗口在 AAA 翻页的那一刻（样本中约 07:00–10:20 UTC；06:35 仍是前一天），不在 10:00 ET**：等到 10:00 ET 再买，获胜档通常已报到 0.99 附近。拟定规则是：从 04:00 UTC 起每 2 分钟读一次 AAA 页面，确认“Price as of”已是当天且“Yesterday Avg.”是前一天后，买入与 Regular/Current Avg. 对应的那一档 YES，仅当可成交卖价 ≤0.95；持有到结算，否则不交易。

## 钱从哪里来

付钱的是 **AAA 翻页后仍挂着旧价格的对手方**。每天 00:00 UTC 时，市场还没有当天 AAA 值，只能按昨天值（如 4.3344）和其他信息猜测今天落在哪一档；AAA 在凌晨（美东约 3:00–6:20）把当天值放上网页后，哪一档会赢就变成确定事实。谁在翻页后仍按旧盘口报价，谁就把这段确定性让给先读到页面的人。

这笔钱能否持续，取决于三点，本文只证实了前两点：

- 模板每天重开一个事件（已证实：series `12954`，`recurrence=daily`，2026-10-15 创建，至 10-20 已有 6 个事件、4 个已结算）；
- AAA 的翻页时刻不固定（已证实：CDX 的 43 个 04:00–10:59 UTC 候选快照（连同事件日盘中快照共解析 47 个不同时刻）里，06:35/07:02/07:12 仍显示前一天、07:30 起看到当天；最晚到 10:22 才看到当天）；
- 翻页后的错价能留多久（**有后续成交的 3 个已结算事件里是 0.3–75 分钟；10-16 最后一笔 0.817 后再无成交，无法判断是否可买**；盘口极薄，10:00 ET 前价格已收敛，见“证据”）。

因此本条不是“10 点值抢跑”，而是“AAA 凌晨翻页后的短窗口抢跑”。把进场时间设在 10:00 ET 的版本在 4 个已结算事件上 **0 个 ≤0.95 的可成交样本**（见证据），不成立。

## 规则

### 市场模板与示例

- 模板：`Gas prices on <month> <day>?`；同一天一个 event，6 个互斥分档，每档宽 1 美分：
  - `<$4.3100`、`$4.3100-4.3199`、`$4.3200-4.3299`、`$4.3300-4.3399`、`$4.3400-4.3499`、`$4.3500+`（2026-10-16 实例）。
  - 档位随前一日价格平移；10-20 的档位是 `<$4.2800`、`$4.2800-4.2899`、…、`$4.3200+`。
- 示例：
  - https://polymarket.com/event/us-gas-price-on-october-16-2026
  - https://polymarket.com/event/us-gas-price-on-october-19-2026
  - https://polymarket.com/event/us-gas-price-on-october-20-2026
- 每个 event 的 6 个市场均为二元 YES/NO，`negRisk=true`、`restricted=true`；Gamma 实测 `feeSchedule={"exponent":1,"rate":0.04,"takerOnly":true,"rebateRate":0.25}`（6 个市场全部相同）。
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
- `resolutionSource` 字段为 `https://gasprices.aaa.com/`；event 的 `endDate` 为当天 14:00 UTC（10:00 ET）。4 个已结算事件的市场级 `umaResolutionStatus=resolved`，`closedTime` 在次日 02:08–16:11 UTC。

### 进场、出场、仓位

1. **数据时钟**：从 04:00 UTC 起，每 2 分钟 GET `https://gasprices.aaa.com/`，解析 `Price as of`、`Current Avg.`（Regular）和 `Yesterday Avg.`（Regular）。不使用任何预测模型；只读页面。
2. **触发**：`Price as of` = 当天日期，且 `Yesterday Avg.` = 前一天日期，且 Regular/Current Avg. 为 4 位小数。任一不满足就继续等。
3. **映射**：把当前值直接映射到 6 档之一（含边界按上节）。只买这一档的 YES。
4. **价格门槛**：只挂限价买单，价格 ≤ 0.95；若最优卖价 >0.95 或没有卖单，放弃当天，不追价。参考成交价只用 data-api 的实际成交，不用 CLOB 中间价。
5. **出场**：买入后持有到 10:00 ET 结算，不中途卖出，避免第二次吃单费。若当天 10:00 ET 前没有触发（页面一直未翻页），放弃。
6. **仓位**：单事件 ≤250 USDC；不超过可见卖单前 3 档总量的 10%；同一时间最多 1 个事件（模板本身每天 1 个）；单场所 ≤2,500 USDC。
7. **风控**：若页面在 10:00 ET 仍未显示当天值，不交易；若 `Current Avg.` 与 `Yesterday Avg.` 同时等于昨天值，视为未翻页；若页面出现两个不同全国均价，按规则原文的“表格优先、其他位置兜底”顺序取，无法判断则放弃。
8. **独立结果**：按日期计；同一天 6 档、同一结算源、同一页面，算 1 个。

## 证据

### 1. AAA 翻页时刻（已核实，网页存档）

用 Wayback CDX 取 `gasprices.aaa.com` 在 2026-08-01 至 2026-10-20 的 292 个 200 快照，其中 43 个候选落在 04:00–10:59 UTC；连同事件日盘中快照，共解析 47 个不同时刻的 `Price as of` 与 `Today's AAA National Average`。事件日附近的实测：

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

更长样本（2026-08 至 10-20，解析 47 个不同时刻；其中 04:00–10:59 UTC 的候选 43 个）显示：04:04、04:16、04:17、04:19、04:33、04:42、06:06、06:28、06:35、07:02、07:12 仍有“前一天”；07:30、07:43、07:57、08:12、08:46、08:50、09:56、10:01、10:22 已是“当天”。**没有在 06:00 前看到当天值；样本中最早看到当天值是 07:30，最晚一次翻页发生在 10:01–10:22 之间。** 这说明 10:00 ET（14:00 UTC）时值几乎总已公布，但也说明翻页时刻不是固定的 10:00 ET。

### 2. 事件研究：翻页后的价格跃迁（描述性，非规则回测）

对 4 个已结算事件和 1 个未结算观察（10-20），取获胜档 YES 在当天 07:00 UTC 后的第一笔成交，以及第一次 ≥0.95 的成交：

| 事件 | AAA 当日值 | 获胜档 | 07:00 后首笔 YES 成交 | 首次 ≥0.95 | 到 0.95 用时 | 收盘前最后一笔 |
|---|---:|---|---:|---|---:|---:|
| 10-16 | 4.3271 | $4.3200-4.3299 | 07:27:34 @ 0.8171 | 无 | — | 07:27:34 @ 0.8171 |
| 10-17 | 4.3085 | <$4.3100 | 07:29:00 @ 0.4902 | 07:56:59 | 28.0 分钟 | 07:56:59 @ 0.98 |
| 10-18 | 4.2988 | $4.2900-4.2999 | 07:41:14 @ 0.7624 | 07:41:32 | 0.3 分钟 | 14:00:00 @ 0.997 |
| 10-19 | 4.2953 | $4.2900-4.2999 | 07:30:50 @ 0.8753 | 08:45:53 | 75.0 分钟 | 10:20:54 @ 0.9884 |
| 10-20（未结算） | 4.2786 | <$4.2800 | 07:21:50 @ 0.8228 | 07:32:14 | 10.4 分钟 | 13:59:21 @ 0.999 |

**这是事后选赢家的事件研究，不是可执行规则的回测。** 它只说明：翻页后赢家档确实曾在 0.49–0.88 成交，并在 0.3–75 分钟内被抬到 0.95 以上；也说明 10:00 ET 前市场已经完成定价。不能把 07:00 的价格当成“当时已知赢家”的证据，因为本文没有 07:00 的 AAA 页面快照。

### 3. 历史回放：11:00 快照规则（主检验；不是预注册样本）

规则：在事件日 11:00 UTC（16/17/18 日分别为 11:00:50、11:02:54、11:03:36；19 日为 11:01:51）读到“当天值”后，买入对应档 YES，仅当该档在决策时点之后、14:00 UTC 之前有实际 BUY 成交价 ≤0.95；费用 0.04、另加 0.5 美分半价差；持有到结算。**选 11:00 的理由是四个事件日都有可核的页面快照；04:42/09:56 只有部分日期有，07:00 没有任何事件日快照。07/09 的结果是在 11:00 主检验之后补做的诊断，不是预注册。** 真正的前向预注册从 2026-10-21 开始：按“04:00 起每 2 分钟轮询、翻页后买 ≤0.95、持有到结算”执行，失败标准见下一节；历史 4 个事件只作回放，不冒充 30 个预注册样本。

- 4 个已结算事件：**0 个 ≤0.95 的可成交样本**（10-16、10-17 在 11:00 后到收盘前没有成交；10-18 在 11:25:41 有一笔 0.988457；10-19 在 11:01 后到收盘前无成交，最后一笔是 10:20:54 @ 0.98836）。
- 把门槛放宽到 0.99：**1 个成交**，10-18 11:25:41 @ 0.988457，75.5 份；费 0.000456/份，半价差 0.005/份，净 0.006087/份，合计 **+0.4595 USDC**。这只是 1 个样本，且几乎全部被半价差吃掉。
- 作为上界：若假设 07:00 时页面已经翻页，并用事后赢家去挑档，4 个事件都能在 0.4902–0.8753 成交，扣同样的费+半价差后中位净 0.1986/份、合计 +101.82 USDC（20–264 份/事件）。**这个数不能用**：它同时用了“07:00 已知页面值”和“事后知道哪档赢”两个未证条件；本文把它列为上界，不作为收益结论。

### 4. 周内 2 个 2025 近似事件（不同规则，不计入 4 个）

- `average-us-gas-prices-on-february-21`（2025-02-21，5 档，close 12:00 UTC，`feeSchedule=null`）：获胜 `$3.16` 档收盘前最后 YES 成交 08:16:08 @ 0.9857。
- `average-us-gas-prices-on-february-28`（2025-02-28，5 档，close 12:00 UTC，`feeSchedule=null`）：获胜 `$3.14 or less` 档 10:26:39 有 SELL @ 0.99。
- 这两个是“某日均价落在第一、二位数字档”，没有 10:00 ET 快照条款，且是周度/一次性事件；只能说明 AAA 分档模板不是 2026-10 才出现，**不能算作同规则的独立结果**。

## 数据

- Gamma（免费、免密钥）：
  - `https://gamma-api.polymarket.com/events?series_id=12954&limit=100`：返回 6 个事件（4 已结算、2 未结算），endDate 2026-10-16 至 2026-10-21。调度侦察记录的是 9 个事件（6 已结算），与本次实抓不一致；本次以 Gamma 实抓为准，`public-search?q=gas%20prices%20on` 也只返回这 6 个日更模板，未找到另外 3 个事件。
  - `https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-16-2026`：规则原文、6 档、`feeSchedule`、`outcomePrices`、`closedTime`。
  - `https://gamma-api.polymarket.com/public-search?q=gas%20prices%20on`：返回 9 个事件，其中 6 个是本日更模板；另有 2 个 2025 事件。
  - `https://gamma-api.polymarket.com/public-search?q=aaa%20gas`：`totalResults=21`；其中 17 个已关闭，但多数是 2022 的“某日前跌破 $4”一次性阈值市场或月末“Will gas hit __”市场，**不是** 1 美分日档模板，未计入独立结果。
- data-api（免费、免密钥）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=0`；已关闭市场可查，返回 `timestamp`、`side`、`price`、`size`、`outcome`。本文 4 个已结算事件共 24 个市场，YES 成交合计 50 笔（逐事件 6/10/21/13），单个市场 0–12 笔；2025 两个事件 10 个市场共 70 笔（38/32）。**成交不是盘口**：只能证明某一刻有人以该价成交，不能证明决策时点一定有同样卖价。
- AAA（免费、免密钥）：
  - 当日页面 `https://gasprices.aaa.com/`：2026-10-20 15:14 UTC 读取，显示 `Today's AAA National Average $4.2786`、`Price as of 10/20/26`；表 `Current Avg.` Regular = `$4.2786`、`Yesterday Avg.` Regular = `$4.2953`。
  - 历史页面用 Wayback：`https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com&from=20260801&to=20261020&output=json&filter=statuscode:200&fl=timestamp,digest`；逐快照用 `https://web.archive.org/web/<timestamp>id_/https://gasprices.aaa.com/`。
- 起始日期：日更模板 2026-10-15 创建；AAA 页面本身有更长的历史，但**Polymarket 同模板的已结算历史只有 4 个**。历史可执行盘口无公开来源；GUIDE 第 8 节已说明，CLOB `prices-history` 只保留最近 2–3 周，不能补 4 个事件之前的盘口。

## 两周内怎么检验

- **独立结果怎么数**：按日期计，同一天 6 档算 1 个；同一日期不同档、同一结算源不独立。
- **历史**：完全同规则的已结算事件只有 **4 个**（2026-10-16 至 10-19），加上 2 个 2025 近似事件也只有 6 个；**不足 30 个**，不能在本条内完成 GUIDE 门槛 2 的历史样本要求。本文不把 4 个事件伪装成 30 个。
- **两周前向**：从 2026-10-21 起每天记录 1 个事件，两周约 **14 个**，仍 <30。两周内只能验证：
  1. AAA 翻页时刻分布（是否落在 06:30–10:30 UTC）；
  2. 翻页后到 10:00 ET 之间，是否还出现 ≤0.95 的可成交卖价；
  3. 扣费+半价差后单笔净收益的符号。
- **失败标准（预先写死）**：
  - 30 个事件的可成交样本中，扣费+0.5 美分半价差后的**中位净收益 ≤0**；或
  - ≤0.95 的可成交率 <20%（说明翻页后价格已被瞬间抹平，抢不到）；或
  - 超过 20% 的成交发生在 >0.99（说明只剩尾部小钱，不值得占用资金）。
  - 任一触发即判失败，不再前向记录。
- **不做**：不用 07:00 事后赢家回放冒充规则检验；不把同一事件的 6 档算 6 个结果；不把 2025 的 2 个不同规则事件算进 4 个。

## 成本与容量

- **吃单费**：Gamma 实测该模板 6 个市场全部 `rate=0.04`、`takerOnly=true`、`rebateRate=0.25`。按 GUIDE 第 8 节：
  - `fee/份 = 0.04 × p × (1−p)`。
  - p=0.82：`0.04×0.82×0.18 = 0.005904/份`，占价格 **0.72%**。
  - p=0.95：`0.0019/份`，占价格 **0.20%**。
  - p=0.99：`0.000396/份`，占价格 **0.04%**。
- **半价差假设**：分档宽度 1 美分，历史盘口无公开来源；按 **0.5 美分/份** 计（即假设 1 美分买卖价差）。p=0.82 时占价格 0.61%，p=0.95 时占 0.53%，p=0.99 时占 0.51%。本文所有净收益都扣了这 0.5 美分；若实际价差更宽，结果更差。
- **粗算**：
  - p=0.82 买入：毛 0.18/份，扣费 0.005904 + 半价差 0.005 = **净 0.169096/份（20.6%）**；但这是事件研究里的价格，不是 11:00 规则能拿到的价格。
  - p=0.988457（唯一一个 11:00 后 ≤0.99 的成交）：毛 0.011543，扣费 0.000456 + 半价差 0.005 = **净 0.006087/份（0.62%）**。
  - p=0.95：毛 0.05，扣费 0.0019 + 半价差 0.005 = **净 0.0431/份（4.54%）**。
- **容量**：
  - 事件总成交额（Gamma 自报）：10-16 **1,728.79**、10-17 **950.98**、10-18 **2,193.14**、10-19 **895.15** USDC。
  - 获胜档市场成交额：10-16 **1,626.55**、10-17 **378.77**、10-18 **965.43**、10-19 **372.37** USDC。
  - 翻页后实际成交笔数 1–12 笔/市场，单笔 20–264 份；按 0.82 计约 16–216 USDC/笔。单事件可放 **100–300 USDC**，但需要看到卖单；看不到深度时按 ≤250 USDC/事件。
  - 频率 1 次/天、约 30 次/月；资金占用从 07:00–08:00 UTC 到 10:00 ET 约 6–7 小时，结算后到账可能到次日 02:00–16:00 UTC，按 **1–2 天**计。
  - 5,000 USDC 放得下（单场所 ≤2,500、单事件 ≤250），但**大部分时间资金闲置**；这是一个小额、低频、容量很小的机会，不适合作为主力收益来源。

## 风险

- **最大风险：没有可抢的价**。10:00 ET 版本 4 个事件 0 个 ≤0.95 成交；翻页后赢家档在 0.3–75 分钟内被抬到 0.95 以上，且 Oct 20 从 0.8228 到 0.989 只用了 10.4 分钟。等你读到页面、连上盘口，可能只剩 0.99 的 1% 空间，扣半价差后接近 0。
- **AAA 翻页时刻不固定**：样本中 06:35 仍有前一天、10:01 才翻到当天。固定 10:00 ET 进场会太晚；固定 07:00 进场会在部分日期早于翻页，读到的是昨天值，买错档。
- **页面口径风险**：`Price as of` 与 `Yesterday Avg.` 必须同时满足；AAA 可能短时显示旧缓存、双值或缺失。规则给了“其他位置兜底”和“用最近一次已发布值”的兜底，但兜底值可能不是你早上读到的值。
- **边界风险**：4 位小数、1 美分档，4.2900 归 `$4.2900-4.2999` 而不是 `<$4.2900`；按 2 位或四舍五入会买错档。
- **成交/深度风险**：市场极薄（获胜档总成交 372–1,627 USDC），历史只有成交价、没有盘口；250 USDC 也可能吃掉数档或无法成交。data-api 只保留最近约 2 万笔，本文市场成交笔数少，但仍不能保证是全部成交。Gamma 的 `volume`/`outcomePrices` 是平台自报，未用链上收据逐笔核实；AAA 数值是页面原样抄录。
- **结算/平台风险**：Polymarket `restricted=true`、UMA 结算；若 AAA 当天页面异常，规则可能按 23:59 ET 的显示值或最近一次已发布值结算，与你买入时读到的值不同。已结算事件 `closedTime` 在次日 02:08–16:11 UTC，资金实际锁 1–2 天。
- **竞争风险**：07:2x 的成交簇说明已有参与者盯页面；新进入者要赢过他们的轮询和下单速度。
- **样本风险**：只有 4 个完全同规则的已结算事件，且 2026-10-15 才上线；任何“胜率/中位收益”都只是 4 个点，不能外推。

## 与最接近条目的区别

- **dot-004（已定事实后的报价收敛）**：最接近的宽口径机制。相同点是“权威事实已公开、买低于 1 的获胜侧”；不同点是 dot-004 是一次性政治官宣、无固定日更节奏、需要解析公告文本；本条是每天固定模板、AAA 页面自动翻页、1 美分分档、10:00 ET 硬截止，且关键变量是“AAA 翻页时刻 vs 市场收盘”。若主审按更宽口径认定二者为同一机制，本条应降为 dot-004 的 `kind: supplement`，`improves: dot-004`；本文按新模板/新关键变量写成 `new`，并在此明示这一判断风险。
- **muse-own-xmkt-resolution-lag（结算窗口时滞折价）**：muse 做的是**收盘后、UMA 正式结算前**的折价（风险是争议/锁仓 4–6 天）；本条是**收盘前 3 小时**、AAA 页面已翻页但市场未完全跟上的窗口，没有 UMA 争议窗口，风险是抢不到价而不是结算争议。
- **quant-010（周榜日更抢跑）**：quant-010 用日榜**估算**尚未发布的官方周榜；本条不估算——AAA 当天值已经原样发布，只比市场报价快。
- **quant-005（发帖数分档）**：quant-005 用已观测部分计数 + 计数过程模型预测最终档；本条是确定值已发布，无模型。
- **quant-015（全球气温 nowcast）/ dot-003（宏观 nowcast）**：都是模型 nowcast 尚未发布的统计值；本条结算值已在页面上，属于信息时滞而非 nowcast。
- **known/**：135 条中没有汽油/AAA 条目；`bots/quant` 也没有 gas 条目。仓库内 grep `gasoline|gasprices|gas price|AAA` 只命中 dot-047/049 的无关文本。

## 门槛自查

1. **机制说得清**：满足（有条件） — 付款方是 AAA 翻页后仍挂旧价的对手方；机制每天重复，但有后续成交的 3 个事件窗口只有 0.3–75 分钟（10-16 无后续成交），且 10:00 ET 版本无价可抢。
2. **有免费数据能检验**：不满足 — Gamma、data-api、AAA 页面/Wayback 都免费免密钥，但完全同规则的已结算事件只有 4 个（加 2 个 2025 近似事件也只有 6 个），不足 30 个；只能前向记录。
3. **小资金能做**：满足（有条件） — 单事件 100–300 USDC、每天 1 次、单场所 ≤2,500，5,000 USDC 放得下；但容量小、大部分时间闲置。
4. **不重复**：不确定 — 仓库无 gas/AAA 条目；但宽口径下可能被视为 dot-004 的变体（见上节）。若判为同一机制，应改为 supplement，而不是 new。
5. **扣成本后粗算够用**：不满足 — 11:00 规则 4 个事件 0 个 ≤0.95 成交；放宽到 0.99 只有 1 笔、净 +0.4595 USDC；07:00 的 +101.82 USDC 是事后赢家+页面已翻页假设的上界，不能当证据。
6. **两周内能检验**：不满足 — 每天 1 个事件，两周约 14 个，历史 4 个，均 <30；两周只能验证翻页时刻和可成交率，不能完成 30 个独立结果。
7. **出处可查**：满足 — 规则原文、6 档、费率、成交、AAA 页面与 Wayback 快照均有 URL、访问日期和片段；脚本与输出在 `bots/quant/notes/scheduler/scratch/B30/`。

## 出处

- https://polymarket.com/event/us-gas-price-on-october-16-2026 — 访问 2026-10-20 — 已读（HTTP 200；页面与 Gamma 同一 event，示例链接）
- https://polymarket.com/event/us-gas-price-on-october-19-2026 — 访问 2026-10-20 — 已读（HTTP 200；示例链接）
- https://polymarket.com/event/us-gas-price-on-october-20-2026 — 访问 2026-10-20 — 已读（HTTP 200；示例链接）
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-16-2026 — 访问 2026-10-20 — 已读（规则原文逐字、6 档、feeSchedule、结算结果）
- https://gamma-api.polymarket.com/events?series_id=12954&limit=100 — 访问 2026-10-20 — 已读（6 个事件、4 个已结算、endDate）
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-17-2026 — 访问 2026-10-20 — 已读
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-18-2026 — 访问 2026-10-20 — 已读
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-19-2026 — 访问 2026-10-20 — 已读
- https://gamma-api.polymarket.com/events?slug=us-gas-price-on-october-20-2026 — 访问 2026-10-20 — 已读（未结算观察）
- https://gamma-api.polymarket.com/public-search?q=gas%20prices%20on — 访问 2026-10-20 — 已读（9 个事件；6 个日更模板 + 2 个 2025 事件 + 1 个无关）
- https://gamma-api.polymarket.com/public-search?q=aaa%20gas — 访问 2026-10-20 — 已读（totalResults=21，17 已关闭；多数为 2022 一次性阈值/月末模板）
- https://gamma-api.polymarket.com/events?slug=average-us-gas-prices-on-february-21 — 访问 2026-10-20 — 已读（2025 周度近似事件，5 档，feeSchedule=null）
- https://gamma-api.polymarket.com/events?slug=average-us-gas-prices-on-february-28 — 访问 2026-10-20 — 已读（同上）
- https://data-api.polymarket.com/trades?market=0x7e86451108a4918d6c138d8b2f37b9c458bc3e7f078b81407b67a5bac8019bb0&limit=1000 — 访问 2026-10-20 — 已读（10-16 获胜档逐笔成交；其余 conditionId 见 scratch 脚本与缓存）
- https://gasprices.aaa.com/ — 访问 2026-10-20 15:14 UTC — 已读（Today $4.2786，Price as of 10/20/26，Current Avg. $4.2786，Yesterday Avg. $4.2953）
- https://web.archive.org/cdx/search/cdx?url=gasprices.aaa.com&from=20260801&to=20261020&output=json&filter=statuscode:200&fl=timestamp,digest — 访问 2026-10-20 — 已读（292 个快照，43 个在 04:00–10:59 UTC）
- https://web.archive.org/web/20261016044208id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10/15 值，未翻页）
- https://web.archive.org/web/20261016110050id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10/16 值 4.3271，已翻页）
- https://web.archive.org/web/20261016124212id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（当天内未改）
- https://web.archive.org/web/20261016160308id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（当天内未改）
- https://web.archive.org/web/20261017110254id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10/17 值 4.3085）
- https://web.archive.org/web/20261017172845id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（当天内未改）
- https://web.archive.org/web/20261018110336id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10/18 值 4.2988）
- https://web.archive.org/web/20261019110151id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10/19 值 4.2953）
- https://web.archive.org/web/20261019194806id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（当天内未改）
- https://web.archive.org/web/20261020110138id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10/20 值 4.2786）
- https://web.archive.org/web/20261009071242id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（07:12 仍是前一天）
- https://web.archive.org/web/20261009074358id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（07:43 已是当天）
- https://web.archive.org/web/20260819060628id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（06:06 仍是前一天）
- https://web.archive.org/web/20260819100105id_/https://gasprices.aaa.com/ — 访问 2026-10-20 — 已读（10:01 已是当天）
- bots/quant/entries/quant-010-streaming-chart-nowcast.md — 访问 2026-10-20 — 已读（差异对比）
- bots/dot/entries/dot-004-confirmed-fact-price-convergence.md — 访问 2026-10-20 — 已读（差异对比）
- bots/muse/entries/muse-own-xmkt-resolution-lag.md — 访问 2026-10-20 — 已读（差异对比）
- bots/quant/notes/scheduler/scratch/B30/rule_test3_out.txt、aaa_snapshots.csv、collect_run.txt — 访问 2026-10-20 — 已读（本文所有数字的可复跑脚本与 stdout）
