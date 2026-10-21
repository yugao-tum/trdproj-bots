---
id: composer-002
name_zh: 飓风季阶梯：按NHC已发生数重估
name_en: Atlantic hurricane ladder repriced off NHC running count
bot: composer
date: 2026-10-21
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many hurricanes will form during the Atlantic Hurricane Season in 2026?」档位 0 / 1-3 / 4-6 / 7+
venues: Polymarket
data: NHC 热带气旋摘要（免费 HTML）；Gamma event 规则与盘口；2025 季 NHC TCR 表作季节长度先验
test_2w: 独立结果按 event 计（单 event 4 档共享 1 个计数结果）；两周内每日拉 NHC 活跃系统 + Gamma 档位 ask/bid，记录「运行计数变化后 24h 内价格是否重定价」≥30 次观测（同一季内 NHC 更新/公告为独立观测）
status: 待核
confidence: 中
---

## 一句话

在大西洋飓风季进行中，每日读取 NHC 已分类为 hurricane（≥74 mph）的数量 H，用「剩余季节日数 + 历史同期条件分布」算各档 1-3 / 4-6 / 7+ 的下限概率；只在某档 ask 低于 `p_lo − 0.05` 且扣费后仍为正时买 YES，持有至 11 月 30 日 ET 后按 NHC 最终计数结算。

## 钱从哪里来

付钱给你的是**在 H 已经很大/很小之后仍按季初先验定价**的对手方。规则写明以 **NHC 初始飓风公告**为准，且季内可追加（见规则原文）。当 H=1 且已进入 10 月下旬（2026 市场上下文：仅 Isaias 一次飓风、Strong El Niño 抑制），「4-6」档仍可能有非零 ask（2026-10-21 Gamma：`4-6` ask≈0.039），若条件分布给 P(4+) 高于 3.9%+费用，则有钱赚；反之应买「1-3」或卖高价尾部（本策略只做 bounded YES 买入，不做裸卖）。

## 规则

**结算原文要点（Gamma，slug `how-many-hurricanes-will-form-during-the-atlantic-hurricane-season-in-2026-20260728201848339`，2026-10-21 已读）**：

- 窗口：market creation 至 **2026-11-30 11:59 PM ET**。
- 计数：大西洋 **hurricane**（≥74 mph，Saffir-Simpson Cat1+），以 NHC 公告为准；链接 https://www.nhc.noaa.gov/aboutsshws.php 。
- **可按首次 NHC 飓风公告结算，即使事后 best track 下调**（对「曾达 hurricane 即算」有利）。
- 若无 hurricane → resolve 「0」。
- 档位：0 / 1-3 / 4-6 / 7+（mutually exclusive event 内多 market）。

**交易规则（提案）**

1. 每日 UTC 12:00 拉 NHC `https://www.nhc.noaa.gov/` 活跃系统列表，统计当前季 hurricane 数 H（含已消散但季内曾达 hurricane 的，按 NHC 季累计表核对）。
2. 条件先验：用 1991–2020 气候态 + 当前 H 与剩余天数 d，查表或负二项近似 P(最终总数 = k | 当前 H, d)（实现：`notes/hurricane_conditional.py` 可复现；本条用 2025 NHC 季末 5 hurricanes / 13 named 作量级校验，**非正式回测**）。
3. 对档位集合 {1-3,4-6,7+} 映射到 k 区间，得 `p_lo`（取下界区间概率）。
4. 进场：若 `ask ≤ p_lo − 0.05`，限价买 YES；单档 ≤400 USDT，event 总计 ≤1,000 USDT。
5. 当 H 跨档（例如从 3→4），24h 内禁止追价，等待盘口重定价后再算（避免在 stale 单上吃单）。

## 证据

### 1）2026-10-21 盘口快照（Gamma）

| 档 | bestBid | bestAsk | outcomePrices 中点 |
|---|---:|---:|---:|
| 1-3 | 0.963 | 0.991 | ~0.977 |
| 4-6 | 0.004 | 0.039 | ~0.022 |
| 7+ | — | 0.001 | ~0.0005 |

市场隐含 **P(1-3)≈97.7%**，与 Polymarket 页面上下文「季内仅 1 次 hurricane（Isaias）」一致（**来源：Polymarket event 页面 Market Context，二手，未独立核对 NHC 全季表**）。

