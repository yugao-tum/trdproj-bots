---
id: dot-032
name_zh: Polymarket报价奖励
name_en: Polymarket Liquidity Rewards (Q-score)
bot: dot
date: 2026-10-19
market: polymarket
pm_category: cross
kind: supplement
improves: M-M4-poly-rewards
category: M
return_type: service
instruments: Polymarket 二元市场双边限价单（奖励市场模板）
venues: Polymarket
data: 官方奖励规则页、Gamma rewards/clobRewards 字段、CLOB 盘口、data-api 成交；免费免密钥；历史逐钱包奖励份额与历史 L2 缺失
test_2w: 前向仅为拟定2026-10-19起点的未启动计划；独立结果按canonical event clusters计，同事件跨日/多市场一簇，30未知；净PnL=(实际现金+库存市值)期末减期初减外部净入金，奖励/费入账后不重复加减；事件簇中位≤0为筛失败，支付阈值按实际范围核实
status: 草稿
confidence: 中
---

整理说明：本稿为已保存证据的操作员侧校订；无新增抓取、交易或回测。未运行的采集与验证仍为计划。

## 一句话

在 Polymarket 有奖励池的二元市场，按官方 Q-score 规则在中间价附近挂双边限价单；不主动预测方向但成交库存仍有方向敞口，拟用每日奖励份额覆盖库存与逆向选择，奖励按 UTC 日发放。

## 钱从哪里来

Polymarket 的流动性奖励预算。平台为“可成交的深度和更紧的价差”付费，付款方是平台激励预算，不是对手方亏损。只要平台继续用奖励换深度，付款动机就存在；但单个市场的池子、最高价差、最低股数和奖励期间都由平台逐市场设置，可以调整或结束。政治类示例把taker费用的25%划入maker返佣池，再按资格和分配规则分给maker；不是每个maker固定拿到相关taker费用的25%，但本条只把返佣当次要项，不把返佣当主要收益来源。

## 规则

- 资格：在奖励市场挂 resting limit order；每个市场有自己的 `rewardsMinSize`（最低合格股数）和 `rewardsMaxSpread`（离中间价的最大美分距离），并有 `clobRewards` 的每日预算与起止日期。官方文档说最低奖励支付为 **$1**，低于 $1 不支付；但未说明 $1 是按市场/地址/日总额合并，不能当普适门槛。
- 计分：订单得分 `S(v,s)=((v-s)/v)^2·b`，其中 `v` 是市场最大价差、`s` 是订单离“按最低股数调整后的中间价”的价差、`b` 是比赛内乘数。`Q_one` 与 `Q_two` 分别按 YES/NO 两侧及互补市场汇总；`Q_min` 在中间价位于 `[0.10,0.90]` 时取 `max(min(Q_one,Q_two), max(Q_one/c,Q_two/c))`，单边报价按 `c=3.0` 打折；中间价在 `[0,0.10)` 或 `(0.90,1.0]` 时必须双边才计分。
- 归一化：`Q_normal=Q_min/ΣQ_min`；一个 epoch 是一个 UTC 日，订单簿每分钟随机偏移采样一次，最多 1,440 个样本；`Q_epoch=ΣQ_normal`；`Q_final=Q_epoch/ΣQ_epoch`；某交易者奖励 = `Q_final × 该市场可用奖励`。
- 付款时点：官方文档写“daily at midnight UTC”，直接付给 maker 地址；最低 $1。实际到账、地址格式和链上转账未在本条核实。
- 本版纸面报价只用YES/NO双bid、各自调整后mid减1¢、每侧最多50份；不同时混入YES买卖双边版本。必须满足当时rewardsMinSize/MaxSpread与实际tick，参数不合格则跳过。库存和挂单潜在成交不能超过各侧50份；任何卖单都需已有对应库存，禁止裸卖。撤单、平仓和部分成交按真实延迟与可见价模拟，吃单费另计，不假设maker减仓必能成交。
- 仓位上限是每outcome库存加潜在新增成交≤50份（最多50对完整集），并非两侧总共50份；现金、买单冻结资金、持仓和费用预留不得重复计，单场所总预算≤2,500 USDT、总资金5,000。严格动态上限下市值/奖励增长可能要求减仓或提现，其成本/可行性未核须报告超限，不能保证上限始终满足。
- 当前状态：官方文档明确说 2026 年 8 月的 crypto 5 分钟/15 分钟/4 小时 TWAP 奖励“This program has ended. The August allocation is no longer active.” 因此不能把 8 月那 $1M 配置当作今日池子；本文示例改用 2026-10-19 Gamma 快照中仍有 `clobRewards` 的政治市场。
- 美国站不迁移：搜索摘要另见 `polymarket.us/rewards` 的 Liquidity Incentive Program，使用 discount factor、target size 等另一套参数；本文只引 global 的 docs/Gamma，不把美国站规则搬到 global。

