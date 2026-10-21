---
id: quant-006
name_zh: 网球Elo给PM比赛盘定价
name_en: Tennis Elo vs Polymarket match-winner (tennis + esports same template)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: sports
kind: new
improves: -
category: S
return_type: direction
instruments: 单打网球比赛胜者二元市场（模板 `atp-<球员1>-<球员2>-YYYY-MM-DD`、`wta-...`、`itf-...`；每个比赛事件下还挂让盘/总分/单盘胜者等子市场，本条只做“胜者”主市场）
venues: Polymarket
data: 免费免密钥：Tennis Abstract ATP/WTA Elo 榜（每周更新，本轮读到 2026-10-19 版）、公开归档镜像 Aneeshers/tennis-sackmann-archive 的 ATP/WTA 2010–2026 比赛数据（原始 JeffSackmann 仓库 404；镜像止于 2026-05-25，可回放时点 Elo）、Gamma events/markets（价格、feeSchedule、结算后 outcomePrices）、data-api 成交（可还原已关闭市场的赛前可成交价）；已关闭市场的 L2 历史盘口仍未取到，买价按“最后成交价 + 1¢”近似
test_2w: 已按预先写死的标准完成历史检验（q006-hist，2026-01-04..2026-05-19，2080 场有价、1366 笔触发，每份净收益中位 −0.114895，判 FAIL）；若要重新检验该机制，须先修正 Elo/成本假设（如场地分项 Elo、真实 ask）再另做独立样本外回测，不得复用本轮数据调参
status: 草稿
confidence: 中
---

> **2026-10-20 降为草稿（撤回第 1 轮复核）**：按 `bots/quant/notes/q006-hist/REPORT.md` 的历史可成交价回测（data-api 赛前成交 + 只用此前比赛回放的时点 Elo），2080 场有价、1366 笔触发，主窗口每份净收益中位数 −0.114895、每美元投入 −0.063537，触发了本条预先写死的失败标准（≥30 笔且中位数 ≤0）→ **FAIL**；敏感性窗口与 `date_lag_days ≤ 2` 子集同样为负；2064 场上 Elo Brier 0.216187 劣于市场 0.196510。门槛 1、5、6 因此改为不满足。正文以下保留原稿结构，其中“没有回测”“Sackmann 仓库 404”等说法已按该报告与 I02 复算更新（报告改用公开归档镜像，数据止于 2026-05-25）。I02 在 `bots/quant/notes/scheduler/scratch/I02/` 只读 `matches.csv` 独立复算，并做零成本敏感性：把 1¢ 半价差和手续费全部置零后，1366 笔的每份净收益中位数仍为 −0.100000、均值 −0.010985，负结论不变（`verify_output.txt`）。

## 一句话

在 Polymarket 的单打网球比赛胜者市场，用 Tennis Abstract 公开的 Elo/hElo/cElo 算出 p_model，只在 `p_model − 可成交卖价 − 吃单费 > 0` 且超过 2¢/份时吃单买入该侧，持有到结算，不提前平仓。

## 钱从哪里来

对手方（其他吃单者/挂单者）在低级别、低关注度比赛上的定价误差。付款方不是平台，而是把某位球员的价格挂得偏离公开 Elo 隐含概率的交易对手。机制能持续的前提是：Elo 榜公开、免费、每周更新，但要把“哪位球员在哪个赛事、当天谁上场”对上号并算概率需要人工核对（Polymarket 的 slug 用缩写名，Elo 榜用全名，如 slug `itf-hurkac1-chang4` 里的 Nika Hurkacz 与 ATP 榜里的 Hubert Hurkacz 不是同一人），所以报价不会立刻被抹平。**这一条是推断；q006-hist 的历史回测没有支持它，反而显示按该规则买入后亏损。**

## 规则

### 市场模板与示例（Gamma 快照，2026-10-20 抓取）

