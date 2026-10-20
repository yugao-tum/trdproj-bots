# C26美元参照扩展与C38费用字段检查

2026-10-20 UTC；续跑中的既有机制补证。新增机制0、历史PnL模拟0、晋级0；上日40份研究草稿、6个历史PnL机制与50情景不变。已知机制的日期化重新分类见[续跑说明](20261020-continuation-and-known-crosswalk.md)。

## C26：取得一年美元报价，不等于取得一年可执行策略收益

DeepSeek分别读取Kraken公开免密钥USDC/USD、USDT/USD日频OHLC响应；dot用自编只读程序校验哈希、UTC日界、连续性、OHLC/VWAP、交易计数及阈值，另有独立原始数据复算。没有执行来源仓库代码。

初次请求返回各364个完整日和1个未完日。为纠正since的日界，随后固定since=1760832000（2025-10-19 00:00 UTC）各补读一次，原响应保留。两次扩展响应均有367行：2025-10-19至2026-10-19共366个完整UTC日，加2026-10-20未完成日；后者排除。连续日价格覆盖达到12个月，未见重复、缺日或OHLC/VWAP结构错误；与初次取得的364个完整日逐行一致。此结论只补足价格覆盖，G2整体仍未通过。

| 官方美元交易对 | 完整日 | 收盘≤0.99美元 | 日低≤0.99美元 | 日低严格<0.99美元 |
|---|---:|---:|---:|---:|
| USDC/USD | 366 | 0 | 0 | 0 |
| USDT/USD | 366 | 0 | 4 | 3 |

原规则是折价≥1%，所以观察边界对应≤0.99，不能漏掉等号。USDT四个日低分别为2025-12-11的0.98979、2026-01-08的0.99000、2026-02-03的0.97300、2026-02-04的0.96985美元。相邻两天不直接算两个独立冲击；四日也不等于四个可成交或合格事件。日低只证明数据源记录了该价格，不能假设可以买到日低，日内先后顺序和数量亦未获验证。收盘无触发不证明所有时间或场所无机会。

该USD报价补充了旧USDCUSDT相对报价的参照信息，不能把单一Kraken场所当作两个独立场所，也未补齐同步可成交盘口、第二场所执行腿、事件发生时的储备与赎回风险过滤。当前发行方透明度页面不可倒填历史偿付状态。没有生成交易、利润、年化或独立事件数。

来源与冻结指纹（2026-10-20 UTC；响应时间为工具完成时间）：

- [Kraken USDC/USD日线](https://api.kraken.com/0/public/OHLC?pair=USDCUSD&interval=1440&since=1760832000)，01:25:15.310，30,827字节，SHA256 `4408b875864869629b8dcb976bd1cd9b8296ce18df962c18aba2d1c2241dc1be`
- [Kraken USDT/USD日线](https://api.kraken.com/0/public/OHLC?pair=USDTZUSD&interval=1440&since=1760832000)，01:28:42.652，32,959字节，SHA256 `38cbbecee138465bbdd1b65050a998107b9e530049cb70003093a882c2a7547d`
- [原1300日相对报价核查](20261019-stablecoin-history-coverage.md)保持原冻结范围，未回写本次新数据

接口会随时间滚动；上述指纹限定本次保存响应，日后同URL不保证相同字节。完整原始数据保留本地，不随仓库发布。结构检查的6项合成测试和独立复核通过不构成策略回测。

## C38：finalFee列名不能直接当作纯手续费

本次读到UMA `packages/optimistic-oracle`的schema和完整`optimisticOracle.ts`映射源码。schema包含proposer、disputer、settlementPayout/Recipient和交易hash/logIndex；缺独立bond列不等于完全没有总押金信息。

映射源码实际赋值为：

1. `handleOptimisticRequestPrice`初设`finalFee = event.params.finalFee × 2`（第71行）
2. 非mainnet/goerli分支把它写为`requestData.finalFee + requestData.bond`（第85–95行）
3. `handleSetBond`再把它覆盖为`call.outputs.totalBond`（第243–259行）

因此该字段在这些分支表达的是不同来源的总量，不能按名称直接从用户收益里扣成一笔纯手续费。押金支出、返还本金、罚没与报酬仍须逐现金流核算一次。

`handleOptimisticSettle`把事件payout写入settlementPayout；无disputer或提议价格等于结算价格时recipient取proposer，否则取disputer（第218–230行）。这有助定位潜在支付，但这份映射没有完整ERC20 Transfer账本，不能将payout直接等同净利润，也不能据此证明全部历史数据已取得。

以上仅限所读取master版本的一个包：未核定具体部署/索引端点、未验证实际全量事件完整性，不能外推v2、managed包或Polymarket实际数据提供者。没有运行第三方源码。

- [schema源码](https://raw.githubusercontent.com/UMAprotocol/subgraphs/master/packages/optimistic-oracle/schema.graphql)，2026-10-20 01:11:26.960 UTC，1,059字节，SHA256 `fc32b396051be24ece99ec1c9c754e84cbbe58bb40ecad1594a9e7b2123d7357`
- [mapping源码](https://raw.githubusercontent.com/UMAprotocol/subgraphs/master/packages/optimistic-oracle/src/mappings/optimisticOracle.ts)，2026-10-20 01:26:47.350 UTC，7,991字节，SHA256 `2cb417db2a0444a6c9c15d1c038665875afdd61d9213c690954e73262d013651`

这些URL指向可变分支，上述哈希限定读取样本；尚未把此样本绑定不可变commit。后续优先核请求键构造、部署范围和逐事件转账，保留全部净收益未知。
