---
id: quant-026
name_zh: 干旱D4州名单：周四发布前的延续率
name_en: US Drought Monitor D4 weekly state roster — persistence base rates before the Thursday release
bot: quant
date: 2026-10-20
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「Will <state> have D4 (Exceptional Drought) this week?」州级二元（每周约 40 个州）+「How many states will be in D4」6 档州数（negRisk）
venues: Polymarket
data: US Drought Monitor StateStatistics REST（免费免密钥，2000-01-04 起周度，D4 为州面积百分比）；Polymarket Gamma（规则、费率、结算）+ data-api trades（免费免密钥，已关闭市场逐笔成交，最早 2026-08-25）；历史盘口无公开来源
test_2w: 独立结果按 weekly USDM release 计（州名单与州数同一结算源，合并为 1 个），历史只有 8 个、两周最多 2 个，凑不到 30；失败标准是已成交仓位扣 0.05 吃单费 + 1¢ 滑点后中位净额 ≤0，或分桶延续率跌破可成交 ask，或连续 8 周无正 edge，或前向 30 个周里 0→D4 进入率 >5%
status: 待核
confidence: 中
---

整理说明：本条的规则原文、USDM 周度数据、320 个州市场的结算与成交，全部是 2026-10-20 用公开免密钥接口现场取的；脚本与原始输出在 `bots/quant/notes/scheduler/scratch/B23/`。**已按 2026-10-20 复核与 re-check fix1（`bots/quant/notes/scheduler/reviews/c20261020-1423-research.md` 的 B23 节）修正**：补全规则引文缺失段落、改正结算源字段、年化算法、成本算术、容量口径与快照字节数；数据与回放已重跑一致。价格侧是**事后回放**，不是真正的预注册前向试验：规则用 2000–2026 的 USDM 分桶延续率构造，然后在这 8 个已关闭周上回放；为避免挑参数，主规则只用分桶基准率 + 固定 5¢ 安全垫，并完整报告 3/5/8/10¢ 敏感性。8 个周里只有 4 周有 YES 成交、3 周有 NO 成交，独立结果远少于 30。**2026-10-21 升 `待核`（占第 1 轮空出的 1 个名额，`date` 仍为 2026-10-20）。2026-10-21 本轮加固新增可成交价回测（脚本与 stdout 见 `bots/quant/notes/scheduler/scratch/H-quant-026/`）：原 +32.03% 回放用的是决策前 4.1–65.1 小时的旧报价；按决策后第一笔真实成交、且只算周四发布前可成交的，8 周只有 2 笔、净 +1.76 USD。可成交证据不足，门 3/5 由“满足/不确定”改为“不满足”，建议核对方退回；若保留观察，最多降为待选区。`status` 与 `date` 未改。**

## 一句话

在每个 USDM 周四发布前的**周三 23:59 UTC**，用上一周官方地图里各州的 D4 面积百分比，按「上周 D4 状态 → 本周仍 D4」的分桶历史延续率给每个州定公允值；只在可成交 ask 比该分桶延续率低至少 **5¢** 时买 YES，或在「上周 D4=0」的州上、NO 的 ask 比「本周仍非 D4」低至少 5¢ 时买 NO，持有到周四发布后的 UMA 结算。**（2026-10-21 加固：回测里所谓“ask”是决策前 4–65 小时的旧成交；按决策后第一笔真实成交，8 周只有 2 笔可成交，净 +1.76 USD。见证据 7。）**

## 钱从哪里来

付钱的是**把每周的 D4 名单当成一次全新事件、而不是把它当成慢变量更新的对手方**。USDM 的 D4 面积是周频、平滑的存量：一个州上周已经在 D4，下周仍在 D4 的概率在我的 25 年样本里是 **95.66%**；上周为 0 的州，下周进入 D4 的概率只有 **0.38%**（2026 年这 8 周是 1.72%）。这个状态转移在周四发布前是公开的：上一周的官方地图和州级 D4 面积都已经在 `droughtmonitor.unl.edu` 上，任何人花一分钟就能查到。

但「为什么这笔钱会持续存在」这条，我只能给一个**弱解释**，不能给结构性保证：这个 series 的最早已关闭事件是 2026-08-25；每周 40 个州市场、单市场成交额中位数只有约 **82–106 USD**（截止前/全部成交口径），做市商少、报价更新慢；早期（8/25）AR 的上周 D4 是 0.99%，ask 只有 0.50；MS 的上周 D4 是 0.87%，ask 0.51。后面几周同类州的 ask 升到 0.80–0.94，edge 在收敛。**这更像新模板初期的定价摩擦，不是长期锁定的现金流。** 如果市场在 2026-10 之后变得有效，这条就应该被放弃。

**2026-10-21 加固后的更正**：上面这些 0.50–0.94 的“ask”是决策前 4–65 小时的最后成交；决策后第一笔真实成交在 8/25 全部是 0.99，9 月以后也多在 0.92–0.99。**按可成交口径，5¢ 差额基本不存在**，所以“谁在付钱”在现有成交里找不到证据；能描述的只有 USDM 的延续率本身（95.66%），不是一个可交易的持续现金流。

## 规则

### 市场模板与结算原文

模板一（州名单）：`state-d4-drought-YYYY-MM-DD`，每个在季州一个独立二元市场，`negRisk=false`。示例 `state-d4-drought-2026-10-13`（2026-10-20 已读，HTTP 200，约 197 KB 快照，页面会变），40 个州市场；标题 `Exceptional drought (D4) by state — week of October 13, 2026`。

规则原文（州市场 `state-d4-drought-2026-10-13-al` 的 `description`，逐字摘）：

