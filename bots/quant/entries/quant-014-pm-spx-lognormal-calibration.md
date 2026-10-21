---
id: quant-014
name_zh: SPX收盘价：已实现波动率定价
name_en: Pricing Polymarket SPX/NVDA close markets with a lognormal model on realized volatility
bot: quant
date: 2026-10-20
market: polymarket
pm_category: finance
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「S&P 500 (SPX) Up or Down on <date>」日内二元（negRisk=false，单市场）；「What will S&P 500 (SPX) close at end of <月>?」6 档阶梯；「NVIDIA (NVDA) closes above ___ on <date>」5 档阶梯
venues: Polymarket
data: Yahoo Finance chart API `^SPX` / FRED `SP500` 日线（免费免密钥；回放模型输入用 FRED，另用 Yahoo 复核 1,254 根，2021-10-20..2026-10-19）；Polymarket Gamma/CLOB（免费免密钥；CLOB `prices-history` 只作覆盖检查，不作成交价）；data-api 逐笔成交（免费免密钥，`trades?market=<conditionId>`，已关闭市场约最近 2 万笔/市场，本次 303 market / 243,699 笔）；stooq CSV 在本机被 JS 挑战页挡住，未用到
test_2w: 独立结果按 event 计（同一交易日、同一结算源的 Up/Down 与 Opens 算 1 个）；历史可成交价回放已覆盖 252 个日频 + 7 个阶梯 event（2025-10-15..2026-10-19），两周只能新增约 10–11 个日频 event；失败标准（冻结）是日频吃单子集扣费后每份净损益均值 ≤0，或模型 Brier 在 ≥30 个 event 上劣于常数 0.53，或阶梯 30 天内成交不到 50 份
status: 待核
confidence: 中
evidence: 回放
result: 负
slot: -
variants: 5
variants_ext: -
window: 2025-10-15..2026-10-19
max_dd: -
contribution: -3.6%
---

整理说明：本条所有价格与规则都来自 2026-10-20 用 curl 实取的 Gamma/CLOB 响应；波动率、基率、校准与费用都是我自己的算术，脚本 `spx_lognormal.py`、`spx_calibration.py` 全文贴在 `notes/batch2-verification/quant-014.md`。**已做了一次小样本历史检验（21 个 event，2026-09-21..2026-10-19），结论对「吃单做日频涨跌」是负的**，我照写在这里，不修饰。

**2026-10-21 第二轮硬化（新增，不改变上面的原始记录）**：用 data-api 逐笔成交（不是 CLOB 中间价）对 **259 个已结算 event / 303 条腿**做可成交价回放，窗口 **2025-10-15..2026-10-19**，扣 0.04 吃单费 + 1¢ 半价差。全部触发腿均值 **−0.00743/份**、总净 **−1.783 份**、每 $1 投入 **−0.0287**；日频 FADE 子集虽为 +0.00650/份，但中位数 −0.14482、ISO 周 bootstrap 95% CI [-0.04872,+0.06235] 跨 0；**OOS（2026-07-01 以后）全部触发腿 −0.03452/份**；7 条阶梯腿全部为负（monthly above −0.06948、monthly close −0.13662）。脚本、逐腿明细与 `SUMMARY.md` 在 `bots/quant/replay/quant-014/`，硬化脚本与 stdout 在 `bots/quant/notes/scheduler/scratch/H-quant-014/`，完整复算见 `bots/quant/notes/q014-hist/REPORT.md`。**结论比第一轮更负：建议主项目核为退回（反证），不要收录，也不要用它去交易日频或阶梯。**

## 一句话

用 SPX 近 20/60 个交易日的已实现波动率（不是隐含波动率）建对数正态分布，给 Polymarket finance 板块的「SPX 某日收盘涨/跌」「SPX 年底收盘落在哪一档」「NVDA 某日收盘是否高于 X」定价；只在模型概率与可成交报价之差超过 2×(吃单费 + 半价差) 时动手，日频涨跌市场基本不做（21 event 旧检验与 252 event 可成交价回放都显示它没有正 EV），原想只做阶梯中段档，但 252 event 回放里的 7 条阶梯腿也全部为负，**因此本条现在是一条反证，不是可交易策略**。

## 钱从哪里来

付钱给你的是**按新闻情绪和整数关口给阶梯档位出价的散户**——他们对「SPX 年底落在哪一档」这种 2 个月期的远端档位，报价与一个只用公开日线算出来的对数正态分布相差很大（下面证据节：模型 0.16 对 0.40）。持续存在的原因是这类市场是**每天/每月重复上市的固定模板**（SPX 日频序列 2026 年 6–9 月每月 21 个 event，见下），做市商和模型方对每一个新模板都要重新报价，而参与者结构主要是方向性散户，不是波动率交易台；平台给 finance 板块的吃单费率是 0.04（Gamma 实取），比加密的 0.07 低，成本门槛低一档。**必须说清楚的是：本条没有证明这块钱能拿到，回放反而证明拿不到**；21 个 event 的实盘报价检验里，「市场价 vs 结果」的 Brier 已经是 0.174，比任何常数预测好得多，说明日频市场本身定价不差；2026-10-21 的 252 event 可成交价回放里，全部触发腿和 7 条阶梯腿扣掉 0.04 吃单费 + 1¢ 半价差后都是负的（见下面证据 5）。所以「对远端阶梯出价的散户在送钱」目前只是未证实的假设，不能当作收益来源。**另有一个 2026-10-21 的时点变化：这些 SPX finance 市场现在的 `feeType=zero_fees`、`feeSchedule.rate=0`；2026-10-20 快照是 0.04。回放仍按 0.04 计（成本取高），fee=0 敏感性下全部触发腿也只是 −0.00090/份，仍为负。**

