---
id: quant-009
name_zh: 交易所上币截止日市场：按基准率定价
name_en: "Will <token> be listed on <venue> by <date>" — base-rate pricing of listing-deadline markets
bot: quant
date: 2026-10-20
market: polymarket
pm_category: crypto
kind: new
improves: -
category: S
return_type: direction
instruments: Polymarket 二元市场模板「<token> 在 <date> 前于 Binance/Coinbase/Upbit/Robinhood 现货上线」
venues: Polymarket
data: Gamma public-search/events/markets（免费免密钥，含历史已结算市场）、CLOB prices-history（免费免密钥，已结算市场可取，但单次请求窗口有限，实测≤7天/次）、Binance 官方公告 CMS 公开接口（免费免密钥）；Coinbase 盘前 roadmap 原文本次未取到（403）
test_2w: 回溯 21 个单市场已结算事件 + 3 个多选事件（按事件计，共 24 个独立结果），用 CLOB 价格历史取截止前 7 天的中间价，比较「基准率模型概率 − 价格 > 费用楔子」时的净损益；两周内凑不到 30 个独立事件或每事件中位净损益≤0 判失败
status: 待核
confidence: 低
---

## 一句话

在 Polymarket 的「某代币在某个日期前被某交易所现货上线」二元市场里，用「交易所自己的公告/盘前名单 → 实际开盘」的机械管道和历史基准率估一个概率，只在模型概率与盘口价格之差大于吃单费加半个价差的楔子时买入对应方向，持到结算（公告出来后价格≥0.95 可提前平仓释放资金）。

## 钱从哪里来

对手方的错误定价，不是平台补贴。这类市场的买家常把「上币」当成随机彩票，给出与「交易所已经公告/已进盘前名单」这一事实不匹配的低价；同时把已临近的截止日当成远期期权定高价。付款方就是这些在截止日结构上系统性下错注的 taker，成交后由 UMA 结算把价值从错误一侧转移到正确一侧。这条现金流是否持续，取决于这类市场是否持续被发出来、以及公告后的价格是否仍慢于事实——两者都只有部分证据（见下），所以本条只是「机制 + 可检验方案」，不是已证实的盈利策略。

## 规则

**市场模板（Gamma 原文摘录，2026-10-20 抓取）**

- `will-coinbase-list-hype-in-2025`（volume 239725.347892）："This market will resolve to Yes if the crypto token Hyperliquid ($HYPE) is listed for spot purchase on Coinbase by December 31, 2025, 11:59 PM ET. Otherwise, this market will resolve to No." 结算源："The primary resolution source for this market will be Coinbase, however a consensus of credible reporting will also be used." 抓取时 `outcomePrices=["0","1"]`、`closed=true`、`closedTime=2026-01-01 09:29:27+00`、`umaResolutionStatus=resolved`。
- `hyperliquid-listed-on-coinbase-before-2027`：同模板，截止 "December 31, 2026, 11:59 PM ET"，`outcomePrices=["1","0"]`，event volume 47799.358913。
- `penguin-listed-on-binance-by-march-31`（volume 224358.07984199983）：结算条件把代币写成 "Nietzschean Penguin ($PENGUIN) (8Jx8AAHj86wbQgUTjGuj6GTTL5Ps3cqxKRTvpaJApump) is listed for spot purchase on Binance by March 31, 2026, 11:59 PM ET"，即**写明合约地址**；结算源 Binance。
- `will-fartcoin-be-listed-on-robinhood-before-june`（volume 14832.369719）：把场所限定为 "listed for spot purchase on **Robinhood U.S.** by May 31, 2025, 11:59 PM ET"。
- `hyperliquid-listed-on-binance-by`：event 下 2 个市场，`hyperliquid-listed-on-binance-by-june-30-2026`→`["0","1"]`（No），`hyperliquid-listed-on-binance-in-2026-485`→`["1","0"]`（Yes），event volume 278645.142524。

**要点与坑（都是从上面的原文里读出来的）**

1. 口径是「listed for **spot** purchase」：永续合约上线不算；对 Robinhood 还额外限定 "U.S."。
2. 截止时间是 **ET 23:59**，不是 UTC 日界；同一代币的「by 6/30」与「in 2026」是两个互不替代的市场。
3. 结算源写的是交易所本身，备用是 "consensus of credible reporting"——公告、开盘、以及「公告了但没开盘」之间的差别只能靠交易所原文判定。
4. 上币日期由交易所决定，截止日只能决定 Yes/No 的时点，不能决定结果。

