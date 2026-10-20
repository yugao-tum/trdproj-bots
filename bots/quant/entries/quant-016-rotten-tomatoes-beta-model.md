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
data: RT 影片页 `criticsScore`（likedCount / notLikedCount / reviewCount，免费免密钥，抓 HTML）；Polymarket Gamma（规则、盘口、feeSchedule、clobRewards）与 CLOB prices-history（已关闭市场也有 1 分钟历史）；**历史"当时已出评论数"取不到**（RT reviews 页日期由 JS 渲染，HTML 里 0 个日期字段），所以早期评论侧只能从现在起前向记录
test_2w: 独立结果按 event 计（同片各档共享一次结算，算 1 个）；两周只覆盖 2026-10-26 与 2026-11-09 两批共约 5–6 个 event，凑不到 30；失败标准：模型对已结算 event 的 Brier/log loss 不优于市场中间价，或已成交份额中位已实现毛利 ≤0
status: 待核
confidence: 中
---

整理说明：本条所有 Polymarket 计数、分档频率、盘口价格都是我在 2026-10-20 用下文 URL 现抓后自己算的（脚本 `calc_rt.py`，全文见 `notes/batch2-verification/quant-016.md`）；RT 那边的"分数=新鲜评论数/(新鲜+烂)"公式我用两部片子的实际页面核对过。**没有做回测**：历史"某时刻已出多少条评论、其中几条新鲜"取不到（见数据节），所以只有"模板+基率+当期横截面"的证据，不是收益证明。

## 一句话

在某片 RT 开分前后的窗口里，从影片页读出**已出评论数 n 与其中新鲜条数 k**，用 Beta(k+1, n−k+1) 得到最终 Tomatometer（RT 显示的是 `floor(100k/(k+n))`）的分布，再折算成"P(最终 ≥ T)"；只在某个档位的买价/卖价与该概率的偏离超过"吃单费 + 半个价差 + 2 分安全垫"时挂 **maker** 单，持到 10:00 AM ET 那次读数结算。

## 钱从哪里来

付钱给你的是**把"当前显示分数"当成"最终分数"的下注者**，以及只看新闻情绪不看样本量的人。这条钱能持续存在，是因为窄档的**抽样噪声本身**就足以让档位接近抛硬币：Tomatometer 是 k/(k+n) 的比例，二项标准差在 p=0.75、n=100 时是 `sqrt(0.75×0.25/100) = 0.0433`，即 **±4.3 分**；而 Polymarket 常把档位加密到 **2 分甚至 1 分间距**（见证据 3 的实例：`74+/72+/76+`、`48+/49+/51+`）。也就是说，即使当期分数完全公开，1–2 分间距的档位在 n≈100 时仍然是真随机；市场若按"离当期分数近就归 0/1"来定价，就会在这类档位上系统性给错价。第二个来源是**"到期没分数"的尾部**：85 个已关闭 event 里有 **14 个（16.5%）全部档位都结算 NO**（见证据 2、4），谁在低估这个尾部，钱就是他的。

## 规则

**结算原文（Gamma 事件 `clayface-rotten-tomatoes-score-20261026` 与 `sense-and-sensibility-rotten-tomatoes-score-20261019`，2026-10-20 已读，两片文字只差片名/日期）**：

