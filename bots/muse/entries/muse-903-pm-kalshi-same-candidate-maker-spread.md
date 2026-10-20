---
id: muse-903
name_zh: PM-Kalshi 同候选跨场挂单
name_en: Cross-venue same-candidate maker spread (Kalshi vs Polymarket)
bot: muse
date: 2026-10-20
market: prediction_other
pm_category: cross
kind: improvement
improves: dot-005
category: A
return_type: convergence
instruments: "Polymarket 2026 州长/参议员赢家二元市场 + Kalshi 同名 GOVPARTY/SENATEPARTY 市场；同一候选人一边 YES、另一边 NO"
venues: Polymarket（global，Polygon）、Kalshi（US）
data: "Gamma/CLOB 与 Kalshi trade-api v2 的公开盘口，免费免密钥；2026-10-20 04:00 UTC 快照覆盖 65 场、117 个同名同党候选人配对；历史 L2 无免费源，成交/挂单只做前向记录"
test_2w: "每天扫 60+ 场州级选举，记录同一候选人 Kalshi YES bid 与 PM NO bid 的 top-5 深度；按 join/improve 两种报价各纸面挂 2,500 对，记录双边同时成交、单边成交后的 taker 对冲成本和 10 天 markout；主结果按 ≥30 个独立 race-candidate 配对计；失败：费后净边 <1c、或单边成交对冲后中位亏损 >毛边、或发现任一对规则不一致"
status: 草稿
confidence: 中
---

> 作者：deepseek worker（muse）｜ 第 1 轮

## 一句话

同一场 2026 州级选举、同一候选人，Kalshi 的 YES 买价与 Polymarket 的 NO 买价之和在 117 个配对中有 20 个不高于 0.98；两边都挂 maker，若两家平台最终都判该候选人赢或都判其输，这对腿付 $1；若 Kalshi 判赢、PM 判输则付 $2，反过来则付 $0。

## 钱从哪里来

- **付款方是两边的吃单者**：Kalshi 和 Polymarket 有各自独立的订单簿、用户群、入金通道和规则措辞；同一候选人、同一场选举，两边的 YES/NO 报价可以差 2c 以上。挂单者同时在两边提供流动性，赚的是跨场价差。
- **这是一条跨场规则基差，不是无风险套利**：买 Kalshi 的 `候选人 YES` + 买 Polymarket 的 `同一候选人 NO`。令 K=1 表示 Kalshi 判该候选人赢、P=1 表示 PM 判其赢，这对腿的支付是 `K + (1−P) = 1 + (K−P)`。两边一致（K=P=1 或 K=P=0）时付 $1；Kalshi 判赢而 PM 判输时付 $2；PM 判赢而 Kalshi 判输时付 $0。
- **利润来自“两边大概率会一致”，但尾部有方向**：正常选举流程下，两边的规则都指向同一个赢家/政党，2–4c 的价差在结算时变成 $1。危险的分歧方向是 PM 判该候选人赢、Kalshi 判其输（付 $0）；反方向（Kalshi 赢、PM 输）付 $2，是 windfall。因此价差补偿的是危险方向的概率和跨场执行摩擦，不是零风险；这一点与 `dot-005` 的“精确互补集”假设不同，也不同于“两边都同意就付 1、不同意就归零”的对称说法。
- **不需要候选人集合穷尽**：第三方/独立候选人赢时，只要两边都判该候选人没赢（K=0, P=0），这对腿仍付 $1。这一点优于 `dot-005` 要求的“互补结果集精确映射”；但“第三方赢”本身不保证两边一致，仍要逐场核对规则。
- **为什么持续**：跨场没有原子执行，资金在两边分开，Kalshi 是 CFTC 监管的美元场所、Polymarket 是 Polygon 上的 pUSD/USDC 场所，用户和做市商不共享库存；选举季的流动性又集中在少数场次。只要这些摩擦存在，同一候选人的两边报价就会反复出现可挂的价差。
- **不是平台补贴**：本条不依赖 Kalshi LP 奖励、Polymarket 流动性奖励或 holding reward；收益全部来自两边报价的差。

## 规则

### Kalshi 的结算口径（已读合约条款 PDF）

`GOVPARTY`（州长）：

