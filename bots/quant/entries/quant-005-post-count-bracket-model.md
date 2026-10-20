---
id: quant-005
name_zh: 发帖数分档：部分计数加计数过程
name_en: Polymarket post-count brackets (Elon Musk tweets / Trump Truth Social) vs count-process model
bot: quant
date: 2026-10-20
market: polymarket
pm_category: mentions
kind: new
improves: -
category: S
return_type: direction
instruments: "Polymarket 档位模板：Elon Musk 在 X 的发帖数落在哪一档（48 小时窗口，<40 / 40-64 / 65-89 / … / 240+）；同类 Trump Truth Social 7 天窗口（<20 / 20-39 / … / 200+）"
venues: Polymarket
data: Gamma（events/markets，含 feeSchedule 与已结算 outcomePrices）、CLOB book 与 prices-history、xtracker.polymarket.com 的 /api/users/<handle>/posts 逐条帖时间戳（回溯到 2025-10-31）；全部免费免密钥；历史盘口 L2 无公开来源
test_2w: 按事件计（同一 event 的 10–11 个档算 1 个结果），历史可重构 ≥30 个独立已结算事件，2 周内可完成；失败标准：条件样本下买入侧的扣费后中位净收益 ≤0
status: 草稿
confidence: 中
---

> **2026-10-20 降为草稿（撤回第 1 轮复核）**：按 `bots/quant/notes/q005-hist/REPORT.md`（PR #14）的历史可成交价回测（xtracker 逐条帖时间戳重建窗口计数 + data-api 已关闭市场成交），50% 决策点 **252 个独立事件触发（≥30）**，每份净收益中位 **−0.034596**、均值 **−0.012555**、每美元投入中位 **−1.047500**、命中率 **0.0992（25/252）**；ISO 周 block bootstrap 均值 95% CI **[-0.048273, 0.026127]** 跨 0；模型 log loss（原始经验模型 **2.269900**、NB **1.802055**）均劣于市场归一化价 **1.473311**（n=225）。75% 决策点 n=197、中位 **−0.036922** 同为负。预先写死的失败标准触发 → **FAIL**。字面口径 `run_output_literal_le.txt`（只保留 `partial ≤ n_elapsed`、去掉“最终计数 ≥ n_elapsed”硬约束，会买入逻辑上已不可能的档位）n=257、中位 **−0.023076**、命中率 **0.0778（20/257）**，结论同为 FAIL。门槛 5 因此改为不满足，门槛 6 记“满足（历史口径）”。正文以下其余内容保留原稿。

## 一句话

在 “Elon Musk # tweets / Trump # Truth Social posts” 这类分档事件里，窗口开始后先用 xtracker 的逐条帖时间戳数出**已观测部分计数**，再用负二项剩余计数过程算各档概率，只买“模型概率 − 吃单价 − 吃单费”仍为正的那一档，持有到窗口结束按结算价兑付。

## 钱从哪里来

付钱的是**在窗口早期按“无条件分布/直觉”给各档出价的对手方**。这类事件每 2–3 天重开一个新窗口、开盘时窗口内一条帖都没有，任何定价都只能靠历史基准率；而真实信息（这 48 小时马斯克发不发）要到窗口中后段才明朗。谁在窗口前 1/3 仍按历史平均定价，谁就把钱付给已经数过实际帖数的一侧。

持续性依赖两点，两点都未核实：(a) 新窗口持续被创建（已核实：series `elon-tweets-48h` 在 2026-01-03 至 2026-08-22 的 100 条已结算事件里每月 10–13 个）；(b) 报价方不快速跟随 tracker。第 (b) 点本条**没有**测量。

## 规则

以下引文来自 2026-10-20 实抓的 Gamma `description` 字段原文。

**Elon 48h 示例**（event `elon-musk-of-tweets-october-19-october-21-2026`，title “Elon Musk # tweets October 19 - October 21, 2026?”，`endDate=2026-10-21T16:00:00Z`，`negRisk=true`，`restricted=true`，tags 含 `Tweet Markets`、`Recurring`）：

