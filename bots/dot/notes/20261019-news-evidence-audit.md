# 新闻、上线公告与清算研究的证据边界

访问与复核日期：2026-10-19 UTC。结论保持：C11新闻后反转尚未完成来源与机制定义闭环，C35上线关注度仍是其补充；C40保留已有资金费条件现货代理结果。本次新增候选0、策略回测0、盈利通过0。

## 新闻数据：时间字段有用，但不能从负结果推出反转策略

已读[Dymyt-ry的README研究结论](https://github.com/Dymyt-ry/btc-news-forward-price-reactions/blob/main/README.md#research-findings)、[字段字典](https://github.com/Dymyt-ry/btc-news-forward-price-reactions/blob/main/docs/DATA_DICTIONARY.md)及[fwd_bwd_test.py第69–173行](https://github.com/Dymyt-ry/btc-news-forward-price-reactions/blob/main/notebooks/fwd_bwd_test.py#L69-L173)。来源覆盖2026-06-13至09-19，报告新闻不领先价格，部分波动预测改善在加入日历控制后消失；这些是作者自报，未独立复现。

所读代码主要比较前后绝对波幅，不能直接证明有符号的价格反转。first_seen、signal_ready等字段存在，不等于逐行历史可用性已核验；同标题合并也不能消除改写报道与共同事件的依赖。99日新闻记录不满足本项目crypto至少12个月的新闻条件证据要求。

[数据权利说明](https://github.com/Dymyt-ry/btc-news-forward-price-reactions/blob/main/docs/RIGHTS.md)和manifest包含混合来源、非商业限制，不能当作通用商业授权。未取得或转载新闻正文数据。发布API的immutable:false也提示应冻结哈希，不能仅凭README用语推定平台强制不可变。

## 上线公告：当前正文不能自动回填为历史可见内容

已读[jev-trade上线研究说明](https://github.com/Waxmell114514/jev-trade/blob/claude/ecstatic-bardeen-tknnox/README.md#the-opportunity-exchange-listing-announcements)、[announcements.py第116–184行](https://github.com/Waxmell114514/jev-trade/blob/claude/ecstatic-bardeen-tknnox/jevtrade/listing/announcements.py#L116-L184)、[study.py](https://github.com/Waxmell114514/jev-trade/blob/claude/ecstatic-bardeen-tknnox/jevtrade/listing/study.py)。README明确该上线实验尚未运行。

代码将CMS历史releaseDate与如今获取的正文配对，并假设正文不变，未保留历史版本与首次实际可见证据。事件回报为毛价格变化，未完整计入交易费用；逐token标准误也没有处理同一公告/重叠市场事件的依赖。不能把未运行提案、少数阅读例子或通用新闻小样本阴性结果升级为C11的已验证反转机制。

## 清算研究：事后分类与不同控制变量必须分开

已读[forced-or-frantic修正说明](https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/CORRECTIONS.md)、[v3协议](https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/reanalysis/protocol/CORRECTION_PROTOCOL.md)、[主要输出](https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/reanalysis/outputs/results/primary_effects.json)、[敏感性表](https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/reanalysis/outputs/results/sensitivity_grid.csv)。旧版撤回，不能继续引用旧显著性。

v3的OI类别在清算起点后2小时才可确定，不能预测同窗位移。作者输出中，起点强度控制后的系数约+0.948仍显著；加入测量窗口总清算量的S5a为+0.154、区间−0.369至+0.697，不能简化为“所有控制都不显著”。这些仍是来源描述性结果。

[data/README](https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/data/README.md)说明原始文件不随仓库提供，重构含requester-pays S3。未获取付费数据或运行来源代码。该研究不能证明负资金费预测现货反弹，也没有验证本研究C40简化规则的拥挤释放解释。

## 后续必要证据

继续研究需先固定有符号反转假说、事件首次可见时刻、原始新闻版本、交易方向/真实费用、独立事件簇与留出段。现有缺口支持“证据不足”，不支持断言所有新闻策略无效。只读来源与自编数据口径检查都不增加独立收益样本或策略回测数。
