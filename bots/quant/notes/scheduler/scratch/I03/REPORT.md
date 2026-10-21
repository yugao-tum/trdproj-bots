# quant-021 可成交价复核（I03）：用 data-api 成交替代 prices-history 最后价

访问/计算日期：2026-10-20。仅使用免费、免密钥的公开 GET；无登录、无交易。原始下载在 `_cache/`（已由 `.gitignore` 排除，不入库）。本目录所有数字由 `fetch_gamma.py`、`fetch_ergast.py`、`match_events.py`、`fetch_trades.py`、`analyze_exec.py`、`score_exec.py`、`diag_exec.py`、`extra_checks.py` 生成，stdout 见对应 `run_*.txt`，逐事件表见 `exec_rows.csv` / `exec_diag.csv`。

## 结论

**上一轮把「正收益主要来自 stale 最后成交价」列为首要风险，本轮用 data-api 真实成交复核后，这个解释没有得到支持。**

- 49 个 2024-09..2026-10 的 Winner event 全部取到了 data-api 成交；49/49 都有 cutoff（正赛日 00:00 UTC）之前和之后的 YES 成交，49/49 的首笔赛后（cutoff 后、正赛前）BUY 都发生在正赛开始前。
- 首笔可成交 BUY 相对 prices-history 最后价的平均差 **+0.95¢/份**（中位 +0.85¢，最小 −3.91¢，最大 +4.50¢）；按前 100 份成交的 VWAP 算平均 **+0.86¢/份**（中位 +0.50¢）。
- 上一轮说「真实可成交 ask 要比最后成交价高约 34¢/份，规则 A 的 +0.343/份才会降到 0」——这个 34.1¢ 是**盈亏平衡所需的缺口**，不是实测缺口。本轮实测缺口约 1¢，差了一个数量级。
- 预登记规则 A（杆位差距分档，触发价用最后价）按 data-api 首笔 BUY 成交重算：21 笔，13 胜，合计 **+7.0018**，均值 **+0.3334/份**；按前 100 份 VWAP 重算：合计 **+7.0413**，均值 **+0.3353/份**。与用最后价的 **+7.2107 / +0.3434** 基本同量级。
- **但这不是「edge 已证实」**：样本仍只有 49 个 event（规则 A 21 笔），且杆位差距分档模型在 2024–2026 的 log loss 仍差于常数（见条目证据 2）。本轮只推翻了「stale 价」这一条替代解释，没有把正收益变成显著。

## 数据实际取到

- Gamma 已关闭 F1 event：`events?tag_slug=f1&closed=true&limit=100&offset=0..400`，5 页共 **401 个唯一 event**（`run_fetch_gamma.txt`）。
- 其中标题含 Winner 且排除 Pole/Podium/Sprint/Constructor/Safety/Red Flag/Head 的候选 **50 个**；按 slug/endDate 与 Ergast 正赛日相差 ≤7 天匹配，排除 IndyCar 后匹配 **49 个**，再按 race 去重（同一 race 保留市场数最多的 event）仍为 **49 个**：2024 年 8 场、2025 年 24 场、2026 年 17 场（`run_match.txt`）。与上一轮 49 场清单逐场一致。
- Ergast 兼容接口 `api.jolpi.ca`：2014–2026 排位+正赛，269 场；本轮用正赛 `date` 和 `time` 定义 cutoff 与开赛时刻（`run_fetch_ergast.txt`）。
- data-api 成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=N&takerOnly=true`，49/49 个杆位车手 YES 市场有成交；每个市场按时间倒序分页到覆盖 cutoff 前至少 1 天为止（`run_fetch_trades.txt`）。单市场取得 118–3,000 笔不等；最高的几个市场（如 `2026-6`）取到 3,000 笔后无更多数据，但其最早一笔仍早于 cutoff，故不影响 cutoff 前后的判断。
- 价格对照：`https://clob.polymarket.com/prices-history?market=<YES token>&startTs=<cut-3d>&endTs=<cut>&fidelity=60`，取 ≤cutoff 的最后一点，作为上一轮 `p_hist` 的复现值；49 个值与上一轮表逐场一致（`run_analyze.txt`）。

## 方法（写死，未调参）

1. **cutoff** = Ergast 正赛日 `00:00:00 UTC`；**开赛** = Ergast 正赛 `date + time`（如 `2026-03-08 04:00:00Z`）。只使用 `(cutoff, 开赛)` 之间的成交。
2. **最后价** `p_hist`：CLOB `prices-history` 在 `t ≤ cutoff` 的最后一点（复现上一轮口径）。
3. **可成交价**：
   - `first` = cutoff 之后、开赛之前的第一笔 taker `BUY`（YES token）的成交价；`size` 为该笔份数。
   - `exec20` / `exec100` = 同一窗口内按时间顺序累计到 20 / 100 份 taker BUY 的成交量加权均价（VWAP）。若累计不足 100 份则该字段为空（本轮 49/49 都够 100 份）。
   - 不看 SELL 作为买入价；SELL 只用于判断 cutoff 前最后一笔是买还是卖。
