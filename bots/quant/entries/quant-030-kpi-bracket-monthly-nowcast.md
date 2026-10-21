---
id: quant-030
name_zh: 季报KPI分档：月度经营数据抢跑
name_en: Polymarket quarterly KPI brackets — front-running with public monthly operating data
bot: quant
date: 2026-10-21
market: polymarket
pm_category: finance
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「<公司> 本季 <KPI> 落在哪一档」区间市场，以及「<公司> 本季 <KPI> 是否 above <阈值>」阈值阶梯（Gamma tag `kpis`）
venues: Polymarket
data: Gamma `tag_slug=kpis`（2026-10-20 实取 192 个已关闭事件 / 931 个市场、102 个开放事件 / 494 个市场；2026-10-21 复核 196/951、102/497；规则原文、outcomePrices、feeSchedule、volume）；CLOB prices-history（已关闭市场可取，单次窗口 ≤6 天）；data-api trades（conditionId，逐笔，约最近 2 万笔/市场）；公司 IR / SEC 8-K / 月度经营数据；BTS T1（月度，滞后约 2 个月）。全部免费免密钥
test_2w: 独立结果按公司-季度计；历史上同口径只有 5 个已结算事件（航空载客率 2、Costco 同店 1、Boeing 交付 1、TSMC 营收 1；严格规则内 0），前向每季约 2–4 个，两周内拿不到 30 个；失败标准：前向累计 ≥10 个事件时，规则净 PnL 中位 ≤0，或 nowcast 落在结算档的比例 ≤ 同批市场价隐含概率
status: 草稿
confidence: 中
---

整理说明：本条的家族普查、价格与逐笔成交最初在 2026-10-20 用 Gamma / CLOB / data-api 现取现算；2026-10-21 按 review `c20261020-170337-research` 的 B29 条逐项复取，并在 `bots/quant/notes/scheduler/scratch/P-quant-030/` 重跑了家族统计、案例逐笔与**历史可成交价回测**（`verify_family.py`、`verify_cases.py`、`inspect_trades.py`、`backtest.py` 及同名 `.out`）。**历史上严格规则内样本是 0 个**（放宽“距阈值 ≥2%”后才只有 TSM above-41 1 笔），所以下面按“案例研究 + 预注册前向规则 + 一次小样本回测”写，不把它们冒充统计检验。结论：**作为可交易策略应当放弃（drop），不建议第 2 轮升 `待核`**；若保留，只作为“月度经营数据抢跑”的边界记录。

## 一句话

只在“公司已经公开的月度经营数据足以把季度 KPI 分档钉死”时，买 nowcast 所在的那一档（或阈值阶梯的对应边）；本轮证据显示这类市场在 2026 年只有约 5 个已结算样本（4 个月度 + 1 个季度经营数据）：**Boeing 交付、TSM above-40 在信息发布后数小时内就被定价，没有滞后；TSM above-41 在发布后约 100 秒有一笔 taker `BUY No @0.9129`（净 +7.4¢/份），但 nowcast 距 41 只有 1.95%，按预注册的“≥2%”规则不算规则内，且月度 TWD 与季度 USD 需汇率折算；Delta 载客率命中但只有 37.55 份；UAL 载客率说明缺一个月时 1pp 档会猜错。** 因此本条当前是“模板 + 前向记录”，**不是可上线策略**。

## 钱从哪里来

付款方是**没有把已公开的月度经营数据加总进季度 KPI 的人**：公司月度/季度经营数据先于财报发布，季度值往往就是月度值的加总或加权平均，而分档市场仍按“分析师一致预期 + 叙事”报价。理论上，谁先完成加总，谁就在信息上领先。

但本轮实测把这个故事削掉了一大半：

- 真正“同口径、公开、可在财报前拿到”的事件极少（192 个已关闭 KPI 事件里只有 5 个：4 个月度序列 + Boeing 的季度交付公告；10-21 复核 196 个，仍是这 5 个）；
- 其中 Boeing、TSMC above-40 在发布当天就被打到 0.98 / 0.99，几乎没有可吃的价差；
- 留下窗口的两个案例（TSMC above-41、Delta 83–85）盘口极薄，单笔只有几十到几百份；
- Costco 的 6.5–7.5 档在 05-22 有一笔 `BUY No @0.92`，但同一钱包在 22:38:53–22:38:55 的 3 秒内于 6 个档各买 NO（篮式成交），不是可执行的 YES 卖价；财报前没有 YES 卖价。

所以“钱从哪里来”的机制成立，但**持续性和容量都不成立**；本条的主要价值是把边界写清楚，避免把“月度数据可抢跑”误当成一条宽策略。

## 规则

### 1）Polymarket 结算规则原文（Gamma `description`，2026-10-20 已读）

区间/分档模板（以 UAL Q3 载客率、MCD Q3 同店、Costco Q3 同店为例，原文同构）：

