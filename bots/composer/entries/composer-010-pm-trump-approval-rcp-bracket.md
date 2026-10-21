---
id: composer-010
name_zh: 特朗普支持率：RCP定档收敛
name_en: Trump approval RCP ladder convergence before snapshot
bot: composer
date: 2026-10-21
market: polymarket
pm_category: politics
kind: new
improves: -
category: E
return_type: direction
instruments: Polymarket「Trump approval rating on <date>」2–5 点宽分档 ladder
venues: Polymarket
data: RealClearPolling 总统工作支持率页（免费）；Gamma 同系列已结算 event；**无**公开历史 RCP 逐日存档（回放需自 2026-10-21 起往前录）
test_2w: 独立结果 = 每个「on <date>」event 一次；已结算 **≥30**（本次 **48** 档结果）；前向：2026-10-23 等开放 event 在 resolution 前 24h 用 RCP 定档 vs 盘口；失败：定档 bracket 与结算 bracket 不一致率 >15% 或扣费后 YES 中位毛利 ≤0
status: 待核
confidence: 中
---

## 一句话

在 **resolution 日 17:00 ET 前**（规则以 Gamma 为准），读取与结算源相同的 **RealClearPolling RCP Average「Approve」一位小数**，映射到当日 ladder 的唯一档位；当该档 **YES ask 仍明显低于 1**（且与相邻档价差显示尾部仍被高估）时吃单买 YES，持有至 UMA 按 RCP 快照 resolve。

## 钱从哪里来

对手方把 **5–7 个互斥档** 当成近似独立彩票押注，在 **距快照仍有一两天** 时仍给 **远档 YES 非零 ask**（2026-10-23 开放 event 快照见证据）。RCP Average 在 resolution 前 **日内变动通常 ≤0.3 个百分点**（机制推断，**未做全样本时序回放**）；当 **现值已落在某档中点 ±0.25** 内，远档 YES 的期望价值应接近 0，近档 YES 应接近 1——若盘口仍分散，存在 **向结算源收敛** 的定价滞后（与 muse 的「结算时滞」泛化不同：本条 **数据源与 PM 规则完全一致**，只做 **RCP→档位** 的确定性映射）。

## 规则

**结算要点（Gamma，`trump-approval-rating-on-october-23`，2026-10-21 已读）**：

- 结算：**2026-10-23 17:00 ET** 的 RealClearPolling「President Trump Job Approval」表 **RCP Average 行 Approve 列**，**一位小数**。
- 数据源 URL：`https://www.realclearpolling.com/polls/approval/donald-trump/approval-rating`
- 17:00 ET 后修订不算；缺数可延至第三日；方法论变更不影响结算。
- 各 market 为 **互斥分档**（例：38.0–38.4、38.5–38.9、…、39.5+）；**恰在边界** 时按 Gamma 各档说明（通常 **较高档** 或 **≥ 档** 规则以该 event 子市场为准）。

**交易规则（提案）**

1. **定档**：在 **resolution 日 12:00–16:00 ET** 读 RCP Approve 值 `a`（一位小数）；找 **包含 `a` 的 open 档** `B`（若 `a` 恰在边界，按该档规则取上档或下档，与 UMA 先例一致）。
2. **进场**：`B` 的 YES **ask ≤ 0.88** 且 **扣 politics 吃单费**（rate=0.04，`fee = size×0.04×p×(1−p)`）后仍 **预期 ≥3¢/份**；可选：对 **与 [a−0.35, a+0.35] 无交集** 的档买 NO 若 ask 支持（单笔 ≤300 USDT）。
3. **禁做**：不赌 RCP ** methodology 变更**；不在 **重大民调发布前 30 分钟** 加仓（尾部波动放大）。
4. **出场**：持有至 resolve；不做 intraday  scalping（无公开历史盘口）。

## 证据

### 1）2026-10-23 开放 ladder YES ask（Gamma，2026-10-21）

