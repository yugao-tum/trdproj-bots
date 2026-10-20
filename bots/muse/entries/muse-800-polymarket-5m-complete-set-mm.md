---
id: muse-800
name_zh: 5分钟涨跌完整集铸造做市
name_en: 5-minute Up/Down complete-set mint market making
bot: muse
date: 2026-10-20
market: polymarket
pm_category: crypto
kind: new
improves: -
category: M
return_type: service
instruments: "btc-updown-5m（BTC 5 分钟 Up/Down 二元市场；1 Up + 1 Down = 1 份完整集）"
venues: Polymarket（global CLOB，Polygon）
data: "Gamma / CLOB / data-api 公开免密钥：市场规则、feeSchedule（crypto rate 0.07、rebateRate 0.2）、逐笔成交、账户 PnL/活动；5m 历史 L2 无免费源，回放用公开 taker prints + 队列假设；账户 PnL 自 2026-07-24 起 89 天"
test_2w: "用公开 data-api 逐笔成交回放 ≥30 个 UTC 日的 5m 窗口（每日约 288 窗，按日聚合为 30+ 个独立结果）；每窗 500 对、post-only、fair+0.03、1s 延迟、队列 0/250/500/1000 股；失败：30 天日净 PnL 中位数 ≤0，或盈利天数 <15/30，或按 20bps 保守返佣后总净 PnL <0，或 500 股队列档成交率 <账户同期的 50%"
status: 待核
confidence: 中
---

> 作者：deepseek worker（muse）｜ 第 1 轮

## 一句话

在每个 BTC 5 分钟涨跌窗口开始前铸造 1:1 的 Up/Down 完整集，然后在两边同时挂 post-only 卖单，赚取吃单者支付的价差和 Polymarket 从吃单费中分给 maker 的 20% 返佣；窗口结束后把未卖出的完整集 merge 回 USDC，未配对的赢方 redeem。

## 钱从哪里来

- **主要付款方是 Polymarket 的 taker fee 池**：crypto 5m 市场的吃单者按 `C × 0.07 × p × (1-p)` 付费，平台把其中 20% 按 maker 的成交贡献返还，按日以 pUSD 发放、最低 $1（官方文档，2026-10-20 已读）。账户的公开数据也显示每日有 MAKER_REBATE 入账（2026-10-19 一笔 $71.1599）。
- **第二来源是价差**：做市方在每个 outcome 上挂 `fair + 0.03` 的卖单，赚 3 美分/股的报价 edge。但账户 Oct 5–12 tape 的市场 PnL 只有约 $0.146/窗口（750 对、约 219 股成交），折合约 0.067 美分/股——3 美分的 edge 大部分被逆向选择吃掉。**因此这条策略本质上是“返佣捕获 + 完整集风险管理”，价差是次要的。**
- **为什么持续**：5 分钟二元市场的高频、方向性零售流需要有人提供即时流动性；完整集铸造让做市方不需要裸卖，未配对库存有限；平台用 taker fee 返佣换深度。付款动机是平台的流动性预算，不是对手方的必然亏损；返佣参数可以调整或取消，这是本条最大的政策风险。
- **不依赖已结束的奖励**：官方文档明确 2026-08 的 crypto 5m/15m/4h TWAP 流动性奖励已经结束；本条只依赖 maker rebate 和价差，不把已结束的奖励算进收益。
- **不是无风险套利**：如果只成交一边而 BTC 在窗口内单边走，未配对的一边会亏；价差和返佣是在覆盖这部分逆向选择后的净收入。

## 规则

（Polymarket：结算规则原文要点和数据源。）

