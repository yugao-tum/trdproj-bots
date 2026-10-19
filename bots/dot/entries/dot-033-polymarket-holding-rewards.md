---
id: dot-033
name_zh: Polymarket持有奖励
name_en: Polymarket Holding Rewards
bot: dot
date: 2026-10-19
market: polymarket
pm_category: cross
kind: new
improves: -
category: Y
return_type: carry
instruments: Polymarket 合格事件 YES/NO 份额
venues: Polymarket
data: Help 页资格清单/费率、Gamma holdingRewardsEnabled 与 feeSchedule、CLOB 中间价、data-api 成交；免费免密钥；历史到账、费率变更、历史资格清单缺失
test_2w: 前向采集尚未启动，原拟定2026-10-19起点；独立canonical event clusters不按日重复，18仅旧页面候选清单且当前资格/到账未知；3.25%仅条件情景，记录实际奖励与全路径成本，未获30独立有效结果或未核费用/资格则检验未完成
status: 草稿
confidence: 低
---

整理说明：本稿为已保存证据的操作员侧校订；无新增抓取、交易或回测。未运行的采集与验证仍为计划。

## 一句话

研究旧Polymarket帮助页描述的持有奖励：合格YES/NO持仓可能按小时抽样、按日获得Treasury补贴；3.25%及18事件仅为该版本页面记录，当前适用性冲突未解，不能当确定实际收益。单边持仓仍有方向风险。

## 钱从哪里来

Polymarket Treasury 的补贴预算。平台为“长期市场定价准确性”和更稳定的持仓付费，付款方是平台 Treasury，不是对手方亏损，也不是交易手续费分成。只要平台继续补贴，付款动机就存在；但帮助页明确说费率可变、平台可随时设上限，且本轮补贴由 Treasury 出资，因此不是结构性、可无限持续的无风险收益。

## 规则

- 资格事件：已保存的2026-06-01页面版本列18个候选事件，不代表历史最大或当前全平台资格上限：
  - 政治：Presidential Election Winner 2028；Republican Presidential Nominee 2028；Democratic Presidential Nominee 2028；Which party wins 2028 US Presidential Election?；Balance of Power: 2026 Midterms；Which party will win the Senate in 2026?；Which party will win the House in 2026?。
  - 人物/地缘：Erdoğan out before 2027?；Zelenskyy out as Ukraine president before 2027?；Netanyahu out before 2027?；Xi Jinping out before 2027?；Putin out as President of Russia before 2027?；Russia x Ukraine ceasefire before 2027?。
  - 加密价格：What price will Bitcoin hit in 2026?；What price will Ethereum hit in 2026?；What price will Hyperliquid hit in 2026?；What price will Solana hit in 2026?；What price will XRP hit in 2026?。
