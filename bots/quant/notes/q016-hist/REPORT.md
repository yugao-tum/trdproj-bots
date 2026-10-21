# quant-016 历史可成交价回测（Wayback 快照 + data-api 成交）

- 分支：`quant-review/q016-hist`
- 数据访问日：**2026-10-21**
- 脚本：`q016_hist.py`；输出：`run_output.txt`；逐 event 明细：`events.csv`
- 全部为免费、免密钥公开 GET；未登录、未下单、未使用任何付费数据。

## 判定

**FAIL**。

- 枚举到 **85 个已关闭 event / 530 个 market**；RT slug 映射 **85/85**。
- 主窗口 `[T−72h, T−12h]` 有可用快照的 event **73 个**；其中 **66 个** 是“既有模型快照、又有窗口内成交”的独立 priced event（≥30，满足样本门槛）。
- 模型 Brier **0.066637** vs 市场 **0.035369**（差 **+0.031268**）；log loss **0.214928** vs **0.121872**（差 **+0.093056**）。模型明显更差。
- 触发 **92 笔**（52 个 event；YES 40 / NO 52）；event 级净损益中位 **−0.113876/份**，均值 **−0.079474/份**；已成交份额毛利中位 **−0.034787/份**，净利中位 **−0.036465/份**；命中率 **9/92 = 0.098**；合计 **−4.132638** / 投入 **12.708319** = 每美元 **−0.325192**。
- 敏感性窗口 `[T−7d, T−24h]` 同样为负：73 个 priced event，103 笔，event 净中位 **−0.104500**，每美元 **−0.232801**；Brier/log loss 仍差于市场。

按条目冻结的失败标准（模型 Brier/log loss 不优于市场，或已成交份额中位毛利 ≤0），两条都触发，判 **FAIL**。

## 数据来源（均为 keyless，访问日 2026-10-21）

- **Polymarket Gamma**（枚举、规则、结算、feeSchedule）：
  `https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false`
  - 返回 **85** 个 closed event、**530** 个 market（累计阈值 **525**、区间写法 **5**）。
  - `endDate` 跨度 **2026-03-02 .. 2026-10-19**；另有 1 个 `endDate=null` 的 `mufasa`，`closedTime=2024-12-23T19:03:39Z`。
  - 阈值市场 `feeSchedule=(rate 0.05, takerOnly true)` 实测 **460** 个；其余按 GUIDE §8 文化板块 **0.05** 处理。
- **RT 页面映射**：`https://www.rottentomatoes.com/search?search=<film title>`（keyless HTML），取完全同名片名、上映年最接近 event 年的结果。85/85 全部映射，无 unmapped。
- **Wayback CDX**（历史快照列表）：
  `https://web.archive.org/cdx/search/cdx?url=rottentomatoes.com/m/<slug>&output=json&from=YYYYMMDDhhmmss&to=YYYYMMDDhhmmss&filter=statuscode:200`
  - 本次 73 个主窗口快照列表全部来自 CDX（输出 `capture-list source={'cdx': 73}`）；CDX 瞬时 503 时脚本按 1 req/s + backoff 重试，并保留 timemap / availability 回退（本次未触发）。
- **Wayback 快照正文**：
  `https://web.archive.org/web/<timestamp>id_/https://www.rottentomatoes.com/m/<slug>`
  从页面内嵌 JSON 解析 `criticsScore`（`likedCount / notLikedCount / reviewCount / score`）。
- **Polymarket data-api 真实成交**：
  `https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&start=<unix>&end=<unix>`
  `outcome="No"` 时 YES 价 = 1 − price；取窗口内最后一笔。
- **结算**：Gamma 各 market 的 `outcomePrices`（`outcomes` 中 `Yes` 的索引）；不另行抓 UMA。
- **Spot check 最终分**：结算后最早的 Wayback 快照 + 当日 live RT 页面（live 可能已漂移，见下）。

## 方法（脚本头已预声明，先于看盈亏）

- **Universe**：Gamma `tag_slug=rotten-tomatoes&closed=true` 全量 85 个 event，不抽样。1 个 event = 1 个独立结果（同片所有阈值共享一次结算）。
- **区间写法**：`mufasa`（`<60 / 60-69 / 70-79 / 80-89 / 90+`）整 event 排除，按条目“明确不做区间写法”；报告为 1 个 range-excluded event、5 个 market。
- **决策时间**：`T` 取自规则原文 `at 10:00 AM ET on <Month D, YYYY>`，按 `America/New_York` 转 UTC（85 个中 84 个解析成功；`mufasa` 无此句，回退 `closedTime`，但已被区间排除）。
- **主快照**：`[T−72h, T−12h]` 内**最晚**的 CDX 200 快照，且 `criticsScore` 可解析、`reviewCount ≥ 1`、`k+m ≥ 1`；若最晚不可解析则在该窗口内向前回退。敏感性窗口 `[T−7d, T−24h]`。无快照的 event 跳过并计数。
- **模型**：`p ~ Beta(k+1, m+1)`；RT 显示 `floor(100p)`，故
  `P(displayed ≥ T) = P(p ≥ T/100) = 1 − I_{T/100}(k+1, m+1)`。
  同一 event 内按阈值升序做保序回归（本次 Beta 后验本身已单调）。