- **市场模板**：`btc-updown-5m`，每个窗口 300 秒。结算比较收盘时的 60 秒 Chainlink BTC/USD TWAP 与窗口开盘的 price-to-beat（同为 TWAP）；收盘 TWAP ≥ 开盘则 Up 支付 $1，否则 Down 支付 $1。来源：仓库 README（作者自报）与 Gamma 市场规则（2026-10-20 读取；示例市场 `btc-updown-5m-1792458000`，conditionId `0xa72a7ced288f71f754d796320bf42ddf3aacb839ba9cdc795075e9032ad3ccc2`）。
- **完整集**：1 Up + 1 Down 始终值 $1。用 USDC split 出等量 Up/Down；把一对 merge 回去换回 $1。仓库通过 Polymarket 的 gasless relayer 做 split/merge/redeem；`SPLIT_SIZE=750` 即每窗 750 USDC → 750 Up + 750 Down。
- **时间线**（账户 Oct 5–12 2026 tape 的默认值）：T−293s 铸造下一窗口的 750 对；T 开盘后到 T+300s 在 Up/Down 两边挂 post-only 卖单；T+358s merge 剩余完整集；T+366s redeem 未配对的赢方。若进程晚于 T−90s 才启动，跳过该窗口。
- **报价**：默认 spot fair value——用 Binance BTCUSDT 现价、price-to-beat、剩余时间和已实现波动率估计 P(Up)，并考虑最后 60 秒 TWAP 的平均效应；每个卖价 = `fair + 0.03`，向上取 tick，且不穿过 touch（post-only）。若 fair 低于最优卖价，就 join 最优卖价；若现价超过 5 秒未更新，撤掉报价。没有方向观点。
- **配对约束**：如果一边已卖出的数量比另一边多 3 股以上，撤掉领先一边的卖单，直到另一边追上；账户的 median absolute lean 约 6 股。
- **规模/风控**：默认 clip 5/10/15/20 股；`MAX_POSITION=800` 股/outcome，`MAX_TOTAL_EXPOSURE=3000` 股，`MAX_OPEN_MARKETS=8`，`MAX_DAILY_LOSS=1000`，`MAX_ORDER_RATE=40`/10s。风控在策略之外，失败检查不发送订单。`MAX_TOTAL_EXPOSURE` 是股数口径，不能直接当 USDT 上限；本条目按自己的 500 对/窗设计另算占用。
- **结算数据源**：Chainlink BTC/USD 60 秒 TWAP（市场规则）；fair value 用 Binance spot，但屏幕参考价用 Polymarket 的 Chainlink TWAP，避免把两个场所的基差 baked into quote。

## 证据

- **来源自报，未核实**：仓库 README（作者即账户 spork30 的运营者）称，2026-10-05 至 10-12 的账户 tape 有 2,012 个已结算窗口，1,953 个窗口发生 merge；median absolute lean 约 6 股；clip 分布 5/10/15/20 股约占 33%/42%/23%/2%；maker rebate 约占 sold notional 的 42 bps。以上是作者自报，未独立复现。
- **本次直接读取的公开账户数据**（Polymarket data-api，2026-10-20）：`/v2/user-pnl?user=0x1dd2a69e73ba444ecd5d87f0073d51a670ad51c2&interval=all&fidelity=1d` 返回 89 个日点（2026-07-24 至 2026-10-20），累计 `economic_pnl=21,402.56`、`realized_market_pnl=11,639.39`、`maker_rebate=9,849.15`、`unrealized_pnl=-85.98`、`volume=6,410,249.57`、`volume_usdc=3,183,055.65`、`trade_count=882,137`。注意：`maker_rebate` 字段在 2026-09-12 后不再变化（最后一次 9,849.15），所以 9 月 12 日后的返佣未计入该字段；`economic_pnl` 也因 `wallet_income` 冻结而低估 9/12 后的返佣；`deposits/withdrawals` 为 null，无法从该接口独立核对出入金。以上是 venue API 返回值，不是独立审计。
- **同一账户的 activity**（2026-10-19 00:55 至 2026-10-20 01:01 UTC，最近 5,500 条）：4,451 条 TRADE、289 条 SPLIT（每笔 750 USDC）、286 条 MERGE、473 条 REDEEM、1 条 MAKER_REBATE（2026-10-19，$71.1599）。说明账户在样本日确实按 750 对/窗口运行，且有每日返佣入账。
- **Oct 5–12 tape 的逐日增量**（用上面的 PnL API 日点相减）：`realized_market_pnl` 从 10,502.54 增至 10,795.51，增加 $292.98；同期 `volume_usdc` 增加 $215,681、`volume` 增加 440,085 股、`trade_count` 增加 60,554。除以 2,012 个窗口：约 $107 sold notional、219 股、30 笔成交/窗口，市场 PnL 约 $0.146/窗口；`maker_rebate` 字段在这段没有变化，因此这 $0.146 **不含返佣**，是保守的市场 PnL。
- **官方规则**（2026-10-20 已读）：Polymarket 费用公式 `fee = C × feeRate × p × (1-p)`；maker 不收费；crypto 的 `feeRate=0.07`、maker rebate 为 taker fee 的 20%，按日发放、最低 $1。Gamma 的 5m 示例市场 `feeSchedule` 显示 `rate=0.07`、`rebateRate=0.2`，tick 0.01、min size 5。（Gamma/CLOB 本次重取超时，数值来自同日早先的直接读取；部署前应复核。）
- **未做独立完整回测**：`backtest_count=0`；`observed_net_return` 不是我的策略收益，而是公开账户的事后值。仓库自带的 `spork30/backtest.py` 用公开 taker prints 重建盘口，按队列位置决定成交；我未运行该代码（第三方代码，未审计，不执行）。因此“费后能赚”目前是机制 + 账户公开数据的证据，不是独立回放结论。

