---
id: dot-006
name_zh: 负风险完整集与转换套利
name_en: Negative-risk complete-set conversion
bot: dot
date: 2026-10-19
market: polymarket
pm_category: politics
kind: supplement
improves: A-A5-poly-complete-set
category: A
return_type: convergence
instruments: "多结果互斥事件的完整 YES 篮子或互斥 NO 子集；示例为 2028 民主党总统提名事件（128 个市场，含 1 个 Other）"
venues: Polymarket
data: "Gamma API（事件 negRisk、negRiskAugmented、outcomes、feeSchedule、endDate，免费免密钥，含当前与历史元数据）；CLOB /book 与 /prices-history（当前盘口与有限历史，免费免密钥）；本轮未取得免费免密钥历史可成交 L2，计划于 2026-10-19 或获准后的实际启动日开始自录（尚未启动）；Polygon 转换 gas 未取。"
test_2w: "前向记录 negRiskAugmented=false 且 3–8 个结果的 neg-risk 事件，逐事件核完整集 YES 篮子、互斥 NO 子集和单 NO 转换的可成交 ask/bid、逐腿费用与深度；纸面执行按逐腿顺序下单，模拟部分成交、撤单延迟和已成交腿的紧急退出成本，不按原子篮子记账；以事件结算为 1 个独立结果，2 周目标 ≥30 个事件（实际不足则记 N）；失败标准为扣费/滑点/退出成本后净收益 ≤0，或可执行腿覆盖 <90%。"
status: 草稿
confidence: 中
---

本轮待核 0；status=草稿。

整理说明：本稿是已保存公开证据的操作员侧校订，没有新增抓取、成交或回测；所有采集方案仍为计划。

## 一句话

在负风险多结果事件中，只有当完整结果集的 YES 篮子含费总成本低于 1，或单个 NO 的买入价、入口费、转换 gas 与全部出口费合计低于其余 YES 的可卖回价值时，才按可成交价买入并持有到结算或转换后卖出。

## 钱从哪里来

同一事件的结果互斥且只有一个赢家。由支付关系可得到两条边界：买齐完整 n 个结果的 YES，结算固定支付 1；买任意互斥子集 S 的 NO，最多只有 1 个 NO 归零，结算至少支付 |S|−1。负风险文档进一步给出转换关系：1 份 NO_A 可转换为其余每个结果各 1 份 YES。

付钱给你的是逐腿报价不一致时的对手方：有人按单腿叙事交易，未把同一事件的互补关系算进去；多腿执行、链上转换、资金占用和结果集核验让跨腿套利者稀少。这个来源可能持续存在，但价差通常小于逐腿费用、gas 和滑点，因此本文只把它当作筛选规则，不宣称可盈利。

## 规则

### 事件层核验

1. Gamma 事件对象必须 `negRisk=true`；所有目标市场属于同一 `negRiskMarketID`，且是 winner-take-all 的互斥结果。
2. 只做 `negRiskAugmented=false` 的事件。`negRiskAugmented=true` 时存在命名结果、可新增结果和显式 Other；官方警告是只交易命名结果、忽略 placeholder，且 Other 的定义会变化。此时“买全命名 YES”不是完整集，sum<1 可以是正确价格。
3. 每个结果都必须已命名并在 UI 显示；不碰 `Person A` 一类占位。所有腿的 `endDate` 必须能解释为同一结算时点；先逐市场核，不能把事件结束日直接当作所有腿的结算日。
4. 执行不是原子的：逐腿下单可能部分成交。任一腿缺可成交 ask/bid、深度不足或结算源有争议时，不开始新篮子；已成交的腿必须在二级市场退出，承担额外 spread 和费用，不能假设整笔可撤销。仓位按“已成交腿全部退出”的最坏情况预留缓冲。

### 三条纸面筛选路径

A/B 以下按一套（每腿一份）报价，费用均用 USD/share；若做 Q 套，将价格与每份费用乘 Q。路径 C 直接按 Q 份总现金流计，gas 是整笔 USD，不能与未缩放的每份价格混减。转换本身的原子性不使前后盘口交易原子化。

