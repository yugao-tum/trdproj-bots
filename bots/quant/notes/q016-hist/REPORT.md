# quant-016 历史可成交价回测（Wayback 快照 + data-api 成交）

- 分支：`quant-review/q016-hist`
- 数据访问日：**2026-10-21**
- 脚本：`q016_hist.py`；v2 输出：`run_output.txt`；v1 输出（保留）：`run_output_v1.txt`；逐 event 明细：`events.csv`（v1 对照：`events_v1.csv`）
- 全部为免费、免密钥公开 GET；未登录、未下单、未使用任何付费数据。
- **2026-10-21 v2 修复**：下面“判定 / 结果 / 局限”是 v1 原始内容（保留）；两处 PR #18 review 修复、v1 vs v2 数字和修订后的映射/缓存审计见文末 **“v2 修复”**。v1 的 **FAIL** 结论不变。

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

## 结果（v1；复制自 `run_output_v1.txt`）

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

- v1 `run_output_v1.txt` sha256 `dbfce42c1e03c802eecf3a8e719068e703ea2ba18bf86b97375fdd060058a9fa`
- v1 `events_v1.csv` sha256 `d0e9121aebadb6e5a8872294aef06b38f1e9f15b6ad7e07e99d02083a1628065`
- v2 输出与审计的校验和见文末 **“v2 修复”**。

Lint：`python3 tools/check.py lint` 仍因仓库既有 `bots/muse/entries/muse-700-*.md`、`muse-701-*.md` 缺字段而 `KeyError: 'id'`，与本次改动无关；原始输出见 `lint_output.txt`。

---

## v2 修复（2026-10-21，PR #18 review comments）

对应 PR #18 的两条 P2 inline comments：`q016_hist.py:867`（无触发 event 被漏出 event 统计）和 `q016_hist.py:303`（未验证的 RT slug fallback 被算作 mapped）。v2 数字来自 `run_output.txt` / `events.csv`；v1 对照来自 `run_output_v1.txt` / `events_v1.csv`；审计与证据分别见 `v2_audit_output.txt`、`v2_evidence.txt`。

### 1) P2#1：无触发 event 必须贡献 0（primary 用全部 priced event）

冻结口径原文（先于看盈亏写在脚本头）：

> `Event result = sum of net/share over its triggered thresholds (equal one share each).`
> —— `bots/quant/notes/q016-hist/q016_hist.py`（PRE-DECLARED DESIGN）

以及条目冻结的独立结果口径：

> `独立结果按 event 计（同片各档共享一次结算，算 1 个）`
> —— `bots/quant/entries/quant-016-rotten-tomatoes-beta-model.md`（frontmatter `test_2w`）

同一脚本的冻结判定还写明：`>= 30 and (... OR median event net <= 0 ...) -> FAIL`。无触发时“所有触发档 net 求和”是空和，空和 = **0**；因此 **PRIMARY = 全部 priced event（无触发的 14 个 event 记 0）**。旧代码只在 `ev_trades` 非空时把 event 加进 `event_nets`，是把这 14 个 0 丢掉了；旧的 triggered-only 视图只能作为 SECONDARY。

| event 统计口径 | event 数 | median net/share | mean net/share | event-cluster bootstrap 95% CI |
|---|---:|---:|---:|---:|
| **PRIMARY：全部 priced event，无触发记 0（v2）** | 66 | **-0.054190** | **-0.062616** | **[-0.132925, +0.014020]** |
| SECONDARY：仅 triggered event（v1 旧口径） | 52 | -0.113876 | -0.079474 | [-0.168443, +0.017816] |

reviewer 的数字由 v2 代码独立复现：median 从 **-0.113876 → -0.054190**（review 写约 -0.0542），mean 从 **-0.079474 → -0.062616**（review 写约 -0.0626）。14 个 zero-trigger priced event 为：`minions-monsters-...`、`mutiny-...`、`normal-...`、`practical-magic-2-...`、`project-hail-mary-...`、`scary-movie-...`、`scream-7-...`、`shaun-the-sheep-...`、`the-breadwinner-...`、`the-invite-...`、`the-sheep-detectives-...`、`undertone-...`、`verity-...`、`you-me-tuscany-...`（完整 slug 见 `run_output.txt`）。