- 触发条件：「This market will resolve to "Yes" if the displayed Rotten Tomatoes "All Critics" Tomatometer score for Clayface is at least equal to the specified number **at 10:00 AM ET on October 26, 2026**」——是**某一个时点**的读数，不是"曾经达到"，也不是"最终"。
- 口径：「**All Critics** Tomatometer」= 影评人侧（RT 页面 JSON 里的 `criticsScore`），**不是** Popcornmeter/Verified Audience；同一页的 `audienceScore` 在 clayface 上是 `"reviewCount":0` 的独立对象，两者不可混用。
- 阈值结构：同一 event 内多个**累积**档（`50+/60+/70+/80+/90+`，`groupItemTitle` 形如 `70+`），各自是独立二元市场，`negRisk=false`；因此"70+ = YES"和"60+ = YES"会同时成立，档与档之间是**单调约束**（P(80+) ≤ P(70+)），不是互斥分桶。少数 event 用区间写法（如 `mufasa-the-lion-king-rotten-tomatoes-score` 有 `<60`、`60-69`、`70-79`、`80-89`、`90+` 五个区间档）。
- **没有分数怎么办**：「If, for any reason, the resolution data is unavailable at this market's specified end time, the resolution source will be checked until the relevant data is available. This market will resolve to **"No"** if no data is available by October 30, 2026, 11:59 PM ET.」——即"到期没有 Tomatometer"会让**全部档位判 NO**（`by-any-means-rotten-tomatoes-score` 就是这种：RT 页面 `reviewCount:0`、无 score 字段，全部档位结算 NO）。
- 结算源字段：两个 event 的 `resolutionSource` 都是**空字符串**（实抓），规则正文只说 "Rotten Tomatoes"，**没有给出具体 URL**；用哪个页面、要不要地区站，**未查到**。
- 时区与取整：规则写美东时间 10:00 AM；显示分数是整数百分比（取整口径见下）。
- 我核到的取整口径（这是本条最关键的一条规则细节）：`sense_and_sensibility_2026` 页面 `likedCount:78, notLikedCount:24, reviewCount:102, score:"76"`，`78/102 = 0.7647` → 显示 **76**（向下取整，不是四舍五入）；`other_mommy` 页面 `likedCount:15, notLikedCount:72` → `15/87 = 0.1724` → 显示 **17**。两个点都只与"截断"一致。**后果**：`76+` 判 YES、`78+` 判 NO（该 event 实际就是这么结算的），而真实比例 76.47% 离 78% 只差 1.5 分——边界档的价格对这条口径极其敏感。
- 实际结算时点与规则文字的差：`sense-and-sensibility` 的 event `closedTime` 是 `2026-10-19 16:03:29+00`（= 12:03 PM ET），比规则写的 10:00 AM ET 晚约 2 小时；市场级字段 `umaEndDate=2026-10-19 16:02:05+00`、`umaResolutionStatus=resolved`、`automaticallyResolved=true`、`customLiveness=0`、`umaBond=500`、`umaReward=5`（这些是市场级、不是 event 级）。为什么晚 2 小时，**未查到**，但这说明"读的是哪一分钟的分数"有数小时不确定性。

**交易规则（本条的提案，未验证）**

1. 每小时抓一次目标影片的 RT 页，记录 `(k=likedCount, n=k+notLikedCount, reviewCount, score)` 与抓取时刻（UTC）。
2. 概率：潜在比例 `p ~ Beta(k+1, n−k+1)`（均匀先验；也可用证据 2 的基率分布做先验）。判据 `档位 T 为 YES ⟺ floor(100p) ≥ T ⟺ p ≥ T/100`，故 `P_T = 1 − F_Beta(T/100; k+1, n−k+1)`。对同一 event 的档位，事后强制单调化（把违反 P(高) ≤ P(低) 的值做保序回归），因为规则结构保证单调。
3. 尾部：`P(到期无分数)` 另算，先验取 `1/85`（已核实的 `by_any_means` 一例）到 `14/85`（全档 NO 的上界）之间，按 1.2%–16.5% 处理；无分数时全档 NO。这个先验**必须在成交前写死**。
4. 只在 `|P_T − mid_T| > fee_rate×p×(1−p) + 半价差 + 0.02` 时下单；只挂 maker（不吃单），限价 `买 YES = P_T − 0.01`、`买 NO = (1−P_T) − 0.01`。若没有排队价值（我的价差于对手最优价）则跳过。
5. 仓位：单档在险 ≤ 100 份；单 event 全部档位合计 ≤ 300 USDT；同时在手 ≤ 4 个 event；单场所 ≤ 2,500 USDT、总资金 5,000 USDT。
6. 出场：持有到结算，不主动平仓（票面收敛免费）；`k+n < 5` 且离读数 > 48 小时时撤掉全部挂单（样本量太小时模型无意义，RT 也不显示分数）。
7. 熔断：抓取失败或页面 `criticsScore` 缺失时，该 event 全部挂单撤掉；`n` 相比上一小时**下降**（RT 撤评论）时也撤。
8. 明确不做：不做区间写法（`<60`）的档位（口径与累积档不同，样本太少）；不做观众分/爆米花桶。

## 证据

### 1) 模板和频率（Gamma 实抓，我数的）