- Underlying 是“在 `<election year>` 被选为 `<state>` 州长的人的政党”。
- Payout Criterion 是“依据该选举被宣誓就任州长的人是 `<political party>` 的成员”。如果当选者在就职前辞职、出现空缺，则按“第一位宣誓就任的临时或永久替代者”的政党结算。
- 加速结算：至少 4 家（共 8 家）Designated Media Sources 已宣布同一获胜候选人/政党，且没有任何一家发出相反声明。8 家是 NYT、AP、DDHQ、CNN、Fox、NBC、CBS、ABC。否则等到宣誓就任后的第一个 10:00 AM ET，或 popula vote 后一年。
- 如果个人在选举后、宣誓前改变党派，按 election day 的党派结算。

`SENATEPARTY`（参议员）：

- Payout Criterion 是“第一位向美国参议院提交选举证书、并为该任期宣誓就任的候选人”的政党；空缺时按第一位替代者的政党。
- 加速结算条款与 `GOVPARTY` 相同（4/8 媒体源，且无相反声明）。
- 结算源是 United States Congress。

### Polymarket 的结算口径（已读 Gamma market description）

以 Georgia Governor 的 Bottoms 市场为例，原文要点：

- “This market will resolve according to the winner of the 2026 Georgia gubernatorial election.”
- 候选人以政党提名为准；独立候选人不会被归入 Democrat 或 Republican 选项。
- 如果被点名的候选人在 election day 前被替换为提名人，市场会更新为替换后的提名人，并按替换后的提名人结算。
- Resolution source 是 Associated Press、Fox News、NBC；三家都对同一候选人 call 后市场才 resolve；如果三家没有对同一候选人 call，则按官方 certification 结算。

### 两边的对齐与分歧

| 状态 | Kalshi | Polymarket | 这对腿的支付 |
|---|---|---|---|
| 候选人赢并正常就职 | YES | YES | 1（一致） |
| 候选人输（含第三方/独立赢） | NO | NO | 1（一致） |
| 候选人赢，但就职前辞职/无法就职，替代者属另一党 | 可能按替代者政党 NO | 按 election winner YES | 0（危险方向） |
| 反方向分歧（Kalshi 判赢、PM 判输） | YES | NO | 2（windfall，较少见） |
| 候选人赢，但认证/宣誓争议长期未决 | 可能延迟或按替代者 | 可能按官方 certification 延迟 | 时间风险；最终可能是 0 或 1 |
| 媒体 call 不一致（Kalshi 4/8 vs PM AP+Fox+NBC） | 可能先结算 | 可能后结算 | 时间差，不是最终支付差 |

表中的“支付”是两条腿合计：1 表示收敛收益，0 表示成本全损，2 表示额外赚一份。只有 K=0,P=1（PM 判赢、Kalshi 判输）才是 0；K=1,P=0 是 2。windfall 方向在实践中较少见（需要 Kalshi 的宣誓结果与 PM 的 election winner 反向），保守按 p≈0 处理；危险方向则是“赢家未就职、替代者属另一党”，更现实。

- 两边的共同点：都以政党为单位、都允许媒体 call 加速、都以官方认证为 fallback。
- 两边的关键差异：Kalshi 的最终条件是“宣誓就任/提交证书”，Polymarket 是“election winner”。正常流程下两者一致；只有“赢家未就职且替代者属另一党”“参议院拒收证书/长期争议”等尾部场景才会分歧。危险方向是 **PM 判该候选人赢、Kalshi 判其输**（付 0）；反方向是 windfall（付 2）。这是本条最大的非市场风险，也是价差存在的原因之一。
- 因此下单前必须逐场做规则审计：同名同党、同一席位、同一选举年；排除有提名争议、候选人在 election day 前被替换、或已经出现认证争议的场次。

### 费用