- 计数口径原文：“This market will resolve according to the number of times Elon Musk (@elonmusk), posts on X from October 19 12:00 PM ET to October 21, 2026 12:00 PM ET.”（起始时间原文未写年份，照抄。）
- 什么算：“only main feed posts, quote posts and reposts will count. Replies will NOT count towards the total - however, replies on the main feed such as https://x.com/elonmusk/status/1786073478711353576 will be counted by the tracker.”
- 删除：“Deleted posts will count as long as they remain available long enough to be captured by the tracker (~5 minutes).”；“Community reposts which are not counted by the tracker not count toward the total.”（原文语法如此。）
- **结算数据源**：“The resolution source for this market is the 'Post Counter' figure for posts found at https://xtracker.polymarket.com. Individual posts can be viewed by clicking \"Export Data\". If the tracker does not update correctly in accordance with the rules, X itself may be used as a secondary resolution source.”（`resolutionSource` 字段另填 `https://x.com/elonmusk`。）
- 截止/日界：窗口 2026-10-19 16:00Z → 2026-10-21 16:00Z（12:00 PM ET = 16:00Z 换算），共 48 小时。
- 档位（10 个，全列）：`<40`、`40-64`、`65-89`、`90-114`、`115-139`、`140-164`、`165-189`、`190-214`、`215-239`、`240+`，25 一档、无缺口。
- 缺数据怎么办：规则只说 tracker 更新不正确时可用 X 作二手源，**未**写 tracker 停机/丢帖的补偿办法 → 未查到。

**Trump 示例**（event `donald-trump-of-truth-social-posts-october-20-october-27-2026`，`endDate=2026-10-27T16:00:00Z`）：同一套文字，窗口“between October 20, 12:00 PM ET and October 27, 2026, 12:00 PM ET”，数据源同为 xtracker 的 “Post Counter”，二手源为 “Truth Social itself”。11 档：`<20`、`20-39`、…、`180-199`、`200+`（20 一档）。

**本条的进场/出场规则（拟定）**

1. 窗口开始后每小时抓一次 xtracker 该 handle 的逐条帖时间戳，数出 `n_elapsed`（只数 `createdAt` 落在窗口内的记录）。
2. 用同一 feed 的历史逐条时间戳，取与当前**同一档窗口长度**（48h 或 7d）且**同一已过时长比例**的历史窗口，做经验条件分布；负数二项拟合只作平滑，不作主口径。
3. 对每个档 `k` 算 `p_k`，与 CLOB 最优卖价 `ask_k` 比：`edge_k = p_k − ask_k − fee_k − halfspread_k`，只取 `edge_k > 0` 的最大一档买入；`p_k` 用保守版（去掉最高的 10% 历史窗口，即“乐观样本剔除”）。
4. 出场：持有到结算（不中途卖，避免第二次吃单）。若窗口最后 6 小时 `n_elapsed` 已越过某档下界且盘口 `ask>0.97`，视为已定价，不再加仓。
5. 仓位：单档不超过该档盘口可见卖单前 3 档累计股数的 30%；单事件 ≤400 USDT；同时最多 3 个事件在跑；场所总额 ≤2,500 USDT（总资金 5,000）。
6. 风控：不开裸卖；只买入；单个窗口的亏损上限即投入本金。若 tracker `lastSync` 超过 60 分钟未更新，本窗口全部跳过（见“风险”里 `lastSync` 与 `importedAt` 不一致的实测）。

## 证据

### 已核实（本文实抓 + 自算）

