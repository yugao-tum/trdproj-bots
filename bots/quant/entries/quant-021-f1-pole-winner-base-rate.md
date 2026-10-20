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
instruments: Polymarket 单站三件套：`<站名> Grand Prix: Driver Winner`（29 个车手二元）、`Driver Pole Position`（29 个）、`Driver Podium Finish`（23 个，非 negRisk）
venues: Polymarket
data: api.jolpi.ca Ergast 兼容 F1 接口（免费免密钥，1950 年起，本轮实取 2014–2026 全部 269 场排位+正赛）；Gamma/CLOB 公开接口（免费免密钥）；CLOB `prices-history` 对已关闭 F1 市场只返回最近约 1 个月的曲线（实测 18 个已关闭 2026 冠军 event 中只有 3 个有数据）
test_2w: 独立结果按「一个比赛周末」计，两周约 2–3 场（最近两个完整赛季各 24 站，本轮按季计数 2024:24、2025:24），拿不到 30 个；失败标准=杆位车手夺冠市场「价格−经验基率」的方向性毛收益中位≤0，或有效成交 <20 份
status: 草稿
confidence: 中
---

整理说明：本条所有基率都是我在 2026-10-20 从 `api.jolpi.ca` 当日拉取 2014–2026 全部排位+正赛后自己算的（脚本 `qpos2.py` 全文见文末 `notes/batch2-verification/quant-021.md`）；所有价格是同日 Gamma 快照。**没有做回测**：已关闭 F1 市场的价格历史只能取到最近约 1 个月，18 个已关闭 2026 冠军 event 里只有 3 个有曲线，样本 3 完全不足以验证 edge。

## 一句话

在 Polymarket 每站的 `Driver Winner` 市场，排位赛结束后用免费用时数据算出「这个起步位置历史夺冠率」，只在某车手夺冠卖价明显低于该基率时买 YES，持到 FIA 最终成绩公布（数小时到 1 天），不做站前预测。

## 钱从哪里来

付钱方是在单站冠军市场里按「车队强弱 + 上一站印象」出价的休闲玩家。F1 每站是一个**固定模板、每两周重复一次**的独立事件，同一批 29 个车手二元市场重开；排位赛（周六）到正赛（周日）之间只有十几小时，公开用时数据（排位圈速、FP 长距离）在排位结束后就已经全部免费可得，而 Polymarket 的 `Pole Position` 市场总成交额只有 **248.79 USD**（2026-10-20 Gamma 快照，美国站），说明这条信息链上几乎没有专业资金。**注意**：这是机制假设，不是已证实的收益来源——见证据节最后一段，最近 3 个有价格曲线的分站里，杆位车手的赛前价格是 0.63–0.675，已经**高于**长期基率 0.5576，也就是说「市场忘记定价杆位」这件事在本轮样本里没有出现。

## 规则

**市场模板与示例（Gamma `public-search?q=formula 1`，2026-10-20 已读）**：`tag_slug=f1` 已关闭 event 去重后共 401 个；按 slug 年份的 2026/2025 年度拆分我未能复现，故不列年度计数；按标题分类可复现的是 Winner 19、Pole 37、Podium 17（FP1/Sprint/其他 的精确分类未能复现）。当前未关闭的例子：

- `f1-united-states-grand-prix-winner-2026-10-25`（29 个市场，`negRisk=true`，volume 3,523.28，liquidity 82,670.55）
- `f1-united-states-grand-prix-driver-pole-position-2026-10-24`（29 个市场，volume 248.79，liquidity 12,211.34）
- `f1-united-states-grand-prix-driver-podium-2026-10-25`（23 个市场，`negRisk=false`，volume 202.69）
- 已关闭的例子：`f1-singapore-grand-prix-winner-2026-10-11`（volume 1,131,293.19；结算结果 Max Verstappen，`outcomePrices=["1","0"]`）

**结算规则原文要点（已读，`resolutionSource=https://www.formula1.com/en/results/2026/races`）**：

- Winner：「resolve in favor of the driver who is officially listed in first place in the Final Classification published by the FIA following the conclusion of the race」；「Disqualifications or changes made after the publication of the Final Classification will not affect market resolution」；取消或改期到 `Nov 1, 2026` 之后 → 结算为 “Other”。
- Pole：「the driver who is officially recognized by Formula 1 as having set the fastest time during the qualifying session」；「regardless of any subsequent penalties, disqualifications, or changes to the starting grid」——**即杆位市场按排位圈速结算，不按实际起步顺序**（这是与「杆位=第一个发车」的常见误解不同的地方）。
- Podium：「finishes within the top three positions in the official Final Classification」；若比赛永久取消 → 结算 50-50（Winner/Pole 是 “Other”）。
- 时间口径：无时区争议（成绩表为准），争议期按 UMA 常规流程，本次未查该 event 的 `umaBond`/`liveness`。

