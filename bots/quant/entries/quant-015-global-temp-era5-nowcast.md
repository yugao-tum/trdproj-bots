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
instruments: Polymarket「<Month> <YYYY> Temperature Increase (ºC)」月距平阶梯（通常 6 档、少数 5 档；档宽 0.04–0.07°C 随月变化，negRisk）
venues: Polymarket
data: Copernicus Climate Pulse 全球日均 2m 气温 CSV（免费免密钥，1940-01-01 起，最新 2026-10-18）+ NASA GISTEMP v4 LOTI 月表（免费免密钥，1880-01 起，最新 2026-09）；Polymarket Gamma/CLOB（免费免密钥；CLOB prices-history 只有 2 个事件非空，其中已关闭 1 个）+ Polymarket data-api 逐笔成交（免费免密钥，已关闭市场可读，覆盖 29 个已关闭月）；GISTEMP 首发布用 Wayback Machine 存档做代理（覆盖 30/33 个月），并用 29 个市场结算档反推首发布档
test_2w: 独立结果按事件（每月 1 个，同月 lower/higher-strikes 变体合并）计；历史 29 个已关闭月已回测，模型 log loss 1.5263 vs 市场 0.7913（23/29 市场更好），按 400 USDT/月仓位 29 个月 −7,049 USDT → 已触发失败标准；两周最多再添 2 个新结果，凑不到 30
status: 待核
confidence: 中
---

> **2026-10-20 改为待核**：占用 quant-006 降为草稿后空出的第 1 轮名额。门槛自查不变：2、4 不确定，5、6 不满足；按 GUIDE 第 2 节本条预期结局是**待选区**，提交理由是 321 个月走前校准（log loss 1.3638 vs 均匀 2.0794）与可复核的结算规则证据，不是收益证明。正文中“`status` 只给 `草稿`”的说法写于改状态之前，结论（应进待选区）不变。

> **2026-10-21 加固（H-quant-015）**：新增 data-api 逐笔成交的 **29 个已关闭月可成交价回测**（脚本、stdout、逐月/逐笔 CSV 见 `bots/quant/notes/scheduler/scratch/H-quant-015/`）。结果**负面**：同一走前模型对市场的 log loss 为 **1.5263 vs 0.7913**（市场在 **23/29** 个月更好，符号检验 **p=0.0023**）；按条目的 200 USDT/档、400 USDT/月仓位，29 个月合计 **−7,049 USDT**（月均 **−243**，仅 **5/29** 个月为正，bootstrap 95% CI **−352..−118**）。因此本条**建议降为草稿/待选区**，不是可交易 edge。`status` 与 `date` 按队列要求未改。此前“没有价格回测”的结论已被本轮推翻；详见证据 9。

整理说明：本版把原稿的「样本内校准」整段替换为真正的走前检验（walk-forward）：目标期为 2000-01 至 2026-09，共 321 个月；每个目标月只用该月之前的数据估 ERA5→GISTEMP 映射。预测、概率、命中率、log loss、PIT、覆盖率都由本地脚本重算，公式和完整输出见 `bots/quant/notes/scheduler/scratch/quant-015/walkforward.out`（复用已合并记录）。价格侧：CLOB `prices-history` 仍然只有 2 个事件非空（已关闭 1 个），但 data-api 逐笔成交可以还原 **29 个已关闭月**的成交价；本轮据此补做了 29 个月的价格回测（证据 9）。结论是**市场更准、按条目仓位扣费后亏损**，不是收益证明。

## 一句话

每个月**月末之后、NASA GISTEMP 月中更新之前**，用 Copernicus Climate Pulse 的 ERA5 日均全球 2m 气温算出整月均值，按「只用过去 120 个月估出来」的线性映射转换成 GISTEMP 口径，得到各档月距平的概率；只在模型概率明显高于可成交价、且高过「吃单费 + 半个价差 + 口径误差垫」时买该档 YES，持有到 GISTEMP 发布结算。

## 钱从哪里来

付钱的是**在 ERA5 已经给出整月答案之后、仍按「月还没过完」的直觉或旧新闻定价的对手方**。这个时滞是结构性的：ERA5 的整月数据在月末后约 3–5 天就齐了（Pulse 文件原文写 CDS 更新有 5 天延迟、单日值通常 3 天后转 FINAL），而 GISTEMP 月表是「around the middle of every month」才更新（原文见数据节）。中间的约 8–12 天就是信息差。

但本轮证据把这句话拆成了两半：

- **预测侧成立**：321 个走前月里，模型对实际所在 0.05°C 档的平均 log loss 是 **1.3638 nats**，8 结果均匀分布是 **2.0794**，naive persistence 是 **2.0608**；PIT 均值 0.5003、KS=0.0372，80% 区间覆盖率 0.7726。也就是说，ERA5 整月值确实能显著降低 GISTEMP 档位的不确定性。
- **收费侧已被本轮价格回测否定**：29 个已关闭月、决策时点固定在次月 5 日 00:00 UTC，模型对市场的 log loss 为 **1.5263 vs 0.7913**（市场在 **23/29** 个月更好，符号检验 **p=0.0023**）。按条目的 200 USDT/档、400 USDT/月仓位，29 个月合计 **−7,049 USDT**，月均 **−243**，仅 **5/29** 个月为正。唯一一个同时有 CLOB 中间价的已关闭事件（2026-09）也给出同样方向：模型 1.1083、市场 0.3740。付款动机可以解释，但「这笔钱会持续存在、且大过市场已消化的信息」已被现有证据否定；市场在次月 5 日基本已经把 ERA5 整月值定价进去。

## 规则

**模板（Gamma 事件 `september-2026-temperature-increase-c`，2026-10-20 已读，HTTP 200）**

