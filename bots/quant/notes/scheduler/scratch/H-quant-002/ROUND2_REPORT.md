# H-quant-002 第 2 轮：回放复核与修正（2026-10-22）

目标条目：`bots/quant/entries/quant-002-tom-monday-oos-counterevidence.md`（supplement，E-E2-turn-of-month，负证据）。
规范回放：`bots/quant/replay/quant-002/`（不是本目录）。本目录只放本次运行的 stdout 副本。

## 1. 复用了什么，重跑了什么

- 先查已合并笔记：`bots/quant/notes/xqt-migration/README.md`、`reproduce.py`、`results.csv`
  给出冻结的 TOM/周一规则和 8 个 `M3_*` 规则名；旧窗口 2020-12-31..2026-10-13，含 2025–2026。
  本条只复用规则定义，**不抄**旧窗口的 2025–2026 数字。`q012-hist/`、`q006-hist/` 是地震和网球，
  与本条无关。
- 规范回放已存在于 `bots/quant/replay/quant-002/`，本次**重跑**而不是重写：
  `fetch_data.py` → `backtest.py` → `verify_results.py` → `verify_sources.py`。
  stdout 副本：`round2_fetch_stdout.txt`、`round2_backtest_stdout.txt`、
  `round2_verify_results_stdout.txt`、`round2_verify_stdout.txt`。
- 数据只取 2022-01-01..2024-12-31（GUIDE §9）；1d 1,096 行/币，1h 26,303 行/币。

## 2. 本次修正（最可能的退回理由）

### 2.1 截断窗口混进了 TOM 错位变体

`backtest.py` 的 TOM 错位版本由精确窗口整体后移一天得到。2022-01-01 边界使 2021-12-31 不在数据里，
于是 2022-01 的 TOM 错位首窗实际只有 3 天（2022-01-02..01-04），却被当成规则的 4 天窗口计入，
得到 36 个窗口。这与 SUMMARY 里“边界截断窗口已剔除”的说法矛盾，也让错位版本和精确版本的窗口数不一致。

修正：删除这个 3 天截断窗。TOM 两个版本现在都是 35 个窗口。受影响的 4 行结果：

| 版本 | 成交价 | 修正前 3 年连乘 | 修正后 3 年连乘 | 修正后年化 |
|---|---|---:|---:|---:|
| BTC TOM 错位 | next_open | −12.50% | −8.34% | −2.86% |
| BTC TOM 错位 | first_hour_vwap | −15.33% | −11.97% | −4.16% |
| ETH TOM 错位 | next_open | −20.29% | −20.22% | −7.26% |
| ETH TOM 错位 | first_hour_vwap | −25.06% | −25.14% | −9.21% |

结论不变：16/16 在 0.30%/边下仍为负；最好（最不亏）的变体从 −12.50% 变为 −8.34%。
条目正文、SUMMARY、placebo 表、trades 行数（768→766）已同步。

### 2.2 条目引用的 scratch stdout 不存在

条目原来引用 `scratch/H-quant-002/round2_fetch_stdout.txt` 等 3 个文件，但此前没有落盘。
本次已用真实运行输出补齐 4 个文件（含新增的 `round2_verify_results_stdout.txt`），
`verify_sources.py` 现在报告 `exists=True`。

### 2.3 回撤口径不清

`max_dd: 55.7%（日线）` 是 2,500 USDT 单币袖套口径，不是 5,000 账户口径。
新增 `verify_results.py` 复算：主变体袖套 −55.72%，账户级（另 2,500 现金不动）−29.33%；
最差变体账户级 −44.24%。条目和 SUMMARY 已写明口径。

## 3. 本次自检（`verify_results.py`，0 failed checks）

- 16 行结果 = 8 条冻结规则 × 2 种成交价；16/16 净连乘 < 0。
- 用 `trades.csv` 的 766 笔逐笔净收益重新连乘，与 `results_variants.csv` 的 8 个主口径结果一致（误差 <1e-5）。
- 1,532 个进场/出场价全部落在当日 `[low, high]` 内。
- 周一交易跨 1 天（周一→周二；错位版周二→周三），TOM 交易跨 4 天；全部在 2022-01-01..2024-12-31 内。
- 8 个主口径窗口数 35/35/156/157，均 ≥30。
- 条目字段 `id/date/evidence/result/window/variants/variants_ext/contribution/max_dd` 与产物一致。

## 4. 出处复核（`verify_sources.py`）

- 两个 listing 页 HTTP 200；BTC/ETH 2024-12 月包各 31 行 × 12 列。
- 1d/1h 完整查询 URL HTTP 200；1d 1,096 行/币，1h 26,303 行/币。
- `aggTrades` 2024-10-09 00:00–01:00 UTC：43,529 笔；首笔价 = 日线开盘价（0.000000 bp）；
  逐笔 VWAP = 1h K 线首小时 VWAP（0.000000 bp）。
- 2024-10-09..2024-12-28 每 4 天采样：BTC、ETH 各 21 天，首笔成交价与日线开盘价
  最大差 0.000000 bp（`aggtrades_open_sample_BTC/ETH`）。
- `known/KNOWN.md` 第 48 行有 `| E-E2-turn-of-month | 月末月初持有 |`。
- 条目 `id: quant-002`、`date: 2026-10-20`、`status: 待核` 未改。

## 5. 七条门槛的判断

1. 机制说得清：满足（作为补充，检验已知的月初月末/周一资金流说法）。
2. 有免费数据：满足（Binance 公开 1d/1h，免密钥，2022-2024 完整）。
3. 小资金能做：满足（现货、无杠杆、单币 ≤2,500 USDT）。
4. 不重复：满足（known 的 E-E2 先到；本条只补负证据）。
5. 扣成本后粗算够用：**不满足**，这正是结论（0.30%/边下 16/16 为负）；只能按反证补充采纳。
6. 两周内能检验：满足（35 个 TOM 窗、156–157 个周一窗；脚本几分钟可重跑）。
7. 出处可查：满足（listing/zip/klines/aggTrades 全部复核；脚本与 stdout 已落盘）。

## 6. 剩余风险

- 2022-2024 是冻结规则后的时序样本，不是盲样本；真正盲测只能靠 2026-10 之后的前向记录。
- `aggTrades` 免密钥端点只回溯到 2024-10-08，逐笔复核只能覆盖 2024-10-09 这一个小时；
  日线/1h 的完整窗口不受影响，但“开盘价来自真实成交”的逐笔证据只覆盖该时段。
- 0.30%/边是 GUIDE 粗算；极端行情下次日开盘成交可能更差，未额外加滑点。
- 未计稳定币利息、交易所托管风险；现货无资金费。