- `public-search?q=rotten tomatoes&limit_per_type=100` 返回 `pagination.totalResults = 163`；同结果里 50 个 event 的 slug 全是 `<film>-rotten-tomatoes-score-<YYYYMMDD>` 形态（个别 `-rotten-tomato-score`）。
- 用 event 自带 tag（`rotten-tomatoes`，id 101453；同 event 另有 `movies`(53)、`pop-culture`(596)）拉清单：`tag_slug=rotten-tomatoes&closed=false` → **9** 个在开 event、47 个市场、成交额合计 **$56,087.15**；`closed=true&limit=500` → **85** 个已关闭 event、**530** 个市场、成交额合计 **$1,818,572.46**。
- 每个 event 的市场数：平均 **6.24**，最少 3、最多 15。
- 已关闭 event 的成交额：中位 **$11,727.77**、均值 $21,394.97、最大 **$241,440.63**。
- 按 `endDate` 月份数已关闭 event：2026-03 **11**、04 **10**、05 **12**、06 **9**、07 **4**、08 **17**、09 **12**、10 **9**（10 月未完）→ **近期约每月 10 个 event**（8 个月均值 10.5）。2026-07 只有 4 个，说明密度会波动，**不能把 8 月的 17 个外推**。

### 2) 最终分数的基率（我用 85 个已关闭 event 的结算结果算的）

对每个 event，取"结算为 YES 的最大档位 `lo`"和"其上方第一个结算为 NO 的档位 `hi`"，得到最终分数区间 `[lo, hi)`：

- **70/85** 个 event 至少有一个档位结算 YES；**14/85（16.5%）** 所有档位全 NO；1 个是区间写法（`<60`）不计入。
- 70 个 event 的最终分数（按 10 分桶）：`[20,30):3`、`[30,40):4`、`[40,50):5`、`[50,60):10`、`[60,70):4`、`[70,80):15`、`[80,90):12`、`[90,100]:17`。
- 派生：`P(最终 ≥ 80) = 29/70 = 0.4143`；`P(≥ 90) = 17/70 = 0.2429`；`P(< 60) = 22/70 = 0.3143`；最终 `lo` 的中位数 = **74**；相邻档中位间距 = **5 分**（最小 1、最大 20）。
- 这就是 Beta 模型的先验形状：大致双峰（一半在 ≥80，三成在 <60），**中间 60–70 只有 4/70**——均值附近的片子本来就少，所以"共识在 60–70"的定价错了会很贵。

### 3) 当期横截面（Gamma 快照 2026-10-20，`clayface`，`endDate 2026-10-26T14:00:00Z`）

