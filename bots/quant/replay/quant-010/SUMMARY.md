# 回放汇总：quant-010

条目：`bots/quant/entries/quant-010-streaming-chart-nowcast.md`（周榜日更抢跑）
回放日期：2026-10-21（UTC）。只读、免费、免密钥、未交易、未登录。

**结论先说：可成交价回放为负。** 原信号（周榜发布前用日榜累计 nowcast 冠军）**没有**被这次回放评估：Netflix 没有免密钥的历史日榜（FlixPatrol 2026-10-21 仍 403），Spotify 日榜没有历史归档。回放的是目前唯一能免费回溯的代理信号——**上一期同榜 #1 继续夺冠**——在真实 data-api 逐笔成交价上、扣吃单费与半个价差、持有到结算。show 口径 54 个独立 chart-week 簇，每份净收益中位 **−0.0110 USDC**，合计 **−0.2611 USDC / 37.2453 USDC 投入**。

## 如何复现

- 脚本：
  - `replay_q010.py` — 枚举 Gamma 已结算事件、抓 Tudum 周榜、从 data-api 取发布前 24h 内最后一条成交、模拟、统计并写逐事件 CSV。头部是冻结的预声明。
  - `oos_split.py` — 按固定 70/30 做时间留出切分（先看规则后看结果，未调参）。
  - `verify_sources.py` — 逐个复核条目引用的 URL 与规则原文（2026-10-21）。
- 依赖：`python3` + `requests`（本机 Python 3.13、requests 2.34.2）。不需要 pandas/numpy。
- 运行：
  ```bash
  cd bots/quant/replay/quant-010
  Q010_CACHE=/tmp/q010_cache python3 replay_q010.py > run_show.log
  Q010_CACHE=/tmp/q010_cache python3 replay_q010.py --kind movie > run_movies.log
  python3 oos_split.py events_show.csv events_movies.csv > oos_split.out
  python3 verify_sources.py > verify_sources.out
  ```
  首次运行会下载约 180 MB 原始数据到 `_cache/`（已 gitignore，不入库）；有缓存时不发网络请求，数字逐字节可复现。
- 参数（全部，不是只报最佳）：
  - 决策窗：`PRIMARY_WINDOW_H=24`（发布前 24h 内最后一条成交）；敏感性 `SENS_WINDOW_H=12`。
  - 半个价差：`HALF_SPREAD=0.01`（YES 成交价 + 1¢ 当 ask）。
  - 费用：市场 `feeSchedule.rate`；历史市场 `feeSchedule=null` 且 `feesEnabled=false` 记 0；否则文化类 `FEE_CULTURE=0.05`。另做“全部 0.05”敏感性。
  - 模型：上周排名 r=1..10 权重 `11−r`，未进上周 Top10 权重 0.1，归一化；仅用于价格筛选与 Brier/logloss，不调参。
  - Bootstrap：`BOOT=10000`，`SEED=42`，按周重采样。
  - 时间留出：唯一 chart-week 按时间排序，前 `ceil(0.70·n)` 周为 dev，其余为 OOS；show `n=54`（dev 38 / OOS 16），movie `n=52`（dev 37 / OOS 15）。
- 数据下载地址（公开、免密钥，访问 2026-10-21）：
  - Gamma 已结算事件：`https://gamma-api.polymarket.com/events?series_id=<id>&closed=true&limit=200`
    - show：`10440`（全球 #1 show）、`10772`（美国 #1 show）
    - movie 扩展：`10441`（全球 #1 movie）、`10775`（美国 #1 movie）
  - 逐笔成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`（`side/price/size/timestamp/outcome`；`No` 价换算 YES=1−p；每市场最多约 2 万笔）
  - 官方周榜：`https://www.netflix.com/tudum/top10/data/all-weeks-global.tsv`、`https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv`
  - 规则原文：各事件 `description` / `resolutionSource`（见 `verify_sources.out`）