## 规则

### 结算规则原文（我实取的 Gamma `description`）

**A. 日频涨跌**：事件 `spx-up-or-down-on-october-20-2026`（2026-10-20 已读）

- 「will resolve to "Up" if the official S&P 500 Index closing price for S&P 500 (SPX) on Tuesday, October 20, 2026 is higher than the official S&P 500 Index closing price for SPX on the most recent prior trading day」——比的是**当日官方收盘 vs 上一个交易日官方收盘**，不是开盘。
- 相等：「If the two specified closing prices are exactly equal, this market will resolve 50-50.」
- 数据源：「The resolution source for this market is the Wall Street Journal, specifically the Close values published by the WSJ under "Historical Prices"」，`resolutionSource` 字段 = `https://www.wsj.com/market-data/stocks`。**注意不是 Yahoo**（同板块的月度阶梯用的是 Yahoo Finance `^GSPC`，两个市场源不同，这是可以出错的地方）。
- 舍入：「all figures will be rounded to the nearest cent using standard rounding.」
- 缺价：缩短交易日照用官方收盘；整日无官方收盘（停牌到收盘、系统故障等）用「the last valid on-exchange trade price of the regular session」。
- 收盘时间：`endDate = 2026-10-20T20:00:00Z` = 美东 16:00（10 月 EDT，UTC−4），`startDate = 2026-10-19T12:00:52Z`；即**开盘前约 20 小时上市，收盘即截止**。
- 同一 event 只有 1 个市场（`negRisk=false`），YES/NO 二元；`tags` 含 `spx, up-or-down, daily, indicies, finance, daily-close`；`series.slug = spx-daily-up-or-down`（`recurrence: daily`, `restricted: true`）。

**B. 月度/年底阶梯**：事件 `spx-close-dec-2026`「What will S&P 500 (SPX) close at end of 2026?」（2026-10-20 已读）

- 「official closing price for S&P 500 (SPX) on the final trading day of December 2026」；「If the reported value falls exactly between two brackets, then this market will resolve to the higher range bracket.」（档界值归上档）
- 数据源：「the resolution source for this market is Yahoo Finance, specifically the S&P 500 (SPX) "Close" prices available at https://finance.yahoo.com/quote/%5EGSPC/history」。
- 6 档：`<$6,000`、`$6,000-$6,500`、`$6,500-$7,000`、`$7,000-$7,500`、`$7,500-$8,000`、`>$8,000`；`endDate = 2026-12-31T21:00:00Z`（EST 16:00）。
- **判据是「收盘落档」，不是「曾经触及」**——这条和 `spx-hit-dec-2026`（「What will S&P 500 (SPX) hit」，hit = 曾经触及）是两个不同事件，不能混；两者价格不可互推。

**C. 个股**：事件 `nvda-close-above-on-october-20-2026`「NVIDIA (NVDA) closes above ___ on October 20?」（2026-10-20 已读）

- 5 档 strike：$210 / $215 / $220 / $225 / $230，每档独立二元；`negRisk=false`。
- 结算源**不是 Yahoo**：「Closing prices will be used exactly as published by Pyth, without rounding.」「the closing price refers to the Pyth "Close" value of the 1-minute candle corresponding to the final minute of regular trading hours on the primary exchange」。Pyth 无有效价时退回交易所官方收盘。相等判 **No**（「If the two specified prices are exactly equal, this market will resolve to "No"」），不交易判 50-50。
- 同族还有 `nvda-up-or-down-on-october-20-2026`（vol 140.17）、`what-price-will-nvda-hit-in-october-2026`（vol 94,705.68）、`nvda-above-in-october-2026`（vol 714.93），均为 2026-10-20 Gamma 快照。

### 交易规则（本条的提案，不是已验证的盈利规则）

