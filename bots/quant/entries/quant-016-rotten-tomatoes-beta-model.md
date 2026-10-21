---
id: quant-016
name_zh: 烂番茄开分：早期评论二项定价
name_en: Rotten Tomatoes Tomatometer brackets priced from early critic reviews (Beta-Binomial)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: culture
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「某片 Rotten Tomatoes All Critics Tomatometer 在 <日期> 10:00 AM ET 是否 ≥ T」嵌套阈值链（同一 event 内 3–15 个累积档，T = 25…99，多为 5 分间距、常在共识值附近加密到 1–2 分）
venues: Polymarket
data: RT 影片页 `criticsScore`（likedCount / notLikedCount / reviewCount，免费免密钥，抓 HTML）；Polymarket Gamma（规则、盘口、feeSchedule、clobRewards）、CLOB prices-history 与 data-api 逐笔成交（已关闭市场都可读，可做价格侧历史回测）；**历史"当时已出评论数"取不到**（RT reviews 页日期由 JS 渲染，HTML 里 0 个日期字段；Wayback/Common Crawl 本次也未取到），所以模型侧只能从现在起前向记录
test_2w: 独立结果按 event 计（同片各档共享一次结算，算 1 个）；两周只覆盖 2026-10-26 与 2026-11-09 两批共约 5–6 个 event，凑不到 30；失败标准：模型对已结算 event 的 Brier/log loss 不优于市场中间价，或已成交份额中位已实现毛利 ≤0
status: 待核
confidence: 中
---

整理说明：本条所有 Polymarket 计数、分档频率、盘口价格都是我在 2026-10-20 用下文 URL 现抓后自己算的（脚本 `calc_rt.py`，全文见 `notes/batch2-verification/quant-016.md`）；RT 那边的"分数=新鲜评论数/(新鲜+烂)"公式我用两部片子的实际页面核对过。**模型侧没有做成回测**：历史"某时刻已出多少条评论、其中几条新鲜"取不到（见数据节）。2026-10-21 我补做了**市场侧历史可成交价回测**（85 个已关闭 event、data-api 逐笔成交 + CLOB prices-history，扣吃单费和 1¢ 半价差；脚本与 stdout 见 `notes/scheduler/scratch/H-quant-016/`），结论对"市场存在可利用的窄档错价"这一前提**偏负**：T-24h 的市场价已经高度校准，预注册的三条模型无关规则全部净亏。该回测不能检验 Beta 模型本身（模型输入仍不可回放），所以本条现在只有"模板+基率+当期横截面+价格侧否证"的证据，**不是收益证明**；建议按 GUIDE 第 2 节第 6 条降为**待选区**，不要按收录推进。

## 一句话

在某片 RT 开分前后的窗口里，从影片页读出**已出评论数 n 与其中新鲜条数 k**，用 Beta(k+1, n−k+1) 得到最终 Tomatometer（RT 显示的是 `round(100k/(k+n))`，22 个页面实测，不是 floor）的分布，再折算成"P(最终 ≥ T)"；只在某个档位的买价/卖价与该概率的偏离超过"吃单费 + 半个价差 + 2 分安全垫"时挂 **maker** 单，持到 10:00 AM ET 那次读数结算。

## 钱从哪里来

付钱给你的是**把"当前显示分数"当成"最终分数"的下注者**，以及只看新闻情绪不看样本量的人。这条钱能持续存在，是因为窄档的**抽样噪声本身**就足以让档位接近抛硬币：Tomatometer 是 k/(k+n) 的比例，二项标准差在 p=0.75、n=100 时是 `sqrt(0.75×0.25/100) = 0.0433`，即 **±4.3 分**；而 Polymarket 常把档位加密到 **2 分甚至 1 分间距**（见证据 3 的实例：`74+/72+/76+`、`48+/49+/51+`）。也就是说，即使当期分数完全公开，1–2 分间距的档位在 n≈100 时仍然是真随机；市场若按"离当期分数近就归 0/1"来定价，就会在这类档位上系统性给错价。第二个来源是**"到期没分数"的尾部**：85 个已关闭 event 里有 **14 个（16.5%）全部档位都结算 NO**（见证据 2、4），谁在低估这个尾部，钱就是他的。**但这两个故事都没有通过价格侧检验**：T-24h 的市场 Brier 只有 0.0248，84.6% 的 event 在 T-24h 就已指向正确边界（但 lo 中位价 0.872，不是 0/1），预注册的模型无关规则全部净亏（见证据 7）。所以下面写的是"假设的付钱方"，不是已证实的付钱方。

## 规则

**结算原文（Gamma 事件 `clayface-rotten-tomatoes-score-20261026` 与 `sense-and-sensibility-rotten-tomatoes-score-20261019`，2026-10-20 已读，两片文字只差片名/日期）**：

