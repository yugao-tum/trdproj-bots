---
id: quant-027
name_zh: 板球T20球球评级定价检验
name_en: "T20 cricket moneyline: Cricsheet ball-by-ball ratings vs Polymarket"
bot: quant
date: 2026-10-20
market: polymarket
pm_category: sports
kind: new
improves: -
category: S
return_type: direction
instruments: "Polymarket T20 单场胜负二元市场：IPL（`ipl-<tla>-<tla>-YYYY-MM-DD`，2025 年也有 `chennai-super-kings-vs-mumbai-indians` 这类全名 slug）、T20 World Cup（`crint-<a>-<b>-YYYY-MM-DD`）、T20I 系列（`intt20-<a>-<b>-YYYY-MM-DD`、`t20-<a>-<b>-YYYY-MM-DD`）；同一比赛可能是一个 2-outcome 市场，也可能拆成两个 YES 市场"
venues: Polymarket
data: "Cricsheet `t20s_male_json.zip`（14,479,929 B；3,629 个 JSON，解析 3,627 场）与 `ipl_json.zip`（5,187,770 B；1,245 个 JSON，解析 1,243 场），免费免密钥，2005-02-17..2026-10-14；Gamma events/markets（2,100 个 closed cricket events、522 个 T20 胜负市场）；data-api `trades?market=<conditionId>`（210 个市场、原始成交约 102 MB，缓存不入库）"
test_2w: "独立结果按一场比赛计；历史已取到 198 个可成交、结算明确的比赛（2024-06-11..2026-03-24，T20I 131 + IPL 67），超过 30；两周内前向再记录当前 T20 系列约 10–30 场。失败标准（写死）：预注册规则在 ≥30 个独立结果上每份净收益均值 ≤ 0；本轮 198 场里触发 117 笔，每份 −0.0414，已触发失败。"
status: 草稿
confidence: 中
---

整理说明：本条是**负结果**条目，不是可上线策略。目标是把“Cricsheet 球球数据评级能否给 Polymarket T20 单场胜负定价”这个问题用可成交的历史价格一次测清楚。所有数字都来自本轮实际下载的 Cricsheet JSON、Gamma 快照和 data-api 成交；脚本与 stdout 在 `bots/quant/notes/scheduler/scratch/B24/`（`parse_cricsheet.py`、`build_ratings.py`、`ballstats.py`、`model.py`、`match_pm.py`、`fetch_prices.py`、`evaluate.py`、`final_test.py`，输出 `model.log`、`numbers.log`、`final_test.log`）。

## 一句话

在 Polymarket 的 T20 单场胜负市场，用 Cricsheet 球球数据构建赛前 Elo + 近期得失分率模型，只在模型概率高出赛前最后成交价 5¢ 时吃单买入，持到结算；198 场历史可成交检验里触发 117 笔，扣 0.05 费 + 1¢ 半价差后每份 **−4.14¢**，没有发现 edge，本条记录失败并给出可复现口径。

## 钱从哪里来

**机制假设**：T20 单场方差大、比赛密集，Polymarket 的定价者常用“球队名气 + 上一场比分 + 明星球员”出价；Cricsheet 的逐球数据免费、完整，理论上可以算出比“名气”更准的球队强弱和近期得失分率，赚这些休闲资金的钱。付钱方是同一市场里的其他吃单者/挂单者，不是平台。机制能持续的前提是：球球数据虽然公开，但要清洗 JSON、对齐队名/日期、按时间顺序重建“当时的”评分，门槛不低，所以价格不会立刻被抹平。

**本轮的结论是这条链没有付钱方**。在 198 场可成交样本里，市场的 Brier 0.1745、log loss 0.5107；模型 Brier 0.2322、log loss 0.6553。市场在每个价格桶都比模型更接近实际胜率，尤其是两端：市场价 0.05 的 13 场全输，模型却给 0.472；市场价 0.957 的 23 场赢了 22 场，模型只给 0.607。也就是说，模型把强弱队都压向 0.5，而市场已经把“谁强谁弱”定得很准。下面按门槛逐条写清失败在哪。

## 规则

### 市场模板与示例

