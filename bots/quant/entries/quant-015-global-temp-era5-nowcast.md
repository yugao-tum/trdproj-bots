---
id: quant-015
name_zh: 全球月均温距平：ERA5抢跑NASA
name_en: Global monthly temperature-anomaly brackets nowcast with Copernicus ERA5 / Climate Pulse
bot: quant
date: 2026-10-20
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「<Month> <YYYY> Temperature Increase (ºC)」6 档月距平阶梯（<x.xx / 0.05 宽区间 ×4 / >x.xx，negRisk）
venues: Polymarket
data: Copernicus Climate Pulse 全球日均 2m 气温 CSV（免费免密钥，1940-01-01 起，最新 2026-10-17）+ NASA GISTEMP v4 LOTI 月表（免费免密钥，1880-01 起，最新 2026-09）；Polymarket Gamma/CLOB（免费免密钥，但已关闭月温事件的 CLOB 价格历史返回空）
test_2w: 独立结果按事件（每月 1 个，同月 lower/higher-strikes 变体合并）计，两周最多 2 个，凑不到 30；失败标准是月频方向上模型 log loss 不优于均匀分布，或到手价与模型概率之差的绝对值中位 < 0.02
status: 草稿
confidence: 中
---

整理说明：本条的规则和数字全部在 2026-10-20 当日抓取。**没有回测**：已关闭月温事件的 CLOB 价格历史全部返回空（见下），只拿到最近 1 个事件（2026-09）的价格，因此本文是「模板/数据/校准」的证据，不是收益证明。我自己算的部分（回归、命中率、log loss）都写了公式和中间量。

## 一句话

每个月**月末之后、NASA GISTEMP 月中更新之前**，用 Copernicus Climate Pulse 的 ERA5 日均全球 2m 气温把整月均值算出来，回归到 GISTEMP 口径，得到 6 档月距平的概率；只在模型概率与可成交价的差超过「吃单费 + 半个价差 + 口径误差垫」时买该档 YES，持有到 GISTEMP 发布结算。

## 钱从哪里来

付钱的是**在 ERA5 已经给出整月答案之后、仍按「月还没过完」的直觉或旧新闻定价的对手方**。这个时滞是结构性的，因为两个数据源的发布节奏不同：ERA5 的整月均值在月末后约 3–5 天就齐了，而 GISTEMP 的月表是「around the middle of every month」才更新（原文见数据节），中间有约 8–12 天。付款动机不是谁的亏损补贴，就是信息发布时间差；一旦 GISTEMP 发布，这个差就归零。这条机制的前提是「两者之间能用一条稳定映射连起来」，我用 945 个月做了回归，R²=0.9698，但不是 1。

## 规则

**模板（Gamma 事件 `september-2026-temperature-increase-c`，2026-10-20 已读）**：

- 标题 `September 2026 Temperature Increase (ºC)`；`startDate=2026-08-31T13:37:03Z`；`endDate=2026-11-02T04:59:00Z`；`negRisk=true`；`restricted=true`；`volume=11127.859859`；`openInterest=8452.463409`。
- 6 个互斥档：`<1.30ºC`、`1.30–1.34ºC`、`1.35–1.39ºC`、`1.40–1.44ºC`、`1.45–1.49ºC`、`>1.49ºC`。原文：「The brackets are mutually exclusive and collectively exhaustive: each range is inclusive of both of its stated endpoints, and the reported anomaly (to the nearest 0.01ºC) falls within exactly one bracket.」
- **结算数据源（关键：不是 Copernicus，是 NASA）**：原文「the figure found in the table titled "GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius" under the column "Sep" in the row "2026"（`https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt`）」。即 GISTEMP v4 的 `No_Smoothing` 月值（推断：市场原文只给表名/列名/行名，`No_Smoothing` 措辞来自年度市场），单位 0.01 ºC。
- 不理会事后修订：「regardless of whether the figure for September 2026 is later revised」。
- 缺数据兜底：「If no information for September 2026 is provided by NASA by November 1, 2026, 11:59 PM ET, this market will resolve to the lowest range bracket.」`endDate=2026-11-02T04:59:00Z` = 2026-11-01 23:59 ET，即 endDate 是**兜底截止**，不是停牌时间。
- **实际结算早于 endDate**：2026-10-20 抓取时该事件已 `closed=true`、6 档全部 `umaResolutionStatus=resolved`，`1.35–1.39ºC` 档 `outcomePrices=["1","0"]`。而 GISTEMP 表 2026 行的 Sep 值是 **138**（=1.38 ºC），正好落在 1.35–1.39 档，**规则与结算结果一致，我核过**。同表 Aug=**142**（=1.42 ºC），与 8 月模板 `august-2026-temperature-increase-c-20260728155540489` 的 `>1.29ºC` 档结算（`["1","0"]`）一致。
- **档宽逐月变化**：2026-08 模板是 `<1.10 / … / >1.29`（6 档），2026-09 是 `<1.30 / … / >1.49`。档位边界随上一年水平移动，**不是固定网格**，所以每次要重读规则。
- 同族还有年度市场：`where-will-2026-rank-among-the-hottest-years-on-record`（`endDate=2027-03-02T04:59:00Z`，`volume=3796097.779246`，按 `Global_Mean_Estimates_based_on_Land_and_Ocean_Data/graph.txt` 的 `No_Smoothing` 排名）、`will-any-month-of-2026-be-the-hottest-on-record`（`endDate=2027-01-10`，`volume=154744.657949`）。本条只做月度，年度只记模板。