敏感性窗口同样改为 PRIMARY 含 0、SECONDARY 仅触发：73 个 priced event 的 median **-0.026219**、mean **-0.055922**、CI **[-0.134821, +0.024336]**；57 个 triggered event 的 median **-0.104500**、mean **-0.071619**、CI **[-0.168442, +0.031436]**。Brier / log loss / 已成交份额中位毛利不受 event 是否记 0 影响，v1 与 v2 完全相同。

### 2) P2#2：fallback slug 必须先验证，否则标 unmapped

v1 声称 **85/85 mapped**，实际是 **83 个 exact-title + 2 个未验证 fallback**（`evil_dead_burn`、`over_your_live_body`）。根因是 RT search 的维护页（1307 字节，`Maintenance in progress`）被当成 HTTP 200 成功结果缓存并复用；fallback 又直接用 Polymarket slug 拼 RT slug，未做任何存在性/标题校验。

- `over-your-live-body` → `/m/over_your_live_body`：live RT **HTTP 404**（`v2_evidence.txt`），旧版却计为 mapped，然后因无快照静默丢掉。
- 修正后从 RT search 取到正确的 2026 页面 `/m/over_your_dead_body_2026`：live RT **HTTP 200**，title `Over Your Dead Body (2026)`。

v2 修复分两层：

1. **搜索页校验**：维护页/错误页不再写入也不再复用为成功搜索；发现旧缓存是维护页时删除并重取。
2. **fallback 校验**：任何非 exact-title 的候选 slug 都必须通过 live RT 页面验证——页面存在、规范化标题与影片名一致、有年份时与 event 年份差 ≤1；否则该 event 标为 `slug_fallback_unmapped`，`rt_slug` 置空，不计入 mapped。

结果：v2 **mapped 85/85，mapping methods = {'rt_search_exact_title': 85}**，即全部 exact-title + 年份最近验证；**unmapped = 0**。这不是把错误 fallback 硬算成 mapped，而是修正了被维护页掩盖的正确页面（`over_your_live_body` 仍是 404，已不再使用）。如果搜索重取失败，fallback 校验会把旧 slug 404 判为 unmapped——这是 v2 的保险。

映射修正后新增 `over_your_dead_body_2026` 的 Wayback 快照 `20260426124238`，但该 event 在 `[t-6h,t]` 内没有可成交 trade（`priced_thresholds=0`），所以 priced event 仍为 **66**、P&L 样本不变。快照覆盖因此从 v1 **primary 73 / sensitivity 80** 变为 **74 / 81**；无主快照 event 从 **11** 降到 **10**；快照分与最终区间一致仍为 **51/74**（v1 `51/73`），有显示分仍为 **74/74**。

### 3) Wayback / trade 缓存的“失败下载被当成完整”审计

- **rt_search**：确实存在该类 bug（2 个维护页被缓存为成功搜索，导致 v1 的 2 个 fallback）。v2 已修；重跑后缓存审计 `rt_search files=84 maintenance_or_invalid=0`。
- **Wayback 快照 HTML**：`wayback snapshot files=109 partial_or_error=0`；没有截断 HTML、维护页或 Wayback 错误页被当成完整快照。v2 的 `fetch_snapshot` 现在会校验 `<html>` 完整性/维护页并在失败时删除缓存。
- **CDX**：`cdx files=90 invalid=0`；其中 4 个是合法空列表。对可疑的 `fantasy_life`、`the_weight_2026` 做了 wider-window 重查：`fantasy_life` 周边 11 个 capture、但目标窗口内 **0** 个；`the_weight_2026` 周边 5 个 capture、目标窗口内 **0** 个（`v2_evidence.txt`），所以它们是**真为空**，不是 partial 缓存。另两个空列表属于已弃用的旧 slug `over_your_live_body` 和结算后窗口。
- **data-api trades**：`trade files=669 invalid=0 max_rows=131 files_with_>=500_rows=0`；当前样本没有触发 500 行分页上限，也没有非法 JSON。v2 仍加了保护：JSON 非 list、分页到 50 页仍满 500 行时拒绝写缓存，避免把 partial 当 complete。
- **CDX / timemap**：非空但无法解析的响应现在会删除缓存并报错，不再把 `[]` 写回当成“完整空结果”。