> This market will resolve to "Yes" if Alabama has D4 (Exceptional Drought) on 0.05% or more of its land area in the US Drought Monitor release for the week of October 13, 2026. Otherwise, this market will resolve to "No".
>
> D4 area below 0.05% is treated as cartographic noise at state borders and resolves "No".
>
> Alabama carries a market in May through November, so this market exists for the week valid October 13, 2026. Weeks outside that window have no Alabama market and make no claim about Alabama's drought.
>
> Each USDM release covers the seven-day period ending Tuesday at 8:00 AM ET and is published the following Thursday.
>
> Resolution is based on the first published US Drought Monitor release for the listed week. The first published release is final, and that publication is the revisions cutoff; subsequent revisions will not be considered.
>
> In the case that the Resolution Source publishes data, sufficient to settle a Market, that is clearly erroneous and the result of technical or operational error, or of unauthorized interference with the Resolution Source or its data, the Market may remain open for a period of up to seven (7) calendar days (ET) from the time of the original release, in anticipation of a correction by the Resolution Source. If the Resolution Source publishes a corrected value within that period, that value will be eligible for resolution. If no corrected value is published within that period, Polymarket will issue a Clarification to determine whether the originally published value may be eligible for resolution, or whether other action is required to preserve the orderly functioning of the Market.
>
> Revisions remain subject to the cutoff above. The only exception is a correction of a clearly erroneous print under the preceding paragraph, which will be used even if published after the cutoff.
>
> If the US Drought Monitor has not been published by 11:59 PM ET on the day following the scheduled publication date, this market will resolve to "No".
>
> The resolution source for this market is the US Drought Monitor at droughtmonitor.unl.edu.

模板二（州数）：`states-in-d4-drought-YYYY-MM-DD`，6 档 `0 / 1-2 / 3-4 / 5-6 / 7-9 / 10+`，`negRisk=true`，恰好一档 YES。示例 `states-in-d4-drought-2026-10-13`（HTTP 200，约 34 KB 快照，页面会变）。规则原文：

> This market will resolve to the bracket containing the number of coterminous US states (out of 48) with D4 percent area of 0.05% or more in the US Drought Monitor release for the week of October 13, 2026.
>
> Brackets: 0 / 1-2 / 3-4 / 5-6 / 7-9 / 10+. Exactly one bracket resolves "Yes".
>
> The count ranges over all 48 coterminous states — the 48 states excluding Alaska and Hawaii. The District of Columbia and U.S. territories are not considered.
>
> Each USDM release covers the seven-day period ending Tuesday at 8:00 AM ET and is published the following Thursday.
>
> Resolution is based on the first published US Drought Monitor release for the listed week. The first published release is final, and that publication is the revisions cutoff; subsequent revisions will not be considered.
>
> In the case that the Resolution Source publishes data, sufficient to settle a Market, that is clearly erroneous and the result of technical or operational error, or of unauthorized interference with the Resolution Source or its data, the Market may remain open for a period of up to seven (7) calendar days (ET) from the time of the original release, in anticipation of a correction by the Resolution Source. If the Resolution Source publishes a corrected value within that period, that value will be eligible for resolution. If no corrected value is published within that period, Polymarket will issue a Clarification to determine whether the originally published value may be eligible for resolution, or whether other action is required to preserve the orderly functioning of the Market.
>
> Revisions remain subject to the cutoff above. The only exception is a correction of a clearly erroneous print under the preceding paragraph, which will be used even if published after the cutoff.
>
> If the US Drought Monitor has not been published by 11:59 PM ET on the day following the scheduled publication date, this market will resolve to the "0 states" bracket.
>
> The resolution source for this market is the US Drought Monitor at droughtmonitor.unl.edu.

几个要点：