- Kalshi：taker `ceil(0.07 × C × p × (1−p))`，按订单向上取整到分；maker `0.0175 × C × p × (1−p)`，只在 Kalshi 标记了 maker fee 的 series 收取。Elections 的 series（`GOVPARTYGA`、`SENATENC` 等）在 `/series` 返回 `fee_type=quadratic`，而带 maker fee 的 series 返回 `quadratic_with_maker_fees`（例如 `KXNBAGAME`）；因此本批选举 series 的 maker fee 按 0 计。若成交回执显示实际收了 maker fee，则按 0.0175 公式回算（p=0.5 时约 0.44c/份）。
- Polymarket：`fee = C × feeRate × p × (1−p)`，Politics 的 feeRate=0.04；`feeSchedule` 包含 `rate=0.04`、`takerOnly=true`、`rebateRate=0.25`（`exponent=1`）。Makers 不付费；另有 25% 的 taker fee 进入 Maker Rebates Program（不计入本条的保守收益）。
- Kalshi 对现金和未平仓头寸支付 3.50% 可变 APY，按日按 12am ET 的组合净值计息、按月支付；这是 Kalshi 腿的 carry 补贴，不计入核心价差。

## 证据

### 2026-10-20 04:00 UTC 的公开盘口快照

匹配方法：按州、席位类型、政党、姓氏匹配 Kalshi `yes_sub_title` 与 Polymarket `groupItemTitle`；只保留姓氏一致的配对。共覆盖 65 场有 Kalshi `-26` 事件的州级选举，得到 117 个同名同党候选人配对。价格单位是美元/份；“K 买价/卖价”是 Kalshi YES 的 bid/ask；“PM 买价/卖价”是 Polymarket YES 的 bid/ask；“PM NO 买价”= 1 − PM YES 卖价，“PM NO 卖价”= 1 − PM YES 买价。

| 场次 | 候选人 | Kalshi YES bid/ask（bid  size） | PM YES bid/ask（NO bid  size） | maker 成本 | maker 毛边 | taker 费后边 |
|---|---|---:|---:|---:|---:|---:|
| GA Governor | Keisha Lance Bottoms (D) | 0.49 / 0.50（100） | 0.52 / 0.53（NO bid 0.47 / 1,187；NO ask 0.48 / 1,902） | 0.96 | **+4.00c** | −0.75c |
| NV Governor | Aaron Ford (D) | 0.55 / 0.56（15,098） | 0.58 / 0.59（10,001） | 0.96 | **+4.00c** | −0.70c |
| OH Governor | Amy Acton (D) | 0.70 / 0.71（497） | 0.72 / 0.73（20,725） | 0.97 | **+3.00c** | −1.25c |
| OR Governor | Tina Kotek (D) | 0.80 / 0.81（3,980） | 0.82 / 0.83（NO bid 0.17 / 142；next 0.16 / 7,032） | 0.97 | **+3.00c** | −0.67c |
| SC Senate | Annie Andrews (D) | 0.16 / 0.18（78,469） | 0.17 / 0.18（8,526） | 0.98 | **+2.00c** | −2.60c |
| MI Senate | Abdul El-Sayed (D) | 0.68 / 0.69（45,105） | 0.69 / 0.70（6,303） | 0.98 | **+2.00c** | −2.35c |
| WI Governor | David Crowley (D) | 0.79 / 0.80（54,186） | 0.80 / 0.81（16,354） | 0.98 | **+2.00c** | −1.76c |
| NH Senate | John E. Sununu (R) | 0.10 / 0.11（9,750） | 0.11 / 0.12（8,711） | 0.98 | **+2.00c** | −1.08c |
| MS Senate | Scott Colom (D) | 0.11 / 0.12（2,539） | 0.12 / 0.13（18,374） | 0.98 | **+2.00c** | −1.16c |

