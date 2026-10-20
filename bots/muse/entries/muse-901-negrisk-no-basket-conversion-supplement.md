> 作者：deepseek worker（muse）｜ 第 1 轮

---
id: muse-901
name_zh: NegRisk NO 转换费与实现证据
name_en: NegRisk NO-basket conversion: fee code and conversion evidence
bot: muse
date: 2026-10-20
market: polymarket
pm_category: politics
kind: supplement
improves: dot-006
category: A
return_type: convergence
instruments: "negRiskAugmented=false、3–8 个命名结果的互斥事件；买 1–m 个 NO，经 NegRiskAdapter 转成 (m−1) 份 collateral + 其余结果的 YES"
venues: Polymarket（global，Polygon）
data: "Gamma 事件/市场对象（negRisk、negRiskAugmented、outcomes、endDate、feeSchedule，免费免密钥）；CLOB 当前盘口（免费免密钥）；NegRiskAdapter 公开源码与 Polygon 地址；Polygon RPC 本轮全部超时，当前 feeBips 未读到；论文有 2,098 个 YES-side / 36 个 NO-side 转换 episode，非公开 L2"
test_2w: "只做 negRiskAugmented=false、3–8 个结果的完整事件；前向记录 12 个独立事件、≥30 个 conversion bundle（同一事件同一方向的多个 bundle 只按事件计主结果）；逐腿可成交 ask/bid、taker fee、转换 feeBips=0/50/100 三档、Polygon gas、非原子执行和退出成本全部计入；失败：事件级扣费净收益均值 ≤0，或可执行 bundle 覆盖 <80%，或任一转换后支付低于理论下界"
status: 待核
confidence: 中
---

## 一句话

在非 augmented 的 NegRisk 事件里，当买入一篮子 NO 的价格加上逐腿费、转换费和 gas 后，仍低于转换得到的 collateral 加其余 YES 的可卖回价值时，买入 NO、调用 adapter 转换、卖出或持有转换出的 YES；本条补充 `dot-006` 缺失的合约级费用代码和 converter-enabled 实证。

## 钱从哪里来

- **付款方是逐腿报价不一致的对手方**：同一事件的结果互斥且只有一个赢家，NO_A 可以转换成其余每个结果的 YES；如果 NO 篮子太便宜，或转换出的 YES 卖价太高，组合就有正的支付下界。
- **转换把“多腿持有到结算”变成“部分 collateral + YES”**：对 n 个结果买 m 个 NO，转换后得到 `(m−1)` 份 collateral（每份 $1）和 `(n−m)` 个其余结果的 YES（每个在对应结果获胜时支付 $1）。到期支付至少 `m−1`，最多 `m`；成本是 m 个 NO 的买价加费用。
- **不是平台补贴**：本条不依赖 LP 奖励、返佣或 holding reward；利润来自报价不一致。`dot-006` 已写出完整集/NO 子集/单 NO 转换的机制，本条只补充合约级费用与论文证据，不重复其“完整 YES 篮子”部分。
- **为什么持续**：NO 篮子通常跨多个订单簿，逐腿深度、转换调用、费用不确定性和结果集核验让多腿套利者稀少；论文观察到 converter-enabled 利润远大于 settlement-based basket formation，说明“转换”是主要实现通道。

## 规则

### 事件层（与 dot-006 相同的硬门槛）

1. Gamma 事件必须 `negRisk=true`、`negRiskAugmented=false`；所有腿属于同一 `negRiskMarketID`，是 winner-take-all 的完整互斥结果集。
2. 只做 3–8 个已命名结果；不碰 `Other`、placeholder、可新增结果的 augmented 事件。
3. 每个市场的 `endDate` 和结算源必须能解释为同一结算时点；事件结束日不能直接当所有腿的结算日。
4. 任一腿缺可成交 ask/bid、深度不足、规则有争议，或转换后得到的 YES 不可交易，则不开始新组合；已成交腿按最坏情况退出，不能假设整篮可撤销。

### 合约级转换公式（本条新增）

以 `NegRiskAdapter.convertPositions(marketId, indexSet, amount)` 为准：

- `m = indexSet` 中 NO 的个数；`n = questionCount`；`yesCount = n − m`。
- `feeAmount = amount × feeBips / 10_000`；`amountOut = amount − feeAmount`。
- 合约先 mint `yesCount × amount` 的 collateral，split 出 YES/NO，把调用者的 m 个 NO 和合约自己 split 出的 NO 都 burn 掉。
- 调用者收到：
  - collateral：`(m − 1) × amountOut`（仅当 `m > 1`）；
  - YES：对每个未被选为 NO 的结果，各 `amountOut` 份。
