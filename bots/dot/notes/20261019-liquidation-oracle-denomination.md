# C37：固定旧样本的历史预言机计价核对

审计日期：2026-10-19 UTC。本补充只改善数据口径；未形成实际出售收益、资本资格或策略回测。

## 样本与读取范围

沿用原先已核对 **12 笔成功交易回执、80 条 LiquidationCall 日志**：两笔原始目的性样本含 68+2 条，另十笔来自预注册等时间分层。没有重选、扩样或按价格择优。冻结的十二个区块位于 **21,029,964—25,387,860**，事件日期为 2024-10-23—2026-06-24；这不是该区间的连续扫描，也不是 80 个独立机会。

仅用 https://eth.drpc.org，共 **45 次串行只读 RPC**，全部成功；已计入 3 次 helper 代码检查，没有批量 RPC、重试或交易操作。最后一次 RPC 于 2026-10-19 21:03:27 UTC 完成。请求与原始响应逐项保留 SHA-256。

## 可复核地址与字段

十二个冻结区块均通过 Pool.ADDRESSES_PROVIDER() → provider.getPriceOracle() 实读得到：

- Pool：0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2
- Provider：0x2f39d218133afab8f2b819b1066c7e434ad94e9e
- Oracle：0x54586be62e3c3580375ae3723c145253060ca0c2

根据事件前官方地址簿快照定位的三个历史 UI helper 均在首次抽中区块存在代码：

- 0x3f78bbd206e4d3c504eb854232eda7e47e9fd8fc：8 个样本区块，41 字段
- 0x56b7a1012765c285afac8b8f25c69bf10ccfe978：2 个样本区块，40 字段
- 0x2dad8162a989cd99d673de4425bb2298db1e1aa2：2 个样本区块，40 字段

原生 getReservesData(provider) 返回的 underlyingAsset、decimals、priceInMarketReferenceCurrency、priceOracle 与 marketReferenceCurrencyUnit 被按历史布局解码；只分析旧样本对应的 **24 个资产×区块**。全部有正价格，160 项事件侧储备精度核对无差异；三个 helper 各取首次冻结区块，六项 getAssetsPrices 直接价格交叉核对均一致。这里的 decimals 是历史 Aave 储备配置精度，未另读 ERC-20 decimals()。

十二个区块的 helper 均返回参考单位 100000000。直接 BASE_CURRENCY() 仅在首尾冻结区块读到零地址；BASE_CURRENCY_UNIT() 仅在首区块直接读到 100000000。[官方接口](https://github.com/aave/aave-v3-core/blob/782f51917056a53a2c228701058a6c3fb233684a/contracts/interfaces/IPriceOracleGetter.sol)规定零地址对应 USD 计价惯例。这不是对真实美元成交或稳定币兑付锚的验证。

## ABI 风险与修复

三个已查地址簿版本导出的 ABI 都有 **54 个储备字段**，与实际返回的 **41/40 字段**不符，不能直接套用。已改用固定版本的官方接口，并严格检查类型、偏移、字符串填充、元组边界与目标资产地址：

- [41 字段接口](https://github.com/aave-dao/aave-v3-origin/blob/740d0a8163197a4948c959078258c12254207bef/src/contracts/helpers/interfaces/IUiPoolDataProviderV3.sol)
- [40 字段接口](https://github.com/aave-dao/aave-v3-origin/blob/a964a096612e3d30d6e2aaec848615278690392f/src/contracts/helpers/interfaces/IUiPoolDataProviderV3.sol)

全部十二份原始响应重新离线解码通过；非法布尔值、错位偏移和截断测试均被拒绝。官方地址、代码存在、布局与直接价格核对相互佐证，但未完成编译源码与运行字节码等价证明。

## 数值能说明什么

80 条事件均另存精确分数与十进制：债务原始数量 × 区块末预言机价格 ÷（10^历史储备精度 × 参考单位）。其中 73 条原来缺少日频 USD 价格；新增字段是另一种时点与语义的参考估值，并未把缺失成交价补成真实现金。

价格来自**单一提供方的区块末状态**，不是交易前或交易内轨迹；同区块后续更新、eMode 和历史配置可能改变实际清算输入。未保证 intratransaction 一致性，亦未用第二提供方或区块哈希重放独立验证。USD 参考单位不等于 USDT 必然等于一美元；预言机估值不是实际购入成本或可执行出售收入。68 条 receiveAToken=true，不能当作已经卖出底层资产。分钟深度、退出现金、费用、失败竞争、资金来源及资金复用仍缺失。

**G2 仍未通过；G3 资本资格、G5 净收益及 G6 独立完整样本仍未知或未建立。没有资本 eligibility PASS，新增回测为 0。**

## 冻结证据指纹

SHA-256：

- 原始 CSV：1e43d7473ff09a4b89136f19420ff4d3e2de3b4d364d2e1883b4b6137667c759
- 样本预注册：39668183008859659096dccc918d8927d65c53cb664e3872ebfad99ceb226156
- RPC 请求/响应清单：37ff0e10f667fab60ebb11b236e85075fb9ef5857ab4ac478954e80fe6f26874
- 锁定审计报告：a938e31bea83016a2bc92428aa892ab65d29f33d4964634f6d8e374744a72801