- 计费口径：帮助页写“3.25% annualized Holding Reward”，按合格持仓的总 position value 计；position value 按当前 YES/NO 股数乘以每个 outcome 的“most recent mid-price”计算。页面例子：30,000 YES @ $0.53 + 10,000 NO @ $0.45 = $20,400；每小时奖励 `$20,400 × (0.0325 / 365 / 24) ≈ $0.075697`，按日累计发放。以上为来源原例，实际到账未核实；算术复核20400×0.0325/365/24≈$0.075685，原文$0.075697有微小计算差异，不作为实际支付数。
- 抽样与支付：总持仓价值每小时随机抽样一次；奖励每日发放。帮助页未写抽样时点、时区、随机偏移、最低支付、舍入规则和奖励币种；这些是缺测，不能自行补。
- 进场/出场：买入合格事件的 YES 或 NO 份额并持有；可以在到期前卖出，但卖出后不再按该持仓计奖；持有到结算则按底层市场规则兑付。没有额外锁仓合约，但资金实际被仓位占住。
- 纸面预算：单场所含购入款、全部费用及风险预留≤2,500 USDT，总资金5,000，不加杠杆借钱。严格动态上限还要包括持仓增值/奖励，减仓或转出路径未核须标超限风险；预算不是实际容量。
- 底层结算示例（JD Vance 市场）：规则原文写明由 Associated Press、Fox News、NBC 三家共同判定；三家都叫同一候选人时结算；到 2029-01-20 就职日仍未三家一致，则按“谁就职”结算。市场 `endDate=2028-11-08T04:59:00Z`（按 EST 约为 2028-11-07 23:59）。
- 费率适用时间：3.25% 只出现在帮助页（`dateModified=2026-06-01T13:58:20Z`）。原研究 直接抓取 `docs.polymarket.com/polymarket-learn/trading/holding-rewards` 时，返回的仍是同一份 3.25%/18 事件文本；但同一 URL 的搜索摘要显示过 4.00%/13 事件的版本。两者冲突，**不能确认 3.25% 在 2026-10-19 仍适用于全部 18 个事件**。因此本文把 3.25% 当作“页面标称值”，不当作今日已核实费率。
- 18只是已保存旧页面的一次清单，不是当前全部、历史最大或最小。另有4%/13事件摘要，与该正文版本冲突，无法以任一旧值回填今日或历史费用/资格；当前完整范围、实际生效日期未核。
- 美国站不迁移：帮助页没有写司法辖区；本文只按 global help 文引用，不使用 `polymarket.us` 的 Rewards/Liquidity Incentive Program 参数，也不把美国站规则当成 global 规则。

### 示例市场、规则源、时间日界、舍入与缺测

- 示例市场 1：`will-jd-vance-win-the-2028-us-presidential-election`（market id 561229）。2026-10-19T17:42Z Gamma 快照：`holdingRewardsEnabled=true`、`feeSchedule={rate:0.04, exponent:1, takerOnly:true, rebateRate:0.25}`、`rewardsMinSize=50`、`rewardsMaxSpread=5.5`、`clobRewards[0].rewardsDailyRate=42`、`startDate=2026-10-19`、`outcomePrices=["0.2005","0.7995"]`、`orderPriceMinTickSize=0.001`、`orderMinSize=5`。
- 示例市场 2：`will-gavin-newsom-win-the-2028-us-presidential-election`（market id 561230），同快照 `holdingRewardsEnabled=true`、`feeSchedule` 同上、`rewardsDailyRate=11`。
- 示例市场 3：`will-alexandria-ocasio-cortez-win-the-2028-us-presidential-election`（market id 561231），同快照 `holdingRewardsEnabled=true`、`feeSchedule` 同上、`rewardsDailyRate=22`。
- 说明：这三个示例同属 event `presidential-election-winner-2028`，只算 **1 个候选事件簇**，不是一个已经完成收益验证的独立结果，不能拿来凑 30。Gamma 快照显示该 event 有 128 个市场、`negRisk=true`、`restricted=true`，128 个市场都 `holdingRewardsEnabled=true`；帮助页只列事件，不逐市场列名，新增/删除候选人是否自动合格未核。另一个旧帮助页候选事件 `putin-out-as-president-of-russia-before-2027` 只在清单中出现，原研究 未抓取其 Gamma 规则。
- 规则源：帮助页的 Eligible Events 清单是资格来源；Gamma 的 `holdingRewardsEnabled` 只是布尔字段，不携带费率、抽样时点或支付地址。底层结算按各市场规则原文，示例见上。
- 时间日界：每小时随机抽样一次，奖励每日发放；具体小时偏移、UTC/ET 日界、跨日归属未写。示例年化用 `/365/24`，不是按 360 天。
- 舍入：帮助页没有写持有奖励的最低支付或舍入；不能套用流动性奖励的 $1 最低支付。PM 交易费本身按 5 位小数、最小 0.00001 USDC 舍入（`docs/trading/fees`），但这不是持有奖励的舍入规则。
- 缺测：逐钱包实际到账、历史费率/资格清单、每小时抽样实现、奖励币种与地址、平台上限、当前 2026-10-19 的生效费率均缺失。