> This market will resolve according to United Airlines' consolidated passenger load factor, for the upcoming third fiscal quarter, as reported in its official company earnings materials.
>
> The specified metric will be considered as reported in the company's official earnings materials. Subsequent revisions will not be considered.
>
> If the specified company's official earnings materials for the specified quarter are released, and the specified metric is not included, this market will resolve to the lowest bracket.
>
> If the specified company does not release quarterly earnings materials for the specified quarter by November 30, 2026, 11:59 PM ET, this market will resolve to the lowest bracket.
>
> If the reported value falls exactly between two brackets, this market will resolve to the higher range bracket.
>
> If the specified metric is reported as a range rather than a specific number, the midpoint of the range will be used for resolution of this market.
>
> The resolution source for this market is United Airlines' official company earnings materials, including press releases, investor presentations, and regulatory filings. If the specified metric is not reported in these materials, recordings or transcripts of the company's earnings webcast may also be used.
>
> Note: This market will resolve based on the most numerically precise version of the specified metric reported in the company's official earnings materials. Only the specified metric will be considered; alternate versions that differ in definition or scope from the specified metric will not be considered.

要点：

- **结算源是公司自己的财报材料**（新闻稿、投资者演示、监管文件；必要时财报电话会录音/记录），不是数据商、不是媒体。
- **只认首次披露**，后续修订不认。
- **缺指标 / 逾期不发 → 最低档**（注意：区间市场是“lowest bracket”，不是“No”；阈值阶梯才是“No”）。
- **正好落在两档之间 → 较高档**。
- **披露为区间 → 取中点**。
- **用最精确的版本**；口径不同的替代版本不认。

Costco 事件额外把“US adjusted comparable sales growth”定义为**剔除汽油价格和汇率影响后的同店增长**（event `description` 原文）：

> For the purposes of this market, US adjusted comparable sales growth refers to comparable sales growth excluding the impact of gasoline prices and foreign exchange, as reported by Costco in its official earnings materials.

阈值阶梯模板（Boeing / TSM，原文同构）：

> This market will resolve to “Yes” if Boeing’s total number of commercial airplane deliveries for the first fiscal quarter of 2026, as reported in its official company earnings materials, is above the listed amount. Otherwise, this market will resolve to “No”.
> …
> If the specified company’s official earnings materials for the specified quarter are released, and the specified metric is not included, this market will resolve to “No”.
> …
> If the specified metric is reported as a range rather than a specific number, the midpoint of the range will be used for resolution of this market.

即：阈值阶梯是“above X?” 的独立二元市场，**不是互斥分档**；同一事件多个阈值可以同时为 YES。

### 2）预注册交易规则（前向，未验证）

只在下述条件同时满足时下单：

1. **同口径**：季度 KPI 的定义与已公开月度序列一致（例如 Costco 的 “US adjusted comps”、Boeing 的 “commercial deliveries”、TSMC 的 “consolidated net revenue”（月度 TWD / 季度 USD 需汇率，属边界）、航空公司的 “RPM/ASM”）。口径不一致（如 consolidated 含 regional、 monthly 只含 mainline）时，必须有历史映射并通过第 3 条。
2. **月份覆盖**：至少覆盖季度 3 个月中的 2 个月；缺的月份只能用“过去 8 个同季度的月度→季度映射”补，且补后的 nowcast 必须离最近档边界 ≥0.5pp（1pp 档）或 ≥1.0pp（2pp 档）。
3. **价差门槛**：现在是 `p ≤ 0.75`（买 YES）或 `p_NO ≤ 0.92`（买 NO），且 nowcast 距阈值至少 2%（阈值阶梯）或距档边界 ≥0.5pp（区间档）。
4. **流动性门槛**：该**事件**的 Gamma `volume ≥ 20,000` 美元，目标市场自身 `volume ≥ 2,000`，且最近 24h 至少有 2 笔 ≥50 份的成交；否则不交易（本轮 5 个案例里只有 UAL 与 TSM 过事件门槛；DAL $9,704、Boeing $13,844、Costco $3,881 均不过，且 DAL 的 37.55 份、Boeing 的 29 份低于 50 份门槛，只作为观察）。
5. **仓位**：单事件 ≤200 USDT，同时在手 ≤10 个事件，总占用 ≤1,500 USDT；持有到 UMA 结算，不中途平仓。
6. **熔断**：同一季度已实现亏损 ≥3 个事件时停止新开仓。
7. **明确不做**：不因为“月度数据看起来接近”就在档边界附近赌；不在 `volume < 20,000` 的市场里把一边的成交价当成可执行卖价；不把同一公司的多个阈值/多档当成多个独立结果。

## 证据

### 1）家族普查（我自己数的）