| 档 | YES ask（约） |
|---|---:|
| <37.5 | 0.034 |
| 37.5–37.9 | 0.05 |
| 38.0–38.4 | 0.185 |
| 38.5–38.9 | 0.385 |
| 39.0–39.4 | 0.27 |
| 39.5+ | 0.07 |

（**来源自报，未核实** 是否含 spread；仅说明 **概率仍分散**。）

### 2）已结算同系列（`notes/trump_approval_resolved.json`，2026-10-21 脚本）

- **49** 个 closed slug 匹配 `trump-approval-rating-on-*`；**48** 条解析到 winning bracket。
- 档位宽度随 event 变化（例 2.0% 宽 `42.0–43.9%` 与 0.5% 宽 `38.0–38.4`）；**未**与同日 RCP 快照逐条对照（缺免费历史 RCP 时间序列）。

### 3）与 muse 区分

muse 有 FOMC **期货隐含概率**、泛化 **结算时滞** 草稿；本条为 **politics 板块 RCP 字面定档**，数据源写在 PM 规则内。

## 数据

- RCP：`https://www.realclearpolling.com/polls/approval/donald-trump/approval-rating`（**2026-10-21 curl 未稳定解析 HTML**，resolution 前需浏览器或人工读表）
- Gamma 示例：`https://gamma-api.polymarket.com/events?slug=trump-approval-rating-on-october-23`
- 已结算列表：脚本 `notes/trump_approval_resolved_fetch.py` → `notes/trump_approval_resolved.json`
- 历史 RCP **逐日 Approve**：**未查到** 免费、免密钥、可批量 API；两周回放需 **从 2026-10-21 起每日存档** 或 Wayback（**不确定**）

## 两周内怎么检验

- **独立结果**：每个「approval on date」event = 1；已有 **48** 个 closed 结算档（**计样本充足，但未绑 RCP 时序**）。
- **前向（必做）**：2026-10-23、后续 weekly 日期 event：在 10-23 **16:00 ET** 录 RCP `a`、各档 ask、映射 `B`；resolve 后对比。
- **失败**：前向 3 个连续 event 定档错误；或 YES 扣费后净利 ≤0。

## 成本与容量

- politics 吃单 rate **0.04**；p≈0.85 时 fee/share≈0.0051。
- 占款约 **2–7 天**（视 event）；每月约 **4–8** 个「on date」event（2026 搜索快照）。
- 单 event ≤600 USDT 符合 5,000 USDT 约束。

## 风险

- **RCP 日内跳变**：突发民调纳入平均，定档 bracket 切换。
- **档位刻度变更**：PM 换 event 边界（脚本需按 slug 读档）。
- **页面不可用**：规则允许延迟；流动性恶化。
- **与「at least ___」系列相关**：勿重复同一 `a` 暴露。

## 改进了什么

不适用。

## 门槛自查

1. 机制：满足 — 分散押档 vs 结算源确定性映射。
2. 数据：部分满足 — 结算源免费；**缺历史 RCP 序列**，48 closed 仅证 PM 频率。
3. 小资金：满足。
4. 不重复：composer 未交 politics；与 muse FOMC/时滞草稿机制不同。
5. 扣成本后：**不确定**（未做扣费回放）。
6. 两周检验：部分满足 — 48 closed + 前向 Oct 23；**RCP 存档**待补。
7. 出处：Gamma 规则已读；RCP 页 **2026-10-21 未稳定读表** 标不确定。

## 出处

- https://gamma-api.polymarket.com/events?slug=trump-approval-rating-on-october-23 — 2026-10-21 — 已读（规则全文）
- https://www.realclearpolling.com/polls/approval/donald-trump/approval-rating — 2026-10-21 — 摘要（curl 未解析 Approve 数值）
- https://gamma-api.polymarket.com/public-search?q=trump+approval+rating+on — 2026-10-21 — 已读（closed 系列枚举）
