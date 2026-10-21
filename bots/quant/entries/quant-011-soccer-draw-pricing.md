---
id: quant-011
name_zh: 足球三向盘平局基准率检验
name_en: Soccer 3-way draw market: base rate vs price bucket
bot: quant
date: 2026-10-20
market: polymarket
pm_category: sports
kind: new
improves: -
category: S
return_type: direction
instruments: 足球比赛三向事件（主胜、平局、客胜各一个独立 Yes/No 市场，同一 event 下）
venues: Polymarket
data: football-data.co.uk E0/I1/SP1/D1/F1 CSV 2017/18–2026/27（赔率+赛果，免费免密钥）；Gamma closed events + data-api 逐笔成交（免费免密钥；已闭合平局市场的成交可回溯）；CLOB prices-history 只作参考、不当成交价
test_2w: 每场足球比赛算 1 个独立结果（按 match 不按市场数）；历史回放已完成：主窗口 161 个独立触发（≥30），已按写死标准判 FAIL；若改做前向，按回放触发率约 74 场/年（两周约 2.8 个触发），凑不到 30，失败标准 = 扣吃单费与半价差后的净收益中位数 ≤ 0。
status: 草稿
confidence: 中
evidence: 回放
result: 负
slot: -
variants: 3
variants_ext: -
window: 2024-08-16..2026-10-19
max_dd: 44.8%（已实现，按比赛日排序，非盯市）
contribution: -16.4%
---

> **2026-10-20 降为草稿（撤回第 1 轮复核）**：按 `bots/quant/notes/q011-hist/REPORT.md`（PR #9）的历史可成交价回测（data-api 已闭合市场成交 + football-data 赛果），主窗口 `[T−6h, T]` 共 **161 场 triggered（≥30）**，每份净收益中位数 **−0.2389**、每美元投入 **−22.82%**、命中率 **18.6%**，触发了本条预先写死的失败标准（≥30 笔且中位数 ≤0）→ **FAIL**；敏感性窗口 `[T−24h, T−1h]` 中位数同为 **−0.2389**、每美元 **−3.21%**，总体仍为负。本条原称“Polymarket 历史平局价格不可得、只能前向记录”，该缺口已被 data-api 的 closed 市场成交记录补上；门槛 5、6 因此改写。正文以下其余内容保留原稿。
> **2026-10-21 第 2 轮回放（结论：应 DROP）**：回放已按 GUIDE §2.1 收进 `bots/quant/replay/quant-011/`（脚本、`params.json`、数据 URL、`SUMMARY.md`、`trades.csv`），并在 2026-10-21 用 data-api 逐笔成交重跑。五个联赛共 2,090 个带平局市场的已闭合 event，匹配 football-data **2,019/2,090 = 96.6%**，其中 1,986 场主窗口有成交打印；平局结算与 `FTR` **2,019/2,019 = 100.0%** 一致。主窗口 **161 场触发**（≥30），每份净收益中位 **−0.2389**、每美元投入 **−22.82%**、命中率 **18.6%**；敏感性窗口 **164 场**、每美元 **−3.21%**；新增 `[T−1h,T]` 新鲜度窗口 **151 场**、每美元 **−26.03%**。把吃单费降到 0 仍 **−19.01%**，连 1¢ 半价差也去掉、直接用打印价仍 **−15.33%**。三个窗口没有一个是正的，负结论不依赖费用假设。**因此本条应丢弃（DROP），不值得再花两周前向记录。** 原 `q011-hist/REPORT.md` 里“匹配 1,987 场”与“2,019/2,090”自相矛盾，以重跑的 **2,019** 为准。另：`bots/quant/forward/quant-011/PLAN.md` 已在 2026-10-21 登记（2026-10-22 起 14 天），但 `ledger.csv` 目前只有表头、没有结果；鉴于回放三个窗口全负，建议操作员**不要开始或取消**这份前向，不要把名额和时间花在这条上（本 worker 未改动 `forward/` 任何文件）。