**交易规则（本稿拟定的版本）**

- 标的池：event 标题匹配 `<token> listed on (binance|coinbase|robinhood)` 的二元市场，以及 `next coin on coinbase` / `next coin on robinhood` 这类多选事件（按事件计 1 个独立结果）。
- 概率：`p_model = 1 - exp(-λ·T)`，`T` = 距离截止日的天数，`λ` = 由历史基准率反解出的到达率；当交易所已公告开盘时间时，`p_model=1`（T 覆盖开盘日）。
- 进场：`p_model − ask ≥ 0.01 + p·(1−p)·0.07`（半价差 + 吃单费，见成本节）买 YES；`bid − p_model ≥ 0.01 + p·(1−p)·0.07` 买 NO。不满足就不做。
- 出场：持到结算；若中途交易所公告开盘且盘口 ≥0.95，则按可见卖价平仓以释放资金（不假设一定成交）。
- 仓位：单市场 ≤300 USDT，同时 ≤8 个市场，本条总占用 ≤1500 USDT（总资金 5000、单场所 ≤2500 均不触碰）。
- 不做的情形：没有公开公告、只有社群传闻；代币合约地址与市场原文不一致；`endDate` 已过但未结算（那时是结算时滞问题，不是本条）。

## 证据

**基准率（本条自己从抓取到的 Gamma 数据算的，不是别人报的）**

- 抓取方式：`https://gamma-api.polymarket.com/public-search` 四个查询（`listed on binance` / `listed on coinbase` / `listed on robinhood` / `be listed`，每个 `limit_per_type=50`），2026-10-20 执行，结果取并集 53 个 event。
- 并集中标题匹配 `listed on (binance|coinbase|robinhood)` 的有 **24 个 event / 40 个 market，24 个 event 全部 `closed=true`**。
- 其中**单市场 event 21 个，3 个结算为 Yes**（`wif-listed-on-coinbase-or-binance-in-march`、`wif-spot-listed-on-coinbase-in-2024`、`hyperliquid-listed-on-coinbase-before-2027`）。
  - 无条件基准率 = 3 / 21 = **14.29%**（我的算术）。
- 按「同一代币」合并后是 **12 个簇**（BITCOIN、FARTCOIN、HYPE、MOG、PENGUIN、PEPE、PNUT、POPCAT、SLERF、SMOLE、WIF、YZY），其中 **2 个簇至少含一个 Yes**（WIF、HYPE）。事件级基准率 = 2 / 12 = **16.67%**（我的算术）。
- 多选事件 3 个：`hyperliquid-listed-on-binance-by`（2 个市场，1 个 Yes）、`next-coin-listed-on-binance`（8 个市场，1 个 Yes）、`first-coin-listed-before-2025`（9 个市场，1 个 Yes）。
- 结论（推断，非来源原文）：**「在截止日前被上线」的无条件概率只有约 1/7**，所以看见 0.10–0.20 的 Yes 报价不能直接当便宜货；真正的边际信息来自「交易所是否已经公告/已进盘前名单」。无条件基准率本身不构成策略。

**公告 → 实际开盘的时滞（可抓到的交易所侧证据，只有 Binance 侧）**

- Binance 官方公告 CMS 公开接口：`catalog 48 "New Cryptocurrency Listing"` 的 `total=2283` 条（2026-10-20 抓取，说明该目录的历史公告量级）。
- 同接口列表里 `Binance Will List Hyperliquid (HYPE) with Seed Tag Applied` 的 `releaseDate` 解析为 **2026-09-24 07:30 UTC**；该公告正文写 "Binance will list Hyperliquid (HYPE) and open trading for the following spot trading pairs at **2026-09-24 11:00 (UTC)**"，另写 "Withdrawals will open at 2026-09-25 11:00 (UTC)"。
- 我的算术：公告发布到开盘 = 11:00 − 07:30 = **3 小时 30 分**（同一天）。
- 与 Polymarket 交叉核对：HYPE 的 `by june-30-2026` 结算 No、`in 2026` 结算 Yes，与「2026-09-24 上线」一致（这是我用两个已抓取事实做的对齐，不是来源原话）。
- **只有 1 个样本，不能外推成「公告后 3.5 小时必开盘」**；Binance 另有 "Binance Will List RWUSD"（2026-10-13 03:30）等同类公告，但正文开盘时间本次只解析了 HYPE 一条。