### 2）2025 季 NHC 官方计数（对照样本）

NHC 2025 北大西洋摘要（https://www.nhc.noaa.gov/data/tcr/index.php?season=2025 ，2026-10-21 已读）：**13 named / 5 hurricanes / 4 major**。说明在活跃年，H 可远高于 2026 当前水平；条件模型必须在 H 更新时跳变，否则静态挂单会亏。

来源自报 volume `73447` USDT（Gamma，**未核实**）。

## 数据

- NHC 飓风定义：`https://www.nhc.noaa.gov/aboutsshws.php`
- NHC 2025 季总结表：`https://www.nhc.noaa.gov/data/tcr/index.php?season=2025`
- Gamma：`https://gamma-api.polymarket.com/events?slug=how-many-hurricanes-will-form-during-the-atlantic-hurricane-season-in-2026-20260728201848339`
- 缺失：2026 季逐日 H(t) 机读 CSV（需从 NHC 公告人工或 HTML 解析）；历史 PM 同 event 各档盘口时间序列（需前向记录）

## 两周内怎么检验

- **独立观测**：每个 NHC 新飓风公告日 = 1 次事件；或对「每日 (H, ask) 快照」计 1 次观测。两周 ≈14 次每日快照，可合并同季多个 PM hurricane ladder event（若存在）至 30 次。
- **操作**：记录 H、各档 bid/ask、模型 `p_lo`；检验公告后 24h 价格是否向 `p_lo` 方向移动。
- **失败标准**：已成交 YES 中位毛利 ≤0；或公告后价格反向移动且持续 72h（说明模型或口径错）。

## 成本与容量

- 天气档 `rate=0.05`（Gamma 快照 `1-3` 档 `feeSchedule.rate=0`，`4-6` 档 rate=0——**以各 market 实取为准**；保守按 0.05 计）。
- 例：买 `4-6` YES@0.039 → 费用占比 `0.05×0.961≈4.8%` + 半价差 ~1.75¢ → 总 ~9% 占本金，需 `p_lo ≥ 0.14` 才够 `−0.05` 边际。
- 占款至 2026-11-30 + 争议，最长 ~40 天（自 10-21 起）。
- 容量：event volume ~73k USDT；单档深度有限，400 USDT 可能移动尾部档价格。

## 风险

- **El Niño 抑制 vs Late season 爆发**：条件分布尾部厚，7+ 虽 ask 低但非零。
- **「首次公告算 hurricane」**：短暂达标后 downgrade 仍可能算数——与 best track 研究不一致，必须以规则为准。
- **H 识别错误**：依赖 NHC 公开页面解析，公告延迟会导致 H 低估。
- **当前 edge 可能为负**：H=1 且市场已 98% 押 1-3 时，买 4-6 更像彩票；只有 `p_lo(4-6)` 明显高于 ask 才做。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清：满足** — 季中 H 已知后仍按季初定价的滞后/尾部错误。
2. **有免费数据能检验：满足** — NHC + Gamma；可前向记录价格。
3. **小资金能做：满足**。
4. **不重复：满足** — quant 有龙卷风/干旱/ERA5，无 NHC hurricane 阶梯条件重估。
5. **扣成本后粗算够用：不确定** — 2026-10-21 4-6 档 ask 3.9%，需条件模型；未在本条跑完整 HURDAT 回测，**不能声称正 EV**。
6. **两周内能检验：满足** — 每日快照 ≥14，加 NHC 更新事件可至 30 观测。
7. **出处可查：满足**。

## 出处

- https://www.nhc.noaa.gov/aboutsshws.php — 访问 2026-10-21 — 已读（74 mph hurricane 定义）
- https://www.nhc.noaa.gov/data/tcr/index.php?season=2025 — 访问 2026-10-21 — 已读（2025：5 hurricanes / 13 named）
- https://gamma-api.polymarket.com/events?slug=how-many-hurricanes-will-form-during-the-atlantic-hurricane-season-in-2026-20260728201848339 — 访问 2026-10-21 — 已读（规则、档位、feeSchedule、盘口）
- https://polymarket.com/event/how-many-hurricanes-will-form-during-the-atlantic-hurricane-season-in-2026-20260728201848339 — 访问 2026-10-21 — 二手（Market Context：2026 季 1 hurricane Isaias 叙述）
