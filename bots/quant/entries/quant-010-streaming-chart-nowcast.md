---
id: quant-010
name_zh: 周榜日更抢跑
name_en: Weekly Chart Nowcast (Netflix / Spotify)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: culture
kind: new
improves: -
category: E
return_type: direction
instruments: Polymarket 每周榜单冠军二元市场（Netflix / Spotify 每周 #1 模板）
venues: Polymarket
data: Gamma 规则与盘口（免费免密钥）；Netflix Tudum 周榜（免费）；kworb.net Spotify 日榜（免费免密钥，本次已验证）；FlixPatrol 日榜本次返回 403；历史盘口无公开来源
test_2w: 用至少 30 个周榜事件回放“日榜→官方周榜 #1”的信号命中率；失败=命中率<80% 或扣费后中位净收益≤0；历史价格只能前向记录
status: 待核
confidence: 中
---

## 一句话

在 Netflix 周二、Spotify 周五官方周榜发布前的 12–72 小时，用公开日榜估算已基本锁定的冠军；只有当 YES 卖价低于“日榜估算胜率 − 吃单费 − 半个价差”时才买入，否则不交易。

## 钱从哪里来

赚的是“结果已基本发生、官方榜单尚未发布”这段信息差。官方周榜由上一周的观看/播放量决定，而公开日榜会逐日暴露这些量；若市场还停在旧价格，官方榜发布后价格向 0/1 收敛，早买入的人赚这段收敛。付款方是未及时更新价格的对手方，不是平台补贴。该机制每周重复，但**是否存在错价完全取决于当时盘口**，本条不假定每周都有钱赚。

## 规则

### 市场模板与示例

- 模板：`Will "<剧名/歌名>" be the #1 [US/global] [Netflix show / Spotify song] this week?`，同一事件下 14–17 个市场（含候选、占位与 `Other`），属于 negRisk 多选事件。
- Netflix 示例：`what-will-be-the-top-global-netflix-show-this-week-october-20`（2026-10-20 抓取，17 个市场，`negRisk=true`，event `volume=5065.164545`、`liquidity=4423.9158`；来源自报，未核实）。其中 `Below: Limited Series` 市场 `outcomePrices=["0.9975","0.0025"]`、`bestBid=0.997`、`bestAsk=0.998`、`spread=0.001`、`volume=1153.424795`。
- Netflix 美国示例：`what-will-be-the-top-us-netflix-show-this-week-october-20`（16 个市场，event `volume=1834.890906`、`liquidity` 随时变动（来源自报，未核实；2026-10-20T04:08:56Z 抓到 6734.08，04:19:29Z 抓到 6952.27）；`Below` 市场 `outcomePrices=["0.995","0.005"]`、`bestBid=0.991`、`bestAsk=0.999`、`spread=0.008`）。
- Spotify 示例：`1-spotify-song-this-week-october-16-20261012`（2026-10-16 周，14 个市场，`volume=8072.917061`；`KAROL G - BbY WOW` 市场 `outcomePrices=["1","0"]`、`volume=4383.916683`）。
- Spotify 美国在跑示例：`1-spotify-song-in-the-us-this-week-october-23-10172026`（15 个市场，`volume=8505.801068`、`liquidity=10002.81181`；`Housewife` 市场 `outcomePrices=["0.9615","0.0385"]`、`bestBid=0.938`、`bestAsk=0.985`、`spread=0.047`、`volume=2337.933896`；`Nicole Kidman` 市场 `outcomePrices=["0.028","0.972"]`、`bestBid=0.011`、`bestAsk=0.045`、`spread=0.034`）。

### 结算规则原文要点

- Netflix：`resolutionSource=https://www.netflix.com/tudum/top10/tv`；规则写“Netflix is expected to update its global Top 10 TV shows list on top10.netflix.com on **Tuesday, October 20, 2026, 3:00 PM ET**, reflecting viewership from the **previous week (Monday to Sunday)**”。按该次更新排出的 **#1 global** 结算；并列时按剧名字母序；排名是“total views globally, as reported by Netflix for TV shows (**English only**)”。若 2026-10-23 23:59 ET 前未更新，结算 `Other`。
- Spotify：`resolutionSource=https://open.spotify.com/charts`；规则写 Spotify “updates it on **Fridays** to reflect streaming data for the previous week, **beginning on the preceding Friday and ending on Thursday**”，按“week labeled October 16”的全球最多播放歌曲结算；若 2026-10-17 23:59 ET 前未发布，默认 `Other`。美国版同样按“week labeled October 23”、美国最多播放歌曲。
- 两类的共同点：官方榜是唯一结算源；`Other` 兜底；并列规则（Netflix 字母序）必须按原文，不能用第三方榜的并列处理替代。
- 时区与截止：Netflix 发布时点是 ET 下午 3 点、10-23 23:59 ET 兜底；Spotify 是周五发布、周六 23:59 ET 兜底。官方发布的**具体小时**除 Netflix 的 3:00 PM ET 外，Spotify 只写“Fridays”，未查到具体时刻。

