---
id: quant-004
name_zh: 提及市场：按历史词频给单词定价
name_en: Polymarket mentions markets — pricing words by historical transcript base rates
bot: quant
date: 2026-10-20
market: polymarket
pm_category: mentions
kind: new
improves: -
category: S
return_type: direction
instruments: 某人在某场活动/某一周/某次财报会/某期节目说某个词（含“N+ 次”次数档）的二元市场
venues: Polymarket
data: Gamma events/markets（含 rule PDF 链接、feeSchedule、outcomePrices）、CLOB prices-history、data-api 成交；全部免费免密钥；转录来源：presidency.ucsb.edu（已读可检索）、rollcall.com/factbase（JS 应用，逐场转写未验证）、fool.com/earnings-call-transcripts（索引 200，单场 URL 未核）；历史词频需自己从转录统计
test_2w: 独立结果按“事件”计（同一事件 20+ 个词市场只算 1 个）；已确认的关闭事件约 117 个/月，两周约 58 个事件；失败标准：事后 |p̂−市场价|>成本的交易，其按事件分组的净 PnL 中位数 ≤0，或 p̂ 的 Brier 分数不优于市场价
status: 草稿
confidence: 中
---

## 一句话

对 Polymarket `mention-markets` 标签下的“某人会说某词”市场，用同一说话人同类历史活动转录里该词的出场率（含“N+ 次”的次数分布）算出 p̂；只在 p̂ 与盘口价之差大于吃单费+半个价差时，按挂单价进场，持有到结算。

## 钱从哪里来

对手方是给“有趣的词/当周热词”出价的方向性散户，以及在几乎没成交的词市场上留下的陈旧报价。证据是价格离散度：2026-10-20 Gamma 快照里，`what-will-trump-say-this-week-october-19-october-25-20261025` 的 `Greenland` 市场 bid 0.51 / ask 0.96（spread 0.45），`"Ceasefire" or "Uranium"` 市场 bid 0.22 / ask 0.92（spread 0.70），而周成交量只有 163.5 和 167.5 美元；同一快照里 Netflix 财报会 `AI 5+` 市场 bid 0.78 / ask 0.81（spread 0.03，volume 42.25）。报价宽说明做市方没有把价格压到基准率附近，谁给出更接近基准率的限价单，谁就在收这笔“没人算过概率”的钱。这类钱能持续，是因为每个词市场都是独立小池子、口径写死在音频/视频里、多数参与者没有同类历史转录词频。

## 规则

**结算规则原文要点**（来源：每个事件 description 直接给出的 Polymarket 合同 PDF；已下载并读）：

