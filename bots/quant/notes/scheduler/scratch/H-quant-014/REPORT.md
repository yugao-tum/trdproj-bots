# H-quant-014 第二轮硬化报告（2026-10-21）

队列项 H-quant-014，目标条目 `bots/quant/entries/quant-014-pm-spx-lognormal-calibration.md`。
保持文件名、`id: quant-014`、`date: 2026-10-20`、`status: 待核` 不变。按任务要求，本报告只记录新增证据；没有改写未被质疑的原文。

## 1. 复用已合并的回放，不重跑另一套数字

已合并的 `bots/quant/notes/q014-hist/` 就是本条目缺失的可成交价回测，直接复用并逐位复核：

- `bots/quant/notes/q014-hist/REPORT.md`：方法、v2 修复、结论 FAIL。
- `bots/quant/notes/q014-hist/q014_hist.py`：采集 + 回测脚本（303 个 market，243,699 笔 data-api 成交）。
- `bots/quant/notes/q014-hist/run_output.txt`：原始 stdout。
- `bots/quant/notes/q014-hist/events.csv`：303 条逐腿明细。

未重跑采集（原缓存不在工作区；q014-hist 已在 2026-10-21 做过 cache-only 重跑，`verify_v2.txt` 记录 stdout 逐字节一致）。本轮只做**离线复算**和**出处重取**，避免重复抓取 24 万笔成交。

## 2. 本轮新增文件

| 路径 | 内容 |
|---|---|
| `bots/quant/replay/quant-014/replay.py` | q014-hist 采集脚本的 canonical 副本（Gamma + FRED + data-api） |
| `bots/quant/replay/quant-014/events.csv` | 冻结的 303 条逐腿明细（104 KB） |
| `bots/quant/replay/quant-014/summarize.py` | 离线复算：主结果、fee=0、OOS、Brier、贡献 |
| `bots/quant/replay/quant-014/summarize_stdout.txt` | 上述脚本 stdout |
| `bots/quant/replay/quant-014/verify_sources.py` | 逐条重取条目引用的 URL |
| `bots/quant/replay/quant-014/SUMMARY.md` | 按 `templates/REPLAY-SUMMARY.md` 填写的回放汇总 |
| `bots/quant/notes/scheduler/scratch/H-quant-014/verify_sources.py` + `verify_sources_stdout.txt` | 出处复核脚本与 stdout（OK=40 / FAIL=0） |
| `bots/quant/notes/scheduler/scratch/H-quant-014/verify_entry_numbers.py` + stdout | 条目数字与 `summarize_stdout.txt` 交叉核对（0 失败） |
| `bots/quant/notes/scheduler/scratch/H-quant-014/lint_output.txt` | `python3 tools/check.py lint --bot quant` 输出（问题 0 个） |

## 3. 回放关键结果（抄自 `summarize_stdout.txt`）

- 样本：259 event / 303 腿（252 日频 + 2 weekly above + 3 monthly above + 2 monthly close），229 event 触发、240 腿触发；2025-10-15..2026-10-19。
- 全部触发腿：均值 **−0.00743/份**、中位数 −0.14482、总净 **−1.783 份**、每 $1 **−0.0287**。
- 日频 FADE（`|p6−0.5|≥0.10`，194 腿）：毛 +0.02267、净 **+0.00650**、中位数 −0.14482、ISO 周 bootstrap 95% CI **[-0.04872,+0.06235]**。
- 日频 FOLLOW（entry 原方向）：净 **−0.03835**、总净 −7.440。
- 阶梯：monthly above **−0.06948**（9 腿）、monthly close **−0.13662**（7 腿）。
- OOS（2026-07-01..2026-10-19）：全部触发腿 **−0.03452**（72 腿）；日频 FADE −0.02703、FOLLOW −0.00451。
- 校准（252 日频 event）：模型 Brier **0.25000** vs 常数 0.53 **0.24923** vs 市场 p6 **0.17783**；OOS 市场 Brier 0.14319。冻结标准第 3 条命中，**VERDICT: FAIL**。
- 贡献（100 份/触发腿、样本约一年）：fee 0.04 时 −178 USDT → **−3.57%**；fee=0 时 −22 USDT → **−0.43%**。

## 4. 出处复核（`verify_sources_stdout.txt`）

40 项检查全部通过。逐条确认了：

