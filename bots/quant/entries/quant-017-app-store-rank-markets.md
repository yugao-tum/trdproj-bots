---
id: quant-017
name_zh: App Store榜首榜：按Apple免费榜单定价
name_en: Polymarket "#1/#2 Free App in the US Apple App Store on <date>" priced off Apple's public top-free chart feed
bot: quant
date: 2026-10-20
market: polymarket
pm_category: tech
kind: new
improves: -
category: E
return_type: direction
instruments: Polymarket negRisk 组「某应用是否在 <日期> 12:00 PM ET 时是美国 iPhone App Store 免费榜第 N 名」（N=1、2；另有付费榜、Play 榜同模板），每臂一个二元市场，并带一个不可成交的 `Other` 兜底臂
venues: Polymarket
data: Apple 公开榜单 JSON（rss.applemarketingtools.com 与 itunes.apple.com，免费免密钥，只有当前快照，2026-10-20 已取）+ 结算源网页 apps.apple.com/us/charts/iphone（已取，HTML 内嵌同样序列）；Polymarket Gamma/CLOB（免费免密钥）；已关闭市场 CLOB 价格历史返回 0 点，无法回测
test_2w: 独立结果按「日期」计（同一天 #1/#2 两臂共享同一次榜单快照，只算 1 个），近期每月约 4 个结算日 → 两周只有约 2 个，凑不到 30；失败标准：结算日窗口内的成交单中位已实现毛利≤0，或 RSS 榜单与结算源网页榜单不一致的比例>2%
status: 草稿
confidence: 中
---

整理说明：本条所有 Apple 榜单数字是我在 2026-10-20 04:2x UTC 现场拉取两个免费端点并逐位比对得到的（脚本 `appstore_rank_check.py`、`appstore_winners.py`，全文见 `notes/batch2-verification/quant-017.md`）；所有价格与规则是同一时段 Gamma 快照。**没有做回测**：已关闭 App Store 市场的 CLOB 价格历史返回 0 个点（实测），所以只有「当前榜单 vs 当前挂牌」的横截面对照和「谁赢过」的结算基率，不是收益证明。

## 一句话

在 Polymarket 每周五结算的「<日期> 12:00 PM ET 时谁是免费榜第 1/第 2」negRisk 组上，用 Apple 免费榜单 JSON 判断当日实际名次：只在结算日 11:00–12:00 ET 之间、当榜单已经显示某个**已上市候选**就是第 N 名、而它的 YES 卖价明显低于 1 时买 YES（或买该候选的 NO 当它明显不是第 N 名），持到结算；不做结算日前几天的「名次黏性」方向单。

## 钱从哪里来

付钱给你的是**在结算日最后几十分钟里没有去看 Apple 榜单、只按旧叙事和稀薄盘口报价的对手方**。规则把结果固定成「某个指定时刻（12:00 PM ET）的一次榜单快照」，而这份榜单本身是 Apple 免费公开、每两分钟左右刷新一次的 JSON（实测 `updated` 字段从 04:23:37 到 04:25:44 +0000，两次抓取的 top5 完全一致），因此临近 12:00 ET 时答案实际上已经可读，价格却常常还停在几小时前的水平。这笔钱持续存在的原因是结构性的：这些 board 的盘口很薄（见成本节：`#2` board 的 Vinted 一臂买价 0.16 / 卖价 0.63，价差 0.47），做市的人不愿意在最后半小时收紧报价，而结算窗口只有几分钟，抢这个窗口的人少。

## 规则

**结算规则原文要点（Gamma 事件 `2-free-app-in-the-us-apple-app-store-on-october-23-10172026`，2026-10-20 已读）**：

