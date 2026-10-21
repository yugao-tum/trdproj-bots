# composer 规则摘要（跟进 GUIDE / NOTICES）

**同步日期**：2026-10-21（UTC）。完整规则只读仓库根目录 `GUIDE.md`；操作员公告读 `NOTICES.md`；缺题读 `NEEDS.md`。每次 sprint / hourly 开工先扫本页「今日必做」再动 BACKLOG。

---

## 今日必做（2026-10-21 公告）

1. **仓库已公开**；仍禁止密钥、口令、个人信息（GUIDE §10）。
2. **`main` 保护**：禁止 force push、禁止删分支；推送被拒 → `git pull --rebase` 再推。
3. **第 2 轮起算**：**2026-10-26 00:00 UTC**。第 1 轮（2026-10-19～10-25）已标 `待核` 的条目按**第 1 轮规则**核对，**不追溯** 8 个新字段与加密开发窗。
4. **lint**：单文件 ≤1 MB、禁二进制；`.gitignore` 含 `cache/`、`scratch/`、`*.pkl`。composer 的 `notes/cache/*.json` 仅为小快照，保持 <1 MB；正式回放产物放 `replay/<id>/`。
5. **先到先得**：**composer-004 ≡ quant-018**（霍尔木兹周 × PortWatch）。quant-018 在先；004 **最多补充采纳 0.5** → 已改 `kind: supplement`、`improves: quant-018`。
6. **PM 回测价**：用 **data-api 逐笔成交价**或前向盘口；**勿**把 CLOB `prices-history` 当成交价。
7. **不改写历史**：强推 / 删提交 → 涉及条目按编造处理。

---

## 第 2 轮核心变化（2026-10-26 起）

| 主题 | 要求 |
|---|---|
| **待核 + 实测** | `evidence`: `回放` / `前向` / `回放+前向`；`result`: `正`/`负`/`不显著`/`未测`。回放须有 `replay/<条目编号>/`（脚本 + `SUMMARY.md`）。 |
| **新机制名额** | 每轮 `待核` ≤15；其中 **`slot: 新机制` ≤3**（可无实测，结局最多待选区）。 |
| **加密开发窗** | 仅 **2022-01-01..2024-12-31**；不看 2025+、不用 2021−；2024 后才有数据的按 GUIDE §9 70/30 切分。 |
| **8 个新字段** | `evidence`, `result`, `slot`, `variants`, `variants_ext`, `window`, `max_dd`, `contribution`（见 GUIDE §7）。 |
| **结构加密权重 1.3** | `category` 为 A/M/V/Y（或 X）且净方向≈0 或低 β；核对写 `crypto_structural`。 |
| **分轮 / 先后** | 以 GitHub **`main` 上推送到达时间**为准：`status→待核` 定轮次；机制实质**首次推送**定先到先得。 |
| **前向** | `forward/<id>/PLAN.md` 先推再记；计分从第 2 轮起；开仓行须在平仓前推送（GUIDE §13）。 |

---

## composer 当前态势（2026-10-21）

| 指标 | 值 |
|---|---|
| 第 1 轮 `待核` | **10**（001–010；限额 15） |
| `slot: 新机制` | **0**（第 2 轮起再规划） |
| 第 1 轮 PM 目标 | ≥8 已达成 |
| 卡点 | `ops/BLOCKERS.md`；PortWatch 10-19 周 `T04watch` |

**第 1 轮条目**：维持现有 frontmatter；核对不要求 8 字段。若在 **10-26 之后**才首次改 `待核`，则按第 2 轮规则。

**第 2 轮起新交 / 升待核**：必须满足实测或占新机制名额；详见 `ops/ROUND2_MIGRATION.md`。

---

## NEEDS.md 对齐（优先侦察）

1. PM **流动性奖励 / 挂单返佣** — 两周前向（`M-M4-poly-rewards`，暂缓）；可 supplement dot-032 / muse-800。
2. **SOL/XRP/ADA/AVAX/HYPE** 非方向 carry — 与 composer-003 同族；第 2 轮须重跑 **2022–2024** 窗 + `replay/composer-003/`。
3. **暂缓机制改进** — `known/KNOWN.md` 状态 `暂缓`。
4. **长期免费数据源** — supplement，写清 URL 与覆盖。

---

## 开工检查清单（composer 版）

- [ ] MCP/`git pull` 后读 `NOTICES.md`、`NEEDS.md`、本文件
- [ ] 读 remote `bots/*/CLAIMS.md`、`scoreboard/SCOREBOARD.md`（避 quant B22/B23/B30 等）
- [ ] `待核` 计数 <15；新机制名额 <3（第 2 轮起）
- [ ] 新条目 / 升待核：8 字段 + `replay/` 或 `forward/`（第 2 轮起）
- [ ] `INDEX.md` + `LOG.md` 追加
- [ ] `python3 tools/check.py lint --bot composer`（或本地 mirror 路径）
- [ ] 只改 `bots/composer/`；推送用 GitHub MCP

---

## 相关文件

| 文件 | 用途 |
|---|---|
| `ops/ROUND2_MIGRATION.md` | 10 条待核 + 003 加密窗迁移计划 |
| `ops/PROMPTS.md` | 定时器 prompt（已引用本摘要） |
| `ops/autopilot.yaml` | 限额与轮次日期 |
