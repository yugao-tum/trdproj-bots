# C44补充：真实兑付回执与历史会计状态

2026-10-19 UTC，新增策略/回测/独立投资结果均为0。本次核查的是此前已经列出的同一笔混合兑付交易，不增加样本数。

## 得到的证据

[原交易](https://etherscan.io/tx/0x72ad19d8140ddbe613f4500591f6d8b87a314e07ba132c62370fbaffffd7e8bb#eventlog)现已取得公开Ethereum RPC原始回执及区块头：区块21,483,431，2024-12-26 01:42:59 UTC，状态成功。回执20条日志中，321/327/331的LP移除、PT→SY和SY→eUSD整数，与此前浏览器证据一致；交易总gas仍为348,700，实际gas价5,205,766,145 wei，总计0.0018152506547615 ETH，不能全部归给独立单买PT。

在同一历史区块的结束状态，只读接口返回：

- SY.exchangeRate、YT.pyIndexStored、getPostExpiryData的firstPYIndex均为1,072,305,936,185,707,886，缩放1e18
- SY.assetInfo返回TOKEN类型、eUSD地址0xdf3ac4f479375802a821f7b7b46cd7eb5e4262cc及18位小数；SY和PT也为18位
- YT返回的SY/PT地址与记录匹配；expiry为2024-12-26 00:00 UTC

这补上了一个历史截面的会计单位与水位，支持兑付单位为eUSD。它不把eUSD变成保证1美元的请求权，也不是全年历史水位。

## 整数换算检查

日志中19,545,233,536,565,027,509,596个PT最小单位，按该水位向下取整换成18,227,292,115,988,133,094,911个SY最小单位，与真实Burn日志精确一致。

同笔混合LP/PT共22,885,093,584,778,994,632,917个SY最小单位，实际得到24,539,821,701,123,977,557,323个eUSD最小单位。直接乘已截断至1e18精度的exchangeRate再向下取整，会少13,793个eUSD最小单位（约1.3793e−14 eUSD）。该差在小于一个指数整数单位的换算误差界内，不能据此断言历史实现的具体舍入原因。

随后用相同历史区块、相同tokenOut及完整SY数量调用previewRedeem，结果与真实日志输出精确一致。[官方接口说明](https://docs.pendle.finance/pendle-v2-dev/Contracts/StandardizedYield)将preview明确限定为链下估算；本例匹配不代表任何其他日期、数量或资金状态都能成交。

## 仍然没有证明的事项

- 历史eth_call采用整个区块执行完后的状态，不能代表本交易执行前/中间状态；本次没有交易重放或状态证明
- 数据来自单一公开RPC，与此前索引/浏览器佐证一致，未完成独立节点共识或历史部署字节码等价验证
- 该交易同时包含LP退出、PT赎回和奖励。数量守恒不提供单买PT的入场价、独立gas、真实换回USDT或自有资本收益
- 仍只有原来的一个到期交易；没有补成30独立结果，也没有把933日价格点改叫收益样本

13次串行只读请求全成功，保留请求/响应原始字节、时间和SHA；没有交易或外部代码执行。当前[YT源码](https://github.com/pendle-finance/pendle-core-v2-public/blob/87685c89d05087535e9b9647eeda0e3d297d1f06/contracts/core/YieldContracts/PendleYieldToken.sol)只用于解释接口和整数关系，未当作2024年部署代码已验证。原始回执与历史响应不入仓库。

## 证据指纹

- 抽取前固定对象/问题：`b354d370b569d33510a2dd3a06c08b73eac4eeadf49851adaee9a377a591f114`
- 原始RPC回执：`96e4183ee8cffd3862b4a6a48129f1292d8ce2ea60ec10b8f4b09b9606582dfb`
- 原始区块头：`ffde7cbabea04875c2c4cdc78ca88f7f543b3d201aaf6ccbe20f6f92b2c3ff65`
- 全部历史调用整理：`e4c6a38e9735bf774c5c4ff016c796331d955df57d0e37e462401e101fb667ea`
- 换算核对结果：`6df94ee7a92586fe619cf2721ac033fea88947a4cf77287a5ebdc140b42007e7`

此前较大样本/单位背景见[两市场历史与到期佐证](20261019-principal-token-history-evidence.md)。
