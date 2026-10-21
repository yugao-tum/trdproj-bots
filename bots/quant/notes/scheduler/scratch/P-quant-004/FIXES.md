# P-quant-004 fixer changelog

条目：`bots/quant/entries/quant-004-pm-mention-base-rates.md`（keep `status: 草稿`, `date: 2026-10-20`）。
队列：`bots/quant/notes/scheduler/queue.tsv:22`（P-quant-004 / quant-004，prio-quant-004，50，backlog）。
任务：按 reviews/checks 把草稿补成第 2 轮完整候选，加真实可成交价、扣费回放，核来源；明确说是否该淘汰。

## 读过的 reviews / checks / audit

- `bots/quant/notes/scheduler/reviews/c20261020-1423-research.md`：3 处提到 quant-004，均只把 `clob…prices-history?market=<clobTokenId` / `data-api…trades?market=<conditionId` 列为**模板 URL**，不是机制重复；没有 quant-004 专项问题。
- `bots/quant/notes/scheduler/audit/c20261020-1423-research.md`：`quant-004` 只在两处出现——① 404 复核里确认 `rollcall/fool` 的 404 已“在条目里注明失败/不引用”，不算编造；② 查重表判 `quant-005 ↔ quant-004` 不同（总发帖数分档 vs 单词提及）。没有要求改数字。
- `bots/quant/notes/scheduler/checks/` 下 `B22/B23/I02/quant-015/quant-017` 均不含 quant-004；`reviews/c20261020-170337`、`c20261021-060001`、`audit/c20261021-030001` 也没有 quant-004 专项结论。
- 结论：reviews/checks 没有列出 quant-004 的具体错误；真正的缺口是**第 2 轮要求**（真实成交价回放 + 8 个字段 + 可复现材料），以及条目自己承认的“没有证明扣成本后为正”。

## 问题 -> 改了什么 -> 证据

1. **缺少第 2 轮 8 个字段**
   - 改：front matter 增加 `evidence: 回放`、`result: 不显著`、`slot: -`、`variants: 41`、`variants_ext: -`、`window: 2025-03-21..2026-10-19`、`max_dd: 2.6%（按结算日累计已实现，非盯市）`、`contribution: 2.9%`。文件名、`id`、`date`、`status` 未动。
   - 证据：`python3 tools/check.py lint --bot quant`（见下）。

2. **原回测用 CLOB `prices-history` 的中间价/最后价，不是可成交价**
   - 改：新增“证据·补充三（Q04c）”，用 `data-api.polymarket.com/trades` 的**逐笔 taker BUY 成交打印**做成交价；决策时点 `creationDate+2h`，只取此时点之后第一笔打印；成本 `0.04×p×(1−p)` + 0.01/份滑点；单笔名义额封顶到该打印的 `price×size`，并要求 ≥10 USDT。CLOB 只作为历史背景保留在“数据”节，不再作成交价。
   - 证据：`bots/quant/replay/quant-004/backtest.py`、`trades.csv`、`SUMMARY.md`；stdout `backtest.stdout.txt`。
   - 复跑命令：`python3 bots/quant/replay/quant-004/backtest.py`。

3. **没有按真实成交规模给出扣费结果 / 没有年化与回撤**
   - 改：主规则 17 个独立事件，合计 **+131.89 USDT**、胜率 52.9%、t=0.67、最大回撤 **2.60%**（按结算日累计已实现）、年化贡献 **+2.87%**；写进“补充三”“成本与容量”和 SUMMARY。
   - 证据：`backtest.stdout.txt` 第 2 行（thr=0.1, min_n=6, slip=0.01, min_notional=10, cap=True）；`trades.csv` 17 行。
   - 关键对照：同一批机会若**不按打印额封顶**，38 笔会显示 +2,178.02 USDT、年化 +34.29%，但那是把 $100 名义额塞进平均不足 $50 的成交打印，**不可实现**；已明确写为不可用证据。

4. **结果定义为“不显著”，不能写“正”**
   - 改：独立事件只有 17 个（<30），且 t=0.67，按 GUIDE §7 记 `result: 不显著`；`contribution` 仍给数但注明只用于排先后。
   - 证据：`backtest.stdout.txt`；SUMMARY“汇总结果”。

