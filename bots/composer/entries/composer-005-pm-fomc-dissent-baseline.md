---
id: composer-005
name_zh: FOMC异议票：声明解析定档
name_en: FOMC funds-rate dissent count priced off statement text
bot: composer
date: 2026-10-21
market: polymarket
pm_category: economics
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many dissent at the <month> Fed meeting?」档位 0 / 1 / 2 / 3 / 4+
venues: Polymarket
data: 美联储 FOMC 声明 HTML/PDF（免费）；Gamma 同系列已结算 event；fomccalendars.htm 会议日程
test_2w: 独立结果按每次 FOMC 会议计；已结算 dissent 系列 ≥10 个 event + 2026-10-28 会议前向；失败标准：声明解析与官方计票不一致或已成交 YES 中位毛利 ≤0
status: 待核
confidence: 低
---

## 一句话

每次 FOMC 利率决策声明发布后（或会议前用「零异议」基准率 + 公开点阵/委员公开言论作弱先验），从 **FOMC 官方声明** 解析对 **联邦基金利率** 决策的 **dissenting votes 人数**，映射到 Polymarket 档位；只在 ask 低于历史基准率下限减 5¢ 且扣费后仍为正时买 YES，持有至 UMA 按声明 resolve。

## 钱从哪里来

付钱给你的是**把「异议」当成头条叙事、在 0–3 票区间近似均匀押注**的对手方。规则只数 **对 Fed Funds Rate 决策的 dissenting votes**（见 2026-10 月 meeting 规则原文），不是对 SEP 或工具使用的泛化「反对」。多数会议 **0 或 1 票异议**（见下表已结算 PM 样本）；市场在 0/1/2/3 上常给出接近 20–25% 的 ask（2026-10-21 10 月 meeting 快照），若基准率集中在 0–1，则 **高估 2+** 的档位有 fade 空间（**需扣费后逐档验证**）。

## 规则

**结算原文要点（Gamma，slug `how-many-dissent-at-the-october-fed-meeting`，2026-10-21 已读）**：

- 会议：**2026-10-27 至 10-28**；声明约 **2:00 PM ET 10-28** 发布。
- 计数：**对 monetary policy 决策中 Fed Funds Rate 的 dissenting votes**。
- 数据源：**FOMC statement**（`federalreserve.gov` 日历页链接的当次声明）。
- 声明缺失时按规则 extension / consensus（以 Gamma 全文为准）。

**交易规则（提案）**

1. **解析**：声明中 “Voting against the action were …” / “dissented because …” 句段，计 **人数**（同一委员一票）；无人 dissent → **0**。
2. **基准率**：滚动最近 **20 次** 已 resolve 的同结构 PM event + 人工核对对应声明（本次已核 **10** 次 PM 结算，见证据）。
3. **进场**：会议声明发布后 30 分钟内，或会议前仅当某档 `ask ≤ p_lo − 0.05` 且 `p_lo` 来自基准率（保守用 10-event 频率）；单档 ≤300 USDT，单 event ≤600 USDT。
4. **出场**：持有至 resolve；不在声明未出前赌 4+  unless `p_lo` 支持。

## 证据

### 1）2026-10-21 Gamma 10 月 meeting 盘口（来源自报，未核实）

| 档 | ask（约） |
|---|---:|
| 0 | 0.25 |
| 1 | 0.23 |
| 2 | 0.25 |
| 3 | 0.20 |
| 4+ | 0.073 |

### 2）2026 年已结算同系列（Gamma outcomePrices，2026-10-21 拉取）

| event（slug 缩写） | 结算档 |
|---|---|
| september-fed-meeting | **0** |
| july-fed-meeting-202606… | **3** |
| next-fed-meeting（多条） | **2** / **1** 等 |

在 **13 个** 已关闭 `how-many-dissent-at-the-*` event 上统计 winning 档（`notes/dissent_resolved.json`，2026-10-21 脚本）：**0→2，1→3，2→3，3→2**（**仍 <30**）。