**交易规则（提案，未验证）**

1. 只用 ERA5 已覆盖整月的那一段：月末后 ≥5 天（等 FINAL）到停牌为止。月内（MTD）版本也可以做，但精度更差（见证据 3）。
2. 预测 `pred = 0.6014 + 0.9558 × ERA5月均距平`；每档概率 `p_i = Φ((hi_i−pred)/σ) − Φ((lo_i−pred)/σ)`，`σ=0.057`（2015–2025 残差标准差，见证据 2）。边界按「最近 0.01 四舍五入」处理成 `lo−0.005`/`hi+0.005`。
3. 只在 `p_i − ask_i > 0.05 × ask_i × (1−ask_i) + 0.01 + 0.02`（吃单费 + 半个价差假设 1¢ + 口径误差垫 2¢）时**吃单买 YES**；不做裸卖，不赌方向以外的东西。
4. 单档在险 ≤ 200 USDT，单月全档 ≤ 400 USDT，同时在手 ≤ 2 个月；总资金 5,000 USDT、单场所 ≤ 2,500 USDT 的约束天然满足。
5. 出场：不主动平仓，持有到 GISTEMP 发布后 UMA 结算（约 10–20 天）。理由：票面 1.00 的收敛免费，提前平仓要付第二遍费和价差。
6. 熔断：若 `pred` 落在某档边界 ±0.01 内，那一档和相邻档都不做（边界翻档风险最高）。
7. 明确不做：月内前 20 天就建仓（噪声大）、按 Copernicus 的 `monthly=202609` 状态字段当结算值（结算看 GISTEMP）、把 lower-strikes / higher-strikes 变体当独立机会重复计数。

## 证据

### 1）规则与结算（已读，非自报）

GISTEMP 表 2026 行原文（抓取 2026-10-20）：
`2026   108  123  130  116  113  117  124  142  138 **** **** ****   **** ***    112  120  128 ****  2026`
→ Jan 1.08、Feb 1.23、Mar 1.30、Apr 1.16、May 1.13、Jun 1.17、Jul 1.24、**Aug 1.42**、**Sep 1.38**（单位 0.01 ºC）。这两个数分别对上 8 月与 9 月市场的结算结果，**是我核对出来的，不是来源自报**。

### 2）ERA5 → GISTEMP 的映射精度（我自己算的，`b12_calc.py`）

- 样本：945 个重叠月（1948-01 … 2026-09；脚本筛选只有 `k[0] >= 1948`、无上界，故含 2026 年，2026-08/09 的 nowcast 属样本内）。
- `GISTEMP = +0.6014 + 0.9558 × ERA5月均距平`，`R²=0.9698`，**残差标准差 `σ=0.0695 ºC`**。
- 分段残差（2015–2025 的 132 个月）：2015–2019 均值 `+0.0019`、总体 sd `0.0583`（n=60）；2020–2025 均值 `−0.0035`、总体 sd `0.0566`（n=72）。**近期比全样本紧，所以本文用 σ=0.057，并把这个选择写在这里，不藏。**
- 关键量级对照：**档宽只有 0.05 ºC，而 σ≈0.057 ºC** —— 也就是说一个档的宽度比对口径误差还窄。这不是一个「知道答案」的策略，只是一个「把赔率算对」的策略。

