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
test_2w: 独立结果按 weekly event 计（不按档）；历史侧 43 个已关闭事件的价格检验已于 2026-10-20 完成，两周内只需再前向记录约 4 个；失败标准是已成交 NO 份额的中位已实现毛利≤0，或两周成交<20 份，或同一批事件上基准率 Brier 差于市场价
status: 待核
confidence: 低
---

整理说明：本条的板块调研、模板计数、PortWatch 复算、费用与盘口数字都是我在 2026-10-20 本会话用 curl/urllib 现场取的（无密钥、无登录、未交易）；脚本 `pw_weekly.py`、`pw_verify.py`、`pw_calib.py` 全码附在文末 `notes/batch2-verification/quant-018.md`。**没有做收益回测**：已关闭市场的逐档价格历史只有 6 个事件可取全，只能做 6 个事件的小样本校准，不能当盈利证明。2026-10-20 复核已补做 43 个已关闭事件的价格侧历史检验，见“证据 4.4”与 PR #4。

## 一句话

在 Polymarket 地缘板块的「本周某海峡通行次数（transit calls）落在哪一档」周度阶梯上，用 IMF PortWatch 同一份免费日度数据算出的近 12 周经验分布当公允值；只在外侧档（`<170`、`230+`）明显被高估时挂 maker 买 NO，持有到 UMA 结算（约 7–9 天），不做 Hormuz，因为它的分布宽到没有基准率可言。

## 钱从哪里来

付钱给你的是**把外侧档按"危机还会升级"来出价的散户**。这条模板的结算值不是新闻、不是民调、不是官方口径的"某方是否宣布"，而是 PortWatch 的一串日度计数：区间内所有日子的通行次数加总。它持续存在的理由是：档位边界由平台按近期水平设定（Bab 的 `170-189 / 190-209 / 210-229` 每档只有 20 次宽，Hormuz 九月底起每档只有 5 次宽），而 2026-10-19 两个 open 市场的中价合计分别是 **Bab 1.010、Hormuz 1.1615**（我按 Gamma 的 bid/ask 中价加总），也就是外侧档合计被系统性多付。这不是套利：十条腿的卖价合计 1.408（Hormuz）根本买不齐，收益只能来自"报价挂在那里被情绪单打中"。

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

说明：`closed=true` 的 `limit=500` 被服务端截到 **100 条/页**，我取了两页共 **200 个已关闭 event**（`endDate` 2026-09-01 至 2027-12-31，含未到期但已被标 closed 的），加上 `closed=false` 的 **100 个 open event**，样本 300 个；这不是板块全量，属于**抽样**，所以上表是"样本内计数"，不是全站总数。**唯一同时满足"≥30 个独立历史结果 + 免费可计数结算源"的是周度海峡通行计数模板**（47 个 event，其中 **43 个已关闭**：Hormuz 31 / Bab 12），所以选它。月度均值模板只有 6 个（两个搜索里 `avgpt-of-ships-*` / `avg-of-ships-*` 按 slug 去重的 union）、UKMTO 只有 1 个，都不够 30。

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
3. 触发：某档 `1-p_i ≥ 该档 NO 的可成交卖价 + 0.01` 才挂 maker 买 NO（`0.01` 为安全垫，成交前写死）。以 2026-10-20 快照的 `<170` 档为例：YES `bestBid=0.127 / bestAsk=0.16`，故 NO 卖价 `1-0.127=0.873`，公允 NO `1-0.0588=0.9412`，价差 `+0.0682/份`。
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