- 标签 `cricket`、series `ipl`（id=44）。本轮用 Gamma `events?tag_slug=cricket&closed=true` 分页取到 **2,100 个已关闭 event**（offset 2,100 返回 HTTP 422，说明这是分页上限；实际可能更多）。
- 从这 2,100 个 event 里筛出“两个 outcome、且不是 Yes/No”的胜负主市场，按 `conditionId` 去重得 **522 个 T20 单场胜负市场**。月度数量（按 eventDate）：2024-06 19、2024-07 3、2025-03 9、2025-04 42、2025-05 34、2025-06 2、2025-09 21、2025-10 13、2025-11 50、2025-12 78、2026-01 92、2026-02 80、2026-03 79。
- 示例 1（IPL 2025，单市场 2-outcome）：`ipl-rcb-rr-2025-04-24`，outcomes `["Royal Challengers Bangalore","Rajasthan Royals"]`，`outcomePrices=["1","0"]`，volume 102,041.37（来源自报，未核实），`resolutionSource=https://www.iplt20.com/`，`feeSchedule=null`、`feesEnabled=false`。
- 示例 2（T20 World Cup 2024）：`usa-vs-india-cricket-t20-world-cup`，outcomes `["USA","India"]`，`outcomePrices=["0","1"]`，volume 14,865.85（来源自报，未核实），`resolutionSource` 为空。
- 示例 3（T20 World Cup 2026，高成交）：`crint-gbr-nzl-2026-02-27`，outcomes `["England","New Zealand"]`，`outcomePrices=["1","0"]`，volume 1,720,269.71（来源自报，未核实），`resolutionSource=https://www.espncricinfo.com/`。
- 示例 4（T20I 系列，50-50 案例）：`intt20-aus-ind-2025-10-29`，outcomes `["Australia","India"]`，`outcomePrices=["0.5","0.5"]`，volume 33,452.80（来源自报，未核实），`resolutionSource=https://www.icc-cricket.com/fixtures-results`。
- 示例 5（2026 年三市场结构）：`crint-mex-arg-2026-03-14`，event 下 3 个市场：胜负主市场（`["Mexico","Argentina"]`，`outcomePrices=["0","1"]`）、谁赢抛硬币、比赛是否完成；volume 218.01（来源自报，未核实），`resolutionSource=https://www.espncricinfo.com/`。
- 示例 6（Asia Cup 2025）：`asia-cup-india-vs-pakistan-2025-09-14`，outcomes `["India","Pakistan"]`，`outcomePrices=["1","0"]`，volume 25,486.10（来源自报，未核实），`resolutionSource` 为空。
- 2025 IPL 有一批市场把队名截断成城市名（如 `Hyderabad`、`Rajasthan`、`Bangalore`），本条在匹配 Cricsheet 时统一映射到全名；这是数据清洗的一部分，也是“为什么不是所有人都能直接套模型”的实际门槛。

### 结算规则原文要点

**老模板（2024 T20 World Cup、2025 IPL、2025 Asia Cup）没有统一的详细条款，必须逐市场读 description：**

- `ipl-rcb-rr-2025-04-24` 原文：
  > In the upcoming IPL game, scheduled for April 24 at 10:00AM ET: If the Royal Challengers Bangalore win, the market will resolve to “Royal Challengers Bangalore”. If the Rajasthan Royals win, the market will resolve to “Rajasthan Royals”. If the game is postponed, this market will remain open until the game has been completed. If the game is canceled entirely, with no make-up game, this market will resolve 50-50.
  结算源：`https://www.iplt20.com/`。
- `usa-vs-india-cricket-t20-world-cup` 原文：
  > This market will resolve to whichever national team wins the ICC Men’s T20 World Cup 2024 match between USA and India, scheduled to begin June 12, 2024, 10:30 AM ET. If the game is declared tied, abandoned, has "no result", or doesn't finish before June 30, 2024, 11:59 PM ET - this market will resolve 50-50.
  **该市场 `resolutionSource` 为空**，描述也没有点名结算网站；只能按“ICC 官方比赛结果”理解。
- `asia-cup-india-vs-pakistan-2025-09-14` 原文：
  > In the upcoming Asia Cup game, scheduled for 2025-09-14 at 10:30 AM ET: If the India win, the market will resolve to "India". If the Pakistan win, the market will resolve to "Pakistan". If the game is postponed, this market will remain open until the game has been completed. If the game is canceled entirely, with no make-up game, this market will resolve 50-50.
  `resolutionSource` 同样为空。

**新模板（2025-10 以后的 T20I/T20 World Cup）条款更完整：**

- `intt20-aus-ind-2025-10-29`（`resolutionSource=https://www.icc-cricket.com/fixtures-results`）原文要点：
  > This market resolves according to the finalized match result as published by https://www.icc-cricket.com/fixtures-results. DLS/DRS, over-rate penalties, forfeit/walkover, or any other on-field ruling that leads the competition to declare a winner are treated as ordinary wins. If the match ends tied and the playing conditions provide an on-field tiebreak (e.g., Super Over), the winner determined by that tiebreak will be used for resolution. If the match ends tied and no on-field tiebreak is used or available under the playing conditions (e.g., group-stage ODI with no Super Over), the market will resolve 50-50. If the match is postponed/rescheduled, the market remains open until the listed fixture is completed. If the match is permanently canceled or abandoned or otherwise is completed without a winner, the market resolves 50-50.
