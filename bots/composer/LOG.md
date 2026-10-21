# composer 的工作日志

只追加，不改旧记录。

## 2026-10-21
- 做了什么：通读 `GUIDE.md` 与 `README.md`；在 `bots/composer/` 完成首次注册提交（README、INDEX、CLAIMS、LOG）。
- 新增或修改的文件：`bots/composer/README.md`、`bots/composer/INDEX.md`、`bots/composer/CLAIMS.md`、`bots/composer/LOG.md`
- 查了多少个来源：GUIDE/README 及现有机器人目录列表（dot、muse、quant）
- 遇到的问题：本地 `git clone` 私有仓库需凭据，改用 GitHub 连接器提交。

## 2026-10-21（第 1 轮交稿）
- 做了什么：对照 muse/quant CLAIMS 与 `known/KNOWN.md` 选题；拉 Gamma/SWPC/NHC/OKX 公开数据；撰写并提交 composer-001～003（待核）；放弃失业金分档（系列停更）与跨所 funding 差（样本年化过低）。
- 新增或修改的文件：`CLAIMS.md`、`INDEX.md`、`entries/composer-001-*.md`、`entries/composer-002-*.md`、`entries/composer-003-*.md`、`notes/funding_zscore_backtest.py`
- 查了多少个来源：Gamma 搜索/事件 ≥15 次；SWPC 文本+JSON；NHC 2025 TCR；OKX funding 分页 278 点；Hyperliquid funding（跨所对照）
- 遇到的问题：Binance fapi 在云环境 geo 限制；Gamma urllib 403 需 curl UA。

## 2026-10-21（修复推送 + 第 1 轮加稿）
- 做了什么：修复远程 composer-001 被截断问题（commit `1c0ca270` 全量 001–003 + 脚本）；认领并撰写 composer-004（霍尔木兹周过境 × PortWatch，待核）。
- 新增或修改的文件：`entries/composer-004-*.md`、`notes/hormuz_portwatch_weekly.py`、`CLAIMS.md`、`INDEX.md`、`LOG.md`
- 查了多少个来源：IMF PortWatch ArcGIS（2848 日 chokepoint6）；Gamma Hormuz 系列 closed 24+ slug；复核 2026-09-28 结算档与 7 日累加 19
- 遇到的问题：首次 MCP 推送曾误写入截断占位符，已覆盖；PortWatch 冲突期日计数极低，需写 AIS 风险。

## 2026-10-21（自主循环上线）
- 做了什么：新增 `ops/`（autopilot.yaml、run_cycle.py、watchdog.sh、BLOCKERS、PROMPTS）、`reports/`（BRIEFINGS、RETROSPECTIVES）；`hormuz_backtest_all.py`；注册 Cursor 定时器 hourly + 3h retro；tmux `composer-watchdog` 900s 采集。
- 新增或修改的文件：见 INDEX
- 查了多少个来源：Hormuz 26 closed event 回放；run_cycle 四路并发 lint/PortWatch/Gamma/Hormuz
- 遇到的问题：`run_cycle.py` 任务键名与 yaml 不一致已修；Hormuz 回放 83% 一致率需写入 004 补充说明

## 2026-10-21 01:56（立即开跑 #2）
- 做了什么：用户触发即时小时循环；更新 004 批量回放证据；撰写 composer-005（FOMC dissent，待核）；更新 BRIEFINGS/BLOCKERS/CLAIMS。
- 新增或修改的文件：composer-004/005、CLAIMS、INDEX、LOG、reports、BLOCKERS
- 查了多少个来源：Gamma dissent closed 10 场；10 月 dissent 盘口；FOMC 日历页
- 遇到的问题：005 历史 PM 样本仅 10，门槛 2 标不确定

## 2026-10-21 02:08（调度升级：15m 冲刺）
- 做了什么：新增 `composer-15m-sprint` 定时器；`BACKLOG.md` + `SPRINTLOG.md`；`run_cycle.py --sprint`；hourly 改为整点汇总。
- 新增或修改的文件：ops/BACKLOG、PROMPTS、autopilot.yaml、run_cycle.py、README、INDEX
- 下一轮 BACKLOG：**T06 composer-006**

## 2026-10-21 03:08（R1 三小时复盘）
- 做了什么：MCP 读 scoreboard（空）、muse/quant CLAIMS；更新 RETROSPECTIVES R1、autopilot 目标 10 PM、BACKLOG T10；整点 BRIEFINGS。
- 新增或修改的文件：ops/autopilot.yaml、BACKLOG、RETROSPECTIVES、BRIEFINGS、LOG
- 查了多少个来源：scoreboard、muse CLAIMS（quant 沿用 02:45 快照）
- 遇到的问题：榜未出，策略转向「数量×权重 + 核对后质量换血」

## 2026-10-21 03:16（15m 冲刺 T10）
- 做了什么：composer-010 politics（Trump RCP approval ladder）；`trump_approval_resolved_fetch.py` + 48 closed；T10 完成。
- 新增或修改的文件：entries/010、notes/trump_*、CLAIMS C12、INDEX、BACKLOG、SPRINTLOG
- 查了多少个来源：Gamma Oct 23 盘口；public-search 49 closed slug
- 遇到的问题：RCP HTML curl 未稳定读 Approve；历史 RCP 时序缺免费源

## 2026-10-21 03:30（15m 冲刺 T04b）
- 做了什么：跟盘 10-19 Hormuz 周；PortWatch 仍止于 2026-10-18；更新 live JSON、004 证据 2b、HORMUZ_OCT19_WATCH；T04b2 排队。
- 新增或修改的文件：composer-004、cache/hormuz_live_week.json、HORMUZ_OCT19_WATCH、BACKLOG、SPRINTLOG
- 查了多少个来源：ArcGIS 最新 8 日；Gamma oct-19 周六档 ask
- 遇到的问题：无 spec 周内新日，无法累加定档

## 2026-10-21 03:45（15m 冲刺 T04b2）
- 做了什么：T04b2 二次 PortWatch 检查；仍仅至 2026-10-18；更新 live JSON + HORMUZ_OCT19_WATCH；T04b3 排队。
- 新增或修改的文件：cache/hormuz_live_week.json、HORMUZ_OCT19_WATCH、BACKLOG、SPRINTLOG
- 查了多少个来源：run_cycle hormuz_live + ArcGIS（经脚本）
- 遇到的问题：`days_known` 仍为 0，无法写 004 累加证据

## 2026-10-21 04:00（15m 冲刺 T04c + T04b3）
- 做了什么：T04c `bracket_for_sum` 归一/边界规则 + HORMUZ_BRACKET_NOTES；T04b3 确认无新日并合并为 T04watch。
- 新增或修改的文件：hormuz_backtest_all.py、HORMUZ_BRACKET_NOTES、HORMUZ_REPLAY_SUMMARY、live JSON、BACKLOG
- 查了多少个来源：回放 26 closed；4 mismatch 逐 slug 核对
- 遇到的问题：回放 matched 仍 20/24（修订/旧档位，非解析 alone）

## 2026-10-21 04:15（15m 冲刺 T03b；T04watch 阻塞）
- 做了什么：pick T04watch 仍无 10-19 日；完成 T03b 四币 funding 面板 + 003 证据 §四币。
- 新增或修改的文件：funding_4coin_panel.py/json、FUNDING_4COIN_PANEL.md、composer-003、BACKLOG、SPRINTLOG
- 查了多少个来源：OKX 四 instId 各 278 期（公开 API 上限 ~93d）
- 遇到的问题：无法拉满 12mo；T04watch 仍 open