### 示例市场、规则源、时间日界、舍入与缺测

- 示例市场 1：`will-jd-vance-win-the-2028-us-presidential-election`（market id 561229）。2026-10-19T17:42Z Gamma 快照：`rewardsMinSize=50`、`rewardsMaxSpread=5.5`、`clobRewards[0].rewardsDailyRate=42`、`startDate=2026-10-19`、`endDate=2500-12-31`、`outcomePrices=["0.2005","0.7995"]`、`orderPriceMinTickSize=0.001`、`orderMinSize=5`（5 份，不是 5 美元）。同日 `rewardsAmount=0`，与 `rewardsDailyRate=42` 的关系未核。
- 示例市场 2：`will-gavin-newsom-win-the-2028-us-presidential-election`（market id 561230），同快照 `rewardsDailyRate=11`、`startDate=2026-10-17`、`rewardsMinSize=50`、`rewardsMaxSpread=5.5`。
- 示例市场 3：`will-alexandria-ocasio-cortez-win-the-2028-us-presidential-election`（market id 561231），同快照 `rewardsDailyRate=22`、`startDate=2026-10-19`。
- 规则源：上述市场属于 event `presidential-election-winner-2028`；Gamma 快照显示该 event 有 128 个市场、`negRisk=true`、`restricted=true`，128 个市场都 `holdingRewardsEnabled=true`。本条只用其中 5 个有 `clobRewards` 的市场做报价奖励示例，不把持有奖励混进本条。
- 结算规则示例（只作底层市场风险，不用于报价方向）：JD Vance 市场写明由 Associated Press、Fox News、NBC 三家共同判定；三家都叫同一候选人时结算；到 2029-01-20 就职日仍未三家一致，则按“谁就职”结算。市场 `endDate=2028-11-08T04:59:00Z`（按 EST 约为 2028-11-07 23:59）。
- 时间日界：奖励 epoch 是 UTC 日；每分钟随机偏移采样一次，最多 1,440 次；每日午夜 UTC 支付。随机偏移的具体实现未公开。
- 舍入：PM 交易费四舍五入到 5 位小数，最小 0.00001 USDC；流动性奖励最低支付 $1。Q-score 本身是否舍入、奖励金额是否按美分/地址舍入，文档未写。
- 缺测：逐钱包历史奖励份额、真实成交/库存路径、竞争者的 Q_min、当前全平台奖励市场清单、实际链上支付均未取得。`https://polymarket.com/api/rewards/markets/current` 在 2026-10-19 返回 404，不能据此枚举全平台当前池。

## 证据