- 数据本身起点：Tudum 周榜自 `2021-07-04`；带成交价的事件自 `2025-03-16`（show）/ `2025-10-12`（movie）。
- 开发窗口：`2025-03-16..2026-10-18`（show）；`2025-10-12..2026-10-18`（movie）。Polymarket 无 2022–2024 窗口限制；本次未查看 2026-10-18 之后的任何数据。
- 切分依据：见上“时间留出”。信号规则无拟合参数，切分用于检验方向稳定性，不是样本内调参。

## 成交和成本

- 成交价和时点：Polymarket **data-api 逐笔成交**，不是 CLOB `prices-history`。对每个候选市场取 `T_pub−24h .. T_pub` 内**最后一条**成交；`T_pub` 从事件 `description` 解析（Netflix 周二 15:00 ET，解析失败时用 `endDate` 当日 15:00 ET，仅 1 个事件）。`ask = YES 成交价 + 0.01` 作为半个价差。无前视：只用发布前的成交。
- 挂单/排队：本次只测**吃单**路径；未假设 maker 成交，未用盘口深度。data-api 成交价是实际成交，但没有 L2 队列信息。
- 全部成本：吃单费按 GUIDE §8 `份数 × rate × ask × (1−ask)`；另加 1¢ 半个价差。没有资金费、借币费或滑点模型；“全部 0.05 费”敏感性仍为负。历史市场 `feesEnabled=false` 主口径按 0 费，对结果**有利**于策略，仍为负。
- 资金和容量：逐事件 1 份，P&L 是每份口径。条目允许单事件 ≤500 USDC、同时 ≤2 个事件；本次**未测**深度、冲击成本与组合占用，所以容量结论仍是“未验证”。

## 汇总结果

- 独立结果数及计法：一个 chart-week = 一簇；同一周全球榜 + 美国榜合并为 1 簇（条目自己的独立性规则），簇内每份净收益取平均。show 主口径 **54 簇**（84 个可成交 market-event），movie 扩展 **52 簇**（85 个），均 ≥30。
- 扣成本后净收益（`run_show.log`、`run_movies.log` 原样）：
  - show 主口径：每份净收益中位 **−0.0110**、均值 **−0.0031**；簇中位 **−0.0110**、簇均值 **−0.0017**；合计 **−0.2611 USDC / +37.2453 staked**；簇 bootstrap 95% CI 均值 **[−0.0081, +0.0098]**。
  - movie 扩展：每份中位 **−0.0110**、均值 **−0.0086**；簇中位 **−0.0110**、簇均值 **−0.0088**；合计 **−0.7268 / +32.7101**；CI **[−0.0117, −0.0063]**。
  - 时间留出：show OOS 16 簇中位 **−0.0094**、均值 **−0.0072**；movie OOS 15 簇中位 **−0.0115**、均值 **−0.0064**。dev 的 show 均值 +0.0006（中位仍 −0.0110），OOS 转负——没有稳定正收益。
- 最大回撤：**未计算**。回放是每份、逐事件口径，没有逐日持仓市值序列；条目 `max_dd` 写 `-`（Polymarket 可选）。
- 对 5,000 USDT 的年化贡献：**不清楚**。净收益为负，且每份口径无法直接映射到账户收益：按每份均值 −0.0031、100 份/事件、约 51.7 个事件/年粗算约 −16 USDC/年（−0.32%），按每份中位 −0.0110 则约 −1.1%/年；若按条目上限 500 USDC/事件放大，亏损会超过本金、外推无意义。因此不写一个看似精确的年化数字。
- `result`：**负**（上述可成交价代理口径，扣全部成本；≥30 独立簇）。**原信号未测**，不能据此判定日榜 nowcast 无效。
- 不可靠或失败原因：代理不是原信号（连庄率约 40%，远弱于日榜 nowcast）；决策价偏晚（窗口内最后一条成交常在发布前几分钟，市场 Brier 0.0026 已接近结算）；无 L2 深度/排队；历史费用依赖 `feesEnabled` 字段；标题匹配有 6 个 `OTHER_NOT_LISTED` 与 1 个 movie 标题写法差异。

