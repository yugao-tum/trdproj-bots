# dot-032 证据准备门槛：完成并停止启动

2026-10-21 04:31–04:33 UTC 完成一次有界来源核对。结论：STOP，数据/登记准备未通过；不是负收益回测、策略淘汰或正式前向结果。dot-032仍草稿，43条/10待核不变。本包关闭 b4e53bc6 中既有dot-032准备认领，不新增机制、PLAN或前向起点。发布前在 eb05c185b17181ad8a1e377ac9f87ac7aae9f0c5 重读规则与全部CLAIMS，muse库存优化/返佣收割仍进行中，本工作没有进入其策略优化范围。

## 核实的文档差异
当前[Market Details](https://docs.polymarket.com/market-data/market-details)将 orderMinSize 定义为USDC最小名义额，rewardsMinSize仍为奖励资格份数。旧缓存将前者5解释为5份而非5美元的断言不再沿用。这是文档口径冲突，不是实际撮合拒单测试。交易标识应按version选择v1的clobTokenIds或v2的positionIds，不能只看字段存在。

[公开订单簿文档](https://docs.polymarket.com/market-data/prices-order-books)提供价格层聚合数据、资产/时间/hash，没有逐maker归属。[Analytics](https://docs.polymarket.com/market-data/public-analytics)说明逐笔字段与分页；SDK/REST时间单位须分别核验，transaction_hash未证明是逐fill唯一键，side也未证明可直接作耗队列的吃单方向。本次没有实际盘口或逐笔请求，不能宣称实时链路可用，也不宣称旧接口已失效。

## 四项尚未闭合的条件
1. 当前奖励池、完整配置和canonical event映射未知，未验证≥30独立事件。旧同一总统事件下5市场不能当5独立事件，也不能跨日相乘。
2. 当前双outcome盘口、完整后续成交、稳定去重、方向语义、漏页恢复与延迟未验证。触价不算成交，撤单不算真实成交耗队列。
3. 奖励分母不能直接从聚合L2反推。[Liquidity Rewards](https://docs.polymarket.com/programs/liquidity-rewards)先逐maker非线性计算Q_min，再归一化；随机分钟采样和最低支付门槛还需可复核口径。代数示例：中间价格区间、c=3，两侧聚合分数各100；同一maker双侧时Q_min=100，两名maker各单侧时合计200/3。相同聚合深度可对应不同分母。这只证明这些聚合输入不足，不证明所有公开数据路线永远不可行；逐maker合格归属/Q、官方可核验份额或严格保守界有新证据时可重评。目前无可复核净正下界。
4. 一次认领推送成功不证明逐笔发布时序。决策、挂单行到达main及之后平/结算的链路未试验，不能先开始再补PLAN；每日推送也不自动满足开/挂早于平/结算。

## 精确失败与停止边界
对 [Gamma已文档化slug路径](https://gamma-api.polymarket.com/markets/slug/will-jd-vance-win-the-2028-us-presidential-election) 的单次公共读取，工具返回不可访问，没有HTTP状态或Retry-After。不是已知403/404，不能推出市场不存在或没有奖励。一个官方迁移文档链接同样不可访问；没有重试或绕路。

来源阶段共5次web调用、8次保守计数的读取选择（含一次已取页面展开），市场API成功0；保存工具响应文本105455字节，不是源站传输字节。发布只用已保存文档做核验，没有额外市场调用。原文访问日期2026-10-21，文档/响应不复制入仓库。

准备认领现已完成、结果为缺口补充；停止启动盈利前向。只有具体新证据补齐数据、独立性、奖励识别及发布条件才重开，不因预算用完机械续抓。不写 evidence: 前向、result: 正/负、observed profit或快速筛选通过；无模型、账户、钱包、交易、留存市场数据读取。官方分数仍待操作员裁决。
