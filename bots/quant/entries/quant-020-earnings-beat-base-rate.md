---
id: quant-020
name_zh: 财报超预期市场：中价带的基准率缺口
name_en: Polymarket "beat quarterly earnings?" — base-rate gap in the coin-flip band
bot: quant
date: 2026-10-20
market: polymarket
pm_category: finance
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「<公司> 本季 GAAP/非GAAP EPS 是否高于 <创建时 SeekingAlpha 一致预期>」二元市场（每事件 1 个市场，negRisk=false）
venues: Polymarket
data: Gamma events/markets（规则原文、outcomePrices、feeSchedule）、CLOB prices-history（已关闭市场仍可取，原稿实取 247 个）、data-api 逐笔成交（2026-10-20 起用于可成交价回测）；全部免费免密钥。结算源 SeekingAlpha 付费墙，未取；SEC EDGAR 全文检索 KEYLESS 可用，可作独立复核口径
test_2w: 独立结果按 event=公司-季度计（一事件一市场）。历史口径可在两周内检验：跨 16 个月有 101 个带内、HOLDOUT 47 个（其中 32 个落在选带窗口）、严格选带外 68 个，均 ≥30。2026-10-21 Gamma 有 105 个 open event，但历史带内只占 7.65%，任一滚动 14 天窗口带内最多 24 个（通常 <10），纯前向两周凑不到 30（只能作补充）。失败标准：0.40–0.55 带内按事件分组净 PnL 中位 ≤0，或带内 YES 率 ≤ 事前价均值
status: 草稿
confidence: 中
---

整理说明：基率与校准是我在 2026-10-20 用 Gamma + CLOB 公开接口现取现算；原稿脚本 `fetch_earn.py` / `scan_all.py` / `sample_price.py` **未随合并笔记入库**（仓库内查不到），可复核的等价脚本片段、命令与输出见 `bots/quant/notes/batch2-verification/quant-020.md` 记录 7，公式写在下方。原稿只有「事前 24h 价 vs 实际结算」的横截面校准；2026-10-20 已补做 data-api 逐笔成交的时间切分样本外回测（`bots/quant/notes/q020-oos/`），2026-10-21 又用**实际 ask 侧成交打印**（BUY YES，或 SELL NO 按 1−p 换算）替代「最后成交价 +1¢」假设重跑，并补了剔除选带窗口的严格前置样本外（`bots/quant/notes/scheduler/scratch/H-quant-020/`）。**仍未做历史盘口/L2 回放**（GUIDE 第 8 节：历史 L2 无公开来源），但不再是「没有逐笔成交」。

## 本轮加固结论（H-quant-020，2026-10-21）

**建议核对时降级到待选区（若严格按门 5 也可直接退回；status 由整合者决定，本轮只保留 `草稿`）。** 理由：**门槛 5 不满足**（门槛 6 按 GUIDE 的历史口径满足，见下）；实际 ask 侧成交打印的 POOLED 均值 **−0.0140/份（每美元 −2.71%）**、95% CI **[−0.1292, +0.0817]** 跨 0，DISCOVERY 为负；即使把费率降到 0，POOLED 均值也只有 **−0.0020/份（−0.38%/美元）**。**更关键的是原「HOLDOUT」并不干净**：选带用的 247 个样本取自 2026-10-20 最新 250 个已关闭事件，而 60/40 的 HOLDOUT 有 **29/43** 落在同一个选带窗口内（切点 `2026-07-30T13:00Z`）。把这 250 个事件全部剔除后，**严格前置样本外 n=68 的均值是 −0.0634/份（每美元 −12.14%）、中位 −0.4120**，95% CI **[−0.1638, +0.0366]**；正收益集中在选带窗口内的 29 个事件（均值 +0.1017/份、每美元 +20.08%）。因此「HOLDOUT PASS」是选带样本内的结果，不是干净的样本外通过。此外，观察到的 ask 成交打印中位只有 **4.8 USDT**，97 个里仅 1 个 ≥200 USDT，200 USDT/event 的可成交性未证实。

## 一句话

在 Polymarket 的「某公司本季 EPS 是否高于创建时的一致预期」二元市场里，只在事前 24h 价格落在 **0.40–0.55** 的带上**吃单买 YES**，持到结算（通常 1 天内出结果）。原稿的依据是 2026-10-20 的 35 个中间带事件：YES 率 **65.71%** 对事前均价 **0.4894**；但把样本扩到 101 个带内事件（其中 97 个有 ask 侧打印）、改用实际成交打印后，合并均值接近 0 且为负；再剔除选带所用的最新 250 个事件，**严格前置样本外 n=68 的均值 −0.0634/份（每美元 −12.14%）**（见「可成交价」与「本轮加固结论」），所以 **65.71% 不能当作已证实的边**。

## 钱从哪里来

付钱给你的是**在 50¢ 附近给「能否 beat」报低价的一方**。机制上的理由是：这类市场的行权价不是「会不会超预期」的模糊叙事，而是 `as of market creation` 那一刻 SeekingAlpha 卖方一致预期的**一个具体数字**（见规则原文），而 GAAP 与非 GAAP 两个口径的历史超预期率差得很远——我数出来 GAAP 是 **64.06%**、非 GAAP 是 **80.95%**（见证据）。当两边的信息被混在一个「财报好不好」的直觉里，接近 50¢ 的报价就没有把口径差异和基准率算进去。