判断说明：本条原稿是规则 + 费用 + 历史基准率的筛查稿，当时**没有跑过 Polymarket 回测**，因为 CLOB 的价格历史不能当成交价、公开检索也没有逐场平局盘口。该缺口已由 data-api 的已闭合市场逐笔成交补上：第 2 轮回放（见“证据 0”）在真实成交价上得到负结果，所以本条不再只是“可检验的假设”，而是一个**已被历史回放否定的假设**。CSV 上算出的偏差方向在两个联赛里相反（见“证据 1”），这一点仍保留作背景。

## 一句话

在 Polymarket 足球比赛的“平局”Yes/No 市场里，用 football-data.co.uk 的历史赔率桶（同一平局隐含概率区间）的实际平局频率作为基准率；当盘口卖价明显低于该桶基准率、且价差够窄时买入平局 Yes，持有到结算。

## 钱从哪里来

假设的付款方是**在平局档位上定价低于历史基准率的对手方**（把平局价格压得过低的挂单者/吃单者）。这属于行为偏差类收益：如果读者/做市方系统性低估平局，或把“大球队比赛”当成必胜叙事，平局 Yes 就会便宜。**这条机制目前没有被本文的证据证实**：本文算出的偏差在英超为正、在意甲为负（见“证据”），所以现在只能算“待检验的偏差”，不能算“已确认的收入来源”。平台本身不付钱给这条策略；体育盘吃单要付费（费率 0.05），所以偏差必须大于费用才有钱。

## 规则

- 结构：一场比赛是一个 event，下面**三个独立二元市场**，各带 Yes/No 两侧。示例 event `epl-new-eve-2026-11-02`（Newcastle United FC vs. Everton FC）下有 `-new`（"Will Newcastle United FC win on 2026-11-02?"）、`-draw`（"Will Newcastle United FC vs. Everton FC end in a draw?"）、`-eve` 三个市场，`negRisk=true`，标签为 `sports, games, soccer, premier-league, EPL`。所以“平局 Yes”和“主胜 No”不是同一张合约，不能用它们互相当对冲。
- 90 分钟口径（原文）："This market refers only to the outcome within the first 90 minutes of regular play plus stoppage time." 即**常规 90 分钟 + 补时，不含加时和点球**，与 football-data.co.uk 的 FTR（全场 90 分钟赛果）口径一致。
- 取消/改期（原文）："If the game is postponed, this market will remain open until the game has been completed."；"If the game is canceled entirely, with no make-up game, this market will resolve \"Yes\"."（**平局市场取消算 Yes**），同 event 的主胜/客胜市场取消算 "No"。即取消风险对平局买方是**有利**的，对三向合计不是零和。
- 结算数据源（原文）："The primary resolution source for this market is the official statistics of the event as recognized by the governing body or event organizers."；官方 2 小时内未公布最终统计，则用 Flashscore，再退到 Sofascore，再退到 "a consensus of credible reporting"；"Revisions to officially declared final scores made after market resolution will not be accounted for"。
- 缺数据的兜底（原文）："If no acceptable data is available within 24 hours of the event's conclusion, this market will resolve 50-50, or to \"Draw\" where applicable." 对平局市场，"where applicable" 是否等于直接算 Yes 原文未写清 —— 记为**规则歧义**，不当作套利机会。
- 进出场（本稿拟定）：只在比赛开赛前 ≥1 小时、盘口 bestAsk ≤ 0.30 且价差 ≤ 0.02 时，用**限价吃单**买入平局 Yes，价格 ≤ 该桶基准率 − 成本缓冲（见“成本与容量”）；每场最多一注，持有到结算（不做日内来回，避免二次付费）；单注 ≤ 50 USDT，未结算总敞口 ≤ 500 USDT，单场所（Polymarket）总资金 ≤ 2,500 USDT。
- 结算源与自己数据的口径差：football-data 的 FTR 是 90 分钟含补时的最终比分，和上面规则一致；但比赛被腰斩/改判时 football-data 可能保留原比分而 Polymarket 走 24 小时兜底条款 —— 这类样本在检验时单独剔除并计数。

