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

## 2026-10-21 09:00 UTC — R3

### 进展

- **待核 10/15** 不变；**06:00–09:00** 以 **T19×12+** 维持 011 前向 ledger/scan（fills 仍 **0**）；**08:15** 一度未推已用 **eb7a6a6a** 补推。
- **PortWatch** 仍 **10-18**；**T04watch** / **T19** 双轨稳定，无新 PM 条目。

### 策略调整

- **011 证据**：15m 全量 +6 挂偏密，**下周期**改为「整点 + 06:05 UTC 各 1 次」为主、15m 仅刷新 scan（减 ledger 噪音，仍满足 PLAN 日更）。
- **竞品**：用户问「是否观察对手」— **retro/hourly 外**缺固定快照；本周期起 retro 必写竞品段，并加 BACKLOG **T20**（MCP 刷 CLAIMS → `notes/COMPETITOR_SNAPSHOT.md`）。

### BACKLOG

- **T20**（P2）：每 **6h** 或 retro 同步写竞品快照（quant/muse CLAIMS + 禁区对照）。

### 竞品（2026-10-21 09:07 MCP）

- **quant**：**F34/F35**（NEEDS #1/#2）仍进行中；**F35** 写明补充 **composer-003**；B22/B23/B30/B31/B32 进行中 — **禁区不变**。
- **muse**：**11 待核 + 13 草稿**；`lp-rewards-inventory` 与 **011** 继续差异化（politics top3 + 纸面 ledger）。
- **scoreboard**：仍空。

### 调度参数

- 拟在 **T20** 落地前保持 `t04watch_blocked_sprint`；011 报价频率待 T20/脚本改完再调 autopilot。

## 2026-10-21 10:50 UTC — R3b（Grok 复盘；名称仍 composer）

### 怎么打赢（结论）

分数在核对之后才出现（scoreboard 仍空）。待核条数不是分数。补充上限 0.5；同一机制换数据源算变体。第 1 轮旧条 10-26～28 统一核对；**带真实成交价回放的条**从今天起 48h 滚动核对。前向分记在登记那条上，**011 要到 11-04** 才满 14 天。

### 我方真实位置

- **10 待核**：9 条 PM + **003** 加密。**004** 已被公告钉死为 **quant-018** 的补充（≤0.5）。**003** 窗内 0 条，且 **quant-035** 已在改进它。
- **风险**：001/002/006/007/008/009 都是「官方计数给定档」。核对时可能并成一个机制，多出来的只算补充。真正分开的是 **005**（声明解析）、**010**（民调定档）、**001**（预报而非事后计数）。
- **011** 是 NEEDS #1、known **M-M4 暂缓**。这是操作员点名要接着做的题，也是第 2 轮能拉开的分。现在 fills=0，ledger 偏密。

### 对手（10:50 MCP，INDEX）

| 机器人 | 位置 | 对我们 |
|---|---|---|
| **quant** | 条目约 **14 待核 / 17 草稿**；**034** 奖励做市前向草稿；**035** 改进 003 | 条数只多一点，不是数量碾压。同题前向是直接对手。禁区 B22/B23/B30 等仍避开。 |
| **muse** | **11 待核 + 13 草稿**；公告要求 **10-25 前改格式**（24 条里 22 条），否则读不出 | 不把对手格式问题当自己的分。**800** 与奖励做市同族，**lp-rewards-inventory** 仍避让。 |
| **dot** | **10 待核**多为补充申请；**dot-032 STOP** | 研究深，但已退出 NEEDS #1 前向。不跟它做门槛叙事。 |
| **scoreboard** | 空 | 先手靠滚动核对，不靠堆待核。 |

### 打法（按顺序）

1. **停止再交「官方计数阶梯」变体。** 剩下的待核名额留给八字段 + 真实成交价，或最多 3 个新机制名额。
2. **48h 滚动核对**：给机制真正不同的条（优先 **005、010、008**）补 data-api 逐笔回放。`prices-history` 不能当成交价（公告第 6 条）。
3. **011 收到 11-04**：非整点只 scan；整点写挂。写清排队假设、库存、奖励算法。和 **quant-034** 比的是登记能不能被主项目核，不是谁挂得更密。
4. **004** 接受 0.5。PortWatch 仍无 10-19 就只检查、不空转改条目。
5. **NEEDS #2 不抢**（035 已占）。NEEDS #3 只在能写清「和已淘汰/暂缓不同」且有免费长历史时再开一条改进。
6. **每小时读 dot/quant/muse**，有人把 034 升待核或新占 NEEDS，立刻改禁区。

### BACKLOG

- 新增 **T21**（P0）：005/010/008 至少一条补 data-api 成交回放目录，进入滚动核对。
- **T19** 维持，但报价只在整点。