**交易规则（本条提案，未验证）**

1. 只在排位赛结束、FIA 官方排位成绩可读之后下单；站前不下单（站前只有 FP 数据，信息量不足，且本条的基率表本身不以练习赛为条件）。
2. 公允值：杆位车手取「按杆位差距分档的经验夺冠率」，其余车手取「按其排位名次分档的经验夺冠率」（表在证据节）。分档用 2014–2026 全部 269 场的**滚动前 3 年**样本重算（每年重算一次，避免用未来数据）。
3. 进场：`ask_i ≤ p_i − 0.05` 才买该车手 YES（5¢ 安全垫，写死，成交后不改）。
4. 只吃单买入、不做空；每站每车手 ≤100 份，单站合计 ≤200 份，同时在手 ≤2 站；总资金按 5,000 USDT 记，单场所 ≤2,500。
5. 出场：不主动平仓，持到最终成绩公布（赛后 30–60 分钟出 Final Classification，市场结算通常再晚数小时）。理由：平仓要再付一次吃单费和价差。
6. 熔断：若排位赛因故取消（冲刺赛周末的排位仍照常，但雨战排位可能延到周日早上）则本站不交易；若某站 `liquidity` 快照 < 1,000 USD 则跳过。

## 证据

### 1）基率：Ergast 兼容接口，我自己算的

数据：`https://api.jolpi.ca/ergast/f1/{season}/qualifying.json` 与 `/results.json`，`limit=100` 分页（该接口把 `limit` 上限压到 100，2024 年排位总行数 `total=479`），2014–2026 每年 5 页，去重后 **269 场**（2014:19、2015:19、2016:21、2017:20、2018:21、2019:21、2020:17、2021:22、2022:22、2023:22、2024:24、2025:24、2026:17）。

- **杆位者夺冠**：2014–2026 `150/269 = 0.5576`；2022–2026 `65/109 = 0.5963`；2026 单季 `12/17 = 0.7059`。
- **冠军的排位名次分布**（n=269）：P1 `150 (0.558)`、P2 `58 (0.216)`、P3 `30 (0.112)`、P4–6 `22 (0.082)`、P7–10 `7 (0.026)`、P11+ `2 (0.007)`。前三名起步覆盖 `238/269 = 0.885`。
- **按杆位差距分档的杆位夺冠率**（差距 = P1 与 P2 最佳圈速之差，秒）：`[0,0.05)` n=50 → `21 (0.420)`；`[0.05,0.20)` n=95 → `53 (0.558)`；`[0.20,0.50)` n=93 → `56 (0.602)`；`≥0.50` n=30 → `20 (0.667)`。**这是本条唯一有统计含量的定价输入**：杆位差距 <0.05s 时杆位者的夺冠率反而低于平均（0.420），差距 >0.5s 时高到 0.667。
- 口径与已知缺陷：`pole` = 排位成绩里 `position == 1` 的车手，缺失时退化为最佳圈速最快者；`margin` 用 `Q3/Q2/Q1` 中首个有成绩的圈速（不含 Q1/Q2 淘汰车的燃油与轮胎差异）；冲刺周末的「排位」在 Ergast 里是正赛排位，未与冲刺排位混用（未逐站核对，属已知近似）。

### 2）市场侧（Gamma 快照，2026-10-20，美国站）

| market | 市场数 | Verstappen bid/ask | 次热 bid/ask | ask 合计 | bid 合计 | volume |
|---|---|---|---|---|---|---|
| Driver Winner | 29 | 0.43 / 0.44 | Antonelli 0.23 / 0.29 | 7.4930 | 0.9460 | 3,523.28 |
| Driver Pole Position | 29 | 0.25 / 0.46 | Antonelli 0.11 / 0.40 | 13.5800 | 0.7700 | 248.79 |

