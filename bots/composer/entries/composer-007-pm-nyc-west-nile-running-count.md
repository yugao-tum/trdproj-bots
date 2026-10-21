---
id: composer-007
name_zh: NYC西尼罗：运行计数定档
name_en: NYC West Nile neuroinvasive count priced off DOH running tally
bot: composer
date: 2026-10-21
market: polymarket
pm_category: other
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many West Nile neuroinvasive disease cases … NYC residents in 2026?」Fewer than 20 / 20–34 / 35–49 / 50+
venues: Polymarket
data: NYC DOH West Nile Summary 页面（免费）；1999–2025 汇总表（同站）；Gamma event 规则
test_2w: 独立结果按 event（2026 季 1 个）；每日 DOH 页 YTD 计数 + 盘口快照 ≥14 次；失败标准：DOH 修订与解析不一致或已成交 YES 中位毛利 ≤0
status: 待核
confidence: 中
---

## 一句话

2026 年 10–11 月，每周读取 NYC DOH **West Nile Virus Reports** 页面上 **2026 Positive Results** 中 **neuroinvasive** 累计整数 C；用 1999–2025 同页汇总表的季节末分布估计「再增 Δ 例」概率，映射到 20–34 / 35–49 / 50+ 档；当 C 已 ≥31 且 **35–49** ask 低于 `p_lo−0.05` 时买 YES（或 C≤19 时买 Fewer than 20），持有至 DOH 2027-01-01 页面上 2026 终值 resolve。

## 钱从哪里来

付钱给你的是**未读 DOH 运行计数、仍按季初先验押档**的对手方。规则只数 **NYC 居民 neuroinvasive**（脑炎/脑膜炎/急性弛缓性麻痹），数据源为 DOH **West Nile Virus Reports** 页（Gamma slug `west-nile-neuroinvasive-cases-nyc-2026-20260820104404`，2026-10-21 已读）。2026-10-21 页面快照 **C=31**，已落在 **20–34** 档内，但 **35–49** ask≈0.13 仍隐含非零尾部；若 10 月下旬新增病例稀少（历史 10 月后增量有限），则 **35+** 可能被高估（**需逐日 DOH 更新验证**）。

## 规则

**结算要点（Gamma，2026-10-21）**：

- 计数：**2026 日历年** NYC 居民 **neuroinvasive** 合计。
- 数据源：`nyc.gov/site/doh/health/health-topics/west-nile-virus-reports.page` 上 **2026** 终值；2027-01-01 页显示的 2026 数为起点（规则原文）。
- 档位：Fewer than 20 / 20 to 34 / 35 to 49 / 50 or more（互不重叠）。

**交易规则（提案）**

1. 每 **3 日** 拉取 DOH 页 HTML，解析 **2026 Positive Results** 表格 neuroinvasive **All NYC** 整数 C。
2. 用汇总页 `west-nile-virus-reports-summary.page` 1999–2025 **neuroinvasive** 年终值，估 10/21 后剩余增量 Δ 的保守上界（负二项或「剩余季节为 0」基准）。
3. 若 C=31：P(20–34) 在「无新增」时为 1；仅当 **35–49** 的 `p_lo` 来自历史「10 月后仍 +≥4 例」频率 &gt; ask+0.05 时买 35–49 YES。
4. 单档 ≤300 USDT，event ≤600 USDT。

## 证据

### 1）2026-10-21 DOH 页（已读 HTML）

- **2026 Positive Results** 段：**West Nile Neuroinvasive Disease** → **All NYC = 31**（`west-nile-virus-reports.page`）。

### 2）2026-10-21 Gamma 盘口（来源自报，未核实）

| 档 | ask（约） |
|---|---:|
| Fewer than 20 | 0.008 |
| 20 to 34 | 0.835 |
| 35 to 49 | 0.130 |
| 50 or more | 0.043 |

### 3）历史 neuroinvasive 年终（DOH summary 页，2026-10-21）

| 年 | neuroinvasive |
|---:|---:|
| 2024 | 26 |
| 2023 | 31 |
| 2022 | 36 |
| 2021 | 18 |
| 2020 | 6 |

说明年际波动大；**2026 已 31 例** 与 2023 全季相当，**10 月后是否 +4 例进 35–49** 为关键（**未做正式生存/计数过程回测**）。

## 数据

- DOH 2026 表：`https://www.nyc.gov/site/doh/health/health-topics/west-nile-virus-reports.page`
- 历史：`https://www.nyc.gov/site/doh/health/health-topics/west-nile-virus-reports-summary.page`
- Gamma：`https://gamma-api.polymarket.com/events?slug=west-nile-neuroinvasive-cases-nyc-2026-20260820104404`
- 缺失：DOH 逐日机读 API（仅 HTML 解析）

## 两周内怎么检验

- **独立结果**：2026 单 event = 1。
- **前向**：≥14 次 (C, bid/ask) 快照（每 3 日或 DOH 更新日）。
- **失败标准**：HTML 解析与人工目视差 ≥1；或买 35–49 后 C 连 14 日不变且 ask 未收敛。

## 成本与容量

- other 板块 rate=0.05（GUIDE；以 market 为准）。
- 占款至 2027 初 resolve 窗口（规则以 2027 页为准），**占款长**。
- 频率：每年 1 个 NYC WNV event；5,000 USDT 足够。

## 风险

- **DOH 页修订**：回溯修正 C。
- **C 已 31**：买 20–34 已无 upside（ask 0.83）；主要博弈 35+ tail。
- **quant B16 麻疹计数** 同族「官方周报计数」但疾病/数据源不同，**不重复**。
- **样本**：历史仅 ~25 年 NYC，且 PM 仅 1 个 2026 event。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清：满足** — YTD 公开计数 vs 滞后 ladder。
2. **有免费数据能检验：不确定** — DOH 免费；**PM 仅 1 event**，30 独立结果需用 **历史年份作伪独立** 或标待选区。
3. **小资金能做：满足**。
4. **不重复：满足** — 无 NYC WNV 条目。
5. **扣成本后粗算够用：不确定** — tail 档 edge 未量化。
6. **两周内能检验：满足** — 14+ 快照。
7. **出处可查：满足**。

## 出处

- https://www.nyc.gov/site/doh/health/health-topics/west-nile-virus-reports.page — 访问 2026-10-21 — 已读（2026 neuroinvasive=31）
- https://www.nyc.gov/site/doh/health/health-topics/west-nile-virus-reports-summary.page — 访问 2026-10-21 — 已读（2020–2024 neuro 表）
- https://gamma-api.polymarket.com/events?slug=west-nile-neuroinvasive-cases-nyc-2026-20260820104404 — 访问 2026-10-21 — 已读
