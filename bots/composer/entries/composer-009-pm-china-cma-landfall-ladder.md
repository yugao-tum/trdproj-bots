---
id: composer-009
name_zh: 中国登陆台风：CMA年计数
name_en: China landfalling TC count priced off CMA best track
bot: composer
date: 2026-10-21
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many tropical cyclones will make landfall in China during 2026?」Fewer than 5 / 5 / … / >8
venues: Polymarket
data: CMA TC Data Center Landfalling TCs（结算 URL）；Gamma negRisk 多 market；JMA/历史 ESCAP 报告（二手）
test_2w: 独立结果按 2026 年 event 计；季中若 CMA 页可读则每 7 日 YTD 计数 + 盘口；失败标准：与 CMA 终值不一致或无法访问结算源仍强行下注
status: 待核
confidence: 低
---

## 一句话

2026 台风季，在 CMA **Landfalling TCs** 页面可访问时统计 **已登陆中国** 的热带气旋个数 N（含 TD 及以上、每 TC 计一次）；用历史年终分布估各 negRisk 档概率；当 **Exactly 8** 或 **>8** 等档 ask 偏离 N 所隐含剩余可能时买 YES/卖高估档（本条仅 bounded YES）；结算以 CMA 2026 Best Track 更新为准。

## 钱从哪里来

规则认 **CMA** 独占口径（含南海岛屿定义，见 Gamma 全文）。2026-10-21 Gamma：**Exactly 8** 档 mid≈0.425、**>8** mid≈0.345（**来源自报**），而季中 N 的公开可读性在自动化环境下差（见数据节）。对手方可能**按常年气候平均或媒体台风数**定价，与 CMA「登陆」定义（含 TD、去重多登陆）不一致；你赚的是**口径对齐**（若能读到 CMA YTD）。

## 规则

**结算要点（Gamma，event `how-many-tropical-cyclones-will-make-landfall-in-china-during-2026-20260805184236864`，2026-10-21 已读）**：

- 数据源：`https://tcdata.typhoon.org.cn/en/dlrdqx.html` 2026 年报 **Landfalling TCs**。
- 计数：所有强度 **登陆中国** 的 TC，每 TC 一次。
- 2027-06-30 前未更新 → ESCAP/WMO Typhoon Committee 2026 最终报告（规则原文）。

## 证据

### 2026-10-21 Gamma（来源自报，未核实）

| 档 | outcome 中点（约） |
|---|---:|
| Fewer than 5 | 0.005 |
| 5 | 0.001 |
| 6 / 7 | （中间档，见 event） |
| 8 | 0.425 |
| Greater than 8 | 0.345 |

volume 合计 ~195k USDT（Gamma 自报）。

### CMA 页访问（2026-10-21）

`curl` 拉取 `tcdata.typhoon.org.cn/en/dlrdqx.html` → **0 字节**（**未读到 YTD 列表**）。本条 **不能声称当前 N**。

## 数据

- 结算：`https://tcdata.typhoon.org.cn/en/dlrdqx.html`
- Gamma：`https://gamma-api.polymarket.com/events?slug=how-many-tropical-cyclones-will-make-landfall-in-china-during-2026-20260805184236864`
- 缺失：**可机读 YTD**；云环境对 .cn 可达性 **未验证通过**

## 两周内怎么检验

- 独立结果：1 event/年。
- 两周内：每日/每 7 日尝试 HTTP 访问 CMA + 记录 **8/>8** ask；若始终不可读，标 **待选区** 并只做规则研究。
- 失败：CMA 永久不可达时仍持仓（规则有 ESCAP 兜底）。

## 成本与容量

- feeSchedule rate=0（快照）；占款至 2027 年中。
- negRisk 结构：一次仅一档 YES=1。

## 风险

- **无法读 CMA**：策略无法执行，仅能人工。
- **与 composer-002 大西洋飓风** 同为「季中计数 ladder」，但 **数据源/盆地完全不同**，不算变体。
- **confidence 低**：证据弱。

## 改进了什么

不适用。

## 门槛自查

1. 机制：满足 — CMA 口径 vs 媒体计数。
2. 数据：**不满足/不确定** — 本次未读到 CMA 页；历史 ESCAP 未逐条录入。
3. 小资金：满足。
4. 不重复：满足。
5. 扣成本后：不确定。
6. 两周检验：不确定 — 依赖 CMA 可达。
7. 出处：Gamma 已读；CMA **未读**（连接失败）。

## 出处

- https://gamma-api.polymarket.com/public-search?q=tropical+cyclones+china+2026 — 2026-10-21 — 已读（event 嵌入 markets）
- https://tcdata.typhoon.org.cn/en/dlrdqx.html — 2026-10-21 — **未读**（HTTP 空响应）