- 标题 `September 2026 Temperature Increase (ºC)`；`startDate=2026-08-31T13:37:03Z`；`endDate=2026-11-02T04:59:00Z`；`negRisk=true`；`restricted=true`；`volume=11127.859859`、`openInterest=8452.463409`（来源自报，未核实）。
- 6 个互斥档：`<1.30ºC`、`1.30–1.34ºC`、`1.35–1.39ºC`、`1.40–1.44ºC`、`1.45–1.49ºC`、`>1.49ºC`。规则原文：「The brackets are mutually exclusive and collectively exhaustive: each range is inclusive of both of its stated endpoints, and the reported anomaly (to the nearest 0.01ºC) falls within exactly one bracket.」
- **结算数据源不是 Copernicus，是 NASA**：原文「the figure found in the table titled "GLOBAL Land-Ocean Temperature Index in 0.01 degrees Celsius" under the column "Sep" in the row "2026"（`https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt`）」。
- 不理会事后修订：原文「An anomaly within a named bracket for September 2026 is necessary and sufficient to resolve this market immediately once the data becomes available, regardless of whether the figure for September 2026 is later revised.」
- 缺数据兜底：原文「If no information for September 2026 is provided by NASA by November 1, 2026, 11:59 PM ET, this market will resolve to the lowest range bracket.」`endDate=2026-11-02T04:59:00Z` 就是 2026-11-01 23:59 ET 的兜底截止。
- **2026-09 已结算且与现行表一致（我核过）**：2026-10-20 抓取时事件 `closed=true`，6 档全部 `umaResolutionStatus=resolved`；GISTEMP 表 2026 行 Sep 值为 **138**（=1.38°C），落在 `1.35–1.39` 档；该档 `outcomePrices=["1","0"]`。同表 Aug=**142**（=1.42°C），与 8 月模板 `august-2026-temperature-increase-c-20260728155540489` 的 `>1.29ºC` 档结算一致。
- **档宽逐月变化**：2026-08 模板是 `<1.10 / … / >1.29`，2026-09 是 `<1.30 / … / >1.49`。边界随上一年水平移动，不是固定网格，每次都要重读规则。
- 同族年度市场：`where-will-2026-rank-among-the-hottest-years-on-record`、`will-any-month-of-2026-be-the-hottest-on-record`；本条只做月度，年度只记模板。

**预测规则（走前，已按此跑完）**

1. 目标月 M 只用 **M 之前最近 120 个完整重叠月**（ERA5 与 GISTEMP 都齐全）。对 `GISTEMP = a + b × ERA5月均距平` 做 OLS；`σ` 取残差样本标准差（分母 n−2）。参数每月重估，不固定。
2. 目标月 ERA5 月均距平 = 该月全部日值 `ano_91-20` 的算术平均；要求日数完整。当前最新可算的完整月是 2026-09（30 天，ERA5 月均 +0.8191）。以 2026-09 为例，滚动 120 个月估出的参数是 `a=0.591262`、`b=0.970383`、`σ=0.056299`，`pred=1.3861`。
3. 每档概率 `p_i = Φ((hi_i−pred)/σ) − Φ((lo_i−pred)/σ)`。档界按「0.01 四舍五入」处理：标称 `1.35–1.39` 对应实数区间 `[1.345,1.395)`，即 `lo = 标称下界 − 0.005`、`hi = 标称上界 + 0.005`。
4. 只在 `p_i − ask_i > 0.05 × ask_i × (1−ask_i) + 0.01 + 0.02`（吃单费 + 半个价差假设 1¢ + 口径误差垫 2¢）时**吃单买 YES**；不做裸卖。回测与前向统一在**次月 5 日 00:00 UTC** 取价（此时 ERA5 整月已齐，GISTEMP 尚未发布）；证据 9 的 29 个月就是这样取的。
5. 单档在险 ≤200 USDT，单月全档 ≤400 USDT，同时在手 ≤2 个月；总资金 5,000 USDT、单场所 ≤2,500 USDT 的约束天然满足。
6. 出场：不主动平仓，持有到 GISTEMP 发布后 UMA 结算（约 10–20 天）。提前平仓要再付一次费和价差。
7. 熔断：若 `pred` 落在某档边界 ±0.01 内，该档和相邻档都不做（边界翻档风险最高）。
8. 明确不做：月内前 20 天就建仓（噪声大）、把 Copernicus 的 `monthly=202609` 状态字段当结算值（结算看 GISTEMP）、把 lower-strikes / higher-strikes 变体当独立机会重复计数。

## 证据

### 1）规则与结算（已读，非自报）

GISTEMP 表 2026 行原文（2026-10-20 抓取，HTTP 200，17,039 bytes）：
`2026   108  123  130  116  113  117  124  142  138 **** **** ****   **** ***    112  120  128 ****  2026`
→ Jan 1.08、Feb 1.23、Mar 1.30、Apr 1.16、May 1.13、Jun 1.17、Jul 1.24、**Aug 1.42**、**Sep 1.38**（单位 0.01°C）。这两个数分别对上 8 月与 9 月市场的结算结果，**是我核对的，不是来源自报**。

### 2）走前检验的设计（先定规则，再看结果）

- 目标期 **2000-01 … 2026-09，共 321 个月**；每个目标月严格只用之前的数据。
- 主设定：**rolling 120 months**（预先选定）；另跑两个稳健性变体：expanding（1940 起全部历史）和 rolling 60。
- 参数：OLS 的 a、b、σ（σ 分母 n−2），每月重估。
- 命中率：模型点预测 `pred` 所在的 0.05°C 档（`floor((x+0.005)/0.05)`）是否等于实际值所在档；均匀随机基准约 1/6=0.1667。
- log loss：为了同时公平比较模型和 persistence，预先把结果分成 **8 个互斥结果**：以「上个月实际 GISTEMP」为锚，6 个内部 0.05°C 档覆盖 `[上个月−0.15, 上个月+0.15)`，再加下尾、上尾两个池化结果。模型和 persistence 都按各自 Normal 分布算这 8 个概率；均匀分布是 1/8，`ln 8 = 2.0794`。
- persistence：点预测 = 上个月实际 GISTEMP；σ 用同一 120 个月窗口内「本月−上月」差值的样本标准差。
- PIT：`u = Φ((actual−pred)/σ)`；若校准良好，u 应近似 Uniform(0,1)。另报中心 50%/80%/90% 区间的实际覆盖率。

### 3）主结果：321 个走前月（`walkforward.py`）