- `https://gamma-api.polymarket.com/events?tag_slug=kpis&limit=100&closed=true&order=endDate&ascending=false` 全量翻页（offset 0…200）：**2026-10-20 快照 192 个已关闭事件、931 个市场**（2026-10-21 复核为 **196 个已关闭事件、951 个市场**，新增 4 个已结算事件）；`endDate` 覆盖 2026-03 至 2027-01。
- 同端点 `closed=false&order=endDate&ascending=true`：**2026-10-20 快照 102 个开放事件、494 个市场**（2026-10-21 复核 **102 个事件、497 个市场**）；其中 **61 个 endDate 在 2026-10、24 个在 2026-11**（10-21 复核为 57 / 26，属时间漂移）。
- 费率：已关闭市场 **2026-10-20 快照 849 个 `rate=0.04`、50 个 `0.05`、4 个 `0.07`、28 个 `feeSchedule=null`**（2026-10-21 复核同分布，另 20 个 `rate=0`）。**开放市场 2026-10-21 复核：464 个 `rate=0`（`feeType=zero_fees`）、27 个 `0.04`、6 个 `0.05`**——2026-10-20 写入时把“开放市场 486 个 0.04、8 个 0.05”写错了，已更正；开放市场以免费为主，因此 §成本 的 0.04 是**保守上界**，不是当前开放市场的实际费率。
- 事件累计成交额（Gamma `volume`，**来源自报，未核实**）：已关闭 **2026-10-20 快照合计 $4,599,544，中位 $8,102，p90 $39,168，最大 $893,324**（Tesla Q1 交付）；开放合计 **$1,761,353**，中位 **$3,780**，p90 **$9,163**。2026-10-21 复核：已关闭合计 **$4,703,475**、中位 **$8,353**；开放合计 **$1,682,295**、中位 **$3,850**、p90 **$7,410**。两组都只是带时间戳的快照，不是稳定常数。
- 按标题关键词（2026-10-20 快照）：`revenue` 68、`comparable sales` 12、`margin` 9、`ARR` 7、`organic` 6、`deliveries` 5、`load factor` 2、`monthly active` 2、`subscriber` 2（10-21 复核 `revenue` 69、`margin` 10、`load factor` 3）。**绝大多数是季度才披露的指标，没有同口径月度序列。**

### 2）同口径公开经营数据事件（人工分类，全部 5 个；4 个月度 + Boeing 季度交付）

| 事件 | 指标 | 公开月度/季度经营数据 | nowcast | 实际档 | 信息发布后首笔成交（taker 方向/价/份数） | 结论 |
|---|---|---|---|---|---|---|
| Boeing Q1 2026 交付（`boeing-airplane-deliveries-above-in-q1`） | commercial deliveries | Boeing 2026-04-14 直接公布 Q1 交付 **143**（季度经营数据，不是月度）（737 114 + 767 6 + 777 8 + 787 15） | 143 | above 140 = YES；above 145 = NO | above 140：04-14 18:27:46 `BUY Yes @0.98` 29 份；above 145：18:32:22 `BUY No @0.98` 29 份 | **无滞后**：当天下午已 0.98；但公告只写日期、无小时，不能单独证明非前视 |
| TSM Q2 2026 营收（`…tsm-q2-revenue-usd…`） | revenue USD | 月度营收 Apr 410,726 + May 416,975 + Jun 442,680 = **NT$1,270,381m**；2026-07-13 公布 June；按公司 31.60 折 **$40.20B**（按指引 31.7 折 $40.08B） | 40.1–40.2 | above 40 = YES；above 41 = NO | above 41：07-13 **05:32:08**（发布后约 100 秒）`BUY No @0.9129` 514.01 份；06:46:29 的 `SELL No @0.8604` 是 taker 卖 NO，不是买入口。above 40：05:31:55 `BUY Yes @0.9345` 721.54 份 | above-41 有约 **+7.4¢/份（扣费+1¢，+8.1%）** 的吃单窗口；above-40 无滞后 |
| Costco Q3 FY2026 US adjusted comp（`costco-q3-us-adjusted-comparable-sales-growth`） | US adjusted comps | 2026-05-06 公布 April：US adjusted **8.0%**；March US adjusted **6.2%**（二手）；Q3 12 周只覆盖其中 8 周 | 简单平均 ≈7.1% | **6.8%（US）；total company 6.6%** | 6.5–7.5 档首笔是 05-22 22:38:55 `BUY No @0.92` 20 份（**同一钱包在 3 秒内于 6 个档各买 NO 的篮式成交**，不是 YES 卖价）；该档首笔 `BUY Yes` 在 05-28 20:15:05、@0.88、11.25 份，已在财报发布后 | **不是可执行缺口**：只有 NO 买盘/篮式成交，没有财报前的 YES 卖价 |
| Delta Q2 2026 载客率（`delta-dal-q2-passenger-load-factor`） | consolidated LF | BTS T1 月度（二手，引用 BTS）：Apr 82.7%、May 84.9%；June 88.1%（财报前未发布） | Apr+May 加权 **83.8%** | **84.8%** → 83–85 档 | 07-02 10:07:10 `BUY Yes @0.2381` 37.55 份（该档首笔 `BUY Yes` 实为 06-24 23:31 @0.46、101.46 份；07-02 只是 May 数据后的观察） | **命中**：83.8 在 83–85；毛 +0.762/份，但 June 缺失、BTS 发布时刻不明、样本只 37.55 份 |
| UAL Q2 2026 载客率（`…ual-q2-consolidated-passenger-load-factor…`） | consolidated LF | 同上：Apr 82.3%、May 82.4%；June 85.9% | Apr+May 加权 **82.3%** | **83.4%** → 83–84 档 | **07-01 09:09:52** `BUY Yes 50 @0.07`（83–84，事后赢）；naive nowcast 实际会选 `<83`，该档在 07-01 附近没有对应的 YES 买盘 | **反例**：naive 部分月 nowcast 落在 82–83，会做错；需用季节补 June 才能得到 83.5 |

