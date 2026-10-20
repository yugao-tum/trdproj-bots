# quant-010 历史可成交价回测（Netflix 周榜 #1 + data-api 成交）

**结论：FAIL（可成交价历史检验为负；不是 INSUFFICIENT）**

- 主口径（条目自己的 #1 show 模板）：53 个独立 chart-week 簇、82 笔可成交模拟；信号代理命中率 **39.62%**（簇口径），簇中位净收益 **−0.0110/份**，均未达到条目的 80% / >0 门槛。
- 扩展口径（Netflix #1 movie，补全“全部周榜”枚举）：52 个簇、85 笔；命中率 **34.91%**，簇中位净收益 **−0.0110/份**，同样 FAIL。
- “100% 会赢”的上界诊断：买入最终赢家，show 有 **81.33%** 的赢家单净收益 ≤0，movie 为 **87.18%**；条目示例 A 的“吃单即使全赢也亏”在多数事件上成立，但不是每一笔（均值 show +0.0099、movie +0.0014，来自少数低价冷门赢家）。

所有数字均来自本目录脚本 `q010_hist.py` 的 stdout（`run_output.txt`、`run_output_movies.txt`）及它生成的 `events.csv`、`events_movies.csv`。未取到的数据明确写“未取到”。

## 1. 数据来源与访问日期

访问日期均为 **2026-10-20（UTC）**；全部免费、免密钥、无登录、无交易。

| 来源 | URL / 查询 | 结果 |
|---|---|---|
| Netflix Tudum 全球周榜 | https://www.netflix.com/tudum/top10/data/all-weeks-global.tsv | HTTP 200；277 周（2021-07-04 .. 2026-10-18） |
| Netflix Tudum 各国周榜 | https://www.netflix.com/tudum/top10/data/all-weeks-countries.tsv | HTTP 200；277 周；美国 TV/Films 行可用 |
| Gamma 全球 #1 show | https://gamma-api.polymarket.com/events?series_id=10440&closed=true&limit=200 | 53 个 closed events |
| Gamma 美国 #1 show | https://gamma-api.polymarket.com/events?series_id=10772&closed=true&limit=200 | 43 个 closed events |
| Gamma 全球 #1 movie | https://gamma-api.polymarket.com/events?series_id=10441&closed=true&limit=200 | 52 个 closed events |
| Gamma 美国 #1 movie | https://gamma-api.polymarket.com/events?series_id=10775&closed=true&limit=200 | 45 个 closed events |
| Polymarket data-api 成交 | https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N | 200；side/price/size/timestamp/outcome |
| FlixPatrol（Netflix 日榜） | https://flixpatrol.com/top10/netflix/world/ | **HTTP 403**（带 Mozilla UA 仍 403；本目录 `source_check.txt` 记录 5454 bytes）→ Netflix 日榜历史 **未取到** |
| kworb Spotify 日榜 | https://kworb.net/spotify/country/global_daily.html；https://kworb.net/spotify/country/global_daily_totals.html | 200；日榜页只给当前日（2026/10/18），totals 页也只含当前日；未找到可回溯历史日榜的 keyless 归档 → Spotify 未纳入 |

**Spotify 为什么没做**：条目的信号需要“本周逐日累计”。kworb 的 keyless 页面只暴露当前日/当前累计，未提供历史逐日归档；本次检查（2026-10-20）没有取到可回溯的日榜历史，因此按任务要求不纳入，而不是用一个不存在的历史源硬编。Netflix 的 show/movie 两个 #1 系列已经给出 53/52 个独立周，足够做检验。

## 2. 方法（脚本头已冻结，未按结果调参）

详见 `q010_hist.py` 顶部 PRE-DECLARED 段。要点：

