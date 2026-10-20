---
id: quant-020
name_zh: 财报超预期市场：中价带的基准率缺口
name_en: Polymarket "beat quarterly earnings?" — base-rate gap in the coin-flip band
bot: quant
date: 2026-10-20
market: polymarket
pm_category: finance
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「<公司> 本季 GAAP/非GAAP EPS 是否高于 <创建时 SeekingAlpha 一致预期>」二元市场（每事件 1 个市场，negRisk=false）
venues: Polymarket
data: Gamma events/markets（规则原文、outcomePrices、feeSchedule）、CLOB prices-history（已关闭市场仍可取，本轮实取 247 个）、data-api；全部免费免密钥。结算源 SeekingAlpha 付费墙，本轮未取；SEC EDGAR 全文检索 KEYLESS 可用，可作独立复核口径
test_2w: 独立结果按 event=公司-季度计（一事件一市场），2026-10-20 起 16 天内 Gamma 上有 118 个 open event，两周可拿到约 100 个；失败标准：0.40–0.55 带内按事件分组净 PnL 中位 ≤0，或带内 YES 率 ≤ 事前价均值
status: 待核
confidence: 中
---

整理说明：基率与校准都是我在 2026-10-20 用 Gamma + CLOB 公开接口现取现算（脚本 `fetch_earn.py` / `scan_all.py` / `sample_price.py` 在本工作目录，公式写在下文）。**没有做完整回测**：只有「事前 24h 价 vs 实际结算」的横截面校准，没有逐笔成交、没有盘口、没有资金曲线。

## 一句话

在 Polymarket 的「某公司本季 EPS 是否高于创建时的一致预期」二元市场里，只在事前 24h 价格落在 **0.40–0.55** 的带上**吃单买 YES**，持到结算（通常 1 天内出结果）；依据是这一段历史上 YES 率 **65.71%** 而事前均价只有 **0.4894**。

## 钱从哪里来

付钱给你的是**在 50¢ 附近给「能否 beat」报低价的一方**。机制上的理由是：这类市场的行权价不是「会不会超预期」的模糊叙事，而是 `as of market creation` 那一刻 SeekingAlpha 卖方一致预期的**一个具体数字**（见规则原文），而 GAAP 与非 GAAP 两个口径的历史超预期率差得很远——我数出来 GAAP 是 **64.06%**、非 GAAP 是 **80.95%**（见证据）。当两边的信息被混在一个「财报好不好」的直觉里，接近 50¢ 的报价就没有把口径差异和基准率算进去。

这是**横截面单点证据 + 事后分桶**，不是持续性的时序证明；§证据 里也如实写了：整体上市场校准比基准率更好（Brier 0.1310 vs 0.1818），缺口只集中在中间那一档。

## 规则

以下逐条来自 Gamma 事件 `hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05` 的 `description` 原文（2026-10-20 已读，普通财报模板同构）：

- 行权价来源：`The Street consensus estimate for ... GAAP EPS for the relevant quarter is $0.05 as of market creation`；另注 `The strike prices used in these markets are derived from SeekingAlpha estimates, and reflect the consensus of sell-side analyst estimates for GAAP EPS.` → **是创建时点（不是结算时点）的一致预期，来源 SeekingAlpha**，会随市场创建日固定，不随分析师上/下调而更新。
- 结算条件：`resolve to "Yes" if ... reports GAAP EPS greater than $0.05`；`Otherwise ... "No."` → **严格大于**，等于算 No。
- 结算源：`the GAAP EPS listed in the company's official earnings documents`；公司未发布 GAAP EPS 时，`resolve according to the GAAP EPS figure reported by SeekingAlpha`；`If no such figure is published within 96h of market close (4:00:00pm ET) on the day earnings are announced, the market will resolve to "No"`。
- 未按期发布：`If the company does not release earnings within 45 calendar days of the estimated earnings date, this market will resolve to "No."`
- 修订口径：`Subsequent restatements, corrections, or revisions ... will not qualify`，只有 `obvious and immediate mistakes (e.g., fat finger errors, as with Lyft's (LYFT) earnings release in February 2024)` 例外。
- 数值口径：`All figures will be rounded to the nearest cent using standard rounding`；`IFRS EPS will be treated as GAAP EPS`；`GAAP EPS refers to diluted GAAP EPS, unless this is not published, in which case it refers to basic GAAP EPS`；跨国公司的美股 ADR/ADS 为准。
- 市场结构：每事件 1 个市场（1378 个已关闭事件对应 1382 个市场），`negRisk=false`，`restricted=true`，`orderMinSize=5`（份），`orderPriceMinTickSize` 为 `0.001`（本轮看到的实例）或 `0.01`。
- 同族还有 `-nongaap-` 版本（行权价用非 GAAP/adjusted 一致预期），slug 只差这一段，**必须逐市场读 description，不能按标题猜口径**。

