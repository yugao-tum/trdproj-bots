---
id: dot-002
name_zh: 集合预报误差校准
name_en: Ensemble forecast error calibration
bot: dot
date: 2026-10-19
market: polymarket
pm_category: weather
kind: new
improves: -
category: S
return_type: direction
instruments: 某城某日最高温整数分档（YES/NO）
venues: Polymarket
data: Open-Meteo Previous Runs/Single Runs 公共预报归档；31/51 真成员历史未确认；Gamma/CLOB 规则和盘口；结算只用市场指定 NOAA hourly whole-degree 源、缺测才 WU；IEM/CLI 仅代理或异站参考；历史可成交盘口与实际发布时间未齐
test_2w: 主版本为 D-1 00Z run、08Z 决策的固定多模型加经验残差方案，先验证版本和可得时间；历史仅校准，前向采集尚未启动；独立天气事件须聚类，30 未证；费后均值≤0、Brier不优于预注册基线或独立结果<30即失败
status: 草稿
confidence: 低
---

整理说明：本稿是已保存公开证据的操作员侧校订，没有新增抓取、成交或回测；所有采集方案仍为计划。

## 一句话

用决策时已收到的固定多模型预报和站点历史经验残差给温度档定价，分别比较 YES 和 NO 的模型概率与各自实际 ask；只有扣每份费及报价之外的滑点后仍为正才进行纸面模拟，持有至结算。

## 钱从哪里来

- 假设付款方是未校准网格到机场站点偏差、集合离散度或未及时更新预报的报价对手。公开预报需要加工，但这不证明报价对手存在可交易错误
- under-dispersion、站点偏差和更新速度可能影响定价；持续性及扣费后优势均待验证，不能由模型较准确推出可盈利
- 本条是预测机制假设，不是结构套利；市场可能已经充分计入这些数据

## 规则

### 市场与结算口径（global）

- NYC：highest-temperature-in-nyc-on-october-19-2026，11 档，id 5798034–5798044，站 KLGA，整 °F；按 NOAA timeseries 的 Temp 列、Show Hourly Data 中观察日的最高读数
- London：highest-temperature-in-london-on-october-19-2026，11 档，id 5795606–5795616，站 EGLC，整 °C；按该市场指定 NOAA timeseries 的观察日最高读数
- Seoul：highest-temperature-in-seoul-on-october-19-2026，RKSI、整 °C；前轮记录在 2026-10-19 16:39Z 为 closed，本次未重抓，规则与日界仍待复核；不是已取得的有效样本
- 观察日按站点本地日暂定，源页面时区尚待确认。按此假设换算：NYC 2026-10-19 日为 04:00Z 至次日 04:00Z；London 为前日 23:00Z 至当日 23:00Z；Seoul 为前日 15:00Z 至当日 15:00Z。Gamma endDate=12:00Z 不是日界证明
- 采用源页面显示的整度标签，不把小数 IEM/API 数值擅自重舍入成正式结算标签。到观察日次日 23:59 ET 无 NOAA 数据才使用 WU Daily Observations；仍无数据则按规则最低档结算。各城该缺测截止统一用 ET
- 正常结算：次日首数据点发布与观察日次日 23:59 ET 孰早。普通修订：到次日首数据点发布为止。技术/运营错误或未授权干扰导致明显错误的可结算数据：可从原始发布时起另留开最多 7 个日历日（ET）等待更正，逾期平台澄清。三条不能合并成一个截止
- 美国站 FAQ 的 CLI、次日 8:00 AM ET 与 KNYC Central Park 口径不适用上述 global 市场。IEM ASOS/NWS CLI 只能作代理核对，不能替换 KLGA/EGLC/RKSI 指定结算源

### 冻结的纸面主版本（设计，尚未实施）