- 结算口径：「according to the iOS app, ranked #2 in the United States on the iPhone Apple App Store's overall Top Charts under "Free Apps", **as of 12:00 PM ET on the specified date**」——是**某一时点**，不是「曾经达到」，也不是当日平均。
- 结算源：「To find the overall chart, click "Apps" at the bottom of the US iOS App Store app, scroll down to "Top Free Apps" and click "See All". Then under "Free Apps" in the "Top Charts" section, you'll see the list ...(https://apps.apple.com/us/charts/iphone)」——结算源是 Apple 自己的榜单页/App 内榜单，不是第三方 tracker。
- 缺数据兜底：「If the chart is unavailable at 12:00 PM ET, this market may remain open for up to 48 hours ... If the data remains unavailable, this market will resolve according to the last published ranking.」——即 12:00 ET 取不到就延后，最终按最后一次发布的榜单。
- 结构：`negRisk=true`；实测该事件 **12 个市场**，其中 7 个是真候选（Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / McDonald's / KICK），另有 **4 个 `Reserved app 2..5` 和 1 个 `Other`**，这 5 个当时 `outcomePrices=["0.5","0.5"]`、`bestBid=0`、`bestAsk=1`、volume 0（我实取的字段）——即**占位臂、不可成交**。已关闭的 20 个同类事件里，市场数是 18–26 个且没有 `Reserved` 残留（见证据 3），说明候选臂会在结算前被补上；「未上市应用拿了第 N」时的兜底就是 `Other`。
- 时间：本次示例 `startDate=2026-10-17T21:06:16Z`（开盘距结算约 6 天）、`endDate=2026-10-23T23:59:00Z`。注意 **`endDate` 是 23:59 UTC = 19:59 ET，不是结算时刻**；结算时刻是规则写的 2026-10-23 12:00 PM ET（10 月为 EDT=UTC−4，即 16:00 UTC）。
- 同族模板：`#1 Free App`、`#2 Free App`、`#1 Paid App`、`#2 Paid App`（同一日期各一个事件），另有 Play Store 榜同模板（`1-free-app-in-play-store-on-december-19`）。

**交易规则（本条的提案，不是已验证的盈利规则）**

1. 只在**结算日** 11:00–12:00 ET（15:00–16:00 UTC）行动。11:50 ET 之后不再新建单。
2. 每分钟同时拉 `rss.applemarketingtools.com/.../top-free/50/apps.json` 和结算源网页 `apps.apple.com/us/charts/iphone`，取第 N 位应用名。两者必须一致，否则跳过（今天的实测：两处顺序完全一致，见证据 1）。
3. 若第 N 位 = 已上市候选 X，且 X 的 YES 最优卖价 ≤ `1 − 吃单费 − 2¢`：买 YES X，持有到结算。
4. 若第 N 位 = 已上市候选 Y，而另一个已上市候选 Z ≠ Y：可买 NO Z（NO 卖价 = 1 − Z 的 YES 买价），价格条件同上。同一 board 同一时刻只做一个方向，不做「全 basket 买 NO」。
5. 若第 N 位是**未上市**应用：今天就是这种情况（实测第 1 名是 Capital One Mobile，而 `#1` board 的 7 个真候选里没有它），只能走 `Other` 臂，而 `Other` 报价 0/1 不可成交 → **不做**。
6. 仓位：单 market ≤ 200 份 / ≤ 200 USDT，单日 ≤ 3 个 board，合计 ≤ 600 USDT；总资金 5,000 USDT、单场所不超 2,500 USDT。
7. 出场：不主动平仓，持有到 UMA 结算（规则允许延后 48 小时）；平仓要再付一次吃单费+价差，票面 1.00 的收敛是免费的。
8. 明确不做：结算日之前（T−6 到 T−1）按「名次黏性」做方向单——没有免费历史可以估黏性（见证据 4），只允许记录前向样本。

## 证据

### 1）Apple 侧：两个免费端点当前序列一致，且与结算源网页顺序一致

