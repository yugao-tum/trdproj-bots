# H-quant-019：quant-019 真实成交价回放

日期：2026-10-21 ｜ 目标：`bots/quant/entries/quant-019-measles-cdc-count-ladder.md`（`status: 待核`、`date: 2026-10-20` 未改）｜ 工作树：`quant-batch/c20261021-080001-research/w04`

## 结论

**不显著、偏负，建议降为待选区/退回或并入 quant-012。** 7 个已结算月度阶梯、17 笔 data-api 真实成交打印：

| 变体 | 成交/事件 | 投入 | 净额 | 收益率 |
|---|---|---:|---:|---:|
| YES（条目主张） | 10 / 5 | 2,123.10 | +274.70 | +12.94% |
| YES 去掉 2026-07-31 | 6 / 4 | 1,887.65 | −366.20 | −19.40% |
| NO（镜像） | 7 / 4 | 922.71 | −624.91 | −67.73% |
| 费率 0（合计） | 17 | 3,045.81 | −273.02 | −8.96% |

独立结果 7 个（按 event），< 30，故 `result: 不显著`；正号完全由 7 月单个事件（`≥2300 @ 0.215`）撑着。

## 文件

- `fetch_events.py` / `fetch_events.stdout.txt` — Gamma 35 个麻疹事件快照（写 `_cache/events.json`，已 gitignore）。
- `replay.py` / `replay.stdout.txt` — 回放；参数：sigma=0.35、edge=0.05、300/档、最多 2 相邻档、费 0.04、seed 19、20,000 路径。
- `verify_sources.py` / `verify_sources.stdout.txt` — 逐条复验条目引用的 URL。
- `fills.csv`、`replay_summary.json` — 17 笔成交与汇总。
- `bots/quant/replay/quant-019/` — 同一套脚本 + `SUMMARY.md`（canonical replay）。

## 复验出处

- Gamma / data-api 全部 HTTP 200（2026-10-21）；数值与 10-20 快照的差异属正常变动。
- CDC 页面 2026-10-21 从本机 **HTTP 403**（未取到，反爬）；CDC 原文引用已合入的 `bots/quant/notes/batch2-verification/quant-019.md`（2026-10-20 记录 HTTP 200 与原文片段），没有重编。
- 未使用 CLOB `prices-history` 当成交价（NOTICES 2026-10-21 第 6 条）。

## 限制

1. CDC 机读周序列仍未取到，流量只能月频代理，不是每周打印后重算。
2. 条目写于样本结算之后，`2026-06-01` 只是日期切分，不是真正盲测。
3. “两条阶梯互相矛盾”的横截面信号无法用已结算样本回放；本次测的是背后的计数流量模型。