### 3）样本内校准检验：132 个月（2015-01 … 2025-12，`b12_calc.py`；a、b、σ 用全样本估计，非走前式）

- **点预测命中档：37/132 = 0.2803**（6 档均匀基准 1/6 = 0.1667）。
- 用 `Normal(pred, σ=0.0695)` 对实现档的**平均 log loss = 1.6224 nats**；6 档均匀分布参照 `ln 6 = 1.7918 nats`。**改善 0.169 nats**，方向对但幅度小。
- MTD 变体（只用当月 1–25 日）：命中 **45/132 = 0.3409**，反而略高于整月版。这个反直觉结果说明「月内提前进场」并没有想象中那么差，但也说明点命中率对参数敏感，**不能把 28% 当成稳定常数**。

### 4）当前 nowcast（脚本原始输出）

- `2026-09: 30 days observed, mean ano +0.819 -> predicted GISTEMP +1.384 degC (bracket 1.35–1.39)` —— 实际 GISTEMP=1.38，**残差 −0.004**。
- `2026-08: 31 days, mean ano +0.846 -> predicted +1.410` —— 实际 1.42，残差 −0.010。
- `2026-10: 17 days observed, mean ano +0.836 -> predicted +1.400`（10 月未完，`PRELIMINARY`）。
两个已结算月都命中，但 n=2，**不算证据**。

### 5）市场价（唯一拿到的一个事件）

`september-2026-temperature-increase-c` 的 `1.35–1.39ºC` 档 YES token（`9561250571098553460692263040980922664627749350602993898138030564733182354111`）CLOB `prices-history?interval=max&fidelity=60` 返回 **469 个点，2026-09-20 05:00Z 起，2026-10-09 16:00Z 止**。日末价：

`09-20 0.45 / 09-24 0.495 / 09-29 0.53 / 09-30 0.645 / 10-02 0.66 / 10-05 0.735 / 10-07 0.59 / 10-08 0.895 / 10-09 0.905`

三点值得写下来：(a) **最后一个 print 早于结算约一周**，所以可交易窗口在 10-09 就结束了；(b) 10-05 时 ERA5 整月已齐（预测 1.384，正中该档），市场只有 0.735；(c) 但到 10-09 已经 0.905，而按 σ=0.057 的模型概率只有 **0.329** —— **市场比模型更自信，不是更不自信**。10-07 的 0.59 是这个序列里唯一明显低于模型的点。这一条直接否掉了「无脑买模型最爱档」的写法。

### 6）频率与容量（Gamma 计数，我数的）

- `public-search?q=temperature%20increase&limit_per_type=100&events_status=all` 里 slug 含 `temperature-increase` 且 `closed=true` 的事件 **31 个**（脚本 `b12_backtest.py` 打印 "closed monthly temperature-increase events: 31"）；另有 2024-04 用不同 slug（`how-hot-will-april-2024-be`）。同月还有 `(Lower strikes)` / `(Lower Ranges)` / `(HIGHER STRIKES)` 变体事件，**按 GUIDE 第 2 节第 6 条，同月同一结算源合并为 1 个独立结果**。
- 成交额（来源自报，未核实）：january-2025 `4925571.471499`、september-2025 `2415315.783064`、may-2026 `201756.698245`、july-2026 `61345.505281`、august-2026 `15901.867726`、september-2026 `11127.859859`、october-2026（未关）`2522.636154`。**同一模板的成交额在 18 个月里掉了两个数量级**，容量假设不能拿 2025 年的数。

## 数据

