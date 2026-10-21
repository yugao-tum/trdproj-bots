# H-quant-019：quant-019 真实成交价回放（v2 因果版）

日期：2026-10-21 ｜ 目标：`bots/quant/entries/quant-019-measles-cdc-count-ladder.md`（`status: 待核`、`date: 2026-10-20` 未改）｜ 工作树：`quant-batch/c20261021-130001-research/w06`

## 结论

**不显著、方向为负，建议降为待选区/退回或并入 quant-012。** 7 个已结算月度阶梯、17 笔 data-api 真实成交打印（净化版，v2）：

| 变体 | 成交/事件 | 投入 | 净额 | 收益率 |
|---|---|---:|---:|---:|
| YES（条目主张） | 10 / 5 | 2,043.16 | −538.50 | −26.36% |
| YES 去掉 2026-07-31 | 8 / 4 | 1,862.34 | −1,135.59 | −60.98% |
| NO（镜像） | 7 / 4 | 503.22 | −479.48 | −95.28% |
| 费率 0（合计） | 17 | 2,546.38 | −943.22 | −37.04% |
| 另扣 1¢ 半价差（合计） | 17 | 2,546.38 | −1,284.86 | −50.46% |

- 独立结果 7 个（按 event），< 30，故 `result: 不显著`；但两个方向扣成本后都为负。
- 最大回撤（5,000 USDT，按结算日已实现）：YES 23.76%，NO 9.63%。
- 年化贡献：YES −25.9%，两变体合计 −34.9%（算法见条目“成本与容量”）。
- v1（含前视 + slug 错）曾报 YES +12.94%、NO −67.73%，**已作废**；原始产物在 `bots/quant/replay/quant-019/v1-lookahead/`。

## 文件

- `fetch_events.py` / `fetch_events.stdout.txt` — Gamma 35 个麻疹事件快照（写 `_cache/events.json`，已 gitignore）。
- `replay.py` / `replay.stdout.txt` — v2 回放；参数：sigma=0.35、edge=0.05、300/档、最多 2 相邻档、费 0.04、seed 19、20,000 路径。
- `test_causality.py` / `test_causality.stdout.txt` — 因果性检查（合成用例 + 1,750 次真实数据截断）。
- `verify_sources.py` / `verify_sources.stdout.txt` — 逐条复验条目引用的 URL。
- `fills.csv`、`replay_summary.json` — 17 笔成交与汇总。
- `bots/quant/replay/quant-019/` — 同一套 v2 脚本 + `SUMMARY.md`（canonical replay）。

## 复验（2026-10-21，fixer 重跑）

- 清空缓存重跑 `fetch_events.py` + `replay.py`：`fills.csv` 与仓库版本**逐字节一致**；stdout 复现 YES −26.36%、NO −95.28%、费 0 −37.04%、1¢ 半价差 −50.46%、回撤 23.76%。
- `test_causality.py`：`synthetic_selection_changed=false`、`real_data_truncation_checks=1750`。
- Gamma / data-api 全部 HTTP 200。
- **CDC 页面本次可直接取到**：普通客户端 UA（`python-requests/2.31`）返回 HTTP 200、106,712 字节，4,410/4,392、更新日、周序列说明逐句命中；浏览器 UA 才 403（不是死链）。因此条目里“CDC 403、只引旧记录”的写法已由 fixer 更正。
- data-api 每市场最多 12 页 × 500 = 6,000 笔；条目原写“约 2 万笔”已更正。
- 未使用 CLOB `prices-history` 当成交价（NOTICES 2026-10-21 第 6 条）。

## 限制

1. CDC 机读周序列未提供（只有渲染图），流量只能月频代理，不是每周打印后重算。
2. 条目写于样本结算之后，`2026-06-01` 只是日期切分，不是真正盲测。
3. “两条阶梯互相矛盾”的横截面信号无法用已结算样本回放；本次测的是背后的计数流量模型。
4. 成交模型假设 `side=BUY` 打印的份数我们也能吃到，不考虑排队位置。
