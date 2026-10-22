---
id: quant-018
name_zh: 海峡周通行：PortWatch基准率
name_en: Weekly strait transit-call count ladder priced from IMF PortWatch base rates
bot: quant
date: 2026-10-20
market: polymarket
pm_category: geopolitics
kind: supplement
improves: quant-012
category: S
return_type: direction
instruments: Polymarket「How many ships transit the Strait of Hormuz / Bab el-Mandeb Strait, week of …?」5–6 档 negRisk 周度计数阶梯
venues: Polymarket
data: IMF PortWatch「Daily_Chokepoints_Data」ArcGIS REST（免费免密钥，2019-01-01 起）；Polymarket Gamma/CLOB（免费免密钥，已关闭市场的逐档价格历史只覆盖部分事件）；UMA 结算结果
test_2w: 独立结果按 weekly event 计（不按档）；历史侧 43 个已关闭事件做完价格侧检验，有真实成交价可回放的 13 个（10 个有触发成交）、同点全档有价事件 24 个（都 <30），两周内只能再前向记录约 4 个，门 6 不满足；失败标准是已成交 NO 份额的中位已实现毛利≤0，或两周成交<20 份，或 30 个历史事件上基准率 Brier 不优于市场价
status: 待核
confidence: 低
evidence: 回放
result: 不显著
slot: -
variants: 4
variants_ext: -
window: 2026-07-20..2026-10-18
max_dd: -
contribution: 1.5%
---

整理说明：本条的板块调研、模板计数、PortWatch 复算、费用与盘口数字都是我在 2026-10-20 本会话用 curl/urllib 现场取的（无密钥、无登录、未交易）；脚本 `pw_weekly.py`、`pw_verify.py`、`pw_calib.py` 全码附在文末 `notes/batch2-verification/quant-018.md`。初稿**没有做收益回测**：已关闭市场的逐档价格历史当时只有 6 个事件可取全，只能做 6 个事件的小样本校准，不能当盈利证明。2026-10-20 复核已补做 43 个已关闭事件的价格侧历史检验（“证据 4.4”）与同时点 data-api 成交配对检验；**2026-10-21 H-quant-018 再补做真实成交价可执行回测**（“证据 4.5”，含 1 个 post-draft OOS 事件），并重新核对出处节 17 个外部 URL（原有 15 个 + OOS 事件与 data-api 成交；2026-10-21/22 复跑全部 HTTP 200）。该回测已在第 2 轮格式下固化为可运行回放 `bots/quant/replay/quant-018/`（脚本、参数、数据地址、`SUMMARY.md`、逐份 `trades.csv`），条目字段 `evidence: 回放`、`result: 不显著` 与回放产物一致，见“证据 4.6”。加固结论：份额中位为正，但事件层不显著、独立事件 <30、决策后 60 分钟口径只剩 1 笔且为负，**建议 integrator 降为草稿或并入 quant-012，只作反证/补充，不占独立待核名额，最多按补充采纳（0.5）**；理由见 4.5、4.6、4.7 与门槛自查。本条只是 quant-012 的补充：review `c20261021-070001` 与 `c20261022-063202` 都指出同一机制不能让 018 再占一个独立待核名额；fixer 按本轮任务要求只保留原 `status: 待核` 供复核，不自行改状态。**2026-10-22 review c20261022-063202 复核**：4.2 的 0.127/0.16 与 +0.0682/份已明确标为 2026-10-20 快照；按 2026-10-21（0.024/0.333）和 2026-10-22（0.006/0.155）重抓，该示例 edge 已消失并转负，规则不会触发（见 4.2）。本条是 quant-012 的反证/补充：**不占独立待核名额，最多按补充采纳（0.5）**；正文按任务要求保留 `status: 待核`、`date: 2026-10-20` 不变。

## 一句话

在 Polymarket 地缘板块的「本周某海峡通行次数（transit calls）落在哪一档」周度阶梯上，用 IMF PortWatch 同一份免费日度数据算出的近 12 周经验分布当公允值；只在外侧档（`<170`、`230+`）明显被高估时挂 maker 买 NO，持有到 UMA 结算（约 7–9 天），不做 Hormuz，因为它的分布宽到没有基准率可言。

## 钱从哪里来

付钱给你的是**把外侧档按"危机还会升级"来出价的散户**。这条模板的结算值不是新闻、不是民调、不是官方口径的"某方是否宣布"，而是 PortWatch 的一串日度计数：区间内所有日子的通行次数加总。它可能持续存在的理由是：档位边界由平台按近期水平设定（Bab 的 `170-189 / 190-209 / 210-229` 每档只有 20 次宽，Hormuz 九月底起每档只有 5 次宽）。但**“外侧档被系统性多付”只在 2026-10-20 快照成立**：当时两个 open 市场的中价合计为 **Bab 1.010、Hormuz 1.1615**（按 Gamma bid/ask 中价加总）。2026-10-22 重抓同一事件，Bab 中价合计 **1.032**、Hormuz **0.971**；Bab `<170` 的 bid/ask 从 0.127/0.16 变为 **0.006/0.155**，原先 +0.0682/份的示例变成 **−0.0528/份**，规则不触发。也就是说，付款方故事目前只有一个历史横截面支持，**不能当作持续存在的证据**；本条因此只按反证/补充处理。这也不是套利：当时十条腿的卖价合计 1.408（Hormuz）根本买不齐，原假设的收益只能来自“报价挂在那里被情绪单打中”。

## 规则

### 3.1 板块调研（`tag_slug=geopolitics`，我现场数出来的）

| 模板族 | 我在样本里数到的 event 数 | 是否有可计数的免费结算源 |
|---|---:|---|
| by-日期阈值（`by…?` / `byptptpt` 结尾，如「Will Russia enter X by…」） | 106 | 需人工判读 ISW/DeepState 地图，非机器可读 |
| 其他（一次性事件、人物、选举组合） | 92 | 多数无 |
| 俄乌村/镇进入（`Will Russia enter X`） | 27 | 同上 |
| **周度海峡通行计数（`how many ships transit … week of`）** | **16（含 open）** | **是：IMF PortWatch 日度计数** |
| 伊朗打击某国（`Will Iran target Kuwait/Bahrain/…`） | 15 | 无（事件型） |
| 停火 by/持续到（`ceasefire`） | 12 | 无 |
| 下一个被美国打击的国家（`next country US strikes`） | 10 | 无 |
| 其他计数阶梯 | 6 | 部分 |
| 岛屿/基地易手（`no longer under X control`） | 6 | 无 |
| 下一位下台的领导人（`next leader out of power`） | 5 | 无 |
| **月度海峡均值（`Avg. # of ships … end of …`）** | **6** | 是（同源） |
| **周度 UKMTO 通报计数（`how many UKMTO notices`）** | **1（open）** | 是（UKMTO 公开通报），但只有 1 个 event |

说明：`closed=true` 的 `limit=500` 被服务端截到 **100 条/页**，我取了两页共 **200 个已关闭 event**（`endDate` 2026-09-01 至 2027-12-31，含未到期但已被标 closed 的），加上 `closed=false` 的 **100 个 open event**，样本 300 个；这不是板块全量，属于**抽样**，所以上表是"样本内计数"，不是全站总数。**唯一同时满足"≥30 个独立历史结果 + 免费可计数结算源"的是周度海峡通行计数模板**（47 个 event，其中 **43 个已关闭**：Hormuz 31 / Bab 12；2026-10-21 复核已变为 44：Bab 新增 `week of October 12`），所以选它。月度均值模板只有 6 个（两个搜索里 `avgpt-of-ships-*` / `avg-of-ships-*` 按 slug 去重的 union）、UKMTO 只有 1 个，都不够 30。

