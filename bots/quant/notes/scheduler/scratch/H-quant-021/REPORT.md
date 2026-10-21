# quant-021 第二轮硬化（H-quant-021）：修正 Ergast 分页 bug + 可成交价样本外回测

访问/计算日期：2026-10-21。仅使用免费、免密钥的公开 GET；无登录、无交易。原始下载在 `_cache/`（`.gitignore` 已排除，不入库）。本目录所有数字由下列脚本生成，stdout 见同名 `run_*.txt`。

## 结论（先说不好的）

1. **上一轮（I03）的 `fetch_ergast.py` 有分页 bug；R021 的 `build2.py` 复算把同一错误数字（137/269）当成“已复现”。** Ergast 的 `limit=100` 是按“成绩行”分页，一场比赛的结果数组会被切到两页；旧脚本用 `{round: race}` 直接覆盖，保留的是**缺少 P1 的后半页**。表现是 2024 意大利站的杆位被读成 Piastri（实际 Norris）、冠军被读成 Piastri（实际 Leclerc）。
2. 修正后：`150/269 = 0.5576`（旧版被“更正”为 137/269 是错的）；2014–2023 `110/204 = 0.5392`；2024–2026 `40/65 = 0.6154`；2026 单季 `12/17 = 0.7059`。
3. **上一轮所谓“Ergast 与 Polymarket 冠军不一致 8/49”不是数据源冲突，是本条自己的 bug。修正后 49/49 一致。** 因此条目里“两套数据源冲突、原因未查到”的整段必须删掉。
4. 可成交价回测重跑后仍为正，但**比上一轮弱很多**：规则 A 23 笔（不是 21 笔），13 胜，`exec100` 每份净收益 **+0.2003**（上一轮 +0.3353），bootstrap 95% 区间 **[-0.0125, +0.408]**，下界含 0（P(mean≤0)=0.033）。这不是“已证实的 edge”。
5. 新增的横截面证据支持“杆位被低估”是**杆位特有**、不是普遍的冷门偏差：同一价格带 0.10–0.50 内，杆位车手 21 个市场胜率 52.4%（均价 0.347），非杆位 89 个市场胜率 15.7%（均价 0.215）；而“买所有 p≤0.20 的车手”平均每份 **-0.0183**。
6. 容量仍是硬伤：按规则每站 100 份，23 笔合计毛利约 **460.77 USDT**（25 个月），折合约 **221 USDT/年**；相对 5,000 USDT 总资金约 **4.4%/年**，低于 GUIDE 加密条目的 8% 粗算线（本条是 Polymarket，门槛表述不同，但容量必须如实写）。

## 修正的分页 bug（可复现）

旧脚本：

```python
rows.extend(mr['RaceTable']['Races'])          # 每页把该页包含的 race 对象整体追加
...
races = {int(x['round']): x for x in raw[...]}  # 同一 round 出现两次时，后者覆盖前者
```

2024 意大利站的实际页边界（`run_fetch_ergast_fixed.txt` 之前的旧输出，可由 `_cache/ergast_raw.json` 复核）：

```
round 16 results  top: [('1','leclerc','4')]                       # 前半页只有 P1
round 16 results  top: [('2','piastri','2'),('3','norris','1'),...] # 后半页没有 P1
```

旧代码保留后半页，于是 `pole=piastri`、`winner=piastri`。`fetch_ergast_fixed.py` 改为：按 round 合并所有分页、按 `driverId` 去重、保留最小 `position`，再取 P1。复跑输出：

```
2024 qualifying: pages=5 total_rows=479 race_objects=28 unique_rounds=24
2024 results:    pages=5 total_rows=479 race_objects=28 unique_rounds=24
races 269
races with <18 qual or results: 0 []
```

修正后 49 个 PM Winner event 的“Ergast 冠军 vs Polymarket 结算冠军”不一致数为 **0/49**（`run_extra_fixed.txt`）。

## 数据实际取到

- Gamma 已关闭 F1 event：`events?tag_slug=f1&closed=true&limit=100&offset=0..400`，5 页共 **401 个唯一 event**；标题含 Winner/Pole/Podium 的 **149 个 event、3,433 个市场**（本轮重数；`run_verify.txt`）。原始 JSON 27.9 MB，保存在 `_cache/`，不入库。
- Ergast 兼容：2014–2026，**269 场**，每季 19/19/21/20/21/21/17/22/22/22/24/24/17。
- 49 个 Winner event（2024: 8、2025: 24、2026: 17），按 slug/endDate 与 Ergast 正赛日相差 ≤7 天匹配（42 场差 0 天、7 场差 1 天）。
- data-api 成交：49/49 个杆位 YES 市场取到成交，单市场 **212–3,000 笔**；49/49 覆盖 cutoff 前至少 1 天，49/49 首笔赛后 BUY 在开赛前。
- CLOB `prices-history`：每市场 `startTs=cutoff-3d, endTs=cutoff, fidelity=60` 取最后一点；49 个值与上一轮 `p_hist` 的复现值一致口径。