**交易规则（提案，未验证）**：

1. 只做 `0.40 ≤ p_24h ≤ 0.55` 的带（`p_24h` = 该市场在 `endDate − 24h` 之前 CLOB `prices-history` 的最后一个 `p`）；带外一律不做。
2. 吃单买 YES（不在这个带里挂单，因为这一带是唯一观察到缺口的区间）。
3. 每个 event ≤ 200 USDT，同时在手 ≤ 15 个 event，总占用 ≤ 2,000 USDT（低于单场所 2,500）。
4. 不加仓、不对冲、不平仓：持有到 UMA 结算，`endDate` 后一般数小时至 2 天。财报在收盘后发布、`endDate` 设 22:00Z，实际占款约 1–3 天。
5. 熔断：同一周内已实现亏损事件数 ≥ 4 时当周停止新开仓。
6. 明确不做：GAAP/非 GAAP 混用同一个基准率（口径分桶，见证据）；不做 `0.8+` 的高价带（那里市场比基准率更准）。

## 证据

### 1）历史超预期率（我自己数的，1378 个已关闭事件）

样本：`https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=…&closed=true&order=endDate&ascending=false` 全量翻页，得 **1378** 个已关闭事件、**1382** 个市场，`endDate` 从 **2024-01-19** 到 **2026-10-19**。结算值取 Gamma `outcomePrices`（`["1","0"]` 记 YES、`["0","1"]` 记 NO，全部 1382 个都能这样判，无未结算残留）。

- 合计 **YES 1028 / NO 354 → 74.38%**。
- 按 slug 口径分：`-nongaap-` **684/845 = 80.95%**；`-gaap-` **344/537 = 64.06%**。
- 每月事件数（同一份数据按 `endDate` 月份数）：2025-10 **156**、2025-11 **172**、2025-12 **53**、2026-01 **54**、2026-02 **169**、2026-03 **73**、2026-04 **120**、2026-05 **155**、2026-06 **44**、2026-07 **143**、2026-08 **154**、2026-09 **44**、2026-10 **28**（只到 10-19）。→ 财报季（1、2、4、5、7、8、10、11 月）每月 120–172 个，淡季（6、9 月）44 个。**这就是「每月多少次机会」的实测值**。
- 单事件成交额（Gamma `volume`，来源自报，未核实）：合计 **$21,633,950**、中位 **$6,232**、p90 **$29,916**。

### 2）事前价 vs 实际结算（247 个事件，我自己取的）

取 `endDate` 最新的 250 个已关闭事件，对每个市场用 `https://clob.polymarket.com/prices-history?market=<clobTokenId[0]>&startTs=<endDate−72h>&endTs=<endDate>&fidelity=60`，抓到的点里取 `t ≤ endDate−24h` 的最后一个 `p` 作为 **p_24h**；3 个市场无价格点，得 **247** 个样本。

| 组 | n | 实际 YES 率 | mean(p_24h) | 差 | Brier(市场) | Brier(常数基准率) |
|---|---:|---:|---:|---:|---:|---:|
| 全部 | 247 | 0.7611 | 0.7230 | **+0.0381** | 0.1310 | 0.1818 |
| GAAP | 90 | 0.6333 | 0.6370 | −0.0036 | 0.1728 | 0.2322 |
| 非 GAAP | 157 | 0.8344 | 0.7723 | **+0.0621** | 0.1070 | 0.1382 |

分桶（同一 247 个样本）：

| p_24h 区间 | n | mean(p_24h) | 实际 YES 率 | 差 |
|---|---:|---:|---:|---:|
| [0.00,0.20) | 7 | 0.0769 | 0.0000 | −0.0769 |
| [0.20,0.40) | 22 | 0.3193 | 0.3182 | −0.0011 |
| **[0.40,0.60)** | **35** | **0.4894** | **0.6571** | **+0.1677** |
| [0.60,0.80) | 59 | 0.7124 | 0.7288 | +0.0164 |
| [0.80,1.01] | 124 | 0.9021 | 0.9274 | +0.0253 |

中间带的内部拆分（同样本）：GAAP n=18，mean 0.4747 / YES 0.5556（+0.0809）；非 GAAP n=17，mean 0.5050 / YES 0.7647（+0.2597）。

