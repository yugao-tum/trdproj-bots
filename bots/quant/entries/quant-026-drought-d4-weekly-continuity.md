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
test_2w: 独立结果按 weekly USDM release 计（州名单与州数同一结算源，合并为 1 个），历史只有 8 个、两周最多 2 个，凑不到 30；失败标准是已成交仓位扣 0.05 吃单费 + 1¢ 滑点后中位净额 ≤0，或分桶延续率跌破可成交 ask，或连续 8 周无正 edge
status: 草稿
confidence: 中
---

整理说明：本条的规则原文、USDM 周度数据、320 个州市场的结算与成交，全部是 2026-10-20 用公开免密钥接口现场取的；脚本与原始输出在 `bots/quant/notes/scheduler/scratch/B23/`。**没有找到 B23 的既有 checks/reviews**，所以没有需要套用的修正。价格侧是**事后回放**，不是真正的预注册前向试验：规则用 2000–2026 的 USDM 分桶延续率构造，然后在这 8 个已关闭周上回放；为避免挑参数，主规则只用分桶基准率 + 固定 5¢ 安全垫，并完整报告 3/5/8/10¢ 敏感性。8 个周里只有 4 周有 YES 成交、3 周有 NO 成交，独立结果远少于 30，故 `status` 只能是 `草稿`。

## 一句话

在每个 USDM 周四发布前的**周三 23:59 UTC**，用上一周官方地图里各州的 D4 面积百分比，按「上周 D4 状态 → 本周仍 D4」的分桶历史延续率给每个州定公允值；只在可成交 ask 比该分桶延续率低至少 **5¢** 时买 YES，或在「上周 D4=0」的州上、NO 的 ask 比「本周仍非 D4」低至少 5¢ 时买 NO，持有到周四发布后的 UMA 结算。

## 钱从哪里来

付钱的是**把每周的 D4 名单当成一次全新事件、而不是把它当成慢变量更新的对手方**。USDM 的 D4 面积是周频、平滑的存量：一个州上周已经在 D4，下周仍在 D4 的概率在我的 25 年样本里是 **95.66%**；上周为 0 的州，下周进入 D4 的概率只有 **0.38%**（2026 年这 8 周是 1.72%）。这个状态转移在周四发布前是公开的：上一周的官方地图和州级 D4 面积都已经在 `droughtmonitor.unl.edu` 上，任何人花一分钟就能查到。

但「为什么这笔钱会持续存在」这条，我只能给一个**弱解释**，不能给结构性保证：这个 series 的最早已关闭事件是 2026-08-25；每周 40 个州市场、单市场成交额中位数只有 **88 USD**，做市商少、报价更新慢；早期（8/25）AR 的上周 D4 是 0.99%，ask 只有 0.50；MS 的上周 D4 是 0.87%，ask 0.51。后面几周同类州的 ask 升到 0.80–0.94，edge 在收敛。**这更像新模板初期的定价摩擦，不是长期锁定的现金流。** 如果市场在 2026-10 之后变得有效，这条就应该被放弃。

## 规则

### 市场模板与结算原文

模板一（州名单）：`state-d4-drought-YYYY-MM-DD`，每个在季州一个独立二元市场，`negRisk=false`。示例 `state-d4-drought-2026-10-13`（2026-10-20 已读，HTTP 200，197,264 bytes），40 个州市场；标题 `Exceptional drought (D4) by state — week of October 13, 2026`。

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
> If the US Drought Monitor has not been published by 11:59 PM ET on the day following the scheduled publication date, this market will resolve to "No".
>
> The resolution source for this market is the US Drought Monitor at droughtmonitor.unl.edu.

模板二（州数）：`states-in-d4-drought-YYYY-MM-DD`，6 档 `0 / 1-2 / 3-4 / 5-6 / 7-9 / 10+`，`negRisk=true`，恰好一档 YES。示例 `states-in-d4-drought-2026-10-13`（HTTP 200，34,030 bytes）。规则原文：

