# 回放汇总：quant-016

**结论：负。** 这是对条目 `quant-016`（Rotten Tomatoes Tomatometer 阈值链，Beta-Binomial 模型）的真实成交价回放。66 个独立已结算 event、192 个有价档，模型 Brier **0.060450** vs 市场 **0.035369**，扣吃单费与 1¢ 半价差后每美元投入 **−0.325353**；模型侧失败标准两条都触发。市场侧预注册的 A/B/C 三条模型无关规则同样全负（T-48h / T-24h / T-6h 共 9 组）。**没有找到可用的净 edge；建议按 GUIDE 第 2 节第 5、6 条降为待选区，不按收录推进。**

本目录同时是第 2 轮 `evidence: 回放` 的交付物；条目字段 `variants: 23`、`window: 2026-03-02..2026-10-19`、`max_dd: 100%`、`contribution: -100%` 与本文一致。

## 如何复现

- 脚本：
  - `replay_model.py` — 条目本身的 Beta-Binomial 模型（主回放）。依赖：Python 3 + `requests`（本机 3.12 / requests 2.32）。
  - `replay_market.py` — 市场侧模型无关规则（否证条目前提）。
  - `snapshots.csv` — 74 个有历史 `(k,m)` 快照的 event（v1 记录 73，v2 修正一个 slug 后 +1）（来自已合并 `bots/quant/notes/q016-hist/events.csv`，提交 `e950778`；只保留回放需要的列）。
  - `universe.csv` — 84 个已关闭 event / 525 个 `N+` 档的 Gamma 快照（2026-10-21）。
- 运行：
  ```bash
  cd bots/quant/replay/quant-016
  python3 replay_model.py                # 主回放，读 _cache/ 或联网重取
  python3 replay_model.py --fetch-clob    # 加 M5（CLOB 价格敏感性）
  python3 replay_market.py --fetch        # 市场侧，首次会下载 525 个档的成交/CLOB
  ```
  脚本只写 stdout、`trades_model.csv`、`events_model.csv`；原始 HTTP 落在 `_cache/`（已 gitignore，单文件 < 1 MB）。
- 参数（全部写死，没有拟合）：
  - 模型：`p ~ Beta(k+1, m+1)`；`P_T = 1 − I_{(T−0.5)/100}(k+1,m+1)`（round half up）；同 event 内按阈值升序做保序回归。
  - 触发：`P_T − mid > fee(ask) + 0.01 + 0.02` 买 YES；`mid − P_T > fee(no_ask) + 0.01 + 0.02` 买 NO；两条件都满足取 edge 大者。
  - 成交：`mid` = 快照前 6h 内最后一笔 data-api 成交（YES 等价价，NO 取 `1−价`），买价再加 1¢ 半价差。每档 1 份，持到结算，不提前平仓。
  - 费用：`fee = 0.05 × q × (1−q)`（q 为买入价，闭合样本 Gamma `feeSchedule` 实测 0.05）；maker-fee-0 变体只去掉费用，仍收 1¢ 半价差。
  - 快照窗口：主窗口 `[T−72h, T−12h]` 内最晚可用快照；敏感性窗口 `[T−7d, T−24h]`。
  - 独立结果：按 event 计（同片各档共享一次结算）；主口径把无触发 event 记为 0（`q016-hist` v2 的 PRIMARY 口径）。
- 数据下载地址（均免费、免密钥，访问 2026-10-21）：
  - Gamma 已关闭 event：`https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false`
  - data-api 逐笔成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`
  - CLOB 价格历史（**不是成交价**，只作敏感性）：`https://clob.polymarket.com/prices-history?market=<tokenId>&startTs=<unix>&endTs=<unix>&fidelity=60`
  - Wayback CDX 快照列表：`https://web.archive.org/cdx/search/cdx?url=rottentomatoes.com/m/<slug>&output=json&from=<ts>&to=<ts>&filter=statuscode:200`
  - Wayback 快照正文：`https://web.archive.org/web/<timestamp>id_/https://www.rottentomatoes.com/m/<slug>`
  - RT 影片页：`https://www.rottentomatoes.com/m/<slug>`（`criticsScore` 的 `likedCount / notLikedCount / reviewCount / score`）
