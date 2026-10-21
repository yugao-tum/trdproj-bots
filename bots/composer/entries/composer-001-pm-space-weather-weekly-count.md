---
id: composer-001
name_zh: 空间天气周计数：SWPC预报定档
name_en: Weekly major space weather count priced off NOAA SWPC forecasts
bot: composer
date: 2026-10-21
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many major Space Weather events this week? (<date range>)」多档计数（0/1/2/…）
venues: Polymarket
data: NOAA SWPC 3 日地磁预报文本（免费免密钥）；SWPC alerts.json（免费）；Gamma/CLOB 公开接口；已结算同系列 8 个 event 的 outcomePrices（2026-04 至 05）
test_2w: 独立结果按 event（周）计；用 2026 年已结算 8 周 + 公开预报对下一开放周的档位做校准，两周内可再跟 2 个新 event；历史回放目标 ≥30 个 event（需向 Gamma 拉取更多已关闭 slug，本次已核 8 个）
status: 待核
confidence: 中
---

## 一句话

每个「本周重大空间天气事件有几个？」event 开盘前后，用 NOAA SWPC 未来 3 天地磁活动概率表估计各档（0、1、2…）概率；只在某一档的卖价低于模型下限且扣完吃单费与半价差后仍有 ≥5¢ 边际时，限价买该档 YES，持有至该 event 结算。

## 钱从哪里来

付钱给你的是**把「G1 监视/活跃」当成「G3+ 重大事件」、或把低基准率周当成 50/50 猜**的对手方。规则只认 SWPC 表格里 **G3+ 地磁暴、S3+ 太阳质子、R3+ 射电黑障**（见规则原文与 https://www.swpc.noaa.gov/noaa-scales-explanation ），而 SWPC 日常预报里大量是 G1 监视（WATA20）或低于 G1 的活跃，**不计入**计数。市场参与者若不看尺度说明，会系统性高估「≥1 个重大事件」的概率；你赚的是**公开预报与规则口径对齐后的校准误差**。

## 规则

**结算原文要点（Gamma，event `how-many-major-space-weather-events-this-week-may-3-may-9`，2026-10-21 已读）**：

- 统计窗口：美东 12:00 AM 至 11:59 PM 的指定 7 天。
- 计数对象：该周内发生的 **G3+ / S3+ / R3+** 各算 1 次；同一事件若先低后高，仅初始报告算一次，除非在窗口内从非 qualifying 升到 qualifying。
- 数据源：NOAA SWPC 网站「Current Space Weather Conditions」下 **「ALERTS, WATCHES AND WARNINGS」** 表（https://www.swpc.noaa.gov/products/alerts-watches-and-warnings#）。
- 若数据源永久不可用，resolve 到**最低档**。
- 落在两档之间 resolve 到**较高档**。

**交易规则（提案）**

1. **模型输入（只用免费公开）**：`https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt` 中「Strong-Extreme storm」三档概率（21–23 Oct 2026 快照为 01/01/01，即每日 1% 量级）；`https://services.swpc.noaa.gov/products/alerts.json` 仅用于核对是否已出现 qualifying 告警（不把 G1 Watch 计入模型事件数）。
2. **周计数分布**：将 7 天内「至少一次 G3+ 地磁」近似为 Bernoulli(p)，p 由 3 日预报 Strong-Extreme 概率按日并集上界估计（保守取 `p = 1 - ∏(1 - p_day)`，p_day 来自预报表）；S3/R3 在 quiet 周单独加 Poisson 小项 λ=0.05/周（来自 2026 年 8 个已结算周仅 1 周计数为 2、0 周出现 ≥3 的粗样本，**样本极短，标为不确定**）。
3. **进场**：对 event 内每一档 i，算模型概率下限 `p_lo_i`；若 `ask_i ≤ p_lo_i − 0.05` 且该档 `acceptingOrders=true`，限价吃单买 YES；同一 event 最多 2 个相邻档，单档 ≤300 USDT，单 event ≤800 USDT。
4. **出场**：持有至 UMA 结算，不主动平仓。
5. **不做**：不把 G1/G2 监视当 edge；不在数据源 outage 时赌「resolve 最低档」（那是极端尾部，单独标风险）。

## 证据

### 1）2026 年已结算同系列 8 周（Gamma outcomePrices，2026-10-21 拉取）

| 周结束 (UTC) | 判定档（groupItemTitle） |
|---|---|
| 2026-04-11 | <3（与 0 事件一致的多档结构） |
| 2026-04-18 | <3 |
| 2026-04-25 | 2 |
| 2026-05-02 | 0 |
| 2026-05-09 | 0 |
| 2026-05-16 | 0 |
| 2026-05-23 | 0 |
| 2026-05-30 | 0 |

**0 事件占 5/8 = 62.5%**；≥1 占 3/8；≥2 占 1/8。说明基准率极低，任何把「≥1」定价到 40%+ 的周都有 fade 空间（需逐周盘口验证，本次未拉历史 ask）。

### 2）预报与规则口径差异（2026-10-20 快照）

- 3 日预报：`Strong-Extreme storm 01/01/01`（10-21–10-23），对应 G3+ 概率极低。
- 同期 alerts.json 含多条 **G1 Predicted** 监视（WATA20），**不计入**本 event 计数。
- 推断：若某周 market 因「有 watch 活动」把「≥1」抬价，而预报 Strong-Extreme 仍 ≈1%，则买 **0** 或最低档 YES 在规则意义下与预报一致（具体档位名以 Gamma 为准）。

### 3）成交价层（data-api，T25，2026-10-21 15:39 UTC）

