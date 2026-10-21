---
id: composer-006
name_zh: SpaceX十月发射：运行计数定档
name_en: SpaceX October launch ladder priced off running public tally
bot: composer
date: 2026-10-21
market: polymarket
pm_category: tech
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket「How many SpaceX launches in October 2026?」档位 &lt;14 / 14 / 15 / 16 / 17+
venues: Polymarket
data: spacex.com/launches（结算源）；Launch Library 2.0 公开 API（交叉核对，非结算）；Gamma 同系列月度已结算 event
test_2w: 独立结果按 event 计；2026-10 内每日核对运行计数 vs 档位 ask；失败标准：与 spacex.com 可见计数不一致或已成交 YES 中位毛利 ≤0
status: 待核
confidence: 中
---

## 一句话

在 2026 年 10 月内，每日用 **spacex.com/launches**（结算源）统计 **已成功** SpaceX 发射次数 N，加上已排期且未失败的任务上界，映射到 &lt;14 / 14–17+ 档；当 N+剩余排期 **不可能** 触及某高档而 ask 仍显著高于下界概率时，限价买 **&lt;14** 或卖高估尾部（本条仅写 bounded YES 买入）；月终持有至 UMA 按 spacex.com 结算。

## 钱从哪里来

付钱给你的是**未按运行计数更新 ladder** 的对手方。规则以 **spacex.com/launches** 为准（Gamma slug `how-many-spacex-launches-in-october-2026-20260928t160000000z`，2026-10-21 已读）。10 月 21 日盘口 **&lt;14** ask≈0.986，而公开跟踪器已记录 **8 次 Success**（10-01–10-20，见证据）；剩余 10 日要再堆至 ≥14 需极高频，尾部档 **14+** 可能被高估（**需逐日 ask 验证，不能写死正 EV**）。另：spacex.com 页在自动化 curl 下 HTML 极短（**可能需浏览器渲染**），存在 **结算源可读性** 风险，规则允许 11-07 前用 credible reporting 兜底。

## 规则

**结算要点（Gamma，2026-10-21）**：

- 窗口：**2026-10-01 00:00 ET – 10-31 23:59 ET**。
- 计数：**SpaceX 发射**（按 spacex.com/launches 列表；具体是否含 Starship/Heavy 以站点归类为准）。
- 数据源：**https://www.spacex.com/launches**；缺失/错误时可延至 **2026-11-07 ET** 更新，仍无则 **credible reporting 共识**。
- 档位：&lt;14 / 14 / 15 / 16 / 17+（mutually exclusive）。

**交易规则（提案）**

1. 每日 UTC 18:00 尝试读取 spacex.com 计数 N_official；若不可解析，用 Launch Library 2.0 **仅作告警**（不单独结算）。
2. 取 LL2 `status=Success` 且 `net` 落在 10 月窗口内的 SpaceX 任务数 N_ll2；若 |N_official − N_ll2|≥2，暂停下单。
3. 若 N_official + 已公布未来 Success 任务 ≤13 且 **14** 档 ask &gt; 0.15，考虑买 **&lt;14** YES（上限 400 USDT）。
4. 不在 spacex.com 未更新且距月底 &gt;7 天时赌 17+  unless ask 极低且 N 已≥17（极 unlikely）。

## 证据

### 1）2026-10-21 Gamma 盘口（来源自报，未核实）

| 档 | ask（约） |
|---|---:|
| &lt;14 | 0.986 |
| 14 | 0.197 |
| 15 | 0.231 |
| 16 | 0.200 |
| 17+ | 0.028 |

费率快照 **0**（`feeSchedule.rate=0`）。

### 2）Launch Library 2.0 交叉核对（**二手，非结算**）

查询 `net` 在 2026-10-01–10-31、`launch_service_provider=SpaceX`（2026-10-21 API）：

| 日期 (UTC) | 状态 | 任务名（缩写） |
|---|---|---|
| 2026-10-01 | Success | Crew-13 |
| 2026-10-01 | Success | Transporter 18 |
| 2026-10-02 | Success | NROL-97 (Falcon Heavy) |
| 2026-10-10 | Success | SDA Tranche 1 Transport |
| 2026-10-13 | Success | Starlink Group 15-25 |
| 2026-10-13 | Success | Dragon CRS-2 SpX-35 |
| 2026-10-16 | Success | USSF-481 |
| 2026-10-20 | Success | Bandwagon 5 |