这是**横截面单点证据 + 事后分桶**，不是持续性的时序证明；§证据 里也如实写了：整体上市场校准比基准率更好（Brier 0.1310 vs 0.1818），缺口只集中在中间那一档。2026-10-20/21 的可成交价回测没有把这个机制解释变成稳定正收益：DISCOVERY 为负、POOLED 均值约 0 或为负；剔除选带样本后的严格样本外均值也为负。

## 规则

以下逐条来自 Gamma 事件 `hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05` 的 `description` 原文（2026-10-20 已读，普通财报模板同构）：

- 行权价来源：`The Street consensus estimate for ... GAAP EPS for the relevant quarter is $0.05 as of market creation`；另注 `The strike prices used in these markets are derived from SeekingAlpha estimates, and reflect the consensus of sell-side analyst estimates for GAAP EPS.` → **是创建时点（不是结算时点）的一致预期，来源 SeekingAlpha**，会随市场创建日固定，不随分析师上/下调而更新。
- 结算条件：`resolve to "Yes" if ... reports GAAP EPS greater than $0.05`；`Otherwise ... "No."` → **严格大于**，等于算 No。
- 结算源：`the GAAP EPS listed in the company's official earnings documents`；公司未发布 GAAP EPS 时，`resolve according to the GAAP EPS figure reported by SeekingAlpha`；`If no such figure is published within 96h of market close (4:00:00pm ET) on the day earnings are announced, the market will resolve to "No"`。
- 未按期发布：`If the company does not release earnings within 45 calendar days of the estimated earnings date, this market will resolve to "No."`
- 修订口径：`Subsequent restatements, corrections, or revisions ... will not qualify`，只有 `obvious and immediate mistakes (e.g., fat finger errors, as with Lyft's (LYFT) earnings release in February 2024)` 例外。
- 数值口径：`All figures will be rounded to the nearest cent using standard rounding`；`IFRS EPS will be treated as GAAP EPS`；`GAAP EPS refers to diluted GAAP EPS, unless this is not published, in which case it refers to basic GAAP EPS`；跨国公司的美股 ADR/ADS 为准。
- 市场结构：财报超预期事件每事件 1 个市场（`q020-oos` 过滤后 1384 个 deduped 事件全部 1 个市场；Gamma tag 原始快照 2026-10-20 为 1378 个事件/1382 个市场，2026-10-21 为 1393/1397，差额来自 tag 下的非财报事件），`negRisk=false`，`restricted=true`，`orderMinSize=5`（份），`orderPriceMinTickSize` 为 `0.001`（hims 实例）或 `0.01`。
- 同族还有 `-nongaap-` 版本（行权价用非 GAAP/adjusted 一致预期），slug 只差这一段，**必须逐市场读 description，不能按标题猜口径**。

**交易规则（提案，未验证）**：

1. 只做 `0.40 ≤ p_24h ≤ 0.55` 的带（原稿 `p_24h` = 该市场在 `endDate − 24h` 之前 CLOB `prices-history` 的最后一个 `p`；可成交价复核改用 data-api 在 `[endDate−72h, endDate−24h]` 的最后一笔 YES 成交/ask 打印，见下）；带外一律不做。
2. 吃单买 YES（不在这个带里挂单，因为这一带是唯一观察到缺口的区间）。
3. 每个 event 上限 200 USDT；但 2026-10-21 观察到的 ask 侧成交打印中位仅 4.8 USDT，**先按 20–50 USDT/event 做**，除非实时盘口显示足够深度；同时在手 ≤ 15 个 event，总占用 ≤ 2,000 USDT（低于单场所 2,500）。
4. 不加仓、不对冲、不平仓：持有到 UMA 结算，`endDate` 后一般数小时至 2 天。财报在收盘后发布、`endDate` 设 22:00Z，实际占款约 1–3 天。
5. 熔断：同一周内已实现亏损事件数 ≥ 4 时当周停止新开仓。
6. 明确不做：GAAP/非 GAAP 混用同一个基准率（口径分桶，见证据）；不做 `0.8+` 的高价带（那里市场比基准率更准）。
7. 费用按保守上界 0.05 算；2026-10-21 复核发现费率不是一律 0.05：105 个 open 里 103 个 `rate=0`、2 个 `rate=0.05`；1393 个已关闭事件共 1397 个市场中，664 个 `rate=0.05`、7 个 0.04、5 个 0、721 个 `feeSchedule=null`。回测用 0.05 是保守值，不声称「每个市场都收 0.05」。

## 证据

### 1）历史超预期率（我自己数的，1378 个已关闭事件）

样本：`https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=…&closed=true&order=endDate&ascending=false` 全量翻页，2026-10-20 快照得 **1378** 个已关闭事件、**1382** 个市场，`endDate` 从 **2024-01-19** 到 **2026-10-19**。结算值取 Gamma `outcomePrices`（`["1","0"]` 记 YES、`["0","1"]` 记 NO，全部 1382 个都能这样判，无未结算残留）。

