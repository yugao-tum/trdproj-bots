# C39：同报告期公开分配文件与有界离线诊断

访问日期：2026-10-20 UTC。来源是 stake-dao/bounties-report 的自报数据，不是独立认证的协议支付。四个完整公开JSON的Git blob均逐字节复核；精确URL、SHA256和源字段位置见 SOURCE-MAP.json。仅检查报告期1792022400（2026-10-15 UTC），361钱包、1期；未检验其他期，不将其记作失败或独立结果。

## 已核与未核

- repartition与repartition_delegation均报告proposalId="5"、snapshotBlock=240，只证明字段相等。已有generator提醒proposal.snapshot是vlCVX epoch，不是区块，但未保留本次提案响应、repartition写入器或执行版本证据，故不认证5→240映射，不把240改名为已证epoch或Ethereum块。
- split的361钱包total精确加总为availableForDistribution = 41283718401576498928496 raw，valuePico精确加总为28015206546320955。后者是价值权重分母，不是有效投票资格分母；池化payout-token身份未证，不换算USD。
- received 56852719162292053271913 − withheld 15569000660715554343417 + carriedIn 0 − available 41283718401576498928496 = 100000000000000 raw。原因未知；不假设费用、dust、reserve或错误。withheld数值等于ceil(votiumReceived/2)只是算术相等，缺分支实现。
- 8个token的逐delegate poolTokens加总等于totalTokens，14个delegate-token池各自守恒，顶层forwarders+nonForwarders也守恒。但token 0x04acaf8d2865c0714f79da09645c13fd2888977f 的逐delegate forwarders加总2200003298699386984022与报告组额2196175964146084624948相差 +3827334553302359074 raw；nonForwarders反向相差同量。总token守恒，分组差异原因未证，不指控损失、欺诈或支付错误，也不静默归一化。
- 360/361钱包键可与Curve forwarders关联；另1条curve=0、fxn>0，和FXN-only标签一致，不构成独立FXN归属或实际付款证明。另4个Curve forwarder键未出现在split，原因不明。所有钱包sources之和等于valuePico；实际total相对floor(available×weight/totalWeight)有173条差0、188条差1，只证明与该整数分配近似相容，不认证tie-break规则或token到权重构造。
- 三个votiumTxs只是来源指针，未取回交易/receipt/log；withdrawal也没有交易ID。源码recipient与withdrawal.source一致只是引用关系。认证权益到支付链路0，认证有效投票分母0。

## 时点、归属和复现边界

Stake DAO池化/委托变体不同于dot-039原自有CVX手动投票，不用最终分配回填事前选池。priceProvenance.fetchedAt=2026-10-20T07:50:15.172Z，不能作为10月15事前价格。合约地址与decimals是来源自报，不是独立链上验证；oo-00/Votium旧样本的canonical身份也未因此获证。

本包只发布小型派生检查摘要及来源映射，无原始JSON、地址名单或执行包装文件。DIAGNOSTIC.json是已完成缓存检查的摘录，不是新的运行结果；未发布依赖本地包装路径的check.py，所以本包不是数据自包含、可直接独立运行的完整复现程序。重核需要按SOURCE-MAP获取相同四个JSON正文，校验Git blob/SHA256，再按这里的字段和整数等式复算；源码语义检查还依赖注明的两份TypeScript版本，且它们不证明生成该期数据。

既有来源阶段总8次读取（本发布0次新来源/市场读取），离线诊断没有外部读取或执行来源代码。停止：本次指定缓存已穷尽，没有整项准入缺口闭合，不启动经济回测、不给APR/收益/得分、不晋级。dot-039保持草稿，原冻结文件与其他参与者不改。