- **事件型**（`Event Mentions Contract DeFi.pdf`）：`This market will resolve to "Yes" if {entity} uses the listed {word} during remarks at {event} scheduled for {date}`；`Speeches, events, or comments that occur outside of the named, scheduled event will not qualify`；**有 Q&A 则 Q&A 计入**。
- **期间型**（`Period Mentions Contract DeFi.pdf`）：`Only remarks made between the starting {datetime} and the ending {datetime} will be considered`；**记录于期外、期内发布的不算**；记录于期内、期内发布算。
- 周市场事件描述明写：`Written usages of terms (e.g. Truth Social posts, written statements, etc.) will not count`；期外拍摄、期内发布的视频不算。
- **词形口径**：复数与所有格算（“Immigrant”→“Immigrants”算，“Russia”→“Russia's”算，但“Russian”不算）；**时态/变位/派生不算**（“Run”→“Running”“Ran”不算）；**缩写展开不算**（“if {word} is 'AI,' 'artificial intelligence' does not qualify”）；同音不同拼不算，同形不同义算（“bass”两种意思都算）；专有名词与普通名词同等（“Apple Inc.”和“apple”水果都算）；**屏幕上打出但没念出来不算**；被静音/审查不算；AI 生成语音不算。→ 注意市场层可以覆盖模板：Netflix 那档市场的问题写的是 `"AI" / "Artificial Intelligence"`，与模板默认相反，**必须以该市场自己的 question/contract terms 为准**。
- **结算数据源**：`The resolution source will be audio or video of the event as provided by` White House、Reuters、AP、Bloomberg、AFP、NYT、FT、WSJ、BBC、Al Jazeera English、Semafor、The Information、WaPo、Axios、Politico、ABC、CBS、CNN、Fox、NBC、MSNBC；期间型另加“与该 entity 关联的官方社交账号”。`Unless otherwise specified, only remarks that are broadcast or streamed live will count`；预录内容按**首次官方发布**的音视频结算，`Transcripts or any subsequent releases that differ from the initial release will not be considered`。→ **转录不是结算源**，用转录算词频只是代理，必须接受“音频口径 ≠ 转录口径”的误差。
- **取消/改期**：事件确定取消或次日 23:59 ET 前未播出，`"No Qualifying Event"` 结算为 Yes、其余全部 No；改期若 2 天内公布且落在原定日 14 天内，市场继续、改期后言论计入。→ 所以“所有词都 No”在取消场景下同时成立，这是尾部风险，不是套利。
- **本条的进场/出场/仓位**：
  1. 只做 `mention-markets` 标签下、说话人与格式可比的词市场（Trump 集会/周市场、公司财报会、播客、PMQs、美联储记者会、体育解说、剧集）。
  2. 对每个词取同类历史活动转录最近 n 场（目标 n≥8；n<5 直接跳过），按上面词形口径统计每场次数，得到事件级命中率与次数分布；二元 p̂=(命中场数+1)/(n+2)（Laplace），次数档用每千词频率×预期时长做 Poisson/负二项。**这是计划口径，本轮未做实际统计。**
  3. 只在 `|p̂ − 盘口可成交价| > 成本阈值` 时进场；命中率 0/1 的词不用 0/1 的 p̂，用平滑后的上/下界。
  4. 进场一律挂限价（maker，费率为 0，另有 `rebateRate 0.25` 的返佣池）；若只能吃单，成本阈值按“0.04×p×(1−p)+半个 spread”放大。
  5. 单事件敞口 ≤ 资金的 2%（5,000 USDT 账户即 ≤100 USDT），单场所 ≤2,500 USDT；同一事件 20+ 个词市场共用这一个额度，不加总成倍下注。
  6. 持有到结算，不中途加仓、不摊平；同一词在 24h 内新闻基本面突变（新热点）时视为不可比，跳过。

## 证据

- **规模（自己数的）**：拉取 `tag_slug=mention-markets&closed=true` 共 600 个事件（分页 offset 0–500，每页 100，endDate 从 2026-12-18 到 2026-05-01，分页边界可能重复计 1 个事件），按 endDate 月份计数：2026-05 66、06 101、07 148、08 104、09 114、10 62、11 4、12 1。**完整月 06–09 平均 (101+148+104+114)/4 = 116.75 个事件/月**；首尾月份不完整，不能当趋势。
- **开盘中的事件**：`closed=false` 一次返回 23 个事件（limit 100），含 Trump 集会（22 个市场）、Trump 周市场（16 个）、Netflix（12 个）、Tesla（17 个）、Meta（15 个）、GM（14 个）、P&G（13 个）、PMQs（15 个）、Joe Rogan（14 个）、MrBeast（12 个）、NFL 解说（16 个）、UFC 解说（14 个）、Warsh 记者会（20 个）。
- **每事件市场数**：100 个已关闭事件里 727 个市场结算 Yes、838 个结算 No（合计 1565），**平均 15.65 个市场/事件**；**Yes 占已结算市场的 727/1565 = 46.45%**（自己算，样本为 endDate 2026-09-23 至 2026-12-18 的 100 个关闭事件）。→ 整体接近五五开，说明**不存在“统一卖 No”的边**，必须逐词定价；这个 46.45% 也只是描述统计，不是收益证据。
- **示例市场与盘口（Gamma 快照，2026-10-20 UTC，均为来源自报字段值，未用成交复现）**：
  - `will-trump-say-tax-during-his-midterm-rally-in-kansas-october-19`（`"Tax" 33+ times`）：`bestBid=null`、`bestAsk=0.001`、`spread=0.001`、`volume=9491.734729`。
  - `will-trump-say-hell-...-kansas-october-19`（`"Hell" 15+ times`）：`bestAsk=0.009`、`spread=0.009`、`volume=3850.5703799999997`。
  - `will-trump-say-biden-...-kansas-october-19`（`"Biden"/"Kamala"/"Obama" 10+ times`）：`bestBid=0.992`、`bestAsk=1`、`spread=0.008`、`volume=3893.583518`。
  - `will-trump-say-ceasefire-this-week-20261025`：`bestBid=0.22`、`bestAsk=0.92`、`spread=0.7`、`volume=167.5`。
  - `will-netflix-say-ai-artificial-intelligence-5-times-during-earnings-call-october-20`：`bestBid=0.78`、`bestAsk=0.81`、`spread=0.03`、`volume=42.25`。
  - 费率：以上市场 `feeSchedule={"exponent":1,"rate":0.04,"takerOnly":true,"rebateRate":0.25}`，与 GUIDE 第 8 节“提及 0.04”一致。
