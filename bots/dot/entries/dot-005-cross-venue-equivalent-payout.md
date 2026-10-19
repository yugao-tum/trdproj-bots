---
id: dot-005
name_zh: 跨场等价命题支付映射
name_en: Cross-venue equivalent-proposition payout mapping
bot: dot
date: 2026-10-19
market: polymarket
pm_category: economics
kind: new
improves: -
category: A
return_type: convergence
instruments: Polymarket FOMC分档 + Kalshi KXFED阈值合约
venues: Polymarket, Kalshi
data: Polymarket Gamma与Kalshi公共市场API已有免密钥读取记录；FOMC规则/报价为留存快照，同步性和可执行性未证；历史同步深度、Kalshi费率与实际扣费缺失
test_2w: 拟从2026-10-19前向记录，未证明连续采集已启动；按FOMC会议/CPI发布事件聚类，当前方案缺30个可用独立exact对；费后均值≤0或支付不等价导致损失为失败
status: 草稿
confidence: 低
---

## 一句话

研究逐条结算规则和所有结局都等价的Polymarket/Kalshi命题，假设可按相同支付单位买入互补结果且总成本低于共同支付额，再持有到结算。当前FOMC样本仅为条件映射，未验证exact对或同步可执行价。

## 钱从哪里来

机制假设是两场订单簿、参与者与资金池分割可能留下报价差，跨场参与者承担连接及非原子执行风险。存在不同报价不等于可锁定利润；需要证明所有普通及异常结局、支付单位、费用和成交条件都匹配。来源将同事件称作无风险价差，但其措辞不能替代合约核对。

## 规则

| 场所/样本 | slug/ticker | 留存规则要点 | 时间字段与缺口 |
|---|---|---|---|
| Polymarket FOMC | fed-decision-in-october-20260617190323537 | 按目标区间上沿相对2026年10月会议前的变动分档；未列出的变动向上取整至25bp，原文以12.5bp作为25bp为例；结算源为FOMC声明；到下一次例会结束仍无声明则“No change” | description写2026-10-27/28会议；endDate=2026-10-29 03:59 UTC，仅为对象字段，不证明可以交易到该时刻；5档与rate=0.05来自留存Gamma |
| Kalshi FOMC | KXFED-26OCT-T4.00 | Fed官网公布的该次会议后目标上沿大于4.00%则Yes；每份名义支付1美元 | close_time=2026-10-28 17:55 UTC；expected_expiration_time=18:05 UTC；expiration_time=2026-11-04 18:05 UTC；rules_secondary写声明后首个2:05 PM ET或会议最后一天后一周到期，缺数据的支付fallback未取得 |
| Polymarket CPI反例 | core-cpi-yoy-september-2026 | BLS核心CPI-U同比、未季调、一位小数；若延期，可等到下一次CPI发布，仍缺数据则用最近有数据月份 | description写2026-10-14 08:30 ET；endDate=2026-10-15 03:59 UTC；closedTime=2026-10-14 14:33:42 UTC；10档已收盘，仅作精度/缺测规则样本，未找到Kalshi对应合约 |

- 条件映射：假设会前目标上沿恰为4.00%，且两场使用相同的会后有效数值，Kalshi T4.00 YES的候选集合为PM{25bp increase, 50+ increase}，NO候选集合为PM{No change, 25bp decrease, 50+ decrease}。会前上沿未从Fed官网核实；价格不能证明它为4.00%。任一假设或异常结算规则未核齐，都不能标为exact。
- 单腿反例：PM“25bp increase”不等于Kalshi YES；在50+ increase结局，PM 25bp YES与Kalshi NO可同时不支付。因此不能只买该单档作跨场对冲，必须按共同支付单位核实完整集合。
- 边界仅作条件算例：在上述4.00%假设下，4.125%、4.00%、4.50%分别对应PM的25bp increase、No change、50+ increase及Kalshi的YES、NO、YES。这些算例不覆盖缺数据/声明延迟等结局，不能据此证明完整等价。
- 时间与fallback：Kalshi的close_time与两场结算时间不同，不能依赖声明后补腿；PM的endDate也不能证明实际可交易截止。Kalshi缺数据fallback未知，PM有无声明→No change规则，终局一致性未证。
- 拟议筛选：逐对记录事件、源、时间/时区、取整、全部结局、支付单位及异常处理；分类exact/conditional/rejected。只有exact且两场同一时点逐腿深度、费用和缓冲后的总成本低于共同支付，才通过研究筛选；当前样本为conditional。
- 拟议资金边界：总额约5000 USDT等值、每场所含费用与缓冲≤2500、单组合含费用与缓冲≤200；不加杠杆、不借款。两场资金计价/兑换路径、锁资与容量仍需核实；金额上限不等于实际可放入资金。
- 拟议退出：完整组合持有到结算；模拟一腿未成交/部分成交时的撤单与平仓成本，不能把紧急平仓假定为无损。当前仅只读研究，不下单。

