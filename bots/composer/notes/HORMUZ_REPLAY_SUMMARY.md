# Hormuz 周回放摘要（自动生成，2026-10-21）

- **脚本**：`hormuz_backtest_all.py` → 本地 `notes/cache/hormuz_replay.json`（不进仓库）
- **closed 周 event**：26（Gamma 搜索，可能分页不全）
- **可评分**：24（能解析 week_start）
- **PortWatch 7 日累加 vs 结算档**：20/24 一致（83.3%）
- **样例**：2026-09-28 周 sum=19 → 结算 `<20` ✓

不一致多出现在 2026-04/05 档位刻度（如 `25-49` vs 预测 `75-99`），可能为当时 PM 档位结构与现 event 不同，或 PortWatch 事后修订；条目 004 已标 AIS/修订风险。
