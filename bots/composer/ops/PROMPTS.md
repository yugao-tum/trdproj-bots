# 定时器 Prompt 模板（subscribe_timer）

## hourly — `composer-hourly-brief`

```
composer 小时报循环（UTC）。严格只改 bots/composer/。

1) 在 VM 运行：python3 /workspace/trdproj-bots-local/bots/composer/ops/run_cycle.py --hourly
2) 读 ops/BLOCKERS.md，能自动修的在本轮修（条目/脚本/索引）；需推送的用 github-official push_files（yugao-tum/trdproj-bots main），小步 commit 说明 [composer] ...
3) 在 reports/BRIEFINGS.md 追加一节（UTC 时间、待核条目列表、本轮数据/提交、卡点、下小时计划）
4) 在聊天给用户 3–6 句中文简报（要点，不贴长日志）
5) list_subscriptions 确认 composer-hourly-brief 与 composer-retro-3h 仍有效
6) 若待核 <15 且有好题：认领 CLAIMS → 研究 → 新 待核 条目（PM 优先，不编造）
```

## retro — `composer-retro-3h`

```
composer 三小时复盘（UTC）。只改 bots/composer/。

1) python3 /workspace/trdproj-bots-local/bots/composer/ops/run_cycle.py --retro
2) MCP 读 bots/quant/CLAIMS.md、bots/muse/CLAIMS.md、scoreboard/SCOREBOARD.md（只读）
3) 在 reports/RETROSPECTIVES.md 追加：竞品变化、得分策略、选题队列、并发/定时参数是否要改 ops/autopilot.yaml
4) 若需调参，改 autopilot.yaml 并 push；给用户一段优化结论（中文）
5) 更新 ops/BLOCKERS.md 优先级
```
