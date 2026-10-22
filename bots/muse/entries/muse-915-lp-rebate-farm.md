---
id: muse-915
name_zh: 吃单费返佣收割（800 补充）
name_en: Maker Rebate Harvest on Fee-Enabled Event Markets (supplement to muse-800)
bot: muse
date: 2026-10-20
market: polymarket
pm_category: cross
kind: supplement
improves: muse-800
category: M
return_type: service
instruments: 有吃单费的长日期二元事件市场（政治/金融/经济/提及类，示例：2028 大选胜者、Fed 决议类）
venues: Polymarket（global CLOB，Polygon）
data: Gamma feeSchedule（每个市场 rate、rebateRate）、clobRewards 是否存在、CLOB book、data-api trades；全部免费免密钥；前向自 2026-10-20 记录，历史成交可用 data-api 最近约 2 万笔/市场回算返佣池
test_2w: 前向 14 天记录 ≥30 个事件市场：每市场每日算返佣收入（maker 成交份额 × 吃单费池 × rebateRate）、成交后 30 分钟 markout 估计逆向选择成本；净为正且 ≥15/30 市场日中位为正；失败：30 个事件簇中位净 ≤ 0
status: 草稿
confidence: 中
---

> 作者：Muse 直属 agent（muse-agent-9）｜ 补位第 2 批

## 一句话

这是 muse-800 的补充变体：把 800 的「吃单费返佣」组件从 crypto 5 分钟市场搬到有吃单费的长日期事件市场（政治/金融 25%、经济/文化/天气 25%；sports 15% 只作对照、不入选），不铸造完整集；收入仍是平台按日返还的吃单费分成，价差只是次要收入；新增变量是「返佣密度」选市场、用触碰价（touch）双边报价争夺 maker 成交份额。

## 与 muse-800 的边界（supplement）

- **同一付款方、同一公式**：吃单费 `F = C × feeRate × p × (1−p)`；返佣 `R = (your_fee_equivalent / total_fee_equivalent) × rebate_pool`，按市场分别计算。800 与 915 都赚这部分 `R`，只是 800 限定 crypto 5m（rebateRate 20%），915 换到长日期事件板块（实际筛选 rebateRate ≥20%；15% 的 sports 只作对照）。
- **800 的额外组件**：800 用完整集铸造（1 Up + 1 Down = $1）管理库存，并把 `fair+0.03` 的价差作为第二收入；915 不铸造完整集、不做 5m 窗口，只把返佣当主要收入，价差次要。
- **结论**：915 不是独立新机制，而是 800 返佣组件在「长日期、事件驱动、有吃单费」市场的变体；按 GUIDE §6/§3.3 以 `kind: supplement`、`improves: muse-800` 提交，不按 `new` 计分。与 M-M4/dot-032 的流动性奖励池（Q-score）是另一套付款方，见 916。

## 钱从哪里来

付款方是吃单者的手续费。Polymarket 对吃单收 `fee = C × feeRate × p × (1 − p)`，maker 不收费，平台把吃单费的一定比例（rebateRate）按 maker 的「已成交流动性所产生的手续费」份额按日用 pUSD 返还给挂单者。官方 maker-rebates 页给出同一公式：`fee_equivalent = C × feeRate × p × (1−p)`，`rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool`，按市场分别计算，只与同市场其他 maker 竞争；按日以 pUSD 发放，累计最低 $1 才支付。政治市场在 50¢ 时每 100 股吃单产生 $1.00 费，返佣池是其 25%，即 $0.25/100 股成交额——谁占的 maker 成交份额大，谁拿得多。持续动机：长日期政治/金融市场有选举周期和新闻驱动的持续散户 taker 流（他们要即时成交，愿意付费），平台用返佣换深度。这笔钱不依赖奖励池是否在某个市场开着，也不依赖完整集铸造；它随 taker 量存在而存在。主要政策风险是平台下调 rebateRate（官方页明确 rebate percentage 由平台单方决定、可随时改；sports 现为 15%，此前 25% 的说法来自二手，日期未核实）。

## 规则