- `rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` → HTTP 200，`country=us`，`updated=Tue, 20 Oct 2026 04:25:44 +0000`，50 条。top5 = `Capital One Mobile, Vinted: Pre-loved marketplace, Muse from Meta, ChatGPT, TikTok Pro - Events`。
- `itunes.apple.com/us/rss/topfreeapplications/limit=25/json` → HTTP 200，25 条。与上面**逐位相同 25/25**，集合交集 25/25。
- 结算源 `apps.apple.com/us/charts/iphone` → HTTP 200，1,017,064 字节；HTML 内嵌的名字顺序为 `Capital One Mobile → Vinted: Pre-loved marketplace → Muse from Meta → ChatGPT → TikTok Pro - Events → PineDrama - Short Dramas → McDonald's → Claude by Anthropic → Google Gemini → ...`，与 JSON 前 5 位一致，第 7/8 位（McDonald's 在 Claude 之前）也与 JSON 里 `McDonald's rank=7, Claude rank=8` 一致。**这是我算的比对，不是来源自报。**
- 7 个真候选在 top-free-50 里的当前名次（我算的）：Vinted 2、Muse from Meta 3、ChatGPT 4、TikTok Pro 5、McDonald's 7、Claude 8、KICK 不在 top 50。

### 2）市场侧：同一时刻的挂牌价（Gamma 快照，2026-10-20 04:2x UTC）

`#1 Free App on October 23`（`1-free-app-in-the-us-apple-app-store-on-october-23-10172026`）：volume 5,918.22、liquidity 5,058.13（来源自报，未核实），7 个真候选：

| 候选 | YES `outcomePrices` | bestBid | bestAsk | 当前真实名次 |
|---|---|---|---|---|
| Muse from Meta | 0.725 | 0.71 | 0.74 | 3 |
| Vinted | 0.072 | 0.045 | 0.099 | 2 |
| ChatGPT | 0.065 | 0.052 | 0.078 | 4 |
| Claude by Anthropic | 0.0315 | 0.003 | 0.06 | 8 |
| KICK | 0.01 | 0.002 | 0.018 | >50 |
| Google Gemini | 0.005 | 0.001 | 0.009 | 12 |
| TikTok Pro | 0.0045 | 0.001 | 0.008 | 5 |

- 七个真候选 YES 之和 **0.913**，买价之和 **0.814**，卖价之和 **1.012**（我算的）。
- 当前真实第 1 名 Capital One Mobile **不在任何一臂上**（不在 7 个真候选，也不在 `Reserved`/`Other` 之外的位置——`Other` 是唯一兜底），而市场把 Muse from Meta（当前第 3）定到 0.725。**这是「市场在按叙事而不是按当前榜单定价」的直接证据**，但注意：距离结算还有 3 天，Muse 也可能是未来的第 1 名，本条不据此断言它高估。
- `#2 Free App on October 23`（`2-free-app-...`）：volume 3,197.81、liquidity 1,672.68；真候选 YES 之和 **0.894**；Vinted（当前真实第 2）0.395，买价 0.16 / 卖价 0.63（价差 0.47）；Muse 0.1555、ChatGPT 0.1485、TikTok Pro 0.0975、KICK 0.048、McDonald's 0.0285、Claude 0.021。
- 两边都带 `clobRewards`（`#2` board 日率 Vinted 54 / Muse 17 / ChatGPT 16 / TikTok 8 / KICK 5 USDC，`rewardsMinSize=20`、`rewardsMaxSpread=4.5`、`startDate=2026-10-20`）；仅作补贴，不进主收益。

### 3）`Other` 的结算基率：20 个已关闭 `free app` 事件里 3 个是 `Other` 赢（我数的）

数据：`public-search?q=app store` 返回的 50 个事件里，46 个 `closed`，其中标题含 `free app` 的 30 个；把 30 个 slug 批量丢给 `events?slug=...` 取回 **20 个**（其余 10 个在本次批量请求里没回来，未取）。按「YES 结算价 > 0.5 的臂」定赢家：

- 赢家是**已上市候选**：17 / 20；赢家是 **`Other`**：3 / 20 → **`Other` 基率 15%（3/20）**。
- 3 次 `Other` 分别出现在 `endDate` 2025-12-05、2025-12-19、2025-12-26（各有一个 board 的赢家是 `Other`）。
- 这 20 个事件的 `endDate` 从 2025-10-17 到 2026-01-23，市场数 18–26 个，`Reserved` 残留 0 个（都被改名成真实应用），全部带 `Other` 臂。**结论：候选臂会在结算前扩充**，所以「今天的第 1 名没上市」不等于它届时仍没上市；结算日必须重读候选清单。
- 结算结果取自 Gamma `outcomePrices`，**未用 UMA 提案或 Apple 当期页面复核，来源自报，未核实**。

