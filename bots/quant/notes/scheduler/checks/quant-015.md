# quant-015 独立核查（checker w07）

核查对象：`bots/quant/entries/quant-015-global-temp-era5-nowcast.md`（status `草稿`，未改动条目）。
核查时间：2026-10-20 UTC。脚本与缓存全部放在仓库外：`/tmp/c20261020-1423-research-w07/`（`cache/`、`out/`）。
结论：预测侧（321 个月走前检验）、首发布代理、规则原文、CLOB 可得性和 n=1 对照均可复现；但“每月 1 个独立结果”与“两周最多 2 个 / 30 个要 15 个月”自相矛盾，必须改为“两周最多 1 个 / 30 个约 30 个月”。成本门槛的 5¢ 也与自己的公式不符（约 3.6–4.1¢）。其余为数据 vintage 备注。

## 1. 每个 URL 的重取结果

| # | URL（条目引用） | 本次结果 | 与条目对比 |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c` | HTTP 200，26,351 B；`closed=true`；`volume=11127.859859`、`openInterest=8452.463409`；`negRisk=true`、`restricted=true`；`startDate=2026-08-31T13:37:03Z`、`endDate=2026-11-02T04:59:00Z`；6 档；`feeSchedule rate=0.05` | **OK**。条目 26,352 B；其余逐项一致。 |
| 2 | `https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489` | HTTP 200，25,839 B；6 档 `<1.10 … >1.29`；`>1.29` 档 `["1","0"]`；volume 15,901.867726；openInterest 6,722.919473 | **OK，一致**。 |
| 3 | `https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all` | HTTP 200，829,011 B；33 个事件（32 closed / 1 open）；29 个不同月份；28 个已关闭月份；191 个 YES token | **OK / 字节数随时间变化**。条目 829,034 B；计数一致。 |
| 4 | `https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset=0..400&closed=true&order=endDate&ascending=false` | 5 页均 HTTP 200；5,791,419 / 6,086,614 / 6,134,624 / 5,877,652 / 6,132,160 B；共 500 个已关闭 weather 事件；标题/slug 含 `temperature increase\|how hot will` 的只有 1 个（`september-2026-temperature-increase-c`） | **OK，一致**（页面大小随时间略变）。 |
| 5 | `https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv` | HTTP 200，1,198,225 B；31,721 行；末行 `2026-10-17,15.303,14.409,0.894,PRELIMINARY`；`# Last updated: 19 Oct 2026`；2026-09 月均 `0.8191`（30 天） | **OK，逐字节一致**。 |
| 6 | `https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json` | HTTP 200，63 B；`{"daily":20261017,"monthly":202609,"annual":2025}` | **OK，一致**。 |
| 7 | `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | HTTP 200，17,039 B；2026 行 `108 123 130 116 113 117 124 142 138 **** **** ****` | **OK，一致**。Sep=1.38、Aug=1.42。 |
| 8 | `https://data.giss.nasa.gov/gistemp/updates_v4/` | HTTP 200，19,967 B；原文 “Graphs and tables are updated around the middle of every month using the current data files provided by NOAA/NCEI (GHCN v4: meteorological stations, ERSST v5: ocean).” | **OK，逐字一致**。 |
| 9 | `https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6` | HTTP 200，16,974 B；82 个快照；其中 `>=20230101` 的 **45** 个；首个 2019-07-21，最后 2026-10-04 | **OK，一致**（条目“2023-01 起 45 个”正确）。 |
| 10 | `https://web.archive.org/web/20251112105542id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | 缓存正文 16,934 B；2025 行 `137 125 136 123 107 105 101 114 **** **** **** ****` | **OK，一致**（Jan–Aug 有值）。 |
| 11 | `https://clob.polymarket.com/prices-history?market=<191 个 YES token>&interval=max&fidelity=60` | 191 个请求全部返回 200；只有 2 个事件非空：`september-2026`（6/6）与 `october-2026`（6/6）；其余 31 个事件所有 token `history=[]` | **OK，一致**。脚本 `clob_temp.py`，输出 `out/clob_temp.txt`。 |
| 12 | `https://clob.polymarket.com/prices-history?market=9561250571098553460692263040980922664627749350602993898138030564733182354111&interval=max&fidelity=60` | HTTP 200，12,171 B；**460** 点（条目 468）；首点 `2026-09-20T14:00:14Z p=0.44`（条目 06:00 p=0.47）；末点 `2026-10-09T16:00:23Z p=0.905` | **OK / 点数随时间变化**。`interval=max` 只保留约 30 天，条目抓取时 06:00 的点现在已被窗口切掉；10-05 和 10-09 的价格仍精确一致。 |
| 13 | `https://gamma-api.polymarket.com/events?slug=where-will-2026-rank-among-the-hottest-years-on-record` / `will-any-month-of-2026-be-the-hottest-on-record` | 各返回 1 个事件，标题匹配 | **OK**。 |