- **回测**：本轮**没有跑回测**，`observed_net_return=null`、`backtest_count=0`。上面只有规则原文、规模计数、盘口快照和总体 Yes 占比，**不构成收益证明**。

## 数据

- Gamma（免费、免密钥）：`https://gamma-api.polymarket.com/events?tag_slug=mention-markets&limit=100&closed=false` 与 `&closed=true&offset=0..500`；字段有 description（含合同 PDF 链接）、`markets[].question`、`outcomePrices`、`bestBid/bestAsk/spread`、`volume`、`feeSchedule`、`clobTokenIds`。
- 搜索（免费）：`https://gamma-api.polymarket.com/public-search?q=mention`，可列出历史提及事件（例：`will-elon-musk-mention-doge-in-his-snl-appearance`，volume 495007.57，closed=true）。
- CLOB 历史中间价（免费、免密钥）：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max&fidelity=60`。已关闭的 `will-anyone-say-kenny-5-times-during-south-park-e2-s29-20260930` 拿到 135 个点，2026-09-25T21:00:19Z 价 0.715 → 2026-10-01T12:00:22Z 价 0.245；新开市场只从创建日起有历史（Netflix 那个市场 `interval=max` 只回了 1365 字节、约从 2026-10-18 起）。→ **历史盘口（L2）仍不公开**，能拿到的是中间价序列，按买卖价算的历史成本只能从当前 spread 近似。
- 转录：`https://www.presidency.ucsb.edu/advanced-search?field-keywords=%22remarks%22` 返回 200，页面报 `1 - 25 of 28398 records found`（免费，可检索总统言论全文；本轮只验证可访问和检索结果数，未做逐场词频）。`https://www.factba.se/` 跳转到 `https://rollcall.com/factbase/`（200），但页面是 JS 应用，**逐场转写文本是否免费可下载未验证**。`https://www.whitehouse.gov/remarks/` 返回 200，**是否提供逐字转写未验证**。`https://www.fool.com/earnings-call-transcripts/` 返回 200、标题 `Earnings Call Transcripts | The Motley Fool`（财报会转写索引，免费），但猜测的单场路径 `/earnings/call-transcripts/nflx/` 返回 404，**单场 URL 结构未查到**。
- data-api 成交：`https://data-api.polymarket.com/trades?market=<conditionId>`（免费、免密钥、每市场约最近 2 万笔），本轮未取。

## 两周内怎么检验

- **独立结果按事件数**，不按市场数：一个集会/一次财报会/一期节目算 1 个，即使它有 22 个词市场（GUIDE 第 2、8 节）。
- 路线 A（前向，2026-10-20 起）：对两周内结算的事件，事前冻结 p̂、成本阈值和限价；事后按事件记净 PnL。已确认规模约 116.75 事件/月 → 两周约 58 个事件，但**通过“p̂ 与价格差 > 成本”过滤后实际成交事件数未知**，可能远少于 30，这条路只能算 forward 观察，不能冒充 30 个结果。
- 路线 B（历史，优先）：取 600 个已关闭事件中的 Trump 集会/周市场类，用 APP 转录统计词频得 p̂，用 `prices-history` 取当时中间价（并注明“按当前 spread 近似半价差”），按事件算净 PnL 与 Brier。此路线能凑够 30+ 事件，但**依赖转录覆盖：本轮未核过 APP 上有多少场能对上这些事件日期**。
- 失败标准（写死）：≥30 个独立事件中，交易组净 PnL 中位数 ≤0；或 p̂ 的事件级 Brier 分数不优于同期市场价（即“用转录算基准率”这个信息本身没有价值）。任一成立即判本策略失败，不靠挑事件救。

## 成本与容量

