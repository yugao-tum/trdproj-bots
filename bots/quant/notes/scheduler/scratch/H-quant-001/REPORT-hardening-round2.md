# H-quant-001 第二轮硬化（2026-10-21）

队列项 H-quant-001，目标条目 `bots/quant/entries/quant-001-vm-btc-regime-gate.md`
（保持文件名、id、date=2026-10-20、status=待核 不变）。

## 1. 复用而不是重做

第一轮 H-quant-001 的脚本与 stdout 已合并在本目录：`tradable_backtest.py`、
`placebo_gate.py`、`tradable_results.csv`、`same_exposure.csv`、`episodes_*.csv`、
`verify_sources.py`，以及旧口径的 `bots/quant/notes/xqt-migration/` 与
`bots/quant/notes/xqt-migration/q001-robustness/`。本轮没有另起炉灶：

- 用原脚本重跑可成交价回测与单闸门 placebo，确认数字逐位一致；
- 只在原证据的薄弱处新增一个 3 闸门家族校正，并补一个可直接读取的论文 PDF 出处；
- 新增 `verify_entry_numbers.py`，把条目里 71 个关键数字与 CSV/stdout 逐一对照。

## 2. 重跑核对（与第一轮逐位一致）

| 文件 | 结果 |
|---|---|
| `harden_fetch_stdout.txt` | BTC/ETH/SOL 各 50,698 根 1h K 线，2,113 个交易日，2020-12-31～2026-10-13 |
| `harden_tradable_stdout.txt` | close-fill VM 基线 +237.1525%/37.8172%/−15.8209%/−22.1166%/0.2886，与 `xqt-migration/results.csv` 一致 |
| `harden_placebo_stdout.txt` | 与 `placebo_stdout.txt` 逐字节一致（SMA50 p(compound)=0.032、p(DD)=0.601） |
| `verify_entry_numbers_stdout.txt` | 71 项检查，0 失败 |

可成交价 4 折 OOS（2022-12-31～2026-10-13，0.30%/边）关键值：

| 版本 | 连乘 | 折年 | 单折最差 | 路径回撤 | 平均仓位 |
|---|---:|---:|---:|---:|---:|
| VM | +232.5% | 37.3% | −15.7% | −22.6% | 0.29 |
| SMA50 | +213.1% | 35.2% | −16.1% | −19.6% | 0.24 |
| SMA100 | +148.1% | 27.1% | −15.5% | −19.5% | 0.22 |
| SMA200 | +140.7% | 26.1% | −15.5% | −20.9% | 0.21 |

## 3. 新增：3 闸门家族校正（本轮唯一的新统计检验）

第一轮留了一个口子：SMA50 的 compound p=0.032 看起来像正结果，但那是**单闸门、
未校正**的，而且同一族的 SMA100/200 不显著。`familywise_placebo.py` 让三个事先指定
的 SMA 闸门共用同一组 2,000 次循环平移，用 max-statistic 校正“三个里挑最好”的选择偏差：

| 闸门 | 实际连乘 / 路径回撤 / Sharpe | 校正后 p(compound / DD / Sharpe) |
|---|---:|---:|
| SMA50 | +213.13% / −19.55% / 1.227 | 0.070 / 0.812 / 0.219 |
| SMA100 | +148.13% / −19.54% / 0.966 | 0.238 / 0.823 / 0.463 |
| SMA200 | +140.70% / −20.86% / 1.031 | 0.281 / 0.741 / 0.393 |

家族整体：p(compound)=0.070、p(pathDD)=0.812、p(Sharpe)=0.219
（`familywise_placebo_stdout.txt`、`familywise_placebo.csv`）。

**结论仍然是负面**：SMA50 的收益优势在 3 闸门校正后 p=0.070，不到 5% 显著；
回撤优势 p=0.812，完全不成立。不能按“改进采纳”计分。

## 4. 出处逐条复核

`verify_sources.py` / `verify_sources_stdout.txt`（本轮重跑，另存
`harden_verify_sources_stdout.txt`）：

