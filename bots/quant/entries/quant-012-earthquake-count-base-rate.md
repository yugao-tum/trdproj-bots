---
id: quant-012
name_zh: 地震周计数：按USGS基率定价
name_en: Earthquake weekly-count ladders priced with Gutenberg-Richter / USGS base rates
bot: quant
date: 2026-10-20
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「本周全球 M6.5+（或 M5.5+）地震发生几次」分档（0/1/2/3/4/5/>5 共 7 档、negRisk）+「M7.0+ 在某日前是否发生」二元
venues: Polymarket
data: USGS FDSN event API（免费免密钥，2000 年起完整目录）；Polymarket Gamma/CLOB（免费免密钥，价格历史只有市场创建后，约 3–4 天）；历史已关闭地震市场的价格取不到
test_2w: 按 event 计独立结果，两周只能拿到约 4 个 event（6.5 与 5.5 两条周度序列各每周 1 个），凑不到 30；失败标准是已成交 NO 份额的中位已实现毛利≤0 或基率模型校准（log loss）劣于市场
status: 待核
confidence: 中
---

整理说明：本条所有基率数字都是我在 2026-10-20 从 USGS 目录当日拉取后自己算的（公式在下面写出）；所有盘口价格是同一日 Gamma/CLOB 快照。**没有做回测**：已关闭地震市场的 CLOB 价格历史返回空，所以只有「基率 vs 当前价格」的横截面对照，不是收益证明。

## 一句话

在 Polymarket 每周的「本周全球发生几次 M6.5+ 地震」七档阶梯上，用 USGS 历史目录算出的 7 日计数分布当公允值；只在档位被高估时**做 maker 卖 YES / 买 NO**，持到结算（约 6 天），不吃单；因为按快照中的卖价，七个档全部是负 EV。

## 钱从哪里来

付钱给你的是**对「本周地震次数」的尾部档出价过高的散户**，加上平台给的流动性奖励。它持续存在的原因是：这类市场是每周重复上市的固定模板，参与者按新闻情绪而不是按泊松/经验基率出价——2026-10-20 快照里七档的卖价之和是 **1.218**（买齐七档必亏 21.8¢），而七档买价之和只有 **0.924**，整个阶梯系统性溢价；溢价集中在 ≥3 的尾部档（中价合计 0.126，经验基率只有 0.0817，1.54 倍）。这不是套利：没有一条腿能锁定，收益来自「报价被情绪单打中」。奖励部分来自 `clobRewards`（见成本节），量很小，只当补贴。

## 规则

**结算原文（Gamma 事件 `how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25`，2026-10-20 已读）**：

- 计数区间：「between October 19, 2026, 12:00 AM ET and October 25, 2026, 11:59 PM ET」——即**美东时间周一 00:00 到周日 23:59**，不是 UTC 日界。2026-10-19 是星期一（我自己核过）。
- 数据源：「the United States Geological Survey (USGS) Earthquake Hazards Program, with the minimum magnitude set to 6.5 and the date parameters set to the relevant dates」，链接是 `https://earthquake.usgs.gov/earthquakes/search/`。也就是 USGS 的 7 天窗口检索结果条数，**不是**某个机构的「官方震级」表。
- 震级口径：USGS 目录的 `mag` 字段（可能是 `mww`/`mwb`/`mb`，见下），「6.5 or higher」——含 6.5。
- 迟报：「may remain open until 48 hours after the market's closing time」；最后一天有合格地震时「may remain open for 24 hours to allow for revisions to the recorded magnitude」，之后按最新数据结算。
- 缺数据兜底：「If no earthquake data ... by 48 hours after the market's closing time, this market will resolve to the lowest bracket.」（即判 0 档）
- 覆盖范围：「anywhere on Earth」，无地理排除，含海域与无人区。
- 七档互斥且穷尽：0/1/2/3/4/5/more than 5，`negRisk = true`，每档一个独立二元市场（`groupItemTitle` 分别为 `0,1,2,3,4,5,more than 5`）。
- 同族还有：M5.5+ 同模板（9 档）、「Megaquake（M7.0+）在某日前」、每月「How many 7.0 or above earthquakes in <月>」、「最高震级分档」、以及地域版「Where will a 6.0+ earthquake occur」。