- 吃单费（官方公式，GUIDE 第 8 节同）：`fee = 份数 × feeRate × p × (1−p)`，`feeRate=0.04`（上列市场 `feeSchedule` 实测值）。maker 不收费且 `rebateRate=0.25` 返佣。
- 每笔成本 = 费 + 半个 spread（自己算的三例）：
  - Netflix `AI 5+`，ask 0.81、spread 0.03：每份费 `0.04×0.81×0.19 = 0.006156`，半个价差 `0.015`，合计 `0.021156` USDC/份 = 2.12 美分；占 0.81 本金 **2.61%**。
  - Trump 周市场 `"Ceasefire" or "Uranium"`，ask 0.92、spread 0.70：每份费 `0.04×0.92×0.08 = 0.002944`，半个价差 `0.35`，合计 `0.352944`，占 0.92 本金 **38.4%** → 这种价差下吃单必亏，只能挂单等成交。
  - Kansas `Tax 33+`，ask 0.001、spread 0.001：每份费 `0.04×0.001×0.999 = 0.00004`，半个价差 `0.0005`，合计 `0.00054`，占 0.001 本金 **54%** → 极端低价档（≤2¢）在类目里普遍不可交易，这是本条只做中段价格的原因。
- 容量：词市场成交量差距极大（同一快照从 volume 10 到 9491.73），深度有限，单笔 50–200 USDC、单事件 ≤100 USDT（账户 2%）比较现实；单场所 ≤2,500 USDT 能放下，但**全事件总成交量本轮未汇总**，`5000 USDT 能否整体铺开` 未核实。资金占用天数 = 事件日到结算，通常 0–7 天（周市场标的是自然周），周市场资金一年可周转很多次，但**每个事件的词市场相互高度相关**，不能按 22 个独立机会算年化。

## 风险

- **口径风险**：结算靠音频/视频，不靠转录；连读、吞音、被静音、主持人插话、预录片段是否“作为节目一部分播出”都可能决定 Yes/No，转录词频会系统偏离。
- **次数档口径**：`33+`、`15+` 这类要人工逐次计数，重复计数与“Joe Biden 算一次还是两次”的解释空间（合同写明全名算 1 次）都带来争议与结算延迟。
- **取消/改期**：`No Qualifying Event` 会让“全部词 No”一起成立，任何同时买多个 No 的组合在取消场景下被反噬；改期 14 天窗口也会把结算推到窗口外。
- **流动性/退出**：spread 到 0.45–0.86 的市场没有对手盘，挂单可能整周不成交，成交了也可能无法在对己方有利的价位退出。
- **非平稳**：词频随新闻周期突变（如新地名、新人名），历史基准率会失效；“热词”当周恰好是市场高估最厉害的地方，也是基准率最不可信的地方。
- **模型风险**：n<5 场时做 Laplace 平滑的估计极不稳，容易把 0/1 的经验频率当成概率，导致在 1¢ 档上过度下注。
- 平台/结算：本条不讨论地区与合规。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：满足 — 付款方是给“有趣/热词”出价的方向性散户和无人维护的陈旧报价，证据是同日快照里同一事件不同词市场 spread 从 0.001 到 0.86、成交量从 10 到 9491.73；本条赚的是“没人按历史词频定价”的差。仅说明机制，不说明盈利。
2. 有免费数据能检验：不确定 — 规则原文、事件清单、`prices-history` 中间价都免费免密钥且已实测可取（含已关闭市场 135 个点），但**转录词频要自己做**，APP/factba/White House/Fool 只验证到“可访问”，逐场覆盖率和是否免费全文未逐一核实；历史 L2 不公开，历史成本只能按当前 spread 近似。
3. 小资金能做：不确定 — 单事件 ≤100 USDT、单笔 50–200 USDC 与实测 volume 相容，2,500 USDT 场所上限放得下；但深池以外的市场挂单未必成交，容量上限未实测。
4. 不重复：不确定 — 本条与库里已有的 Polymarket 收益来源（报价奖励、持有奖励、天气/数值模型定价）在付款方和关键变量上都不同（此条变量是“转录词频 vs 市场价格”）；但与任何已存在的“提高提及市场”条目是否重叠，需主审确认，本轮未查 `known/`。
5. 扣成本后粗算够用：不满足（未证） — 没有回测，`observed_net_return=null`；已算出中段价格每笔成本约 2.61%（0.81 档），而 1¢ 档成本达 54%，能否覆盖取决于 p̂ 的准确度，目前无法证明有正收益。
6. 两周内能检验：不确定 — 独立结果按事件计；已确认约 116.75 事件/月（两周约 58 个），规模够，但过滤后实际成交事件数未知，且转录覆盖率未核，可能只能记 forward 观察，不能凑够 30 个。
7. 出处可查：满足（规则与规模部分） — 合同 PDF、事件 description、Gamma 字段、`prices-history` 都给了 URL、访问日期和原文位置；转录源只到“HTTP 200 + 页面标题/记录数”这一级，逐场可下载性标了未验证。