## 证据

### 0. 第 2 轮真实成交价回放（2026-10-21，决定性证据）

- 产物：`bots/quant/replay/quant-011/SUMMARY.md`（汇总）、`run_replay.py`（主脚本）、`summarize.py`（离线汇总）、`params.json`（全部参数）、`data_urls.md`（数据地址）、`trades.csv`（201 行触发并集）；stdout 在 `bots/quant/notes/scheduler/scratch/P-quant-011/`（`run_replay.stdout.txt`、`summarize_from_replay.stdout.txt`、`verify_sources.stdout.txt`）。
- 成交价：**data-api 逐笔成交**（`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`），不是 CLOB `prices-history`。决策时点 `T = kickoff − 1h`；取窗口内最后一笔 YES 成交打印，NO 打印按 `1−p` 换成 YES；可执行 ask 近似为 **last YES print + 0.01**（1¢ 半价差 / 一个 tick）；窗口内无打印 = unpriced，不填单。没有用晚于 `T` 的打印。
- 数据：Gamma closed events keyset（按 EPL / serie-a / la-liga / bundesliga / ligue-1 枚举）+ data-api 成交 + football-data 2017/18–2026/27。被评估的 Polymarket 已闭合比赛为 **2024-08-16..2026-10-19**（本条是 Polymarket，不适用 GUIDE §9 的 crypto 2022–2024 开发窗；窗口如实写进字段 `window`）；基准率只用**严格早于该比赛赛季**的 football-data 赛季（expanding walk-forward），n≥30，不足回退五联赛合并同桶。
- 成本：体育 taker `0.05`，每份 `fee = 0.05 × ask × (1−ask)`；1¢ 半价差已含在 ask 内，不重复扣。
- 匹配与结算：2,090 个带平局市场的 closed event，匹配 football-data **2,019（96.6%）**，69 个未匹配（改期、2026/27 新升班马/队名差异）；1,986 场主窗口有成交打印；平局结算与 `FTR` **2,019/2,019 = 100.0%** 一致。

| 变体 | 窗口 | 触发（独立比赛） | 每份净收益中位 | 每美元投入净收益 | 命中率 | 年化贡献（5,000 USDT） |
|---|---|---:|---:|---:|---:|---:|
| V1 主 | `[T−6h,T]` | **161** | **−0.2389** | **−22.82%** | 18.6% | **−16.4%** |
| V2 敏感性 | `[T−24h,T−1h]` | 164 | −0.2389 | −3.21% | 23.2% | −1.3% |
| V3 新鲜度 | `[T−1h,T]` | 151 | −0.2389 | −26.03% | 17.9% | −17.1% |

- **成本压力测试**：V1 把 taker 费降到 0（ask 仍含 1¢）→ 每美元 **−19.01%**；连 1¢ 半价差也去掉、直接用最后一笔打印价（不可执行）→ **−15.33%**。负结论不是费用假设造成的。
- **最大回撤**：V1 按触发比赛日排序的已实现权益峰谷为 **2,239 USDT = 44.8%**（5,000 USDT 账户；不是逐日盯市）；V2 23.1%，V3 41.7%。
- **与旧笔记的关系**：`bots/quant/notes/q011-hist/REPORT.md` 用 `q011-hist/q011_hist.py` 跑出 V1/V2；本次 replay 的主逻辑相同（只加了 `[T−1h,T]` 新鲜度窗口和 CLI 参数），重跑数字逐项复现（161 场、−0.2389、−22.82%；164 场、−0.2389、−3.21%）。旧 REPORT 的“匹配 1,987 场”与“2,019/2,090”不一致，以本次 **2,019** 为准；旧 REPORT 没有 V3。
- **限制（如实写）**：① closed 市场没有历史 L2 盘口，ask=print+1¢ 是模型不是观测，entry 原要求的 `spread ≤ 0.02` 无法逐场核实；② last print 可能陈旧，主窗口最长 6 小时、敏感性 24 小时，但 1 小时新鲜度窗口结果更差；③ data-api 每市场约最近 2 万笔，热门市场可能截断；④ I1 仅 17 场匹配、4 次触发，F1 7 次触发，分联赛结论不可靠，主结论以 ALL 为准。
- **结论**：**result = 负**，独立结果 161（≥30），按预先写死的“中位净收益 ≤ 0”判 **FAIL**。三个窗口、零费、零价差压力测试全部为负；**本条作为策略应丢弃（DROP）**，不要再登记前向记录。若操作员只想保留一条反证（GUIDE §2.1 允许负结果待核，结局最多补充采纳 0.5），回放材料已齐全，可直接用 `replay/quant-011/`；但不要把它当作可继续开发的策略。