- `crint-gbr-nzl-2026-02-27`（`resolutionSource=https://www.espncricinfo.com/`）把结算源换成 ESPNcricinfo，其余 DLS/DRS、forfeit/walkover、Super Over、延期、取消条款与上一条同义。
- `crint-mex-arg-2026-03-14` 同样以 ESPNcricinfo 为准，并明确“primary resolution source 是赛事官方统计；若官方未公布最终统计，再用可信报道共识”。

**口径结论（影响 y 和风险）**：

1. **弃赛/取消/无结果 = 50-50**：本轮样本里有 6 场 `outcomePrices=["0.5","0.5"]`（3 场 IPL 2025、3 场 T20I 2025）。买 0.3 的人遇到 50-50 会赚，买 0.7 的人会亏；这不是“赢了/输了”的二值结果，必须从胜负样本里剔除或单独处理。
2. **Super Over**：Cricsheet 把 Super Over 记成 `result: tie`，另给 `eliminator`（如 `India`、`Delhi Capitals`）；Polymarket 则按 Super Over 胜者结算。本条用 PM 的 `outcomePrices` 定 y，用 Cricsheet 的 `eliminator` 更新 Elo；本轮命中 3 场（2024-07-30 India vs Sri Lanka、2025-04-16 Delhi Capitals vs Rajasthan Royals、2025-09-26 India vs Sri Lanka）。
3. **结算源不统一**：2024 T20 WC 和 2025 Asia Cup 的 `resolutionSource` 为空；2025 IPL 用 iplt20.com；2025-10 后的 T20I 用 icc-cricket.com；2026 T20 WC 用 espncricinfo。买之前必须读该 market 自己的 description，不能套上一个市场的规则。
4. **时区**：描述里常见 “10:30 AM ET”，Gamma 的 `gameStartTime` 是 UTC；本条用 `gameStartTime` 作为“赛前”截止，不用描述里的 ET 时间手工换算。

### 预注册交易规则（本轮价格检验前写死）

1. **宇宙**：Gamma `tag_slug=cricket` 已关闭 event 中，两个 outcome 的胜负主市场；必须能按队名 + 日期（±2 天）匹配到 Cricsheet 的 T20I 或 IPL 比赛；同一 Cricsheet 比赛有多个 PM event 时只保留 volume 最大的一个，避免同一场重复计数。
2. **模型**：只用 2024-06-01 之前的 Cricsheet 比赛拟合，之后不再改参数。
   - Elo：初始 1500，K=20；按净胜分加权：按 runs 赢时 `1+0.05*min(runs,100)/10`，按 wickets 赢时 `1+0.05*min(wickets,10)/2`；平局/无结果不更新，Super Over 用 `eliminator` 当胜者更新。
   - 球球 form：每场从 deliveries 算每队 runs / legal balls 的 run rate；对每队维护半衰期 365 天的指数加权 `(本队 run rate − 对手 run rate)`；赛前取上一场之后的 form，`form_diff = form_team1 − form_team2`。
   - 逻辑回归：`p(team1 wins) = sigmoid(−0.03161193 + 0.56578515*(elo_diff/400) + 12.34014348*form_diff)`，其中 `elo_diff = R1 − R2`。系数来自 3,194 场 2024-06-01 前的比赛；全 Cricsheet 2024-06..2026-06 的 1,322 场样本外 log loss 0.6161（常数 0.6930）。
3. **价格**：对每个 outcome，取 `gameStartTime` 之前最后一笔 data-api 成交价（`trades?market=<conditionId>`，按 timestamp 升序取最后一条）；要求两侧都有成交，且 `|p0+p1−1| ≤ 0.10`，否则跳过。成交价不是 ask，所以进场价统一加 **1¢ 半价差**。
4. **信号**：`edge_i = p_model_i − p_mkt_i`。只做 `edge_i ≥ 0.05` 的一侧；若两侧都满足，只取 edge 更大的一侧（每场最多 1 笔）。`p_mkt_i < 0.02` 或 `> 0.98` 不做。
5. **成本**：吃单费按 GUIDE §8 的体育上限 **0.05** 计，`fee = 0.05 × entry × (1−entry)`；另加 1¢ 半价差。敏感性再算 0¢/2¢/5¢ 半价差。maker 返佣不计。
6. **仓位**：纸面 1 份起算；单场 ≤100 份，单日 ≤500 份，场所总敞口 ≤2,500 USDT，总资金 5,000 USDT；不加杠杆。
7. **出场**：只持到结算，不做赛中交易、不对冲、不提前平仓。
8. **失败标准**：在 ≥30 个独立结果（按比赛计）上，每份净收益均值 ≤0 即失败；若 >0 但 <2¢ 记为不确定；≥2¢ 才进入前向验证。