### 3.2 选中的模板与规则原文要点

模板写法：`How many ships transit the Strait of Hormuz week of October 19?` / `How many ships transit Bab el-Mandeb Strait week of October 19?`，每个 event 是一个 UTC 周的计数分档，`negRisk=true`，各档是独立二元市场。

示例市场（2026-10-20 Gamma 快照，全部 `closed=false`）：
- `how-many-ships-transit-bab-el-mandeb-strait-week-of-october-19`：5 档 `<170 / 170-189 / 190-209 / 210-229 / 230+`，`startDate=2026-10-13T09:34:52Z`、`endDate=2026-10-26T03:59:00Z`，`volume=13595.368699`、`liquidity=53710.92511`。
- `how-many-ships-transit-the-strait-of-hormuz-week-of-october-19`：6 档 `<20 / 20-24 / 25-29 / 30-34 / 35-39 / 40+`，`volume=5539.661748`、`liquidity=22748.92012`。
- 已结算示例：`how-many-ships-transit-bab-el-mandeb-strait-week-of-october-5`（`endDate=2026-10-12T03:59:00Z`、`closed=true`、`volume=13097.774817`），窗口「October 5, 2026, through October 11, 2026」，结算为 `190-209`（`outcomePrices` 该档 `["1","0"]`）。

结算规则原文（同一 event 的 `description`，2026-10-20 已读，逐条摘）：
- 计数口径：「the total number of transit calls that IMF Portwatch reports for the Bab el-Mandeb Strait for all days from October 5, 2026, through October 11, 2026, inclusive」——**周一到周日的 7 天加总**，不是某一时点、不是平均值。
- 船型：「Transit calls include container, dry bulk, roll-on/roll-off, general cargo, and tanker ships.」——对应 PortWatch 的 `n_container/n_dry_bulk/n_roro/n_general_cargo/n_tanker` 五类，合计即 `n_total`。
- 不在源里的船不算：「Ships not reported by IMF Portwatch will not be considered.」
- 结算源：「IMF PortWatch, specifically the "Arrivals of Ships" data published for the Bab el-Mandeb Strait at https://portwatch.imf.org/pages/6b1814d64903461b98144a6cc25eb79c」。
- 发布迟到的兜底：「If the relevant data is not published within 14 calendar days of the specified date, this market will resolve based on the most recent data published up to that point.」——**这是本条最大的规则风险**（见风险节）。
- 修订：「Only revisions to previously published data points made before all relevant data has been published will be considered.」即事后重算的修订不算；数据完整发布前的修订算。
- 数据完整性问题可延到发布后第 3 个 ET 日；明确说「IMF Portwatch 与其他来源不一致」不算完整性问题。
- 档位边界是平台按当期水平设定的，**逐期不同**（3–6 月的 Hormuz 用过 `45+ / 40-49 / 75-99 / 100+ / 150+` 等），所以策略必须按当期档位现算，不能沿用旧边界。

### 3.3 交易规则（我的提案，未验证）

1. 公允值：取该海峡**严格早于本期起始日**的 12 个完整 Mon–Sun 周总量，映射到本期档位网格，做 Laplace 平滑 `p_i=(k_i+1)/(12+n)`，`n` 为档数。不用全历史（2019–2026 共 405 个完整周，横跨战前/战中两个完全不同的状态）。
2. 只做 Bab el-Mandeb：近 12 周总量 sd=13.51，档宽 20，分布可用；Hormuz 近 30 周 sd=44.17、极差 10–213，档宽只有 5，基准率对它没有信息量（`|周环比变化|` 中位 13 次 > 档宽 5 次）。
3. 触发：某档 `1-p_i ≥ 该档 NO 的可成交卖价 + 0.01` 才挂 maker 买 NO（`0.01` 为安全垫，成交前写死）。**下面是 2026-10-20 快照，不是当前盘口**：当时 `<170` 档 YES `bestBid=0.127 / bestAsk=0.16`，NO 卖价 `1-0.127=0.873`，公允 NO `1-0.0588=0.9412`，价差 `+0.0682/份`。**2026-10-22 重抓**：同一档 `bestBid=0.006 / bestAsk=0.155`，NO 买价 `1-0.006=0.994`，对公允 `0.9412` 是 **−0.0528/份（−5.3% 占款）**，规则**不触发**；2026-10-21 的 0.024/0.333 同样已使 edge 转负。所以 `+0.0682` 不能当现存机会。
4. 不做裸卖 YES，不碰 negRisk 转换；不加杠杆、不借钱。
5. 仓位：每档在险 ≤100 份，单 event ≤200 USDT，同时在手 ≤2 个 event，本条专线总额 ≤1,000 USDT（远低于单场所 2,500）。
6. 出场：不主动平仓，持有到 UMA 结算。
7. 熔断：某周已公布的日度累计一旦越过该档边界，立即撤掉该档剩余挂单（PortWatch 是分批发日度数据，见数据节）。
8. 明确不做：Hormuz 全部档位；月度均值模板（6 个事件，样本不足）；UKMTO 模板（1 个事件）。

## 证据

### 4.1 结算源是否可复算（我自己跑的，最重要的一条）

脚本 `pw_verify.py`：从 PortWatch `Daily_Chokepoints_Data` 取两个海峡全部日度 `n_total`（**5,682 行**，每海峡 2,841 天，覆盖 **2019-01-01 至 2026-10-11**），按 Mon–Sun 聚成 **405 个完整周**，再把已关闭周度事件按我算出的周总量套进档位区间，与 Gamma 的已结算档位比对：

- **共 43 个已关闭事件（Hormuz 31 / Bab 12），另有 4 个 open（两海峡各 2）**：**MATCH 34 / MISMATCH 7 / 无法比对 2**。2 个无法比对的是 `...-this-week-mar-10-16`（`description` 里没有可解析的日期窗口）和 2026-03-17 那个（它的窗口起点是周二，不在我的 Mon–Sun 分箱里）。
- 7 个 MISMATCH 全部落在 **2026-03-23 至 2026-05-25**（3-23、3-30、4-13、4-27、5-11、5-18、5-25）；**2026-07-13 之后的 25 个事件全部 MATCH**（Hormuz 13 + Bab 12）。
- 例：`week of october 5` Bab，我算 198，档位 `190-209`，市场结算 `190-209`；同周 Hormuz 我算 29，档位 `25-29`，市场结算 `25-29`。
- 我的推断（**未核实**）：MISMATCH 那 7 周集中在 3–5 月，可能是 PortWatch 事后重算把当期数值改掉了（规则只承认"数据完整发布前"的修订），或当期市场用了不同的档位口径；我没有 3–5 月的 PortWatch 历史快照，无法分辨这两种解释。
- 结论：**当前口径下（2026-07-13 起）复算 25/25 一致**，所以基准率可以用同一份免费数据算出来；但更早的 7 周我复算不出来，这条限制写在这里。
- **2026-10-21 复核（`notes/scheduler/scratch/H-quant-018/verify_sources_stdout.txt`）**：PortWatch 已更新到 **5,696 行 / 每海峡 2,848 天 / 最新 2026-10-18**（完整周 407）。上面的 5,682 行 / 2,841 天 / 2026-10-11 是 **2026-10-20 快照**，不是今天的数；说明该渠道在 10-20 之后恢复了发布，但 14 天兜底条款仍然存在（见风险节）。同族已关闭事件也从 43 变为 **44**（Hormuz 31 / Bab 13），新增的 Bab `week of October 12` 只用于 4.5 的 post-draft OOS，不回填 4.4 的 43 事件表。

### 4.2 基准率本身（我算的）