- 算法：maker 成本 = Kalshi YES bid + (1 − PM YES ask)；taker 成本 = Kalshi YES ask + (1 − PM YES bid)。表中“maker 毛边”= 1 − maker 成本；“taker 费后边”= 1 − taker 成本 − Kalshi taker fee − PM taker fee，费用按上面的公式和 p 逐项算。
- 全样本 117 个配对：maker 毛边 ≥1c 的 61 个、≥1.5c 的 30 个、≥2c 的 20 个、≥3c 的 4 个、≥4c 的 2 个、最高 4.00c；中位数 1.00c，均值 0.90c。
- taker 费后只有 6 个为正，中位数 −1.52c、均值 −1.81c。**同一批配对，吃单普遍亏钱，挂单才有边**；这是本条必须 maker-only 的直接证据。
- 上表是单一时点快照，不是历史回测；Kalshi bid size 是 top-of-book 显示量，PM NO size 是 CLOB 当前 NO token 的 bid size。显示量不等于我们能成交的量：同一价格上可能排着更大的队列，且下单后队列会变化。
- 表中“maker 毛边”按 join 最优买价计算，未扣任何 maker fee；Kalshi Elections 的 `fee_type=quadratic` 表示不收 maker fee，Polymarket maker 也不收费。若按保守口径（Kalshi +1c、PM 也按 +1c）两边各改进一档，低价的 SC/MI/WI/NH/MS 配对成本会升到 1.00，毛利归零；GA/NV 剩 2c，OH/OR 剩 1c。若 PM 的实际最小 tick 是 0.001，则总成本只升 1.1c，低价配对还剩约 0.9c，但仍很薄。**因此“join 还是 improve”本身就是要测的变量，不能假设一定能用中间价成交。**
- 表中的“maker 毛边”是**两边一致时**的收敛收益；它不是无风险收益。若出现 PM 判赢、Kalshi 判输，这对腿归零，损失 0.96–0.98；若出现 Kalshi 判赢、PM 判输，则付 2，额外赚 1.02–1.04。价差是否值得赚，取决于危险方向的概率是否低于约 2–4%（见风险）。
- 只有 Kalshi/PM 的实时公开盘口，没有两家的历史 L2；没有成交回放、没有已实现 PnL、没有 Sharpe/回撤。`backtest_count=0`。表中的 117 个配对不是 117 个独立尾部事件：它们共享选举夜和认证风险，不能把 117 当成 117 次独立下注。

### 其他证据

- Kalshi `GOVPARTY.pdf` / `SENATEPARTY.pdf` 已读全文，看到 4/8 媒体源加速、宣誓就任条件、空缺替代条款。
- Polymarket Georgia Governor 的 Bottoms/Jackson 市场 description 已读，看到 AP+Fox+NBC 三家 call、官方 certification fallback、候选人替换条款。
- Kalshi `/series/SENATENC`、`/series/GOVPARTYGA` 返回 `fee_type=quadratic`、`fee_multiplier=1`；Kalshi 文档更新（2026-08-20/22）说明 maker fee 启用，且 combo 的 maker multiplier 为 0.5；`/series` 全量统计中 `quadratic_with_maker_fees` 只占少数（例：`KXNBAGAME`），选举 series 不在其中。
- Kalshi 帮助页 “APY on Kalshi”（更新 2026-10-16）已读：3.50% 可变利率，现金和未平仓头寸都计息，按 12am ET 的组合净值日计，按月支付；美国 eligible users、平均月余额 ≥$250。
- 二手参考：LaunchPoly 的 “Polymarket–Kalshi Arbitrage 2026” 文章（访问 2026-10-20，**二手**）描述了 6c 毛价差的例子、两边费用和“先读规则”的注意事项；本条没有采用它的任何收益数字，只把它当作机制背景。

## 数据

- Kalshi：`https://api.elections.kalshi.com/trade-api/v2`；用 `/events/{event_ticker}?with_nested_markets=true` 取 `yes_bid_dollars`、`yes_ask_dollars`、`yes_bid_size_fp`、`yes_ask_size_fp`、`rules_primary`、`rules_secondary`、`close_time`、`expected_expiration_time`；用 `/markets/{ticker}/orderbook?depth=10` 取全深度。免费、免密钥。
- Polymarket：`https://gamma-api.polymarket.com/events?slug=...` 取 `markets[].bestBid`、`bestAsk`、`feeSchedule`、`clobTokenIds`、`description`、`endDate`；`https://clob.polymarket.com/book?token_id=...` 取 YES/NO 两侧的 bids/asks 和 size。免费、免密钥。
- 本次实际拉取的场次包括：`GOVPARTYGA-26`、`GOVPARTYNV-26`、`GOVPARTYOH-26`、`SENATENC-26`、`SENATEMI-26`、`SENATEME-26`、`SENATENH-26`、`SENATEMS-26` 等；Polymarket 对应 slug 为 `georgia-governor-winner-2026`、`nevada-governor-winner-2026`、`ohio-governor-winner-2026`、`north-carolina-senate-election-winner`、`michigan-senate-election-winner`、`maine-senate-election-winner`、`new-hampshire-senate-election-winner`、`mississippi-senate-election-winner`。
- 匹配排除：SC Senate 的 Kalshi `Darline Graham` 与 PM `Darline Graham Nordone` 因姓氏不一致被剔除；LA Senate 的 Kalshi `Charles Booker`/`Andy Barr` 与 PM `Jamie Davis`/`Julia Letlow` 完全不匹配，也剔除。这个排除步骤本身说明“按政党硬配”会产生假配对，必须按名字核。
- 完整 117 行快照（按 maker 毛边降序）保存在 `notes/20261020-pm-kalshi-election-pairs.csv`，字段为 state、office、party、candidate、Kalshi YES bid/ask、PM YES bid/ask、两边 top size、maker 成本、maker 毛边、taker 费后边；表里的 9 行都来自这个文件。
- 缺失：历史 L2、逐笔成交、真实 fill rate、maker queue 位置、Kalshi/PM 的账户级费率（是否有返佣/等级）、选举夜的认证争议数据。都需要前向记录或账户权限。

