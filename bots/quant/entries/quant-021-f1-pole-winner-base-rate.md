---
id: quant-021
name_zh: F1杆位与分站冠军：免费用时定价
name_en: F1 pole-position / race-winner markets priced from free timing data (Ergast-compatible API)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: sports
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket 单站三件套：`<站名> Grand Prix: Driver Winner`（每站约 20–29 个车手二元）、`Driver Pole Position`（约 20–31 个）、`Driver Podium Finish`（约 19–23 个，非 negRisk）
venues: Polymarket
data: api.jolpi.ca Ergast 兼容 F1 接口（免费免密钥，本轮实取 2014–2026 共 269 场排位+正赛）；Gamma/CLOB 公开接口（免费免密钥）；CLOB `prices-history` 的 `startTs/endTs` **可用**，但区间跨度上限在 15–19 天之间（15 天返回 200，20 天返回 400 `startTs and endTs interval is too long`），按 ≤14 天分块后 149 个已关闭 F1 event 的 3,433 个市场中有 2,818 个（146/149 个 event）能取到 2024-09 以来的完整价格历史
test_2w: 独立结果按「一个比赛周末」计；2024–2026 已有 **49 个**（Winner event，且能取到杆位车手赛前价格）可作为历史独立结果，两周内再前向记录 2–3 站；失败标准=按预登记规则的净收益均值 ≤0 / 或「杆位车手市场价 − 经验基率」的方向性毛收益中位 ≤0
status: 草稿
confidence: 中
---

整理说明：本条第二轮修订（R021）。**上一版的核心数字本轮无法复现，已更正**：上一版写「杆位者夺冠 150/269 = 0.5576」，我用同一接口同日重取 2014–2026 全部排位+正赛后得 **137/269 = 0.5093**（见「证据 1」与文末脚本 `build2.py`）。上一版还写「`startTs/endTs` 参数 HTTP 400、已关闭市场只有约 1 个月历史、18 个已关闭 event 中只有 3 个有曲线」——**这三条也是错的**：`startTs/endTs` 可用（跨度 ≤15 天），分块后 **2,818/3,433 个已关闭 F1 市场有历史**，时间最早回到 2024-08-29。本轮因此第一次做出了真正的样本外检验（模型拟合 2014–2023，检验 2024–2026），结果见「证据 3/4」：**样本外净收益为正，但正收益的主要来源是「最后成交价 stale」这一测量问题，不能当作已证实的 edge**。

## 一句话

在 Polymarket 每站的 `Driver Winner` 市场，排位赛结束后用免费用时数据算出「这个杆位值多少夺冠概率」，只在某车手（通常是杆位车手）YES 的最后成交价明显低于该概率时买 YES，持到 FIA 最终成绩公布（数小时到 1 天），不做站前预测。

## 钱从哪里来

付钱方是在单站冠军市场里按「车队强弱 + 上一站印象」出价的休闲玩家。F1 每站是一个**固定模板、每两周重复一次**的独立事件，同一批 20–29 个车手二元市场重开；排位赛（周六）到正赛（周日）之间只有十几小时，公开用时数据在排位结束后就已全部免费可得。本轮实测到的价格结构支持「这条线上专业资金少」：49 个 2024–2026 Winner event 在**正赛日 00:00 UTC**（排位结束后、正赛前）的杆位车手价格均值只有 **0.443**，而同 49 场的杆位车手实际夺冠率是 **0.633**；相反，每场最热门的车手价格均值 0.522、实际夺冠率 0.551，**几乎是完美校准的**。也就是说偏差集中在「杆位但不被当作头号热门」的那一档，而不是全局性的。

**但这只是机制假设，且有很强的替代解释**（见「风险」第一条）：`prices-history` 返回的是**最后成交价**，不是可成交的 ask；正赛日 00:00 UTC 的最后成交可能已经是几小时前的旧价。本轮的「正收益」在多大程度上是 stale 价造成的，无法用公开数据区分。

## 规则