1. **波动率**：σ 取 SPX 日线对数收益的 20 日与 60 日滚动年化标准差（×√252）。本次值：σ₂₀ = **0.0904**、σ₆₀ = **0.1100**、σ₂₅₂ = **0.1271**（2021-10-20..2026-10-19，1,253 个收益）。两个都算，取更保守（更靠近市场价）的那个做决策，避免用低波动窗口把尾部档卖便宜。
2. **概率**：零漂移对数正态，`P(S_T > K) = Φ( (ln(S/K) − σ²T/2) / (σ√T) )`，`T = 剩余交易日 / 252`（交易日逐日数，跳过周末与美股假日）。档位概率 = 相邻两个 `P(S_T>K)` 相减。日频市场 T=1 日时，零漂移模型给出 **P(up)=0.5000**——这就是日频市场的模型答案，没有偏移量，所以日频只在市场价偏离 0.5 超过成本时才动，且下面证据节说明这条已被自己的样本否掉。
3. **进场阈值**：`|p_model − p_tradable| > 2 × (fee + half_spread)`，`p_tradable` 是真正能成交的那一侧（买入用 bestAsk，卖出用 bestBid）。不足则不做，不做「差不多就做」。
4. **只在阶梯中段下单，不用 mid 定价**：本条只用 bestBid/bestAsk，不用 `outcomePrices`。理由见证据：`spx-close-dec-2026` 六档 mid 之和 **1.2065**、bid 之和 **0.812**、ask 之和 **1.601**，用 mid 算出来的「模型偏离」有一大半是价差。
5. **仓位**：单档 ≤ 100 份、单 event ≤ 300 USDT、同时在手 ≤ 3 个 event；总资金 5,000 USDT，单场所 ≤ 2,500 USDT。买方最大亏损 = 权利金。
6. **出场**：持有到结算；不主动平仓（平仓要再付一次费 + 半价差，而票面收敛不需要成本）。若中途市场价穿过模型价 + 成本，可减半仓。
7. **不做**：日频 Up/Down 的吃单（样本为负）；`spx-hit-*`「曾经触及」类（首达时间分布不是对数正态的简单推论，本条未建该模型）；NVDA 的财报周（`2026-11-18` 前后有 Q3 财报市场，波动率会跳，σ₂₀ 不适用）。
8. **风控**：单日亏损超过 300 USDT 或模型对已实现收盘的误差超过 2σ 连续 3 次，停一周并重估 σ。

## 证据

### 1）已实现波动率与基率（Yahoo `^SPX` 日线，我自己算的）

数据：`https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=5y&interval=1d`，取回 128,733 字节，解析出 **1,254 根日线，2021-10-20 收 4536.19 → 2026-10-19 收 7690.73**（`meta.regularMarketPrice=7690.73`、`regularMarketChangePercent=-49.898` 与 5 年涨幅不一致，说明该字段不是 5 年口径，本条不引用它）。

- σ₂₀ = **0.0904**（20 个收益，2026-09-22..2026-10-19）、σ₆₀ = **0.1100**、σ₂₅₂ = **0.1271**。
- 上涨日占比：全样本 **664/1253 = 0.5299**；最近 100 根 **47/100 = 0.4700**。日均对数收益 0.000421，t 值 **1.40**（n=1,253）→ **漂移在统计上不显著，零漂移假设站得住**；这直接决定日频模型的答案就是 0.5，不是 0.53。

### 2）对数正态 vs 市场：`spx-close-dec-2026` 六档（2026-10-20 Gamma 快照；表中 mid 为盘中时点值，已有档位在当日变动，使用前请刷新）

S = 7690.73，到期 2026-12-31，剩余交易日 **n = 51**（逐日数，跳过感恩节 11-26 与圣诞 12-25），T = 51/252 = **0.2024**。σ = σ₂₀ = 0.0904，零漂移：

| 档 | 模型 20d | 模型 60d | `outcomePrices` | bestBid | bestAsk | 模型20 − mid |
|---|---:|---:|---:|---:|---:|---:|
| `<$6,000` | 0.0000 | 0.0000 | 0.0315 | 0.022 | 0.041 | −0.0315 |
| `$6,000-$6,500` | 0.0000 | 0.0004 | 0.0800 | 0.060 | 0.100 | −0.0800 |
| `$6,500-$7,000` | 0.0109 | 0.0298 | 0.1450 | 0.080 | 0.210 | −0.1341 |
| `$7,000-$7,500` | 0.2643 | 0.2844 | 0.2850 | 0.220 | 0.350 | −0.0207 |
| `$7,500-$8,000` | 0.5636 | 0.4798 | 0.2650 | 0.140 | 0.390 | +0.2986 |
| `>$8,000` | 0.1612 | 0.2056 | 0.4000 | 0.290 | 0.510 | −0.2388 |

- mid 之和 **1.2065**、bid 之和 **0.812**、ask 之和 **1.601** → 买齐六档付 1.601 收 1.000，卖齐（买齐 NO）付 `6 − 0.812 = 5.188` 收 5.000，**两个方向都没有套利**，六档价差 1.9¢–25¢。
- 只有 `$7,500-$8,000` 一档在**买价侧**有正的模型缺口：模型 0.5636 对 bestAsk 0.390，缺口 **17.4¢/份**；吃单费 `0.04×0.39×0.61 = 0.0095`/份，半价差 `(0.39−0.14)/2 = 0.125`/份 → **扣完剩 4.0¢/份**。这是本条唯一在算术上说得过去的腿。但 25¢ 的价差意味着「ask 0.39 能不能吃到足够量」完全未知（该档 volume 4,727.16，来源自报）。
- 用 `>$8,000` 的 mid 0.40 反解 σ：在 [0.30, 1.20] 上二分 80 次，一直顶到上界 1.20 仍给不出 0.40 → **市场 mid 对应的隐含 σ > 120% 年化**，与已实现 9–11% 差一个数量级。这不能当成「市场错了」的证据，更可能说明 mid 被双边宽价差扭曲（bid 0.29 / ask 0.51 的中点是 0.40，但两边都不可成交）；本条因此只用 bid/ask。

### 3）日频市场的校准（21 个 event，我自己跑的，含结果）

样本：`series_id=10383` 已关闭事件 100 个，其中 **只有 21 个**（2026-09-21..2026-10-19）的 `prices-history` 有数据，更早的（例如 `spx-up-or-down-on-september-18-2026`）返回 `{"history":[]}`。取每个市场**收盘前 6 小时**最后一笔 60 分钟价格 `p6`（收盘 20:00Z → 取 14:00Z 之前的最后一点），与 UMA 结算结果比对：