## 证据

- 原研究 已读 `help.polymarket.com/en/articles/13364459-holding-rewards`：3.25% annualized、Treasury 出资、每小时随机抽样、每日发放、position value 按 YES/NO 股数乘最近 mid-price、18 个事件清单、$20,400 的例子。以上是来源自报，未用实际支付复现。
- 原研究 已读 `docs.polymarket.com/polymarket-learn/trading/holding-rewards`：webfetch 最终返回同一份 help 文本（3.25%/18 事件，`dateModified=2026-06-01T13:58:20Z`）。同一 URL 的搜索摘要显示 4.00%/13 事件；这是**摘要与正文的版本冲突**，未解决。本文不把 4.00% 当今日费率，也不把 3.25% 当已核实今日费率。
- 原研究 已读 Gamma `events?slug=presidential-election-winner-2028`（对象 `updatedAt=2026-10-19T17:42:58Z`）：示例市场 `holdingRewardsEnabled=true`，政治类 `feeSchedule.rate=0.04`、`rebateRate=0.25`、`takerOnly=true`；`rewardsMinSize=50`、`rewardsMaxSpread=5.5`、`clobRewards` 日率 42/11/22/11/14。注意这些是 Gamma 的流动性与奖励配置字段，不证明持有奖励的 3.25% 或实际支付。
- 原研究 已读 `docs.polymarket.com/trading/fees`：费用公式 `fee=C×feeRate×p×(1-p)`、maker 不收费、政治类 0.04/25% rebate、5 位小数舍入。用于成本计算，不用于声称持有奖励已扣费。
- X 检索（`site:x.com`，2026-10-19）返回了 Gravia 的月度奖励摘要：2026 年 7 月 holding rewards $0.4M、liquidity rewards $12.9M；这是二手摘要，未打开正文、未核实，只用于说明持有奖励池相对小。
- 第三方 `polyscalping.org/leaderboard/yield` 搜索摘要：称该计划 2026 年初启动、3.25%、Treasury 出资、按小时抽样、每日以 pUSD 发放；并称“买 YES+NO 近似无风险”。这是二手摘要，未打开正文；pUSD、Split/完整集操作未在官方帮助文核实，本文不把“无风险”当结论。
- 未做完整盈利回测：`observed_net_return=null`；Sharpe=未知；最大回撤=未知；`backtest_count=0`（只表示没有完整盈利回测，不表示收益为 0）。本文是规则/费用/数据筛查，不是收益证明。

## 数据

- 帮助页：`https://help.polymarket.com/en/articles/13364459-holding-rewards`；免费，无需密钥；给出 3.25%、18 个事件、抽样/支付描述；页面日期 2026-06-01。
- 文档别名：`https://docs.polymarket.com/polymarket-learn/trading/holding-rewards`；原研究 抓取时返回同一 help 文；搜索摘要另有 4.00%/13 事件版本。免费。
- Gamma：`https://gamma-api.polymarket.com/events?slug=presidential-election-winner-2028`；免费、免密钥；提供 `holdingRewardsEnabled`、`feeSchedule`、`clobRewards`、`endDate`、`outcomePrices` 等。它是逐市场快照，不含持有奖励费率。
- CLOB：公开 book/price 接口；免费、免密钥；用于取 mid-price 和盘口。本轮未取得免费免密钥历史可执行L2；前向记录尚未启动。
- data-api：`https://data-api.polymarket.com/trades?market=<conditionId>`；免费、免密钥；每个市场最近约 2 万笔成交，用于核对成交/流动性，不足以重建历史持有奖励支付。
- 缺失：逐钱包持有奖励支付、历史资格清单/费率、每小时抽样偏移、奖励币种/舍入、平台总上限。链上支付理论上可查，但本条未取，不能写成已有数据。