| 样本 | n | 模型命中 | persistence 命中 | 模型 log loss | persistence log loss | 均匀 log loss | 80% 覆盖 | 90% 覆盖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL 2000-01..2026-09 | 321 | **0.3832** (123/321) | 0.1308 (42/321) | **1.3638** | 2.0608 | 2.0794 | 0.7726 | 0.8816 |
| 2000-2012 | 156 | 0.4679 (73/156) | 0.1218 (19/156) | 1.2976 | 2.0580 | 2.0794 | 0.8077 | 0.9231 |
| 2013-2026 | 165 | 0.3030 (50/165) | 0.1394 (23/165) | 1.4264 | 2.0634 | 2.0794 | 0.7394 | 0.8424 |
| 2020-2026 | 81 | 0.3086 (25/81) | 0.1358 (11/81) | 1.4649 | 2.0675 | 2.0794 | 0.7901 | 0.8642 |
| 2024-2026 | 33 | 0.3636 (12/33) | 0.1212 (4/33) | 1.7819 | 2.0789 | 2.0794 | 0.7273 | 0.8485 |
| 2024-04..2026-09 | 30 | 0.3667 (11/30) | 0.1333 (4/30) | 1.7697 | 2.0740 | 2.0794 | 0.7667 | 0.8667 |

- PIT 全样本：**mean=0.5003，sd=0.2893，KS vs U(0,1)=0.0372**；十分位计数 `[31,29,41,25,40,36,33,21,23,42]`，没有明显堆积在两端。
- 但 2024–2026 的 KS 升到 **0.1592**，80% 覆盖降到 **0.7273**，log loss 升到 **1.7819**（仍低于均匀 2.0794，但优势只剩 0.2975 nats）。**近期在退化，不能把全样本 1.3638 当成现在可用的精度。**
- 命中率在近期仍有 0.303–0.367，高于 1/6=0.1667，但低于 0.05 档在 σ≈0.056 下的理论上限（约 0.33–0.35）；这和「σ 略宽、偶发大跳变」一致。2026 年 3 月是最坏月：pred=1.107、实际=1.300、单月 log loss=6.964，属于典型的大跳变，不是可忽略的离群点。

### 4）稳健性变体（全部跑了，不藏）

| 设定 | n | 命中 | 模型 log loss | 80% 覆盖 | PIT mean | PIT KS | 2024-2026 模型 log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| **rolling 120（主）** | 321 | 0.3832 | 1.3638 | 0.7726 | 0.5003 | 0.0372 | 1.7819 |
| expanding（1940 起） | 321 | 0.3084 | 1.5173 | 0.9128 | 0.6061 | 0.2279 | 1.7241 |
| rolling 60 | 321 | 0.3894 | 1.3669 | 0.7352 | 0.5039 | 0.0511 | 1.7956 |

- expanding 明显更差：PIT 均值 0.6061、80% 覆盖 0.9128、KS 0.2279，说明把 1940 年以来的老关系一起塞进去会系统性地「过度自信地宽」；这也反过来说明 **rolling 120 不是随便挑的，是主设定里预先写死的，变体只作稳健性对照**。
- rolling 60 的 80% 覆盖只有 0.7352，近端更差；主设定仍取 120。

### 5）最新一个月的档位概率（2026-09，走前模型）

`pred=1.3861`、`σ=0.0563`、实际 GISTEMP=1.38（命中 `1.35–1.39` 档）：

| 标称档 | 实数区间 | 模型概率 |
|---|---:|---:|
| 1.25–1.29 | [1.245,1.295) | 0.0467 |
| 1.30–1.34 | [1.295,1.345) | 0.1799 |
| **1.35–1.39** | [1.345,1.395) | **0.3301** |
| 1.40–1.44 | [1.395,1.445) | 0.2895 |
| 1.45–1.49 | [1.445,1.495) | 0.1212 |
| 1.50–1.54 | [1.495,1.545) | 0.0242 |

这张表说明两件事：(a) 即使 ERA5 整月值已经知道，最高档概率也只有约 0.33，因为 0.05°C 的档宽比 σ≈0.056 还窄；(b) 模型对相邻档（1.40–1.44）仍给 0.2895，翻档是常态，不是尾部事件。

### 6）GISTEMP 首发布 vs 修订（Wayback 代理，本轮新做）

NASA 没有公开的「首发布月表归档」；我改用 Wayback Machine 的 `GLB.Ts+dSST.txt` 历史快照做**首发布代理**：

- CDX 返回 2023-01 起 45 个快照（HTTP 200，16,974 bytes 的 CDX JSON；本地解析 45 个快照）。
- 对 2024-01..2026-09 的 33 个月，取「月末后 14–55 天内、且表里已有该月值」的最早快照，得到 **30 个月**的首发布代理；2025-09、2026-07、2026-09 未覆盖（快照时序不够）。
- 首发布 vs 现行修订值：**平均修订 +0.002°C，平均绝对修订 0.012°C，sd 0.0158°C，最大绝对修订 0.04°C**；**0.05°C 档不变的 23/30 = 0.7667**，0.01°C 完全相同的只有 8/30。
- 在这 30 个月上，走前模型对**修订值**命中 9/30，对**首发布值**命中 7/30（差 −2）。换档的 7 个月是：2024-01（1.21→1.25，pred 1.253）、2024-05（1.14→1.16，pred 1.220）、2024-06（1.25→1.23，pred 1.246）、2024-11（1.31→1.29，pred 1.294）、2025-06（1.03→1.06，pred 1.052）、2025-08（1.14→1.17，pred 1.068）、2026-03（1.28→1.30，pred 1.107）。
- **用市场结算反推首发布档（本轮新做，比 Wayback 硬）**：29 个已关闭事件的 `outcomePrices` 直接给出当时的结算档。把该档区间与现行 GISTEMP 修订值对照：**22/29 = 0.7586** 仍落在首发布档内，**7/29 = 0.2414** 换档。换档月为 **2024-06、2024-09、2024-11、2025-06、2025-10、2026-03、2026-08**。在这 29 个月上，走前模型对**首发布档**命中 **11/29 = 0.3793**，对**现行修订档**命中 **13/29 = 0.4483**（差 −2）。市场按首发布结算，所以用修订值回测会高估命中率。
- **Wayback 代理与市场结算的差异**：Wayback 也给出 7/30 换档（0.7667），量级对；但换档月份只有 **4/7** 与市场结算重合（2024-06、2024-11、2025-06、2026-03），并多报 2024-01、2024-05、2025-08。Wayback 快照受抓取时点和页面临时状态影响，**只能当量级参考，不能当月度首发布值**；市场结算档才是硬证据。
- **结论**：首发布和修订值大约每 4 个月就有 1 个月换 0.05°C 档；市场按首发布结算，所以用修订值回测会**略微高估**命中率（29 个月上 13/29 vs 11/29）。这个偏差不大，但不能忽略。Wayback 代理不是官方首发布档案，且 3 个月没覆盖；市场结算档补上了这个缺口，但仍不知道首发布的**具体数值**，只能知道落在哪一档。