- 模板：每个比赛一个 event，event 里 16 个子市场（本轮读到的 `atp-friend-geerts-2026-08-25` 有 16 个），其中第 1 个是“谁赢”，其余是 completed-match、单盘胜者、让盘 ±1.5、总分 21.5/22.5/23.5、单盘总分等。本条只做胜者主市场。
- 示例 1（进行中，2026-10-20）：`itf-lacass1-arsene1-2026-10-20`，W75 Saguenay: Raphaelle Lacasse vs Ariana Arseneault，`outcomePrices=["0.265","0.735"]`、`spread=0.03`、`liquidity=3327.0396`、`orderMinSize=5`、`orderPriceMinTickSize=0.01`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}`、`closed=false`。
- 示例 2（进行中）：`itf-arsene3-kuhar1-2026-10-20`，M15 Ithaca: Mikael Arseneault vs Matt Kuhar，`outcomePrices=["0.625","0.375"]`、`spread=0.03`、`liquidity=1496.0896`，同一 `feeSchedule`（rate 0.05、rebateRate 0.15）。
- 示例 3（进行中，反例）：`itf-hurkac1-chang4-2026-10-20`，`outcomePrices=["0.515","0.485"]`、`spread=0.91`、`liquidity=71.8424`；价差 91¢ 的市场按本文阈值不可能有正期望，用来演示“必须按卖价而不是中间价算”。
- 示例 4（已结算，可核对结算字段）：`atp-friend-geerts-2026-08-25`，event `volume=58047.700409`、16 个市场，胜者市场 `outcomePrices=["1","0"]`、`resolutionSource=https://www.atptour.com/en/scores/current`、`endDate=2026-09-01T09:00:00Z`。
- 示例 5（电竞，同一机制）：`cs-sashi-vs-hotu-2025-09-18`，CS: Sashi vs HOTU，`outcomePrices=["1","0"]`、`feeSchedule` 字段为 `None`（2025 年的老市场没有该字段，不能据此说电竞免费），结算源 liquipedia。

### 结算规则原文要点（**不存在统一模板，必须逐市场读描述**）

- `atp-friend-geerts-2026-08-25` 描述原文：比赛取消/打平/到 2026-09-08 23:59 ET 仍未定胜负 → resolve to **50-50**；“If the match begins but is not completed, and one player advances due to the opponent's retirement, default, or disqualification, this market will resolve to the player who advances.”（中途退赛/取消资格 → 判给晋级者）；“If the match ends in a walkover (player withdraws before the start and the other advances automatically), this market will resolve to 50-50.”（**开赛前弃权 = walkover → 50-50**）。结算源：ATP Tour 官方信息，可用可信报道共识。
- `wta-yastremska-vs-siegemund-2025-10-06` 描述原文：取消/打平/延迟超过 7 天 → 50-50；但“If the match ends in a walkover ..., this market will resolve in favor of the player(s) who officially advances to the next round.”（**walkover → 判给晋级者**）。结算源 `https://www.wtatennis.com/scores`。
- 结论（本条最重要的一条规则证据）：同样是网球胜者市场，**walkover 的处理在两个模板里相反**（2026-08-25 ATP 版 50-50；2025-10-06 WTA 版判给晋级者）。买 0.735 的热门遇到 walkover，前者只退 0.5（每份亏 0.235），后者退 1.0。因此进场前必须读该 market 自己的 description，不能套用上一个市场的规则。
- `cs-sashi-vs-hotu-2025-09-18`（电竞）描述原文：延后 → 市场保持开放直到打完；彻底取消且无补赛 → 50-50；结算源 liquipedia。电竞没有“退赛判给晋级者”的等价条款，处理方式不同。
- 结算时区：网球描述里截止时间是 `11:59 PM ET`，事件 `endDate` 是 UTC（示例 4 为 `2026-09-01T09:00:00Z`），两者差 4 小时。

### 进场、出场、仓位