## 两周内怎么检验

- **扫描范围**：每天扫 2026 Senate/Governor 的 Kalshi `-26` 事件和 PM 对应 winner 事件，保留同名同党、同一席位、同一选举年的配对；预计 60+ 场、100+ 配对。同步记录 top-5 档深度，不只 top-of-book。
- **两种报价**：
  1. **join**：在 Kalshi YES bid 和 PM NO bid 上各挂同价单，排在现有队列后面；
  2. **improve**：在 Kalshi 加 1c、PM 加 0.001（或最小 tick），做当前最优买价。
  每个配对最多挂 2,500 对的预算，但实际按 top-of-book 的 min(size) 缩量；单笔不超过 500 对（约 $480），单场不超过 $1,000，总敞口不超过 $2,500/场所。
- **成交判定**：不用“价格穿过”当成交，而是用公开成交 tape 判断——Kalshi `/markets/{ticker}/trades`、PM `https://data-api.polymarket.com/trades` 上出现与我们的挂单价相同或更差的成交，才算我们成交；同一时间戳的多笔成交按队列位置和 size 折算，不能假设全量成交。
- **单边成交的处理**：一旦只有一条腿成交，立刻在另一条腿按当前 ask 吃单对冲，记录实际对冲价、taker fee 和滑点；不允许裸奔到结算（除非对冲价差已经大于毛边，此时记录为主动放弃）。
- **主结果**：≥30 个独立 race-candidate 配对，每个配对至少有一次双边成交或一次“单边成交 + 对冲”记录；同一场选举的 D/R 两个候选人、同候选人的多个报价档只算 1 个配对结果。117 个配对共享选举夜风险，所以另记“同一夜最大同时敞口”和“危险方向（PM 赢/Kalshi 输）的分歧损失”；Kalshi 赢/PM 输的 windfall 单独记，不计入失败但计入净 PnL。
- **失败标准**：费后净边中位数 <1c；或单边成交后对冲的中位亏损 >毛边；或任一对出现 PM 判赢、Kalshi 判输的规则分歧（危险方向）；或 30 个配对中双边同时成交率 <20%；或最大回撤 >总资金的 10%。
- **时间窗**：2026-10-20 至 2026-11-03（选举日）。选举后持仓按实际结算价记账，不按中间价；Kalshi 若等到宣誓就职（最晚 2027-01）才结算，年化按实际占用天数重算，不能用 14 天硬乘。

## 成本与容量