| 来源 | 结果 |
|---|---|
| Binance 日线前缀页 / 月包 zip | 200；zip 可打开 |
| Binance data-api 1h K 线 | 200；2 行 × 12 列 |
| RePEc 文章页 | 200；含标题与 “nearly doubles the Sharpe ratio” |
| Crossref DOI | 200；标题/作者/页码 111-120/DOI 对上 |
| DOI 解析 | 200；Elsevier PII S0304405X14002566 |
| ScienceDirect 文章页 | 403（本机），仍无法直连 |
| 作者版 PDF（thetabruv 托管） | **200，444,689 字节**；`pdftotext` 读出 “The Sharpe ratio improves from 0.53 … to 0.97 …” 与 “The maximum drawdown of raw momentum is -96.69% versus -45.20%” |

这修掉了第一轮最可能被挑的出处问题：0.53/0.97 与 −96.69%/−45.20% 原先只能靠
ScienceDirect 搜索索引摘要，现在有可直接读取、逐句核对的作者版 PDF；DOI/页码仍由
Crossref 独立确认。PDF 是第三方托管，条目里已如实写成“第三方托管的作者版 PDF”。

## 5. 七条门槛结论

1. 机制说得清：**部分满足** — 趋势收益本身清楚；“BTC 先走弱所以能躲跌”的时序优势被独立区段、同仓位对照、单闸门 placebo 和 3 闸门家族校正共同否定。
2. 免费数据：满足 — Binance 公开日线 + 1h K 线，免密钥，6 年。
3. 小资金：满足 — 现货多头、不加杠杆、平均仓位 0.21–0.29。
4. 不重复：不确定 — 仍是对 T-T2-vm 的改进申报，但改进未成立；由整合者判断是否只算变体。
5. 扣成本够用：**绝对收益满足，作为改进不满足** — 0.30%/边下 SMA50 折年 35.2%，1.00%/边下 22.1%；但回撤不优于同仓位常数缩放，收益优势校正后 p=0.070。
6. 两周内能检验：满足 — 60/39/25 个独立关闭区段，脚本约 10 s + 30 s + 60 s。
7. 出处可查：满足 — 外部 URL 全部复核；ScienceDirect 403 已标注，关键数字改由可读 PDF 直接核实。

## 6. 建议

维持第一轮结论并写进条目：**建议整合者把 quant-001 从 `improvement` 降为待选区
（1.0），不要按“改进采纳”（2.0）计分。** 若主审把“收益低于 VM”作为硬条件，也可
直接退回。条目未改 `kind/status/date`，由整合者决定最终结局。

## 7. 复现

```bash
cd bots/quant/notes/scheduler/scratch/H-quant-001
python3 fetch_hourly.py          # 首次约 3 分钟；_cache 已 gitignore
python3 tradable_backtest.py     # 约 10 s
python3 placebo_gate.py          # 2,000 次，约 30 s
python3 familywise_placebo.py    # 3 闸门共用平移，2,000 次，约 60 s
python3 verify_sources.py        # 外部 URL + 作者版 PDF
python3 verify_entry_numbers.py  # 条目 71 个数字对照 CSV/stdout
python3 lint_entry.py            # 字段检查
```

## 8. 限制

- 只有 3 个币、约 3.8 年严格 OOS、日线信号；1h VWAP 是执行近似，不是逐笔成交。
- 3 闸门家族校正只覆盖条目推荐的 SMA 家族；更广的 106 闸门选择偏差仍用旧收盘价口径的 DSR/PBO 作参考（`q001-robustness/REPORT.md`），没有用可成交价重算 106 个闸门。
- 2022 压力折不是严格 OOS；私有仓库的 22.4 万次搜索规模无法复核。

## 9. 备注

全仓 `python3 tools/check.py lint` 仍会在 `bots/muse/entries/muse-700-*` / `muse-701-*`
上缺字段并抛 `KeyError: 'id'`（与本条无关，未改他人文件）；本条的 `lint_entry.py`
逐字段检查通过。