- p_model：`p = 1/(1+10^(-(Elo_A-Elo_B)/400))`。Tennis Abstract 原文写“100 分差 → 三盘两胜里热门 64%”；本条用标准 Elo 公式复算 `1/(1+10^(-100/400))=0.6400`，与原文一致，所以采用 `400` 尺度。优先用同一榜单里的 hElo（硬地）/cElo（红土）/gElo（草地），场地不明时用总 Elo。
- 可成交价用卖价（=`mid + spread/2`，没有 L2 时按此近似；有 L2 时用真实 ask）。中间价只能用于生成候选，不能用于算 EV。
- EV/份 = `p_model − ask − 0.05×ask×(1−ask)`（rate 取该市场 `feeSchedule.rate`，本轮读到的网球市场都是 0.05）。只做 `EV/份 ≥ 0.02` 的一侧；两侧都不满足就不下注。
- 过滤：任一球员不在当周榜单（未达“近 52 周 10 场以上巡回赛/资格赛/挑战赛/ITF 5 万美元以上”门槛）→ 跳过；`spread > 0.10` → 跳过；`liquidity < 200` → 跳过；比赛已开始 → 不进场。
- 仓位：单场 ≤ 100 份且 ≤ 60 USDT；同一赛事日 ≤ 5 场；未结算敞口合计 ≤ 300 USDT；场地总预算 ≤ 2,500 USDT（总资金 5,000）。
- 出场：只有两种——结算，或结算前发现比赛改期/球员退赛公告（此时按当时 bid 平掉，费用按 taker 再算一次）。不做“开赛后对冲”。
- 不挂单：本条全部吃单进场，避免“挂单必然成交”的假设；maker 返佣（网球 `rebateRate=0.15`）不计入收益。

## 证据

- **Elo 榜（官方页面原文，2026-10-19 更新）**：ATP 页写 “A 100-point difference in Elo ratings implies that the favorite has a 64% chance of winning a best-of-three-set match; 200 points implies 76%, 300 points implies 85%, 400 points implies 91%, and 500 points implies 95%.”，并写明榜单只收“近 52 周完成 10 场以上巡回赛/巡回赛资格赛/男子挑战赛/ITF 5 万美元以上”的球员；WTA 页有同样的句子、同样 `Last update: 2026-10-19`。这是模型输入，不是收益证据。
- 同日榜面上的具体数字（`Elo` 列）：Sinner 2296.9、Alcaraz 2149.8、Siegemund 1762.3、Yastremska 1762.2、Hanna Chang 1355.0、Ariana Arseneault 1266.4。我的算术：Sinner−Alcaraz=147.1 → p=0.6999；Siegemund−Yastremska=0.1 → p=0.5001；Chang−Arseneault=88.6 → p=0.6248。以上是公式演示，不是任何市场的成交价对比。
- **覆盖率实测（关键负面证据）**：示例 1 的 Lacasse 在 WTA 榜里查不到（榜单里只有 Arseneault 1266.4），示例 3 里的 Nika Hurkacz 在 ATP 榜里查不到（榜单里的 Hurkacz 是 Hubert Hurkacz 1897.8），示例 2 的 Kuhar 也未查到 —— 即当前挂牌的比赛里，很多是 M15/W15/W35 这类低于 5 万美元、球员未达门槛的赛事，模型无法定价。这是本条最大的现实约束。
- **费用**：官方 Fees 页原文表格 “Sports 0.05 / 0 / 15%”（Taker / Maker / Maker Rebate），公式 `fee = C × feeRate × p × (1 - p)`；Gamma 里网球市场的 `feeSchedule` 也确实是 `rate: 0.05, takerOnly: true, rebateRate: 0.15`（两个来源一致，属配置值与文档一致，不是实际扣费回执）。
- **每月挂牌数量（自己数，Gamma 分页）**：筛 `tag_slug=tennis`、`closed=true`、`end_date_min=2026-09-01T00:00:00Z`、`end_date_max=2026-10-01T00:00:00Z`，offset 0–800 每页 100 条全部非空，按 slug 去重后 **900 个唯一 event（这是本轮分页上限，实际只会更多，不是精确总数）**；slug 前缀分布：`itf-` 621、`atp-` 166、`wta-` 101、其他 12；再剔除 doubles/winner/rank/qualifying 后，**atp-/wta- 单打比赛事件 219 个**。这是 2026 年 9 月一个自然月，换算每天约 7.3 场（219/30）。
- **当前挂牌（2026-10-20 快照）**：`closed=false&tag_slug=tennis&limit=100` 返回满 100 条（说明 ≥100），其中 `itf-` 46、`atp-` 39、`wta-` 10、`will-` 3、`nitto-` 2；atp-/wta- 前缀且非 doubles 的 41 条，但其中多数是“年终排名/入围”类，真正的比赛市场集中在 ITF 级别。
- **历史回测（q006-hist，已合并；I02 复用不重跑）**：2080 场有赛前成交价、1366 笔触发；主窗口每份净收益中位 −0.114895、均值 −0.031543、每美元投入 −0.063537，敏感性窗口与 `date_lag_days ≤ 2` 子集同样为负；Elo Brier 0.216187 劣于市场 0.196510。I02 只读 `matches.csv` 独立复算，结果一致；零成本敏感性（去掉 1¢ 半价差与手续费）后中位仍 −0.100000、均值 −0.010985。完整方法与限制见 `bots/quant/notes/q006-hist/REPORT.md`，复算见 `bots/quant/notes/scheduler/scratch/I02/verify_output.txt`。Sharpe、最大回撤仍未计算。
- **原始仓库未查到，改用公开归档镜像**：Jeff Sackmann 的 `tennis_atp` GitHub 仓库本轮打不开（`api.github.com/repos/JeffSackmann/tennis_atp`、`github.com/JeffSackmann/tennis_atp`、`raw.githubusercontent.com/.../{main,master}/atp_matches_2026.csv` 全部 404），所以不把原仓库当来源；q006-hist 改用 README 注明为归档镜像的 `https://github.com/Aneeshers/tennis-sackmann-archive`（本轮复查 HTTP 200；`atp/atp_matches_2026.csv` 300,795 bytes，含 `tourney_date` 等列），并用其 2010–2026 比赛数据回放时点 Elo（镜像数据止于 2026-05-25）。