- 数据本身起点：2026-03-02（最早 event `endDate`；快照最早 2026-03-01）。
- 开发窗口：**2026-03-02..2026-10-19**（Polymarket 无 2022–2024 限制；主项目据此知道这段已不是盲的）。
- 切分依据：不切分调参——Beta(k+1,m+1) 先验、round 判据和 A/B/C 阈值都在看回放盈亏前写死，没有拟合参数；市场侧另按 2026-08-01 做过前后两段稳定性检查（两段都负，见 M/P 表注）。**严格说不是盲测**：条目作者在 2026-10-20 已用同一批 85 个已关闭 event 描述过基率和档位频率，所以这 66 个 event 对“基率长什么样”不是完全未知；但对模型参数和交易规则是样本外。这个保留必须写清，不能把回放说成独立盲测。

## 成交和成本

- 成交价和时点：data-api 的**逐笔真实成交**，取决策时点（快照或 T−h）之前的最后一笔，最多 24h 前（模型只取 6h 前）。成交是市场上真的有人付出的价格，不是 CLOB 的 last/mid。CLOB 版本仅作敏感性（M5、P13–P15）。
- 无前视：模型只用快照时刻的 `(k,m)` 和该时刻之前的成交；市场规则只用 T−h 之前的成交；结算结果只用于计 P&L。
- 全部成本：吃单费 `0.05×q×(1−q)` + 1¢ 半价差。**未计**：真实 ask 可能高于“成交价+1¢”（2026-10-20 快照里 80+ 档半价差 11¢）、滑点、资金占用费。**重要**：条目原提案是 maker 挂单，但历史 L2/队列数据不存在，回放无法重建“对手是否吃到我的价位、排队第几”，所以主回放是**保守的 taker-at-touch 版**；M4 只是把吃单费置 0 的上界，不是 maker 成交模拟。maker 原规则没有被直接回放，其排队与逆向选择成本未量化。
- 资金和容量：单 event 上限 300 USDT、最多 4 个 event 并行 → 1,200 USDT；总资金 5,000 USDT，单场所 < 2,500。5,000 USDT 放不满，容量受 event 成交额限制（中位 $11,727.77）。回放按每档 1 份计，不按 300 USDT 放大；年化贡献的放大假设见下。

## 汇总结果

- 独立结果数及计法：**66 个独立 priced event**（192 个有价档；同片所有档算 1 个）。主窗口另有 74 个 event 有快照、其中 66 个有可成交价；市场侧 T-24h 有 **82 个 event / 341 个档**有成交价。
- 扣成本后净收益（主回放 M2，round / 主窗口 / 真实成交 / 吃单费）：
  - 触发 **87 笔**、49 个 event，命中（net>0）**8/87**；
  - 合计 **−3.666836**，投入 **11.270339** → **每美元 −0.325353**；
  - event 级（PRIMARY，无触发记 0）中位 **−0.046602/份**、均值 **−0.055558/份**；
  - 仅触发 event（SECONDARY）中位 **−0.112858/份**、均值 **−0.074833/份**。
  - 生成命令：`python3 replay_model.py`；逐笔明细 `trades_model.csv`，逐 event `events_model.csv`。
