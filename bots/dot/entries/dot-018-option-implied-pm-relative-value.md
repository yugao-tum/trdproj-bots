---
id: dot-018
name_zh: 期权隐含分布对PM相对价值
name_en: Deribit implied distribution vs Polymarket binaries
bot: dot
date: 2026-10-19
market: polymarket
pm_category: crypto
kind: new
improves: -
category: S
return_type: direction
instruments: PM 二元价格市场（模板 “Will the price of Bitcoin be above $X on <date>”）；只以 Deribit BTC 期权为定价参考，本版只研究固定时点 above 二元市场，不含 range/barrier 或实际期权对冲
venues: Polymarket（纸面单边）；Deribit（只读定价参考）
data: 免key：PM gamma/CLOB/data-api（规则、费率、价格史、结算点）；Deribit public API（index_price 原研究 2026-10-19 实测返回 81846.23；期权链端点按来源 README，历史期权快照覆盖未验证）；本轮未取得免费免密钥 PM 历史可成交 L2，前向记录尚未启动
test_2w: 计划前向记录 PM 单边实际 ask 和 Deribit 对齐快照；每份偏差减 r×A×(1−A) 与报价外滑点，ask不再扣半价差；同源同到期多桶为1候选簇、结算后才计结果且须检查跨簇相关性；费后均值≤0或不足30独立完成结果则失败；尚未启动
status: 草稿
confidence: 低
---

整理说明：本稿是已保存公开证据的操作员侧校订，没有新增抓取、成交或回测；所有采集方案仍为计划。

## 一句话

把 Deribit 期权隐含概率当作定价参考，在严格匹配结算口径后，分别比较 PM YES/NO 的模型侧概率与实际 ask、每份费和额外滑点；本版仅提出 PM 单边纸面假设，不声称已恢复完整风险中性密度或锁定利润。

## 钱从哪里来

同一天同一标的，期权市场（机构、连续监测、指数结算）与 PM（散户为主、oracle 结算、二元赔付）参与者结构与摩擦不同，理论上同一区间的概率可以定价不同，若实际买入侧价格向模型参考价收敛且覆盖成本才可能产生收益。但风险中性概率 ≠ 真实概率：差价可能只是风险溢价，而不是错误定价；不对冲就是方向赌注，理论上用期权价差近似 digital 会涉及长短腿、pin risk、结算基差和更高成本；本版不包含该对冲。来源 README 自述 “This is a pricing tool, not an arbitrage bot. Edge is statistical, not risk-free.” —— 谁在付钱、是否持续，均未验证。

## 规则

- PM 费用（已保存官方文档，2026-10-19）：总费用 F=C×r×A×(1−A) USD，C 为份数、A 为该腿实际成交价；每份费 f=F/C=r×A×(1−A) USD/share；费用/名义本金 F/(C×A)=r×(1−A)。只用每份费与概率价格差相减，不混本金比例。当前示例 crypto r=0.07，taker 收费；maker 的零费/返佣不计入本版。费用精度按原文五位小数、最小 0.00001 USDC；无成交回执。历史费用不能直接套今日费率。
- 市场级 feeSchedule（gamma 实拉 2026-10-19，下述 3 个真实市场）：`{"exponent":1,"rate":0.07,"takerOnly":true,"rebateRate":0.2}`，feesEnabled=true，feeType=crypto_fees_v2。
- 3 个真实市场 slug（gamma-api 实拉，global Polymarket/UMA 市场，**不是美国站，规则不得迁移到其他站点**）：`bitcoin-above-80k-on-october-20-2026`、`bitcoin-above-82k-on-october-20-2026`、`bitcoin-above-84k-on-october-20-2026`（同一 event `bitcoin-above-on-october-20-2026`，outcomePrices 0.9435/0.485/0.045，endDate `2026-10-20T16:00:00Z`）。
- 结算规则原文要点（上述市场 description，逐字摘）：以 “Binance 1 minute candle for BTC/USDT closing at 12:00 in the ET timezone (noon) on the date specified in the title” 的 Close 是否严格高于标题价格；数据源为 Binance BTC/USDT 页面 “1m + Candles”；“Price precision is determined by the number of decimal places in the source”。标注：无 “at any point” 措辞、无独立舍入条款、无缺数据条款（均未读到）。
- 时区/日界：标题日 ET 12:00 = 16:00 UTC（实拉 endDate 一致）。跨市场对齐注意：另一来源（FinkBig README**已读**）用文件名推断 PM 到期 18:00 UTC、Deribit 到期 08:00 UTC（同一 end date）——两边到期时点不同，直接比较会混入时间差，必须先对齐口径。
- 交易假设固定为 PM 单边纸面持有至结算，Deribit 只作只读定价参考；不买卖期权、不声称 call spread 已复制。单场所本金、入场费及风险预留总计≤2500 USDT，总资本5000，不加杠杆。真实深度未测，预算不等于容量。来源默认 min-edge 3%、min-liquidity $10k 只是来源参数，不作为本研究经过验证的门槛。
- 分侧计算：设模型参考 YES 概率 q，YES ask=A_Y，NO ask=A_N。E_Y=q−A_Y−0.07×A_Y×(1−A_Y)−s_Y；E_N=(1−q)−A_N−0.07×A_N×(1−A_N)−s_N。s 是报价以外的执行滑点；ask 已含 crossing，不再扣半价差。E>0 只是模型定价偏差，q为风险中性参考不是真实胜率，因此不构成实际正期望证明。
- 模型限制：N(d2) 仅是平坦波动率等特定 Black–Scholes 假设下的 digital 概率；逐行权价套不同隐含波动率的 N(d2) 不自动恢复完整 RND。有微笑时须对满足无套利条件的期权价格曲线求行权价导数、处理折现与边界，二阶导数对应密度。本研究未实现/验证这些步骤，不能声称已得到完整分布；未完成口径与模型验证前不产可交易信号。