### 进场、出场、仓位

- 观察窗口：Netflix 周一 00:00 ET（周日数据结束后）至周二 15:00 ET；Spotify 周四夜（本周五至周四的 7 天走完）至周五官方榜发布前。
- 信号：把本周已过天数的日榜播放量/排名加总，得到候选的领先幅度；只在“领先幅度已大于日榜本身波动、且剩余天数不足以翻盘”时，才把该候选视为高置信领先者。具体阈值需用历史回放校准，本文不写死一个未经检验的数字。
- 进场：只挂**限价买单**，价格 ≤ 估算胜率 − 费用缓冲；不追 ask。若只能吃单，要求 `估算胜率 − ask − 吃单费 − 半个价差 > 0` 才买；否则放弃。
- 出场：持有到结算（官方榜发布后），不设止损式的二次交易；若官方榜延迟，按 `Other` 规则处理，不假设一定按候选结算。
- 仓位：单事件候选合计 ≤ 500 USDC，同时在跑 ≤ 2 个事件；单场所 ≤ 2,500 USDC、总资金 5,000 USDC。不用杠杆，不裸卖。
- 独立结果：按“榜单-周”计，不按市场数。同一周的 Netflix 美国 + 全球算 1 簇（同一结算源、同一周、高度相关）；Spotify 全球 + 美国同理算 1 簇；同一周的 #1 与 #2 也算同一簇。

### 频率

- Netflix：每周一次，周二 15:00 ET 更新；美国榜与全球榜各一个事件，另有 #2 等变体。2026-10-20 当天可见 `what-will-be-the-top-us-netflix-show-this-week-october-20`、`what-will-be-the-top-global-netflix-show-this-week-october-20`。
- Spotify：每周一次，周五更新；本次搜到同一周（10-16）的全球 #1、全球 #2、美国 #1、美国 #2 四个事件（只拉取全球 #1 的 14 个市场，其余市场数未核）。
- 独立机会约 2 簇/周（Netflix 1 + Spotify 1），约 8–9 簇/月；但“有错价的机会”远少于此，未查到可靠计数。

## 证据

- Gamma 规则与盘口（2026-10-20 抓取，对象 `updatedAt` 约 `2026-10-20T04:00:46Z`）：上列 event/market 的 `resolutionSource`、`description`、`outcomePrices`、`bestBid/bestAsk`、`spread`、`volume`、`liquidity`、`feeSchedule`。这些是 **Gamma 自报，未核实**（未用成交回执或链上结算复现）。
- 日榜可读性（本次实测）：`https://kworb.net/spotify/country/global_daily.html` 返回 HTTP 200，页面写 “Spotify Daily Chart - Global - **2026/10/18**”，第 1 名 “KAROL G - BbY WOW (w/ Judeline , rusowsky)”，当日 “**4,719,966**” streams、7Day “**35,919,162**”。`https://kworb.net/spotify/country/us_daily.html` 返回 200，页面写 “Spotify Daily Chart - United States - 2026/10/18”，第 1 名 “Tate McRae - Housewife”，当日 “**1,127,046**” streams。kworb 首页写 “Aggregates of all daily and weekly charts provided by Spotify”。以上为 **kworb 自报，未核实**，但页面免费、免密钥、本次可直接读取。
- 官方周榜可读性：`https://www.netflix.com/tudum/top10/tv` 返回 200，页面显示 “Global | **10/5/26 - 10/11/26**”，第 1 名 “Below: Limited Series”，Views “**17,000,000**”，Hours Viewed “**69,300,000**”；美国页 `https://www.netflix.com/tudum/top10/united-states/tv` 返回 200，显示 “United States | 10/5/26 - 10/11/26”，第 1 名同为 Below。页面含最早到 `2021-06-28` 的日期字符串（本次正则统计），但“是否每周齐全”未核。
- 日榜与盘口的方向一致性（只作观察，不作盈利证明）：Spotify 美国 10-23 周，kworb 2026/10/18 日榜第 1 是 Housewife，Gamma 同日盘口把 Housewife 定价 `0.9615`（bid 0.938 / ask 0.985）；这说明市场已把日榜领先计入，**不等于**还有错价。
- Netflix 日榜：`https://flixpatrol.com/top10/netflix/world/` 本次 curl 返回 **HTTP 403**（加 `Mozilla/5.0` UA 仍 403），未能读取页面；因此“FlixPatrol 免费免密钥可用”**未核实**，本节不把它当作已证实数据源。Netflix App 内的每日 Top 10 也没有公开网页入口被本次取到。
- 未做回测：`backtest_count=0`，`observed_net_return=null`。本文只证明规则、日榜可读性和盘口结构，不证明扣费后为正。