- 费用同时从 collateral 和每个 YES 输出中扣除：总费用 = `(n − 1) × feeAmount`，相对于输入的 `amount` 是 `(n−1) × feeBips/10_000`。**结果数越多，转换费对输入的放大越明显。**
- 单 NO 转换（m=1）没有 collateral 输出，只有 `n−1` 个 YES；此时总费用 = `(n−1) × feeAmount`，全部从 YES 中扣。

### 三条纸面路径

- **路径 A：买 m 个 NO 并持有到结算**。成本 `Σ ask_no_i + Σ fee_i + 缓冲`；到期至少 `m−1`。只要成本 < `m−1` 就有保证边际；不需要卖出 YES。
- **路径 B：买 m 个 NO，转换后按 bid 卖出全部 YES**。收入 `(m−1) + Σ bid_yes_j`；成本 `Σ ask_no_i + 转换费 + 卖出费 + gas + 缓冲`。要求收入 − 成本 > 0。
- **路径 C：买 1 个 NO_A，转换成其余所有 YES，按 bid 卖出**。收入 `Σ bid_yes_j`；成本 `ask_no_A + 转换费 + 卖出费 + gas + 缓冲`。这是论文中的 converter-enabled 方向，也是 NO-side 机会的主要实现方式。

- 单腿费用按 Polymarket `C × r × p × (1−p)` 逐腿计，p 用该腿实际成交价；买 NO 时用 NO 价格，不能拿 YES 价格代入。
- 转换费按 `feeBips` 计；当前 `feeBips` 未读到，必须做 0/50/100 三档敏感性（0%、0.5%、1%），不能假设为 0。
- gas 是整笔 USD，不是每份；Polygon gas 未实测，按实际链上 gas 计，并加失败重试预算。
- 执行顺序：先买 NO 腿，确认全部成交或按最坏情况退出，再调用转换；转换后如果卖 YES，逐腿按 bid 卖出，未卖出的 YES 持有到结算或按最坏情况折价。

## 证据

- **`dot-006` 已读**：它已写出完整 YES 篮子、互斥 NO 子集、单 NO 转换三条路径，并给出 Gamma 的 `negRisk=true`/`negRiskAugmented=true` 反例（128 个市场、含 Other）；本条不重复这些内容。
- **官方合约代码已读**：`NegRiskAdapter.sol` 的 `convertPositions` 明确 `feeAmount = (_amount * md.feeBips()) / FEE_DENOMINATOR`、`amountOut = _amount - feeAmount`；collateral 为 `multiplier * amountOut`（`multiplier = noPositionIds.length - 1`）；YES 每个为 `amountOut`；费用转给 `vault`。`FEE_DENOMINATOR=10_000`。这是本条相对 `dot-006` 的核心增量。
- **来源自报，未核实**：arXiv 2608.00666 重建约 $1.118M 机制相关利润，其中 converter-enabled 约 $1.086M（约 97%），settlement-based basket formation 约 $32,283；CLOB 样本中 YES-side 正向 episode 2,098 个、NO-side 仅 36 个；exact-duration 子样本 253 个 YES / 5 个 NO，中位持续 16.15 秒 / 7.99 秒；conversion bundle 与 CLOB 买入在 5 个 block（约 10 秒）内匹配；top-10 地址拿走约 75% converter 利润。
- 论文称 converter-enabled 利润在 NegRisk Adapter 于 2023-11-28 部署后，从 2024-01 开始出现；NO-side 违规更少、更短，方向上符合“转换通道在 NO 侧可用、YES 侧不可用”的机制解释。论文也承认 NO-side 样本极小，不能做强统计比较。
- 论文的 $1.086M 是作者从链上转换调用与 CLOB 成交匹配重建的，样本、方法和地址聚类都未独立复现；本条只把它当作“机制存在且曾被利用”的证据，不当作当前收益预测。
- 本次未取得当前 `feeBips`，也未取得当前可执行盘口（Polygon RPC 与 Gamma/CLOB 重取均超时）；因此没有“今天某事件费后为正”的实时例子，只有机制、代码和论文证据。

## 数据

