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
data: football-data.co.uk E0/I1 CSV 2022/23–2025/26（赔率+比分+赛果，免费免密钥）；Gamma/CLOB 公开 GET（免费免密钥）；Polymarket 历史平局盘口/价格无公开来源，只能从记录日起前向记录
test_2w: 每场足球比赛算 1 个独立结果（按 match 不按市场数）；两周内按宽价桶（平局隐含概率 0.15–0.30）约可凑 30 场；失败标准 = 扣吃单费与半价差后的净收益中位数 ≤ 0，或平局实现频率落在历史桶基准率的 95% 区间内（说明无偏差）。
status: 待核
confidence: 中
---

判断说明：本条是规则 + 费用 + 历史基准率的筛查稿，**没有跑过 Polymarket 回测**，因为 Polymarket 的历史平局价格对公开检索不可得（见“数据”）。CSV 上算出的偏差方向在两个联赛里相反（见“证据”），本稿据此把结论压到“可检验的假设”，不写成可赚钱的策略。

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

**关键结论（自己的判断）**：同一个 0.18–0.22 桶，英超 +4.42pp / ROI +15.09%，意甲 −1.74pp / ROI −13.78%，符号相反；合并后只剩 +1.74pp。B365D 是含庄家水位的赔率，能在 238 注上打赢庄家 15% 不合常理，所以这更可能是**分桶噪声**，不能写成“平局被低估”。这是我**没有**回测就写下来的原因。

### 2. 示例市场的实际盘口（Gamma 快照，2026-10-20 抓取）

