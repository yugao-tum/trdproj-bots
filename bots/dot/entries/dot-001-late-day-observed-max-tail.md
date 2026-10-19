---
id: dot-001
name_zh: 日末观测尾部 nowcast
name_en: Late-day observed-max tail nowcast
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
data: Gamma/CLOB/data-api 公共接口（规则、盘口、成交；历史盘口缺）；结算标签按市场指定 NOAA timeseries（整度，缺测才 WU）；IEM 观测仅作筛查代理，valid time≠可得时间；前向抓取计划尚未开始
test_2w: 计划 3 城 × 14 个本地日；独立天气事件数须按天气系统聚类后确认（30 未证）；费后均值≤0 或可用独立结果<30 即失败
status: 草稿
confidence: 中
---

整理说明：本稿是已保存公开证据的操作员侧校订，没有新增抓取、成交或回测；所有采集方案仍为计划。

## 一句话

在站点本地日尚未结束、最终最高温还未锁定时，用截至决策时已发布的逐时观测最高值，加上该站该时点剩余升温的经验分布，给每个温度档定价；只有模型概率减可成交 ask 后仍覆盖每份费用和报价以外的滑点缓冲才买 YES（ask 已包含 crossing，不再扣半价差），持有到结算。

## 钱从哪里来

- 对手：日内仍挂着旧尾部报价的报价者/交易者，没有及时把“已经观测到的最高值”和剩余时段还能升多少纳入；尤其是当前观测值上方、看起来很远但仍有物理可能的上尾档。
- 为何可能存在（待证）：站点观测按 METAR/整点发布，存在发布与入库延迟；不同参与者对站点、日界、整度舍入的理解不一致；尾档本身流动性薄，做市商重新报价慢。收益来自信息处理速度和规则口径，不是内幕。
- 边界：这不是“结果已发生、只等结算”的无风险套利。最终最高温仍取决于剩余时段，模型会错；亏损场景是买了不中的上尾档，或实际峰值落在相邻档。

## 规则

### 市场模板与真实实例（global，不是美国站）

- 模板：`Highest temperature in {city} on {date}`，每个城市-本地日 10–11 个整数温度档，每档一个 YES/NO 市场。
- NYC：slug `highest-temperature-in-nyc-on-october-19-2026`，event 含 11 个市场（id 5798034–5798044），站 KLGA，°F。原文要点：结算为 NOAA 在 LaGuardia Airport Station 记录的当日最高温；取 `weather.gov/wrh/timeseries?site=klga` 的 “Temp” 列、“Show Hourly Data” 中所有时刻的最高读数。
- London：slug `highest-temperature-in-london-on-october-19-2026`，event 含 11 个市场（id 5795606–5795616），站 EGLC，°C。规则同上，按整 °C；结算源 `https://www.weather.gov/wrh/timeseries?site=eglc`。
- Seoul：slug `highest-temperature-in-seoul-on-october-19-2026`，站 RKSI，°C。前轮审计记录该 event 在 2026-10-19 16:39Z 已 `closed:true`，本轮未重开；只作为第三个城市候选，规则与日界需再核。

### 时间日界

- Gamma 的 `endDate=2026-10-19T12:00:00Z` 是平台字段，不是结算日界。NYC 本地日（EDT，UTC−4）为 2026-10-19 04:00Z–2026-10-20 04:00Z。
- London 本地日（BST，UTC+1）为 2026-10-18 23:00Z–2026-10-19 23:00Z。
- Seoul 本地日（KST，UTC+9）为 2026-10-18 15:00Z–2026-10-19 15:00Z。
- 观察日时区按站点所在地推断（NYC ET、London 英国时间、Seoul 韩国时间），需以市场源页面显示确认；所有结算/缺测期限统一用 ET。
- 三个条款分别保留：(a) 正常结算时点为“次日首个数据点发布”与“观察日次日 23:59 ET”孰早；(b) 普通温度修订接受到次日首个数据点发布为止，不把它改写成统一的 23:59 截止；(c) 若已发布的可结算数据明显错误且由技术/运营异常或未授权干扰造成，可从原始发布时起另留开最多 7 个日历日（ET）等更正，逾期由平台澄清。该异常条款与普通修订条款不同。

### 舍入与缺测

- 按结算源显示的整度：NYC 整 °F，London/Seoul 整 °C。不能用小数 API 值四舍五入后再换档；一个显示度就可能翻档。
- 缺测：到观察日次日 23:59 ET（统一 ET 截止，不是“次日本地 23:59”）仍无 NOAA 数据，改用 Weather Underground Daily Observations；仍无数据则结算到最低档。总缺测会让高档 YES 归零，是明确的尾部风险。