## 所有变体（所有市场都要写，看了不用的也算）

- variants（自己的）：**6**
- variants_ext（外部来源）：**-**（未引用外部变体）

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| 1 | 自己 | show 主口径：24h 窗最后成交 + 1¢ 半价差，吃单费（历史 0），持有到结算；单份 | 2025-03-16..2026-10-18 | 54 簇；簇中位 −0.0110，合计 −0.2611；`run_show.log` |
| 2 | 自己 | 同 1，决策窗改 12h | 同上 | 47 簇；簇中位 −0.0073，均值 −0.0021；`run_show.log` §SENSITIVITY 1 |
| 3 | 自己 | 同 1，所有市场一律按文化类 0.05 费（忽略 `feesEnabled=false`） | 同上 | 簇中位 −0.0115，均值 −0.0034；`run_show.log` §SENSITIVITY 2 |
| 4 | 自己 | 同 1，仅当 `p_model − ask − fee − 0.01 > 0` 才买 | 同上 | 47 笔 / 36 簇，命中 0，簇中位 −0.0115；`run_show.log` |
| 5 | 自己 | movie 扩展：同一管线跑 #1 movie 两个系列 | 2025-10-12..2026-10-18 | 52 簇；簇中位 −0.0110，合计 −0.7268；`run_movies.log` |
| 6 | 自己 | 同 1，固定 70/30 时间留出（无调参） | dev 2025-03-16..2026-06-28 / OOS 2026-07-05..2026-10-18 | OOS 16 簇中位 −0.0094、均值 −0.0072；`oos_split.out` |
| 7 | 自己（诊断，不计入 variants） | Oracle：事后买最终赢家，检验“100% 会赢仍亏”上界（有前视，不是策略） | 同 1 | show 77 笔中 81.82% 净 ≤0（均值 +0.0097）；movie 87.18%；`run_show.log`、`run_movies.log` |

外部来源变体：无。未引用任何外部回测结果。

## 复用的早前合并记录

- `bots/quant/notes/q010-hist/REPORT.md`（2026-10-20，53 show / 52 movie 簇）与本目录是同一冻结设计；本次因新增 2026-10-12..10-18 一周，show 变为 54 簇（新增周未改变方向），movie 仍 52 簇。**以本目录 2026-10-21 重跑的数字为准**。原文的关键结论（原信号 UNVERIFIED、代理 FAIL、oracle 多数净 ≤0）与本次一致。
- `bots/quant/notes/q010-hist/source_check.txt` 记录 FlixPatrol 403；本次 `source_check_2026-10-21.txt` 复现 403。

## 源复核要点（`verify_sources.out`）

- Netflix 全球/美国事件仍在，规则原文含 “Tuesday, October 20, 2026, 3:00 PM ET”、“previous week (Monday to Sunday)”、“English only”、“October 23, 2026, 11:59 PM ET”，`resolutionSource` 为 Tudum；2026-10-21 事件已结算，`outcomePrices` 变 1/0、`liquidity=null`、`feeSchedule.rate` 从 0.05 变 0（结算后快照），条目里的 10-20 盘口/费率是时点值。
- Spotify 事件仍在，规则原文含 “Fridays” 与 “beginning on the preceding Friday and ending on Thursday”；`Housewife` / `Nicole Kidman` 现在带艺人后缀（`Housewife - Tate McRae` 等），价格已结算。
- `open.spotify.com/charts`（条目引用的规则结算源）2026-10-21 返回 **404**；`charts.spotify.com` 前端页 200 但未解析出数字。FlixPatrol 仍 403。kworb 当前日已从 10/18 前进到 10/19，且没有历史日档。