按预注册规则严格回看这 5 个事件：**没有 1 个同时满足全部条件**。TSM above-41 差在“nowcast 距阈值 ≥2%”（40.20 vs 41 = **1.95%**），且月度 TWD 与季度 USD 需要汇率折算，严格说不是同一口径；Boeing 是季度数据（不满足“至少 2 个月”）且公告无小时；DAL 只有 37.55 份（不满足 50 份）且 BTS 发布时刻不明；Costco 没有财报前可验证的 YES 卖价；UAL 的 naive nowcast 不在目标档内、`<83` 档会做错。**所以严格规则内样本是 0 个；只把“2% 距离”放宽到 1.9% 后，才剩 TSM above-41 1 笔（净 +8.1%/3 天，约 $469 本金）。**

### 3）三个细节

**(a) Boeing 的公告时刻取不到。** 2026-04-14 的季度交付公告把 Q1 钉死在 143（Boeing 页面只写 `April 14, 2026`，没有小时；重取 2026-10-21 仍无 `dateModified` 可用）。第一笔 above-140 的 YES 成交在 18:27:46 UTC 就是 0.98，above-145 的 NO 在 18:32:22 就是 0.98；这只能证明“当天下午已定价”，**不能单独证明非前视**。CLOB 日线在 04-14 00:00 还显示 0.785 / 0.415，但那是**公告前**的最后价，不是公告后的可执行价。用日线会误以为有 21¢ 缺口。

**(b) TSM 的缺口在 USD 换算，且“首发价”是 taker 买 NO @0.9129，不是 0.8604。** TSMC 新闻页 `dateModified = 2026-07-13T13:30:28+08:00`（= **05:30:28Z**），发布后约 100 秒（05:32:08Z）有一笔 taker `BUY No @0.912887`、514.01 份；这才是可执行的吃单买入口。06:46:29 的 `SELL No @0.860366` 是 taker **卖** NO（对手方挂单买 NO），不能当买入口——上一版把它写成“taker 卖 NO … YES≈0.14 的 12–14¢ 窗口”是错的。按 0.9129 买入，扣 0.04 吃单费（0.00318/份）与 1¢ 半价差，净 **+0.0739/份（+8.1%）**，持有约 3 天；单笔 514 份约 **$469**。**但 40.20 距 41 只有 1.95%（<2%），按预注册规则不算规则内。**

**(c) 航空公司的月度数据只覆盖 2/3 个月，且 mainline ≠ consolidated。** 2026 Q2 的 June 月度数据在财报后才出；用 Apr+May 的 mainline 加权，UAL 82.3%、DAL 83.8%，而最终 consolidated 分别是 83.4%、84.8%。DAL 因为档宽 2pp 而侥幸命中；UAL 的 1pp 档则直接猜错。**这说明“月度数据抢跑”在 1pp 档上需要季节补全模型，而本轮没有足够历史月度数据去验证该模型。**

### 4）没有做的事

- **已做**历史可成交价回测（见下节），但严格规则内 n=0（放宽 2% 距离后 n=1），所以仍不做 log loss、Brier、资金曲线，也不声称胜率。
- 没有构建/验证“缺月季节补全”模型；没有 30 个独立事件。
- 没有历史 L2 盘口（GUIDE 第 8 节：无公开来源），所以所有“半价差”都是假设；Costco 的 0.08 只是 NO 买盘/篮式成交隐含的 YES 买价，不是 YES 卖价。
- 没有把同一公司的多个阈值/多档算成多个结果；Tesla 交付（6 个事件）没有计入，因为它的月度数据是 China CPCA + Europe 注册的**区域代理**，不是同一口径的全球交付。

### 5）历史可成交价回测（扣费）

脚本 `bots/quant/notes/scheduler/scratch/P-quant-030/backtest.py`，stdout 同目录 `backtest.out`；逐笔数据来自 data-api（`trades_<conditionId>.json`），费率取 Gamma 的 `0.04`，费 = `p × 0.04 × (1−p)`/份，净 = `结算 − 买入价 − 费 − 半价差`。半价差基准 1¢，压力 3¢/5¢；买入价一律用 **taker 成交价**，不用日线、mid 或对手方挂单价。

