---
id: dot-046
name_zh: 跨链先垫后偿服务补偿
name_en: Cross-chain fast-fill relayer compensation
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: new
improves: -
category: M
return_type: service
instruments: 跨链原生USDC目标链库存及有效deposit退款请求权
venues: Across已知映射的简单EVM路由；具体部署及开放订单资格待核
data: 已读deposit→fill→refund规范及官方源码；生产API需key，免密钥探针未取数，12月实际退款/gas/竞争/补库存联合账本未取得
test_2w: 从公开日志重建当时可接开放订单、全部垫款和实际退款，按共同最终性/bundle/协议事故聚类；不足30独立完成结果、重用未偿款或费后/预算失败则不晋级
status: 草稿
confidence: 低
---

## 一句话

以自有目标链USDC库存为有效开放跨链订单先行垫付，待可验证退款实际到账后释放本金；只在差额覆盖全部费用、占款与风险时研究，当前没有净收益数据。

## 钱从哪里来

跨链用户锁inputAmount，relayer先付outputAmount；有效填单结算后获得扣LP/system fee的偿还，用户input/output差额补偿速度、库存、gas与最终性风险[S1、S4、S5]。区别AMM双边曲线收费dot-029与浮息贷款dot-025，本条每笔有deposit→fill→refund状态机。

## 规则

- 自拟总资本5000 USDT，Across全部链合并场所额度≤2500，另至少2500现金；单笔垫付≤1000，未偿敞口≤2000，其余留燃料/成本。未到账退款不得重用，不借款或闪贷。
- 仅研究同种原生USDC明确映射、无附加message的简单EVM路线。先核部署版本、源事件最终性、token/decimals、完整RelayData、目标链未填、截止与余额；无有效匹配源deposit可能不获偿还。
- 只取开放流量或他人排他期真正结束后的可接订单，必须在fill deadline前。全网成交量不是新relayer能拿到的量，指定排他名单不得假定已获资格。
- F=输入资产在偿还链的可实现价值−LP/system fee−目标链垫付价值；F须大于全部成本和事前冻结的风险缓冲。具体缓冲尚未定量冻结，因此当前只是条件框架。
- 源链偿还可能免LP费却需补目标链库存，目标链偿还可能省补库存却有LP费；不得同时无条件取两项好处。每笔至实际退款到账或可确认失败/坏账才结账。
- 所有竞争失败、撤回、退款延迟及gas保留。bundle发布时间不是到账承诺，根证明/挑战/执行可继续占款。

## 证据

固定提交SpokePool中fillRelay核排他资格，_fillRelayV3不支持部分填单、重复回退、完整转出金额；executeRelayerRefundLeaf需有效根证明，并处理deferredRefunds[S4]。这是源码机制证据，未核全部当前主网部署。

官方排他文档部分仍含2025推广目标，不据此断言2026当前覆盖率；配置README的maxFillSize=2500和minProfitThreshold=0.00005只是示例，不能当最低本金或保证利润[S3、S6]。生产API说明需API key和Integrator ID；测试网免key不等于真实历史可得[S7]。

实际回测0，真实净收益、成功率与回款延迟未知；未运行relayer或来源代码。

## 数据

deposits接口文档有deposit/fill、额度、token及排他字段，但示例不是真实返回，也不足构造净收益；还需fill gas、实际refund leaf/到账、LP费、库存重平衡及失败交易[S8]。

已尝试免密钥/deposits?limit=1&skip=0及官方1000-USDC suggested-fees示例，返回“not accessible via this tool”，没有HTTP状态或JSON；不能写成403或实测报价。至少12个月免费免密钥实际填单→退款收益未取得。公共链日志只是待核替代研究路线，前向未启动。

## 两周内怎么检验

先核日志覆盖和部署映射，再按事前可见信息重建开放订单与全部垫付，不能预知未来竞争成交。至少30完整可接机会还须按源链最终性事故、共享结算bundle、稳定币/桥/合约故障与拥堵聚类；同bundle的30笔不算30独立结果，跨链仍共享HubPool/UMA风险。