- 原研究 已读 `docs.polymarket.com/programs/liquidity-rewards`：Q-score 公式、`c=3.0`、UTC 日 epoch、每分钟随机采样、最多 1,440 样本、每日午夜 UTC 支付、$1 最低支付、8 月 crypto TWAP 奖励已结束。以上是官方规则原文，不是收益实测。
- 原研究 已读 `docs.polymarket.com/market-data/market-details`：`rewardsMinSize` 单位为股、`rewardsMaxSpread` 单位为美分、`clobRewards` 含 `rewardsDailyRate/startDate/endDate`；这些字段是 Gamma 可读的逐市场配置。
- 原研究 已读 Gamma `events?slug=presidential-election-winner-2028` 快照（对象 `updatedAt=2026-10-19T17:42:58Z`）：5 个市场有 `clobRewards`，日率分别为 42、11、22、11、14 USDC；示例见上。来源自报的字段值，未用成交或链上支付复现。
- 原研究 已读 `docs.polymarket.com/trading/fees`：费用公式 `fee=C×feeRate×p×(1-p)`，maker 不收费，政治类 `rate=0.04`、25%为按资格分配的maker返佣池比例，费用按 5 位小数舍入、最小 0.00001 USDC。未重开其他市场的费用请求，不把任何既有市场清单当本次新证据。
- X 检索（`site:x.com Polymarket liquidity rewards Q-score holding rewards`，2026-10-19，摘要）：Gravia 文章摘要称 2026 年 7 月 liquidity rewards $12.9M、其中 7 月 7 日 $9.4M、holding $0.4M；这是二手摘要，未打开正文，未核实，不能当作本策略收益。另有 Poly_VPN 摘要称 2026 年 4 月 sports 有 $5M 奖励，属历史campaign，不是今日池。
- 未做完整盈利回测：`observed_net_return=null`；Sharpe=未知；最大回撤=未知；`backtest_count=0`（只表示没有完整盈利回测，不表示收益为 0）。本文是规则/费用/数据筛查，不是收益证明。

## 数据

- Gamma：`https://gamma-api.polymarket.com/events?slug=presidential-election-winner-2028`；免费、免密钥；返回市场、`rewardsMinSize`、`rewardsMaxSpread`、`clobRewards`、`feeSchedule`、`holdingRewardsEnabled`、`endDate` 等。上述updatedAt只是对象更新时间，不证明各字段/盘口的同步生成时间。
- CLOB：`https://clob.polymarket.com/` 的公开 book/price 接口；免费、免密钥；本轮未取得免费免密钥历史可执行L2；前向记录仅为未启动计划。
- data-api：`https://data-api.polymarket.com/trades?market=<conditionId>`；免费、免密钥；每个市场约最近 2 万笔成交，适合做 forward 成交/库存核对，不足以重建完整历史 L2。
- 官方文档：`https://docs.polymarket.com/programs/liquidity-rewards`、`https://docs.polymarket.com/market-data/market-details`、`https://docs.polymarket.com/trading/fees`；免费。
- 缺失：逐钱包奖励支付、历史 Q_final/份额、竞争者深度、库存路径、全平台当前奖励市场清单。链上奖励转账理论上公开，但本条未取，不能写成已有数据。

## 两周内怎么检验

- 计划未启动，2026-10-19只是原拟定起点，实际以首次记录为准。v1固定YES/NO双bid各自调整后mid−1¢，每侧挂单与既有库存合计≤50份；示例v=5.5¢，真实市场配置不同须先核是否合格。YES/NO各自mid不混同一数值；全部现金/库存及费预留受2,500含费预算约束。其他spread/卖单形式不混入主结果。
- 每天记录 `rewardsDailyRate`、`rewardsMinSize`、`rewardsMaxSpread`、中间价、冻结报价、CLOB 可见深度、成交、库存盯市和当日奖励；以上是采集计划，本轮没有执行。
- 独立结果按 canonical event cluster 计，不按“事件-日”、不按市场数：同一 event 的多个候选人市场、同一 event 跨多日，都只算一簇；当前快照只验证 1 个 event，能否在两周内得到 30 个独立簇未知，不能写成已有 30 个。
- 失败标准（预先写死）：有效独立事件簇中位净PnL≤0。主账本净PnL=(实际现金+按统一规则估值的库存)期末−期初−外部净入金；实际现金已含奖励、成交收入及费用，不再次加奖励或减费。若用分解账本，须明确交易现金为未含奖励/费的毛现金，再加库存变动+奖励−费；两套口径仅选一种。价差已在成交现金/库存中体现，不再单列重复相加或扣正MTM。次级条件：若某地址在某单池的当日应得单独结算且确认<$1不付，记该池失败；官方未说明$1是按市场/地址/日总额，故不把$1当普适门槛。
- 如果两周内凑不够 30 个独立簇，只能记为 forward 观察，不冒充 30 个结果；历史 L2 缺失，不能做完整历史回测。