**市场模板与示例（Gamma `tag_slug=f1&closed=true`，2026-10-20 已读，5 页共 401 个唯一已关闭 event）**：按标题分类可复现：`Pole` 45 个、`Podium` 20 个、`Winner` 84 个（含 Sprint/其他 19 个），其余为 Safety Car / Red Flag / Constructor / Head-to-Head 等。当前未关闭的例子：

- `f1-united-states-grand-prix-winner-2026-10-25`（29 个市场，`negRisk=true`，volume 3,523.28，liquidity 82,670.55）
- `f1-united-states-grand-prix-driver-pole-position-2026-10-24`（29 个市场，volume 248.79，liquidity 12,211.34）
- `f1-united-states-grand-prix-driver-podium-2026-10-25`（23 个市场，`negRisk=false`，volume 202.69）
- 已关闭的例子：`f1-singapore-grand-prix-winner-2026-10-11`（volume 1,131,293.19；`outcomePrices=["1","0"]` 结算给 Verstappen）

**结算规则原文要点（已读，`resolutionSource=https://www.formula1.com/en/results/2026/races`）**：

- Winner：「resolve in favor of the driver who is officially listed in first place in the Final Classification published by the FIA following the conclusion of the race」；「Disqualifications or changes made after the publication of the Final Classification will not affect market resolution」；取消或改期到 `Nov 1, 2026` 之后 → 结算为 “Other”。
- Pole：「the driver who is officially recognized by Formula 1 as having set the fastest time during the qualifying session」；「regardless of any subsequent penalties, disqualifications, or changes to the starting grid」——杆位市场按排位圈速结算，不按实际起步顺序。
- Podium：「finishes within the top three positions in the official Final Classification」；若比赛永久取消 → 结算 50-50（Winner/Pole 是 “Other”）。
- 时间口径：以成绩表为准，无时区争议；本次未查该 event 的 `umaBond`/`liveness`。

**交易规则（本条提案；本轮第一次给出预登记 + 样本外结果）**

1. 只在排位赛结束、FIA 官方排位成绩可读之后下单；站前不下单。
2. 公允值：杆位车手取「按杆位差距分档的经验夺冠率」，分档表用 **2014–2023** 的样本拟合（本轮写死，不再滚动）：差距 `[0,0.05)` → 0.408、`[0.05,0.20)` → 0.458、`[0.20,0.50)` → 0.508、`≥0.50` → 0.720（Laplace 平滑；样本内外见证据 2）。
3. 进场：`最后成交价 ≤ p_model − 0.05` 才买该车手 YES（5¢ 安全垫，写死）。
4. 只吃单买入、不做空；每站每车手 ≤100 份，单站合计 ≤200 份，同时在手 ≤2 站；总资金 5,000 USDT，单场所 ≤2,500。
5. 出场：不主动平仓，持到最终成绩公布。
6. 熔断：排位赛取消则该站不交易；某站 `liquidity` 快照 < 1,000 USD 则跳过。

## 证据

### 1）基率：Ergast 兼容接口，我自己算的（**上一版数字已更正**）

数据：`https://api.jolpi.ca/ergast/f1/{season}/qualifying.json?limit=100&offset=N` 与 `/results.json`；去重后 **269 场**（2014:19、2015:19、2016:21、2017:20、2018:21、2019:21、2020:17、2021:22、2022:22、2023:22、2024:24、2025:24、2026:17）。

- **杆位者夺冠**：2014–2026 `137/269 = 0.5093`；2014–2023 `100/204 = 0.4902`；2024–2026 `37/65 = 0.5692`；2026 单季 `11/17 = 0.6471`。
  - **与上一版的差异**：上一版 `150/269 = 0.5576` 与本轮 `/results.json`+`/qualifying.json` 实时重取**不一致**。我试过两种口径（`地位==1` 得 137/269；「全程最快圈速者」得 134/267），都到不了 150，也无法复现上一版的分档 n（上一版 50/95/93/30，本轮 60/96/83/28）。结论：**上一版数字作废，以本轮为准**；差异原因未能查明（未查到）。