- **Gamma**：`https://gamma-api.polymarket.com/events?slug=...`；取 `negRisk`、`negRiskAugmented`、`outcomes`、`endDate`、`feeSchedule`；免费免密钥。
- **CLOB**：`https://clob.polymarket.com/book?token_id=...`；取当前全深度盘口；免费免密钥；历史 L2 无免费源。
- **NegRiskAdapter**：Polygon `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296`；`negRiskCtfExchange` `0xC5d563A36AE78145C45a50134d48A1215220f80a`；`negRiskFeeModule` `0x78769D50Be1763ed1CA0D5E878D93f05aabff29e`；USDC `0x2791bca1f2de4661ed88a30c99a7a9449aa84174`。合约源码：`https://github.com/Polymarket/neg-risk-ctf-adapter`。
- **`feeBips` 查询**：`getFeeBips(bytes32)` selector `0x2582cb5e`；也可读 `MarketDataManager.feeBips()`。需要具体 `marketId`；本轮没有可用 RPC，未取。
- **Polygon RPC**：本轮 `polygon-rpc.com`、`polygon-bor-rpc.publicnode.com`、`polygon.drpc.org`、`1rpc.io/matic`、`rpc.ankr.com/polygon`、`polygon-mainnet.public.blastapi.io` 全部超时；部署前必须换可用 RPC 复核。
- **论文**：`https://arxiv.org/abs/2608.00666`；样本包含 32,702 个事件、259M 笔交易；没有公开的逐笔 L2 数据。
- **缺失**：当前 `feeBips`、当前可执行深度、Polygon gas、转换失败率、转换后 YES 的卖盘深度；这些都需要前向记录或链上查询补齐。

## 两周内怎么检验

- **事件筛选**：每天扫 Gamma 的 active neg-risk 事件，只保留 `negRiskAugmented=false`、3–8 个命名结果、所有腿 `endDate` 可对齐的事件；预计两周内可找到 12 个左右独立事件，实际不足则记 N。
- **bundle 记录**：每个事件每天记录 top 5 档的 NO asks、YES bids、feeSchedule、`feeBips`（若 RPC 可用）；对每条路径 A/B/C 按实际深度计算费后边际，单笔最多 $500，单事件最多 $1,000。
- **纸面执行**：NO 腿逐腿按 ask 成交，允许部分成交；转换费按 0/50/100 bps 三档分别记账；gas 按 Polygon 实际 gas 或 $0.05/笔的保守值；YES 卖出按 bid 逐腿成交；未卖出的 YES 按结算价盯市，不用中间价。
- **独立结果**：主结果按事件计（12 个事件），bundle 数（≥30）只作为观测数，不把同一事件的多个 bundle 当独立结果；同一事件的不同 NO 子集也合并为 1 个事件级结果。
- **失败标准**：事件级扣费净收益均值 ≤0；或可执行 bundle 覆盖 <80%；或任一转换后实际支付低于理论下界；或 `feeBips` 采用 100 bps 时全部路径转负且没有 0 bps 的可用证据；或最大回撤 >总资金 10%。
- **对照**：同一批事件上跑“只买完整 YES 篮子并持有”的 `dot-006` 路径，比较转换路径与完整集路径的费后收益；如果转换路径只在 `feeBips=0` 时为正，必须在条目中明确标注对费用的依赖。

## 成本与容量

- **费用公式**：单腿 taker `C×r×p×(1−p)`；politics 约 r=0.04，p=0.5 时费/名义 2%，p=0.9 时 0.4%，p=0.1 时 3.6%。转换费 `(n−1)×feeBips/10_000 × amount`；n=8、feeBips=100 时，转换费是输入 NO 金额的约 7%，足以吃掉大多数边际。
- **示例**：3 个结果、买 2 个 NO、每个 40¢，成本 80¢；转换后得 1 份 collateral + 1 个 YES；若 `feeBips=0`、YES bid 25¢，收入 1.25，毛利 45¢（未计逐腿费和 gas）；若 `feeBips=100`，转换费约 `2×1%×amount`（相对输入约 2%），收入降到约 1.23，仍为正但缓冲变薄。该例是纸面算术，不是当前盘口。
- **容量**：单事件最多 $1,000，单场所总未平仓 + 费用 + 退出缓冲 ≤$2,500；3–8 腿可以缩量，单腿深度未测。论文的 converter 利润集中在少数地址，说明容量存在但竞争激烈。
- **资金占用**：转换前买 NO、转换后卖 YES 的路径只占用数分钟到数小时；持有到结算的路径占用数天，按事件结算日计算年化，不能把单次 2% 直接乘 365。
- **粗略净收益**：若单次转换路径毛利 3–5%、逐腿费 1–2%、gas 和缓冲 0.5%，净 0.5–3.5%；只有 `feeBips=0` 或很低时才够用。`feeBips` 未知是本条最大的定量不确定性。

## 风险

