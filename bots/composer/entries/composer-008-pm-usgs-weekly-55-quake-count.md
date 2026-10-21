---
id: composer-008
name_zh: 全球M5.5+周计数：USGS定档
name_en: Weekly global M5.5+ earthquake count priced off USGS feed
bot: composer
date: 2026-10-21
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many 5.5 or above earthquakes worldwide <date range>?」多档（≤6 / 7 / … / >13）
venues: Polymarket
data: USGS FDSNWS Event API（免费免密钥）；Gamma 同系列 weekly event 结算档
test_2w: 独立结果按 event（周）计；已关闭 5.5+ 周 event 回放 + 2026-10-19 开放周前向；失败标准：USGS 计数与 UMA 档不一致率 >10%
status: 待核
confidence: 中
---

## 一句话

每个「全球 M≥5.5 地震本周几个？」event，用 USGS `fdsnws/event/1/query` 在 spec 周 ET 窗口内计数；以 **Poisson(λ)** 估各档概率（λ 来自滚动 52 周 USGS 周均值）；仅在 ask 低于 `p_lo−0.05` 且扣费后为正时买 YES，持有至 UMA 按 USGS 结算。

## 钱从哪里来

对手方常**按直觉均匀押 7–10 档**（2026-10-21 开放周各档 ask 0.10–0.16），而 2025 年 USGS 全球 M5.5+ **513 次/年 ≈ 9.9/周**（见证据），分布右尾厚，**≤6 档**有时被低估、**>13** 被高估（**需逐周回放验证**）。规则数据源与 quant 地震**基准率**条目不同：本条为 **固定 7 日窗口 + 5.5 阈值 + 多档 ladder**（quant-012 为震级频率模板，机制不同）。

## 规则

**结算要点（Gamma，slug `how-many-5pt5-or-above-earthquakes-worldwide-october-19-october-25`，2026-10-21 已读）**：

- 窗口：ET **2026-10-19 00:00 – 10-25 23:59**。
- 计数：全球 **M≥5.5**（USGS 目录）。
- 数据源：USGS Earthquake Hazards Program（`earthquake.usgs.gov/earthquakes/search/` 同等查询）。
-  substantial 地震后可能短暂延迟更新（规则原文）。

**交易**：λ = 最近 52 个已结算同系列周的实际 USGS 计数均值（不足则用 2024–2025 年周均值 ~7–10）；Poisson 算各 `groupItemTitle` 档 `p_lo`；单档 ≤300 USDT。

## 证据

### 1）USGS 年计数（API count，2026-10-21）

| 年 | M≥5.5 次数 |
|---|---:|
| 2024 | 344 |
| 2025 | 513 |

粗算 λ_week ≈ 513/52 ≈ **9.9**。

### 2）2026-10-19 周盘中价（Gamma，来源自报）

≤6 ask≈0.11；7–12 ask≈0.10–0.16；>13 ask≈0.20。

### 3）已结算样例

slug `how-many-5pt5-or-above-earthquakes-worldwide-august-31-september-6` → 结算档 **12**（Gamma outcomePrices，2026-10-21）。

### 4）当周进行中 USGS 计数（2026-10-19–10-21 部分周）

`starttime=2026-10-19&endtime=2026-10-25&minmagnitude=5.5` → **5** 次（**周未结束，非终局**）。

## 数据

- API：`https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5.5`
- Count：`.../event/1/count?format=geojson&starttime=...&minmagnitude=5.5`
- Gamma：`https://gamma-api.polymarket.com/events?slug=how-many-5pt5-or-above-earthquakes-worldwide-october-19-october-25`

## 两周内怎么检验

- 独立结果：每 7 天 event = 1；目标 **≥30** 已关闭 5.5+ 周 slug（Gamma 分页拉取）。
- 前向：10-19 周结束后 USGS 终值 vs 成交档。
- 失败：回放不一致率 >10%。

## 成本与容量

- 天气 rate=0.05（GUIDE；快照 fee=0 以 market 为准）。
- 占款 ~7 天；weekly event 频率高，5,000 USDT 可轮换。

## 风险

- **与 6.5 周 market 相关**：勿重复下注同一物理周两套阈值。
- **USGS 修订**：catalog 更新可能改计数。
- **Poisson 简化**：忽略主震-余震聚类。

## 改进了什么

不适用。

## 门槛自查

1. 机制：满足 — 均匀押档 vs Poisson 基准。
2. 数据：满足 — USGS 多年免费；closed 周需补至 30（**不确定**）。
3. 小资金：满足。
4. 不重复：与 quant-012 模板/阈值/窗口不同（**待核对 quant 条目原文**）。
5. 扣成本后：不确定。
6. 两周检验：满足 — 多 closed 周 + 1 开放周。
7. 出处：满足。

## 出处

- https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2024-01-01&endtime=2025-01-01&minmagnitude=5.5 — 2026-10-21 — 已读（344）
- https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2025-01-01&endtime=2026-01-01&minmagnitude=5.5 — 2026-10-21 — 已读（513）
- https://gamma-api.polymarket.com/events?slug=how-many-5pt5-or-above-earthquakes-worldwide-august-31-september-6 — 2026-10-21 — 已读（结算 12）