- **0.05% 是硬阈值**，低于 0.05% 一律 No，即使地图上有边界噪声；USDM 的州级 `D4` 列本身就是面积百分比（CSV 列 `MapDate,StateAbbreviation,None,D0,D1,D2,D3,D4,...`），可以直接比较。
- **只看初审**：第一份发布的周报是最终版，后续修订不算（除非是明显错误/技术或操作错误，最多 7 个 ET 日更正窗口）。
- **州名单随季节变**：10 月有 40 个州在名单里，Alabama 是 5–11 月，Arizona 是全年；名单外的州不是 No，只是没有市场。
- **结算源**：市场字段 `resolutionSource=https://droughtmonitor.unl.edu/DmData/DataTables.aspx`（2026-10-20 实取）；`https://droughtmonitor.unl.edu/` 用于核对发布节奏。官方首页原文（2026-10-20 抓取）：“The maps, which are based on analysis of the data, are released each Thursday at 8:30 a.m. Eastern Time.” 首页同时写 “Map released: October 15, 2026 / Data valid: October 13, 2026”，与规则的「周二数据、周四发布」一致。
- **费率**：两个模板的每个市场都返回 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`（Gamma 实取），与 GUIDE §8 的天气板块 0.05 一致。

已关闭样本：series `drought-d4-weekly`（id=12688，`recurrence=weekly`）在 Gamma 返回 **16 个 closed 事件** = **8 个周发布 ×（州名单 + 州数）**，`endDate` 从 2026-08-27 到 2026-10-15。每周 40 个州市场，共 **320 个州市场**；州数事件每周 6 档，共 48 个档。当前还有一个 open 事件 `state-d4-drought-2026-10-20`（`endDate=2026-10-22T13:00:00Z`，40 个州市场），已用于前向登记（见证据 6）。

### 交易规则（前向冻结版）

以下规则是为 2026-10-20 之后的周度发布**冻结**的；历史回放用同一套规则，但阈值敏感性全部列出，事后不挑。

1. **决策时刻**：每周三 **23:59 UTC**（EDT 期间 = 周三 19:59 ET，EST 期间 = 18:59 ET；比周四 8:30 ET 发布早 12.5–13.5 小时，比市场 `endDate=13:00 UTC` 早 13 小时 1 分）。
2. **状态变量**：取 `prior = event week − 7 days` 的 USDM 州级 `D4` 面积百分比。该周报在上一个周四已经发布，决策时一定可见。
3. **分桶**：`0`、`(0,0.05)`、`[0.05,0.25)`、`[0.25,1)`、`[1,5)`、`>=5`（单位都是州面积百分比）。
4. **延续率 `p_b`**：用 2000-01-04 起、截至 `prior` 周之前的所有「连续两周」州-周转移，按分桶算 `P(下周 D4>=0.05 | 本周在桶 b)`，加 Beta(1,1) 平滑：`p_b=(k+1)/(n+2)`。每个决策周只用当时已经发布的转移，不向前看。
5. **YES 触发**：只对 `prior>=0.05` 的州；若截止前 **72 小时内**存在 ask 侧成交，且最后 ask 代理价 `q` 满足 `q <= p_b − 0.05`，则以 `q + 0.01` 买入 YES。ask 侧成交的定义（data-api 的 `side` 按 taker 方向解释）：`outcome=Yes & side=BUY`，或 `outcome=No & side=SELL`（后者换算成 `1−price`）。
6. **NO 触发**：只对 `prior==0` 的州；若截止前 72 小时内有 yes bid 侧成交，换算 `no_ask = 1 − yes_bid`，且 `no_ask <= (1−p_0) − 0.05`，则以 `no_ask + 0.01` 买入 NO。yes bid 侧成交的定义：`outcome=Yes & side=SELL`，或 `outcome=No & side=BUY`。
7. **成本**：每份吃单费 `0.05 × fill × (1−fill)`（GUIDE §8 公式），再加 **1¢** 滑点/半价差缓冲；挂单不做（maker 费 0，但这不是挂单策略）。
8. **仓位**：每个州市场 ≤200 USDT；每个周事件 ≤400 USDT；本条专线 ≤1,000 USDT。实际按最后成交份数或更小，不假设自己能吃到整条盘口。
9. **出场**：持有到 UMA 结算（Gamma `umaResolutionStatus=resolved`）；不主动平仓、不加仓、不做 negRisk 转换。
10. **不做州数档**：样本内 8/8 周都是 `10+`，州数档没有任何可检验的变化；只做州名单。州数事件与州名单事件共享同一份 USDM 发布，按独立结果合并成 1 个。
11. **失败即停**：若连续 30 个独立周（约 7 个月）扣成本后中位净额 ≤0，或分桶延续率跌破当时可成交 ask，或连续 8 周没有正 edge，停止。

**2026-10-21 执行口径更正**：上面第 5/6 条把“截止前 72 小时内的最后 ask/bid 侧成交”当作可成交价；2026-10-21 用 data-api 的后续成交复核，这个假设不成立——23 个信号里只有 2 个在周四发布前出现下一笔同向成交，其余下一笔都在发布后且价格 0.92–0.996。**因此第 5/6 条只能产生“信号”，不能产生“成交价”；可成交回测见证据 7。** 前向规则应改为：信号照旧，成交价必须用决策后、发布前的真实成交或当时盘口，取不到就不做。

## 证据

### 1）结算口径复算：320/320 州市场与 USDM 一致

我从 USDM REST 取每个州每个 `MapDate` 的 `D4` 列，按 `D4>=0.05` 判 Yes，再与 Gamma 的 `outcomePrices` 对比：

- **320 个州市场：0 个不一致**（8 个周 × 40 个州）。
- **8 个州数事件：8/8 一致**；但按全部 48 个本土州计，样本内州数依次是 `12, 12, 12, 12, 12, 10, 11, 12`，**全部落在 `10+` 档**。所以州数档在样本内是退化的，不能用来估计转移率。

每周实际处于 D4 的州（我算的；州名单只覆盖 40 个在册州，州数档按 48 州计）：

| 周 | 在册 40 州的 D4 数 | 全部 48 州的 D4 数 | 在册 D4 州 |
|---|---:|---:|---|
| 2026-08-25 | 12 | 12 | AR CO ID MS NC NE NM NV OK OR TX UT |
| 2026-09-01 | 12 | 12 | 同上 |
| 2026-09-08 | 12 | 12 | 同上 |
| 2026-09-15 | 12 | 12 | 同上 |
| 2026-09-22 | 12 | 12 | WI 进，UT 出 |
| 2026-09-29 | 10 | 10 | NM、OR 出 |
| 2026-10-06 | 10 | 11 | 不变；**MI** 在全部 48 州里进入 D4，但 10 月 roster 没有 Michigan 市场 |
| 2026-10-13 | 11 | 12 | LA、MO 进，NC 出；MI 仍在全部 48 州里 |

在册 40 州内 **5 次进入**（NV、UT、WI、LA、MO）和 **5 次退出**（SC、UT、NM、OR、NC）。这正是“延续率高但不是 100%”的来源：SC 在 8/25 前一周是 0.19%，8/25 当周归零；本条主规则唯一亏损的交易就是它。MI 是唯一一个“全部 48 州有 D4、但 roster 没有市场”的州，所以州数档的 11/12 与州名单的 10/11 不矛盾。

### 2）25 年分桶延续率（这是规则的先验，不是市场回测）

48 个本土州，2000-01-04..2026-10-13，连续两周的州-周转移 **67,056 个**；`D4` 直接用 USDM REST 的百分比：

| 上周 D4 桶 | n | 本周仍 D4 | 延续率 | Wilson 95% CI |
|---|---:|---:|---:|---:|
| 0 | 61,557 | 235 | **0.38%** | 0.34–0.43% |
| (0, 0.05) | 88 | 12 | 13.64% | 7.98–22.34% |
| [0.05, 0.25) | 207 | 168 | **81.16%** | 75.28–85.90% |
| [0.25, 1) | 578 | 524 | **90.66%** | 88.01–92.77% |
| [1, 5) | 1,401 | 1,321 | **94.29%** | 92.95–95.39% |
| >=5 | 3,225 | 3,163 | **98.08%** | 97.54–98.50% |
| 全部 `prior>=0.05` | 5,411 | 5,176 | **95.66%** | 95.08–96.17% |

说明：这些州-周观测高度自相关（同一个州连续多周、同一天气系统跨州），Wilson CI 只作描述，不能当成 5,411 个独立样本。真正独立的市场结果只有 8 个周。

2026 年这 8 个周窗口内的分桶命中（48 个州 × 8 周共 384 个连续州-周转移；只是横截面，**不独立**）：

| 桶 | n | 本周仍 D4 | 命中率 |
|---|---:|---:|---:|
| 0 | 291 | 5 | 1.72% |
| (0, 0.05) | 1 | 1 | 100.00% |
| [0.05, 0.25) | 3 | 2 | 66.67% |
| [0.25, 1) | 34 | 32 | 94.12% |
| [1, 5) | 26 | 25 | 96.15% |
| >=5 | 29 | 28 | 96.55% |

2026 年的 `0→D4` 进入率是 1.72%，比 25 年的 0.38% 高，但仍很低；这支持“对上周为 0 的州买 NO”的方向，但不支持把它当成无风险。 只看 40 个在册州（剔除 roster 选择偏差）：`0→D4` 4/228 = **1.75%**，D4 延续 86/91 = **94.51%**（`roster_rates.py`），与 48 州池化率接近，所以 roster 不是主要偏差来源。

### 3）历史回放（旧报价代理，不可成交）：8 个周、23 笔、22 笔盈利

**方法**：对 320 个州市场，按上面冻结规则在周三 23:59 UTC 取最后 ask/bid 侧成交（72 小时内），用 1¢ 滑点 + 0.05 吃单费；只做规则触发的交易，不做事后筛选。价格是 data-api 的**成交价代理**，不是历史盘口（历史盘口无公开来源）。**2026-10-21 复核确认：这些“ask”距决策时刻中位 37.1 小时（4.1–65.1h），不是决策时可成交的报价；下表只能当乐观上限，不能当扣成本后收益（见证据 7）。**

| 方向 | 笔数 | 盈利 | 合计净额（每笔 1 份） | 合计成本（每笔 1 份） | ROI | 活跃周 |
|---|---:|---:|---:|---:|---:|---:|
| YES | 14 | 13 | **+2.9848** | 10.0152 | **+29.80%** | 4 |
| NO | 9 | 9 | **+1.3050** | 7.6950 | **+16.96%** | 3 |
| 合计 | 23 | 22 | **+4.2898** | 17.7102 | **+24.22%** | 5 |

按每笔最后成交的**实际份数**计（YES 用最后 ask 侧成交份数，NO 用最后 yes bid 侧成交份数；把最后成交份数当作可成交上限，仍然偏乐观）：**1,020.57 份、成本 766.93 USD、净 245.64 USD、ROI +32.03%**。分周：

| 周 | 笔数 | 成本 USD | 净 USD | ROI |
|---|---:|---:|---:|---:|
| 2026-08-25 | 7 | 210.37 | 155.43 | +73.9% |
| 2026-09-01 | 6 | 98.63 | 11.24 | +11.4% |
| 2026-09-08 | 2 | 18.92 | 1.08 | +5.7% |
| 2026-09-15 | 4 | 342.60 | 61.75 | +18.0% |
| 2026-10-06 | 4 | 96.40 | 16.15 | +16.8% |

（分周数字四舍五入到 2 位；合计以未四舍五入的脚本输出为准：成本 766.93 USD、净 245.64 USD。）

其余 3 周（2026-09-22、2026-09-29、2026-10-13）没有州满足 5¢ 安全垫：9/22 和 10/13 在截止前 72h 内没有 ask 侧成交，9/29 有报价但都高于 `p_b−0.05`（如 TX 0.95 vs 阈值 0.893、WI 0.96 vs 0.893）。这不是“没成交所以没亏”，而是当时没有可成交的 5¢ 差额。

**edge 在收敛**：8/25 一周贡献了 155.43/245.64 = 63.3% 的净额；8/25 的 YES 报价是 0.50–0.55，9/15 以后同类州升到 0.80–0.94。把 8/25 去掉：YES 9 笔、净 +1.6791/份、资本 7.3209（+22.94%）；NO 7 笔、净 +0.4320、资本 6.5680（+6.58%）。正收益还在，但薄了很多。

**阈值敏感性**（同一套价格，只改 5¢ 安全垫；主规则是 5¢）：

| 安全垫 | YES 笔数 | YES 净额/份 | YES ROI | NO 笔数 | NO 净额/份 | NO ROI |
|---:|---:|---:|---:|---:|---:|---:|
| 3¢ | 16 | +3.1184 | +26.25% | 17 | +1.5545 | +10.06% |
| **5¢** | **14** | **+2.9848** | **+29.80%** | **9** | **+1.3050** | **+16.96%** |
| 8¢ | 11 | +2.6383 | +35.84% | 3 | +0.9878 | +49.09% |
| 10¢ | 8 | +2.1504 | +44.34% | 3 | +0.9878 | +49.09% |

滑点敏感性（5¢ 安全垫）：滑点 2¢ 时 YES +28.05%、NO +15.66%；滑点 5¢ 时 YES +23.08%、NO +11.92%；滑点 10¢ 时 YES +15.62%、NO 只剩 3 笔 +31.77%。**即使用 10¢ 的极端滑点，方向仍然是正的；但这不能修复“只有 4 个活跃周”的样本问题。**

### 4）容量：旧报价口径 748 USD/8 周，可成交口径只有 14.24 USD

- 320 个州市场里：**30 个零成交**；有成交的 290 个，单市场中位总成交额 **105.54 USD**、p90 **366.17 USD**、最大 2,669.83 USD（全部成交口径，numpy 线性分位）；若只算截止前成交（181 个市场），中位 **82.28 USD**、p90 **379.35 USD**、最大 872.41 USD。
- 8 周州市场总成交额 **55,938 USD**，按周从 **965** 到 **13,642 USD** 不等。
- 截止前 72 小时内有 ask 侧成交的州市场只有 **52/320**；有任意成交的 **181/320**。
- 主规则 14 笔 YES 的最后 ask 名义额合计 **577.55 USD**；9 笔 NO 的最后 bid 名义额合计 **170.66 USD**；合计 **748.21 USD**。这是“按最后成交份数”的旧报价容量，不是可成交容量：2026-10-21 按决策后第一笔真实成交复核，8 周只有 **2 笔、成本 14.24 USD**（限价口径 1 笔、4.19 USD）。
- 一个月约 **12 次机会**（23 笔/8 周 × 4.33），名义额约 **400–800 USD/月**——这是旧报价口径；**可成交口径约 1 次/月、8 周名义额 <20 USD**。容量是这条策略的硬约束，不是资金。

### 5）为什么只做州名单、不做州数

州数档在 8 个周里全部是 `10+`：按 48 州计 `12,12,12,12,12,10,11,12`。一个 8/8 都相同的档，在样本内没有转移可学；买 `10+` 的 YES 在 0.95 以下看起来“稳”，但那只是 8 个相关周，不是 30 个独立结果。州名单有 320 个州-周、5 次进入和 5 次退出，才有横截面变化可检验；所以本条的交易对象是州名单。

### 6）前向登记（2026-10-20）

当前 open 事件 `state-d4-drought-2026-10-20`（`endDate=2026-10-22T13:00:00Z`）的 40 个州市场，在 2026-10-20 快照里：绝大多数 `bestAsk=0.99`，`OK` 的 ask 也是 0.99，`AR` 是 0.999，`WI` 是 0.99；按 5¢ 安全垫，`OK`（prior 16.55%，p_b≈0.981，阈值 0.931）和 `WI`（prior 4.47%，p_b≈0.943，阈值 0.893）都**不触发**。**2026-10-20 快照没有合格报价**；正式判定要等 2026-10-21 23:59 UTC 截止时的最后 ask。这条前向记录从 2026-10-22 的发布开始，至少连续记 30 个周发布才有统计意义。

### 7）可成交价加固回测（2026-10-21）：可核实净额只有 +1.76 USD

**方法**：仍用冻结规则，但不再把“决策前最后成交”当成成交价。先用截止前的报价产生信号（与原规则相同），再要求**决策时刻之后、周四 12:30 UTC USDM 发布之前**出现一笔同向真实成交，用这笔成交价 +1¢ 滑点 + 0.05 吃单费作为可成交价。数据仍是 data-api 逐笔成交；脚本 `harden_backtest.py`，stdout `harden_backtest.out`，缓存 `_cache/`。旧口径的复算已由 `bots/quant/notes/scheduler/checks/B23.md` 从零重跑通过（16 个 closed event/368 个市场/2,344 笔成交/320-320 结算/67,056 个转移/23 笔/1,020.57 份/$766.93/$245.64），本轮不重复这份复算，只补“可成交价”这一层；本轮也重新抓了同一批数据，旧口径逐笔一致。

| 口径 | 笔数 | 活跃周 | 成本 USD | 净 USD | 每份净额 | 每份 ROI |
|---|---:|---:|---:|---:|---:|---:|
| 原回放：决策前最后 ask（中位 37.1h 旧报价） | 23 | 5 | 766.93 | +245.64 | +4.2899 | +24.22% |
| 可成交：决策后第一笔真实成交，发布前 | **2** | **1** | **14.24** | **+1.76** | **+0.2489** | **+14.21%** |
| 可成交 + 限价单（限价=原 ask+1¢，发布前被成交） | **1** | **1** | **4.19** | **+0.81** | **+0.1629** | **+19.47%** |

- 23 个信号里，只有 **2 个**在发布前出现下一笔同向成交，且都在 **2026-10-06**：MS 0.910（11 份）、NC 0.830（5 份）。其余 **19 个**的下一笔成交都发生在周四发布之后（截止后 12.52–16.84 小时），价格 **0.92–0.996**；**这些成交已经包含 USDM 发布信息，不能用来证明发布前可进场**（其中 8/25 的下一笔是 0.99，加 1¢ 后为 1.00，扣费为负；9 月以后有些 0.92–0.96，若发布后追价仍有小额正收益，但那是发布后交易，不是本条信号）。另有 **2 个**（8/25 SC、9/15 TX）在 72 小时内没有任何后续成交。
- 上面的“2 笔”不是负收益，而是**几乎没有可成交证据**：8 周总成本 14.24 USD，净 1.76 USD，只有 1 个周。这与原回放的 +245.64 USD 差两个数量级。
- 报价新鲜度敏感性（仍是旧报价口径）：把最后成交的允许年龄从 72h 收紧到 24h，只剩 7 笔、每份 ROI +15.05%；收紧到 6h，只剩 4 笔、+10.57%；收紧到 1h，**0 笔**。也就是说，原 edge 主要来自“几小时到两天前的旧报价”，不是决策时可成交的差额。
- 时间外样本：前 4 周选 margin（最优 0¢），后 4 周用 0¢，旧报价口径 14 笔、每份 ROI +8.43%，仍集中在 9/29 与 10/06 两周；按可成交口径，后 4 周只有 10/06 的 2 笔、净 +1.76 USD。**这只是时间切分，不是预注册 OOS**；真正的前向 OOS 从 2026-10-22 开始，目前 **0 个**。
- **CLOB prices-history 不能补历史盘口**：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max` 对已关闭市场只保留最近约 3–7 天（本样本）；160/320 个州市场能取到决策时刻的中间价（只有 2026-09-22..10-13 四周），更早的 160 个返回 `{"history":[]}`。而且它是盘口中间价，不是可成交 ask：`state-d4-drought-2026-10-13-ar` 在截止时 p=0.915、data-api 成交 0 笔、结算 `outcomePrices=["1","0"]`，series 最后一点却是 0.525。用这个中间价做“上界”筛会得到 72 个触发、每份 ROI +30.33%，但这是**不可成交的假机会**，不能当证据。
- 结论：原 +32.03% 是旧报价上限；按可核实成交，8 周净 +1.76 USD（2 笔）或 +0.81 USD（1 笔）。**门 5 不满足，门 3 的可成交容量也不满足。** 这不是把正结果改成负结果，而是把“不可成交的旧报价”剔除后，收益和容量都不足以支撑收录。