## 数据

- **Gamma**：`https://gamma-api.polymarket.com/markets?slug=btc-updown-5m-<window_start_epoch>` 与 `/events?slug=...`；免费免密钥；返回规则、outcomes、feeSchedule、tick、min size、rewards 配置。5m 市场按 300 秒窗口枚举；窗口起点是 Unix 秒。
- **CLOB**：`https://clob.polymarket.com/book?token_id=...`；免费免密钥；当前盘口；历史 L2 无免费完整源。
- **data-api**：`https://data-api.polymarket.com/activity?user=...&limit=500&offset=...`（offset 上限 5,000，超过返回 `max historical activity offset of 5000 exceeded`）；`/trades?market=<conditionId>`（每个市场约最近 2 万笔公开成交；该端点由 dot-032 同日读取，本次未重取）；`/v2/user-pnl?user=...&interval=all&fidelity=1d`；`/value?user=...`；`/traded?user=...`；免费免密钥。
- **Binance**：`https://api.binance.com/api/v3/klines`、`/api/v3/aggTrades`；免费免密钥；用于 fair value 的 spot/波动率；与 Chainlink TWAP 的基差需在回放中显式处理。
- **缺失**：5m 市场的历史 L2/队列位置；账户 2026-10-19 之前超过 5,000 条的 activity；`deposits/withdrawals`；独立验证的逐窗 rebate 支付（只有最近一条 $71.1599 可见）。回放必须用 taker prints + 队列假设，不能把“print 穿过卖价”当成必然成交。

## 两周内怎么检验

- **数据**：用 data-api 枚举过去 ≥30 个 UTC 日的全部 `btc-updown-5m` 市场（每天约 288 个），拉取每个市场的公开 taker prints；用 Binance 1s/1m K 线重建每个窗口的 spot、price-to-beat 和已实现波动率。
- **回放**：每个窗口按 500 对（不是账户的 750，给单场所 2,500 上限留余量）在 T−293s 铸完整集；从 T 到 T+300 用 `fair+0.03` 挂 post-only 双边卖单，1 秒延迟，队列 0/250/500/1,000 股四档；一边领先 >3 股时撤领先边；T+358 merge 剩余对，T+366 按结算价 redeem 未配对赢方。成交只在该窗口的 print 穿过卖价且队列耗尽时发生。
- **记账**：maker 费 0；返佣按官方公式 `0.2 × 0.07 × p × (1-p) × 成交股数` 逐笔计，日终汇总；主结果另给“返佣=0”和“返佣按 20 bps of sold notional”两个保守情景。merge/redeem 若走 gasless relayer 记 0，否则按 Polygon 实际 gas 记；USDC 充提成本另计。未配对库存按结算价盯市，不用中间价。
- **独立结果**：按 UTC 日聚合（30+ 天），每天一个净 PnL；同日 288 个窗口高度相关，不能当 288 个独立结果。另报 30 天中盈利天数、日 PnL 分布、最大单日亏损、按队列档位的敏感性。
- **失败标准**（预先写死）：30 天日净 PnL 中位数 ≤0；或盈利天数 <15/30；或按 20 bps 保守返佣后总净 PnL <0；或 500 股队列档的成交率 <账户同期成交率的 50%；或最大单日亏损 >总资金 10%。任一触发即判该规模下不可用。
- **对照**：同一数据上跑“touch-only 报价（FAIR_EDGE=0）”和“只挂单不铸完整集（裸卖）”两个对照；若 fair edge 的增量在扣返佣后消失，说明收益主要来自返佣而不是价差，需单列返佣依赖。

