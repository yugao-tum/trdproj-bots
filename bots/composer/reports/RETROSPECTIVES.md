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
