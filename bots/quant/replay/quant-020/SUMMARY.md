# 回放汇总：quant-020

按 `templates/REPLAY-SUMMARY.md` 写。条目：`bots/quant/entries/quant-020-earnings-beat-base-rate.md`。
回放日期 2026-10-21；只读公开接口，未交易、未用密钥。

## 如何复现
- 脚本：`run_replay.py`（Python 3，`requests`、`numpy`；无其他依赖）。运行：
  `cd bots/quant/replay/quant-020 && python3 run_replay.py`
  输出 `run_output.txt`、`trades.csv`（逐事件）、`results.json`（汇总）。
- 参数（全部，不只报最好的）：带 `0.40 ≤ p24 ≤ 0.55`；吃单买 YES；费率 `0.05`（另跑 `0.04`、`0.00`）；60/40 时间切分沿用冻结快照；严格样本外切点 = 最新 250 个 endDate 的第 250 个（`2026-07-30T13:00:00Z`）；周聚类 bootstrap 10,000 次，seed `20261020`；每事件 20 USDT、账户 5,000 USDT。
- 数据下载地址（免费、免密钥）：
  - Gamma 事件/结算：`https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=0&closed=true&order=endDate&ascending=false`（其余页按 offset 递增；2026-10-20 冻结快照 1,384 个 deduped 事件）。
  - data-api 逐笔成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=<0..10000>`。
  - 访问日期：2026-10-20（冻结快照）与 2026-10-21（本轮重抓）。
- 数据本身起点：2025-06-05（`events_frozen.csv` 最早的 endDate）；条目别处用的 Gamma 全量从 2024-01-19 起。
- 开发窗口：回放评估窗口 `2025-06-05..2026-10-20`；条目总体窗口 `2024-01-19..2026-10-20`。
- 切分依据：条文冻结的 60/40 按 endDate 时间切分（DISCOVERY 最早 60%，HOLDOUT 最新 40%），不做随机抽样；另加“剔除选带窗口”的严格样本外。Polymarket 无加密式窗口限制。
- 冻结输入：`events_frozen.csv` 是从 2026-10-20 的 `bots/quant/notes/q020-oos/events.csv` 抽出的派生表（slug、endDate、split、conditionId、y、p24、in_band、in_band_old），不是原始下载；上游全量枚举/定价脚本是 `bots/quant/notes/q020-oos/q020_oos.py`（2026-10-20 运行，stdout 见同目录 `run_output.txt`）。本回放不重新拟合 universe，只对冻结的 101 个带内事件重取 ask 侧成交；原始 JSON 只进 `_cache/`（已 gitignore，不入库）。

## 成交和成本
- 成交价和时点：对每个带内事件，在 `[endDate−72h, endDate−24h]` 的 data-api 逐笔成交中取**最后一笔 ask 侧打印**：`BUY Yes @ p` 记 `p`，`SELL No @ p` 记 `1−p`。这是实际发生过的吃单方向成交价，不是 CLOB `prices-history` 的最后价/中间价，也不是“最后价 +1¢”。没有 ask 侧打印的事件按未定价剔除（4/101）。
- 重抓校验：101/101 个事件的“最后一笔 YES 等价成交”与冻结 `p24` 完全一致；data-api 截断 0 个。
- 全部成本：吃单费 `0.05 × ask × (1−ask)` / 份；成交价已是 ask 侧打印，价差含在成交价里，未另加半价差。无资金费、无借贷、无其他腿。费率敏感性 0.04 / 0.00 同表列出。
- 资金和容量：每事件 20 USDT（观察到的 ask 打印中位成交额仅 4.8 USDT，97 个里仅 1 个 ≥200 USDT，200 USDT/event 没有证据）；同时最多 15 个事件 ≈ 300 USDT，远低于单场所 2,500。账户 5,000 USDT。

## 汇总结果
- 独立结果数及计法：一 Gamma 事件 = 一公司-季度 = 一结果。带内且可定价 **97** 个；其中严格样本外（不在选带用的最新 250 个事件里）**68** 个，选带窗口内 29 个。均 ≥30。
- 扣成本后净收益（费率 0.05）：
  - POOLED n=97：均值 **−0.0140/份**，按每份 1 股等权的每美元投入 **−2.71%**，95% CI **[−0.1292, +0.0817]**。
  - DISCOVERY n=54：均值 −0.0881/份（−16.92%/美元）；HOLDOUT n=43：均值 +0.0790/份（+15.38%/美元），但 **29/43** 落在选带窗口内。
  - STRICT_OOS n=68：均值 **−0.0634/份（−12.14%/美元）**、中位 **−0.4120**，95% CI **[−0.1638, +0.0366]**；费率 0.04 → −0.0610，0.00 → −0.0515，仍为负。
  - 换回原 CLOB 带内口径：STRICT_OOS n=42，均值 −0.0503/份；换回“最后 YES +1¢”：STRICT_OOS n=68，均值 −0.0237/份。方向不变。
- 固定 20 USDT/事件（等额，非每份 1 股）：97 笔、跨度 502 天，总净 PnL **−8.52 USDT**；等价于每美元投入约 **−0.44%**（低价事件份数更多，故与上面的每份等权 −2.71% 不同权）。
- 最大回撤：已实现累计 PnL 曲线（20 USDT/笔，含已结算浮亏）最大回撤 **266.58 USDT = 5.3%**（非盯市，按事件序列）。
- 对 5,000 USDT 的年化贡献：`−8.52 ÷ 5,000 × 365 ÷ 502 = **−0.12%/年**`。
- result：**负**（扣全部成本后合并与严格样本外均值均为负，n≥30）。
- 不可靠或失败原因：正收益全部集中在“选带所用最新 250 个事件”窗口内；窗口外为负，说明 0.40–0.55 带是事后选出来的，HOLDOUT 不是干净样本外。合并均值不显著（CI 跨 0），且 ask 打印容量中位仅 4.8 USDT。即使费率归零也不转正。

## 所有变体（所有市场都要写，看了不用的也算）
- variants（自己的）：**8**
- variants_ext（外部来源）：**-**（未引用外部策略变体）

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| 1 | 自己 | 最后 YES 成交 +1¢，费率 0.05，60/40 | 2025-06-05..2026-10-20 | HOLDOUT n=47 中位 +0.4376；POOLED n=101 均值 +0.0081。`bots/quant/notes/q020-oos/run_output.txt` |
| 2 | 自己 | 同上，但 p6 = `[endDate−54h, endDate−6h]` 最后成交 +1¢ | 同上 | POOLED 均值 −0.0082；`q020-oos/run_output.txt` [2b] |
| 3 | 自己 | 实际 ask 侧最后打印，费率 0.05，60/40（主回放） | 同上 | POOLED n=97 均值 −0.0140；HOLDOUT n=43 +0.0790；`run_output.txt` [1] |
| 4 | 自己 | 实际 ask 打印，剔除选带最新 250 事件（严格样本外） | 同上 | n=68 均值 −0.0634、中位 −0.4120；`run_output.txt` [1] |
| 5 | 自己 | 实际 ask 打印，但带内成员按原 CLOB `p_24h` 判 | 同上 | 严格样本外 n=42 均值 −0.0503；`run_output.txt` [2] |
| 6 | 自己 | 实际 ask 打印，费率 0.04 | 同上 | POOLED −0.0116；严格样本外 −0.0610；`run_output.txt` [3] |
| 7 | 自己 | 实际 ask 打印，费率 0.00 | 同上 | POOLED −0.0020；严格样本外 −0.0515；`run_output.txt` [3] |
| 8 | 自己 | 严格样本外改用“最后 YES +1¢” | 同上 | n=68 均值 −0.0237；`run_output.txt` [4] |

切点敏感性（2026-06-01 / 07-01 / 07-30 / 08-01）是同一套参数的子段稳健性，按 GUIDE 第 7 节不另算变体；各值见 `bots/quant/notes/scheduler/scratch/H-quant-020/strict_oos.out`。