## 2. 数字重算

### 2.1 规则与结算（逐项）

- 6 档标题：`<1.30ºC`、`1.30–1.34`、`1.35–1.39`、`1.40–1.44`、`1.45–1.49`、`>1.49` ✅
- 规则原文逐字对照见 §3。
- 2026-09：`closed=true`，6 档全部 `umaResolutionStatus=resolved`；`1.35–1.39` 档 `["1","0"]`；GISTEMP Sep=`138` ✅
- 2026-08：`>1.29` 档 `["1","0"]`；GISTEMP Aug=`142` ✅
- `endDate=2026-11-02T04:59:00Z` = 2026-11-01 23:59 ET（11 月起 EST=UTC−5）✅

### 2.2 走前检验（重跑条目笔记里的 `walkforward.py`）

我把条目笔记 `bots/quant/notes/r2prep-verification/quant-015.md` 里的 `walkforward.py` 原文抽出，对本次新下载的 `gistemp.txt`/`era5.csv` 重跑。输出 `out/wf_orig.txt` 与条目逐项一致：

```text
=== MAIN rolling 120 months: n=321, skipped=0, span=(2000, 1)..(2026, 9) ===
 PIT: mean=0.5003 sd=0.2893 KS_vs_U(0,1)=0.0372
 PIT deciles: [31, 29, 41, 25, 40, 36, 33, 21, 23, 42]
 ALL: n=321 hit=123/321=0.3832 persist_hit=42/321=0.1308 LL_model=1.3638 LL_persist=2.0608 LL_uniform=2.0794 cov50=0.5016 cov80=0.7726 cov90=0.8816 KS=0.0372
 2000-2012: n=156 hit=73/156=0.4679 persist_hit=19/156=0.1218 LL_model=1.2976 LL_persist=2.0580 LL_uniform=2.0794 cov50=0.5705 cov80=0.8077 cov90=0.9231 KS=0.0913
 2013-2026: n=165 hit=50/165=0.3030 persist_hit=23/165=0.1394 LL_model=1.4264 LL_persist=2.0634 LL_uniform=2.0794 cov50=0.4364 cov80=0.7394 cov90=0.8424 KS=0.0882
 2020-2026: n=81 hit=25/81=0.3086 persist_hit=11/81=0.1358 LL_model=1.4649 LL_persist=2.0675 LL_uniform=2.0794 cov50=0.4815 cov80=0.7901 cov90=0.8642 KS=0.1026
 2024-2026: n=33 hit=12/33=0.3636 persist_hit=4/33=0.1212 LL_model=1.7819 LL_persist=2.0789 LL_uniform=2.0794 cov50=0.5455 cov80=0.7273 cov90=0.8485 KS=0.1592
 2024-04..2026-09: n=30 hit=11/30=0.3667 persist_hit=4/30=0.1333 LL_model=1.7697 LL_persist=2.0740 LL_uniform=2.0794 cov50=0.5667 cov80=0.7667 cov90=0.8667 KS=0.1380
```

最新月参数与档位概率也逐项一致：

