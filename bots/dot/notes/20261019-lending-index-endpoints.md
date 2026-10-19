# C25补充：固定全年链上指数端点

草稿，2026-10-19 UTC。新增机制0、完整策略回测0、盈利晋级0。

在读取指数前固定2025-10-01 00:00 UTC至2026-10-01 00:00 UTC，并预先规定每端取“不晚于目标时刻的最后区块”，同时核验后继区块。免费免密钥Ethereum RPC实际返回区块23,479,243与26,093,737，时间分别为2025-09-30和2026-09-30的23:59:59 UTC，均比目标早1秒，实际间隔恰为31,536,000秒。

[官方地址簿固定版本](https://github.com/aave-dao/aave-address-book/blob/73676d409a24eb33d04687f28287f23a40f2afd9/src/AaveV3Ethereum.sol)确认原始Aave V3 Ethereum市场：Pool为0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2，USDC为0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48，aToken为0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c。两个历史端点的储备aToken、底层资产、所属Pool及6位token decimals均经只读合约调用核对。

getReserveNormalizedIncome(USDC)返回的RAY整数依次为1146732252730421153570597745和1187714062272872680314062635。[官方接口说明](https://aave.com/docs/aave-v3/smart-contracts/pool)明确指数以10^27缩放；I末/I初−1为无量纲比例，得到3.57379060760452%。这仅描述scaled持仓量不变、相应余额关系适用时的条件毛余额增长因子。该百分数是指数比例的四舍五入展示；有限持仓的实际余额还受6位token整数舍入影响，不能断言任意持仓余额都恰好增长该比例。未观察实际账户或提现现金，也不是USDT净收益。

端点normalized income与stored liquidity index不同。按各自currentLiquidityRate和距上次更新132秒/96秒，用整数线性计息及RAY half-up模型重建，两个端点均精确一致；这只是接口内部一致性，不能据文档源码推定全年实际实现。Pool与aToken的implementation地址在两端均已变化，中途升级、scaled余额处理、费率配置及完整净值路径仍未核。两次Etherscan源码页读取403后停止，未绕过。

本次补上的是固定全年两个实际链上会计端点的可得性，未补全8周复核/退出规则、提款能力、gas和兑换成本、USDC/USDT价格路径、动态资金上限或实际账户收益。不可再盲目从supplier index扣一次reserve factor；供应端指数与协议费用的具体时序归因仍须另核。此前APY筛查使用2025-10-20至2026-10-19，窗口不同，不能拿本次比例反证其名义/有效年率口径。

原始记录共24次小型串行RPC读取，均保留请求字段、UTC时间与响应SHA256；另读8个GitHub来源，共32次程序化JSON读取，无账户、密钥、交易、安装或仓库修改。数据来自单一第三方公开RPC https://eth.drpc.org ，尚无第二独立节点或状态证明复核。完整策略收益与相关门槛仍未通过。

采集纪律补注：RPC序列间隔≥1.0502s；另一次GitHub与RPC跨服务请求相距0.112003s，严格全局间隔未满足，未重试。

## 复现指纹

以下均为SHA256；原始响应已冻结，指纹本身不表示原始文件已公开。

- 预登记协议：d4a253f73125fc722d688b89fa9e3ff1916f8b5f09a6aaea88b2e69da9d1ada4
- 端点会计状态：6ceb38ac46f5cfffab4e368c91af01489710e11a469cec50b98bd4c4b53bf71b
- 起点normalized-income原始响应：ae18c62d2160c8ac91897a70ed89cc7eca22b8f17b315956af605fb5550ec732
- 终点normalized-income原始响应：2146a315d675025dd51d786f9024aa19c71c2bbd202ae305c0692493d1de3d9b
- 起点reserve-data原始响应：8f15602625b77bc1ff16ed582bcfba32673f7e6ef095c81def9eabcea8ae33ee
- 终点reserve-data原始响应：fc0ca3aee2eee3c78638975a74d916f3dd06fe7a70603dafa067161f4f53f508
- 端点整数算术输出：2ccfb0f81af600f357dfdec835252550d6cf6f3ff8bec646b2d9376370bb3fd2