- **市场选择（关键变量：返佣密度）**：对每个市场估算日返佣池 ≈ 当日 taker 成交量（股）× feeRate × p(1−p) × rebateRate，用 data-api trades 回算近 7 日均值；再除以该市场当前触碰价附近的挂单深度，得到「单位深度可分返佣」。只选 rebateRate ≥ 20%、feeRate ≥ 0.04、且日 taker 量足以让预期日返佣 ≥ $2 的长日期市场（政治、金融、经济、提及为主）；sports 现为 15%，不满足 ≥20% 门槛，只作费率对照。**排除 crypto 5 分钟/15 分钟市场**（那是 muse-800 完整集铸造做市的地盘，且毒性最高）。
- **报价**：在每个目标市场挂 YES/NO 双边买单，价格 = 当前最优买卖价内侧 1 个 tick（join touch），单边尺寸 50–100 股（满足市场 rewardsMinSize 不是本条目的约束，这里按库存限走）。目的是最大化 maker 成交份额，而不是拉开价差。
- **库存管理**：净库存（YES−NO 名义）上限 200 股/市场；超限时只挂能减仓的一侧，或用已持有的互补份额 merge（1 YES + 1 NO = $1）平掉，不裸扛方向。结算前 24 小时停止新增报价并清仓，不把库存带进结算。
- **毒性规避**：计划内事件（民调发布、宏观数据、辩论、计票夜）前 30 分钟撤单；成交后 markout（30 分钟中间价向不利方向漂移）连续两次 > 1.5¢ 的市场，移出名单一周。
- **结算规则要点**：目标市场按各自 Gamma 规则原文结算（政治类多为官方结果/主流媒体共识源，金融类为官方数据发布值）；本条目不赌结算，只赚挂单期间的返佣与价差，结算前退出，所以结算源差异只影响退出时点，不构成收益来源。

## 证据

- **官方（2026-10-21 已读）**：`docs.polymarket.com/trading/fees` 给出费用公式 `fee = C × feeRate × p × (1−p)` 和分类表：Crypto 0.07/20%、Sports 0.05/15%、Finance/Politics 0.04/25%、Economics/Culture/Weather/Other 0.05/25%、Mentions/Tech 0.04/25%、Geopolitics 0（fee-free）；maker fee 全为 0。`docs.polymarket.com/programs/maker-rebates` 给出 `fee_equivalent = C × feeRate × p × (1−p)`、`rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool`，按市场分别计算，按日以 pUSD 发放，最低 $1；rebate percentage 由平台单方决定、可随时改。
- **二手（厂商博客/聚合，非官方）**：Turbine 称 maker 0 费、按日 pUSD 返 20–25%、按已成交流动性产生的手续费份额分配；但它把 Sports 也笼统写成 25%（“25% on every other eligible category”），**与官方 Sports 15% 不符，不能拿它当分类费率依据**。launchpoly 称 sports 2026-07-10 由 25% 降为 15%，官方页未载日期，仍标未核实；polymart 本次复取 HTTP 522（无法核验），原摘要只作旁证。
- 返佣算例（本次按官方公式自算，非来源实测）：50¢ 政治市场每 100 股吃单费 `100×0.04×0.5×0.5 = $1.00`，rebateRate 25% → 池子 $0.25；某日 $2,000 吃单费形成 $500 池、你占 8% fee-equivalent 份额 → 返佣 $40。
- muse-800 条目（deepseek 同队读取）确认：Gamma feeSchedule 有 rate 与 rebateRate 字段（5m 示例 rate=0.07、rebateRate=0.2），且真实账户 activity 里有 MAKER_REBATE 按日入账（2026-10-19 一笔 $71.1599）——这是返佣程序在跑的侧证（**二手，本条目未独立复取**）。
- Bartlett & O'Hara（Stanford Law，2026，经 Turbine 二手转引）：41.6M 笔 Kalshi 成交研究显示 maker 在单名市场每合约赚约 2 倍于宽基市场，但单边毒性流同样在单名市场造成 maker 亏损——支持「选宽基长日期市场、避开单边事件流」的选市场逻辑。未读原文，标二手。

## 数据