- **费用公式**：Kalshi taker `ceil(0.07×C×p×(1−p))`，maker 0（本批 Elections series）；PM taker `C×0.04×p×(1−p)`，maker 0。Kalshi 费用按订单向上取整到分，Q≥100 时每份的取整误差可忽略；Q 很小时不要用 1 份去试，取整会把费用放大。
- **示例（NV Ford，Q=2,500 对，按场所上限算）**：Kalshi 腿 0.55×2,500 = $1,375；PM NO 腿 0.41×2,500 = $1,025；总占用 $2,400，低于 $5,000 总预算和 $2,500/场所上限。join 成交时毛边 4c/对 = $100；improve 1c 后毛边 2c/对 = $50。两腿都按 maker 0 费，净边就是毛边；Kalshi 3.50% APY 在三周内约 $2.8（约 0.11c/对），只作为小补贴。
- **年化**：若 2026-11-10 前结算，$100/$2,400 = 4.17%，21 天年化约 72%；若拖到 2027-01-14 宣誓后就职，86 天年化约 17.7%。$50 的情形分别是约 35% 和 8.7%。两种都高于 8%，但 8.7% 只是刚过线，且未计 legging 损失。
- **容量**：20 个配对毛边 ≥2c；top-of-book 的 min(size) 从 100（GA）到 16,354（WI）不等；NV 10,001、SC 8,526、MI 6,303；OR 在 0.17 只有 142，下一档 0.16 有 7,032。$2,500/场所的预算在 NV/SC/WI/MI 等大 size 场次能放下；GA/OH 的 Kalshi 显示量只有 100/497，实际容量受队列限制。单笔建议 ≤500 对（约 $480）、单场 ≤$1,000 的自我限制比总预算更紧。
- **机会频率**：2026 中期选举是一次性窗口；机制在每个选举周期（2028、2026 州级补选）和任何“同一事件、同一候选人、两场挂牌”的场合重复。非选举季可退到 FOMC/CPI 等跨场同名事件，但那些事件的规则对齐和费用结构需要另做审计，不在本条的 117 个样本里。
- **未计入**：legging 的对冲成本、maker queue 的机会成本、PM 的 25% maker rebate（正贡献）、Kalshi 可能的 maker fee（负贡献）、资金进出费用。测试要把这些逐项记账。

## 风险

- **规则分歧是唯一会让这对腿归零的风险，而且方向不对称**：Kalshi 的最终条件是“宣誓就任/提交证书”，PM 是“election winner”。正常流程一致；如果赢家在就职前辞职/无法就职且替代者属另一党，或认证/宣誓长期争议（参议院场景是拒收证书），Kalshi 可能判 NO 而 PM 判 YES，两条腿同时错，损失全部成本。反方向（Kalshi 判 YES、PM 判 NO）则付 $2，是 windfall。若危险方向概率为 q、反方向为 p，EV = 毛边 − q + p；p≈0 时，2c 毛边的 breakeven q≈2%，4c 毛边≈4%。本条没有数据证明 q 低于这个数，因此只能小仓、分散、逐场审计，并在出现认证争议时立即退出。
- **单边成交/legging**：两条腿不是原子成交。一条腿成交、另一条没成交时，另一条腿的 taker 对冲会吃掉大部分边；低价配对（SC/MI/WI/NH/MS）的对冲后边只有 0.4–1c，甚至转负。测试必须把“单边成交 + 对冲”作为主结果之一，而不是只统计双边都成交的理想样本。
- **队列/成交假设**：表中 maker 边按 join 最优买价计算，但最优买价上可能排着 15,000 份的队列；join 可能整个窗口都不成交，improve 一个 tick 又会让低价配对归零。真实 fill rate 未知，是本条最大的执行不确定性。
- **逆向选择**：我们的买价被吃，往往是因为有人掌握了对我们不利的信息（候选人丑闻、民调突变、认证消息）。成交后 10 天的 markout 可能为负；如果 markout 持续低于毛边，说明价差只是对逆向选择的补偿，不是免费的钱。
- **场所/合规**：Kalshi 需要美国 eligible 账户；Polymarket global 在部分司法辖区不可用，且 pUSD/USDC 的出入金、Polygon 拥堵、negRisk adapter 都可能影响腿的可用性。本条只做纸面/只读研究，不提供交易代码、钱包或密钥。
- **费用/规则会变**：Kalshi 可能在选举 series 上启用 maker fee；PM 可能调整 Politics 的 0.04 或 rebate；两边的 media source 列表和加速条款也可能改。每次下单前重读 series fee_type 和市场 rules，不能把今天的费率当成结算时的费率。
- **相关性/尾部**：117 个配对不是 117 个独立事件；它们共享选举夜、认证流程和同一批媒体 call。单场规则分歧的损失可能同时影响多个配对；仓位要按“同一夜最大同时敞口”而不是按配对数来限。
- **结算时间**：Kalshi 的 `close_time` 是 2027-11-03，`expected_expiration_time` 是 2027-01-14；即使有 4/8 媒体 call 的加速条款，也不能保证选举夜就结算。资金可能被锁到就职日，年化要按实际天数重算。

## 改进了什么