4. **盈亏**：每份净收益 `= y − p − 0.05·p·(1−p) − 0.01`；`y` 取该 Winner 市场 Polymarket `outcomePrices` 的 YES 结算值（1 或 0），不用 Ergast 名次。费用率 0.05、半价差 1¢ 与条目原口径一致。
5. **规则**：完全沿用条目预登记规则 A/B——A 用 2014–2023 拟合的杆位差距分档（0.408/0.458/0.508/0.720/0.333），B 用常数 0.4903；触发条件仍是 `p_hist ≤ p_model − 0.05`，即交易决策只用当时能看到的最后价；成交价分别替换为 `first` / `exec20` / `exec100`。
6. **独立结果**：一个比赛周末算 1 个；49 个 event 即 49 个独立结果。

## 结果

### 1）可成交价 vs 最后价（49 场）

| 口径 | 均值 | 中位 | 最小 | 最大 |
|---|---:|---:|---:|---:|
| `first − p_hist` | **+0.0095** | +0.0085 | −0.0391 | +0.0450 |
| `exec20 − p_hist` | +0.0086 | +0.0050 | −0.0391 | +0.0481 |
| `exec100 − p_hist` | +0.0086 | +0.0050 | −0.0391 | +0.0481 |

cutoff 前最后一笔成交的方向：**BUY 41 场 / SELL 8 场**。若最后一笔是 BUY，说明最后价本身是买方向（ask 侧），下一笔 BUY 相对它的均值是 **−0.29¢**；若最后一笔是 SELL（最后价是 bid 侧），下一笔 BUY 相对它的均值是 **+1.00¢**。把「下一笔 BUY − 最后一笔」当作价差代理，49 场均值 **−0.08¢**、中位 **0.00¢**。也就是说，最后价在大多数场次已经是可买到的价位；即使最后一笔是卖，缺口也只有约 1¢。49 场中最大 `first − p_hist` 为 **+4.50¢**，低于规则 A 的 5¢ 安全垫；没有一场的实测缺口超过安全垫。

### 2）按可成交价重算预登记规则

| 规则 / 成交价口径 | 笔数 | 胜 | 每份净收益合计 | 每份均值 |
|---|---:|---:|---:|---:|
| A，`p_hist`（上一轮） | 21 | 13 | **+7.2107** | **+0.3434** |
| A，`first` | 21 | 13 | +7.0018 | +0.3334 |
| A，`exec20` | 21 | 13 | +7.0111 | +0.3339 |
| A，`exec100` | 21 | 13 | +7.0413 | +0.3353 |
| B，`p_hist` | 23 | 12 | +5.6619 | +0.2462 |
| B，`exec100` | 23 | 12 | +5.4529 | +0.2371 |
| 无条件买每个杆位者，`p_hist` | 49 | 31 | +8.2887 | +0.1692 |
| 无条件买每个杆位者，`exec100` | 49 | 31 | +7.8676 | +0.1606 |

逐笔（规则 A，`exec100`）见 `run_tables.txt`；完整字段见 `exec_rows.csv`。

### 3）盈亏平衡缺口 vs 实测缺口

对规则 A 的 21 笔，把成交价统一加上 `u`，求净收益合计 ≤0 的最小 `u`：**u = 0.341**（34.1¢/份）。本轮实测 `first − p_hist` 均值 0.95¢、`exec100 − p_hist` 均值 0.86¢。**实测缺口约为盈亏平衡缺口的 1/35–1/40**。

这与上一轮的表述不矛盾：上一轮说「要 34¢ 才会归零」是敏感性上界；本轮第一次测出真实缺口，结论是这个上界远未达到。

### 4）容量/深度代理（不是 L2）

- 21 笔规则 A 触发中，cutoff 后、开赛前的 YES taker BUY 总量最小 **1,000 份**，中位 **12,186 份**（全 49 场中位 14,805 份）。
- 21 笔规则 A 触发中，累计到 100 份所需时间中位 **1.20h**、最大 **18.53h**（`2026-5`，该场赛前窗口 20h）；全 49 场 p90 为 2.99h；21/21 都在开赛前累计到 100 份。
- 但首笔 BUY 的 size 中位并不大：21 笔中只有 9 笔首笔 ≥100 份；多数需要分多笔/等待。`exec100` 是「别人已经成交的价格」的 VWAP，**不是我们下 100 份市价单的滑点**。若我们的 100 份与这些买盘同时存在，真实成交价可能更差；历史 L2 深度无公开来源，无法量化。