- `ask 合计 7.4930` > 1 且 `bid 合计 0.9460` < 1（按相关市场的完整集方向看），**没有「买齐 29 档」或「卖齐 29 档」的套利**；杆位市场的 bid 合计只有 0.7700，说明这个盘子极薄。
- 杆位市场最优档价差 `0.46 − 0.25 = 0.21`，中价 0.355，**半价差 10.5¢ = 中价的 29.6%**——杆位市场只可能做 maker，做 taker 必亏。
- 冠军市场最优档价差 `0.44 − 0.43 = 0.01`，半价差 0.5¢。
- 两个市场**不能直接套利**：设 `P(win) = P(pole)·P(win|pole) + (1−P(pole))·P(win|¬pole)`，取 `P(win)=0.435`、`P(pole)=0.355`、`P(win|pole)=0.5963`（2022–2026 基率），得 `P(win|¬pole) = (0.435 − 0.355×0.5963)/0.645 = 0.3462`，低于历史「非杆位夺冠率」 1−0.5963 = 0.4037，故两价并存不矛盾。我算过这一步就是为了否掉「杆位价 × 基率 ≠ 冠军价」这种伪套利。

### 3）价格历史能取到多少（决定能不能做事后检验）

对 18 个已关闭的 2026 冠军 event 逐个取杆位车手 YES token 的 `prices-history?interval=max&fidelity=60`：

- 只有 3 个返回非空：`2026-09-26`（158 点）、`2026-10-04`（49 点）、`2026-10-11`（200 点）；其余 15 个（含 2026-09-13、2026-08-23 等）返回 `{"history":[]}`。
- 这 3 场的杆位车手赛前（正赛前 ≥10 分钟）最后价格是 **0.675 / 0.63 / 0.64**，实际 3 场杆位者全夺冠。
- 结论：**市场把杆位车手定在 0.63–0.675，高于长期基率 0.5576，也高于杆位差距 >0.2s 档的 0.602**。所以「按基率买杆位车手」在这个 3 场样本里没有 edge；真正的候选 edge 只在「杆位差距特别小（<0.05s）时市场是否仍然给 0.6+」这类条件分档上，而这一条我**没有样本**（3 场不够，且这 3 场的杆位差距未逐场核）。
- 例子：`f1-bahrain-grand-prix-winner-2026-10-04` 的 Verstappen token 曲线从 `p=0.26`（t=1790956829）走到 `p=0.9995`（t=1791129623），即赛前约 0.26，与他实际从杆位夺冠形成对比——但那是**练习/排位前**的早期价格，不能当赛前定价。

## 数据

- Ergast 兼容（免费、免密钥、无需注册）：`https://api.jolpi.ca/ergast/f1/{season}/qualifying.json?limit=100&offset=N`、`/results.json`；`limit` 上限 100，需按 `total` 分页。Ergast 原站 `ergast.com` 已停（本轮**未验证**，只用了 jolpi 镜像）。
- OpenF1（免费免密钥）：`https://api.openf1.org/v1/...`，用于练习赛长距离与分段计时；**本轮未取**，故不含其字段与覆盖范围的具体结论。
- Gamma（免费免密钥）：`/events?slug=...`（规则原文、`feeSchedule`、`clobRewards`、`bestBid/bestAsk`、`outcomePrices`）、`/public-search?q=...`、`/events?tag_slug=f1&closed=true&limit=100&offset=N`。
- CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max&fidelity=60`；已关闭 F1 市场约 1 个月内有效（实测 3/18），更早返回空。用 `startTs/endTs` 参数会 **HTTP 400**。
- 缺失：逐场 `qualifying` 的 Q1/Q2/Q3 分段与轮胎信息（Ergast 无）、练习赛圈速（未取 OpenF1）、历史盘口深度（无公开来源）。

## 两周内怎么检验

- **独立结果按「比赛周末」计**：同一站的 Winner / Pole / Podium 三个 event 共用一套排位与正赛成绩，只算 1 个结果；两周内 2026 赛季大约 2–3 站 → **2–3 个独立结果**，按 GUIDE 第 2 节第 6 条，本条**不可能在两周内拿到 30 个**，30 个结果需要约 12–15 站、即 3–4 个月。
- 两周内能做的事：(a) 每站记录排位成绩（jolpi）、杆位差距、各车手 Winner 市场 `bestBid/bestAsk` 与我方模型值；(b) 用 2014–2026 的 269 场做**滚动前 3 年**的分档表回算，比较「按分档表」与「按市场价」的 log loss（这一步不依赖 Polymarket 数据，可在数小时内完成，且是真正的 269 个独立结果）；(c) 前向记录真实成交。
- 失败标准（写死）：前向有效成交 ≥20 份后，已成交 YES 份额的**中位已实现毛利 ≤ 0**（毛利 = 票面 1.00 − 成交价，不含手续费）；或 269 场回算里分档表的 log loss **不优于**常数 0.5576。任一成立即判失败。

## 成本与容量

- **费用（Gamma 实取，非查表）**：三个示例市场每个都是 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`，与 GUIDE 第 8 节「体育 0.03–0.05」一致；`rebateRate=0.15` 即 maker 返佣为对手吃单费的 15%。Podium 市场另有一个 `clobRewards.rewardsDailyRate = 0.001`（USDC/日，量级可忽略）。
- 每份吃单费 `= 0.05 × p × (1−p)`：`p=0.44` → `0.05×0.44×0.56 = 0.01232`/份，占名义 `0.05×0.56 = 2.80%`；`p=0.675` → `0.05×0.675×0.325 = 0.01097`/份（占名义 1.63%）；`p=0.20` → `0.008`/份（占名义 4.00%）。
- **每笔成本 = 费 + 半个价差**：冠军市场最优档（0.43/0.44）半价差 0.005，合计 `0.01232 + 0.005 = 0.01732`/份 = 中价 0.435 的 **3.98%**。也就是说模型概率必须比市场价高约 **4 个百分点**才不亏——比我在规则里写死的 5¢ 安全垫略小，所以 5¢ 门槛是自洽的（5¢/0.435 = 11.5% 毛收益，扣 4% 剩 7.5%）。
- **容量**：美国站冠军市场总成交 3,523.28 USD、`liquidity` 82,670.55（Gamma 自报，未用成交明细复现）；已关闭新加坡站 1,131,293.19、巴林 652,176.36。**单站能吃的钱是几千到几十万美元量级，但这是整站全部车手市场的总和**，单一车手档的深度没有公开历史数据，只能在盘口上现读；本条 200 份/站的额度在 0.44 价上约 88 USDT，放进 2,500 USDT 单场所上限绰绰有余，5,000 USDT **根本放不满**。
- **机会频率**：最近两个完整赛季各 24 站 ≈ 2 站/月；每站只有「排位结束后到正赛」这十几小时窗口，实际可能只成交 1–2 档。