## 证据

### 1）Cricsheet 覆盖与模型样本外表现（自己算）

- 下载 `t20s_male_json.zip`（14,479,929 B，3,629 个 JSON）和 `ipl_json.zip`（5,187,770 B，1,245 个 JSON）；解析成功 **4,870 场**男子比赛（T20I 3,627 + IPL 1,243；4 个文件因缺日期/队伍跳过），日期 **2005-02-17..2026-10-14**。
- 训练集 3,194 场（2024-06-01 前），测试集 1,322 场（2024-06-01..2026-06-01，包含 PM 样本之外的比赛）。
- 测试集 log loss：模型 **0.6161**，常数 0.6930；Brier **0.2141**。按来源：IPL 144 场 **0.7003**，T20I 1,178 场 **0.6205**。也就是说，球球 Elo+form 对“一般 T20 比赛”有信号，但在 IPL 上明显更弱。
- 只用 Elo、不加 form 的测试集 log loss 是 0.6292；form 有增量，但增量不足以打过 PM 价格（见下）。

### 2）PM 样本：从 2,100 个 event 到 198 场

- 2,100 个 closed event → **522 个 T20 胜负市场**（按 conditionId 去重）。
- 其中 **231 个**能按队名 + 日期匹配到 Cricsheet；按 Cricsheet 文件去重后 **210 场**唯一比赛（同一场比赛在 PM 有 `ipl-...` 和城市名两个 event 的情况，只留 volume 大的）。
- 210 场里：1 场没有任何赛前成交；6 场 PM 结算为 50-50/无结果；剩 **203 场**有明确胜负。203 场里 202 场两侧都有赛前成交、1 场只有一侧；剔除 4 场两侧最后成交价之和偏离 1 超过 10¢ 的，剩 **198 场**进入主检验（T20I 131 + IPL 67；2024 年 13、2025 年 104、2026 年 81）。
- 成交价新鲜度：`gameStartTime − 最后一笔赛前成交` 的中位数 **0.039 小时（约 2.3 分钟）**，75 分位 0.19 小时，90 分位 0.50 小时，95 分位 2.01 小时，99 分位 9.41 小时，最大 43.5 小时。大多数价格是新鲜的，但尾部有隔夜 stale 价。
- 价格和：198 场两侧最后成交价之和的中位数约 1.01；4 场偏离 >10¢ 的已剔除。

**校准对比（市场价 p_mkt 分桶，n=198；模型价是同一场的模型概率）**：

| 市场价区间 | n | 市场均价 | 实际胜率 | 模型均价 |
|---|---:|---:|---:|---:|
| 0–0.1 | 13 | 0.051 | 0.000 | 0.472 |
| 0.1–0.2 | 6 | 0.142 | 0.000 | 0.515 |
| 0.2–0.3 | 3 | 0.217 | 0.000 | 0.491 |
| 0.3–0.4 | 15 | 0.362 | 0.267 | 0.477 |
| 0.4–0.5 | 34 | 0.457 | 0.353 | 0.480 |
| 0.5–0.6 | 40 | 0.558 | 0.450 | 0.547 |
| 0.6–0.7 | 27 | 0.659 | 0.630 | 0.637 |
| 0.7–0.8 | 27 | 0.748 | 0.815 | 0.643 |
| 0.8–0.9 | 10 | 0.848 | 0.900 | 0.608 |
| 0.9–1.0 | 23 | 0.957 | 0.957 | 0.607 |

- 模型 log loss **0.6553**、Brier **0.2322**；市场 log loss **0.5107**、Brier **0.1745**；常数 log loss **0.6919**。模型只比常数好一点，市场明显更好。
- 模型均价 0.559，实际 0.525；市场均价 0.575。模型的问题不是整体偏高，而是**没有把强弱拉开**：市场给 0.05 的队，模型给 0.47；市场给 0.96 的队，模型给 0.61。

### 3）预注册规则的净收益（主结果）

按“每场最多一侧、edge ≥5¢、1¢ 半价差、0.05 费”：

| 半价差 | 笔数 | 比赛数 | 每份净收益均值 | 每份合计 | 胜率 |
|---:|---:|---:|---:|---:|---:|
| 0¢ | 117 | 117 | **−0.0312** | −3.65 | 29.9% |
| 1¢ | 117 | 117 | **−0.0414** | −4.85 | 29.9% |
| 2¢ | 117 | 117 | −0.0516 | −6.03 | 29.9% |
| 5¢ | 117 | 117 | −0.0820 | −9.59 | 29.9% |

