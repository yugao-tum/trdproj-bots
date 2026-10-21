---
id: composer-011
name_zh: PM CLOB奖励池双边做市前向
name_en: Polymarket CLOB liquidity rewards market making (forward)
bot: composer
date: 2026-10-21
market: polymarket
pm_category: cross
kind: supplement
improves: M-M4-poly-rewards
category: M
return_type: service
instruments: Gamma 每日 rewardsDailyRate>0 的 politics/crypto/finance 市场（前 3 名）
venues: Polymarket
data: Gamma markets API、CLOB book、data-api trades（均免密钥）；前向自 2026-10-21 起纸面记录
test_2w: 前向 14 天见 forward/composer-011/PLAN.md；独立结果=distinct conditionId 完成报价日且结算/结束；失败见 PLAN
status: 草稿
confidence: 中
evidence: 无
result: 未测
slot: "-"
variants: 1
variants_ext: 不清楚
window: "-"
max_dd: "-"
contribution: 不清楚
---

> 作者：composer（Composer 2.5）；前向登记 **2026-10-21** 推送 `forward/composer-011/PLAN.md` 后执行。

## 一句话

在 Polymarket 上对 **CLOB 流动性奖励池** 市场（Gamma `clobRewards.rewardsDailyRate>0`）**双边挂单**，纸面记录 14 天，赚 **奖励 + maker 返佣 + spread**，库存中性、不押方向。

## 钱从哪里来

- **流动性奖励池**：Polymarket 对满足 **min size / max spread** 的挂单给 **USDC 日奖励**（Gamma 可见 `rewardsDailyRate`）。
- **Maker 返佣**：对手 taker 费的 **15–25%**（PLAN 按 **20%** 保守）。
- **Spread**：被动成交价差（若被 taker 打到）。

## 规则

详见 **`forward/composer-011/PLAN.md`**（登记后不改）。要点：每日 06:00 UTC 按奖励率选 top3 market；Yes token 双边挂价在 `rewardsMaxSpread` 内；size≥max(minSize,200) 且 ≤400；data-api 悲观成交判定。

## 证据

- 前向进行中；登记前无实测。`evidence` 在 `RESULT.md` 完成后改为 `前向`。

## 数据

- Gamma：`https://gamma-api.polymarket.com/markets`
- CLOB book：`https://clob.polymarket.com/book?token_id=...`
- Trades：`https://data-api.polymarket.com/trades?market=<conditionId>`
- 官方费用与奖励说明（2026-10）：`https://docs.polymarket.com/`（挂单返佣与 liquidity rewards 章节，**摘要**）

## 两周内怎么检验

- 执行 PLAN 14 天；`ledger.csv` + `RESULT.md`。
- **独立结果** ≥30；扣成本净 PnL 为正为通过快速筛选候选。

## 成本与容量

- 单笔按 GUIDE §8 吃单费公式；挂单 0 费 + 返佣；spread 半宽。
- 单 market ≤约 400 USDT/边；三 market 合计 ≤5,000 USDT。
- **年化贡献**：前向结束后按「净 PnL ÷ 5,000 ÷ 天数 × 365」写入 `contribution`（登记时 **不清楚**）。

## 风险

- 奖励池规则/公式变更；inventory 在结算前单边暴露；薄 spread 市场假成交；API 与真实排队位置差异。

## 改进了什么

不适用（`kind: supplement`）。相对 known **M-M4-poly-rewards**：补 **可核对的前向 PLAN**（价位、成交悲观假设、Gamma 字段选市）+ 14 天 paper ledger，供 NEEDS #1。

## 门槛自查

1. 机制说得清：**满足** — 奖励池 + 返佣 + spread。
2. 有免费数据能检验：**满足** — 前向 + 公开 API。
3. 小资金能做：**满足** — ≤5k USDT 纸面。
4. 不重复：**满足** — supplement M-M4；与 dot/muse 条目为同族变体/补充，本前向独立登记。
5. 扣成本后粗算够用：**不确定** — 待前向。
6. 两周内能检验：**满足** — PLAN 14 天。
7. 出处可查：**满足** — Gamma/CLOB/docs 链接见上。

## 出处

- https://docs.polymarket.com/ — 访问 2026-10-21 — 摘要（费用与 maker 返佣）
- https://gamma-api.polymarket.com/markets — 访问 2026-10-21 — 已读（`clobRewards` 字段）
- https://github.com/yugao-tum/trdproj-bots/blob/main/NEEDS.md — 访问 2026-10-21 — 已读（#1 前向需求）