- **“到期无分数”尾部**：快照已有非空 `score` 时，尾部概率**设为 0**；快照有计数但无显示分数时，用条目上界先验 `q0 = 14/85 = 0.16470588235294117`，`P_YES(T) = (1−q0)·P_T`。本次 **73/73** 主快照都有显示分数，故实际全部 `q0=0`，尾部未被触发。
- **可成交价（保守 taker 版）**：`mid` = `[t−6h, t]` 内最后一笔 data-api 成交换算的 YES 价；`ask_yes = mid + 0.01`、`bid_yes = mid − 0.01`；买 NO 价 `= 1 − bid_yes`。条目原提案是 maker；本回测按任务要求测试 **taker-at-touch**，是保守版本。
- **费用**：`fee/share = rate × entry_price × (1−entry_price)`，`rate` 取 market `feeSchedule`，缺省 0.05（GUIDE §8 文化板块）。不计 maker 返佣。
- **触发**：`edge` 相对 `mid` 计；门槛为 `fee + 0.01 半价差 + 0.02 buffer`：
  `P_T − mid > fee(ask_yes)+0.01+0.02` 买 YES；
  `mid − P_T > fee(no_ask)+0.01+0.02` 买 NO；两边都满足取 edge 大者。
- **持有**：到 Gamma 结算，不提前平仓。每档 1 份。`gross = payoff − entry`，`net = gross − fee`。
- **event 结果**：该 event 所有触发档的 `net` 求和（等份）。Bootstrap 按 event 重采样，10,000 次，seed **20261021**。
- **Brier / log loss**：所有 scored threshold；event 级为“先按 event 取均值、再对 event 等权平均”。

## 结果（复制自 `run_output.txt`）

### Universe / 快照

```
closed events enumerated: 85
date span (endDate): 2026-03-02 .. 2026-10-19   (one event has endDate=null, closedTime ['2024-12-23T19:03:39Z'])
markets: 530 (cumulative-threshold markets 525, range-style 5)
feeSchedule (rate, takerOnly) observed: {(0.05, True): 460}
mapped to RT slug: 85/85

Wayback: events with primary snapshot=73  with sensitivity snapshot=80  no primary snapshot (excl. range)=11  range-excluded=1  capture-list source={'cdx': 73}
snapshot lag T-t: median=30.70h min=12.86h max=69.02h
primary snapshots with displayed score: 73/73  (no-display-score snapshots use tail q0=0.164706; with a score q0=0)
snapshot score equals final settlement interval (exact YES-range): 51/73  (all-NO events consistent with below-min: 11/12)
```

无主快照的 11 个（均为窗口内无可用 CDX 200 快照，跳过，不补价）：
`by-any-means`、`fall-2-deadpoint`、`fantasy-life`、`heart-of-the-beast`、`ice-cream-man`、`idiots`、`over-your-live-body`、`sense-and-sensibility`、`super-troopers-3`、`the-dog-stars`、`the-weight`。

### 主窗口 `[T−72h, T−12h]`

```
independent priced events=66  scored thresholds=192
triggered trades=92  events/triggered=52  YES=40  NO=52
median event net/share=-0.113876  mean event net/share=-0.079474
event-cluster bootstrap 95% CI of mean: [-0.168443, +0.017816]
median trade gross/share=-0.034787  median trade net/share=-0.036465  mean trade net/share=-0.044920
hit rate (net>0)=9/92 = 0.098
total net=-4.132638 on staked=12.708319 -> per $ staked=-0.325192
Brier  model=0.066637 market=0.035369 diff=+0.031268
LogLoss model=0.214928 market=0.121872 diff=+0.093056
event-level Brier model=0.070931 market=0.039374  LogLoss model=0.226112 market=0.135803
```

### 敏感性 `[T−7d, T−24h]`

```
independent priced events=73  scored thresholds=218
triggered trades=103  events/triggered=57  YES=49  NO=54
median event net/share=-0.104500  mean event net/share=-0.071619
event-cluster bootstrap 95% CI of mean: [-0.168442, +0.031436]
median trade gross/share=-0.041000  median trade net/share=-0.042966  mean trade net/share=-0.039634
hit rate (net>0)=14/103 = 0.136
total net=-4.082294 on staked=17.535528 -> per $ staked=-0.232801
Brier  model=0.070161 market=0.045723 diff=+0.024439
LogLoss model=0.224015 market=0.149771 diff=+0.074244
event-level Brier model=0.076955 market=0.055868  LogLoss model=0.242717 market=0.177844
```

### Spot check（seed 20261021，3 个随机 event）

1. `the-sheep-detectives`（`/m/the_sheep_detectives`，主快照 `20260508165855`）
   - 归档页 `criticsScore`：`liked=101, notLiked=5, reviewCount=106, score=95`（snippet 见 `run_output.txt`）。
   - Gamma 结算：YES 最高 90、下一档 95 → 最终显示分在 `[90,95)`。
   - 结算后最早快照 `20260516021756`：`liked=153, notLiked=10, reviewCount=163, score=94`；当日 live：`score=95`。