**必须一起读的三件事**：(a) 整体缺口只有 +3.81pp，小于一次吃单的费+半价差，所以「整体买 YES」不是策略；(b) 市场整体 Brier **优于**常数基准率（0.1310 < 0.1818），即市场是有信息含量的，不是系统性低估；(c) 唯一的大缺口在 [0.40,0.60) 这 35 个事件上，**区间边界是我看完数据才划的**，有事后选择偏差，n=35 也小。这三条合起来说明：这是**待验证的候选**，不是已证实的边。

### 3）没有做的事

没有逐笔成交回放、没有历史盘口（GUIDE 第 8 节：历史 L2 无公开来源）、没有资金曲线、没有 `observed_net_return`（= null）、`backtest_count = 0`。没有取 SeekingAlpha 的原始预期值或公布值（付费墙），所以**无法**独立复核「strike 是否等于当时一致预期」，只能照抄规则原文。

## 数据

- Gamma（免费免密钥）：`https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=<0..1400>&closed=true&order=endDate&ascending=false`（1378 个已关闭事件，规则原文 + `outcomePrices` + `feeSchedule`）；`closed=false&order=endDate&ascending=true`（当前 open 清单）。
- CLOB（免费免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=&endTs=&fidelity=60`。**本条实测：已关闭的财报市场仍然能取到价格**（247/250 成功），这与 quant-012 里已关闭地震市场返回空 `history` 的情况不同——所以本族可以做历史校准，这是它与地震条目的关键数据差异。
- SEC EDGAR 全文检索（免费免密钥，可作独立口径）：`https://efts.sec.gov/LATEST/search-index?q=form%3A8-K%20items%3A2.02&forms=8-K` 返回 JSON（`hits.total.value`）；8-K Item 2.02 的 EX-99.1 是公司自己的财报新闻稿，可用来直接数「公布 EPS vs 当时一致预期」。本轮只验证端点可达、**未**逐份抽取数字。
- 缺失：SeekingAlpha 原始预期/公布值（付费墙，不抓）；历史逐笔成交（data-api 只保留约最近 2 万笔/市场，本轮未取）。

## 两周内怎么检验

- **独立结果按事件（公司-季度）计，不按市场计**：一事件一市场，天然不重复。同一公司同一天若有 GAAP 与非 GAAP 两个事件，二者共用同一份财报、同一份新闻稿 → **合并为 1 个结果**（严口径），这会削掉一部分样本。
- 样本量：2026-10-20 起 16 天内 Gamma 上 open 事件 **118 个**（第一页 100 个的 `endDate` 全部 ≤ 2026-10-30，第二页 18 个到 2026-11-05），财报季两周约 100 个，去掉非 GAAP/GAAP 合并与无价格点的，预计仍有 **60–90** 个 → 两周内**能**拿到 ≥30 个独立结果，不需要等一年。
- 每天记录：`p_24h`（盘口 bid/ask 与实际成交价，不只 `p`）、`feeSchedule`、结算值、结算时间戳。
- **失败标准（写死，事后不改）**：0.40–0.55 带内、按事件分组的**净 PnL 中位 ≤ 0**（每笔扣吃单费与半个实际价差）；或带内实际 YES 率 **≤ mean(p_24h)**（缺口消失）。样本不足 20 个事件则判「证据不足」进待选区，不算通过也不算失败。
- 不允许的自我安慰：不能用「中间带之外也赚了」改口扩大区间；不能把 GAAP 与非 GAAP 合并成一个样本再声称缺口。

## 成本与容量