- 时间只用 D-1 00Z 初始化的单次 run，在 D-1 08Z 做一次决策；不混用 12Z 或 D-2/D-3，也不看结果挑时点。全球模式通常需 4–6 小时计算/分发只是文档范围，不是实际可用性保证；只有 08Z 前真实抓到并保存接收时间戳的 run 可用
- 模型池固定为原方案的 GFS、ECMWF IFS HRES、ICON、GEM、Météo-France 五个确定性模式，等权构造 mini-ensemble，不能称 31/51 成员集合。具体接口 model ID、版本和同一 run 完整覆盖尚未核定，必须在采集前冻结，否则不启动；缺任一模式则跳过，不事后换池
- 统计方法固定为经验残差校准，不保留 EMOS/spread inflation/t 分布择优菜单：取五模型预测日最高温的等权均值，加该站此前 180 个日历日内同版本预测与正式标签的经验残差；至少 60 个完整匹配日才评估，不足则跳过。180/60 是预注册设计参数，不是实测样本量；该数据目前未齐。按源显示单位映射各档，映射未核则不产交易信号
- 设模型 YES 概率 p，YES 实际 ask 为 A_Y，NO 实际 ask 为 A_N；分别计算 E_Y=p−A_Y−0.05×A_Y×(1−A_Y)−s_Y，E_N=(1−p)−A_N−0.05×A_N×(1−A_N)−s_N。s 为报价之外的滑点/深度损失；ask 已含 crossing，不再加半价差。YES ask>p 不能推出 NO 便宜，严禁用绝对值价差选侧
- 主版本固定只在相应 E>0 时纸面买入并持有至结算，不做未建模的择时提前退出。单市场含本金、费用和风险预留 ≤$300，单城日 ≤$600，三城合计 ≤$1,500，单场所全部未平仓含费预算 ≤$2,500；不加杠杆。Kelly 未校准，不采用自动 Kelly 放大
- 同站同日多档和多个 lead 不加独立计数；同天气系统、邻近城市与连续日须聚类。停止新增记录/仓位不保证已持仓损失可被某个日止损截断

## 证据

- AadiXD README 已保存正文（2026-10-19）：自报 2026-03-28 至 04-03 七天 63 个结算 paper 仓位、52W/11L、82.5%、+$806.49、deployed $2,264.15、ROI +35.6%；60 NO/3 YES，Houston 六笔 +$623.53。paper 使用实时 CLOB mid，0.5–2pp 实际 spread 未计，未说明手续费。来源自报，未核实；同城同日多档不独立，不能当费后收益
- 同一 README 自报 2026-04-05 有 18 个 live 仓位、八城、未结算，没有 live P&L。60/63 买 NO 不证明低价 NO；冷门 YES 的互补 NO 常可能高价，必须检查实际成交价
- MihirM9 README 已保存正文：明确没有 audited live P&L、forward-test equity curve 或 canonical backtest scorecard，只提供方法；这是该来源的证据缺口，不能推广为所有同类项目都无业绩
- 搜索摘要提到 lukasjagnesak 的 31 GFS/51 ECMWF、EMOS、20% inflation 与 8% edge；ElPatron3333 的 3°F spread gate；kshitij406 的 multi-model/WU tracker。仅摘要，未读正文，均不作本方案参数或业绩依据
- Open-Meteo 已保存文档：Previous Runs 的 previous_day1/2 对应 valid time 前 24/48h，最多七天；多数模式自 2024-01，GFS 2m 自 2021-03。Historical Forecast 是拼接 run 前几小时，不能恢复任一次完整发布；Single Runs 多数模式自 2026-04-02，ECMWF IFS HRES 自 2024-03-14。31/51 成员级历史未确认。预报初始化/valid time 不等于当时实际接收时间
- 前轮公开来源审计转述：kevinbadi 站点偏差 −1.8°C（4/14）与约 −1.0°C（4/16）；windgeek 自报 111 笔净 −$62.51；natestokens 23 笔 +$77.01。未重新抓取且未复现，不用于证明本方案收益
- observed_net_return=null，Sharpe=null，最大回撤=null，backtest_count=0；没有完整盈利回测或已运行的前向采集

- 后续已保存数据状态（数据报告尚未公开，访问日志的 2026-10-19/20 日期冲突待核）：市场盘点为28行、15个事件slug，混有不同天气模板，不是28个本策略结果；30个候选观测行是IEM代理，其中三个末日不完整、另一个日缺小时。只有NYC 2026-09-14的Gamma对象已核`umaResolutionStatus=resolved`与76–77°F桶，且没有独立UMA链上审计。三城同日的previous_day1最大值来自BestMatch、非指定GFS，也非一个固定起报快照；NYC的22.5单位是°C（72.5°F）。这不是30个正式结算标签、独立事件或as-of可交易结果；前向仍未启动