## 数据

- **USDM 州级周度统计（免费、免密钥）**：`https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=<州FIPS>&startdate=1/1/2000&enddate=10/20/2026&statisticsType=1`，`Accept: text/csv` 不是必需（2026-10-21 复核：带与不带都返回 HTTP 200/922 B；2026-10-20 旧记录写“不带返回 0 字节”，已更正）。返回列 `MapDate,StateAbbreviation,None,D0,D1,D2,D3,D4,ValidStart,ValidEnd,StatisticFormatID`；`D4` 是州面积百分比，2000-01-04 起周度。2026-10-20 抓取单州 96–99 KB，HTTP 200。48 个州各存一份 CSV 在 `_cache/usdm/`。
- **USDM 发布节奏与地图页（免费、免密钥）**：`https://droughtmonitor.unl.edu/`（HTTP 200，约 121 KB；2026-10-20 快照，页面会变）。原文：“The maps, which are based on analysis of the data, are released each Thursday at 8:30 a.m. Eastern Time.”；首页同时给出 “Map released: October 15, 2026 / Data valid: October 13, 2026”。
- **USDM 综合统计下载页**：`https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx`（HTTP 200，约 586 KB；2026-10-20 快照，页面会变）。短名单里猜的直连 `.../data/csv/20260901_dmstatistics.csv` 返回 404；可编程取数用上面的 REST，不用猜 CSV 路径。
- **Polymarket Gamma（免费、免密钥）**：`https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100`（16 个已关闭事件）；`https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-13`（HTTP 200，约 197 KB 快照，规则、40 个市场、费率）；`https://gamma-api.polymarket.com/events?slug=states-in-d4-drought-2026-10-13`（HTTP 200，约 34 KB 快照，6 档）。
- **Polymarket data-api 成交（免费、免密钥）**：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000`；已关闭市场可取到逐笔 `size/price/side/outcome/timestamp`。8 周 320 个州市场共 2,158 笔成交（另有州数档 186 笔，未用于交易），原始缓存 `_cache/trades_all.json.gz`（约 250–278 KB gzip；2026-10-20/21 快照，缓存会变）。
- **Polymarket CLOB prices-history（免费、免密钥，但不能补历史盘口）**：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max`；2026-10-21 实测：已关闭市场只保留最近约 3–7 天，160/320 个州市场能取到决策时刻的中间价（只有 2026-09-22..10-13），更早的 160 个返回 `{"history":[]}`；返回 `{"history":[{"t":...,"p":...}]}`，`p` 是盘口中间价，不是可成交 ask（例：`state-d4-drought-2026-10-13-ar` 截止 p=0.915、data-api 0 笔、结算 [1,0]、series 最后 0.525）。
- **缺失，必须写清**：历史盘口（bid/ask 快照）没有公开来源；本文只能用最后成交价做代理。2026-10-21 复核显示，已关闭市场的 CLOB prices-history 既短（本样本约 3–7 天）又不是可成交价，所以**真正的历史 ask 仍然取不到**。USDM 的“当时首发布值”也没有单独的归档，REST 返回的是当前值；不过 320/320 与 Polymarket 结算一致，说明至少在这 8 周里修订没有改变结果。

