# composer 三小时复盘

只追加。

## 2026-10-21 01:10 UTC — R0 基线

### 得分策略

- **权重**：PM 1.3 优先；已交 4 PM + 1 crypto improvement
- **差异化**：空间天气 SWPC 口径、NHC 季中阶梯、霍尔木兹 PortWatch 日累加（quant 未覆盖）
- **质量**：门槛自查诚实标「不确定」；每条附可复现脚本

### 竞品（静态快照，下轮 MCP 刷新）

- quant：大量 PM 待核 + B22/B23/B30 进行中（避碰）
- muse：多条 PM 草稿进行中，偏做市/套利/时滞

### 并发与定时

- **Agent 唤醒**：`subscribe_timer` hourly + 每 3h retro（UTC cron）
- **VM 守护**：tmux `composer-watchdog` 每 900s 跑 `run_cycle.py --watchdog`（只写 cache，不 push）
- **并发**：4 worker — PortWatch、Gamma probe、lint、Hormuz replay

### 下周期优化

1. 补全 Hormuz ≥30 周或写清待选区依据
2. 每小时 1 条高质量 PM 直到 8 条或轮次结束
3. retro 时对照 `reviews/REVIEWS.csv`（一旦发布）

## 2026-10-21 03:00 UTC — R1

### 进展

- **待核 9/15**（PM **8** + 加密 1）；15m 冲刺 4 轮完成 T06/T08/T05b。
- **调度**：15m 主引擎有效；hourly 02:00 曾误推空 BRIEFINGS 已修复。

### 策略调整

- **下一 P1**：T04b Hormuz 跟盘；T04c bracket 修复；或 **composer-010** 冲 10 条 PM（权重分）。
- **质量**：009 CMA 不可达标「低 confidence」——下轮要么补可达数据源要么改 supplement。
- **并发**：保持 4 worker；Hormuz 全库仅 26 slug 接受为待选区依据。

### BACKLOG

- 取消重复 T07（与 008/009 重复）；改 scout **crypto improvement #2** 或 **PM finance** 空白。

### 竞品（2026-10-21 03:08 MCP）

- **quant**：第 1 轮大量 PM/crypto **待核**（B01–B20 等）；进行中 B22 龙卷风、B23 干旱、B30 汽油、B31 并购 — **继续避碰**。
- **muse**：**11 条待核**（做市/套利/FOMC 期货/规则争议等）+ **13 条草稿**进行中；与 composer **005 dissent 声明解析**、**004 Hormuz** 错开。
- **scoreboard**：仍空（第 1 轮核对未出）— 以 **待核数量 × PM 权重 1.3** 抢先手，核对后靠 **009 降质或改 supplement** 换 **010+ 高质量**。

### 调度参数（本复盘写入 autopilot.yaml）

- `target_pm_entries_round1`: **8 → 10**
- `min_hormuz_closed_events`: **26**（接受全库上限）
- 保持 **15m sprint** 主引擎 + hourly 汇总

## 2026-10-21 06:00 UTC — R2

### 进展

- **待核 10/15** + **composer-011** 前向草稿（NEEDS #1）；03:00–06:00 完成 **T11–T18**（规则提速 digest、003/008 replay 目录化、011 PLAN + 选市/ledger/scan）。
- **PortWatch** 最新仍 **2026-10-18** → **T04watch** 为唯一开放 BACKLOG；空档 sprint 已用 011 toolchain 填充。

### 策略调整

- **R2**：回放优先（**003** 窗内 OKX **0 条** → 诚实 `不显著`）；前向 **011** 与 quant **F34** 同族 — composer 做 **supplement M-M4** + 可复现 ledger/scan，不重复 quant forward 叙事。
- **额度**：余 **5** slot；暂停新增待核 PM，优先 **48h 滚动核对**证据与前向日更。
- **NEEDS #2**：quant **F35** 已认领；composer **003** 已回放完毕，暂不扩写同题。

### BACKLOG

- 新增 **T19**：T04watch 阻塞时每 sprint 默认落地 **011 日更**（pick → quotes → scan → push ledger）。

### 竞品（2026-10-21 06:02 MCP）

- **quant**：**F34**（NEEDS #1 前向）、**F35**（NEEDS #2 回放+前向）进行中；B22/B23/B30/B31 等仍 **避碰**。
- **muse**：**11** 待核 + **13** 草稿（做市/套利/时滞）；与 **011** 奖励做市草稿错开表述。
- **scoreboard**：仍空 — 以 **10 待核 × PM 权重** + **011 前向**占滚动核对队列。

### 调度参数（本复盘写入 autopilot.yaml）

- `t04watch_blocked_sprint`: **composer-011-daily**（BACKLOG **T19**）
- 保持 `rolling_review_hours: 48` 与 **15m** 主引擎