**交易规则（本条的提案，不是已验证的盈利规则）**

1. 公允值：对第 i 档算出 `p_i`。做法 A（纯泊松）：`p_i = e^-λ λ^i / i!`，`λ` 用近期窗口的周均次数。做法 B（经验分布，推荐）：直接取历史 7 日计数 bin 的频率；因为经验分布比泊松更胖，泊松会低估尾部。
2. 周内更新（泊松细化）：窗口已过比例 `f` 时，若已记录 `k` 次，剩余次数 ≈ `Poisson(λ(1-f))`，故 `P(总次数 = n) = P(Poisson(λ(1-f)) = n-k)`，`n<k` 时为 0。经验分布版同理：把历史 bin 计数按 `(1-f)` 缩尾后加 `k`（自助抽样）。若市场还没反映当天已发生的地震，这一步就是主要 edge。
3. 只挂 maker：只在高估档挂**买 NO 的限价单**，价格 `q_i = 1 - p_i - m`，`m = 0.01`（1¢ 安全垫；`m` 必须在成交前写死，成交后不得改）。若 `q_i` 低于当前 NO 最优买价（没有排队价值）则跳过该档，不做。
4. 不做做空裸卖 YES：只用「买 NO」表达看空档位，避免 negRisk 转换/铸造的操作风险。
5. 仓位：每档在险 NO 份额 ≤ 100 份；单个 event 全部档位合计在险金额 ≤ 300 USDT；同时在手的 event ≤ 4 个；总资金按 5,000 USDT 记，单场所 ≤ 2,500 USDT。
6. 出场：**不主动平仓**，持有到 UMA 结算（约 6 天 + 最多 48 小时争议期）。理由：平仓要付吃单费和价差，而票面 1.00 的收敛是免费的。
7. 风控熔断：同一周内已记录地震数 `k ≥ 3` 时，全部剩余 NO 挂单撤掉（尾部已经实现，模型不再有意义）；任一 event 浮亏超过在险金额 50% 时同周停止新增挂单。
8. 明确不做：不做吃单侧（下面证据里七档在卖价上全是负 EV）；不做「预测下一次大震位置」类市场（无基率可依）。

## 证据

### 1）基率：USGS 目录，我自己算的

数据：`https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2000-01-01&endtime=2026-10-01&minmagnitude=6.4&orderby=time-asc`，抓回文件共 **1,513 行（含表头）**，其中 `mag ≥ 6.5` 的 **1,216** 条。按从 2000-01-03（星期一）起切成整 7 天 bin（UTC 对齐，与 ET 周界相差 4–5 小时，属已知近似），得 **1,395** 个完整 bin，bin 内合计 1,216 条（与查询总条数一致，说明无遗漏）。

- 周均次数：`1216 / 1395 = 0.8717` 次/周。
- 经验 7 日计数分布（`count: bins (占比)`）：
  - `0: 663 (47.53%)`，`1: 440 (31.54%)`，`2: 178 (12.76%)`，`3: 70 (5.02%)`，`4: 29 (2.08%)`，`5: 5 (0.36%)`，`6: 7 (0.50%)`，`7: 1`，`8: 1`，`12: 1`。
  - 派生：`P(≥3) = (70+29+5+7+1+1+1)/1395 = 114/1395 = 0.0817`；`P(≥5) = 15/1395 = 0.0108`。
