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
data: USGS FDSN event API（免费免密钥，2000 年起完整目录）；Polymarket Gamma/CLOB（免费免密钥，CLOB 历史价格从市场创建后开始，本族市场创建约在窗口开始前 3–4 天）；已关闭市场的逐笔成交可从 data-api 读到（免费免密钥），可重建窗口前可成交价
test_2w: 按 event 计独立结果；68 个已关闭事件里 40 个严格组中只有 35 个有窗口前价格、34 个有成交（≥30），不是 40 个都有价；时间外样本 2026-07..10 的 45 个成交档合计 −1.99%（费 0.05）/−1.22%（费 0），点估计为负；失败标准是已成交 NO 份额的中位已实现毛利≤0 或基率模型 log loss 劣于市场（本次 log loss 触发 FAIL；作者建议降为待选区/退回）
status: 待核
confidence: 中
---

整理说明：本条所有基率数字都是我在 2026-10-20 从 USGS 目录当日拉取后自己算的（公式在下面写出）；盘口快照同一天。**2026-10-20 的历史回测**用 Gamma 已关闭事件 + data-api 逐笔成交 + USGS 基率，样本是 68 个事件 / 514 档；40 个严格独立组中只有 **35 个有窗口前价格、34 个有成交**（不是 40 个都有价），按写死准则判 **FAIL**（基率模型 log loss `1.4455` 劣于市场 `1.4152`）。**2026-10-21 的 H-quant-012 复用已合入 `main` 的 `bots/quant/notes/q012-hist/`（`REPORT.md`、`buckets.csv`、`events.csv`，md5 与 I01 完全相同），补做时间外样本和真 maker 成交代理**：2026-07..10 的 45 个成交档合计 **−1.99%**（费 0.05）/ **−1.22%**（费 0）；真 maker 代理（挂 NO mid/bid，只有 taker 卖 NO 穿过才成交）全样本 **−0.98%**、时间外 **−8.25%**。同时复验出处：USGS 1,513 行 / `mag≥6.5` 1,216 条 / 1,395 个 7 日 bin、count 462/153/5,031、Gamma 已关闭事件 69 个，均与原文一致；**当前 10/19 事件七档费率是 0，不是 0.05**（费率逐事件变，原文写死 0.05 已修正）。脚本与 stdout 在 `bots/quant/notes/scheduler/scratch/H-quant-012/`。**结论是负结果：不支持收录；作者建议核对时降为待选区或退回，不得按 7 门全过处理。**

## 一句话

在 Polymarket 每周的「本周全球发生几次 M6.5+（或 M5.5+）地震」分档阶梯上，用 USGS 历史目录算出的同长度窗口计数分布当公允值，在高估档**买 NO** 并持到结算（约 6 天）。历史上有可成交价的是**吃单代理**（log loss 与时间外收益均不支持 edge）；真 maker 版本没有盘口/排队数据，成交代理同样为负，因此本条只作为负结果，不作为可交易策略。

## 钱从哪里来

付钱给你的是**对「本周地震次数」的尾部档出价过高的散户**，加上平台给的流动性奖励。它持续存在的原因是：这类市场是每周重复上市的固定模板，参与者按新闻情绪而不是按泊松/经验基率出价——2026-10-20 快照里七档的卖价之和是 **1.218**（买齐七档必亏 21.8¢），而七档买价之和只有 **0.924**，整个阶梯系统性溢价；溢价集中在 ≥3 的尾部档（中价合计 0.126，经验基率只有 0.0817，1.54 倍）。这不是套利：没有一条腿能锁定，收益来自「报价被情绪单打中」。奖励部分来自 `clobRewards`（见成本节），量很小，只当补贴。**但 2026-10-21 复验的价格侧证据没有支持这个溢价能被稳定赚到：时间外样本为负，原“maker”报价还有 78.6% 会穿价吃单（见证据 6、7）。**

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
3. **执行价必须区分 maker / taker（本轮修正）**：原写 `q_i = 1 - p_i - m`（`m=0.01`）并称“只挂 maker”，但这是错的——当 `市场YES − p_i > 2¢` 时，`q_i` 会高于 NO 最优卖价（`1 − YES买价`），下单会立即穿价吃单。历史 103 个触发档里 **81 个（78.6%）** 属于这种穿价，只有 22 个落在买卖价之间。因此把规则拆成两版：
   - **可执行版（已回测，证据 5/6）**：taker 买 NO，成交价按 `1 − 市场YES + 1¢`（半价差），吃单费按当时 `feeSchedule`（历史回测保守地统一用 0.05；当前 10/19 事件实为 0）。
   - **真 maker 版（未验证，只有代理，证据 7）**：若要挂单，报价必须满足 `q_i ≤ 1 − 市场YES − tick`（低于 NO 卖价），并承担排队和逆向选择；历史盘口取不到，只能用 data-api 成交打印做“taker 卖 NO 穿过才成交”的代理，结果同样为负。
   - 原 `q_i = 1 - p_i - m` 只能当**估值上限**，不能当 maker 报价；`m=0.01` 也必须在下单前写死。
