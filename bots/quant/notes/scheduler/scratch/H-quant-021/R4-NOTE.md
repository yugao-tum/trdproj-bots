# R4 复核（2026-10-22，round-2）

未改 `id/date/status`（`quant-021` / `2026-10-20` / `待核`）。

## 做了什么

1. 用全新缓存重跑 `bots/quant/replay/quant-021/verify_sources.py`：
   `run_r4_verify_sources.txt`，**91 PASS / 0 FAIL**。
2. 把 `run_replay.py` 复制到 `/tmp/q021-r4-replay`，用空缓存冷启动重跑：
   `run_r4_replay_repro.txt`；`r4_repro_compare.py` 对比提交版：
   `run_r4_repro_compare.txt`，`primary/bootstrap/per_season/fit/cross_section/variants`
   全部相等，`trades.csv`/`all_events.csv`/`cross_section.csv` 字节一致。
3. 新增变体 **V28**：触发价改为 `cutoff` 前最后一笔 data-api 成交
   （时间戳严格 ≤ cutoff），成交仍为赛后 `exec100`。
   - 22 笔、13 胜、合计 +5.1391、均值 **+0.2336/份**（sd 0.5076、t=2.16）。
   - 与 V07 的 22 笔相同，但 V07 用赛后成交触发（前视），V28 无前视。
   - 相对主规则 23 笔只少 2024-17 阿塞拜疆（主规则最差一笔 -0.5315/份）；
     均值提高来自事后少掉一笔亏损，不能当独立 edge 改善，`result` 仍为
     **不显著**。

## 产物

- `bots/quant/replay/quant-021/run_replay.py`（加 V28、`p_last_trade` 列）
- `bots/quant/replay/quant-021/verify_sources.py`（28 变体 + V28 前视检查）
- `bots/quant/replay/quant-021/results.json`（28 变体）
- `bots/quant/replay/quant-021/all_events.csv`（新增 `p_last_trade`、`p_last_trade_ts`）
- `bots/quant/replay/quant-021/SUMMARY.md`（V28 行与说明）
- 本目录 `run_r4_*`、`r4_repro_compare.py`