## 成本与容量

- **成本**：maker 不付 taker fee；split/merge/redeem 若走 gasless relayer 为 0，否则 Polygon gas 约几美分/笔（未实测，按实际链上 gas 计）。主要成本是逆向选择/库存风险：未配对的一边在 BTC 单边走时会亏，价差 3 美分和返佣需覆盖它。
- **规模设计**：账户默认 750 对/窗口；为满足单场所 ≤2,500 USDT，本条目用 500 对/窗口。任意时刻有当前窗口 + 下一窗口两笔铸造（T−293s 铸下一窗），峰值约 500×2 = 1,000 USDC 锁定；两窗共 2,000 股（500 Up + 500 Down ×2），按 $0.5/股约 $1,000 市值；未配对 lean 约 6–20 股，另留 <100 USDC 缓冲。总占用 <1,500 USDC，低于 2,500 上限。若同时开更多窗口，按 500/窗线性增加，最多 5 窗即到 2,500。
- **收益粗算（只用公开账户 tape，不保证）**：Oct 5–12 的 2,012 个窗口中，账户 `realized_market_pnl` 增加 $292.98（`maker_rebate` 字段自 9/12 起冻结，故不含这段返佣），折合约 $0.146/窗口（750 对、219 股、$107 sold notional）。缩到 500 对按 2/3 计约 $0.097/窗口。返佣按作者估算 42 bps × $107 ≈ $0.45/窗口；按更保守的 20 bps ≈ $0.21/窗口。合计约 $0.31–0.55/窗口；288 窗/天 ≈ $89–158/天。这个数字看起来很高，是因为资金每 5 分钟周转一次；它不是年化保证，且高度依赖成交率和返佣。若返佣归零，只剩约 $0.10/窗口（500 对），仍为正但缓冲很薄。
- **容量**：5m 市场深度未独立测量；账户在 750 对下每天约 4,451 笔成交、289 次 split，说明该规模已被市场吸收；500 对更小，但成交率可能因队列份额下降而非线性下降。一个月机会 = 约 288 × 30 = 8,640 个窗口；有效容量需用回放的队列档位验证，不能由账户规模直接外推。

## 风险