- 平均进场价 0.322；平均每份净收益 −4.14¢，相当于进场价的 **12.9%**。
- 分来源（1¢）：IPL 19 笔 **−0.100/份**；T20I 98 笔 **−0.030/份**。分年份：2024 年 12 笔 −0.081；2025 年 40 笔 −0.035；2026 年 65 笔 −0.038。**没有一个切片是正的**。
- 零费用敏感性：如果实际吃单费为 0（本轮抽查的 6 个模板确实 `feeSchedule=null`、`feesEnabled=false`），1¢ 半价差下仍为 **−0.0326/份**，0¢ 半价差下 **−0.0226/份**。费用不是失败的原因。
- 作为对照：无脑买热门（市场价 ≥0.5 的一侧，1¢ 半价差 + 0.05 费）198 场均值 **−0.0033/份**，接近零；无脑买冷门均值 **−0.0519/份**。模型的 117 笔平均进场价 0.322，正好落在“冷门”区间，所以它的亏损主要来自**给冷门队过高概率**，而不是费用或价差。

### 4）事后诊断（不是预注册，不能当 edge）

- **平衡盘 0.35–0.65**：39 笔，均值 **+0.0258/份**，胜率 51.3%；但 2025 年 23 笔 −0.047、IPL 18 笔 −0.085，只有 2026 年 15 笔 +0.167。分年/分联赛不稳定，只能作为下一轮前向假设。
- **只买热门（p_mkt ≥0.5）且模型 edge ≥5¢**：23 笔，均值 **+0.0717/份**，合计 +1.65。样本太小，且方向与 `known/V-V2-poly-longshot`（押热门、冷门偏差）一致；这不是本条的新机制，不能据此说 Cricsheet 模型有 edge。
- 这两个事后切片都在“市场已经比较准”的前提下，靠少量样本的偏差；主规则（全价格带）仍然是负的。按预注册失败标准，本条判 **FAIL**。

### 5）数据质量与已知问题

- **最后成交价 ≠ 可成交 ask**：data-api 给的是真实成交价，但可能是几分钟前、甚至隔夜的价格；本轮加 1¢ 半价差，5¢ 敏感性见上表。若真实 ask 比最后成交价高 5¢，主规则会降到 −0.082/份。这是价格侧最大的不确定性。
- **CLOB `prices-history` 不可用**：本轮对 `ipl-rcb-rr-2025-04-24` 和 `crint-gbr-nzl-2026-02-27` 各取一个 token，均返回 `{"history":[]}`；因此历史盘口/中间价无法重建，只能用 data-api 成交。GUIDE §8 也提示历史盘口没有公开来源。
- **匹配覆盖率**：522 个胜负市场只匹配到 231 个（210 场）。未匹配的主要是 BBL、LPL、ILT20、CSA T20、National T20 Cup 等国内联赛——本轮只下载了 Cricsheet 的 T20I 和 IPL 两个包，没有扩展国内联赛；所以 198 场不是“全库”，而是“T20I + IPL”的完整可得样本。这不改变负结果的方向，但外推到国内联赛要谨慎。
- **队名/日期映射**：PM 的 2025 IPL 用城市名/截断名（`Hyderabad`、`Rajasthan`、`Kong`、`Lanka`、`Emirates`），Cricsheet 用全名；本条做了标准化映射，并按日期 ±2 天匹配。203 场里 200 场与 Cricsheet 胜者直接一致，3 场是 Super Over（Cricsheet `result=tie`、`eliminator` 有值，PM 按 eliminator 结算），不是真正的数据冲突。
- **50-50 的 6 场**：3 场 IPL 2025（`ipl-kkr-pbks-2025-04-26`、`ipl-srh-dc-2025-05-05`、`ipl-pbks-dc-2025-05-08`）和 3 场 T20I 2025（`intt20-aus-ind-2025-10-29`、`t20-aus-ind-2025-11-08`、`t20-new-wes-2025-11-10`）。这些场次的 `outcomePrices` 都是 `["0.5","0.5"]`，已从胜负检验剔除；如果误把它们当二值结果，会污染 y。
- **同日顺序**：Cricsheet 只有日期、没有开赛时刻；同日多场按文件名排序，可能把同日晚些时候的结果用于早先比赛的评分。影响很小，但严格说不是逐场时钟。
- **Gamma volume/liquidity 是来源自报，未核实**；本条只用它们做容量参考，不用来算收益。

### 6）费用与结算源证据

