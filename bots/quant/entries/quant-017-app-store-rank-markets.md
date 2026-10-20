---
id: quant-017
name_zh: App Store免费榜排名定价
name_en: Polymarket "#1/#2 Free App in the US Apple App Store on <date>" priced off Apple's public top-free chart feed
bot: quant
date: 2026-10-20
market: polymarket
pm_category: tech
kind: supplement
improves: quant-007
category: E
return_type: direction
instruments: Polymarket negRisk 组「某应用是否在 <日期> 12:00 PM ET 时是美国 iPhone App Store 免费榜第 N 名」（N=1、2；另有付费榜、Play 榜同模板），每臂一个二元市场，并带一个不可成交的 `Other` 兜底臂
venues: Polymarket
data: Apple 公开榜单 JSON（rss.applemarketingtools.com 与 itunes.apple.com，免费免密钥，只有当前快照）+ 结算源网页 apps.apple.com/us/charts/iphone（当前快照 + Wayback 存档，免费免密钥；CDX 实测 4,295 个 HTTP 200 快照（按 digest 去重），2022-06-04..2025-11-03；2025 年按事先写死的 04:00–08:00/14:00–18:00 UTC 窗口为 60 个双窗口日、解析 54 个，按事后放宽的 04:00–09:00/14:00–19:00 日期框（每侧取当天最接近 06:00/16:00 的快照）为 79 个双窗口日、解析 71 个）+ Polymarket Gamma/CLOB（免费免密钥）；CLOB 价格历史：247 个 App Store 相关事件中 21 个有 >0 点（16 个已关闭、5 个在途），已关闭的集中在 2026-09-25..10-16 的 4 个结算日，2025 年样本仍为 0 点
test_2w: 独立结果按「日期」计（同一天 #1/#2 两臂共享同一次榜单快照，只算 1 个），近期每月约 5 个结算日 → 两周只有约 2–3 个，凑不到 30；名次黏性可用 2025 年历史基率（事先写死窗口 04:00–08:00/14:00–18:00 下 P1=47/54=87.0%；事后放宽到 04:00–09:00/14:00–19:00 为 64/71=90.1%），但收益侧仍只有前向记录。失败标准：结算日窗口内的成交单中位已实现毛利≤0，或 RSS 榜单与结算源网页榜单不一致的比例>2%
status: 草稿
confidence: 中
---