`volume=4096.90`、`liquidity=870.65`、`openInterest=1234.13`、`negRisk=false`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`。

| 档 | bestBid | bestAsk | mid | `outcomePrices` | volume | `clobRewards` 日率 |
|---|---|---|---|---|---|---|
| 50+ | 0.932 | 0.977 | 0.9545 | `["0.9545","0.0455"]` | 185.88 | 3 |
| 60+ | 0.61 | 0.90 | 0.755 | `["0.755","0.245"]` | 563.93 | 3 |
| 70+ | 0.42 | 0.51 | 0.465 | `["0.465","0.535"]` | 440.99 | 3 |
| 80+ | 0.04 | 0.26 | 0.15 | `["0.15","0.85"]` | 2307.23 | 5 |
| 90+ | 0.021 | 0.061 | 0.041 | `["0.041","0.959"]` | 598.87 | 3 |

- 同日 RT 页面：`clayface` 的 `criticsScore = {"likedCount":0,"notLikedCount":1,"ratingCount":1,"reviewCount":1}`，**没有 `score` 字段**——n=1 时 RT 还不显示百分数。也就是说 2026-10-20 这条链的价格是在"n=1、无显示分数"的状态下报出来的。
- 相邻档的中间价**逐档单调**（0.9545 > 0.755 > 0.465 > 0.15 > 0.041），没有可利用的单调性破坏；90+/80+ 的 `bestBid`（0.021 / 0.04）与 mid 差异很大，说明尾部档的盘口极薄，**这既是机会也是陷阱**（见成本节）。
- 半价差：70+ 是 `(0.51−0.42)/2 = 4.5¢`、80+ 是 `(0.26−0.04)/2 = 11¢`、90+ 是 `2¢`。**70+ 和 80+ 的半价差比任何合理的模型 edge 都大**，所以这两档只能做 maker。

### 4) "到期没分数"的 14 个全 NO event，两种成因我都核了

- `other-mommy-rotten-tomatoes-score-20261009`：全档（30+/40+/50+/60+/70+）结算 NO；RT 今天显示 `likedCount:15, notLikedCount:72, score:"17"` → 是"分数确实低于最低档"，不是缺数据。
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

### 6) 价格历史存在，但这不足以回测

对已关闭市场 `you-can-see-everything` 的 80+ token（`115247292569760568274899790090301720359959003343471261064290162154153281032682`）取 `prices-history?interval=max&fidelity=60`：**564 个点**，从 `2026-09-25T16:00:19Z` 的 `p=0.8745` 到 `2026-10-19T16:00:22Z` 的 `p=0.9995`，**最低 `p=0.5445` 出现在 `2026-09-26T06:00Z`**；`T−7d p=0.9785`、`T−3d p=0.989`、`T−1d p=0.998`。

- 好消息：**已关闭的 RT 市场有完整到 1 分钟的价格历史**（不像地震那类市场返回 `{"history":[]}`），所以"市场侧"可以事后回测。
- 坏消息：这次暴跌（0.8745 → 0.5445 → 1.0）说明**价格在早期会被单条评论打穿**，而**早期评论的时间序列我拿不到**（下节），所以"模型侧"无法事后回放。**这就是本条只有草稿、没有回测的原因。**

## 数据

- RT 影片页（免费、免密钥、无需登录）：`https://www.rottentomatoes.com/m/<slug>`。我用 `curl -sL -A "<桌面 UA>"` 拿到 HTTP 200，页面内有一行 JSON：`"criticsScore":{"likedCount":..,"notLikedCount":..,"ratingCount":..,"reviewCount":..,"score":"..","scorePercent":"..%","sentiment":"..","reviewsPageUrl":".."}`。`audienceScore` 是另一个对象，不要混。**注意**：这是抓 HTML，不是官方 API（RT 是否有公开 API：**未查到**）；UA/地区/反爬一变就可能抓不到，本次只是单次成功。
- RT reviews 页（`/m/<slug>/reviews`）：HTTP 200，但**HTML 里 0 个评论日期字段**（`publicationDate/reviewDate/createDate/datePublished` 全部无匹配），列表由 JS 渲染 → **"某时刻已出多少条评论"无法事后回放**。这是本条的硬约束。
- Polymarket Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?slug=<event-slug>`（规则原文、各档 `bestBid/bestAsk/outcomePrices/groupItemTitle`、`feeSchedule`、`clobRewards`）；`https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true|false&order=endDate&ascending=false`（数频率）；`https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100`（找同族）。
- Polymarket CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`；已关闭市场也有历史。
- 缺失：历史"当时评论数与新鲜比例"（必须现在起前向记录）；RT 的反爬稳定性；`resolutionSource` 为空导致的具体结算页面；14 个全 NO event 的成因拆分；逐笔成交（data-api 每市场约最近 2 万笔，本条未取）。

## 两周内怎么检验

- **独立结果按 event 数**：同一部片的所有档位共用一次结算（同一数据源、同一时点），算 **1 个**结果。两周内到期的是 `2026-10-26` 那批（clayface、klara-and-the-sun、ali-g-who-iz-i、wildwood 共 4 个）和 `2026-11-09` 那批（godzilla-minus-zero、wild-horse-nine 共 2 个）→ **最多 6 个 event**；`2026-11-23`、`2026-12-21` 的三批到期更晚。**因此两周内拿不到 30 个独立结果**，30 个约需 3 个月（按每月 10 个 event）。这一点如实写在这里，`status` 只给 `草稿`。
- 前向记录（每天 4 次，UTC 00/06/12/18）：每片的 `(k, n, reviewCount, score, 抓取时刻)`；每个档位的 `bestBid/bestAsk/mid/outcomePrices`；我挂的单与实际成交。存成 CSV，字段写死。
- 可先做的**不需要未来数据**的一步（两周内能完成）：用 70 个已结算 event 做校准对照——把"最终分数"换成"只用 Beta 先验 + 已知 n 条评论"的模拟（假设早期评论是最终评论的随机子样本），算模型 log loss vs 常数基率 log loss，看"随机子样本"假设能把基率改进多少。这检验的是模型骨架，不检验 edge。
- **失败标准（成交前写死）**：
  1. 至少 1 个 event 结算后，模型对该 event 各档的 Brier 分数**不优于**市场 mid 的 Brier；
  2. 或已成交份额的中位已实现毛利 ≤ 0（毛利 = 票面 1.00 − 成交价，只算成交，不算未成交挂单）；
  3. 或两周内可用 event < 3 个 / 抓 RT 成功率 < 80% → 判"容量/数据失败"，进待选区而不是算策略失败。