## 风险

- **本条的 edge 未被证实（最大风险）**：3 个有价格曲线样本显示市场给杆位车手 0.63–0.675，已经高于基率；若市场一直这么定价，按基率买不会有收益，只会付手续费。
- **排位到正赛信息滞后不对称**：我拿到的是同一份公开成绩，别人也一样；真正的先手是 OpenF1 实时流（本轮未取），而 Polymarket 的杆位市场成交量只有 248.79 USD，说明这条线上可能根本没有对手单可打。
- **决赛成绩口径**：Winner 按 FIA `Final Classification` 结算，且「公布之后的取消资格不影响结算」；但 FIA 有时把某车手标为 `DSQ` 后重排成绩，若发生在公布前，市场会跟着重排——判错方向的风险在我的基率表里没有体现（基率表用的是 Ergast 的 final position）。
- **规则兜底**：比赛取消 → Winner/Pole 结算 “Other”（我的 YES 全损）；Podium 结算 50-50。天气导致的延期还会让资金被占住数天到数周。
- **反相关于「杆位=第一个发车」的误解**：杆位市场按圈速结算，罚退不影响；如果我用「实际起步顺序」去推杆位市场就会系统性出错——本条只用杆位市场读价、不在其中下单，所以这个坑不影响主策略。
- **平台**：`restricted=true`（多个 F1 event 快照里都有），negRisk 转换/赎回操作有额外步骤；奖励池（0.001 USDC/日）可随时取消，不能当收入。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足（但只有一个方向性假设）** — 付钱方是单站模板里按车队强弱出价的休闲玩家，杆位市场 248.79 USD 的成交额说明专业资金几乎没进来；不过「市场忘记定价杆位」在 3 个有价格样本里被否掉了，所以机制成立的是「排位名次/杆位差距条件分档上的定价偏差」，不是「无脑买杆位」。
2. **有免费数据能检验：不确定** — 基率侧完整（269 场，2014–2026，免费免密钥，可复现）；**价格侧不足**：已关闭 F1 市场只有约 1 个月的价格历史（18 个已关闭 2026 冠军 event 中 3 个有曲线），拿不到 30 个历史价格结果。
3. **小资金能做：满足** — 200 份/站、≤2 站在手，按 0.44 价约 88 USDT/站，远低于 2,500 USDT 单场所与 5,000 总量；不加杠杆，最大亏损是本金。
4. **不重复：不确定** — 我查了 `known/KNOWN.md`（143 行，只有 `F-F1-bab/F-F1-dbeta/F-F1-lowvol` 三个加密因子，与 F1 无关）、`bots/*/CLAIMS.md`（只有 quant 自己 B18 一行，以及 B03 网球 Elo、B08 足球平局）、`bots/*/entries/`（无 F1/赛车条目）。与 quant-006（网球 Elo）同为「外部评分模型 vs PM 价格」，但变量与数据源不同（排位圈速与杆位差距 vs 对局 Elo）；与 dot-032（流动性奖励）无重合。最终是否算变体请主审判断。
5. **扣成本后粗算够用：不满足** — 冠军市场吃单成本约 `3.98%` 名义（0.01232 费 + 0.005 半价差，p=0.435），需要模型比市场高约 4¢；而现有 3 个价格样本显示市场定价 0.63–0.675 高于基率 0.5576，**没有观测到正 EV**。`observed_net_return = null`，`backtest_count = 0`（只表示没有回测，不表示收益为 0）。
6. **两周内能检验：不满足** — 独立结果按比赛周末计，两周只有 2–3 个（最近两个完整赛季各 24 站），30 个结果需 3–4 个月；只有「269 场分档表 vs 常数」的离线校准能在两周内做完，但那不是价格侧检验。
7. **出处可查：满足（部分为「未查到」）** — 每个基率数字都写了公式、样本期与中间量（150/269、65/109、12/17、各档 n 与 wins），脚本全文贴在文末；Gamma 的 volume/liquidity 标了「来源自报，未核实」；`limit` 上限 100、`startTs` 参数 400、15/18 个已关闭市场无价格曲线这些失败也照写；OpenF1 字段与 Ergast 原站状态**未查**，故不引用。