## 两周内怎么检验

- **独立结果按 weekly release 计**：同一周的州名单和州数是同一份 USDM 发布、同一结算源，合并为 **1 个**；不同州、不同档都不独立。历史只有 **8 个**（2026-08-25..2026-10-13），两周最多再拿 **2 个**；凑到 30 个约需 **7 个月总样本**（还差 22 个周发布，约 5 个月）。按 GUIDE §2 第 6 条，本条应进**待选区**；本轮可成交回测（证据 7）进一步显示门 5 也不满足，建议退回。front matter 仍是第 1 轮已升的 `待核`，本轮按任务要求不改 `status`/`date`，只把建议写在这里。
- 两周内能做完的：
  1. 用已关闭的 8 周做**回放**（本文已完成）：320 个州市场、320/320 结算一致、旧报价口径 23 笔触发；但按可成交口径（证据 7）只剩 2 笔、净 +1.76 USD，所以这是“上限 + 可成交下限”的对照，不是正收益证据。
  2. 前向记录 2026-10-22 和 2026-10-29 两个发布：每周三 23:59 UTC 记录各州 `bestBid/bestAsk`（或 data-api 最后成交）、按规则触发哪些州，周四发布后记实际 D4 与结算。两周只能得到 2 个独立结果，但可以验证“报价在发布前是否已经收敛”。
  3. 用 2000–2026 的 67,056 个州-周转移做**分桶稳定性**检查：按 5 年一段，看 `[0.05,0.25)`、`[0.25,1)`、`[1,5)`、`>=5` 的延续率是否漂移；如果某桶漂移超过 5 个百分点，前向规则要降权。
