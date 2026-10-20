---
id: dot-019
name_zh: 永续资金费现货对冲
name_en: Perpetual funding cash-and-carry
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: supplement
improves: A-A1-funding-carry
category: A
return_type: carry
instruments: BTC, ETH, SOL（现货 + USDT本位永续）
venues: Binance（Spot + USDⓈ-M Perpetual）
data: 已保存资金费汇总覆盖2024-01–2026-09，BTC/ETH/SOL各33个月、合计9,036行；官方月档免费免密钥；同步成交、mark与保证金路径未齐
test_2w: 复核33个月资金费分期报告并区分固定名义费用基准与完整持仓模拟；月份不自动独立，独立结果数未知；月度净现金流中位数≤0或累计<0为预设失败标准
status: 待核
confidence: 中
---

> 状态：待核；仅申请补充评审，未获采纳或晋级。本稿保留既有完整对冲模拟缺口；2026-10-19补充固定名义资金费单项上界核查，不新增完整策略回测，不是交易建议。

## 一句话

研究买入现货并按同一标的币数量做空线性永续、收付浮动资金费的对冲机制；首笔费用须有结算前已成立的持仓，两腿退出与全过程资金约束尚需模拟。

## 钱从哪里来

正资金费由永续多头支付给空头，负资金费时空头反付。现货多头用于对冲标的币方向敞口；正溢价或多头拥挤是机制解释，不保证未来结算费率为正。资金费以外仍有基差、交易摩擦和保证金风险，不能把现金流收入当作完整策略利润。

## 规则

- **仓位与边界**：BTCUSDT、ETHUSDT、SOLUSDT 是三个分别评价的单币情景，一次只做一个币；总资本 5,000 USDT、单场所约 2,500 USDT，不借款。1,200 USDT 是已保存现金流筛的固定名义基准，不是已经验证可持续的头寸。
- **同币数量对冲**：仅研究 USDT 本位线性合约。若现货初始价格为 S0、买入数量 q=1,200/S0，空头同为 q；期货名义 q×F0 不必等于 1,200。要求初始期货抵押至少覆盖其实际名义，并把开仓费用和可用缓冲计入单场所预算；“1,200 现货 + 1,200 保证金≈2,400”只是忽略基差的简化，不能据此宣布全额抵押或通过资金门槛。
- **入场时序**：两腿持仓须严格早于首个 fundingTime 成立；上一个完整 1h bar 仅可作已知参考，不是可执行成交价。缺少成交与资金费资格证据时不计该笔首费；不可在结算同刻开仓又收该笔费用。
- **资金费归属**：空头条件现金流为 q_t×markPrice_t×fundingRate_t，正收负付。已保存筛只算 1,200×rate，没有逐次 mark 与数量路径；维持固定名义所需的调整换手未知。
- **持有与再平衡**：原稿“名义偏离 5% 或缓冲不足再平衡”仅为未验证规则假设；与固定名义现金流筛分开。实际调整费用按每次实际成交名义逐腿计，不能用季度数或月份数代替已发生的换手。
- **退出与费用**：两腿退出时分别记实际成交价、时点与费用，不能假设原子成交。一次完整往返的固定名义费用基准为四个腿侧，见成本节；实际基差与残余方向敞口另记。
- **规则缺口**：合约最小名义、数量步长、资金费上下限及间隔历史、保证金档位、维持保证金、强平和费用规则未齐。样本观测为 8h 不代表未来或所有合约永远为 8h；初始 1x 不保证全程无清算。

## 证据

本稿转述原研究已保存的官方资料、来源 README 和资金费汇总。公开页面的访问日期均沿用 2026-10-19 UTC 原记录，本次仅核对保存文本与算术，未重新打开网页或执行研究代码。

**既有资金费现金流汇总，非完整对冲回测**