## 两周内怎么检验

- 原拟定起点为2026-10-19，采集尚未启动；实际以首条真实记录为准。先对旧页面18个候选逐个核当前资格、有效费率、计奖基数与实际支付。无法核实的只列缺口；按3.25%算的数只作条件情景，不能与实际到账混合。
- 独立结果按canonical event clusters计：同一事件连续14天、多个候选人/档位均只一簇，共同政治/价格驱动还需合并。旧清单18个只是候选数量，不等于18个已完成收益结果，更不代表全历史/全平台上限；历史资格与支付缺失，当前未证30个独立有效结果。
- 两周计划仅可尝试规则与公开支付核验，未取得就写未完成。更多历史或前向候选可再核，但不同事件也需独立性审查，不能按市场、小时或日奖励次数补足30；不把计划写成运行或清单全局上限。
- 当前判据：真实有效费率、资格、支付或全路径现金流无法核对，或有效独立簇不足30，则证据门槛未完成；有完整数据后才按预注册持有期评估全资本费后收益。旧3.25%条件下的成本敏感性不能直接判真实收益通过/失败，不把两周补贴外推为确定年化。
- 由于不能交易，本检验只做公开数据与规则核对，不产生真实成交；实际到账只能引用公开链上/平台记录，未取得就写缺失。

## 成本与容量

- PM总费F=C×r×A×(1−A)，每份f=r×A×(1−A)，费用/名义本金F/(C×A)=r×(1−A)。A是各腿实际成交价。政治类当前快照r=0.04只作示例：两腿各0.50时每腿每份0.01，一对共0.02/合计本金1=2%，不是4%；0.20/0.80为1.28%，0.10/0.90为0.72%。实际盘口各ask未必恰好互补，须逐腿重算
- 以ask买入时crossing已包含；仅从mid价值起算才另加每腿half-spread，不能ask再扣一次半价差。提前卖出另用实际bid并扣出口费；maker成交与Split/merge路径未核，不假设免费执行
- 条件算例（非实测、资格与3.25%全年不变且完整集正常兑付等假设）：1,000对YES/NO，mid各0.50、ask各0.505，则买入价款$1,010；两腿费=2×1000×0.04×0.505×0.495=$19.998，初始现金支出$1,029.998。若全年计奖mid价值保持$1,000且确有3.25%，毛奖励$32.50；若同时按面值$1,000退出且无额外费用，现金净差仅$2.502。它不是“$1,000全包预算赚$32.50”，也不证明一年时能免费退出，未计出口成本可让其转负
- 若以5,000总资本且最多2,500计奖价值粗看，在3.25%不变等条件下毛贡献上限约81.25/5000=1.625%/年；实际含费预算使可部署计奖价值更低，动态上限和退出成本还需核。若以初始现金或已部署本金作分母必须另列，不能把部署年率当全资本收益
- 完整集持有至2028是可选研究路径，不是资金必然锁死：可尝试提前二级卖出，但深度和费用未知；同一条件完整集能否merge提前赎回、操作费/gas与奖励资格影响本轮未核，不假定可无损释放本金
- 实际容量、持有期与每月独立机会数未知。旧页面18事件与Gamma订单门槛都不能证明2,500可部署；orderMinSize=5是5份，金额随成交价变化

## 风险

