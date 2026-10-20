# quant-020 前向复核（预注册）

- 冻结规则：`0.40 ≤ p_24h ≤ 0.55` 吃单买 YES；`p_24h` 取 `[endDate−72h, endDate−24h]` 最后一笔 data-api 成交，入场价 `p_24h + 0.01`，费率 0.05。
- 窗口：只看 `endDate ∈ [2026-10-21T00:00Z, 2026-10-26T00:00Z)` 的事件；复用 `../q020-oos/q020_oos.py` 的逻辑，不修改该文件。
- 失败判据 = HOLDOUT 判据：带内事件 ≥30 时，净 PnL/份中位 ≤0 或 YES 率 ≤ 平均入场价；不足 30 判 INSUFFICIENT。
- 运行：`python3 bots/quant/notes/q020-forward/q020_forward.py`；窗口内事件未全部结算时只打印计数与 `PENDING`，不出判定。
- 请在 2026-10-26 之后、窗口内事件全部结算后再运行；本次运行结果见同目录 `run_output.txt`。
