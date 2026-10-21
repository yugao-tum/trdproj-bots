---
id: composer-004
name_zh: 霍尔木兹周过境：Portwatch累加定档
name_en: Weekly Hormuz transit ladder priced off IMF Portwatch daily sums
bot: composer
date: 2026-10-21
market: polymarket
pm_category: geopolitics
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many ships transit the Strait of Hormuz week of <date range>」多档计数（<20 / 20-24 / …）
venues: Polymarket
data: IMF PortWatch ArcGIS 公开层 `Daily_Chokepoints_Data`（chokepoint6=霍尔木兹，`n_total` 日过境次数，免费免密钥，2019-01 起）；Gamma 同系列 event 规则与结算档
test_2w: 独立结果按 event（周）计；已结算同系列 24 个 event 回放 + 两周内跟 2 个开放周（含 2026-10-19 周）每日累加与盘口；历史 closed slug 若分页仍 <30 则标待选区；失败标准：已成交 YES 中位毛利 ≤0 或累加和与 UMA 结算档不一致
status: 待核
confidence: 中
---

## 一句话

每个霍尔木兹「本周过境船次」event 内，用 IMF PortWatch 公布的逐日 `n_total` 做 7 日滚动累加；在当周尚未出齐 7 天数据前，用「已观测日之和 + 剩余日条件期望」算各档概率下限；只在某档 ask 低于 `p_lo − 0.05` 且扣吃单费后仍为正时买 YES，持有至 PortWatch 数据齐备后 UMA 结算。

## 钱从哪里来

付钱给你的是**把地缘头条当成恒定高流量、或忽视 PortWatch 发布滞后与 AIS 覆盖缺口**的对手方。规则只认 IMF PortWatch 对霍尔木兹的 **transit calls**（与 `n_total` 一致），且每周单独结算。冲突期日过境可从常态数十次/日骤降到个位数（2026-10-14–10-18 API 快照为 3、2、7、0、4），而盘口仍可能按「恢复常态」定价中间档；你用**可下载的日序列累加**约束当周可能总数，赚的是**公开数据与情绪定价之间的偏差**。另有一批参与者不读 ArcGIS 更新节奏（每周二 9 ET 批量修订、约 5 日滞后），在数据落库前 overpay 中间档。

## 规则

**结算原文要点（Gamma，slug `how-many-ships-transit-the-strait-of-hormuz-week-of-october-19`，2026-10-21 已读）**：

- 统计：美东日历 **2026-10-19 至 10-25**  inclusive 全部日期的过境次数**总和**。
- 计数：container、dry bulk、RoRo、general cargo、tanker；**未出现在 IMF PortWatch 的船不计**。
- 数据源：IMF PortWatch 对 Strait of Hormuz 的报告；与 `portid=chokepoint6` 的 `n_total` 一致。
- 数据在 spec 周结束后 **14 个日历日**内未发布则按已发布部分 resolve（极端条款）。
- 落在两档之间 resolve 到**较高档**（与同系列其他周 event 一致）。

**交易规则（提案）**

1. **日数据拉取**：`Daily_Chokepoints_Data/FeatureServer/0/query?where=portid='chokepoint6'&outFields=date,n_total`（分页至覆盖 spec 周；脚本见 `notes/hormuz_portwatch_weekly.py`）。
2. **周内累加**：对 spec 周每一天求和得 `S`；交易期内若仅出齐 `k<7` 天，记 `S_obs`，剩余 `7−k` 天用过去 8 周同星期几的 median 日计数作条件期望（保守取下界分位 25%）。
3. **档位映射**：按 Gamma `groupItemTitle`（`<20`、`20-24`、…）把 `S` 或 `S_obs` 的预测区间映射到各档 `p_lo`。
4. **进场**：event 开放且 `acceptingOrders=true` 时，若某档 `ask ≤ p_lo − 0.05`，限价买 YES；单档 ≤300 USDT，单 event ≤800 USDT。
5. **出场**：持有至结算；PortWatch 出齐 7 日后不再加仓（避免与 UMA 抢跑争议）。
6. **不做**：把 Bab el-Mandeb 或其他 chokepoint 计数混进本 event；不在 IMF 标注的 AIS blackout/干扰日假装精度（那些日 widen 区间）。

## 证据

### 1）2026-09-28 周已结算 event 与 PortWatch 回放（2026-10-21 自算）

| 项目 | 数值 |
|---|---:|
| Spec 周 | 2026-09-28 – 2026-10-04（7 天） |
| PortWatch 7 日 `n_total` 之和 | **19** |
| Gamma 结算档（`outcomePrices` YES=1） | **<20** |

来源：Gamma slug `how-many-ships-transit-the-strait-of-hormuz-week-of-september-28`；ArcGIS 累加与 `notes/hormuz_portwatch_weekly.py` 输出一致（**自算，未由 UMA 独立复核**）。

### 2）2026-10-19 开放周盘中价 vs 已出数据（2026-10-21 22:00 UTC 前）

