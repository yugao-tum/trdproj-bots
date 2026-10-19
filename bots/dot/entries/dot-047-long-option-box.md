---
id: dot-047
name_zh: 期权箱式固定支付价差
name_en: Cash-funded long option box spread
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: new
improves: -
category: A
return_type: convergence
instruments: 同标的同到期线性USDC四腿long box；反向BTC快照仅作单位/报价审计
venues: Deribit；四腿原子执行及具体保证金/费用资格未核
data: 已读合约/费用/保证金与公开数据路线；已读取一份2026-10-19第三方保存的BTC反向快照，非USDC链，无12月同步可执行四腿历史
test_2w: 先证明所选线性合约四腿、全程现金/保证金和费用上界，再以同步历史按共同到期及非重叠窗口聚类；缺任一条件或不足30独立完成结果即不晋级，当前无回测
status: 草稿
confidence: 低
---

## 一句话

以自有现金买同到期四腿long box，研究固定毛终值相对今天可成交全成本的差额；固定支付不是无风险净利润，保证金和非豁免交割费仍可能破坏资金上限。

## 钱从哪里来

short box对手方提前获得现金并支付隐含融资成本，long box方提前付现金等待到期；报价摩擦可能造成利差，持续超额收益未证。CME官方支持该融资解释，但其清算/保证金待遇不能搬到Deribit[S1]。只研究自有现金买箱，不做卖箱融资。关键变量是同到期put-call恒等式，区别偏斜、期限结构或现货期货基差。

## 规则

- 自拟linear-long-box-v1：固定UTC观察，仅真实已上市BTC_USDC/ETH_USDC欧式同到期、同指数、同结算价四腿，DTE 7–14日。实际观察时刻、收益阈值仍须冻结，当前未回测。
- K1<K2，四腿为+C(K1)−C(K2)+P(K2)−P(K1)，底层数量q=合约数×乘数，四腿数量一致。线性毛终值q(K2−K1) USDC；净debit D=q(ask_C1−bid_C2+ask_P2−bid_P1)。必须按真实数量、乘数与step，不用整份premium误替每底层单位报价。
- 只有同刻有效touch和足够深度才入候选，不用mid/mark/last作成交。Combo Books只证明允许的组合能同时执行，已读类型表未明确四腿box；不假定原子成交。分腿时先买完整保护腿，且每个中间状态现金和保证金都必须合格，否则跳过。
- 总5000 USDT等值，同场所debit、抵押、费用与缓冲约2500内，不借款、不把短腿premium循环扩大面值。约束同时看q翼宽、初始/维持保证金与最差中间状态。
- 计划持有至结算；提前退出按全部四腿反向touch重算，不承诺盈利。完整结束才开始下一非重叠周期；保留所有候选、未成交和失败，不择优strike/expiry。

## 证据

自行恒等式：c(K)−p(K)=S_T−K，故完整线性box毛终值严格为q翼宽。反向BTC/ETH支付为q翼宽/S_T个币，交割时美元毛值才相同；剩余BTC抵押仍有方向风险。若花b BTC权利金、留c BTC现金，忽略全部费用的USD损益为q翼宽−bS0+c(S_T−S0)，不能把抵押按最终汇率倒填历史[S2、S3]。

已读官方SM限制长腿未实现利润支持其他仓位。自行条件反例：q=0.01、90000/100000翼的线性box毛终值100 USDC；若Index=350000、短call mark=250000，按BTC/ETH SM公式短call维持保证金2762.50，单腿已超2500，完整支付有界仍不能证明资金路径[S2]。

标准非豁免交割费为逐腿q·min(0.00015S，0.125内在值)。足够高S下两call合计2×0.00015qS随S增长，而box毛终值不变，故该费表下不存在由翼宽单独保证的全价格费后损失界。具体全腿豁免或其他硬费用界必须先核[S4]。这些均为数学/规则核查，新增实际回测0。

第三方保存的2026-10-19 13:06:37Z BTC快照已读取882期权；全部反向BTC，不能作本线性USDC规则收益。12个稍后L2没有任何strike同时具call与put深度，不能形成完整四腿同期容量证据[S8]。报价行数、strike对和到期数不计独立交易结果。净收益未知。

## 数据

Deribit公开instrument、book、trade、delivery路径可查，近期expired目录不等于一年完整历史，成交历史也不能重建同步四腿盘口[S6、S7]。第三方目录显示短期BTC/ETH档案；本条只核一份BTC原始快照，未取得至少12个月线性USDC完整可成交链。

