# H-quant-001 修复记录（2026-10-21）

- 队列项：`H-quant-001`，条目 `bots/quant/entries/quant-001-vm-btc-regime-gate.md`。
- 输入：`notes/scheduler/reviews/c20261021-070001-research.md` 的 H-quant-001 三条问题；`notes/scheduler/audit/c20261021-070001-research.md` 的 S5（第 2 轮 8 字段/窗口）；较早的 S8/S13（CCI 回撤口径）已在条目中不存在。`notes/scheduler/checks/` 没有 quant-001 专项文件。
- 约束：未改 `status`（仍 `待核`）、`date`（仍 `2026-10-20`）、文件名、`id`；未改 `kind`/`improves`；只改条目和允许的 replay/scratch 路径。

## 问题 -> 改动 -> 证据

| # | 复核指出的问题 | 改了什么 | 证据 |
|---|---|---|---|
| 1 | `门槛自查` 第 6 条写“满足”，但同一节的预注册独立结果是 SMA50/100/200 = 24/18/8，全部 <30。自相矛盾，也是最可能的拒绝理由。 | 第 6 条改为 **“不满足”**：写明 24/18/8 均 <30、3 闸门家族校正 p=0.066/0.084/0.278，已按预注册失败标准判不显著。其余门槛结论不变。 | 重跑 `bots/quant/replay/quant-001/run_replay.py`：`episodes=24/18/8`；`familywise p(compound)=0.066 p(DD)=0.278 p(Sharpe)=0.084`。与 `replay/quant-001/replay_results.json`、`replay_stdout.txt` 一致。 |
| 2 | 第 4 条只与 `T-T1-regime-filter` 对比，没有回答复核提出的 `known/T-T1-turtle`（同为“多币突破加仓，BTC 开关”）为何不是同一机制。 | 第 4 条补充具体差别：T-T1-turtle 的入场和加仓来自突破信号；本条不做突破、不做加仓，只把 T-T2-vm 的既有仓位乘一个 BTC 日线 SMA50 的二元开关（收盘确认、次日开盘执行、每 5 日调仓）。仍保持 **“不确定”**，交核对判断。 | `known/KNOWN.md` 中 `T-T1-turtle`（多币突破加仓，BTC 开关）、`T-T1-regime-filter`（小时突破放量，状态过滤）、`T-T2-vm`（主流币正动量等权，波动管理）三行；条目规则见 `## 规则` 第 2–3 条。 |
| 3 | `:129` 建议“从 improvement 降为待选区”，但 front matter 仍是 `kind: improvement`，读起来像已改分类。 | 改为“建议按待选区（1.0）处理……本条 `kind` 仍是 `improvement`（不改 front matter），上述只是对结局的建议”。 | 条目 `## 改进了什么` 最后两条；front matter 第 9–10 行未动。 |
| 4 | S5：第 2 轮 8 字段、可成交价回放、2022–2024 窗口。 | 条目现有字段 `evidence: 回放`、`result: 不显著`、`slot: -`、`variants: 7`、`variants_ext: 不清楚`、`window: 2022-01-01..2024-12-31`、`max_dd: -24.6%（日线）`、`contribution: 21.0%`；与 `replay/quant-001/SUMMARY.md` 的 7 个变体、窗口、回撤、21.0% 一致。本次未改数字，只重跑核验。 | `verify_replay_entry.py`：88 checks，0 failed；重跑 `run_replay.py` 输出与条目表逐行一致（VM +23.31%/8.90%/−35.69%；SMA50 +59.73%/20.99%/−24.58%；常数缩放 +20.07%/7.73%/−28.54%）。 |
| 5 | “每个引用来源都要能打开、说所声称的话”。 | 重取全部外部 URL；35 个本地引用文件逐个确认存在、<1 MB、非二进制。ScienceDirect 仍 403（条目已写“摘要”），作者版 PDF 仍 200 且逐句含 0.53→0.97 与最大回撤 −96.69%→−45.20%。 | `verify_sources.py`/`verify_sources_stdout.txt`（本次重跑）；`verify_cited_local.py`/`verify_cited_local_stdout.txt`（35/35 OK）。 |
| 6 | 较早审计 S8/S13：CCI `−11.1%` 是单折最差回撤，不是路径回撤。 | 条目中已无 CCI/SAR/`−11.1%` 字样（`grep` 无命中），无需再改；旧窗口数字也未抄入本条。 | `grep -n "CCI\|11\.1\|SAR\|单折"` 对条目无输出。 |