- **返佣政策风险**：20% 的 maker rebate 是平台参数，可能调整或取消；账户 tape 显示价差 edge 的绝大部分被逆向选择吃掉，返佣是主要利润。若返佣归零，收益会从约 $0.31–0.55/窗口降到约 $0.10/窗口，仍为正但很薄。
- **逆向选择/单边行情**：BTC 在 5 分钟内单边走时，只成交一边，未配对的一边可能亏掉多个窗口的价差；3 美分的 edge 和 lean 约束只能限制、不能消除。
- **成交模型风险**：公开 taker prints 不包含队列位置；回放假设“print 穿过卖价 + 队列耗尽才成交”，真实成交可能更少或更多。账户的 42 bps 返佣是作者估算，官方公式随成交价变化（p=0.5 时约 70 bps，p=0.7 时约 42 bps，p=0.9 时约 14 bps）。
- **结算/预言机风险**：5m 市场按 60 秒 Chainlink TWAP 结算，极端行情下 TWAP 与最后成交价可能偏离；窗口边界、延迟和数据源故障会影响未配对边的价值。
- **运营风险**：需要持续运行、处理 split/merge/redeem、CLOB 断连、post-only 拒单、gasless relayer 故障；账户需要 builder credentials 和私钥，任何密钥管理失误都是灾难性的。本条目不提供实盘代码或密钥。
- **样本/选择风险**：公开账户是作者自己的展示账户，只有 89 天 PnL 和 7 天 tape 的细节；可能有生存者偏差、提款/入金未披露、返佣字段冻结。不能把账户历史当成策略的上界或保证。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清**：满足。吃单者付 taker fee，平台把其中 20% 返给 maker；完整集铸造把裸卖风险变成可管理的未配对库存；价差是次要收入。
2. **有免费数据能检验**：满足。Gamma/CLOB/data-api 免密钥；5m 市场逐笔成交和账户 PnL 可公开读取；历史 L2 无免费源，回放用 taker prints + 队列假设（已写明）；账户 PnL 已有 89 天，30 个 UTC 日的市场覆盖需在检验时逐日枚举。
3. **小资金能做**：满足。总资金 5,000；Polymarket 单场所 ≤2,500；500 对/窗、两窗重叠约 1,000 USDC 锁定，无杠杆；容量受 5m 深度限制，未独立测量。
4. **不重复**：满足。与 known/M-M1-orderbook-mm（CEX 盘口做市）、M-M4-poly-rewards（Q-score 流动性奖励）、A-A5-poly-complete-set（折价完整集套利）以及 dot-032（Q-score）、dot-006（负风险多结果转换）关键变量不同：本条是 5m 二元市场的完整集铸造 + 双边 post-only 卖单 + taker fee 返佣 + merge/redeem。
5. **扣成本后粗算够用**：满足（有条件）。按账户 Oct 5–12 tape 的市场 PnL $0.146/窗（750 对），缩到 500 对约 $0.097/窗；加 20–42 bps 返佣约 $0.21–0.45/窗；合计约 $0.31–0.55/窗，扣 gas 和保守滑点后仍为正。若返佣归零，约 $0.10/窗，仍为正但薄；依赖成交率和返佣。
6. **两周内能检验**：满足。用公开数据回放 30+ 个 UTC 日（每日 288 窗，按日聚合为 30+ 个独立结果），失败标准明确；队列档位和返佣情景已预先写死。
7. **出处可查**：满足。官方费用/返佣文档、Gamma 市场规则、data-api 账户数据、仓库 README 均有链接和访问日期；来源自报/venue API 未审计处已标注。

## 出处

- https://docs.polymarket.com/polymarket-learn/trading/fees — 访问 2026-10-20 — 已读（费用公式、maker 不收费、crypto rate 0.07、rebate 20%）
- https://docs.polymarket.com/programs/maker-rebates — 访问 2026-10-20 — 已读（返佣按日发放、最低 $1、按成交贡献）
- https://docs.polymarket.com/programs/liquidity-rewards — 访问 2026-10-20 — 已读（crypto 5m/15m/4h TWAP 奖励已于 2026-08 结束；本条不依赖它）
- https://gamma-api.polymarket.com/markets?slug=btc-updown-5m-1792458000 — 访问 2026-10-20 — 已读（示例 5m 市场规则、feeSchedule rate=0.07/rebateRate=0.2、tick 0.01、min size 5；本次重取超时，数值来自同日早先读取）
- https://github.com/0xbrutusdev/polymarket-5min-crypto-trading-bot — 访问 2026-10-20 — 已读（README、spork30/config.py、strategy.py、backtest.py；作者自报的 tape 与参数）
- https://data-api.polymarket.com/v2/user-pnl?user=0x1dd2a69e73ba444ecd5d87f0073d51a670ad51c2&interval=all&fidelity=1d — 访问 2026-10-20 — 已读（账户累计 PnL/成交量/返佣字段）
- https://data-api.polymarket.com/activity?user=0x1dd2a69e73ba444ecd5d87f0073d51a670ad51c2&limit=500&offset=0 — 访问 2026-10-20 — 已读（最近 5,500 条活动；offset 上限 5,000）
- https://data-api.polymarket.com/trades?market=0xa72a7ced288f71f754d796320bf42ddf3aacb839ba9cdc795075e9032ad3ccc2 — 访问 2026-10-20 — 摘要（端点存在与用途来自 bots/dot/entries/dot-032 的同日读取；本次未重取）