4. 不做做空裸卖 YES：只用「买 NO」表达看空档位，避免 negRisk 转换/铸造的操作风险。
5. 仓位：每档在险 NO 份额 ≤ 100 份；单个 event 全部档位合计在险金额 ≤ 300 USDT；同时在手的 event ≤ 4 个；总资金按 5,000 USDT 记，单场所 ≤ 2,500 USDT。
6. 出场：**不主动平仓**，持有到 UMA 结算（约 6 天 + 最多 48 小时争议期）。理由：平仓要付吃单费和价差，而票面 1.00 的收敛是免费的。
7. 风控熔断：同一周内已记录地震数 `k ≥ 3` 时，全部剩余 NO 挂单撤掉（尾部已经实现，模型不再有意义）；任一 event 浮亏超过在险金额 50% 时同周停止新增挂单。
8. 明确不做：不把 maker 的模型期望当作实测，也不把 `q=1-p-m` 的穿价单叫 maker；不做无保护的裸卖 YES（避免 negRisk 转换/铸造操作风险）；不做「预测下一次大震位置」类市场（无基率可依）。

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
- 吃单 EV（每份 = 基率 − 卖价，我算的）：`0: −0.035`、`1: −0.025`、`2: −0.042`、`3: −0.060`、`4: −0.038`、`5: −0.006`、`>5: −0.012`。**七档全负**；这是 2026-10-20 快照的吃单价，只能说明“按卖价追进去”不划算，不是策略收益证据。
- 若按 NO 卖价买 NO（`1 − 卖价`，**这实际是吃单，不是 maker**），每份 `= 1 − 基率 − (1 − 卖价) = 卖价 − 基率`：`0: +0.035`、`1: +0.025`、`2: +0.042`、`3: +0.060`、`4: +0.038`、`5: +0.006`、`>5: +0.012`。按占用资金折：3 档买 NO 于 `0.89`，收票面 `0.9498`，**6 天 +5.98¢ / 0.89 = +6.7%**。这是**按卖价成交的算术期望**，不是实测；真正的 maker 要挂在 NO 买价/价差内，成交概率和排队都未验证（见证据 7）。
- CLOB `prices-history`（`market=<桶0 token>&interval=max&fidelity=60`）显示该市场 `t=1792162843`（UTC 2026-10-16 15:00:43）`p=0.345`，`t=1792270842`（UTC 2026-10-17 21:00:42）`p=0.475`，中间在 0.42–0.475 间震荡；桶 3 同一段从 `p=0.225` 起步，后段在 `0.055–0.225` 区间震荡。说明档位价格确实在大幅漂移，maker 有对手单。
- **快照会漂移**：2026-10-20T12:58Z 复查同一事件，`volume` 已从 1,467.66 变到 5,163.42、`liquidity` 6,405.59，七档 `bestAsk` 合计 **1.111**、`bestBid` 合计 **0.914**（仍 >1）；但 ≥3 的四档中价合计只剩 **0.0875**（基率 0.0817，约 1.07 倍），尾部溢价比上表明显收窄。**上表只作快照示例，结论只对快照时刻成立；下面历史回测才是收益证据。**

### 3）一周内「已发生未结算」的现成例子

事件 `how-many-6pt5-or-above-earthquakes-worldwide-october-12-october-18`（`endDate=2026-10-19`）：Gamma 在 2026-10-20 仍返回 `closed=false`、七档全未结算；而 USGS `/query?starttime=2026-10-12&endtime=2026-10-19&minmagnitude=6.5` 当天返回**恰好 3 条**（`us6000u2mq` M6.9 2026-10-16T03:35:31.925、`us6000u214` M6.8 2026-10-13T12:23:07.248、`us6000u1z5` M6.7 2026-10-13T05:44:46.919）。该事件「3」档 `outcomePrices=["0.95","0.05"]`、volume 1930.25，其余档 0.0035–0.05。**这说明市场对已实现的计数反应是快的**（0.95 对 1.0 只余 5¢），所以「周内更新」这条 edge 不能想当然，只能靠逐个 event 记录来验证。

### 4）频率与容量（我数的）

`https://gamma-api.polymarket.com/events?tag_slug=earthquake&limit=500&closed=true&order=endDate&ascending=false` 返回 **69** 个已关闭事件，`endDate` 从 `2024-09-30` 到 `2026-10-19`，成交额合计 **$5,869,975**。按标题分类：`how-many` 周度阶梯 **37** 个、「Megaquake」**17** 个、「7.0 or above」单一阈值 **12** 个、其他 **3** 个。按 `endDate` 月份：2026-06 5 个、2026-07 9 个、2026-08 10 个、2026-09 9 个、2026-10 5 个（10 月未完）→ **近期约每月 9–10 个 event**；2 条周度序列（6.5+ 与 5.5+）各每周 1 个，理论约 8–9 个/月。2025 年多数月份只有 1–3 个，说明这个系列的密度是平台后来才加上去的，**不能把 2026 下半年的密度外推到明年**。