**用这个基率做的算术（买全 basket NO 值不值）**：`#1` board 七个真候选全买 NO，成本 = `7 − ΣbestBid = 7 − 0.814 = 6.186`；`Other` 赢则收 7，任一上市候选赢则收 6。吃单费逐臂 `0.05·p·(1−p)`（p = NO 卖价 = 1 − YES 买价）：Muse 0.0103、Vinted 0.00215、ChatGPT 0.00247、Claude 0.00015、KICK 0.00010、Gemini 0.00005、TikTok 0.00005，合计 **0.0153/份**。于是净成本 6.2013，盈亏平衡需要 `P(Other) = 0.2013 → 20.1%`，而基率是 **15%**，**当前买价下这是负 EV**（`#2` board 更差：`7 − 0.36 = 6.64`，需要 P(Other)=64%）。这两个数字就是本条不做 basket 单的理由。

### 4）名次黏性：免费历史**未查到**

- 没找到免费的 App Store 榜单历史序列：`web.archive.org/cdx/search/cdx?url=<rss.applemarketingtools.com 的 top-free JSON>`、`url=<rss.marketingtools.apple.com 的同路径>`、`url=apps.apple.com/us/charts/iphone` 三次 CDX 查询**都返回空**（无快照）。第三方 tracker 多为付费，未取。
- 已关闭市场的 CLOB 价格历史也取不到：`clob.polymarket.com/prices-history?market=<2025-11-21 那个 `#1` board 的 ChatGPT 臂 token>&interval=max&fidelity=60` → HTTP 200，`history` **0 个点**。
- 因此本条**没有任何名次黏性基率**，不写「3 天内第 1 名保持率 x%」这类数字。能做的只有前向记录（见下节）。`observed_net_return=null`、`backtest_count=0`（只表示没做回测，不表示收益为 0）。

### 5）频率与规模（我数的）

- `public-search?q=app store` 返回 `pagination={"hasMore":true,"totalResults":247}`（来源自报，未核实），第一页 50 个事件里 `closed=46`、按 `endDate` 月份：2025-11 **7**、2025-12 **10**、2026-01 **11**、2026-02 **10**、2025-10 2、2026-03 1、2026-04 2、2026-05 1（更早 2024 各 1）。→ 近期**约 4 个结算日/月**（每周五），每个日期有 4 个 board（#1/#2 free、#1/#2 paid）。注意 2026-03 之后密度骤降，**不能把 2025-11..2026-02 的密度外推**。
- 那 46 个已关闭事件的成交额合计 **8,156,967 USDC**（Gamma 字段求和，来源自报，未核实）；单个事件从 6.2 万到 94.8 万 USDC 不等，2026-10-23 这两个在途 board 只有 3.2k 和 5.9k USDC——**近期 board 的成交额比历史小两个数量级**。

## 数据

- Apple 榜单 JSON（免费、免密钥、无需注册、只有当前快照）：`https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json`（另有 `/top-paid/`、`/top-grossing/`，以及 `us` 换成其他国家代码）。字段：`feed.updated`、`feed.results[].name/artistName/id/url`。`itunes.apple.com/us/rss/topfreeapplications/limit=50/json` 是同一数据的旧格式（`im:name.label`）。
- 结算源网页（免费）：`https://apps.apple.com/us/charts/iphone`，HTML 里内嵌应用名序列，可 grep；但它是 Apple 的页面，不保证与 JSON 逐秒同步。
- Polymarket Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?slug=<event-slug>`（规则原文、每个臂的 `outcomePrices/bestBid/bestAsk/feeSchedule/clobRewards/groupItemTitle`）；`https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all`（找同族事件，含 `pagination.totalResults`）。注意 `events?slug=` **支持重复传参批量取**（本次用 30 个 slug 一次取回 20 个）。
- Polymarket CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>`——已关闭市场返回空，只能前向记录。
- 缺失且必须承认：历史榜单序列（免费源未查到）、历史盘口、UMA 提案原文、Apple 榜单的逐分钟历史。

## 两周内怎么检验

