---
id: dot-007
name_zh: 阶梯单调性下界套利
name_en: Nested-threshold ladder monotonicity
bot: dot
date: 2026-10-19
market: polymarket
pm_category: crypto
kind: new
improves: -
category: A
return_type: convergence
instruments: "ETH 同到期嵌套 above 二元阶梯（Binance ETH/USDT 1h close）；当前示例为 16 档同到期市场"
venues: Polymarket
data: "Gamma API（事件/市场规则、strike、endDate、feeSchedule，免费免密钥）；CLOB /book（当前盘口，免费免密钥）；CLOB /prices-history（有限历史）；本轮未取得免费免密钥历史可成交 L2，前向自录仅为计划（拟定 2026-10-19 或获准后的实际启动日）；Binance ETH/USDT 1h K 线公开。"
test_2w: "前向记录 ETH/BTC 同到期嵌套 above 阶梯的 top-of-book，同到期阈值族先作为候选计数；同日多时刻/多币共享行情驱动须再聚类，2 周目标 ≥30 个独立事件簇（当前未证，不用 30 个时间戳冒充）；失败标准为扣费/滑点后中位净收益 ≤0，或可执行价差小于费用+1 tick 的样本占比 >90%。"
status: 草稿
confidence: 中
---

本轮待核 0；status=草稿。

整理说明：本稿是已保存公开证据的操作员侧校订，没有新增抓取、成交或回测；所有采集方案仍为计划。

## 一句话

同一标的、同一结算源、同一到期时刻的两个嵌套阈值 `L < H`，当实际 `ask_yes(L)+ask_no(H)` 加两腿费用和额外执行成本仍低于 1 时，纸面模拟买入低阈值 YES 和高阈值 NO；仅在两腿完整成交、规则完全匹配且正常结算的条件下，支付下界为 1；部分成交没有该保证。

## 钱从哪里来

嵌套阈值有硬性概率次序：`P(above H) ≤ P(above L)`。若市场把低阈值 YES 的卖价压到高阈值 YES 的买价之下，两个报价就互相矛盾。买 `YES(L)` 加 `NO(H)` 的支付真值表是：

- 结算价 ≤ L：低阈值 NO，高阈值 NO 支付 1 → 合计 1；
- L < 结算价 ≤ H：低阈值 YES 支付 1，高阈值 NO 支付 1 → 合计 2；
- 结算价 > H：低阈值 YES 支付 1，高阈值 NO → 合计 1。

因此合计支付至少 1。付钱给你的是报出陈旧单腿价格的做市商或方向交易者；薄盘、事件波动和逐档独立报价让这种交叉偶尔出现。它通常很小、很快消失，且要被两腿费用和滑点吃掉，所以这是筛选规则，不是已证盈利策略。

## 规则

### 标的与到期核验

1. 同一标的、同一结算源、同一到期时刻；只做规则原文明确写“1 小时 K 线收盘价高于 strike”的 `above` 市场。
2. 只用同一事件内、同一 `endDate` 的档位；不把不同时刻的 5AM/6AM/5PM 市场混成一对，也不把不同交易所的 BTC/ETH 报价混用。
3. 结算源为 Binance 对应现货对（示例为 ETH/USDT）的 1h K 线 Close；规则原文明确“not according to other exchanges or trading pairs”。
4. 原文用 “higher than”，等号归 NO；strike 的精度按源的小数位决定。到期时若 Binance 数据缺失或争议，已读规则没有专门回退条款（缺测）。

### 进场与仓位

- 对每一对 `L < H`：`cost = ask_yes(L) + ask_no(H)`；其中 `ask_no(H)` 必须取自 NO 盘口，只有同步互补订单簿映射及可成交深度已核时，才可按 `1 − bid_yes(H)` 计算，绝不能用 `1 − ask_yes(H)`（会把 spread 当成免费边缘）。
- 主触发条件：`cost + f_yes(L) + f_no(H) + 额外滑点缓冲 < 1`，f 是按实际两腿 ask 计算的每份费；仅在上述互补映射成立时，才等价于 YES ask/bid 形式。ask 已包含 crossing，不再扣半价差。
- 两腿等份纸面建仓；单场所全部头寸、两腿费用与紧急退出预留合计 ≤2,500 USDT，并限制到两腿可见深度。开仓前缺一腿则跳过；开始后可能部分成交，不能撤销已成交腿。逐腿模拟撤单延迟、已成交腿按实际 bid 紧急退出的额外价差与费用；无可执行 bid 时保留未平仓风险和最坏损失，不能记为成功套利。
- 退出：持有到到期结算；若到期前两腿价格收敛，也可按可执行 bid/ask 平仓，但必须把两腿费用算回去。
- 不做跨所（Polymarket vs Kalshi）配对；本文只用 Polymarket global 的规则和费率，不迁移美国站规则。

### 真实市场与规则源（Polymarket global）

