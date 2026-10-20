# quant-012 历史可成交价格回测（data-api 成交 + USGS 基率）

日期：2026-10-20 ｜ 分支：`quant-review/q012-hist` ｜ 脚本：`q012_hist.py`

## 结论先说

- 找到 **68 个已关闭地震计数阶梯事件**：M5.5+ 28 个、M6.5+ 38 个、M7.0+ 2 个。
- 有窗口前成交价的事件 58 个；严格独立结果（同周 5.5/6.5 合并）**35 个有价格、34 个有成交**，样本跨 2026-01 至 2026-10。因此 **历史 ≥30 个严格独立结果是拿得到的**，不需要只靠两周前向记录。
- 已成交 NO 的 **中位已实现毛利 +0.1200/份、净利 +0.1147/份**，命中率 77.7%，合计净利 `+1.1010` / 投入 `78.0863` = **+1.41%**（每个档 1 份，非 100 份仓位）。
- 基率模型对市场的多类 log loss：**模型 1.445508 vs 市场 1.415152，模型更差 0.0304 nats**（29 个配对事件）。按写死准则 2 判 **FAIL**。
- 但该 FAIL **不稳健**：在 25 个“USGS 自算计数与市场结算档一致”的事件上，模型 1.3107 **优于**市场 1.3560；全样本的失败主要由 9 个 M5.5 结算与现行 USGS 目录不一致的事件拉动（M6.5 为 38/38 一致）。
- **正式判定：FAIL**（严格独立数 35 ≥ 30，故不是 INSUFFICIENT；准则 1 通过，准则 2 按全样本点估计不通过）。

## 取到的数据

访问日期均为 **2026-10-20**，全部免费、免密钥。

- Gamma public-search（分页，`events_status=closed`）：`https://gamma-api.polymarket.com/public-search?q=earthquake&limit_per_type=50&events_status=closed&page=N`；另用 `q=magnitude`、`q=earthquakes` 补漏。筛 `slug` 以 `how-many` 开头且含 `earthquake`、`closed=true` 的事件。
- Gamma 事件详情：`https://gamma-api.polymarket.com/events?slug=<slug>`（规则原文、窗口、各档 `conditionId`、`outcomePrices`）。
- data-api 真实成交（已关闭市场可读）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`。字段 `side/price/size/timestamp/outcome`。YES 价 = Yes 成交价，或 `1 - No 成交价`。
- USGS FDSN：`https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2000-01-01&endtime=2026-10-20&minmagnitude={5.4,6.4,6.9}&orderby=time-asc`，再按 `mag≥5.5/6.5/7.0` 过滤（与 entry 的 6.4→6.5 口径一致）。
- 原始下载全部放在 `_cache/`（43 MB，已 `.gitignore`），未入库。

### 事件数量与日期跨度（脚本输出）

| 序列 | 事件数 | 每事件档数 | 窗口跨度 |
|---|---:|---|---|
| M5.5+ | 28 | 6 / 8 / 9 | 2026-04-06 .. 2026-10-19 |
| M6.5+ | 38 | 7 | 2026-01-04 .. 2026-10-12 |
| M7.0+ | 2 | 7 / 9 | 2025-12-04 .. 2026-07-01 |
| 合计 | 68 |  |  |

逐档表见 `buckets.csv`（514 行），逐事件表见 `events.csv`（68 行）。

## 方法（看结果前写死）

1. **决策时点 = 窗口开始时刻**；窗口按规则原文的 ET 边界解析，`endDate 23:59 ET` 加 1 分钟转 UTC 作为开区间终点。
2. **基率模型**：取与事件窗口**同长度**、紧邻窗口开始前的连续窗口，只用窗口开始前的 USGS 数据（2000-01-01 起），数每个历史窗口的 `mag≥阈值` 条数，得到经验分布；每个档加 `0.5` 伪计数后归一化（Laplace 平滑，避免 log(0)）。
3. **可成交价**：`[窗口开始-24h, 窗口开始]` 内最后一笔 data-api 成交，换算成 YES 价；另报“窗口开始后第一笔”的敏感性。没有成交的档标记为空。
4. **交易规则**：沿用 entry 的 1¢ 安全垫，即 `市场YES - 模型YES > 0.01` 才买 NO。执行按吃单：`NO价 = 1 - 市场YES + 0.01`（半价差 1¢），费 `= 0.05 × p_NO × (1-p_NO)`（GUIDE §8，天气类 5%）。持到结算，不主动平仓。
5. **已验证结果**：`payoff_NO` 取市场 `outcomePrices`；毛利 `= payoff_NO - NO价`，净利再减吃单费。**注意：亏损档毛利为负，不是只算票面 1.00−成交价。**
6. **独立结果**：同一 `(window_start, window_end)` 的 5.5 与 6.5 两个事件合并为 1 个严格结果；不合并为宽松结果。
7. **log loss**：每事件用全部档的窗口前市场 YES 价归一化成市场分布，与实际结算档算 `-log p`；模型同理。配对比较，符号检验为双侧二项检验。

## 结果（均从 `run_output.txt` 原样抄录）

### 样本与价格覆盖

```
events with at least one pre-window fill: 58
events with every bracket priced pre-window: 29
independent results: loose=68, strict=40 (strict with prices=35, weekly-only=35, strict with trades=34)
events with non-exhaustive bracket sets: 1
traded NO buckets: 103
USGS own-count vs resolved bracket: 59/68 MATCH (86.8%)
  M5.5+  19/28 MATCH
  M6.5+  38/38 MATCH
  M7.0+  2/2 MATCH