## 成本与容量

- maker零费不代表执行零成本。PM总费F=C×r×A×(1−A)，每份f=F/C=r×A×(1−A)，A为实际成交价；F/(C×A)=r×(1−A)是名义本金比例，不与每份价格差混减。政治类示例 `rate=0.04`：p=0.50 时每份费 $0.01，名义 $0.50，费/名义=2.0%；p=0.20 时每份费 $0.0064，名义 $0.20，费/名义=3.2%。本文不套用 crypto 的“单边 0.30%/压力 0.60%”，因为这是 PM，费用和分母不同。
- 价差/滑点/成交（以下只作敏感性，主检验冻结 s=1c）：报价离中间价越远，`S` 按平方下降。以 `v=5.5c` 为例，令b=1作算术示例，`s=1c` 时 `S≈0.669`，`s=2c` 时 `S=0.405`，`s=3c` 时 `S=0.207`，`s=5.5c` 时为 0；越紧越有分，但成交和逆向选择越多。本轮未取得历史L2；未来纸面成交不能只看到交易print就假定己方成交，还需队列与可见深度/延迟模型，均未验证。
- 资金与腿的定义：50 股 @0.20 的 YES 买单现金约 $10。若同时挂 YES 卖单，卖单必须有 50 股 YES 库存（或等值完整集/铸造来源），不能裸卖；买单一腿现金约 $10 + 已有 YES 库存约 $10，合计占用约 $20，但库存来源、建仓成本和费用要另计。若采用 YES/NO 双 bid（两者都是买单），50 股 YES @0.20 加 50 股 NO @0.80 约 $50，不产生裸卖；这些是资金组成示例，非本版已成交价格；本版mid分别0.20/0.80且各减0.01时，双bid分别0.19/0.79，50份各侧最多冻结$49，另预留库存退出费用/损失。
- 池子规模：示例 5 个市场日率合计 $100/日（42+11+22+11+14），单个池 $11–42/日。若某地址在某单池的当日应得单独结算、且没有其他池合并到 $1，则 $42 池需 Q_final≥1/42≈2.38095%、$11 池需≥1/11≈9.09091% 才达到 $1；官方未说明 $1 是按市场/地址/日总额，故这是条件算术，不是普适门槛或预测。
- 机会频率：当前快照只看到 1 个 event 的 5 个奖励市场；全平台奖励市场清单缺失，不能给“每月多少次”的可靠数字。7 月 $12.9M 的月度总量是二手摘要，且含一次性大额日，不能外推。

## 风险

- 逆向选择：报价被成交时，价格往往正朝不利于库存的方向走；奖励可能不够覆盖库存亏损。
- 竞争稀释：Q_final 是相对份额，其他 maker 加大报价或收紧价差会稀释收益；小池子还可能因低于 $1 而不支付。
- 池子变化：奖励预算、`rewardsMinSize`、`rewardsMaxSpread` 和起止日期都可变；8 月 crypto TWAP 已结束，说明 campaign 会停。
- 运营：随机分钟采样要求报价持续在线；撤单/重挂、断线、延迟都会漏采样。
- 数据：没有历史 L2 和逐钱包奖励支付，不能回测；只能 forward。
- 平台/地域：示例 event `restricted=true`；本条不讨论地区合规，只记录字段。美国站规则不同，未迁移。
- 费用： maker 费为 0，但库存退出可能吃单；吃单费在 p=0.5 时可达名义的 2%，会吞掉薄奖励。
- 一次性偏差：7 月 7 日 $9.4M 流动性奖励是二手摘要中的一次性结算日，不能当作稳定日收益。