## 出处

- https://polymarket-upload.s3.us-east-2.amazonaws.com/market_products/Mentions/Event+Mentions+Contract+DeFi.pdf — 访问 2026-10-20 — 已读（HTTP 200，124188 字节；Event scope、Plurals and Possessives、Expanded Acronyms、On-Screen Text、Cancellation/No Qualifying Event、Source Agency 各段）
- https://polymarket-upload.s3.us-east-2.amazonaws.com/market_products/Mentions/Period+Mentions+Contract+DeFi.pdf — 访问 2026-10-20 — 已读（HTTP 200，105546 字节；Period Scope、Previously Recorded Content、Source Agency）
- https://gamma-api.polymarket.com/events?tag_slug=mention-markets&limit=100&closed=false — 访问 2026-10-20 — 已读（23 个开盘事件及各事件市场数）
- https://gamma-api.polymarket.com/events?tag_slug=mention-markets&limit=100&closed=true&order=endDate&ascending=false&offset=0..500 — 访问 2026-10-20 — 已读（600 个事件月度计数；前 100 个事件的 727 Yes / 838 No / 1565 市场）
- https://gamma-api.polymarket.com/events?slug=what-will-trump-say-during-his-midterm-rally-in-kansas-october-19 — 访问 2026-10-20 — 已读（description 原文、22 个市场、bid/ask/spread/volume/feeSchedule）
- https://gamma-api.polymarket.com/events?slug=what-will-trump-say-this-week-october-19-october-25-20261025 — 访问 2026-10-20 — 已读（周市场规则：“Written usages … will not count”、16 个市场盘口）
- https://gamma-api.polymarket.com/events?slug=what-will-netflix-say-during-their-next-earnings-call-october-20 — 访问 2026-10-20 — 已读（“mentioned by anyone during this event”、resolution source 为 audio、12 个市场盘口）
- https://gamma-api.polymarket.com/public-search?q=mention — 访问 2026-10-20 — 已读（历史事件 slug、volume；如 Elon/SNL 事件 volume 495007.57）
- https://clob.polymarket.com/prices-history?market=<clobTokenId>&interval=max&fidelity=60 — 访问 2026-10-20 — 已读（HTTP 200；已关闭 South Park 市场 135 点 2026-09-25→2026-10-01；Netflix 市场仅 1365 字节）
- https://www.presidency.ucsb.edu/advanced-search?field-keywords=%22remarks%22&items_per_page=25 — 访问 2026-10-20 — 已读（HTTP 200；`1 - 25 of 28398 records found`）
- https://www.factba.se/ — 访问 2026-10-20 — 已读（301/跳转到 https://rollcall.com/factbase/，HTTP 200；JS 应用，逐场转写未验证）
- https://www.whitehouse.gov/remarks/ — 访问 2026-10-20 — 摘要（HTTP 200、261807 字节；未验证是否含逐字转写）
- https://www.fool.com/earnings-call-transcripts/ — 访问 2026-10-20 — 已读（HTTP 200，标题 `Earnings Call Transcripts | The Motley Fool`）
- https://www.fool.com/earnings/call-transcripts/nflx/ — 访问 2026-10-20 — 已尝试，HTTP 404，不作为数据源（单场 URL 结构未查到）
- https://rollcall.com/factbase/trump/ — 访问 2026-10-20 — 已尝试，HTTP 404，不作为数据源
- https://gamma-api.polymarket.com/tags?limit=20&search=mention — 访问 2026-10-20 — 已读（HTTP 200，返回的是模糊匹配的无关 tag 列表，**不能**据此当 mentions 板块标签证据；板块标签以事件自带 `mention-markets` tag 为准）