## 重跑与检查命令

```bash
python3 bots/quant/replay/quant-001/run_replay.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_sources.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_cited_local.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_replay_entry.py
python3 tools/check.py lint --bot quant
```

结果：replay 与已存 `replay_results.json` 一致（仅 `generated_utc` 时间戳随重跑更新）；来源 200/403 与条目注记一致；本地引用 35/35 存在；`verify_replay_entry.py` 88/0；`lint --bot quant` 输出“检查完毕，问题 0 个”。

## 诚实结论（不改数字）

- 7 门：1 部分满足；2、3、7 满足；4 不确定；5 仅在 0.30%/边、且不作为“改进采纳”时成立（1.00%/边推荐版折年 7.75%）；6 **不满足**（独立关闭段 24/18/8 <30）。
- `result: 不显著` 保持不变；没有把任何数字上调或改成显著。
- 建议：不按“改进采纳”（2.0）或收录计分；按待选区（1.0）或退回处理。若要继续，最有价值的是补足独立关闭段/做前向，而不是继续在本窗口调参。

## 2026-10-21（batch c20261021-120001，按 review/c20261021-120001-research.md）

| # | 复核指出的问题 | 改了什么 | 证据 |
|---|---|---|---|
| 1 | 家族校正 p 值被错误归给 SMA50（条目 `:31`、`:83`、`:115`、`:127`、`:139`、`:144`、`:149`）。`familywise` 是 SMA50/100/200 的 max-statistic，最佳实际变体是 **SMA100**；p(DD)=0.278 不能当 SMA50 的结果。 | 上述位置全部改为“家族 max-statistic 取最佳变体 SMA100”，并补上 SMA50 自己的单闸门 placebo：p(compound≥实际)=0.065、p(Sharpe≥实际)=0.084、p(DD≤实际)=0.756（实际更好的 DD 尾概率 0.244）。结论仍为“不显著”，未改任何收益/回撤数字。 | 重跑 `run_replay.py` 的 `familywise` 块：`best_compound_pct=83.41`、`best_dd_pct=-23.28`、`best_sharpe=1.141`、`p_family_compound=0.066`、`p_family_dd=0.278`、`p_family_sharpe=0.084`；`placebo.SMA50` 为 0.065/0.756/0.084。见 `bots/quant/replay/quant-001/replay_results.json`。 |
| 2 | 外部来源被写成“最大回撤显著下降”（条目 `:38`、`:150`、`:164`，`SUMMARY.md` 变体表第 9 行）。原文有夏普接近翻倍的表述和回撤对比，但没有回撤差异的显著性检验。 | 改为“最大回撤明显下降；原文未给回撤差异的显著性检验”。同时遵守 GUIDE §9：原文样本早于 2021，具体数字按第 2 轮规则不抄入条目，写“见原文”。未删掉“来源自报，未核实”。 | `verify_sources_round2_stdout.txt`：作者版 PDF HTTP 200、444,689 字节；`pdftotext` 命中 “The Sharpe ratio improves from 0.53” / “0.97 for its risk-managed version” / “maximum drawdown ... -96.69% versus -45.20%”；未命中任何回撤显著性检验的说法。ScienceDirect 仍 403（如实标注）。 |
| 3 | 门 4 仍未决；不能因为条目给了区别就改成“满足”或另占新机制名额。 | 保留 `kind: improvement`、`improves: T-T2-vm`、`slot: -`；`:147` 继续写“不确定”，并保留与 `T-T1-turtle`（突破入场/加仓 vs VM 仓位上的二元 SMA50 开关）的具体区别，交主审裁决。 | front matter 第 9–11、21 行未动；`known/KNOWN.md` 的 `T-T2-vm`、`T-T1-turtle` 行。 |
| 4 | 门 5/6 不满足，贡献 21.0% 不能当可外推预期。 | `:148`/`:149` 保持“作为改进不满足”“不满足”；`:122` 保留 21.0% 全样本粗算，并继续注明 2024 单年约 0.4%。未上调任何数字。 | `run_holdout.py` 重跑：2024 SMA50 +0.39%；1.00%/边 SMA50 折年 7.75%；关闭段 24/18/8。 |
| 5 | 8 个 front-matter 字段与 `SUMMARY.md` 一致性。 | 未改字段：`evidence: 回放`、`result: 不显著`、`slot: -`、`variants: 8`、`variants_ext: 不清楚`、`window: 2022-01-01..2024-12-31`、`max_dd: -24.6%（日线）`、`contribution: 21.0%`。只同步了 `SUMMARY.md` 的 p 值归属与外部引文措辞。 | `verify_replay_entry.py`：108 checks，0 failed；`lint --bot quant`：问题 0 个。 |
| 6 | 每个引用来源要能打开、说所声称的话。 | 本轮重跑 `verify_sources.py`、`verify_cited_local.py`；外部 URL 状态与条目一致，44 个本地引用全部存在且 <1 MB、非二进制。 | `verify_sources_round2_stdout.txt`、`verify_cited_local_stdout.txt`（44/44 OK）。 |