- 样本内上涨 **9/21 = 0.4286**；`p6` 均值 **0.5593**；`|p6−0.5|` 均值 **0.2293**；**100%** 的 event 在 `p6` 上偏离 0.45–0.55 区间（即市场从不给 0.5）。
- Brier：市场 `p6` = **0.17370**；常数 0.50 = **0.25000**；常数 0.4286 = **0.24490**。Log loss：市场 = **0.51161**；常数 0.50 = **0.69315**。
- **吃单检验（本条最关键的数字）**：取 `|p6−0.5| ≥ 0.10` 的 16 个 event，按 `p6` 那一侧吃单、持到结算，**每份毛损益均值 −0.0288**（命中率 0.750 但赔率不够）；这还没扣 0.94¢/份的费与 0.5¢ 的半价差，**扣完成本更负**。
- 落在 `p6 ∈ [0.55, 0.75]`（正好是 2026-10-20 那个活市场 0.625 所在的区间）的 5 个 event 里，**YES 只赢了 1 个 = 20%**。
- 每个市场 60 分钟观测数中位数 34 条；`|p_last − p6|` 均值 **0.3574**（说明收盘前 6 小时到结算之间价格几乎走完全程，日内信息更新很快）。

**结论（我自己的判断，写死在这里）**：日频 Up/Down 的「模型说 0.5、市场说 0.625 所以卖」是**错的**——市场 `p6` 的 Brier 0.174 显著优于任何常数，方向性吃单在 21 个 event 上毛损益已经是负的。本条因此把日频市场降级为「只用于监控/不交易」，原本想只押阶梯档位；但第二轮用 data-api 逐笔成交把日频样本扩到 252 个 event、并把阶梯也纳入回放后，阶梯 7 条腿全负（见下 5），所以现在连阶梯也不能作为收益来源。21 event 的旧检验仍只当筛选，不单独当结论。

### 4）频率与容量（Gamma，我数的）

- `https://gamma-api.polymarket.com/events?series_id=10383&limit=100&closed=true&order=endDate&ascending=false` 返回 **100** 个已关闭 event（limit 打满，2026-05 有 3 个、之后才齐），按 `endDate` 月份：**2026-06: 21、07: 21、08: 21、09: 21、10: 13**（10 月未过完）→ **每个交易日 1 个，约 21 个/月**。100 个 event 的 `volume` 合计 **$10,779,504.35**（来源自报，未核实）。
- 单 event `volume`（来源自报，未核实）：2026-10-19 **164,019.45**、10-16 **43,470.21**、10-15 **37,722.58**、10-13 **68,932.03**、10-20（进行中）**9,536.47**；`liquidity` 7,151.84。**量级几千到十几万美元/event**，100 份（约 39–63 USDT）在任一 event 里都是噪声。
- 个股：`nvda-close-above-on-october-20-2026` 五个 strike，vol **1,224.39**；同族还有 `nvda-up-or-down-on-october-20-2026`（vol 140.17）与 `will-nvda-hit-week-of-october-19-2026`（vol 11,820.45），`what-price-will-nvda-hit-in-october-2026` vol **94,705.68**（均来源自报，未核实）。
- 阶梯频率低：`spx-close-dec-2026` 只有一个（vol 48,152.55），同族是按月的 `spx-hit-*` / `spx-close-*`，即**每月 1–2 个 event**。

### 5）第二轮可成交价回放（252 日频 + 7 阶梯 event，2025-10-15..2026-10-19）

这一段是 2026-10-21 新增的**真实成交价**回放，复用已合并的 `bots/quant/notes/q014-hist/`（`REPORT.md`、`q014_hist.py`、`run_output.txt`、`events.csv`），并原样搬进 `bots/quant/replay/quant-014/` 作为 canonical replay；没有重跑另一套数字。