```

### 已成交 NO 的已实现收益

```
median gross/share = +0.1200
median net/share   = +0.1147
mean gross/share   = +0.0186
mean net/share     = +0.0107
hit rate (NO won)  = 80/103 = 77.7%
total net P&L      = +1.1010 on 78.0863 staked = +1.41% per $ staked
pre-window fill age: median 2.36h, max 22.30h before window start
```

中位数为正，但均值只有 +0.0107/份：80 个小赢、23 个大亏（NO 输时亏掉几乎全部权利金），这也是为什么中位准则与均值结论差很多。

### 基率模型 vs 市场（多类 log loss，按事件配对）

```
events compared = 29
mean model log loss  = 1.445508
mean market log loss = 1.415152
median paired (market - model) log loss = +0.012292
model better on 15 events, market better on 14
two-sided sign test p = 1.0000
```

稳健性（脚本输出）：

```
all paired              n=29 model=1.4455 market=1.4152 model_better=15 market_better=14
USGS MATCH only         n=25 model=1.3107 market=1.3560 model_better=12 market_better=13
full bracket coverage   n=28 model=1.3616 market=1.4295 model_better=15 market_better=13
MATCH + M6.5            n=18 model=1.0554 market=1.0605 model_better=7 market_better=11
MATCH + M5.5            n= 7 model=1.9670 market=2.1159 model_better=5 market_better=2
```

全样本判模型更差；但去掉“结算与现行 USGS 计数不一致”的事件后模型更好。符号检验 `p=1.0000`，说明 15:14 的胜负完全不可区分。**准则 2 的 FAIL 是点估计结论，不是统计显著结论。**

### 敏感性：窗口开始后第一笔成交

```
traded buckets = 183
median gross/share = +0.1300
median net/share   = +0.1243
total net P&L      = +36.1969 on 145.5814 staked
```

方向与主结果一致，但成交档数从 103 增到 183，说明很多档在窗口开始前 24h 内没有成交；主结果只覆盖有窗口前成交的子样本。

## 判据与判定

写死失败标准：

1. 已成交 NO 的中位已实现毛利 ≤ 0 ⇒ FAIL。
2. 基率模型 log loss 劣于市场 ⇒ FAIL。
3. 严格独立结果 < 30 ⇒ INSUFFICIENT（不凑数）。

本次：

- 准则 1：中位毛利 `+0.1200` > 0，**不触发**。
- 准则 2：模型 `1.445508` > 市场 `1.415152`，**触发 FAIL**。
- 严格独立结果 `35`（有成交的严格组 `34`）≥ 30，**不是 INSUFFICIENT**。

```
VERDICT = FAIL
```

## 对 gate 6 的意义

entry 的 gate 6 写“不满足：两周只能拿到约 4 个 event”。本次证明：

- 已关闭市场的 **data-api 逐笔成交是可取的**，entry 里“CLOB `prices-history` 返回空 ⇒ 无法回测”的阻塞可以绕开；本次拿到 68 个已关闭阶梯事件、514 个档、103 个可成交 NO 档。
- **历史严格独立结果 35 个（有成交 34 个），已达到 ≥30 的门槛**，时间跨度 2026-01..2026-10。因此 gate 6 的“≥30 独立结果”在历史回测口径下**可以满足**，不必等 15 周前向记录。
- 但“能检验”不等于“策略通过”：本次按写死准则判 **FAIL**，且失败主要来自模型校准而非收益中位数。若要把本条从待选区往前推，应先解决 M5.5 结算口径问题、再用真正的盘口/挂单成交（而非逐笔成交代理）复跑。

## 已知问题与限制

- **逐笔成交 ≠ 完整盘口**：用最后一笔成交价当可成交价，只加 1¢ 半价差，没有深度、滑点和排队；无法还原 maker 挂单的实际成交概率与逆向选择。
- **流动性薄**：514 个档里只有 103 个触发并成交；10 个事件在窗口前 24h 内完全没有成交。窗口前成交距开始的中位时间 2.36h、最大 22.30h，价格可能已过时。
- **USGS 修订 / 结算口径**：自算计数与市场结算档 59/68 一致；**9 个不一致全部是 M5.5**（M6.5 38/38、M7.0 2/2 一致）。不一致例：`april-13-april-19` 自算 9、结算 `>9`；`july-20-july-26` 自算 8、结算 9；`september-14-september-20` 自算 4、结算 7。可能是结算时目录与现行目录的修订差、震级/余震口径差，或市场问题文本与窗口不一致；本次未逐事件定因。
- **一个事件档位不穷尽**：`april-6-april-12` 只有 `3..>9` 八档，缺 0/1/2，且市场问题写“by April 5”与描述窗口不符；其结算为“3”而现行 USGS 计数为 2。该事件保留在成交收益中（保守地计入一笔亏损），但 log loss 对它敏感。
- **基率用的是现行修订后目录**：虽然只取窗口开始前的数据，但目录本身含事后修订，存在轻微前视。
- **吃单 vs entry 的 maker**：entry 只做 maker；本次按任务要求用吃单费 + 1¢ 半价差，结论不能直接等同于 maker 实盘。
- **仓位**：每档按 1 份计算，未套用 entry 的 100 份/档、300 USDT/event、4 event 上限；总收益率对仓位规模不敏感，但绝对金额不是实盘 P&L。
- **M7.0 长窗口**：两个 7.0 事件窗口约 7 个月，且无窗口前成交，未进入交易与 log loss 样本；它们与周度事件在时间上重叠，严格计数时未额外折算相关性。

## 复现与校验

```
cd bots/quant/notes/q012-hist
python3 q012_hist.py | tee run_output.txt
```

从 `_cache/` 重跑：`run_output.txt`、`buckets.csv`、`events.csv` 的 md5 均与首次一致（`md5sum -c` 全部 OK）。

`python3 tools/check.py lint`（在 worktree 根目录）当前因其他 bot 的文件崩溃，输出已存 `lint_output.txt`；错误为 `muse-700/701` 缺字段后 `KeyError: 'id'`，不属于本目录，未改动。