- 合计 **YES 1028 / NO 354 → 74.38%**。
- 按 slug 口径分：`-nongaap-` **684/845 = 80.95%**；`-gaap-` **344/537 = 64.06%**。
- 每月事件数（同一份数据按 `endDate` 月份数）：2025-10 **156**、2025-11 **172**、2025-12 **53**、2026-01 **54**、2026-02 **169**、2026-03 **73**、2026-04 **120**、2026-05 **155**、2026-06 **44**、2026-07 **143**、2026-08 **154**、2026-09 **44**、2026-10 **28**（只到 10-19）。→ 财报季（1、2、4、5、7、8、10、11 月）每月 120–172 个，淡季（6、9 月）44 个。**这就是「每月多少次机会」的实测值**。
- 单事件成交额（Gamma `volume`，来源自报，未核实）：合计 **$21,633,950**、中位 **$6,232**、p90 **$29,916**。
- **2026-10-21 复核快照**（同端点、同口径，脚本 `verify_sources.py` / `verify_sources.out`）：**1393** 个已关闭事件、**1397** 个市场，`endDate` 2024-01-19 至 2026-10-20；YES **1038 / NO 359 = 74.30%**；`-nongaap-` **691/856 = 80.72%**、`-gaap-` **347/541 = 64.14%**。10 月事件数从 10-19 的 28 增至 10-20 的 43。与 1378 快照的差异是 2026-10-20/21 新结算事件陆续入库，**不是口径修正**；按口径基率三次快照差异 <0.3pp（q020-oos 的 1384 个 deduped 事件为 74.64% / 80.94% / 64.49%）。

### 2）事前价 vs 实际结算（247 个事件，我自己取的）

取 `endDate` 最新的 250 个已关闭事件，对每个市场用 `https://clob.polymarket.com/prices-history?market=<clobTokenId[0]>&startTs=<endDate−72h>&endTs=<endDate>&fidelity=60`，抓到的点里取 `t ≤ endDate−24h` 的最后一个 `p` 作为 **p_24h**；3 个市场无价格点，得 **247** 个样本。

| 组 | n | 实际 YES 率 | mean(p_24h) | 差 | Brier(市场) | Brier(常数基准率) |
|---|---:|---:|---:|---:|---:|---:|
| 全部 | 247 | 0.7611 | 0.7230 | **+0.0381** | 0.1310 | 0.1818 |
| GAAP | 90 | 0.6333 | 0.6370 | −0.0036 | 0.1728 | 0.2322 |
| 非 GAAP | 157 | 0.8344 | 0.7723 | **+0.0621** | 0.1070 | 0.1382 |

分桶（同一 247 个样本）：

| p_24h 区间 | n | mean(p_24h) | 实际 YES 率 | 差 |
|---|---:|---:|---:|---:|
| [0.00,0.20) | 7 | 0.0769 | 0.0000 | −0.0769 |
| [0.20,0.40) | 22 | 0.3193 | 0.3182 | −0.0011 |
| **[0.40,0.60)** | **35** | **0.4894** | **0.6571** | **+0.1677** |
| [0.60,0.80) | 59 | 0.7124 | 0.7288 | +0.0164 |
| [0.80,1.01] | 124 | 0.9021 | 0.9274 | +0.0253 |

中间带的内部拆分（同样本）：GAAP n=18，mean 0.4747 / YES 0.5556（+0.0809）；非 GAAP n=17，mean 0.5050 / YES 0.7647（+0.2597）。

该 247 样本已由 `bots/quant/notes/batch2-verification/quant-020.md` 独立重跑复核（记录 7：重跑 246/247，分桶到 0.6 的数字一致），本轮未重复抓取 250 个 CLOB 端点。

**必须一起读的三件事**：(a) 整体缺口只有 +3.81pp，小于一次吃单的费+半价差，所以「整体买 YES」不是策略；(b) 市场整体 Brier **优于**常数基准率（0.1310 < 0.1818），即市场是有信息含量的，不是系统性低估；(c) 唯一的大缺口在 [0.40,0.60) 这 35 个事件上，**区间边界是我看完数据才划的**，有事后选择偏差，n=35 也小；剔除选带窗口后严格样本外均值为负（见「严格前置样本外」）。这三条合起来说明：这是**待验证的候选**，不是已证实的边。

### 3）没有做的事

原稿没有逐笔成交回放、没有资金曲线；2026-10-20 的 `q020-oos` 已补 data-api 逐笔成交的时间切分回测，2026-10-21 的 H-quant-020 又补了实际 ask 侧成交打印复核和剔除选带窗口的严格前置样本外。**仍未做**：历史盘口/L2 深度（GUIDE 第 8 节：历史 L2 无公开来源）、资金曲线、实际 UMA 结算到账时间分布；也没有取 SeekingAlpha 的原始预期值或公布值（付费墙），所以**无法**独立复核「strike 是否等于当时一致预期」，只能照抄规则原文。

## 可成交价时间切分样本外检验

2026-10-20 补做（PR #10，完整脚本、逐事件表与 stdout 见 `bots/quant/notes/q020-oos/REPORT.md`、`run_output.txt`）：按 `endDate` 排序，最早 60% 为 DISCOVERY、最新 40% 为 HOLDOUT；规则冻结为原条目的 `0.40 ≤ p_24h ≤ 0.55` 吃单买 YES，价格改用 data-api 同一时点可成交近似（`p_24h + 0.01` 半价差，费率 0.05）。

- HOLDOUT：**n=47，按冻结判据判 PASS** — 净 PnL/份中位 **+0.4376 > 0**，YES 率 **0.5745 > 平均入场价 0.4881**；但其中 **32 个**落在选带用的最新 250 个事件内（见「严格前置样本外」）。
- DISCOVERY：**n=54，中位 −0.4313、均值 −0.0494**，为负；POOLED：**n=101，中位 +0.4277、均值仅 +0.0081**（每美元 +1.66%）。
- 周聚类 bootstrap 的均值净收益 95% CI：HOLDOUT **[-0.1074, +0.1841]**、POOLED **[-0.1005, +0.0972]**，两者都跨 0；且该 HOLDOUT 与选带样本重叠，不能当作独立验证。