- 不允许的自我安慰：不能因为"挂单没成交"就报正收益；不能只报成交到的那几档。

## 成本与容量

- **费率（Gamma 实取，不是查表）**：本族每个市场的 `feeSchedule = {"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`，与 GUIDE 第 8 节"经济/文化/天气 = 0.05"一致；`makerBaseFee=1000`、`takerBaseFee=1000`。
  - 吃单费 = `份数 × 0.05 × p × (1−p)`：`p=0.75` → 每份 `0.05×0.75×0.25 = 0.009375`（占投入 1.25%）；`p=0.9545` → `0.00217`（占投入 0.23%）；`p=0.465` → `0.01244`（占投入 2.68%）。
  - maker 费 0，另返对手吃单费的 `rebateRate=0.25`（25%）。
  - **每笔成本 = 费 + 半个买卖价差**。70+ 档半价差 **4.5¢**、80+ 档 **11¢**——比模型在 n≈50 时的可分辨 edge 还大，所以吃单一定不行；maker 的代价换成"排队 + 逆向选择"，后者**未量化**。
- **单笔能放多少**：单档在险 100 份；70+ 档买 YES 于 0.45 ≈ 45 USDT，全链 5 档约 200–500 USDT，但 event 上限 300 USDT 会先撞到。占款天数 = 到 `endDate` 的 10:00 AM ET + 1–3 天结算滞后（`sense-and-sensibility` 实际 event `closedTime` 比规则读数晚约 2 小时）。
- **一个月多少次机会**：近期约 **10 个 event/月**（证据 1），每个 event 3–15 个档 → 每月 60–150 个档位可选；但单个 event 成交额中位只有 **$11,727.77**（在开的 9 个里最小的只有 **$297.91**：`klara-and-the-sun`），**5,000 USDT 放不满**，给这条线 1,000 USDT 上限就够，剩余资金不被占用。
- **奖励（补贴，不是主收益）**：在开 event 的 `clobRewards` 日率实测 3 / 5 / 10 / 100 USDC/日不等（`klara-and-the-sun`、`ali-g-who-iz-i` 是 100，`avengers-doomsday` 是 3，`godzilla-minus-zero` 有 2 档是 10）；`dune-part-three` 没有 `clobRewards`。按 dot-032 记录的 Q-score 规则分摊，**不能当固定收入**（这类字段随时可改）。
- **容量结论**：单 event 300 USDT、最多 4 个 event 并行 → 1,200 USDT 在险，远低于 2,500 单场所上限；但**容量受 event 成交额限制，不是受我的资金限制**。

## 风险