- **Universe**：Gamma 两个 show 系列的全部 closed event（#1 global + #1 US），同一 (scope, chart-week) 重复 event 取 volume 最大者；movie 系列用同一管线单独跑，作为“全部周榜”补全。`#2` 与“多少 views”系列不属于 #1 模板，未纳入（series id 见脚本头）。
- **独立结果**：一个 chart-week = 一簇；同周 global + US 合并为一簇（条目自己的独立性规则），簇内两份净收益取平均。show 主口径 53 簇；movie 52 簇。
- **信号（明确标注为代理）**：条目真正的信号是“本周日榜累计 → 官方周榜 #1”，但 Netflix 没有 keyless 的日榜历史（FlixPatrol 403），所以用条目允许的最简单冻结代理：**上一期已发布周榜的同榜 #1 预测本周 #1**；只有当这个实体在当前 event 的候选市场里上市时才交易。模型分布：上一周排名 r=1..10 权重 11−r，未进上一周 Top10 的候选权重 0.1，再归一化。
- **决策时点与价格**：从 Gamma `description` 解析官方更新时间（“<weekday>, <Month D, YYYY>, 3:00 PM ET”），解析不到时用 endDate 当日 15:00 ET（仅 1 个 event）。取 **[T_pub−24h, T_pub]** 内该候选市场最后一条 data-api 成交；`ask = YES成交价 + 0.01`（半个价差）；持有到 Gamma `outcomePrices` 结算。
- **费用**：按 GUIDE §8，`份数 × rate × ask × (1−ask)`；rate 优先用市场 `feeSchedule.rate`，否则 `feesEnabled=false` 记 0（历史市场），再否则用文化类 0.05。另做“全部按 0.05”的敏感性。
- **Brier / log loss**：只在“有决策窗成交价的非 Other 候选”上做多分类；模型与市场在同一子集上归一化。
- **失败标准（条目原文）**：
  - “信号：30 个历史周中，发布前 24h 的 #1 预测命中率 < 80%，判失败。”
  - “成本：前向每笔按‘吃单费 + 半个价差’计，若已成交样本的中位净收益 ≤ 0，判失败。”
  - “若无法取得至少 30 个独立周事件，或无法取得可执行 bid/ask，结论写‘未验证’，不写‘有效’。”
  - 本脚本的操作化：可成交簇 <30 → INSUFFICIENT；否则信号簇命中率 <80% 或簇中位净收益 ≤0 → FAIL；两者都过才 PASS。
- **敏感性**：决策窗改为 12h（同一“最后一条成交”规则）；另报“全部 0.05 费”一档。Bootstrap：按周重采样 10000 次，固定 seed 42。

## 3. 结果（`run_output.txt` 原样）

### 3.1 枚举与漏斗（show 主口径）

```
Gamma closed events by series: global=53, us=43
deduped (scope, chart-week) events: 95
chart-week span: 2025-03-16 .. 2026-10-11 (53 unique weeks)

FUNNEL
  checks with a computed chart week: 95
  skipped prior_no1_not_listed:  2
  skipped fill_too_old:          11
  simulated market-events: 82
  independent chart-week clusters: 53
```

### 3.2 信号代理（条目自己的命中率标准）

```
SIGNAL PROXY HIT RATE (entry's own signal criterion)
  n chart-scope weeks with a prediction: 93 | clusters: 53
  hit rate (events): 0.3871 (36/93) | cluster mean: 0.3962
```

### 3.3 主口径（买代理预测的 #1，按 ask 吃单，持有到结算）

```
PRIMARY ARM (buy proxy's predicted #1 at ask, hold to resolution)
  n market-events: 82 | n clusters: 53
  hit rate (market-events): 0.4268 (35/82)
  hit rate (cluster mean): 0.3962
  net/share: median -0.0110 | mean -0.0032 | cluster median -0.0110 | cluster mean -0.0017
  net per $ staked: median -1.0000 | mean -0.5832
  cluster bootstrap 95% CI of mean net/share: [-0.0083, +0.0099]
  total net: -0.2611 USDC on +35.2453 staked
```

### 3.4 条目价格筛选（p_model − ask − fee − 0.01 > 0）

```
PRICE-FILTER ARM (entry's p_model - ask - fee - 0.01 > 0)
  triggers: 47 market-events | 36 clusters
  net/share: median -0.0115 | mean -0.0121 | cluster median -0.0115
  hit rate: 0.0000
```

代理模型与市场方向相反：能触发价格筛选的，都是市场已定价为“会输”的上一周 #1；47 笔全输。这说明这个代理不是可用的 nowcast。