- **费用（Gamma 实取，不是查 GUIDE 表）**：本轮看到的每个财报市场都是 `feeSchedule = {"exponent": 1, "rate": 0.05, "takerOnly": true, "rebateRate": 0.25}`，`feesEnabled=true`、`takerBaseFee=1000`、`makerBaseFee=1000`。**注意：GUIDE 第 8 节把「金融」列为 0.04，与本族实取的 0.05 不一致；本条按实取值 0.05 算。**
- 吃单费（GUIDE 公式 `费用 = 份数 × 费率 × p × (1 − p)`）：`p=0.4894` 时每份 `0.05×0.4894×0.5106 = 0.01250`；折成投入资金 `= 0.05×(1−p) = 2.55%`。`p=0.55` 时每份 `0.01238`（2.25%）；`p=0.40` 时 `0.01200`（3.00%）。
- 半价差：**历史盘口取不到，本轮无法实测**。以 2026-10-20 三个 open 财报市场的 bid/ask 作量级参考（来源自报，未核实，非随机样本）：`bfc-…-2pt66` 0.44/0.46（2¢）、`efx-…-2pt24` 0.56/0.69（13¢）、`ally-…-1pt43` 0.17/0.77（60¢）。**半价差按 1¢ 做基准算例**（在 0.49 上约 2.0%），把 2–6¢ 当压力情景；这是假设，不是实测。
- 每笔成本 = 费 + 半价差 ≈ `0.0125 + 0.01 = 0.0225`/份（p≈0.49，基准情景）。
- 带内毛期望（模型算术，非实测）：`0.6571 − (0.4894 + 0.01) − 0.0125 = +0.1452`/份，按投入 `0.4994` 折 **+29.1%**；压力情景半价差 4¢ → `+0.1152`/份 = +23.1%。**这个数字大得不合理，只能当作「方向为正」的粗算**：n=35、事后分桶、用的 `p` 是价格序列而非可执行卖价。
- 容量：单事件成交额中位 $6,232、p90 $29,916（来源自报，未核实）。200 USDT/event 在中位事件上约占 3.2%，可放；**5,000 USDT 总量放不满**——15 个 event × 200 = 3,000，但真实只在手 1–3 天，且中间带本身只占样本 **35/247 = 14.2%**，机会密度低于事件密度：财报季约 100 event/两周 × 14.2% ≈ **14 次/两周 ≈ 每月 28 次**，每次约 1–3 天，200 USDT/次 → 占用约 400–600 USDT。**频率够、单次的钱不够**。
- 资金被占住：`endDate` 后到 UMA 结算，本轮样本末价格点距 `endDate` 最近的记录显示价格已在结算方向（如 `tfc-…` 从 0.52 跌到 0.0045、`mtb-…` 从 0.745 升到 0.9995），说明结果通常在 `endDate` 附近已定，但**实际结算到账时间未统计**。

## 风险

- **口径风险（最大）**：GAAP 与非 GAAP 两个基准率差 16.9pp（80.95% vs 64.06%）。若把非 GAAP 的基准率套到 GAAP 市场上，中间带的「+16.8pp」会消失甚至反向（GAAP 中间带只有 +8.1pp，n=18）。
- **事后分桶**：区间 0.40–0.55/0.60 是我看完 247 个样本才定的，真正的样本外表现可能归零；`p` 用的是价格序列不是卖价，实际成交价更高。
- **strike 不可复核**：行权价是 `as of market creation` 的 SeekingAlpha 一致预期，付费墙，本条未能独立验证「strike = 当时市场一致预期」。若 strike 本身被设在一个容易/难以 beat 的水平（发行方选点），基准率会系统性偏移，而这不是「定价错误」而是标的设计。
- **`resolve to "No"` 的兜底条款**：96 小时内 SeekingAlpha 无数字、或 45 天内不发财报 → 判 **No**。买 YES 在这些情形下全损，且这类事件在样本里无法从 `outcomePrices` 事后区分，会污染基准率（方向：让真实 beat 率被**低估**）。
- **肥手指例外**：规则明文允许 Lyft 2024 那种明显错误例外，属于裁量条款，可能改变结算。
- **信息时点**：`p_24h` 距财报发布通常只有几小时到 1 天，机构在发布前已按 channel checks 调价；我买到的可能正是「知道得更多的一方」卖出的。
- **平台**：`restricted=true`；UMA 结算争议、`endDate` 后账期不确定；财报季 118 个 event 集中在 2 周内，结算系统拥堵时资金占用会拉长。
- **样本选择**：1378 个事件里只有 2024-01 一个早于 2025-06，实际上等于**只有约 13 个月的样本**（2025-09 起密集），不足以覆盖一轮完整周期；`endDate` 在 2026-10 的 28 个事件到 10-19 截止，是部分月。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付款方是 50¢ 附近给 beat 概率报低价的对手方；量化证据是中间带 35 个事件事前价 0.4894 对实际 0.6571。但「为什么持续存在」只有单点横截面，没有时序证据，且整体 Brier 显示市场并不系统性低估。
2. **有免费数据能检验：满足** — Gamma 全量 1378 个已关闭事件 + CLOB 对已关闭市场**仍可取价格**（247/250 成功），独立结果按事件计远超 30；SEC EDGAR 全文检索免密钥，可做独立口径复核。
3. **小资金能做：满足** — 200 USDT/event、≤15 event、≤2,000 USDT，低于 2,500/场所与 5,000 总资金；不加杠杆、不借钱；买 YES 最大亏损即本金。容量如实写了：5,000 USDT 放不满。
4. **不重复：不确定（倾向不重复）** — 查了 `known/KNOWN.md`（135 条，grep `earnings|EPS|财报|盈利|beat|finance|股票` 无命中，最接近的是 `E-E1-macro-window`（FOMC/CPI 宏观窗口）与 `E-E1-index-etf-event`（指数纳入/ETF 获批），二者结算看宏观数据与监管公告，没有 EPS 一致预期行权价）；另 grep 全部 `bots/*/entries/*.md`，只有 `quant-004`（财报电话会**提及词**市场，结算看说了哪个词，不是 EPS 数字）命中 earnings，机制不同；`quant-007`（AI 榜单）、`dot-032`（流动性奖励）无关。`bots/*/CLAIMS.md` 里 B17 由本 bot 于 2026-10-20 认领。是否与主项目未公开条目重复要主审确认。
5. **扣成本后粗算够用：不确定** — 中间带粗算 `+0.1452`/份（+29.1%）远大于成本 `0.0225`/份，但 n=35、区间事后划定、`p` 非可执行卖价、半价差是假设值；整体口径下缺口只有 +3.81pp，**小于**成本。`observed_net_return = null`、`backtest_count = 0`（只表示没回测，不表示收益为 0）。
6. **两周内能检验：满足** — 独立结果按 event（公司-季度）计；2026-10-20 起 16 天内 Gamma 上有 118 个 open event，财报季两周约 100 个，扣掉口径合并与无价格点后预计 60–90 个 ≥ 30。失败标准写死（带内净 PnL 中位 ≤0 或 YES 率 ≤ 事前均价）。
7. **出处可查：满足** — 每个数字都有 URL + 访问日期 + 取数方式；基率与校准是我从原始 JSON 算的，样本量、公式、分桶阈值、失败次数（3 个无价格点）都写出；Gamma 的 `volume` 一律标「来源自报，未核实」；3 个 open 市场价差明说是非随机样本；未取到的（SeekingAlpha、历史 L2、结算到账时间）都写「未查到」。