## 重跑与检查（本轮）

```bash
python3 bots/quant/replay/quant-001/run_replay.py
python3 bots/quant/replay/quant-001/run_holdout.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_sources.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_cited_local.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_replay_entry.py
python3 tools/check.py lint --bot quant
```

- `run_replay.py`：VM +23.31%、SMA50 +59.73%、SMA100 +83.41%、SMA200 +48.97%；关闭段 24/18/8；家族 p=0.066/0.084/0.278，最佳实际变体 SMA100；与 `replay_results.json` 一致（仅 `generated_utc` 更新）。
- `run_holdout.py`：2024 VM −8.64%、SMA50 +0.39%、SMA100 +2.10%、SMA200 −16.29%；walk-forward +96.04%，与 always-SMA100 逐日相同。
- `verify_replay_entry.py`：108/0；`lint --bot quant`：问题 0 个。
- `status: 待核`、`date: 2026-10-20`、文件名、`id` 均未改。

## 诚实结论（本轮）

- 建议不变：**待选区（1.0）/反证**，不按“改进采纳”（2.0）或收录计分。
- 门 1 部分满足；2、3、7 满足；4 不确定；5、6 不满足；`result: 不显著`。
- 21.0% 只是全样本账户级算术，2024 单年约 0.4%，不可当预期；若主审要求“稳定优于原版”，可直接退回。

## 2026-10-22（batch c20261022-063202/research，queue H-quant-001，fixer f1-03）

输入：`reviews/c20261022-063202-research.md` 的 H-quant-001 三条（门 6 / `contribution: 21.0%` 误导 / replay 复核）；
`reviews/c20261021-120001-research.md` 的 re-check 尾项（`:38` “最大回撤明显下降”措辞、待选区处置）；
`audit/c20261020-170337-research.md` S8 与 `audit/c20261021-030001-research.md` S13（CCI 回撤口径，条文中已无此内容）；
`checks/` 下没有 quant-001 专项文件。任务要求不改 status/date/文件名/id。