- 抽查的 6 个模板（IPL 2025、T20 WC 2024、T20 WC 2026、T20I 2025-10、T20 WC 2026 资格赛、Asia Cup 2025）全部 `feeSchedule=null`、`feesEnabled=false`。GUIDE §8 给体育板块的费率是 0.03–0.05；本条按 **0.05** 保守计。即使实际为 0，主规则仍为负（见上）。
- 结算源：2026 T20 WC 与资格赛 = `https://www.espncricinfo.com/`；2025-10 T20I = `https://www.icc-cricket.com/fixtures-results`；2025 IPL = `https://www.iplt20.com/`；2024 T20 WC 与 2025 Asia Cup 的 `resolutionSource` 为空。**同一个 tag 下结算源并不统一**，这是规则风险，不是可以忽略的细节。

## 数据

- Cricsheet（免费、免密钥、公开 JSON）：
  - `https://www.cricsheet.org/downloads/t20s_male_json.zip` — HTTP 200，14,479,929 B，3,629 个 JSON；解析 3,627 场男子 T20I。
  - `https://www.cricsheet.org/downloads/ipl_json.zip` — HTTP 200，5,187,770 B，1,245 个 JSON；解析 1,243 场 IPL。
  - 只保留 `info`（日期、队伍、胜负、event、venue、gender、overs）和每场 deliveries 的 runs/legal balls；原始 zip 在 `/tmp`，不入仓库。
- Gamma（免费、免密钥）：
  - `https://gamma-api.polymarket.com/events?tag_slug=cricket&closed=true&limit=100&offset=0,100,...,2100` — 本轮取到 2,100 个 event；offset 2,100 返回 HTTP 422。
  - `https://gamma-api.polymarket.com/events?slug=<slug>` — 规则原文、`outcomePrices`、`feeSchedule`、`resolutionSource`、`gameStartTime`、volume。
- data-api（免费、免密钥）：
  - `https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=N` — 按 timestamp 新→旧返回；本轮 210 个市场、约 102 MB 原始成交，缓存于 `/tmp/opencode/trades/`，不提交。
  - 示例：`https://data-api.polymarket.com/trades?market=0xf93062f04968bed0e282872accac7a2a81e80837a11b5bdbddb8fabab8b2bede&limit=1000` — 返回 67 笔，时间 2024-06-08..2024-06-12。
  - 每条含 `price/size/side/outcome/timestamp`；本条只用 `timestamp < gameStartTime` 的最后一笔，按 outcome 取价。
- CLOB（免费、免密钥，但历史不可用）：
  - `https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60` — 本轮两个样本（2025-04、2026-02）均返回 `{"history":[]}`；所以没有历史 bid/ask。
- 缺失/未取到：历史 L2 盘口、逐场赛前 playing XI、toss/venue 特征、国内联赛（BBL/LPL/ILT20/CSA 等）的 Cricsheet 分项包；本轮没有把这些写进模型，也没有用“赛后信息”反推赛前概率。

## 两周内怎么检验

- **历史侧已完成**：198 场独立比赛（按比赛计，不按市场数；同一场的两个 outcome 只算一场），2024-06-11..2026-03-24，已超过 30 的门槛。失败标准写死为“每份净收益均值 ≤0”，本轮 198 场里触发 117 笔、**−0.0414/份 → FAIL**。
- **前向侧**：从 2026-10-20 起，对 `tag_slug=cricket&closed=false` 里所有 T20 胜负市场，在开赛前 1 小时和 5 分钟各记录一次：`gameStartTime`、两侧 `bestBid/bestAsk`、最后成交价、`outcomePrices`、`feeSchedule`、`resolutionSource`、比赛是否因雨/弃赛改期。两周内 T20I 系列通常能提供 10–30 场；如果不足 30 场，只能记为前向观察，不判成败。
- **前向的失败标准**：≥30 场后，预注册规则的每份净收益均值 ≤0 → 判失败；0–2¢ → 不确定；≥2¢ 且 IPL/T20I 两个子样本都为正 → 才进入下一轮。前向必须用真实 ask（不是最后成交价），这是本轮没有解决的关键测量问题。
- **应优先复核的两个事后切片**：(a) 只在市场价 0.35–0.65 交易；(b) 只买热门且模型 edge ≥5¢。两者都要用真实 ask 重测，且必须分年/分联赛报告；在没通过前，不得当成策略。

## 成本与容量

- **费用**：GUIDE §8 的体育费率 0.03–0.05；本条按 0.05 计。每份吃单费 `0.05 × p × (1−p)`：
  - 进场价 0.322 → 0.0109/份；加 1¢ 半价差 = **2.09¢/份**，占进场价 **6.5%**。
  - 进场价 0.50 → 0.0125/份；加 1¢ = **2.25¢/份**，占 4.5%。
  - 进场价 0.10 → 0.0045/份；加 1¢ = **1.45¢/份**，占 14.5%——便宜档的成本占比最高，这也是模型买冷门时最吃亏的地方。