## 数据

- `https://tennisabstract.com/reports/atp_elo_ratings.html`（HTTP 200，289,710 bytes）与 `https://tennisabstract.com/reports/wta_elo_ratings.html`（HTTP 200，267,826 bytes）：免费、免密钥、每周更新，本轮读到 `Last update: 2026-10-19`。只给“当前”评分，**没有 as-of 历史评分**；q006-hist 改用公共归档镜像的 2010–2026 比赛数据回放时点 Elo（赛事周粒度）。
- `https://gamma-api.polymarket.com/events?slug=<event-slug>`、`?tag_slug=tennis&closed=false|true&end_date_min=..&end_date_max=..&limit=100&offset=..`：免费、免密钥；给 description（规则原文）、`outcomePrices`（结算后为 `["1","0"]`）、`feeSchedule`、`liquidity`、`spread`、`orderMinSize`、`orderPriceMinTickSize`、`rewardsMinSize`。
- `https://data-api.polymarket.com/trades?market=<conditionId>&limit=N`：免费、免密钥；实测返回 `price/size/side/outcome/timestamp/slug`（示例：Wuhan 那场 `price=0.999, size=7050, side=BUY, outcome=Siegemund`），适合做结算前成交核对。
- `https://clob.polymarket.com/prices-history?market=<conditionId>&interval=max`：本轮对已关闭市场返回 `{"history":[]}`，**拿不到历史盘口**；要做盘口回测只能从现在起自建记录（每场赛前 1 小时抓一次 best bid/ask）。
- 缺失/近似：逐场“入场时”Elo 只能用赛事周前回放近似（q006-hist 已做）；挑战赛/ITF 排名、历史 L2 盘口、退赛公告的结构化数据仍缺（只能读文字）；q006-hist 的买价用“最后成交价 + 1¢”近似，不是真实 ask。

## 两周内怎么检验