单 event 成交额差异极大（Gamma 快照）：`how-many-6pt5-...october-19-october-25` = 1,467.66；`october-12-october-18` = 15,189.73；`september-28-october-4` = 9,449.79；`march-23-march-29` = 259,657.7。**这就是容量上限的量级：几百到几万美元一个 event**，本条 300 USDT/event 的额度在最近的稀薄期已经是 event 成交额的约 20%，实际能挂到多少须实测。

来源自报的成交额/流动性字段均未用成交明细复现，**来源自报，未核实**。

### 5）历史可成交价格回测（q012-hist 复用，2026-10-20）

**方法（先写死再看结果）**：取 Gamma `events_status=closed` 的 `how-many-*earthquake*` 阶梯事件；决策时点 = 窗口开始；基率只用窗口开始前的 USGS 目录，取同长度、紧邻窗口的连续历史窗口做经验分布（每档 +0.5 伪计数）；可成交价 = 窗口开始前 24h 内最后一笔 data-api 成交换算成 YES，买 NO 按 `1 − 市场YES + 1¢`（半价差），吃单费 `0.05 × p_NO × (1−p_NO)`，持到结算；独立结果按 `(window_start, window_end)` 合并 5.5/6.5 两条序列。**这是吃单代理，不是本条提出的 maker 挂单**；maker 版本仍未验证。

**样本**：68 个已关闭阶梯事件、514 个档；M5.5+ 28、M6.5+ 38、M7.0+ 2，窗口跨 2025-12..2026-10。58 个事件至少有一档窗口前成交；29 个事件全部档位都有窗口前成交；严格独立结果 40 个，其中有价格 35 个（全部为周度事件）、有成交 34 个（≥30）。

**已成交 NO 的实际结果**（每档 1 份，103 个触发档）：

- 命中 80/103 = 77.7%；中位毛利 `+0.1200`/份、中位净利 `+0.1147`/份；但均值净利只有 `+0.0107`/份。
- 合计净利 `+1.1010` / 投入 `78.0863` = **+1.41%**（103 笔、每笔约 6 天的累计投入口径，**不能直接年化**；均值只有 `+0.0107`/份）。
- 23 个档是输的（NO 输时亏掉几乎全部权利金），最差 `−0.9141`/份；分序列 M5.5+ `+0.23%`、M6.5+ `+3.14%`，收益几乎全部来自 M6.5+。
- 窗口前成交距开始中位 2.36h、最大 22.30h，价格可能已过时。

**基率模型 vs 市场（log loss）**：29 个全档有价事件配对，模型 `1.445508` vs 市场 `1.415152`，模型更差 `0.0304` nats；15:14，双侧符号检验 `p=1.0000`。稳健性：只看 USGS 自算计数与结算档一致的 25 个事件，模型 `1.3107` vs 市场 `1.3560`（模型略好）；M6.5+ 38/38 一致，9 个不一致全部是 M5.5+（例：`september-14-september-20` 自算 4、结算 7）。所以 FAIL 是点估计，不是显著结论。

**判定（沿用写死准则）**：准则 1（中位毛利 ≤0）未触发；准则 2（模型 log loss 劣于市场）触发 → **VERDICT = FAIL**。敏感性（窗口开始后第一笔成交）方向一致，但成交档增至 183，不能改变主结论。**负结果：本回测不支持「基率模型对市场有稳定 edge」；证据 2 的 +6.7% 是按卖价买 NO（实际是吃单）的算术期望，不是实测。** 本轮直接复用已合入 `main` 的 `bots/quant/notes/q012-hist/`：`REPORT.md`、`buckets.csv`、`events.csv`、`q012_hist.py`、`run_output.txt`；`buckets.csv` md5 `f563d8e005f13217a4478f0f7638ecd1`、`events.csv` md5 `61ca26645b55de274abba1fb45e44c48`，与 I01 逐字节一致（见 `H-quant-012/analyze_merged_output.txt`）。

### 6）时间外样本与费率敏感性（H-quant-012，2026-10-21）

**方法（先写死）**：沿用证据 5 的同一样本、同信号（`市场YES − 模型YES > 1¢`）和吃单执行，只按 `window_start` 切时间：`< 2026-07-01` 为内样本，`>= 2026-07-01` 为时间外样本。未用时间外样本调任何参数；`m=1¢`、模型平滑 `0.5`、独立结果合并规则都保持证据 5 的原值。费用同时算两档：历史回测的 0.05，和当前 10/19 事件实取的 0。