- **`feeBips` 未知**：合约支持转换费，且费用按每个输出单位扣；如果当前费率非零，8 结果事件的转换费可能达到输入金额的 7%。在读到真实 `feeBips` 前，不能把“转换免费”当假设。
- **结果集不完整/Other**：`negRiskAugmented=true` 时买全命名 NO 不是完整集；Other 的定义会变化，转换可能得到不可交易的 placeholder YES。本条只做非 augmented。
- **非原子执行**：先买 NO 腿，部分成交会留下裸露的 NO；转换后卖 YES 也可能只成交一部分。已成交腿的退出成本和撤单延迟必须计入。
- **结算源/日期不一致**：同一事件的不同市场可能 `endDate` 不同；转换后的 YES 支付取决于对应结果，若结算延迟或争议，资金占用会拉长。
- **智能合约/链上风险**：adapter、fee module、USDC、Polygon 拥堵、RPC 故障、转换交易失败或重试；本条不提供私钥或交易代码。
- **论文外推风险**：2,098/36 个 episode 和 $1.086M 利润来自特定样本；NO-side 只有 36 个，统计上很弱；top-10 地址集中度高，说明竞争和地址聚类可能影响结果。
- **与 dot-006 重复的风险**：如果主审认为“转换费代码”只是实现细节、不构成关键证据，本条可能只算重复；因此本条把费用放大公式和 converter-enabled 实证作为核心增量，而不是重写完整集路径。

## 改进了什么

- `dot-006` 只写了“NO_A 可转换为其余每个结果的 YES”，没有给出 adapter 的精确费用公式、费用同时从 collateral 和 YES 扣除、以及 `(n−1)` 倍放大；本条补上合约级公式和 0/50/100 bps 敏感性。
- `dot-006` 的两周检验目标为 30 个独立事件，但 arXiv 的 NO-side exact-duration 样本只有 5 个；本条把主结果改为 12 个事件、30 个 bundle，避免用不可能达到的事件数硬凑。
- `dot-006` 没有 converter-enabled 的实证；本条补上 2,098 个 YES-side / 36 个 NO-side episode、16.15s/7.99s 中位持续、5 block 匹配和 97% 利润占比，作为“转换通道曾被实际利用”的证据。
- `dot-006` 把 `feeBips` 当成未取的 gas 级细节；本条把它提升为决定策略是否成立的核心变量，并给出查询 selector 和地址。

## 门槛自查

1. **机制说得清**：满足。买 NO 篮子→转换→collateral+YES 的支付关系、费用公式和三条路径均已写出；付款方是逐腿错价的对手方。
2. **有免费数据能检验**：部分满足。Gamma/CLOB/合约地址免费；当前 `feeBips` 和盘口因 RPC 超时未取；历史 L2 无免费源，只能前向记录。
3. **小资金能做**：满足（在可访问 Polymarket 的前提下）。单事件 ≤$1,000、总额 ≤$2,500，无杠杆；3–8 腿可缩量。
4. **不重复**：满足（作为 supplement）。`dot-006` 已覆盖机制；本条只交新增的合约费用公式、费用放大和 converter-enabled 实证，`improves: dot-006`。
5. **扣成本后粗算够用**：不确定。示例在 `feeBips=0` 时为正，在 100 bps 时可能转负；当前费率未读到，不能宣称费后一定为正。
6. **两周内能检验**：部分满足。12 个事件、30 个 bundle 的目标已写死；NO-side 机会频率可能不足，届时如实记 N，不把扫描次数当结果。
7. **出处可查**：满足。合约源码、官方负风险文档、arXiv 论文、Polygon 地址均有链接和访问日期；未取的 `feeBips`/盘口已明确标注。

## 出处

- https://github.com/Polymarket/neg-risk-ctf-adapter/blob/main/src/NegRiskAdapter.sol — 访问 2026-10-20 — 已读（`convertPositions`、`FEE_DENOMINATOR`、`feeAmount`、`amountOut`、collateral/YES 输出、fee 转 vault）
- https://docs.polymarket.com/concepts/negative-risk — 访问 2026-10-19 — 已读（NO→其余 YES 的转换关系、augmented 的 Other 警告；来自 `dot-006` 同日读取）
- https://arxiv.org/abs/2608.00666 — 访问 2026-10-20 — 已读（converter-enabled 利润、2,098/36 episode、16.15s/7.99s、5 block 匹配、top-10 75%；来源自报，未核实）
- https://github.com/Polymarket/neg-risk-ctf-adapter — 访问 2026-10-20 — 已读（仓库结构、部署地址引用；地址同时来自已保存的 `addresses.json`）
- https://polygonscan.com/address/0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296 — 访问 2026-10-20 — 摘要（adapter 地址；本轮 RPC 超时，未读取链上状态）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-20 — 已读（taker fee 公式、politics r≈0.04；来自同日已保存的官方正文）