## 数据

- 预报归档：Previous Runs 与 Single Runs 官方文档及公开接口见出处。前者固定 lead 逐小时序列可能来自不同 run，离线取日最大值不等于 D-1 08Z 的同一可交易快照；历史校准结果不能冒充主版本 as-of 收益回测
- 正式标签只用市场指定 NOAA timeseries：KLGA、EGLC、RKSI；缺测才按该市场规则 WU fallback。IEM 的 valid time 是观测时刻，不能证明发布/入库时间，CLI 也不能替代 global 标签
- 市场：Gamma 的规则、feeSchedule 与结算状态需逐场核；CLOB /book 是盘口，/prices-history 是价格史；data-api /trades 是成交。价格史/成交代理不是历史可执行 L2
- 预测归档起点来自文档，不等于已下载、与标签匹配、可交易的完整历史；真实前向保存接收时间、两侧 bid/ask、深度和当时 feeSchedule 才能检验净收益
- 3 城 ×14 日最多是 42 个候选站点-日，不能保证 30 个独立天气事件；标签和天气系统聚类尚未物化

## 两周内怎么检验

- 历史部分仅作预测校准可行性检查：用 Previous Runs 的固定 lead 序列匹配可核的结算标签，训练与测试按时间分离、按天气系统聚类。没有同期盘口，不比较历史市场 Brier 或历史可执行净收益；该代理试验也不能代替同一 run 的主版本
- 前向部分只执行上文冻结主版本的纸面设计，拟定起点 2026-10-19 或获准后的实际启动日，尚未开始；先核 model ID、版本、时区与可得性。数据不足则报告缺口，不换方法补出好结果
- 计数先合并同站同日各档，再按共同天气系统及连续日相关性聚类；30 是目标，实际独立结果未知
- 主筛失败条件（任一）：前向费后组合均值≤0；前向匹配市场报价基线或预注册的未校准同模型池基线 Brier 不被改善；有效独立事件簇<30；主版本所需数据无法冻结/取得。30 只是门槛，不是统计显著性保证。历史代理只报告校准，不以无盘口的结果通过净收益门槛

## 成本与容量

- weather 当前快照 r=0.05、takerOnly=true、rebateRate=0.25；总费 F=C×r×A×(1−A)，每份 f=F/C，费/名义本金 F/(C×A)=r×(1−A)。A 始终是所买那一侧实际成交价，不能用模型 p 或 1−p 代替
- 自算每份费/本金费率：A=0.20 为 0.80¢/4.00%；0.50 为 1.25¢/2.50%；0.80 为 0.80¢/1.00%；0.90 为 0.45¢/0.50%；0.95 为 0.2375¢/0.25%。NO 用自己的 A_N，费率敏感性来自实际价格，不来自 NO 标签或交易笔数占比
- 使用 ask 时只减每份 fee 与额外滑点；若从 mid 出发才另计一次 half-spread。不能把 5¢ 每份概率差直接减 6.5% 本金成本。今日费率只能用于当前情景，不是历史真实收费证据
- 算术示例（非实测）：1,000 份 YES，ask=0.20，假设真 p=0.25，支出本金 $200 加费 $8=$208；未计额外滑点时 EV=1,000×(0.25−0.20−0.008)=$42；初始支出 $208 在 $300 含费预算内。ask 已含 crossing，不再扣 $5 半价差
- 从 D-1 08Z 决策至 D+1 发布/结算可能跨两天或更长，资金占用须按实际进场至可用回款时间计，异常更正/争议另可延长；只有三城持续上架且每日可用时，一个月 20–30 日才有 60–90 个候选站点-日，不是实测成交机会，也不是独立事件数。真实深度、成交数和容量未知

## 风险

- 初始化时刻/历史 valid time 当实际可用时间会产生前视；run 通常延迟 4–6 小时不是保证，须保存真实接收时戳
- 机场与网格偏差、残差分布变化、mini-ensemble 相关性与样本不足会让概率失准；不靠事后换模型修补
- 整度显示、站点日界与缺测最低档会改变支付；美国站 CLI 规则不能迁移 global
- 来源 paper 用 mid、未计费用和 spread，可能高估收益；历史盘口缺失不能用 paper 赢率填补
- 平台/稳定币、薄盘、结算延迟与争议；restricted 标志不构成交易资格证明
- 同城多档、多 lead、邻近城市和连续日共享天气驱动，42 候选站点-日不能证明 30 独立结果

