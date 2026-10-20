---
id: quant-003
name_zh: 三币广度闸门时序动量
name_en: PAA-style breadth-gated spot momentum (BTC/ETH/SOL)
bot: quant
date: 2026-10-20
market: crypto
pm_category: -
kind: supplement
improves: T-T2-tsmom
category: T
return_type: direction
instruments: BTC, ETH, SOL 现货
venues: Binance 现货
data: Binance 公开日线（data.binance.vision，免密钥；本条用 2020-12-31～2026-10-13）
test_2w: 用 notes/xqt-migration/reproduce.py 重跑 4 个年度样本外折；独立结果按“广度不足转现金”的区段数；失败标准：0.30% 成本下拼接回撤不比单币 ETH 30 日时序动量小，或折年低于 8%
status: 草稿
confidence: 中
---

## 一句话

三个主流币里至少两个的 60 日收益为正才持有（持有其中为正的、等权，组合稀释到 30% 年化波动），否则全部现金；每 5 个交易日调仓。作为 T-T2-tsmom（时序动量）的补充证据，说明“广度”开关比单币时序动量回撤小得多。

## 钱从哪里来

趋势延续（同 T-T2-tsmom）；广度开关的作用是在多数币同时转弱时整体离场（思路来自 Keller 的 Protective Asset Allocation，记忆，未核实，本条不引用其数字）。

## 规则

- 动量 = 60 日收益；正动量币数 ≥2 才持有，否则现金；持有正动量币等权；按 60 日已实现波动把组合稀释到 30% 年化（不加杠杆，上限 1 倍）；lag-1；每 5 日调仓。

## 证据

自己算的回测（`bots/quant/notes/xqt-migration/reproduce.py`，`results.csv`，2026-10-20）。每边 0.30%：
- 广度闸门：4 折连乘 +202.9%，折年 34.0%，单折最差回撤 −19.1%，拼接回撤 −19.1%，平均仓位 0.29。
- 对照 ETH 30 日时序动量：+184.5%，折年 31.8%，拼接回撤 −45.3%。
- 对照 VM（T-T2-vm）：+237.2%，拼接回撤 −22.1%——广度闸门在收益上不如 VM，回撤略好。
- 这些规则是私有研究里挑选过的（同批还试过其他参数），存在挑选偏差；原项目结论 NOT READY。

## 数据

- https://data.binance.vision/?prefix=data/spot/monthly/klines/SOLUSDT/1d/ 等，免费免密钥。

## 两周内怎么检验

- 重跑脚本；按转现金区段计独立结果；失败标准见字段区。

## 成本与容量

- 0.10%→0.30% 成本时 4 折连乘从 +220.9% 降到 +202.9%；容量远超 5,000 USDT。

## 风险

- 和 VM 高度相似（都是三币趋势 + 波动稀释），对主项目的增量可能很小；样本外仅约 3.8 年。

## 改进了什么

不适用（kind: supplement）。

## 门槛自查

1. 机制说得清：满足 — 趋势 + 广度离场。
2. 有免费数据能检验：满足。
3. 小资金能做：满足。
4. 不重复：不确定 — 与 T-T2-vm、T-T2-rptrend 很近，所以只作补充并保留草稿。
5. 扣成本后粗算够用：满足（回测）— 0.30% 下折年 34.0%。
6. 两周内能检验：满足。
7. 出处可查：满足 — 自己算的、可复现。

## 出处

- bots/quant/notes/xqt-migration/README.md、reproduce.py、results.csv（本仓库，2026-10-20 运行）— 访问 2026-10-20 — 已读（自己算的）
- https://data.binance.vision/?prefix=data/spot/monthly/klines/SOLUSDT/1d/ — 访问 2026-10-20 — 已读（数据下载）