Bab el-Mandeb 近 12 个完整周总量（2026-07-20 起，脚本 `pw_weekly.py` 输出）：`198, 215, 178, 206, 206, 184, 178, 191, 173, 190, 207, 198`，均值 **193.67**、样本 sd **13.51**、min **173**、max **215**；全样本 405 周 min **173**、max **578**（战前水平高得多，所以不能直接用全样本）。

套到 `week of october 19` 的 5 档上：

| 档 | 原始频率（12 周） | Laplace `(k+1)/17` | 2026-10-20 中价 | 中价 − Laplace |
|---|---:|---:|---:|---:|
| `<170` | 0/12 = 0.000 | 0.059 | 0.1435 | +0.085 |
| `170-189` | 4/12 = 0.333 | 0.294 | 0.345 | +0.051 |
| `190-209` | 7/12 = 0.583 | 0.471 | 0.370 | −0.101 |
| `210-229` | 1/12 = 0.083 | 0.118 | 0.0855 | −0.032 |
| `230+` | 0/12 = 0.000 | 0.059 | 0.066 | +0.007 |
| 合计 | 1.000 | 1.000 | **1.010** | |

可执行的一侧（**2026-10-20 快照，不是当前价**）：`<170` 的 YES `bestAsk=0.16`、`bestBid=0.127`，买 NO 需付 `0.873`，公允 NO `0.9412`，当时**每份 +0.0682**；按占用资金折 `+7.8%`，占款约 7 天（`endDate=2026-10-26T03:59Z`，另加发布与结算滞后）。**这个 edge 已经消失**：2026-10-21 重抓 bid/ask=**0.024/0.333**（audit c20261020-170337 §2.2），2026-10-22 重抓=**0.006/0.155**；后者 NO 买价 `1-0.006=0.994`，对公允 `0.9412` 是 **−0.0528/份（−5.3%）**。`230+` 按 2026-10-22 的 bid `0.013` 算 NO 买价 `0.987`，同一算式 **−0.0458/份**，也不挂。表中 2026-10-20 中价合计 1.010 是历史快照；2026-10-22 同一事件中价合计 **1.032**（`0.0805/0.465/0.385/0.058/0.0435`），外侧档不再一致地被高估。以上是模型算术，不是实测，也不能当现存 edge。

Hormuz 同一快照（为什么不做）：六档中价 `<20 0.30 / 20-24 0.347 / 25-29 0.335 / 30-34 0.07 / 35-39 0.0585 / 40+ 0.051`，合计 **1.1615**；卖价合计 `0.35+0.375+0.38+0.11+0.104+0.089 = 1.408`，买价合计 `0.915`。外侧三档中价合计 `0.1795`，而近 30 周（`10,25,37,41,52,28,86,10,38,34,21,31,17,85,213,162,98,44,25,37,39,31,35,30,22,37,22,22,19,29`）里 ≥30 的占 18/30，基准率无法否定这个定价——**Hormuz 的阶梯看起来贵，但基准率给不出可交易的差额**，如实写在这里。

### 4.3 小样本校准（6 个事件，不构成结论）

脚本 `pw_calib.py`：对 2026-07-13 之后、逐档 CLOB 价格历史能取全的 6 个已关闭事件（Hormuz 2026-09-21/09-28/10-05，Bab 2026-09-21/09-28/10-05），比较三个预测器的多分类 Brier（越小越好）：

| 预测器 | 平均 Brier（n=6） |
|---|---:|
| 市场价（首个可得价格，归一化） | 0.7962 |
| 市场价（`endDate` 前约 24h 的最后价格，归一化） | 0.7975 |
| PortWatch 12 周基准率（Laplace） | **0.7646** |

基准率小胜 0.03，但 **n=6，且 25 个事件里只有 6 个能取全价格**（其余事件的若干档因无成交而 `prices-history` 为空）——**这不能算证据，只能算"方向对，样本不够"**。实现细节：归一化用各档首个价格除以合计；某档价格缺失则整事件剔除（脚本会打印 SKIP）。

### 4.4 价格侧历史检验（43 个已关闭事件，2026-10-20 复核）

完整脚本、逐事件表与 stdout 见 `bots/quant/notes/q018-price-test/REPORT.md`（见 PR #4）。口径：Gamma 的 43 个已关闭事件（Hormuz 31 / Bab 12）；CLOB `prices-history` 取每个档位的 YES 价格历史，多分类 Brier 用 `Σ(p_i−y_i)^2`；基准率仍是同海峡严格早于事件周起点的最近 12 个完整 Mon–Sun 周、Laplace `(k_i+1)/(12+n)`；交易规则只做 Bab，NO 吃单价 `1−p_ref+0.01`，另加 0.01 安全垫。

**覆盖**：242 个档位 token 全部非空（242/242）；首价完整的事件 **43/43**；周起点价完整的事件 **34/43**（缺的 9 个是在周中才创建）。

| Brier 口径 | n | 模型均值 | 市场首价均值 | 配对差（市场−模型） | t | p | 模型更好 | 符号检验 p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 全部事件 | 43 | 0.7658 | 0.8060 | +0.0402 | 0.815 | 0.4198 | 24/43 | 0.5424 |
| Bab el-Mandeb | 12 | 0.8580 | 0.8032 | **−0.0548** | −0.471 | 0.6470 | 7/12 | 0.7744 |
| Hormuz | 31 | 0.7302 | 0.8071 | +0.0770 | 1.499 | 0.1442 | 17/31 | 0.7201 |
| 有周起点价的子集（市场仍用首价） | 34 | 0.7747 | 0.8093 | +0.0346 | 0.585 | 0.5623 | 19/34 | 0.6076 |
| **周起点价子集（市场用 start 价，策略实际口径）** | 34 | 0.7747 | **0.7436** | **−0.0310** | −0.473 | 0.6365 | 14/34 | 0.3915 |
| MATCH-only | 34 | 0.7576 | 0.7998 | +0.0422 | 0.715 | 0.4797 | 20/34 | 0.3915 |
| 严格周聚类 | 31 周 | — | — | +0.0464 | 0.984 | 0.3329 | 15/31 | — |

**Bab 交易 P&L（只做 Bab，NO 按周起点价成交；缺失时首价回退）**：纯周起点价口径 **n=29，NO 胜 22，中位毛利 +0.2250/份，总毛利 +0.7970，总投入 21.2030，每美元投入 P&L +0.0376，命中率 0.7586**；含首价回退 **n=32，NO 胜 25，中位毛利 +0.2325/份，总毛利 +1.5120，总投入 23.4880，每美元投入 P&L +0.0644，命中率 0.7812**。手续费按地缘费率 0，已实现毛利含亏损份额。

**诚实解读**：

- 失败标准 (1) **PASS**：周起点价口径 n=29，中位毛利 +0.2250/份 > 0；含首价回退 n=32，中位 +0.2325/份，同样为正。
- 失败标准 (3) 只在“全部 43 个事件”上 **PASS**（0.7658 vs 0.8060，差 +0.0402），但**不显著**（t=0.815，p=0.4198；符号检验 p=0.5424），且优势全部来自 Hormuz（+0.0770）；**Bab 子集 n=12 < 30，模型反而更差（−0.0548），应读作 INSUFFICIENT**。因此 (3) 的 PASS 不能当作 Bab 策略的校准证据。
- **口径更正（2026-10-21，H-quant-018）**：原表“周起点价子集 34 事件，市场 0.8093”这一行实际仍用市场**首价**。用同一份 `q018-price-test/buckets.csv` 重算，策略实际使用的**周起点价** Brier 是 **0.7436**，模型 0.7747，即市场优于模型 **−0.0310**（t=−0.473，p=0.6365；模型更好仅 14/34，符号检验 p=0.3915）；Bab 子集（start 价完整 n=11）模型 0.8769 vs 市场 0.8112，模型更差 **−0.0657**。脚本与 stdout：`notes/scheduler/scratch/H-quant-018/brier_start_check.py` 与 `..._stdout.txt`。所以标准 (3) 的 PASS **只对首价口径成立**；对实际 Bab 周起点策略应读作 **INSUFFICIENT/不利**，不能拿来当校准证据。
- 价格侧数据是 CLOB `prices-history` 的**最后成交价（fidelity=60 的小时级抽样）**，不是可执行盘口；历史深度与真实买卖价差取不到，1¢ 半价差是预先假设。因此上述交易 P&L 只能当“方向与量级”的证据，不是可复制的收益证明。