整理说明：本版是 R2 前的加强稿。新增的关键证据是 **Wayback Machine 对结算源网页 `apps.apple.com/us/charts/iphone` 的存档**：CDX 实测 4,295 个 HTTP 200 快照（2022-06-04 至 2025-11-03），PREREG_R017.md 事先写死的样本框是 2025 年「04:00–08:00 UTC 与 14:00–18:00 UTC 都有快照」的日期（脚本 C0 原文），按这个框是 120 张目标快照 / 60 个日期，成功解析 54 个双窗口日，得到 **P(06:00 UTC #1 在 16:00 UTC 仍是 #1)=47/54=87.0%**、**P(06:00 UTC #1 在次日 06:00 仍是 #1)=15/21=71.4%（仅 21 个连续日对，样本不足 60，作参考）**。**口径更正**：先前引用的 **64/71=90.1%**（及 23/32=71.9%）不是这个事先写死的框算出来的——它用的是放宽到 04:00–09:00 / 14:00–19:00 的日期框、且每侧取当天最接近 06:00 / 16:00 的快照（158 张目标快照 / 79 个日期；因此有 2 张落在窗口外：20250105 AM=03:49 UTC、20250217 PM=13:12 UTC），属**事后放宽口径**，不是预注册结果；下面凡用 90.1% 处都按此标注。这推翻了上一版「免费历史未查到、没有任何名次黏性基率」的说法。上一版还有一处需要更正：不是所有已关闭 App Store 市场都没有 CLOB 价格历史——247 个相关事件里有 21 个有 >0 点，但 16 个已关闭的只覆盖 4 个独立结算日（2026-09-25、10-02、10-09、10-16），仍不足以做 ≥30 个独立结果的价格回测；2025 年样本仍是 0 点。除此之外，当前榜单、当前挂牌价、`Other` 基率、成本与门槛结论均按本次现场取数重算，见下。

**本版仍没有收益回测**：`observed_net_return=null`、`backtest_count=0`。下面的 90.1%（事后放宽口径；事先写死口径为 87.0%）是**名次黏性基率**，不是策略收益率；它只能用来给「结算日前 10 小时翻面风险」定量，不能证明最后 1 小时「榜单已定、价格未到 1」的价差能赚钱。

## 一句话

在 Polymarket 每周五结算的「<日期> 12:00 PM ET 时谁是免费榜第 1/第 2」negRisk 组上，用 Apple 免费榜单 JSON 判断当日实际名次：只在结算日 11:00–12:00 ET 之间、当榜单已经显示某个**已上市候选**就是第 N 名、而它的 YES 卖价明显低于 1 时买 YES（或买该候选的 NO 当它明显不是第 N 名），持到结算；结算日之前的名次黏性单不做——2025 年基率只有 90.1%（06:00→16:00，事后放宽口径；事先写死口径 47/54=87.0%），按 0.88 以上的 YES 买价扣费后已经是负 EV（见证据 3 与成本节）。

## 钱从哪里来

付钱给你的是**在结算日最后几十分钟里没有去看 Apple 榜单、只按旧叙事和稀薄盘口报价的对手方**。规则把结果固定成「某个指定时刻（12:00 PM ET）的一次榜单快照」，而这份榜单本身是 Apple 免费公开、更新很快的 JSON（本次实测 `updated` 字段为 `Tue, 20 Oct 2026 05:14:43 +0000`，精确到秒），因此临近 12:00 ET 时答案实际上已经可读，价格却常常还停在几小时前的水平。这笔钱持续存在的原因是结构性的：这些 board 的盘口很薄（见成本节：`#2` board 的 Vinted 一臂买价 0.16 / 卖价 0.62，价差 0.46），做市的人不愿意在最后半小时收紧报价，而结算窗口只有几分钟，抢这个窗口的人少。

**新增的定量约束**：2025 年双窗口日里，06:00 UTC 的 #1 到 16:00 UTC 只有 90.1% 还是 #1（事后放宽口径；事先写死窗口下为 47/54=87.0%）。也就是说，结算日前 10 小时按「现在 #1」下单，会吃到约 10% 的翻面；这个数不小，所以本条仍然只做最后 1 小时、并且要求榜单已经当场显示目标名次。最后 1 小时的黏性没有历史快照可直接测（Wayback 的 16:00 快照前后没有稳定的 15:00 快照配对），只能前向记录。

## 规则

**结算规则原文要点（Gamma 事件 `2-free-app-in-the-us-apple-app-store-on-october-23-10172026`，2026-10-20 本次重取）**：

- 结算口径：「according to the iOS app, ranked #2 in the United States on the iPhone Apple App Store's overall Top Charts under "Free Apps", **as of 12:00 PM ET on the specified date**」——是**某一时点**，不是「曾经达到」，也不是当日平均。
- 结算源：「To find the overall chart, click "Apps" at the bottom of the US iOS App Store app, scroll down to "Top Free Apps" and click "See All". Then under "Free Apps" in the "Top Charts" section, you'll see the list ...(https://apps.apple.com/us/charts/iphone)」——结算源是 Apple 自己的榜单页/App 内榜单，不是第三方 tracker。
- 缺数据兜底：「If the chart is unavailable at 12:00 PM ET, this market may remain open for up to 48 hours ... If the data remains unavailable, this market will resolve according to the last published ranking.」——即 12:00 ET 取不到就延后，最终按最后一次发布的榜单。
- 结构：`negRisk=true`；本次实测该事件 **12 个市场**，其中 7 个是真候选（Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / Google Gemini / KICK），另有 **4 个 `Reserved app 2..5` 和 1 个 `Other`**，这 5 个当时 `outcomePrices=["0.5","0.5"]`、`bestBid=0`、`bestAsk=1`、volume 0（我实取的字段）——即**占位臂、不可成交**。已关闭的 117 个 US Apple 免费周度板里，市场数是 11–26 个；**这 117 个里只有 8 个在关闭后仍带 `Reserved` 臂（8/117=6.8%）**（不是所有占位臂都会在结算前改名），所以不能假设候选臂一定被补上，`Other` 兜底更重要（见证据 4）。
- 时间：本次示例 `startDate=2026-10-17T21:06:16Z`（开盘距结算约 6 天）、`endDate=2026-10-23T23:59:00Z`。注意 **`endDate` 是 23:59 UTC = 19:59 ET，不是结算时刻**；结算时刻是规则写的 2026-10-23 12:00 PM ET（10 月为 EDT=UTC−4，即 16:00 UTC）。
- 同族模板：`#1 Free App`、`#2 Free App`、`#1 Paid App`、`#2 Paid App`（同一日期各一个事件），另有 Play Store 榜同模板（`1-free-app-in-play-store-on-december-19`）。

**交易规则（本条的提案，不是已验证的盈利规则）**

1. 只在**结算日** 11:00–12:00 ET（15:00–16:00 UTC）行动。11:50 ET 之后不再新建单。
2. 每分钟同时拉 `rss.applemarketingtools.com/.../top-free/50/apps.json` 和结算源网页 `apps.apple.com/us/charts/iphone`，取第 N 位应用名。两者必须一致，否则跳过（本次实测：两处前 10 位顺序完全一致，见证据 1）。
3. 若第 N 位 = 已上市候选 X，且 X 的 YES 最优卖价 ≤ `1 − 吃单费 − 2¢`：买 YES X，持有到结算。
4. 若第 N 位 = 已上市候选 Y，而另一个已上市候选 Z ≠ Y：可买 NO Z（NO 卖价 = 1 − Z 的 YES 买价），价格条件同上。同一 board 同一时刻只做一个方向，不做「全 basket 买 NO」。
5. 若第 N 位是**未上市**应用：本次就是这种情况（实测第 1 名是 Capital One Mobile，而 `#1` board 的 7 个真候选里没有它），只能走 `Other` 臂，而 `Other` 报价 0/1 不可成交 → **不做**。
6. 仓位：单 market ≤ 200 份 / ≤ 200 USDT，单日 ≤ 3 个 board，合计 ≤ 600 USDT；总资金 5,000 USDT、单场所不超 2,500 USDT。
7. 出场：不主动平仓，持有到 UMA 结算（规则允许延后 48 小时）；平仓要再付一次吃单费+价差，票面 1.00 的收敛是免费的。
8. 明确不做：结算日之前（T−6 到 T−1）按「名次黏性」做方向单。理由不再是「没有数据」，而是**有了 2025 年基率后算出来不划算**：P1=90.1%（事后放宽口径；换成事先写死的 87.0% 只会让结论更强），若 06:00 UTC 买 YES 的价格是 0.88，费 0.0053 + 半价差 0.015 = 成本 0.9003，EV≈+0.1%；0.89 时 EV≈−0.9%，0.90 时 EV≈−1.8%（完整表见成本节）。按 90.1% 算，只有 0.86 以下才有 2% 以上的毛边（按 87.0% 则要 0.83 以下）；但没有历史盘口能证明「榜单显示 #1 时 YES 会卖到 0.86 以下」。
9. 用 2025 年基率只做**风险刻度**：把 06:00→16:00 的 90.1%（事后放宽口径；事先写死口径 87.0%）当作「10 小时翻面风险」的量级参考（两个口径对应翻面约 10% / 13%）；不把它当成最后 1 小时的翻面率，也不把它当成收益证据。

## 证据

### 1）Apple 侧：两个免费端点当前序列一致，且与结算源网页顺序一致（本次重取）

- `rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` → HTTP 200，25,783 字节，`country=us`，`updated=Tue, 20 Oct 2026 05:14:43 +0000`，50 条。top12 = `Capital One Mobile, Vinted: Pre-loved marketplace, Muse from Meta, ChatGPT, TikTok Pro - Events, PineDrama - Short Dramas, McDonald's, Claude by Anthropic, Google Gemini, Kalshi: Trade Football & more, Threads, CapCut: Photo & Video Editor`。
- 结算源 `apps.apple.com/us/charts/iphone` → HTTP 200，1,017,064 字节；HTML 内嵌的名字顺序以 `Capital One Mobile → Vinted: Pre-loved marketplace → Muse from Meta → ...` 开头，与 JSON 前 3 位一致。**这是我算的比对，不是来源自报。**
- 7 个真候选在 top-free-50 里的名次（2026-10-20 05:14Z 快照，我算的）：Vinted 2、Muse from Meta 3、ChatGPT 4、TikTok Pro 5、Claude 8、Google Gemini 9、KICK 不在 top 50。
- 上一版说 `itunes.apple.com/us/rss/topfreeapplications/limit=25/json` 与 RSS 逐位相同 25/25；本次没有重取该端点，故不重复引用其具体数字（只保留“上一版曾比对过”的记录）。

### 2）市场侧：同一时刻的挂牌价（Gamma 快照，2026-10-20 本次重取）

`#1 Free App on October 23`（`1-free-app-in-the-us-apple-app-store-on-october-23-10172026`）：volume 5,918.22、liquidity 5,115.60（来源自报，未核实），7 个真候选：

| 候选 | YES `outcomePrices` | bestBid | bestAsk | 当前真实名次 |
|---|---|---|---|---|
| Muse from Meta | 0.715 | 0.71 | 0.72 | 3 |
| Vinted | 0.06 | 0.02 | 0.10 | 2 |
| ChatGPT | 0.063 | 0.05 | 0.076 | 4 |
| Claude by Anthropic | 0.0315 | 0.003 | 0.06 | 8 |
| KICK | 0.01 | 0.002 | 0.018 | >50 |
| Google Gemini | 0.005 | 0.001 | 0.009 | 9 |
| TikTok Pro | 0.0045 | 0.001 | 0.008 | 5 |

- 七个真候选 YES 之和 **0.889**，买价之和 **0.787**，卖价之和 **0.991**（我算的）。
- 当前真实第 1 名 Capital One Mobile **不在任何一臂上**（不在 7 个真候选，也不在 `Reserved`/`Other` 之外的位置——`Other` 是唯一兜底），而市场把 Muse from Meta（当前第 3）定到 0.715。**这是「市场在按叙事而不是按当前榜单定价」的直接证据**，但注意：距离结算还有 3 天，Muse 也可能是未来的第 1 名，本条不据此断言它高估。
- `#2 Free App on October 23`（`2-free-app-...`）：volume 3,197.81、liquidity 1,558.69；真候选 YES 之和 **0.9215**；Vinted（当前真实第 2）0.39，买价 0.16 / 卖价 0.62（价差 0.46）；Muse 0.1555、ChatGPT 0.1485、TikTok Pro 0.0975、KICK 0.0795、McDonald's 0.0285、Claude 0.022。
- 两边都带 `clobRewards`（`#2` board 日率 Vinted 54 / Muse 17 / ChatGPT 16 / TikTok 8 / KICK 5 USDC，`rewardsMinSize=20`、`rewardsMaxSpread=4.5`、`startDate=2026-10-20`；`#1` board 首个市场日率 92 USDC（本次重取））；仅作补贴，不进主收益。

### 3）名次黏性：2025 年 Wayback 基率（本版新增；预注册口径 87.0%，正文引用的 90.1% 为事后放宽口径）

**数据来源**：`https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest` → HTTP 200，**4,295 个快照**，首个 `20220604145458`、最后一个 `20251103152602`；按年：2022 18、2023 28、2024 2,648、2025 1,601；共 454 个不同 UTC 日期。

**事先写死的规则（在解析任何快照内容之前写入 `PREREG_R017.md`）**：

- 只用该 URL 的 HTTP 200 存档；用页面里的 `<script name="schema:top-free" type="application/ld+json">` 的 `itemListElement` 第 1 位取 #1。
- 样本框：2025 年、且在 04:00–08:00 UTC 与 14:00–18:00 UTC 各至少有一个快照的日期；每个窗口取最接近 06:00 / 16:00 的那一张。（**实际执行时窗口被放宽到 04:00–09:00 / 14:00–19:00，且每侧取当天最接近 06:00 / 16:00 的快照（2 张落在窗口外）；这不是预注册口径，见下**。）
- P1（同日 06:00→16:00）= 两个窗口都能解析的日期里，#1 相同的比例。
- P2（隔夜 06:00→次日 06:00）= 连续两天早晨快照都能解析的日对里，#1 相同的比例；不足 60 对时只作参考。
- 不做变体挑选；额外只报一个次要指标（top-6 集合重合）。

**结果（我算的）**：

- **事先写死口径（04:00–08:00 / 14:00–18:00 UTC）**：2025 年双窗口日 **60** 个、目标快照 120 张，实际成功解析 **54** 个日期（其余 6 张快照三次重试后仍抓取失败）。**P1 = 47/54 = 87.04%**，Wilson 95% CI 约 **[75.6%, 93.6%]**；**P2 = 15/21 = 71.43%**，Wilson 95% CI 约 **[50.0%, 86.2%]**；只有 21 个连续日对（<60），**作参考，不作为主结论**。这是预注册结果。
- **事后放宽口径（实际执行的快照清单：日期框 04:00–09:00 / 14:00–19:00，每侧取当天最接近 06:00 / 16:00 的快照）**：2025 年双窗口日 **79** 个、158 张目标快照中 150 张解析成功 → **71** 个双窗口日。**P1 = 64/71 = 90.14%**，Wilson 95% CI 约 **[81.0%, 95.1%]**；**P2 = 23/32 = 71.88%**，Wilson 95% CI 约 **[54.6%, 84.4%]**（32 对 <60，仅参考）。**正文引用的 90.1% 就是这一行，它比 PREREG_R017.md 写死的框更宽，属事后放宽口径，不是预注册结果。**
- 次要（按事后放宽口径的 71 天）：16:00 与 06:00 的 top-6 **集合**平均重合 90.4%（最低 66.7%，最高 100%）；top-6 **顺序完全相同**只有 12/71 天。说明 #1 相对稳，但第 2–6 名换位很频繁——这正是 #2 board 比 #1 board 更难做的原因。
- 翻面的例子（我解析的）：2025-01-04 06:00 #1 ChatGPT → 16:00 #1 Threads；2025-01-11 Watch Duty → Lemon8；2025-01-24 ChatGPT → Watch Duty；2025-03-05 Jimmy John's → ChatGPT。多数日子 #1 不变（ChatGPT 长期占据 2025 年大部分时间）。
- **重要限制**：存档到 2025-11-03 就断了，没有 2026 年快照；2026 年的榜单结构（ChatGPT/Gemini/Sora 轮换）与 2025 年不完全一样。这个 90.1%/87.0% 是**历史基率，不是当前市场的保证**。

### 4）`Other` 的结算基率：本次重算 14/117 = 12.0%（US Apple 免费周度 #1/#2 板）

**方法（本次）**：用 Gamma `public-search?q=app store&limit_per_type=50&events_status=all` 翻 5 页，按 slug 去重得到 **247 个事件**（242 已关闭、5 在途），其中标题含 `free app` 的 **141 个**（139 已关闭）。对每个已关闭事件，取 `outcomes` 里字面为 `Yes` 的 `outcomePrices` > 0.5 的臂为赢家；赢家 `groupItemTitle` 为 `Other` 的计为 Other。**关键样本过滤**：不能用 slug 含 `in-the-us-apple-app-store` 的全部事件——里面混有 `chatgpt-out-as-1-free-app...` 这类多日期阶梯（同一事件多个 Yes=1，且不是周度 #1/#2 板）。本条只取正则 `^[12]-free-app-in-the-us-apple-app-store-on-` 的周度板；本次该样本 117 个已关闭事件里没有多 Yes=1、没有无法判定的。

- **US Apple 免费周度 #1/#2 板：117 个已关闭，Other 赢 14 个 → 12.0%**；`#1` 子集 8/63=12.7%，`#2` 子集 6/54=11.1%。
- 更宽的 free-app 样本（含上面的阶梯和 Play Store）为 16/137=11.7%，只作对照，**不作为主基率**。
- 这 117 个周度板的 `endDate` 从 2025-10-10 到 2026-10-16，市场数 11–26 个，全部带 `Other` 臂，**8 个关闭后仍带 `Reserved` 臂（8/117）**；成交额合计 7,711,532 USDC（Gamma 字段求和，来源自报，未核实）。
- **上一版 3/20 的样本太小；本版把周度板扩到 117 个后，`Other` 不是 15% 而是 12.0%。**
- **结论**：候选臂会在结算前扩充，所以「今天的第 1 名没上市」不等于它届时仍没上市；结算日必须重读候选清单。`Other` 不是 15% 那种高概率，按本次大样本只有约 11%。

**用这个基率做的算术（买全 basket NO 值不值）**：`#1` board 七个真候选全买 NO，成本 = `7 − ΣbestBid = 7 − 0.787 = 6.213`；`Other` 赢则收 7，任一上市候选赢则收 6。吃单费逐臂 `0.05·p·(1−p)`（p = NO 卖价 = 1 − YES 买价），合计 **0.0140/份**。于是净成本 6.227，盈亏平衡需要 `P(Other) = 0.227 → 22.7%`，而基率是 **12.0%**，**当前买价下这是负 EV**（`#2` board 更差：`7 − 0.362 = 6.638`，费 0.0158，需要 P(Other)=65.4%）。这两个数字就是本条不做 basket 单的理由。

### 5）CLOB 价格历史：21/247 个事件有 >0 点，但只覆盖 4 个独立结算日（本版更正）

**方法（本次）**：对 247 个事件的每个事件取第一个有 `clobTokenIds` 的市场，调 `clob.polymarket.com/prices-history?market=<token>&interval=max&fidelity=60`，记 `history` 点数；再对 16 个「已关闭且有历史」的事件，把其全部 196 个市场的第一个 token 都查一遍。

- **事件级**：247 个事件中 **21 个有 >0 点**（226 个返回 0 点）；其中 **16 个已关闭、5 个在途**。正点数的范围 51–711 点。
- **已关闭的 16 个**：全部集中在 **2026-09-25、2026-10-02、2026-10-09、2026-10-16** 四个结算日（每个日期 4 个 board），即 **4 个独立日期**。这 16 个事件共有 **196 个市场，其中 92 个有 >0 点、104 个为 0 点**。
- **2025 年及更早的已关闭 App Store 事件**：本次抽到的样本仍返回 0 点（上一版点名的 2025-11-21 `#1` board ChatGPT 臂也是 0 点），所以**无法用 2025 年价格回测**。
- **更正上一版**：上一版写「已关闭 App Store 市场的 CLOB 价格历史返回 0 点」作为普遍结论，不准确。正确说法是：**2025 年及更早的已关闭市场为 0 点；2026-09-25 之后的 16 个已关闭事件有 85–166 点的 1 分钟历史，但只覆盖 4 个独立结算日**，仍远少于 30 个独立结果。
- 这意味着：如果要在 R2 里做价格回测，只能从 2026-09-25 起的 4 个日期做**小样本**，或者从现在起前向记录；不能假装有 2025 年价格。

### 6）频率与规模（本次重数）

- `public-search?q=app%20store` 的 `pagination={"hasMore":true,"totalResults":247}`（来源自报，未核实）；5 页去重后 **247 个事件**：242 已关闭、5 在途；按标题分类 free 141、paid 76、other 30。
- 117 个已关闭的 US Apple 免费周度 #1/#2 板覆盖 **62 个独立结算日**（2025-10..2026-10），按 `endDate` 月份：2025-10 **4**、2025-11 **5**、2025-12 **7**、2026-01 **8**、2026-02 **6**、2026-03 **14**、2026-04 **15**、2026-05 **16**、2026-06 **12**、2026-07 **8**、2026-08 **8**、2026-09 **8**、2026-10 **6**。→ 近期约 **5 个结算日/月**，每个日期有 4 个 board（#1/#2 free、#1/#2 paid）；2026-03 之后密度没有像上一版说的那样骤降，上一版只看了前 50 个事件，样本偏差。
- 这 117 个已关闭周度板的成交额合计 **7,711,532 USDC**（Gamma 字段求和，来源自报，未核实）；单个事件从很小到约百万 USDC 不等。2026-10-23 这两个在途 board 只有 3.2k 和 5.9k USDC——**近期 board 的成交额仍远小于历史峰值**。

## 数据

- Apple 榜单 JSON（免费、免密钥、无需注册、只有当前快照）：`https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json`（另有 `/top-paid/`、`/top-grossing/`，以及 `us` 换成其他国家代码）。字段：`feed.updated`、`feed.results[].name/artistName/id/url`。`itunes.apple.com/us/rss/topfreeapplications/limit=50/json` 是同一数据的旧格式（`im:name.label`）。
- 结算源网页（免费）：`https://apps.apple.com/us/charts/iphone`，HTML 里内嵌应用名序列；Wayback 存档里同一页有 `<script name="schema:top-free" type="application/ld+json">`，含 `itemListElement[].position/name`，可直接取 #1–#6。它是 Apple 的页面，不保证与 JSON 逐秒同步。
- **Wayback CDX（免费免密钥）**：`https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest`；单张快照原文用 `https://web.archive.org/web/<14位timestamp>id_/https://apps.apple.com/us/charts/iphone`（返回 gzip，需解压）。实测 4,295 个 200 快照，2022-06-04..2025-11-03；**2026 年没有快照**。
- Wayback 对 RSS JSON 的覆盖：`rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` 只有 **1 个** 200 快照（`20230522143120`），`/100/` 为 0 个；`itunes.apple.com/us/rss/topfreeapplications/limit=50/json` 只有 **1 个**（`20180107065423`）；`apps.apple.com/us/charts/iphone/free-apps` 与 `apps.apple.com/us/app-store/charts/iphone` 均为 0 个。**所以能用的历史序列只有结算源网页这一条，RSS 没有足够历史。**
- Polymarket Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?slug=<event-slug>`（规则原文、每个臂的 `outcomePrices/bestBid/bestAsk/feeSchedule/clobRewards/groupItemTitle`）；`https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all&page=<1..5>`（找同族事件，含 `pagination.totalResults` 和每个事件内嵌的 `markets`）。
- Polymarket CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max&fidelity=60`——2025 年及更早的已关闭市场返回空；2026-09-25 起的部分已关闭市场有 85–166 点。
- 缺失且必须承认：2026 年的历史榜单序列（Wayback 未收录）、2025 年的历史盘口、UMA 提案原文、最后 1 小时（15:00→16:00 UTC）的榜单快照配对。

## 两周内怎么检验

- **独立结果按「日期」计**，不按臂、不按市场：同一天 `#1` 与 `#2` 两个 board 共享同一次 12:00 ET 榜单快照，算 1 个；`#1 paid`/Play 榜若同源同日也合并。近期约 5 个结算日/月 → **两周只有约 2–3 个独立结果**，按 GUIDE 第 2 节第 6 条**凑不到 30 个**，30 个约需 6 个月。本条因此只交 `草稿`，按规则应进**待选区**。
- 两周内可以真正做完的三件事：
  1. **源一致性**：每 15 分钟记录一次 JSON 榜单与网页榜单的前 10 名，算不一致分钟占比。这是一天就能出数、两周能出稳定估计的量。
  2. **窗口内价差是否真的存在**：在 2 个结算日的 11:00–12:00 ET 每分钟记录「当前第 N 名是谁」+ 各臂 `bestBid/bestAsk`，看是否存在 `YES 卖价 ≤ 0.98` 而该应用已经稳居第 N 的情况。
  3. **最后 1 小时黏性**：在同样的 2 个结算日，每 1 分钟记录一次 #N 名，直接估 15:00→16:00 的翻面率；这是 2025 年 Wayback 数据补不上的关键缺口。
- **失败标准（写死，事后不改）**：
  1. 窗口内成交单的**中位已实现毛利 ≤ 0**（毛利 = 结算兑付 − 成交价 − 吃单费，不含未成交挂单）；
  2. 或两周内成交 < 20 份（容量不足，判「容量失败」而不是「策略失败」，同样进待选区）；
  3. 或 JSON 与网页榜单不一致分钟占比 > 2%（结算源不可靠，机制前提不成立）。
- 不许的自我安慰：不能用「最后价格收敛到 1」当成自己赚到；不能挑成交到的那几单报收益；不能把 2025 年 90.1%（事后放宽口径）的 10 小时黏性当成最后 1 小时的成交胜率。

## 成本与容量

- **费率（Gamma 本次实取，不是查表）**：这些市场的 `feeType="culture_fees"`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`——**注意是 0.05，不是 GUIDE 表里 tech 的 0.04**（GUIDE 第 8 节说以每个市场的 `feeSchedule` 为准，此处实测 0.05）。
- **吃单费**（GUIDE 公式 `份数 × rate × p × (1−p)`），我算的每份费用与占名义本金比 `= rate×(1−p)`：p=0.10 → 0.0045（4.50%）；p=0.385 → 0.01184（3.075%）；p=0.50 → 0.0125（2.50%）；p=0.90 → 0.0045（**0.50%**）；p=0.93 → 0.00326（0.35%）。**价格越高，费占比越低**——这正是只在临近 12:00 ET、价格已经接近 0.9+ 时才吃单的定量理由。
- **半价差**：`#2` board 的 Vinted 臂价差 `0.62 − 0.16 = 0.46`，半价差 **0.23/份**，是任何「现在买 YES」的直接否决项；`#1` board 的 Muse 臂价差 `0.72 − 0.71 = 0.01`、ChatGPT `0.076 − 0.05 = 0.026`，半价差 0.5–1.3¢，是唯一还能做的两个臂。
- **06:00→16:00 预先下单的 EV（用事后放宽口径 P1=90.14%，半价差按 1.5¢；换成事先写死的 87.04% 时，同样算术的盈亏平衡约 0.849、+2% 毛边门槛约 0.828）**：p=0.84 → 成本 0.8617，EV **+4.0¢（+4.6%）**；p=0.85 → +3.0¢（+3.5%）；p=0.86 → +2.0¢（+2.3%）；p=0.87 → +1.1¢（+1.2%）；p=0.88 → +0.1¢（+0.1%）；p=0.89 → −0.9¢（−0.9%）；p=0.90 → −1.8¢（−2.0%）。**盈亏平衡约 0.881。** 这只是 10 小时黏性下的算术；最后 1 小时的入场价通常远高于 0.88，所以不能用这张表给最后 1 小时估值。
- **隔夜（事后放宽口径 P2=71.9%，仅 32 对，参考）**：p=0.68 → EV +1.3¢；p=0.69 → +0.3¢；p=0.70 → −0.7¢；p=0.71 → −1.7¢。隔夜单不划算，且样本不足，本条不做。
- **每笔成本 = 费 + 半价差**：以 p=0.90 买 YES 为例，费 0.45¢ + 半价差（若价差 3¢）1.5¢ ≈ **1.95¢/份 = 名义的 2.2%**；窗口内若该臂已涨到 0.98，费 0.098¢ + 半价差 1.5¢ ≈ 1.6¢，但 0.98 的票面只剩 2¢，扣完成本几乎不剩——所以真正能做的是「榜单已定、价格在 0.90–0.96、价差 ≤2¢」的窄窗口，而不是盲目追到 0.99。
- **单笔能放多少**：Gamma `liquidityNum` 逐臂 123.12（Vinted）／546.09（ChatGPT）／242.35（Muse）／239.09（KICK）／208.76（Claude）／168.61（McDonald's）／146.97（TikTok Pro）USDC（来源自报，未核实；上一版快照，本次未逐臂重取）。所以**单臂现实容量是几十到一两百 USDT**，本条单笔上限 200 USDT 已经贴近上限；5,000 USDT **放不满**这条线，给它 600 USDT 额度就够。
- **资金占用**：结算日窗口内下单 → 当天 12:00 ET 快照 → UMA 结算（规则允许延后 48 小时）→ 一般 1–3 天回款。年化意义不大（占款天数太短、样本太少），不做年化外推。
- **机会频率**：约 5 个结算日/月 × 1–2 个可做臂 = 每月 5–10 笔，远低于「高频」。

## 风险

- **最后 1 小时的瞬时不确定性（最大风险）**：榜单在最后几分钟会跳（免费发布、买量、App 内更新都可能推动名次）。本版新增的 2025 年基率只说明 **06:00→16:00 的 10 小时**有 90.1% 保持率（事后放宽口径；事先写死口径 87.0%）；它**不能**直接给出 15:00→16:00 的翻面率。最后 1 小时的黏性仍只能前向记录。p=0.95 买入意味着容忍 5% 的翻面；这个数没有历史验证。
- **结算源与数据源不是同一个东西**：规则指定的是 iOS App 内榜单 / `apps.apple.com/us/charts/iphone`，我比对的是 RSS JSON。本次两者前 10 位顺序一致（证据 1），但**没有跨日证据**；Apple 的网页榜单可能按设备/地区/登录状态个性化。
- **候选臂会变，而且不一定补全**：117 个已关闭周度免费板里 **只有 8 个仍带 `Reserved` 臂（8/117）**（不是全部都会在结算前改名），所以开盘时的候选集不是结算时的候选集；未上市应用可能被加进臂，也可能一直留在 `Reserved`/`Other`，`Other` 的 12.0% 基率是在这个机制下测出来的。
- **`Other` 不可成交**：`Other` 与 `Reserved` 臂 `bid=0/ask=1`，任何「赔率在 Other 上」的判断都无法执行；本条因此只能用「买已上市候选的 YES/NO」表达观点，且**无法对冲**「未上市应用夺冠」的情形。
- **成本吞掉薄边**：吃单费在 p=0.5 时是名义的 2.5%，半价差在薄臂上可达 23¢（Vinted 臂）；只有 p≈0.9 以上且价差 ≤2–3¢ 的臂才有空间。0.98 以上票面只剩 2¢，扣 1.6¢ 成本后几乎不剩。
- **历史基率的时代错配**：Wayback 基率来自 2025 年，当前是 2026-10；2026 年的结算记录显示 ChatGPT、Muse、Gemini 等候选轮换，2025 年的 90.1%（放宽口径）/87.0%（事先写死口径）可能高估或低估当前黏性。存档在 2025-11-03 后中断，无法验证 2026 年。
- **结算争议/延迟**：事件对象本次未返回 `umaBond`/`umaReward`（字段为 `None`）；规则允许「图表不可用 → 最多延后 48 小时 → 按最后一次发布榜单」，这类条款会让「12:00 ET 的答案」在极端情况下变成别的时点。
- **平台**：这些事件 `restricted=true`；negRisk 组的多臂持仓在结算/赎回时需要额外步骤和 gas（本条只做单臂买卖，不涉及转换）。
- **容量与规模的双重不利**：近期的两个在途 board 只有 3.2k/5.9k USDC 成交额（历史同类峰值高两个数量级），既是「没人抢」的原因，也是「赚不到多少钱」的原因。

## 改进了什么

本条是 quant-007（arena.ai 月度 AI 榜首，固定时刻排名市场）的**补充条目**，不是新机制：两者都是「用公开榜单的当前值给『固定时刻排名快照』结算的市场定价」。按 GUIDE 第 6 节与独立审计 S2-2（`notes/scheduler/audit/c20261020-1423-research.md`），只换榜单源/标的/频率属变体，故改 `kind: supplement`、`improves: quant-007`，不另立新机制。

相对 quant-007 新增的证据与差异：结算源换成 Apple 免费榜单（`apps.apple.com/us/charts/iphone` 与 RSS JSON 均可读，quant-007 的 arena.ai 返回 403）；模板是周度 `#1/#2 free/paid` negRisk 组并带不可成交的 `Other` 兜底臂；给 quant-007 补了 117 个已关闭周度板的 `Other` 基率 **14/117=12.0%** 与 2025 年 Wayback 名次黏性基率（预注册口径 47/54=87.0%）；频率从 1 次/月提高到约 5 个结算日/月。

## 门槛自查

1. **机制说得清：满足** — 付款方是结算日最后半小时里不看 Apple 榜单、只按旧叙事报价的对手方；机制是「规则把结算锁在 12:00 PM ET 的一次公开榜单快照，而这份榜单免费可读（本次实测 `updated` 字段精确到秒）」，可以一句话说清谁付钱。证据是 `#1` board 当前真实第 1 名 Capital One Mobile 根本不在候选里、而当前第 3 名 Muse from Meta 被定到 0.715（当前榜单与挂牌的劈叉），但这是单点横截面，不是收益证明。
2. **有免费数据能检验：不确定（部分满足）** — 结算源和榜单数据都免费免密钥且已实测可读（JSON 200、网页 200，两处顺序一致）；**名次黏性现在有 2025 年 Wayback 基率（事先写死口径 47/54=87.0% 与 15/21=71.4%；事后放宽口径 64/71=90.1% 与 23/32=71.9%）**；**但收益侧仍不够**：247 个相关事件里只有 21 个有 CLOB 历史，已关闭的只有 16 个、覆盖 4 个独立结算日（2026-09-25..10-16），2025 年样本 0 点，拿不到 ≥30 个独立结果的收益序列。
3. **小资金能做：满足** — 单臂 ≤200 USDT、单日 ≤600 USDT，远低于单场所 2,500 与总资金 5,000；不加杠杆、不借钱；买单最大亏损就是本金。容量写清了：单臂盘口 123–546 USDC，5,000 USDT 放不满。
4. **不重复：按审计判为变体，已申报补充** — 我在 2026-10-20 用 `grep -ril "app store|app-store|itunes|排行榜|rank"` 扫了 `known/KNOWN.md`、`bots/*/CLAIMS.md`、`bots/*/INDEX.md`、`bots/*/entries/`：`known/` 无命中，相关的是本机器人自己的 `quant-007`（月度 AI 榜首，结算源 arena.ai，月末 12:00 ET）、`quant-010`（Netflix/Spotify 周榜日更抢跑）与 `quant/CLAIMS.md` 里 B14 这一行。差异：数据源（Apple 榜单 JSON 已实测可读 vs arena.ai 返回 403）、板块与模板（App Store 每周五 #1/#2/free/paid，negRisk 带 `Other` 兜底臂）、频率（约 5 个结算日/月 vs 1 次/月）、以及本条有可算的 `Other` 基率 14/117；与 `quant-010` 的差异是结算取数方式：本条是**结算日 12:00 ET 的瞬时榜单快照**，`quant-010` 是**周榜聚合的日更 nowcast**。**核心机制「用公开榜单的当前值给『固定时刻快照』结算的市场定价」与 quant-007 同源，只是标的和频率不同；按 GUIDE 第 6 节这是变体，故本条已按 `kind: supplement`、`improves: quant-007` 申报，不主张全新机制，是否采纳为补充由主审决定。**
5. **扣成本后粗算够用：不确定** — 吃单费实取 `rate=0.05`（不是 GUIDE 的 tech 0.04），p=0.90 时费/名义 0.50%，加半价差约 2.2%/笔。用 2025 年 P1=90.1%（事后放宽口径）算，06:00 预先买 YES 的盈亏平衡约 0.881；0.88 以上负 EV，0.86 以下才有 2% 以上毛边；换成事先写死的 87.0%，盈亏平衡约 0.849、0.83 以下才有 2% 以上毛边——两种口径下结论一致：**没有历史盘口证明榜单显示 #1 时 YES 会卖到那么低**。最后 1 小时的窄窗口是否有足够价差，仍要前向记录；`observed_net_return=null`、`backtest_count=0`，不写正收益。另一个可算的反例：买全 basket NO 的盈亏平衡需要 `P(Other)=22.7%`（`#1` board）与 65.4%（`#2` board），都 ≥ 本次实测基率 12.0%，所以 basket 方向明确不做。
6. **两周内能检验：不满足** — 独立结果按日期计，近期约 5 个结算日/月，两周只有约 2–3 个，凑不到 30 个（约需 6 个月）。按 GUIDE 第 2 节第 6 条，本类应进**待选区**。
7. **出处可查：满足** — 每个数字都有 URL、访问日期和取数方式；榜单数字是两个端点现场对比+结算源网页 HTML 顺序（我算的）；Wayback 4,295 个快照、两组口径的基率（54/71 个双窗口日）、CLOB 21/247、`Other` 14/117 都是本次脚本输出（全文与原始输出见文末 `notes/r2prep-verification/quant-017.md`）；Gamma 自报的 volume/liquidity 都标了「来源自报，未核实」；Wayback 对 RSS 只有 1 个快照、CLOB 226/247 返回 0 点、158 张目标快照只有 150 张解析成功这些失败都照写。

## 出处

- https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json — 访问 2026-10-20T05:14Z — 已读（HTTP 200，25,783 字节，`updated=Tue, 20 Oct 2026 05:14:43 +0000`，50 条，top12 与名次）
- https://apps.apple.com/us/charts/iphone — 访问 2026-10-20T05:14Z — 已读（HTTP 200，1,017,064 字节，HTML 内嵌序列 `Capital One Mobile → Vinted → Muse from Meta → ...`；这是规则指定的结算源页面）
- https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest — 访问 2026-10-20 — 已读（HTTP 200，4,295 个 200 快照，2022-06-04..2025-11-03，454 个 UTC 日期）
- https://web.archive.org/web/20250101050435id_/https://apps.apple.com/us/charts/iphone — 访问 2026-10-20 — 已读（HTTP 200，gzip 解压后 767,828 字节；`schema:top-free` 第 1 位 = `CapCut - Video Editor`）
- https://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com%2Fapi%2Fv2%2Fus%2Fapps%2Ftop-free%2F50%2Fapps.json&output=json&fl=timestamp,statuscode&limit=3 — 访问 2026-10-20 — 已读（HTTP 200，只有 1 个快照 `20230522143120`）
- https://web.archive.org/cdx/search/cdx?url=itunes.apple.com%2Fus%2Frss%2Ftopfreeapplications%2Flimit%3D50%2Fjson&output=json&fl=timestamp,statuscode&limit=8 — 访问 2026-10-20 — 已读（HTTP 200，只有 1 个快照 `20180107065423`）
- https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone%2Ffree-apps&output=json&fl=timestamp,statuscode&limit=8 — 访问 2026-10-20 — 已读（HTTP 200，`[]`，无快照）
- https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fapp-store%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode&limit=8 — 访问 2026-10-20 — 已读（HTTP 200，`[]`，无快照）
- https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all&page=1..5 — 访问 2026-10-20 — 已读（HTTP 200；5 页去重 247 个事件，`totalResults=247`；242 已关闭、5 在途；free 141 / paid 76 / other 30）
- https://gamma-api.polymarket.com/events?slug=2-free-app-in-the-us-apple-app-store-on-october-23-10172026 — 访问 2026-10-20 — 已读（规则原文、12 个市场、7 真候选 + 4 Reserved + Other、`feeSchedule` rate=0.05、`clobRewards`、`negRisk=true`、volume 3,197.81）
- https://gamma-api.polymarket.com/events?slug=1-free-app-in-the-us-apple-app-store-on-october-23-10172026 — 访问 2026-10-20 — 已读（volume 5,918.22、liquidity 5,115.60、7 臂报价；Capital One Mobile 不在候选里）
- https://clob.polymarket.com/prices-history?market=<247 个事件的第一个 token>&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（HTTP 200；21 个事件 >0 点，226 个 0 点；16 个已关闭的正点事件覆盖 4 个独立结算日；196 个市场中 92 个有历史）
- https://web.archive.org/cdx/...（通配符查询 `rss.applemarketingtools.com*`、`apps.apple.com/us/charts/iphone*` 等） — 访问 2026-10-20 — **HTTP 000 / 超时**，未用于结论；改用上面的精确 URL 查询


---