- 历史侧已完成（见门槛 6）：2080 场有价、1366 笔触发，判 FAIL。以下保留原前向方案，仅作为若修正模型后重新检验的模板。
- 前向起点 2026-10-20，每天对 `tag_slug=tennis&closed=false` 里所有 atp-/wta-/itf- 单打胜者市场记录：slug、球员名、`outcomePrices`、`spread`、`liquidity`、`feeSchedule.rate`、抓取时间；对每个市场在开赛前 1 小时再抓一次。名称与当周 Elo 榜对齐（手工或模糊匹配 + 人工核对，必须记录核对结果）。
- 逐场算 p_model、ask、EV/份；按上文阈值决定是否“纸面买入”，记录份额、价格、费用，等 Gamma 把该市场 `outcomePrices` 改成 `["1","0"]`/`["0","1"]` 或 50-50 后结算。
- 独立结果**按比赛场次计**：同一 event 下的胜者/让盘/总分多档只算 1 个结果；同一对球员在两周内重复交手也只算 1 个（取第一次）。
- 数量：2026-09 有 219 场 atp-/wta- 单打事件 → 两周约 110 场（219×14/30≈102，取整为约 100–110）；但这些比赛中“两人都在榜上”的比例未知，本轮实测的几个示例全部不满足，所以**能否凑够 30 笔触发未知**。凑不够就只记为前向观察，不得写成 30 个结果。
- 失败标准（预先写死）：触发 ≥30 笔时，每份净收益（结算现金流 − 买入价 − 费用）的**中位数 ≤ 0**，或按价差分档（ask<0.3 / 0.3–0.7 / >0.7）中任意一档的净收益均值 ≤ 0 且该档 ≥10 笔，即判失败。只跑通过/不通过，不做参数搜索。

## 成本与容量

- 费用（`fee = C × 0.05 × p × (1−p)`，网球 `rate=0.05`）：ask=0.265 时每份 0.009739 USDC，占投入 3.675%；ask=0.625 时 0.011719，占 1.875%；ask=0.735 时 0.009739，占 1.325%。价格越接近 0.5 越贵，越靠近两端越便宜。
- 价差：示例 1/2 的 `spread=0.03`，半价差 1.5¢，占 ask=0.625 的投入 2.4%；示例 3 的 `spread=0.91` 直接不可做。这就是“2¢/份门槛”的由来：没有 2¢ 边际，费用+半价差就吃掉了。
- 算术示例（只演示公式）：ask=0.735、p_model=0.80 → EV/份 = 0.80 − 0.735 − 0.009739 = +0.0553 USDC，占投入 7.5%；同一笔若遇 walkover 判 50-50，实际收益 = 0.5 − 0.735 − 0.009739 = −0.2447/份。
- 容量：单场 100 份 × 0.735 ≈ 73.5 USDT，示例 2 的 `liquidity=1496` 足以承接，示例 3 的 `liquidity=71.8` 不行。挑战赛 `atp-cadenas-sachko-2026-10-02` 的市场已结算、event 未关闭（volume 为累计值仍会增长），event `volume=232018.803794`、`atp-friend-geerts-2026-08-25` event `volume=58047.700409`，说明流动性在赛事之间差两个数量级。5,000 USDT 总资金下按 300 USDT 未结算敞口算，容量不是约束，**能凑够独立结果数才是约束**。
- 资金占用：单场从进场到结算通常 <24 小时（示例 4 的 event `endDate` 是开赛后约 7 天的最迟结算日），年化换算需按实际占用天数算，本文不给年化。

## 风险