```text
latest target (2026, 9) ERA5 0.8191 pred 1.3861 actual 1.38 sigma 0.0563
latest OLS a,b,sigma 0.591262 0.970383 0.056299
bracket probabilities: 1.25–1.29 .0467 | 1.30–1.34 .1799 | 1.35–1.39 .3301 | 1.40–1.44 .2895 | 1.45–1.49 .1212 | 1.50–1.54 .0242
```

- 2000-01..2026-09 共 **321** 个月 ✅
- `2026-03` 最坏月：pred=1.10704、actual=1.300、单月 log loss **6.9637** ✅（条目 6.964）
- 我另写的一个独立重实现得到 1.3687（分箱边界/KS 口径不同）；按条目自己的脚本重跑得到 1.3638，说明差异来自我的重写，不是条目数字错。所有核心结论不受影响。

**非阻断方法备注**：条目的 8 结果均匀基线是 `ln8=2.0794`，这是为了和 persistence 共用分区；市场实际只有 6 档，6 档均匀基线是 `ln6=1.7918`。2024-2026 的 1.7819 对 `ln8` 低 0.2975，但对 `ln6` 只低 **0.0099 nats**（几乎无技能）。条目已说“近期退化”，但若给主审看，补一句 `ln6=1.7918` 会更准确。这不是伪造，是口径提示。
另：脚本里的 KS 是单侧 `max|F_n(i)-i/n|`；标准双侧 KS 在 2024-2026 为 **0.1895**（全样本仍是 0.0372）。按标准定义退化更强，不影响结论。

### 2.3 首发布 vs 修订（Wayback 代理）

脚本 `firstrel.py`，输出 `out/firstrel.txt`。结果与条目逐项一致：

```text
snapshots 45
covered months 30
mean revision 0.002 mae 0.012 sd 0.015844 maxabs 0.04
bracket unchanged 23 / 30 exact 8 / 30
switch 2024 1 1.21 -> 1.25 pred 1.253
switch 2024 5 1.14 -> 1.16 pred 1.22
switch 2024 6 1.25 -> 1.23 pred 1.246
switch 2024 11 1.31 -> 1.29 pred 1.294
switch 2025 6 1.03 -> 1.06 pred 1.052
switch 2025 8 1.14 -> 1.17 pred 1.068
switch 2026 3 1.28 -> 1.3 pred 1.107
hits first 7 revised 9 of 30
```

- 45 个快照 ≥2023-01 ✅；30 个月覆盖 ✅；未覆盖 2025-09、2026-07、2026-09 ✅
- 平均修订 +0.002、MAE 0.012、sd 0.0158、max 0.04 ✅
- 0.05 档不变 23/30、0.01 完全相同 8/30 ✅
- 首发布命中 7/30、修订命中 9/30 ✅
- 7 个换档月及 pred 全部一致 ✅

### 2.4 事件、CLOB、n=1 对照

脚本 `temp_stats.py` / `clob_temp.py` / `sep_check.py`，输出 `out/temp_stats.txt`、`out/clob_temp.txt`、`out/sep_check.txt`：

```text
events 33 closed 32 open 1
months 29 closed months 28
tokens 191
september-2026 11127.859859 closed
october-2026 2522.636154 open
august-2026 15901.867726 closed
january-2025 4925571.471499 closed
september-2025 2415315.783064 closed
```

```text
events nonempty 2
september-2026-temperature-increase-c 6 456 460
october-2026-temperature-increase-c-20260928t160000000z 6 463 469
empty events 31
```

```text
2026-10-05T00:00:00Z sum 0.923 settled 0.635 norm 0.688 modelLL 1.1084 marketLL 0.374
2026-10-09T16:00:00Z sum 0.9075 settled 0.905 norm 0.9972 modelLL 1.1084 marketLL 0.0028
```