## 方法（写死，未调参）

1. **cutoff** = Ergast 正赛日 `00:00:00 UTC`；**开赛** = Ergast `date + time`。只用 `(cutoff, 开赛)` 之间的成交。
2. **最后价** `p_hist`：CLOB `prices-history` 在 `t ≤ cutoff` 的最后一点。
3. **可成交价**：`first` = cutoff 后第一笔 taker BUY 的价格；`exec20`/`exec100` = 同窗口按时间累计 20/100 份 taker BUY 的 VWAP；都只取 YES token。
4. **盈亏**：每份 `= y − p − 0.05·p·(1−p) − 0.01`；`y` 用 Polymarket 自身 `outcomePrices`；费率 0.05 来自 Gamma `feeSchedule`，半价差 1¢ 是保守假设（历史 L2 无公开来源）。
5. **模型**：只用 2014–2023 拟合。A = 杆位差距分档 Laplace 平滑（[0,0.05) 0.4737、[0.05,0.20) 0.5286、[0.20,0.50) 0.5373、≥0.50 0.7273，训练 n=36/68/65/20）；B = 常数 0.5392（110/204）。触发条件 `p_hist ≤ p_model − 0.05`。
6. **独立结果**：一个比赛周末算 1 个，49 个 event 即 49 个独立结果。
7. **横截面对照**：对 49 个 event 的**全部**车手市场取 cutoff 前价格，按价格分桶看 `y − p`；用于区分“杆位定价错误”与“普遍冷门偏差”。

## 结果

### 1）基率（修正后）

| 区间 | 杆位者夺冠 | 比例 |
|---|---|---:|
| 2014–2023 | 110/204 | 0.5392 |
| 2024–2026 | 40/65 | 0.6154 |
| 2014–2026 | 150/269 | 0.5576 |
| 2026 单季 | 12/17 | 0.7059 |

冠军起步位分布（n=269）：P1 147、P2 63、P3 27、P4–6 21、P7–10 7、P11+ 4。

### 2）样本外模型比较（2024–2026，65 场，不需要价格）

| 预测器 | log loss | Brier |
|---|---:|---:|
| Model A（杆位差距分档，2014–2023 拟合） | **0.6706** | **0.2388** |
| Model B（常数 0.5392） | 0.6781 | 0.2425 |

分档看（样本外）：`[0,0.05)` 4/10=0.400；`[0.05,0.20)` 17/28=0.607；`[0.20,0.50)` 16/21=0.762；`≥0.50` 2/3=0.667。

**诚实解读**：修正后 A 只是**略好于**常数（log loss 差 0.0075），远不足以证明“杆位差距”是有用的预测变量；正收益不依赖 A（B 也正）。上一轮“A 比常数更差”的结论同样是分页 bug 造成的。

### 3）49 个 Winner event：杆位价格 vs 结果

- 杆位车手价格均值 **0.4816**，模型 A 均值 0.5222，实际夺冠 **32/49 = 0.6531**。
- 每场最热门车手：价格均值 0.5217，实际 0.5510，净收益合计 **+0.3736**（每份 +0.0076，≈0）。
- 每场 20–29 个市场在 cutoff 的价格之和：中位 1.042，最小 0.99，最大 1.568；**47/49 ≤ 1.17**，两个为 1.262 / 1.568。
- 按价格分桶：~0.1（n=2）1/2；~0.2（n=6）4/6；~0.4（n=15）7/15；~0.6（n=22）16/22；~0.8（n=4）4/4。

### 4）可成交价回测（规则 A/B，扣 5% 吃单费 + 1¢ 半价差）

| 规则 / 成交价口径 | 笔数 | 胜 | 每份净收益合计 | 每份均值 |
|---|---:|---:|---:|---:|
| A，`p_hist` | 23 | 13 | +4.8046 | +0.2089 |
| A，`first` | 23 | 13 | +4.5862 | +0.1994 |
| A，`exec20` | 23 | 13 | +4.6008 | +0.2000 |
| A，`exec100` | 23 | 13 | **+4.6077** | **+0.2003** |
| B，`exec100` | 23 | 12 | +3.8733 | +0.1684 |
| 无条件买每个杆位者，`exec100` | 49 | 32 | +6.9508 | +0.1419 |