- 最大回撤：**100%**（模拟：每 event 投 300 USDT、账户 5,000 USDT、按 event 时间顺序、含已实现亏损；第 27/66 个 event 后权益跌破 0，即本金耗尽）。只按 1 份/档的原始曲线不折算百分比。
- 对 5,000 USDT 的年化贡献：原始线性公式 `每美元 −0.325353 × 300 USDT × 104.3 event/年 ÷ 5,000 = −203.6%`；现金账户最多亏光本金，故**报告 −100%**（等价于一年内本金耗尽）。
- result：**负**。
- 不可靠或失败原因：
  1. 快照不是结算前最后一刻：主快照滞后 `T−t` 中位 **30.70h**（12.86–69.02h），结算前新进的评论会让模型系统性过期。
  2. 只有成交价，没有历史 L2：1¢ 半价差对 80+ 档是乐观值（当期快照实测 11¢）；真实 ask 更差。
  3. 快照分与最终结算区间只有 **51/74** 精确一致，早期评论的选择性偏差没有被 Beta 抽样噪声覆盖。
  4. M5/P13–P15 的 CLOB 价格是 last/mid，不是可成交价，只能作为方向一致的敏感性。
  5. 66 个 priced event 中只有 49 个触发，同片各档高度相关；负结果稳健，但 event 数不算大。

## 所有变体（所有市场都要写，看了不用的也算）

- variants（自己的）：**23**
- variants_ext（外部来源）：**-**（没有外部来源的策略变体；外部数据源只提供成交价/快照）

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| M1 | 自己 | Beta(k+1,m+1)，**floor** 取整 `p≥T/100`；主快照 `[T−72h,T−12h]`；data-api 成交 +1¢；吃单费 0.05 | 2026-03-02..2026-10-19 | 66 event/192 档；Brier 0.066637 vs 0.035369；92 笔/52 event；每美元 −0.325192。`replay_model.out` |
| M2 | 自己 | Beta，**round half up** `p≥(T−0.5)/100`；主快照；data-api 成交 +1¢；吃单费 0.05（**主回放**） | 同上 | 66 event/192 档；Brier 0.060450 vs 0.035369，logloss 0.203451 vs 0.121872；87 笔/49 event；PRIMARY event 中位 −0.046602/份；每美元 −0.325353。`replay_model.out`、`trades_model.csv` |
| M3 | 自己 | round；**敏感性快照** `[T−7d,T−24h]`；data-api 成交 +1¢；吃单费 0.05 | 同上 | 73 event/218 档；Brier 0.064620 vs 0.045723；102 笔/55 event；每美元 −0.155980。`replay_model.out` |
| M4 | 自己 | round；主快照；data-api 成交；**maker 费 0**（仍收 1¢ 价差） | 同上 | 66 event/192 档；92 笔/51 event；每美元 −0.339870。`replay_model.out` |
| M5 | 自己 | round；主快照；**CLOB prices-history**（last/mid，非成交价）+1¢；吃单费 0.05 | 同上 | 74 event/442 档；Brier 0.038814 vs 0.024737；181 笔/64 event；每美元 −0.134400。`replay_model_clob.out`（敏感性，不作为成交价证据） |
| M6 | 自己（复用 `notes/q016-hist/`） | **floor**；敏感性快照 `[T−7d,T−24h]`；data-api 成交 +1¢；吃单费 0.05 | 同上 | 73 event/218 档；Brier 0.070161 vs 0.045723；103 笔/57 event；每美元 −0.232801。`bots/quant/notes/q016-hist/run_output.txt`（已合并提交 `e950778`，未重跑） |
| P1 | 自己 | 市场规则 A：买 NO，YES 价 ≥0.90；T−48h；成交 +1¢；吃单费 0.05 | 同上 | 131 档/57 event；每份 −0.033131；0/57 正。`replay_market.out` |
| P2 | 自己 | A；T−24h | 同上 | 125 档/59 event；每份 −0.024966；0/59 正。`replay_market.out` |
| P3 | 自己 | A；T−6h | 同上 | 180 档/63 event；每份 −0.017897；0/63 正。`replay_market.out` |
| P4 | 自己 | 市场规则 B：买 YES，YES 价 ≤0.10；T−48h | 同上 | 172 档/62 event；每份 −0.005608；3/59 正。`replay_market.out` |
| P5 | 自己 | B；T−24h | 同上 | 170 档/64 event；每份 −0.018371；1/63 正。`replay_market.out` |
| P6 | 自己 | B；T−6h | 同上 | 220 档/71 event；每份 −0.008070；2/69 正。`replay_market.out` |
| P7 | 自己 | 市场规则 C：买 NO，0.25≤YES 价≤0.75；T−48h | 同上 | 40 档/36 event；每份 −0.059512；19/17 正。`replay_market.out` |
| P8 | 自己 | C；T−24h | 同上 | 24 档/22 event；每份 −0.100814；9/13 正。`replay_market.out` |
| P9 | 自己 | C；T−6h | 同上 | 10 档/10 event；每份 −0.094716；4/6 正。`replay_market.out` |
| P10 | 自己 | A；T−24h；**maker 费 0**（仍收 1¢） | 同上 | 125 档/59 event；每份 −0.024283。`replay_market.out` |
| P11 | 自己 | B；T−24h；maker 费 0 | 同上 | 170 档/64 event；每份 −0.017724。`replay_market.out` |
| P12 | 自己 | C；T−24h；maker 费 0 | 同上 | 24 档/22 event；每份 −0.089090。`replay_market.out` |
| P13 | 自己 | A；T−24h；**CLOB last/mid** +1¢；吃单费 0.05 | 同上 | 186 档/64 event；每份 −0.023901。`replay_market.out`（敏感性） |
| P14 | 自己 | B；T−24h；CLOB +1¢ | 同上 | 234 档/68 event；每份 −0.024166。`replay_market.out` |
| P15 | 自己 | C；T−24h；CLOB +1¢ | 同上 | 43 档/39 event；每份 −0.031979。`replay_market.out` |
| P16 | 自己 | **探索性、未预注册**：买 YES，0.25≤YES 价≤0.90；T−24h；成交 +1¢；吃单费 | 同上 | 36 档/31 event；每份 +0.0881、event 均值 +0.1130、22/9 正、符号检验 p=0.0294。**只作线索，不作本条证据**。`replay_market.out` |
| P17 | 自己 | 探索性：按 T−24h 市场隐含边界买 YES(`lo`) + 买 NO(`hi`)，各 1 份；成交 +1¢；吃单费 | 同上 | 51 event；YES 腿每份 +0.0308、NO 腿 −0.0272，两腿相加约 +0.0036/event，扣完成本约为 0。`replay_market.out` |