- 路径 A，完整 YES 篮子：`sum(ask_yes_i) + 逐腿 taker fee + 滑点缓冲 < 1`。买入等份并持有到结算。只用 ask，不用 mid；只在完整、非 augmented 的结果集上做。
- 路径 B，互斥 NO 子集：`sum(ask_no_i) + 逐腿 fee + 缓冲 < |S|−1`。买入等份并持有到结算。该下界只依赖“至多一个结果赢”，不要求覆盖整个事件；但 S 内每个结果都必须真正互斥且可结算。
- 路径 C，单 NO 转换：`Q×ask_no_A + Q×f_in(ask_no_A) + gas + Q×Σ f_out(bid_yes_i) + 额外滑点USD + 缓冲USD < Q×Σ bid_yes_i`（f 为各腿每份费）。买 NO_A，转换为其余结果的 YES，再按可执行 bid 卖出；不卖则等价于持有 NO_A。入口费和每个出口费都必须计入，否则会把假边际当利润。只在完整、非 augmented 的事件上做，避免转换出 placeholder YES。

仓位：单场所全部未平仓头寸、入场费和紧急退出预留合计不超过 2,500 USDT；每事件也受该总额约束，等份买入，不加杠杆、不借款。退出：结算；或转换后按可执行 bid 卖出。费用后边际不足缓冲则放弃。

### 真实市场与规则源（Polymarket global）

- 示例事件：`democratic-presidential-nominee-2028`；市场 slug：`will-gavin-newsom-win-the-2028-democratic-presidential-nomination-568`、`will-alexandria-ocasio-cortez-win-the-2028-democratic-presidential-nomination-653`。
- 规则原文要点：若被点名者在 2028 年赢得并接受民主党总统提名，则 Yes；结算源为“consensus of official Democratic Party sources”；选举日前更换提名人不会改变市场结算。
- 时间日界：抽样的 Newsom、AOC 市场 `endDate=2028-11-08T04:59:00Z`；事件对象也是该值。事件内 128 个市场对象的 `endDate` 还出现 `2028-11-07T00:00:00Z`，两种值并存，必须逐市场核，不能把事件日期当成所有腿的结算日。API 用 UTC；若标题/规则写 ET，跨日/夏令时需人工核对；本事件规则文本未逐字给出时区，尚需核实真实结算日程，不能仅凭各市场 `endDate` 判定结算时点。
- 舍入：价格 tick 逐市场不同——该事件 128 个市场中 53 个为 0.001、75 个为 0.01；不能统一按 0.001 计算。费用舍入精度未由原研究 独立核验，不作为收益依据；费用公式见“成本与容量”。
- 缺测：转换 gas 与合约地址未取；当前 L2 深度未取；未取到符合“非 augmented 完整集”的正面真实例子；事件内 `Other` 之外的 placeholder 未逐市场列举；已读规则未给出缺数据/UMA 争议的专门回退条款。

## 证据

- 官方负风险文档已读：原文写明 “A No share in any market can be converted into 1 Yes share in every other market”；标准负风险要求创建时知道完整结果集；augmented 有 named/additional/explicit Other，且警告只交易 named outcomes、不要直接交易 Other。
- Gamma 事件对象已读：`democratic-presidential-nominee-2028` 为 `negRisk=true`、`negRiskAugmented=true`，128 个市场，含 1 个 `groupItemTitle=Other`；抽样的 128 行 `feeType=politics_fees`、`rate=0.04`、`rebateRate=0.25`。该例正好说明：命名结果不全，买全命名 YES 不是套利；本策略因此只做 `negRiskAugmented=false`。
- GitHub 检索：2026-10-19，query=`site:github.com polymarket negative risk conversion complete set arbitrage`，numResults=5，livecrawl=fallback，type=auto，contextMaxCharacters=6000；成功返回。摘要中出现 `Polymarket/neg-risk-ctf-adapter` PR #41（转换恒等式与反向 convertYESPositions）及 `mearley24/polymarket-edge-scanner` README（negRiskAugmented 的隐式 Other 使“买全命名 YES 捡便宜”不是套利）。仅读搜索摘要，未打开仓库正文；来源自报，未核实。
- 本研究 `backtest_count=0`；`observed_net_return=null`；Sharpe、最大回撤=未知。费用、规则、数据筛选不是完整盈利回测；没有可归属于本研究的费后盈利验证。

## 数据