- 示例事件：`ethereum-above-on-october-6-2026-6am-et`；同到期档位 slug 例：`ethereum-above-2790-on-october-6-2026-6am-et`、`ethereum-above-2780-on-october-6-2026-6am-et`、`ethereum-above-2770-on-october-6-2026-6am-et`。
- 该事件共 16 档，strike 从 2,630 到 2,790，2700→2720 缺 2,710；`negRisk=false`，不是互斥结果集，多个档可以同时为 YES。这正好说明本条与 C06 的完整集/转换是不同机制。
- 规则原文要点：“This market will resolve to Yes if the Close price for the ETH/USDT 1 hour candle that ends on the time and date specified in the title is higher than the price specified in the title. Otherwise ... No.”；结算源 Binance ETH/USDT 1h Close；“Price precision is determined by the number of decimal places in the source.”
- 时间日界：该事件 `endDate=2026-10-06T10:00:00Z`，对应标题的 6AM ET（2026-10-06 为 EDT，UTC−4）；冬令时后同一“6AM ET”会变成 11:00Z，不能固定套 10:00Z。所有档位的 `endDate` 相同；市场已 closed，`acceptingOrders=false`。
- 舍入：价格 tick 为 0.001；strike 以整数加逗号显示；费用精度为前轮官方 Fee Precision 审计记录的 5 位小数（本次未重新抓取、无实际扣费回执）。到期比较用 Binance 源精度，不用市场显示价。
- 缺测：已读 description 没有 Binance 缺数据/异常 K 线的回退条款；未取该事件的实际 Binance Close 数值；只抽样了一个已结算到期族，未取 30 个独立结果；本轮未取得免费免密钥历史可成交 L2。

## 证据

- EDGES #4 已读：该条把机制列为 Tier A，写法是 `ask_yes(Lower) < ask_yes(Upper)` 时买 Lower YES + Upper NO；并明确提醒“买 NO 付的是 `1 − yes_BID`，不是 `1 − yes_ASK`”，否则会制造假阳性。原文同时说真实违规“thin depth”“most ... <$50 cap at quoted prices and 5-7pp spreads”，样本期、样本数、费后收益均未给出。以上均为来源自报，未核实；该条原生例子是 Kalshi，本文只取机制，不迁移 Kalshi/美国站规则。
- Gamma 事件已读：`ethereum-above-on-october-6-2026-6am-et` 含 16 个同 `endDate` 市场，`feeType=crypto_fees_v2`、`rate=0.07`、`rebateRate=0.2`、`negRisk=false`；规则原文与结算源如上。
- 本研究 `backtest_count=0`；`observed_net_return=null`；Sharpe、最大回撤=未知。费用、规则、数据筛选不是完整盈利回测；未对历史阶梯做过成交回放。
- 自算例（非成交）：若 `ask_yes(L)=0.45`、`ask_no(H)=0.50`，成本 0.95；两腿费用约 `0.07×0.45×0.55 + 0.07×0.50×0.50 = 0.034825`，净约 0.0152/份（约 1.5 美分/1 美元支付），尚未扣滑点和深度。若两腿价格均接近 0.5，且毛折价只有 1 美分（成本 0.99），费用约 3.5 美分，扣费为负；该近中价算例费用量级约 3.5 美分；不能据此断言所有报价需要固定 5–7 美分，实际逐腿费用与额外执行成本须重算。

## 数据

- Gamma：`https://gamma-api.polymarket.com/events?slug=...` 取全部同到期市场、规则原文、endDate、feeSchedule；免费、免密钥。
- CLOB：`https://clob.polymarket.com/book?token_id=...` 取两腿当前盘口；`/prices-history` 只有有限历史，不能还原历史 L2。
- 结算源：Binance ETH/USDT 1h K 线公开；但本轮未打开 Binance 页面取具体 Close，只读了 Gamma 规则原文。
- 历史回测缺口：本轮未取得免费免密钥历史可成交 L2，只能规划前向记录（拟定 2026-10-19，尚未启动）；跨费率变更时须按成交日重建 feeSchedule，不能拿今日 0.07 代替历史费率。

## 两周内怎么检验

前向记录只是计划，拟定 2026-10-19 或获准后的实际启动日，尚未运行。每个同到期嵌套阶梯先记一个候选到期族，同族多档与重复 poll 不加数；同日 BTC/ETH 和多个时刻不能自动视为独立结果。主统计按共享行情冲击/结算源预注册聚类，至少按 UTC 日块合并同日多币多时刻，并检查跨日自相关；独立事件簇数量未知。

两周目标为 30 个独立事件簇。仅 ETH 6AM 族每天 1 个，两周至多 14 个候选到期族；增加同日时间戳或 BTC 只能增加观测，不能补足独立性。当前方案尚未展示满足 30 个独立结果的来源，不扩充市场数冒充达标。

