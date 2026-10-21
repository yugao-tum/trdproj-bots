# 定时器 Prompt 模板（subscribe_timer）

## sprint — `composer-15m-sprint`（**主循环，每 15 分钟**）

```
composer 15 分钟冲刺（UTC）。只改 bots/composer/。目标：不空闲，赢比赛。

1) python3 /workspace/trdproj-bots-local/bots/composer/ops/run_cycle.py --sprint
   读输出里的 backlog_pick.task_id — 本轮必须执行该任务（或同等 P0）。
2) 读 ops/BACKLOG.md、ops/BLOCKERS.md；待核数 pending_review，若 ≥15 则只做卡点/证据，不交新条。
3) 执行 1 条 BACKLOG（写条目/脚本/补证据/CLAIMS/INDEX）；GitHub MCP push_files 小步提交。
4) 在 reports/SPRINTLOG.md 追加一行（UTC、任务 ID、动作、commit）；BACKLOG 对应行改 [x]。
5) 不要每 15 分钟骚扰用户聊天；只有出错或完成 P0 条目时可一句话提示。
6) 若 backlog_pick 为空：Gamma 侦察新 PM 模板 → 写入 BACKLOG 并立刻做一条。
```

## hourly — `composer-hourly-brief`（整点汇总）

```
composer 整点简报（UTC）。只改 bots/composer/。

1) python3 .../ops/run_cycle.py --hourly
2) 读 reports/SPRINTLOG.md 自上一小时以来的行 → 汇总
3) 追加 reports/BRIEFINGS.md；聊天给用户 3–6 句中文（含 15m 冲刺进展）
4) list_subscriptions 确认 composer-15m-sprint / hourly / retro 仍有效
5) 整点不重复做 15m 已完成的同一 BACKLOG 任务，除非失败需重试
```

## retro — `composer-retro-3h`

```
composer 三小时复盘（UTC）。只改 bots/composer/。

1) python3 .../ops/run_cycle.py --retro
2) MCP 只读 quant/muse CLAIMS、scoreboard/SCOREBOARD.md
3) 追加 reports/RETROSPECTIVES.md；调整 ops/BACKLOG.md 优先级与 ops/autopilot.yaml
4) push；给用户一段优化结论（中文）
```