- 实测缺口：`first − p_hist` 均值 **+0.96¢**（中位 +0.85¢，范围 −3.91¢..+4.50¢）；`exec100 − p_hist` 均值 +0.86¢。把规则 A 打到 0 所需的统一加价是 **20.0¢/份**，实测缺口约为其 1/21。
- 上半价差/费率敏感性：fee 7% + half 5¢ 时 A 仍为 **+0.1561/份**；cushion 从 5¢ 降到 0 时 A 为 +0.1850/份（n=26），说明结果不靠 5¢ 安全垫。
- 分年：A 2024 n=4 +0.1784；2025 n=10 +0.1338；2026 n=9 +0.2841。三年都为正，但 2024 只有 4 笔。
- 滚动重拟合（每季只用之前所有赛季）：wfA 三年分别为 +0.1784 / +0.1338 / +0.2841；wfB 为 +0.1784 / +0.0847 / +0.2785。
- **统计强度**：23 笔、均值 +0.2003、sd 0.5204、t=1.85；事件级 bootstrap 95% 区间 **[-0.0125, +0.408]**，P(mean≤0)=0.033。区间含 0。
- 限价单语义（触发价和成交价都用可成交价，`exec100 ≤ model−0.05`）：n=22、+5.1391、+0.2336；少 1 笔，结论不变。

### 5）横截面：杆位是否是“普遍的冷门偏差”？

对 49 个 event 的 1,173 个车手市场，取到 940 个有 cutoff 前价格：

| 价格桶 | n | 均价 | 胜率 | 每份净收益 | 杆位 n | 杆位胜率 | 非杆位 n | 非杆位胜率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [0.00,0.05) | 752 | 0.007 | 0.000 | -0.0169 | 0 | - | 752 | 0.000 |
| [0.05,0.10) | 50 | 0.070 | 0.080 | -0.0028 | 2 | 0.500 | 48 | 0.062 |
| [0.10,0.20) | 48 | 0.137 | 0.104 | -0.0491 | 1 | 0.000 | 47 | 0.106 |
| [0.20,0.30) | 28 | 0.250 | 0.286 | +0.0169 | 5 | 0.800 | 23 | 0.174 |
| [0.30,0.50) | 34 | 0.378 | 0.353 | -0.0470 | 15 | 0.467 | 19 | 0.263 |
| [0.50,0.70) | 24 | 0.600 | 0.667 | +0.0452 | 22 | 0.727 | 2 | 0.000 |
| [0.70,1.01) | 4 | 0.711 | 1.000 | +0.2685 | 4 | 1.000 | 0 | - |

- 0.10–0.50 合并：杆位 n=21、均价 0.347、胜率 0.524、净 +0.1560；非杆位 n=89、均价 0.215、胜率 0.157、净 **-0.0759**。
- “买所有 p≤0.20 的车手”：n=852、9 胜、每份 **-0.0183**；p≤0.30：n=879、17 胜、-0.0171。
- 结论：**不是**“买便宜车手”能赚钱；便宜档整体是负的（市场对冷门略微高估）。正收益集中在“杆位且价格不高”这一小类，符合“排位信息未被完全定价”的机制，而不是 KNOWN 里 `V-V2-poly-longshot` 的普遍冷门偏差。

### 6）容量与年化（必须一起读）

- 23 笔触发中，cutoff 后赛前 YES taker BUY 总量最小 **1,089 份**、中位 **13,669 份**；100 份约占中位买量 0.7%。
- 首笔 BUY 距 cutoff 中位 0.62h、最大 2.99h；累计 100 份中位 1.04h、最大 6.38h；23/23 都在开赛前完成。
- 按每笔 100 份，23 笔毛利合计 **460.77 USDT**（25 个月），约 **221 USDT/年**；相对 5,000 USDT 总资金 **4.4%/年**。资金实际占用只有约 1 天/笔，但机会频率约 11 笔/年，所以放大不了。
- 若把单笔提高到 500 份，毛利约 2,304 USDT（约 22%/年），但**没有历史 L2 深度**，不能假设 500 份能按 `exec100` 成交；本条仍按 100 份写死。

## 来源核对（本轮逐条打开）