- 泊松对照（`λ=0.8717`）：`P(0)=0.4182`、`P(1)=0.3646`、`P(2)=0.1589`、`P(3)=0.0462`、`P(4)=0.0101`、`P(5)=0.0018`、`P(>5)=0.0003`。**结论：经验分布明显比泊松胖**——`P(0)` 47.5% vs 41.8%，`P(≥3)` 8.17% vs 5.83%（泊松 `P(≥3)=1-0.4182-0.3646-0.1589=0.0583`）。这就是「按泊松定价会系统性卖便宜尾巴」的原因，也是本条必须用经验分布而不是教科书泊松的理由。
- 分段稳定性（同一文件的子集，我算的）：2000-01-01..2026-10-01 `1216` 条 / 45.46 次每年；2016-01-01 起 `434` 条 / 40.38 次每年；2021-01-01 起 `243` 条 / 42.28 次每年；2025-10-01 起 `42` 条 / 42.03 次每年。**近期约 0.80 次/周，比 26 年均值 0.8717 略低**，所以 `λ` 取 0.80–0.87 之间做敏感性，别只用一个数。
- 交叉核对（`/count` 端点，2026-10-20 抓）：`starttime=2015-01-01&endtime=2026-01-01&minmagnitude=6.5` → `{"count":462,"maxAllowed":20000}`；同参数 `minmagnitude=7.0` → `{"count":153,...}`。即 11 年 462 条 = 42.0 次/年，与上段一致。`minmagnitude=5.5` 的同一请求首次抓取返回 **502 Bad Gateway**，复核（2026-10-20）返回 `{"count":5031,"maxAllowed":20000}`，即同一 11 年窗口 5,031 条；5.5 序列的逐年基率未逐段拆分。

### 2）当前盘口（Gamma 快照，2026-10-20）

事件 `how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25`：`startDate=2026-10-16T14:23:50Z`、`endDate=2026-10-26T03:59:00Z`、`volume=1467.663831`、`liquidity=5469.92364`、`negRisk=true`，全部七档 `orderMinSize=5`、`orderPriceMinTickSize` 多为 `0.01`（4、5、>5 档为 `0.001`）。

| 档 | bestBid | bestAsk | mid | `outcomePrices` | 经验基率 | mid − 基率 |
|---|---|---|---|---|---|---|
| 0 | 0.46 | 0.51 | 0.485 | `["0.485","0.515"]` | 0.4753 | +0.010 |
| 1 | 0.30 | 0.34 | 0.32 | `["0.32","0.68"]` | 0.3154 | +0.005 |
| 2 | 0.11 | 0.17 | 0.14 | `["0.14","0.86"]` | 0.1276 | +0.012 |
| 3 | 0.04 | 0.11 | 0.075 | `["0.075","0.925"]` | 0.0502 | +0.025 |
| 4 | 0.011 | 0.059 | 0.035 | `["0.035","0.965"]` | 0.0208 | +0.014 |
| 5 | 0.001 | 0.01 | 0.0055 | `["0.0055","0.9945"]` | 0.0036 | +0.002 |
| >5 | 0.002 | 0.019 | 0.0105 | `["0.0105","0.9895"]` | 0.0072 | +0.003 |

- 卖价之和 `0.51+0.34+0.17+0.11+0.059+0.01+0.019 = 1.218`；买价之和 `0.46+0.30+0.11+0.04+0.011+0.001+0.002 = 0.924`；中价之和 `1.071`。**吃单侧无套利**：买齐七档付 1.218 必收 1.000。
- 吃单 EV（每份 = 基率 − 卖价，我算的）：`0: −0.035`、`1: −0.025`、`2: −0.042`、`3: −0.060`、`4: −0.038`、`5: −0.006`、`>5: −0.012`。**七档全负**，这就是为什么本条只做 maker。
- maker 侧 EV（买 NO 于 `1 − 卖价`，被填则每份 `= 1 − 基率 − (1 − 卖价) = 卖价 − 基率`）：`0: +0.035`、`1: +0.025`、`2: +0.042`、`3: +0.060`、`4: +0.038`、`5: +0.006`、`>5: +0.012`。按占用资金折：3 档买 NO 于 `0.89`，收票面 `0.9498`，**6 天 +5.98¢ / 0.89 = +6.7%**。这是**模型的算术期望**，不是实测；成交概率未验证。
- CLOB `prices-history`（`market=<桶0 token>&interval=max&fidelity=60`）显示该市场 `t=1792162843`（UTC 2026-10-16 15:00:43）`p=0.345`，`t=1792270842`（UTC 2026-10-17 21:00:42）`p=0.475`，中间在 0.42–0.475 间震荡；桶 3 同一段从 `p=0.225` 起步，后段在 `0.055–0.225` 区间震荡。说明档位价格确实在大幅漂移，maker 有对手单。