### 美国站规则隔离

- `https://docs.polymarket.us/faqs/weather-faqs`（原研究 已读）是美国站的规则：结算用 NWS Daily Climate Report（CLI），次日 8:00 AM ET；CLI 与 24 小时 METAR 不一致可延到 11:00 AM ET；一周无数据则按 last fair market prices。其 NYC 站还是 KNYC Central Park。
- 这与 global Gamma 的 `weather.gov/wrh/timeseries` + 最低档缺测规则不同，不能迁移到 global。本文只用 global Gamma 规则；美国站只作为“不可混用”的对照。

### 进场、出场、仓位

- 决策时点 T：预注册单一触发点，本稿写死为本地 14:00；本稿不运行其他时点，不得看结果再挑时段。只用计划抓取时刻之前已可见的观测，按抓取时间戳过滤。
- 观测最高值 M_T = 截至 T 已发布逐时 Temp 的最大值；剩余升温 Δ = 日最高 − M_T，其经验分布按站点、月份、T 时刻、云量/风分层，训练只用更早的站点-日。
- 对每档 [lo,hi]，p = P(M_T + Δ ∈ [lo,hi])；以可成交 ask 计，买 YES 当 `p − ask > fee/share + s`（ask 已含 crossing，不再扣半价差）；若以 mid 为参考，等价条件是 `p − mid > 实际 half-spread + fee/share + s`，s 为报价之外的每份额外滑点缓冲，实际 half-spread=ask−mid；两种口径只取一种。主策略只做 YES，不把买 NO 混进来（NO 偏重留给 C02 讨论）。
- 仓位：单市场本金加费用及退出预留 ≤ $300；单日三城含费总预算 ≤ $900；Polymarket 全部未平仓头寸含费及预留合计 ≤ $2,500；不加杠杆。持有到结算；若新观测已使某档不可能（M_T > hi），可尝试卖出，但不假设一定有流动性。
- 风控：单城单日最多 2 档；三城若受同一天气系统影响则只算一个独立簇；规则/缺测争议日不交易。

## 证据

- 规则：原研究 直接读取 Gamma NYC/London event JSON（2026-10-19 UTC），核对 `description`、`resolutionSource`、11 个档位与 `feeSchedule`。两 event 均为 `restricted:true`、`negRisk:true`；实际交易资格未验证。
- 现场快照：同一任务窗口内，Gamma `outcomePrices` 显示 NYC 62–63°F 0.625、60–61°F 0.2445、64–65°F 0.17；London 14°C 0.9985。注意 `outcomePrices` 是平台价格字段，不是 CLOB 盘口。London 本地已晚、市场接近确定；NYC 仍处午后，上尾仍有报价。这是规则/价格字段快照，不是机制盈利或报价错误的证据，也没有成交验证。
- 站点数据：原研究 请求 IEM ASOS KLGA（`America/New_York`，2026-10-19）返回 00:51–12:51 ET，最高 60°F。IEM 的时间戳是观测 valid time，不是发布/入库时间；本次只说明抓取时接口可见数据到 12:51，不能证明历史任一时点的 as-of 可见性。结算标签仍以市场指定 NOAA 逐时源为准，IEM 只是筛查代理。
- 前轮审计笔记（round03-worker05，原研究 未重开原始 X/README）：30 个站点-日采样框已列出但标签未物化；X 账号自报 4 个 bot 竞争、首个 METAR 后约 5 秒盘口被扫；windgeek README 自报 111 笔、51.4% 胜率、净 −$62.51；natestokens 自报 23 笔 +$77.01。均为来源自报/前轮审计，未独立复现。
- 原研究 未取得历史盘口，无法回测历史净收益。observed_net_return=null，Sharpe=null，最大回撤=null，backtest_count=0。本文是规则/成本/数据筛查，不是完整盈利回测。
- 前向抓取只有计划，尚未开始；本文没有运行任何采集脚本。
- 本轮只读公开接口；未登录、未下注、未使用密钥。

- 后续已保存数据状态（数据报告尚未公开，访问日志的 2026-10-19/20 日期冲突待核）：市场盘点为28行、15个事件slug，混有不同天气模板，不是28个本策略结果；30个候选观测行是IEM代理，其中三个末日不完整、另一个日缺小时。只有NYC 2026-09-14的Gamma对象已核`umaResolutionStatus=resolved`与76–77°F桶，且没有独立UMA链上审计。三城同日的previous_day1最大值来自BestMatch、非指定GFS，也非一个固定起报快照；NYC的22.5单位是°C（72.5°F）。这不是30个正式结算标签、独立事件或as-of可交易结果；前向仍未启动

## 数据

