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


---

## 补充核查（批次 c20261020-170337-research）

# CHECK quant-015 — Global monthly temperature-anomaly brackets (ERA5 → GISTEMP)

Independent fact-check, 2026-10-20 UTC. Entry checked: `bots/quant/entries/quant-015-global-temp-era5-nowcast.md` (currently `status: 待核`; not edited). All scripts, raw downloads and stdout are outside the repo under `/tmp/c20261020-170337-research-w07/` (`scripts/`, `cache/`, `out/`); no raw file was added to the repo.

## 1. URL re-fetch log

| # | URL (as cited in entry) | Result | Live value vs entry |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c` | **OK** HTTP 200, 26,352 B | Exact: title, 6 brackets, `negRisk=true`, `restricted=true`, `startDate=2026-08-31T13:37:03Z`, `endDate=2026-11-02T04:59:00Z`, `volume=11127.859859`, `openInterest=8452.463409`, `feeSchedule rate=0.05` (`weather_fees`), all 6 `umaResolutionStatus=resolved`; `1.35–1.39` = `["1","0"]`. |
| 2 | `https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489` | **OK** HTTP 200, 25,839 B | Exact: grid `<1.10 … >1.29`, `>1.29` = `["1","0"]`, `volume=15901.867726`, `endDate=2026-09-01T03:59:00Z`. |
| 3 | `https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all` | **OK** HTTP 200, 829,033 B | 33 events; 32 closed, 1 open; 29 distinct month slugs; 28 closed months. Exact. |
| 4 | `https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset=0..400&closed=true&order=endDate&ascending=false` | **OK** 5× HTTP 200, ~5.8–6.1 MB each | 500 events; only 1 title/slug contains `temperature increase|how hot will` (`september-2026-temperature-increase-c`). Matches entry's side note. |
| 5 | `https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv` | **OK** HTTP 200, 1,198,262 B, 31,722 lines | Entry's 1,198,225 B / 31,721 lines / last row `2026-10-17,…,0.894,PRELIMINARY` was its 05:xxZ snapshot. Re-fetch: `Last updated: 20 Oct 2026`; last row `2026-10-18,15.260,14.371,0.889,PRELIMINARY`; 2026-10-17 is now `15.307,14.409,0.899,FINAL`. **Changed (time-varying).** |
| 6 | `https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json` | **OK** HTTP 200, 63 B | Entry `{"daily":20261017,"monthly":202609,"annual":2025}`; now `{"daily":20261018,"monthly":202609,"annual":2025}`. **Changed (time-varying); monthly still 202609.** |
| 7 | `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | **OK** HTTP 200, 17,039 B | 2026 row exactly `2026 108 123 130 116 113 117 124 142 138 **** **** **** ...`; Sep = 1.38, Aug = 1.42. **Exact.** |
| 8 | `https://data.giss.nasa.gov/gistemp/updates_v4/` | **OK** HTTP 200, 19,967 B | Quote `Graphs and tables are updated around the middle of every month using the current data files provided by NOAA/NCEI (GHCN v4 ... ERSST v5 ...)` — exact. |
| 9 | `https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6` | **OK** HTTP 200, 16,974 B | 82 rows total, 45 from 2023-01 onward; range 2019-07-21..2026-10-04. Entry's "2023-01 起 45 个" matches. |
| 10 | `https://web.archive.org/web/20251112105542id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt` | **OK** HTTP 200, 16,934 B | 2025 row `137 125 136 123 107 105 101 114 **** …` = Jan–Aug values, as entry says. |
| 11 | `https://clob.polymarket.com/prices-history?market=<YES token>&interval=max&fidelity=60` for 191 YES tokens | **OK** 191 requests, 0 errors | Only 2 events non-empty: `september-2026-temperature-increase-c` (6/6 brackets, **453–457** points) and `october-2026-temperature-increase-c-20260928t160000000z` (6/6, **466–472** points, open). Remaining 31 events all `history=[]`. Entry's §7 has these two point ranges **swapped**. |
| 12 | `https://clob.polymarket.com/prices-history?market=9561250571098553460692263040980922664627749350602993898138030564733182354111&interval=max&fidelity=60` | **OK** HTTP 200 | 457 points; first `2026-09-20T17:00Z p=0.45`; last `2026-10-09T16:00Z p=0.905`. At `2026-10-05T00:00Z` (nearest 00:00:21Z) p=0.635. Matches entry's raw prices. |
| 13 | Local scripts `walkforward.py`, `pm_histcheck.py`, `pm_count.py`, `pm_model_market.py`, `firstrelease_local.py` | Re-ran independent equivalents | See §2; all key results reproduce, with the small differences listed in §7. |