- 保存汇总记载：三币各 3,012 行、合计 9,036 行，2024-01-01 00:00 至 2026-09-30 16:00 UTC；各 33 个月、共 99 个官方月包；无重复或缺槽，观测间隔 8h，最大时间戳抖动约 26ms。这是既有数据完整性检查，不是本次新验证，也不是独立交易数。
- 固定名义条件现金流为 1,200×rate；每个币单独评价，不把三币同时置于 5,000 组合。未计现货/期货价格损益、mark 名义变化、基差、保证金、清算及真实再平衡成本。
- 只挑正费率的 positive-only 列是事后 oracle，含未来信息，不作为可交易结果。

| 单币情景 | 结算观测 | 条件毛资金费 USDT | 负费观测 | 扣一次14.4费用基准后余量 USDT | 扣11轮158.4费用基准后余量 USDT |
|---|---:|---:|---:|---:|---:|
| BTC | 3,012 | 231.3466 | 446（14.807%） | 216.9466 | 72.9466 |
| ETH | 3,012 | 232.4547 | 471（15.637%） | 218.0547 | 74.0547 |
| SOL | 3,012 | 157.9115 | 941（31.242%） | 143.5115 | -0.4885 |

表中余量只是毛现金流减固定费用的算术，不是已实现或可交易净收益。11 轮是既有“每季一轮”预设费用情景，并非观测到 11 次交易；双倍该费用为 316.8 USDT，三币余量均为负。首个 00:00 结算已在汇总内，但尚未证明结算前持仓，因此不能把全表作为可执行策略收入。本文不年化、不报告策略 Sharpe 或最大回撤，也不把部署约 2,400 的分母冒充总资本 5,000 的收益分母。

**2026-10-19补充：资金费单项上界**

在完整1,004日、总资本5,000、每次空头名义≤1,200的条件下，免费事后只收正费的BTC/ETH/SOL上界简单年均贡献分别为1.804117%/1.845553%/1.806099%。更宽松的每次只持一个币、免费择最高正费率的上界为343.897116 USDT，简单年均2.500447%。这是允许完美预知的历史账本上界，不是CAGR或完整策略利润；只限制该名义规模的资金费分量，不排除更大规模、基差或其他收益来源。首费资格被放宽，原始时间网格与数值经独立复核。见[完整上界方法和边界](../notes/20261019-funding-only-upper-bound.md)。

**GitHub 来源自报，未核实**

保存的 README 描述 2020-01-01 至 2026-04-09 数据、entry 1bp / exit 0.5bp，以及每腿每边 taker 4bps、往返 16bps 的模型。§4 自报 BTC/ETH 年回报 9.0%/11.4%、18/14 笔、平均持有 38/58 天及 100% 胜率；原文强调未扣现金资金占用机会成本、样本稀疏，不能直接解释为本稿扣足费用后的年收益。所有数字均为来源自报，未核实、未复现。

同一保存文本自述 2026-08-24 修正过丢失 44% 资金费历史的时间戳 join 问题，并在 Limitations 承认价格时间索引存在前视、原结果不能原样重现。它只支持机制和待核问题，不证明该策略通过门槛；其条件入场和低费用假设也不能与本稿固定名义现金流表直接比较。

## 数据

- **公开原始月包**：[BTCUSDT 2024-01资金费月包](https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2024-01.zip)，同 URL 加 `.CHECKSUM`；保存研究以 BTC/ETH/SOL、2024-01–2026-09 的同类月包构成 99 包，CSV 定位 calc_time、funding_interval_hours、last_funding_rate。这里只转述既有读取与校验，不新增下载。
- **目录证据**：已保存 [BTC资金费S3列表](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/fundingRate/BTCUSDT/) 含 2020-01 起月档，但更早数据未纳入上述现金流筛；目录存在不能替代逐文件内容核验。
- **现货与对冲价格**：保存的 [BTC现货K线S3列表](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/BTCUSDT/) 含 1h 子目录；完整同步现货、永续成交和 mark 路径未齐，不能由命名模板推出数据齐备。
- **字段与访问边界**：保存的 [Binance资金费文档](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History) 给出 fundingRate、fundingTime、markPrice，并列出 fundingInfo / fundingIntervalHours。文档读到字段不等于已下载历史 mark 或间隔变更；本稿不调用受限接口、不登录。
- **缺口与统计状态**：实际历史费用、盘口/滑点、资金划转时延、稳定币折价、保证金与清算路径均未齐。backtest_count=0；observed_net_return=null；Sharpe/最大回撤=未知。[公开现金流方法](../notes/20261019-cashflow-data-screens.md)与[单项上界核查](../notes/20261019-funding-only-upper-bound.md)提供输入指纹和结果；全量原始数据本地保存。官方月包是原始来源，不能冒充完整策略审计。