失败标准：数据/版本/费用闭环失败、有效簇<30、超5000/2500预算、重用未偿款、5000口径年化<8%且无≥3%低趋势相关组合证据，或压力成本后非正。即使正常运营样本足够，也不代表灾难概率已验证。

## 成本与容量

现金账=全部实际到账退款−全部垫付−gas（含失败和退款执行）−未在退款中扣过的LP费−真实补库存/兑换及基础设施费用。只加实际退款且已减全部垫付时，最终确认未回收本金已含在关闭事件现金净额内，坏账只能单列归因，不能重复减；退款已净扣LP费也不再扣。

截面尚未退款但未确认坏账时，现金缺口不等于最终亏损。可回收但受限的应收权利须单列保守估值；净资产由剩余现金、库存及这些权利构成，不能把已确认退款现金与同一应收再计一次。应收仍不可用作下一笔垫款现金。

保守初筛另设每笔垫付/回收两腿名义各0.30%/0.60%预算，1000垫款约6/12 USDT，再加未含gas/协议费。这不是链转账实际收0.30%的声明。真实库存账逐次换汇费与这个总预算分开，不重复算同一次兑换。

所有年化用完整5000净值及真实占款日，不用单笔差额乘无限周转。实际月机会、可获取率、库存并发、成本和容量未知；1000/2000只是研究约束。

## 风险

源链重组、deposit不匹配、错误token映射/黑名单、退款根争议或延迟、竞争失败gas、升级/暂停、单向库存流失。目标链转账成功不保证有偿还权；跨链最终性、稳定币和共享协议尾险可共同发作。

## 改进了什么

不适用。

## 门槛自查

1. 机制说得清：满足定义；用户为快速垫付及风险承担付差额
2. 有免费数据能检验：不满足现有证据；生产API限制已核，完整历史现金账未得
3. 小资金能做：不确定；预算框架明确，真实订单资格/尺寸/gas及容量未证
4. 不重复：满足初步去重；先垫后偿服务区别AMM和浮息借贷
5. 扣成本后粗算够用：不确定；净收益未知，风险缓冲尚未冻结
6. 两周内能检验：不满足现有证据；有效30独立回款簇未证
7. 出处可查：满足规则/固定源码描述；部署和数据失败明示

## 出处

- [S1] https://docs.across.to/introduction/fees — 访问2026-10-19 UTC — 已读（48–109、137–148行，input/output、LP费、偿还链及库存风险）
- [S2] https://docs.across.to/introduction/relayers/running-relayer — 访问2026-10-19 UTC — 已读（48–119行，余额限制、bundle节奏；未安装/运行）
- [S3] https://docs.across.to/introduction/relayers/relayer-nomination — 访问2026-10-19 UTC — 已读（48–70行，排他与履历；推广目标不当当前比例）
- [S4] https://raw.githubusercontent.com/across-protocol/contracts/555475cdee6109afc85065ca415c740d7f97b992/contracts/SpokePool.sol — 访问2026-10-19 UTC — 已读（887–1010、1128–1185、1545–1616行；固定提交，未运行）
- [S5] https://raw.githubusercontent.com/UMAprotocol/UMIPs/master/UMIPs/umip-179.md — 访问2026-10-19 UTC — 已读（405–487匹配、515–534偿还、619–636退款叶聚合）
- [S6] https://github.com/across-protocol/exclusive-relayer-configs — 访问2026-10-19 UTC — 已读（README 202–247行；参数仅示例）
- [S7] https://docs.across.to/introduction/api-keys — 访问2026-10-19 UTC — 已读（49–55、125–141行，生产凭据/测试网与限流）
- [S8] https://docs.across.to/api-reference/deposits/get — 访问2026-10-19 UTC — 已读（接口字段、bearerAuth、分页和示例，非实测数据）