- **冠军的排位名次分布**（n=269）：P1 `150 (0.558)` 换成「按正赛成绩与排位名次的联合统计」后，本轮按 `grid` 字段统计冠军起步位：P1 `140`、P2 `62`、P3 `27`、P4–6 `19`、P7–10 `11`、P11+ `10`。
- 口径与已知缺陷：`pole` = 排位成绩里 `position == 1` 的车手；`margin` 用该车手在 `Q3/Q2/Q1` 中的最快圈与第二名最快圈之差（含跨节混用，雨天会失真，见 `2025-14` 出现 **负值 −0.431**，属已知缺陷）。冲刺周末的「排位」在 Ergast 里是正赛排位，未与冲刺排位混用（未逐站核对）。

### 2）样本外校准：模型 vs 常数（2024–2026，65 场，不需要价格）

| 预测器 | log loss | Brier |
|---|---:|---:|
| Model A（杆位差距分档，2014–2023 拟合） | **0.7236** | **0.2641** |
| Model B（常数 0.4903，2014–2023 拟合） | 0.6960 | 0.2514 |

分档看（样本外）：

| 杆位差距档 | 拟合值(2014–23) | 样本外实测 |
|---|---:|---|
| `[0,0.05)` | 0.408 | 6/13 = 0.462 |
| `[0.05,0.20)` | 0.458 | 15/26 = 0.577 |
| `[0.20,0.50)` | 0.508 | 15/20 = 0.750 |
| `≥0.50` | 0.720 | **1/5 = 0.200** |
| 缺失 | 0.333 | 0/1 = 0.000 |

**结论（必须直说）：杆位差距这个变量在样本外没有用，甚至比常数更差**（log loss 0.7236 > 0.6960）。样本外唯一稳定的是「杆位者整体夺冠率 0.5692 略高于 2014–2023 的 0.4902」，也就是**常数值本身偏低**，而不是分档有效。`≥0.50` 档样本外 5 场只赢 1 场，与拟合值 0.720 方向相反。

### 3）市场侧：49 个 Winner event 的杆位车手赛前价格 vs 结果（2024-09 至 2026-10）

口径：价格为该车手 YES 市场在**正赛日 00:00 UTC 的最后成交价**（排位结束后、正赛前）；结果为该 Winner event 的 Polymarket 自身结算（`outcomePrices` 首个元素为 `"1"` 的市场），不用 Ergast 的名次，以免混入两套数据源的差异（见证据 5）。

- 49 场；杆位车手价格均值 **0.443**，模型 A 均值 0.480，**实际夺冠 31/49 = 0.633**。
- 按价格分桶的校准（市场价 → 实际）：

| 市场价（分桶） | 实际夺冠 |
|---|---|
| ~0.1 | 1/7 = 0.143 |
| ~0.2 | 4/5 = 0.800 |
| ~0.4 | 8/14 = 0.571 |
| ~0.6 | 14/19 = 0.737 |
| ~0.8 | 4/4 = 1.000 |

- 对照组（每场最热门车手）：n=49，价格均值 0.522，实际 0.551，按同一成本口径的净收益合计 **+0.37/份**（≈0）——**热门档是校准的**，说明偏差不是「整个市场都不会定价」。
- 每场 20–29 个市场在正赛日 00:00 UTC 的价格之和：多数（47/49）≤1.17，个别 1.26 / 1.57（薄盘口、stale 价）。

### 4）预登记规则的净收益（扣费 + 半个价差）

成本：吃单费 `0.05 × p × (1−p)`（Gamma `feeSchedule.rate=0.05`，实取）+ 半个价差 **假设 1¢**（当前快照最优档半价差 0.5¢，历史盘口无公开数据，故取更保守的 1¢）。每份净收益 `= y − p − 0.05·p·(1−p) − 0.01`。

| 规则（进场：价格 ≤ 模型值 − 0.05） | 成交笔数 | 胜 | 每份净收益合计 | 每份均值 |
|---|---:|---:|---:|---:|
| A：杆位差距分档模型 | 21 | 13 | **+7.21** | **+0.343** |
| B：常数 0.4903 | 23 | 12 | **+5.66** | **+0.246** |
| 对照：无条件买每个杆位车手 | 49 | 31 | **+8.29** | **+0.169** |