| 案例 | 规则状态 | 采用的可成交 print | 费/份 | 净/份（1¢） | 总净（实际份数） | 说明 |
|---|---|---|---|---|---|---|
| TSM above-41 → NO | **边界**：距阈值 1.95% < 2% | 07-13 05:32:08 `BUY No @0.912887` 514.01 份 | 0.003181 | **+0.073932** | **+$38.00**（本金 $469，+8.1%，约 3 天） | 唯一接近规则；3¢/5¢ 半价差下 +$27.72 / +$17.44 |
| TSM above-40 → YES | 不满足：距阈值 0.5% | 07-13 05:31:55 `BUY Yes @0.934495` 721.54 份 | 0.002449 | +0.053057 | +$38.28（+5.7%） | 无滞后；3¢ 下 +$23.85，5¢ 下 +$9.42 |
| Boeing above-140 → YES | 不满足：季度数据、公告无时刻 | 04-14 18:27:46 `BUY Yes @0.98` 29 份 | 0.000784 | +0.009216 | +$0.27（+0.9%） | 3¢ 半价差转负（−$0.31），5¢ −$0.89 |
| Costco 6.5–7.5 → YES | 不满足：财报前无可执行 YES 卖价 | 财报后 05-28 20:15:05 `BUY Yes @0.88` 11.25 份（上界，不计入规则） | 0.004224 | +0.105776 | +$1.19（+12.0%） | 首笔 05-22 `BUY No @0.92` 是篮式 NO，不是 YES 卖价 |
| DAL 83–85 → YES | 不满足：37.55 份 < 50 份、BTS 时刻不明 | 07-02 10:07:10 `BUY Yes @0.238136` 37.55 份 | 0.007257 | +0.744607 | +$27.96（+312.7%） | 只作观察；该档首笔 YES 是 06-24 @0.46 |
| UAL `<83`（naive） | 反例，不计入 | 07-01 附近 `<83` 无对应 YES 买盘 | — | — | — | naive 会选错档；不计 PnL |

**回测结论：严格规则内 0 笔；唯一接近的 TSM above-41 在 1¢ 半价差下 +8.1%/3 天，但本金只有约 $469，且“距阈值 ≥2%”实际是 1.95%。这不足以支持任何“扣成本后够用”的结论，也不足以进 `待核`。**

## 数据

- Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?tag_slug=kpis&limit=100&offset=<0..200>&closed=true&order=endDate&ascending=false`；`closed=false&order=endDate&ascending=true`。字段：`description`（规则原文）、`outcomePrices`（结算）、`feeSchedule`、`volume`、`clobTokenIds`、`conditionId`。
- CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=&endTs=&fidelity=60`。**单次窗口超过约 6 天会报 `invalid filters: 'startTs' and 'endTs' interval is too long`**；本轮按 6 天分块抓取，脚本已处理。
- data-api（免费免密钥）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=`。返回逐笔 `side`、`price`、`size`、`timestamp`、`outcome`；`side` 是 taker 方向。约最近 2 万笔/市场。
- 公司/官方月度与季度数据：
  - Boeing Q1 交付公告（2026-04-14）：`https://investors.boeing.com/investors/news/press-release-details/2026/Boeing-Announces-First-Quarter-Deliveries/default.aspx`
  - TSMC 2026 月度营收：`https://investor.tsmc.com/english/monthly-revenue/2026`
  - TSMC June 营收新闻（2026-07-13）：`https://pr.tsmc.com/english/news/3323`
  - TSMC Q2 结果（2026-07-16）：`https://pr.tsmc.com/english/news/3326`
  - Costco April sales（2026-05-06）：`https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-April-Sales-Results/default.aspx`
  - Costco Q3 FY2026（2026-05-28）：`https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-Third-Quarter-and-Year-To-Date-Operating-Results-For-Fiscal-2026/default.aspx`
  - Delta Q2 2026 8-K：`https://www.sec.gov/Archives/edgar/data/27904/000002790426000031/dal-20260630.htm`
  - UAL Q2 2026 8-K Ex.99.1：`https://www.sec.gov/Archives/edgar/data/0000100517/000010051726000135/ual_erx06302026xex991.htm`
- BTS T1 月度（二手汇总，引用 BTS T1）：`https://theairside.news/en/invest-united`、`https://theairside.news/en/invest-delta`。**注意**：`data.bts.gov` 的 `q4tb-tbff`（T100 Segment Summary By Carrier）只有 passenger/seat 比值，不是 RPM/ASM；本轮没有用它算载客率。
- 缺失：历史 L2 盘口；Boeing 公告与 BTS T1 的精确发布时间戳（BTS T1 只到月）；Costco 财报前各档的 YES 卖价；TSMC 月度营收的 USD 换算时点（TSMC 新闻页有 `dateModified`，Boeing 没有）。

## 两周内怎么检验

- **独立结果按公司-季度计**，同一公司同一季度的多个档/多个阈值算 1 个；Tesla 的 China/Europe/US 数据源算 1 个，不拆。
- **历史侧已不可能补到 30**：192 个已关闭 KPI 事件（2026-10-21 复核 196 个）里，同口径月度数据只有 5 个（上表），而且 UAL/Boeing/TSM 的规则原文和价格都已取到；再往前没有更多 KPI 事件。
- **前向记录**：从 2026-10-20 起，每天扫 `tag_slug=kpis` 的开放事件，按预注册规则记录：月度数据发布日期、nowcast、档位、下单时 bid/ask、成交价、费用、结算值。预计**每季 2–4 个**同口径事件（2026-10 开放清单里只有 UAL Q3 载客率 1 个；下一个可能是 Costco Q4/Boeing Q3/TSM Q3，均未挂出）。
- **失败标准（写死，事后不改）**：
  1. 前向累计 <10 个独立事件 → 判“证据不足”，不进待选区；
  2. 前向累计 ≥10 个时，规则净 PnL 中位 ≤0；
  3. 或 nowcast 落在结算档的比例 ≤ 同批市场价隐含概率（即没有信息优势）。