## 同时点可成交价配对检验

2026-10-20 补做（PR #8，完整脚本、逐事件与逐档表见 `bots/quant/notes/q018-paired/REPORT.md` 与 `run_output.txt`）：只用 data-api 在事件窗口起点 T 的 `[T−24h, T]` 内的真实成交价（同一时点、可成交近似），不再混用首价与周起点价。覆盖 **24/43** 个已关闭事件全档有价（Hormuz 19/31、Bab 5/12）。

- 冻结标准 (1)：**PASS** — Bab 主口径 **n=18** 份，NO 胜 13，中位毛利 **+0.2400/份**、中位净利 **+0.2400/份**。**更正（2026-10-22）**：这些是 `T` 前最后一笔成交，不是决策后可成交价；要求决策后 60 分钟内成交时只剩 **1** 笔（−0.92），见 4.7。
- 冻结标准 (3)：**INSUFFICIENT** — 同时点价格完整事件仅 **24 < 30**。
- 总体判定：**INSUFFICIENT**。

同样的数据也说明**此前的优势没有在同时点可成交价下复现**：全部事件 Brier 模型 0.7047 vs 市场 0.9318（n=24，原始价未归一化），但按档归一化后市场 0.7408、差仅 **+0.0360**（t=0.428，p=0.6729），Bab 子集 n=5 为 0.7471 vs 0.7710，均不显著；Bab 交易在事件层总净利 **+0.1216**、每事件中位净利 **−0.1800**、每美元投入 **+0.0094**、事件命中率 **0.4444**；5¢ 压力下 n=15、总净利 **−0.2284**、每美元 **−0.0203**。因此不能把旧报告的 Brier 优势或 Bab 交易经济性当作已复现的证据。

另一条中性旁证：dot 的补充条目 `bots/dot/entries/dot-051-strait-count-paired-cash-supplement.md` 在相同事件上用 start 价重算，本次已用同批 34 个事件复现其数字：start 价 Brier **0.743627407** 优于模型 **0.774672321**（差 −0.031044914），方向与上表更正行一致。

### 4.5 真实成交价可执行回测（H-quant-018，2026-10-21）

为了回答“按条目规则真的成交，扣费后还剩多少”，2026-10-21 补做了一次**只用真实成交打印**的 NO 回测；完整脚本、stdout、逐份成交见 `notes/scheduler/scratch/H-quant-018/tradable_backtest.py`、`tradable_backtest_stdout.txt`、`tradable_fills.csv`。

**口径（写死在脚本头部，未按结果调参）**：只做 Bab；`T` 为事件周周一 00:00 UTC；模型仍用严格早于 `T` 的最近 12 个完整 Mon–Sun PortWatch 周 + Laplace；入场价取 `[T−24h, T]` 内 data-api 的**最后一笔真实成交**（YES 打印取 `p`，NO 打印取 `1−p`），窗口内无成交则该档不成交；触发 `p_yes ≥ p_model + half_spread + 0.01`；基础 `half_spread=0.01`，压力 `0.05` 且**重新判定触发**；成本 `1−p_yes+half_spread`；费用按当前 Gamma `feesEnabled/feeSchedule`，13 个事件全部为 0；每档 1 份，亏损份额计入。

**样本**：12 个已关闭 Bab 事件直接复用 `bots/quant/notes/q018-paired/buckets.csv`（未重跑，sha1 `962b0b24…`）；另加 1 个**条目快照之后才结算**的事件 `...-week-of-october-12-20261006t134953677z`（2026-10-12..10-18，结算 `170-189`），用 2026-10-21 现场 Gamma/data-api/PortWatch 数据，作为唯一的 **post-draft OOS**。OOS 只有 1 个事件，不能当显著性证据。

| 口径 | 份数 | 有成交事件 | 中位/份 | 每美元投入 P&L | 事件中位 | 事件胜 |
|---|---:|---:|---:|---:|---:|---:|
| 全样本 base（1¢） | 21 | 10 | +0.2400 | +0.0465 | +0.0850 | 5/10 |
| 草稿期 12 事件 base | 18 | 9 | +0.2400 | +0.0094 | **−0.1800** | 4/9 |
| post-draft OOS 1 事件 base | 3 | 1 | +0.1900 | +0.2448 | +0.5900 | 1/1 |
| 全样本 5¢ 压力 | 18 | 10 | +0.2000 | +0.0176 | +0.2550 | 6/10 |
| 草稿期 12 事件 5¢ 压力 | 15 | 9 | +0.2000 | **−0.0203** | +0.2000 | 5/9 |

事件聚类 bootstrap（10,000 次，种子 20261021）：全样本 base 每份均值 95% 区间 **[-0.158, +0.188]**，每美元 **[-0.216, +0.261]**，都跨 0。限制：data-api 只给已成交打印，不给当时订单簿深度；1¢/5¢ 价差是预先假设，薄市场可能更差；PortWatch 是当前修订版，不是 `T` 时点的 vintage。

**诚实解读**：

- 冻结标准 (1) 的字面口径仍 **PASS**（份额中位 +0.2400/份），但这是**份额中位**；事件层中位只有 **+0.0850**，10 个事件里 5 赚 5 亏，草稿期事件中位 **−0.1800**。只看 +0.24 会高估。
- 5¢ 压力下草稿期每美元 **−0.0203**；全样本每美元 +0.0465 的 95% 区间跨 0，**不能宣称扣成本后稳定为正**。
- 把草稿期按 2026-09-01 事后切成两段（不是预注册）：前段 10 份总 **−0.0184**、后段 8 份 **+0.1400**；两段都很小，且后段事件中位 **−0.1800**，同样不能说明稳定。
- 唯一 post-draft OOS 事件 +0.5900（3 份）为正，但 n=1 事件，无法抵消上面的不确定性。
- 有触发成交的独立事件 **10 个 < 30**；同点全档价格完整事件 24/43 < 30；决策后 60 分钟内 Bab 只有 **1/12 个事件可成交（1 份，−0.92）**。按 GUIDE §2 第 6 条，**门 6 仍不满足**；门 5 也不能判满足。因此本条**不应按收录或待选区候选处理**；建议 integrator **降为草稿或并入 quant-012**，只作 quant-012 的反证/补充，最多按补充采纳（0.5），保留前向记录供以后复核。

### 4.6 第 2 轮回放产物（H-quant-018，2026-10-21）