- `epl-liv-ars-2026-11-01-draw`（"Will Liverpool FC vs. Arsenal FC end in a draw?"）：`bestBid=0.25`、`bestAsk=0.27`、`spread=0.02`、`outcomePrices=["0.26","0.74"]`、`liquidity=3469.4498`、`orderPriceMinTickSize=0.01`、`endDate=2026-11-01T16:30:00Z`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`。这是“可以交易”的价差水平。
- `sea-ata-par-2026-11-02-draw`（"Will Atalanta BC vs. Parma Calcio 1913 end in a draw?"）：`bestBid=0.09`、`bestAsk=0.30`、`spread=0.21`、`orderPriceMinTickSize=0.01`、`orderMinSize=5`、`endDate=2026-11-02T19:45:00Z`、同一 `feeSchedule`（rate 0.05）。**价差 0.21，半价差就是 0.105 ≈ 名义的 35%**，任何 2–4pp 级的偏差在这种盘口上都不可能兑现。这条就是本策略的主要杀手。
- 同 event 三个 Yes 的 Gamma 中间价（`events?tag_slug=soccer` 快照，`sea-ata-par-2026-11-02`）：`0.66`（Atalanta）/`0.195`（Draw）/`0.17`（Parma），合计 1.025 > 1；`epl-new-eve-2026-11-02` 三个市场当时都报 `0.5/0.5`（新上市、未定价），合计 1.5。说明**新上架的三向事件在定价前是不可交易的**，也会污染“按中间价算的边缘”。
- CLOB 价格历史：`prices-history?market=<draw Yes token>&interval=max` 只返回 **6 个点**（首个 `t=1792454444, p=0.315`，其余 `p=0.195`），因为市场刚上架。**Polymarket 侧没有可用的历史平局价格序列**，这条必须前向记录。

### 3. 费用（官方文档，已读）

- `fee = C × feeRate × p × (1 - p)`，C=份数，p=成交价；"Makers are never charged fees. Only takers pay fees."；体育类 Taker Fee Rate **0.05**、Maker Fee Rate 0、Maker Rebate **15%**。本文所有费用按 0.05 算（与上面两个示例市场 `feeSchedule.rate=0.05` 一致）。

## 数据

- football-data.co.uk：`https://www.football-data.co.uk/mmz4281/2223/E0.csv`（把 `2223` 换成 `2324/2425/2526`，`E0` 换成 `I1` 得四个赛季两个联赛的 8 个文件）；免费、免密钥、HTTP 200、每个 380 行；列含 `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, B365H, B365D, B365A, PSCH/PSD/PSA`（本稿只用 B365 与 FTR）。
- Gamma：`https://gamma-api.polymarket.com/markets?slug=<market-slug>`（单市场；返回 description 原文、`feeSchedule`、`bestBid/bestAsk`、`clobTokenIds`）；`https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&limit=N&offset=K`（枚举比赛 event）；免费、免密钥。
- CLOB：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`；免费、免密钥；本例只有 6 个点。
- 缺口（未查到）：Polymarket 历史平局盘口/成交价（公开接口只给开放市场和有限历史）；未找到按比赛逐场的 Polymarket 历史价格数据集。因此本条的“Polymarket 侧回测”做不了，只能前向记录。
- 每周场次数：英超 2025/26 赛季 380 场 / 282 天 = **9.4 场/周**，意甲 380 场 / 274 天 = **9.7 场/周**（自算）。Polymarket 侧：一次拉取的 600 个 open soccer event 样本里，纯三向比赛 event（slug 形如 `联赛-主-客-日期`）有 **111 个**，比赛日期跨 2026-10-20 至 2026-11-02（13 天），约 **60 场/周**；全平台 open soccer event 总数**未查到**（分页未按日期过滤，无法给出准确总数）。

## 两周内怎么检验

- 数据：前向记录（从记录日起）每场足球比赛 event 的三个市场在 **T−24h 与 T−1h** 的 `bestBid/bestAsk`、`feeSchedule`、`endDate`；结算后从 Gamma 取结果，与 football-data 下一版 CSV 的 FTR 对照（两者都应在 90 分钟口径上一致，不一致的单独列）。
- 独立结果计数：**一场比赛 = 1 个独立结果**（三个市场算一个、同一比赛的多档比分/角球市场不算）。两周 ≈ 120 场 Polymarket 比赛 event；按历史比例，qD 0.15–0.30 桶在英超+意甲合计 8 个联赛赛季里共 2,675 场（自算：1409+1266），即每联赛每季约 334 场 ≈ 8.4 场/周，两联赛 ≈ **17 场/周**，两周约 **34 场**，刚好过 30 的门线；Polymarket 覆盖的联赛更多，但当日赛程决定实际数量。**若两周凑不满 30 场，只能记为前向观察，不冒充 30 个结果。**
- 失败标准（写死）：(a) 扣费与半价差后净收益中位数 ≤ 0；或 (b) 记录到的平局卖出价与历史同桶基准率的差，在 30 场样本上不显著（二项检验 p > 0.05）；或 (c) 有效样本里过半比赛的可交易价差 > 0.02（说明根本没有能交易的报价）。任一成立即判失败，不再加仓。

## 成本与容量

- 吃单费（官方公式，自己代入）：每份费 = `0.05 × p × (1−p)`；占名义本金比例 = `0.05 × (1−p)`。
  - p=0.27（利物浦-阿森纳 draw 卖价）：每份费 `0.05×0.27×0.73 = 0.009855` USDC，占名义 **3.65%**。
  - p=0.20：每份费 `0.05×0.20×0.80 = 0.008` USDC，占名义 **4.00%**。
- 价差（半价差按中间价算）：`epl-liv-ars` 例子 `ask 0.27 / bid 0.25`，半价差 `0.01`，占 0.27 的 **3.70%**；两笔成本合计约 **7.35%** 的名义资金。`sea-ata-par` 例子半价差 `0.105`，占 0.30 的 **35%**，直接放弃。
- 扣成本后的粗算（我的算术，不是回测）：把英超 0.18–0.22 桶的 +4.42pp 偏差套到卖价 0.20、价差 0.02 的盘口上：每份毛优势 `0.0442`，减费 `0.008`、减半价差 `0.01`，净 `+0.0262` USDC/份，占 0.20 成本的 **+13.1%**。同一算法套合并样本的 +1.74pp：`0.0174 − 0.008 − 0.01 = −0.0006` USDC/份，**约等于打平**。所以“扣成本后够用”只在英超单联赛的桶上成立，而该桶在意甲符号相反 —— 本稿不认为已证明为正。
- 容量：`epl-liv-ars` draw 市场 `liquidity=3469.4498`（USDC 计，Gamma 字段），单笔 50 USDT 在这个池子里不会明显推动价格，但 0.02 的价差说明深度集中在窄区间，一次拿 200 份以上就可能吃掉多档。每月机会：按 qD 0.15–0.30 桶约 17 场/周 → **约 70 场/月**，单注 50 USDT 时月投放上限约 2,500 USDT，符合 5,000 USDT 总资金 / 2,500 单场所的限制。
- 资金占用：从买入到结算平均约 1–3 天（示例 `endDate=2026-11-01T16:30:00Z`），年化换算必须按占用天数折算，本稿不算年化。

## 风险

- **价差风险（最大）**：示例 `sea-ata-par` 平局盘 bid 0.09 / ask 0.30，价差 0.21；很多小联赛三向事件都是这种状态，2pp 级的偏差在 35% 的往返成本前毫无意义。这也是为什么本稿要求先筛 `spread ≤ 0.02`。
- **证据不支持**：英超 +15% ROI、意甲 −14% ROI，同一个桶符号相反；把 B365 含水位赔率当成“公平价”本身就可能把庄家水位当成偏差。这是本条最可能被退回的原因。
- **规则歧义**：24 小时无数据时 “resolve 50-50, or to \"Draw\" where applicable”，平局市场可能直接按 Yes 结算，原文没写死；“取消整场算 Draw Yes” 对平局买方有利，但这属于规则漏洞型收益，不做为主要依据。
- **结算口径差**：Polymarket 以官方统计为准，退到 Flashscore/Sofascore；football-data 的 FTR 与官方“腰斩后改判”的记录可能不一致；赛后改判不追溯（原文）。
- **新上架未定价**：`epl-new-eve-2026-11-02` 三个市场都报 0.5/0.5，合计 1.5，说明定价前盘口无意义，误按中间价算会得到假边缘。
- **平台/费用变动**：体育费率 0.05 与 15% maker 返佣来自当前文档；费率可变，且逐市场 `feeSchedule` 需逐个读。
- 未做回测，`observed_net_return = null`，夏普、最大回撤均未知。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：**不确定** — 机制写成“对手方把平局定价低于历史基准率时买入平局”，付款方与行为偏差的因果链清楚；但本文自己的数据在两个联赛里符号相反，机制**未被证实**，只能说“说得清、未验证”。
2. 有免费数据能检验：**满足（部分）** — football-data.co.uk 的 E0/I1 四个赛季、3,040 场、赔率+赛果齐全，免费免密钥，独立结果数远超 30；但 Polymarket 侧历史平局价格未查到，只能前向记录，所以“历史可回测”只对基准率成立，对成交价不成立。
3. 小资金能做：**满足** — 单注 50 USDT、未结算敞口 ≤ 500 USDT、单场所 ≤ 2,500 USDT，示例 draw 市场 `liquidity=3469.4498`；容量与“能否真的成交在 bestAsk”仍未验证。
4. 不重复：**不确定** — 仓库内 grep 未发现足球平局/三向盘条目，`bots/quant/CLAIMS.md` 已认领 B08（2026-10-20）；它区别于冷门-热门偏差类条目的关键变量是“平局单桶基准率 vs Polymarket 平局卖价”，但最终去重需主审确认。
5. 扣成本后粗算够用：**不满足（暂）** — 按 0.05 吃单费 + 0.02 价差：英超桶净 +13.1%，合并样本净 −0.3%（占 0.20 成本的 −0.0006 USDC/份，打平），意甲桶为负；证据不足以支撑正收益结论，故按“不满足”记。
6. 两周内能检验：**不确定** — 独立结果按比赛数计，宽松桶（qD 0.15–0.30）两联赛约 17 场/周，两周约 34 场，刚好过 30 门线，但实际取决于当周赛程与可交易盘口；失败标准已写死（净收益中位数 ≤ 0 / 二项检验不显著 / 过半样本价差 > 0.02）。
7. 出处可查：**满足** — 规则原文、`feeSchedule`、盘口、费率表、CSV 均有可打开 URL 与访问日期，详见“出处”与 `notes/batch1-verification/quant-011.md` 核对日志；所有偏差数字都写明是自算并给出公式。

## 出处

- https://gamma-api.polymarket.com/markets?slug=sea-ata-par-2026-11-02-draw — 访问 2026-10-20 — 已读（规则原文、feeSchedule、bestBid/bestAsk/spread）
- https://gamma-api.polymarket.com/markets?slug=epl-liv-ars-2026-11-01-draw — 访问 2026-10-20 — 已读（贴价差示例、liquidity）
- https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&limit=20&order=startDate&ascending=false — 访问 2026-10-20 — 已读（`epl-new-eve-2026-11-02` 与 `sea-ata-par-2026-11-02` 的两个三向 event、三个 Yes 中间价、negRisk、标签）
- https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&limit=100&offset=0..500 — 访问 2026-10-20 — 已读（600 个 open soccer event 样本，数出 111 个纯三向比赛 event 与比赛日期分布）
- https://clob.polymarket.com/prices-history?market=115347507753485536976403009642719279973942206992108120088763998979109693996472&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（6 个点：t=1792454444 p=0.315，其后 0.195）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-20 — 已读（`fee = C × feeRate × p × (1 - p)`；Sports 0.05 / maker 0 / rebate 15%；"Makers are never charged fees"）
- https://www.football-data.co.uk/mmz4281/2223/E0.csv、2324/E0.csv、2425/E0.csv、2526/E0.csv、以及同四季 I1.csv — 访问 2026-10-20 — 已读（列结构与 FTR/B365 赔率，每文件 380 场）
- 一句话搜索结论：Polymarket 侧历史平局价格未查到公开来源（Gamma 只给开放市场快照，CLOB prices-history 对本例只有 6 个点）