| # | 问题（复核原文） | 改了什么 | 证据 |
|---|---|---|---|
| 1 | 复核：`contribution: 21.0%` 是全样本净折年，但条目自己写 2024 单年 +0.39%，“不能当作可外推的预期”；21.0% 不能当 head-line。 | front matter `contribution: 21.0%` → **`0.4%`**（2024 单年 +0.39% × 5,000 ÷ 5,000）。`## 成本与容量` 改写：字段用 2024 单年 0.4%；全样本 20.99%（≈21.0%）明确标为“样本内复算”，`**不把 21.0% 当字段值或预期**`。`SUMMARY.md` 同一段同步。 | `run_holdout.py` 重跑：2024 VM_x_SMA50 compound=+0.39%、cagr=+0.39%；`run_replay.py` 全样本 cagr=20.99%。`verify_replay_entry.py` 新增 contribution=0.4% 与“21.0% 仅作 caveat”两项检查，116 checks / 0 failed。 |
| 2 | 复核：门 6 不满足，不能 PASS/改进采纳；状态建议改待选区/草稿。 | 按队列硬要求**未改 `status: 待核`、`date`、文件名、`id`**；在 `## 改进了什么` 末条补一句：status 是第 1 轮名额留下的状态，是否降级由整合者定，结局建议仍是待选区（1.0）/反证。门 6 仍写“不满足”，未上调任何数字。 | `verify_replay_entry.py` 的 `id/date/status unchanged` 检查通过；`lint --bot quant` 问题 0 个。 |
| 3 | re-check：`:38` “最大回撤明显下降”把外部来源写成已检验的改进，但原文没有回撤差异的显著性检验。 | 改为“原文报告最大回撤低于未缩放版，但原文未给该差异的显著性检验”；保留“来源自报，未核实”，具体数字按第 2 轮规则不抄入。 | `verify_sources.py` 重跑：作者版 PDF HTTP 200、444,689 bytes，命中 `The maximum drawdown of raw momentum is -96.69% versus -45.20%`；未命中任何回撤显著性检验语句。ScienceDirect 仍 403（条目如实标注“摘要”）。 |
| 4 | 任务：重做可成交价历史回放，扣费、样本外。 | 回放已存在于 `replay/quant-001/`（2022-01-01..2024-12-31、次日 Binance 日线 **open** 成交、0.30%/边），本轮**从缓存/重下载重跑**确认；未改窗口、未看 2021/2025+ 数据。加密按 GUIDE §9 用次根开盘价，Polymarket 的 data-api/prices-history 规则不适用。 | `run_replay.py` 重跑输出 VM +23.31%/8.90%/−35.69%、SMA50 +59.73%/20.99%/−24.58%、SMA100 +83.41%/27.99%/−23.28%、常量缩放 +20.07%/7.73%/−28.54%；关闭段 24/18/8；家族 p=0.066/0.084/0.278；`run_holdout.py` 重跑 2024 SMA50 +0.39%。与 `replay_results.json`/`holdout_results.json`/`SUMMARY.md` 一致（仅 `generated_utc` 随重跑更新）。本次重跑的 stdout 与已入库的 `replay_stdout.txt`/`holdout_stdout.txt` 数字逐位一致。 |
| 5 | 任务：逐个确认引用来源存在且说所声称的话。 | 重跑来源脚本；44 个本地引用全部存在、<1 MB、非二进制；外部 URL 状态见 stdout。 | `verify_sources.py`：binance 各接口 200；RePEc 200；Crossref 200；DOI 200；作者版 PDF 200；ScienceDirect 403（已披露）。`verify_cited_local.py`：44/44 OK。 |
| 6 | 任务：`lint --bot quant` 必须 0 个问题。 | 改完字段后重跑。 | `python3 tools/check.py lint --bot quant` → `检查完毕，问题 0 个`。 |
| 7 | 任务：不能核实的来源陈述要删或降级。`data:` 与 `## 数据` 原写“2017 年起有（SOL 2020 年 8 月起）”，但第 2 轮窗口禁止下载/查看 2021 及以前数据，本轮无法在不违规的前提下核实这两句。 | 删掉 2017/2020 起点的具体断言，改为“本条回放只用 2022-01-01～2024-12-31，BTC/ETH/SOL 在该区间均有数据；更早数据未下载、未使用”。 | `run_replay.py` 实际请求并得到三币 2022-01-01～2024-12-31 日线（`replay_results.json` 的 window 与数据行数）；未请求更早区间。 |

### 本轮重跑命令与结果

```bash
python3 bots/quant/replay/quant-001/run_replay.py
python3 bots/quant/replay/quant-001/run_holdout.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_sources.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_cited_local.py
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_replay_entry.py
python3 tools/check.py lint --bot quant
```

- `verify_replay_entry.py`：116 checks，0 failed（已删除运行时生成的 `replay/quant-001/__pycache__`）。
- `lint --bot quant`：问题 0 个。
- 未新增/删除任何收益、回撤、p 值；`result: 不显著` 不变。

### 诚实结论（本轮，覆盖上文旧的 21.0% 表述）

- 7 门：1 部分满足；2、3、7 满足；4 不确定；5 作为改进不满足（1.00%/边 7.75%、2024 +0.39%）；6 **不满足**（独立关闭段 24/18/8 <30，家族 p>0.05）。
- `evidence: 回放`、`result: 不显著`、`window: 2022-01-01..2024-12-31`、`max_dd: -24.6%（日线）` 不变；`contribution` 改为 **0.4%**（2024 单年）。
- 建议：**不按“改进采纳”（2.0）或收录计分；按待选区（1.0）/反证，或直接退回。** 若继续，价值在补足 ≥30 个独立关闭段/做前向，而不是在本窗口继续调参。