- **独立结果按「日期」计**，不按臂、不按市场：同一天 `#1` 与 `#2` 两个 board 共享同一次 12:00 ET 榜单快照，算 1 个；`#1 paid`/Play 榜若同源同日也合并。近期 4 个结算日/月 → **两周只有约 2 个独立结果**，按 GUIDE 第 2 节第 6 条**凑不到 30 个**，30 个约需 7–8 个月。本条因此只交 `草稿`。
- 两周内可以真正做完的两件事：
  1. **源一致性**：每 15 分钟记录一次 JSON 榜单与网页榜单的前 10 名，算不一致分钟占比。这是一天就能出数、两周能出稳定估计的量。
  2. **窗口内价差是否真的存在**：在 2 个结算日的 11:00–12:00 ET 每分钟记录「当前第 N 名是谁」+ 各臂 `bestBid/bestAsk`，看是否存在 `YES 卖价 ≤ 0.98` 而该应用已经稳居第 N 的情况。
- **失败标准（写死，事后不改）**：
  1. 窗口内成交单的**中位已实现毛利 ≤ 0**（毛利 = 结算兑付 − 成交价 − 吃单费，不含未成交挂单）；
  2. 或两周内成交 < 20 份（容量不足，判「容量失败」而不是「策略失败」，同样进待选区）；
  3. 或 JSON 与网页榜单不一致分钟占比 > 2%（结算源不可靠，机制前提不成立）。
- 不许的自我安慰：不能用「最后价格收敛到 1」当成自己赚到；不能挑成交到的那几单报收益。

## 成本与容量

- **费率（Gamma 实取，不是查表）**：这些市场的 `feeType="culture_fees"`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`——**注意是 0.05，不是 GUIDE 表里 tech 的 0.04**（GUIDE 第 8 节说以每个市场的 `feeSchedule` 为准，此处实测 0.05）。
- **吃单费**（GUIDE 公式 `份数 × rate × p × (1−p)`），我算的每份费用与占名义本金比 `= rate×(1−p)`：p=0.10 → 0.0045（4.50%）；p=0.385 → 0.01184（3.075%）；p=0.50 → 0.0125（2.50%）；p=0.90 → 0.0045（**0.50%**）；p=0.93 → 0.00326（0.35%）。**价格越高，费占比越低**——这正是只在临近 12:00 ET、价格已经接近 0.9+ 时才吃单的定量理由。
- **半价差**：`#2` board 的 Vinted 臂价差 `0.63 − 0.16 = 0.47`，半价差 **0.235/份**，是任何「现在买 YES」的直接否决项；`#1` board 的 Muse 臂价差 `0.74 − 0.71 = 0.03`、ChatGPT `0.078 − 0.052 = 0.026`，半价差 1.3–1.5¢，是唯一还能做的两个臂。
- **每笔成本 = 费 + 半价差**：以 p=0.90 买 YES 为例，费 0.45¢ + 半价差（若价差 3¢）1.5¢ ≈ **1.95¢/份 = 名义的 2.2%**；窗口内若该臂已涨到 0.98，成本 ≈ 0.098¢ + 1.5¢ ≈ 1.6¢，需要吃到的价 ≤ 0.984 才正收益。
- **单笔能放多少**：Gamma `liquidityNum` 逐臂 123.12（Vinted）／546.09（ChatGPT）／242.35（Muse）／239.09（KICK）／208.76（Claude）／168.61（McDonald's）／146.97（TikTok Pro）USDC（来源自报，未核实）。所以**单臂现实容量是几十到一两百 USDT**，本条单笔上限 200 USDT 已经贴近上限；5,000 USDT **放不满**这条线，给它 600 USDT 额度就够。
- **资金占用**：结算日窗口内下单 → 当天 12:00 ET 快照 → UMA 结算（规则允许延后 48 小时）→ 一般 1–3 天回款。年化意义不大（占款天数太短、样本太少），不做年化外推。
- **机会频率**：约 4 个结算日/月 × 1–2 个可做臂 = 每月 4–8 笔，远低于「高频」。

## 风险