- **计数可重建，且与已结算结果一致**：用 xtracker 的 `/api/users/elonmusk/posts` 取到 13,671 条记录，`createdAt` 从 `2025-10-31T00:17:35Z` 到 `2026-10-20T02:41:54Z`。数落在 `[2026-10-17T16:00Z, 2026-10-19T16:00Z)` 的条数 = **62**（本文算术）。该事件 `elon-musk-of-tweets-october-17-october-19-2026` 的 Gamma 结算为：`40-64` 档 `outcomePrices=["1","0"]`、`umaResolutionStatus="resolved"`、`closedTime=2026-10-19 18:03:14+00`，其余 9 档均 `["0","1"]` → 62 落在 40-64 内，**一致**。官方 “Post Counter” 的最终数值本身**未查到**（xtracker 的 tracking 对象里 `metrics={}`、`target=null`，不返回计数）。
- **过度离散是真实的**：以该 feed 计 180 个自然日（截至 2026-10-19）的日发帖数，均值 **30.678**、样本方差 **281.728**，方差/均值 = **9.18**（本文算术）→ 泊松（比值应为 1）明显不够，必须用负二项/经验分布。
- **48h 窗口分布**：取 160 个滚动 48h 窗口（结束于 16:00Z，2026-05-13 至 2026-10-19），均值 **63.20**、方差 **673.36**、最小 **22**、最大 **171**；其中 **78/160 = 48.7%** 落在 40-64 档（本文算术）。注意这 160 个窗口**互相重叠**，不是 160 个独立结果。
- **当前窗口的部分计数**（实抓时刻 2026-10-20T02:41:54Z）：窗口 `2026-10-19T16:00Z → 2026-10-21T16:00Z`，已过 **10.70 h**、剩 **37.30 h**，已观测 **11** 条（本文算术）。
- **经验条件分布**：在 160 个历史窗口里，取“前 10.70 h 计数 ≤ 11”的 **61** 个窗口，其最终总数的均值 **51.3**、中位 **51**、最小 22、最大 100；落档：`<40` 15/61 = **0.25**、`40-64` 37/61 = **0.61**、`65-89` 7/61 = **0.11**、`90-114` 2/61 = **0.03**、`115+` 0/61（本文算术）。
- **同刻市场价**（同一快照，Gamma `outcomePrices` 的 Yes 侧）：`<40` 0.07、`40-64` 0.55、`65-89` 0.335、`90-114` 0.055、`115-139` 0.0085、`140-164` 0.004、`165-189` 0.0015、`190-214` 0.0005、`215-239` 0.0005、`240+` 0.0005；十档相加 = **1.025**（本文算术，中间价口径的 2.5¢ overround）。
- **盘口**：CLOB `book`（token 为 `40-64` 的 Yes，`224420617112...891148`）返回 best bid **0.54**（257.39 股）/ best ask **0.57**（232.52 股），中间价 **0.555**，价差 **0.03**；响应 `timestamp=1792468954667`（毫秒，本文换算为 2026-10-20T04:02:34Z）。前 3 档卖单 0.57/232.52、0.58/214.45、0.59/86.91 ≈ 533 股 / 约 310 USDT。
- **已结算市场也有价格历史**：对上面同一已结算事件的 `40-64` Yes token 请求 `prices-history?interval=max&fidelity=60`，返回 **86** 个点，首点 `t=1792083636 p=0.515`，末点 `t=1792432830 p=0.9995`（覆盖约 97 小时，含窗口前与窗口内）。只测了这 1 个 token，其余 token 未测。
- **事件频率**：series `10816`（slug `elon-tweets-48h`，title “Elon Tweets 48H”，`recurrence="daily"`，`createdAt=2025-12-29T18:59:23Z`，`volume24hr=346875.646022`）查 `closed=true` 返回 100 条事件（接口上限），`endDate` 从 `2026-01-03T17:00:00Z` 到 `2026-08-22T16:00:00Z`，按 endDate 月份计：2026-01 **13**、02 **12**、03 **13**、04 **13**、05 **13**、06 **13**、07 **13**、08 **10**（08 为 100 条截断，非整月）。Trump series 为 `11108`（`trump-truth-social`，`recurrence="daily"`，`volume24hr=21980.33482`），搜索只看到 3 个并行 7 天窗口 → 约 **4 个/月**。合计约 **17 个事件/月**（13 + 4，本文算术）。
- **成交量**：Elon Oct 19-21 event `volume=94153.668804`、`liquidity=53563.09908`；Trump Oct 20-27 event `volume=11389.525684`、`liquidity=31857.22875`（同一快照字段，来源自报，未核实）。

### 未做（不要当成结论）

- **没有回测**：`backtest_count=0`、`observed_net_return=null`。上面的 0.61 vs 0.55 只是**一个时点的条件频率 vs 一个时点的盘口**，样本是 1 年重叠窗口、且条件只用了“前 10.7h 计数 ≤ 11”，没控制星期几/时段（该 feed 的日内节奏很强：2026-10-17 28 条、10-18 36 条、10-19 仅 21 条）。
- 没有做成交层面的分析，因此“谁在付钱”是按价格差推断的，不是从 data-api 成交里数出来的。

## 数据