## 与已合并笔记的关系

- `bots/quant/notes/q006-hist/REPORT.md` 用同一类方法（data-api 成交 + 1¢ 半价差）复核 quant-006 的网球 Elo，结论是 **FAIL**（1366 笔触发，每份净收益中位数 −0.1149）。这说明 data-api 成交价确实能推翻「最后价可成交」的假设；但那是另一个条目/另一个市场，不能直接搬到 F1。
- 本条没有已合并的 F1/data-api 笔记可复用（`bots/quant/notes/` 下只有 batch2-verification、r2prep-verification 两条 quant-021 核对日志，均用 prices-history 最后价），因此按任务要求重新跑了脚本；上一轮的 49 场清单、`p_hist` 与模型值均从 `bots/quant/notes/r2prep-verification/quant-021.md` 逐场对齐后复用。
- `bots/quant/notes/q012-hist/REPORT.md` 是地震计数，与 F1 价格侧无关，未复用。

## 限制（必须与结论一起读）

1. **成交价不是我们的成交价**：data-api 只给历史成交打印，没有历史 bid/ask 深度。`first` 是别人的 taker BUY，`exec100` 是别人成交的 VWAP；我们自己的 100 份需求可能吃掉更多档位。
2. **等待时间**：`first` 可能发生在 cutoff 后数小时（中位 0.49h，p90 1.66h，最大 12.85h）。规则允许「排位后到正赛前」下单，但如果要求 cutoff 时刻立即成交，部分场次的实际可成交价可能更差；本轮用首笔 BUY 是对「立即成交」的保守替代，仍不是同一时点的盘口。
3. **prices-history 与 data-api 不完全一致**：抽样核对 `2024-17` 的 2024-09-14 22:34:34 成交（data-api 0.5081）时，`prices-history fidelity=1` 在 22:35 显示 0.495、22:34 显示 0.485。两者差异约 1–2¢，说明上一轮的 `p_hist` 本身有小时级抽样误差；本轮结论用的是 data-api 原始成交，不受这一点影响，但也说明不能把 `prices-history` 当逐笔成交。
4. **data-api 分页上限**：单市场最多取到约 3,000 笔（本样本中 `2026-6` 等）；49/49 的最早一笔都早于 cutoff，故 cutoff 前后的判断不受影响；更早的历史可能未取全，但不用于本检验。
5. **样本与模型**：49 个 event、规则 A 21 笔，仍不足以把 +0.33/份 当作稳定 edge；杆位差距分档样本外 log loss 0.7236 > 常数 0.6960（条目证据 2），正收益主要来自「杆位者 2024–2026 实际夺冠 31/49 = 0.633」高于市场价 0.443，而不是分档模型的预测力。这个 19 个百分点的差距也可能是 49 场样本的运气。
6. **匹配**：event→race 用日期 ±7 天 + 标题/slug；49 场与上一轮清单逐场一致，但未逐场人工核对每个车手名（用 Ergast `driverId` 末段匹配 `groupItemTitle`，49/49 唯一匹配）。
7. **结算**：y 用 Polymarket 自身 `outcomePrices`，与上一轮一致；Ergast 与 Polymarket 冠军不一致的 8/49 仍存在，原因未查到，本条不使用 Ergast 判胜负。

## 复现

```bash
cd bots/quant/notes/scheduler/scratch/I03
python3 fetch_gamma.py       # -> run_fetch_gamma.txt
python3 fetch_ergast.py      # -> run_fetch_ergast.txt
python3 match_events.py      # -> run_match.txt
python3 fetch_trades.py      # -> run_fetch_trades.txt  (data-api，49 个市场)
python3 analyze_exec.py      # -> run_analyze.txt       (含 prices-history 复现)
python3 score_exec.py        # -> run_score.txt
python3 diag_exec.py         # -> run_diag.txt
python3 extra_checks.py      # -> run_extra.txt
python3 make_tables.py       # -> run_tables.txt, exec_rows.csv
```

`_cache/` 保存 Gamma/Ergast/成交原始 JSON（已 gitignore；其中 `closed_events.json`、`ergast_raw.json` 体积超过 1 MB，复跑时由 `fetch_gamma.py` / `fetch_ergast.py` 重新生成，本轮结束前已删除）；`exec_rows.csv` 与 `exec_diag.csv` 为逐事件结果表。

`python3 tools/check.py lint` 在当前 HEAD 上退出 1：`bots/muse/entries/muse-700-*.md`、`muse-701-*.md` 的既有 frontmatter 缺字段导致 `KeyError: 'id'`，与本任务无关；输出见 `lint_output.txt`。