## 数据

- Gamma：`https://gamma-api.polymarket.com/events?slug=<event-slug>`、`https://gamma-api.polymarket.com/public-search?q=<关键词>`；免费、免密钥；给规则原文、event/market、`outcomePrices`、`bestBid/bestAsk`、`spread`、`volume`、`feeSchedule`、`endDate`。历史已结算 event 可按 slug 查（`closed=true` 参数本次未验证）；历史**盘口**无公开来源（按 GUIDE 第 8 节）。
- Netflix 官方周榜：`https://www.netflix.com/tudum/top10/tv`（全球）、`https://www.netflix.com/tudum/top10/united-states/tv`（美国）；免费、免密钥；本次可直接读，含周标签、Views、Hours Viewed。历史周标签最早见 `2021-06-28`；覆盖面待核。
- Spotify 日榜：`https://kworb.net/spotify/` 首页 + `country/global_daily.html` + `country/us_daily.html`；免费、免密钥；本次读到 2026/10/18 的当日 streams 与 7Day 累计。是否提供逐日历史页、能回溯到哪一天，本次**未核**。
- 结算源官网：`https://open.spotify.com/charts`（规则指定）；本次只按 Gamma 规则引用，未从该页解析出榜单数据；`https://charts.spotify.com/charts/view/regional-global-weekly/latest` 返回 200（12650 bytes），但页面为前端应用，本次未取到可引用数字，故不作数据源。
- FlixPatrol：`https://flixpatrol.com/top10/netflix/world/` 本次 403，未读到；不作为已证实来源。
- 缺失：历史可执行 bid/ask、逐日 Netflix 官方日榜、Spotify 官方日榜历史、候选市场的完整已结算价格序列。

## 两周内怎么检验

1. **信号回放（可历史做）**：取至少 30 个“榜单-周”事件（Netflix 周榜从 Tudum 周标签取，Spotify 若 kworb 历史可取则取；否则只做 Netflix）。对每个事件，在官方发布前 24 小时（Netflix 周一 15:00 ET；Spotify 周四 23:00 ET）只用当时可得的日榜/上周榜，输出一个 #1 预测；与官方最终 #1 对比。独立结果按“榜单-周”计，不按候选市场数；Netflix 美国+全球同一周合并为 1 个，Spotify 全球+美国同一周合并为 1 个。两周内可整理 30 个历史周（Netflix 页面含 2021 起日期），但 Spotify 历史日榜是否齐备未核。
2. **价格与成本（只能前向）**：从 2026-10-20 起，每日记录候选的 `bestBid/bestAsk`、`spread`、`feeSchedule`，以及发布前 24h/12h 的日榜快照。两周只有约 4 个“榜单-周”簇，**不足以**得到 30 个带价格的结果；因此两周只能验证信号命中率，不能验证 30 个盈利结果。不得把 4 个前向结果冒充 30 个。
3. **失败标准（预先写死）**：
   - 信号：30 个历史周中，发布前 24h 的 #1 预测命中率 < 80%，判失败。
   - 成本：前向每笔按“吃单费 + 半个价差”计，若已成交样本的中位净收益 ≤ 0，判失败。
   - 若无法取得至少 30 个独立周事件，或无法取得可执行 bid/ask，结论写“未验证”，不写“有效”。
4. **进出场口径**：只回放“发布前买入、结算后退出”，不混入发布后追涨；同一周多候选只取一个预测，不做事后挑赢家。

## 成本与容量