- **不允许的自我安慰**：不能把同一公司的不同阈值算成多个结果；不能用“事后知道 June 很旺”去补 nowcast；不能把一边的 NO 成交价当成 YES 的可执行卖价。

## 成本与容量

- **费率（Gamma 实取）**：已关闭 KPI 市场绝大多数 `feeSchedule={"exponent":1,"rate":0.04,"takerOnly":true,"rebateRate":0.25}`（2026-10-20 快照 849/931）；少数 0.05（50 个）与 0.07（4 个，加密相关）。**但 2026-10-21 复核的开放市场 464/497 是 `rate=0`（`feeType=zero_fees`），只有 27 个 0.04、6 个 0.05。** 本条按 **0.04** 算，是保守上界，和 GUIDE 第 8 节“金融 0.04”一致；若实际成交在免费市场，净收益会更高。
- 吃单费（GUIDE 公式 `份数 × 费率 × p × (1−p)`）：
  - `p=0.2381`（DAL）：每份 `0.04×0.2381×0.7619 = 0.00726`，占投入 **3.05%**；
  - `p=0.9129`（TSM NO）：每份 `0.04×0.9129×0.0871 = 0.00318`，占投入 **0.35%**；
  - `p=0.07`（UAL）：每份 `0.04×0.07×0.93 = 0.00260`，占投入 **3.72%**；
  - `p=0.92`（Costco NO）：每份 `0.04×0.92×0.08 = 0.00294`，占投入 **0.32%**。
- **半价差**：历史 L2 取不到。基准按 **1¢**，压力按 **3¢ / 5¢**。在这类薄市场里 5¢ 很常见；TSM NO 在 0.9129 上扣 5¢ 后仍有约 +3.4¢/份（+3.7%），DAL 在 0.2381 上扣 5¢ 仍有约 +0.48/份。
- **毛/净算例（回测口径）**：
  - TSM above-41 taker 买 NO @0.9129，结算 1：毛 `+0.0871`；扣费 0.00318 → `+0.0839`；再扣 1¢ → `+0.0739`/份（**+8.1%**，持有约 3 天）。3¢/5¢ 半价差下为 `+0.0539` / `+0.0339`（+5.9% / +3.7%）。
  - DAL 83–85 YES @0.2381，结算 1：毛 `+0.7619`；扣费 0.00726 → `+0.7546`；再扣 1¢ → `+0.7446`/份（**+312.7%**）。**这个数字大得不合理，只能当方向为正的观察**：n=1、成交只有 37.55 份、且 nowcast 用的是部分月份、BTS 发布时刻不明。
- **容量（Gamma `volume`，来源自报，未核实）**：事件总额 DAL $9,704、UAL $25,551、Boeing $13,844、Costco $3,881、TSM $35,119；对应关键档：DAL 83–85 $5,526、UAL 83–84 $10,338、Boeing above-140 $443、Costco 6.5–7.5 $621、TSM above-41 $5,160。**这些是生命周期总额，不是日成交额**；实际单笔只有 37.55–514 份（约 $9–$469）。5,000 USDT **放不满**，2,500/场所的上限根本不是约束。
- **频率**：同口径事件每季约 2–4 个；按 200 USDT/事件，占用约 400–800 USDT，**资金利用率极低**。

## 风险