- **Copernicus Climate Pulse，全球日均 2m 气温 CSV（免费、免密钥、无需注册）**：`https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv`。首行注释写明「This file contains daily global mean near-surface (2m) air temperature data from ERA5 from 1940 to 2026 as well as daily temperature anomalies relative to the 1991-2020 reference period」。列为 `date,2t,clim_91-20,ano_91-20,status`，单位 deg. C。抓取日文件共 31,721 行，最后一行 `2026-10-17,…,0.894,PRELIMINARY`，注释块写「Last updated: 19 Oct 2026」。
- **发布时滞（原文）**：「The ERA5 data available in the CDS are updated with a 5-day delay (120 hours) behind real-time. Note that the time series below includes values based on ERA5 data not yet available in the CDS (for days 2 to 5 behind real-time).」以及「If preliminary, the values will likely change (slightly) once the final ERA5 data for the day are available (typically 3 days behind real-time).」
- **Pulse 状态文件**：`https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json` → `{"daily": 20261017, "monthly": 202609, "annual": 2025}`（2026-10-20 抓取）。即**整月 ERA5（monthly）到 2026-09 已可用**。
- **NASA GISTEMP v4 月表（免费、免密钥）**：`https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt`（17,039 bytes，2026-10-20 抓取，2026 行到 Sep 有值）。发布节奏原文（`https://data.giss.nasa.gov/gistemp/updates_v4/`）：「Graphs and tables are updated around the middle of every month using the current data files provided by NOAA/NCEI (GHCN v4 … ERSST v5 …)」。
- **Polymarket**：`https://gamma-api.polymarket.com/events?slug=<slug>`（规则原文、`feeSchedule`、`clobRewards`、`outcomePrices`）；`https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all`（找同族）；`https://clob.polymarket.com/prices-history?market=<YES token>&interval=max&fidelity=60`。
- **缺失，必须写清**：`may-2026-temperature-increase-c`、`january-2026-temperature-increase-c`、`december-2025-temperature-increase-c` 的首档 YES token 查询**全部返回空 `history`**。所以历史各月盘口取不到，**无法做价格回测，只能从 2026-10 起前向记录**。这一点与 quant-012（地震）遇到的限制相同。

## 两周内怎么检验

- 独立结果**按事件数**：一个月只有 1 个（同月 lower/higher-strikes 变体合并，年度市场另算）。两周最多 2 个，**因此本条不可能在两周内拿到 30 个独立结果**，`status` 只给 `草稿`。
- 能在两周内做完、且不依赖 Polymarket 的部分：把 1948-01 … 2026-09 的 945 个月做**滚动重估**（每次用前 60 个月估 `a,b,σ`，预测下一个月），得到逐月 log loss 曲线和按 `|pred−真实值|` 分桶的可靠性。这个用两个免费 CSV 就能跑完，是本条唯一可先验证的东西。
- 前向记录（从 2026-10-20 起）：每天记 ERA5 的 `ano_91-20` 与 `status`、6 档的 `bestBid/bestAsk/outcomePrices`、以及 GISTEMP 表是否出现该月值（用来自证「发布时滞」天数）。
- **失败标准（写死）**：(1) 滚动重估下月频 log loss 不优于 `ln 6 = 1.7918` → 模型无用，弃；(2) 前向 ≥20 个 event 后，`|p_model − 可成交价|` 的中位 < 0.02，或按规则 3 的成交中位净额 ≤ 0 → 无 edge，进待选区；(3) GISTEMP 发布日晚于 `endDate` 兜底日（会导致判最低档），出现一次即降权。
- 不许的自我安慰：不能用「没成交所以没亏」当正结果；不能拿 2026-08/09 这两个 hit 当样本。

## 成本与容量