### 3）一周内「已发生未结算」的现成例子

事件 `how-many-6pt5-or-above-earthquakes-worldwide-october-12-october-18`（`endDate=2026-10-19`）：Gamma 在 2026-10-20 仍返回 `closed=false`、七档全未结算；而 USGS `/query?starttime=2026-10-12&endtime=2026-10-19&minmagnitude=6.5` 当天返回**恰好 3 条**（`us6000u2mq` M6.9 2026-10-16T03:35:31.925、`us6000u214` M6.8 2026-10-13T12:23:07.248、`us6000u1z5` M6.7 2026-10-13T05:44:46.919）。该事件「3」档 `outcomePrices=["0.95","0.05"]`、volume 1930.25，其余档 0.0035–0.05。**这说明市场对已实现的计数反应是快的**（0.95 对 1.0 只余 5¢），所以「周内更新」这条 edge 不能想当然，只能靠逐个 event 记录来验证。

### 4）频率与容量（我数的）

`https://gamma-api.polymarket.com/events?tag_slug=earthquake&limit=500&closed=true&order=endDate&ascending=false` 返回 **69** 个已关闭事件，`endDate` 从 `2024-09-30` 到 `2026-10-19`，成交额合计 **$5,869,975**。按标题分类：`how-many` 周度阶梯 **37** 个、「Megaquake」**17** 个、「7.0 or above」单一阈值 **12** 个、其他 **3** 个。按 `endDate` 月份：2026-06 5 个、2026-07 9 个、2026-08 10 个、2026-09 9 个、2026-10 5 个（10 月未完）→ **近期约每月 9–10 个 event**；2 条周度序列（6.5+ 与 5.5+）各每周 1 个，理论约 8–9 个/月。2025 年多数月份只有 1–3 个，说明这个系列的密度是平台后来才加上去的，**不能把 2026 下半年的密度外推到明年**。

单 event 成交额差异极大（Gamma 快照）：`how-many-6pt5-...october-19-october-25` = 1,467.66；`october-12-october-18` = 15,189.73；`september-28-october-4` = 9,449.79；`march-23-march-29` = 259,657.7。**这就是容量上限的量级：几百到几万美元一个 event**，本条 300 USDT/event 的额度在最近的稀薄期已经是 event 成交额的约 20%，实际能挂到多少须实测。

来源自报的成交额/流动性字段均未用成交明细复现，**来源自报，未核实**。

## 数据

- USGS 目录（免费、免密钥、无需注册）：`https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=...&endtime=...&minmagnitude=6.4`；条数端点 `/count?format=geojson&...`；1970 年起基本完整，`minmagnitude=6.4` 起 USGS 全球台网基本无漏检（**这是我的判断，未在本次抓取中核实完备性**）。字段：`time, latitude, longitude, depth, mag, magType, net, id, place, status`。
- Polymarket Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?slug=<event-slug>`（规则原文、`outcomePrices`、`bestBid/bestAsk`、`feeSchedule`、`clobRewards`）；`/public-search?q=earthquake&limit_per_type=50&events_status=all`（找同族市场）；`/events?tag_slug=earthquake&closed=true&limit=500`（数频率）。
- Polymarket CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max&fidelity=60`。**只有市场创建之后的价格**（本族市场创建约在窗口开始前 3–4 天）。
- 缺失且必须承认：已关闭地震市场的 CLOB 价格历史返回 `{"history":[]}`（我用 2025-08-31 那个事件的 token 试过），所以**历史各档报价取不到，无法做事后回测**，只能从现在起前向记录。逐笔成交只有 data-api 约最近 2 万笔/市场，本次未取。

## 两周内怎么检验