- Gamma：`https://gamma-api.polymarket.com/events?slug=...` 与 `/markets?slug=...`，可取 negRisk 标志、outcomes、规则原文、feeSchedule、endDate；免费、免密钥。
- CLOB：`https://clob.polymarket.com/book?token_id=...` 取当前盘口；`/prices-history` 只有有限历史。本轮未取得免费免密钥历史可成交 L2，只能规划前向记录；2026-10-19 为拟定起点，尚未启动。
- 转换：官方文档指向 `/resources/contracts`；Polygon gas 需公共链浏览器数据。本轮未取，也未执行任何转换。
- 费用：逐市场 `feeSchedule`；上文的 0.04/0.25 是 2026-10-19 抓取值。若回测跨费率变更，必须按成交日重建，不能拿今日费率代替历史费率。

## 两周内怎么检验

前向记录计划起点为 2026-10-19 或获准后的实际启动日，尚未运行。每天至少扫描一次所有 active neg-risk 事件；对每个 `negRiskAugmented=false`、3–8 个结果的事件，记录全部腿的 top-of-book、深度、feeSchedule 和 endDate，计算路径 A/B/C 的费后边际。

纸面成交必须逐腿模拟：按可见深度部分成交，未成交部分设撤单延迟，已成交但篮子未完成的腿按当时可执行价紧急退出并计费；不得假设整篮原子成交，也不得把未成交腿当 0 成本消失。

独立结果按事件计：同一事件的多个结果、多个档、同一天同一 program 的多个市场只算 1 个；不同事件也需检查共同政治事件/结算源依赖，先按共同驱动聚类再计独立结果。2 周目标 30 个独立事件簇，但负风险事件出现频率未知，实际不足就如实记 N，不把“扫描次数”冒充结果数。

失败标准：各预注册路径分别统计，扣费、额外滑点、gas 和部分成交紧急退出成本后样本均值 ≤0；或有效独立事件簇 <30；或可执行腿覆盖 <90%；或发现 placeholder/结果集不完整；或转换无法执行。若 2 周内没有满足条件的完整集事件，这本身是有效结果（策略过窄），不补造样本。

## 成本与容量

总费用 F = `C × r × p × (1−p)` USD；每份费用 f = `r × p × (1−p)` USD/share（C 为份数，p 为实际成交价，r 为该市场费率）。F/(C×p) = `r×(1−p)` 是费/名义本金比例。ask/bid 已含 crossing，不重复加半价差；额外滑点只指报价之外的深度损失。

- politics `r=0.04` 单腿：p=0.50 时费/notional=2.0%；p=0.90 时=0.4%；p=0.10 时=3.6%。注意 `r×(1−p)` 在 p→1 时趋 0，在 p→0 时趋 r（4%），不是两端都下降。
- 路径 A 的整篮费用不能一概按 2%。均匀完整集（n 腿、Σp=1、p=1/n）的整篮费/资本 = `r×(1−1/n)`：r=0.04 时 n=3→2.67%，n=8→3.5%，n=2 才是 2.0%。这是 Σp=1 的费用基准；实际折价篮子仍须逐腿重算 USD 费用，再检验 1−Σask 是否足以覆盖，不能把近似比例直接当所有篮子的费用。
- 路径 B 同理，按每腿自己的 NO 成交价计 `r×(1−p_no)`；费用不是按 r 乘一次，而是逐腿累加。
- 路径 C 的总支出 = Q×买 NO_A 的价格 + Q×入口每份 taker fee + Polygon 转换 gas + Q×Σ各 YES 出口每份 taker fee + 额外退出滑点USD；gas 未测，无法给出正收益下界。
- 以上都是理想费后边界。多腿非原子执行还要加：部分成交腿的紧急退出价差/费、撤单延迟期间的价格变动、未成交腿的机会成本；纸面模拟必须逐腿记账，不能把整篮当一次成交。

容量：单场所含费及退出缓冲总上限 2,500 USDT；3–8 腿可以缩量设计，但单腿深度未测，未证实际可成交容量。128 市场示例只用于完整性反例，不作为可执行容量。月机会数未知；5,000 USDT 总资金中本策略最多占用 2,500（单场所上限）。

## 风险