- 日频规则：官方 SPX 收盘、相等判 50-50、WSJ `Historical Prices`、`resolutionSource=https://www.wsj.com/market-data/stocks`、`endDate=2026-10-20T20:00:00Z`、`startDate=2026-10-19T12:00:52Z`。
- 月度阶梯：Yahoo `^GSPC`、正好落档界归上档、6 档、`endDate=2026-12-31T21:00:00Z`。
- NVDA：Pyth 1 分钟收盘、相等判 No、5 档 $210–$230。
- series 10383：100 个已关闭 event，2026-06..09 各 21，10 月 14（2026-10-21 时点；原文 13 是 10-20 快照）。
- CLOB：2026-10-16 token 有历史、2026-09-18 token 返回 `{"history":[]}`；100 个里 22 个非空（原文 21 是 10-20 快照）。
- Yahoo：截到 2021-10-20..2026-10-19 后 1,254 根，首尾 4536.19 / 7690.73，σ₂₀ 0.0904、σ₆₀ 0.1100、σ₂₅₂ 0.1271，上涨日 664/1253，与 entry 逐位一致。
- data-api 逐笔成交字段齐全；stooq 仍是 JS 挑战页；FRED 复核可达。

**时点变化（已写进 entry，不当作原文错误）**：

1. `spx-up-or-down-on-october-20-2026` 已于 2026-10-20 结算（`outcomePrices=["1","0"]`），且这些 SPX finance 市场现在 `feeType=zero_fees`、`feeSchedule.rate=0`；2026-10-20 快照是 0.04。回放仍按 0.04 计，成本取高。
2. 2026-10 已关闭日频 event 从 13 变 14，series volume 变为 $10,718,368.34（原文 $10,779,504.35，均为来源自报）。
3. CLOB 覆盖从 21/100 变 22/100（10-20 收盘后又关闭一个）。

## 5. 对条目的改动

- 8 个第二轮字段：`evidence: 回放`、`result: 负`、`slot: -`、`variants: 5`、`variants_ext: -`、`window: 2025-10-15..2026-10-19`、`max_dd: -`、`contribution: -3.6%`。
- 新增“2026-10-21 第二轮硬化”段和“证据 5）可成交价回放”，把 252 日频 + 7 阶梯的负结果写清楚。
- 修正内部矛盾：
  - 原文“本条没有任何回测收益数字”“`backtest_count` 只能记 21 event” → 改为已有 259 event 可成交价回放、结论为负。
  - 门槛 #2“价格侧不够、只能 21 个历史” → 改为 data-api 已覆盖 259 event，但独立性仍不确定。
  - 门槛 #5“不确定/没有回测收益” → 改为“不满足”，列真实净数。
  - 门槛 #6“约 31 个” → 改为历史 259 event，但两周新增仍只有 10–11 个。
  - 原文“收益只押在阶梯档位” → 明确 7 条阶梯腿也全负，本条是反证。
- 出处：补 data-api、FRED、真实 Sep-18 CLOB token URL，并把 2026-10-21 时点变化写在对应行。

## 6. 七条门槛结论

| # | 门槛 | 结论 |
|---:|---|---|
| 1 | 机制说得清 | **不满足**：回放没有找到正 EV，付钱方未被证据支持 |
| 2 | 有免费数据能检验 | 满足（数量 259 event）/ 不确定（一年、高度相关） |
| 3 | 小资金能做 | 满足（单腿 39–90 USDT，总额 ≤900） |
| 4 | 不重复 | 满足（与 dot-048、quant-008 等不同变量） |
| 5 | 扣成本后够用 | **不满足**：全部触发腿 −0.00743/份，OOS −0.03452 |
| 6 | 两周内能检验 | 历史满足 / 两周新增不足 |
| 7 | 出处可查 | 满足：2026-10-21 重取 40 项全通过 |

**建议：主项目核为退回（反证）**，不要收录，不要占新机制名额。保留价值在于证明“用 0.5 模型打日频 SPX 涨跌/阶梯在真实成交价上不成立”。

## 7. 未解决 / 局限

- 只有 2025-10-15..2026-10-19 约一年；data-api 每个 market 只留最近约 2 万笔，无法补更早。
- 没有历史盘口深度，`ask=成交价+1¢` 是近似，100 份成交概率未量化。
- 阶梯回放固定在结算前 6 小时/前一日，**没有复现 entry 的远端（约 72 天）阶梯主张**；7 条阶梯腿为负只能否掉临近到期吃单。
- 结算源 WSJ / Yahoo `^GSPC` / Pyth 与模型输入 FRED 不完全同源；随机 5 个结算日 5/5 一致，但档界附近仍可能差几分钱。
- 未计 maker rebate、结算滞后资金占用；当前费率为 0，回放按 0.04 计偏保守。