### 3.5 “100% 会赢”上界（诊断，不是策略）

```
ORACLE DIAGNOSTIC (buy eventual Gamma winner at its ask; 100% win)
  n market-events: 75 | n clusters: 50
  net/share: median +0.0000 | mean +0.0099 | cluster median +0.0000
  net per $ staked: median +0.0000 | mean +0.0126
  share of winners with net<=0: 0.8133
```

### 3.6 敏感性

```
SENSITIVITY 1: decision window 12h instead of 24h
  n market-events: 69 | n clusters: 46
  net/share: median -0.0110 | mean -0.0021 | cluster median -0.0092
  hit rate: 0.4638

SENSITIVITY 2: all-in 0.05 culture fee (ignores historical feesEnabled=false)
  net/share: median -0.0115 | mean -0.0035 | cluster median -0.0115
```

### 3.7 模型 vs 市场

```
MODEL vs MARKET (priced non-Other candidates, multi-class)
  n events: 75 | mean priced candidates/event: 7.92
  Brier model 0.8742 | market 0.0027 | diff(market-model) -0.8715
  logloss model 2.7923 | market 0.0169 | diff(market-model) -2.7754
  model better on Brier: 0/75
```

市场 Brier 接近 0，是因为决策价取的是“发布前 24h 内最后一条成交”，实际常在发布前几分钟；此时市场已基本知道结果。这个对比对市场极有利，不能当作“日榜信号无用”的证据，但说明**可成交时点市场已经有效**。

### 3.8 结算核对

```
SETTLEMENT CHECK (Tudum computed #1 vs Gamma resolved market)
  MATCH=76 | OTHER_NOT_LISTED=6
```

6 个 `OTHER_NOT_LISTED` 是：Tudum 算出的 #1 不在该 event 的候选市场里，Gamma 按规则结算 `Other`；不是 Netflix 数据与 Gamma 的结算冲突，而是**候选覆盖缺口**（这些周买代理候选必输）。movie 另有 1 个标题写法差异（`Grand Theft Auto VI: An Extended Look` vs `Grand Theft Auto VI Extended Look`），属于匹配口径，不是结算源分歧。

### 3.9 扩展：Netflix #1 movie（`run_output_movies.txt`）

```
Gamma closed events by series: global=52, us=45
deduped (scope, chart-week) events: 97
chart-week span: 2025-10-12 .. 2026-10-18 (53 unique weeks)
  simulated market-events: 85
  independent chart-week clusters: 52
  hit rate (events): 0.3474 (33/95) | cluster mean: 0.3491
  net/share: median -0.0110 | mean -0.0086 | cluster median -0.0110 | cluster mean -0.0088
  cluster bootstrap 95% CI of mean net/share: [-0.0117, -0.0063]
  share of winners with net<=0: 0.8718
VERDICT: FAIL
  clusters=52 | signal cluster hit=0.3491 | trade cluster hit=0.3462 | cluster median net/share=-0.0110
```

## 4. 结论

`run_output.txt` 的 `VERDICT: FAIL` 是主口径；`run_output_movies.txt` 的 movie 扩展同样是 `FAIL`。

- 独立簇 53（show）/ 52（movie），都 ≥30，排除 INSUFFICIENT。
- 信号命中率 39.62% / 34.91%，远低于条目的 80%。
- 簇中位净收益 −0.0110/份（show）与 −0.0110/份（movie），均 ≤0。
- 按条目自己的失败标准，**FAIL**。

**重要的解释边界**：这次测的不是条目的“日榜累计 nowcast”，而是唯一能免费回溯的代理“上周 #1 是否连庄”。代理失败不能证明日榜 nowcast 一定失败；但它证明了两件事：(1) 用最简单的历史信号定义，扣可成交成本后是负的；(2) 在发布前最后一条成交的价位上，市场已经把本周结果定价得接近确定（Brier 0.0027），靠“等官方榜发布后收敛”的吃单路径没有空间。

## 5. 对门槛 5 / 6 的含义

