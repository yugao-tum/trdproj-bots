# H-quant-001 本轮硬化（2026-10-22，batch c20261022-080324-research / w01）

目标条目：`bots/quant/entries/quant-001-vm-btc-regime-gate.md`。
保持文件名、`id=quant-001`、`date=2026-10-20`、`status=待核` 不变；不改结局状态。

## 1. 复用已合并证据

`bots/quant/notes/q001-hist/` 不存在，本条的已合并证据在
`bots/quant/notes/scheduler/scratch/H-quant-001/`、`bots/quant/notes/xqt-migration/`
和 `bots/quant/replay/quant-001/`。本轮先用原脚本重跑，没有另起炉灶：

| 脚本 | 本轮结果 |
|---|---|
| `replay/quant-001/run_replay.py` | VM +23.31%/8.90%/−35.69%，SMA50 +59.73%/20.99%/−24.58%，SMA100 +83.41%/27.99%/−23.28%，SMA200 +48.97%/17.61%/−33.54%；关闭段 24/18/8；家族 p=0.066/0.084/0.278；与 `replay_stdout.txt` 逐位一致 |
| `replay/quant-001/run_holdout.py` | 2024 单年 SMA50 +0.39%、SMA100 +2.10%；walk-forward 与 always-SMA100 逐日相同；与 `holdout_stdout.txt` 一致 |
| `replay/quant-001/montecarlo_round3.py` | 20,000 次家族 p=0.0723/0.0880/0.2710；块 bootstrap SMA50−VM p(diff≤0)=0.0670、SMA50−常数缩放 p=0.0178（描述性）；与 `montecarlo_stdout.txt` 一致 |

原始 stdout 另存 `replay_rerun_stdout_20261022.txt`、`holdout_rerun_stdout_20261022.txt`；
`verify_round2_numbers.py` 逐项核对 front matter 与 JSON，0 失败。

## 2. 新增：成交价真实性抽查

`verify_fill_prices.py`：用 data-api `aggTrades` 独立取执行日 00:00 UTC 后第一笔成交，
与回放用的日线 open 对比。

- aggTrades 在 data-api 只保留近段历史；2024-08 及更早返回空，2024-10-15 起可取。
- 可取区间 2024-10-15～2024-12-31 共 **30 个执行点**（BTC/ETH/SOL）：
  日线 open 与首笔成交价 **逐点完全相同**（最大偏差 0.0000 bp），
  首笔成交在 00:00 UTC 后 **≤0.6 s**。
- 这只证明日线 open 是真实成交价、不是中间价或陈旧报价；
  不消除“收盘后 1 秒内下不到单”的执行延迟风险（条目风险节已写）。
- 产物：`verify_fill_prices.csv`、`verify_fill_prices_stdout.txt`。

## 3. 修掉的内部不一致

- `replay/quant-001/montecarlo_round3.py` 及其 JSON/stdout 之前已在目录里，但
  `SUMMARY.md` 和条目都没提。本轮把 20,000 次精度复核与块 bootstrap 写进
  `SUMMARY.md` 和条目证据节，明确它**不新增交易变体**，并如实写出
  `SMA50−常数缩放 p=0.0178` 这个偏正面的描述性结果，同时注明 CAGR 差分位区间
  向上偏、未校正 3 闸门选择偏差，结论仍是“不显著”。
- `run_holdout.py`、`montecarlo_round3.py`、`verify_fill_prices.py` 加入
  `sys.dont_write_bytecode = True`，避免重跑时在 `replay/` 生成 `__pycache__`
  触发 lint 的二进制告警。

## 4. 出处复核（本轮重抓）

`verify_sources.py` 重跑：Binance 页面/月包/日线/1h 均 200；RePEc 200（含
“nearly doubles the Sharpe ratio”）；Crossref 200（标题/作者/页码 111-120）；
DOI 200（Elsevier PII S0304405X14002566）；ScienceDirect 直连仍 403（如实标注）；
作者版 PDF 200、444,689 字节，逐句含“Sharpe ratio improves from 0.53…0.97…”
与“maximum drawdown … -96.69% versus -45.20%”。

## 5. 七条门槛

1. 机制说得清：**部分满足**。趋势收益清楚；“BTC 先走弱能躲跌”的时序优势未获统计确认。
2. 免费数据：**满足**。Binance 公开日线/aggTrades，免密钥，2022–2024。
3. 小资金：**满足**。现货多头、不加杠杆，平均仓位 0.23–0.33。
4. 不重复：**不确定**。仍是对 T-T2-vm 的改进申报；改进未成立时可能只算变体。
5. 扣成本够用：**0.30%/边满足（SMA50 折年 20.99%）；作为改进不满足**
   （1.00%/边 7.75%，2024 单年 +0.39%，独立结果 <30）。
6. 两周内能检验：**不满足**。独立关闭段 24/18/8 <30；20,000 次家族校正
   p(compound)=0.0723、p(Sharpe)=0.0880、p(DD)=0.2710，均 >0.05。
7. 出处可查：**满足**。外部 URL 本轮重抓；403 如实标注，关键句由作者版 PDF 核实。

## 6. 建议

维持“不显著 / 待选区（1.0）”，不要按“改进采纳”（2.0）计分。
2024 切分、walk-forward、20,000 次精度复核和块 bootstrap 都没有把负面证据翻正；
若主审要求“稳定优于原版”，可直接退回。