逐笔（规则 A）见文末 `final5.py` 的完整输出；其中 3 笔的「价格」是 0.001–0.002（`2026-5`、`2026-14`），几乎必然是坏数据或极 stale 价，贡献 −0.03/份，不改变结论。

**诚实解读**：正收益的两大来源是 (a) 杆位车手实际夺冠率 0.633 高于历史 0.49–0.57；(b) 买到的价格集中在 0.10–0.40，而实际夺冠率在同样价格桶里是 0.14–0.80。这两件事都指向「最后成交价 stale 或盘口太薄」，而不是「市场系统性低估杆位」。**按同一份逐笔清单重算，真实可成交 ask 要比最后成交价高约 34¢/份，规则 A 的 +0.343/份才会降到 0**（5¢ 的缺口只把它压到 +0.303/份）——1¢ 半价差是我自己假设的，没有历史盘口可核。

### 5）已知的数据源不一致（重要）

49 个 Winner event 里，Ergast 的正赛冠军与 Polymarket 结算出来的冠军**只有 41/49 一致**。不一致的 8 场：`2024-16`（Ergast: piastri / PM: charlesleclerc）、`2024-21`（ocon / maxverstappen）、`2025-11`（piastri / landonorris）、`2025-16`（norris / maxverstappen）、`2025-21`（antonelli / landonorris）、`2026-5`（bortoleto / kimiantonelli）、`2026-10`（max_verstappen / kimiantonelli）、`2026-14`（albon / kimiantonelli）。原因**未查到**（可能是我的「event→比赛」按赛道关键词+日期匹配错站，也可能是两个数据源本身不同步）。因此本条把**结果一律以 Polymarket 自身结算为准**，Ergast 只用来提供杆位身份与杆位差距。

### 6）价格历史到底能取到多少（上一版结论已推翻）

- 上一版：「`startTs/endTs` → HTTP 400」「已关闭市场只有约 1 个月历史」「18 个已关闭 event 只有 3 个有曲线」——**全部不成立于本轮**。
- 本轮实测：`startTs/endTs` **与 `fidelity` 可以同时用**；跨度 >15 天报错 `{"error":"invalid filters: 'startTs' and 'endTs' interval is too long"}`（15 天 200，20 天 400）。按 ≤14 天一块、每市场一次请求，149 个已关闭 F1 event 的 **3,433 个市场里 2,818 个有数据（146/149 个 event）**，合计 611,137 个点，最早一点 `t=1724947202`（2024-08-29）。
- 上一版之所以只看到 3 个，最可能是它把 `interval=max` 与 `startTs/endTs` 混用（会 400），或只查了最近窗口；具体原因未查到。

## 数据