每族记录：满足 `ask_yes(L) < bid_yes(H)` 的相邻对数量、可成交份额、两腿费用、1 tick 滑点后的净边际、是否两腿都成交。失败标准：扣费/滑点后中位净收益 ≤0；或可执行价差小于“费用+1 tick”的样本占比 >90%；或多数机会只有单腿成交。若有效独立事件簇不足 30，门槛失败并如实记 N，不用市场数或时间戳数冒充。纸面 P&L 必须包括部分成交、撤单延迟与紧急退出的额外成本。

## 成本与容量

总费用 F = `C×r×p×(1−p)` USD；每份费用 f = `r×p×(1−p)` USD/share；费用/名义本金 F/(C×p) = `r×(1−p)`。p 必须是该腿实际成交价；ask/bid 已含 crossing，额外滑点只指该报价之外的执行损失。

- crypto `r=0.07`：p=0.50 时费/notional=3.5%；p=0.10 时=6.3%；p=0.90 时=0.7%。
- 两腿都在 p≈0.5 时，费用约 3.5 美分/1 美元支付；再加每腿 1 tick（0.001）和 20% 费用缓冲，毛违规需约 4–5 美分才可能为正。
- EDGES #4 自报多数违规在报价上只有 <$50 容量、5–7pp spread；若属实，单次可放金额很小，2,500 USDT 上限远用不满。
- 月机会数未知；5,000 USDT 总资金中本策略最多占用 2,500（单场所上限），且实际受单腿深度限制。PM CLOB 交易本身不另收 gas；结算/赎回的链上路径未核，未计入成本。

## 风险

- 把 `1 − ask_yes(H)` 当成 NO 买价，会用满 spread 制造假机会；必须用 NO 盘口或 `1 − bid_yes(H)`。
- 单腿成交、另一腿被抢跑，留下方向仓；薄盘下这是主要亏钱场景。
- 若按 mid 筛选，应先改为两腿可成交 ask（一次计入各腿 crossing）；若已用 ask，不再加 EDGES 的 5–7pp spread。两腿费用、额外滑点及部分成交退出损失仍可能吃掉边际。EDGES 自报不能当作费后证据。
- 到期时点/时区错误：标题是 ET，API 是 UTC；夏令时切换会让 6AM ET 的 UTC 值变化。等号归 NO，strike 精度按 Binance 源，不能按显示价四舍五入。
- Binance 1h K 线异常、缺数据或结算争议；已读规则没有缺测回退条款。不同交易所/交易对不能替代。
- 市场可能在到期前关闭或停止接受订单；已结算事件不能提供当前盘口。
- 不把 Kalshi/美国站规则迁移到 global；本文的 PM 规则均来自 global Gamma 对象。

## 改进了什么

不适用（kind: new）。

## 门槛自查

1. 机制说得清：满足 — 三区域支付真值表证明合计至少 1；进场条件是 `ask_yes(L) < bid_yes(H)` 扣费后仍成立；EDGES #4 与 16 档同到期市场规则已读。
2. 有免费数据能检验：不确定 — Gamma/CLOB 可免密钥取当前盘口和规则，Binance 1h K 线公开；但本轮未取得免费免密钥历史可成交 L2，已结算事件只有结果，前向计划尚未启动，更未取得 30 个独立事件簇。
3. 小资金能做：不确定 — 可设计 2,500 USDT 含费预算上限的纸面方案，但 EDGES 自报单次 <$50 容量、5–7pp spread，实际可放金额和成交率未测。
4. 不重复：不确定 — 与 C06 的完整集/转换不同（本条是嵌套阈值单调性，negRisk=false）；但原研究 未读 known/ 全仓库，不能独立确认无重复。
5. 扣成本后粗算够用：不确定 — 已给出两腿接近 0.5 时约 3.5 美分/1 美元支付的费用量级和该近中价下 1 美分折价扣费为负的反例；没有费后成交回测，`observed_net_return=null`，不能称够用。
6. 两周内能检验：不确定 — 前向方案未运行；同日多币多时刻须聚类，跨日仍需检查相关性；仅 ETH 6AM 族两周最多 14 个候选族，当前没有满足 30 个独立结果的证据。
7. 出处可查：满足 — EDGES raw 与 Gamma 事件均由原研究 打开；EDGES 的深度/价差数字标来源自报、未核实；Kalshi 原生例子未迁移。

## 出处

- https://raw.githubusercontent.com/AKCodez/prediction-market-alpha-playbook/main/EDGES.md — 访问 2026-10-19 — 已读（原研究 打开；位置：EDGES #4 Cross-Market Monotonicity Violations、Gotcha、Evidence）。
- https://gamma-api.polymarket.com/events?slug=ethereum-above-on-october-6-2026-6am-et — 访问 2026-10-19 — 已读（原研究 打开；位置：16 个同 endDate 市场、strike、description、feeSchedule、negRisk=false）。
- https://docs.polymarket.com/trading/fees — 访问记录 2026-10-19 — 二手（前轮已保存官方正文审计；Fee Structure、Fee Precision；本次未重新抓取，无成交回执）。
