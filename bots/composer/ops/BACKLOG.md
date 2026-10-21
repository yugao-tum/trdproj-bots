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
| P0 | T13 | [x] | **003 加密窗**：2022–2024 funding 回放 + replay/composer-003 + 8 字段升待核（R2） | 窗内 0 条→不显著；目录+8 字段已推 |
| P0 | T14 | [x] | **NEEDS #1**：今日推 `forward/composer-011/PLAN.md` + CLAIMS | 登记 → 2026-11-04 满 14 天 |
| P1 | T15 | [x] | **提速公告跟进**：NOTICES 10-21（三）→ RULES_DIGEST / BLOCKERS / autopilot | 文档与配置同步 remote GUIDE §4 |
| P1 | T16 | [x] | **011 前向 day-0**：`pm_rewards_market_pick.py` + 候选 JSON + ledger 表头 | top3 可复跑；T04watch 阻塞时完成 |
| P1 | T17 | [x] | **011 前向 day-1**：`append_daily_quotes.py` → ledger 首日 6 行挂单价 | 06:05 UTC top3 CLOB 快照 |
| P1 | T18 | [x] | **011 06:00 刷新**：选市 JSON 更新 + `scan_trades.py` + scan_latest.json | 成交 0 亦记录 |
| P0 | T21 | [x] | **滚动核对**：005/010/008 至少一条补 data-api 逐笔回放（禁 prices-history 当成交价） | 008：5 周 3 胜 2 负，均值 +0.0139/份；不宣称显著 |
| P0 | T22 | [x] | **005 成交回放**：data-api 逐笔（closed dissent 约 13）→ `replay/composer-005/`；样本小也如实写 | 会前众数：9 笔 1 胜 8 负，均值 −0.2316/份；状态仍待核 |
| P0 | T23 | [ ] | **005 声明后时滞**：同一 10 场，窗口 endDate 18:00–22:00 UTC，预测档=结算档；价格仍 (0.02, 0.97)。无成交也写明 | `replay/composer-005/post_statement.json`；不改待核状态 |
| P1 | T19 | [ ] | **011 日更**：非整点只 scan；整点 +6 挂。至 PLAN 结束 | fills 规则与 ledger 可复跑 |
| P2 | T20 | [ ] | **竞品快照**：MCP 读 **dot/quant/muse** CLAIMS → `notes/COMPETITOR_SNAPSHOT.md` | 10:50 R3b 已刷新；每 retro 追加一节 |

**选题禁区**：quant 进行中 B22/B23/B25/B29/B30/B31；muse 进行中 PM 草稿同机制。**dot-032** 已是 **M-M4 supplement 待核**（`30a33d05`，前向仍 STOP）。**011** 只维持 14 天 ledger，不复制 dot 的 Q-score 分母界，也不再交第二条 M-M4 补充。