- **早期评论不是最终评论的随机样本（最大风险，且未量化）**：影评 embargo 分批解禁，先出的一批常是友好媒体/类型片媒体；n=10 时点估计 60% 的片子在 n=200 时可能落到 40%。Beta 区间只覆盖抽样噪声，**不覆盖这种选择性偏差**，所以"模型看起来很准"的假象最可能出在这里。缓解办法只能用前向记录实测"k/n 随 n 的漂移"，两周内看不出来。
- **"到期没有分数"尾部**：14/85 的 event 全档 NO。买 `90+` 的 YES 在缺数据时全损；反过来，**在正确的先验下卖高估的低档**才是这条尾部的用法——但 1.2%–16.5% 的区间太宽，先验选错会直接把正期望做负。
- **取整与边界**：显示分数是 `floor`，`76.47 → 76`。我的模型若用四舍五入，`76+`/`77+` 这种边界会系统性算错 1 分；而档位常以 1–2 分间距加密，1 分就是 100% 的胜负翻转。
- **"读哪一分钟"不确定**：规则写 10:00 AM ET，实际 event `closedTime` 是 12:03 PM ET（差约 2 小时）。若最终读数落在两次抓取之间，我可能带着过期的 `(k,n)` 下单。原因**未查到**。
- **抓取风险**：RT 没有公开 API（未查到），我这次是抓 HTML，靠桌面 UA 拿到 200。反爬加强、地区跳转、页面结构改动都会让 `criticsScore` 消失；一旦如此本条直接失效。
- **`resolutionSource` 为空**：规则正文只说 "Rotten Tomatoes"，没给页面。若结算方看的是某个地区站或"Verified"标签下的分数，可能与我读的 `criticsScore` 不同。**未查到**具体页面。
- **取错字段**：同一页 HTML 里还有别的百分数（`sense_and_sensibility_2026` 页面里我正则同时匹配到 `88%`、`81%`、`98%`，来自页内其它模块/推荐位），所以必须从那段 `criticsScore` JSON 里取值，不能用正则捞百分数；抓错字段会让每个档差 10 分以上。是否有独立的 `Top Critics` 字段、它与结算口径的关系：**未查到**。
- **流动性与逆向选择**：`80+` 档 bid 0.04 / ask 0.26，`liquidity` 只有 870.65；挂在这种档上成交时很可能是对手拿到了新评论。这个成本**未量化**。
- **平台与结算**：`restricted=true`；UMA 提案，`umaBond=500`、`umaReward=5`、`customLiveness=0`，`automaticallyResolved=true`。客观分数出争议概率低，但"数据不可用 → 全判 No"这条兜底对买方是本金全损。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付钱方是"把当前分数当最终分数"的下注者；定量依据是二项标准差（n=100、p=0.75 时 ±4.3 分）与平台把档位加密到 2 分的实测实例，以及 14/85 的"无分数"尾部。但"这钱是否持续"只有横截面 + 结构论证，**没有时序证据**。
2. **有免费数据能检验：不确定** — 市场侧完美（Gamma + CLOB，已关闭 event 也有 1 分钟历史，564 个点实测）；**模型侧不行**：RT reviews 页由 JS 渲染，HTML 里 0 个评论日期字段，所以"某时刻已出多少条评论、几条新鲜"**无法事后回放**，只能前向记录。历史 ≥30 个独立结果的"模型"数据拿不到。
3. **小资金能做：满足** — 300 USDT/event、≤4 event 并行、总计 ≤1,200 USDT，低于 2,500 单场所与 5,000 总资金；不加杠杆；买单最大亏损就是本金。容量写清了：受 event 成交额（中位 $11,727.77）限制，5,000 USDT 放不满。
4. **不重复：不确定，需主审确认** — 我 grep 了 `known/KNOWN.md`、全部 `bots/*/CLAIMS.md`、`bots/*/entries/`：RT/烂番茄/票房关键词只命中 `bots/dot/notes/20261019-research-plan.md`（调研计划，不是条目）与 `bots/quant/CLAIMS.md` 里我自己这条 B13。最近的邻居是 **quant-010（流媒体周榜，culture，用每日公开榜单提前估周榜）** 与 **dot-032（流动性奖励，用 clobRewards 字段）**：本条收益来源是**评论抽样比例的统计预测**（`category: S`），不是榜单排名（E）也不是奖励份额（M）；共用的是 Gamma/CLOB 接口，这一点与 quant-012 共用 USGS 之外无重叠。区别写在"钱从哪里来"而不是"换个市场"。
5. **扣成本后粗算够用：不确定** — 吃单侧明确不行（70+ 半价差 4.5¢、80+ 11¢，加 1.25%–2.68% 的吃单费后没有 edge 空间）；maker 侧费率为 0，但**成交概率与逆向选择未量化**，`observed_net_return = null`、`backtest_count = 0`（只表示没有回测，不表示收益为 0）。不报盈亏数字。
6. **两周内能检验：不满足** — 独立结果按 event 计，两周只到期约 5–6 个 event，凑不到 30；30 个约需 3 个月（每月约 10 个）。按 GUIDE 第 2 节第 6 条，本类应进**待选区**。
7. **出处可查：满足** — 每个数字都有 URL + 抓取日期 + 取数方式；我自己算的量（163 / 85 / 530 / 9 / $1,818,572.46 / $11,727.77 / 70 与 14 的拆分 / 基率分布 / 78÷102=76.47→76 / 15÷87=17.24→17 / Beta 区间宽度 / 564 个价格点）都写了公式或中间量，脚本全文在 `notes/batch2-verification/quant-016.md`。Gamma 自报的 volume/liquidity 标为"来源自报，未核实"。