5. **“两周内怎么检验”里的路线 B 还写用 `prices-history` 中间价，与新口径冲突**
   - 改：路线 B 改为“已做第一版：同名历史周命中率代理 + data-api 逐笔打印”，并说明只有 17 个独立事件、仍不到 30，需要补更多同类事件和逐场转录。
   - 证据：条目“两周内怎么检验”与“证据·补充三”一致。

6. **门槛自查与新证据不一致**
   - 改：门 2 从“不确定”改为“部分满足”（成交价已可取自 data-api，但转录词频仍是代理）；门 5 改为“不满足”（+2.9% 年化、t=0.67，低于 8% 粗算线）；门 6 改为“不满足（对 30 个独立结果而言）”；门 7 补上 data-api 与回放材料。
   - 证据：条目“门槛自查”；`backtest.stdout.txt`。

7. **来源复核（2026-10-21）**
   - 改：在“出处”补 3 行（Gamma closed 查询、data-api 成交、回放文件）；`data-api` 段落从“本轮未取”改为“已用于 Q04c”。
   - HTTP 复核：两个 Mentions 合同 PDF 200（124,188 / 105,546 字节，与条目一致）；Gamma closed/false 200；data-api 旧市场 200（832 笔）；CLOB prices-history 该 token 返回 200 但只有 15 字节（空，符合“已关闭市场未必有历史”的旧注）；presidency.ucsb 200（96,161 字节）；fool 索引 200；whitehouse 200；rollcall.com/factbase 200。条目原有的 `factbase/trump/` 404、`fool/.../nflx/` 404 仍按“已尝试、不作为数据源”保留。
   - 证据：`/tmp/q004` 的 requests 复核输出（脚本只读公开 GET）；条目“出处”。

8. **是否该淘汰（直说）**
   - 结论：**按真实可成交规模，本条没有可用的正收益证据，不建议升待核。** 若 2026-11 前拿不出“逐场转录词频 + 真实成交打印 + ≥30 个独立事件”的版本，建议直接 DROP；保留价值只是“历史词频基准率在提及市场不可交易规模上无效”的反证。
   - 证据：17 个独立事件、+131.89 USDT、t=0.67；无容量封顶的 +2,178 不可实现。

## lint

`python3 tools/check.py lint --bot quant` 见运行输出。

## 2026-10-21 w05 复核追加

- 重跑 `bots/quant/replay/quant-004/backtest.py`：主规则复现 17 笔 / +131.89 USDT / t=0.67 / 胜率 52.9% / 回撤 2.60% / 年化 +2.87%；stdout 存 `backtest.stdout.w05-rerun.txt`。
- 发现并修复静默丢单：data-api 偶发非 200 时旧 `trades_for` 直接 `break`，第一次重跑因此只有 16 笔（+115.00、t=0.59）。已加 5 次重试、持续失败抛错，修复后恢复 17 笔。
- 独立算术复核 `verify_replay.py`（不 import 回测脚本）：`arithmetic_mismatches=0`（`verify_replay.stdout.txt`）。
- 敏感性 `sensitivity.py`：去最大 1/2/3 笔后合计 +47.43 / −25.82 / −90.40；bootstrap 95% 区间合计 −251.24..+493.63（`sensitivity.stdout.txt`）。点估计脆弱，维持 `result: 不显著`。
- 来源复核 `verify_sources.py`：PDF 条款 11/11 命中；Gamma 1,317 关闭事件 / 80 周 / 1,315 市场；data-api 旧市场 832 笔；两个 404 仍 404（`verify_sources.stdout.txt`）。实时值有漂移（开盘事件 19、Kansas volume 9507.35、Netflix 闭市后费率 0、presidency 28,405），条目按访问日标注。
- 结论：作为可交易策略 **建议 DROP**；仅作为“小成交规模下历史词频基准率无效”的反证保留，`status: 草稿` 与 `date: 2026-10-20` 未动，8 个第 2 轮字段与 SUMMARY 一致。