### 7）Polymarket 月温事件与 CLOB 价格历史（本轮重查）

- `public-search?q=temperature increase&limit_per_type=100&events_status=all`（2026-10-21 抓取 HTTP 200，约 829 KB；响应字节数会小幅变化）返回 **33 个事件**：**32 个 closed、1 个 open**，共 **191 个 YES token**。
- 按**标题里的月份**（不是 slug；`july-2025-temperature-increase-c-394` 的实际标题是 **August 2025**）归并：**30 个不同日历月（2024-04 … 2026-10，缺 2024-07）**；其中已关闭的 **29 个月**。变体/重复：2025-04 有 main + lower-ranges，2025-10 有 main + lower-strikes，2026-08 有 main + higher-strikes；2025-07 只有一个事件，2025-08 是 slug 带 `july` 的那个。按 GUIDE 第 2 节第 6 条，同月同一结算源只算 **1 个独立结果**。
- **CLOB `prices-history` 仍然很窄**：对 191 个 YES token 逐个查 `https://clob.polymarket.com/prices-history?market=<token>&interval=max&fidelity=60`：**只有 2 个事件返回非空 history** —— `september-2026-temperature-increase-c`（6/6 档，**444–448 点**）和 `october-2026-temperature-increase-c-20260928t160000000z`（6/6 档，**475–481 点**，未关闭）。其余 **31 个事件的所有 token 全部返回 `history=[]`**。点数和首点是时变的：2026-10-20 的 454–458 点/`2026-09-20T16:00Z` 到 2026-10-21 已变成 448 点/`2026-09-21T02:00Z`。
- **data-api 逐笔成交补上了价格侧**：`https://data-api.polymarket.com/trades?market=<conditionId>&start=...&end=...&limit=500&offset=N` 对已关闭市场可读；29 个已关闭月、每个 4–6 档都能取到决策时点之前的成交。用“最后一笔 ask 侧成交 + 1¢”做可成交价代理，29 个月全部有价格覆盖。这是**成交打印**，不是完整订单簿；且含少量同钱包对倒的异常打印（例：2026-09 `<1.30` 档同一钱包 0xF769… 在 1 小时内 0.707 买、0.015 卖），所以证据 9 同时给了去掉同钱包往返的敏感性。
- 因此「已关闭且有价格」不再只有 1 个：**CLOB 中间价只有 1 个，data-api 成交价有 29 个**。但 29 仍差 1 个到 GUIDE 的 30 个历史独立结果；第 30 个月（2026-10）目前是 open，只能前向记录。
- 唯一同时有 CLOB 中间价的已关闭事件（2026-09）n=1 对照：在 **2026-10-05 00:00Z** 取 6 档最近中间价并归一化，模型给结算档 0.3301，市场给 0.6880；实际结算在该档，**模型 log loss 1.1083，市场 0.3740**。到 **2026-10-09 16:00Z**，市场该档 0.9050（归一化 0.9972），模型仍是 0.3301。方向和 29 个月回测一致：**市场已经消化了 ERA5**。
- 成交额（来源自报，未核实）：`september-2026` 11,127.86、`october-2026` 2,522.64、`august-2026` 15,901.87；更早的 2025-01 是 4,925,571.47、2025-09 是 2,415,315.78。同一模板成交额在 18 个月里掉了两个数量级，容量假设不能拿 2025 年的数。

### 8）频率

- 2024-04 至 2026-10 共 31 个日历月，**30 个有事件（缺 2024-07）**、33 个事件，平均约 **1.06 个事件/月**；按独立结果合并后仍是**每月 1 个**。已关闭的是 2024-04..2026-09 的 **29 个月**。
- 所以本条的独立结果上限是 **12 个/年**，两周最多 2 个；本轮把 29 个历史月全部用完，仍差 1 个到 GUIDE 的 30 个门槛，第 30 个只能等 2026-10 结算后前向记录。

### 9）历史可成交价格回测：29 个已关闭月（本轮新做，负面）

**方法（先写死，再看结果）**

- **决策时点**：目标月次月 5 日 00:00 UTC。例：2026-09 在 2026-10-05 00:00Z 决策；此时 ERA5 整月已齐，GISTEMP 尚未发布。
- **价格**：data-api 逐笔成交。优先取决策前最后一笔 YES `BUY`；没有则取 NO `BUY` 的补价（1−p）；再没有才用 YES/NO `SELL`（bid + 2¢）。买价 = 该打印 + 1¢ 半价差。不做 maker 假设。
- **模型**：与证据 3 完全相同的 rolling-120 走前模型；每个目标月只用之前 120 个月估 a、b、σ，不重新拟合、不调参。
- **结算**：Gamma `outcomePrices`，即市场自己的首发布结算档；**不用现行 GISTEMP 修订值**。这样结算侧没有前视。
- **费用**：`0.05 × ask × (1−ask)`/份（天气类 5%，Gamma `feeSchedule.rate=0.05`），不吃 maker 返佣。
- **触发**：沿用规则 4，`p_model − ask > fee + 1¢ + 2¢`。
- **仓位**：逐笔先按 1 份记，报每份净额；再按条目的真实仓位（每月 400 USDT、单档 ≤200、触发档等权，最多 6 档）折算月度 P&L。
- **独立结果**：一个日历月 1 个，同月 main/lower-ranges/higher-strikes 变体不重复计数；29 个已关闭月 = 29 个独立结果。

**主结果（`backtest_015.out`、`primary_months.csv`、`primary_trades.csv`）**

| 指标 | 结果 |
|---|---:|
| 独立月数 / 有完整价格覆盖 | 29 / 29 |
| 模型平均 log loss | **1.5263** |
| 市场平均 log loss | **0.7913** |
| 配对差（市场−模型）均值 / 中位 | **−0.7350 / −0.7885** |
| 市场更好的月数 | **23/29**（模型 6/29；符号检验 **p=0.0023**） |
| 模型点预测命中首发布结算档 | **11/29 = 0.3793** |
| 模型点预测命中现行修订档 | 13/29 = 0.4483 |
| 触发交易 / 命中 | 74 / 6 |
| 每份净额合计 / 投入 | +0.2372 / 5.5423 = **+4.28%** |
| 每份净额中位 / 均值 | **−0.0256 / +0.0032** |
| 400 USDT/月真实仓位（400 预算、单档 ≤200） | **−7,049.06 USDT**，月均 **−243.07**，正收益月 **5/29**，bootstrap 95% CI **−351.5..−118.0** |
| 去掉最大 1 / 3 笔盈利后的每份净额 | **−0.6277 / −2.3028** |