## 改进了什么

不适用（kind: new）；保留已有认领，本次校订不新增机制计数。

## 门槛自查

1. 机制说得清：满足（仅定义）— 公开预报校准对应的潜在付款方与变量已描述；有市场优势或持续收益未证
2. 有免费数据能检验：不确定 — 预报归档有文档，但成员、版本、实际可得时间、正式标签和历史盘口尚未齐；前向未启动
3. 小资金能做：不确定 — 已设 2,500/场所含费预算，但盘口深度、成交概率和占资时间未验证
4. 不重复：不确定 — 与 C01 的当日 running max 变量不同；本次只修已有条目，完整查重由主审确认
5. 扣成本后粗算够用：不确定 — 两侧每份费用与 ask 口径已统一；来源 mid-price paper、自报胜率与 NO 占比都不是费后证据
6. 两周内能检验：不确定 — 42 候选站点-日不保证 30 个独立天气事件，主版本数据及实际结果未取得；历史校准不能替代净收益验证
7. 出处可查：不确定（部分完成）— 已保存正文与摘要已分层，来源自报未复现；日界、完整标签及可得时间证据仍缺

## 出处

- https://raw.githubusercontent.com/AadiXD200/polymarket-weather-bot/main/README.md — 访问记录 2026-10-19 — 已读存档正文（Performance、Architecture、Data Sources；来源自报未核实）
- https://raw.githubusercontent.com/MihirM9/polymarket-weather-bot/main/README.md — 访问记录 2026-10-19 — 已读存档正文（How It Works、Key Math、Performance Evidence）
- https://open-meteo.com/en/docs/previous-runs-api — 访问记录 2026-10-19 — 已读存档正文（lead-time offsets、Data Availability）
- https://open-meteo.com/en/docs/historical-forecast-api — 访问记录 2026-10-19 — 已读存档正文（stitched archive 限制）
- https://open-meteo.com/en/docs/single-runs-api — 访问记录 2026-10-19 — 已读存档正文（归档起点、4–6h 延迟；不证明具体历史接收时间）
- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-nyc-on-october-19-2026 — 访问记录 2026-10-19 — 已读存档 JSON（description、resolutionSource、11 档、feeSchedule）
- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-london-on-october-19-2026 — 访问记录 2026-10-19 — 已读存档 JSON（description、11 档、fallback/revision/technical error 条款）
- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-seoul-on-october-19-2026 — 前轮访问记录 2026-10-19 — 二手（前轮规则审计；本次未重抓）
- https://docs.polymarket.us/faqs/weather-faqs — 访问记录 2026-10-19 — 已读存档正文（美国站 CLI/8:00 AM ET，明确不迁移 global）
- https://docs.polymarket.com/trading/fees — 访问记录 2026-10-19 — 二手（前轮已保存官方正文审计，Fee Structure/Fee Precision；无成交回执）
- https://github.com/kevinbadi/polymarket-weather-quant/blob/main/PLAYBOOK.md — 前轮访问记录 2026-10-19 — 二手（前轮站点偏差审计，未重新打开或复现）
- https://github.com/windgeek/polymarket-weather — 前轮访问记录 2026-10-19 — 二手（Project status/run results；来源自报未复现）
- https://github.com/natestokens/polymarket-weather-bot — 前轮访问记录 2026-10-19 — 二手（Results as of May 27, 2026；来源自报未复现）
- GitHub 检索“Polymarket weather temperature market bot ensemble forecast calibration”，2026-10-19 — 摘要（lukasjagnesak/ElPatron3333/kshitij406；未打开正文，不承接业绩或模型参数）

- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-nyc-on-september-14-2026 — 后续存档日志自标2026-10-20（与任务日期2026-10-19冲突，待核）— 二手（已保存Gamma核查记录；closed与umaResolutionStatus=resolved及76–77°F桶，不代表独立链上最终性审计）
- https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py — 后续存档访问日期存在上述冲突，待核 — 二手（已保存2026-09-10至19、LGA/EGLC/RKSI的routine-hourly代理记录；公开可复核报告尚缺，部分日覆盖不足）