### 1. 我已经算出的东西（自己的算术，基于下面 4 个赛季 CSV）

数据：football-data.co.uk `E0`（英超）与 `I1`（意甲）2022/23、2023/24、2024/25、2025/26 四个赛季，每个文件 380 场，共 3,040 场；只保留 `FTR∈{H,D,A}` 且 `B365H/B365D/B365A` 齐全的行（全部保留，未丢行）。

平局隐含概率（去水/归一化，自算公式）：

`qD = (1/B365D) / (1/B365H + 1/B365D + 1/B365A)`

按 qD 分桶后的实际平局频率（自算，样本 2022-08-05 至 2026-05-24）：

| 联赛 | qD 桶 | 样本 n | 平均 qD | 实际平局率 | 差（pp） | 按 B365D 平赔投注 ROI |
|---|---|---:|---:|---:|---:|---:|
| 英超 E0 | 0.18–0.22 | 238 | 0.2037 | 0.2479 | +4.42 | +15.09% |
| 英超 E0 | 0.22–0.26 | 513 | 0.2422 | 0.2378 | −0.44 | −7.17% |
| 英超 E0 | 0.26–0.30 | 548 | 0.2758 | 0.2646 | −1.12 | −8.94% |
| 意甲 I1 | 0.18–0.22 | 184 | 0.2021 | 0.1848 | −1.74 | −13.78% |
| 意甲 I1 | 0.22–0.26 | 322 | 0.2423 | 0.2329 | −0.94 | −8.61% |
| 意甲 I1 | 0.26–0.30 | 696 | 0.2804 | 0.3060 | +2.56 | +3.56% |
| 合并 | 0.18–0.22 | 422 | 0.2030 | 0.2204 | +1.74 | +2.50% |
| 合并 | 0.22–0.26 | 835 | 0.2422 | 0.2359 | −0.63 | −7.72% |
| 合并 | 0.15–0.30 整体 | 2,675 | — | — | — | — |

联赛整体平局率：英超 0.2408（1,520 场），意甲 0.2757（1,520 场），合并 0.2582（3,040 场）—— 自算。

**关键结论（自己的判断）**：同一个 0.18–0.22 桶，英超 +4.42pp / ROI +15.09%，意甲 −1.74pp / ROI −13.78%，符号相反；合并后只剩 +1.74pp。B365D 是含庄家水位的赔率，能在 238 注上打赢庄家 15% 不合常理，所以这更可能是**分桶噪声**，不能写成“平局被低估”。这是原稿当时没有回测就把它写成“假设”的原因；第 2 轮的真实成交价回放已补上，并给出负结果（见“证据 0”）。

### 2. 示例市场的实际盘口（Gamma 快照，2026-10-20 抓取）