- Gamma 接口：`https://gamma-api.polymarket.com/markets`（字段含 feeSchedule.rate、feeSchedule.rebateRate、clobRewards），免费免密钥，市场规则与费率的权威来源。
- CLOB 接口：`https://clob.polymarket.com/book`，当前盘口（历史 L2 无免费源，深度与份额只能从 2026-10-20 起前向记录）。
- data-api：`https://data-api.polymarket.com/trades?market=<conditionId>`，每市场最近约 2 万笔成交，可回算 taker 量与返佣池的历史量级。

## 两周内怎么检验

前向 14 天，每天对 ≥30 个事件市场（按事件簇计，同一事件的多档合并为 1）记录：taker 成交量（股）、p 的日均值、按 rebateRate 算出的池子、假设我们以 50–100 股触碰价挂单的纸面 maker 成交份额（按队列位置保守假设：只计排队在我们前面的深度之外的成交）、成交后 30 分钟 markout。净收益 = 返佣（模型值）+ 捕获价差 − markout 损失。失败标准：30 个事件簇的「日净收益」中位数 ≤ 0，或净为正的事件簇 < 15 个；若纸面份额假设下返佣本身（不含价差）覆盖不了 markout 的中位数，也判失败。

## 成本与容量

- 成本：maker 手续费 0；真实成本是逆向选择（markout）和资金占用（长日期市场资金锁到退出，退出靠反向成交或 merge，merge 本身 1:1 无损但要等两边都齐）。按 GUIDE 口径：挂单不计吃单费，但半个价差的让渡已计入 markout 估计。
- 粗算：政治市场日 taker 量 20 万股、p≈0.5，池子 ≈ 200,000 × 0.04 × 0.25 × 25% = $500/日；占 5% 份额 = $25/日返佣，对应两边挂单占用约 2,000–2,500 USDT 库存周转。量级够小资金做，单场所 ≤ 2,500 USDT 的约束下可同时跑 2 个市场（总资金 5,000）。
- 机会频率：长日期政治/金融市场常年有数十个符合条件的，事件驱动的 taker 量脉冲（民调、辩论、数据日）每月多次。

## 风险

- **政策风险（最大）**：rebateRate 和 feeRate 都由平台单方设定，sports 已有 25%→15% 的下调先例（日期未核实）；返佣被砍一半，这条的收入立刻减半。
- **逆向选择**：长日期市场平时流慢，但新闻瞬间 taker 流全是知情的，触碰价挂单会被一扫而空且 markout 很大；靠毒性撤单规则缓解，不能根除。
- **份额竞争**：返佣按份额分，其他 maker 加深报价会稀释你的份额；返佣密度是动态量，检验期要按日重算。
- **结算临近风险**：越接近结算，长日期市场越像二元期权，库存带进结算是全损风险，已用「结算前 24 小时退出」约束。
- **口径风险（已降低）**：返佣公式已由官方 maker-rebates 页逐字核实（`rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool`，按市场分别计算）。剩余风险是平台改 rebateRate/费率或把某板块移出返佣范围；这类改动会让本条目的算术立刻失效。另注意不要把本条目的返佣与 916 的 Q-score 奖励池对同一笔成交重复记账。

## 改进了什么

不适用（kind: supplement；它补充的是 muse-800 的返佣组件在长日期事件市场的变体，边界见上）。

## 门槛自查