- **独立结果按 event 数**（不是按档、不按市场）：七档共享同一个 USGS 计数，算 1 个结果。6.5+ 与 5.5+ 两条序列若在同一周、结算源相同，也应合并为 1 个（严口径）；宽松口径最多 2 个/周。**两周最多 4 个 event**，因此本条**不可能在两周内拿到 30 个独立结果**，只能作为「先跑通、先看成交」的小样本，30 个结果大约需要 15 周。这一点我如实写在这里，`status` 只给 `草稿`。
- 每天记录：USGS 当日 M6.5+ 事件列表（`eventid, time UTC, mag, magType, status`）、各档 `bestBid/bestAsk/outcomePrices`、我挂的 NO 报价与实际成交、CLOB 盘口。
- 校准检验（可以在两周内做完，用历史做样本）：拿 1,395 个历史 7 日 bin 做留一法，比较三种预测器的 log loss——(a) 常数经验分布、(b) `λ=0.80` 泊松、(c) 市场价（用小样本即可）。若 (b) 明显差于 (a)，说明「必须用经验分布」这一条判断成立；这个检验不依赖 Polymarket 数据。
- **失败标准（写死，事后不改）**：
  1. 已成交 NO 份额的**中位已实现毛利 ≤ 0**（毛利 = 票面 1.00 − 成交价，不含未成交挂单）；
  2. 或两周内成交份额 < 20 份（流动性不足，无法验证，判「容量失败」而不是「策略失败」，但也进待选区）；
  3. 或基率模型对「3」档的 7 日校准误差 > 2¢（模型本身坏了）。
- 不允许的自我安慰：不能用「挂单没成交所以没亏」当作正结果；不能挑成交到的那几档报收益。

## 成本与容量

- **费用（Gamma 实取，不是查表）**：本族每个市场的 `feeSchedule = {"exponent": 1, "rate": 0.05, "takerOnly": true, "rebateRate": 0.25}`，`feesEnabled=true`、`takerBaseFee=1000`、`makerBaseFee=1000`。GUIDE 第 8 节把天气/经济/文化列为 `0.05`，与实取一致。
  - 吃单费（按 GUIDE 公式 `费用 = 份数 × 费率 × p × (1 − p)`）：`p=0.11` → 每份 `0.05×0.11×0.89 = 0.0049`；`p=0.50` → `0.0125`；`p=0.075`（3 档 mid）→ `0.0035`。折成投入资金比例 `= 0.05×(1−p)`：`p=0.11` 时 **4.45%**。
  - maker 费 0，另返对手吃单费的 `rebateRate=0.25`（25%）。
  - **每笔成本 = 费 + 半个买卖价差**。3 档价差 `0.11−0.04 = 0.07`，半价差 `3.5¢`——这就是不可以吃单的定量原因：吃单要吃 3.5¢ 的价差，而模型 edge 只有 6.0¢，扣 0.49¢ 费后剩 2.0¢，但半价差已经把 edge 吃掉 58%，且这是按 mid 成交的乐观假设。做 maker 时半价差不是支出，代价变成「排队 + 逆向选择」，后者**未量化**。
- **单笔能放多少**：3 档 NO 挂 `0.89`、100 份 = 89 USDT 占用；七档全挂最多约 `(1−q_i)×份数`，按上表全部定价约 100 份合计约 500 USDT，超出单 event 300 USDT 上限，故实际按 300 分给 ≤3 档。占款天数 = 窗剩余 + 2 天争议 ≈ 6–8 天。
- **一个月多少次机会**：近期 9–10 个 event/月（我在 Gamma 上数的已关闭事件按 `endDate` 月份）；但每个 event 的成交量只有几百到几万美元，**机会数是够的，单次的钱不够**。5,000 USDT 里给这条线 1,000 USDT 上限就够，剩余资金不会被占用——这既是优点（不占资金）也是缺点（赚的钱对总资金微不足道）。
- **流动性奖励（补贴，不是主收益）**：该 event 的 `clobRewards` 日率合计 **20 USDC/日**（0 档 11、1 档 6、2 档 2、3 档 1，4/5/>5 档无），`startDate=2026-10-20`、`rewardsMinSize=20`、`rewardsMaxSpread=5.5`（4/5/>5 档为 `4.5`）。按 Q-score 规则（见 dot-032），$20/日按份额瓜分，另一件事要提醒：GUIDE 要求按 `feeSchedule/feeRate` 实取值算，这里的 maker 返佣池比例是 `rebateRate=0.25`。这笔钱**不足以**支撑策略，只覆盖部分风险。
- **容量结论**：500–1,000 USDT 能放下（远低于 2,500 单场所上限），但 5,000 USDT **放不满**，因为 event 成交量本身就是几百到几万美元量级，且做 maker 只占其中被吃单的一部分。