- 33 事件 / 32 closed / 1 open / 29 个月 / 28 个已关闭月份 / 191 token ✅
- 只有 2 个事件非空、其余 31 个全空 ✅
- 2026-09 已关闭事件：模型 0.3301，市场原始 0.635、归一化 0.688；模型 log loss 1.1083、市场 0.3740 ✅
- 2026-10-09：0.905 / 归一化 0.9972 ✅
- 条目写的 468/454–460 点是抓取时的点数；`interval=max` 约 30 天窗口，现在 Sep 变成 456–460、Oct 463–469，属于数据窗口滚动，不是条目错。10-05/10-09 两个关键价格仍精确复现。

### 2.5 成本算术

- `p=0.10`：`0.05×0.10×0.90=0.0045`，占投入 4.5% ✅
- `p=0.33`：`0.05×0.33×0.67=0.011055`，占投入 3.35% ✅
- `p=0.905`：`0.05×0.905×0.095=0.004299`，占投入 0.47% ✅
- 规则 4 的门槛：`0.05·ask·(1−ask)+0.01+0.02`；ask=.33 时 `0.011055+0.03=0.041055`，约 **4.1¢**。
- 成本节假设半价差 0.5¢：`0.011055+0.02+0.005=0.036055`，约 **3.6¢**。
- 条目写“需要模型概率比价格高约 0.05”“门槛约 5¢”，比自己的公式高约 0.9–1.4¢。这是保守方向的四舍五入，不改变“不买”的结论，但数字应对齐。

## 3. 结算规则原文对照（live Gamma）

| 条目写法 | live 原文（`september-2026-temperature-increase-c`） | 判定 |
|---|---|---|
| 6 档互斥 | `The brackets are mutually exclusive and collectively exhaustive: each range is inclusive of both of its stated endpoints, and the reported anomaly (to the nearest 0.01ºC) falls within exactly one bracket.` | ✅ 逐字一致。 |
| 结算源是 NASA，不是 Copernicus | `The primary resolution source for this market will be the figure found in the table titled "GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius" under the column "Sep" in the row "2026" (https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt).` | ✅ 逐字一致。 |
| 不理会事后修订 | `An anomaly within a named bracket for September 2026 is necessary and sufficient to resolve this market immediately once the data becomes available, regardless of whether the figure for September 2026 is later revised.` | ✅ 逐字一致。 |
| 缺数据兜底最低档 | `If no information for September 2026 is provided by NASA by November 1, 2026, 11:59 PM ET, this market will resolve to the lowest range bracket.` | ✅ 逐字一致；`endDate=2026-11-02T04:59:00Z` 正是该时点。 |
| `negRisk=true`、`restricted=true`、volume/OI | 本次 `negRisk=true`、`restricted=true`、volume `11127.859859`、OI `8452.463409` | ✅ |
| 档宽随月份变化 | 2026-08 为 `<1.10 … >1.29`；2026-09 为 `<1.30 … >1.49` | ✅ |

## 4. Look-ahead / 成本 / 独立性 / 容量

- **Look-ahead**：目标月只用该月之前 120 个完整重叠月估 OLS；目标月 ERA5 是整月日均的算术平均；没有用目标月之后的 GISTEMP。✅
- **Vintage 偏差**：训练/评估用的是现行修订后的 GISTEMP 和当前 ERA5 再分析值，不是当时的首发布值；条目已明确承认，并用 Wayback 代理量化（30 个月里 7 个换 0.05 档，首发布命中 7/30 vs 修订 9/30）。这是已知偏差，不是隐藏的 look-ahead。
- **n=1 价格对照**：2026-10-05 的价格在 12:00 ET 结算前、GISTEMP 发布前读取，不构成未来信息；但只有 1 个已关闭事件，不能统计。✅
- **成本**：费 `rate·p·(1−p)`，p=.33 时 3.35% 占投入；加半价差（假设 1¢，实际盘口取不到）和 2¢ 口径垫。没有正收益证据。✅
- **独立性**：一个月 1 个事件；同月 lower/higher-strikes 变体合并；两周最多 **1** 个（条目误写 2 个），30 个约需 **30 个月**（条目误写 15 个月）。✅（除该算术错误外，独立性口径正确。）
- **容量**：400 USDT/月；近期单 event 成交额 11k–16k USD（2026-10 只有 2,522.64），5,000 USDT 用不上。✅