## 证据

- avion23/deribit-polymarket-scanner README（原研究已读 2026-10-19）：方法 digital=N(d2)、range=digital call spread、barrier=GBM first passage；数据为 PM `/events` + Deribit `/public/get_instruments`、`/public/get_order_book`，均免key、只读。Caveats 原文要点：对冲成本/pin risk；极值行权价外推（标 ~）；barrier 假设连续 GBM 监测而 PM 按 1 分钟 K 线结算→模型概率会略高；结算基差（PM oracle vs Deribit 指数）；vol 快照数分钟内即可能过期。**无收益/Sharpe/回撤数字；来源自报，未复现。**
- FinkBig/THESIS_deribit_probability_analyzer README（原研究已读 2026-10-19）：Breeden-Litzenberger 逐小时 RND + PM 桶概率归一化对比；PM 到期 18:00 UTC、Deribit 08:00 UTC（由文件名推断）。先前草稿转述单到期报告为 938 行/7 桶，但给定证据记录未提供可定位报告链接或行数核验，本次撤下该数作为证据。无论有多少逐小时行，同一到期多个桶仍只有一个候选事件簇，不能扩成独立样本。**无费后收益数字。**
- 原研究实拉（2026-10-19）：gamma public-search 返回上述 3 个活跃市场（同 event、同数据源、同结算时点）→ 尚未结算，只是 **1 个候选事件簇、0 个已完成结果**，不是 3 个独立结果。Deribit `public/get_index_price?index_name=btc_usd` 免key返回 okay（index 81846.23）。
- 收益/Sharpe/最大回撤：未测（未知）；backtest_count=0。
- 检索旁证（**摘要**，未开正文）：FinkBig/probability_backtester_v1（“Polymarket-Deribit 套利”回测器）；TenghanZhong/polymarket-data-scraper（ccxt 拉 Deribit 全期权链 + PM 日志）；polybacktest/convexlake（第三方汇总/付费数据，仅记录不采用）。

## 数据

- PM：`https://gamma-api.polymarket.com` 提供市场规则、feeSchedule 与 endDate；CLOB `https://clob.polymarket.com/book` 是当前盘口，`https://clob.polymarket.com/prices-history` 是价格史；`https://data-api.polymarket.com/trades` 是成交，不是价格历史接口。价格史末点不能自动当正式结算，需另核最终结算状态与来源。当前资料未提供历史可执行 L2，只能规划前向记录。
- Deribit：`/api/v2/public/get_instruments`、`get_order_book`（来源 README 给出）、`get_index_price`（仅此 index 端点原研究实测免key可用）；历史期权成交/波动率面免key的完整覆盖：**未验证**。
- 缺测项（如实列出）：PM 历史盘口与滑点缺测，不能默认为零；本次只搜索 bitcoin，未验证 ETH 对齐市场；Deribit 历史 vol surface 快照可得性未知；缺数据/异常结算条款在市场规则中未读到。

## 两周内怎么检验

前向仅为未启动计划。先冻结模型、结算口径和快照时点，再同步记录 PM 两侧 ask/bid、深度、当时费率和 Deribit 对齐的期权价格；同结算源、同到期的多个桶只记一个候选簇，正式结算后才计完成结果。相邻到期/多币共享行情驱动仍需聚类，30 个时间戳不保证独立。主版只做 PM 单边纸面，按实际 ask 加每份费、额外滑点记账，若有退出需另计出口费。失败条件为预注册费后样本均值≤0，或两周不足30个有效独立完成结果；模型概率偏差本身不是真实期望收益。历史成交只能作代理敏感性分析，缺历史 L2 时不能用代理替代可成交回测。任何实现须自编审核后才运行，本次未执行来源代码。

## 成本与容量