## 2. Numbers recomputed

Scripts/outputs (all in `/tmp/c20261020-170337-research-w07/`):

- `scripts/fetch15_base.py` — base fetches.
- `scripts/wf15.py` → `out/wf15.txt` — 321-month walk-forward.
- `scripts/wf15_var.py` → `out/wf15_var.txt` — expanding / rolling-60 variants.
- `scripts/first15.py` → `out/first15.txt` — Wayback first-release proxy.
- `scripts/pm15.py` → `out/pm15.txt` — event/month count.
- `scripts/clob15.py` → `out/clob15.txt` — 191-token CLOB census and 2026-09 price path.
- `scripts/summarize15.py` → `out/summarize15.txt` — live Gamma/GISTEMP/ERA5 snapshot.

### 2.1 Walk-forward (target 2000-01..2026-09, 321 months)

`out/wf15.txt`:

```text
ALL n=321 hit=0.38317757 ll=1.36377414 llp=2.06138469 pitmean=0.50025313 pitsd=0.28885837
    cov50=0.50155763 cov80=0.77258567 cov90=0.88161994
2000-2012 n=156 hit=0.46794872 ll=1.29757127 llp=2.05810293 cov80=0.80769231
2013-2026 n=165 hit=0.30303030 ll=1.42636595 llp=2.06448744 cov80=0.73939394
2020-2026 n=81  hit=0.30864198 ll=1.46487250 llp=2.06912315 cov80=0.79012346
2024-2026 n=33  hit=0.36363636 ll=1.78194821 llp=2.07967896 cov80=0.72727273
2024-04..2026-09 n=30 hit=0.36666667 ll=1.76966717 llp=2.07456795 cov80=0.76666667
KS all=0.03720775
deciles [31, 29, 41, 25, 40, 36, 33, 21, 23, 42]
last 2026-09 pred=1.38610297 sd=0.05629885 actual=1.38 a=0.59126199 b=0.97038332
2026-09 probs [0.05281, 0.17986, 0.33012, 0.28947, 0.12121, 0.02654] sum=1.0
2026-03 pred=1.10703766 actual=1.30 ll=6.96366755
```

- Main table (hit 123/321, model LL 1.3638, persistence 2.0614 vs entry 2.0608, uniform ln8=2.0794, 80% 0.7726, 90% 0.8816) reproduces. The persistence difference is 0.0006 and does not change any conclusion.
- PIT mean 0.50025, sd **0.28886** (entry 0.2893), KS **0.03721** (entry 0.0372), deciles exactly match.
- 2024–2026: hit 12/33=0.3636, LL 1.78195, 80% coverage 0.72727 — all exact. **But 2024–2026 KS recomputes to 0.18948, not the entry's 0.1592.** The degradation conclusion is stronger, not weaker.
- 2026-03 worst month: pred 1.10704, actual 1.300, LL 6.96367 — exact.
- Latest 2026-09 bracket probabilities: 0.05281 / 0.17986 / 0.33012 / 0.28947 / 0.12121 / 0.02654 — exact; `pred=1.38610`, `a=0.591262`, `b=0.970383`, `σ=0.056299` — exact.

`out/wf15_var.txt`:

```text
rolling120 n=321 hit=0.3832 ll=1.3638 cov80=0.7726 pitmean=0.5003 KS=0.0372 ll2024=1.7819
expanding  n=321 hit=0.3084 ll=1.5173 cov80=0.9128 pitmean=0.6061 KS=0.2310 ll2024=1.7241
rolling60  n=321 hit=0.3894 ll=1.3669 cov80=0.7352 pitmean=0.5039 KS=0.0542 ll2024=1.7956
```