- **walkover 规则风险（最大）**：买 0.735 的热门，若开赛前对手弃权且该市场按 ATP 2026-08-25 模板判 50-50，一下亏 0.2447/份（约 33.3% 投入，含吃单费）；而 2025-10-06 的 WTA 模板会判给晋级者（赚满）。同一平台两套规则，选错市场等于换了一个赌注。
- **模型风险**：Elo 每周才更新（“Updated weekly(ish)”），不含伤病、退赛、旅行、场地速度变化；对低级别球员样本少、评分噪声大。
- **覆盖风险**：当前挂牌以 M15/W15 为主，这些球员进不了榜单，模型无从下手；能做的场次可能很少。
- **数据风险**：历史 as-of Elo 只能用赛事周前回放近似；已关闭市场的 L2 历史盘口仍拿不到（CLOB prices-history 返回空），q006-hist 用 data-api 最后成交价 +1¢ 近似买价。回测已做（2026-01..2026-05），但样本受镜像止于 2026-05-25 限制。
- **结算争议**：网球描述允许“可信报道共识”作为辅助结算源；电竞用 liquipedia（社区站点）。改期、弃权、判负的认定可能与模型假设不同。
- **平台**：示例 event 都是 `restricted=true`；`orderMinSize=5`、tick=0.01，最小下单 5 份。
- **费用变化**：官方费率表当前 Sports=0.05、maker 返 15%，但费率由协议设定，可改；`cs-sashi-vs-hotu-2025-09-18` 的 `feeSchedule` 为 `None` 说明字段本身也不稳定。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：不满足（2026-10-20 更新）— 机制本身可一句话说清（对手方定价偏离公开 Elo），但“偏离会持续存在且方向可交易”的推断已被 q006-hist 历史回测反驳：1366 笔触发每份净中位 −0.114895，Elo Brier 也劣于市场。
2. 有免费数据能检验：满足（2026-10-20 更新，有限）— Gamma 给结算结果和当前价、Tennis Abstract 给当前 Elo、data-api 给成交，都免费免密钥；历史 as-of Elo 用公开归档镜像 Aneeshers/tennis-sackmann-archive 的 ATP/WTA 2010–2026 数据回放（原始 JeffSackmann 仓库 404；镜像止于 2026-05-25），历史成交价用 data-api 还原，q006-hist 已跑通 2080 场有价；已关闭市场的 L2 历史盘口仍未取到。
3. 小资金能做：满足 — `orderMinSize=5`、tick=0.01，单场 100 份约 26–74 USDT；示例市场 `liquidity` 71.8–3327 USDT，2,500 USDT 场所上限和 5,000 总资金都放得下；但低价差场次的可成交量未实测。
4. 不重复：不确定 — 本条用外部评分模型给体育比赛定价（category S），与做市/奖励类条目收益来源不同；已按 `bots/quant/CLAIMS.md` B03 行登记去重：区别 dot C13（伤病消息），电竞同机制并入本题。
5. 扣成本后粗算够用：不满足（2026-10-20 更新：notes/q006-hist 历史回测 1366 笔触发、净中位 −0.114895/份；I02 零成本敏感性去掉 1¢ 半价差与手续费后中位仍 −0.100000、均值 −0.010985）— 原稿： 费用与半价差可精确算（示例 ask=0.625 时费 1.875%+半价差 2.4%），但**没有回测也没有实测胜率**，`observed_net_return=null`，不能声称扣费后为正。
6. 两周内能检验：不满足（2026-10-20 更新，复用已合并的 q006-hist，不重跑）— 已按预先写死的失败标准完成历史检验：2026-01-04..2026-05-19、2080 场有赛前 data-api 成交价的比赛，触发 1366 笔（≥30）；主窗口每份净收益中位 −0.114895、均值 −0.031543、每美元投入 −0.063537，命中率 0.470（642/1366）；敏感性窗口 [−24h,−1h] 中位 −0.094095（1379 笔），`date_lag_days ≤ 2` 子集中位 −0.182218（800 笔），均为负；Elo Brier 0.216187 劣于市场 0.196510。I02 只读 `matches.csv` 独立复算一致，零成本敏感性后中位仍 −0.100000。最接近为正的分档是 ask>0.7（219 笔，中位 +0.192000、均值 +0.011021），但另两档均值也为负（REPORT：ask<0.3 为 −0.030074/246 笔，0.3–0.7 为 −0.042290/901 笔）；无论按整体中位还是按预设分档规则都判 **FAIL**。原文见 `bots/quant/notes/q006-hist/REPORT.md`，复算见 `bots/quant/notes/scheduler/scratch/I02/verify_output.txt`。
7. 出处可查：满足 — 每个数字都有本轮抓到的 URL、HTTP 状态和原文片段（见 `bots/quant/notes/batch1-verification/quant-006.md` 核对日志）；未查到的（原始 Sackmann 仓库、历史 L2 盘口）已明确写“404/返回空”，归档镜像与复算路径均已写明。