## 证据

- tswaim仓库README（既有留存原文）自称同事件跨场可锁定价差；例子0.62+0.35=0.97，并自报Fed 2024年23次机会、平均净2.8%、1000美元约+38%；经济报告2024年47次、2.1%、+29%；美国选举2024年10–11月61次、3.4%、+52%；体育决赛2024年18次、4.1%、+44%。全部为来源自报，未核实；逐笔成本、样本独立性和资金占用没有在该表交代，不计作本研究回测。
- 同一README将PM费写成约交易额2%、Kalshi约每份0.07美元或百分比；不作为当前真实费率。既有官方PM费用审计采用C×r×p×(1−p)，Kalshi本次仍无官方费率/扣费证据。
- 留存PM FOMC的Gamma字段：No change bid/ask=0.84/0.85；25bp increase=0.14/0.15；25bp decrease=0.003/0.004；50+ increase=0.003/0.004；50+ decrease的ask=0.001；feeSchedule.rate=0.05。对象updatedAt为2026-10-19 17:48 UTC附近，未取得同步CLOB深度，不能把这些字段直接当成交证明。
- 留存Kalshi T4.00：YES bid/ask=0.15/0.16，NO bid/ask=0.84/0.85，YES ask size=248.69份、bid size=203.15份；对象updated_time=2026-09-30T18:52:10.746156Z。2026-10-19取得响应不等于报价新鲜；该字段也不能单独证明报价恰在9月30日形成。
- 条件静态算例A：Kalshi NO 0.85 + PM 25bp increase YES 0.15 + PM 50+ increase YES 0.004 = 1.004。以各腿一份、r=0.05自算，PM费用=0.006375+0.0001992=0.0065742，总额1.0105742，尚未计Kalshi费、滑点和实际舍入。
- 条件静态算例B：Kalshi YES 0.16 + PM No change YES 0.85 + PM 25bp decrease YES 0.004 + PM 50+ decrease YES 0.001 = 1.015。PM费用=0.006375+0.0001992+0.00004995=0.00662415，总额1.02162415，尚未计Kalshi费、滑点和实际舍入。
- 上述对象更新时间相隔约19天，报价同步性/新鲜度未证，且共同支付映射依赖未核假设。A/B仅是留存数字的静态算术，不能据此断言当前可套利或当前无套利；没有实际组合收益。
- 测量状态：backtest_count=0；observed_net_return=null；Sharpe=null；max_drawdown=null。未测收益未知，不是0；这是规则/费用/数据可行性草稿。

## 数据

- https://gamma-api.polymarket.com/public-search?q=Fed%20Decision%20in%20October%202026&limit_per_type=5 ：已有免密钥读取记录，含上述FOMC事件的description、时间、feeSchedule与bestBid/bestAsk字段；没有本策略所需的历史同步完整L2。
- https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=KXFED-26OCT ：已有免密钥读取记录，含T4.00规则、时间、价格和size；历史覆盖起点、报价新鲜度、实际可成交性与费用仍未知。
- CPI规则反例与BLS日历已留存，但对应Kalshi CPI合约未取得。公开历史价格与完整历史盘口不是同一种数据，不能将前者标为历史L2。
- 关键缺口：Fed会前上沿、两场完整异常结算映射、同步逐腿深度、Kalshi费率/实际扣费、资金计价与锁资、30个独立exact事件；当前不能建立可复现净收益数据集。

## 两周内怎么检验

- 拟议前向起点为2026-10-19，未证明连续采集已启动；同一FOMC所有strike/bucket/多次报价合为一个事件，同一CPI发布所有档和跨场配对也合为一个事件，不能按合约或报价条数充数。
- 既有FOMC规则样本指向2026-10-27/28；既有BLS日历的下一项为2026-11-10，晚于至2026-11-02的两周窗口。当前方案只列出这一场窗口内FOMC候选，尚未证实为exact；缺30个可用独立事件，不代表所有历史或其他前向路径都不可能。
- 拟议记录：逐候选审查映射，conditional/rejected不得计入有效exact样本；对合格事件留存同一时点逐腿ask、深度、费用、未成交/部分成交假设及实际结算。当前没有完成该记录。
- 拟议失败标准：至少30个合格独立事件的费后平均PnL≤0；或发现原本归为exact的组合在某结局支付不互补/产生单腿损失。样本或费用证据不足则结论未完成；不以两周观察直接推定盈利。