- `https://gamma-api.polymarket.com/events?slug=<slug>`：规则原文、档位、`outcomePrices`、`feeSchedule`、`endDate`、已结算市场的 `closedTime`/`umaResolutionStatus`/`resolutionSource`。免费、免密钥。
- `https://gamma-api.polymarket.com/events?series_id=10816&closed=true&limit=500`：返回 **100** 条（实际被截到 100，`limit` 上限）；统计每月事件数用它 + 翻页。
- `https://gamma-api.polymarket.com/public-search?q=elon%20musk%20tweets&limit_per_type=25&events_status=closed`：`totalResults=342`（含各种历史变体，不是纯 48h 系列）。
- `https://clob.polymarket.com/book?token_id=<id>`：当前盘口；需带 `User-Agent`，不带时 `urllib` 默认 UA 返回 **403**（实测）。
- `https://clob.polymarket.com/prices-history?market=<token_id>&interval=max&fidelity=60`：**已结算市场也能取**，实测 86 个 1 小时点。`startTs/endTs` 参数实测返回 **400 Bad Request**。
- `https://xtracker.polymarket.com/api/users/elonmusk`：`platformId=44196397`、`lastSync=2026-10-13T22:55:30Z`、`lastSyncError=2026-10-20T04:00:38Z`、7 个 `trackings`（全部 `isActive=true`）。
- `https://xtracker.polymarket.com/api/users/elonmusk/posts?limit=100&offset=0`：一次返回 **13,671** 条（`limit` 被忽略，4.84 MB），字段 `createdAt`/`importedAt`/`platformId`/`content`/`metrics`。这是本条最关键的数据源：逐条帖时间戳可回溯到 2025-10-31。
- 起始日期：帖级历史 **2025-10-31**；价格历史未测出统一起点（一次实测覆盖 97 小时）。
- 缺失：历史 L2 盘口（GUIDE 第 8 节已说明无公开源）；tracker 的官方 Post Counter 数值。

## 两周内怎么检验

- 数据：xtracker 帖级历史（已到手）+ `prices-history` 取已结算事件的每小时价。
- 独立结果**按事件计**：同一 event 的 10 档算 **1** 个结果（档间是同一计数过程，不独立）；同一时间窗内 Elon 与 Trump 是两个事件，但日度共同驱动（同一天的市场情绪）会把相关性拉高，主口径**只用 Elon 48h 系列**。series 10816 已结算事件 100 条（2026-01-03 至 2026-08-22），**≥30 个独立事件可在两周内凑齐**；重叠窗口同时开跑时，按“结算时刻去重到每 48 小时一个”的保守口径会掉到约 90 个，仍 ≥30。
- 步骤：对每个历史事件，重建“前 x% 时长”的观测计数（x 取 20%/30%/50%），跑上面的经验条件分布 + 保守版剔除，得到每档 `p_k`，与 `prices-history` 在该时点的**可成交价近似**（用该小时点价格 ± 当时半个价差；历史价差未取得，先用 1.5¢ 假设并在结果里标为假设）比较，算扣费后收益。
- 失败标准（预先写死）：扣费后逐事件净收益的**中位数 ≤ 0**，或胜率 < 50% 且均值 ≤ 0 → 判失败，不再往前记录。次级失败：`p_k` 与实际落档的 Brier 分数不优于“无条件基准率”分布。
- 若 30 个事件里被剔除的（skip 率）超过 60%，也判失败——说明门槛太紧、没有可执行机会。

## 成本与容量

- **吃单费**按 Gamma 该市场实际返回的 `feeSchedule`：`{exponent: 1, rate: 0.05, takerOnly: true, rebateRate: 0.25}`，10 个档全部相同。用 GUIDE 第 8 节公式 `fee = 份数 × feeRate × p × (1−p)`：p=0.57 时每份 `0.05×0.57×0.43 = 0.012255`（占价的 **2.15%**）；p=0.55 时 `0.012375`（**2.25%**）；p=0.07 时 `0.003255`（**4.65%**）；p=0.335 时 `0.011139`（**3.33%**）（本文算术）。价格越低，费占本金比例越高，尾部档尤其贵。
- **注意与 GUIDE 表格的差异**：GUIDE 第 8 节把“提及”列为 `0.04`，而 Gamma 这 10 个市场实际返回 `rate=0.05`。本条**以 Gamma 实际值为准**，并记下这处不一致；Trump 的 11 个档同样 `rate=0.05`。
- **价差**：`40-64` 实测 mid 0.555、半价差 **0.015**（占 mid 的 2.70%）。吃单实际上要付**全**价差 0.03（0.54↔0.57），GUIDE 口径的“半价差”只用于把 mid 价折成可成交价。
- 单笔成本（GUIDE 口径 = 费 + 半价差）= `0.012375 + 0.015 = 0.027375`/份，占 mid 0.555 的 **4.93%**。
- 同一时点的粗算（**这是一个时点的算术，不是回测、不是收益证明**）：条件样本给 `40-64` 0.61、市场 mid 0.555 → `0.61 − 0.555 = 0.055`，减 0.027375 = **+0.0277/份 = +4.9%**（对 0.555）。`<40` 更极端（0.25 vs 0.07），但 61 个样本里 15 个落 `<40`，且没控时段；这个差距大到不像纯套利，更像“市场知道 feed 之外的信息”或“这 10.7 小时恰好是低发帖时段”，**不能**按 0.25 下单。
- **容量**：单档前 3 档卖单约 **533 股 ≈ 310 USDT**（`40-64`，实测），所以单事件最多也就几百 USDT 级别。加上 400 USDT/事件的上限，5,000 USDT 里同时跑 3–6 个事件，**放不满**是常态；单场所 2,500 的上限不构成约束。
- **频率**：约 17 事件/月（Elon 48h 13 + Trump 周度 4）。资金占用 2 天（Elon）/ 7 天（Trump）。
- **资金占住天数**：Elon 48h ≈ 2 天/次；按 17 事件/月、每次 400 USDT 计，月周转 ≈ 8,000 USDT·天量级——规模小，属“小额多次”的机会，不适合当主力收益来源。