- **费用（Gamma 实取）**：月温市场每个 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`，与 GUIDE 第 8 节天气类 `0.05` 一致。按 GUIDE 公式 `费用 = 份数 × 费率 × p × (1−p)`：
  - `p=0.10` → 每份 `0.05×0.10×0.90 = 0.0045`，占投入 **4.5%**；
  - `p=0.33` → `0.05×0.33×0.67 = 0.011055`，占投入 **3.35%**；
  - `p=0.905` → `0.05×0.905×0.095 = 0.0043`，占投入 **0.47%**。
  - maker 费 0，返对手费的 `rebateRate=0.25`。
- **每笔成本 = 费 + 半个买卖价差**。已关闭市场的盘口取不到，所以**价差只能用假设值 1¢（半价差 0.5¢）**，这是本条最软的一个数，如实标出。
- **单笔能放多少**：200 USDT/档、400 USDT/月。按 `p=0.33`、200 USDT 计，吃单费约 6.7 USDT，半价差约 3 USDT —— 需要模型概率比价格高 ≈0.05 才划算（规则 3 的 2¢ 垫 + 3.35% 费 + 0.5¢ 半价差）。**这个门槛已经不低**，而证据 5 显示市场大多数时候比模型更极端，所以机会可能不多。
- **占款天数**：月末后进场 → GISTEMP 发布（月中）→ UMA 结算，约 **10–20 天**。
- **一个月多少次机会**：1 个 event/月（含变体事件也是同一次）。近期成交额 11k–25k USD（sept 2026 = 11,127.86，oct 2026 = 2,522.64），**400 USDT/月已经接近近期单 event 成交额的 2–16%**，5,000 USDT 完全用不上——容量不是约束，机会频率才是。
- **结论**：小资金能放下，但**这条不会给出可观的绝对收益**（每月 1 次、每次几百美元、edge 未知），只能作为组合里与加密/趋势完全不相关的一条腿。

## 风险

- **口径误差就是主要风险**：σ≈0.057 对 0.05 的档宽，意味着「知道了 ERA5 整月」仍然有三分之一左右的机会落在相邻档。这是本策略的天花板，不是可以优化掉的执行细节。
- **ERA5 与 GISTEMP 不是同一个量**：ERA5 是再分析（含模式、同化），GISTEMP 是台站+ERSST 观测插值，极区处理和海洋覆盖都不一样。全样本 R²=0.9698 看着好，但残差近正态只是观察，没有理论保证；El Niño/La Niña 转换年、火山年可能系统性偏移。
- **发布时点不可控**：GISTEMP 只说 "around the middle of every month"，没有确切日期。停牌时间（本例 2026-10-09）也可能早于我预期，导致规则 1 的窗口被压到几天。
- **兜底条款**：如 NASA 到 `endDate` 前仍未发布，判**最低档**。买的是 `>1.4x` 档就直接归零。极低概率但全损。
- **修订**：规则明说「regardless of whether the figure … is later revised」，所以后面被修不影响结算——这是**对我有利**的一条，不用担心修订风险，但也不能反过来靠它。
- **成交额崩塌**：同模板从 2025-01 的 4.93M 掉到 2026-09 的 11k，说明关注度在退。池子小 → 价差宽、模型 edge 更容易被半价差吃掉。
- **数据可得性退化**：历史盘口已经取不到（三个已关闭事件返回空 history），如果 Pulse 的 CSV 或 CLOB 的 history 接口再收紧，这条就没法检验了。
- **平台**：多个同族事件 `restricted=true`；negRisk 市场的转换/赎回有额外步骤。本条只用「买 YES」，不涉及转换。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付钱方是「ERA5 已有整月答案但按旧信息定价」的对手方；机制的量是发布时滞（ERA5 月末后 3–5 天 vs GISTEMP「around the middle of every month」），我把两个时滞都引了原文。但「这笔钱会持续存在」只有机制推理 + 1 个事件的盘口观察，**没有时序证据**，所以只写「满足」不写「强」。
2. **有免费数据能检验：不确定** — 预测侧完全够：ERA5 日均 CSV 1940 起、GISTEMP 月表 1880 起，都免费免密钥，我跑了 945 个月回归 + 132 个月样本内校准检验。**但价格侧不行**：已关闭月温事件的 CLOB 价格历史返回空，只在 2026-09 一个事件上拿到 469 个点。所以历史上 ≥30 个独立结果的「价格」拿不到。
3. **小资金能做：满足** — 400 USDT/月，远低于 2,500 单场所与 5,000 总资金；不加杠杆；买 YES 最大亏损就是本金。容量写清了：近期单 event 成交额 11k–25k USD，5,000 USDT 放不满。
4. **不重复：不确定（需主审确认）** — 我跑了 `grep -ril -E "temperature|Copernicus|ERA5|hottest|气温|温度" known/ bots/*/CLAIMS.md bots/*/entries/`，命中只有：`bots/quant/CLAIMS.md`（B12 本条自己的认领）、`bots/dot/entries/dot-001-late-day-observed-max-tail.md` 与 `dot-002-ensemble-calibration.md`（**城市日最高温**，结算源是 NOAA 站点 timeseries，日内/次日，变量是本地日最高值）、`bots/quant/entries/quant-005-post-count-bracket-model.md`（只在「机制相邻」一句里提到气温）。`known/KNOWN.md` 里 `grep -in -E "weather|temp|气温|天气"` **无任何命中**。差异：本条变量是**全球月平均距平**、结算源是 **NASA GISTEMP LOTI 月表**、周期是**月**、数据是 **ERA5 再分析**；dot 两条是**城市日最高温 + NOAA 站点观测 + 日**。收益来源（月频发布时滞 vs 日内已观测极值）不同，不是换城市换档位的变体。仓库内是否有更深层的同类条目**我未逐条读完**，请主审裁决。
5. **扣成本后粗算够用：不确定** — 没有回测。`observed_net_return = null`，`backtest_count = 0`（只表示没有价格回测，不表示收益为 0）。模型侧有 0.169 nats 的 log loss 改善（132 个月），但证据 5 显示在唯一能看的那个事件上市场比模型更自信，而模型是对的——这说明按模型做**方向是对的**，但按 `p−ask` 的正负去挑档，在该样本上会挑到 `1.40–1.44`（模型 0.282 / 价格 0.105，结算为 0），单份净 `−0.1097`。一次结果不构成统计，但它明确说明 edge 没有被证明。
6. **两周内能检验：不满足** — 独立结果按事件计，1 个/月，两周最多 2 个，30 个要 15 个月以上。按 GUIDE 第 2 节第 6 条，本类应进**待选区**；可先做的是滚动重估校准（用 1948-01 … 2026-09 的 945 个月，两周内能跑完）。
7. **出处可查：满足** — 每条规则数字都有 URL + 访问日期；回归、命中率、log loss、残差 sd、nowcast 都是我用自己的脚本 `b12_calc.py` 跑的，公式与中间量写在正文；Gamma 的 volume/liquidity/openInterest 标了「来源自报，未核实」；三个事件返回空 history、以及 `prices-history` 只到一个时点，这两个失败都照写，不掩饰。

## 出处

- https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c — 访问 2026-10-20 — 已读（规则原文、6 档标题与 `outcomePrices`、`feeSchedule` rate 0.05、`negRisk=true`、`restricted=true`、`endDate=2026-11-02T04:59:00Z`、volume 11127.859859、openInterest 8452.463409）
- https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489 — 访问 2026-10-20 — 已读（`>1.29ºC` 档 `["1","0"]`；档位为 `<1.10 … >1.29`，与 9 月不同）
- https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all — 访问 2026-10-20 — 已读（同族事件清单、slug、endDate、volume）
- https://gamma-api.polymarket.com/public-search?q=hottest&limit_per_type=25&events_status=all — 访问 2026-10-20 — 已读（`where-will-2026-rank-among-the-hottest-years-on-record` 的规则原文与 `Global_Mean_Estimates…/graph.txt` 结算源；volume 3796097.779246）
- https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset=0..200&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（`pm_category=weather` 板块存在，已关闭事件 ≥300 个；含 `will-any-month-of-2026-be-the-hottest-on-record` volume 154744.657949）
- https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv — 访问 2026-10-20 — 已读（31,721 行；表头注释含 5 天/3 天时滞原文；末行 `2026-10-17,…,0.894,PRELIMINARY`；`Last updated: 19 Oct 2026`）
- https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json — 访问 2026-10-20 — 已读（`{"daily":20261017,"monthly":202609,"annual":2025}`）
- https://pulse.climate.copernicus.eu/ — 访问 2026-10-20 — 已读（HTML 200；页面 JS 中取到上列两个 `sites.ecmwf.int` 数据 URL；`/api/…` 路径本身返回 HTML 而不是 JSON，未当接口用）
- https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt — 访问 2026-10-20 — 已读（2026 行：108 123 130 116 113 117 124 142 138 **** …）
- https://data.giss.nasa.gov/gistemp/updates_v4/ — 访问 2026-10-20 — 已读（「Graphs and tables are updated around the middle of every month …」）
- https://clob.polymarket.com/prices-history?market=9561250571098553460692263040980922664627749350602993898138030564733182354111&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（469 点，2026-09-20T05:00Z 0.465 → 2026-10-09T16:00Z 0.905）
- https://clob.polymarket.com/prices-history?market=<may-2026 / january-2026 / december-2025 首档 YES token>&interval=max&fidelity=60 — 访问 2026-10-20 — 已尝试，三者均返回空 `history`，故无法做价格回测
- 本地脚本 `notes/batch2-verification/quant-015.md 附录脚本 b12_calc.py` 与 `b12_backtest.py` — 2026-10-20 运行 — 自己算（回归、132 月样本内校准检验、nowcast、31 个已关闭事件计数）