## 两周内怎么检验

1. 预定检查现有 99 包与 CHECKSUM、UTC 时间戳、缺槽及重复，并区分文件完整性与成交可达性；只有完成同步价格和保证金路径后才进入完整策略模拟。本次整理未执行该流程。
2. 先按 33 个非重叠月份报告固定 1,200 名义资金费，作为现金流分期统计。若改做持仓模拟，用实际 q_t、mark、入出时点和负费归属；上一根 1h 收盘只提供历史信息，不能当成两腿成交。
3. 月扣 14.4 是另一项拟议费用基准，不能混入现有一次往返/11 轮结果后声称已实跑月度策略。月度入出、首费资格、实际调整换手和资金路径须重新建账；已有表格只保留其原费用口径。
4. 预设失败标准：月度费用版的中位月净现金流≤0、累计<0，或压力费用下失败；这只检验现金流假设。33 个月、三币和 8h 观测均不能自动凑成 30 个独立策略结果，必须审持仓 episode、共同 funding/行情依赖和分组；独立结果数未知，G6 不确定。

## 成本与容量

- **固定费用基准**：假设四个腿侧各成交 1,200，0.30%/腿侧，则 4×1,200×0.003=14.4 USDT；0.60% 压力为 28.8。11 轮基准为 158.4，双倍 316.8。它们是费用算术，既非真实 turnover，也非官方实际费率。
- **实际成交口径**：实际成本按逐笔成交名义×对应腿侧成本率累计，再加未覆盖摩擦；开仓和退出名义可能不同，固定 14.4 不能当真实成本上界。每次 resize 仅对实际 delta 成交计费，不用整仓往返替代。
- **初始与后续现金分开**：初始现金至少覆盖现货、按实际期货名义的抵押、当时开仓费用和可用缓冲；未来累计 14.4/158.4 不能全部加在初始本金上证明超限。后续费用及负费须按到账顺序扣减，不能提前动用尚未收到的 funding；资金/保证金路径未模拟。
- **容量边界**：忽略基差与开仓费的 1,200+1,200=2,400 方案距 2,500 只余约 100，实际缓冲须扣开仓费并按基差重算。三个同样方案约 7,200，既超过总资金也超过单场所边界；1,000 名义只是待验降规模方案，不是安全结论。剩余总资本不能默认跨过单场所限额补仓。
- **机会频率**：8h 结算不是 8h 一次可交易独立机会；月度可执行机会数未知。预设每季一轮仅用于费用压力测试。全部回报门槛用总资本 5,000 与完整占用期间评价，不能据本表宣布达到 3% 组合腿或 8% 单独年化门槛。

## 风险

- **负费和状态变化**：保存汇总中 SOL 负费观测占 31.242%，2026 年至 9 月为 48.352%；只是该样本统计，不是未来概率。负费可持续，过去正现金流不保证未来收益。
- **基差与执行**：固定名义资金费未覆盖现货/永续损益；两腿不同步、价差、滑点、部分成交与价格背离均可令完整对冲亏损。
- **保证金**：以 1,200 简化名义计算，空头不利变动 5%/10% 对应约 60/120 USDT 浮亏；100 是额外缓冲，不是全部抵押，超过它不等于保证金耗尽或必然强平。现货浮盈是否能及时转成保证金、mark 与维持保证金均未模拟；不能据初始 1x 排除清算。
- **场所、稳定币与数据**：交易所对手方、USDT 折价、规则变更、资金费间隔变化、时间戳或数据缺失、钱包间流动性约束仍在。PM 风险与规则不适用。

## 改进了什么