## 改进了什么

本条改按 `kind: supplement`，`improves: M-M4-poly-rewards` 归类。分类依据是 [known 中的 M-M4-poly-rewards](https://github.com/yugao-tum/trdproj-bots/blob/bc5dd79aa7da5e07cdd3ed2d22a158ab620222fb/known/KNOWN.md#L60)（2026-10-20 UTC 核对，仅含名称，不含既有规则或绩效）。预测市场挂单领奖励，Q-score/净库存会计为实现与证据。

本条提供的研究补充：整理 Q-score、奖励门槛、双 bid/库存预算与净现金会计；真实逐钱包奖励份额、队列、成交和库存损益仍未取得。

补充材料相对既有实现的新增性与采纳价值仍待核；本次不主张新机制、已证改进、盈利或已采纳，状态保持草稿。

## 门槛自查

1. 机制说得清：满足 — 官方文档给出 Q-score 公式、UTC 日采样、每日支付和 $1 最低支付；付款方是平台奖励预算。这里只证明机制清楚，不证明盈利。
2. 有免费数据能检验：不确定 — 规则和当前 Gamma 配置免费可读，但历史逐钱包奖励份额、真实成交/库存、历史 L2 缺失；只能 forward 记录。
3. 小资金能做：不确定 — 50份是份数门槛，YES/NO实际买价不同；双bid预算与库存来源已区分，但深度、动态场所上限、队列和退出路径未验证，不能说2,500必定足够。
4. 不重复：同机制补充，非新策略——对应 `M-M4-poly-rewards`；补充材料的新增性与采纳价值仍待核，不据 dot 内部区别主张全局新颖性。
5. 扣成本后粗算够用：不确定 — 没有完整回测；当前单池 $11–42/日，maker 费为 0 但逆向选择和库存损失未知；`observed_net_return=null`，不能写正收益。
6. 两周内能检验：不确定 — 前向未启动；按canonical event clusters计数，同一事件跨日仍只一簇，共同驱动事件还需合并；当前只验证1个event，30独立簇与真实奖励/库存结果未取得。
7. 出处可查：不确定（部分完成）— 每个规则数字有 URL、访问日期和页面位置；X 内容只标摘要；实际奖励、支付阈值归并范围、成交队列和库存路径证据仍缺。

## 出处

- https://docs.polymarket.com/programs/liquidity-rewards — 访问 2026-10-19 — 已读（原研究；Methodology、Equations、Crypto TWAP Rewards、$1 最低支付）
- https://docs.polymarket.com/market-data/market-details — 访问 2026-10-19 — 已读（原研究；Liquidity Reward Settings、Trading Fees）
- https://gamma-api.polymarket.com/events?slug=presidential-election-winner-2028 — 访问 2026-10-19T17:42Z — 已读（原研究；event 与 market 的 rewards/feeSchedule/endDate 字段）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-19 — 已读（原研究；Fee Structure、Fee Tables、Fee Precision）
- https://x.com/graviahq/article/2093332229044977863 — 访问 2026-10-19 — 摘要（搜索结果，未打开正文；二手，来源自报，未核实）
- https://polymarket.com/api/rewards/markets/current — 访问 2026-10-19 — 已尝试，404，不作为数据源
- 费用采用上列已保存官方Fee Structure/Fee Precision正文；没有实际成交扣费回执，不以配置字段证明实际费用或奖励到账