- 规则/结算：Gamma `https://gamma-api.polymarket.com/events?slug=...`，免费免密钥；可查 `description`、`resolutionSource`、`outcomes`、`feeSchedule`。
- 盘口：CLOB 公共接口（开放市场盘口与价格历史）；成交：data-api（每市场约最近 2 万笔）。本轮未取得免费免密钥完整历史可执行盘口，所以可执行净收益只能规划前向记录；2026-10-19 为拟定起点，尚未启动。记录内容：T 时刻各档 bid/ask、top-5 深度、时间戳。
- 观测/标签：结算标签只按市场指定源 NYC 的 `https://www.weather.gov/wrh/timeseries?site=klga`、London 的 `https://www.weather.gov/wrh/timeseries?site=eglc`、Seoul 的 `https://www.weather.gov/wrh/timeseries?site=rksi`（NOAA 逐时、整度）；缺测才按规则 fallback 到 WU Daily Observations。IEM ASOS `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py`（keyless，CSV）只作筛查代理，valid time≠发布/入库时间，不能当结算标签。
- 可见性：前向抓取必须保存抓取时间戳；历史回填的 valid time 不能证明 as-of 可见性，因此该策略的历史部分最多做离线预测校准（还需物化对应标签），不能做“当时可见”的净收益回测。
- 独立结果：计划 3 城 × 14 个本地日抓取；同一城同日 11 档只算 1 个计数；但站点-日不自动等于独立天气事件，需按天气系统聚类（邻近城市、连续日同站合并），实际独立数未知，30 未证。
- 起始：计划从 2026-10-19 起前向记录（尚未开始）；没有历史盘口，历史只可用于预测校准，不可做净收益回测。

## 两周内怎么检验

- 计划从 2026-10-19 起（尚未开始），选 NYC/London/Seoul 三城，连续 14 个本地日；每天在预注册固定 T（本稿 14:00 本地）记录所有档的 bid/ask 与 top-5 深度，冻结模型 p。
- 结算后按市场指定源得最终最高温，按档给 0/1；1 个站点-本地日 = 1 个计数。42 个站点-日不自动等于 30 个独立天气事件：需按天气系统聚类，独立事件数是未知量；30 只是目标，未证。
- 失败标准（任一）：费后（按可成交 ask 计，每份 `0.05×ask×(1−ask)`，加报价之外的额外滑点）组合均值 ≤0；前向匹配报价的 Brier 不优于同批市场基线（报价并非校准的真实概率）；被选中交易的命中率低于 breakeven；聚类后独立结果 <30。
- 泄漏检查（计划）：前向记录中只用抓取时间戳早于 T 的数据重算；历史回填不能替代这一步。

## 成本与容量

- 费率：本轮 Gamma `feeSchedule` 显示 weather `rate:0.05, takerOnly:true, rebateRate:0.25`；按给定公式每份费（USD/share）`0.05×A×(1−A)`，A 是实际入价；费/notional=`0.05×(1−A)`。挂单不收费但成交不确定，本文按吃单算。历史市场费率未逐场核，不能用今日费率回填历史。
- 自算成本表（A=入价；fee/share 与概率价差同单位 USD/share；fee/notional 是比例，两者不能混着减）：
  - A=0.20：fee/share 0.80¢，fee/notional 4.00%
  - A=0.50：fee/share 1.25¢，fee/notional 2.50%
  - A=0.80：fee/share 0.80¢，fee/notional 1.00%
  - A=0.90：fee/share 0.45¢，fee/notional 0.50%
  - A=0.95：fee/share 0.2375¢，fee/notional 0.25%
- 两种等价判据（只取一种，避免重复扣 crossing）：以可成交 ask 计，要求 `p − ask > fee/share + s`；以 mid 计，要求 `p − mid > 实际 half-spread + fee/share + s`。低价档 fee/notional 高（0.20 档 4.0%）来自 `0.05×(1−A)`，不能把 5¢ 的价差直接对 6.5% 混比。
- 容量：单市场实际可执行深度与含费预算共同限制在 $300 内；三城/日含费预算 ≤ $900；Polymarket 总含费预算 ≤ $2,500；正常资金占用可从数小时延续到次日，异常更正/争议可更久，不能固定为 0–1 天。一个月计划约 60–90 个站点-日机会（3 城 × 20–30 天），但只在有尾部错价时下单，实际成交数未知。
- 算术示例（不是实测，且假设 p 为真）：1,000 份 @ ask 0.20 = $200 notional；费 $8，初始总支出 $208（在 $300 单市场 cap 内，余下 $92 仅作风险预留）；EV/share = p − ask − fee/share = 0.25 − 0.20 − 0.008 = 4.2¢，在未计额外滑点且能全额成交时约 $42。ask 已含 crossing，不再扣半价差；换 mid 口径才把半价差和费各算一次。该数字只演示成本量级，不表示边际被成本吃掉。