Entry's robustness table reproduces (expanding KS 0.2279 vs my 0.2310; rolling60 KS 0.0511 vs 0.0542 — both minor and same direction).

### 2.2 First-release proxy (Wayback)

`out/first15.txt`: 30 months covered (2024-01..2026-09; missing 2025-09, 2026-07, 2026-09). Reproduced exactly:

```text
mean rev +0.002  mean abs 0.012  sd 0.01558  max abs 0.04
bracket unchanged 23/30 = 0.7667 ; exact 0.01 same 8/30
switch months: 2024-01 1.21→1.25, 2024-05 1.14→1.16, 2024-06 1.25→1.23,
               2024-11 1.31→1.29, 2025-06 1.03→1.06, 2025-08 1.14→1.17, 2026-03 1.28→1.30
walk-forward hit on revised values 9/30 ; on first-release values 7/30
```

The seven switch months and the 9/30 vs 7/30 comparison are exact. This is a real first-release-vs-revision bias, correctly disclosed.

### 2.3 Polymarket count / CLOB

`out/pm15.txt`: 33 events, 32 closed, 1 open; 29 distinct months; 28 closed months; volumes `september-2026 11,127.859859`, `october-2026 2,522.636154`, `august-2026 15,901.867726`, `january-2025 4,925,571.471499`, `september-2025 2,415,315.783064`. Exact.

`out/clob15.txt`: 191 YES tokens, 0 request errors; 12 non-empty tokens from 2 events; Sept 6 brackets 453–457 points, Oct 6 brackets 466–472; target Sept `1.35–1.39` 457 points; 2026-10-05 00:00Z p=0.635; 2026-10-09 16:00Z p=0.905. The entry's raw prices match, but its point ranges are assigned to the wrong events.