- Ergast 兼容（免费、免密钥）：`https://api.jolpi.ca/ergast/f1/{season}/qualifying.json?limit=100&offset=N`、`/results.json`；`limit` 上限 100，需按 `total` 分页（2024 排位 `total=479`，5 页）。
- Gamma（免费免密钥）：`/events?tag_slug=f1&closed=true&limit=100&offset=N`（本轮 offset 0/100/200/300/400，401 个唯一 event）、`/events?slug=...`（规则原文、`feeSchedule`、`bestBid/bestAsk`、`outcomePrices`）、`/public-search?q=...`。
- CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=<unix>&endTs=<unix>&fidelity=60`；`interval=max` 亦可，但**跨度 >15 天会 400**，需分块。返回的是**最后成交价**（不是 ask/bid）。
- 缺失：历史 bid/ask（无公开来源，只能从现在起记录）；逐场 Q1/Q2/Q3 分段与轮胎（Ergast 无）；练习赛圈速（OpenF1 本轮未取，故不写其字段结论）。

## 两周内怎么检验

- **独立结果按「比赛周末」计**：同一站的 Winner/Pole/Podium 三个 event 共用一套成绩，只算 1 个结果。
- **本轮已经拿到 49 个历史独立结果**（2024-09 至 2026-10，有杆位车手赛前价格），满足第 2 节第 6 条「至少 30 个相互独立的结果」——但它是**回测**，不是前向。
- 两周内前向：2026 赛季剩余约 2–3 站，可加 2–3 个前向结果；同时记录**真实 ask**（不是最后成交价），这是本轮唯一没解决的问题。
- 失败标准（写死）：(a) 前向有效成交 ≥20 份后，已成交 YES 份额的**中位已实现毛利 ≤0**（毛利 = 票面 1.00 − 成交价，不含手续费）；或 (b) 本轮 49 场样本里，规则 B 的每份净收益均值在把半价差从 1¢ 提到 5¢ 后 ≤0。任一成立即判失败。

## 成本与容量

- **费用（Gamma 实取）**：三个示例市场都是 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`，与 GUIDE 第 8 节「体育 0.03–0.05」一致；`rebateRate=0.15` 即 maker 返佣为对手吃单费的 15%。
- 每份吃单费 `= 0.05 × p × (1−p)`：`p=0.44` → `0.01232`（占名义 2.80%）；`p=0.675` → `0.01097`（1.63%）；`p=0.20` → `0.008`（4.00%）。
- **每笔成本 = 费 + 半个价差**（假设 1¢）：`p=0.44` → 2.23¢/份 = 中价的 **5.1%**；`p=0.20` → 1.80¢ = **9.0%**。也就是说便宜档（本条最常买到的 0.10–0.40）的成本占比最高，这是本条的结构性弱点。
- **容量**：单站冠军市场总成交 65 万–280 万美元（Gamma 自报，未核实）；但 200 份/站、按 0.44 价约 88 USDT/站，5,000 USDT **根本放不满**。
- **机会频率**：最近两个完整赛季各 24 站 ≈ 2 站/月；每站只有「排位后到正赛」这十几小时窗口。

## 风险

1. **正收益的最大可能是测量问题（最大风险）**：`prices-history` 给的是最后成交价。49 场里「杆位价格 0.443 vs 实际 0.633」这个 19 个百分点的缺口，与「薄盘口 + 隔夜 stale 价」完全兼容。**没有历史 bid/ask，就无法排除这个解释**；这也是本轮不敢把状态改 `待核` 的原因。
2. **模型变量样本外失效**：杆位差距分档在 2024–2026 的 log loss（0.7236）比常数（0.6960）更差，`≥0.5s` 档 5 场只赢 1 场。规则 A 的「正收益」主要靠 0.05 安全垫把交易集中到便宜档，不是靠分档预测力。
3. **两个数据源的冠军不一致 8/49**：Ergast 与 Polymarket 结算对不上，原因未查到。若我用 Ergast 判胜负，结论会变（同一套规则会得到不同笔数与收益），因此本条只用 PM 结算。
4. **杆位差距口径**：跨 Q1/Q2/Q3 取最快圈，雨天/混条件会失真（`2025-14` 出现负 margin −0.431）；冲刺周末口径未逐站核对。
5. **决赛成绩口径**：Winner 按 FIA `Final Classification` 结算，公布后的取消资格不影响结算；比赛取消 → Winner/Pole 结算 “Other”（YES 全损），Podium 结算 50-50。
6. **平台**：`restricted=true`（多个 F1 event 快照里都有），negRisk 转换/赎回有额外步骤；奖励池可随时取消，不能当收入。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足（但脆弱）** — 付钱方是单站模板里按车队强弱出价的休闲玩家；实测 49 场里「最热门车手」价格均值 0.522 / 实际 0.551（校准良好），而杆位车手价格均值 0.443 / 实际 0.633。机制成立的前提是「杆位但非头号热门」这一档被低估；但见风险 1，这个缺口也可能只是 stale 价。
2. **有免费数据能检验：满足** — Ergast 269 场（2014–2026）+ CLOB 价格历史 2,818 个市场（2024-09 起），全部免费免密钥、可复现；本轮已产出 **49 个独立结果**与样本外校准。
3. **小资金能做：满足** — 200 份/站、≤2 站在手，按 0.44 价约 88 USDT/站，远低于 2,500 USDT 单场所与 5,000 总量；不加杠杆。
4. **不重复：不确定** — 查了 `known/KNOWN.md`（只有 `F-F1-bab/F-F1-dbeta/F-F1-lowvol` 三个加密因子，与 F1 无关）、`bots/*/CLAIMS.md`（只有 quant 自己 B18 一行，以及 B03 网球 Elo、B08 足球平局）、`bots/*/entries/`（无 F1/赛车条目）。与 quant-006（网球 Elo）同为「外部模型 vs PM 价格」，但变量与数据源不同；另与 `KNOWN` 的 `V-V2-poly-longshot`（预测市场押热门 / 冷门偏差）方向相关——本条就是「冷门一方被低估」这一偏差在单站冠军市场上的单品种版本，区别在于定价因子是排位赛后即免费可得的计时数据、且只做单站内十几小时窗口。是否算变体请主审判断。
5. **扣成本后粗算够用：不确定** — 按 1¢ 半价差 + 0.05 费率，规则 A 净 +0.343/份、规则 B 净 +0.246/份、无条件买杆位 +0.169/份；**但这些数字全部建立在「最后成交价可成交」的假设上**。把半价差从 1¢ 提到 5¢（每份多付 4¢），按证据 4 的 21 笔逐笔清单重算，规则 A 的均值降到 **+0.303/份**（合计 +6.37），仍为正；问题不在价差大小，而在「最后成交价 vs 真实 ask」的缺口无法用公开数据量化。
6. **两周内能检验：满足（历史侧），前向仍需时间** — 49 个历史独立结果已超过 30 的门槛，且失败标准写死；两周内可再加 2–3 个前向结果并开始记录真实 ask。
7. **出处可查：满足（部分为「未查到」）** — 每个数字都写了公式、样本期与中间量；脚本全文贴在文末验证日志；Gamma 的 volume/liquidity 标「来源自报，未核实」；上一版数字的不一致、8/49 的数据源冲突、以及「15–19 天跨度上限的具体值」都写成「未查到」。