## 风险

- 模型/分布错：剩余升温分布用错月份、云况或站点，p 被高估；尾档一旦不中全损。
- 观测延迟/竞争：METAR 发布延迟、其他 bot 抢跑，看到信号时 ask 已消失；前轮审计的 X 自报称首个报告后约 5 秒盘口被扫，未独立核实。
- 规则风险：整度舍入、站点选择、日界理解错会直接判错档；总缺测按最低档结算是高档 YES 的尾部损失；结算可延迟/复核。
- 平台/执行：`restricted:true`，资格未验证；`negRisk` 多档结算；盘口薄，市价单滑点大；CLOB 故障。
- 数据/可见性：IEM 的 valid time 不是发布/入库时间，历史回填不能证明 as-of 可得；只有前向保存抓取时间戳才能防前视泄漏。
- 容量：尾档深度小，2,500 不一定放得下；三城相关性、天气系统聚类会降低独立样本数。

## 改进了什么

不适用（kind: new）。

## 门槛自查

1. 机制说得清：满足 — 谁付钱（日内未更新尾档的报价者）、状态变量（已发布 running max + 剩余升温）、为何持续（观测发布延迟、尾档薄、规则口径差异）均已写明；持续盈利未证。
2. 有免费数据能检验：不确定 — Gamma/CLOB/data-api 有免密钥接口，市场指定 NOAA 源已在规则中识别，但可回溯标签覆盖与实际可得时间尚未验证；历史盘口缺失，前向计划尚未开始，尚无 30 个独立结果；IEM 仅代理。
3. 小资金能做：不确定 — 2,500/场所上限可设，但各档 top-5 深度未测，尾档容量可能不足；未验证 5,000 总资金下的完整资金路径。
4. 不重复：不确定 — 与 C02（集合预报校准）状态变量不同；但受只读范围限制未做仓库全量查重，留给主调度。
5. 扣成本后粗算够用：不确定 — 已按 0.05 公式算出每份费和两种等价 breakeven（ask 口径不再扣半价差）；没有任何净收益实测，edge 是否覆盖 0.20 档 0.8¢/份的费用未知。
6. 两周内能检验：不确定（计划）— 42 个站点-日不等于 30 个独立天气事件；需按天气系统聚类后才知道实际独立数，30 未证；前向采集尚未开始。
7. 出处可查：不确定（部分完成）— 已保存 Gamma NYC/London 与 US FAQ 的原文记录；费用有前轮官方正文审计，转述明确分层；源页面日界、结算标签及所有运行时可见性尚未核全，不能视为完整证据链。

## 出处

- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-nyc-on-october-19-2026 — 访问 2026-10-19 — 已读（description、resolutionSource、11 档、feeSchedule）
- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-london-on-october-19-2026 — 访问 2026-10-19 — 已读（同上；14°C 档 0.9985）
- https://docs.polymarket.us/faqs/weather-faqs — 访问 2026-10-19 — 已读（美国站 CLI/8:00 AM ET；明确不迁移 global）
- https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=KLGA&data=tmpf&year1=2026&month1=10&day1=19&year2=2026&month2=10&day2=20&tz=America%2FNew_York&format=onlycomma&report_type=3 — 访问 2026-10-19 — 已读（KLGA 00:51–12:51 ET，最高 60°F；当日数据未完整）
- 二手（转述自前轮审计笔记 round03-worker05，原研究 未独立打开）：https://x.com/AlterEgo_eth/status/2067944048594473208；https://x.com/xmayeth/status/2096628194753515748；https://github.com/windgeek/polymarket-weather；https://github.com/natestokens/polymarket-weather-bot — 前轮访问 2026-10-19 — 二手

- https://docs.polymarket.com/trading/fees — 访问记录 2026-10-19 — 二手（前轮已保存官方正文审计，Fee Structure/Fee Precision；本次未重新抓取、无实际扣费回执）

- https://gamma-api.polymarket.com/events?slug=highest-temperature-in-nyc-on-september-14-2026 — 后续存档日志自标2026-10-20（与任务日期2026-10-19冲突，待核）— 二手（已保存Gamma核查记录；closed与umaResolutionStatus=resolved及76–77°F桶，不代表独立链上最终性审计）
- https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py — 后续存档访问日期存在上述冲突，待核 — 二手（已保存2026-09-10至19、LGA/EGLC/RKSI的routine-hourly代理记录；公开可复核报告尚缺，部分日覆盖不足）