- 费率：上述 Netflix、Spotify 市场的 Gamma `feeSchedule` 均为 `{"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`，`feeType="culture_fees"`。按 GUIDE 第 8 节，文化类吃单费率 0.05；吃单费 = 份数 × 0.05 × p × (1−p)。挂单不收费（Gamma 标 `takerOnly=true`；返佣 `rebateRate=0.25` 不计入主账本）。
- 示例 A（买热门，吃单）：Housewife YES，100 份，ask `0.985`，bid `0.938`，mid `0.9615`。
  - 本金 = 100 × 0.985 = **98.50 USDC**。
  - 吃单费 = 100 × 0.05 × 0.985 × (1−0.985) = **0.073875 USDC**。
  - 半个价差 = (0.985−0.938)/2 × 100 = **2.35 USDC**。
  - 总成本 = 0.073875 + 2.35 = **2.423875 USDC**，占本金 **2.46%**（2.423875/98.50）。
  - 若赢，净 = 100 − 98.50 − 2.423875 = **−0.923875 USDC**。即：**即使 100% 会赢，按 ask 吃单也亏**。这是本条最重要的成本事实。
- 示例 B（买冷门，吃单）：Nicole Kidman YES，100 份，ask `0.045`，bid `0.011`。
  - 本金 = 4.50 USDC；吃单费 = 100 × 0.05 × 0.045 × 0.955 = **0.214875 USDC**；半个价差 = (0.045−0.011)/2 × 100 = **1.70 USDC**；总成本 **1.914875 USDC**，占本金 **42.55%**。
  - 按市场 mid 0.028 计，100 份的期望赔付仅 2.80 USDC，已低于 4.50 本金，更不用说费用；说明冷门 ask 的价差极贵。
- 示例 C（近确定，吃单）：Netflix `Below`，ask `0.998`、bid `0.997`，100 份：本金 99.80；费 = 100×0.05×0.998×0.002 = 0.00998；半个价差 = 0.05；总成本 0.05998，占本金 0.0601%；若赢净 +0.14002。费用很低，但剩余空间也只有 0.14%，且“是否真的 99.8%”才是风险。
- 结论：**吃单买热门/冷门都不划算**；可行路径只能是 maker 限价单（无费）在 mid 或更好价格成交，或等到 ask 因竞争收窄。maker 成交概率、排队和逆向选择未知，本文不假设必成交。
- 容量：Housewife 市场 `volume=2337.933896`、event `volume=8505.801068`、`liquidity=10002.81181`；Netflix 全球 event `volume=5065.164545`、`liquidity=4423.9158`。单事件 100–500 份、约 100–500 USDC 名义上可放；但本次未取 L2 深度，该价位是否有足够深度**未验证**。同时 2 个事件 ≤ 1,000 USDC，低于单场所 2,500 USDC 上限。5,000 USDC 总资金放得下，但**容量不等于可赚**。
- 占款天数：Netflix 从周一买入到周二结算约 1–2 天；Spotify 从周四夜到周五/周六结算约 1–2 天。年化必须按实际占款天数换算，不能把单次 4% 当成年化 4%。

## 风险

- **没有错价**：本文观察到的 Housewife 已被定价 0.9615，说明市场会读日榜；多数周可能没有可交易价差。
- **日榜≠官方榜**：kworb 是第三方聚合，官方 Spotify 榜的口径、去重、地区归属可能不同；Netflix 全球榜还有 “English only” 限定，第三方全球榜常把非英语剧也算进去，直接用会选错。
- **日榜延迟/修订**：Spotify 日榜可能晚一天、后续修订；Netflix 官方没有公开日榜，FlixPatrol 本次 403，Netflix 日榜信号实际上**未验证可取得**。
- **并列与 Other**：Netflix 并列按字母序，第三方榜的并列处理可能不同；官方延迟更新会结算 `Other`，买入的候选可能归零。
- **价差与流动性**：热门 bid/ask 可差 4.7¢（Housewife `0.938/0.985`），冷门价差可达 3.4¢；薄盘口下 500 份也可能推动价格。
- **结算延迟/争议**：规则指定官方榜为源，但发布延迟、页面缓存、地区版本差异都可能造成争议；`Other` 兜底不等于按你的候选结算。
- **数据与回测**：历史盘口无公开来源，无法做完整历史价格回测；`backtest_count=0`。两周前向只有约 4 个独立簇，不足 30 个。
- **竞争**：其他交易者同样读 kworb/Tudum，错价会被迅速抹平；maker 单还可能被逆向选择。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清**：满足 — 官方周榜由上一周观看/播放量决定，公开日榜逐日暴露该量；付款方是未及时更新价格的对手方。只证明机制，不证明有错价。
2. **有免费数据能检验**：不确定 — Netflix 周榜、kworb Spotify 日榜本次均免费免密钥可读；但 Netflix 日榜源（FlixPatrol）403、历史可执行盘口缺失、Spotify 历史日榜未核，30 个带价格的独立结果不能保证。
3. **小资金能做**：满足（有条件）— 100 份热门约 98.50 USDC、冷门约 4.50 USDC，单事件 ≤ 500 USDC、同时 ≤ 2 个事件，远低于 2,500 USDC；但吃单买热门即使赢也亏，必须 maker 或更优价格，成交不保证。
4. **不重复**：不确定 — 本次未读 `CLAIMS.md`/`known/` 做完整去重；按机制看是“周榜结果已基本发生、官方发布前定价”，与做市奖励、持有奖励不同，但需主审确认是否已有同类条目。
5. **扣成本后粗算够用**：不满足 — 示例 A 按 ask 吃单即使 100% 赢也净亏 0.923875 USDC；示例 B 冷门成本占本金 42.55%；只有 maker 在 mid 附近成交才有空间，而成交概率未验证。没有回测，不能写正收益。
6. **两周内能检验**：不确定 — 历史信号回放可凑 30 个 Netflix 周（页面含 2021 起日期），但 Spotify 历史日榜未核；带价格的前向两周只有约 4 簇，不足 30；失败标准已写死。
7. **出处可查**：满足 — 规则、盘口、日榜、周榜均有 URL、访问日期和原文片段；FlixPatrol 403 已如实标注，未当作已读。