- **正的头条数字是假象**：每份等权时合计 +0.2372，但中位数 −0.0256，且 74 笔里只有 6 笔命中；把最大 3 笔盈利去掉就变成 −2.3028/份。按条目的固定 USDT 仓位，低价长尾票会买到更多份数，亏损被放大，29 个月合计 −7,049 USDT。
- **敏感性都不救**：决策推迟到次月 7 日，市场 log loss 降到 0.4296（市场 27/29 更好），交易净额 −2.7897/份（−76.7%）；推迟到 12 日，市场 0.1578（29/29 更好），净额 −2.2114/份（−104.7%）。零手续费仍为 **−6,534.93 USDT**；去掉同钱包往返异常打印后市场 log loss 0.7843、P&L 不变。方向一致：**越晚市场越准，策略越亏**。
- **数据质量限制（照写）**：data-api 是成交打印，不是订单簿；同钱包对倒会打出远离中间价的异常价（2026-09 `<1.30` 档同一钱包 1 小时内 0.707 买、0.015 卖），所以主结果另给了去往返敏感性。对唯一同时有 CLOB 的 2026-09，data-api 代理归一化结算档概率 0.5211，CLOB 中间价 0.6880，差 0.1669；但两者都远高于模型 0.3301，结论不变。成交打印也可能滞后（74 笔触发的中位年龄 5.0h、最大 131h），1¢ 半价差是保守假设，真实盘口可能更宽。
- **结论**：这不是“样本不足、无法判断”。29 个独立月、价格覆盖完整，**市场在统计上显著优于模型，按条目仓位扣费后亏损**。即使模型对档位的点预测有 37.9% 命中（高于 1/6），也不足以覆盖市场已经消化的信息和长尾票的仓位放大。**建议把本条降为草稿/待选区，不应按“可交易 edge”继续推进。**

**逐月明细**

| 月 | pred | 首发布结算档 | 现行 GISTEMP | 模型 log loss | 市场 log loss | 触发笔数 | 净额/份 |
|---|---:|---|---:|---:|---:|---:|---:|
| 2024-04 | 1.2380 | >1.31 | 1.32 | 2.3429 | 1.3839 | 2 | -0.1842 |
| 2024-05 | 1.2201 | 1.10-1.16 | 1.16 | 1.8480 | 1.3695 | 2 | -0.2910 |
| 2024-06 | 1.2459 | 1.16-1.22 | 1.23 | 1.2026 | 0.7701 | 2 | -0.4864 |
| 2024-08 | 1.2772 | >1.29 | 1.30 | 0.9679 | 1.7883 | 3 | +0.7066 |
| 2024-09 | 1.2899 | 1.23-1.28 | 1.21 | 1.0888 | 0.6445 | 2 | -0.0806 |
| 2024-10 | 1.3588 | 1.29-1.34 | 1.34 | 1.1844 | 0.3389 | 2 | -0.1481 |
| 2024-11 | 1.2945 | 1.30-1.34 | 1.29 | 1.1782 | 1.8868 | 3 | +0.7844 |
| 2024-12 | 1.3193 | 1.25-1.29 | 1.26 | 1.4338 | 2.0620 | 3 | +0.8204 |
| 2025-01 | 1.3435 | >1.34 | 1.37 | 0.7148 | 0.1446 | 2 | -0.1561 |
| 2025-02 | 1.1998 | 1.25-1.29 | 1.25 | 1.7938 | 0.1378 | 2 | -0.1244 |
| 2025-03 | 1.2215 | 1.32-1.36 | 1.36 | 3.1529 | 0.2380 | 3 | -0.0535 |
| 2025-04 | 1.1742 | 1.22-1.26 | 1.24 | 1.7100 | 0.6430 | 1 | -0.6322 |
| 2025-05 | 1.1023 | 1.05-1.09 | 1.07 | 1.2179 | 0.4294 | 2 | -0.0473 |
| 2025-06 | 1.0521 | 1.00-1.04 | 1.06 | 1.2152 | 2.0396 | 3 | +0.8167 |
| 2025-07 | 1.0271 | 1.00–1.04 | 1.02 | 1.0651 | 0.1377 | 4 | -0.1779 |
| 2025-08 | 1.0675 | >1.10 | 1.17 | 1.3868 | 0.2092 | 3 | -0.2365 |
| 2025-09 | 1.2334 | >1.19 | 1.24 | 0.2843 | 1.6066 | 1 | +0.7509 |
| 2025-10 | 1.2701 | 1.20–1.24ºC | 1.18 | 1.4402 | 0.9984 | 2 | -0.3741 |
| 2025-11 | 1.2247 | 1.20–1.24ºC | 1.21 | 1.0795 | 0.6579 | 3 | -0.2615 |
| 2025-12 | 1.0608 | 1.05–1.09ºC | 1.05 | 1.0782 | 1.3253 | 4 | +0.6564 |
| 2026-01 | 1.0840 | 1.05–1.09ºC | 1.08 | 1.0912 | 0.4706 | 3 | -0.1016 |
| 2026-02 | 1.1094 | 1.20–1.24ºC | 1.23 | 2.9102 | 1.0156 | 3 | -0.1559 |
| 2026-03 | 1.1070 | 1.25–1.29ºC | 1.30 | 5.0559 | 0.8394 | 3 | -0.0827 |
| 2026-04 | 1.0967 | 1.15–1.19ºC | 1.16 | 1.8574 | 0.2834 | 2 | -0.2017 |
| 2026-05 | 1.1192 | 1.10–1.14ºC | 1.13 | 1.0854 | 0.1041 | 3 | -0.1299 |
| 2026-06 | 1.1329 | 1.15–1.19ºC | 1.17 | 1.2819 | 0.1311 | 3 | -0.1559 |
| 2026-07 | 1.2429 | 1.20–1.24ºC | 1.24 | 1.1589 | 0.3177 | 2 | -0.0591 |
| 2026-08 | 1.4122 | 1.38–1.41ºC | 1.42 | 1.3271 | 0.3476 | 3 | -0.0619 |
| 2026-09 | 1.3861 | 1.35–1.39ºC | 1.38 | 1.1083 | 0.6259 | 3 | -0.0954 |
## 数据