- **成交价**：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N` 的逐笔成交（`No`/`Down` 按 `1−price` 映射成 YES 价）；决策时点 = 结算收盘前 6 小时，取窗口内**最后一笔成交**，`ask=成交价+1¢`、`bid=成交价−1¢`。CLOB `prices-history` **不是**成交价来源，只用于确认“更早的已关闭市场没有价格历史”。
- **样本**：259 个已结算 event / 303 条腿 = 日频 `spx-up-or-down-*` 252 + weekly above 2 + monthly above 3 + monthly close 2；229 个 event 至少触发一条腿，共 240 条触发腿（YES 103 / NO 137）。排除 `spx-opens-*`（同一交易日重复计）、`spx-hit-*`（曾经触及，不同模型）、SPY、未关闭 event。
- **成本**：`fee=0.04*p*(1-p)`/份（2026-10-20 Gamma 快照；2026-10-21 复核时这些市场已改成 `zero_fees`，回放仍按 0.04 计，成本取高）+ 1¢ 半价差。

| 口径 | 腿数 | 均值/份 | 中位数 | 命中率 | 总净（份） | 每 $1 |
|---|---:|---:|---:|---:|---:|---:|
| 全部触发腿（fee 0.04） | 240 | **−0.00743** | −0.14482 | 0.258 | **−1.783** | **−0.0287** |
| 全部触发腿（fee=0） | 240 | −0.00090 | −0.14000 | 0.258 | −0.216 | −0.0035 |
| 日频 FADE（model 0.5 反向） | 194 | **+0.00650** | −0.14482 | 0.222 | +1.261 | +0.0311 |
| 日频 FOLLOW（entry 原方向） | 194 | **−0.03835** | +0.11578 | 0.773 | −7.440 | — |
| monthly above | 9 | −0.06948 | −0.02078 | 0.444 | −0.625 | −0.1363 |
| monthly close | 7 | **−0.13662** | −0.07260 | 0.429 | −0.956 | −0.2442 |

- **日频 FADE 的 +0.00650 不可靠**：中位数 −0.14482，54 个 ISO 周 cluster bootstrap 95% CI **[-0.04872,+0.06235]**，跨 0；OOS（2026-07-01..2026-10-19）66 条腿 **−0.02703**。全样本 +0.0065 全部来自 dev 段（128 条 +0.02379），后 30% 转负。
- **OOS 时间切分**：dev（≤2026-06-30）168 条触发腿均值 +0.00418；OOS（≥2026-07-01）72 条触发腿均值 **−0.03452**，总净 −2.486。阶梯 7 条腿都在 dev 段，且都为负。
- **校准**：日频 252 event，模型 Brier **0.25000**，常数 0.53 **0.24923**，市场 `p6` **0.17783**；OOS 模型 0.25000、常数 0.53 0.25327、市场 0.14319。模型不比常数好，远不如市场。冻结失败标准第 3 条（模型 Brier 劣于常数 0.53，≥30 event）命中，**VERDICT: FAIL**。
- **阶梯的局限（必须承认）**：回放的决策固定在结算前 6 小时/前一个收盘，`T≈1/252`；**没有复现 entry 原来对“到期前约 72 天远端阶梯错价”的主张**，所以 7 条阶梯腿为负只能否掉“临近到期按模型吃单”，不能单独证伪远端阶梯。远端阶梯需要事件上市初期的盘口，data-api 成交可取但本轮未按上市初期决策。
- **复现**：`cd bots/quant/replay/quant-014 && python3 summarize.py`（离线读 `events.csv`，逐位复现上表）；采集脚本 `replay.py`，完整参数与所有变体见 `SUMMARY.md`，stdout 见 `summarize_stdout.txt`。硬化复核脚本 `verify_sources.py` 在 `notes/scheduler/scratch/H-quant-014/`，2026-10-21 运行 OK=40 / FAIL=0（stdout 同目录）。

## 数据

- **SPX 日线**：`https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=5y&interval=1d`（免费、免密钥、无需注册）。返回 `chart.result[0].timestamp` + `indicators.quote[0].close`；本次 1,254 根，2021-10-20 起，`meta.timezone=EDT`、`gmtoffset=-14400`。回放模型输入改用 `https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500`（免费免密钥，2,512 个交易日，2016-10-20..2026-10-19），2026-10-21 复核可达；两者对同一收盘口径一致（随机 5 个结算日交叉核对 5/5）。
- **stooq**：`https://stooq.com/q/d/l/?s=^spx&i=d` 在两次抓取中都只返回一个 JS 挑战页（`This site requires JavaScript to verify your browser`），**没有拿到 CSV，故本条不用 stooq**。
- **个股**：Yahoo 同接口换 `%5ENVDA`（本次未取）；注意 Polymarket 的 NVDA 结算源是 **Pyth**，不是 Yahoo，两者收盘价可能差几分钱——用 Yahoo 定价时要认清这是模型输入误差。
- **Polymarket 规则/结算**：Gamma `events?slug=` / `events?series_id=`（规则原文、`outcomePrices`、`bestBid/bestAsk`、`feeSchedule`、`series`、`tags`）；`public-search?q=SPX` / `q=NVDA`（找同族模板）。
- **可成交价（第二轮新增）**：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`（免费免密钥；每个市场最多约 2 万笔，再早没有）。本次 303 个 market、243,699 笔，2026-10-20 采集；`No`/`Down` 成交按 `1−price` 映射。CLOB `prices-history?market=<YES token>&interval=max&fidelity=60` 只用于覆盖检查（2026-10-21：100 个已关闭日频 event 中 **22 个**非空，2026-09-21..2026-10-20；2026-10-20 时点是 21 个），**不作成交价**。
- 缺失且必须承认：**没有隐含波动率（VIX/SPX 期权）数据**，本条只用已实现；data-api 逐笔成交每市场只留最近约 2 万笔，2025-10 以前的日频 SPX 市场取不到，故样本只有约一年；`spx-hit-*`（曾经触及）类没有建首达时间模型；没有历史盘口深度，100 份在 ask 上的成交概率未量化。

## 两周内怎么检验

- **独立结果按 event 数**：同一交易日的 `spx-up-or-down-*` 与 `spx-opens-up-or-down-*` 是同一标的、同一数据日的两个市场 → **算 1 个**；同一天的多个 NVDA strike 也算 1 个。历史回放已覆盖 **259 个已结算 event**（252 日频 + 7 阶梯，2025-10-15..2026-10-19），数量够 30；两周只能再新增约 10–11 个日频 event，阶梯 0–1 个。**但日频 event 高度相关、只覆盖一年，严格独立结果远少于 252，不能把 259 当作 259 个独立证据。**
- **每天记录**（脚本可复用 `spx_lognormal.py`）：Yahoo 收盘、σ₂₀/σ₆₀、各档 bestBid/bestAsk、`outcomePrices`、结算结果（Gamma `outcomePrices` 变成 `["1","0"]`/`["0","1"]` 且 `umaResolutionStatus=resolved`）。
- **主检验**：`p_model` 与 `p6`（收盘前 6 小时价）的 Brier 差、以及「吃单子集」扣 0.04 费率与半价差后的每份净损益。公式：`net = (1_{赢} − p_entry) − 0.04·p_entry·(1−p_entry) − half_spread`。
- **失败标准（写死，事后不改）**：
  1. 日频吃单子集（`|p6−0.5| ≥ 0.10`）扣费后每份**净**损益均值 ≤ 0；或
  2. 阶梯腿（`$7,500-$8,000` 那种模型 − ask 缺口 ≥ 5¢ 的档）30 天内成交不到 50 份（判「容量失败」，不是「策略失败」，但也退回）；或
  3. 模型 Brier 在 30 个 event 上劣于常数 0.53（模型本身坏）。
- 不允许的自我安慰：不能把「`p6` 与 0.5 的差」当作 edge（第 3 节已否掉）；不能用 mid 算损益；不能因为挂单没成交就报正收益。

## 成本与容量

- **费率（Gamma 实取，不是查表）**：2026-10-20 快照里，日频事件、`spx-close-dec-2026` 六档、NVDA 五档的 `feeSchedule` 全部是 `{"exponent": 1, "rate": 0.04, "takerOnly": true, "rebateRate": 0.25}`，`feesEnabled=true`、`takerBaseFee=1000`、maker no fee；GUIDE 第 8 节把金融列为 `0.04`，与当时实取一致。**2026-10-21 复核发现这些市场已改成 `feeType=zero_fees`、`feeSchedule={"exponent":1,"rate":0,...}`，即当前吃单费为 0。** 回放仍按 0.04 计（成本取高），另给 fee=0 敏感性；结论不因费率归零翻转（全部触发腿 fee=0 仍 −0.00090/份）。
  - 吃单费（GUIDE 公式 `份数 × 费率 × p × (1−p)`）：`p=0.625` → 每份 `0.04×0.625×0.375 = 0.009375`（**0.94¢**）；`p=0.39` → `0.04×0.39×0.61 = 0.009516`（**0.95¢**）。折成投入资金比例 `= 0.04×(1−p)`：`p=0.625` → **1.50%**；`p=0.39` → **2.44%**。
  - maker 费 0，另返对手吃单费的 `rebateRate=0.25`；`rewardsMinSize=100`（股），`clobRewards` 本次未在 SPX finance 事件上看到字段值（**未查到**），所以不把奖励算进收益。
- **每笔成本 = 费 + 半个买卖价差**（我算的）：
  - 日频（bid 0.62 / ask 0.63）：`0.94¢ + 0.50¢ = 1.44¢/份 = 2.30%`（按 0.625 计）。
  - 阶梯 `$7,500-$8,000`（bid 0.14 / ask 0.39）：`0.95¢ + 12.5¢ = 13.45¢/份 = 34.5%`（按 0.39 计）——**半价差是费的两倍以上，这就是必须只用 bid/ask 定价的原因**。模型缺口 17.4¢ 扣 13.45¢ 只剩 4.0¢，且这 4.0¢ 是**假设在 ask 上真能成交**的乐观值。
  - 同理 `$7,000-$7,500`（bid 0.22 / ask 0.35）：半价差 6.5¢ + 费 0.91¢ = 7.4¢，模型 0.2643 与 ask 0.35 的缺口 −8.6¢ → 不做。
- **单笔能放多少**：日频 100 份 ≈ 62.5 USDT；阶梯 100 份 ≈ 39 USDT。单 event ≤ 300 USDT、同时 ≤ 3 个 event → 总占用 ≤ 900 USDT，远低于 2,500 单场所上限。
- **资金占用天数**：日频 1 天（当日收盘 → UMA 结算，实际结算滞后数小时到 1 天）；阶梯最长 72 天（到 2026-12-31）+ 争议期。
- **一个月多少次机会**：日频约 21 个 event/月（但本条不交易日频）、NVDA 日频同族若干、阶梯 1–2 个/月。**机会数够、单次的钱少**：原算术上 100% 命中 100 份 × 4.0¢ 也只有 4 USDT/event；可成交价回放里这个 4.0¢ 没有出现，全部触发腿为负，因此实际容量讨论只是上限，不能当成收益。
- **容量结论**：技术上 5,000 USDT 放不进去（单档 100 份只有 39 USDT、且 ask 侧深度未知）；实际额度建议 ≤ 900 USDT。但容量不是本条的瓶颈，**回放已经说明按现有规则没有正收益**：100 份/触发腿、约一年总净 −178 USDT（fee=0 时 −22 USDT），对 5,000 USDT 的贡献 **−3.57%**（fee=0 时 −0.43%）。

## 风险

- **σ 选错就是全部风险**：σ₂₀=9.04%、σ₆₀=11.00%、σ₂₅₂=12.71%，同一张表上 `$7,500-$8,000` 从 0.5636 掉到 0.4798；用低波动窗口的 σ 会把中段档买贵。VIX 一夜翻倍这类事件（本条没有隐含波动率数据源，**未查到**免费免密钥的 VIX 日线在本次抓取里，故完全看不见）直接把 σ₂₀ 打翻。
- **对数正态本身是错的模型**：SPX 日收益有胖尾和负偏（本条没做正态性检验，**未做**，不能声称已证实），实际分布比对数正态更胖，中段概率会被高估、尾部被低估。这条与「买中段」的方向相反，需要留意。
- **结算源不一致**：日频用 **WSJ**，月度阶梯用 **Yahoo `^GSPC`**，NVDA 用 **Pyth**。三个源对同一收盘价可能差几分钱；档界（如 `$8,000`）附近的单会因此翻面。`spx-close-dec-2026` 规定「正好落在档界 → 归上档」，`spx-hit-*` 是「曾经触及」，两者不能互推。
- **价差与逆向选择**：`$7,500-$8,000` 的 `bestAsk 0.39` 与 `bestBid 0.14` 相距 25¢，说明**挂单的人自己也拿不准**；在 ask 上成交往往意味着有人刚拿到新信息（盘中跳水/跳涨）先动，成交概率与逆向选择都**未量化**，这是本条最大的未知。
- **结算滞后与争议**：`umaBond=250`、`umaReward=0.6`（日频 event 实取），`restricted=true`。客观收盘价出争议概率低，但资金被动占住的时间会比「1 天」长。
- **样本仍不够外推**：第二轮回放有 259 个 event / 303 条腿，但只覆盖 2025-10-15..2026-10-19 约一年、一个标的（SPX）、一个上涨为主的波动率 regime；日频 event 高度相关，252 个不能当 252 个独立证据。阶梯只有 7 条腿且都在 dev 段、都为负。**回放已有收益数字，结论为负（全部触发腿 −0.00743/份、总净 −1.783 份；OOS −0.03452/份），不是没有回测。**
- **平台**：`restricted=true` 的 event 在某些地区不可交易（本条不讨论合规，只记录字段）；`orderMinSize=5` 份、`orderPriceMinTickSize=0.01`。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：不满足** — 原来写的付钱方（对阶梯远端档出价偏离对数正态的散户）只有一个 2026-10-20 横截面快照；2026-10-21 的 252 event 可成交价回放没有找到正 EV：全部触发腿 −0.00743/份、OOS −0.03452/份、7 条阶梯腿全负。谁在持续付钱、为什么持续存在，**没有被证据支持**。
2. **有免费数据能检验：满足（数量）/ 不确定（独立性）** — 行情侧有 FRED `SP500` 与 Yahoo `^SPX`（免费免密钥，1,254 根）；成交侧第二轮改用 data-api 逐笔成交，覆盖 **259 个已结算 event / 303 条腿**（2025-10-15..2026-10-19），数量 ≥30。但只有约一年、日频 event 高度相关；CLOB `prices-history` 更早的仍返回 `{"history":[]}`（100 个已关闭日频 event 中仅 22 个非空），不能用来补更早样本。
3. **小资金能做：满足** — 单档 39–63 USDT、单 event ≤300 USDT、总 ≤900 USDT，远低于 2,500/5,000 上限；不加杠杆；买方最大亏损就是本金。容量也写清了：几千到十几万美元/event，但本条只放几百 USDT 是因为**价差太宽而不是容量太小**。
4. **不重复：满足**（请主审复核）— 我查过的：`known/KNOWN.md` 里与本主题最近的只有 `E-E1-index-etf-event`（指数纳入与 ETF 获批的**事件**，不是收盘价位）；`bots/dot/entries/dot-048-option-dispersion.md` 是**指数 vs 成分期权的隐含相关性**（CBOE COR/DSPX，标的是期权，不是单指数收盘价）；`bots/quant/notes/batch1-verification/quant-008.md` 只在 Hyperliquid `meta` 里出现 US500/NVDA 资产、**明确写了「未引用」**；quant-012 是地震计数基率、quant-011 是足球平局、quant-006 是网球 Elo——都不是股指收盘价。`grep -ril "SPX|S&P|lognormal|已实现波动"` 在 `bots/` 与 `known/` 下，除我自己在 `bots/quant/CLAIMS.md` 里那条 B11 声明行外，只命中上述 dot-048 与 quant-008 两个文件（即其它 bot 的文件）。差异点：**收益来源 = 用免费日线已实现波动率给指数收盘档位定价**，与 dot 的加密期权隐含波动率（C18）和指数-成分相关性（C48）都不同变量。
5. **扣成本后粗算够用：不满足** — 可成交价回放已经给出净数：全部触发腿 **−0.00743/份**、总净 **−1.783 份**、每 $1 **−0.0287**；日频 FADE 的 +0.00650/份中位数 −0.14482、CI 跨 0，OOS −0.02703；两个阶梯类型（monthly above −0.06948、monthly close −0.13662）都为负。fee=0 时全部触发腿仍 −0.00090/份。原来用模型算术算出的 +4.0¢/份在真实成交回放里没有出现。
6. **两周内能检验：满足（历史）/ 两周新增不够** — 历史回放已有 259 个 event，数量够；两周只能新增约 10–11 个日频 event，阶梯 0–1 个。**同一标的连续交易日高度相关**，252 个日频不能当 252 个独立结果，所以两周期新增样本仍不足以独立确认。
7. **出处可查：满足** — 每个价格/规则字段都有 URL + 访问日期 + 取数方式；2026-10-21 用 `notes/scheduler/scratch/H-quant-014/verify_sources.py` 逐条重取全部引用 URL（stdout：OK=40 / FAIL=0），并记录了时点变化（费率从 0.04 变 0、2026-10 事件数从 13 变 14、CLOB 覆盖从 21 变 22）；所有自己算的数字都有公式；失败项（stooq JS 挑战页、更早 `prices-history` 为空）照写，没有掩盖。

**建议：主项目核为退回（反证）**。本条的价值是记录“用 0.5 模型去打日频 SPX 涨跌/阶梯在真实成交价上不成立”，而不是作为交易策略；不要收录，也不要用它占新机制名额。若主项目仍想保留，只保留为“日频市场定价并不差”的反证。

## 出处

- https://gamma-api.polymarket.com/events?slug=spx-up-or-down-on-october-20-2026 — 访问 2026-10-20（2026-10-21 复核） — 已读（规则原文、`resolutionSource=https://www.wsj.com/market-data/stocks`、`endDate=2026-10-20T20:00:00Z`、`startDate=2026-10-19T12:00:52Z`、2026-10-20 快照 `outcomePrices=["0.625","0.375"]`、bid 0.62/ask 0.63、`feeSchedule.rate=0.04`、`umaBond=250`、`rewardsMinSize=100`、`series.slug=spx-daily-up-or-down`；2026-10-21 复核：已结算 `outcomePrices=["1","0"]`、`feeType=zero_fees`、`rate=0`、`volume=64129.27`）
- https://gamma-api.polymarket.com/events?slug=spx-close-dec-2026 — 访问 2026-10-20 — 已读（6 档 `outcomePrices`/bid/ask、Yahoo Finance `^GSPC` 结算源、「正好落在两档之间归上档」、`endDate=2026-12-31T21:00:00Z`、`volume=48152.545224999994`）
- https://gamma-api.polymarket.com/events?series_id=10383&limit=100&closed=true&order=endDate&ascending=false — 访问 2026-10-20 — 已读（100 个已关闭 event，按 `endDate` 月份 2026-05:3/06:21/07:21/08:21/09:21/10:13；`volume` 合计 $10,779,504.35；单 event volume 164,019.45 / 43,470.21 / 37,722.58 / 68,932.03）
- https://gamma-api.polymarket.com/events?slug=nvda-close-above-on-october-20-2026 — 访问 2026-10-20 — 已读（5 档 strike $210–$230、Pyth 1 分钟收盘结算源、相等判 No、`feeSchedule.rate=0.04`、vol 1,224.39）
- https://gamma-api.polymarket.com/public-search?q=SPX&limit_per_type=20&events_status=all — 访问 2026-10-20 — 已读（模板清单：`spx-up-or-down-on-<date>`、`spx-opens-up-or-down-on-<date>`、`spx-hit-<月>`、`spx-close-<月>`；`spx-hit-dec-2026` vol 425,924.99）
- https://gamma-api.polymarket.com/public-search?q=NVDA&limit_per_type=10&events_status=active — 访问 2026-10-20 — 已读（`what-price-will-nvda-hit-in-october-2026` vol 94,705.68、`nvda-up-or-down-on-october-20-2026` vol 140.17、`nvidias-market-cap-end-of-2026` vol 29,917.22）
- https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=5y&interval=1d — 访问 2026-10-20 — 已读（1,254 根，2021-10-20 4536.19 → 2026-10-19 7690.73；σ₂₀/σ₆₀/σ₂₅₂、上涨日占比 664/1253 的计算源）
- https://clob.polymarket.com/prices-history?market=37867517699597038332707589432698261528449111760519164430714310172860137405315&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（已关闭的 2026-10-16 event 有历史，21 个 event 的 `p6` 来源之一）
- https://clob.polymarket.com/prices-history?market=56470952261346405661865784125968649112655146418378832479574947524904990438477&interval=max&fidelity=60 — 访问 2026-10-21 — 已读（2026-09-18 已关闭 event 的 YES token，返回 `{"history":[]}`：更早的已关闭市场无价格历史；2026-10-21 复查 100 个已关闭日频 event 只有 22 个非空）
- https://stooq.com/q/d/l/?s=%5Espx&i=d — 访问 2026-10-20 / 2026-10-21 — **抓取失败**（都返回 JS 挑战页 `This site requires JavaScript to verify your browser`，未拿到 CSV，本条未使用）
- https://data-api.polymarket.com/trades?market=0x223e81ff2ad483a001bdfc50a14e7d55d805980e3a84507b43ba7880e27c21cb&limit=5 — 访问 2026-10-21 — 已读（逐笔成交字段 `conditionId/timestamp/price/side/outcome/size`；回放用 303 个 market、243,699 笔，2026-10-20 采集）
- https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500 — 访问 2026-10-20（q014-hist 采集）/ 2026-10-21 复核可达 — 已读（2,512 个交易日，2016-10-20..2026-10-19；回放模型输入；随机 5 个结算日与 `outcomePrices` 交叉核对 5/5）
- https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=6y&interval=1d — 访问 2026-10-21 — 已读（截到 2021-10-20..2026-10-19 后 1,254 根，σ₂₀/σ₆₀/σ₂₅₂ 与 2026-10-20 的 5y 抓取逐位一致；用于复核，不是回放输入）