## 出处

- https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100 — 访问 2026-10-20 — 已读（`pagination.totalResults=163`，50 个 event，slug 形态 `<film>-rotten-tomatoes-score-<date>`）
- https://gamma-api.polymarket.com/events?slug=clayface-rotten-tomatoes-score-20261026 — 访问 2026-10-20 — 已读（规则原文、5 档 bid/ask/outcomePrices、`feeSchedule.rate=0.05`、`clobRewards` 3/5、`negRisk=false`、volume 4096.90、liquidity 870.65；tags 含 `rotten-tomatoes` id 101453）
- https://gamma-api.polymarket.com/events?slug=sense-and-sensibility-rotten-tomatoes-score-20261019 — 访问 2026-10-20 — 已读（11 档全部已结算；60–76 为 YES、78/80/85/90 为 NO，event `closedTime=2026-10-19 16:03:29+00`、市场级 `umaEndDate=2026-10-19 16:02:05+00`、`resolutionSource=""`）
- https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（85 个已关闭 event、530 个市场、合计 $1,818,572.46，按月分布 11/10/12/9/4/17/12/9）
- https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=false&order=endDate&ascending=false — 访问 2026-10-20 — 已读（9 个在开 event、47 个市场、合计 $56,087.15，逐 event 的 volume 与 `clobRewards` 日率）
- https://gamma-api.polymarket.com/events?tag_slug=culture&limit=3 — 访问 2026-10-20 — 已读（HTTP 200，但返回 0 个 event；仅用于确认 tag 端点可达，本条实际用的是 event 自带的 `rotten-tomatoes` tag）
- https://gamma-api.polymarket.com/tags?limit=200 — 访问 2026-10-20 — 已读（请求 limit=200 但实际只返回 100 条，其中与本主题相关的只有 `caesars-entertainment`，说明 tag 清单不能这样枚举；`rotten-tomatoes` tag 是从 event 对象里读到的）
- https://clob.polymarket.com/prices-history?market=115247292569760568274899790090301720359959003343471261064290162154153281032682&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（564 个点，0.8745@2026-09-25T16:00Z → 最低 0.5445@2026-09-26T06:00Z → 0.9995@2026-10-19T16:00Z；已关闭 RT 市场**有**价格历史）
- https://www.rottentomatoes.com/m/clayface — 访问 2026-10-20 — 已读（HTTP 200，180,045 字节；`"criticsScore":{"likedCount":0,"notLikedCount":1,"ratingCount":1,"reviewCount":1,...}`，**无 `score` 字段**）
- https://www.rottentomatoes.com/m/sense_and_sensibility_2026 — 访问 2026-10-20 — 已读（HTTP 200，236,529 字节；`"likedCount":78,"notLikedCount":24,"reviewCount":102,"score":"76","scorePercent":"76%"`，`78/102=0.7647`→显示 76；同页其它模块另有 `88%`/`81%`/`98%` 等百分数，故只能认 `criticsScore` 字段）
- https://www.rottentomatoes.com/m/other_mommy — 访问 2026-10-20 — 已读（HTTP 200；`"likedCount":15,"notLikedCount":72,"reviewCount":87,"score":"17"`，`15/87=0.1724`→17）
- https://www.rottentomatoes.com/m/by_any_means — 访问 2026-10-20 — 已读（HTTP 200，145,244 字节；`"likedCount":0,"notLikedCount":0,"reviewCount":0`，**无 `score` 字段** → 该 event 全档 NO 属"缺数据"路径，不是"分数低"）
- https://www.rottentomatoes.com/m/sense_and_sensibility_2026/reviews — 访问 2026-10-20 — **抓到了 HTTP 200 但不可用**（96,227 字节；`publicationDate/reviewDate/createDate/datePublished` 匹配数 0，`reviewCount` 匹配数 0，列表为 JS 渲染）→ 历史"当时已出评论数"无法回放，这是本条没有回测的直接原因
- https://docs.polymarket.com/ 系列文档 — **本次未抓**，故不引用；费率取自各市场 `feeSchedule` 实取值与 GUIDE 第 8 节表格

---