- 结果集不完整或实际赢家是 Other/placeholder，导致 YES 篮子支付不足；这是最主要的假套利来源。
- 同一事件各市场 endDate 不一致；结算源“consensus of credible/official sources”存在解释空间；UMA 争议可能拖延。
- 转换合约调用失败、gas 飙升、转换出不可交易的 placeholder YES；本策略要求非 augmented 正是为规避此项。
- 单腿缺流动性、只成交一部分，形成裸露方向仓；已成交腿退出还要再付 spread/费，撤单延迟期间价格继续变动，费用可能吃掉全部边际。不能把“整笔放弃”当作已成交腿可自动撤销。
- 历史费率与当前费率不同；用今日 0.04 回测历史会高估或低估。
- 平台/合约/稳定币风险；本研究不执行交易，也不使用美国站规则替代 global 规则。

## 改进了什么

本条改按 `kind: supplement`，`improves: A-A5-poly-complete-set` 归类。分类依据是 [known 中的 A-A5-poly-complete-set](https://github.com/yugao-tum/trdproj-bots/blob/bc5dd79aa7da5e07cdd3ed2d22a158ab620222fb/known/KNOWN.md#L20)（2026-10-20 UTC 核对，仅含名称，不含既有规则或绩效）。互斥且穷尽结果全买/负风险转换，属于已知完整集套利。

本条提供的研究补充：整理完整 YES 篮子、互斥 NO 子集和负风险转换的支付恒等式、逐腿费用与非原子执行风险；历史可成交 L2、转换成本和独立结果仍缺。

补充材料相对既有实现的新增性与采纳价值仍待核；本次不主张新机制、已证改进、盈利或已采纳，状态保持草稿。

## 门槛自查

1. 机制说得清：满足 — 完整 YES 篮子支付 1、互斥 NO 子集支付至少 |S|−1、NO_A 转换其余 YES 的恒等式均已写出；付钱方是逐腿错价的对手方。
2. 有免费数据能检验：不确定 — Gamma/CLOB 可免密钥取当前规则和盘口，但本轮未取得免费免密钥历史可成交 L2；仅有拟定前向方案，尚未启动且未取得 30 个独立结果。
3. 小资金能做：不确定 — 3–8 腿事件可以按 2,500 USDT 含费总预算设计纸面规模，但真实深度、成交率和转换 gas 未测；128 腿示例不可执行。
4. 不重复：同机制补充，非新策略——对应 `A-A5-poly-complete-set`；补充材料的新增性与采纳价值仍待核，不据 dot 内部区别主张全局新颖性。
5. 扣成本后粗算够用：不确定 — 已给出逐腿费用公式和均匀 3–8 腿在 Σp=1 时 2.67%–3.5% 的费用基准，但没有费后成交回测；`observed_net_return=null`，不能称够用。
6. 两周内能检验：不确定 — 已列拟定前向起点、独立事件簇计数法和失败标准，尚未运行；30 个独立 neg-risk 事件在两周内是否出现未知，预计可能不足。
7. 出处可查：满足 — 官方文档、Gamma 事件与市场对象均由原研究 打开；URL、UTC 访问日期和位置在出处列明；GitHub 仅摘要且已标注。

## 出处

- https://docs.polymarket.com/concepts/negative-risk — 访问 2026-10-19 — 已读（原研究 打开；位置：How It Works、Augmented Negative Risk、Conversion Mechanics）。
- https://gamma-api.polymarket.com/events?slug=democratic-presidential-nominee-2028 — 访问 2026-10-19 — 已读（原研究 打开；位置：event negRiskAugmented、128 个 markets、Other、feeSchedule、endDate）。
- https://gamma-api.polymarket.com/markets?neg_risk=true&closed=false&limit=3 — 访问 2026-10-19 — 已读（原研究 打开；返回 Newsom/AOC 等市场对象、feeSchedule、endDate）。
- https://github.com/Polymarket/neg-risk-ctf-adapter/pull/41 — 访问 2026-10-19 — 摘要（GitHub 搜索摘要，未打开正文；来源自报，未核实）。
- https://github.com/mearley24/polymarket-edge-scanner/blob/main/README.md — 访问 2026-10-19 — 摘要（GitHub 搜索摘要，未打开正文；来源自报，未核实）。
- https://docs.polymarket.com/trading/fees — 访问记录 2026-10-19 — 二手（已保存的前轮官方正文审计；Fee Structure、Fee Precision；本次未重新抓取，无成交回执）。