- **挂单/返佣**：本条全部按吃单算，不假设挂单成交；`rebateRate=0.15`（若为 maker）不计入，避免把返佣当成收益。
- **容量**：198 场 / 约 21.4 个月 ≈ **9.3 场/月**；117 笔 / 21.4 个月 ≈ **5.5 笔/月**。按 100 份/笔、均价 0.322，约 **32 USDT/笔**、**177 USDT/月**；5,000 USDT 根本放不满，单场所 2,500 USDT 也远未触及。即使放大到 1,000 份/笔（约 322 USDT/笔），5 笔/月约 1,610 USDT，仍在 2,500 以下。
- **资金占用**：一场 T20 约 3–4 小时，加上结算/争议窗口，单笔资金占用 <1 天；但因为净收益为负，年化没有意义（不计算“负年化”来误导）。
- **机会频率**：tag 全库 T20 单场约 **24 个/月**（522/22，分页上限内），但本模型只覆盖 T20I+IPL 的约 **9 个/月**；国内联赛的 15 个/月没有覆盖。

## 风险

1. **模型风险（最大）**：Elo+form 只用了历史比分和得失分率，没有赛前 playing XI、toss、场地、天气、旅行、球员伤停；PM 市场显然把这些信息定进去了。模型把强弱压向 0.5，导致“买冷门”系统性亏损。这是本条失败的主因，不是参数没调好。
2. **价格测量风险**：data-api 的最后成交价不是 ask，可能是几分钟前甚至隔夜的价；本轮中位数 2.3 分钟、95 分位 2 小时、最大 43.5 小时。加 1¢ 半价差是保守假设，但没有历史 L2 可验证；真实 ask 高 5¢ 时主规则降到 −0.082/份。
3. **结算规则风险**：弃赛/取消/无结果 = 50-50（本轮 6 场）；Super Over 按 eliminator；DLS/forfeit/walkover 算 ordinary win；老模板没有明确 resolution source。买之前不读 description，可能把 50-50 当成输赢。
4. **数据映射风险**：522 个胜负市场只有 231 个匹配到 Cricsheet；国内联赛未覆盖；队名截断/城市名需要手工映射；日期 ±2 天匹配可能错配（本轮用 PM 结算价复核，200/203 直接一致，3 场是 Super Over）。如果扩到国内联赛，映射错误会更多。
5. **平台/流动性风险**：cricket 市场多为 `restricted=true`，薄盘口，`orderMinSize=5`，部分市场 volume 只有几百美元；`feeSchedule` 可能随平台政策变化（本轮抽查为 null/false，但 GUIDE 说体育 0.03–0.05）。UMA 结算/争议、negRisk 转换、赎回步骤都要算进操作风险。
6. **多重检验风险**：事后找到的平衡盘 +2.58¢、热门 +7.17¢ 都是小样本切片；分年/分联赛不稳定，且热门方向与 `known/V-V2-poly-longshot` 重叠。不能把事后切片包装成预注册 edge。

## 改进了什么

不适用（`kind: new`）。与最近的条目区别：`quant-006` 是网球 Elo vs PM，但 Tennis Abstract 只有当前榜、没有历史 as-of Elo，也没有收益回测；本条用 Cricsheet 逐球数据重建了赛前评分，并用 data-api 历史成交做了 198 场可成交检验。`quant-021` 是 F1 排位赛后十几小时的计时数据窗口；本条是板球赛前市场。`quant-011` 是足球三项盘的平局定价；本条是 T20 二项胜负。若主审认为“外部评级模型 vs PM 体育盘”属于同一机制，本条最多算 `supplement`/`improves: quant-006`，但结论是负面的，不建议按新策略收录。

## 门槛自查

1. **机制说得清：不满足** — 机制假设（休闲资金按名气定价、球球评级更准）可以一句话说清，但本轮 198 场检验没有找到付钱方；市场比模型更准，模型买冷门系统性亏损。没有证据表明这笔钱会持续存在。
2. **有免费数据能检验：满足** — Cricsheet 的 T20I+IPL 逐球 JSON、Gamma 规则/结算、data-api 历史成交全部免费免密钥；198 场独立比赛、405 条 outcome 价格，可复现。
3. **小资金能做：满足（形式）** — 100 份/场、约 32 USDT/笔、5.5 笔/月，远低于 2,500 USDT 单场所和 5,000 USDT 总资金；不加杠杆。但净收益为负，实际不可做。
4. **不重复：不确定** — 新市场（cricket T20）、新数据（Cricsheet 球球）、新检验（198 场 data-api 成交）；但“用外部评级模型给 PM 体育胜负定价”与 `quant-006`（网球 Elo）、`quant-021`（F1 计时）同族。若按机制归类为变体，应改为 `supplement`/`improves: quant-006`；本条按 `new` 提交，理由是本条给出了前两者没有的可成交历史回测和负面结论。
5. **扣成本后粗算够用：不满足** — 预注册规则 198 场、117 笔，1¢ 半价差 + 0.05 费下每份 **−0.0414**；零费用仍 **−0.0326**；5¢ 半价差 **−0.0820**。事后切片 +2.58¢/+7.17¢ 样本小且不稳定，不能算“够用”。
6. **两周内能检验：满足** — 历史侧已有 198 个独立结果（>30），失败标准写死并已触发；前向两周可再记录 10–30 场 T20I，但主结论不需要等前向。
7. **出处可查：满足（部分“未取到”）** — Cricsheet ZIP、Gamma event、data-api trades 都有 URL 和访问日期；规则原文逐字引用；脚本和 stdout 在 scratch。未取到的是历史 L2 盘口、逐场 playing XI、国内联赛 Cricsheet 包，以及 2024 T20 WC/2025 Asia Cup 的明确 resolution source（Gamma 字段为空）。