其他看过但不单列为变体的诊断（同规则的不同子样本，按 GUIDE 第 7 节算同一个变体）：
- 时间稳定性：A/B/C 在 2026-08-01 前后两段都负（例如 B 前半 −0.013594 / 后半 −0.024140）。
- T−24h 价格校准：分桶 Brier、整体 0.024829 vs 常数 0.247659（市场已经很准）。
- 隐含边界准确率：T−24h 与最终边界完全相同 55/65（84.6%），|误差|≤2 分 59/65。

## 复核

- 2026-10-22 重跑 `replay_model.py` 与 `replay_market.py`，得到的分桶、Brier、A/B/C 数字与已合并的 `H-quant-016/backtest.out`、`model_hist_round.out` 逐位一致（`replay_model.out`、`replay_market.out`）。
- 条目所有出处已用 `verify_entry_citations.py` 重抓：Gamma/CLOB/data-api/RT/rounding 共 18 PASS；RT 实时页面按日期漂移（`clayface` 2026-10-22 已变为 67/22/89、score 75），条目只把带日期的快照当证据；Wayback availability / archive.ph / Common Crawl 仍 TLS 失败，但 Wayback CDX 与归档快照本次可读（spot check 通过）。stdout：`bots/quant/notes/scheduler/scratch/H-quant-016/verify_entry_citations_replay.out`。
- 取整：2026-10-22 重跑 23 个有显示分数的 RT 页面，**23/23 与 round 一致、11 个能区分 floor/round 的样本全部是 round**；stdout：`.../check_rounding_replay.out`。