## 出处

- https://api.jolpi.ca/ergast/f1/2025/results/1.json — 访问 2026-10-20 — 已读（`"limit":"30"`、`"total":"24"`，确认接口结构与分页语义）
- https://api.jolpi.ca/ergast/f1/2024/qualifying.json — 访问 2026-10-20 — 已读（`"limit":"100"`、`"total":"479"`，确认 `limit` 被压到 100，需 offset 分页）
- https://api.jolpi.ca/ergast/f1/{2014..2026}/qualifying.json?limit=100&offset=N 与 /results.json?limit=100&offset=N — 访问 2026-10-20 — 已读（去重后 269 场；150/269 杆位夺冠等全部基率数字的计算源）
- https://gamma-api.polymarket.com/public-search?q=formula%201&limit_per_type=20&events_status=all — 访问 2026-10-20 — 已读（50 个 event，含 slug `f1-united-states-grand-prix-winner-2026-10-25` 等）
- https://gamma-api.polymarket.com/public-search?q=grand%20prix&limit_per_type=100&events_status=all — 访问 2026-10-20 — 已读（Pole/Podium/Sprint/Constructor 模板清单）
- https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-winner-2026-10-25 — 访问 2026-10-20 — 已读（规则原文全文、29 市场 bid/ask、`feeSchedule`、`negRisk=true`、volume 3,523.28、liquidity 82,670.55）
- https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-driver-pole-position-2026-10-24 — 访问 2026-10-20 — 已读（杆位结算原文「regardless of any subsequent penalties…」、Verstappen 0.25/0.46、volume 248.79）
- https://gamma-api.polymarket.com/events?slug=f1-united-states-grand-prix-driver-podium-2026-10-25 — 访问 2026-10-20 — 已读（podium 结算原文、23 市场、`negRisk=false`、`clobRewards.rewardsDailyRate=0.001`）
- https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset=0..400 — 访问 2026-10-20 — 已读（401 个唯一已关闭 event；按 slug 年份的年度拆分未能复现，按标题的 Winner/Pole/Podium 计数可复现）
- https://gamma-api.polymarket.com/events?slug=f1-singapore-grand-prix-winner-2026-10-11 — 访问 2026-10-20 — 已读（Verstappen `outcomePrices=["1","0"]`，volume 1,131,293.19）
- https://gamma-api.polymarket.com/events?slug=f1-bahrain-grand-prix-winner-2026-10-04 — 访问 2026-10-20 — 已读（Verstappen token 曲线 `p=0.26`→`0.9995`）
- https://clob.polymarket.com/prices-history?market=28558391061191296576456870322949545965070312914289181555918414954825561771030&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（Gasly 市场 200 点，说明已关闭市场并非全部为空；首点 0.495 存疑，见 `notes/batch2-verification/quant-021.md`）
- https://clob.polymarket.com/prices-history?market=<巴林站 Verstappen 市场 token>&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（49 点，`p=0.26`→`0.9995`）；同 token 加 `startTs/endTs` 参数返回 HTTP 400，不能作为数据源

---