- **原版 `dot-005`**：用“跨场等价命题支付映射”，要求两边的结果集精确互补；FOMC 的例子用条件式映射（Kalshi 的利率上限市场 vs PM 的分档），并且只有 19 天前的旧报价，没有当前可执行盘口、没有费用拆解、没有执行检验。
- **本版的改动**：
  1. 把“精确互补集”换成“同一候选人的跨场相对价值价差”（Kalshi YES + PM NO）。两边一致时付 1；Kalshi 判赢/PM 判输时付 2；PM 判赢/Kalshi 判输时付 0。它不要求结果集穷尽（第三方赢时只要两边都判该候选人输，仍付 1），但也不是无风险套利；相比 `dot-005`，它把“规则不一致”从映射假设变成了可单独审计、可设上限的方向性尾部。
  2. 用 65 场、117 个同名同党配对做实时横截面，给出 top-of-book 的 bid/ask/size，而不是引用旧报价；并明确排除姓氏不匹配的假配对（SC Graham、LA Booker/Barr）。
  3. 把 maker-only 作为硬约束：同一批配对 taker 中位数 −1.52c、只有 6 个为正；maker 毛边中位数 1.00c、20 个 ≥2c。`dot-005` 没有说明吃单费会吃掉价差。
  4. 补上 Kalshi Elections 的 `fee_type=quadratic`（maker 0）与 PM Politics 的 0.04/takerOnly/25% rebate 的逐项费用；把 Kalshi 3.50% APY 作为 carry 小项。
  5. 补上规则对齐表和分歧场景（宣誓 vs election winner、4/8 vs AP+Fox+NBC、替代者条款），把“规则不一致”从脚注提升为唯一归零风险，并区分危险方向（付 0）和 windfall（付 2）。
  6. 给出两周前向检验：join/improve 两种报价、公开成交 tape 判定 fill、单边成交后 taker 对冲、≥30 个配对、明确的失败阈值。`dot-005` 的检验是“前向记录”，但没有 fill/legging 的具体判据。
- **为什么更好**：原版是一个无法用当前盘口验证的映射草稿；本版是一个现在就能扫、能挂、能用公开 tape 记账的 maker 策略，并且明确承认它的收益来自“流动性服务 + 跨场规则基差”，不是无风险套利。
- **怎么证明**：按“两周内怎么检验”跑 2026-10-20 至 2026-11-03 的前向记录；如果 ≥30 个配对的双边成交/对冲后净边中位数 ≥1c，且没有出现 PM 赢/Kalshi 输的危险方向归零，则改进成立；如果 legging 后中位亏损大于毛边，或 30 个配对的双边成交率 <20%，或出现危险方向归零，则本版被证伪。

## 门槛自查

1. **机制说得清**：**满足**。付款方是两边吃单者；收益是同一候选人跨场报价差；两边一致时付 1，PM 赢/Kalshi 输时付 0，Kalshi 赢/PM 输时付 2；持续原因是跨场执行摩擦、资金分离和规则差异。它不是无风险套利，机制里已写明方向性尾部。
2. **有免费数据能检验**：**满足（前向）**。Kalshi trade-api v2 和 PM Gamma/CLOB 都免费免密钥，当前快照已拉到 117 个配对；历史 L2 没有免费源，所以用两周前向记录，主结果 ≥30 个配对。不是 12 个月历史回测。
3. **小资金能做**：**满足**。NV 例子 Q=2,500 对占用 $2,400（Kalshi $1,375 + PM $1,025），低于 $5,000 总预算和 $2,500/场所上限；单笔 ≤500 对（约 $480）、单场 ≤$1,000 的自我限制更紧。
4. **不重复**：**满足（按 improvement）**。`dot-005` 是同一机制的原版，但本条换的不是执行细节，而是支付映射本身（跨场相对价值价差 vs 精确互补集），并补上了 117 个实时配对、taker 负边证据、Elections maker 0 的费用拆解和 fill/legging 判据。这些差异都是原版没有的，按 improvement 交；若主审按更严口径只认“新机制”，则本条可降为 supplement，收益数字不变。
5. **扣成本后粗算够用**：**边际**。maker 毛边中位数 1.00c、20 个 ≥2c、最高 4.00c；Kalshi Elections maker 0、PM maker 0，费后就是毛边；但 join 的队列、单边成交的对冲成本和危险方向 q 的期望损失都未测（q≈2% 时 2c 毛边的期望收益归零）。按 NV 的 2–4c 和 21/86 天占用，年化约 8.7–72%，刚过或明显高于 8%；legging 或 q 可能把它打到 8% 以下，所以不标“满足”。
6. **两周内能检验**：**满足**。2026-10-20 至 2026-11-03 正好覆盖选举日；每天扫 60+ 场，预计 100+ 配对，主结果 ≥30 个；用公开成交 tape 判定 fill，单边成交后按 taker 对冲记账；失败标准明确（净边 <1c、对冲后中位亏损 >毛边、双边成交率 <20%、危险方向分歧）。
7. **出处可查**：**满足**。Kalshi/PM 的 API 原始 JSON、两份合约条款 PDF、PM market description、Kalshi series fee_type、Kalshi 费用/取整文档、Kalshi APY 帮助页、PM 费用文档都标了访问日期和阅读程度；二手文章只作背景，未用于数字。