- **Copernicus Climate Pulse，全球日均 2m 气温 CSV（免费、免密钥、无需注册）**：`https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv`。文件头注释（去掉行首 `#` 后的原文）：「This file contains daily global mean near-surface (2m) air temperature data from ERA5 from 1940 to 2026 as well as daily temperature anomalies relative to the 1991-2020 reference period.」列为 `date,2t,clim_91-20,ano_91-20,status`，单位 deg. C。2026-10-21 抓取 HTTP 200，1,198,262 bytes，31,722 行；末行 `2026-10-18,15.260,14.371,0.889,PRELIMINARY`；注释写「Last updated: 20 Oct 2026」。
- **发布时滞（原文）**：「The ERA5 data available in the CDS are updated with a 5-day delay (120 hours) behind real-time. Note that the time series below includes values based on ERA5 data not yet available in the CDS (for days 2 to 5 behind real-time).」以及「If preliminary, the values will likely change (slightly) once the final ERA5 data for the day are available (typically 3 days behind real-time).」
- **Pulse 状态文件**：`https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json` → `{"daily": 20261018, "monthly": 202609, "annual": 2025}`（2026-10-20，HTTP 200，63 bytes）。即整月 ERA5 到 2026-09 已可用。
- **NASA GISTEMP v4 月表（免费、免密钥）**：`https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt`（HTTP 200，17,039 bytes；2026 行到 Sep 有值；表头来源行写 `GHCN-v4 1880-09/2026 + SST: ERSST v5 1880-09/2026`）。发布节奏原文（`https://data.giss.nasa.gov/gistemp/updates_v4/`，HTTP 200，19,967 bytes）：「Graphs and tables are updated around the middle of every month using the current data files provided by NOAA/NCEI (GHCN v4: meteorological stations, ERSST v5: ocean).」
- **GISTEMP 首发布代理**：Wayback CDX `https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6`（HTTP 200，16,974 bytes），取快照正文 `https://web.archive.org/web/<timestamp>id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt`。这是第三方存档，不是 NASA 官方首发布。
- **Polymarket 规则与结算**：`https://gamma-api.polymarket.com/events?slug=<slug>`（规则原文、`feeSchedule`、`outcomePrices`）；`https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all`（找同族）。
- **Polymarket 价格（两套，用途不同）**：`https://clob.polymarket.com/prices-history?market=<YES token>&interval=max&fidelity=60` 只有 2 个事件非空，适合做单点中间价对照；`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`（已关闭市场可读，`start`/`end` 为 Unix 秒）可还原 29 个已关闭月的逐笔成交，适合做证据 9 的成交价回测。data-api 是**成交打印**，不是完整订单簿。
- **缺失，必须写清**：31 个事件的 191 个 YES token 在 CLOB `prices-history` 里全部返回空 history；只有 2 个事件有 CLOB 数据（已关闭 1 个）。所以**完整历史盘口仍然取不到**，只能用 data-api 成交打印 + 1¢ 半价差做代理；真实价差、深度、排队都无法还原。ERA5 的「当时首发布值」也没有免费历史归档，本文用的是当前再分析值；这是另一个未解决的 vintage 偏差。

## 两周内怎么检验

- 独立结果**按事件数**：一个月 1 个，两周最多 2 个，**不可能在两周内拿到 30 个新结果**。按 GUIDE 第 2 节第 6 条，本条本应进**待选区**。
- 已经做完、不需要等市场的事：
  - 2000-01…2026-09 的 **321 个月走前重估**（`walkforward.py`，两个免费 CSV），逐月命中、log loss、PIT、覆盖率和三个变体，写在证据 3/4；
  - **29 个已关闭月的可成交价回测**（data-api；`backtest_015.py`），写在证据 9。
- 历史独立结果是 **29 个**（2024-04…2026-09 的已关闭月；缺 2024-07，2026-10 仍 open），**差 1 个到 GUIDE 的 30 个门槛**；靠两周前向最多再添 2 个，补不上 1 个历史月。
- 前向记录（可选，从 2026-10-20 起）：每天记 ERA5 的 `ano_91-20` 与 `status`、6 档 `bestBid/bestAsk/outcomePrices`、GISTEMP 表是否出现该月值（自证发布时滞天数），以及首发布 vs 后来修订值。至少连续记 12 个月，才有 12 个新独立结果。
- **失败标准（写死）**：
  1. 未来 12 个月走前 log loss ≥ `ln 8 = 2.0794`，或命中率 ≤1/6 → 模型无用，弃；
  2. 累计到 ≥5 个已关闭且有价格的事件后，模型 log loss ≥ 市场 log loss，或按规则 4 的成交中位净额 ≤0 → 无 edge，进待选区或弃；
  3. 首发布 vs 修订的换档率 >30%，或 GISTEMP 在兜底日之后才发布（判最低档）出现一次 → 降权；
  4. 不允许用「没成交所以没亏」当正结果，也不允许拿 2026-08/09 两个 hit 当样本。
- **按写死标准的判定（2026-10-21）**：已有 **29 个已关闭且有价格**的事件，超过第 2 条的「≥5」；模型 log loss **1.5263 > 市场 0.7913**，且按规则 4 的成交中位净额 **−0.0256/份 ≤0**。**第 2 条触发 → 判 FAIL，进待选区/草稿，不应按可交易 edge 推进。** 第 1 条未触发（29 个月模型 LL 1.5263 < 2.0794），第 3 条未触发（实际换档率 7/29=24.1% <30%）。

## 成本与容量

- **费用（Gamma 实取）**：月温市场每个 `feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`，与 GUIDE 第 8 节天气类 `0.05` 一致。按 GUIDE 公式 `费用 = 份数 × 费率 × p × (1−p)`：
  - `p=0.10` → 每份 `0.05×0.10×0.90 = 0.0045`，占投入 **4.5%**；
  - `p=0.33` → `0.05×0.33×0.67 = 0.011055`，占投入 **3.35%**；
  - `p=0.905` → `0.05×0.905×0.095 = 0.0043`，占投入 **0.47%**。
  - maker 费 0，返对手费的 `rebateRate=0.25`。
