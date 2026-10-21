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