## 成本与容量

- PM费用：C份总费F=C×r×p×(1−p)，每份费F/C=r×p×(1−p)，费/该腿成交名义本金F/(C×p)=r×(1−p)。买NO时p取NO成交价。r须按各市场和成交时点取，历史费率不可用今日表回填。
- 自算示例r=0.05时，p=0.15/0.50/0.85的费/该腿成交名义本金为4.25%/2.50%/0.75%。组合应把各腿美元成本相加；除以单腿本金、整个组合投入或条件共同支付，是不同分母，不能混称收益率。
- Kalshi费率和实际扣费未知，README的每份0.07美元不代替官方费率。A/B静态数字已经列出，但没有同步报价、完整支付证明及全部成本，不能形成净收益结论。
- 容量：旧快照YES ask的248.69份对应248.69×0.16=39.7904美元的单腿名义额；它不等于整套组合可用金额。应按各腿共同份数和完整组合成本比较，不能直接拿200美元组合上限与约40美元单腿金额比较。PM各腿深度与新鲜快照缺失，因此实际容量未知。
- 200美元是研究单组合上限（原来源配置示例），不是实测容量；总额5000、每场所2500 USDT等值均含费与缓冲。每月合格exact机会、兑换成本和实际资金占用天数未知，不年化未知收益。

## 风险

- 规则不等价：变动分档与绝对阈值需要会前上沿和所有边界/异常结局一致；相似标题、单个25bp档或几个数值例子都不能证明exact。
- 异步/陈旧报价与时间字段误读：两场更新时间不同，元数据endDate不保证该时刻可交易，不能保证声明后可补腿。
- 非原子成交、部分成交、深度不足、手续费/兑换成本与锁资可能消耗静态价差；紧急平仓会产生损失。
- 平台/结算源、数据延迟、声明缺失及争议处理可能导致终局不同。全球站与美国站规则不能互相移用，来源的无风险措辞不是验证。

## 改进了什么

不适用。C08已合并进C05，本条保留一条跨场机制，不反向并回C08；不等价配对属于失败/排除样本，不能另计新策略。全库去重仍未完成。

## 门槛自查

1. 机制说得清：满足——报价分割和潜在付款方已说明；没有证明样本无风险或持续盈利
2. 有免费数据能检验：不确定——公开规则/快照已可读，历史同步深度、完整费用与独立exact结果缺失
3. 小资金能做：不确定——资金边界含费用与缓冲，但逐腿可匹配份数、资金路径与容量未核
4. 不重复：不确定——C08已合并，仅机制级初步去重，全库复核未完成
5. 扣成本后粗算够用：不确定——A/B为不同更新时间对象的条件静态算术，不是同步可执行组合，也非实测净收益
6. 两周内能检验：不确定——当前方案缺30个可用独立exact事件；历史/其他前向方案尚未穷尽
7. 出处可查：不确定——已有原文与位置可追溯，但会前上沿、完整fallback、Kalshi费用和同步执行证据缺失

## 出处

- https://raw.githubusercontent.com/tswaim/polymarket-kalshi-arbitrage-bot/main/README.md — 既有访问2026-10-19 UTC — 已读（留存原文，本次仅复核留存）；位置：The Core Idea、Configuration、Fee Structure Reference、Backtested Results、Important Risks；性能数均来源自报，未核实
- https://gamma-api.polymarket.com/public-search?q=Fed%20Decision%20in%20October%202026&limit_per_type=5 — 既有访问2026-10-19 UTC — 已读（留存接口原文，本次仅复核留存）；位置：上述FOMC事件description、markets、updatedAt、feeSchedule、bestBid/bestAsk
- https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=KXFED-26OCT — 既有访问2026-10-19 UTC — 已读（留存接口原文，本次仅复核留存）；位置：T4.00的rules_primary/rules_secondary、notional_value_dollars、updated_time、bid/ask、size与到期字段
- https://gamma-api.polymarket.com/events?slug=core-cpi-yoy-september-2026 — 既有访问2026-10-19 UTC — 已读（留存接口原文，本次仅复核留存）；位置：description、endDate、closedTime、markets；仅为CPI精度/缺测反例
- https://www.bls.gov/schedule/news_release/cpi.htm — 既有访问2026-10-19 UTC — 已读（留存官方日历，本次仅复核留存）；位置：Reference Month=October 2026、Release Date=Nov. 10, 2026
- https://docs.polymarket.com/trading/fees — 既有审计访问2026-10-19 UTC — 二手（引用既有费用审计，本次未复取原页）；位置：Fee Structure、Fee Precision；无实际扣费回执