## 风险

- **余震造成的过度离散（最大风险）**：一周内 5、6、7、8、12 次都出现过（12 次那周是我 bin 出的最大值）。一次 M8 主震会在同一周带出多个 M6.5+ 余震，`0/1/2` 档同时归零、`>5` 档直接命中。按泊松定价会严重低估这种聚集，按经验分布也只是把聚集「平均进去」，**不能预测哪一周会聚集**。做法 B 加 `k≥3` 撤单熔断只是止血，不是解决。
- **震级修订**：USGS 会把 `6.4` 修成 `6.6`，或 `6.6` 修成 `6.4`（`magType` 从 `mb` 改 `mww` 时常见）。规则允许「最后一天有合格地震 → 多开 24 小时按最新数据结算」，所以 5→6 档的边界单会翻。
- **数据源与时区**：结算按 USGS 检索结果条数 + ET 周界；USGS 目录对同一次地震只出 1 条（`id` 唯一），但**目录里另有 `type` 字段**（`earthquake`/`explosion`/`quarry` 等），规则只说「earthquakes」，本次未核 USGS 检索页是否默认过滤 `type=earthquake`——**未查到**，属规则歧义。
- **「按最低档结算」兜底**：若 48 小时内 USGS 没发布该期数据，结算判 0 档。买 NO 在 0 档上会因此全输。极低概率但后果是本金全损。
- **结算争议**：UMA 提案，`umaBond=500`、`umaReward=5`、`customLiveness=0`。地震这类客观数据出争议的概率低，但 2026-10-12–18 那个事件在 `endDate` 已过后一天仍是 `closed=false`，说明**结算有滞后（数小时到数天）**，资金被动占住的时间会比"6 天"长。
- **流动性/逆向选择**：单 event 成交量 1,467 USD（10/19–10/25 那个）意味着挂单可能长期不成交；一旦成交，往往是有人拿到了更快的地震信息（USGS 目录有分钟级延迟），你卖在了坏消息上。这个成本**未量化**，是本节最大的未知。
- **平台**：`restricted=true`（多个同族事件），negRisk 市场的转换/赎回操作有额外步骤和 gas；本条只用「买 NO」，不涉及转换。
- **奖励收缩**：`clobRewards.rewardsDailyRate` 逐市场配置，`rewardsAmount` 当前为 0（日率 20 但已发 0），可随时改；不能把 20 USDC/日 当固定收入。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付钱方是对尾部档出价过高的情绪单；量化证据是七档卖价之和 1.218（买齐必亏 21.8¢）、≥3 的四档中价 0.126 对经验基率 0.0817（1.54 倍）。谁付钱清楚了，但「为什么这钱持续存在」只有横截面单点证据，不是时序证据。
2. **有免费数据能检验：不确定** — 基率侧完美（USGS 免费免密钥，1,216 条 / 1,395 个 7 日 bin，26 年）；**价格侧不行**：已关闭地震市场的 CLOB 价格历史返回 `{"history":[]}`，只能用市场创建后 3–4 天的数据前向记录。所以历史上 ≥30 个独立结果的「价格」拿不到。
3. **小资金能做：满足** — 300 USDT/event、≤4 event、总计 ≤1,000 USDT，远低于 2,500 单场所与 5,000 总资金；不加杠杆、不借钱；NO 买单最大亏损就是本金。容量写清了：几百到几万美元/event，5,000 USDT 放不满。
4. **不重复：不确定** — 需要主审确认。本条与 dot-032（流动性奖励）共用激励池字段，但收益来源不同（本条是基率定价的方向性 maker，dot-032 是纯奖励份额）；与任何「天气市场分档」（如气温分档）不同，变量是地震计数与 USGS 目录，不是气象站观测。仓库内是否有同类条目我未逐条核。
5. **扣成本后粗算够用：不确定** — 吃单侧明确不够（七档全负 EV，见上表），只有 maker 侧在**模型期望**上有 0.6–6.0¢/份；maker 费为 0，但成交概率与逆向选择**未量化**，`observed_net_return = null`，`backtest_count = 0`（只表示没有回测，不表示收益为 0）。若有成交，按 3 档算 6 天 +6.7%（模型期望，未含逆向选择），年化需按资金占用天数折算且**样本不足，不做年化外推**。
6. **两周内能检验：不满足** — 独立结果按 event 计，两周最多 4 个（6.5+ 与 5.5+ 两条序列各 1/周，严口径还要合并成 2 个），拿不到 30 个；30 个约需 15 周。按 GUIDE 第 2 节第 6 条，本类应进**待选区**。
7. **出处可查：满足** — 每个数字都有 URL + 访问日期 + 取数方式；基率是我从原始 CSV 算的并写了公式与中间量（1,216 / 1,395 / 1,218 / 0.924 / 0.126 / 0.0817）；Gamma 自报的 volume/liquidity 标了「来源自报，未核实」；5.5 的 502 复核为 200（count 5,031）与空 history 这个失败都照写。

