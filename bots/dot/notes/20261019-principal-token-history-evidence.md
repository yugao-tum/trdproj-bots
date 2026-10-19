# dot-044：历史价格可得性与到期单位补核（2026-10-19 UTC）

数据证据补核；新增机制/回测均为 0，继续保留草稿。

官方免密钥 GET 已实取两条已到期市场日频数据：Ethereum eUSD 市场 0x23aefced9255ad3560cdaa4a10cbfe9ec230dc5a，472 行（2023-09-11–2024-12-25）；S*USDT 市场 0x30e0dc9a1d33eac83211a1113de238b3ce826950，461 行（2023-03-24–2024-06-26）。均超过 12 个月，价格/池字段无日频断档；两次查询均延伸到到期后，但返回只到到期前一天。三项费字段分别缺 311/472、221/461 行，其中 25、13 个缺费日有正交易量，不能补零。[S1–S3]

官方 schema 指 ptPrice、syPrice 为 USD 价格，tvl 为池内 USD 流动性；它们不是 SY.exchangeRate、PY 水位或指定金额的成交报价。历史价格的精确采样/可用时间和生成算法未核；日标签不能未经核对当作午夜已知值。[S1]

已读公开交易回执 0x72ad19…d7e8bb（block 21483431，2024-12-26 01:42:59 UTC）：Burn 日志 327 显示 19,545.233536565027509596 PT→18,227.292115988133094911 SY；同交易合并 LP 移除后，SY Redeem 日志 331 显示 22,885.093584778994632917 SY→24,539.821701123977557323 eUSD。交易总 gas 费 0.0018152506547615 ETH，但混有 LP/奖励，未显示换回 USDT，不能当单买 PT 的成本或收益。[S4]

特别注意：该市场到期前末日 ptPrice=0.9546928977 USD，不能据此算对“保证 1 USD”的折价。会计资产是 eUSD，到期索引 priceInAsset.pt=1 而 assetUsd=0.9546049954。API 名为 ptExchangeRate 的字段也不能直接替代合约 PY 水位。[S1–S4]

仅作单位交叉核对：同笔 PT/SY 数量比约 1.072305936185707886，合并 eUSD/SY 兑换比亦约 1.072305936185707887。按相同 18 位单位、同一种 SY 的同笔兑换比例相除，得到约 1 eUSD/PT（余差约 5.62×10^-19，整数舍入量级）。这不是混合现金/费用归因或 PnL，更不能据单点恢复历史水位。[S4]

933 日点仅覆盖 2 市场、2 到期日；1 个到期日有兑付回执佐证，完整独立 PT→USDT 策略现金流结果仍为 0。当前目录虽列出 830 市场、其中 733 已过到期日，目录数量并非独立收益结果。历史 SY/PY 水位、部署核对、费用、最终 USDT 兑换和 ≥30 独立完成周期仍不足，继续保留草稿，不晋级。[S1、S5]

出处均为 2026-10-19 UTC 已读；以下是可复现原始公开地址，不上传原始数据：

- [S1] https://api-v2.pendle.finance/core/docs — MarketHistoricalDataPoint、historical-data 与 PnLTransactionEntity schema；HTTP Date 20:02:50 GMT
- [S2] https://api-v2.pendle.finance/core/v3/1/markets/0x23aefced9255ad3560cdaa4a10cbfe9ec230dc5a/historical-data?time_frame=day&timestamp_start=2023-01-01T00%3A00%3A00.000Z&timestamp_end=2024-12-28T00%3A00%3A00.000Z&fields=timestamp,ptPrice,syPrice,tvl,totalTvl,totalPt,totalSy,totalSupply,tradingVolume&includeFeeBreakdown=true — HTTP 200，20:02:09 GMT；138280 bytes；SHA-256 f851f19fed3eb573c0bc99b748ea9a160e6138897927491567f8dc3c6e3294c3
- [S3] https://api-v2.pendle.finance/core/v3/1/markets/0x30e0dc9a1d33eac83211a1113de238b3ce826950/historical-data?time_frame=day&timestamp_start=2023-01-01T00%3A00%3A00.000Z&timestamp_end=2024-06-29T00%3A00%3A00.000Z&fields=timestamp,ptPrice,syPrice,tvl,totalTvl,totalPt,totalSy,totalSupply,tradingVolume&includeFeeBreakdown=true — HTTP 200，20:02:14 GMT；140678 bytes；SHA-256 41405c99ce6de9ccddbf9051e511a0578993182d7dff2a6f6c7ec48f9eeb93f8
- [S4] https://etherscan.io/tx/0x72ad19d8140ddbe613f4500591f6d8b87a314e07ba132c62370fbaffffd7e8bb#eventlog — 回执与日志 321、327、331；HTTP 200，20:05:11 GMT；Pendle 同笔公开索引 https://api-v2.pendle.finance/core/v1/pnl/transactions?chainId=1&user=0xe2680c6c726d2fbd9f8766e6c6d0bfd289414122&market=0x23aefced9255ad3560cdaa4a10cbfe9ec230dc5a&limit=100&skip=0 ，20:04:27 GMT
- [S5] https://api-v2.pendle.finance/core/v2/markets/all?limit=100&skip=0 — 相同参数 skip 依次取 0、100…800 共九页；20:01:16–20:02:17 GMT；当前目录，非完整历史部署证明

GitHub/X 实际搜索已做；X 无可核相关原帖。公开仓库示例仅静态阅读；历史数据与缺失核查使用自编标准库程序。