**Coinbase 盘前 roadmap（题目要求的核心来源）**

- `https://www.coinbase.com/blog/listing` 用 curl 抓取返回 **403**，正文是 Cloudflare "Just a moment..." 挑战页；`https://www.coinbase.com/blog/rss` 同为 403；`https://www.coinbase.com/rss/blog?category=listing` 返回 404。
- 尝试取网页存档：`https://archive.org/wayback/available?url=www.coinbase.com/blog/listing` 返回 `{"archived_snapshots": {}}`（无快照）；`web.archive.org/web/2025id_/...` 与 CDX 查询在本环境均失败（返回码 000）。
- 因此 **Coinbase roadmap 公告日、以及「进 roadmap → 开始交易」的时滞，本稿未查到**，不引用任何相关数字。X 上的 @CoinbaseAssets 也未抓（本环境不抓 X 正文）。
- 本条对这个缺口的处理：把「Coinbase 侧公告」当作**不可用信号**（模型在该场所退化为纯基准率，只能做「明显偏离基准率」的少数交易）；不假装有 roadmap 数据。

**价格是否留有余量（部分实测）**

- `https://clob.polymarket.com/prices-history` 对已结算市场可读：`will-coinbase-list-hype-in-2025` 的 YES token，2025-12-26 → 2026-01-01 窗口（fidelity=60）返回 200，首个点 `t=1766707211, p=0.011`；2026-01-01 附近的 3 天窗口首个点 `t=1767139214, p=0.002`。
- 含义：**临近截止日时市场把 No 定到 0.2%–1.1%**，这段没有可用余量（我的解读）。所以本策略的战场只能是「离截止日还有数周 + 有公告管线」的那一段，具体那一段的错价程度本次**没有回测**（`backtest_count=0`）。
- 未做任何盈亏回测；`observed_net_return=null`；Sharpe 未知；最大回撤未知。上文基准率和时滞都是描述性统计，不是收益。

## 数据

- Gamma public-search：`https://gamma-api.polymarket.com/public-search?q=listed%20on%20coinbase&limit_per_type=50`；免费免密钥；给出 event/market、`outcomePrices`、`closed`、`endDate`、`volume`。注意返回有上限，24 个匹配 event 是 4 个截断查询的并集，**不是全量**（未查到全量清单）。
- Gamma markets/events：`https://gamma-api.polymarket.com/markets?slug=<slug>&closed=true`、`https://gamma-api.polymarket.com/events?slug=<slug>`；本次抓到的示例市场 `feeSchedule=null`、`fee=null`、`takerBaseFee=null`，因此费用按 GUIDE 第 8 节的 crypto 费率 0.07。
- CLOB 价格历史：`https://clob.polymarket.com/prices-history?market=<clobTokenId>&startTs=<unix>&endTs=<unix>&fidelity=60`；免费免密钥；已结算市场可取；**区间过长会 400**（"invalid filters: 'startTs' and 'endTs' interval is too long"），实测 31 天被拒、6 天成功，所以要分段拼接。
- Binance 公告：`https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20` 与 `.../article/detail/query?articleCode=<code>`；免费免密钥；公告标题带日期、正文带 UTC 开盘时间。
- 缺失：Coinbase 盘前 roadmap（403）、@CoinbaseAssets 时间线、Upbit 公告（本次 4 个查询未返回任何 upbit 专属上币 event，未查到）、历史盘口（CLOB 历史只给成交价序列，不给 L2）。

## 两周内怎么检验

