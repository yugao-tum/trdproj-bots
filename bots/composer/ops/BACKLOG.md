# composer 任务队列（15 分钟冲刺用）

优先级 **P0 > P1 > P2**。每轮 `--sprint` 只做 **1 条**；完成后标 `[x]` 并写 `reports/SPRINTLOG.md`。

| P | ID | 状态 | 任务 | 完成标准 |
|---|---|---|---|---|
| P0 | T06 | [x] | 认领并交 **composer-006**（PM，未覆盖模板；避 quant B22/B23/B30） | CLAIMS + 待核条目 + INDEX + push |
| P0 | T08 | [x] | 待核 PM 条数 **≥8**（第 1 轮目标） | INDEX 计数 |
| P1 | T05b | [x] | **005 补充**：拉 closed dissent slug ≥20 并写入 `notes/dissent_resolved.json` | 仅 13 closed；脚本+摘要已交 |
| P0 | T10 | [x] | **composer-010** PM（finance/politics 空白；muse 未覆盖） | composer-010 politics 待核 |
| P1 | T04b | [x] | **004 补充**：跟 10-19 Hormuz 周 PortWatch 新日 → `notes/cache/hormuz_live_week.json` | 03:30 仍无 10-19 日；已跟盘+004 §2b |
| P1 | T04b2 | [x] | **004 续跟**：PortWatch ≥2026-10-19 落库后更新 live JSON + 004 累加 | 03:45 仍无新日；watch 已更 |
| P1 | T04b3 | [x] | **004 续跟**：PortWatch ≥2026-10-19 落库后更新 live JSON + 004 累加 | 04:00 仍无；合并 T04watch |
| P1 | T04watch | [ ] | **004 跟盘**：PortWatch≥10-19 落库 → live JSON + 004 累加节 | `days_known`≥1（sprint 自动查） |
| P1 | T07 | [x] | ~~composer-007~~（已由 007–009 覆盖） | 取消 |
| P2 | T04c | [x] | Hormuz bracket 映射修复（提高回放一致率） | 解析归一+边界规则；20/24；见 BRACKET_NOTES |
| P2 | T03b | [x] | OKX 四币 12mo funding 面板（补 003 样本） | 四币 JSON+面板；API ~93d/币 |
| P2 | T06b | [x] | **006 补充**：10 月 SpaceX Success 运行计数脚本 + 006 续证 | LL2 8 Success / 上界 11 |
| P2 | T08b | [x] | **008 补充**：USGS M5.5+ closed 周回放脚本 + 008 证据 | 5 周 3/5；见 REPLAY md |
| P1 | T11 | [x] | **规则跟进**：GUIDE/NOTICES → RULES_DIGEST + ROUND2_MIGRATION；004→supplement quant-018 | BLOCKERS B6/B7；PROMPTS/autopilot/README |
| P1 | T12 | [x] | **008 replay 目录化**：`replay/composer-008/` + SUMMARY.md | 链到 usgs_weekly_55_replay.py |
| P0 | T13 | [ ] | **003 加密窗**：2022–2024 funding 回放 + replay/composer-003 + 8 字段升待核（R2） | 滚动 48h + 结构快车道 |
| P0 | T14 | [ ] | **NEEDS #1**：今日推 `forward/composer-011/PLAN.md` + CLAIMS | 登记 → 2026-11-04 满 14 天 |
| P1 | T15 | [x] | **提速公告跟进**：NOTICES 10-21（三）→ RULES_DIGEST / BLOCKERS / autopilot | 文档与配置同步 remote GUIDE §4 |

**选题禁区**：quant 进行中 B22/B23/B25/B29/B30/B31；muse 进行中 PM 草稿同机制。
