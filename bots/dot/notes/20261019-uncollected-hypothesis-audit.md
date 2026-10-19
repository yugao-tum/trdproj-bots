# 三类线索为何仍未计入40个已收集机制

2026-10-19 UTC。本页补充C10、C11/C35、C17的来源核查；新增独立机制0、策略回测0。收益、Sharpe、最大回撤均未知。这些限制不证明相关效应永远不存在，也不要求每个已收集候选先证明盈利。

## C10：季节风险率缺少合约一致的历史标签

实际读到三条合约规则：
- [2026年首个大西洋飓风日期档](https://polymarket.com/event/when-will-the-first-hurricane-form-in-the-atlantic-in-2026-20260904095717296/will-the-next-atlantic-hurricane-form-between-september-26-and-september-30-2026-20260904095717155)，按首次NHC将系统归为飓风的公告发布时间、ET日界
- [2026-05-31前美国飓风登陆](https://polymarket.com/event/will-a-hurricane-make-landfall-in-the-us-by-may-31?outcomeIndex=1)，依初始公告中的登陆强度，后验修订不回填
- [Beryl以热带风暴登陆](https://polymarket.com/event/will-beryl-hit-the-us-as-a-tropical-storm/will-beryl-hit-the-us-as-a-tropical-storm)，特定风暴、特定强度档，不能把更强飓风自动当成热带风暴档成功

上述正文定位分别为Rules、Rules、Rules；访问日期均为2026-10-19。[NOAA托管季节性论文](https://repository.library.noaa.gov/view/noaa/49029/noaa_49029_DS1.pdf)的Methods支持日历及环境状态值得研究；[IBTrACS官方说明](https://www.ncei.noaa.gov/products/international-best-track-archive)说明best-track及修订来源。后验轨迹中的首次强度记录，并不自动等于原公告首次公开时刻。

本轮没有取得含无事件年份、首次合格公告时刻及可得版本的完整风险集。没有估计条件发生率，更没有与可成交价比较。三合约不是三个独立季节结果；同年多个日期档不能凑独立样本。另有州别合约的七日延长条款只见搜索索引，未获正文核验，不用于计算。保留C10为待补证线索。

## C11/C35：可下载CSV仍只是分组统计

[CoinSight正文](https://getcoinsight.com/en/research/exchange-announcement-study)与其[实际CSV](https://getcoinsight.com/api/research/exchange-announcement-study.csv)已读取；2026-10-19 19:46:27 UTC取得3,349字节，29行、20列。7个all组与22个细分组不能重复相加。仅汇总7个all组得3,775个coin-events、2,596个公告计数、38个标注reachable的coin-events；缺事件ID，不能证明这些是全局唯一或独立公告。

Upbit组有230个coin-events，24小时有228个观测，reachable子组仅7个。缺逐事件时刻、同一批事件各期限配对、盘口和费用；reachable是来源的捕获标签，不是成交保证。故不能从不同期限收益中位数下降直接算出可交易反转利润。

**纯合成反例**：三事件基价均100；1小时价为100/115/150，24小时价为107.5/120/100。两期限累计收益中位数为15%和7.5%，相除得到−6.52%；逐事件真实配对的1至24小时收益中位数却为+4.35%。这仅证明聚合运算不能代替配对计算，不是市场收益。

CSV SHA256：`12b566e655ce19e84bea9fd710c536d5aa1ba3ced218878bf1f67e7fdeeddc97`。C35仍为C11的上市事件补充，未新增独立机制。

## C17：live入口不等于真实历史回测

已冻结并静态读取[该仓库版本](https://github.com/punyamodi/binary_market_engine/tree/da3a599422aeca3af677ccd816882a542633df26)，11个源码/文本文件的Git blob与目录一致，未执行来源代码。

- [strategy.py](https://github.com/punyamodi/binary_market_engine/blob/da3a599422aeca3af677ccd816882a542633df26/strategy.py#L16-L52)用类别常数和关键词估概率；年龄用于入场过滤，未提供独立年龄效应估计
- [simulator.py](https://github.com/punyamodi/binary_market_engine/blob/da3a599422aeca3af677ccd816882a542633df26/simulator.py#L14-L42)对煽动性关键词强加YES负漂移；漂移不依赖上市年龄，不能验证新市场独有优势
- [main.py](https://github.com/punyamodi/binary_market_engine/blob/da3a599422aeca3af677ccd816882a542633df26/main.py#L108-L122)的live入口取初始快照后仍调用模拟未来路径。已提交12.01% ROI、80%胜率、6.79 Sharpe来自5个合成持仓，仅为来源演示输出
- [backtest.py](https://github.com/punyamodi/binary_market_engine/blob/da3a599422aeca3af677ccd816882a542633df26/backtest.py#L134-L157)的费率变量未进入实际现金扣款；[Kalshi解析](https://github.com/punyamodi/binary_market_engine/blob/da3a599422aeca3af677ccd816882a542633df26/fetch_data.py#L118-L148)也没有提供买NO所需的真实ask

这补齐了“有人提出年龄过滤假说”的出处，却没有建立区别于静态价格校准或新闻效应的独立年龄机制。不能称已证伪所有早期市场效应，也不直接等同C09。需要真实首次交易/公开时刻、同价格和类别的年龄对照及可执行成本，才可重审。

本轮确实继续GitHub和X检索；这些新增X查询没有读到相关原帖正文，因此不增加原帖正文计数。来源结果、合成演示、机械核查和实际策略回测继续分开。
