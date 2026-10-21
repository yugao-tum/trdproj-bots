# H-quant-019：quant-019 真实成交价回放

日期：2026-10-21 ｜ 目标：`bots/quant/entries/quant-019-measles-cdc-count-ladder.md`（`status: 待核`、`date: 2026-10-20` 未改）｜ 工作树：`quant-batch/c20261021-080001-research/w04`

## 结论（2026-10-21 v2 更正，回应 dot 核验）

v1 回放有两处错误，bot `dot` 已指出，本机复核属实：一是按决策之后的成交均价选档（前视）；二是 `fills.csv` 的 market slug 沿用了循环里残留的值，17 行中有 14 行写错。v2 改为因果选档，入场价取决策之后的第一笔成交，并逐档写入正确的 slug。修复后：

| 变体 | 成交/事件 | 投入 | 净额 | 收益率（v1 → v2） |
|---|---|---:|---:|---:|
| YES（条目主张） | 10 / 5 | 2,043.16 | −538.50 | +12.94% → **−26.36%** |
| YES 去掉 2026-07-31 | 8 / 4 | 1,862.34 | −1,135.59 | −19.40% → **−60.98%** |
| NO（镜像） | 7 / 4 | 503.22 | −479.48 | −67.73% → **−95.28%** |
| 费率 0（合计） | 17 | 2,546.38 | −943.22 | −8.96% → −37.04% |

独立结果只有 7 个（按 event 计），少于 30，所以按 GUIDE 字段只能写 `result: 不显著`。但两个变体扣成本后都为负，这是**负结果，作为反证保留**。v1 YES 的正号主要来自 5 月：v1 用事后成交选中了两个赢的档，v2 按当时价格选档，这个事件少赚 794 USDT。完整前后对比见 `SUMMARY.md`，v1 原始输出见 `v1-lookahead/`。

## 文件

- `fetch_events.py` / `fetch_events.stdout.txt` — Gamma 35 个麻疹事件快照（写 `_cache/events.json`，已 gitignore）。
- `replay.py` / `replay.stdout.txt` — 回放；参数：sigma=0.35、edge=0.05、300/档、最多 2 相邻档、费 0.04、seed 19、20,000 路径。
- `verify_sources.py` / `verify_sources.stdout.txt` — 逐条复验条目引用的 URL。
- `fills.csv`、`replay_summary.json` — v2 的 17 笔成交与汇总（每行带自己的 market slug/condition_id、决策时刻与首笔成交）。
- `test_causality.py` / `test_causality.stdout.txt` — dot 合成用例 + 1,750 次真实数据截断测试。
- `v1-lookahead/` — v1（含前视、slug 错）原始输出，仅作对比。
- `bots/quant/replay/quant-019/` — 同一套脚本 + `SUMMARY.md`（canonical replay）。

## 复验出处

- Gamma / data-api 全部 HTTP 200（2026-10-21）；数值与 10-20 快照的差异属正常变动。
- CDC 页面 2026-10-21 从本机 **HTTP 403**（未取到，反爬）；CDC 原文引用已合入的 `bots/quant/notes/batch2-verification/quant-019.md`（2026-10-20 记录 HTTP 200 与原文片段），没有重编。
- 未使用 CLOB `prices-history` 当成交价（NOTICES 2026-10-21 第 6 条）。

## 限制

1. CDC 机读周序列仍未取到，流量只能月频代理，不是每周打印后重算。
2. 条目写于样本结算之后，`2026-06-01` 只是日期切分，不是真正盲测。
3. “两条阶梯互相矛盾”的横截面信号无法用已结算样本回放；本次测的是背后的计数流量模型。
