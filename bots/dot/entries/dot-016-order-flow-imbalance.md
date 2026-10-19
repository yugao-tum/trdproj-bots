---
id: dot-016
name_zh: 订单流不平衡成本筛否决
name_en: Order-flow imbalance short-horizon signal (cost-screen rejected)
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: new
improves: -
category: S
return_type: direction
instruments: BTCUSDT 永续（Binance）、Coinbase BTC-USD L2（检验与对照数据）
venues: Binance, Coinbase, Hyperliquid（均为公开数据；本条结论是不建议实盘）
data: 免费免key：Tardis 回放仅每月 1 日（YYYY-MM-01）无需 key、Binance 公共行情主机 data-api.binance.vision（摘要级，未自开）、可自录 L2；月初日可覆盖的历史深度未核
test_2w: 用自编（须先过安全审查）固定实现，跨多个历史月份的 Tardis 月初日复算 q90 毛优势与费用比，先按日聚合并检查跨日相关性；30 个独立日簇未证；失败标准=日簇费后均值≤0或95%CI含0或100ms延迟情景均值≤0；基准往返15、压力30 USDT@2500；独立日簇不足30则G6未达标
status: 草稿
confidence: 中
---

整理说明：本稿是已保存公开证据的操作员侧校订，没有新增抓取、成交或回测；所有采集方案仍为计划。

## 一句话

两篇来源自报订单流不平衡（OFI）在各自 100ms–5s 设置下对 BTC 中间价方向有统计预测力，分别给出 0.085 bps 与 0.13–0.26 bps 的毛优势（样本/规则不同，未复现），低于本研究成本基准（往返 0.60%）及来源自用的 Binance VIP0 手续费口径；本条按成本筛否决（仅 G5 明确失败），其余门槛保留未知。

## 钱从哪里来

机制上，知情订单流先于价格移动，提前接住它的做市商/流动性提供者赚这笔信息差；吃单者付价差和手续费。但公开证据显示：在本条规则与成本口径下未找到可归属给吃单者的费后正期望（G5 失败）——Rubin-S README 自述“neither a taker nor a maker breaks even”（**来源自报，未复现**）；Ronak-Mahajan README 在单日测量中吃单列全负，被动挂单列只在“两边都成交且无逆向选择”的假设下才为正（**来源自报，未复现；单日负不等于总体信号失效**）。不能据此推断机制整体无付款方。

## 规则

（本条为否决策略检验方案，不是实盘方案）
- 信号：多级 OFI（CKS 式）与状态变量（queue imbalance、microprice−mid、近端 ΔP）；在 |forecast| 超过训练期 q90 时按预测方向吃单持有 1 秒；只用决策时点之前的数据。
- 数据：Tardis 免key月初日（binance-futures incremental_book_L2 + trades，BTCUSDT），自录补日。
- 成本：基准 0.30%/边 = 往返 0.60%（15 USDT@2500）；压力 0.60%/边 = 往返 1.20%（30 USDT@2500）。对照：Binance USDⓈ-M VIP 0 手续费 0.02%/0.05% 每边（来源 README 记 2026-10-18 核对）= 往返 4/10 bps，另加价差。
- 仓位：≤2500 USDT/场所、总 5000、无杠杆（用于检验上限，不是建仓建议）。
- 失败标准统一为预注册的样本外总体均值与置信区间：日簇加权费后均值≤0，或日簇 bootstrap 的 95% 区间包含 0，或预注册 100ms 延迟情景下总体费后均值≤0，任一即筛否；不是任一笔/任一天亏损就否决总体信号。覆盖不足 30 个独立日簇则 G6 未达标，不能宣称显著性通过。

## 证据

- Rubin-S/order-flow-imbalance README（原研究已读，2026-10-19）：预注册 2026-10-18，dev=2026-04~07、holdout=2026-08~10（每月 1 日 00:00–02:00 UTC，共 7 日，BTCUSDT 永续）。Holdout Q5 毛优势 0.085 bps/笔 [95% CI 0.058,0.112]，820 笔；仅覆盖 4 bps maker 往返费的 2.1%。README 明言 make/take 均不 break even；100ms 延迟令 dev R² 从 0.84% 掉到 0.45%。**来源自报，未复现**（含预注册/冻结代码与单次 holdout 运行，但原研究未运行代码）。
- Ronak-Mahajan/crypto-microstructure README（原研究已读，2026-10-19）：Coinbase BTC-USD 2026-09-01，43,743,612 条消息、86,379 根 1 秒 bar；1 秒 horizon OOS R²=0.0081 [0.0046,0.0117]；预测最强十分位实现 0.13–0.26 bps 中价移动，而最便宜的吃单场景约 7 bps（Hyperliquid 两笔 3.5 bps taker + 价差），take 列全部为负；零 maker 被动列 +0.25~+0.39 bps 但假设双边无逆向选择成交。**来源自报，未复现**。
- lukeyin08/order-flow-imbalance（**摘要**，GitHub 检索结果，未打开正文）：合成/可复现实验，预测移动 0.09 tick vs 往返成本 2.48 tick（约 29 倍），成本感知吃单者 0 交易。
- 原研究成本算术：2500×0.085/10000=0.02125 USDT/笔毛额；基准往返 0.60%=15 USDT → 净约 −14.97875；压力往返 1.20%=30 USDT → 净约 −29.97875。**更多交易不能摊薄每一笔重复发生的费用**（费用与曝光同比例重复，不是固定摊销项）。
- 判定标准：来源报告 pooled holdout 均值/95% CI；本研究拟用上文日簇总体均值/CI 判据，尚未运行。单一交易日的负结果不构成对整信号总体的否定。**不执行来源代码**；如需复算只可自编、先过安全审查的实现。
- 收益/Sharpe/最大回撤：未测（未知）；backtest_count=0（原研究未运行任何回测）。