## 出处

- https://gamma-api.polymarket.com/events?slug=what-will-be-the-top-global-netflix-show-this-week-october-20 — 访问 2026-10-20 — 已读（规则原文、17 个市场、价格/盘口/费用）
- https://gamma-api.polymarket.com/events?slug=what-will-be-the-top-us-netflix-show-this-week-october-20 — 访问 2026-10-20 — 已读（16 个市场、价格/盘口）
- https://gamma-api.polymarket.com/events?slug=1-spotify-song-this-week-october-16-20261012 — 访问 2026-10-20 — 已读（Spotify 全球 #1 规则、14 个市场、费用）
- https://gamma-api.polymarket.com/events?slug=1-spotify-song-in-the-us-this-week-october-23-10172026 — 访问 2026-10-20 — 已读（Spotify 美国在跑示例、价格/盘口）
- https://gamma-api.polymarket.com/events?slug=1-song-on-spotify-this-week-april-3 — 访问 2026-10-20 — 已读（历史 Spotify 周规则写法）
- https://gamma-api.polymarket.com/public-search?q=netflix — 访问 2026-10-20 — 已读（搜到 Netflix 周事件与 #2 事件）
- https://gamma-api.polymarket.com/public-search?q=spotify — 访问 2026-10-20 — 已读（搜到 Spotify 周/月事件）
- https://gamma-api.polymarket.com/public-search?q=spotify%20song%20this%20week%20october%2016 — 访问 2026-10-20 — 已读（全球/美国 #1/#2 四个事件）
- https://gamma-api.polymarket.com/public-search?q=spotify%20song%20this%20week%20october%2023 — 访问 2026-10-20 — 已读（美国 10-23 事件）
- https://kworb.net/spotify/ — 访问 2026-10-20 — 已读（“Aggregates of all daily and weekly charts provided by Spotify”）
- https://kworb.net/spotify/country/global_daily.html — 访问 2026-10-20 — 已读（2026/10/18 全球日榜，第 1 名 4,719,966 streams）
- https://kworb.net/spotify/country/us_daily.html — 访问 2026-10-20 — 已读（2026/10/18 美国日榜，第 1 名 1,127,046 streams）
- https://www.netflix.com/tudum/top10/tv — 访问 2026-10-20 — 已读（Global 10/5/26–10/11/26，第 1 名 17,000,000 views）
- https://www.netflix.com/tudum/top10/united-states/tv — 访问 2026-10-20 — 已读（United States 10/5/26–10/11/26，第 1 名 Below）
- https://flixpatrol.com/top10/netflix/world/ — 访问 2026-10-20 — 失败（HTTP 403，含 Mozilla UA 仍 403，未读，不作数据源）
- https://charts.spotify.com/charts/view/regional-global-weekly/latest — 访问 2026-10-20 — HTTP 200 但未解析出榜单数字，不作数据源
- https://gamma-api.polymarket.com/events?slug=top-netflix-show-this-week — 访问 2026-10-20 — HTTP 200，返回 `[]`，说明该猜测 slug 不存在