可执行的一侧（不是中价）：`<170` 的 YES `bestAsk=0.16`、`bestBid=0.127`，买 NO 需付 `0.873`，公允 NO `0.9412`，**每份 +0.0682**；按占用资金折 `0.0682/0.873 = +7.8%`，占款约 7 天（`endDate=2026-10-26T03:59Z`，另加发布与结算滞后）。`230+` 的 NO 卖价 `1-0.028=0.972` 已经高于公允 `0.9412`，**同一算式的 EV 是 −0.031/份，不挂**。这是模型算术，不是实测。

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
| 周起点价子集 | 34 | 0.7747 | 0.8093 | +0.0346 | 0.585 | 0.5623 | 19/34 | 0.6076 |
| MATCH-only | 34 | 0.7576 | 0.7998 | +0.0422 | 0.715 | 0.4797 | 20/34 | 0.3915 |
| 严格周聚类 | 31 周 | — | — | +0.0464 | 0.984 | 0.3329 | 15/31 | — |

**Bab 交易 P&L（只做 Bab，NO 按周起点价成交；缺失时首价回退）**：纯周起点价口径 **n=29，NO 胜 22，中位毛利 +0.2250/份，总毛利 +0.7970，总投入 21.2030，每美元投入 P&L +0.0376，命中率 0.7586**；含首价回退 **n=32，NO 胜 25，中位毛利 +0.2325/份，总毛利 +1.5120，总投入 23.4880，每美元投入 P&L +0.0644，命中率 0.7812**。手续费按地缘费率 0，已实现毛利含亏损份额。

**诚实解读**：

- 失败标准 (1) **PASS**：周起点价口径 n=29，中位毛利 +0.2250/份 > 0；含首价回退 n=32，中位 +0.2325/份，同样为正。
- 失败标准 (3) 只在“全部 43 个事件”上 **PASS**（0.7658 vs 0.8060，差 +0.0402），但**不显著**（t=0.815，p=0.4198；符号检验 p=0.5424），且优势全部来自 Hormuz（+0.0770）；**Bab 子集 n=12 < 30，模型反而更差（−0.0548），应读作 INSUFFICIENT**。因此 (3) 的 PASS 不能当作 Bab 策略的校准证据。
- 价格侧数据是 CLOB `prices-history` 的**最后成交价（fidelity=60 的小时级抽样）**，不是可执行盘口；历史深度与真实买卖价差取不到，1¢ 半价差是预先假设。因此上述交易 P&L 只能当“方向与量级”的证据，不是可复制的收益证明。

## 同时点可成交价配对检验

2026-10-20 补做（PR #8，完整脚本、逐事件与逐档表见 `bots/quant/notes/q018-paired/REPORT.md` 与 `run_output.txt`）：只用 data-api 在事件窗口起点 T 的 `[T−24h, T]` 内的真实成交价（同一时点、可成交近似），不再混用首价与周起点价。覆盖 **24/43** 个已关闭事件全档有价（Hormuz 19/31、Bab 5/12）。

- 冻结标准 (1)：**PASS** — Bab 主口径 **n=18** 份，NO 胜 13，中位毛利 **+0.2400/份**、中位净利 **+0.2400/份**。
- 冻结标准 (3)：**INSUFFICIENT** — 同时点价格完整事件仅 **24 < 30**。
- 总体判定：**INSUFFICIENT**。

同样的数据也说明**此前的优势没有在同时点可成交价下复现**：全部事件 Brier 模型 0.7047 vs 市场 0.9318（n=24，原始价未归一化），但按档归一化后市场 0.7408、差仅 **+0.0360**（t=0.428，p=0.6729），Bab 子集 n=5 为 0.7471 vs 0.7710，均不显著；Bab 交易在事件层总净利 **+0.1216**、每事件中位净利 **−0.1800**、每美元投入 **+0.0094**、事件命中率 **0.4444**；5¢ 压力下 n=15、总净利 **−0.2284**、每美元 **−0.0203**。因此不能把旧报告的 Brier 优势或 Bab 交易经济性当作已复现的证据。

另一条中性旁证：dot 的补充条目 `bots/dot/entries/dot-051-strait-count-paired-cash-supplement.md` 在相同事件上用 start 价重算，方向与此一致（该条目写的是 start 价 Brier **0.743627407** 优于模型 **0.774672321**）。