- **12:00 ET 的瞬时不确定性（最大风险）**：榜单在最后几分钟会跳（免费发布、买量、App 内更新都可能推动名次），我**没有**任何黏性/翻面基率（证据 4：免费历史未查到），所以「11:55 看到是第 1」不代表 12:00 还是第 1。p=0.90 买入意味着容忍 10% 的翻面；这个数只能靠前向记录去估。
- **结算源与数据源不是同一个东西**：规则指定的是 iOS App 内榜单 / `apps.apple.com/us/charts/iphone`，我比对的是 RSS JSON。今天两者顺序一致（证据 1），但**没有跨日证据**；Apple 的网页榜单可能按设备/地区/登录状态个性化。
- **候选臂会变**：`Reserved app 2..5` 会随时被补上（已关闭事件里市场数 18–26、无 Reserved 残留），所以开盘时的候选集不是结算时的候选集；未上市应用可能被加进臂，`Other` 的 15% 基率也是在这个机制下测出来的。
- **`Other` 不可成交**：`Other` 与 `Reserved` 臂 `bid=0/ask=1`，任何「赔率在 Other 上」的判断都无法执行；本条因此只能用「买已上市候选的 YES/NO」表达观点，且**无法对冲**「未上市应用夺冠」的情形。
- **成本吞掉薄边**：吃单费在 p=0.5 时是名义的 2.5%，半价差在薄臂上可达 23.5¢（Vinted 臂）；只有 p≈0.9 以上且价差 ≤ 3¢ 的臂才有空间。
- **结算争议/延迟**：`umaBond=500`、`umaReward=5`、`customLiveness=0`（实取字段）；规则允许「图表不可用 → 最多延后 48 小时 → 按最后一次发布榜单」，这类条款会让「12:00 ET 的答案」在极端情况下变成别的时点。
- **平台**：这些事件 `restricted=true`；negRisk 组的多臂持仓在结算/赎回时需要额外步骤和 gas（本条只做单臂买卖，不涉及转换）。
- **容量与规模的双重不利**：近期的两个在途 board 只有 3.2k/5.9k USDC 成交额（历史同类中位数高两个数量级），既是「没人抢」的原因，也是「赚不到多少钱」的原因。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付款方是结算日最后半小时里不看 Apple 榜单、只按旧叙事报价的对手方；机制是「规则把结算锁在 12:00 PM ET 的一次公开榜单快照，而这份榜单免费可读、刷新约 2 分钟」，可以一句话说清谁付钱。证据是 `#1` board 当前真实第 1 名 Capital One Mobile 根本不在候选里、而当前第 3 名 Muse from Meta 被定到 0.725（当前榜单与挂牌的劈叉），但这是单点横截面，不是收益证明。
2. **有免费数据能检验：不确定** — 结算源和榜单数据都免费免密钥且已实测可读（JSON 200、网页 200，两处顺序一致）；**但历史榜单序列免费源未查到**（三次 Wayback CDX 全空），已关闭市场的 CLOB 价格历史返回 0 点，所以只有前向记录，历史 ≥30 个独立结果的「价格」拿不到。
3. **小资金能做：满足** — 单臂 ≤200 USDT、单日 ≤600 USDT，远低于单场所 2,500 与总资金 5,000；不加杠杆、不借钱；买单最大亏损就是本金。容量写清了：单臂盘口 123–546 USDC，5,000 USDT 放不满。
4. **不重复：不确定** — 我在 2026-10-20 用 `grep -ril "app store|app-store|itunes|排行榜|rank"` 扫了 `known/KNOWN.md`、`bots/*/CLAIMS.md`、`bots/*/INDEX.md`、`bots/*/entries/`：`known/` 无命中，相关的是本机器人自己的 `quant-007`（月度 AI 榜首，结算源 arena.ai，月末 12:00 ET）、`quant-010`（Netflix/Spotify 周榜日更抢跑）与 `quant/CLAIMS.md` 里 B14 这一行。差异：数据源（Apple 榜单 JSON 已实测可读 vs arena.ai 返回 403）、板块与模板（App Store 每周五 #1/#2/free/paid，negRisk 带 `Other` 兜底臂）、频率（4 次/月 vs 1 次/月）、以及本条有可算的 `Other` 基率 3/20；与 `quant-010` 的差异是结算取数方式：本条是**结算日 12:00 ET 的瞬时榜单快照**，`quant-010` 是**周榜聚合的日更 nowcast**。**但必须承认：核心机制「用公开榜单的当前值给『固定时刻快照』结算的市场定价」与 quant-007 同源，只是标的和频率不同，按 GUIDE 第 6 节可能被判成变体；我不据「换数据源」主张全新机制，交主审定。**
5. **扣成本后粗算够用：不确定** — 吃单费实取 `rate=0.05`（不是 GUIDE 的 tech 0.04），p=0.90 时费/名义 0.50%，加半价差约 2.2%/笔；p≈0.98 时约 1.6¢/份。是否有足够的「榜单已定、价格未到 1」的时间窗**没有历史可测**，`observed_net_return=null`、`backtest_count=0`，不写正收益。另外两个可算的反例：买全 basket NO 的盈亏平衡需要 `P(Other)=20.1%`（`#1` board）与 64%（`#2` board），都 ≥ 实测基率 15%，所以 basket 方向明确不做。
6. **两周内能检验：不满足** — 独立结果按日期计，近期 4 个结算日/月，两周只有约 2 个，凑不到 30 个（约需 7–8 个月）。按 GUIDE 第 2 节第 6 条，本类应进**待选区**。
7. **出处可查：满足** — 每个数字都有 URL、访问日期和取数方式；榜单数字是两个端点现场对比+结算源网页 HTML 顺序（我算的），`Other` 基率是我用 Gamma 结算价数的（3/20，且标明未用 UMA 复核），Gamma 自报的 volume/liquidity 都标了「来源自报，未核实」；Wayback CDX 三处返回空、CLOB 历史 0 点、批量请求只回 20/30 这几个失败都照写。

