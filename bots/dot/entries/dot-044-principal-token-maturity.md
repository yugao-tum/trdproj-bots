---
id: dot-044
name_zh: 本金代币折价到期
name_en: Principal-token discount to maturity
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: supplement
improves: Y-Y1-pendle-pt
category: A
return_type: convergence
instruments: Pendle PT及对应SY；具体稳定币会计单位市场待冻结
venues: Pendle及所选SY底层兑换路径
data: 两个已到期市场933个日频价格点已取回，1笔混合兑付获回执佐证；同一历史区块SY/PY水位已补，完整历史路径、可执行价格、最终USDT现金与联合收益仍缺
test_2w: 先核具体部署与会计单位，取已结束本金周期并还原真实PT→SY→输出资产现金账；按共同底层/到期/压力聚类，不足30独立结果或费后/动态资金超限则不晋级
status: 草稿
confidence: 低
---

## 一句话

用自有现金买低于指定会计资产面值的PT，持有至明确到期后按真实SY适配器赎回，尝试赚折价收敛；兑付可能低于面值，USDT本金不受保证。

## 钱从哪里来

卖方出售分拆的本金请求权，折价补偿提前流动性、利率与底层风险；终值由已有SY及其底层资产背书，不是协议凭空付固定利息。关键变量是PT价格、期限、会计资产、SY汇率和PY水位。区别浮动借贷息dot-025及无固定到期的LST队列折价dot-028，不把YT/积分/LP奖励另加为本条收益。

## 规则

- 自拟研究先冻结链、市场/PT/SY地址、部署版本、会计资产A、到期T、可兑输出及转换路径。仅考虑明确稳定币会计单位；ETH单位另作风险对照，不能直接记USDT固定收益。
- 候选窗口距到期30–180天；入场时SY汇率E≥PY水位I，已核到期流程，事前估计回款扣全成本符合5000总资本门槛才入样本。窗口为自拟，未验证；不能以未来已知赎回日/价格决定入场。
- 只买PT、不借款/循环抵押。持有至到期后最早真实可赎回并换回USDT时点，额外等待计资金占用。失败则按可变现价或损失入账，不能强制按1兑付。
- 已读VERSION=6源码中，_pyIndexCurrent=max(E，I_stored)，PT按q/I_current换SY；以SY汇率折回会计资产，简化兑付比例h=E/I_current≤1。正常h=1，负收益可h<1。仍须逐市场核实际部署/适配器。
- 到期后取得SY的数量不保证固定；firstPYIndex用于到期后treasury收益计算，不能把PT误写成持续获得到期后浮动收益。PT兑SY、SY兑输出资产两步分别核验。
- 单场所初始PT成本、gas和退出准备金≤2500，另2500现金，总5000；同协议多池合并额度。锁定期间价格/兑付上涨也可能使严格动态2500诊断超限，不能假设随时能无损减仓。

## 证据

官方PT正文支持本金单位、到期与赎回；PT-ezETH(ETH)示例为1 ETH价值的ezETH，不能改写为1 ezETH或1 USDT[S1]。Negative Yield说明水位下跌可使PT少于面值赎回；源码给出E/I现金流边界[S2–S4]。

官方费用页称成熟PT赎回本身无Pendle协议费、仍有网络gas，不能推成兑换和整条退出零成本；到期后收益转treasury[S5]。这些是合约/规则证据，非历史收益。本条实际回测0，真实净收益未知；广告固定APY不是已实现USDT收益。

## 数据

官方历史路线GET https://api-v2.pendle.finance/core/v3/{chainId}/markets/{address}/historical-data ，文档有time_frame、timestamp_start/end、fields、includeFeeBreakdown，示例含PT/SY价格与池费[S6、S7]。早期探针未取到数据；20:02 UTC新增官方免密钥GET已实际取回eUSD市场472日点（2023-09-11至2024-12-25）和S*USDT市场461日点（2023-03-24至2024-06-26），两者均超过12个月。ptPrice/syPrice为USD市场价格，不是SY/PY兑换索引或可成交报价；三项费字段分别缺311/472、221/461行，其中合计38个缺费日有正交易量，不能补0。

一笔到期交易的公开索引与浏览器回执日志已交叉读取，含PT兑SY及混合LP后的SY兑eUSD；不能将整笔gas或现金归给单买PT。数量单位交叉核验约1 eUSD/PT，eUSD当时约0.9546 USD，不能误算成对保证1 USD的折价。详见[历史价格与到期单位补核](../notes/20261019-principal-token-history-evidence.md)。

20:51 UTC补取同一交易的原始RPC回执、历史区块头与区块结束状态。SY.exchangeRate、YT.pyIndexStored及firstPYIndex一致为1.072305936185707886；PT→SY整数换算精确匹配，历史previewRedeem也与混合兑付日志一致。区块结束状态不等于交易执行中状态，当前源码未证明与历史字节码相同，单节点响应亦非状态证明；详见[历史会计状态与整数换算](../notes/20261019-principal-token-chain-state.md)。

目前933点对应2市场、2到期日，仍只有1次混合兑付佐证；完整独立PT→USDT策略结果0。至少12个月真实成交、连续历史PY/SY水位、部署版本、赎回与gas联合收益数据仍未取得；前向未启动，不能推定全部已到期市场均有完整数据。

## 两周内怎么检验

枚举当时已存在的市场并包括已到期/停止者，冻结入场时点，按真实部署、适配器和索引还原PT→SY→输出资产，再按当时价格转换USDT；每次费/gas及等候时间留账。共同底层协议×到期批次×压力事件聚类，不按链、池、每日价重复凑30。