## 数据

- Tardis 免key数据：只有每月 1 日（YYYY-MM-01）可拉；loader 对其他日期直接拒绝（Ronak README 已读所述）。端点 GET https://api.tardis.dev/v1/data-feeds/coinbase 。
- Binance 公共行情主机 data-api.binance.vision：免key（**摘要**，来自 GitHub 检索结果，原研究未开）；是否有覆盖 12 个月的完整 L2 增量历史：未验证。
- 自录 L2 仅为计划：若获准，可自编并审查 Coinbase level2 / Hyperliquid l2Book（非全深度）采集实现；不执行来源 record.py 或其他抓取代码，本次未启动。
- 缺口：免key、连续 ≥12 个月的完整 L2 增量流未证实可得；这正是 G2 不确定的原因。

## 两周内怎么检验

固定自编（先过安全审查、非来源代码）实现，跨多个历史月份拉 Tardis 月初日（免key仅限每月 1 日，能回溯多少个月未核）复算 q90 毛优势、Binance VIP0 费后值与 0.60%/1.20% 费后值；同一日内多桶/多笔先合并，跨日相关性需检查，不能自动视为 30 个独立日；按上文冻结的日簇均值/95% CI 和 100ms 压力判据筛选。名义额 2500 时基准成本 15、压力 30 USDT，不足独立日簇则如实报告缺口。**本轮不执行任何脚本。**

## 成本与容量

- 每笔：基准往返 0.60%=15 USDT@2500；压力 0.60%/边=往返 1.20%=30 USDT@2500；毛优势 0.02125 USDT/笔 → 净约 −14.98（基准）/−29.98（压力）USDT/笔。
- 单笔容量：没有本研究可成交深度或延迟下成交记录，不能宣称可容纳数千 USDT。2,500 只是单场所预算上限，真实可放金额未知。
- 一个月有效机会次数未知；bar 数或同日交易笔数不是独立结果数，重复交易也不能摊薄逐笔费用。
- 总 5,000 USDT、单场所含费用和损失预留 ≤2,500 的纸面规模可以设计，真实容量和资金占用未核；不能把预算可写成执行已证。

## 风险

- 执行延迟：来源自报 dev R² 在 100ms 延迟下从 0.84% 降到 0.45%，未独立复现，也不代表所有网络/信号都损失一半。
- 逆向选择：被动成交恰好发生在价格穿过挂单时（README 明示无 fill model）。
- 统计风险：7 日、1 资产、每日仅 2 小时窗口；Aug 1 安静日导致 per-day R² 为负；多重比较未校正。
- 数据风险：L2 重建错误、reset/资金费时段的处理；不同数据源（Tardis/Binance vision）口径差异。
- 把“来源自报”当已复现是最大误用风险。

## 改进了什么

不适用（kind: new）。

## 门槛自查

1. 机制说得清：**不确定**。机制与状态变量可描述；在本条成本口径下未找到费后可归属的付款方，但这只否掉本条规则的 G5，不足以宣告机制本身失败。
2. 有免费数据能检验：**不确定**。Tardis 月初日、Binance 公共行情、自录均可免key；是否达到“连续 ≥12 个月”所需覆盖未核（免key仅每月首日，历史回溯深度未验证）。
3. 小资金能做：**不确定**。可按 ≤2500/场所含费预算设纸面规模；真实深度、执行延迟与竞争下的可成交性未证，不能因成本筛否定 G3。
4. 不重复：**不确定**。本轮限制下未检索 known/ 与其他 bots 索引，仅保留已有 C16 认领，不新增机制计数。
5. 扣成本后粗算够用：**不满足**。2500×0.085/10000=0.02125 USDT 毛额 vs 基准往返 15 USDT（0.60%）、压力往返 30 USDT（1.20%）→ 净约 −14.98 / −29.98 USDT/笔；即使用 Binance VIP0 的 4 bps maker 口径，优势也只覆盖 2.1%；重复交易不能摊薄重复费用。
6. 两周内能检验：**不确定**。免key样本可跨多个历史月份的每月首日拉取（覆盖未核），但两周内能否在“按日计独立”口径下取得 30 个独立结果未证。
7. 出处可查：**满足**。两个一手 GitHub README 原研究已读并给定位；性能数字均为来源自报、未复现，已逐条标注。

## 出处

- https://raw.githubusercontent.com/Rubin-S/order-flow-imbalance/main/README.md — 访问 2026-10-19 — 已读（pre-registration/Results/Q5/Limitations 节）
- https://raw.githubusercontent.com/Ronak-Mahajan/crypto-microstructure/main/README.md — 访问 2026-10-19 — 已读（The measured day/Data/Tardis free days 节）
- https://github.com/lukeyin08/order-flow-imbalance — 访问 2026-10-19 — 摘要（GitHub 检索结果，未打开正文）
- GitHub 检索 “order flow imbalance crypto trading signal”（2026-10-19）— 摘要级；amritsinha06072022 的 data-api.binance.vision 免 key 说明未打开正文，不作为完整历史 L2 可得性证据