## 出处

- https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&offset=0..1400&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（全量翻页得 1378 个已关闭事件 / 1382 个市场 / YES 1028 / NO 354；`endDate` 2024-01-19 至 2026-10-19）
- https://gamma-api.polymarket.com/public-search?q=earnings&limit_per_type=20&events_status=all — 访问 2026-10-20 — 已读（模板确认：`Will Hims & Hers Health (HIMS) beat quarterly earnings?`，`resolutionSource=https://seekingalpha.com/`，`restricted=true`，`volume=287931.953117`）
- https://gamma-api.polymarket.com/events?slug=hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05 — 访问 2026-10-20 — 已读（规则原文全文：SeekingAlpha 一致预期、`greater than $0.05`、96h/45天兜底、舍入到分、IFRS=GAAP、diluted 优先）
- https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=<endDate-72h>&endTs=<endDate>&fidelity=60 — 访问 2026-10-20 — 已读（247/250 个已关闭市场返回非空 history；例：`tfc-…-10-16-2026-1pt13` 从 `p=0.52` 到 `p=0.0045`；`mtb-…-10-16-2026-5pt00` 从 `p=0.745` 到 `p=0.9995`）
- https://gamma-api.polymarket.com/events?tag_slug=earnings&limit=100&closed=false&order=endDate&ascending=true — 访问 2026-10-20 — 已读（100 个 open 事件，`endDate` 至 2026-10-30；示例 `bfc-…-2pt66` bid 0.44/ask 0.46、`efx-…-2pt24` 0.56/0.69、`ally-…-1pt43` 0.17/0.77；`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`）
- 同上 `&offset=100` — 访问 2026-10-20 — 已读（另 18 个 open 事件，`endDate` 至 2026-11-05 → 16 天内共 118 个）
- https://efts.sec.gov/LATEST/search-index?q=form%3A8-K%20items%3A2.02&forms=8-K — 访问 2026-10-20 — 已读（返回 JSON：`{"took":178,...,"hits":{"total":{"value":10000,"relation":"gte"},...}`；端点可达，逐份 EPS 抽取本轮**未做**）
- https://docs.polymarket.com/ — 本轮**未重新抓取**；费用公式与 5 位小数舍入沿用 GUIDE 第 8 节与本条 Gamma 实取 `rate=0.05`
- 未查到：SeekingAlpha 原始一致预期与公布值（付费墙）；历史盘口/L2；结算到账时间分布；`data-api` 逐笔成交

---