- 费率与资格风险：3.25% 可变，平台可设上限；帮助页日期 2026-06-01，当前是否仍适用未核实；同一 docs URL 出现 4.00%/13 事件的冲突版本，说明费率和清单都可能已变。
- 结算风险：底层市场按 AP/Fox/NBC 等源结算；若三家不一致，按就职人结算；结算延迟、争议、规则解释都会影响兑付。
- 本金风险：若只持单边，价格下跌会亏损，奖励远不足以覆盖；若持同条件YES+NO完整集，正常结算时理论兑付$1/对，但实际入场价与费用可能超过1；持到2027/2028只是路径选择，提前卖出/merge的流动性和成本仍未知，平台/Treasury可改变奖励。
- 费用风险：taker 入场费在 p=0.5 时一对约 2%，加价差后可能吃掉约一年奖励；maker成交、Split/merge都是待核路径，不能声称可把实际入场成本降到接近0。
- 平台/资产风险：Treasury 补贴、奖励币种、支付地址、平台运营和稳定币/托管风险；帮助页未写奖励币种和最低支付。
- 数据风险：没有逐钱包历史到账，无法验证 3.25% 是否真实支付；没有历史资格清单，无法证明当前 18 个是历史最大或最小。
- 美国站/global 混用风险：本文只用 global help 文；不把 `polymarket.us` 的 Rewards 规则迁移到 global，也不把 global 的 3.25% 当成美国站费率。
- 流动性/退出风险：合格事件多为长周期政治/地缘市场，盘口可能变薄；提前退出可能吃价差，持有到期则占用资金。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：满足 — 帮助页给出付款方（Treasury）、计奖基数（YES/NO 股数×最近 mid-price）、小时抽样/日发放和 3.25% 页面值；机制清楚，但今日费率未核实。
2. 有免费数据能检验：不确定 — 帮助页、Gamma、CLOB、data-api 都免费免密钥；但逐钱包历史到账、历史资格清单、实际费率变更缺失，无法做完整历史检验。
3. 小资金能做：不确定 — orderMinSize=5是5份，tick0.001只是示例配置；2,500为含费设计预算，当前资格、实际深度、价差、动态上限与退出尚未验证。
4. 不重复：不确定 — 与 C32 的报价奖励不同：本条按持仓价值拿 Treasury 补贴，不要求挂单或成交；仅保留已有C33认领，不新增机制计数，完整查重待主审确认。
5. 扣成本后粗算够用：不确定 — 3.25%仅旧页面条件，当前资格/到账冲突未解；完整集ask和两腿费、初始现金与总资本分母已分开，退出/merge未知，未证费后足够。
6. 两周内能检验：不确定 — 旧页面18个仅候选，非全历史/当前上限；同事件跨日是一簇，共同驱动仍须聚类；前向未启动、30个独立有效结果未取得，不能声称所有路径不可能。
7. 出处可查：不确定（部分完成）— 帮助页、docs 别名、Gamma、fees 均有 URL/访问日期/位置；3.25% 与 4.00% 的版本冲突明示；二手内容标摘要，未冒充正文。

## 出处

- https://help.polymarket.com/en/articles/13364459-holding-rewards — 访问 2026-10-19 — 已读（原研究；What are we doing、Reward Rate and Conditions、Total Position Value、Example、Eligible Events；`dateModified=2026-06-01T13:58:20Z`）
- https://docs.polymarket.com/polymarket-learn/trading/holding-rewards — 访问 2026-10-19 — 已读（原研究；webfetch 返回同一 help 文，3.25%/18 事件）
- https://gamma-api.polymarket.com/events?slug=presidential-election-winner-2028 — 访问 2026-10-19T17:42Z — 已读（原研究；`holdingRewardsEnabled`、`feeSchedule`、`clobRewards`、`endDate`、`outcomePrices`）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-19 — 已读（原研究；Fee Structure、Fee Tables、Fee Precision）
- https://polyscalping.org/leaderboard/yield — 访问 2026-10-19 — 摘要（搜索结果，未打开正文；二手，3.25%/Treasury/pUSD/Split 说法均未核实）
- https://x.com/graviahq/article/2093332229044977863 — 访问 2026-10-19 — 摘要（搜索结果，未打开正文；二手，2026-07 holding $0.4M 未核实）
- https://polymarket.com/api/rewards/markets/current — 访问 2026-10-19 — 已尝试，404，不作为数据源