| 来源/断言 | 结果 |
|---|---|
| `events?tag_slug=f1&closed=true&limit=100&offset=0..400` → 401 个唯一 event | 200；offset 0/100/200/300 各 100、400 为 1；合 401 |
| 149 个 Winner/Pole/Podium event、3,433 个市场 | 本轮重数一致 |
| 2026 US GP Winner：29 市场、negRisk=true、volume 3,523.28、liquidity 82,670.55、restricted=true | 29/true/restricted 一致；volume/liquidity 为实时值，2026-10-21 已变为 5,296.86 / 约 9.48 万（实时值） |
| 同场 Pole：29 市场、volume 248.79、liquidity 12,211.34 | 29 市场一致；2026-10-21 变为 950.59 / 约 1.24 万 |
| 同场 Podium：23 市场、negRisk=false | 一致；volume 202.69 → 333.10 |
| `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.15}` | 三个 event 全部一致 |
| Winner 结算原文（FIA Final Classification；赛后改判不影响；改期到 Nov 1 后 → Other） | 原文一致 |
| Pole 结算原文（最快排位圈速；后续处罚/发车顺序不影响） | 原文一致 |
| Podium 结算原文（Final Classification 前三；永久取消 → 50-50） | 原文一致 |
| Singapore 2026 Winner：volume 1,131,293.19；Verstappen `["1","0"]` | 一致（volume 1,131,293.185） |
| Ergast 2024 排位 `limit=100` 被压到 100、`total=479` | 一致 |
| `prices-history interval=max` → 200 点 | 一致（200 点） |
| 跨度 15 天 200、20 天 400 `interval is too long` | 20 天 400 一致；15 天 200，2026 新加坡 token 返回 135 点（区间是否有数据取决于 token） |
| `interval=max` 与 `startTs/endTs` 混用会 400 | **错**：返回 200；2026 新加坡 token 14 天区间返回 110 点。“返回空数组”只是特定 token/区间，不是通则 |
| data-api `/trades` 字段 side/price/size/timestamp/asset/outcome | 一致；单市场 212–3,000 笔 |
| `bots/quant/notes/q006-hist/REPORT.md`：1366 笔触发、每份净收益中位 -0.1149 | 原文一致（同方法在网球上 FAIL 的先例） |
| `bots/quant/notes/r2prep-verification/quant-021.md`：3433/2818/146/611,137 点 | 原文一致；本轮未复跑这一项 |
| `bots/quant/notes/q012-hist/REPORT.md` | 地震计数，与本条无关，未复用 |

## 限制

1. **成交价是别人的成交打印**：`first`/`exec100` 都是历史 taker BUY，不是我们的买单滑点；没有历史 L2 深度，无法量化 100 份（更不用说 500 份）会吃掉几档。
2. **样本小且集中**：23 笔、3 个赛季，2024 只有 4 笔；bootstrap 区间含 0。
3. **触发时点**：cutoff 是正赛日 00:00 UTC，不是“排位刚结束”。v3 已用 Ergast `Qualifying.date/time` 逐场核对：49/49 的排位开始 +2h 早于 cutoff（最小余量 0h、中位 8h），所以不存在排位前价格；按排位结束（+2h）用可成交价触发/成交为 21 笔 +0.2539/份，00:00 口径 +0.2003/份。
4. **prices-history 不是逐笔**：`fidelity=60` 是抽样，和 data-api 逐笔有 1–2¢ 差异；本轮结论主要用 data-api，但 `p_hist` 仍是抽样值。
5. **模型 A 的差距口径**：跨 Q1/Q2/Q3 取最快圈，雨天/混条件会失真；`2025-14` 出现负 margin −0.482（已保留在样本里，是一笔亏损交易）。
6. **匹配**：event→race 用日期 ±7 天，未逐场人工核对车手名；49/49 用 `driverId` 末段唯一匹配。
7. 修正分页 bug 后，上一轮所有基于 137/269、0.4903、0.408/0.458/0.508/0.720、+0.3434 的数字都作废；旧 `exec_rows.csv`/`exec_diag.csv` 也不再对应当前 49 个市场。

## 复现