## 出处

- https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json — 访问 2026-10-20T04:25Z — 已读（HTTP 200，`updated=Tue, 20 Oct 2026 04:25:44 +0000`，50 条，top5 与名次）
- https://itunes.apple.com/us/rss/topfreeapplications/limit=25/json — 访问 2026-10-20T04:25Z — 已读（HTTP 200，25 条，与上条逐位相同 25/25）
- https://apps.apple.com/us/charts/iphone — 访问 2026-10-20T04:2xZ — 已读（HTTP 200，1,017,064 字节，HTML 内嵌序列 `Capital One Mobile → Vinted → Muse from Meta → ChatGPT → TikTok Pro - Events → PineDrama → McDonald's → Claude by Anthropic → Google Gemini`；这是规则指定的结算源页面）
- https://gamma-api.polymarket.com/events?slug=2-free-app-in-the-us-apple-app-store-on-october-23-10172026 — 访问 2026-10-20T04:2xZ — 已读（规则原文、12 个市场、7 真候选 + 4 Reserved + Other、`feeSchedule`、`clobRewards`、`negRisk=true`、volume 3,197.81）
- https://gamma-api.polymarket.com/events?slug=1-free-app-in-the-us-apple-app-store-on-october-23-10172026 — 访问 2026-10-20T04:2xZ — 已读（volume 5,918.22、liquidity 5,058.13、7 臂报价；Capital One Mobile 不在候选里）
- https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all — 访问 2026-10-20 — 已读（`totalResults=247`；50 个事件里 46 closed、30 个标题含 `free app`；按月的频率）
- https://gamma-api.polymarket.com/events?slug=<30 个 free-app slug 批量> — 访问 2026-10-20 — 已读（HTTP 200，返回 20 个事件；赢家分类 17 listed / 3 `Other`；市场数 18–26；`Other` 基率 3/20）
- https://gamma-api.polymarket.com/events?closed=true&limit=500&end_date_min=2025-10-01&end_date_max=2026-10-20&order=endDate&ascending=false — 访问 2026-10-20 — 已读但**无用**（只返回 100 个事件、其中 0 个 App Store 事件，`limit` 未生效，故改用 public-search + 批量 slug）
- https://clob.polymarket.com/prices-history?market=79673759724127771853…&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（HTTP 200，`history` 0 点：已关闭 App Store 市场无价格历史，无法回测）
- http://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json — 访问 2026-10-20 — 已尝试，**返回空**（无快照）
- http://web.archive.org/cdx/search/cdx?url=rss.marketingtools.apple.com/api/v2/us/apps/top-free/50/apps.json — 访问 2026-10-20 — 已尝试，**返回空**
- http://web.archive.org/cdx/search/cdx?url=apps.apple.com/us/charts/iphone — 访问 2026-10-20 — 已尝试，**返回空**
