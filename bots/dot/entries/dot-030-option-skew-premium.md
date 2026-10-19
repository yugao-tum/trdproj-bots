---
id: dot-030
name_zh: 同期限期权偏斜溢价
name_en: Same-expiry option skew risk premium
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: new
improves: -
category: V
return_type: insurance
instruments: BTC同到期期权；有保护翼的put vertical为自拟变体
venues: Deribit；具体可执行合约和保证金方案未核
data: 已读risk-reversal机制与线性/反向期权规则；未取得至少12个月免费免密钥的同步可成交期权链、费用与完整资金路径
test_2w: 先冻结真实合约、偏斜信号、保护翼、退出及逐时限损，再用历史同步报价按共同到期/冲击聚类；不足30独立完整结果或费后/资金门槛失败则不晋级，现无回测
status: 草稿
confidence: 低
---

## 一句话

利用同到期call-put隐含波动率偏斜的事前历史偏离，研究卖相对昂贵风险、买对侧或保护翼的组合；只在实际币种、费用与全程资金约束可证明后测试，当前尚非完整执行规则。

## 钱从哪里来

付款假说是看涨/看跌保险需求不对称，使同期限不同执行价或方向的风险价格出现溢价。承担偏斜继续扩大与尾部风险并不保证获利。关键变量是跨strike相对IV，区别dot-031跨到期期限结构、dot-047四腿固定毛支付，不把共同short-vol风险当统计独立性。

## 规则

- 来源原规则为risk reversal：call-IV减put-IV偏斜、滚动30日z-score、阈值1、目标30日到期，历史估价用mark并动态对冲[S1]。本稿没有复现，不将其回报或限损转给其他组合。
- 本研究的put vertical只是有保护翼的自拟方向：同到期、等底层数量q，卖高执行价K_H put、买低执行价K_L put。它和call-put risk reversal不同；实际合约、delta/翼宽、信号方向/阈值、退出与数量尚须独立冻结。
- 线性结算下，到期内在净负债L=q[(K_H−S)^+−(K_L−S)^+]满足0≤L≤q(K_H−K_L)。若信用C保留在同结算币种，零费用毛损失≤max(0，q翼宽−C)。这是自行代数证明，只适用于完整持有至同一结算。
- 反向币本位净负债为L/S；S趋近0时，即使美元内在负债有界，也没有覆盖所有S>0的有限固定BTC储备。不能把“美元有界”写成“2500等值BTC抵押全程足额”。
- 总本金5000 USDT等值，同一场所权利金、抵押、所有费用和缓冲合计约2500以内；不借款。先买保护腿也不自动解决保证金、换汇和中间状态风险。证据未闭合时不运行裸卖组合。

## 证据

Deribit Insights刊载Amberdata研究的Risk Reversals段支持同期限偏斜变量；其历史结果属于来源自报，未核实。本稿不引用其数值收益，mark价格与动态对冲不能视为本变体的真实成交[S1]。

既有离线自写数学核查验证上述线性支付界及反向币储备反例；这不是历史回测。固定非豁免线性交割费模型中，put单腿费q·min(aS，b(K−S)^+)≤q·aK，a=0.00015、b=0.125，因而可给出该模型下有限终局费用界；仍不能涵盖强平、提前退出、兑换或制度变更[S2–S4]。

实际策略回测0，净收益、回撤和成交容量未知。来源risk reversal、数学put vertical和实盘资金可行性三者不混用。

## 数据

官方公开接口可查询当前instrument、交易与报价；近期expired目录不等于全年历史链[S5]。需要至少12个月同刻bid/ask/depth、固定delta映射、结算价、实际费用、保证金及币种兑换数据，当前未取得。现货或IV中间值序列不等于期权净收益数据；前向采集未启动。

## 两周内怎么检验

先定义可上市且可限损的线性变体，冻结训练窗、规则、OOS、触价成交和退出，不看结果调翼宽。独立结果以完整组合持有周期为基础，并合并同到期/共同市场冲击和重叠窗口；30个strike、腿或同一天多币不算30结果。

规则和数据未齐前只做可行性核查。若有效独立簇<30、历史不足12个月、途中资金不合规、5000口径费后年化<8%且无≥3%低趋势相关组合证据，或压力成本后非正，不晋级。当前未证明两周能得到30完整独立结果。

## 成本与容量

真实交易费逐腿用该合约费率、底层数量与premium cap计算；触价已含买卖差，不重复扣。入场、退出/交割、滑点、换汇都须计入。官方一般费率不能替代选定合约/账户的真实字段；未核费用保持未知。

另做0.30%/0.60%每次实际腿的保守压力时，必须明确采用权利金还是底层名义作分母，不能把0.30%乘净信用当全成本，也不能与已代表总成本的预算重复加费。分母未冻结，不作盈利判断。2500是预算上限，真实单笔容量和月机会数未知；最小底层名义超过2500本身也不等于风险资本必然超过2500。

## 风险

偏斜继续扩大、跳空、保护翼无流动性、非原子成交、币本位抵押贬值、保证金调整和清算均可破坏假定资金路径。信用、未实现长腿价值不保证可用于即时付款。USDC/USDT兑换与交易所风险单列，不假设稳定币永远等价。

## 改进了什么

不适用。

## 门槛自查

1. 机制说得清：满足定义；保险需求与相对偏斜清楚，持续利润未证
2. 有免费数据能检验：不满足现有证据；无12个月同步可成交链及完整资金账
3. 小资金能做：不确定；线性终局有条件限损不等于全程2500抵押足额
4. 不重复：满足初步去重；必要变量为跨strike偏斜，变体不另计
5. 扣成本后粗算够用：不确定；净收益未知，不能迁移来源risk reversal回报
6. 两周内能检验：不满足现有证据；规则未完全冻结且30独立结果未证
7. 出处可查：满足机制与边界描述；真实执行/收益缺口明示

## 出处

- [S1] https://insights.deribit.com/industry/bitcoin-options-finding-edge-in-four-years-of-volatility-regimes/ — 访问2026-10-19 UTC — 已读（Harvesting BTC’s Risk-Reversal Premium及skew entry indicator，正文257–264行；来源自报，未复现）
- [S2] https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options — 访问2026-10-19 UTC — 已读（币本位结算、合约数量、USD equivalent与forward区分）
- [S3] https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options — 访问2026-10-19 UTC — 已读（线性支付、乘数、Standard Margin与长腿未实现利润限制）
- [S4] https://support.deribit.com/hc/en-us/articles/25944746248989-Fees — 访问2026-10-19 UTC — 已读（标准期权费、逐腿cap、交割费和条件豁免；数学费用界为本稿推导）
- [S5] https://docs.deribit.com/api-reference/market-data/public-get_instruments — 访问2026-10-19 UTC — 已读（数量字段及expired仅近期目录）；https://docs.deribit.com/articles/options-data-collection-best-practices — 同日已读（chain/book/trade/delivery采集路线，不代表已取得历史）