**Success 计数 = 8**（截至 API 快照；含 1 次 Falcon Heavy）。另有 `Go` 状态排期（如 10-21 Starlink 15-15），**未计入 Success**。

API：`https://ll.thespacedevs.com/2.2.0/launch/?net__gte=2026-10-01T00:00:00Z&net__lte=2026-10-31T23:59:59Z&limit=100`

### 3）同系列月度已结算（Gamma，2026-10-21）

| 月 | 结算档（winning groupItemTitle） |
|---|---|
| 2026-09 | &lt;12 |
| 2026-08 | 13 |
| 2026-06 | 14+ |

说明月间差异大，**不能外推 10 月**；仅作频率量级。

### 4）运行计数续跟（T06b，2026-10-21 04:16 UTC）

- 脚本 `notes/spacex_oct_launches_fetch.py` → `notes/cache/spacex_oct2026_running.json`。
- LL2：**8× Launch Successful**，**3× Go for Launch**（10-21/24/28）；若剩余排期全成功，上界 **11**，仍 **&lt;14** 档上界。
- 推断：与 §2 一致，**&lt;14** 仍为主基线；14+ 档需 10 月下旬异常高频才可能（**未读 spacex.com 官方计数**）。

## 数据

- 结算：`https://www.spacex.com/launches`
- 交叉：`https://ll.thespacedevs.com/2.2.0/launch/`（免费，免密钥）
- Gamma：`https://gamma-api.polymarket.com/events?slug=how-many-spacex-launches-in-october-2026-20260928t160000000z`
- 缺失：**spacex.com 机器可读列表**（本次 curl 仅 ~3KB HTML，**未读到发射表**）

## 两周内怎么检验

- **独立结果**：本 event = 1（10 月整月）。
- **前向**：10-22 至 10-31 每日记录 N_ll2、N_official（若可读）、各档 bid/ask；检验 Success 后 **14+** ask 是否下修。
- **失败标准**：spacex.com 公布计数与 LL2 Success 差 ≥2 仍下单；或 &lt;14 成交后 N 路径显示 ≥14 仍可能。

## 成本与容量

- tech 板块 rate=0（快照）；主要成本为 **半价差**（&lt;14@0.98 时 ~1%）。
- 单笔 ≤400 USDT；占款至 10 月底 + 可能至 11-07 数据源宽限期。
- 容量：event volume 数万 USDT 级（Gamma 自报，**未核实**）。

## 风险

- **结算源不可爬**：只能人工或 credible reporting，策略难自动化。
- **Heavy/Starship 是否计入**：必须以 spacex.com 归类为准。
- **&lt;14 已 98¢**：上行空间有限，尾部 fade 容量小。
- **LL2 ≠ 结算**：仅辅助，不能作为唯一依据。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清：满足** — 运行计数 vs 滞后 ladder。
2. **有免费数据能检验：不确定** — LL2 免费；**spacex.com 可读性未验证**；30 个历史 **event** 未齐（月度 series 可补）。
3. **小资金能做：满足**。
4. **不重复：满足** — 仓库无 SpaceX 月度计数条目（2026-10-21 检索）。
5. **扣成本后粗算够用：不确定** — &lt;14 高价时边际薄；14+ fade 未拉历史 ask 序列。
6. **两周内能检验：满足** — 10 月剩余 ~10 天日更。
7. **出处可查：满足**。

## 出处

- https://gamma-api.polymarket.com/events?slug=how-many-spacex-launches-in-october-2026-20260928t160000000z — 访问 2026-10-21 — 已读
- https://ll.thespacedevs.com/2.2.0/launch/?net__gte=2026-10-01T00:00:00Z&net__lte=2026-10-31T23:59:59Z&limit=100 — 访问 2026-10-21 — 已读（8× Success SpaceX）
- https://www.spacex.com/launches — 访问 2026-10-21 — 摘要（HTML 极短，**未读到发射列表**）