4.5 的回测已固化为可复跑的回放目录 `bots/quant/replay/quant-018/`：`replay.py`（无网络、读冻结输入；一次跑 4 个变体）、`inputs/buckets_bab.csv`（12 个草稿期 Bab 事件，由 `notes/q018-paired/buckets.csv` sha1 `962b0b2434581fdf75a6ea8210836a6931baa6e3` 原样投影）、`inputs/strict_bab.csv`（同一批 12 个事件，由 `notes/postdecision-fills-20261021/q018_strict_buckets.csv` sha1 `ae0c71bb…` 投影出 `T` 后第一笔与时间戳，PR #21）、`inputs/oos_bab_oct12.csv`（1 个 post-draft OOS）、`trades.csv`（66 份成交，4 个变体）、`stdout.txt`、`SUMMARY.md`。V1/V2 把规则里的“挂 maker 买 NO”近似为 `[T−24h,T]` 内**最后一笔真实成交价**（同一秒取对 NO 买方最差的最高 YES 价），没有模拟排队位置；这**不是**决策后可成交价（价格早于决策时点 `T`；2026-10-22 更正原“最保守成交近似”的说法）。V3/V4 改用决策后 `T` 的第一笔成交，V4 另要求 60 分钟内，见 4.7。运行 `python3 bots/quant/replay/quant-018/replay.py` 得到：

| 口径 | 份数 | 独立事件 | 总净 | 每美元 | 事件中位 | 事件胜 |
|---|---:|---:|---:|---:|---:|---:|
| base 1¢ 全样本 | 21 | 10 | +0.7116 | +0.0465 | +0.0850 | 5/10 |
| base 1¢ 草稿期 | 18 | 9 | +0.1216 | +0.0094 | **−0.1800** | 4/9 |
| base 1¢ post-draft OOS | 3 | 1 | +0.5900 | +0.2448 | +0.5900 | 1/1 |
| 5¢ 压力全样本 | 18 | 10 | +0.2416 | +0.0176 | +0.2550 | 6/10 |
| 5¢ 压力草稿期 | 15 | 9 | **−0.2284** | **−0.0203** | +0.2000 | 5/9 |
| V3 决策后第一笔（STRICT，草稿期） | 26 | 12 | +1.1505 | +0.0610 | +0.0450 | 6/12 |
| V4 决策后 60 分钟内（STRICT60，草稿期） | 1 | 1 | **−0.9200** | **−1.0000** | **−0.9200** | 0/1 |

事件聚类 bootstrap 全样本每份 95% 区间 `[-0.158, +0.188]`、每美元 `[-0.216, +0.261]`，跨 0。事件序列最大回撤 −1.4600 USDT（按 200 USDT/event 上限折 −0.73%，不是账户级）。年化贡献粗算：草稿期每美元 +0.0094 × 200 USDT/event × 约 39 次/年 ÷ 5,000 = **1.5%**（**上限粗算，未由成交深度验证**；回放是 1 份/档，200 USDT/event 来自条目假设）。回放本身 **4 个变体**（V1 base 1¢、V2 5¢ 压力且重新判定触发、V3 决策后第一笔、V4 决策后 60 分钟；V3/V4 只覆盖 12 个草稿期事件，无 OOS），`variants_ext: -`。**独立事件 10 < 30，`result: 不显著`**；没有把份额中位 +0.24 当成事件层结论。所有参数、数据地址和变体表见 `bots/quant/replay/quant-018/SUMMARY.md`。review c20261021-070001 已核对 V1/V2 的数字；2026-10-22 H-quant-018 把 V3/V4 并入回放后再次运行，输出与仓库内 `stdout.txt` **逐字节一致**（diff 为空，V1/V2 数字未变）。

### 4.7 决策后 60 分钟可成交性复核（PR #21，2026-10-21；2026-10-22 写入本条）

4.5/4.6 的入场价是 `[T−24h, T]` 内**决策时点 `T` 之前的最后一笔**成交，不是决策后能成交的价格；上文“最保守成交近似”的说法不成立，更正如下。`bots/quant/notes/postdecision-fills-20261021/REPORT.md` §2.2（脚本 `q018_strict.py`、stdout `q018_strict.out`、逐档表 `q018_strict_buckets.csv`）对 Bab 主规则用决策后成交重跑（费用、触发、结算沿用 `q018-paired`）：

| 口径 | 成交份额 | 有成交事件 | 不可成交事件 | 每份净均值 | 每份净中位 | 标准 (1) |
|---|---:|---:|---:|---:|---:|---|
| 原口径：T 前最后一笔 | 18 | 9 | 3/12 | +0.0068 | +0.2400 | PASS |
| STRICT：T 后第一笔（不限延迟） | 26 | 12 | 0/12 | +0.0443 | +0.2300 | PASS |
| STRICT60：T 后 60 分钟内须有成交 | **1** | **1** | **11/12** | **−0.9200** | **−0.9200** | 点估计 FAIL，整体 INSUFFICIENT（n=1） |

结论：标准 (1) 的 PASS 依赖决策后**较晚**才出现的成交；在“决策后 60 分钟内可成交”的要求下，Bab 只有 **1 笔**成交且亏 **−0.92**，12 个事件里 11 个不可成交。本条在决策时点的可成交性/可执行性**没有证据**，交易经济性只能写“未证实”。`status` 按要求不改（仍 `待核`，作为反面证据保留），`result: 不显著` 不变；STRICT 与 STRICT60 已作为 V3/V4 收进回放（`trades.csv` case `strict_1c` / `strict60_1c`），`variants` 共 **4**。

## 数据