- 触发条件：「This market will resolve to "Yes" if the displayed Rotten Tomatoes "All Critics" Tomatometer score for Clayface is at least equal to the specified number **at 10:00 AM ET on October 26, 2026**」——是**某一个时点**的读数，不是"曾经达到"，也不是"最终"。
- 口径：「**All Critics** Tomatometer」= 影评人侧（RT 页面 JSON 里的 `criticsScore`），**不是** Popcornmeter/Verified Audience；同一页的 `audienceScore` 在 clayface 上是 `"reviewCount":0` 的独立对象，两者不可混用。
- 阈值结构：同一 event 内多个**累积**档（`50+/60+/70+/80+/90+`，`groupItemTitle` 形如 `70+`），各自是独立二元市场，`negRisk=false`；因此"70+ = YES"和"60+ = YES"会同时成立，档与档之间是**单调约束**（P(80+) ≤ P(70+)），不是互斥分桶。少数 event 用区间写法（如 `mufasa-the-lion-king-rotten-tomatoes-score` 有 `<60`、`60-69`、`70-79`、`80-89`、`90+` 五个区间档）。
- **没有分数怎么办**：「If, for any reason, the resolution data is unavailable at this market's specified end time, the resolution source will be checked until the relevant data is available. This market will resolve to **"No"** if no data is available by October 30, 2026, 11:59 PM ET.」——即"到期没有 Tomatometer"会让**全部档位判 NO**（`by-any-means-rotten-tomatoes-score` 就是这种：RT 页面 `reviewCount:0`、无 score 字段，全部档位结算 NO）。
- 结算源字段：两个 event 的 `resolutionSource` 都是**空字符串**（实抓），规则正文只说 "Rotten Tomatoes"，**没有给出具体 URL**；用哪个页面、要不要地区站，**未查到**。
- 时区与取整：规则写美东时间 10:00 AM；显示分数是整数百分比（取整口径见下）。
- 取整口径（2026-10-21 用 22 个有显示分数的 RT 影片页系统核对，脚本 `check_rounding.py`）：显示分数是**四舍五入到整数（round half up）**，不是 floor。22/22 与 `round(100k/n)` 一致，只有 10/22 与 `floor` 一致；12 个能区分两者的样本全部是 round，例如 `the_wild_robot` `252/261=96.5517→97`（floor 96）、`inside_out_2` `298/329=90.5775→91`（floor 90）、`other_mommy` `16/89=17.9775→18`（floor 17）、`klara_and_the_sun` `5/21=23.8095→24`（floor 23）。旧稿用 `78/102=76.47→76` 和 `15/87=17.24→17` 推断"只与截断一致"是**错的**：这两个小数四舍五入也是 76/17，根本不能区分 floor 与 round。**后果**：判据应改为"四舍五入后 ≥ T"，即近似 `p ≥ (T−0.5)/100`，不是 `p ≥ T/100`；`76+`/`77+`、`78+`/`79+` 这种边界会因此翻转，而该族档位常以 1–2 分间距加密。2026-10-20 的快照 `78/102→76`、`15/87→17` 已过期（现在分别是 `82/106→77`、`16/89→18`），但两版都与 round 一致。x.5 的精确边界（half-up 还是 half-even）没有样本，RT 官方口径**未查到**；做敏感性时对 T±1 两档都算。这个结论与已合并的审计 `notes/scheduler/audit/c20261020-170337-research.md` §S2（指出旧稿把 floor 判反）一致；本次用 22 个页面把它坐实。
- 实际结算时点与规则文字的差：`sense-and-sensibility` 的 event `closedTime` 是 `2026-10-19 16:03:29+00`（= 12:03 PM ET），比规则写的 10:00 AM ET 晚约 2 小时；市场级字段 `umaEndDate` 在 2026-10-19 16:02:02–16:03:29 之间（各档略有差异）、`umaResolutionStatus=resolved`、`automaticallyResolved=true`、`customLiveness=0`、`umaBond=500`、`umaReward=5`（这些是市场级、不是 event 级）。为什么晚 2 小时，**未查到**，但这说明"读的是哪一分钟的分数"有数小时不确定性。

**交易规则（本条的提案，未验证）**

1. 每小时抓一次目标影片的 RT 页，记录 `(k=likedCount, n=k+notLikedCount, reviewCount, score)` 与抓取时刻（UTC）。
2. 概率：潜在比例 `p ~ Beta(k+1, n−k+1)`（均匀先验；也可用证据 2 的基率分布做先验）。判据按上节的四舍五入口径：`档位 T 为 YES ⟺ round(100p) ≥ T`，近似 `p ≥ (T−0.5)/100`，故 `P_T ≈ 1 − F_Beta((T−0.5)/100; k+1, n−k+1)`；对 T±1 做敏感性。对同一 event 的档位，事后强制单调化（把违反 P(高) ≤ P(低) 的值做保序回归），因为规则结构保证单调。
3. 尾部：`P(到期无分数)` 另算，先验取 `1/85`（已核实的 `by_any_means` 一例）到 `14/85`（全档 NO 的上界）之间，按 1.2%–16.5% 处理；无分数时全档 NO。这个先验**必须在成交前写死**。
4. 只在 `|P_T − mid_T| > fee_rate×p×(1−p) + 半价差 + 0.02` 时下单；只挂 maker（不吃单），限价 `买 YES = P_T − 0.01`、`买 NO = (1−P_T) − 0.01`。若没有排队价值（我的价差于对手最优价）则跳过。
5. 仓位：单档在险 ≤ 100 份；单 event 全部档位合计 ≤ 300 USDT；同时在手 ≤ 4 个 event；单场所 ≤ 2,500 USDT、总资金 5,000 USDT。
6. 出场：持有到结算，不主动平仓（票面收敛免费）；`k+n < 5` 且离读数 > 48 小时时撤掉全部挂单（样本量太小时模型无意义，RT 也不显示分数）。
7. 熔断：抓取失败或页面 `criticsScore` 缺失时，该 event 全部挂单撤掉；`n` 相比上一小时**下降**（RT 撤评论）时也撤。
8. 明确不做：不做区间写法（`<60`）的档位（口径与累积档不同，样本太少）；不做观众分/爆米花桶。

## 证据

### 1) 模板和频率（Gamma 实抓，我数的）

- `public-search?q=rotten tomatoes&limit_per_type=100` 返回 `pagination.totalResults = 163`；同结果里 50 个 event 的 slug 全是 `<film>-rotten-tomatoes-score-<YYYYMMDD>` 形态（个别 `-rotten-tomato-score`）。
- 用 event 自带 tag（`rotten-tomatoes`，id 101453；同 event 另有 `movies`(53)、`pop-culture`(596)）拉清单：`closed=true&limit=500` → **85** 个已关闭 event、**530** 个市场、成交额合计 **$1,818,572.46**（2026-10-21 重抓不变）。在开清单会漂移：2026-10-20 快照是 **9** 个 event、**47** 个市场、**$56,087.15**；2026-10-21 重抓是 **9** 个 event、**49** 个市场、**$70,507.74**（同日 `clayface` volume 从 4,096.90 涨到 5,125.88）。下文凡引用在开盘口/成交额，均标明快照日期。
- 每个 event 的市场数：平均 **6.24**，最少 3、最多 15。
- 已关闭 event 的成交额：中位 **$11,727.77**、均值 $21,394.97、最大 **$241,440.63**。
- 按 `endDate` 月份数已关闭 event：2026-03 **11**、04 **10**、05 **12**、06 **9**、07 **4**、08 **17**、09 **12**、10 **9**（10 月未完）→ 这 8 个月合计 **84** 个；另有 **1** 个已关闭 event 的 `endDate` 为空，故总数 85。**近期约每月 10 个 event**（84/8 = 10.5）。2026-07 只有 4 个，说明密度会波动，**不能把 8 月的 17 个外推**。