**结果（`analyze_merged_output.txt` 原样）**：

- 全样本 103 个成交 NO：中位净利 `+0.1147`/份，均值 `+0.0107`/份（bootstrap 95% CI `[−0.0628, +0.0799]`），合计 `+1.1010 / 78.0863 = +1.41%`；把费改成 0 后合计 `+1.9137 / 78.0863 = +2.45%`。
- 内样本 `< 2026-07-01`：58 个成交档，中位净利 `+0.1292`，均值 `+0.0318`，合计 `+1.8469 / 40.6284 = +4.55%`（费 0：`+5.84%`）。
- **时间外 `>= 2026-07-01`：45 个成交档，中位净利 `+0.1051`，均值 `−0.0166`（95% CI `[−0.1247, +0.0795]`），合计 `−0.7459 / 37.4579 = −1.99%`；费 0 仍为 `−0.4579 / 37.4579 = −1.22%`。** 点估计为负，但 CI 跨 0，不能说是显著亏损；它是“没有证据支持正 edge”，不是“已证明稳定亏钱”。
- log loss 的时间外配对只有 4 个全档有价事件（模型 `1.7732` vs 市场 `1.7511`），样本太小，只能作方向参考；全样本 29 个配对仍是模型 `1.4455` vs 市场 `1.4152`，`diff(market−model) = −0.0304`，95% CI `[−0.2726, +0.1365]`。

**结论**：全样本的正收益几乎全部来自 2026 年上半年；把同一规则原样推到 2026-07 之后，45 个成交档在费 0.05 和费 0 两档下都是负的。**这说明证据 5 的 FAIL 不是“只差一点”，时间外也不支持继续往前走。**

### 7）真 maker 成交代理与穿价检查（H-quant-012，2026-10-21）

**为什么要做**：证据 5 是吃单代理；本条原提案写“只挂 maker”，但原文的 `q=1−p−0.01` 没有约束不能穿价。先用 CSV 做静态检查：103 个触发档中 **81 个（78.6%）** 的 `q` 大于等于 NO 最优卖价（`1−市场YES+1¢`），只有 22 个在买价与卖价之间，**0 个**低于 NO 最优买价。也就是说，原规则在绝大多数档上会立刻吃单，不是 maker。

**代理方法**：对同样的 103 个触发档，在窗口开始 `t0` 挂 NO 买单：① `q_mid = 1 − 市场YES`（用窗口前最后一笔成交当 mid）；② `q_bid = 1 − 市场YES − 1¢`。只有 `[t0, window_end]` 内出现 **taker 卖 NO**（`outcome=No, side=SELL` 或等价于卖 NO 的 `outcome=Yes, side=BUY`）且成交价 `≤ q` 才算成交；成交价按 `q`，maker 费 0，持到结算。`data-api` 只有成交打印，没有盘口/排队，所以这是**代理，不是实盘证明**；成交打印穿过限价是成交的必要条件，不是充分条件。

**结果（`maker_proxy_output.txt` 原样）**：

- 挂 NO mid：103 档中 81 档有穿过成交；中位净利 `+0.1300`/份，均值 `−0.0071`/份，合计 `−0.5728 / 58.5728 = −0.98%`。内样本 50 档 `+4.46%`；**时间外 31 档 `−2.0678 / 25.0678 = −8.25%`**。
- 挂 NO bid：75 档成交；中位 `+0.1325`，均值 `−0.0199`，合计 `−2.79%`；内样本 `+1.44%`，**时间外 30 档 `−8.02%`**。
- 成交时间中位 5.86h、最大 134h（相对窗口开始）；成交率 81/103（mid）、75/103（bid），说明“挂着不成交”不是主要问题，问题是成交后的尾部亏损。

**结论**：真 maker 代理也是全样本为负、时间外更负；再叠加排队位置、深度和逆向选择（这三项 `data-api` 都看不到），没有理由把 maker 版本判为“更好”。证据 7 只能证明“原 maker 公式是穿价的”，不能证明“真 maker 一定亏”，但足以让本条不能按 maker 收录。

## 数据