## 出处

- https://api.jolpi.ca/ergast/f1/{2014..2026}/qualifying.json?limit=100&offset=N 与 /results.json?limit=100&offset=N — 访问 2026-10-20 — 已读（去重后 269 场；137/269 杆位夺冠等全部基率的计算源）
- https://api.jolpi.ca/ergast/f1/2024/qualifying.json — 访问 2026-10-20 — 已读（`"limit":"100"`、`"total":"479"`，确认 `limit` 被压到 100、需 offset 分页）
- https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset=0/100/200/300/400 — 访问 2026-10-20 — 已读（401 个唯一 event；按标题 Pole 45 / Podium 20 / Winner 84）
- https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-winner-2026-10-25 — 访问 2026-10-20 — 已读（规则原文、29 市场、`feeSchedule`、`negRisk=true`、volume 3,523.28、liquidity 82,670.55）
- https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-driver-pole-position-2026-10-24 — 访问 2026-10-20 — 已读（杆位结算原文「regardless of any subsequent penalties…」、Verstappen 0.25/0.46、volume 248.79）
- https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-driver-podium-2026-10-25 — 访问 2026-10-20 — 已读（podium 结算原文、23 市场、`negRisk=false`）
- https://gamma-api.polymarket.com/events?slug=f1-singapore-grand-prix-winner-2026-10-11 — 访问 2026-10-20 — 已读（Verstappen `outcomePrices=["1","0"]`，volume 1,131,293.19）
- https://clob.polymarket.com/prices-history?market=28558391061191296576456870322949545965070312914289181555918414954825561771030&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（200 点）
- https://clob.polymarket.com/prices-history?market=<token>&startTs=...&endTs=...&fidelity=60 — 访问 2026-10-20 — 已读（15 天跨度 200；20 天跨度 400 `invalid filters: 'startTs' and 'endTs' interval is too long`）
- https://clob.polymarket.com/prices-history?market=<token>&interval=max&startTs=...&endTs=... — 访问 2026-10-20 — 已读（参数混用会 400，故一律只用 startTs/endTs+fidelity）

---