本条改按 `kind: supplement`，`improves: A-A1-funding-carry` 归类。分类依据是 [known 中的 A-A1-funding-carry](https://github.com/yugao-tum/trdproj-bots/blob/bc5dd79aa7da5e07cdd3ed2d22a158ab620222fb/known/KNOWN.md#L9)（2026-10-20 UTC 核对，仅含名称，不含既有规则或绩效）。现货多加永续空收资金费，正费筛选和名义约束只是变体/证据。

本条提供的研究补充：整理固定名义的历史资金费现金流上界与完整对冲所需的资金、保证金和基差约束；该上界不是完整策略净收益。

补充材料相对既有实现的新增性与采纳价值交由评审判断；本次申请补充核对，尚未采纳，不主张新机制、已证改进或盈利，提交状态为待核。

浮动资金费现金流与 C20 固定到期基差是不同机制描述，但不代表已完成全仓库查重或获准分别计分。

## 2026-10-20 补充送审说明

- **送审目的与增量**：向 `A-A1-funding-carry` 提交固定规模的必要条件反证，不申请新策略或盈利资格。对完整1,004日、总资本5,000、每结算空头名义不超过1,200的历史窗，即使放宽为免费事后择三币最高正费率，上界也只有343.897116 USDT、简单年均2.500447%。负面价值是排除“这一规模仅靠资金费即可贡献3%/8%”的希望，避免用部署本金、正费样本或更短期间夸大收益。
- **可复算的内容**：[上界笔记](../notes/20261019-funding-only-upper-bound.md)列出单币及切换oracle公式、99个官方月包的范围/来源模板、输入SHA256与分母。按完整UTC网格重建后，可逐笔复算正费和、max上界与简单年均；笔记记载的17项测试及独立实现核对是既有机械检验，不是本次新增回测。计算脚本和完整结果JSON未随该笔记公开，哈希不能替代缺失文件，不宣称完整一键复现。
- **不外推的边界**：首费资格被故意放宽；oracle不可交易，9,036行也不是独立结果。结论只限资金费分量，不否定更大名义、不同资本安排、基差/价格收益或未来路径；同步两腿、mark、保证金存活和真实净收益仍未证。
- **请评审核对**：上述有明确名义、时间窗和分母的上界，是否构成对已知资金费carry的关键约束补充。known未公开内部规则/绩效，无法比较胜负；当前仅待核，不预设补充采纳、收录或阶段分。

## 门槛自查

1. **机制说得清：满足。** 说明正费由多头付给空头、负费反付，以及对冲与基差风险；这不等于全部场所规则已核。
2. **有免费数据能检验：不确定。** 既有汇总有 33 个月实际资金费及官方免费来源，满足资金费观测长度；同步完整对冲、mark、保证金和费用数据未齐，不能把目录存在当完整数据通过。
3. **小资金能做：不确定。** 总资本 5,000、单场所约 2,500 已写清；1,200 固定名义只是近似，实际 q×F 抵押、开仓费、动态缓冲及最低合约要求未验。
4. 不重复：同机制补充，非新策略——对应 `A-A1-funding-carry`；补充材料的新增性与采纳价值仍待核，不据 dot 内部区别主张全局新颖性。
5. **扣成本后粗算够用：不确定。** 14.4/158.4 是固定费用基准，表中余量不是完整净策略回报；年化、组合腿相关性和达标情况均未证，observed_net_return=null。
6. **两周内能检验：不确定。** 33 个月是报告分期，独立结果数未知；尚缺共同依赖审计、持仓路径和完整策略 PnL，不能声明已有 30 个独立结果。
7. **出处可查：不确定。** 机制、字段和原始数据有保存的公开来源与位置；来源自报未复现，完整规则和可公开访问的冻结现金流输出仍有缺口，不能整体判为满足。

## 出处

- https://github.com/zwmjj/funding-rate-arb — 原访问 2026-10-19 UTC — 已读（既有抓取正文，本次读保存文本）— README Data、§4、Limitations；所有性能与修订数字为来源自报，未核实、未执行代码
- https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2024-01.zip — 原访问 2026-10-19 UTC — 已读（既有研究下载与校验记录，本次未重下载）— CSV 的 calc_time、funding_interval_hours、last_funding_rate；三币2024-01–2026-09同类月档是现金流汇总输入，汇总输出公共链接未提供
- https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/fundingRate/BTCUSDT/ — 原访问 2026-10-19 UTC — 已读（保存 XML）— 月档 Key；目录存在与数据完整性分开
- https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/BTCUSDT/ — 原访问 2026-10-19 UTC — 已读（保存 XML）— CommonPrefixes 的 1h 子目录，未据此认定同步对冲数据齐备
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History — 原访问 2026-10-19 UTC — 已读（保存正文相关段落）— Get Funding Rate History 的 fundingRate/fundingTime/markPrice，Get Funding Rate Info 的 fundingIntervalHours；不是历史 mark 下载记录
- https://www.binance.com/en/fee/futureFee — 原访问 2026-10-19 UTC — 摘要/读取不足（保存内容仅导航壳）— 未取得可核费率，0.30%/0.60% 是研究费用假设，非该页证实数字

## 2026-10-20 r20：实际结算 mark 与固定数量现金账补证

本次另行冻结两个购买预算（1,250/625，均含现货买入成本）及0.30%/0.60%成本情景，实际取得9,036笔资金费结算mark，和99个月包的精确时间/费率一致，并补齐1,004日现货、永续、mark观察。每币严格排除入场同刻首费，资金费使用q×真实mark×rate。旧1,200固定名义上界及初始全额抵押测试原样保留，不把新情景回填成旧配置通过。

条件账中BTC/SOL的1,250预算出现负保证金，其正终值不可作为可执行收益。ETH1,250在主成本下场内2,500分母CAGR4.5238%、总5,000分母2.3057%；压力成本腿CAGR4.2918%。日高保证金界非负但未核实历史清算规则，主成本后可容纳维持保证金及其他平仓摩擦约2.5144%的条件名义比例，不是已验证档位。日频趋势参照相关−0.0513、月频+0.3822，不能只选低者宣布低相关。

已完成独立现金账与资金守恒复现；真实数据、条件模拟和实际可执行结果严格分开。3,011个共同结算事件或1,004个日聚合是待评审认可的操作性结果计数，不是IID或独立策略数。历史成交、数量过滤、维护率及稳定相关性仍有缺口。保留现有supplement待核身份，不新增条目/待核、不主张收录、已证改进或阶段分。详见[完整证据与全部12情景](../notes/r20-funding-settlement-evidence.md)。

## C19 / dot-019: r21 historical context and prospective protocol

This is a single supplement to existing C19, not a new mechanism, entry, pending item, official score or stage change. Status remains 待核. ETH was selected post hoc from the retained twelve r20 cases.

Two official historical notices now bound plausible low-tier ETH maintenance-rate scenarios: [2 January 2024 notice](https://www.binance.com/en/support/announcement/detail/d75c5ca94f704e96a6a4e55ffddfd65d), effective 24 December 2023 09:35 UTC, reports a 0.50% old low tier and 0.40% new low tier; [17 August 2025 notice](https://www.binance.com/en/support/announcement/detail/8e428625ebeb4cc7ae8678026846095c), effective 19 August 2025 06:30 UTC, reports 0.40% at 0–300,000 USDT before and after. These documents neither establish every historical bracket change nor give the maintenance deduction. The later [official FAQ](https://www.binance.com/en/support/faq/detail/360033162192) allows small unannounced adjustments; absence of announcements cannot prove continuity. The January notice is retrospective; the August page was subsequently revised.

Four ETH allocation/cost cases were independently recomputed over 1,004 days under fixed 0.40% and 0.50% scenarios, assuming maintenance deduction D=0, with 12,048 exact daily comparisons. For the 1,250-USDT allocation, 0.40% maintenance and the extra assumed close-cost reserve, the minimum conditional surplus is 57.2220 USDT at 0.30% friction and 48.9536 USDT at 0.60% friction, on 24 August 2025. These are source-supported conditional simulations, not continuous risk-history reconstruction, actual liquidation survival, true fills or qualification. Spot is not automatically derivatives collateral. ExchangeInfo's ignored maintMarginPercent and liquidationFee are not substituted for maintenance history or trading commission.

The prospective ETHUSDT protocol is implemented and offline tested, with 5,000 total virtual capital, 2,500 venue capital and 2,500 external reserve. A 1,250 spot budget includes assumed 0.30% friction; the equal-quantity short uses bid-depth VWAP, spot uses ask-depth VWAP, and quantity is floored to the shared valid lot grid. The 0.60% sensitivity retains the same quantity. Current market-rule acceptance remains unverified where a five-minute-average notional filter is unavailable.

No entry or prospective funding event has been created by this appendix. Existing quotes are feasibility-only. Root must first freeze configuration, implementation, tests and criteria hashes, then explicitly authorize a new paired observation. Entry validation requires both requests after the lock and a complete pair envelope/response age of at most five seconds; absent spot exchange-event time remains unknown. A snapshot that fails cannot be refreshed repeatedly within the hourly budget.

Only actual funding timestamps strictly after entry accrue signed cash. Deduplication, cash, cursor and request completion share one atomic checkpoint; restart verifies artifact hashes and recomputes cash from events. Explicit rate limits, unresolved requests and source denials block retries. The first 30 distinct timestamps support a descriptive review, not IID inference, annualized profit, an official score or a forced stop. Full-cost quote liquidation estimates retain both capital denominators; absent exit quotes yield null, not mark-price replacement. Observed nonpositive margin permanently invalidates the feasible-path claim. There is no seven-hour cutoff and no real account, order, wallet or credential use.

### 冻结后状态更新（2026-10-20 12:17:36 UTC）

上节“尚未创建”是协议冻结时点事实。冻结后已于12:14:33.688 UTC用新公开配对报价建立0.522 ETH纯虚拟参考，实际资金费事件仍0，无订单/账户/实际成交，不自授模拟盘阶段。独立46项保存后复核通过；旧模板描述字段有明确追加纠正，1319ms配对间隔及新来源hash已核，原件不改。详见[当前补证说明](../notes/r21-c19-margin-forward-evidence.md)。

## 2026-10-20追加：固定12情景的依赖、集中度与成本余量

本轮不新增市场数据或重选配置，仍用r20的真实结算mark、固定2024-01-01至2026-09-30窗口、全部12资本/费用情景；原1200基线及r20/r21冻结成果保持。见[同轮完整报告与聚合](../research/r22/REPORT.md)。

- ETH1250/每边0.30%：每日相关−0.051283与33个月相关+0.382215并列，不以较好频率证明低相关。预注册配对循环块bootstrap，块长1/3/6、各5000次：月相关95%区间分别[0.000981,0.640473]、[−0.007496,0.570370]、[0.026257,0.573468]。规则未给低相关数值门槛，也未要求相关必须为零，不能自动否决或自动认证。
- 9036来源行中9033个合格资产付款，分属3011个共同结算时间戳组、1004日/33月，不把它们算作独立投资结果。三个最高正资金费月均为2024年3/11/12月，分别占BTC/ETH/SOL净资金费29.38%/34.20%/52.65%；同月三币现金相关约0.87–0.95。去掉月份只是加法集中度诊断，不是可交易反事实。
- ETH1250的3%场内2500分母CAGR附加成本空间：主摩擦111.705846 USDT、压力94.509710 USDT。折为在全部四个冻结执行名义额上均匀增加单边成本，分别205.839470/174.673181 bps；是在已有0.30%/0.60%之外，不是建议费率。零利润现金余量323.314430/306.118294另列，不能混为3%门槛。BTC625主情景仅1.666641 USDT。公式并非新发明，12个固定C19数值是新增描述性应用，不是新增机制。
- 原端点基差价差仅占各情景净额0.532886%–0.643815%。把该价差归零的F−C仍为117.820062–424.277425 USDT；对两个终止腿额外10/30/100bps的36个固定敏感性仍端点为正。仅说明本固定终值的资金费/基差归因，不证明期间生存、可执行性或抗危机。BTC/SOL1250四个保证金失败情景始终标为不可执行反事实，不能被终值压力测试救活。

全部12情景及失败标签保留。维护保证金连续历史、实际成交与真实账户资金占用仍未知；历史条件账与纯虚拟前向观察分开。无官方分数、阶段晋级或新机制，仍为原dot-019的一条supplement待核。更严格的每日2500市值上限只是敏感性，不能把GUIDE“约2500”擅自解释为强制逐日平仓要求。


### 2026-10-20 C19历史保证金补证（claim 8a8f7ffd）

本附录只增证，不替换旧冻结12配置/失败终值，不增加机制或entry，不改变单独冻结的forward数量协议。

首先收窄可执行性：全部1250配置在明确选定1x、原价格及经济费用假设下初始成本不等式失败（无缓冲缺口0.675875–1.079159 USDT）；625对照通过此单项不等式。真实杠杆/费率/订单接受未知，条件失败不等于历史拒单。GUIDE现货对冲例外仍有效，不能发明抵押比必须全程≥1的规则，也未缩量修复。

官方历史锚点可取得，但MMR/cum/档位完整连续历史未补齐。ETH固定最大名义额2706.261779低于已证50,000及300,000首档cap，不代表未知期间cap恒定。在已取得的ETH 2025-08-24共1440根1m mark记录及分钟现金模型中19:12高点在三笔精确毫秒资金费之后，主配置该日最小权益由日界下界76.165880890收紧至76.948608952；cum=0条件MMR上限2.843354236%，扣0.4%假设MMR与另列0.3%关闭储备余58.004776497。只补单日时序，不认证全历史清算生存。

BTC1250原零权益首败2024-11-13、SOL1250原零权益首败2024-11-11保留；SOL1250在0.5%、cum=0的条件维护规则下已于2024-03-18失败。历史实际清算日期仍未知。单个ETH资金费mark低于日低0.0075异常保留，并集日高不变，不影响本批空头下界。清算后费用不冒充触发MMR，现货不自动补逐仓现金。

四分类为官方锚点支持／条件区间通过／未知／已失败（注明命题）。详见[同批整合报告](../research/r23/REPORT.md)、[12配置聚合](../research/r23/INDEPENDENT.json)及[复现输入说明](../research/r23/INPUTS.md)；新证据不计作新机制、认可分或forward样本。

## 2026-10-20 16:00 UTC：首笔实际结算对应的虚拟资金费

冻结的0.522 ETH虚拟参考，绑定公开历史接口2026-10-20 16:00:00.006 UTC唯一结算事件ETHUSDT:1792512000006，实际费率0.00007381、mark 2440.13000000，条件现金每个费用情景均为+0.0940153295466 USDT。只有一个事件，不能把两费用情景当两次付款或相加；不是账户收款、成交或实际PnL。ETH路线来自已见历史结果的事后选择，不是历史盲测；前瞻协议在12:14入场前冻结，数量在入场时固定，均早于16:00结算，并非看到首费后选仓。

在同一16:16:46.327 UTC退出报价下，扣齐四腿成本及价格损益后，0.30%/0.60%情景净额分别为−15.3878365104534/−30.4938483504534 USDT，仍为负。此处扣除资金费前后的比较使用相同报价，不把15:15至16:16价格变化归因给资金费。来源另行显示下一结算时间为2026-10-21 00:00 UTC，不以固定8小时推测、不以lastFundingRate预记现金。

仅追加首事件证据，非新研究轮、新机制、新条目或阶段晋级；原历史失败、1x初始成本限制、未齐维护档位和执行证据保持。单事件不证明IID、30独立结果、盈利门槛或真实账户资格。详见[报告](../notes/20261020-c19-first-forward-funding/REPORT.md)及[精简来源与算术证据](../notes/20261020-c19-first-forward-funding/EVIDENCE.json)。原始盘口、活动checkpoint及18个冻结文件均未上传或修改。