- `epl-liv-ars-2026-11-01-draw`（"Will Liverpool FC vs. Arsenal FC end in a draw?"）：`bestBid=0.25`、`bestAsk=0.27`、`spread=0.02`、`outcomePrices=["0.26","0.74"]`、`liquidity=3469.4498`、`orderPriceMinTickSize=0.01`、`endDate=2026-11-01T16:30:00Z`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`。这是“可以交易”的价差水平。
- `sea-ata-par-2026-11-02-draw`（"Will Atalanta BC vs. Parma Calcio 1913 end in a draw?"）：`bestBid=0.09`、`bestAsk=0.30`、`spread=0.21`、`orderPriceMinTickSize=0.01`、`orderMinSize=5`、`endDate=2026-11-02T19:45:00Z`、同一 `feeSchedule`（rate 0.05）。**价差 0.21，半价差就是 0.105 ≈ 名义的 35%**，任何 2–4pp 级的偏差在这种盘口上都不可能兑现。这条就是本策略的主要杀手。
- 同 event 三个 Yes 的 Gamma 中间价（`events?tag_slug=soccer` 快照，`sea-ata-par-2026-11-02`）：`0.66`（Atalanta）/`0.195`（Draw）/`0.17`（Parma），合计 1.025 > 1；`epl-new-eve-2026-11-02` 三个市场当时都报 `0.5/0.5`（新上市、未定价），合计 1.5。说明**新上架的三向事件在定价前是不可交易的**，也会污染“按中间价算的边缘”。
- CLOB 价格历史：`prices-history?market=<draw Yes token>&interval=max` 在 2026-10-20 只返回 **6 个点**（首个 `t=1792454444, p=0.315`，其余 `p=0.195`），2026-10-21 复核为 32 个点。它仍只是最后成交价/中间价，**不能当成交价**；可用的历史成交价来自 data-api 的已闭合市场逐笔成交（见“证据 0”），不必只靠前向记录。

### 3. 费用（官方文档，已读）

- `fee = C × feeRate × p × (1 - p)`，C=份数，p=成交价；"Makers are never charged fees. Only takers pay fees."；体育类 Taker Fee Rate **0.05**、Maker Fee Rate 0、Maker Rebate **15%**。本文所有费用按 0.05 算（与上面两个示例市场 `feeSchedule.rate=0.05` 一致）。

## 数据

- football-data.co.uk：模板 `https://www.football-data.co.uk/mmz4281/<season>/<league>.csv`；回放用 season `1718`…`2627`、league `E0/I1/SP1/D1/F1`（50 个文件，每个 380 行；`2021` 是 2020/21 赛季代码，`2122` 是 2021/22）；免费、免密钥、HTTP 200；列含 `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, B365H, B365D, B365A`。原稿的校准表只用了 2022/23–2025/26 的 E0/I1 8 个文件。
- Gamma：`https://gamma-api.polymarket.com/markets?slug=<market-slug>`（单市场；返回 description 原文、`feeSchedule`、`bestBid/bestAsk`、`clobTokenIds`）；`https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=<tag>&limit=100`（枚举已闭合比赛 event，分页 `after_cursor`）；免费、免密钥。
- data-api 逐笔成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`；免费、免密钥；字段含 `outcome/price/size/side/timestamp`，每个市场约可取最近 2 万笔。这是回放的成交价来源。
- CLOB：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`；免费、免密钥；只是最后成交价/中间价，**不当成交价**。
- 旧“缺口”已补上：`bots/quant/notes/q011-hist/REPORT.md` 与 `bots/quant/replay/quant-011/` 用 data-api 的已闭合市场逐笔成交完成了 Polymarket 侧回放（2,019 场匹配、1,986 场有打印）；历史 L2 盘口仍无公开来源，所以 `spread ≤ 0.02` 只能建模、不能逐场核实。
- 每周场次数：英超 2025/26 赛季 380 场 / 282 天 = **9.4 场/周**，意甲 380 场 / 274 天 = **9.7 场/周**（自算）。Polymarket 侧：一次拉取的 600 个 open soccer event 样本里，纯三向比赛 event（slug 形如 `联赛-主-客-日期`）有 **111 个**，比赛日期跨 2026-10-20 至 2026-11-02（13 天），约 **60 场/周**；全平台 open soccer event 总数**未查到**（分页未按日期过滤，无法给出准确总数）。

## 两周内怎么检验