- **每笔成本 = 费 + 半个买卖价差**。已关闭市场的完整盘口取不到；证据 9 用「最后 ask 侧成交 + 1¢」做代理，等于假设半价差 1¢。这是**偏乐观**的：2026-09 的 CLOB 中间价与 data-api 成交打印相差可达 16.7¢（归一化结算档 0.688 vs 0.521），真实价差可能远宽于 1¢。
- **单笔能放多少**：200 USDT/档、400 USDT/月。按 `p=0.33`、200 USDT 计，吃单费约 6.7 USDT，半价差约 3 USDT —— 需要模型概率比价格高约 **0.05** 才划算（规则 4 的 2¢ 垫 + 3.35% 费 + 0.5¢ 半价差）。**这个门槛已经不低。**
- **占款天数**：月末后进场 → GISTEMP 发布（月中）→ UMA 结算，约 **10–20 天**。
- **一个月多少次机会**：1 个事件/月（含变体事件也是同一次）。近期成交额 11k–16k USD（2026-09 = 11,127.86，2026-08 = 15,901.87，2026-10 = 2,522.64），**400 USDT/月已接近近期单 event 成交额的 2–16%**；5,000 USDT 完全用不上——容量不是约束，机会频率和 edge 才是。
- **本轮已有价格回测，且是负的**：`backtest_count = 29`（已关闭月），`observed_net_return`（400 USDT/月、单档 ≤200、扣 5% 吃单费和 1¢ 半价差）**为负**：29 个月合计 **−7,049.06 USDT**，月均 **−243.07**，仅 **5/29** 个月为正。按每份等权看是 +0.2372/份（+4.28%），但中位 −0.0256/份，且去掉最大 3 笔盈利后为 **−2.3028/份**；正的头条数字完全依赖少数低价长尾命中。**扣成本后正收益没有被证明，现有证据反而指向负收益。**

## 风险

- **口径误差就是主要风险**：σ≈0.056 对 0.05 的档宽，意味着「知道了 ERA5 整月」仍然只有约 33% 的概率命中最高档，翻到相邻档是常态。
- **关系在近期漂移**：2024–2026 log loss 1.7819，明显差于全样本 1.3638；2026-03 单月 log loss 6.964。变暖加速、El Niño/La Niña 转换会让「过去 120 个月」的线性关系滞后。这不是可以靠调 σ 消掉的执行细节。
- **ERA5 与 GISTEMP 不是同一个量**：ERA5 是再分析（含模式、同化），GISTEMP 是台站+ERSST 观测插值，极区处理和海洋覆盖都不一样。全样本 R² 高只说明平均关系好，不保证极端月。
- **首发布 ≠ 修订值**：市场按首发布结算，但本轮回测用的是现行修订表；用 29 个市场结算档反推，**7/29 = 24.1%** 换 0.05°C 档，模型对首发布档命中 **11/29**、对修订档 13/29。真实结算精度比修订值回测低。
- **市场已经消化 ERA5（本轮已有统计证据）**：29 个已关闭月里，市场在次月 5 日的 log loss **0.7913**，模型 **1.5263**，市场在 **23/29** 个月更好（符号检验 p=0.0023）。唯一有 CLOB 的 2026-09 也是市场 0.3740 vs 模型 1.1083。规则 4 在这类月份要么不触发，要么触发在「市场已经知道」的一侧。
- **低价长尾票的仓位放大**：按每份等权，触发交易合计 +0.2372/份；按条目的固定 USDT 仓位，29 个月却是 −7,049 USDT。原因是 74 笔里只有 6 笔命中，低价票在固定金额下买到最多份数，亏损被放大。**不要用每份等权的正均值当收益证据。**
- **成交打印不是订单簿**：data-api 有同钱包对倒打出的异常价（2026-09 `<1.30` 档同一钱包 1 小时内 0.707 买、0.015 卖），也有 5 天以上的陈旧打印；1¢ 半价差是乐观假设。去掉同钱包往返后主结论不变（市场 LL 0.7843、P&L −7,049），但单笔可成交价仍有误差。
- **发布时点不可控**：GISTEMP 只说 "around the middle of every month"，没有确切日期；停牌时间可能早于预期，窗口被压缩。
- **兜底条款**：NASA 到 `endDate` 前仍未发布则判**最低档**；买 `>1.4x` 档会直接归零。概率低但全损。
- **成交额崩塌**：同模板从 2025-01 的 4.93M 掉到 2026-09 的 11k，池子小 → 价差宽、模型 edge 更容易被半价差吃掉。
- **数据可得性退化**：完整历史盘口取不到（31/33 个事件的 CLOB `prices-history` 返回空）；data-api 成交打印目前可读 29 个已关闭月，但如果它再收紧、或 Pulse CSV 停止更新，这条就没法继续检验。
- **平台**：多个同族事件 `restricted=true`；negRisk 市场转换/赎回有额外步骤。本条只用「买 YES」，不涉及转换。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付钱方是「ERA5 已有整月答案但按旧信息定价」的对手方；量是发布时滞（ERA5 月末后 3–5 天 vs GISTEMP「around the middle of every month」），两个时滞都引了原文。但「这笔钱会持续存在」已被 29 个月价格回测否定：市场在次月 5 日更准，按条目仓位扣费后亏损。
2. **有免费数据能检验：不确定（29/30）** — 预测侧完全够：ERA5 日均 CSV 1940 起、GISTEMP 月表 1880 起，都免费免密钥，已跑 321 个月走前检验。价格侧本轮用 data-api 成交打印拿到 **29 个已关闭月** 的可成交价，**差 1 个到 30**；CLOB `prices-history` 仍只有 1 个已关闭事件可用。第 30 个月（2026-10）目前 open，只能前向记录。
3. **小资金能做：满足** — 400 USDT/月，远低于 2,500 单场所与 5,000 总资金；不加杠杆；买 YES 最大亏损就是本金。容量写清了：近期单 event 成交额 11k–16k USD，5,000 USDT 放不满。
4. **不重复：不确定（需主审确认）** — 本轮重跑 `grep -ril -E "temperature|Copernicus|ERA5|hottest|气温|温度" known/ bots/*/CLAIMS.md bots/*/entries/`，命中：`bots/quant/CLAIMS.md`（本条自己的认领）、`bots/dot/entries/dot-001-late-day-observed-max-tail.md`、`dot-002-ensemble-calibration.md`（**城市日最高温**，NOAA 站点 timeseries，日内/次日）、`bots/quant/entries/quant-005-post-count-bracket-model.md`、`bots/quant/entries/quant-012-earthquake-count-base-rate.md`（只在文字里出现关键词，不是气温策略）。`known/KNOWN.md` 里 `grep -in -E "weather|temp|气温|天气"` **无命中**。差异：本条变量是**全球月平均距平**、结算源是 **NASA GISTEMP LOTI 月表**、周期是**月**、数据是 **ERA5 再分析**；dot 两条是**城市日最高温 + NOAA 站点观测 + 日**。收益来源不同，不是换城市换档位的变体。仓库内是否有更深层同类条目**我未逐条读完**，请主审裁决。
5. **扣成本后粗算够用：不满足（已有 29 个月证据）** — 模型 log loss 1.5263 vs 市场 0.7913（23/29 市场更好，p=0.0023）；按 400 USDT/月、单档 ≤200、5% 吃单费和 1¢ 半价差，29 个月合计 **−7,049.06 USDT**，月均 −243.07，仅 5/29 月为正。每份等权的 +4.28% 去掉最大 3 笔盈利即变成 −2.3028/份。**扣成本后不是“够用”，是负的。**
6. **两周内能检验：不满足** — 独立结果按事件计，1 个/月，两周最多 2 个；历史月已用尽也只有 29 个（缺 2024-07，2026-10 未结算），**差 1 个到 30**。按 GUIDE 第 2 节第 6 条，本类应进**待选区**。
7. **出处可查：满足** — 每条规则数字都有 URL + 访问日期；走前回归、命中率、log loss、PIT、覆盖率、首发布代理、29 个月价格回测都是我用自己的脚本跑的，脚本与 stdout 在 `bots/quant/notes/scheduler/scratch/H-quant-015/`；Gamma 的 volume/liquidity/openInterest 标了「来源自报，未核实」；CLOB 31 个事件空 history、Wayback 只覆盖 30/33 个月、data-api 含同钱包异常打印，这些失败都照写，不掩饰。