## 5. 查重（known/ 与全部 bots/*/entries）

- `known/KNOWN.md` 无 weather/temperature 条目（`grep -in -E 'weather|temp|气温|天气' known/KNOWN.md` 无命中）。
- `bots/dot/entries/dot-001-late-day-observed-max-tail.md`、`dot-002-ensemble-calibration.md`：城市 **日最高温**、NOAA 站点、日内/次日；变量、结算源、周期都不同。
- `bots/muse/entries/muse-own2-tail-weather-expiry-favfade.md`：每日最高温分档的临到期热门买 NO；不同机制。
- `quant-005`、`quant-012` 只是文字里出现温度/关键词，不是气温策略。
- `quant-007`（AI 榜单）、`quant-010`（流媒体周榜）、`quant-017`（App Store 榜单）是榜单类，不是气温。
- **判为不重复**；条目的 gate 4 “不确定”是过度保守，但不算错。

## 6. 七条门槛

1. **机制说得清：满足**。ERA5 月末后 3–5 天有整月值，GISTEMP 月中才更新；付钱方是仍按旧信息定价的对手方。时滞引了原文。持续性和“市场已消化”未被证明。
2. **有免费数据能检验：部分满足 / 不确定**。预测侧数据完整（321 个月走前）；价格侧只有 2 个事件有 CLOB 历史，已关闭只有 1 个，拿不到 ≥30 个独立价格结果。
3. **小资金能做：满足**。400 USDT/月、买 YES 最大亏损为本金、不加杠杆；容量写清。
4. **不重复：满足**。与 dot/muse 的城市日最高温、quant-007/010/017 的榜单、known/ 均不同。
5. **扣成本后粗算够用：不满足**。没有价格回测；唯一已关闭事件上模型 log loss 1.1083、市场 0.3740，模型输；规则 4 不会在该事件买。
6. **两周内能检验：不满足**。1 个/月，两周最多 1 个，30 个约 30 个月；应进待选区。
7. **出处可查：满足**。规则、数据、脚本输出、失败项（31 个事件空 history、3 个月未覆盖、CLOB 点数变化）都有出处或脚本；Gamma 量标了“来源自报，未核实”。

## 7. 需要改的地方（精确）

1. 前置字段 `test_2w`：`两周最多 2 个` → `两周最多 1 个`（1 个/月）。
2. `## 两周内怎么检验` 第一条：`一个月 1 个，两周最多 2 个` → `一个月 1 个，两周最多 1 个`。
3. `## 门槛自查` 第 6 条：`1 个/月，两周最多 2 个，30 个要 15 个月以上` → `1 个/月，两周最多 1 个，30 个要 30 个月（约 2.5 年）以上`。
4. `## 成本与容量`：`需要模型概率比价格高约 0.05` → `约 0.036（费 0.0111 + 2¢ 垫 + 0.5¢ 半价差；按规则 4 的 1¢ 价差缓冲则约 0.041）`；`## 门槛自查` 第 5 条 `约 5¢` → `约 3.6–4.1¢`。
5. 非阻断（不要求改）：CLOB `interval=max` 约 30 天窗口，Sep 点数已从 468 降到 460、首点从 06:00 移到 14:00；条目已给抓取时间，建议在数据节补一句“点数会随抓取时间滚动”。

CHECK: quant-015 FIX
1. 前置字段 `test_2w`：`两周最多 2 个` → `两周最多 1 个`。
2. `## 两周内怎么检验` 第一条：`两周最多 2 个` → `两周最多 1 个`。
3. `## 门槛自查` 第 6 条：`30 个要 15 个月以上` → `30 个要 30 个月（约 2.5 年）以上`。
4. `## 成本与容量` 的 `约 0.05` 与 `## 门槛自查` 第 5 条的 `约 5¢`：改为 `约 0.036` / `约 3.6–4.1¢`（按条目自己的费 0.0111 + 2¢ 垫 + 0.5¢ 半价差，或规则 4 的 1¢ 价差缓冲）。