- USGS 目录（免费、免密钥、无需注册）：`https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=...&endtime=...&minmagnitude=6.4`；条数端点 `/count?format=geojson&...`；1970 年起基本完整，`minmagnitude=6.4` 起 USGS 全球台网基本无漏检（**这是我的判断，未在本次抓取中核实完备性**）。字段：`time, latitude, longitude, depth, mag, magType, net, id, place, status`。
- Polymarket Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?slug=<event-slug>`（规则原文、`outcomePrices`、`bestBid/bestAsk`、`feeSchedule`、`clobRewards`）；`/public-search?q=earthquake&limit_per_type=50&events_status=all`（找同族市场）；`/events?tag_slug=earthquake&closed=true&limit=500`（数频率）。
- Polymarket CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max&fidelity=60`。**只有市场创建之后的价格**（本族市场创建约在窗口开始前 3–4 天）。
- Polymarket data-api（免费免密钥）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`，**已关闭市场也能读逐笔成交**；字段 `side/price/size/timestamp/outcome`。本次对 68 个事件、514 个档逐档取窗口前最后一笔；逐档表在 `bots/quant/notes/q012-hist/buckets.csv`（514 行）与 `events.csv`（68 行），真 maker 代理另取 `[窗口开始, 窗口结束]` 的成交打印。
- 缺失且必须承认：CLOB `prices-history` 对已关闭市场仍返回 `{"history":[]}`；data-api 只有成交打印，**没有完整盘口/深度**，所以只能做「最后成交价 + 1¢」的吃单代理和「成交打印穿过限价」的 maker 代理，不能还原挂单排队和逆向选择。历史盘口本身仍然取不到。
- 本次复核（2026-10-21）：`H-quant-012/verify_sources.py` 重抓条目中所有**具体** URL（`data-api .../<conditionId>` 与 `page=N` 是模板，用具体 conditionId 和 page=1 代替），全部 HTTP 200；USGS CSV 重算 1,513 行 / `mag≥6.5` 1,216 条 / 1,395 个 7 日 bin / 分布 663-440-178-70-29-5-7-1-1-1；count 462/153/5,031；Gamma 已关闭事件仍是 69 个、成交合计 $5,869,974.95、分类 37/17/12/3；CLOB 开放 token 非空、已关闭 token 仍为 `{"history":[]}`。stdout 在 `H-quant-012/verify_sources_output.txt`。

## 两周内怎么检验

- **独立结果按 event 数**（不是按档、不按市场）：七档共享同一个 USGS 计数，算 1 个结果；6.5+ 与 5.5+ 同一周、同一结算源的合并为 1 个（严口径）。两周前向仍然只有约 4 个 event，但**不必只靠前向**：2026-10-20 已用 data-api 成交在 68 个事件里得到 40 个严格组，其中 **35 个有窗口前价格、34 个有成交**（按“有价”口径 35 ≥ 30；不能写 40 个都有价）。本次已按下面准则执行并判 **FAIL**（证据 5），2026-10-21 又补了时间外样本（证据 6：2026-07 起 45 个成交档 −1.99% / 费 0 −1.22%）。历史样本只覆盖 2025-12..2026-10，不能外推到更早。
- 每天记录（若要做前向复核）：USGS 当日 M6.5+ 事件列表（`eventid, time UTC, mag, magType, status`）、各档 `bestBid/bestAsk/outcomePrices`、我挂的 NO 报价与实际成交、CLOB 盘口。
- 校准检验（可复跑）：拿历史同长度窗口做留一法/滚动窗口，比较三种预测器的 log loss——(a) 常数经验分布、(b) `λ=0.80` 泊松、(c) 市场价。本次 (a) 对市场在 29 个全价事件上已经跑过：`1.4455` vs `1.4152`，模型更差；按时间切，内样本 25 个事件 `1.3931` vs `1.3614`，时间外只有 4 个全价事件 `1.7732` vs `1.7511`，时间外校准样本不足以下强结论。
- **失败标准（写死，事后不改）**：
  1. 已成交 NO 份额的**中位已实现毛利 ≤ 0**（毛利 = 票面赔付 − 成交价，不含未成交挂单）；
  2. 或基率模型 log loss 劣于市场（本次触发）；
  3. 或两周内成交份额 < 20 份（流动性不足，判「容量失败」而不是「策略失败」，但也进待选区）；
  4. 或基率模型对「3」档的 7 日校准误差 > 2¢（模型本身坏了）。
- **本轮已经触发第 2 条，结论是 FAIL**；不能把「中位毛利为正」当作通过，也不能把「挂单没成交所以没亏」当作正结果。时间外点估计为负（证据 6）和真 maker 代理为负（证据 7）都不改变这个 FAIL，只是进一步支持降级。

## 成本与容量

- **费用（逐事件读 `feeSchedule`，2026-10-21 复核）**：**不是全族固定 0.05**。`how-many-6pt5-...october-19-october-25` 的 7 档当前全部 `rate=0, rebateRate=0`；`october-12-october-18` 是 4 档 `0.05/0.25`、3 档 `0/0`；`september-28-october-4` 是 7 档 `0.05/0.25`。2026-10-20 快照里的 0.05 只对当时那批市场成立，不能写成“本族每个市场”。
  - 吃单费（按 GUIDE 公式 `费用 = 份数 × 费率 × p × (1 − p)`，只对 `rate=0.05` 的市场）：`p=0.11` → 每份 `0.05×0.11×0.89 = 0.0049`；`p=0.50` → `0.0125`；`p=0.075`（3 档 mid）→ `0.0035`。折成投入资金比例 `= 0.05×(1−p)`：`p=0.11` 时 **4.45%**。
  - maker 费 0；返佣按当时 `rebateRate`，当前 10/19 事件为 0（不是 2026-10-20 快照的 0.25）。
  - **每笔成本 = 费 + 半个买卖价差**。3 档价差 `0.11−0.04 = 0.07`，半价差 `3.5¢`——吃单要吃 3.5¢ 的价差，而模型 edge 只有 6.0¢，扣 0.49¢ 费后剩 2.0¢，但半价差已经把 edge 吃掉 58%，且这是按 mid 成交的乐观假设。做 maker 时半价差不是支出，代价变成「排队 + 逆向选择」，后者**未量化**；而且原 `q=1−p−0.01` 在 81/103 档会穿价，实际仍按吃单算。
- **单笔能放多少**：3 档 NO 挂 `0.89`、100 份 = 89 USDT 占用；七档全挂最多约 `(1−q_i)×份数`，按上表全部定价约 100 份合计约 500 USDT，超出单 event 300 USDT 上限，故实际按 300 分给 ≤3 档。占款天数 = 窗剩余 + 2 天争议 ≈ 6–8 天。
- **一个月多少次机会**：近期 9–10 个 event/月（我在 Gamma 上数的已关闭事件按 `endDate` 月份）；但每个 event 的成交量只有几百到几万美元，**机会数是够的，单次的钱不够**。5,000 USDT 里给这条线 1,000 USDT 上限就够，剩余资金不会被占用——这既是优点（不占资金）也是缺点（赚的钱对总资金微不足道）。
- **流动性奖励（补贴，不是主收益）**：2026-10-20 快照该 event 的 `clobRewards` 日率合计 **20 USDC/日**（0 档 11、1 档 6、2 档 2、3 档 1）；2026-10-21 复核已变成 **50 USDC/日**（0 档 30、1 档 18、2 档 2，其余无），`rewardsAmount=0`，`startDate=2026-10-20`。奖励逐日可改，不能当固定收入；`rebateRate` 同一天已从 0.25 变 0。按 Q-score 规则（见 dot-032），这笔钱**不足以**支撑策略，只覆盖部分风险。
- **历史回测的实际成本（吃单代理）**：103 个触发档按 0.05 费合计净利 `+1.1010` / 投入 `78.0863` = `+1.41%`（累计投入口径，不能直接年化），均值 `+0.0107`/份；把费改成 0 后 `+1.9137 / 78.0863 = +2.45%`。**时间外 45 档：费 0.05 `−1.99%`、费 0 `−1.22%`；真 maker 代理全样本 `−0.98%`、时间外 `−8.25%`。** 23 个档大亏；maker 版本能省掉吃单费和半价差，但成交概率、排队和逆向选择都未量化，不能把 maker 的模型期望当实测。
- **容量结论**：500–1,000 USDT 能放下（远低于 2,500 单场所上限），但 5,000 USDT **放不满**，因为 event 成交量本身就是几百到几万美元量级，且做 maker 只占其中被吃单的一部分。

## 风险

- **余震造成的过度离散（最大风险）**：一周内 5、6、7、8、12 次都出现过（12 次那周是我 bin 出的最大值）。一次 M8 主震会在同一周带出多个 M6.5+ 余震，`0/1/2` 档同时归零、`>5` 档直接命中。按泊松定价会严重低估这种聚集，按经验分布也只是把聚集「平均进去」，**不能预测哪一周会聚集**。做法 B 加 `k≥3` 撤单熔断只是止血，不是解决。
- **震级修订**：USGS 会把 `6.4` 修成 `6.6`，或 `6.6` 修成 `6.4`（`magType` 从 `mb` 改 `mww` 时常见）。规则允许「最后一天有合格地震 → 多开 24 小时按最新数据结算」，所以 5→6 档的边界单会翻。
- **数据源与时区**：结算按 USGS 检索结果条数 + ET 周界；USGS 目录对同一次地震只出 1 条（`id` 唯一），但**目录里另有 `type` 字段**（`earthquake`/`explosion`/`quarry` 等），规则只说「earthquakes」，本次未核 USGS 检索页是否默认过滤 `type=earthquake`——**未查到**，属规则歧义。
- **「按最低档结算」兜底**：若 48 小时内 USGS 没发布该期数据，结算判 0 档。买 NO 在 0 档上会因此全输。极低概率但后果是本金全损。
- **结算争议**：UMA 提案，`umaBond=500`、`umaReward=5`、`customLiveness=0`。地震这类客观数据出争议的概率低，但 2026-10-12–18 那个事件在 `endDate` 已过后一天仍是 `closed=false`，说明**结算有滞后（数小时到数天）**，资金被动占住的时间会比"6 天"长。
- **流动性/逆向选择**：单 event 成交量 1,467 USD（10/19–10/25 那个）意味着挂单可能长期不成交；一旦成交，往往是有人拿到了更快的地震信息（USGS 目录有分钟级延迟），你卖在了坏消息上。这个成本**未量化**，是本节最大的未知。
- **历史回测自身的方法风险**：用最后成交价 +1¢ 代替真实卖价，没有深度、滑点、排队；M5.5+ 有 9/28 个事件自算计数与结算档不一致（M6.5+ 38/38 一致），可能是目录修订或结算口径差；模型 log loss 已经劣于市场，说明「基率有 edge」这个前提在本样本上不成立。
- **时间外样本为负（新增）**：2026-07..10 的 45 个成交档合计 `−1.99%`（费 0.05）/ `−1.22%`（费 0），均值 `−0.0166`/份；95% bootstrap CI 跨 0，所以不能说是显著亏损，但也不能再说“全样本正收益”能代表未来。
- **原 maker 公式穿价（新增）**：`q=1−p−0.01` 在 81/103 个历史触发档会高于 NO 卖价，下单即吃单；真 maker 代理（挂 mid/bid、穿过才成交）全样本 `−0.98%`、时间外 `−8.25%`。这不是“maker 一定亏”的证明，但足以否定“maker 版本会更好”的原假设。
- **平台**：`restricted=true`（多个同族事件），negRisk 市场的转换/赎回操作有额外步骤和 gas；本条只用「买 NO」，不涉及转换。
- **奖励收缩**：`clobRewards.rewardsDailyRate` 逐市场配置，2026-10-21 已从 20 变成 50 USDC/日，`rewardsAmount` 仍为 0；可随时改，不能把任何一档日率当固定收入。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：基本满足，但“为什么持续”没有被时序证据支持** — 付钱方可以指认为对尾部档出价过高的情绪单；2026-10-20 横截面证据是七档卖价之和 1.218（买齐必亏 21.8¢）、≥3 的四档中价 0.126 对经验基率 0.0817（1.54 倍）。但 2026-07 之后 45 个成交档合计为负，说明“这个溢价每周都能赚”没有证据；机制本身能说清，持续性和经济性不合格（见门 5）。
2. **有免费数据能检验：满足（有保留）** — 基率侧完整（USGS 免费免密钥，1,216 条 / 1,395 个 7 日 bin，26 年）；价格侧可用 data-api 逐笔成交（已关闭市场可读）。**准确口径是 40 个严格组中 35 个有窗口前价格、34 个有成交，不是 40 个都有价**；按 35 个有价结果算 ≥30。保留：只有成交打印、没有完整盘口，历史盘口仍取不到，maker 排队无法验证。
3. **小资金能做：满足（容量很小）** — 300 USDT/event、≤4 event、总计 ≤1,000 USDT，远低于 2,500 单场所与 5,000 总资金；不加杠杆、不借钱；NO 买单最大亏损就是本金。容量写清了：几百到几万美元/event，5,000 USDT 放不满；这是经济容量小，不是资金门槛失败。
4. **不重复：基本满足（同族较多，需主审确认）** — `quant-018`（PortWatch 海峡）与 `quant-019`（CDC 麻疹）都已声明 `improves: quant-012`，本条是最早的 base；`composer-008`（2026-10-21，M5.5+ 周计数、Poisson、买 YES）晚于本条（2026-10-20），按 GUIDE §3.3 先到先得，它最多算同族变体/补充，不是本条重复。与 dot-032（纯流动性奖励）不同：本条是基率方向性交易，dot-032 是奖励份额。若主审把所有“官方计数阶梯”合并为一条，本条仍是 012 base，不会被 018/019/composer-008 反向覆盖。
5. **扣成本后粗算够用：不满足（负结果）** — 全样本吃单代理 103 档 `+1.41%`（费 0.05）/ `+2.45%`（费 0），但这是 2025-12..2026-10 的累计投入口径、不能年化；**时间外 2026-07..10 的 45 档为 `−1.99%` / `−1.22%`，真 maker 代理全样本 `−0.98%`、时间外 `−8.25%`**。均值仅 `+0.0107`/份（95% CI 跨 0），23 个档大亏；基率模型 log loss 也劣于市场（证据 5）。既没有 8% 年化的全周期证据，也没有 3% 组合腿的正证据，**门 5 判不满足**。
6. **两周内能检验：满足（可检验性），但检验结果 FAIL** — 历史 data-api 成交在 68 个事件中给出 40 个严格组、**35 个有窗前价格、34 个有成交**（≥30），两周内可复跑；按写死准则第 2 条触发，`VERDICT = FAIL`（证据 5）。时间外 45 档为负（证据 6）和 maker 代理为负（证据 7）不改变 FAIL，只支持降级。
7. **出处可查：满足** — 2026-10-21 重抓条目所有具体 URL 均 200（两个带 `<conditionId>`/`page=N` 的模板用真实示例代替）；基率从原始 CSV 重算（1,513 行 / 1,216 条 / 1,395 bin / 663-440-178-70-29-5-7-1-1-1 / P(≥3)=0.0817），count 462/153/5,031，Gamma 69 个已关闭事件、$5,869,974.95、37/17/12/3，CLOB 空 history 与 data-api 成交都复现；**费率 0.05 的旧写法已按 2026-10-21 实取改成逐事件读（10/19 为 0）**。脚本、stdout、逐档表都在 `q012-hist/` + `H-quant-012/`，可复跑。

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
- https://clob.polymarket.com/prices-history?market=101519993085150541985963030400073395102135944737997204045298260898135285026732&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（返回 `{"history":[]}`：已关闭市场无历史盘口；本次改用 data-api 成交做代理回测）
- https://gamma-api.polymarket.com/public-search?q=earthquake&limit_per_type=50&events_status=closed&page=N — 访问 2026-10-20 — 已读（分页取已关闭事件；本次筛出 68 个 `how-many` 阶梯）
- https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N — 访问 2026-10-20 — 已读（68 事件 / 514 档的逐笔成交；103 个触发 NO 档）
- https://gamma-api.polymarket.com/markets?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25 — 访问 2026-10-20 — 已读（返回空数组；`markets?slug=` 不吃 event 级 slug，改用 `events?slug=`）
- `bots/quant/notes/scheduler/scratch/I01/q012_hist.py`、`run_output.txt`、`verify.py`、`verify_output.txt`、`buckets.csv`（514 行）、`events.csv`（68 行） — 访问 2026-10-20（重跑） — 已读（本次历史回测脚本与 stdout；`verify_output.txt` 从 CSV 独立复算中位/均值/合计与 log loss）
- https://earthquake.usgs.gov/earthquakes/search/ — 访问 2026-10-21 — 已读（重抓 HTTP 200，标题仍为 `Search Earthquake Catalog`）
- https://gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25 — 访问 2026-10-21 — 已读（`closed=false`、`volume=6025.908212`、`liquidity=7533.111`、七档 `rate=0/rebate=0`、`clobRewards` 30/18/2、规则五个关键词逐字命中）
- https://gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-12-october-18 — 访问 2026-10-21 — 已读（仍 `closed=false`；`outcomePrices` 已显示「3」档 `0.935`，费率 4 档 0.05 / 3 档 0）
- https://gamma-api.polymarket.com/events?tag_slug=earthquake&limit=500&closed=true&order=endDate&ascending=false — 访问 2026-10-21 — 已读（仍 69 个事件、成交 $5,869,974.95、37/17/12/3、endDate 2024-09-30..2026-10-19）
- https://clob.polymarket.com/prices-history?market=2500092545816023700094480893694885475686508335314406123382468585117526026802&interval=max&fidelity=60 — 访问 2026-10-21 — 已读（`t=1792162843,p=0.345` 等与原文一致）
- https://clob.polymarket.com/prices-history?market=101519993085150541985963030400073395102135944737997204045298260898135285026732&interval=max&fidelity=60 — 访问 2026-10-21 — 已读（仍 `{"history":[]}`）
- https://data-api.polymarket.com/trades?market=0xe88699f06db8629bf5497f00343d0bc4c52497eae0476212b5bff381769d863a&limit=2&offset=0 — 访问 2026-10-21 — 已读（HTTP 200，字段含 `side/price/size/timestamp/outcome`）
- `bots/quant/notes/q012-hist/REPORT.md`、`q012_hist.py`、`run_output.txt`、`buckets.csv`（514 行）、`events.csv`（68 行） — 访问 2026-10-21 — 已读（已合入 `main`；md5 `f563d8e005f13217a4478f0f7638ecd1` / `61ca26645b55de274abba1fb45e44c48`，与 I01 逐字节一致）
- `bots/quant/notes/scheduler/scratch/H-quant-012/analyze_merged.py`、`analyze_merged_output.txt` — 访问 2026-10-21 — 已读（时间外切分、费 0 敏感性、bootstrap CI）
- `bots/quant/notes/scheduler/scratch/H-quant-012/verify_sources.py`、`verify_sources_output.txt` — 访问 2026-10-21 — 已读（全部 URL 200；USGS/Gamma/CLOB/data-api 数字复算）
- `bots/quant/notes/scheduler/scratch/H-quant-012/maker_proxy.py`、`maker_proxy_output.txt` — 访问 2026-10-21 — 已读（穿价 81/103；真 maker 代理全样本 −0.98%、时间外 −8.25%）
- `bots/composer/entries/composer-008-pm-usgs-weekly-55-quake-count.md` — 访问 2026-10-21 — 已读（同族 M5.5+ 周计数；2026-10-21 提交，晚于本条 2026-10-20）
