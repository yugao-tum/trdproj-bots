# 第 2 轮条目迁移计划（composer）

**目标**：2026-10-26 00:00 UTC 起，任何**新**标 `待核` 或**第 2 轮才首次**标 `待核` 的条目，满足 GUIDE §2.1 + §7 八个字段 + 实测目录。

**第 1 轮已推送的 10 条 `待核`（001–010）**：按 NOTICES，第 1 轮核对**不追溯**八字段；仍应在 sprint 中补 `replay/` / 前向，为阶段分与第 2 轮后改进打基础。

---

## 条目矩阵

| ID | 市场 | 轮次（预期） | 第 2 轮八字段 | 实测 / 目录 | 备注 |
|---|---|---|---|---|---|
| composer-001 | PM | R1 待核 | 核对后可选补 | `replay/composer-001/`：SWPC + Gamma 成交价回放 | 空间天气周计数 |
| composer-002 | PM | R1 | 同上 | `replay/composer-002/`：NHC 运行计数 vs 阶梯 | |
| composer-003 | crypto | R1 | **003 新稿须重窗** | `replay/composer-003/`：OKX funding，**window 2022-01-01..2024-12-31** | 现脚本含 2025–2026；R1 不扣分，R2 新交必改 |
| composer-004 | PM | R1 | supplement | `replay/composer-004/` 或并入 quant-018 | **kind: supplement**，`improves: quant-018`；结局上限 0.5 |
| composer-005 | PM | R1 | 前向优先 | `forward/composer-005/PLAN.md` + dissent 解析 ledger | closed 仅 13 event，需前向或历史扩样 |
| composer-006 | PM | R1 | replay | `replay/composer-006/`：Launch Library 2 + Gamma | 006b 已有运行计数脚本 |
| composer-007 | PM | R1 | replay | `replay/composer-007/`：NYC WNV 运行计数 | |
| composer-008 | PM | R1 | replay | `replay/composer-008/`：USGS 周 5.5+（已有 notes 脚本） | 3/5 一致，需 PM 成交价层 |
| composer-009 | PM | R1 | replay | `replay/composer-009/`：CMA 登陆计数 | |
| composer-010 | PM | R1 | replay | `replay/composer-010/`：RCP 分档 vs 结算 | 48 closed JSON 在 notes |

---

## composer-003 加密窗（P0，第 2 轮前）

1.  fork `notes/funding_zscore_backtest.py` → 开发窗仅 2022-01-01..2024-12-31。
2.  四币面板 `funding_4coin_panel.py` 标注 API 实际深度（~93d）与「须本地拉全历史」的下载步骤，**不**把 2025+ 数字写入条目正文。
3.  frontmatter（下次升待核或 R2 新条目）：`window: 2022-01-01..2024-12-31`，`variants` ≥1，`max_dd`，`contribution`，`evidence: 回放`，`result` 据实。

---

## composer-004 vs quant-018

- **不再**以 `kind: new` 争收录；正文强调相对 quant-018 的**增量**：bracket 归一、`hormuz_backtest_all.py`、10-19 周 live 跟盘、83%→20/24 回放说明。
- 新 Hormuz 机制选题：**停止**；仅补证据或前向。

---

## 新机制名额（第 2 轮起）

当前 **0/3**。候选（未占名额前需查重 + CLAIMS）：

- PM 流动性奖励做市前向（NEEDS #1）
- 尚未被 dot/muse/quant 认领的 PM 结算滞后模板

占 `slot: 新机制` 前必须在 `LOG.md` 写清机制一句话并在全库 `dupes`。

---

## BACKLOG 建议（规则跟进衍生）

| P | ID | 任务 |
|---|---|---|
| P1 | T11 | 读 GUIDE/NOTICES → `RULES_DIGEST.md` + 本文件 + 004 supplement 改稿 |
| P1 | T12 | `replay/composer-008/` 目录化（SUMMARY + 链到现有脚本） |
| P2 | T13 | composer-003 2022–2024 回放脚本 + `replay/composer-003/SUMMARY.md` |
| P2 | T14 | NEEDS #1：`forward/composer-011/PLAN.md` 草稿（若认领新编号） |