### 2) 最终分数的基率（我用 85 个已关闭 event 的结算结果算的）

对每个 event，取"结算为 YES 的最大档位 `lo`"和"其上方第一个结算为 NO 的档位 `hi`"，得到最终分数区间 `[lo, hi)`：

- **70/85** 个 event 至少有一个档位结算 YES；**14/85（16.5%）** 所有档位全 NO；1 个是区间写法（`<60`）不计入。
- 70 个 event 的最终分数（按 10 分桶）：`[20,30):3`、`[30,40):4`、`[40,50):5`、`[50,60):10`、`[60,70):4`、`[70,80):15`、`[80,90):12`、`[90,100]:17`。
- 派生：`P(最终 ≥ 80) = 29/70 = 0.4143`；`P(≥ 90) = 17/70 = 0.2429`；`P(< 60) = 22/70 = 0.3143`；最终 `lo` 的中位数 = **74**；相邻档中位间距 = **5 分**（最小 1、最大 20）。
- 这就是 Beta 模型的先验形状：大致双峰（一半在 ≥80，三成在 <60），**中间 60–70 只有 4/70**——均值附近的片子本来就少，所以"共识在 60–70"的定价错了会很贵。

### 3) 当期横截面（Gamma 快照 2026-10-20，`clayface`，`endDate 2026-10-26T14:00:00Z`）