因此这只是“按冻结判据 PASS、统计上不显著”：发现段为负、合并均值约等于 0，且二元合约上的**中位数判据本身证据力很弱**（单注多数亏掉本金时中位数容易机械为正/负）。前向复核已预注册在 `bots/quant/notes/q020-forward/`：只评估 `endDate` 在 `[2026-10-21T00:00Z, 2026-10-26T00:00Z)` 的事件，未全部结算前只打印计数与 PENDING，不出判定。

### 实际 ask 侧成交打印复核（H-quant-020，2026-10-21）

脚本 `tradable_fills.py`、stdout `tradable_fills.out`、逐事件表 `tradable_fills.csv`，全部在 `bots/quant/notes/scheduler/scratch/H-quant-020/`。口径：取 `q020-oos/events.csv` 已冻结的 **101** 个带内事件，不重新拟合区间；入场价改为 `[endDate−72h, endDate−24h]` 内**最后一笔 ask 侧成交打印**的 YES 等价价（`BUY Yes` 取 `p`，`SELL No` 取 `1−p`），费率 0.05，时间切分沿用 60/40。若窗口内没有 ask 侧打印则标为未定价。这样得到的是实际发生过的吃单方向成交价，不再是「最后成交价 +1¢」的假设。

| 组 | n | YES 率 | 平均入场价 | 中位净 PnL/份 | 均值净 PnL/份 | 每 $ 投入 | 周聚类 bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|
| DISCOVERY | 54 | 0.4444 | 0.5205 | −0.4221 | −0.0881 | −16.92% | [−0.2077, +0.0326] |
| HOLDOUT | 43 | 0.6047 | 0.5136 | **+0.4476** | +0.0790 | +15.38% | [−0.1007, +0.1953] |
| POOLED | 97 | 0.5155 | 0.5175 | +0.2406 | **−0.0140** | **−2.71%** | [−0.1292, +0.0817] |

- 用同一批 101 个事件、原来的「最后 YES 成交价 +1¢」口径重跑，得到 DISCOVERY n=54 / HOLDOUT n=47 / POOLED n=101，HOLDOUT 中位 +0.4376、POOLED 均值 +0.0081、CI [−0.1005, +0.0972]，与 `bots/quant/notes/q020-oos/REPORT.md`、`run_output.txt` 完全一致（复现校验）。
- **费率敏感性**（同一实际成交打印样本）：费率 0.05 → POOLED 均值 −0.0140/份（−2.71%/美元）；0.04 → −0.0116（−2.24%）；**0.00 → −0.0020（−0.38%）**。即使按 2026-10-21 多数 open 市场的 `rate=0`，合并均值仍约等于 0 且为负，没有可用的边。
- **价差实测**：同一窗口内同时有 ask 侧和 bid 侧打印的 93 个事件，ask−bid 中位 **4.0¢**、均值 **7.2¢**，远宽于原稿假设的 1¢ 半价差；实际 ask 打印与「最后成交价 +1¢」的中位差为 −0.26¢（53/97 低于假设），说明原假设方向不稳，不能把 +1¢ 当成保守下界。
- **容量**：ask 打印的 `size × price` 中位只有 **4.8 USDT**，97 个里只有 **1 个 ≥200 USDT**。这不一定等于盘口深度（单笔可能是部分成交），但足以说明 200 USDT/event 没有证据支持；应先按 20–50 USDT/event 做，并在实时盘口记录可成交量。
- 结论：HOLDOUT 按原冻结判据 PASS，但 29/43 落在选带窗口；剔除后严格样本外为负（下一节）。POOLED 均值负、CI 跨 0、费率归零也不转正；这是**负证据**，不能据此认定「扣成本后够用」。
- 限制：ask 打印可能早于 `p24` 决策时点数小时，且无法知道该价位的剩余深度；它是「历史可成交价」的近似，不是逐笔队列模拟。data-api 返回体没有解释 `side` 是吃单方还是挂单方，本文按常见解释（`side` = 吃单方）把 `BUY Yes`/`SELL No` 当 ask 侧；若实际相反，ask/bid 会对调，需用实时盘口复核。

### 严格前置样本外：剔除选带窗口（H-quant-020，2026-10-21）

原稿的 247 个校准样本不是随机抽样，而是 2026-10-20 **最新 250 个已关闭事件**（`bots/quant/notes/batch2-verification/quant-020.md` 记录 7 保存的 `sample_price.py` 片段：`ev.sort(...reverse=True)` 后取 `ev[:250]`）。因此 `q020-oos` 的 60/40 HOLDOUT 虽然按时间靠后，却仍与选带样本重叠：有 ask 打印的 43 个 HOLDOUT 事件里 **29 个** `endDate ≥ 2026-07-30T13:00Z`，正落在最新 250 个事件内；旧价口径的 47 个 HOLDOUT 里也有 **32 个**在该窗口。脚本 `strict_oos.py`、stdout `strict_oos.out`（同目录）用同一批已冻结的 `tradable_fills.csv`，以 `q020-oos/events.csv` 的 1384 个 deduped 事件重算切点（原始 1378 快照与它在边界可能差一两个事件，故另做切点敏感性）：

- **STRICT_OOS** = `endDate < 2026-07-30T13:00Z`（即不在选带用的最新 250 个事件里），n=68；**SELECTION** = `endDate ≥ 2026-07-30T13:00Z`，n=29。
- 入场价仍是实际 ask 侧成交打印，费率 0.05，周聚类 bootstrap 同前（seed 20261020）。
- 注意：`q020-oos` 的 101 个带内事件是用 data-api `p24` 重新判带，不是原稿的 CLOB `p_24h`；同一批事件按旧 CLOB 价只有 **65/101** 仍在带内（`q020-oos/run_output.txt` [2c]）。所以下面另给 `in_band_old` 的稳健性结果。