```bash
cd bots/quant/notes/scheduler/scratch/H-quant-021
python3 fetch_gamma.py            # -> run_fetch_gamma.txt
python3 fetch_ergast_fixed.py     # -> run_fetch_ergast_fixed.txt  (修正分页)
python3 match_events.py           # -> run_match_fixed.txt
python3 fetch_trades.py           # -> run_fetch_trades_fixed.txt
python3 analyze_exec.py           # -> run_analyze_fixed.txt
python3 fetch_all_prices.py       # -> run_allprices_fixed.txt
python3 harden_analysis2.py       # -> run_harden_fixed.txt
python3 extra_fixed.py            # -> run_extra_fixed.txt
python3 final_stats.py            # -> run_final_stats.txt
python3 counts_and_ranges.py      # -> run_counts.txt
python3 verify_sources.py         # -> run_verify.txt
```

`_cache/closed_events.json`（27.9 MB）与 `ergast_raw.json`（6.3 MB）超过 1 MB，已在 `.gitignore` 排除，本轮结束前已删除；复跑时由 `fetch_gamma.py` / `fetch_ergast_fixed.py` 重新生成。

## 对条目的建议

历史侧仍为正，但强度不足以称“已证实”：23 笔、均值 +0.20/份、bootstrap 下界 -0.0125。**建议主审按“待选区”处理，而不是直接“收录”**；若要继续，前向至少再补 10 笔并记录我们自己的真实成交价/份数。若主审要求统计显著或年化 ≥8%，本条当前证据不满足（100 份/站时约 4.4%/年）。


## 第三轮复核（v3，2026-10-21，同一 queue item 重跑）

在干净 worktree 重跑本目录脚本，证据 1–6 的 headline 数字逐位复现（`run_v3_analysis.txt`、`run_v3_extra.txt`、`run_v3_cross.txt`）。新增与更正：

1. **排位时点核对（撤掉旧限制 3）**：用 `https://api.jolpi.ca/ergast/f1/{season}.json` 的 `Qualifying.date/time` 逐场核对 49 个 event：`排位开始 +2h` 全部早于回测 cutoff（正赛日 00:00 UTC），最小余量 0h、中位 8h。因此证据 3–5 的价格确实在排位之后，不存在“用排位前价格假装排位后”的前视。见 `run_v3_precheck.txt`。
2. **执行延迟**：把成交起点推迟 1h/3h 后取前 100 份 VWAP，规则 A 仍为 +0.1973/+0.1889（23 笔、13 胜）；`exec100_3h − p_hist` 缺口均值 1.36¢，仍远低于 20¢ 盈亏平衡缺口。见 `run_v3_analysis.txt`。
3. **按规则字面时点（排位结束 +2h）**：可成交价同时触发和成交（`exec100_q ≤ model−0.05`）21 笔、+0.2539/份；最后价触发 + `exec100_q` 成交 38 笔、+0.1562/份。两种都为正；00:00 口径反而更保守。见 `run_v3_extra.txt`。
4. **显著性**：32/49 对 2014–2023 基率 110/204 的二项检验，P(X≥32)=0.0718、双侧 p=0.1436；49 场的高胜率不能说不显著高于基率。见 `run_v3_extra.txt`。
5. **归因检查**：prices-history 最后一点在 cutoff 前 ≤1h（49/49），不是数天前的 stale 点；`run_v3_staleness.txt`。
6. **更正**：data-api 单市场成交数 **212–3,000**（旧稿“122”与 `run_fetch_trades_fixed.txt` 最小值 212 不符）；`interval=max + startTs/endTs` 返回 200 **且有数据**（110 点），“空数组”不是通则。
7. **横截面复算**：1,173 个市场、940 个有价格、分桶与 0.10–0.50 杆位/非杆位对照全部逐位复现；买 p≤0.20 仍为 -0.0183/份。见 `run_v3_cross.txt`。
8. **来源核对**：401 个唯一 event、149 个 Winner/Pole/Podium event、3,433 个市场；三个示例 event 的结算原文、`feeSchedule`、`restricted=true`；Singapore Winner volume 1,131,293.185、Verstappen `["1","0"]`；15 天 200 / 20 天 400；data-api 字段。见 `run_v3_verify_sources.txt`。

复现（v3）：

```bash
cd bots/quant/notes/scheduler/scratch/H-quant-021
python3 fetch_gamma.py && python3 fetch_ergast_fixed.py && python3 match_events.py
python3 v3_fetch_schedule.py
python3 v3_precheck.py
python3 fetch_trades.py
python3 v3_analysis.py
python3 v3_model.py
python3 v3_extra.py
python3 v3_staleness.py
python3 fetch_all_prices.py && python3 v3_cross.py
python3 v3_verify_sources.py
```

`_cache/` 已被 `.gitignore` 排除；`closed_events.json`、`ergast_raw.json` 与 trades 缓存不入库。