## 风险

- **模型/样本风险（最大）**：条件样本来自 160 个**重叠**窗口、只 1 年、没控星期几与时段；剔除最高 10% 只是缓解而非消除。真实落档一旦比条件频率更集中（当前窗口 28/36/21 条/日的节奏就与 180 日均值 30.7 完全不同），`<40` 的 0.07 可能是对的、0.25 是错的。
- **数据源风险**：tracker 是 Polymarket 自己的界面站。实测 `lastSync=2026-10-13T22:55:30Z` 而最新一条帖的 `importedAt=2026-10-20T02:45:30Z`，同时 `lastSyncError=2026-10-20T04:00:38Z` 非空 —— `lastSync` 字段不可当新鲜度指标，必须用 `importedAt`/`createdAt` 判断。若 tracker 漏帖或延迟 >5 分钟，口径与结算源不一致，本条算出来的 `n_elapsed` 会系统性偏低（规则：删除的帖只要被 tracker 抓到也算）。
- **结算源风险（2026-10-20 回测实测）**：`bots/quant/notes/q005-hist/REPORT.md` 的 tracker 最终计数落档与 Gamma 结算档在 **257 个可核对事件中有 20 个不一致（7.8%）**；tracker 删除/漏抓会系统性改变最终计数，直接影响按档结算。
- **结算口径争议**：规则把“main feed posts / quote posts / reposts 算，replies 不算，但 main feed 上的 replies 算”写在一起，边界依赖 tracker 的分类；“Community reposts”一句原文有语法错误（“which are not counted by the tracker not count”），含义需按 tracker 行为理解。出现争议时以 UMA 仲裁（`resolvedBy=0x69c47De9D4D3Dad79590d61b9e05918E03775f24`，实测已结算事件字段）。
- **市场结构**：这些 event `negRisk=true`、`restricted=true`（字段实测）；十档中间价相加 1.025 > 1，看似可“卖全套”，但那是中间价错觉（GUIDE 第 8 节已警告），实际按 bid 卖会变成 0.52+…< 1，本条不碰。
- **费用风险**：低概率档的费占本金比例高（p=0.07 时 4.65%），尾部档买入的成本远高于直觉。
- **平台风险**：说明见 GUIDE 红线；本条只读公开接口，不连接钱包、不下单。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：**不确定** — 一句话能说清（窗口早段按无条件分布出价的一方付钱，新窗口每 2–3 天重开使该行为重复出现），但“谁在付钱”是从价差推断的，没有用 data-api 成交验证过；第 (b) 点“报价方不跟随 tracker”完全未测量。
2. 有免费数据能检验：**满足** — 结算结果（Gamma `outcomePrices`/`closedTime`）+ 逐条帖时间戳（xtracker，回溯至 2025-10-31，13,671 条）+ 历史每小时价（`prices-history` 在一个已结算 token 上实测可取 86 点），全部免费免密钥。扣分项：历史 L2/历史价差无公开源，只能用假设的半价差。
3. 小资金能做：**满足** — 单档前 3 档卖单约 310 USDT、单事件上限 400 USDT、同时 3 个事件，完全在 5,000 / 2,500 之内；容量小是缺点不是不可行。
4. 不重复：**满足** — 已 `grep -ril "tweet|truth.social|xtracker|post.count" bots/ known/`，仓库内无同机制条目；`bots/quant/CLAIMS.md` 已登记 B02；与 dot C01（气温分档）机制相邻但关键变量不同（发帖速率 vs 数值预报）。
5. 扣成本后粗算够用：**不满足**（2026-10-20 更新：`bots/quant/notes/q005-hist/REPORT.md` 历史回测 252 个触发事件，每份净收益中位 **−0.034596**、每美元投入中位 **−1.047500**，模型 log loss 劣于市场）— 原稿：一个时点的算术是 +4.9%/份（0.61 − 0.555 − 0.027375），但那是重叠样本上的单点比较，`backtest_count=0`、`observed_net_return=null`；不过这个门槛也**未**算年化（资金只占 2 天）。不能据此声称有正收益。
6. 两周内能检验：**满足（历史口径）**（2026-10-20 更新：`bots/quant/notes/q005-hist/REPORT.md` 已用 data-api 成交完成历史检验，50% 决策点 **252 个独立事件触发（≥30）**，按预先写死的失败标准判 **FAIL**）— 原稿：历史已结算事件 ≥30 个独立结果（series 10816 一页就 100 条，2026-01-03 至 2026-08-22，每月 10–13 个），两周内可跑完；失败标准已预先写死（扣费后逐事件净收益中位 ≤0）。风险：其余 token 的 `prices-history` 未逐个验证，若多数已结算市场没有价格历史，本项降为不满足。
7. 出处可查：**满足** — 每个数字都来自本节实抓的 URL，引文照抄，自算部分写明公式与样本；官方 Post Counter 最终计数与历史价差已明确写“未查到”。