30–180天持有不能靠两周前向直接证明30完整周期；需历史数据，当前独立数量未知。数据不足12月、单位/兑付无法核对、独立簇<30、5000口径费后年化不足8%且无≥3%低趋势相关组合证据、压力后非正或资金违规，均不晋级。

## 成本与容量

现金净额=q·h·S_exit·(1−c_exit)−q·p_A·S_entry·(1+c_entry)−F−G；S为A/USDT，F仅含未嵌入报价的协议/适配器费，G为gas。额外swap逐次计，不重复扣已含费用。

纯假设例：2500 PT、买价0.95 A、A/USDT恒1、h=1、90天、gas10，尚未计F；每边0.30%时净100.375−F，按5000简单年化8.1415%减F项；0.60%压力净85.75−F、简单年化6.9553%减F项。不是报价、实测收益或可重复CAGR；基准若初始场内2500且不转出盈余，期末2600.375−F还可能超严格动态限额。

实际单笔容量、费用、月机会数未知；2500是预算，不是深度证明。

## 风险

负收益使E<I、底层损失、稳定币脱锚、SY适配器或预言机错误、暂停和无法赎回、gas骤升及到期后等待。明确到期不等于准时USDT到账，“固定APY”依赖资产单位与兑付假设。

## 改进了什么

本条改按 `kind: supplement`，`improves: Y-Y1-pendle-pt` 归类。分类依据是 [known 中的 Y-Y1-pendle-pt](https://github.com/yugao-tum/trdproj-bots/blob/bc5dd79aa7da5e07cdd3ed2d22a158ab620222fb/known/KNOWN.md#L137)（2026-10-20 UTC 核对，仅含名称，不含既有规则或绩效）。折价购买Pendle PT到期兑现，兑付单位/水位核查为关键补充。

本条提供的研究补充：整理 PT 到期支付单位、SY/PY 水位与混合兑付交易的历史会计证据；单次截面及交易回执不等于完整历史路径、最终现金回款或策略净收益。

补充材料相对既有实现的新增性与采纳价值仍待核；本次不主张新机制、已证改进、盈利或已采纳，状态保持草稿。

## 门槛自查

1. 机制说得清：满足定义；分拆本金的条件性到期收敛
2. 有免费数据能检验：整体仍不满足；两条超过12月日频价格及一个历史水位截面已取回，连续水位/成交/最终回款联合数据缺失
3. 小资金能做：不确定；部署/深度/gas和锁定期动态限额未验证
4. 不重复：同机制补充，非新策略——对应 `Y-Y1-pendle-pt`；补充材料的新增性与采纳价值仍待核，不据 dot 内部区别主张全局新颖性。
5. 扣成本后粗算够用：不确定；仅条件算术，实际净收益未知
6. 两周内能检验：不满足现有证据；历史30独立周期未证，前向两周不足
7. 出处可查：满足机制/负收益/源码描述；新增历史GET与混合兑付出处已保存，实证缺口明示

## 出处

- [S1] https://docs.pendle.finance/pendle-v2/ProtocolMechanics/YieldTokenization/PT — 访问2026-10-19 UTC — 已读（19:20实际补读29–64行，Principal Token、Redemption Value、How to Redeem）
- [S2] https://docs.pendle.finance/pendle-v2/ProtocolMechanics/NegativeYield — 访问2026-10-19 UTC — 已读（Watermark Rate，22–37行）
- [S3] https://docs.pendle.finance/pendle-v2-dev/Contracts/YieldTokenization — 访问2026-10-19 UTC — 已读（redeemPY、pyIndexCurrent、getPostExpiryData）
- [S4] https://github.com/pendle-finance/pendle-core-v2-public/blob/87685c89d05087535e9b9647eeda0e3d297d1f06/contracts/core/YieldContracts/PendleYieldToken.sol#L323-L367 — 访问2026-10-19 UTC — 已读（另核379–412行；current index与到期后treasury计算，未运行）
- [S5] https://docs.pendle.finance/pendle-v2/ProtocolMechanics/Mechanisms/Fees — 访问2026-10-19 UTC — 已读（Swap Fees、Trading Fee Calculation、Post-Maturity Yield Redirection）
- [S6] https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview — 访问2026-10-19 UTC — 已读（API Entry Points、Rate Limiting、Market Data Endpoints）
- [S7] https://github.com/pendle-finance/pendle-examples-public/blob/main/backend-api-demo/src/get-market-historical-data-v3.ts — 访问2026-10-19 UTC — 已读（Query/DataPoint与历史API示例；仅阅读未运行）

- [历史价格可得性与到期单位补核](../notes/20261019-principal-token-history-evidence.md) — 访问2026-10-19 UTC — 实际历史GET、官方schema与混合兑付回执；原始公开地址、时间和SHA详列

- [历史会计状态与整数换算](../notes/20261019-principal-token-chain-state.md) — 访问2026-10-19 UTC — 同一交易原始回执、13次历史只读RPC、整数与preview核对；仍无独立策略现金收益

## 2026-10-20 到期兑付单位与条件现金反证（r14）

固定eUSD最长完整472日序列的入场日标记0.96695448 USD且成交量0；到期约1 eUSD/PT并不等于1 USD/PT。USDT=USD、标记可成交、零gas且双边0.30%条件下2500预算亏46.69，总5000回报−0.934%。实际成交、gas与USDT退出未知；零gas保本eUSD价0.972774。仅条件会计算术，保持草稿，933日不是933独立结果。

详见 [本轮结果与来源](../notes/20261020-r14-evidence/05-test_c44_maturity_cash/RESULT.md)。