该gzip SHA-256为bcfd5eb5c7b809e2cc1d01c7561551f815d2d8dd809358ecdc74e154aeec3b9b，JSON为a697b5a0001d8f08aad2e46cdeb9e82cae862be0419fc6daaa88c51d3cca46aa。采集过程和真实报价可执行性并未独立确认。前向采集尚未启动。

## 两周内怎么检验

先核真实合约、豁免、费用上界、四腿执行与全程资金可行性，再冻结观察、期限/宽度选择和OOS。若有足够长同步历史，按非重叠持有窗、共同到期/结算源聚类，至少30真实有信号且完成的独立簇。7–14日持有不能靠两周前向凑30，腿/strike/快照不得加数。

单位/任一资金状态或费用上界不能证明、四腿不同步/缺深度、数据不足12个月、独立簇<30、5000口径净值年化<8%且无≥3%低趋势相关组合证据，或压力净额非正，均不晋级。静态报价差正数也不等套利，尚含时间价值且未有真实兑换/后费。

## 成本与容量

线性标准单腿交易费q·min(0.0003S，0.125P) USDC；反向为q·min(0.0003，0.125p)个币，再按真实兑换时点折算。具体折扣、组合资格、交割豁免未知，不能填0；期权到期生成future过渡不另假造一次重复交割费[S2–S4]。

额外压力定义为每次腿底层名义N_j=|q_j|S_j的0.30%/0.60%；总入场预算取max(实际交易费+额外冲击，αΣN_j)，再加未来交割/兑换等，不重复加实际费。它是自定保守敏感性，非交易所费率或指南唯一分母，touch价差已含。

纯算例：S0=100000、q=0.01、翼宽10000、D=98，毛差2；四腿名义4000，压力预算12/24后为−10/−22，尚未计交割/兑换。不是报价或实测。真实单笔容量、月机会数未知，2500仅资本上限。年化须以完整5000净值及实际占款日计算。

## 风险

SM/PM途中要求、分腿失败、强平、长腿不可立即兑现、非豁免费用随价格增长、稳定币与BTC抵押汇率、交易所和结算风险。PM只测试有限情景，不构成所有价格路径保证[S5]。固定终值、终局限损、同币种足额抵押和全程存活是不同要求。

## 改进了什么

不适用。

## 门槛自查

1. 机制说得清：满足定义；固定毛支付与融资补偿清楚，超额收益未证
2. 有免费数据能检验：不满足现有证据；单反向快照不能替代12月线性同步链
3. 小资金能做：不满足现有验证；SM/PM资金和全状态费后界未闭合
4. 不重复：满足初步去重；同到期四腿支付恒等式为独立必要变量
5. 扣成本后粗算够用：不确定；真实净收益未知，静态差不作利润
6. 两周内能检验：不满足现有证据；30完整独立持有结果未证
7. 出处可查：满足机制/规则/单快照范围描述；执行与收益缺口明确

## 出处

- [S1] https://www.cmegroup.com/articles/2024/index-options-box-spreads-as-financing-tool.html — 访问2026-10-19 UTC — 已读（Structure、implied rate、financing及closing footnote，28–73、99–105行）
- [S2] https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options — 访问2026-10-19 UTC — 已读（Settlement Process、contract specs、BTC/ETH SM及long PNL限制）
- [S3] https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options — 访问2026-10-19 UTC — 已读（币本位支付、index换算与forward模型区别）
- [S4] https://support.deribit.com/hc/en-us/articles/25944746248989-Fees — 访问2026-10-19 UTC — 已读（标准3bps、12.5%单腿cap、组合优惠、0.015%常规交割及条件豁免）
- [S5] https://support.deribit.com/hc/en-us/articles/25944756247837-Portfolio-Margin — 访问2026-10-19 UTC — 已读（overview、Long Options in PM、risk matrix的有限情景限制）
- [S6] https://support.deribit.com/hc/en-us/articles/31424954956061-Combo-Books — 访问2026-10-19 UTC — 已读（summary及完整公布类型表，四腿box资格未确认）；https://docs.deribit.com/api-reference/market-data/public-get_instruments — 同日已读（数量与近期expired范围）
- [S7] https://docs.deribit.com/articles/options-data-collection-best-practices — 访问2026-10-19 UTC — 已读（59–204行，chain/book/trade/combos/delivery，未实际启动采集）
- [S8] https://github.com/Ronak-Mahajan/neural-options-lab/blob/surfaces/deribit/btc_20261019T130637Z.json.gz — 访问2026-10-19 UTC — 已读数据（Git blob f5e4f982f3918b3c8c98c58854626c555c23832e；仅此单快照字段/静态审计，非直接交易所实时抓取或回测）