2. `shaun-the-sheep-the-beast-of-mossy-bottom`（主快照 `20260921005214`）
   - 归档页：`liked=61, notLiked=1, reviewCount=62, score=98`。
   - Gamma：YES 最高 95、下一档 100 → `[95,100)`；结算后最早快照 `20260925165938`：`liked=74, notLiked=1, reviewCount=75, score=99`；live：`99`。
3. `tony`（`/m/tony_2026`，主快照 `20260808144617`）
   - 归档页：`liked=77, notLiked=4, reviewCount=81, score=95`。
   - Gamma：YES 最高 95、下一档 96 → `[95,96)`；结算后最早快照 `20260815230829`：`liked=126, notLiked=8, reviewCount=134, score=94`；live：`93`。
   - 说明：结算后快照与 live 都可能因后续评论而漂移，不能把“晚于结算的快照分”直接当作结算时点分；这里只作为核对线索。

## 对 gate 5 / gate 6 的含义

- **gate 5（扣成本后够用）**：**不通过**。保守 taker 口径下，主窗口每美元投入 **−32.52%**，event 净中位 **−0.113876/份**；模型 Brier/log loss 均明显差于市场末笔成交价。条目原先“用 Beta 分布赚把当前分数当最终分数的人的钱”的机制，在历史样本上没有兑现；更符合条目自己列出的最大风险——早期评论不是最终评论的随机样本，快照分与最终结算只有 **51/73** 精确落在同一区间。
- **gate 6（两周内可检验）**：**方法上已解锁，但结果仍是 FAIL**。CDX 快照确实能恢复历史 `(k,m)`，本次拿到 **73** 个有主快照的 event、**66** 个独立 priced event，已经超过 30 的样本门槛；因此不再是“拿不到历史评论数”的问题，而是策略本身未通过冻结的收益/校准标准。按条目规则，不应因“样本够了”升级，仍应停留在待选区/失败。

## 局限

- **Wayback 快照时点偏差（最重要）**：主窗口内取“最晚可用快照”，滞后 `T−t` 中位 **30.70h**、最短 **12.86h**、最长 **69.02h**。模型用的不是结算前最后一刻的评论数；若结算前又进了评论，模型会系统性过期。CDX 覆盖稀疏时只能在窗口内向前回退，进一步加大偏差。
- **快照分 ≠ 结算分**：主快照分精确落入最终区间的只有 **51/73**；11 个全 NO event 快照分低于最低档（一致），另有 **10 个漂移 + 1 个全 NO 但快照分不低于最低档**。这正是条目担心的“早期评论选择偏差”，Beta 抽样噪声覆盖不了。
- **无分数尾部未真正检验**：73/73 主快照都有显示分数，`q0=0` 实际生效；`14/85` 的“到期无数据 → 全 NO”尾部没有在本样本中通过无分数快照触发。14 个非区间全 NO event 多数在快照时已有分数、只是低于最低档；`by-any-means` 等无快照 event 被跳过。
- **成交价不是订单簿**：只有 data-api 成交打印，没有 L2 历史；用最后成交 ±1¢ 近似 taker touch，真实盘口可能更差，且未建模成交量/滑点。条目原提案是 maker，本回测的 taker 版本更保守，但 maker 的排队与逆向选择仍未量化。
- **事件级样本仍集中**：66 个 priced event 中只有 52 个触发；同一部片的所有阈值高度相关，bootstrap 按 event 聚类后 CI 仍宽（主窗口 `[−0.168443, +0.017816]`）。
- **区间写法排除**：`mufasa` 整个 event（5 个 market）未交易/未评分；与条目的“不做区间写法”一致。
- **映射风险**：RT 搜索按“完全同名 + 上映年最接近”选片，仍可能把同名翻拍/纪录片选错；3 个 spot check 的归档页文本与计数一致，未发现错片。
- **结算口径**：只用 Gamma `outcomePrices`，未核 UMA 争议；`floor` 取整按条目实测口径，未再逐 event 重验 RT 的取整实现。
- **CDX 可用性**：本次最终 73 个快照列表全部由 CDX 返回；运行中遇到瞬时 503，靠 1 req/s + backoff 重试成功。若 CDX 长期不可用，脚本会回退 timemap/availability，覆盖可能更稀。

## 复现

```bash
cd bots/quant/notes/q016-hist
python3 q016_hist.py > run_output.txt
```

脚本优先读 `_cache/`（已 gitignore）。本次从缓存连续重跑两次，`run_output.txt` 与 `events.csv` 均逐字节一致：

- `run_output.txt` sha256 `dbfce42c1e03c802eecf3a8e719068e703ea2ba18bf86b97375fdd060058a9fa`
- `events.csv` sha256 `d0e9121aebadb6e5a8872294aef06b38f1e9f15b6ad7e07e99d02083a1628065`

Lint：`python3 tools/check.py lint` 仍因仓库既有 `bots/muse/entries/muse-700-*.md`、`muse-701-*.md` 缺字段而 `KeyError: 'id'`，与本次改动无关；原始输出见 `lint_output.txt`。