- **口径风险（最大）**：月度序列与季度 KPI 经常不是同一口径。航空公司 monthly 是 mainline、季度是 consolidated（含 regional）；Costco 的 4 周 retail month 与 12 周 fiscal quarter 只重叠 8 周；TSMC 月度是 TWD、季度是 USD（汇率与“最精确版本”都可能改口径）。口径错一次，nowcast 直接偏 1–2pp，足够跨档。
- **“最低档”兜底**：区间市场在缺指标/逾期时结算到**最低档**，不是 No；如果你买的是中间档，会全损。阈值阶梯则是“No”。两种模板不能混用。
- **修订不认**：公司后续修订/重述不算；若首次披露是区间，取中点；若首次披露用了不同定义（如 adjusted vs GAAP），只认指定指标。
- **薄市场/一边报价**：Costco 的 0.08 只是篮式 NO 买盘隐含的 YES 买价，不等于 YES 卖价；把一边成交价当成可执行价，是这类市场最常见的假机会（GUIDE 第 8 节明确警告）。
- **信息时点**：BTS T1 滞后约 2 个月，且发布日不是精确到小时；公司月度营收/销售公告通常在月初，但周末/假期会漂移。用“我知道的那天”回测会产生前视偏差。
- **平台/结算**：UMA 结算争议、`endDate` 后到账时间不确定；财报季 KPI 事件集中在 2–3 周，结算拥堵会拉长占款。
- **样本风险**：5 个事件里，TSM above-41 是边界（+8.1%）、DAL 是观察（37.55 份）、UAL 是反例、Costco 不可执行、Boeing 无滞后；TSM above-40 与它们同事件，也无滞后。这不是“胜率 60%”，只是 5 个故事。任何“年化”都不可外推。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足（但弱）** — 付款方是没把已公开月度数据加总进季度 KPI 的人；机制一句话能说清。但实测显示 Boeing/TSM above-40 在数小时内被定价，真正的滞后只出现在薄市场，持续性和容量都弱。
2. **有免费数据能检验：不满足（历史）/ 只能前向** — Gamma + CLOB + data-api + 公司 IR/SEC/BTS 全部免费免密钥；但 192 个已关闭 KPI 事件（2026-10-21 复核 196 个）里同口径公开经营数据只有 **5 个**独立结果（4 个月度 + 1 个季度交付），远低于 30。按 GUIDE 允许“写明从哪天起只能往前记录”，本条从 2026-10-20 起前向记录；历史上不能声称有 30 个。
3. **小资金能做：满足（容量极小）** — 200 USDT/事件、≤10 事件、≤1,500 USDT，远低于 5,000/2,500 限制；但关键档的单笔只有 37.55–514 份（约 $9–$469），5,000 USDT 放不满，容量如实写了。
4. **不重复：满足** — 最接近的是 `quant-020`（财报 EPS 是否高于创建时 SeekingAlpha 一致预期，二元市场、按事件校准），本条是**数值 KPI 的分档/阈值**，结算看公司财报里的 revenue/comps/load factor/deliveries，不看 EPS 一致预期；`quant-010`（流媒体周榜）、`quant-015`（全球气温）、`quant-016`（烂番茄）都是“外部数据 nowcast”，但标的、结算源、数据频率不同。`known/KNOWN.md` 里 `A-A3-poly-cross-market`、`A-A5-poly-complete-set` 是跨市场/全套套利，`M-M4-poly-rewards` 是做市奖励，均不同。`bots/*/entries` grep `load factor|comparable sales|RASM|Boeing|TSM` 无同机制条目。
5. **扣成本后粗算够用：不满足** — 按预注册规则，历史上**严格规则内 0 笔**：TSM above-41 距阈值只有 1.95%（<2%），放宽到 1.9% 后才算 1 笔，按 taker `BUY No @0.9129`、扣 0.04 吃单费与 1¢ 半价差，净 +0.0739/份（+8.1%/3 天，约 $469 本金）；DAL 83–85 的 +313% 只是观察（37.55 份，未过 50 份门槛，BTS 时刻不明）；Boeing/TSM above-40 扣成本后没有 edge；Costco 财报前没有可执行 YES 卖价。n=0（放宽后 n=1），不能判“够用”。
6. **两周内能检验：不满足** — 独立结果按公司-季度计；前向每季约 2–4 个，两周最多 2–3 个，达不到 30；历史只有 5 个（4 个月度 + 1 个季度交付），其中严格规则内 0 个。失败标准已写死，但样本量本身就不够。
7. **出处可查：满足** — 每个数字都有 URL/端点 + 访问日期 + 取数方式；规则原文逐字引用；Gamma `volume` 标了“来源自报，未核实”；BTS 月度标了“二手，引用 BTS T1”；逐笔成交、费率、回测脚本与 stdout 都在 `scratch/P-quant-030/`；未取到的（历史 L2、Boeing/BTS 精确发布时刻、Costco 财报前 YES 卖价）都写了“缺失”。

## 出处