## 出处

- https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2000-01-01&endtime=2026-10-01&minmagnitude=6.4&orderby=time-asc — 访问 2026-10-20 — 已读（1,513 行，`mag≥6.5` 1,216 条；基率与经验分布的计算源）
- https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2015-01-01&endtime=2026-01-01&minmagnitude=6.5 — 访问 2026-10-20 — 已读（`{"count":462,"maxAllowed":20000}`）
- https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2015-01-01&endtime=2026-01-01&minmagnitude=7.0 — 访问 2026-10-20 — 已读（`{"count":153,...}`）
- https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2015-01-01&endtime=2026-01-01&minmagnitude=5.5 — 访问 2026-10-20 — 已读（首次 502，复核返回 `{"count":5031,"maxAllowed":20000}`）
- https://earthquake.usgs.gov/fdsnws/event/1/query?format=text&starttime=2026-10-12&endtime=2026-10-19&minmagnitude=6.5 — 访问 2026-10-20 — 已读（3 条：`us6000u2mq` 6.9、`us6000u214` 6.8、`us6000u1z5` 6.7）
- https://earthquake.usgs.gov/earthquakes/search/ — 访问 2026-10-20 — 已读（HTML 标题 `Search Earthquake Catalog`；这是结算规则里指定的检索页，规则歧义 `type` 过滤未查到）
- https://gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25 — 访问 2026-10-20 — 已读（规则原文、七档 bid/ask/outcomePrices、`feeSchedule`、`clobRewards`、`negRisk=true`、volume 1,467.66）
- https://gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-12-october-18 — 访问 2026-10-20 — 已读（`closed=false` 但 USGS 已可数出 3 条；「3」档 0.95）
- https://gamma-api.polymarket.com/public-search?q=earthquake&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（同族市场清单与 slug：`megaquake-*`、`how-many-6pt5-*`、`how-many-5pt5-*`、`magnitude-6pt5-earthquake-in-la-before-2026`、`highest-earthquake-magnitude-in-2026`）
- https://gamma-api.polymarket.com/public-search?q=magnitude&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（`how-many-7pt0-or-above-earthquakes-in-2026` vol 1,477,696.9、`how-many-7pt0-or-above-earthquakes-by-june-30` vol 1,941,867.7）
- https://gamma-api.polymarket.com/events?tag_slug=earthquake&limit=500&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（69 个已关闭事件，合计成交 $5,869,975，按月份数频率）
- https://clob.polymarket.com/prices-history?market=2500092545816023700094480893694885475686508335314406123382468585117526026802&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（0 档从 `p=0.345`@2026-10-16T15:00Z 到 `p=0.475`@2026-10-17T21:00Z）
- https://clob.polymarket.com/prices-history?market=101519993085150541985963030400073395102135944737997204045298260898135285026732&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（返回 `{"history":[]}`：已关闭市场无历史价格，故无法回测）
- https://gamma-api.polymarket.com/markets?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25 — 访问 2026-10-20 — 已读（返回空数组；`markets?slug=` 不吃 event 级 slug，改用 `events?slug=`）