- **2026-10-21 更新**：历史回放已完成，不需要再等两周——`bots/quant/replay/quant-011/` 用 data-api 成交价得到 **161 个独立比赛触发（≥30）**，按写死的失败标准判 **FAIL**。本条建议 **DROP**；若主审仍要求前向，下面原方案保留，但不应再花两周去救一个三个窗口都为负的规则。
- 数据：前向记录（从记录日起）每场足球比赛 event 的三个市场在 **T−24h 与 T−1h** 的 `bestBid/bestAsk`、`feeSchedule`、`endDate`；结算后从 Gamma 取结果，与 football-data 下一版 CSV 的 FTR 对照（两者都应在 90 分钟口径上一致，不一致的单独列）。
- 独立结果计数：**一场比赛 = 1 个独立结果**（三个市场算一个、同一比赛的多档比分/角球市场不算）。原稿按桶内比赛数估“qD 0.15–0.30 两联赛约 17 场/周，两周约 34 场”；**第 2 轮回放的实际触发只有 161 场/2.177 年 ≈ 74 个触发/年（两周约 2.8 个）**，因为还要满足 `ask ≤ base − 0.02` 和价格带，桶内大部分比赛被筛掉。原稿“两周凑 30 场”的估计因此过于乐观；若做前向，两周根本凑不到 30 个独立触发。
- 失败标准（写死）：(a) 扣费与半价差后净收益中位数 ≤ 0；或 (b) 记录到的平局卖出价与历史同桶基准率的差，在 30 场样本上不显著（二项检验 p > 0.05）；或 (c) 有效样本里过半比赛的可交易价差 > 0.02（说明根本没有能交易的报价）。任一成立即判失败，不再加仓。

## 成本与容量

- 吃单费（官方公式，自己代入）：每份费 = `0.05 × p × (1−p)`；占名义本金比例 = `0.05 × (1−p)`。
  - p=0.27（利物浦-阿森纳 draw 卖价）：每份费 `0.05×0.27×0.73 = 0.009855` USDC，占名义 **3.65%**。
  - p=0.20：每份费 `0.05×0.20×0.80 = 0.008` USDC，占名义 **4.00%**。
- 价差（半价差按中间价算）：`epl-liv-ars` 例子 `ask 0.27 / bid 0.25`，半价差 `0.01`，占 0.27 的 **3.70%**；两笔成本合计约 **7.35%** 的名义资金。`sea-ata-par` 例子半价差 `0.105`，占 0.30 的 **35%**，直接放弃。
- 扣成本后的粗算（原稿算术；已被第 2 轮回放取代，见“证据 0”）：把英超 0.18–0.22 桶的 +4.42pp 偏差套到卖价 0.20、价差 0.02 的盘口上：每份毛优势 `0.0442`，减费 `0.008`、减半价差 `0.01`，净 `+0.0262` USDC/份，占 0.20 成本的 **+13.1%**。同一算法套合并样本的 +1.74pp：`0.0174 − 0.008 − 0.01 = −0.0006` USDC/份，**约等于打平**。所以“扣成本后够用”只在英超单联赛的桶上成立，而该桶在意甲符号相反 —— 本稿不认为已证明为正。
- 容量：`epl-liv-ars` draw 市场 `liquidity=3469.4498`（2026-10-20 快照，2026-10-21 复核为 3591.03；USDC 计，Gamma 字段），单笔 50 USDT 在这个池子里不会明显推动价格，但 0.02 的价差说明深度集中在窄区间，一次拿 200 份以上就可能吃掉多档。机会数要分清：qD 0.15–0.30 桶约 17 场/周 ≈ **70 场/月**，但第 2 轮回放里满足全部触发条件的只有 **74 场/年 ≈ 6.2 场/月**。按 50 USDT/场，月投放约 310 USDT，远低于 2,500 USDT 场所上限；5,000 USDT 总资金放得下。
- 资金占用：从买入到结算平均约 1–3 天（示例 `endDate=2026-11-01T16:30:00Z`）。
- **第 2 轮年化贡献算法（回放实测，不是粗算）**：主窗口每场净收益率均值 **−22.18%** × 单场 **50 USDT** × 每年 **74.0 场触发** ÷ **5,000 USDT** = **−16.4%/年**；敏感性窗口 −1.3%，新鲜度窗口 −17.1%。回放触发 161 场/2.177 年 = 74.0 场/年；按触发比赛日排序的已实现最大回撤 2,239 USDT = **44.8%**。负贡献表示按本条规则部署会亏，不是可部署收益。