- **回溯（可立刻做，两周内可完成）**：对上面 24 个匹配 event（含 3 个多选事件，多选事件按 event 计 1 个结果）逐个取 `clobTokenIds`，用 `prices-history` 以 ≤7 天窗口分段拼出「截止日 −7 天」和「截止日 −1 天」的中间价；用无条件基准率（3/21）和「按剩余天数缩放的基准率」两种模型算 `p_model`；凡 `p_model − ask > 楔子` 就记一笔买入，净损益 = 结算支付 − 成交价 − 吃单费 − 半个价差（价差用当日可见买卖价，无 L2 时用 1¢ 保守假设并写明）。
- **独立结果怎么数**：按 event 计，不按 market 计；同一代币的多个截止日只算一个簇（上面 21 个单市场 event 合并后只有 12 个簇）。这条很要紧：21 个市场其实只有 12 个独立赌注。
- **两周内能不能凑到 30 个**：不确定——历史匹配 event 只有 24 个（12 个簇）；要凑到 30 个独立结果，必须把 `next coin on coinbase` / `next coin on robinhood` 周度系列（本次看到 `next-coin-on-robinhood-3-7-2025` volume 98,601.89、`next-coin-on-robinhood-03132025` volume 246,413.65；约 2.0M/0.99M 的 volume 属于 `first-coin-listed-before-2025`（2,009,956.35）与 `next-coin-listed-on-binance`（986,717.83），不是这两个周度市场）也拉进来，具体条数**未核实**。
- **前向**：从 2026-10-20 起记录所有新建的该类 event，记 `ask/bid`、`endDate`、公告原文与时间戳、结算结果。
- **失败标准（预先写死）**：(a) 两周内拿不到 ≥30 个独立 event 结果 → 只能记 forward 观察，不冒充；(b) 30 个结果里，触发交易的子样本每事件中位净损益 ≤0；(c) 触发交易的子样本胜率虽然高但净损益被费用+价差吃光（即平均净损益 < 0）；(d) `p_model` 的 Brier 分数不优于直接用市场价 → 判模型无信息。

## 成本与容量

- 吃单费（GUIDE 第 8 节 crypto 费率 0.07，因为 Gamma 对示例市场返回 `feeSchedule=null`）：`fee = 份数 × 0.07 × p × (1−p)`；maker 不收费。
  - 100 份、p=0.30：`fee = 100 × 0.07 × 0.30 × 0.70 = 1.47 USDC`；占名义（30 USDC）的 4.9%。
  - 100 份、p=0.90：`fee = 100 × 0.07 × 0.90 × 0.10 = 0.63 USDC`，占名义 0.70%。
- 半个价差：无历史 L2，按 1¢/份假设（100 份 = 1.00 USDC），在成本里单列，并标注为假设而非测量。
- 每笔成本（价差 1¢、100 份）= 1.47 + 1.00 = 2.47 USDC；折成概率单位是 **2.47pp**，所以 p=0.30 时的盈亏平衡概率约 **32.5%**（我的算术：0.30 + 0.0147 + 0.01）。这就是本策略要求的「模型领先市场的最小幅度」。
- 容量：示例市场 volume 从 14832.369719（FARTCOIN/Robinhood）到 239725.347892（HYPE/Coinbase）到 2009956.351265（`first-coin-listed-before-2025`）；单市场放 300 USDT 在这些池子里占比都很小，但没有 L2 无法证明 1¢ 以内能成交 300 USDT——**容量上限未验证**。
- 资金占用：从建仓到 `endDate` 结算，典型数周到数月，等于资金被锁住；年化必须除以占用天数（本稿没算年化，因为还没有收益率）。
- 机会频率：24 个匹配 event 分布在 2024-02 到 2027-01 的 `endDate` 上（大部分 2024–2026），量级是**每月个位数**；`next coin` 周度系列可能提高频率，但条数未核实。

## 风险