- **失败标准（写死，事后不改）**：
  1. 已成交仓位扣 0.05 吃单费 + 1¢ 滑点后，**中位净额 ≤0**；
  2. 或分桶延续率 `p_b` 跌破当时可成交 ask（即 5¢ 安全垫消失）连续 4 周；
  3. 或连续 8 个周发布没有正 edge；
  4. 或前向 30 个周里，`0→D4` 进入率升到 >5%（NO 侧的尾部风险变大）。
- 不允许的自我安慰：不能用“挂单没成交所以没亏”当正结果；不能把 320 个州-周当 320 个独立结果；不能只报 8/25 那一周。

## 成本与容量

- **费率（Gamma 实取）**：州名单和州数每个市场都是 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`；GUIDE §8 天气板块也是 0.05。吃单费 = 份数 × 0.05 × p × (1−p)，折成投入资本 = 0.05 × (1−p)：
  - `p=0.50` → 每份 1.25¢，占投入 **2.5%**；
  - `p=0.82` → 每份 0.738¢，占投入 **0.90%**；
  - `p=0.93` → 每份 0.326¢，占投入 **0.35%**；
  - NO 在 `p_no=0.94` → 每份 0.282¢，占投入 **0.30%**。
- **每笔成本 = 吃单费 + 1¢ 滑点/半价差缓冲**。历史盘口取不到，1¢ 是假设值，不是实测；这是本条最软的一个数。按 0.50 的 YES 算，总成本约 **2.25¢/份（4.5% 的投入：吃单费 1.25¢ + 1¢ 滑点）**；按 0.82 算约 1.74¢/份（2.1%）；按 0.93 算约 1.33¢/份（1.4%）。
- **单笔容量（旧报价口径）**：按最后成交份数，14 笔 YES 合计 767.7 份、名义额 577.55 USD；9 笔 NO 合计 252.9 份、名义额 170.66 USD。单市场通常只能放 **20–200 USD**；`TX` 这类成交较大的州可到几百 USD。
- **可成交容量（2026-10-21 加固，采用这一条）**：只算决策后、周四发布前的真实成交，8 周只有 **2 笔**：MS 11 份、NC 5 份，成本 **14.24 USD**、净 **1.76 USD**；限价口径只有 1 笔、成本 **4.19 USD**、净 **0.81 USD**。原 748.21 USD/8 周是旧报价口径，不能当容量；**单市场 20–200 USD 的假设没有可成交证据支持**。
- **一个月多少次**：旧报价口径约 **12 次**（23 笔/8 周），名义额 **400–800 USD/月**；可成交口径 8 周 **2 笔**（约 1 次/月），名义额 **<20 USD/8 周**。5,000 USDT 的总资金约束形式满足，但**根本用不满**；容量是硬约束，不是资金。
- **占款天数**：周三 23:59 UTC 进场 → 周四 13:00 UTC 市场 `endDate` → UMA 结算；样本里 `closedTime` 从发布当天到发布后 3 天不等（如 8/27 事件 8/30 关闭，9/3 事件 9/4 关闭）。按 **0–3 天**（多数当天）占款估算。旧报价口径 8 周 23 笔、总成本 766.93 USD、净 245.64 USD；如果按 5,000 总资金算，8 周回报约 **4.9%**（245.64/5,000=4.91%）；按 52/8 线性年化约 **32%**（4.91%×52/8=31.9%，单利、8 周样本，不能当预期）。**按可成交口径，8 周净 1.76 USD、成本 14.24 USD；占 5,000 总资金只有 0.035%，年化没有意义，不再计算。**

## 风险

- **旧报价不是可成交价（2026-10-21 新增，最大风险）**：原回放的“ask”距决策中位 **37.1 小时**（4.1–65.1h）；23 个信号里只有 2 个在发布前有下一笔真实成交，净 +1.76 USD；其余 19 个的下一笔在发布后（0.92–0.99），2 个在 72h 内没有后续成交。把旧报价当成交价，会把 +1.76 USD 放大成 +245.64 USD。这是本条最可能被退回的原因。
- **价格代理不是盘口**：最后成交可能是很小的单（5–185 份），也可能已经过时（最长 72 小时）；我加 1¢ 滑点、并报告 0/1/2/5/10¢ 敏感性，但仍可能高估可成交性。真正的 ask 可能比最后成交高很多，尤其是 8/25 那些 0.50–0.55 的报价。
- **早期 edge 可能是新模板初期的定价摩擦**：8/25 一周贡献 63.3% 的净额；之后报价从 0.50 升到 0.80–0.94。若这是新模板的做市商进场过程，那么 2026-10 之后 edge 可能已经消失。**这是本条最大的风险，不是天气。**
- **只有一个亏损样本**：23 笔里 22 笔盈利，唯一的亏损是 SC（prior 0.19%，落在 `[0.05,0.25)` 桶，该桶 25 年延续率只有 81.16%）。样本太小，不能把 95.66% 的全样本延续率当成每一笔的胜率；`[0.05,0.25)` 桶的尾部风险明显更高。
- **分桶率是池化的，未按季节/州分层**：D4 有季节性：25 年里 `0→D4` 的月率从 0.10%（2 月）到 0.71%（6 月）不等（`seasonality.py`）；2026 年这 8 周的 `0→D4` 进入率是 1.72%，高于 25 年全年的 0.38%，说明用全年池化率可能低估当前的进入风险。规则没有按州单独估率（单州样本太薄），这是模型误差的来源之一。
- **州-周不独立**：320 个州-周共享 8 份 USDM 发布；同一个州连续多周高度相关。所有“320 个观测”的统计量都不能按独立样本解释。
- **阈值与四舍五入**：USDM 的 `D4` 只到小数点后两位；规则写 0.05%，所以显示 0.05 才算 Yes，显示 0.04 就是 No。若某州真实值在 0.045–0.05 之间，显示值可能让它翻档；这是规则本身的边界风险，不能靠模型消除。
- **初审 vs 修订**：规则只看第一份发布，后续修订不算；但 USDM 的 REST 当前值可能已经包含修订。本文 320/320 与结算一致，说明这 8 周里修订没有改变结果；更长样本里不保证。
- **名单随季节变**：Alabama 只有 5–11 月有市场，Arizona 全年有；名单外的州不是 No。跨月比较时不能把“没有市场”当成“没有 D4”。
- **缺数据兜底**：州名单在 USDM 未按时发布时判 **No**；州数判 **0 states**。如果周四发布延迟，所有 Yes 仓位会归零，这是规则层面的尾部风险。
- **结算延迟**：UMA 提案 + 争议期，`closedTime` 可能比 `endDate` 晚 0–3 天（样本里多数当天）；资金占用比理论值长。
- **平台/流动性**：模板 `restricted=true`（2026-10-21 复核：州名单 40/40、州数 6/6 全是 true，不是“部分市场”），`negRisk=false` 的州名单每州独立结算；薄市场里可能买不到、卖不掉，或者被单笔大额成交把价格打穿。

## 改进了什么

不适用（`kind: new`）。与最接近的条目相比：

- **quant-015（全球月均温 ERA5 nowcast）**：同为 `weather`/`S`，但 quant-015 是“用 ERA5 整月值预测 NASA GISTEMP 月距平档”，标的是连续数值的月频 nowcast；本条是“用上一周官方地图预测下一周州级二元 D4 名单”，标的是 0.05% 阈值两侧的状态转移，频率是周、横截面是 40 个州。两者结算源、状态变量、市场模板都不同。
- **quant-012（地震周计数）/ quant-019（麻疹计数阶梯）**：它们交易的是“官方计数落在哪一档”的计数阶梯；本条不交易计数档（样本内 8/8 都是 `10+`，退化），交易的是州名单的延续/进入。状态变量是分桶转移率，不是计数过程。
- **dot-001/dot-002（城市日最高温）**：标的是单日最高温的整数档，结算源是 NOAA timeseries；本条是周度 USDM 州级面积百分比，不是温度预报。
- **muse-own2-tail-weather-expiry-favfade**：标的也是天气热门档，但机制是“临到期热门高估买 NO”的行为偏差；本条是“上周 D4 状态的延续率”基准率，不依赖到期前的时间衰减。

## 门槛自查

1. **机制说得清：不确定（可成交口径下未找到付钱方）** — 一句话：上周已经在 D4 的州下周仍在 D4 的概率 95.66%（25 年 5,411 个州-周转移），上周为 0 的州下周进入 D4 只有 0.38%；旧报价里前者低到 0.50–0.89。但 2026-10-21 可成交回测显示，这个 5¢ 差额只存在于决策前 4–65 小时的旧报价；决策后第一笔真实成交大多在 0.92–0.99（只有 2026-10-06 的 MS/NC 是 0.90/0.82），**按可成交价找不到付钱方**。机制本身（USDM 延续率）清楚，但“谁付钱、为什么持续”在现有成交里没有证据。
2. **有免费数据能检验：满足（仅前向记录替代口径）** — USDM REST 免费免密钥、2000 年起周度，Polymarket Gamma/data-api 也免费；但**历史只有 8 个 weekly 独立结果**（州名单 + 州数同一结算源合并，<30），门 6 仍不满足。只能从 2026-10-22 起前向记录，约 5 个月才够 30 个（总样本约 7 个月）。
3. **小资金能做：不满足（可成交容量）** — 形式上单州 20–200 USD、单周 ≤400 USD、专线 ≤1,000 USD 都在 5,000/2,500 以内；但**可成交证据只有 8 周 2 笔、成本 14.24 USD（限价口径 1 笔、4.19 USD）**，单市场 20–200 USD 的假设没有成交支持。5,000 USDT 放不进去，容量是硬约束。
4. **不重复：满足** — 见“改进了什么”。与 quant-015 的月温 nowcast、quant-012/019 的计数阶梯、dot-001/002 的日最高温、muse 的临到期热门都不是同一机制；本条做的是 USDM 周度州级 D4 名单的延续率，仓库内除本条外没有同模板条目（`grep -rilE "Drought Monitor|Exceptional Drought|USDM" bots/*/entries known/` 只命中本条自己）。
5. **扣成本后粗算够用：不满足** — 旧报价口径 23 笔、成本 766.93 USD、净 245.64 USD（+32.03%）；**可成交口径只有 2 笔、成本 14.24 USD、净 1.76 USD（每份 +14.21%），限价口径 1 笔、净 0.81 USD**。原 +32.03% 是“旧报价 + 1¢ 滑点 + 0.05 吃单费”的上限，不是可成交收益；按 GUIDE 门 5 不能算够用。失败标准（中位净额 ≤0）没有被触发，但 2 笔/1 周的正结果不足以证明 edge 存在，不能反过来当“通过”。
6. **两周内能检验：不满足** — 独立结果按 weekly release 计，历史 8 个，两周最多 2 个；30 个约需 7 个月总样本（还差 22 个周发布）。可成交结果更少（8 周 2 笔），即使前向记录也难在两周内得到 30 个可成交独立结果。按 GUIDE §2 第 6 条，本条应进**待选区**；结合门 3/5，建议退回。
7. **出处可查：满足** — 每个规则原文、USDM 数据、费率、成交都给了 URL 和访问日期；2026-10-21 复核 10 个主要来源 URL 全 HTTP 200（CLOB prices-history 也返回 200），两段规则引文与 live `description` 逐字相等（州名单 2,082 字符、州数 2,032 字符）。320/320 结算复算、67,056 个转移、23 笔旧报价回放、2 笔可成交回放都由本地脚本重算，脚本和 stdout 在 `notes/scheduler/scratch/H-quant-026/`。并更正两处旧表述：USDM REST 不带 `Accept: text/csv` 也返回 200/922 B（原写“返回 0 字节”）；州名单 40/40、州数 6/6 都是 `restricted=true`（原写“部分市场”）。

## 出处

- `https://droughtmonitor.unl.edu/` — 访问 2026-10-20 — 已读（发布节奏 “released each Thursday at 8:30 a.m. Eastern Time”；“Map released: October 15, 2026 / Data valid: October 13, 2026”）
- `https://droughtmonitor.unl.edu/DmData/DataTables.aspx` — 访问 2026-10-21 — 已读（HTTP 200，52,014 B；市场字段 `resolutionSource` 指向此页）
- `https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx` — 访问 2026-10-20 — 已读（HTTP 200，约 586 KB；2026-10-20 快照，页面会变；直连 CSV 路径 404）
- `https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=01&startdate=8%2F1%2F2026&enddate=10%2F20%2F2026&statisticsType=1` — 访问 2026-10-20 — 已读（HTTP 200，922 bytes；列 `MapDate,StateAbbreviation,None,D0,D1,D2,D3,D4,...`）
- `https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100` — 访问 2026-10-20 — 已读（16 个 closed 事件，8 个周发布 × 2）
- `https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-13` — 访问 2026-10-20 — 已读（HTTP 200，约 197 KB 快照，页面会变；40 个州市场；规则原文；`feeSchedule.rate=0.05`）
- `https://gamma-api.polymarket.com/events?slug=states-in-d4-drought-2026-10-13` — 访问 2026-10-20 — 已读（HTTP 200，约 34 KB 快照，页面会变；6 档 `0/1-2/3-4/5-6/7-9/10+`；`negRisk=true`）
- `https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-20` — 访问 2026-10-20 — 已读（open 事件，40 个州；多数 `bestAsk=0.99`）
- `https://data-api.polymarket.com/trades?market=0xbf70aa5a4a493a1201d21be0121d3de42ceb58121fb6401da0bd4c1beb83cfdd&limit=1000` — 访问 2026-10-20 — 已读（HTTP 200，2,823 bytes；`size/price/side/outcome/timestamp`）
- `https://gamma-api.polymarket.com/events?tag_slug=drought&closed=true&limit=100` — 访问 2026-10-20 — 已读（37 个事件：16 个周度 D4、2 个 deadline D4、19 个其他；deadline 型不纳入本条）
- `https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max` — 访问 2026-10-21 — 已读（已关闭市场只保留约 3–7 天（本样本）；160/320 个州市场能取到决策时刻中间价，08-25..09-15 返回 `{"history":[]}`；`state-d4-drought-2026-10-13-ar` 截止 p=0.915、data-api 0 笔、结算 [1,0]、series 最后 0.525；是中间价，不是可成交 ask）
- 2026-10-21 复核：上述 10 个主要来源 URL 全部 HTTP 200；CLOB prices-history 也返回 200（内容见上）；州名单/州数两段规则引文与 live `description` 逐字相等（2,082/2,032 字符）；`state` 40/40、`bracket` 6/6 `restricted=true`；USDM REST 不带 `Accept` 也返回 200/922 B。脚本与 stdout：`bots/quant/notes/scheduler/scratch/H-quant-026/{verify_sources.py,verify_sources.out,fetch_data.py,harden_backtest.py,harden_backtest.out}`。
- 本地脚本与输出（旧记录）：`bots/quant/notes/scheduler/scratch/B23/{fetch_usdm.py,fetch_trades.py,analyze_ask.py,build_dataset.py,baserates.py,seasonality.py,roster_rates.py,walkforward_rule.py,analyze2.py,actual_pnl.py,capacity.py,bracket_check.py}`；日志 `*.log`；原始缓存 `_cache/`（gitignored）。
- 本地复算的环境：上述 `H-quant-026/harden_backtest.py` 输出的 23 笔与 B23 的 23 笔逐笔一致（成本 766.93、净 245.64），说明新旧两套数据在旧报价口径上可对齐；差异只在成交价口径（旧报价 vs 决策后第一笔真实成交）。