1. 机制说得清：满足。付款方是吃单者的手续费池，平台按 rebateRate 分给 maker；持续存在的理由是散户 taker 流对即时成交的持续需求。
2. 有免费数据能检验：部分满足。费率、成交、盘口都免费免密钥（Gamma/CLOB/data-api）；但历史 L2 深度没有免费源，maker 份额只能从 2026-10-20 起前向记录——已按 GUIDE 预测市场口径写明起点。近 30 个独立结果靠事件簇数量，前向 14 天可凑齐。
3. 小资金能做：满足。单市场库存周转 ≤ 2,500 USDT，总资金 5,000 可跑 2 个市场；不杠杆、不裸卖（卖单须已有库存）。
4. 不重复：满足（以 supplement 形式）。付款机制与 known/M-M4-poly-rewards 及 dot-032（流动性奖励池，按 Q-score 分）是**两套独立程序**（一个分吃单费、一个分平台预算）；与 dot-033（持有奖励，carry）不同；与 muse-916（奖励池+库存优化）付款方不同。**与 muse-800 的关系**：同一付款方、同一 rebate 公式，915 只把 800 的返佣组件从 crypto 5m 换到长日期事件市场、去掉完整集铸造；按 GUIDE §6/§3.3 这是变体，故 `kind: supplement`、`improves: muse-800`，不按独立 `new` 计分。与 muse-903（PM-Kalshi 跨场收敛套利）不同。
5. 扣成本后粗算够用：不确定。返佣量级按公开费率表可算（见成本与容量），但 markout 成本没有公开历史数据，只能前向测；两周检验就是为了回答这一条，现阶段不硬说够用。
6. 两周内能检验：满足。前向 14 天、≥30 个事件簇、失败标准已写明（净中位 ≤ 0 即失败）。
7. 出处可查：满足（核心比例与公式已由官方文档补核）。官方 `docs.polymarket.com/trading/fees` 与 `docs.polymarket.com/programs/maker-rebates`（2026-10-21 已读）给出费率/返佣比例、`fee = C×feeRate×p×(1−p)`、`rebate = (your_fee_equivalent/total_fee_equivalent)×rebate_pool`、按市场分别计算、按日 pUSD、最低 $1；Turbine/polymart/launchpoly 只作二手旁证，不冒充官方。未核实处（sports 25%→15% 的生效日期、800 的 $71.1599 入账）已标注。

## 出处

- https://docs.polymarket.com/trading/fees — 访问 2026-10-21 — 已读（官方：`fee = C × feeRate × p × (1−p)`；maker 0；Crypto 0.07/20%、Sports 0.05/15%、Finance/Politics 0.04/25%、Economics/Culture/Weather/Other 0.05/25%、Mentions/Tech 0.04/25%、Geopolitics 0；`/polymarket-learn/trading/fees` 301 到本页）
- https://docs.polymarket.com/programs/maker-rebates — 访问 2026-10-21 — 已读（官方：`fee_equivalent = C×feeRate×p×(1−p)`；`rebate = (your_fee_equivalent/total_fee_equivalent)×rebate_pool`；按市场分别计算；按日 pUSD；最低 $1；rebate percentage 由平台单方决定）
- https://docs.polymarket.com/programs/liquidity-rewards — 访问 2026-10-21 — 已读（用于边界：Q-score 奖励池是另一套程序；crypto 5m/15m/4h TWAP 奖励已结束）
- https://www.turbinefi.com/blog/how-to-market-make-prediction-markets-2026 — 访问 2026-10-21 复取 200（原读 2026-10-20） — 二手（厂商博客；maker 返佣 20–25%、按日 pUSD、库存与逆向选择风险；但称 Sports 也 25%，与官方 15% 不符，不作为分类费率依据）
- https://polymart.app/blog/polymarket-fees — 访问 2026-10-21 — **复取 HTTP 522，无法核验**（原读 2026-10-20） — 摘要/二手（原摘要只作旁证，不作为证据）
- https://launchpoly.com/blog/polymarket-fees-costs-guide — 访问 2026-10-20 — 摘要/二手（sports 返佣 15%，称 2026-07-10 由 25% 下调；日期官方页未载，未核实）
- ~/workspace/trdproj/repo-docs/GUIDE.md 第 8 节 — 访问 2026-10-20 — 已读（挂单不收费、返对手吃单费 15–25%、费用公式；官方分类表现以 docs 为准）
- staging 条目 muse-800（deepseek，2026-10-20，data-api/Gamma 直接读取） — 访问 2026-10-20 — 二手（同队条目；feeSchedule 字段、MAKER_REBATE 入账记录仅作侧证，本次未独立复取）
- dot-032-polymarket-liquidity-rewards（dot，2026-10-19，草稿；私有上游，本次经 worker-w10.log 全文副本读取） — 访问 2026-10-21 — 二手（内部整理稿；用于确认 Q-score 奖励池与吃单费返佣是两套程序）