- **基准率不是信号**：无条件 14.29% 意味着大多数「by 某个近期日期」的市场应该结算 No；把这类市场一律当作「会 Yes」是常见亏法。
- **公告 ≠ 开盘**：「listed for spot purchase」要求真的能现货买卖；公告、盘前名单、只开合约都不满足条件，市场上可能出现「公告了但没开盘」的假象。
- **结算源争议**：结算源写「交易所 + 可信报道共识」，交易所页面改版/删文、地区差异（Robinhood "U.S."）都会引发争议；`endDate` 过后到 UMA 结算之间还有时滞。
- **数据缺口**：Coinbase roadmap 原文抓不到（403），这条策略在 Coinbase 场所基本失去先手；Upbit 侧本次没找到专属 event。
- **流动性与退出**：这类市场深度差，想提前平仓可能要吃很大的价差；「≥0.95 平仓」只是意图，不保证成交。
- **资本锁定**：数周到数月，且同一代币多个截止日会重复占用（要按簇限仓）。
- **信息合规**：只用公开公告；不去买内部名单、不碰未公开的上所信息。
- **平台风险**：Polymarket 的 crypto 板块吃单费 0.07 是四类里最高的之一，费用楔子会直接吃掉小额错价。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：满足 — 付款方是把「上币」当彩票定价的对手方，本条用交易所公告管道 + 基准率判断哪一侧错价；但「这笔钱是否持续」只有部分证据（24 个历史 event / 12 个簇），不宣称稳定。
2. 有免费数据能检验：满足（部分）— Gamma 历史已结算市场 + CLOB `prices-history`（已实测可读，分段窗口）+ Binance 官方公告接口都是免费免密钥；缺口是 Coinbase roadmap（403，未查到）和 Upbit 公告。
3. 小资金能做：满足 — 单市场 ≤300 USDT、同时 ≤8 个、总占用 ≤1500 USDT，均在 5000/2500 约束内；但 300 USDT 能否在 1¢ 内成交未验证。
4. 不重复：不确定 — 仓库里已有 `E-E1-listing-chase`、`E-E1-listing-short`、`E-E1-upbit-pump-short` 等（现货/永续方向交易），本条交易的是预测市场上的「上币截止日」二元合约、按基准率定价，收益来源不同；是否与主项目 `A-A3-poly-cross-market` 类条目冲突待主审确认。
5. 扣成本后粗算够用：不确定 — 没有回测（`backtest_count=0`）；已算清 p=0.30 时盈亏平衡概率约 32.5%（费 1.47 + 半价差 1.00 每 100 份），但「模型能否稳定领先 2.5pp」未证明。
6. 两周内能检验：不确定 — 回溯可在两周内做完（24 个 event，价格历史已确认可读），但独立结果合并后只有 12 个簇，要凑 30 个必须并入 `next coin` 周度系列，条数未核实。
7. 出处可查：满足（部分）— 每条市场规则、基准率、时滞都有 URL、访问日期和原文位置；Coinbase roadmap 与 Upbit 公告明确写「未查到」，没有用二手内容充数。

## 出处

- https://gamma-api.polymarket.com/public-search?q=listed%20on%20binance&limit_per_type=50 — 访问 2026-10-20 — 已读（18 个 event）
- https://gamma-api.polymarket.com/public-search?q=listed%20on%20coinbase&limit_per_type=50 — 访问 2026-10-20 — 已读（26 个 event）
- https://gamma-api.polymarket.com/public-search?q=listed%20on%20robinhood&limit_per_type=50 — 访问 2026-10-20 — 已读（4 个 event）
- https://gamma-api.polymarket.com/public-search?q=be%20listed&limit_per_type=50 — 访问 2026-10-20 — 已读（27 个 event）
- https://gamma-api.polymarket.com/markets?slug=will-coinbase-list-hype-in-2025&closed=true — 访问 2026-10-20 — 已读（结算规则原文、`umaResolutionStatus=resolved`、`feeSchedule=null`、`volumeNum=239725.347892`）
- https://gamma-api.polymarket.com/events?slug=will-coinbase-list-hype-in-2025 — 访问 2026-10-20 — 已读
- https://gamma-api.polymarket.com/events?slug=hyperliquid-listed-on-coinbase-before-2027 — 访问 2026-10-20 — 已读（volume 47799.358913，`outcomePrices=["1","0"]`）
- https://gamma-api.polymarket.com/events?slug=hyperliquid-listed-on-binance-by — 访问 2026-10-20 — 已读（2 个市场，by-6/30 No、in-2026 Yes）
- https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20 — 访问 2026-10-20 — 已读（catalog 48 total=2283；HYPE 公告 releaseDate 2026-09-24 07:30 UTC）
- https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=d49de208bb6d4a26b02677d7c3d89b5d — 访问 2026-10-20 — 已读（"open trading ... at 2026-09-24 11:00 (UTC)"、"Withdrawals will open at 2026-09-25 11:00 (UTC)"）
- https://clob.polymarket.com/prices-history?market=72111237001093028212763921723631481836210139498389057357896030642910594584975&startTs=1766707200&endTs=1767225600&fidelity=60 — 访问 2026-10-20 — 已读（200，首点 p=0.011）
- https://www.coinbase.com/blog/listing — 访问 2026-10-20 — 抓取失败 403（Cloudflare 挑战页），不作为来源
- https://www.coinbase.com/blog/rss — 访问 2026-10-20 — 抓取失败 403，不作为来源
- https://www.coinbase.com/rss/blog?category=listing — 访问 2026-10-20 — 404，不作为来源
- https://archive.org/wayback/available?url=www.coinbase.com/blog/listing — 访问 2026-10-20 — 已读（`archived_snapshots: {}`，无存档）
- https://archive.org/wayback/cdx/... （CDX 查询）— 访问 2026-10-20 — 抓取失败（返回码 000），不作为来源