- PM 自算费示例：A=0.55 时 f=0.017325 USD/share，本金费率3.15%；A=0.30 时 f=0.0147，本金费率4.90%；A=0.90 时 f=0.0063，本金费率0.70%。例如假设模型 q=0.60、YES ask=0.55，模型偏差扣费为0.60−0.55−0.017325=0.032675 USD/share，未计额外滑点；不能减3.15%后再扣半价差，也不能把该模型数称实测净收益。
- Deribit 只读参考，本版无交易腿。若未来另设计 call spread，对冲一般涉及卖腿，须独立证明组合最大损失、保证金和资金路径，并计双腿 spread、手续费与交割成本；“只买期权”不能证明已复制 digital。
- 容量：PM 单市场流动性差异大（来源默认过滤 $10k，未验证）；单场所含费预算 ≤2500 USDT、总5000只是设计上限，实际容量未知；每月独立机会数取决于对齐的到期/结算源数量，未测。

## 风险

- **风险中性 ≠ 真实概率**：RND 之差可能全是风险溢价；无对冲时是方向风险，有对冲时是复制误差。
- 模型/复制误差：N(d2) 不等于已恢复微笑下完整 RND；本版未做对冲，理论 call spread 近似的 pin risk 不能据“只买期权”消除。
- 结算口径不一致：PM 用 1 分钟 K 线/自有 oracle，Deribit 用指数结算；连续监测 vs 离散观测使 barrier 类模型概率系统性偏高。
- 时间口径：PM 与 Deribit 到期时点不同（18:00 vs 08:00 UTC 一例），未对齐即伪信号。
- 独立性陷阱：同到期逐小时行/多桶只能是一个候选簇；尚未结算则不计完成结果，跨日和跨币相关性也须核。旧草稿938行/7桶未定位原报告，不作量化证据。
- 数据陈旧：vol surface 快照数分钟即过期；历史盘口与可成交价缺失。
- 规则迁移风险：本条规则读自 global Polymarket 市场与官方文档；不得迁移到美国站或其他平台。

## 改进了什么

不适用（kind: new）。

## 门槛自查

1. 机制说得清：**不确定**。定价路径与参与方差异可描述，但“谁付钱”未证：差价可能是风险溢价；来源自述非套利、无费后收益数字。
2. 有免费数据能检验：**不确定**。gamma/CLOB/data-api 与 Deribit public API 免key（index_price 原研究已验；期权链端点来源自报）；“≥30 个独立结果/≥12 个月”所需的历史期权快照与 PM 历史盘口覆盖未验证。
3. 小资金能做：**不确定**。本版仅PM单边、≤2500/场所含费预算；最大持有损失为实际支付价款加费，但真实深度、资金占用和成交未验证，未证期权复制。
4. 不重复：**不确定**。本轮未检索 known/ 与其他 bots 索引；只保留已有C18认领，不新增机制计数，完整查重待主审确认。
5. 扣成本后粗算够用：**不确定**。本批无可归属的费后验证；费用必须用 f=r×A×(1−A) 与每份概率差同单位；风险中性概率未转成真实胜率，PM深度、额外滑点与fill未测。
6. 两周内能检验：**不确定**。当前只有1个尚未结算候选簇、0个完成结果；前向未启动，现有路径未展示30个独立完成结果，但不能据一个事件断言所有历史/前向路径都不可能。
7. 出处可查：**不确定（部分完成）**。scanner README、FinkBig README、PM 官方费率文档、gamma 实拉（含 3 个真实 slug 与 feeSchedule）、Deribit 实测均标注访问日期与阅读程度；性能类宣称全部标“来源自报，未复现”。

## 出处

- https://raw.githubusercontent.com/avion23/deribit-polymarket-scanner/main/README.md — 访问 2026-10-19 — 已读（What it does / Data sources / Caveats 节）
- https://raw.githubusercontent.com/FinkBig/THESIS_deribit_probability_analyzer/main/README.md — 访问 2026-10-19 — 已读（Data Sources / Setup 节，PM 18:00 UTC vs Deribit 08:00 UTC）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-19 — 已读（fee 公式、crypto 0.07、maker rebate 20%、5 位小数舍入、最小 0.00001）
- https://gamma-api.polymarket.com/public-search?q=bitcoin+above — 访问 2026-10-19 — 已读（JSON；3 个活跃市场 slug、description 原文、feeSchedule、endDate 2026-10-20T16:00:00Z）
- https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd — 访问 2026-10-19 — 已读（免key实测返回 index_price 81846.23）
- 证据缺口：旧稿所称 FinkBig 单到期938行/7桶报告未在给定记录中定位公共原报告；本次不把该数字作为已核证据，README链接只支持方法与到期推断，不能替代报告
- GitHub 检索旁证（websearch “FinkBig Deribit Polymarket 938 rows 7 buckets”，2026-10-19）— 摘要：probability_backtester_v1、TenghanZhong/polymarket-data-scraper；付费/第三方站点 convexlake、polybacktest 仅记录，不采用