- https://gamma-api.polymarket.com/events?tag_slug=kpis&limit=100&closed=true&order=endDate&ascending=false（offset 0…200）— 访问 2026-10-20，复核 2026-10-21 — 已读（10-20：192 个已关闭事件 / 931 个市场；10-21：196 / 951；费率 0.04 占 849；事件 volume 合计 $4,599,544 / $4,703,475，中位 $8,102 / $8,353）
- https://gamma-api.polymarket.com/events?tag_slug=kpis&limit=100&closed=false&order=endDate&ascending=true — 访问 2026-10-20，复核 2026-10-21 — 已读（10-20：102 个开放事件 / 494 个市场；10-21：102 / 497；费率 10-21：464 个 rate=0、27 个 0.04、6 个 0.05）
- https://gamma-api.polymarket.com/events?slug=united-airlines-ual-q3-consolidated-passenger-load-factor-20261008120016000 — 访问 2026-10-20 — 已读（规则原文全文；5 档价格合计 0.9665：<82 0.0435、82–83 0.08、83–84 0.138、84–85 0.45、85+ 0.255）
- https://gamma-api.polymarket.com/events?slug=mcdonalds-mcd-q3-global-comparable-sales-growth-20261008120128000 — 访问 2026-10-20 — 已读（同构区间规则；5 档；feeSchedule rate=0.04）
- https://gamma-api.polymarket.com/events?slug=united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130 — 访问 2026-10-20 — 已读（Q2 结算 83–84；5 档；volume $25,551）
- https://gamma-api.polymarket.com/events?slug=delta-dal-q2-passenger-load-factor — 访问 2026-10-20 — 已读（Q2 结算 83–85；5 档；volume $9,704）
- https://gamma-api.polymarket.com/events?slug=costco-q3-us-adjusted-comparable-sales-growth — 访问 2026-10-20 — 已读（US adjusted comps 定义；6 档；Q3 结算 6.5–7.5；fee rate=0.04）
- https://gamma-api.polymarket.com/events?slug=boeing-airplane-deliveries-above-in-q1 — 访问 2026-10-20 — 已读（above 阈值阶梯；above 140 YES、above 145 NO；9 个市场）
- https://gamma-api.polymarket.com/events?slug=will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419 — 访问 2026-10-20 — 已读（above 阈值阶梯；above 40 YES、above 41 NO；5 个市场）
- https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=&endTs=&fidelity=60 — 访问 2026-10-20 — 已读（单次窗口 >6 天报错；Boeing 04-14 00:00 公告前 0.785/0.415；Costco 05-14 全档 0.46 是无效中间价）
- https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=<0..N> — 访问 2026-10-20，复核 2026-10-21 — 已读（Boeing 04-14 18:27:46 `BUY Yes @0.98` 29 份；TSM 07-13 05:32:08 `BUY No @0.912887` 514.01 份（05:32:08 后的 06:46:29 `SELL No @0.860366` 是 taker 卖）；DAL 07-02 10:07:10 `BUY Yes 37.55 @0.238136`；Costco 6.5–7.5 档 05-22 22:38:55 `BUY No @0.92` 20 份（同钱包 22:38:53–55 在 6 档篮式）；UAL **07-01** 09:09:52 `BUY Yes 50 @0.07`）
- https://investors.boeing.com/investors/news/press-release-details/2026/Boeing-Announces-First-Quarter-Deliveries/default.aspx — 访问 2026-10-20，复核 2026-10-21 — 已读（2026-04-14：737 114、767 6、777 8、787 15，Total 143；页面只写 `April 14, 2026`，无小时）
- https://investor.tsmc.com/english/monthly-revenue/2026 — 访问 2026-10-20 — 已读（Apr 410,726；May 416,975；Jun 442,680；NT$m）
- https://pr.tsmc.com/english/news/3323 — 访问 2026-10-20，复核 2026-10-21 — 已读（2026-07-13：June 营收 NT$442.68bn，Jan–Jun NT$2,404.48bn；页面 `dateModified = 2026-07-13T13:30:28+08:00` = 05:30:28Z）
- https://pr.tsmc.com/english/news/3326 — 访问 2026-10-20 — 已读（2026-07-16：Q2 营收 NT$1,270.38bn；US$40.20bn；汇率 31.60）
- https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-April-Sales-Results/default.aspx — 访问 2026-10-20 — 已读（2026-05-06：April 4 周 US adjusted comps 8.0%，total 7.8%；35 周 US 6.3%）
- https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-Third-Quarter-and-Year-To-Date-Operating-Results-For-Fiscal-2026/default.aspx — 访问 2026-10-20 — 已读（2026-05-28：Q3 12 周 US adjusted comps 6.8%，total company 6.6%）
- https://www.fool.com/investing/2026/05/08/is-costco-stock-a-buy-sell-or-hold-after-april-sal/ — 访问 2026-10-20 — 二手（March adjusted total comps 6.2%，April 7.8%；仅用于 March 月度值，未在 Costco 官方稿中找到单列）
- https://www.sec.gov/Archives/edgar/data/27904/000002790426000031/dal-20260630.htm — 访问 2026-10-20 — 已读（Delta Q2 2026：consolidated passenger load factor 84.8%；RPM 66,767m、ASM 78,694m）
- https://www.sec.gov/Archives/edgar/data/0000100517/000010051726000135/ual_erx06302026xex991.htm — 访问 2026-10-20 — 已读（UAL Q2 2026：consolidated load factor 83.4%；RPM 72,765m、ASM 87,279m）
- https://theairside.news/en/invest-united — 访问 2026-10-20 — 二手（引用 BTS T1：UAL mainline 2026-04 ASM 25,729 / RPM 21,165 / LF 82.3；05 27,957 / 23,029 / 82.4；06 28,263 / 24,271 / 85.9）
- https://theairside.news/en/invest-delta — 访问 2026-10-20 — 二手（引用 BTS T1：DAL mainline 2026-04 ASM 23,627 / RPM 19,538 / LF 82.7；05 24,938 / 21,164 / 84.9；06 24,724 / 21,778 / 88.1）
- https://data.bts.gov/resource/q4tb-tbff.json — 访问 2026-10-20 — 已读（T100 Segment Summary By Carrier；只有 passenger/seat 比值，不是 RPM/ASM，因此**没有**用于载客率计算）
- GUIDE.md 第 8 节 — 访问 2026-10-20 — 已读（Polymarket 吃单费公式、半价差、历史 L2 无公开来源）
- `bots/quant/notes/scheduler/scratch/P-quant-030/backtest.py` + `backtest.out` — 运行 2026-10-21 — 已跑（历史可成交价回测：TSM above-41 taker BUY NO @0.912887、费 0.003181/份、1¢ 净 +0.073932/份、514.01 份 +$38.00；严格规则内 0 笔）
- `bots/quant/notes/scheduler/scratch/P-quant-030/verify_family.py`、`verify_cases.py`、`inspect_trades.py` 及同名 `.out` — 运行 2026-10-21 — 已跑（196/951 已关闭、102/497 开放；5 个案例逐笔复核）
- 缺失：历史 L2 盘口；Boeing 公告与 BTS T1 的精确发布时间戳；Costco 财报前各档 YES 卖价；TSMC 月度营收的 USD 换算时点（本回测用公司 Q2 公布的 31.60）；TSLA 交付（区域代理，未计入）