没有历史预报原文。测的是静态规则：周开始前 48 小时（美东零点前）买标题为 `0` 的 YES，价格在 (0.02, 0.97)，费用每份 `0.05×p×(1−p)`。没有 `0` 这一档的周不算成最低档。

8 个已关闭周。3 周梯子是 `<2` 或 `<3`，没有 `0`，其中 4 月 19 日那周结算是 `2`。另外 5 周有 `0` 且都结算为 `0`。这 5 周里 2 周在窗口内没有成交，3 周有成交且都命中：进场 0.80、0.536、0.77，均值 **+0.2882/份**。n=3，不宣称显著。状态仍待核。脚本 `replay/composer-001/trade_replay.py`。

来源自报的 PM volume/liquidity 未用成交明细复现（**来源自报，未核实**）。

## 数据

- SWPC 3 日地磁预报：`https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt`（免费免密钥，2026-10-21 HTTP 200）
- SWPC 警报 JSON：`https://services.swpc.noaa.gov/products/alerts.json`（84 条滚动消息，2026-10-21）
- SWPC 尺度说明：`https://www.swpc.noaa.gov/noaa-scales-explanation`
- Polymarket Gamma：`https://gamma-api.polymarket.com/public-search?q=how-many-major-space-weather-events&limit_per_type=50&events_status=closed`；`events?slug=<slug>`
- 缺失：逐档历史 CLOB 盘口（GUIDE：历史盘口无公开源，需从现在起前向记录）；2026-10 当周是否仍有新 event 开盘 **未在本条写入前逐 slug 确认**

## 两周内怎么检验

- **独立结果**：每个 7 天 event = 1 个结果（同 event 多档共享计数，算 1 个）。
- **两周内**：跟 2 个新 event 的开盘盘口 + 用 SWPC 预报算 `p_lo`，记录是否触发进场；同时对已结算 8 周做回放（用**事后**预报不可，仅用「若当时 Strong-Extreme 为 1% 则模型给 P0≈0.97」的静态敏感性）。
- **扩展到 30 个结果**：向 Gamma 拉取 2025–2026 全部已关闭 `how-many-major-space-weather-events-this-week-*` slug（本次 8 个），两周内脚本化拉取并人工核对 SWPC 归档是否 qualifying；不足 30 则标为待选区。
- **失败标准**：已成交 YES 的中位毛利 ≤0；或 30 event 回放中模型 log loss 劣于市场中间价；或单 event 成交额 <50 USDT（容量失败）。

## 成本与容量

- **费率**：天气板块 `feeSchedule.rate=0.05`（Gamma 同系列 event 快照，2026-05 市场；以各档 `markets?slug=` 为准）。
- **吃单费示例**：p=0.15 → 费用占比 `0.05×(1−0.15)=4.25%`；再加半价差（典型 1–2¢）。
- **单笔**：≤300 USDT/档；**占款**约 7 天 + 争议缓冲。
- **频率**：2026-04/05 各 4 个 event，约 **每周 1 个**；5,000 USDT 可轮换 2–3 个重叠 event。
- **容量**：2026-05 样本 event `volume≈5,900 USDT`（Gamma 自报），800 USDT/event 占比高，需实测滑点。

## 风险

- **样本过短**：仅 8 周结算，λ 估计不可靠；太阳活动上行周可能连续 ≥1。
- **规则只认 SWPC 表格**：与 alerts.json 推送时间可能不同步；以结算源为准。
- **resolve 最低档条款**：数据源永久 outage 时全仓指向最低档——极端但写进规则。
- **G1 误读**：把监视当 storm 会在社交端放大「≥1」价格，你可能在预报已 quiet 时仍遇对手方抬价。
- **平台**：`restricted` 市场；历史盘口缺失导致无法证明过去 edge，只能前向检验。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 对手方混淆 G1 监视与 G3+ 计数；你用 SWPC 官方尺度 + 3 日 Strong-Extreme 概率对齐规则。
2. **有免费数据能检验：满足** — SWPC 文本/JSON + Gamma 结算档；收益数据来自 PM 结算与（可选）前向盘口。
3. **小资金能做：满足** — 300/档、800/event，无杠杆。
4. **不重复：满足** — 仓库内未检索到 space weather 条目（GitHub code search 无命中）；与 quant 天气类（龙卷风/干旱/ERA5）机制不同（SWPC 警报计数 + 周频 Poisson）。
5. **扣成本后粗算够用：不确定** — 有 `0` 档的 3 笔成交都命中，均值 +0.2882/份（`replay/composer-001/`）。n=3，另外 2 周没有窗内成交，3 周根本没有 `0` 档。不能写成扣成本后必为正。
6. **两周内能检验：不确定** — 8 个历史 event <30；可两周内扩 slug 列表，若仍 <30 则待选区。
7. **出处可查：满足** — 下列 URL + 访问日期。

## 出处

- https://www.swpc.noaa.gov/noaa-scales-explanation — 访问 2026-10-21 — 已读（G/R/S 3+ 定义）
- https://services.swpc.noaa.gov/text/3-day-geomag-forecast.txt — 访问 2026-10-21 — 已读（Strong-Extreme 01/01/01）
- https://services.swpc.noaa.gov/products/alerts.json — 访问 2026-10-21 — 已读（84 条，含 WATA20 G1 监视样例）
- https://gamma-api.polymarket.com/events?slug=how-many-major-space-weather-events-this-week-may-3-may-9 — 访问 2026-10-21 — 已读（规则全文、7 档结构）
- https://gamma-api.polymarket.com/public-search?q=how-many-major-space-weather-events&limit_per_type=50&events_status=closed — 访问 2026-10-21 — 已读（8 个已关闭 event slug）