## 出处

- https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c — 访问 2026-10-21 — 已读（HTTP 200，26,351 bytes；规则原文、6 档标题与 `outcomePrices`、`feeSchedule` rate 0.05、`negRisk=true`、`restricted=true`、`endDate=2026-11-02T04:59:00Z`、volume 11127.859859、openInterest 8452.463409；6 档全部 `umaResolutionStatus=resolved`）
- https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489 — 访问 2026-10-21 — 已读（HTTP 200，25,839 bytes；`>1.29ºC` 档 `["1","0"]`；档位为 `<1.10 … >1.29`）
- https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-higher-strikes — 访问 2026-10-21 — 已读（HTTP 200，25,390 bytes；`1.38–1.41ºC` 档 `["1","0"]`，说明 2026-08 首发布落在 1.38–1.41，现行 GISTEMP 1.42 是后来修订）
- https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all — 访问 2026-10-21 — 已读（HTTP 200，约 829 KB；33 个事件、32 closed、1 open、191 个 YES token；按标题 **30 个不同月份**，其中 **29 个已关闭**）
- https://gamma-api.polymarket.com/events?tag_slug=weather&limit=100&offset=0..400&closed=true&order=endDate&ascending=false — 访问 2026-10-21 — 已读（5 页各 HTTP 200；扫描 500 个已关闭 weather 事件，标题/slug 含 `temperature increase|how hot will` 的只有 1 个，说明 tag 覆盖不全，事件计数以 public-search 为准）
- https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv — 访问 2026-10-21 — 已读（HTTP 200，1,198,262 bytes，31,722 行；表头注释含 5 天/3 天时滞原文；末行 `2026-10-18,…,0.889,PRELIMINARY`；`# Last updated: 20 Oct 2026`）
- https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json — 访问 2026-10-21 — 已读（HTTP 200，63 bytes；`{"daily":20261018,"monthly":202609,"annual":2025}`）
- https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt — 访问 2026-10-21 — 已读（HTTP 200，17,039 bytes；2026 行：108 123 130 116 113 117 124 142 138 **** …）
- https://data.giss.nasa.gov/gistemp/updates_v4/ — 访问 2026-10-21 — 已读（HTTP 200，19,967 bytes；渲染文本「Graphs and tables are updated around the middle of every month …」，HTML 里 middle of every month 是链接文字）
- https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6 — 访问 2026-10-21 — 已读（HTTP 200，16,974 bytes；82 个快照，2023-01 起 45 个）
- https://web.archive.org/web/20251112105542id_/https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt — 访问 2026-10-21 — 已读（HTTP 200，16,934 bytes；2025 行含 Jan–Aug 值）
- https://clob.polymarket.com/prices-history?market=<YES token>&interval=max&fidelity=60（对 191 个 token 逐一请求）— 访问 2026-10-21 — 已读（脚本 `check_clob.py`；只有 2 个事件非空，其余 `history=[]`；非空 token 共 12 个）
- https://clob.polymarket.com/prices-history?market=9561250571098553460692263040980922664627749350602993898138030564733182354111&interval=max&fidelity=60 — 访问 2026-10-21 — 已读（HTTP 200，11,857 bytes；2026-09 `1.35–1.39` 档 **448 点**，首点 `2026-09-21T02:00Z` p=0.45，末点 `2026-10-09T16:00Z` p=0.905；点数和首点时变）
- https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N（`start`/`end` 为 Unix 秒；对 29 个已关闭月、每事件 4–6 档逐一请求）— 访问 2026-10-21 — 已读（脚本 `fetch_trades.py`；29 个已关闭月全部有决策前成交；74 笔触发，逐笔表 `primary_trades.csv`）
- 本地脚本 `bots/quant/notes/scheduler/scratch/H-quant-015/` 下的 `fetch_core.py`、`fetch_trades.py`、`backtest_015.py`、`check_clob.py`、`verify_sources.py`、`revision_check.py`、`crosscheck_0905.py` — 2026-10-21 运行 — 自己算（来源复核、29 月成交价回测、CLOB 191 token、首发布档反推、data-api vs CLOB 对照）；stdout 为同名 `.out`，逐月/逐笔为 `primary_months.csv` / `primary_trades.csv`
- 复用已合并记录：`bots/quant/notes/scheduler/scratch/quant-015/walkforward.out`、`firstrelease_local.out`（321 月走前回归与 Wayback 首发布代理，2026-10-20 运行；本轮只复核，不重跑）