| 组 | n | YES 率 | 平均入场价 | 中位净 PnL/份 | 均值净 PnL/份 | 每 $ 投入 | 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|
| **STRICT_OOS（选带样本外）** | 68 | 0.4706 | 0.5221 | **−0.4120** | **−0.0634** | **−12.14%** | [−0.1638, +0.0366] |
| SELECTION（选带窗口内） | 29 | 0.6207 | 0.5067 | +0.4476 | +0.1017 | +20.08% | [−0.1822, +0.2824] |

- **费率归零也不转正**：STRICT_OOS 在费率 0.04 时均值 −0.0610（−11.68%/美元），费率 0.00 时 −0.0515（−9.86%/美元），CI 仍跨 0。
- **换回原稿 CLOB 价选带口径也不转正**：若用 `in_band_old`（原始 CLOB `p_24h` 在带内）定义样本，STRICT_OOS n=42、均值 −0.0503/份（−9.78%/美元）、中位 −0.4322；SELECTION n=20、均值 +0.1376/份（+27.52%/美元）。
- **+1¢ 假设同样为负**：即使不用实际 ask、退回 `q020-oos` 的「最后 YES 成交价 +1¢」，STRICT_OOS n=68 均值仍为 −0.0237/份（−4.92%/美元）。
- **切点敏感性**：把切点提前到 2026-07-01（n=62）或 2026-06-01（n=60），均值分别为 −0.0741 / −0.0715（−13.99% / −13.59%/美元）；推迟到 2026-08-01（n=69）仍为 −0.0552（−10.59%/美元）。结论不依赖某一天。
- 解读：最新 250 个事件既是选带样本、又是正收益来源；把它们剔除后，早期 68 个带内事件的均值和中位都为负。这不是「样本外通过」，而是**选带偏差 + 小样本**。因此原 `HOLDOUT` 的正结果不能作为独立验证，条目应降级。

## 数据

- Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=<0..1400>&closed=true&order=endDate&ascending=false`（2026-10-20 快照 1378 个已关闭事件，2026-10-21 复核 1393 个；规则原文 + `outcomePrices` + `feeSchedule`）；`closed=false&order=endDate&ascending=true`（2026-10-21 为 105 个 open）。
- CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=&endTs=&fidelity=60`。**本条实测：已关闭的财报市场仍然能取到价格**（247/250 成功），这与 quant-012 里已关闭地震市场返回空 `history` 的情况不同——所以本族可以做历史校准，这是它与地震条目的关键数据差异。
- SEC EDGAR 全文检索（免费免密钥，可作独立口径）：`https://efts.sec.gov/LATEST/search-index?q=form%3A8-K%20items%3A2.02&forms=8-K` 返回 JSON（`hits.total.value`）；8-K Item 2.02 的 EX-99.1 是公司自己的财报新闻稿，可用来直接数「公布 EPS vs 当时一致预期」。本轮只验证端点可达、**未**逐份抽取数字。
- data-api（免费免密钥）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=<0..10000>`，逐笔成交含 `side`（BUY/SELL）、`outcome`（Yes/No）、`price`、`size`、`timestamp`。2026-10-20/21 已用它对 101 个带内事件取 `[endDate−72h, endDate−24h]` 的成交；本轮 0 个市场因 offset 上限被截断。只保留最近约 2 万笔/市场，更早/更活跃市场可能缺成交。
- 缺失：SeekingAlpha 原始预期/公布值（付费墙，不抓）；历史盘口/L2 深度（无公开来源）；实际 UMA 结算到账时间。

## 两周内怎么检验

- **独立结果按事件（公司-季度）计，不按市场计**：一事件一市场，天然不重复。同一公司同一天若有 GAAP 与非 GAAP 两个事件，二者共用同一份财报、同一份新闻稿 → **合并为 1 个结果**（严口径），这会削掉一部分样本。
- 样本量（本轮更正）：2026-10-21 Gamma 上 open 事件 **105 个**（`endDate` 2026-10-21 至 2026-11-05），但历史带内只占 **7.65%**（101/1321 个有价事件）；`q020-oos` 实测任一滚动 14 天窗口带内最多 **24 个**，通常 <10。因此**纯前向两周凑不到 30 个独立结果**，原稿「两周 60–90 个」把全部财报事件都算进去了，是错的。101 个带内事件跨 2025-06-05 至 2026-10-20（约 16.5 个月），不是两周样本。→ 按 GUIDE §2 第 6 条，**用历史数据在两周内可完成检验**（101 个带内、严格选带外 68 个，均 ≥30），门 6 记满足；但纯前向只能作补充观察，不能承诺两周凑够 30。
- 每天记录：`p_24h`、实际 ask/bid 成交打印、`size`、`feeSchedule`、结算值、结算时间戳；不要只记中间价 `p`。
- **失败标准（写死，事后不改）**：0.40–0.55 带内、按事件分组的**净 PnL 中位 ≤ 0**（每笔扣吃单费与半个实际价差）；或带内实际 YES 率 **≤ mean(p_24h)**（缺口消失）。样本不足 20 个事件则判「证据不足」进待选区，不算通过也不算失败。
- 不允许的自我安慰：不能用「中间带之外也赚了」改口扩大区间；不能把 GAAP 与非 GAAP 合并成一个样本再声称缺口。

## 成本与容量

- **费用（2026-10-21 复核后更正）**：原稿说「每个财报市场都是 `rate=0.05`」，这不准确。2026-10-21 全量复核：1393 个已关闭事件共 1397 个市场中，**664 个 `rate=0.05`、7 个 `rate=0.04`、5 个 `rate=0`、721 个 `feeSchedule=null`**；105 个 open 事件中 **103 个 `rate=0`、2 个 `rate=0.05`**（`xom-…-10-30`、`imax-…-11-05`）。回测仍按 **0.05 保守上界**算；即使按 0 费率，实际成交打印的 POOLED 均值也只有 −0.0020/份（−0.38%/美元），没有转正。
- 吃单费（GUIDE 公式 `费用 = 份数 × 费率 × p × (1 − p)`）：`p=0.4894` 时每份 `0.05×0.4894×0.5106 = 0.01250`；折成投入资金 `= 0.05×(1−p) = 2.55%`。`p=0.55` 时每份 `0.01238`（2.25%）；`p=0.40` 时 `0.01200`（3.00%）。
- 价差（实测，不是假设）：在 93 个同时有 ask 侧和 bid 侧成交打印的带内事件上，ask−bid 中位 **4.0¢**、均值 **7.2¢**；半价差中位约 **2.0¢**，不是原稿假设的 1¢。历史 L2 仍取不到，无法知道整条盘口深度。
- 原稿的「带内毛期望 +0.1452/份（+29.1%）」是**模型算术，已被实际成交打印回测否定**，不再作为证据：同样本 POOLED 均值 **−0.0140/份（−2.71%/美元）**，HOLDOUT 为正但 DISCOVERY 为负，CI 跨 0；剔除选带样本后严格样本外均值也为负。
- 容量：Gamma `volume` 中位 $6,232、p90 $29,916（来源自报，未核实）；但实际 ask 成交打印的 `size × price` 中位只有 **4.8 USDT**，97 个里仅 **1 个 ≥200 USDT**。200 USDT/event 没有成交证据支持，先按 **20–50 USDT/event**。机会密度也应按带内算：101 个带内事件跨约 16.5 个月 ≈ **每月 6 次**，不是原稿的「每月 28 次」；财报季峰值 14 天最多 24 个，淡季更少。**频率和单次容量都偏小，5,000 USDT 放不满。**
- 资金被占住：`endDate` 后到 UMA 结算，本轮样本末价格点距 `endDate` 最近的记录显示价格已在结算方向（如 `tfc-…` 从 0.52 跌到 0.0045、`mtb-…` 从 0.745 升到 0.9995），说明结果通常在 `endDate` 附近已定，但**实际结算到账时间未统计**。

## 风险

- **口径风险（最大）**：GAAP 与非 GAAP 两个基准率差 16.9pp（80.95% vs 64.06%）。若把非 GAAP 的基准率套到 GAAP 市场上，中间带的「+16.8pp」会消失甚至反向（GAAP 中间带只有 +8.1pp，n=18）。
- **事后分桶 / 选带偏差**：区间 0.40–0.55/0.60 是我看完 247 个样本才定的，而这 247 个又正是最新 250 个已关闭事件；`q020-oos` 的 HOLDOUT 有 29/43（有 ask 打印口径）落在同一窗口。剔除后 STRICT_OOS n=68 均值 **−0.0634/份（−12.14%/美元）**，正是这个风险的实现。真正的样本外表现没有转正。
- **实际成交打印很小**：带内事件 ask 侧打印的 `size × price` 中位 4.8 USDT，97 个里 1 个 ≥200 USDT；200 USDT/event 可能吃不到报价，或把价格推高。历史 L2 无公开来源，无法回放整条盘口。
- **价差比假设宽**：实测 ask−bid 中位 4.0¢（半价差约 2¢），原稿按 1¢ 算；价差再宽 1¢ 就足以把 POOLED 的微弱均值压得更负。
- **费率口径会变**：2026-10-20 看到 0.05，2026-10-21 的 105 个 open 里 103 个已是 0；回测按 0.05 是保守值，但未来费率若上调会直接吃掉本就很薄的均值。
- **strike 不可复核**：行权价是 `as of market creation` 的 SeekingAlpha 一致预期，付费墙，本条未能独立验证「strike = 当时市场一致预期」。若 strike 本身被设在一个容易/难以 beat 的水平（发行方选点），基准率会系统性偏移，而这不是「定价错误」而是标的设计。
- **`resolve to "No"` 的兜底条款**：96 小时内 SeekingAlpha 无数字、或 45 天内不发财报 → 判 **No**。买 YES 在这些情形下全损，且这类事件在样本里无法从 `outcomePrices` 事后区分，会污染基准率（方向：让真实 beat 率被**低估**）。
- **肥手指例外**：规则明文允许 Lyft 2024 那种明显错误例外，属于裁量条款，可能改变结算。
- **信息时点**：`p_24h` 距财报发布通常只有几小时到 1 天，机构在发布前已按 channel checks 调价；我买到的可能正是「知道得更多的一方」卖出的。
- **平台**：`restricted=true`；UMA 结算争议、`endDate` 后账期不确定；2026-10-21 的 105 个 open event 集中在两周内，结算系统拥堵时资金占用会拉长。
- **样本选择**：1378 个事件里只有 2024-01 一个早于 2025-06，实际上等于**只有约 13 个月的样本**（2025-09 起密集），不足以覆盖一轮完整周期；2026-10-21 复核为 1393 个事件，10 月到 10-20 为 43 个，仍是部分月。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：部分满足** — 付款方是 50¢ 附近给 beat 概率报低价的对手方；原稿的量化证据是中间带 35 个事件事前价 0.4894 对实际 0.6571。但「为什么持续存在」只有单点横截面，没有时序证据；整体 Brier 显示市场并不系统性低估，可成交价回测也没有把缺口变成稳定正收益。
2. **有免费数据能检验：满足** — Gamma 全量 1378/1393 个已关闭事件 + CLOB 对已关闭市场**仍可取价格**（247/250 成功）+ data-api 逐笔成交（97/101 个带内事件有 ask 侧打印）；独立结果按事件计，历史 HOLDOUT 47 个、带内 101 个、严格前置样本外 68 个；SEC EDGAR 全文检索免密钥，可做独立口径复核。
3. **小资金能做：满足（容量偏小）** — 资金门槛满足：20–200 USDT/event、≤15 event、≤2,000 USDT，低于 2,500/场所与 5,000 总资金；不加杠杆、不借钱；买 YES 最大亏损即本金。容量已写明但偏小：观察到的 ask 成交打印中位仅 4.8 USDT，97 个里 1 个 ≥200 USDT，200 USDT/event 的可成交性未证实，所以实际只能先做 20–50 USDT/event。容量小是收益问题，不影响“小资金能做”。
4. **不重复：不确定（倾向不重复）** — 查了 `known/KNOWN.md`（135 条，grep `earnings|EPS|财报|盈利|beat|finance|股票` 无命中，最接近的是 `E-E1-macro-window`（FOMC/CPI 宏观窗口）与 `E-E1-index-etf-event`（指数纳入/ETF 获批），二者结算看宏观数据与监管公告，没有 EPS 一致预期行权价）；另 grep 全部 `bots/*/entries/*.md`，只有 `quant-004`（财报电话会**提及词**市场，结算看说了哪个词，不是 EPS 数字）命中 earnings，机制不同；`quant-007`（AI 榜单）、`dot-032`（流动性奖励）无关。`bots/*/CLAIMS.md` 里 B17 由本 bot 于 2026-10-20 认领。是否与主项目未公开条目重复要主审确认。
5. **扣成本后粗算够用：不满足** — 实际 ask 侧成交打印、费率 0.05：POOLED n=97 均值 **−0.0140/份（−2.71%/美元）**，95% CI [−0.1292, +0.0817] 跨 0；DISCOVERY n=54 均值 −0.0881（−16.92%）；HOLDOUT n=43 中位 +0.4476、均值 +0.0790，但 29/43 落在选带窗口内。剔除选带样本后 **STRICT_OOS n=68 均值 −0.0634/份（−12.14%/美元）、中位 −0.4120**，95% CI [−0.1638, +0.0366]；费率 0.04 → −0.0610（−11.68%），0.00 → −0.0515（−9.86%），仍不转正。原稿的「+29.1%」是模型算术，已作废，不再作为扣成本后为正的证据。
6. **两周内能检验：满足（历史口径，前向稀疏）** — GUIDE §2 第 6 条允许用历史数据；现有 101 个带内事件（严格选带外 68 个、HOLDOUT 47 个）都是按事件计的独立结果，均 ≥30，失败标准已冻结，两周内可完成这套历史检验。但若只算纯前向，`q020-oos` 实测任一滚动 14 天窗口带内最多 **24** 个（通常 <10），2026-10-21 的 105 个 open event 也不能改变这一点；前向复核见 `bots/quant/notes/q020-forward/`，只能作补充观察。本条不因门 6 降级，降级理由是门 5。
7. **出处可查：满足** — 每个数字都有 URL + 访问日期 + 取数方式；2026-10-21 已重抓 Gamma 全量、hims 规则原文、public-search、open 清单、CLOB、data-api、SEC 并保存 stdout（`verify_sources.out`，当日重跑逐字一致）；严格样本外脚本与 stdout 为 `strict_oos.py` / `strict_oos.out`；另对 3 个事件重取 data-api 核对最后一笔 ask 打印，`spotcheck_fills.out` 全部一致；基率与校准用 `verify_sources.py` 现取 JSON 重算，原稿 247 样本由 `batch2-verification/quant-020.md` 独立重跑（246/247 一致）；Gamma 的 `volume` 一律标「来源自报，未核实」；原稿「每个市场都收 0.05」已更正为分费率统计；未取到的（SeekingAlpha、历史 L2、结算到账时间）都写「未查到」。

## 出处

- https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=0..1400&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（全量翻页得 1378 个已关闭事件 / 1382 个市场 / YES 1028 / NO 354；`endDate` 2024-01-19 至 2026-10-19）
- 同上 — 访问 2026-10-21 — 已读（复核 1393 个已关闭事件 / 1397 个市场 / YES 1038 / NO 359 = 74.30%；nongaap 691/856 = 80.72%、gaap 347/541 = 64.14%；`endDate` 2024-01-19 至 2026-10-20；新结算 5 个事件与 2026-10-20 13:00 的 1384 个 deduped 快照一致；脚本 `verify_sources.py`，输出 `verify_sources.out`）
- https://gamma-api.polymarket.com/public-search?q=earnings&limit_per_type=20&events_status=all — 访问 2026-10-20 — 已读（模板确认：`Will Hims & Hers Health (HIMS) beat quarterly earnings?`，`resolutionSource=https://seekingalpha.com/`，`restricted=true`，`volume=287931.953117`）
- 同上 — 访问 2026-10-21 — 已读（返回 20 条事件，`pagination={"hasMore":true,"totalResults":1729}`；首条仍是 hims，`resolutionSource`、`restricted=true`、`volume=287931.953117` 不变；脚本 `verify_sources.py`）
- https://gamma-api.polymarket.com/events?slug=hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05 — 访问 2026-10-20 — 已读（规则原文全文：SeekingAlpha 一致预期、`greater than $0.05`、96h/45天兜底、舍入到分、IFRS=GAAP、diluted 优先）
- 同上 — 访问 2026-10-21 — 已读（10 个关键短语逐条命中：`as of market creation`、`SeekingAlpha estimates`、`greater than $0.05`、`within 96h`、`45 calendar days`、`rounded to the nearest cent`、`IFRS EPS will be treated as GAAP EPS`、`diluted GAAP EPS`、`fat finger errors`、`Lyft`；`resolutionSource=https://seekingalpha.com/`、`restricted=true`、`volume=287931.953117`、`outcomePrices=["1","0"]`；已关闭市场的 `feeSchedule=null`）
- https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=<endDate-72h>&endTs=<endDate>&fidelity=60 — 访问 2026-10-20 — 已读（247/250 个已关闭市场返回非空 history；例：`tfc-…-10-16-2026-1pt13` 从 `p=0.52` 到 `p=0.0045`；`mtb-…-10-16-2026-5pt00` 从 `p=0.745` 到 `p=0.9995`）
- 同上 — 访问 2026-10-21 — 已读（示例 `jef-…-2025-09-29-0pt8` 返回 57 个点，`t ≤ endDate−24h` 最后一点 `{"t":1759014011,"p":0.525}`；脚本 `verify_sources.py`）
- https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=<0..10000> — 访问 2026-10-20/21 — 已读（字段 `side`、`outcome`、`price`、`size`、`timestamp`；101 个带内事件中 97 个在 `[endDate−72h,endDate−24h]` 有 ask 侧打印；0 个市场因 offset 上限截断；脚本 `tradable_fills.py`，输出 `tradable_fills.out`、`tradable_fills.csv`）
- https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&closed=false&order=endDate&ascending=true — 访问 2026-10-20 — 已读（100 个 open 事件，`endDate` 至 2026-10-30；示例 `bfc-…-2pt66` bid 0.44/ask 0.46、`efx-…-2pt24` 0.56/0.69、`ally-…-1pt43` 0.17/0.77；`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`）
- 同上 `&offset=100` — 访问 2026-10-20 — 已读（另 18 个 open 事件，`endDate` 至 2026-11-05 → 16 天内共 118 个）
- 同上 — 访问 2026-10-21 — 已读（全量翻页得 **105** 个 open 事件，`endDate` 2026-10-21 至 2026-11-05；105 个中 103 个 `feeSchedule.rate=0`、2 个 `rate=0.05`；脚本 `verify_sources.py`）
- https://efts.sec.gov/LATEST/search-index?q=form%3A8-K%20items%3A2.02&forms=8-K — 访问 2026-10-20 — 已读（返回 JSON：`{"took":178,...,"hits":{"total":{"value":10000,"relation":"gte"},...}`；端点可达，逐份 EPS 抽取本轮**未做**）
- 同上 — 访问 2026-10-21 — 已读（`hits.total.value=10000, relation="gte"`；脚本 `verify_sources.py`）
- https://docs.polymarket.com/ — 本轮**未重新抓取**；费用公式与 5 位小数舍入沿用 GUIDE 第 8 节与本条 Gamma 实取 `rate=0.05`
- `bots/quant/notes/q020-oos/REPORT.md`、`run_output.txt`、`events.csv`、`q020_oos.py` — 2026-10-20 合并笔记 — 已读（+1¢ 口径：HOLDOUT n=47 中位 +0.4376、YES 0.5745 > 0.4881；POOLED n=101 均值 +0.0081、CI [−0.1005,+0.0972]；本次用 `tradable_fills.py` 逐项复现）
- `bots/quant/notes/scheduler/scratch/H-quant-020/strict_oos.py`、`strict_oos.out`、`STRICT_OOS.md`、`tradable_fills.csv` — 2026-10-21 — 已读（选带窗口切点 `2026-07-30T13:00Z`；STRICT_OOS n=68 均值 −0.0634/份、每美元 −12.14%、中位 −0.4120；SELECTION n=29 均值 +0.1017；旧 CLOB 选带口径 STRICT_OOS n=42 均值 −0.0503）
- `bots/quant/notes/scheduler/scratch/H-quant-020/verify_sources.py`、`verify_sources.out` — 2026-10-21 — 已读（当日重跑，stdout 与文件逐字一致；所有引用端点仍返回相同值）
- `bots/quant/notes/scheduler/scratch/H-quant-020/spotcheck_fills.out` — 2026-10-21 — 已读（对 `jef-…`、`hims-…08-10`、`tfc-…10-16` 三个事件重取 data-api，最后一笔 ask 打印与 `tradable_fills.csv` 完全一致）
- `bots/quant/notes/q020-forward/README.md`、`run_output.txt`、`q020_forward.py` — 2026-10-20 合并笔记 — 已读（预注册窗口 `[2026-10-21T00:00Z, 2026-10-26T00:00Z)`；`run_output.txt` 显示 29 个事件、0 个结算、2 个带内，`PENDING`，无判定）
- `bots/quant/notes/batch2-verification/quant-020.md` — 2026-10-20 核对笔记 — 已读（原稿 247 样本独立重跑；记录 7 的分桶数字与本条一致）
- 未查到：SeekingAlpha 原始一致预期与公布值（付费墙）；历史盘口/L2；结算到账时间分布

---
