# H-quant-021 / quant-021 修正记录（fixer，2026-10-21）

条目：`bots/quant/entries/quant-021-f1-pole-winner-base-rate.md`
未改：文件名、`id: quant-021`、`date: 2026-10-20`、`status: 待核`。

## 1. 审查指出的问题及处理

| 问题（来源） | 改了什么 | 证据 |
|---|---|---|
| `reviews/c20261021-070001-research.md`：`:16` 把 49 个“有价格的 event”写成历史独立结果，未说明主规则只触发 23 个。 | `test_2w:` 改为“49 个 Winner event 能取到价格/成交，但主规则只触发 23 个，交易级样本 <30”。 | 回放 `results.json`：`events=49`、`primary.n=23`、`bootstrap.ci95=[-0.010062,+0.411496]`；stdout `run_fix_replay.txt`。 |
| 同审查：`:258` 门 6 写“49 个历史独立结果已超过 30 的门槛”，与主规则 23 笔矛盾。 | 门 6 改为“49 个 event 有价格，但主规则只触发 23 个；23<30，且 bootstrap 下界含 0，只能按待选区/前向补充”。 | 同上；`result: 不显著` 与 GUIDE §7 定义一致。 |
| 同审查：`:254` 门 2 也把“49 个独立结果”说得过满。 | 改为“49 个 event 的价格样本（主规则触发 23 个交易级结果）”。 | 同上。 |
| `audits/c20261020-170337`、`c20261021-030001`：旧稿 137/269 是 Ergast 分页覆盖错误，须恢复 150/269 等。 | 条目已是修正后的 150/269、110/204、40/65、12/17；本轮未再改数，重新复核。 | 冷启动回放：`ergast races 269`、`fit races 204 p0 0.5392`；本轮 `verify_fix_sources.py` 另查 2024 排位 `limit=100 total=479`。 |
| 要求：逐条核对引用来源。 | 新建 `verify_fix_sources.py`，重取 Ergast、Gamma 5 页、4 个规则页、CLOB 15/20 天与 `interval=max`、data-api 字段、回放产物与 8 字段。 | `run_fix_verify.txt`：**80 项 PASS，ALL PASS**。 |
| 要求：真实可成交价、扣费、样本外回放。 | 用全新缓存重跑 `replay/quant-021/run_replay.py`（未用旧缓存）。 | `run_fix_replay.txt`：`gamma events 401`、`ergast races 269`、`matched winner events 49`、`primary n=23 wins=13 mean=+0.2003`、bootstrap `[-0.0101,+0.4115]`、`contribution_pct=4.542`。 |

## 2. 本轮重新跑出的关键数字

- 主规则：23 笔、13 胜、合计 `+4.6077`/份、均值 **+0.2003**/份。
- 事件级 bootstrap 95%：**[-0.0101, +0.4115]**，`P(mean<=0)=0.03095`，区间含 0。
- 年化贡献：`+4.6077 × 100 = 460.77 USDT`，跨 24.34 个月，`227.12/5000 = 4.542%` → 字段 `contribution: 4.5%`。
- 数据：269 场（2014–2026），2014–2023 拟合 `n=204`、常数 `p0=110/204=0.5392`；49 个 event、32 个杆位夺冠。
- 横截面：940 个有价市场；价格和 `median=1.0415`、`min=0.99`、`max=1.568`。

## 3. 8 个 round-2 字段（与 replay/SUMMARY 一致）

`evidence: 回放`｜`result: 不显著`｜`slot: -`｜`variants: 27`｜`variants_ext: -`｜`window: 2014-03-16..2026-10-11`｜`max_dd: -`（Polymarket 可选填，GUIDE §7）｜`contribution: 4.5%`。

`variants: 27` 与 `replay/quant-021/SUMMARY.md` 的 V01–V27 表一致；`SUMMARY.md` 也写明事件级 49 个、交易级主规则只触发 23 个（<30）。

## 4. 结论 / 建议

证据支持“方向为正但统计不显著”，**不支持**升级为“已证实 edge”。主规则交易级 23<30、bootstrap 下界含 0，年化约 4.5%，容量小且无历史 L2 深度。建议按**待选区**处理；若主审要求独立结果 ≥30 且区间不含 0，当前证据不满足，应先做两周前向记录。

## 5. 文件

- 修改：`bots/quant/entries/quant-021-f1-pole-winner-base-rate.md`（仅上述 4 处措辞；字段/状态/日期未动）。
- 重跑：`bots/quant/replay/quant-021/results.json`（仅 `generated_utc` 变化，数字逐位一致）。
- 新增：`scratch/H-quant-021/verify_fix_sources.py`、`run_fix_verify.txt`、`run_fix_replay.txt`、本文件。