## 风险

- **价差风险（最大）**：示例 `sea-ata-par` 平局盘 bid 0.09 / ask 0.30，价差 0.21；很多小联赛三向事件都是这种状态，2pp 级的偏差在 35% 的往返成本前毫无意义。这也是为什么本稿要求先筛 `spread ≤ 0.02`。
- **证据不支持**：英超 +15% ROI、意甲 −14% ROI，同一个桶符号相反；把 B365 含水位赔率当成“公平价”本身就可能把庄家水位当成偏差。这是本条最可能被退回的原因。
- **规则歧义**：24 小时无数据时 “resolve 50-50, or to \"Draw\" where applicable”，平局市场可能直接按 Yes 结算，原文没写死；“取消整场算 Draw Yes” 对平局买方有利，但这属于规则漏洞型收益，不做为主要依据。
- **结算口径差**：Polymarket 以官方统计为准，退到 Flashscore/Sofascore；football-data 的 FTR 与官方“腰斩后改判”的记录可能不一致；赛后改判不追溯（原文）。
- **新上架未定价**：`epl-new-eve-2026-11-02` 三个市场都报 0.5/0.5，合计 1.5，说明定价前盘口无意义，误按中间价算会得到假边缘。
- **平台/费用变动**：体育费率 0.05 与 15% maker 返佣来自当前文档；费率可变，且逐市场 `feeSchedule` 需逐个读。
- **回放已做且为负**：`observed_net_return` 不再为空——主窗口每美元投入 **−22.82%**、每份中位 **−0.2389**、已实现最大回撤 **44.8%**；夏普未算，但不影响 FAIL 结论。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：**不确定** — 机制写成“对手方把平局定价低于历史基准率时买入平局”，付款方与行为偏差的因果链清楚；但本文自己的数据在两个联赛里符号相反，机制**未被证实**，只能说“说得清、未验证”。
2. 有免费数据能检验：**满足** — football-data.co.uk 的 5 联赛 10 个赛季、赔率+赛果齐全；Gamma closed events + data-api 逐笔成交免费免密钥，已闭合平局市场的成交可回溯。第 2 轮回放匹配 **2,019/2,090 场（96.6%）**、主窗口 161 个独立触发（≥30）；历史 L2 盘口仍没有公开来源，但成交价本身已够做回放。
3. 小资金能做：**满足** — 单注 50 USDT、未结算敞口 ≤ 500 USDT、单场所 ≤ 2,500 USDT，示例 draw 市场 `liquidity=3469.4498`；容量与“能否真的成交在 bestAsk”仍未验证。
4. 不重复：**不确定** — 仓库内 grep 未发现足球平局/三向盘条目，`bots/quant/CLAIMS.md` 已认领 B08（2026-10-20）；它区别于冷门-热门偏差类条目的关键变量是“平局单桶基准率 vs Polymarket 平局卖价”，但最终去重需主审确认。
5. 扣成本后粗算够用：**不满足** — 第 2 轮回放主窗口 161 次触发，每份净收益中位 **−0.2389**、每美元投入 **−22.82%**、命中率 18.6%；零吃单费仍 **−19.01%**，连 1¢ 半价差也去掉仍 **−15.33%**。原稿按 0.05 吃单费 + 0.02 价差算出的“英超桶 +13.1%”没有被真实成交价复现；合并样本当时就是打平/为负。
6. 两周内能检验：**满足（历史回放已完成并 FAIL）** — `bots/quant/replay/quant-011/` 给出主窗口 **161**、敏感性 **164**、新鲜度 **151** 个独立比赛结果（均 ≥30），按预先写死的失败标准（净收益中位数 ≤ 0）判 **FAIL**；不需要再等两周前向记录。原稿按桶内比赛数估“两周约 34 场”；实际经过价格带和 `ask ≤ base − 0.02` 过滤后只有约 **74 个触发/年（两周约 2.8 个）**，原估算没有扣掉这些筛选，过于乐观。
7. 出处可查：**满足** — 规则原文、`feeSchedule`、盘口、费率表、CSV、data-api 成交、Gamma closed keyset 均有可打开 URL 与访问日期（2026-10-20 抓取，2026-10-21 复核）；8 个 football-data CSV 已拆成独立 URL，逐一下载均 HTTP 200/380 行。回放脚本、参数、stdout 和 `SUMMARY.md` 在 `bots/quant/replay/quant-011/`；核对日志见 `bots/quant/notes/batch1-verification/quant-011.md`。