`volume=4096.90`、`liquidity=870.65`、`openInterest=1234.13`、`negRisk=false`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`（**2026-10-20 快照**）。

2026-10-21 重抓同一 event：`volume=5,125.88`、`liquidity=1,507.62`、`feeSchedule={"exponent":1,"rate":0,"takerOnly":true,"rebateRate":0}`，五档 `outcomePrices` 变成 `0.8505/0.665/0.320/0.140/0.0445`。**费率字段和盘口都会变**；回测按 0.05 保守计，见成本节。

| 档 | bestBid | bestAsk | mid | `outcomePrices` | volume | `clobRewards` 日率 |
|---|---|---|---|---|---|---|
| 50+ | 0.932 | 0.977 | 0.9545 | `["0.9545","0.0455"]` | 185.88 | 3 |
| 60+ | 0.61 | 0.90 | 0.755 | `["0.755","0.245"]` | 563.93 | 3 |
| 70+ | 0.42 | 0.51 | 0.465 | `["0.465","0.535"]` | 440.99 | 3 |
| 80+ | 0.04 | 0.26 | 0.15 | `["0.15","0.85"]` | 2307.23 | 5 |
| 90+ | 0.021 | 0.061 | 0.041 | `["0.041","0.959"]` | 598.87 | 3 |

- 同日 RT 页面：`clayface` 的 `criticsScore = {"likedCount":0,"notLikedCount":1,"ratingCount":1,"reviewCount":1}`，**没有 `score` 字段**——n=1 时 RT 还不显示百分数。也就是说 2026-10-20 这条链的价格是在"n=1、无显示分数"的状态下报出来的。2026-10-21 重抓变成 `0/0/0`（仍**无 `score`**）；RT 计数会漂移，所以任何"当前分数"都要带抓取时刻。
- 相邻档的中间价**逐档单调**（0.9545 > 0.755 > 0.465 > 0.15 > 0.041），没有可利用的单调性破坏；90+/80+ 的 `bestBid`（0.021 / 0.04）与 mid 差异很大，说明尾部档的盘口极薄，**这既是机会也是陷阱**（见成本节）。
- 半价差：70+ 是 `(0.51−0.42)/2 = 4.5¢`、80+ 是 `(0.26−0.04)/2 = 11¢`、90+ 是 `2¢`。**70+ 和 80+ 的半价差比任何合理的模型 edge 都大**，所以这两档只能做 maker。

### 4) "到期没分数"的 14 个全 NO event：两种成因各核一例

- `other-mommy-rotten-tomatoes-score-20261009`：全档（30+/40+/50+/60+/70+）结算 NO；2026-10-20 快照显示 `likedCount:15, notLikedCount:72, score:"17"`，2026-10-21 重抓为 `16/89, score:"18"` → 都是"分数确实低于最低档（30）"，不是缺数据。
- `by-any-means-rotten-tomatoes-score`：全档结算 NO；RT 今天 `likedCount:0, notLikedCount:0, reviewCount:0`、**无 score 字段** → 是"根本没有 Tomatometer"，走了规则里的"no data → No"。
- 两者合计的 14 个里**各占多少，我没有逐个核**，所以尾部概率只能给区间（1.2%–16.5%），这是本条最大的定量弱点。

### 5) Beta 可信区间宽度（我自己用 Beta CDF 二分算的，均匀先验 Beta(k+1, n−k+1)，90% 区间）

| n | k | 点估计 | 90% CI | 宽度 |
|---|---|---|---|---|
| 10 | 6 | 60% | [35.0%, 80.0%] | 45.1 分 |
| 20 | 12 | 60% | [41.7%, 75.5%] | 33.8 分 |
| 20 | 18 | 90% | [72.9%, 96.0%] | 23.1 分 |
| 50 | 30 | 60% | [48.3%, 70.5%] | 22.1 分 |
| 50 | 45 | 90% | [80.5%, 94.8%] | 14.3 分 |
| 100 | 75 | 75% | [67.2%, 81.3%] | 14.1 分 |
| 200* | 150 | 75% | ≈±5.0 分（`1.645×sqrt(0.75×0.25/200)`） | — |

（`*` 最后一行是正态近似手算，不是上表的精确 Beta 计算。）**结论**：n≤50 时 90% 区间比整条档位链还宽，模型只能给"粗方向"；n≈100 时 1–2 分间距的档位仍是 50/50；要到 n 数百，2 分档才可判。这就是"把当前分数当最终分数"必然出错的地方。

### 6) 价格历史存在，但只够做市场侧回测

对已关闭市场 `you-can-see-everything` 的 80+ token（`115247292569760568274899790090301720359959003343471261064290162154153281032682`）取 `prices-history?interval=max&fidelity=60`：**564 个点**，从 `2026-09-25T16:00:19Z` 的 `p=0.8745` 到 `2026-10-19T16:00:22Z` 的 `p=0.9995`，**最低 `p=0.5445` 出现在 `2026-09-26T06:00Z`**；`T−7d p=0.9785`、`T−3d p=0.989`、`T−1d p=0.998`。

- 好消息：**已关闭的 RT 市场有小时级价格历史（`fidelity=60` 分钟，564 个点约合 24 天）**（不像地震那类市场返回 `{"history":[]}`），所以"市场侧"可以事后回测。
- 坏消息：这次暴跌（0.8745 → 0.5445 → 1.0）说明**价格在早期会被单条评论打穿**，而**早期评论的时间序列我拿不到**（下节），所以"模型侧"无法事后回放。**这就是本条仍然不能验证 Beta 模型的原因。**

### 7) 市场侧历史可成交价回测（2026-10-21 新做，模型无关，out-of-sample）

**先说清楚：这一节检验的是"市场价是否已经足够有效"，不是 Beta 模型本身。** 模型侧仍然不可回放（下节），所以不能用这次回测给模型报收益。脚本 `backtest.py` / `extra_stats.py`，stdout 在 `notes/scheduler/scratch/H-quant-016/`。

**样本与可成交价。** 85 个已关闭 event 中 84 个有 `endDate` 且能解析出 `N+` 档（另 1 个 `mufasa` 是区间写法且 `endDate` 为空），共 **525** 个档；结算价全部是 0/1（YES 242、NO 283）。对每个档取 event `endDate` 前 24h 的**最后一笔 data-api 成交**作为可成交价：YES 成交价原样，NO 成交价取 `1−价`；成交必须发生在决策时点前 24h 内。买价再加 **1¢ 半价差**和吃单费 `0.05×q×(1−q)`（`q` 为买入侧价格）。T-24h 有成交的档 **341** 个、event **82** 个（T-48h 374/82、T-6h 413/80、T-7d 109/35）；T-24h 成交距决策时点的中位数 **5.9h**。CLOB `prices-history` 同时取，T-24h 6h 内有价 **495** 个档/82 个 event；用 CLOB 价替代成交价做同一组规则，A/B/C 均值变成 **−0.023901 / −0.024166 / −0.031979**，方向不变（CLOB 点可能是 mid 或 last，不是 ask，所以只作敏感性）。所有规则在写脚本时预注册，没有拟合参数；全部 84 个可用 event 都是样本外，另按 `2026-08-01` 切成两段做稳定性检查。**局限**：成交价不是 ask，可能 stale（中位 5.9h、最长 24h），真实可成交价可能更差；固定 1¢ 半价差对 80+ 档是乐观值（快照 11¢）。这些偏差只会让回测结果更好看，不会让负结果翻正。

**T-24h 价格校准（成交价，按档分桶）**

| YES 价区间 | 档数 | event 数 | 平均价 | 实际 YES 率 | Brier |
|---|---:|---:|---:|---:|---:|
| <0.05 | 156 | 60 | 0.0078 | 0.0000 | 0.0002 |
| 0.05–0.10 | 14 | 13 | 0.0785 | 0.0714 | 0.0639 |
| 0.10–0.25 | 11 | 11 | 0.1642 | 0.1818 | 0.1466 |
| 0.25–0.50 | 8 | 8 | 0.4100 | 0.5000 | 0.2346 |
| 0.50–0.75 | 16 | 14 | 0.6139 | 0.6875 | 0.2271 |
| 0.75–0.90 | 11 | 11 | 0.8275 | 1.0000 | 0.0316 |
| 0.90–0.95 | 9 | 8 | 0.9215 | 1.0000 | 0.0063 |
| ≥0.95 | 116 | 57 | 0.9907 | 1.0000 | 0.0002 |

档级 Brier **0.024829**，常数基率（YES 率 0.451613）的 Brier **0.247659**；按 event 先平均再平均，市场 **0.029557** vs 常数 **0.250723**。也就是说，T-24h 的市场价已经非常准；剩下能赚的钱只能来自"市场价与最终结果之间还没被定价的信息"，而不是"把当前分数当最终分数"这种粗错。

**预注册的三条模型无关规则（T-24h，吃单费 + 1¢ 半价差，持到结算）**

| 规则 | 档数/event 数 | 每份均值 | 每份中位 | 合计 | 每 event 均值 | 正/负 event |
|---|---:|---:|---:|---:|---:|---:|
| A 买 NO，YES 价 ≥0.90 | 125 / 59 | **−0.024966** | −0.020495 | −3.120756 | −0.025633 | 0 / 59 |
| B 买 YES，YES 价 ≤0.10 | 170 / 64 | **−0.018371** | −0.014199 | −3.123080 | −0.011254 | 1 / 63 |
| C 买 NO，0.25≤YES 价≤0.75 | 24 / 22 | **−0.100814** | −0.360254 | −2.419546 | −0.115258 | 9 / 13 |

三条全负；A、B 的正 event 数为 0/59 和 1/63（二项 z ≈ −7.7）。把吃单费改成 0（假设全是 maker）后仍负：A −0.024283、B −0.017724、C −0.089090，所以亏损主要不是手续费，而是"极端价档的结果几乎全 0/1，买两边都要付价差"。分桶表里唯一接近正的是**买 p≥0.90 的 YES**（125 档，均值约 **+0.0036/份**），但这是 1¢ 半价差的乐观值；真实 80+ 档 11¢ 半价差会直接吃掉，而且它也不是条目的方向。按时间切：A 前半 −0.026913（32 event）/后半 −0.023225（27 event），B 前半 −0.013594（36）/后半 −0.024140（28），C 前半 −0.117835（12）/后半 −0.080699（10），两段都负。换决策时点也不翻正：T-48h 的 A/B/C = **−0.033131 / −0.005608 / −0.059512**，T-6h = **−0.017897 / −0.008070 / −0.094716**。

**边界档还剩多少不确定性（描述性，不用来选择交易）**

对每个 event 取"实际结算为 YES 的最大档 `lo`"和"其上方第一个 NO 档 `hi`"。T-24h 有 **65** 个 event 能按 0.5 交叉推出市场边界并与最终边界比较：**完全相同 55/65（84.6%）**，误差 ≤2 分 59/65。另有 **33** 个 event 的 `lo`/`hi` 在 T-24h 都有成交，可看价格：`lo` 中位 **0.872**、`hi` 中位 **0.065**；其中 36.4% 的 `lo` ≥0.95、45.5% 的 `hi` ≤0.05。到 T-6h（54 个 event），这两个比例升到 74.1%/85.2%。**市场在 T-24h 对边界的判断已经与最终边界一致 84.6%，但价格仍留约 13% 的不确定性（`lo` 中位 0.872，不是 0/1）**；留给"1–2 分窄档"的错价空间比条目假设的小，但不是零。

按 T-24h 市场价选边界对（买 YES 市场隐含 `lo`、买 NO 其上一档，51 个 event）：YES 腿均值 **+0.0308**、NO 腿 **−0.0272**，两条腿相加 **+0.0036/event**，扣完成本基本是零。**这条对子不能单独赚钱**。

**一个必须标清楚的探索性结果（不是本条证据）**：把 T-24h 价格在 0.25–0.90 的所有档都买 YES，36 个档/31 个 event，每份均值 **+0.0881**、每 event 均值 **+0.1130**、正/负 22/9，符号检验 **p=0.0294**。这是我看完分桶表后追加的、**没有预注册**，而且是在多个桶里挑出来的；它最多说明"边界附近的 YES 可能被低估"，与条目的 maker 双边规则不是一回事，**不能拿来给 Beta 模型背书**。若要做，必须另立条目、另写预注册规则、前向验证。

**结论（不粉饰）**：市场侧没有找到可用的净 edge；T-24h 的市场已经高度校准，边界档也基本定型。这与条目"市场会把 1–2 分窄档按 0/1 错误定价"的前提**相反**。Beta 模型本身仍无法历史回放（下一节），所以本条不能报任何模型收益；按 GUIDE 第 2 节第 5、6 条，建议降为**待选区**，不要按收录推进。

## 数据

- RT 影片页（免费、免密钥、无需登录）：`https://www.rottentomatoes.com/m/<slug>`。我用 `curl -sL -A "<桌面 UA>"` 拿到 HTTP 200，页面内有一行 JSON：`"criticsScore":{"likedCount":..,"notLikedCount":..,"ratingCount":..,"reviewCount":..,"score":"..","scorePercent":"..%","sentiment":"..","reviewsPageUrl":".."}`。`audienceScore` 是另一个对象，不要混。**注意**：这是抓 HTML，不是官方 API（RT 是否有公开 API：**未查到**）；UA/地区/反爬一变就可能抓不到，本次只是单次成功。
- RT reviews 页（`/m/<slug>/reviews`）：HTTP 200，但**HTML 里 0 个评论日期字段**（`publicationDate/reviewDate/createDate/datePublished` 全部无匹配），列表由 JS 渲染 → **"某时刻已出多少条评论"无法事后回放**。这是本条的硬约束。2026-10-21 又试了 Wayback availability（HTTP 429）、`web.archive.org` CDX（TLS 000）、`archive.ph`（TLS 000）、Common Crawl 索引（HTTP 504），都**未取到**；没有找到任何免费的历史评论数快照。
- Polymarket Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?slug=<event-slug>`（规则原文、各档 `bestBid/bestAsk/outcomePrices/groupItemTitle`、`feeSchedule`、`clobRewards`）；`https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true|false&order=endDate&ascending=false`（数频率）；`https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100`（找同族）。
- Polymarket CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`，也支持 `startTs/endTs`；已关闭市场也有历史。
- Polymarket data-api 逐笔成交（免费免密钥）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`，字段 `side/outcome/price/size/timestamp`，最新在前；已关闭市场可读。本次回测对 525 个档各翻到 `endDate−9d`，共取 525/525 个市场。
- 缺失：历史"当时评论数与新鲜比例"（必须现在起前向记录）；RT 的反爬稳定性；`resolutionSource` 为空导致的具体结算页面；14 个全 NO event 的成因拆分；历史盘口（只有成交价，没有 bid/ask，所以回测只能加固定半价差）。

## 两周内怎么检验

- **独立结果按 event 数**：同一部片的所有档位共用一次结算（同一数据源、同一时点），算 **1 个**结果。两周内到期的是 `2026-10-26` 那批（clayface、klara-and-the-sun、ali-g-who-iz-i、wildwood 共 4 个）和 `2026-11-09` 那批（godzilla-minus-zero、wild-horse-nine 共 2 个）→ **最多 6 个 event**；`2026-11-23`、`2026-12-21` 的三批到期更晚。**因此两周内拿不到 30 个独立结果**，30 个约需 3 个月（按每月 10 个 event）。这一点如实写在这里；按 GUIDE 第 2 节第 6 条，本条应进**待选区**（是否留在待核由整合者按 15 条上限决定）。
- **已经做完的历史检验（不能替代模型检验）**：85 个已关闭 event 的价格侧回测，T-24h 有 341 个档/82 个 event 的可成交价；预注册的 A/B/C 三条规则净收益全负，市场 Brier 0.024829 vs 常数 0.247659（证据 7）。这证明"市场侧能回测、且没有模型无关的便宜可捡"，但**没有**证明 Beta 模型的对错。
- 前向记录（每天 4 次，UTC 00/06/12/18）：每片的 `(k, n, reviewCount, score, 抓取时刻)`；每个档位的 `bestBid/bestAsk/mid/outcomePrices`；我挂的单与实际成交。存成 CSV，字段写死。
- 原计划的"Beta 先验 + 随机子样本"校准模拟**仍未做**：它需要历史 `(k,n)`，而 RT 只给最终计数、reviews 页无日期；在做出来之前不能把它写成证据。
- **失败标准（成交前写死）**：
  1. 至少 1 个 event 结算后，模型对该 event 各档的 Brier 分数**不优于**市场 mid 的 Brier；
  2. 或已成交份额的中位已实现毛利 ≤0（毛利 = 票面 1.00 − 成交价，只算成交，不算未成交挂单）；
  3. 或两周内可用 event < 3 个 / 抓 RT 成功率 < 80% → 判"容量/数据失败"，进待选区而不是算策略失败。
- 按证据 7，标准 1 的前置条件已经很苛刻：T-24h 市场 Brier 只有 0.0248，模型要在 82 个 event 上稳定优于它，必须有市场不知道的评论信息；目前没有证据。
- 不允许的自我安慰：不能因为"挂单没成交"就报正收益；不能只报成交到的那几档。

## 成本与容量

- **费率（Gamma 实取，但会变）**：2026-10-20 快照里本族每个市场是 `feeSchedule = {"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`，与 GUIDE 第 8 节"经济/文化/天气 = 0.05"一致；2026-10-21 重抓，**在开的 9 个 event 中 8 个 `rate=0`（`rebateRate=0`），`ali-g-who-iz-i` 的市场混用 0 与 0.05；85 个已关闭 event 里 70 个是 0.05、15 个是 `None`**。所以不能把 0.05 写成永久事实；下面的算术和回测一律按 **0.05 保守计**（对已关闭样本是实际值，对当前在开市场是高估）。`makerBaseFee=1000`、`takerBaseFee=1000`。
  - 吃单费 = `份数 × 0.05 × p × (1−p)`：`p=0.75` → 每份 `0.05×0.75×0.25 = 0.009375`（占投入 1.25%）；`p=0.9545` → `0.00217`（占投入 0.23%）；`p=0.465` → `0.01244`（占投入 2.68%）。
  - maker 费 0，另返对手吃单费的 `rebateRate=0.25`（25%；2026-10-21 在开市场已变成 0，返佣也归零）。
  - **每笔成本 = 费 + 半个买卖价差**。70+ 档半价差 **4.5¢**、80+ 档 **11¢**（2026-10-20 快照）——比模型在 n≈50 时的可分辨 edge 还大，所以吃单一定不行；maker 的代价换成"排队 + 逆向选择"，后者**未量化**。回测里 1¢ 半价差是乐观值，真实 80+ 档可能是 11¢，只会更差。
- **单笔能放多少**：单档在险 100 份；70+ 档买 YES 于 0.45 ≈ 45 USDT，全链 5 档约 200–500 USDT，但 event 上限 300 USDT 会先撞到。占款天数 = 到 `endDate` 的 10:00 AM ET + 1–3 天结算滞后（`sense-and-sensibility` 实际 event `closedTime` 比规则读数晚约 2 小时）。
- **一个月多少次机会**：近期约 **10 个 event/月**（证据 1），每个 event 3–15 个档 → 每月 60–150 个档位可选；但单个 event 成交额中位只有 **$11,727.77**。2026-10-21 在开的 9 个 event、49 个市场合计 **$70,507.74**，最小的 `dune-part-three` 只有 **$1,062.19**（2026-10-20 快照里 `klara-and-the-sun` 是 $297.91，一天就涨到 $6,072.78），**5,000 USDT 放不满**，给这条线 1,000 USDT 上限就够，剩余资金不被占用。
- **奖励（补贴，不是主收益）**：在开 event 的 `clobRewards` 日率实测 3 / 5 / 10 / 100 USDC/日不等（`klara-and-the-sun`、`ali-g-who-iz-i` 是 100，`avengers-doomsday` 是 3，`godzilla-minus-zero` 有 2 档是 10）；`dune-part-three` 没有 `clobRewards`。按 dot-032 记录的 Q-score 规则分摊，**不能当固定收入**（这类字段随时可改）。
- **容量结论**：单 event 300 USDT、最多 4 个 event 并行 → 1,200 USDT 在险，远低于 2,500 单场所上限；但**容量受 event 成交额限制，不是受我的资金限制**。

## 风险

- **早期评论不是最终评论的随机样本（最大风险，且未量化）**：影评 embargo 分批解禁，先出的一批常是友好媒体/类型片媒体；n=10 时点估计 60% 的片子在 n=200 时可能落到 40%。Beta 区间只覆盖抽样噪声，**不覆盖这种选择性偏差**，所以"模型看起来很准"的假象最可能出在这里。缓解办法只能用前向记录实测"k/n 随 n 的漂移"，两周内看不出来。
- **"到期没有分数"尾部**：14/85 的 event 全档 NO。买 `90+` 的 YES 在缺数据时全损；反过来，**在正确的先验下卖高估的低档**才是这条尾部的用法——但 1.2%–16.5% 的区间太宽，先验选错会直接把正期望做负。
- **取整与边界**：显示分数是 **round half up**，不是 floor（22/22 个页面与 `round(100k/n)` 一致，12 个能区分两者的样本全部 round；见证据 1 前的规则节）。旧稿把它写成 floor 是错的；若模型仍用 floor，`76+`/`77+`、`78+`/`79+` 这种边界会系统性差 1 分，而档位常以 1–2 分间距加密，1 分就是胜负翻转。x.5 的精确边界（half-up/half-even）**未查到**，只能对 T±1 做敏感性。
- **"读哪一分钟"不确定**：规则写 10:00 AM ET，实际 event `closedTime` 是 12:03 PM ET（差约 2 小时）。若最终读数落在两次抓取之间，我可能带着过期的 `(k,n)` 下单。原因**未查到**。
- **抓取风险**：RT 没有公开 API（未查到），我这次是抓 HTML，靠桌面 UA 拿到 200。反爬加强、地区跳转、页面结构改动都会让 `criticsScore` 消失；一旦如此本条直接失效。
- **`resolutionSource` 为空**：规则正文只说 "Rotten Tomatoes"，没给页面。若结算方看的是某个地区站或"Verified"标签下的分数，可能与我读的 `criticsScore` 不同。**未查到**具体页面。
- **取错字段**：同一页 HTML 里还有别的百分数（`sense_and_sensibility_2026` 页面里我正则同时匹配到 `88%`、`81%`、`98%`，来自页内其它模块/推荐位），所以必须从那段 `criticsScore` JSON 里取值，不能用正则捞百分数；抓错字段会让每个档差 10 分以上。是否有独立的 `Top Critics` 字段、它与结算口径的关系：**未查到**。
- **流动性与逆向选择**：`80+` 档 bid 0.04 / ask 0.26，`liquidity` 只有 870.65（2026-10-20 快照）；挂在这种档上成交时很可能是对手拿到了新评论。这个成本**未量化**。
- **价格侧回测为负（新增，最直接的降级理由）**：T-24h 市场 Brier 0.024829（常数 0.247659），预注册的 A/B/C 三条模型无关规则每份净 −0.024966 / −0.018371 / −0.100814，两段时间都负（证据 7）。这说明"窄档错价"的前提在价格数据里看不到；模型即使有 edge，也必须来自市场没有的评论信息，而这条信息恰恰无法历史回放。
- **费率字段会变（新增）**：2026-10-21 在开市场多数 `feeSchedule.rate=0`，已关闭样本仍是 0.05。按 0.05 算是保守，但如果费率长期为 0，成本节的高估会压低表面收益；反过来，若费率再调高，maker 返佣也可能归零。**不要把 2026-10-20 的费率快照当成永久规则。**
- **平台与结算**：`restricted=true`；UMA 提案，`umaBond=500`、`umaReward=5`、`customLiveness=0`，`automaticallyResolved=true`。客观分数出争议概率低，但"数据不可用 → 全判 No"这条兜底对买方是本金全损。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：不确定** — 叙述是清楚的：付钱方是"把当前分数当最终分数"的下注者；定量依据是二项标准差（n=100、p=0.75 时 ±4.3 分）与平台把档位加密到 2 分的实例，以及 14/85 的"无分数"尾部。但 2026-10-21 的价格侧回测（证据 7）显示 T-24h 市场 Brier 0.0248、84.6% 的 event 在 T-24h 已指向正确边界、`lo` 中位价 0.872（不是 0/1），**"市场会把窄档按 0/1 错误定价"这个前提没有被数据支持**。机制故事讲得通，付钱方的存在性没有证据。
2. **有免费数据能检验：不满足（模型侧）** — 市场侧现在有了：Gamma + CLOB + data-api，85 个已关闭 event、525 个档，T-24h 有 341 个档/82 个 event 的可成交价（证据 7）。**模型侧仍不行**：RT reviews 页由 JS 渲染，HTML 里 0 个评论日期字段；Wayback/archive.today/Common Crawl 本次都取不到（429/TLS 000/504），所以"某时刻已出多少条评论、几条新鲜"**无法事后回放**，只能前向记录。历史 ≥30 个独立结果的"模型"数据拿不到。
3. **小资金能做：满足** — 300 USDT/event、≤4 event 并行、总计 ≤1,200 USDT，低于 2,500 单场所与 5,000 总资金；不加杠杆；买单最大亏损就是本金。容量写清了：受 event 成交额（中位 $11,727.77）限制，5,000 USDT 放不满。
4. **不重复：满足** — r1-audit 已判 quant-016 与 quant-010 不同（同属文化 nowcast，但数据源/变量不同）；最近的邻居是 **quant-010（流媒体周榜）** 与 **dot-032（流动性奖励）**，本条收益来源是**评论抽样比例的统计预测**（`category: S`），不是榜单排名（E）也不是奖励份额（M）。共用 Gamma/CLOB 接口不等于同一机制。
5. **扣成本后粗算够用：不满足** — 吃单侧本来就不行（70+ 半价差 4.5¢、80+ 11¢，加 1.25%–2.68% 的吃单费后没有 edge 空间）；本次历史回测把"模型无关的便宜"也排除了：预注册 A/B/C 三条规则每份净 −0.024966 / −0.018371 / −0.100814，maker 费 0 版本仍负，两个时间段都负。Beta 模型本身没被检验，所以不能报正收益；按现有证据，**扣成本后不够用**。
6. **两周内能检验：不满足** — 独立结果按 event 计，两周只到期约 5–6 个 event，凑不到 30；30 个约需 3 个月（每月约 10 个）。历史价格侧虽有 82 个 event，但**模型信号不可回放**，不能用它冒充模型检验。按 GUIDE 第 2 节第 6 条，本类应进**待选区**。
7. **出处可查：满足** — 每个数字都有 URL + 抓取日期 + 取数方式；2026-10-21 我把本条引用的 Gamma/CLOB/RT/data-api 全部重抓了一遍（`verify_sources.py` + `verify_sources.out`），并记录了会漂移的数（在开 47→49 个市场、$56,087→$70,508、`clayface` 费率 0.05→0、`sense` 78/102→82/106、`other_mommy` 15/87→16/89）。我自己算的量（163 / 85 / 530 / 84+1 / $1,818,572.46 / $11,727.77 / 70 与 14 的拆分 / 基率分布 / Beta 区间宽度 / 564 个价格点 / 22 个取整样本 / 341 档回测）都写了公式或中间量，脚本在 `notes/scheduler/scratch/H-quant-016/`。Gamma 自报的 volume/liquidity 标为"来源自报，未核实"。

**总判**：7 条里没有 1 条全满足；门 2、5、6 不满足，门 1 的前提被价格数据削弱。按 GUIDE 第 2 节，本条应进**待选区**（不是收录），建议整合者降级；在拿到可回放的 `(k,n)` 历史序列之前，不要按"策略"推进。

## 出处

- https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100 — 访问 2026-10-20、2026-10-21 — 已读（两次都是 `pagination.totalResults=163`，50 个 event；50/50 的 slug 匹配 `<film>-rotten-tomatoes-score-<date>`；2026-10-21 第一条是 `klara-and-the-sun-rotten-tomatoes-score-20261026`）
- https://gamma-api.polymarket.com/events?slug=clayface-rotten-tomatoes-score-20261026 — 访问 2026-10-20、2026-10-21 — 已读（规则原文含 "at 10:00 AM ET on October 26, 2026"、"All Critics"、"no data ... No"、"October 30, 2026, 11:59 PM ET"；`resolutionSource=""`；2026-10-20 快照 5 档、`feeSchedule.rate=0.05`、volume 4,096.90、liquidity 870.65；2026-10-21 重抓 volume 5,125.88、liquidity 1,507.62、`feeSchedule.rate=0`、五档 outcomePrices 0.8505/0.665/0.320/0.140/0.0445；tags 含 `rotten-tomatoes` id 101453）
- https://gamma-api.polymarket.com/events?slug=sense-and-sensibility-rotten-tomatoes-score-20261019 — 访问 2026-10-20、2026-10-21 — 已读（11 档全部已结算；YES 档 60/65/70/72/74/75/76，NO 档 78/80/85/90；event `closedTime=2026-10-19T16:03:29Z`、市场级 `umaEndDate` 在 16:02:02–16:03:29 之间、`umaResolutionStatus=resolved`、`automaticallyResolved=true`、`umaBond=500`、`umaReward=5`、`customLiveness=0`、`resolutionSource=""`）
- https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false — 访问 2026-10-20、2026-10-21 — 已读（两次都是 85 个已关闭 event、530 个市场、合计 $1,818,572.46；中位 $11,727.77、最大 $241,440.63；按月 11/10/12/9/4/17/12/9，合计 84，另 1 个 `endDate` 为空）
- https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=false&order=endDate&ascending=false — 访问 2026-10-20、2026-10-21 — 已读（2026-10-20：9 个在开 event、47 个市场、$56,087.15；2026-10-21：9 个、49 个市场、$70,507.74；逐 event 的 volume 与 `clobRewards` 日率会漂移）
- https://gamma-api.polymarket.com/events?tag_slug=culture&limit=3 — 访问 2026-10-20 — 已读（HTTP 200，但返回 0 个 event；仅用于确认 tag 端点可达，本条实际用的是 event 自带的 `rotten-tomatoes` tag）
- https://gamma-api.polymarket.com/tags?limit=200 — 访问 2026-10-20 — 已读（请求 limit=200 但实际只返回 100 条，`rotten-tomatoes` 不在其中；tag 是从 event 对象里读到的）
- https://clob.polymarket.com/prices-history?market=115247292569760568274899790090301720359959003343471261064290162154153281032682&interval=max&fidelity=60 — 访问 2026-10-20、2026-10-21 — 已读（564 个点，0.8745@2026-09-25T16:00:19Z → 最低 0.5445@2026-09-26T06:00:18Z → 0.9995@2026-10-19T16:00:22Z；T−7d=0.9785、T−3d=0.989、T−1d=0.998；已关闭 RT 市场**有**价格历史）
- https://data-api.polymarket.com/trades?market=0x9bd927360a0fc46492f245d2d1bc4b6ef3fcbe750f916c59df0837b1eef259b3&limit=5&offset=0 — 访问 2026-10-21 — 已读（HTTP 200，5 笔；字段含 `side/outcome/price/size/timestamp`，最新在前；本次回测用同一端点对 525 个档翻页到 `endDate−9d`，`verify_sources.out` 有原始 5 笔）
- https://www.rottentomatoes.com/m/clayface — 访问 2026-10-20、2026-10-21 — 已读（2026-10-20：HTTP 200，180,045 字节，`"criticsScore":{"likedCount":0,"notLikedCount":1,"ratingCount":1,"reviewCount":1,...}`；2026-10-21：176,744 字节，`0/0/0`；两次都**无 `score` 字段**）
- https://www.rottentomatoes.com/m/sense_and_sensibility_2026 — 访问 2026-10-20、2026-10-21 — 已读（2026-10-20：`likedCount:78, notLikedCount:24, reviewCount:102, score:"76"`，`78/102=0.7647`；2026-10-21：`82/24/106, score:"77"`，`82/106=0.7736`；两版都与四舍五入一致，旧稿"floor"推断错误）
- https://www.rottentomatoes.com/m/other_mommy — 访问 2026-10-20、2026-10-21 — 已读（2026-10-20：`15/72/87, score:"17"`，`15/87=0.1724`；2026-10-21：`16/73/89, score:"18"`，`16/89=0.1798`；后者只有 round 能解释，floor 会给 17）
- https://www.rottentomatoes.com/m/by_any_means — 访问 2026-10-20、2026-10-21 — 已读（`likedCount:0, notLikedCount:0, reviewCount:0`，**无 `score` 字段** → 该 event 全档 NO 属"缺数据"路径，不是"分数低"）
- https://www.rottentomatoes.com/m/sense_and_sensibility_2026/reviews — 访问 2026-10-20、2026-10-21 — **抓到了 HTTP 200 但不可用**（2026-10-21 是 96,727 字节；`publicationDate/reviewDate/dateCreated/datePublished/createDate` 匹配数全部 0，列表为 JS 渲染）→ 历史"当时已出评论数"无法回放，这是本条没有模型侧回测的直接原因
- 取整样本（22 个 RT 影片页，2026-10-21 抓，`check_rounding.out`）：`https://www.rottentomatoes.com/m/the_wild_robot`（252/261=96.5517→97，floor 96）、`.../inside_out_2`（298/329=90.5775→91，floor 90）、`.../klara_and_the_sun`（5/21=23.8095→24，floor 23）、`.../wicked_for_good`（234/356=65.7303→66，floor 65）、`.../project_hail_mary`（407/430=94.6512→95，floor 94）等 — 访问 2026-10-21 — 已读；22/22 与 round 一致，12 个能区分 floor/round 的样本全部是 round
- https://web.archive.org/、https://archive.ph/、https://index.commoncrawl.org/ — 访问 2026-10-21 — **未取到**（Wayback availability HTTP 429、CDX TLS 000；archive.today TLS 000；Common Crawl 索引 HTTP 504），所以没有历史评论数快照；不据此写任何数字
- https://docs.polymarket.com/ 系列文档 — **本次未抓**，故不引用；费率取自各市场 `feeSchedule` 实取值与 GUIDE 第 8 节表格
- 本次脚本与 stdout：`bots/quant/notes/scheduler/scratch/H-quant-016/`（`fetch_data.py`、`backtest.py`、`extra_stats.py`、`check_rounding.py`、`verify_sources.py` 及对应 `.out`；原始缓存 `_cache/` 已 gitignore，单文件 <1 MB）

---
