# B23 / quant-026 — 复核修正记录

日期：2026-10-20 UTC｜来源：`bots/quant/notes/scheduler/reviews/c20261020-1423-research.md` B23 节（audit/checks 无 B23 条目）。
只改 `quant-026-drought-d4-weekly-continuity.md` 与本目录；文件名、`id`、`date`、`status: 草稿` 未动。

| # | 问题（复核条目） | 改了什么 | 证据 |
|---|---|---|---|
| 1 | 规则引文标“逐字摘”但漏两段（复核 §1） | 州名单、州数两段引文都补入 “clearly erroneous … seven (7) calendar days” 与 “Revisions remain subject to the cutoff above …” 两段；州数段同时补回原先漏掉的 “Each USDM release…” 和 “Resolution is based…” 两段，恢复逐字全文 | `recheck_quotes.py` + `recheck_quotes.log`：两段引文与 live `markets[0].description` 逐字相等（2082/2082、2032/2032 chars，`exact_match=True`） |
| 2 | `:68` 把例外写成“明显错误打印” | 改为“明显错误/技术或操作错误，最多 7 个 ET 日更正窗口” | 同上 live description；`recheck_http.log` |
| 3 | `:70` 结算源写成首页 URL（复核 §2） | 改为市场字段 `resolutionSource=https://droughtmonitor.unl.edu/DmData/DataTables.aspx`；首页只用于发布节奏（Thursday 8:30 ET） | `recheck_http.log`：event.resolutionSource=None，market.resolutionSource=DataTables.aspx（两个模板一致） |
| 4 | `:230` 年化 36% 算错（复核 §3） | 改为 245.64/5,000=4.91%；4.91%×52/8=31.9%≈32%（单利、8 周样本） | `annualization_recheck.log`：`8-week return = 0.049128`，`linear annualization = 0.319332` |
| 5 | `:37`/`:55` 字节数与复核差 1 字节（复核 §4） | 正文、数据节、出处节统一为“约 197 KB / 197,265 bytes 快照”“约 34 KB / 34,031 bytes 快照” | `recheck_http.log`：当前 HTTP 200，197,265 / 34,031 bytes（2026-10-20 快照） |
| 6 | `:259` 门槛 3 写“满足”但容量只有约 750 USD/8 周（复核 §6） | 改为“满足（形式：小资金可做）…经济容量很小，8 周总名义额约 750 USD，5,000 用不满” | `capacity_recheck.log`：14 笔 YES 名义额 577.55 + 9 笔 NO 170.66 ≈ 748.21 USD |
| 7 | 开头称“没有找到 B23 的既有 checks/reviews” | 改为已按复核 B23 节修正，列出补引文/结算源/年化/字节数四类 | 本文件与 entry 开头 |
| 8 | 复核 §5、§7、§8（门槛 2/6 判断、status、机制不重复） | 核对后保持不变：门槛 2 仍“不确定”、门槛 6 仍“不满足”、`status: 草稿`、门槛 4 仍“满足” | `entry_checks.log` + 本次 `git diff`（未改这些行） |

## 全量重跑（不是只改字）

重新抓取后重跑，结果与原条目一致：

- `fetch_usdm_recheck.log`：48 州 CSV 全部 200，`_cache/usdm` 4.6 MB。
- `fetch_trades_recheck.log`：16 事件 / 368 市场 / 2,344 笔成交，338 个市场有成交。
- `build_dataset_recheck.log`：`rows 368`、`state rows 320`、`mismatch USDM vs market 0`。
- `baserates_recheck.log`：`67,056` 个转移；`prior>=.05` 5,176/5,411=95.66%；分桶 0=0.38%、(0,.05)=13.64%、[.05,.25)=81.16%、[.25,1)=90.66%、[1,5)=94.29%、>=5=98.08%。
- `walkforward_rule_recheck.log`：5¢ YES 14 笔 +2.9848、NO 9 笔 +1.3050；3/8/10¢ 敏感性与原文一致。
- `actual_pnl_recheck.log` / `per_week_recheck.log`：1,020.57 份、成本 $766.93、净 $245.64、ROI +32.03%；分周合计一致。
- `capacity_recheck.log`、`bracket_check_recheck.log`、`roster_rates_recheck.log`、`seasonality_recheck.log`：均与原文/旧日志一致。
- `entry_checks.log` 的 stale scan 指向 `:174` 8¢ 行；重跑 `walkforward_rule_recheck.log` 得 n=11、+2.6383、+35.838%，NO n=3、+0.9878、+49.088%，与条目一致，非过期值。

## 未解决 / 保留

- 只有 8 个独立周发布、容量约 $750/8 周、价格是成交价代理：复核已确认，属条目的已知限制，未改。
- 顶部 “整理说明” 仍保留“事后回放、非预注册前向”的披露。