- API 最新日：**2026-10-18**（spec 周仅第 0 天在窗口内，10-19 尚未发布）——**当周累加尚不可终局**。
- 同日 Gamma 中间档 ask 示例：`<20` 0.16、`20-24` 0.32、`25-29` 0.33（**来源自报，未核实**）。
- 2026-07-07 周 PortWatch 7 日和 = **83**（高流量周，对照说明档位跨度大）。

### 3）批量回放（`notes/hormuz_backtest_all.py`，2026-10-21）

| 指标 | 数值 |
|---|---:|
| closed 周 event | **26** |
| 可解析 week_start | 24 |
| PortWatch 7 日累加 vs 结算档一致 | **20/24（83.3%）** |

摘要见 `notes/HORMUZ_REPLAY_SUMMARY.md`。不一致多出现在 2026-04/05 档位刻度与现结构差异或 PortWatch 事后修订（**推断**）。

### 4）同系列 closed 数量

Gamma 搜索仍可能分页不全；目标两周内补拉至 ≥30 slug 或维持待选区说明。

## 数据

- ArcGIS：`https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=portid%3D%27chokepoint6%27&outFields=date%2Cn_total&f=json`
- IMF 方法说明（滞后、AIS 限制）：`https://portwatch.imf.org/pages/data-and-methodology`
- Gamma 示例：`https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-the-strait-of-hormuz-week-of-october-19`
- 缺失：历史各档 CLOB 盘口时间序列（GUIDE：需前向记录）；2025 年同系列 slug 未全量拉取

## 两周内怎么检验

- **独立结果**：每个 7 天 event = 1 个结果。
- **历史**：对 24 个已关闭 event 用 PortWatch 重算 `S`，与 winning `groupItemTitle` 对照（目标一致率 ≥90%；失败则模型或日期对齐错误）。
- **前向**：跟 **2026-10-19** 与下一开放周；每个 PortWatch 新日发布后记录累加与各档 bid/ask（≥14 次日更观测）。
- **扩展到 30 个 event**：Gamma 分页补拉 2025–2026 slug；不足 30 则门槛 2/6 标「不确定」。
- **失败标准**：已成交 YES 中位毛利 ≤0；或重算 `S` 与结算档不一致率 >10%。

## 成本与容量

- 地缘板块 `feeSchedule.rate=0`（2026-10-19 周 event 快照；以各 market 实取为准）。
- 无吃单费时仍计 **半价差**（例：ask 0.32 → 约 16% 占本金）。
- 单笔 ≤300 USDT/档；占款约 7 天 + PortWatch 发布滞后（最长规则 14 天）。
- 频率：2026 年约 **每周 1 个** event；5,000 USDT 可覆盖 2–3 个重叠周。
- 容量：2026-09-28 周 event `volume≈` 数千 USDT（Gamma 自报，**未核实**）；冲突期深度可能骤降。

## 风险

- **AIS 缺口/干扰**：IMF 公开说明霍尔木兹周边 transponder 关闭与 GPS 干扰会导致 **undercount**；规则仍以 PortWatch 为准，模型与真实航运感受可能背离。
- **数据修订**：PortWatch 历史序列会 backfill（方法页 2024-10 修订）；交易后修订可能改变 `S`。
- **规则 14 日条款**：极端延迟发布时 resolve 逻辑与完整 7 日加总不同。
- **与 Bab el-Mandeb 周市场机制相似**：仅换 chokepoint 不算新策略；本条只写 Hormuz。
- **当前样本 <30 周**：历史回放统计力有限。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 对手方忽视 PortWatch 日累加与滞后；你用公开 `n_total` 约束档位。
2. **有免费数据能检验：满足** — ArcGIS 2019 起 + Gamma 结算档；**closed event 本次仅 24 个 <30**，需前向补足或标待选区。
3. **小资金能做：满足** — 300/档、800/event。
4. **不重复：满足** — 仓库内无 Hormuz/Portwatch 条目（2026-10-21 检索）；与 quant 地震/Netflix 等机制不同。
5. **扣成本后粗算够用：不确定** — 地缘费率为 0，但 09-28 周若曾在数据发布前买入 `<20` 理论上空间大；**未拉历史 ask，不能写扣价差后必为正**。
6. **两周内能检验：不确定** — 24 历史 + 2 前向周仍可能 <30 event；日更观测可 ≥14。
7. **出处可查：满足** — 下列 URL + 访问日期。

## 出处

- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-the-strait-of-hormuz-week-of-october-19 — 访问 2026-10-21 — 已读（规则、档位）
- https://gamma-api.polymarket.com/events?slug=how-many-ships-transit-the-strait-of-hormuz-week-of-september-28 — 访问 2026-10-21 — 已读（结算档 <20 YES）
- https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=portid%3D%27chokepoint6%27&outFields=date%2Cn_total&orderByFields=date%20DESC&resultRecordCount=5&f=json — 访问 2026-10-21 — 已读（2026-10-14–18 日计数）
- https://portwatch.imf.org/pages/data-and-methodology — 访问 2026-10-21 — 已读（更新节奏、AIS 局限）