## 出处

- https://gamma-api.polymarket.com/markets?slug=sea-ata-par-2026-11-02-draw — 访问 2026-10-20 — 已读（规则原文、feeSchedule、bestBid/bestAsk/spread）
- https://gamma-api.polymarket.com/markets?slug=epl-liv-ars-2026-11-01-draw — 访问 2026-10-20 — 已读（贴价差示例、liquidity）
- https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&limit=20&order=startDate&ascending=false — 访问 2026-10-20 — 已读（`epl-new-eve-2026-11-02` 与 `sea-ata-par-2026-11-02` 的两个三向 event、三个 Yes 中间价、negRisk、标签）
- https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&limit=100&offset=0..500 — 访问 2026-10-20 — 已读（600 个 open soccer event 样本，数出 111 个纯三向比赛 event 与比赛日期分布）
- https://clob.polymarket.com/prices-history?market=115347507753485536976403009642719279973942206992108120088763998979109693996472&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（6 个点：t=1792454444 p=0.315，其后 0.195）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-20 — 已读（`fee = C × feeRate × p × (1 - p)`；Sports 0.05 / maker 0 / rebate 15%；"Makers are never charged fees"）
- https://www.football-data.co.uk/mmz4281/2223/E0.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、176,180 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2223/I1.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、171,573 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2324/E0.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、172,196 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2324/I1.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、167,015 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2425/E0.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、197,110 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2425/I1.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、191,722 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2526/E0.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、203,438 字节、380 行）— 已读
- https://www.football-data.co.uk/mmz4281/2526/I1.csv — 访问 2026-10-20（2026-10-21 复核 HTTP 200、196,217 字节、380 行）— 已读
- https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=EPL&limit=100 — 访问 2026-10-21 — 已读（已闭合 event；`next_cursor` 分页，回放用 EPL/serie-a/la-liga/bundesliga/ligue-1 五个 tag）
- https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N — 访问 2026-10-21 — 已读（逐笔成交；回放用 `outcome/price/size/side/timestamp`；这是本条成交价来源）
- 模板 `https://www.football-data.co.uk/mmz4281/<season>/<league>.csv`，season = 1718…2627、league = E0/I1/SP1/D1/F1（5 联赛 × 10 赛季，共 50 个独立文件；示例 `https://www.football-data.co.uk/mmz4281/1718/E0.csv`）— 访问 2026-10-21 — 已读（回放基准率训练；最早的 2017/18 文件起点 2017-08-04）
- `bots/quant/replay/quant-011/SUMMARY.md`、`run_replay.py`、`params.json`、`data_urls.md`、`trades.csv` — 2026-10-21 — 已读（第 2 轮回放产物；stdout 在 `bots/quant/notes/scheduler/scratch/P-quant-011/`）
- 一句话结论：Polymarket 历史 L2 盘口仍无公开来源；但 data-api 的已闭合市场逐笔成交可回放，CLOB `prices-history` 只作参考、不当成交价。