## 数据

- **IMF PortWatch（本条核心，免费、免密钥、无需注册）**：ArcGIS FeatureServer `https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query`，字段 `date, portname, n_total, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, capacity...`；`where=portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')`；单页上限 1,000 行（`exceededTransferLimit=true`），需 `resultOffset` 翻页。覆盖 **2019-01-01 起**；我 2026-10-20 抓时最大 `date` 是 **2026-10-11**。
- **发布节奏（我观察到的，不是官方说明）**：结算规则里指定的那个 PortWatch 页面 `https://portwatch.imf.org/pages/6b1814d64903461b98144a6cc25eb79c` 我在 2026-10-20 抓到 216,598 字节的 ArcGIS Hub 页面，但**页面 HTML 里没有直接的表格链接**（条目 id 只有一个 logo 的 `fe7fbd7489ec425d8c415e7ad3ef01da`），所以日度数据我是经 ArcGIS 服务取的，不是经这个页面点的；这条"页面 = 服务"的对应关系**未完全核实**。观察到的事实：2026-10-20 时最新日度数据是 2026-10-11，而 `week of October 12`（10/12–10/18）的事件在 Gamma 里仍是 `closed=false`、无结算——**本周的计数在周内完全不可见**，这一点和"已发生未结算"类策略相反，也决定了本条不能做周内 nowcast。
- **Polymarket Gamma（免费免密钥）**：`events?slug=<event slug>`（规则原文、`outcomePrices`、`bestBid/bestAsk`、`feesEnabled`、`clobRewards`、`negRisk`）；`events?tag_slug=geopolitics&closed=true|false`（板块普查）；`public-search?q=how many ships transit&limit_per_type=100&events_status=all`（同族清单）。
- **CLOB（免费免密钥）**：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`；原稿只覆盖 6 个事件（Hormuz `week of october 5` 的 `25-29` 档有完整序列，其余无成交档返回空）；2026-10-20 复核改用 `startTs/endTs` 分段后，43/43 个事件有首价、34/43 有周起点价，见“证据 4.4”。
- **缺失且必须承认**：每条策略所需的"事件当天的盘口"取不到（CLOB 只给价格序列，不给历史深度）；逐笔成交本次未取（data-api 每个市场约最近 2 万笔）；PortWatch 的历史版本（3–5 月当时发布值）取不到，所以那 7 个 MISMATCH 无法解释。

## 两周内怎么检验

- **独立结果按 event 计，不按档、不按市场**：一个周度 event 的 5–6 个档共享同一个 PortWatch 计数，算 1 个结果；同一周两条海峡共用同一份源、同一驱动（地区冲突），按严口径也算 1 个，宽口径算 2 个。
- **历史侧（已完成，2026-10-20）**：43 个已关闭事件的价格侧检验已做完——首价完整 43/43、周起点价完整 34/43，Brier 与 Bab 交易 P&L 见“证据 4.4”。结论是标准 (1) PASS，标准 (3) 只在全部 43 个事件上 PASS 且不显著、Bab 子集 n=12 INSUFFICIENT 且更差；历史侧不再需要补数。
- **前向侧**：每周 2 个 event（两海峡），两周 4 个，凑不到 30；只能当"先看成交"的小样本。
- 每天记录：PortWatch 当日新发布的 `date, portname, n_total`；各档 `bestBid/bestAsk/outcomePrices`；我的挂单、成交、库存。
- **失败标准（写死，事后不改）**：
  1. 已成交 NO 份额的**中位已实现毛利 ≤ 0**（毛利 = 票面 1.00 − 成交价，不含未成交挂单）；
  2. 或两周内成交份额 < 20 份（判"容量失败"，同样进待选区）；
  3. 或补全的 30 个历史事件上，基准率的平均 Brier **不优于**市场价首价（当前 6 个事件上是 0.7646 vs 0.7962，方向对但样本不足）。
- 不允许的自我安慰：不能把"挂单没成交"当正结果；不能在 6 个事件上说"已验证"。

## 成本与容量

- **费用**：该族市场 Gamma 返回 `feesEnabled=false`、`feeSchedule=null`（2026-10-20 快照，`bab … week-of-october-19` 的 `170-189` 档），与 GUIDE 第 8 节"地缘 0"一致，**吃单费为 0**。按 GUIDE 公式 `费=份数×费率×p×(1−p)`，费率 0 时费用 0；maker 亦 0（另有 `clobRewards`，见下）。
- **每笔成本 = 费 + 半个买卖价差**：以 `<170` 档为例，YES 价差 `0.16−0.127=0.033`，半价差 `0.0165/份`。上面 4.2 的 `+0.0682` 已按可成交的 NO 卖价（`1−YES bid`）算，即已跨过价差；若按中价成交则要再加半价差，故实际期望应打折看。
- **单笔能放多少**：`<170` 档 NO 挂 `0.873`、100 份 ≈ **87.3 USDT**；单 event 上限 200 USDT，两条海峡同时做也只到 400 USDT。
- **一个月多少次机会**：每周 2 个 event（Hormuz + Bab，2026-07-13 起每周都有；更早 Hormuz 也是每周一个）→ **约 8–9 个 event/月**。但真正会触发挂单的只有外侧档，多数周只有 0–2 档触发。
- **容量**：event 成交额（Gamma 自报，**未用成交明细复现**）Bab 12 个已关闭事件合计 **$265,080**、Hormuz 30 个（不含日期解析失败的 `mar-10-16`）合计 **$6,332,007**；open 的 Bab `week of october 19` `volume=13,595.37`、`liquidity=53,710.93`。**几百到几十万美元/event** 的量级，1,000 USDT 的专线额度放得下，但 5,000 USDT 放不满——赚的钱对总资金微不足道，这是本条的主要缺点。
- **流动性奖励（补贴，不是主收益）**：该市场 `clobRewards` 是**逐档（逐 leg）**字段，5 档 `rewardsDailyRate` 依次为 **6/39/42/5/8**（`170-189` 档为 39；各档 `rewardsAmount=0`、`startDate=2026-10-20`、`endDate=2500-12-31`）、`rewardsMinSize=50`、`rewardsMaxSpread=8.5`；按 Q-score 规则（见 dot-032）`170-189` 档 $39/日由所有合格 maker 分。这条不靠它，只把它当噪声补贴。

## 风险

- **14 天兜底条款（最大风险）**：规则写明若数据 14 天内没发布，就按"此前最新已发布数据"结算。如果某周 PortWatch 断更，结算值可能根本不是我算的那个窗口，买 NO 的仓位会按错误窗口判。我 2026-10-20 看到的最新数据是 10-11，**已落后 9 天**，说明这条渠道确实可能断更。
- **事后修订**：7 个 MISMATCH（2026-03 至 05）说明"当期发布值"和"现在能取到的值"可能不同；规则只承认数据完整发布前的修订，所以**用今天的 PortWatch 反推历史结算是不可靠的**，这也是为什么我只用近 12 周、且把 25/25 的复算一致当作可用的边界。
- **状态切换**：Bab 全样本 405 周 min 173 / max 578，战前与战中差一倍以上；近 12 周虽然都落在 173–215，但一条"海峡重开/封锁"的新闻就能让分布整体平移，`p_i` 会同时全错。这既是收益来源，也是本金风险。
- **结算滞后占款**：`week of october 12` 的两个 event 在 2026-10-20（窗口已过两天）仍 `closed=false`、无结算；加上 UMA 争议期，占款可能从 7 天拉到 10 天以上，年化会被摊薄。
- **小样本**：Laplace 后 `<170` 的公允值 0.059 完全来自平滑项（12 周里 0 次），真实概率可能是 3% 也可能是 12%；按 87.3 的 NO 成本算，只要真实概率 > 6.4% 这笔就是亏的（`0.873 < 1−p` ⇒ `p < 0.127` 才赚——实际要赚需要 `p<0.127−0.01=0.117`）。**这就是本条最薄的地方：安全垫只有 6.8 个点，而 12 周样本给不出这么细的分辨率。**
- **规则/口径**：`n_total` 我按五类船型之和理解（`n_container+n_dry_bulk+n_roro+n_general_cargo+n_tanker`），规则原文列的五类与之一致，但我只验证了总数一致（34/43 事件档位吻合，另 7 个不符、2 个无法比对），**没有逐日核对五类之和是否等于 `n_total`**，这一步未做。
- **平台**：多个同族 event `restricted=true`；negRisk 阶梯的赎回/转换有额外步骤；`clobRewards` 与 `feesEnabled` 逐市场可改。
- **不交易/不付费**：本条全部数据均来自公开 GET，未使用密钥，未下单。

## 改进了什么

并入 quant-012（地震周计数基准率）：同一机制「免费计数源的经验分布 vs 计数阶梯」，本条的关键差异变量是 0 吃单费（quant-012 为 0.05）、结算源存在事后修订与 9 天级发布滞后（周内无部分信息、不能 nowcast）、档宽 20 对 sd 13.51。

## 门槛自查

1. **机制说得清：满足** — 付钱方是按地缘恐慌给外侧档出价的散户；量化证据是两个 open 阶梯的中价合计 1.010（Bab）与 1.1615（Hormuz），以及 Bab `<170` 档中价 0.1435 对 12 周经验值 0（Laplace 0.059）。谁付钱清楚了；"为什么持续"只有单点横截面证据。
2. **有免费数据能检验：满足（有条件）** — 结算源 IMF PortWatch 免费免密钥、2019 起有日度数据，我复算 43 个已关闭事件中 41 个可比对的里 34 个与结算档位一致（2026-07-13 起 25/25）；预言机结算结果也在 Gamma 免费可读。2026-10-20 复核已取到 43/43 个事件的首价与 34/43 的周起点价；但价格是最后成交价、不是可执行盘口，历史深度缺失。
3. **小资金能做：满足** — 87.3 USDT/档、200 USDT/event、本条专线 1,000 USDT，远低于单场所 2,500 与总资金 5,000；不加杠杆；NO 买单最大亏损就是本金。
4. **不重复：不确定** — 本仓库里 `pm_category: geopolitics` 的条目为 **0 条**（`grep -rl "pm_category: geopolitics" bots/*/entries/` 无输出），所以板块是新的。但**机制同族于 quant-012（地震周计数基准率）**：同样是"免费计数源的经验分布 vs 计数阶梯"。真正的差别是：这里吃单费为 0（quant-012 是 0.05）、结算源存在**事后修订**与 9 天级发布滞后（所以周内无任何部分信息，不能做 nowcast，只能做纯预测）、档宽 20 对 sd 13.51 的量级。与 dot C04（政治官宣与未结算窗口）、C10（截止日型时间衰减）、C11（新闻后过度反应）都不同：本条不依赖任何公告、不依赖截止日临近的时间价值、也不预测新闻后的修正方向。按主审判法，本条已按 `kind: supplement` 并入 quant-012。
5. **扣成本后粗算够用：不确定（2026-10-20 同时点检验后）** — 吃单费 0；同时点可成交价下 Bab 主口径 n=18、中位净利 +0.2400/份，但事件层总净利 +0.1216、每事件中位净利 −0.1800、每美元投入 +0.0094，5¢ 压力下每美元 −0.0203，且同时点完整事件仅 24/43（Bab 5/12）；不足以宣称扣成本后稳定为正。原稿：模型期望 `+0.0682/份 = +7.8%/7 天`，43 个事件历史检验 Bab 交易 P&L 中位 +0.2250/份（n=29，周起点价），但 Brier 在 Bab 子集为 −0.0548（n=12，模型更差），且价格是最后成交价不是可执行 ask。
6. **两周内能检验：不满足（同时点口径）** — 独立结果按 event 计；43 个已关闭事件虽够 30，但要求同一时点全档都有成交价时只有 **24/43**（Bab **5/12**），低于 30，冻结标准 (3) 因此 **INSUFFICIENT**；前向两周也只有约 4 个 event，不能补足。
7. **出处可查：满足** — 每个数字都有 URL + 访问日期 + 取数方法；PortWatch 的 5,682 行、405 个完整周、12 周序列、34/7/2 的 MATCH/MISMATCH 明细、Brier 数字都是我自己脚本算的，全码附在 `notes/batch2-verification/quant-018.md`；Gamma 的 `volume/liquidity` 标了"来源自报，未核实"；两个失败/未核实项（PortWatch 页面→服务的对应、3–5 月 MISMATCH 的解释）都照写。

## 出处

- https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=500&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（100 个 event，3,988,406 字节）
- https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=500&closed=false&order=endDate&ascending=true — 访问 2026-10-20 — 已读（100 个 open event，4,390,404 字节）
- https://gamma-api.polymarket.com/events?tag_slug=geopolitics&limit=100&closed=true&offset=100&order=endDate&ascending=false — 访问 2026-10-20 — 已读（第 2 页 100 个）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-5 — 访问 2026-10-20 — 已读（规则原文全文、5 档、结算 `190-209`、`volume=13097.774817`）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-19 — 访问 2026-10-20 — 已读（5 档 bid/ask、`feesEnabled=false`、逐档 `clobRewards` rate 6/39/42/5/8（`170-189` 档 39）、`rewardsMinSize=50`、`rewardsMaxSpread=8.5`）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-the-strait-of-hormuz-week-of-october-19 — 访问 2026-10-20 — 已读（6 档 bid/ask、`volume=5539.661748`）
- https://gamma-api.polymarket.com/public-search?q=how%20many%20ships%20transit&limit_per_type=100&events_status=all — 访问 2026-10-20 — 已读（47 个 `how-many-*` 同族 event 的 slug 与 endDate，用于 43 个已关闭事件的枚举）
- https://gamma-api.polymarket.com/public-search?q=UKMTO&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（1 个 event：`how-many-ukmto-notices-october-1925`）
- https://gamma-api.polymarket.com/public-search?q=Strait%20of%20Hormuz&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（50 个 event，含月度均值模板）
- https://gamma-api.polymarket.com/public-search?q=Bab%20el-Mandeb&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（23 个 event）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services?f=json — 访问 2026-10-20 — 已读（服务清单里找到 `Daily_Chokepoints_Data`、`Daily_Ports_Data`）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0?f=json — 访问 2026-10-20 — 已读（字段 `date, portname, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, n_total`）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')&outFields=date,portname,n_total&returnGeometry=false&f=json&resultOffset=0&resultRecordCount=1000&orderByFields=date ASC — 访问 2026-10-20 — 已读（分页取全 **5,682 行**，每海峡 2,841 天，2019-01-01..2026-10-11）
- https://portwatch.imf.org/pages/6b1814d64903461b98144a6cc25eb79c — 访问 2026-10-20 — 部分（216,598 字节的 ArcGIS Hub 页面，**未找到指向日度表格的直接链接**；日度数据改经上条 ArcGIS 服务取得，对应关系未完全核实）
- https://clob.polymarket.com/prices-history?market=83323157431384565919039651171113228419822107706617450318634509280075717583619&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（Hormuz `week of october 5` 的 `25-29` 档有完整序列，`p` 从 0.255 到 0.405 等；其余事件多档返回空）
- GUIDE.md 第 2、7、8、10、11 节 — 访问 2026-10-20 — 已读（费用公式、地缘费率 0、七条门槛、分类代码）
