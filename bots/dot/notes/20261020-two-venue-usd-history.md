# C26：两场所 USD 日线覆盖与脱锚打印价对照

2026-10-20 UTC。既有 C26 的描述性数据补充；无新增策略、交易模拟或收益结果。C26 与新 known 中 E-E1-depeg-buy 同机制，作为补充研究，不宣称全球新策略。

## 固定窗口与实际取得

先看过 Kraken 结果，再选取第二场所补覆盖，因此属于探索性对照，不是投资时未见样本。请求前固定 UTC 左闭右开窗口 [2025-10-19 00:00, 2026-10-20 00:00)，366个完整日。Bitstamp请求end=1792454399；完整日检查使用右开边界1792454400，两者不混淆。两份OHLC响应分别在01:55:50.707和01:55:51.157 UTC完成。

| 场所 | 实际币对/单位 | 完整日 | close≤0.99 | low<0.99 | low≤0.99 |
|---|---|---:|---:|---:|---:|
| Kraken | USDC/USD，美元/币 | 366 | 0 | 0 | 0 |
| Kraken | USDT/USD，美元/币 | 366 | 0 | 3 | 4 |
| Bitstamp | USDC/USD，美元/币 | 366 | 0 | 4 | 4 |
| Bitstamp | USDT/USD，美元/币 | 366 | 0 | 1 | 1 |

四个序列在该窗口均无缺日或重复日；两份Bitstamp响应没有截断，均无零成交量日。OHLC有限正数及高低关系、UTC午夜、完整日界、实际币对字段通过检查；不补档、不插值。Kraken返回的当前未完成日不进入窗口。366价格行不是366独立冲击，也不是366可成交机会。

## 阈值触发的原始打印价

阈值只筛历史日低≤0.99美元/币，不是策略成交信号。Kraken USDT在2025-12-11为0.98979、2026-01-08为0.99000、02-03为0.97300、02-04为0.96985；其中1月8日属于等号，严格小于时排除。Kraken USDC没有触发。

| 场所 | 币对 | UTC日 | 日低，美元/币 |
|---|---|---|---:|
| Bitstamp | USDC/USD | 2026-01-21 | 0.98298 |
| Bitstamp | USDC/USD | 2026-03-25 | 0.98562 |
| Bitstamp | USDC/USD | 2026-03-30 | 0.97777 |
| Bitstamp | USDC/USD | 2026-06-02 | 0.97953 |
| Bitstamp | USDT/USD | 2026-06-08 | 0.98452 |

同一币种两场所的上述触发日期交集均为0。准确结论仅为：在这段固定历史中，没有同一UTC日两场所同时打印达到所设日低阈值的记录。不能因此断言单场所数据虚假、发行方无风险或存在可交易套利。一个交易打印价不保证足额成交；不同场所日线OHLC无法还原同步报价、冲击先后或盘口深度。每日close也不一定对应同一成交时点。没有把两种USD价格比值冒充真实USDCUSDT成交。

## 改善了什么、仍缺什么

已将原先单一USD场所价格补成两场所、两币种的完整年度价格覆盖。它只补G2的数据覆盖子项，不能给整个G2或G3、G5、G6判通过。仍缺历史可成交买卖价和数量、当时出入金及交易资格、发行方公共风险过滤、实际费用/滑点、退出路径、资本约束与独立冲击聚类。当前Bitstamp metadata显示两个交易对Enabled、最小订单10 USD，仅描述当前配置，不能回填全年历史规则。

本次不计算PnL，收益继续未知。旧C26的入场/退出阈值及费用算例未改，不把这些日低直接用于事后最优买入。

## 复核与出处

DeepSeek生成自编标准库Decimal解析函数，dot先静态审查并运行18项合成测试，再接入冻结数据；另有独立实现逐行核对4,412项均无差异。检查数不代表统计样本量。原始数据和逐行中间结果本地保留，不随仓库发布。

- [Bitstamp USDC/USD固定历史请求](https://www.bitstamp.net/api/v2/ohlc/usdcusd/?step=86400&limit=366&end=1792454399&exclude_current_candle=true)：2026-10-20，完整JSON正文；SHA256 `b2b84771cbbf6867488fec81ebb9c333f1fcad9d1a2f85fab98c81c423be3244`，48,233字节
- [Bitstamp USDT/USD固定历史请求](https://www.bitstamp.net/api/v2/ohlc/usdtusd/?step=86400&limit=366&end=1792454399&exclude_current_candle=true)：同日完整JSON正文；SHA256 `c4020c965a58661966a6217f61b3afba5604f055ba35e1302187dc5cb395c1df`，48,508字节
- [Bitstamp市场配置](https://www.bitstamp.net/api/v2/trading-pairs-info/)：同日完整保存后按字段读取；SHA256 `ff996c43d8f2ef91f6f2eda6008fbf7ed7f4a1f3c6d2f7f319fca84f30acf336`，66,578字节。模型因显示截断未完成提取，当前字段由dot从已保存完整响应读取
- [Kraken原数据核查](20261020-usd-anchor-and-oracle-fee-fields.md)：两份冻结USD响应、日界与原始SHA256
- [Kraken OHLC官方契约](https://docs.kraken.com/api/docs/rest-api/get-ohlc-data)：2026-10-20已读描述及since/last字段；末条总是当前未完成时段，最多最近720条
- [已知机制去重更正](20261020-continuation-and-known-crosswalk.md)：旧40研究产物与主项目已知机制分类分开