### 4) v1 vs v2 关键数字

| 指标 | v1 | v2 |
|---|---:|---:|
| mapped | 85/85（83 exact + 2 未验证 fallback） | **85/85（85 exact，全部验证）** |
| 无主快照 event | 11 | 10 |
| primary / sensitivity 有快照 event | 73 / 80 | 74 / 81 |
| priced events / scored thresholds | 66 / 192 | 66 / 192 |
| triggered trades / triggered events | 92 / 52 | 92 / 52 |
| **PRIMARY median event net/share** | （v1 只报 triggered-only） | **-0.054190** |
| **PRIMARY mean event net/share** | （v1 只报 triggered-only） | **-0.062616** |
| PRIMARY bootstrap 95% CI | （v1 只报 triggered-only） | [-0.132925, +0.014020] |
| **SECONDARY median / mean** | -0.113876 / -0.079474 | -0.113876 / -0.079474 |
| median filled-share gross | -0.034787 | -0.034787 |
| Brier model / market / diff | 0.066637 / 0.035369 / +0.031268 | 同左 |
| LogLoss model / market / diff | 0.214928 / 0.121872 / +0.093056 | 同左 |
| sensitivity PRIMARY median / mean | （v1 只报 triggered-only） | -0.026219 / -0.055922 |
| sensitivity SECONDARY median / mean | -0.104500 / -0.071619 | -0.104500 / -0.071619 |
| **VERDICT** | **FAIL** | **FAIL** |

### 5) 冻结 VERDICT 是否改变

**不改变，仍为 FAIL。** PRIMARY 纳入 14 个 0 后 median event net 从 -0.113876 变为 **-0.054190**，仍 ≤ 0；已成交份额中位毛利仍为 **-0.034787** ≤ 0；模型 Brier 仍比市场差 **+0.031268**，log loss 仍差 **+0.093056**。映射修复只修正了 1 个无成交 event 的快照，没有增加 priced event。因此冻结判定 `median event net <= 0`、`median filled-share gross <= 0` 以及模型校准差于市场三项仍触发，FAIL 不变。

v2 的 3 个随机 spot check 因候选集多了 1 个有快照 event 而换成了 `the-odyssey` / `sense-and-sensibility` / `they-will-kill-you`，原始输出见 `run_output.txt`；上面 v1 节的 3 个 spot check 保留为 v1 记录。

### 6) 复现与文件

```bash
cd bots/quant/notes/q016-hist
python3 q016_hist.py > run_output.txt          # 缓存复用；v2 stdout
python3 v2_audit.py > v2_audit_output.txt       # v1 vs v2、映射、缓存审计
python3 v2_evidence.py > v2_evidence.txt        # 空 CDX 重查、旧/新 slug live 状态
```

v2 校验和（来自 `v2_audit_output.txt`）：

- `run_output.txt` sha256 `46f410db4fc04f452430a8bbd88c040f2121af4827ea9bc12d8dcfba98bcdead`
- `events.csv` sha256 `7c8bd5972c7805fb32a39d1666a79142e3f447f2e53a4990c2ef917e51a1f626`
- v1 `run_output_v1.txt` sha256 `dbfce42c1e03c802eecf3a8e719068e703ea2ba18bf86b97375fdd060058a9fa`
- v1 `events_v1.csv` sha256 `d0e9121aebadb6e5a8872294aef06b38f1e9f15b6ad7e07e99d02083a1628065`

原始下载仍在 gitignore 的 `_cache/`（v2 新增的 CDX/快照/trade 也只写 `_cache/`）；提交文件均 <1 MB。