## 出处

- https://gamma-api.polymarket.com/events?slug=elon-musk-of-tweets-october-19-october-21-2026 — 访问 2026-10-20 — 已读（规则原文、10 档、`outcomePrices`、`feeSchedule{rate:0.05}`、`endDate`、tags、series 10816）
- https://gamma-api.polymarket.com/events?slug=elon-musk-of-tweets-october-17-october-19-2026 — 访问 2026-10-20 — 已读（已结算：40-64 档 `["1","0"]`、`closedTime 2026-10-19 18:03:14+00`、`umaResolutionStatus=resolved`）
- https://gamma-api.polymarket.com/events?slug=donald-trump-of-truth-social-posts-october-20-october-27-2026 — 访问 2026-10-20 — 已读（Trump 规则原文、11 档、`rate=0.05`、series 11108）
- https://gamma-api.polymarket.com/events?series_id=10816&limit=500&closed=true — 访问 2026-10-20 — 已读（返回 100 条，2026-01-03 至 2026-08-22，按月 13/12/13/13/13/13/13/10）
- https://gamma-api.polymarket.com/public-search?q=elon%20musk%20tweets&limit_per_type=25&events_status=closed&page=1 — 访问 2026-10-20 — 已读（`totalResults=342`，含历史变体 slug）
- https://gamma-api.polymarket.com/public-search?q=truth%20social%20posts&limit_per_type=10&events_status=active — 访问 2026-10-20 — 已读（3 个并行 7 天窗口）
- https://xtracker.polymarket.com — 访问 2026-10-20 — 已读（规则中点名的界面站，返回 HTML，非数据接口）
- https://xtracker.polymarket.com/api/users/elonmusk — 访问 2026-10-20 — 已读（`platformId=44196397`、`lastSync`/`lastSyncError`、7 个 trackings、`metrics={}`）
- https://xtracker.polymarket.com/api/users/elonmusk/posts?limit=100&offset=0 — 访问 2026-10-20 — 已读（13,671 条，2025-10-31T00:17:35Z 至 2026-10-20T02:41:54Z）
- https://clob.polymarket.com/book?token_id=22442061711236593150409027149743058571520366316242909612280801414810466891148 — 访问 2026-10-20 — 已读（bid 0.54/257.39、ask 0.57/232.52）
- https://clob.polymarket.com/prices-history?market=34767215645050247279179635677802776215709078037234086703701315748816860889727&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（86 个点，0.515 → 0.9995）
- 未查到：xtracker 的 “Post Counter” 数值接口（`/api/trackings/<id>` 返回 `metrics:{}`、`target:null`）；官方最终计数；历史逐小时价差；tracker 停机时的补偿规则

---