## 出处

- https://tennisabstract.com/reports/atp_elo_ratings.html — 访问 2026-10-20 — 已读（Elo 榜、100 分=64% 原文、`Last update: 2026-10-19`、球员评分）
- https://tennisabstract.com/reports/wta_elo_ratings.html — 访问 2026-10-20 — 已读（同句映射说明、`Last update: 2026-10-19`、Arseneault 1266.4、Hanna Chang 1355.0）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-20 — 已读（`fee = C × feeRate × p × (1 - p)`、Sports 0.05 / maker 0 / rebate 15%）
- https://gamma-api.polymarket.com/events?closed=false&limit=8&tag_slug=tennis&order=startDate&ascending=false — 访问 2026-10-20 — 已读（示例 1/2/3 的价格、spread、liquidity、feeSchedule）
- https://gamma-api.polymarket.com/events?slug=atp-friend-geerts-2026-08-25 — 访问 2026-10-20 — 已读（结算规则原文、16 个子市场、volume、resolutionSource、已结算 `["1","0"]`）
- https://gamma-api.polymarket.com/events?closed=true&tag_slug=tennis&end_date_min=2026-09-01T00:00:00Z&end_date_max=2026-10-01T00:00:00Z&limit=100&offset=0..800 — 访问 2026-10-20 — 已读（900 个唯一 event、前缀分布、219 场单打）
- https://gamma-api.polymarket.com/public-search?q=tennis&limit_per_type=5 — 访问 2026-10-20 — 已读（`wta-yastremska-vs-siegemund-2025-10-06` 规则原文：walkover 判给晋级者、取消 50-50、结算源 wtatennis.com/scores）
- https://gamma-api.polymarket.com/public-search?q=Counter-Strike&limit_per_type=3&events_status=active — 访问 2026-10-20 — 已读（电竞示例 `cs-sashi-vs-hotu-2025-09-18` 规则：延后保持开放、取消 50-50、结算源 liquipedia、`feeSchedule=None`）
- https://data-api.polymarket.com/trades?market=0x5a9641cc6e3a60a0e729493ef4d9fe81d5aacfc06d5c49511248462afe969be9&limit=3 — 访问 2026-10-20 — 已读（成交字段与示例成交）
- https://clob.polymarket.com/prices-history?market=0x5a9641cc...&interval=max — 访问 2026-10-20 — 已读（返回 `{"history":[]}`，历史盘口不可得）
- https://github.com/Aneeshers/tennis-sackmann-archive — 访问 2026-10-20 — 已读（公开归档镜像 README；q006-hist 的历史比赛数据来源）
- https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/atp/atp_matches_2026.csv — 访问 2026-10-20 — 已读（HTTP 200、300,795 bytes、含 `tourney_date` 列）
- https://api.github.com/repos/JeffSackmann/tennis_atp — 访问 2026-10-20 — 已尝试，404，**不作为来源**
- https://raw.githubusercontent.com/JeffSackmann/tennis_atp/{main,master}/atp_matches_2026.csv — 访问 2026-10-20 — 均 404，**不作为来源**
- https://polymarket.com/api/rewards/markets/current — 本轮未访问，不引用
- 本地复现（非 URL）：`bots/quant/notes/q006-hist/REPORT.md`、`run_output.txt`、`matches.csv`；`bots/quant/notes/scheduler/scratch/I02/verify.py`、`verify_output.txt` — 访问 2026-10-20 — 已读（历史回测原始报告 + 独立复算）