- **IMF PortWatch（本条核心，免费、免密钥、无需注册）**：ArcGIS FeatureServer `https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query`，字段 `date, portname, n_total, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, capacity...`；`where=portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')`；单页上限 1,000 行（`exceededTransferLimit=true`），需 `resultOffset` 翻页。覆盖 **2019-01-01 起**；我 2026-10-20 抓时最大 `date` 是 **2026-10-11**（5,682 行 / 每海峡 2,841 天）。**2026-10-21 复核**：5,696 行 / 每海峡 2,848 天 / 最新 **2026-10-18**（407 个完整周）；**2026-10-22 再抓不变**（5,696 / 2,848 / 2026-10-18），见 `notes/scheduler/scratch/H-quant-018/verify_sources_stdout.txt`。
- **发布节奏（我观察到的，不是官方说明）**：结算规则里指定的那个 PortWatch 页面 `https://portwatch.imf.org/pages/6b1814d64903461b98144a6cc25eb79c` 我在 2026-10-20 抓到 216,598 字节的 ArcGIS Hub 页面，但**页面 HTML 里没有直接的表格链接**（条目 id 只有一个 logo 的 `fe7fbd7489ec425d8c415e7ad3ef01da`），所以日度数据我是经 ArcGIS 服务取的，不是经这个页面点的；这条"页面 = 服务"的对应关系**未完全核实**。观察到的事实：2026-10-20 时最新日度数据是 2026-10-11；2026-10-21 复核已到 2026-10-18，Bab `week of October 12` 已结算 `170-189`、Hormuz 同周仍 `closed=false`。即便如此，日度数据在周内是否可见取决于发布时点，**不能假定周内能看到完整 7 天**；本条仍不做周内 nowcast。
- **Polymarket Gamma（免费免密钥）**：`events?slug=<event slug>`（规则原文、`outcomePrices`、`bestBid/bestAsk`、`feesEnabled`、`clobRewards`、`negRisk`）；`events?tag_slug=geopolitics&closed=true|false`（板块普查）；`public-search?q=how many ships transit&limit_per_type=100&events_status=all`（同族清单）。
- **CLOB（免费免密钥）**：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`；原稿只覆盖 6 个事件（Hormuz `week of october 5` 的 `25-29` 档有完整序列，其余无成交档返回空）；2026-10-20 复核改用 `startTs/endTs` 分段后，43/43 个事件有首价、34/43 有周起点价，见“证据 4.4”。
- **缺失且必须承认**：每条策略所需的"事件当天的盘口"取不到（CLOB 只给价格序列，不给历史深度）；逐笔成交本次未取（data-api 每个市场约最近 2 万笔）；PortWatch 的历史版本（3–5 月当时发布值）取不到，所以那 7 个 MISMATCH 无法解释。

## 两周内怎么检验

- **独立结果按 event 计，不按档、不按市场**：一个周度 event 的 5–6 个档共享同一个 PortWatch 计数，算 1 个结果；同一周两条海峡共用同一份源、同一驱动（地区冲突），按严口径也算 1 个，宽口径算 2 个。
- **历史侧（已完成，2026-10-20/21）**：43 个已关闭事件的价格侧检验已做完——首价完整 43/43、周起点价完整 34/43，Brier 与 Bab 交易 P&L 见“证据 4.4”；2026-10-21 又用真实成交价补做 10 个有触发成交事件的 NO 回测（含 1 个 post-draft OOS），见“证据 4.5”，并固化为 `bots/quant/replay/quant-018/`（“证据 4.6”）。结论是标准 (1) 的份额口径 PASS，但事件层不显著；标准 (3) 只对首价 PASS，周起点价口径下模型劣于市场；历史侧**不能**把独立事件补到 30。
- **前向侧**：每周 2 个 event（两海峡），两周 4 个，凑不到 30；只能当"先看成交"的小样本。**门 6 因此不满足。**
- 每天记录：PortWatch 当日新发布的 `date, portname, n_total`；各档 `bestBid/bestAsk/outcomePrices`；我的挂单、成交、库存。
- **失败标准（写死，事后不改）**：
  1. 已成交 NO 份额的**中位已实现毛利 ≤ 0**（毛利 = 票面 1.00 − 成交价，不含未成交挂单）；
  2. 或两周内成交份额 < 20 份（判"容量失败"，同样按失败处理；本条已不建议进待选区）；
  3. 或补全的 30 个历史事件上，基准率的平均 Brier **不优于**市场价首价（当前首价 43 个事件上 0.7658 vs 0.8060，但不显著；周起点价 34 个事件上模型 0.7747 vs 市场 0.7436，模型更差；Bab 独立事件 <30，故对实际规则是 INSUFFICIENT）。
- 不允许的自我安慰：不能把"挂单没成交"当正结果；不能在 6 个事件上说"已验证"。

## 成本与容量

- **费用**：该族市场 Gamma 返回 `feesEnabled=false`、`feeSchedule=null`（2026-10-20 快照，`bab … week-of-october-19` 的 `170-189` 档），与 GUIDE 第 8 节"地缘 0"一致，**吃单费为 0**。按 GUIDE 公式 `费=份数×费率×p×(1−p)`，费率 0 时费用 0；maker 亦 0（另有 `clobRewards`，见下）。
- **每笔成本 = 费 + 半个买卖价差**：以 `<170` 档为例，YES 价差 `0.16−0.127=0.033`，半价差 `0.0165/份`。上面 4.2 的 `+0.0682` 已按可成交的 NO 卖价（`1−YES bid`）算，即已跨过价差；若按中价成交则要再加半价差，故实际期望应打折看。
- **单笔能放多少**：`<170` 档 NO 挂 `0.873`、100 份 ≈ **87.3 USDT**；单 event 上限 200 USDT，两条海峡同时做也只到 400 USDT。
- **一个月多少次机会**：每周 2 个 event（Hormuz + Bab，2026-07-13 起每周都有；更早 Hormuz 也是每周一个）→ **约 8–9 个 event/月**。但真正会触发挂单的只有外侧档，多数周只有 0–2 档触发；回放里 Bab 草稿期 12 个事件有 9 个至少一档触发。
- **对 5,000 USDT 的年化贡献（第 2 轮粗算）**：只做 Bab，草稿期每美元投入 **+0.0094** × 单 event 上限 **200 USDT** × 每年约 **39** 次触发（52 周 × 9/12）÷ 5,000 = **1.5%**。这是**上限粗算，未由成交深度验证**：回放只有 1 份/档，200 USDT/event 是条目假设而不是实测容量；bootstrap 区间跨 0，且是税前、无滑点之外成本；不等于可稳定拿到的收益。
- **容量**：event 成交额（Gamma 自报，**未用成交明细复现**）Bab 12 个已关闭事件合计 **$265,080**、Hormuz 30 个（不含日期解析失败的 `mar-10-16`）合计 **$6,332,007**；open 的 Bab `week of october 19` `volume=13,595.37`、`liquidity=53,710.93`。**几百到几十万美元/event** 的量级，1,000 USDT 的专线额度放得下，但 5,000 USDT 放不满——赚的钱对总资金微不足道，这是本条的主要缺点。`volume` 是 Gamma 自报且会变（2026-10-21 Hormuz `week of october 19` 为 17,126.44；**2026-10-22 为 18,101.58，Bab 同周为 15,809.84、`liquidity=22,960.27`**），这里只作量级参考，未用成交明细复现。
- **流动性奖励（补贴，不是主收益）**：该市场 `clobRewards` 是**逐档（逐 leg）**字段，2026-10-20 快照的 5 档 `rewardsDailyRate` 依次为 **6/39/42/5/8**（`170-189` 档为 39；各档 `rewardsAmount=0`、`startDate=2026-10-20`、`endDate=2500-12-31`）、`rewardsMinSize=50`、`rewardsMaxSpread=8.5`；按 Q-score 规则（见 dot-032）`170-189` 档 $39/日由所有合格 maker 分。**2026-10-21/22 复核仍在逐档漂移（10-21 同日多次重抓见到 1/53/41/5/无、2/9/7/2/无、2/9/8/1/无；10-22 为 无/11/9/无/无，`rewardsMinSize` 在 20 与 50 之间混合）**，见 `notes/scheduler/scratch/H-quant-018/verify_sources_stdout.txt`；这条不靠它，只把它当噪声补贴，且奖励参数逐日可变。

## 风险

- **14 天兜底条款（最大风险）**：规则写明若数据 14 天内没发布，就按"此前最新已发布数据"结算。如果某周 PortWatch 断更，结算值可能根本不是我算的那个窗口，买 NO 的仓位会按错误窗口判。我 2026-10-20 看到的最新数据是 10-11，**当时已落后 9 天**；2026-10-21 复核最新已到 10-18（落后 3 天），说明这次发布恢复了，但条款本身仍在，不能把“这次没断”当成“不会断”。
- **事后修订**：7 个 MISMATCH（2026-03 至 05）说明"当期发布值"和"现在能取到的值"可能不同；规则只承认数据完整发布前的修订，所以**用今天的 PortWatch 反推历史结算是不可靠的**，这也是为什么我只用近 12 周、且把 25/25 的复算一致当作可用的边界。
- **状态切换**：Bab 全样本 405 周 min 173 / max 578，战前与战中差一倍以上；近 12 周虽然都落在 173–215，但一条"海峡重开/封锁"的新闻就能让分布整体平移，`p_i` 会同时全错。这既是收益来源，也是本金风险。
- **结算滞后占款**：`week of october 12` 的两个 event 在 2026-10-20（窗口已过两天）仍 `closed=false`、无结算；2026-10-21 复核 Bab 已结算、Hormuz 仍 open。加上 UMA 争议期，占款可能从 7 天拉到 10 天以上，年化会被摊薄。
- **小样本**：Laplace 后 `<170` 的公允值 0.059 完全来自平滑项（12 周里 0 次），真实概率可能是 3% 也可能是 12%；按 87.3 的 NO 成本算，只要真实概率 > 6.4% 这笔就是亏的（`0.873 < 1−p` ⇒ `p < 0.127` 才赚——实际要赚需要 `p<0.127−0.01=0.117`）。**这就是本条最薄的地方：安全垫只有 6.8 个点，而 12 周样本给不出这么细的分辨率。**
- **规则/口径**：`n_total` 我按五类船型之和理解（`n_container+n_dry_bulk+n_roro+n_general_cargo+n_tanker`），规则原文列的五类与之一致，但我只验证了总数一致（34/43 事件档位吻合，另 7 个不符、2 个无法比对），**没有逐日核对五类之和是否等于 `n_total`**，这一步未做。
- **平台**：多个同族 event `restricted=true`；negRisk 阶梯的赎回/转换有额外步骤；`clobRewards` 与 `feesEnabled` 逐市场可改。
- **不交易/不付费**：本条全部数据均来自公开 GET，未使用密钥，未下单。

## 改进了什么

并入 quant-012（地震周计数基准率）：同一机制「免费计数源的经验分布 vs 计数阶梯」，本条的关键差异变量是 0 吃单费（quant-012 为 0.05）、结算源存在事后修订与 9 天级发布滞后（2026-10-21 复核时已恢复至 3 天，但规则风险仍在；周内无部分信息、不能 nowcast）、档宽 20 对 sd 13.51。按 GUIDE §3.3，本条不主张独立“开新路”，只按补充计；**quant-012 是本机制的主条目，018 是它的补充**，不应再单独占一个待核名额（review c20261021-070001 第 1 条）。

## 门槛自查

1. **机制说得清：满足** — 付钱方是按地缘恐慌给外侧档出价的散户；量化证据是 2026-10-19 快照两个 open 阶梯的中价合计 1.010（Bab）与 1.1615（Hormuz；2026-10-21 复核已漂移），以及 Bab `<170` 档中价 0.1435 对 12 周经验值 0（Laplace 0.059）。谁付钱清楚了；"为什么持续"只有单点横截面证据。
2. **有免费数据能检验：满足（有条件）** — 结算源 IMF PortWatch 免费免密钥、2019 起有日度数据，我复算 43 个已关闭事件中 41 个可比对的里 34 个与结算档位一致（2026-07-13 起 25/25）；预言机结算结果也在 Gamma 免费可读。2026-10-20 复核已取到 43/43 个事件的首价与 34/43 的周起点价；2026-10-21 又补到同时点 data-api 成交价（24/43 事件全档有价）和 1 个 post-draft OOS 事件。但价格是已成交打印、不是完整盘口，历史深度缺失。
3. **小资金能做：资金门槛满足，可成交性未证实** — 87.3 USDT/档、200 USDT/event、本条专线 1,000 USDT，远低于单场所 2,500 与总资金 5,000；不加杠杆；NO 买单最大亏损就是本金。但按 PR #21，决策后 60 分钟内 Bab 12 个事件只有 1 个有成交（1 份，−0.92），决策时点按回放价成交没有证据（4.7）。
4. **不重复：不满足（作为独立条目）** — 2026-10-21 复核时 `grep -rl "pm_category: geopolitics" bots/*/entries/` 已能查到 `composer-004`、`dot-051` 与本条：板块**不再空白**，不能按“开新路”加分；其中 composer-004 与本条是同一 PortWatch 周转模板。更关键的是**机制同族于 quant-012（地震周计数基准率）**：同样是"免费计数源的经验分布 vs 计数阶梯"，差别只是计数源、费用和档宽。按 GUIDE §2 第 4 条和 §3.3，这属于变体/补充，**不能算独立的新收益来源**，所以作为独立条目门 4 不满足。与 dot C04（政治官宣与未结算窗口）、C10（截止日型时间衰减）、C11（新闻后过度反应）都不同：本条不依赖任何公告、不依赖截止日临近的时间价值、也不预测新闻后的修正方向。按主审判法，本条已按 `kind: supplement` 并入 quant-012。composer-004 的提交时间晚于本条（2026-10-20 06:50 +0200 vs composer 2026-10-21 08:57 +0800），按 GUIDE §3.3 先到先得，018 相对 composer-004 先到；但**本机制的主条目是 quant-012，quant-018 只按 quant-012 的补充**，不单独占待核名额。本条不主张独立开新路。
5. **扣成本后粗算够用：不确定（偏负，2026-10-21 真实成交价回放后）** — 吃单费 0；1¢ 基础成本下全样本 21 份 / 10 事件，份额中位 +0.2400/份、每美元 +0.0465，但事件中位仅 +0.0850、事件 5 胜 5 负，事件聚类 bootstrap 每美元 95% 区间 **[-0.216, +0.261]** 跨 0；草稿期 12 事件事件中位 **−0.1800**，5¢ 压力下每美元 **−0.0203**。唯一 post-draft OOS 事件 +0.5900（n=1）不能改变结论。回放产物见 `bots/quant/replay/quant-018/`，年化贡献粗算仅 **1.5%**（**上限粗算，未由成交深度验证**；1 份/档，200 USDT/event 是假设而非实测容量）。不足以宣称扣成本后稳定为正；按门 5 不应收录。另：以上价格均为 `T` 前最后一笔；决策后 60 分钟口径下 Bab 仅 1 笔成交、每份 −0.92（`bots/quant/notes/postdecision-fills-20261021/REPORT.md`）。
6. **两周内能检验：不满足** — 独立结果按 event 计；有触发成交的事件只有 **10 个 < 30**，同一时点全档都有成交价的事件也只有 **24/43**（Bab **5/12**），均低于 30；决策后 60 分钟内只有 **1/12** 个 Bab 事件可成交；前向两周只有约 4 个 event，不能补足。冻结标准 (3) 因此 **INSUFFICIENT**。这是本条不能收录的主要原因（`result: 不显著` 也是按这一条，而不是因为回放净收益为负）。
7. **出处可查：满足** — 2026-10-22 用 `notes/scheduler/scratch/H-quant-018/verify_sources.py` 重抓出处节的 **17/17 个外部 URL，全部 HTTP 200、0 FAIL**（stdout 见同目录 `verify_sources_stdout.txt`；较早一版只列 15 个，加入 OOS 事件与 data-api 成交后为 17 个）；另用 `verify_citations.py` 全文扫描 **25/25 项检查通过**（含正文里全部外部 URL、OOS 事件结算 `170-189`、data-api 成交字段、PortWatch 5,696 行 / 2,848 天 / 最新 2026-10-18、**19 个**本地引用路径存在、**5 个**冻结输入 sha1、8 个第 2 轮字段与 `SUMMARY.md` 一致；stdout `verify_citations_stdout.txt`）；回放输入与参数在 `bots/quant/replay/quant-018/SUMMARY.md`，可离线复跑；PortWatch 的 5,682 行、405 个完整周、12 周序列、34/7/2 的 MATCH/MISMATCH 明细、Brier 与 P&L 数字都是我自己脚本算的，全码附在 `notes/batch2-verification/quant-018.md` 与本轮 scratch；Gamma 的 `volume/liquidity` 标了"来源自报，未核实"；快照漂移（PortWatch 行数/最新日期、clobRewards、盘口）已照写。两个失败/未核实项（PortWatch 页面→服务的对应、3–5 月 MISMATCH 的解释）仍照写。

## 结论与建议

七条门槛里，作为**独立条目**只有 1/2/3/7 基本满足：**4 不满足**（与 quant-012 同机制、与 composer-004 同模板，只按 supplement 计）、**5 不确定且偏负**（份额中位为正但事件层不稳，5¢ 压力和决策后 60 分钟为负）、**6 不满足**（独立事件 10<30）。按 GUIDE §2“七条全部满足才收录”，本条**不应按收录处理**，也不应再按“待选区候选”占位；建议 integrator **降为草稿或并入 quant-012**，只作反证/补充（最多补充采纳 0.5），保留前向记录，并把 2026-10-12 的 post-draft OOS 事件继续跟踪。第 2 轮交付已按 GUIDE §2.1/§7 补齐：`evidence: 回放`（`bots/quant/replay/quant-018/` 可复跑）、`result: 不显著`（10 个独立事件 < 30，bootstrap 区间跨 0）、`variants: 4`（V1/V2 决策前回放 + V3/V4 决策后回放）、`window: 2026-07-20..2026-10-18`、`contribution: 1.5%`（上限粗算，未由成交深度验证）。这是**负/不显著证据**，不是可盈利证明。PR #21 的决策后 60 分钟复核（4.7）显示 Bab 只有 1 笔可成交（−0.92），11/12 个事件不可成交，可成交性/可执行性未证实。

按 review c20261021-070001 第 1 条和 c20261022-063202 的同机制/盘口问题，**建议 integrator 把本条降为草稿或并入 quant-012，不单独占待核名额**；quant-012 才是本机制的主条目。fixer 按本轮任务要求未改 `status`（仍 `待核`）与 `date`（仍 `2026-10-20`），只把正文里的降级建议和盘口快照写死，避免与 front matter 的差异被误读为“仍主张独立待核”。

## 出处

- `bots/quant/notes/postdecision-fills-20261021/REPORT.md`、`q018_strict.py`、`q018_strict.out`、`q018_strict_buckets.csv`（同目录）— 2026-10-21（PR #21 合并）— 已读（Bab：原口径 18 份中位 +0.24；STRICT 26 份中位 +0.23；STRICT60 仅 1 份 −0.92，11/12 事件不可成交）
- https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=500&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（100 个 event，3,988,406 字节）
- https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=500&closed=false&order=endDate&ascending=true — 访问 2026-10-20 — 已读（100 个 open event，4,390,404 字节）
- https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=100&closed=true&offset=100&order=endDate&ascending=false — 访问 2026-10-20 — 已读（第 2 页 100 个）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-5 — 访问 2026-10-20 — 已读（规则原文全文、5 档、结算 `190-209`、`volume=13097.774817`）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-19 — 访问 2026-10-20 — 已读（5 档 bid/ask、`feesEnabled=false`、逐档 `clobRewards` rate 6/39/42/5/8（`170-189` 档 39）、`rewardsMinSize=50`、`rewardsMaxSpread=8.5`；**2026-10-22 复访**：`<170` bid/ask=0.006/0.155，`volume=15,809.844682`、`liquidity=22,960.26523`，各档仍 `feesEnabled=false`）
- `bots/quant/notes/scheduler/audit/c20261020-170337-research.md` §2.2 — 访问 2026-10-20/22 — 已读（同日重抓 Bab `<170` bid/ask=0.024/0.333，说明 0.127/0.16 只是 2026-10-20 快照且 edge 已转负）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-the-strait-of-hormuz-week-of-october-19 — 访问 2026-10-20 — 已读（6 档 bid/ask、`volume=5539.661748`；**2026-10-22 复访**：中价合计 0.971、`volume=18,101.584663`、`liquidity=72,694.61991`）
- https://gamma-api.polymarket.com/public-search?q=how%20many%20ships%20transit&limit_per_type=100&events_status=all — 访问 2026-10-20 — 已读（47 个 `how-many-*` 同族 event 的 slug 与 endDate；**2026-10-22 复访仍 47 个，其中 44 个已关闭 = Hormuz 31 / Bab 13**，用于 43 个草稿期已关闭事件的枚举）
- https://gamma-api.polymarket.com/public-search?q=UKMTO&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（1 个 event：`how-many-ukmto-notices-october-1925`）
- https://gamma-api.polymarket.com/public-search?q=Strait%20of%20Hormuz&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（50 个 event，含月度均值模板）
- https://gamma-api.polymarket.com/public-search?q=Bab%20el-Mandeb&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（23 个 event）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services?f=json — 访问 2026-10-20 — 已读（服务清单里找到 `Daily_Chokepoints_Data`、`Daily_Ports_Data`）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0?f=json — 访问 2026-10-20 — 已读（字段 `date, portname, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, n_total`）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')&outFields=date,portname,n_total&returnGeometry=false&f=json&resultOffset=0&resultRecordCount=1000&orderByFields=date ASC — 访问 2026-10-20 — 已读（分页取全 **5,682 行**，每海峡 2,841 天，2019-01-01..2026-10-11）
- https://portwatch.imf.org/pages/6b1814d64903461b98144a6cc25eb79c — 访问 2026-10-20 — 部分（216,598 字节的 ArcGIS Hub 页面，**未找到指向日度表格的直接链接**；日度数据改经上条 ArcGIS 服务取得，对应关系未完全核实）
- https://clob.polymarket.com/prices-history?market=83323157431384565919039651171113228419822107706617450318634509280075717583619&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（Hormuz `week of october 5` 的 `25-29` 档有完整序列，`p` 从 0.255 到 0.405 等；其余事件多档返回空）
- GUIDE.md 第 2、7、8、10、11 节 — 访问 2026-10-20 — 已读（费用公式、地缘费率 0、七条门槛、分类代码）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z — 访问 2026-10-21 — 已读（post-draft OOS 事件，结算 `170-189`，5 档全部 `feesEnabled=false`）
- https://data-api.polymarket.com/trades?market=0xc3f0b47231b149f564840ae702749014a9f1a63c39d20375d505eba509f10039&limit=500&offset=0 — 访问 2026-10-21 — 已读（新 OOS 事件 `170-189` 档的逐笔成交；脚本按 conditionId 逐档分页，见 `tradable_backtest.py`）
- `bots/quant/notes/scheduler/scratch/H-quant-018/verify_sources_stdout.txt` — 访问 2026-10-22 — 已读（出处节 17 个外部 URL 全部 HTTP 200、0 FAIL；PortWatch 行数/最新日期、`clobRewards`、`volume` 漂移均记录）
- `bots/quant/notes/scheduler/scratch/H-quant-018/verify_citations_stdout.txt` — 访问 2026-10-22 — 已读（全文 25 项检查全部通过，含 19 个本地引用路径与 5 个冻结输入 sha1）
- `bots/quant/replay/quant-018/SUMMARY.md` — 访问 2026-10-22 — 已读（第 2 轮回放：参数、数据地址、4 个变体、独立事件数与全部结果）
- `bots/quant/replay/quant-018/stdout.txt` 与 `trades.csv` — 访问 2026-10-22 — 已读（`python3 replay.py` 逐字输出；66 份成交，4 个变体）
- `bots/quant/replay/quant-018/inputs/buckets_bab.csv`（sha1 `205f1fac…`）、`inputs/strict_bab.csv`（sha1 `f58e5073…`）与 `inputs/oos_bab_oct12.csv`（sha1 `420531cd…`）— 访问 2026-10-22 — 已读（冻结输入，来自 `notes/q018-paired/buckets.csv`、`notes/postdecision-fills-20261021/q018_strict_buckets.csv` 与 2026-10-21 现场 OOS 数字）
- `bots/quant/notes/postdecision-fills-20261021/q018_strict_buckets.csv`（sha1 `ae0c71bb…`）与 `q018_strict.out` — 访问 2026-10-22 — 已读（Bab STRICT 26 份 12 事件、STRICT60 1 份 −0.92；本回放 V3/V4 的冻结来源）
- `bots/quant/notes/scheduler/scratch/H-quant-018/tradable_backtest_stdout.txt` 与 `tradable_fills.csv` — 2026-10-21 — 已读（真实成交价 NO 回测，含 1 个 post-draft OOS；复用 `q018-paired/buckets.csv`）
- `bots/quant/notes/scheduler/scratch/H-quant-018/brier_start_check_stdout.txt` — 2026-10-21 — 已读（周起点价 Brier 0.7436 vs 模型 0.7747，复现 dot-051）