### 4）成交价层（data-api，T22，2026-10-21 12:11 UTC）

会前规则，不是声明发布后的解析。预测档 = 此前已结算次数的众数（并列取较小档）。进场 = 该档在 endDate 当天 **16:00 UTC** 前 48 小时内、价格 (0.02, 0.97) 的 YES 成交中位数。16:00 UTC 早于通常 14:00 ET 的声明。费用每份 `0.05×p×(1−p)`。脚本 `replay/composer-005/trade_replay.py`。

已结算 **10**。第一场无先验。其余 **9** 场都有窗内成交，**1 胜 8 负**，均值 **−0.2316/份**。唯一命中是 2026-01-28（预测 `2`、结算 `2`、进场 0.37）。n=9，不宣称显著。这条会前规则扣费后为负。声明解析仍等 **2026-10-28**。

### 3）机制对照

muse 条目含 FOMC **期货隐含概率**比价；本条仅 **声明可数的 dissent 人数**，数据源与 muse 不重复。

## 数据

- 日历：`https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm`
- 声明：当次 `https://www.federalreserve.gov/newsevents/pressreleases/monetary2026*.htm`（**具体 URL 会议前一日确认**）
- Gamma：`https://gamma-api.polymarket.com/events?slug=how-many-dissent-at-the-october-fed-meeting`
- 缺失：1990 以来全体 FOMC 异议机器可读表（需从声明/PDF 人工或半自动爬取补 30 会议）

## 两周内怎么检验

- **独立结果**：每次 FOMC 利率会议 = 1 个。
- **前向**：2026-10-28 声明发布后 1 小时内解析并对比 UMA 档。
- **历史**：两周内补拉 closed dissent slug 至 **≥30**，并各配一条声明 URL 人工核对。
- **失败标准**：解析人数与 Fed 声明官方表述不一致；或 30 会议中基准率模型 log loss 劣于市场中间价。

## 成本与容量

- 经济板块费率 **0.05**（GUIDE；以 market `feeSchedule` 为准）。
- 例：买 YES@0.25 → 费用占比约 `0.05×0.75=3.75%` + 半价差。
- 占款：会议前下单至 resolve，约 **0–7 天**（10 月 event 约 7 天）。
- 频率：约 **8 次 FOMC/年**；5,000 USDT 单 event 600 足够。

## 风险

- **声明措辞**： dissent 须绑定 **rate decision**；若规则解读偏宽/窄，解析错。
- **样本仅 10 个 PM event**：基准率不稳。
- **无 edge 可能**：0–3 档 ask 接近均匀时，扣费后 EV 可为负。
- **与 muse FOMC 期货策略相关但不同腿**：勿合并仓位假设。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清：满足** — 叙事型均匀押注 vs 可解析的声明计数。
2. **有免费数据能检验：不确定** — 声明免费；**≥30 独立结果未齐**（现 10 PM + 待补 Fed 历史）。
3. **小资金能做：满足**。
4. **不重复：满足** — 非 muse 期货隐含；非 quant 已列模板。
5. **扣成本后粗算够用：不满足（会前基准率）** — 9 笔成交，1 胜 8 负，均值 −0.2316/份（`replay/composer-005/`）。声明发布后的解析还没有成交样本。
6. **两周内能检验：满足** — 10-28 会议 + 扩 slug。
7. **出处可查：满足**。

## 出处

- https://gamma-api.polymarket.com/events?slug=how-many-dissent-at-the-october-fed-meeting — 访问 2026-10-21 — 已读（规则、档位、ask）
- https://gamma-api.polymarket.com/events?slug=how-many-dissent-at-the-september-fed-meeting — 访问 2026-10-21 — 已读（结算 0）
- https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm — 访问 2026-10-21 — 已读（2026-10-27/28 会议）