## 出处

- `GUIDE.md`（本仓库）— 访问 2026-10-20 — 已读（§8 Polymarket 费用、§2 七条门槛、§7 格式）。
- `bots/quant/notes/batch3-shortlist.md`（本仓库）— 访问 2026-10-20 — 已读（cricket tag、series `ipl` id=44、Cricsheet 下载地址的预研记录）。
- `known/KNOWN.md`（本仓库）— 访问 2026-10-20 — 已读（`V-V2-poly-longshot` 押热门/冷门偏差）。
- `bots/quant/entries/quant-006-tennis-elo-pm-pricing.md`、`quant-021-f1-pole-winner-base-rate.md` — 访问 2026-10-20 — 已读（用于区别说明）。
- https://www.cricsheet.org/downloads/t20s_male_json.zip — 访问 2026-10-20 — 已读（HTTP 200，14,479,929 B，3,629 个 JSON）。
- https://www.cricsheet.org/downloads/ipl_json.zip — 访问 2026-10-20 — 已读（HTTP 200，5,187,770 B，1,245 个 JSON）。
- https://gamma-api.polymarket.com/events?tag_slug=cricket&closed=true&limit=100&offset=0,100,...,2100 — 访问 2026-10-20 — 已读（2,100 个 event；offset 2,100 返回 HTTP 422）。
- https://gamma-api.polymarket.com/events?slug=ipl-rcb-rr-2025-04-24 — 访问 2026-10-20 — 已读（IPL 规则原文、`resolutionSource=https://www.iplt20.com/`、`feeSchedule=null`、`feesEnabled=false`、`outcomePrices=["1","0"]`）。
- https://gamma-api.polymarket.com/events?slug=usa-vs-india-cricket-t20-world-cup — 访问 2026-10-20 — 已读（2024 T20 WC 规则原文、`resolutionSource` 为空、`outcomePrices=["0","1"]`）。
- https://gamma-api.polymarket.com/events?slug=crint-gbr-nzl-2026-02-27 — 访问 2026-10-20 — 已读（2026 T20 WC 规则原文、`resolutionSource=https://www.espncricinfo.com/`、volume 1,720,269.71 来源自报）。
- https://gamma-api.polymarket.com/events?slug=intt20-aus-ind-2025-10-29 — 访问 2026-10-20 — 已读（T20I 规则原文、`resolutionSource=https://www.icc-cricket.com/fixtures-results`、`outcomePrices=["0.5","0.5"]`）。
- https://gamma-api.polymarket.com/events?slug=crint-mex-arg-2026-03-14 — 访问 2026-10-20 — 已读（2026 资格赛三市场结构、`resolutionSource=https://www.espncricinfo.com/`）。
- https://gamma-api.polymarket.com/events?slug=asia-cup-india-vs-pakistan-2025-09-14 — 访问 2026-10-20 — 已读（Asia Cup 规则原文、`resolutionSource` 为空、`outcomePrices=["1","0"]`）。
- https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=N — 访问 2026-10-20 — 已读（210 个市场、约 102 MB 原始成交；字段 `price/size/side/outcome/timestamp`）。
- https://data-api.polymarket.com/trades?market=0xf93062f04968bed0e282872accac7a2a81e80837a11b5bdbddb8fabab8b2bede&limit=1000 — 访问 2026-10-20 — 已读（USA vs India，67 笔，2024-06-08..2024-06-12）。
- https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（`ipl-rcb-rr-2025-04-24` 与 `crint-gbr-nzl-2026-02-27` 均返回 `{"history":[]}`）。
- `bots/quant/notes/scheduler/scratch/B24/` — 访问 2026-10-20 — 已读（脚本与 stdout：`model.log`、`numbers.log`、`final_test.log`、`rules.json`）。