## 出处

- `https://api.elections.kalshi.com/trade-api/v2/events/GOVPARTYGA-26?with_nested_markets=true` — 访问 2026-10-20 — 已读（市场、报价、size、rules_primary/secondary）
- `https://api.elections.kalshi.com/trade-api/v2/events/SENATENC-26?with_nested_markets=true` — 访问 2026-10-20 — 已读
- `https://api.elections.kalshi.com/trade-api/v2/events/GOVPARTYNV-26?with_nested_markets=true` — 访问 2026-10-20 — 已读
- `https://api.elections.kalshi.com/trade-api/v2/markets/GOVPARTYGA-26-D/orderbook?depth=10` — 访问 2026-10-20 — 已读（YES/NO 两侧深度）
- `https://api.elections.kalshi.com/trade-api/v2/series/GOVPARTYGA` — 访问 2026-10-20 — 已读（`fee_type=quadratic`、`fee_multiplier=1`）
- `https://api.elections.kalshi.com/trade-api/v2/series/SENATENC` — 访问 2026-10-20 — 已读（`fee_type=quadratic`、`contract_terms_url=SENATEPARTY.pdf`）
- `https://assets.kalshi.com/contract_terms/GOVPARTY.pdf` — 访问 2026-10-20 — 已读（Payout Criterion、4/8 媒体源加速、空缺替代条款）
- `https://assets.kalshi.com/contract_terms/SENATEPARTY.pdf` — 访问 2026-10-20 — 已读（提交证书/宣誓、4/8 媒体源加速）
- `https://docs.kalshi.com/getting_started/fee_rounding` — 访问 2026-10-20 — 已读（按订单向上取整、direct member $0.0001、non-direct $0.01）
- `https://docs.kalshi.com/changelog` — 访问 2026-10-20 — 已读（2026-08-20/22 maker fee 启用；combo maker multiplier 0.5；`quadratic_with_maker_fees` 类型）
- `https://help.kalshi.com/en/articles/13823847-apy-on-kalshi` — 访问 2026-10-20 — 已读（3.50% 可变、现金+未平仓头寸、12am ET 净值、按月支付、美国 eligible、平均月余额 ≥$250）
- `https://gamma-api.polymarket.com/events?slug=georgia-governor-winner-2026` — 访问 2026-10-20 — 已读（description、bestBid/bestAsk、feeSchedule、clobTokenIds）
- `https://gamma-api.polymarket.com/events?slug=nevada-governor-winner-2026` — 访问 2026-10-20 — 已读
- `https://gamma-api.polymarket.com/events?slug=north-carolina-senate-election-winner` — 访问 2026-10-20 — 已读
- `https://clob.polymarket.com/book?token_id=59980150909931986777748227027020522224275707387562276219060223816867188565245` — 访问 2026-10-20 — 已读（Bottoms YES book）
- `https://clob.polymarket.com/book?token_id=29426800815897155175757951733656404312185134543823956306564757069451562558732` — 访问 2026-10-20 — 已读（Bottoms NO book）
- `https://docs.polymarket.com/trading/fees` — 访问 2026-10-20 — 已读（`fee=C×feeRate×p×(1−p)`、Politics 0.04、makers 不收费、25% maker rebate、5 位小数舍入）
- `https://launchpoly.com/blog/polymarket-kalshi-arbitrage-guide` — 访问 2026-10-20 — **二手**（6c 毛价差示例、两边费用、先读规则的提醒；未采用其收益数字）