- **门槛 5（扣成本后粗算够用）：仍不满足。** 条目示例 A 的“吃单全赢也亏”在历史样本里是多数情形：show 赢家单 81.33% 净 ≤0，movie 87.18% 净 ≤0。只有少数“市场没定价到的冷门赢家”能把均值拉正（show 均值 +0.0099/份），但这不是可事前识别的信号，不能当作策略收益。中位数为 0 或负，按 GUIDE §8 的门槛读法就是不够用。
- **门槛 6（两周内能检验）：从“不确定”变为“可检验，但代理口径结果为负”。** 现在有 53 个 show 周 + 52 个 movie 周的可成交价历史回放，方法可复跑；但条目真正的日榜信号仍无法用 keyless 历史复现（Netflix 日榜历史未取到，Spotify 历史日榜未取到）。因此：
  - 若按“能否用公开数据做至少 30 个独立结果”的字面标准，**可检验性已证明**；
  - 若按“能否验证条目原信号”，**仍不确定**，不能因为这次 FAIL 就宣称日榜 nowcast 无效。
  - 无论哪种读法，都不能把本条从 `待核` 升为“有效”；门槛 5 依旧是硬伤。

## 6. 限制

1. **代理不是原信号**：上周 #1 连庄率约 40%，而条目假设日榜能在发布前锁定冠军；两者信息量差一个数量级。FAIL 主要打的是“可成交价 + 简单历史信号”，不是直接打死日榜 nowcast。
2. **决策价偏晚**：任务口径是“发布前 24h 内最后一条成交”，实际常在 T_pub 前几分钟；市场此时已接近结算，Brier/logloss 对市场极有利。若改成 T_pub−24h 整点价，结果可能不同；本次未事后改口径。
3. **Netflix 日榜历史未取到**：FlixPatrol 2026-10-20 仍 403；没有用它构造信号。
4. **Spotify 未纳入**：kworb keyless 页面只有当前日/当前累计，没有历史逐日归档；未取到可用历史日榜。
5. **成交价不是 L2 盘口**：data-api 最后一条成交 + 1¢ 只是可执行价的近似；没有深度、排队、滑点信息，500 份的真实冲击未知。
6. **历史费用**：旧市场 `feeSchedule=null` 且 `feesEnabled=false`，主口径按 0 费；全按 0.05 的敏感性仍为负。新市场按 `feeSchedule.rate=0.05`。
7. **标题匹配**：用规范化标题 + season/collection 后缀，仍可能有个别漏配；已报告的 6 个 Other 缺口和 1 个 movie 标题差异是真实存在的边界，不是脚本崩溃。
8. **data-api 覆盖**：每个市场最多约 2 万笔；本样本未触及上限，但更早/更热的市场可能取不全。
9. **单 event 1 份**：P&L 是“每份”口径，不是 500 份容量测试；容量、冲击、同时挂 2 个 event 的组合效应未测。

## 7. 复现与检查

```bash
cd bots/quant/notes/q010-hist
python3 q010_hist.py                 # show 主口径，缓存存在时不发网络请求
python3 q010_hist.py --kind movie    # movie 扩展
```

- 缓存目录 `_cache/` 已由本目录 `.gitignore` 排除，不入库。
- 两次 from-cache 重跑的 `run_output.txt`、`run_output_movies.txt`、`events.csv`、`events_movies.csv` 已用 `diff` 验证逐字节一致（diff=0）。
- `python3 tools/check.py lint` 输出保存在 `lint_output.txt`；该命令在 `bots/muse/entries/*.md` 上因缺字段 `KeyError: 'id'` 崩溃（不是本目录文件），崩溃前的输出已原样保留。

## 8. 文件

- `q010_hist.py` — 枚举、抓价、模拟、统计；头部为冻结的预声明。
- `run_output.txt` — show 主口径 stdout。
- `run_output_movies.txt` — movie 扩展 stdout。
- `events.csv` — show 逐事件明细（82 行）。
- `events_movies.csv` — movie 逐事件明细（85 行）。
- `source_check.txt` — 2026-10-20 对 Tudum / FlixPatrol / kworb 的 HTTP 状态与字节数原始记录。
- `lint_output.txt` — `tools/check.py lint` 原始输出。
- `.gitignore` — 排除 `_cache/`、`_data/`。