At 2026-10-05 00:00Z nearest point, the six Sept YES prices are `0.0925, 0.07, 0.635, 0.075, 0.018, 0.017`, sum **0.9075**; normalized target = `0.635/0.9075 = 0.6997`, market log loss `−ln(0.6997)=0.3570`. The entry says 0.6880 and 0.3740. (The entry's raw 0.635 is right; 0.6880 would require a price-sum of ~0.923, so either a different timestamp or a different price set was used. State the exact point if keeping it.) The direction is unchanged: model 1.1083 vs market ~0.36–0.37, market still better.

### 2.4 Frequency

33 events over 31 calendar months (2024-04..2026-10) = 1.06 events/month; after merging same-month variants, **1 independent result/month**. Matches entry. Two weeks can never reach 30 independent results.

## 3. Resolution-rule quotes vs live page

Fetched live `https://polymarket.com/event/september-2026-temperature-increase-c` (HTTP 200, 1,017,659 B) and the Gamma event. The live page contains the same text:

- `「...the figure found in the table titled "GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius" under the column "Sep" in the row "2026" (https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt).」` — exact.
- `「An anomaly within a named bracket for September 2026 is necessary and sufficient to resolve this market immediately once the data becomes available, regardless of whether the figure for September 2026 is later revised.」` — exact.
- `「The brackets are mutually exclusive and collectively exhaustive: each range is inclusive of both of its stated endpoints, and the reported anomaly (to the nearest 0.01ºC) falls within exactly one bracket.」` — exact.
- `「If no information for September 2026 is provided by NASA by November 1, 2026, 11:59 PM ET, this market will resolve to the lowest range bracket.」` — exact. `endDate=2026-11-02T04:59:00Z` is 2026-11-01 23:59 EST (UTC−5), so the fallback deadline matches.
- Settlement check: GISTEMP Sep 2026 = 1.38 → `1.35–1.39` → `["1","0"]`. Aug 2026 = 1.42 → `>1.29` → `["1","0"]`. Both verified against the live table.

## 4. Look-ahead / cost / independence / capacity

- **Look-ahead (main model):** each target month uses only the previous 120 complete overlap months for the OLS; the current month's ERA5 mean is computed from days that are already over. No future target value enters the regression. **OK.**
- **Vintage look-ahead (not fully disclosed):** the rolling regression uses the **current revised GISTEMP history**, not the vintage that was available at each target date. The entry discloses the ERA5 vintage problem and the first-release-vs-revision target bias, but not this feature-window revision bias. Mean absolute revision is only 0.012°C, so the effect is small, but it should be stated.
- **Target vintage:** the entry correctly warns that the market settles on the first release, that its 30-month proxy shows 7/30 bracket switches, and that using revised values overstates hit rate (9/30 vs 7/30). Good.
- **Cost:** fee `0.05` from `feeSchedule`; `p=0.10 → 0.0045 (4.5% of stake)`, `p=0.33 → 0.011055 (3.35%)`, `p=0.905 → 0.0043 (0.47%)` — exact. The 1¢ spread is explicitly an assumption (closed-market book unavailable), correctly labelled as the softest number.
- **Independence:** one event per month; same-month lower/higher-strikes variants merged; correct. The 321 walk-forward months are evaluation months, not 321 independent trades; the entry does not claim otherwise.
- **Capacity:** 200 USDT/bracket, 400 USDT/month; recent event volume 11k–16k USDT, so 400 is ~2.5–16% of event volume. 5,000 USDT cannot be deployed. Correct.

## 5. Duplicate risk

- `grep -ril -E "ERA5|Copernicus|GISTEMP|global.*temp|气温|temperature" known/ bots/*/entries/ bots/*/CLAIMS.md bots/*/INDEX.md` → no `known/KNOWN.md` weather/temperature mechanism.
- Nearest neighbours:
  - `dot-001-late-day-observed-max-tail`, `dot-002-ensemble-calibration`, `muse-own2-tail-weather-expiry-favfade`: city **daily maximum** temperature, NOAA station observations/forecasts, daily horizon. Different variable, source, horizon.
  - `dot-003-macro-nowcast-vintage-surprise` (GDP nowcast) and `muse-own-predmarket-kalshi-cpi-nowcast` (Cleveland Fed CPI nowcast): same broad "official statistic release lag" family, but different statistic, data source, venue and settlement. Not a duplicate of the global monthly temperature mechanism.
  - `quant-005`, `quant-012`: keyword-only mentions, not temperature strategies.
- Conclusion: **no exact duplicate**; gate 4 can pass, but the "official-statistic nowcast" family is crowded and the integrator should confirm the distinction. The entry's own gate 4 says "不确定（需主审确认）", which is honest.

## 6. Gates 1–7 assessment

| Gate | Entry self-check | Checker verdict | Reason |
|---|---|---|---|
| 1 mechanism clear | 满足 | **PASS (with caveat)** | ERA5 month-end availability vs GISTEMP mid-month release is a real, sourced lag; whether the market still misprices it is unproven. |
| 2 free data | 不确定 | **PARTIAL** | Prediction side is excellent (ERA5 1940+, GISTEMP 1880+, 321 walk-forward months). Price side has only 1 closed event with CLOB history (2 events total), so no ≥30 independent return results; only forward recording remains. |
| 3 small capital | 满足 | **PASS** | 200/400 USDT, no leverage; event volume supports it. |
| 4 not duplicate | 不确定 | **PASS WITH CAVEAT** | No exact duplicate in `known/` or other bots; nearby daily-city-temperature and macro/CPI nowcast entries use different variables/sources/venues. Broad family is crowded; integrator should confirm. |
| 5 cost-adjusted | 不满足 | **FAIL/UNPROVEN** | No price backtest; the only closed priced event has model LL 1.1083 vs market ~0.357–0.374, so the market wins; `observed_net_return=null`. |
| 6 two-week test | 不满足 | **FAIL** | 1 independent event/month; two weeks gives at most 2, not 30. Must be 待选区, not 收录. |
| 7 sources | 满足 | **PASS** | URLs, access dates, script outputs and failed-fetch admissions are present; Gamma volume/openInterest are labelled 来源自报，未核实. |

Unambiguous passes: 1, 3, 4 (with caveat), 7 → 4/7. Gate 2 partial; 5 and 6 fail. This is consistent with the entry's own conclusion: a calibrated-nowcast candidate for the 待选区, not a proven money-making strategy.

## 7. Corrections

1. **§7 line 135: CLOB point ranges are swapped.** Re-fetch the 191 YES tokens: `september-2026-temperature-increase-c` has **453–457** points (6/6 brackets); `october-2026-temperature-increase-c-20260928t160000000z` has **466–472** points (6/6, open). The entry says Sept 466–468 and Oct 454–460. Swap them. (A 19-day hourly Sept series cannot have 466–468 points; 457 is the full history.)
2. **§3 line 92: 2024–2026 PIT KS.** Recompute = **0.18948**, not 0.1592. The degradation conclusion is unchanged (it is stronger). Also §3 line 91: PIT sd = **0.28886** (entry 0.2893); §3 line 35/table line 84: persistence log loss = **2.0614** (entry 2.0608). These are small but should be made consistent.
3. **§7 line 137 and risk line 185 / gate 5 line 202: normalized market price.** At the stated `2026-10-05T00:00Z` nearest point (00:00:21Z), the six YES prices sum to **0.9075**, so the normalized `1.35–1.39` price is `0.635/0.9075 = 0.6997`, and market log loss is **0.3570**, not 0.6880 / 0.3740. The raw 0.635 and 0.905 prices are correct. Either update to 0.6997 / 0.3570 or state the exact timestamp/price set that gives 0.6880. The direction (market beats model) does not change.
4. **Add the GISTEMP vintage look-ahead disclosure.** The rolling regression uses the current revised GISTEMP history for the 120-month feature window, not the vintage that was available at each target date. The entry already discloses the ERA5 vintage and the target first-release-vs-revision bias; add one sentence that the feature-window GISTEMP values are also revised (mean absolute revision 0.012°C in the 30-month proxy).
5. **Data-freshness line (optional, time-varying).** As of this re-fetch, ERA5's last row is `2026-10-18,…,0.889,PRELIMINARY`, `Last updated: 20 Oct 2026`, and the status JSON is `daily=20261018`; the entry's `2026-10-17` / `Last updated: 19 Oct 2026` was correct at its access time. If the entry is refreshed, update the access-time snapshot rather than treating the old values as current.
6. **Process note, not a text correction:** the entry is `status: 待核` (existing promotion in commit `8f10a6d`) while its body says `status 只给草稿`. The checker did not change it. Under the batch rule that only the integrator promotes, the integrator should decide whether this occupies a 待核 slot or is returned to `草稿`; no `date:` change is needed.

CHECK: quant-015 FIX

1. §7 line 135: swap the CLOB point ranges — Sept = 453–457 points, Oct = 466–472 points (not Sept 466–468 / Oct 454–460).
2. §3 line 92: change 2024–2026 KS from 0.1592 to 0.18948; line 91 change PIT sd from 0.2893 to 0.28886; line 35/table 84 change persistence log loss from 2.0608 to 2.0614 (or state rounding).
3. §7 line 137 / line 185 / gate 5: change the normalized 2026-09 price from 0.6880 to 0.6997 and market log loss from 0.3740 to 0.3570, or state the exact timestamp/price set used; keep raw 0.635 and 0.905.
4. Add a sentence in 数据/风险: the rolling 120-month regression uses current revised GISTEMP history, not the vintage available at each target date (mean absolute revision 0.012°C in the 30-month proxy); this is an additional vintage look-ahead next to the already-disclosed ERA5 vintage and target first-release bias.
5. (Optional, time-varying) if refreshing: ERA5 last row is now 2026-10-18 (0.889 PRELIMINARY), `Last updated: 20 Oct 2026`, status `daily=20261018`; the entry's 2026-10-17/19-Oct snapshot is stale but was correct at its access time.
6. Process: `status: 待核` is an existing promotion; leave the decision to the integrator and do not change `date:`.
