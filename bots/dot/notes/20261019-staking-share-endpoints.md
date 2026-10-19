# C27：stETH 恒定份额的历史账面数量证据

研究执行：native dot；取证日期：2026-10-19。

固定 10^18 stETH shares 对应的 ETH 账面数量，在指定的 12 个月区间增长 **2.48049172%**。这是两次历史只读接口返回整数的比例，不能称为 USDT 利润、实际提款收益或完整策略回测。

## 区间与原始整数

2026-10-19 在抽取 stETH 历史读数前，冻结了 2025-10-01 至 2026-10-01 的区间、区块及哈希；这不是 2025 年投资开始前的预注册。两端均采用目标 UTC 时刻之前最后一个区块，实际时间各提前 1 秒，相隔 31,536,000 秒，恰好 365 天。

- Ethereum 主网 stETH 地址：`0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84`，见 [Lido 官方部署清单](https://docs.lido.fi/deployed-contracts/)
- 只读方法：`getPooledEthByShares(1000000000000000000)`；返回单位为 wei（18 位小数，1 ETH = 10^18 wei），份额始终不变
- 起点：区块 `23479243`，返回 `1215109858893216176`
- 终点：区块 `26093737`，返回 `1245250558309363625`
- 算式：终点整数 ÷ 起点整数 − 1；使用 Fraction 精确分数与 Decimal，百分比展示四舍五入至 8 位小数

## 核查与边界

两端区块哈希均已复核；15 次串行 RPC 请求全部成功，原始请求/响应哈希及 5 个手算测试通过。端点合约版本由 2 变为 4，implementation 地址也发生变化；尚未完成历史源码与部署字节码的等价验证。GitHub 标签查询遇到 HTTP 403 限流后停止，没有更换凭据或绕过限制。

[当前官方源码](https://github.com/lidofinance/core/blob/master/contracts/0.4.24/StETH.sol) 的份额换算向下取整。若两端历史实现均遵循该语义，每次接口读数相对未取整换算值的误差小于 1 wei；这仅界定接口舍入，不代表经济收益率无限精确。[LIP-31](https://github.com/lidofinance/lido-improvement-proposals/blob/develop/LIPS/lip-31.md) 引入外部份额，因此没有机械地用总 pooled ETH ÷ 总 shares 替代接口读数。

[Lido 官方说明](https://docs.lido.fi/guides/lido-tokens-integration-guide/) 涵盖 rebase、费用份额、罚损和异步提款。两个端点不能拆分验证者奖励、捐赠、份额销毁等账务影响，也不能给出中间路径、回撤、ETH/USDT 或折溢价变化、交易成本和提款结果。证据来自单一公共 RPC；机制数和回测数不增加。

## SHA-256 证据锁

原始 JSON 响应不纳入公开仓库；以下哈希标识本次取证文件：

- 抽取前冻结方案：`773a54f2da1341574962ff948c4d7f1ed01eceb0031fbd0a9709d79fbbad8093`
- 两端状态记录：`3ed931d7b75da312d57dc23a4b9b0d6070c1889367da2000080718f892c5410a`
- 起点原始响应：`25560fe81f8c068270fddfff2d4b7c4b6da23f39a2a276d94e74f9f2a08d8b31`
- 终点原始响应：`11ebac5c264c53edd3d2f4d5cfa7d60286d2a620e5ae886deeba45fcfdae1c23`