> This market will resolve to the bracket containing the number of coterminous US states (out of 48) with D4 percent area of 0.05% or more in the US Drought Monitor release for the week of October 13, 2026.
>
> Brackets: 0 / 1-2 / 3-4 / 5-6 / 7-9 / 10+. Exactly one bracket resolves "Yes".
>
> The count ranges over all 48 coterminous states — the 48 states excluding Alaska and Hawaii. The District of Columbia and U.S. territories are not considered.
>
> If the US Drought Monitor has not been published by 11:59 PM ET on the day following the scheduled publication date, this market will resolve to the "0 states" bracket.

几个要点：

- **0.05% 是硬阈值**，低于 0.05% 一律 No，即使地图上有边界噪声；USDM 的州级 `D4` 列本身就是面积百分比（CSV 列 `MapDate,StateAbbreviation,None,D0,D1,D2,D3,D4,...`），可以直接比较。
- **只看初审**：第一份发布的周报是最终版，后续修订不算（除非是规则里定义的“明显错误打印”）。
- **州名单随季节变**：10 月有 40 个州在名单里，Alabama 是 5–11 月，Arizona 是全年；名单外的州不是 No，只是没有市场。
- **结算源**：`https://droughtmonitor.unl.edu/`；官方首页原文（2026-10-20 抓取）：“The maps, which are based on analysis of the data, are released each Thursday at 8:30 a.m. Eastern Time.” 首页同时写 “Map released: October 15, 2026 / Data valid: October 13, 2026”，与规则的「周二数据、周四发布」一致。
- **费率**：两个模板的每个市场都返回 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`（Gamma 实取），与 GUIDE §8 的天气板块 0.05 一致。

已关闭样本：series `drought-d4-weekly`（id=12688，`recurrence=weekly`）在 Gamma 返回 **16 个 closed 事件** = **8 个周发布 ×（州名单 + 州数）**，`endDate` 从 2026-08-27 到 2026-10-15。每周 40 个州市场，共 **320 个州市场**；州数事件每周 6 档，共 48 个档。当前还有一个 open 事件 `state-d4-drought-2026-10-20`（`endDate=2026-10-22T13:00:00Z`，40 个州市场），已用于前向登记（见证据 6）。

### 交易规则（前向冻结版）

以下规则是为 2026-10-20 之后的周度发布**冻结**的；历史回放用同一套规则，但阈值敏感性全部列出，事后不挑。

1. **决策时刻**：每周三 **23:59 UTC**（= 周三 19:59 ET；比周四 8:30 ET 发布早约 12.5 小时，比市场 `endDate=13:00 UTC` 早 13 小时 1 分）。
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

### 3）历史回放：8 个周、23 笔、22 笔盈利

**方法**：对 320 个州市场，按上面冻结规则在周三 23:59 UTC 取最后 ask/bid 侧成交（72 小时内），用 1¢ 滑点 + 0.05 吃单费；只做规则触发的交易，不做事后筛选。价格是 data-api 的**成交价代理**，不是历史盘口（历史盘口无公开来源）。

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

### 4）容量：总名义额只有约 750 USD/8 周

- 320 个州市场里：**30 个零成交**；有成交的 290 个，单市场中位总成交额 **88 USD**，p90 为 350 USD，最大 2,670 USD。
- 8 周州市场总成交额 **55,938 USD**，按周从 **965** 到 **13,642 USD** 不等。
- 截止前 72 小时内有 ask 侧成交的州市场只有 **52/320**；有任意成交的 **181/320**。
- 主规则 14 笔 YES 的最后 ask 名义额合计 **577.55 USD**；9 笔 NO 的最后 bid 名义额合计 **170.66 USD**；合计 **748.21 USD**。这就是“按最后成交份数”能算出的全部容量，5,000 USDT 根本用不上。
- 一个月约 **12 次机会**（23 笔/8 周 × 4.33），名义额约 **400–800 USD/月**。容量是这条策略的硬约束，不是资金。

### 5）为什么只做州名单、不做州数

州数档在 8 个周里全部是 `10+`：按 48 州计 `12,12,12,12,12,10,11,12`。一个 8/8 都相同的档，在样本内没有转移可学；买 `10+` 的 YES 在 0.95 以下看起来“稳”，但那只是 8 个相关周，不是 30 个独立结果。州名单有 320 个州-周、5 次进入和 5 次退出，才有横截面变化可检验；所以本条的交易对象是州名单。

### 6）前向登记（2026-10-20）

当前 open 事件 `state-d4-drought-2026-10-20`（`endDate=2026-10-22T13:00:00Z`）的 40 个州市场，在 2026-10-20 快照里：绝大多数 `bestAsk=0.99`，`OK` 的 ask 也是 0.99，`AR` 是 0.999，`WI` 是 0.99；按 5¢ 安全垫，`OK`（prior 16.55%，p_b≈0.981，阈值 0.931）和 `WI`（prior 4.47%，p_b≈0.943，阈值 0.893）都**不触发**。**2026-10-20 快照没有合格报价**；正式判定要等 2026-10-21 23:59 UTC 截止时的最后 ask。这条前向记录从 2026-10-22 的发布开始，至少连续记 30 个周发布才有统计意义。

## 数据

- **USDM 州级周度统计（免费、免密钥）**：`https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=<州FIPS>&startdate=1/1/2000&enddate=10/20/2026&statisticsType=1`，必须带 `Accept: text/csv`（不带时返回 0 字节，实测）。返回列 `MapDate,StateAbbreviation,None,D0,D1,D2,D3,D4,ValidStart,ValidEnd,StatisticFormatID`；`D4` 是州面积百分比，2000-01-04 起周度。2026-10-20 抓取单州 96–99 KB，HTTP 200。48 个州各存一份 CSV 在 `_cache/usdm/`。
- **USDM 发布节奏与地图页（免费、免密钥）**：`https://droughtmonitor.unl.edu/`（HTTP 200，121,145 bytes）。原文：“The maps, which are based on analysis of the data, are released each Thursday at 8:30 a.m. Eastern Time.”；首页同时给出 “Map released: October 15, 2026 / Data valid: October 13, 2026”。
- **USDM 综合统计下载页**：`https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx`（HTTP 200，587,046 bytes）。短名单里猜的直连 `.../data/csv/20260901_dmstatistics.csv` 返回 404；可编程取数用上面的 REST，不用猜 CSV 路径。
- **Polymarket Gamma（免费、免密钥）**：`https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100`（16 个已关闭事件）；`https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-13`（HTTP 200，197,264 bytes，规则、40 个市场、费率）；`https://gamma-api.polymarket.com/events?slug=states-in-d4-drought-2026-10-13`（HTTP 200，34,030 bytes，6 档）。
- **Polymarket data-api 成交（免费、免密钥）**：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000`；已关闭市场可取到逐笔 `size/price/side/outcome/timestamp`。8 周 320 个州市场共 2,158 笔成交（另有州数档 186 笔，未用于交易），原始缓存 `_cache/trades_all.json.gz`（252 KB gzip）。
- **缺失，必须写清**：历史盘口（bid/ask 快照）没有公开来源；本文只能用最后成交价做代理。USDM 的“当时首发布值”也没有单独的归档，REST 返回的是当前值；不过 320/320 与 Polymarket 结算一致，说明至少在这 8 周里修订没有改变结果。

## 两周内怎么检验

- **独立结果按 weekly release 计**：同一周的州名单和州数是同一份 USDM 发布、同一结算源，合并为 **1 个**；不同州、不同档都不独立。历史只有 **8 个**（2026-08-25..2026-10-13），两周最多再拿 **2 个**；凑到 30 个约需 **7 个月总样本**（还差 22 个周发布，约 5 个月）。按 GUIDE §2 第 6 条，本条应进**待选区**，`status` 只能 `草稿`。
- 两周内能做完的：
  1. 用已关闭的 8 周做**回放**（本文已完成）：320 个州市场、320/320 结算一致、23 笔触发、22 笔盈利；这是横截面证据，不是 30 个独立结果。
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
- **每笔成本 = 吃单费 + 1¢ 滑点/半价差缓冲**。历史盘口取不到，1¢ 是假设值，不是实测；这是本条最软的一个数。按 0.50 的 YES 算，总成本约 3.5¢/份（7% 的投入）；按 0.82 算约 1.74¢/份（2.1%）；按 0.93 算约 1.33¢/份（1.4%）。
- **单笔容量**：按最后成交份数，14 笔 YES 合计 767.7 份、名义额 577.55 USD；9 笔 NO 合计 252.9 份、名义额 170.66 USD。单市场通常只能放 **20–200 USD**；`TX` 这类成交较大的州可到几百 USD。
- **一个月多少次**：约 **12 次**（23 笔/8 周），名义额 **400–800 USD/月**。5,000 USDT 的总资金约束天然满足，但**用不满**；单场所 2,500 也远高于实际需要的几百 USD。容量是约束，不是资金。
- **占款天数**：周三 23:59 UTC 进场 → 周四 13:00 UTC 市场 `endDate` → UMA 结算；样本里 `closedTime` 从发布当天到发布后 3 天不等（如 8/27 事件 8/30 关闭，9/3 事件 9/4 关闭）。按 **0–3 天**（多数当天）占款估算。8 周 23 笔、总成本 766.93 USD、净 245.64 USD；如果按 5,000 总资金算，8 周回报约 **4.9%**（年化约 36%，但这是 8 周样本，不能当预期）。

## 风险

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
- **平台/流动性**：模板 `restricted=true`（部分市场），`negRisk=false` 的州名单每州独立结算；薄市场里可能买不到、卖不掉，或者被单笔大额成交把价格打穿。

## 改进了什么

不适用（`kind: new`）。与最接近的条目相比：

- **quant-015（全球月均温 ERA5 nowcast）**：同为 `weather`/`S`，但 quant-015 是“用 ERA5 整月值预测 NASA GISTEMP 月距平档”，标的是连续数值的月频 nowcast；本条是“用上一周官方地图预测下一周州级二元 D4 名单”，标的是 0.05% 阈值两侧的状态转移，频率是周、横截面是 40 个州。两者结算源、状态变量、市场模板都不同。
- **quant-012（地震周计数）/ quant-019（麻疹计数阶梯）**：它们交易的是“官方计数落在哪一档”的计数阶梯；本条不交易计数档（样本内 8/8 都是 `10+`，退化），交易的是州名单的延续/进入。状态变量是分桶转移率，不是计数过程。
- **dot-001/dot-002（城市日最高温）**：标的是单日最高温的整数档，结算源是 NOAA timeseries；本条是周度 USDM 州级面积百分比，不是温度预报。
- **muse-own2-tail-weather-expiry-favfade**：标的也是天气热门档，但机制是“临到期热门高估买 NO”的行为偏差；本条是“上周 D4 状态的延续率”基准率，不依赖到期前的时间衰减。

## 门槛自查

1. **机制说得清：满足** — 一句话：上周已经在 D4 的州下周仍在 D4 的概率 95.66%（25 年 5,411 个州-周转移），上周为 0 的州下周进入 D4 只有 0.38%；市场在新模板初期给前者的报价低到 0.50–0.89。付钱方是把周度名单当独立事件、不查上一周地图的对手方。**但“为什么持续”只有薄市场/新模板的弱解释，8 周内 edge 已在收敛。**
2. **有免费数据能检验：不确定** — USDM REST 免费免密钥、2000 年起周度，Polymarket Gamma/data-api 也免费；但**独立历史结果只有 8 个周发布**（州名单 + 州数同一结算源合并），达不到“预测市场至少 30 个独立结果”。只能从 2026-10-22 起前向记录，约 5 个月才够 30 个（总样本约 7 个月）。
3. **小资金能做：满足** — 单州 20–200 USD、单周 ≤400 USD、专线 ≤1,000 USD，远低于 5,000 总资金和 2,500 单场所；不加杠杆、不借钱，买 YES/NO 的最大亏损就是权利金。**容量很小：8 周总名义额约 750 USD，5,000 用不上。**
4. **不重复：满足** — 见“改进了什么”。与 quant-015 的月温 nowcast、quant-012/019 的计数阶梯、dot-001/002 的日最高温、muse 的临到期热门都不是同一机制；本条做的是 USDM 周度州级 D4 名单的延续率，仓库内除本条外没有同模板条目（`grep -rilE "Drought Monitor|Exceptional Drought|USDM" bots/*/entries known/` 只命中本条自己）。
5. **扣成本后粗算够用：满足（样本内）/不确定（样本外）** — 23 笔按最后成交份数计，成本 766.93 USD、净 245.64 USD（+32.03%）；按每份等价计 +24.22%；加 5¢ 滑点后 YES +23.08%、NO +11.92%；加 10¢ 滑点后 YES +15.62%。**但只有 4 个活跃周、8/25 一周贡献 63.3% 的净额，且价格是成交价代理，不是盘口。** 所以“扣成本后为正”在样本内成立，样本外没有被证明。
6. **两周内能检验：不满足** — 独立结果按 weekly release 计，历史 8 个，两周最多 2 个；30 个约需 7 个月总样本（还差 22 个周发布）。按 GUIDE §2 第 6 条，本条应进**待选区**。
7. **出处可查：满足** — 每个规则原文、USDM 数据、费率、成交都给了 URL 和访问日期；USDM 的 320/320 结算复算、67,056 个转移、23 笔回放都由本地脚本重算，脚本和 stdout 在 `notes/scheduler/scratch/B23/`。Gamma 的 `volume`/`liquidity` 字段本文没有用作结论，成交额全部用 data-api 逐笔成交复算。

## 出处

- `https://droughtmonitor.unl.edu/` — 访问 2026-10-20 — 已读（发布节奏 “released each Thursday at 8:30 a.m. Eastern Time”；“Map released: October 15, 2026 / Data valid: October 13, 2026”）
- `https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx` — 访问 2026-10-20 — 已读（HTTP 200，587,046 bytes；直连 CSV 路径 404）
- `https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=01&startdate=8%2F1%2F2026&enddate=10%2F20%2F2026&statisticsType=1` — 访问 2026-10-20 — 已读（HTTP 200，922 bytes；列 `MapDate,StateAbbreviation,None,D0,D1,D2,D3,D4,...`）
- `https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100` — 访问 2026-10-20 — 已读（16 个 closed 事件，8 个周发布 × 2）
- `https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-13` — 访问 2026-10-20 — 已读（HTTP 200，197,264 bytes；40 个州市场；规则原文；`feeSchedule.rate=0.05`）
- `https://gamma-api.polymarket.com/events?slug=states-in-d4-drought-2026-10-13` — 访问 2026-10-20 — 已读（HTTP 200，34,030 bytes；6 档 `0/1-2/3-4/5-6/7-9/10+`；`negRisk=true`）
- `https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-20` — 访问 2026-10-20 — 已读（open 事件，40 个州；多数 `bestAsk=0.99`）
- `https://data-api.polymarket.com/trades?market=0xbf70aa5a4a493a1201d21be0121d3de42ceb58121fb6401da0bd4c1beb83cfdd&limit=1000` — 访问 2026-10-20 — 已读（HTTP 200，2,823 bytes；`size/price/side/outcome/timestamp`）
- `https://gamma-api.polymarket.com/events?tag_slug=drought&closed=true&limit=100` — 访问 2026-10-20 — 已读（37 个事件：16 个周度 D4、2 个 deadline D4、19 个其他；deadline 型不纳入本条）
- 本地脚本与输出：`bots/quant/notes/scheduler/scratch/B23/{fetch_usdm.py,fetch_trades.py,analyze_ask.py,build_dataset.py,baserates.py,seasonality.py,roster_rates.py,walkforward_rule.py,analyze2.py,actual_pnl.py,capacity.py,bracket_check.py}`；日志 `*.log`；原始缓存 `_cache/`（gitignored）。
