---
id: quant-034
name_zh: 奖励池与返佣做市前向
name_en: Polymarket Liquidity Rewards + Maker Rebate Forward MM
bot: quant
date: 2026-10-21
market: polymarket
pm_category: cross
kind: supplement
improves: composer-011, dot-032
category: M
return_type: service
instruments: Polymarket 二元市场 YES/NO 双边限价买单（流动性奖励池 + 吃单费返佣）
venues: Polymarket（global CLOB，Polygon）
data: Gamma、CLOB /rewards/markets/current 与 /rewards/markets/{condition_id}、CLOB /book 与 /books、data-api /trades；免费免密钥；历史 L2 无公开源，只能前向记录；2026-10-21T05:16Z 快照 14,383 个奖励市场，登记快照筛出 37 个事件；record.py 开始时按同一规则重选最多 40 个
test_2w: 前向 14 天，登记快照 37 个事件，record.py 开始时按同一规则冻结最多 40 个（event_id=condition_id，同一市场跨日合并为一个结果）；按报价、真实 taker SELL 成交、Q-score 奖励、feeSchedule 返佣、期末盘口平库存记账；失败：有效事件<30，或每事件净 PnL 中位≤0，或总净 PnL≤0
status: 草稿
confidence: 中
evidence: 无
result: 未测
slot: -
variants: 0
variants_ext: 不清楚
window: -
max_dd: -
contribution: 不清楚
---

## 一句话

在 Polymarket 同时有流动性奖励池和 taker 费的二元市场，对 YES/NO 各挂一笔 20 股、按 `min(最优卖价−tick, 中间价−1¢)` 定价的买单；只把真实 taker SELL 打到我们价位的成交算作成交，按官方 Q-score 计提每日奖励、按市场 `feeSchedule` 计提 maker 返佣，期末按盘口平掉库存，用 14 天、最多 40 个事件的纸面前向记录检验净现金流是否为正。

## 钱从哪里来

有两笔付款方，都是平台规则明示的：

1. **流动性奖励预算**：Polymarket 为“可成交的深度和更紧的价差”付费。官方文档写明，挂 resting limit order 的 maker 自动有资格；每个 UTC 日为一个 epoch，订单簿每分钟随机偏移采样一次，最多 1,440 个样本；按 `Q-score` 归一化后把每个市场的每日奖励分给 maker；奖励每日午夜 UTC 直接发给 maker 地址，最低支付 $1。付款方是平台的激励预算，不是对手方亏损。
2. **吃单费返佣**：官方文档写明，taker 费按 `fee = C × feeRate × p × (1-p)` 收取，maker 费为 0；平台把 taker 费的一部分按 `rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool` 每日以 pUSD 返给 maker，最低 $1。比例：crypto 20%、sports 15%、finance/politics/economics/culture/weather/other/mentions/tech 25%、geopolitics 0。返佣池来自 taker 费，所以 0 费市场没有返佣。

为什么持续：二元事件市场需要有人持续提供双边深度，平台用奖励和返佣换深度；只要平台继续这套预算，付款动机就存在。两笔钱都不是无风险：奖励池、`rewardsMinSize`、`rewardsMaxSpread`、`feeRate`、`rebateRate` 都由平台逐市场设置并可调整或结束；官方文档明确 2026-08 的 crypto 5m/15m/4h TWAP 奖励已经结束，说明整类项目会停。

## 规则

### 市场选择（机械规则，主项目可重算）

2026-10-21T05:16Z 快照，按以下顺序：

1. `GET https://clob.polymarket.com/rewards/markets/current` 分页取全部奖励市场（500 条/页，`next_cursor=LTE=` 为末页）。该快照 14,383 个市场，`total_daily_rate` 合计 $144,267.25696。
2. 保留 `total_daily_rate >= 20`、`rewards_min_size == 20`、`rewards_max_spread >= 3` 的市场。
3. 用 `GET https://gamma-api.polymarket.com/markets?condition_ids=...` 保留 `active=true`、`closed=false`、`enableOrderBook=true`、`endDate >= 2026-11-20`、两个 outcome、两个 `outcomePrices` 都在 `[0.10, 0.90]`、`feeSchedule.rate > 0`、`clobTokenIds` 有两个的市场。
4. 登记快照按 `events[0].slug` 去重，同一 event 只留日率最高的一个市场；再按日率从高到低取前 37 个 event。`record.py` 开始时对当时快照重新应用同一规则，最多取 40 个 event 并冻结在 `state.json`。
5. 登记快照结果：37 个不同 event slug，日率合计 $1,225.00；`rewards_min_size` 全为 20 股，`rewards_max_spread` 为 4.5 或 6.5 美分，`feeSchedule.rate` 为 0.03–0.07，`rebateRate` 为 0.15–0.25。登记快照的完整列表在 `forward/quant-034/PLAN.md`；`record.py` 的 `MARKETS` 是网络失败回退，最终名单在 `state.json` 的 `selected` 和 ledger 的 `挂` 行。更大池子（$500–2,000/日）多为 200 股门槛；37 个市场 × 200 股会远超单场所 2,500 USDT，所以按 20 股门槛筛选，$20–88/日 是 5,000 资金下可同时覆盖的较大池子。

记录期每天重读奖励配置和 Gamma；若某市场日率跌破 $10、`rewards_min_size` 不再是 20、`rewards_max_spread < 3`、`feeSchedule.rate <= 0`、`closed=true` 或 `endDate < 2026-11-20`，撤销该市场挂单并停止新报价。阈值从选择时的 $20 降到维护时的 $10，是登记时写死的缓冲，用来避免日常池子调整把有效事件砍到 30 个以下；不是事后调参。

### 报价（价位、份数、撤单/改价）

- 决策时刻 `T`：`record.py` 每小时运行一次，运行开始时间为 `T`。只用 `T` 之后第一次请求取得的盘口快照（`POST https://clob.polymarket.com/books` 批量取 74 个 token），`price_source` 写该快照的毫秒时间戳；CLOB 的 `timestamp` 可能比请求时间早几秒到几分钟（缓存），以“决策后第一次请求的响应”为准。
- 对每个 outcome：`mid=(best_bid+best_ask)/2`，`tick` 取 book 的 `tick_size`；只在 `0.10 <= mid <= 0.90` 且 `best_ask > best_bid` 时报价。
- 目标买价 `bid = floor_to_tick(min(best_ask - tick, mid - 0.01), tick)`；计分距离 `s=(mid-bid)×100` 必须满足 `0 <= s <= rewardsMaxSpread`，否则该侧不报。
- 每侧固定 **20 股**（正好等于 `rewardsMinSize`）；只挂买单，不挂卖单，不裸卖。
- 目标价变化 `>= tick/2`：撤旧单、按新价重挂。中间价相对挂单时移动 `>3` 美分：撤单并暂停该市场 1 小时。中间价跌出 `[0.10,0.90]`、`s` 超限、盘口缺失/过期、池子低于维护阈值、市场关闭或到结束时间：撤单，不重挂。
- 未触发条件的挂单跨小时保留；UTC 日界只重置“当日已成交股数”，不强制撤单。

### 成交判定（只算真实对手方打到我们这一档）

- 数据源：`GET https://data-api.polymarket.com/trades?market=<condition_id>&limit=1000&offset=...`，免费免密钥，返回最近约 2 万笔，按时间倒序；最多翻到 offset 5000。为避免同一秒多笔成交被游标漏掉，每次多取上次游标前 5 秒的成交，再用 trade key 去重。
- 只处理 `timestamp > 挂单时间` 的成交；只看 `asset == 我们的 token`、`side == "SELL"`（taker 卖出，打我们的 bid）、`price <= 我们的买价` 的成交。taker `BUY`（打 ask）不算我们成交。
- **排队位置假设（写死）**：挂单时记 `queue_ahead = 盘口快照中价格 >= 我们买价的全部可见 bid size 之和`；假设我们排在所有这些可见数量的最后面，且前面不撤单。对每笔符合条件的 taker SELL，`cum_sell += size`；只有超过 `queue_ahead` 的部分才算我们成交，且不超过剩余股数：
  `fill = max(0, min(remaining, cum_sell - queue_ahead - already_filled))`。
  这是保守假设（不给队列优先、不假设前面撤单）；真实成交可能更多，不会多算。
- 成交价用我们的挂单价，maker 费 0；`price_source` 写 `trade:<transactionHash>:<asset>:<timestamp>:<size>:<price>`。若一次返回 1000 笔且最早一笔仍晚于上次游标，note 记 `trade_gap`，不补造成交。

### 奖励和返佣的计算

**奖励**（官方原文）：

- 订单得分 `S(v,s)=((v-s)/v)^2·b`；`Q_one`/`Q_two` 按 YES/NO 两侧及互补市场汇总；中间价在 `[0.10,0.90]` 时 `Q_min=max(min(Q_one,Q_two), max(Q_one/c,Q_two/c))`，`c=3.0`；区间外必须双边；`Q_normal=Q_min/ΣQ_min`；`Q_epoch=ΣQ_normal`（一个 UTC 日，最多 1,440 个随机分钟样本）；`Q_final=Q_epoch/ΣQ_epoch`；奖励 `= Q_final × 市场当日奖励`；每日午夜 UTC 支付；最低 $1。
- 纸面算法：每次运行用当次盘口和我们在挂单算 `Q_own`；把盘口内其他可见订单按同一 `S` 聚合成一个“其他 maker”算 `Q_others`；`share = Q_own_min/(Q_own_min+Q_others_min)`；当天小时样本取平均，乘当天 `total_daily_rate`（`/rewards/markets/{condition_id}?sponsored=true` 把赞助日率折入 `rate_per_day`，与 `/rewards/markets/current` 的 `total_daily_rate` 同口径）。官方是每分钟随机采样，我们只有小时快照，这是近似，`结算` 行 note 写 `samples` 和 `share_mean`。
- 最低支付：官方只写“最低 $1，低于不支付”，未说明按市场/地址/日合并；本记录按**市场-日**分别应用 $1 阈值，保守处理：`reward_paid = reward_gross if reward_gross >= 1 else 0`。

**返佣**（官方原文）：

- taker 费 `fee = C × feeRate × p × (1-p)`；maker 费 0；`rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool`；`fee_equivalent = C × feeRate × p × (1-p)`；每日 pUSD，最低 $1。
- 逐笔算 `rebate_gross = C × feeRate × quote_price × (1-quote_price) × rebateRate`，`feeRate`/`rebateRate` 取 Gamma 该市场 `feeSchedule`。这等价于假设返佣池 = 全部 taker 费 × `rebateRate`，且我们的 fee-equivalent 占比按成交贡献计。按市场-日应用 $1 最低支付（同上，保守）。
- 不重复计入：`成交` 行 `pnl=0`；返佣和奖励只在每日 `结算` 行的 `pnl` 里出现一次，note 同时写 gross/paid。

### 库存与结算风险

- 每个市场每个 outcome 库存上限 **40 股**（两笔 20 股）；到上限的那一侧停止报价，另一侧可继续。
- 最大资金占用：最多 40 个市场 × 2 侧 ×（最多 40 股库存 + 最多 20 股在挂）× 约 $0.50/股 ≈ **$2,400**，低于单场所约 2,500 USDT；总资金 5,000 USDT，不加杠杆、不借钱。
- 选中的市场 `endDate` 都不早于 2026-11-20，晚于记录结束；记录结束（2026-11-05T00:00:00Z）后第一次运行撤销全部挂单，并在之后第一份盘口快照按 `best_bid` 卖出全部库存，按 taker 费 `C × feeRate × p × (1-p)` 计费；没有买盘时按 0 估值并写明。若市场提前 `closed`，按 Gamma `outcomePrices` 的 1/0 结算库存。不把库存带进结算。
- 只做二元 Yes/No，不做 negRisk 多结果转换；结算源按各市场 Gamma 规则原文，记录期不主动持有到结算。

### event_id 和独立结果

- `event_id = condition_id`（一个市场 = 一个事件）；同一市场的每日记录合并为该 event 的一个结果，不把同一市场 14 天当 14 个独立结果。
- 2026-10-21T05:16Z 快照按上述规则得到 **37 个不同 event slug**，满足 GUIDE 第 2 节“至少 30 个相互独立的结果”。2026-10-21T05:33Z 复核时其中 36 个 event 两侧都能按规则报价；primmie 市场的日率已从选择时的 23 降到 6，低于维护阈值 $10，按规则会被跳过。同一规则在 2026-10-21T05:40Z 重跑得到 40 个 event（池子每日变化），所以 `record.py` 在开始时按同一规则重选最多 40 个并冻结，既不用 05:16Z 的旧名单硬撑，也不在记录中事后调参。有效 event 数按记录期实际报价/结算的 event 计，仍以 30 为失败线。Dota 2、Valorant 等同一游戏生态的不同问题有不同 event slug 和不同结算问题，按事件分别计数；它们之间的相关性作为风险记录，不重复当作独立结果。

### 失败标准（登记时写死）

14 天结束后，满足任一条即失败：

1. 有效 event 数 `< 30`（有效 = 至少有一个 `结算` 或 `平` 行，且记录未因数据缺口作废）；
2. 有效 event 的净 PnL 中位数 `<= 0`；
3. 全部 event 净 PnL 合计 `<= 0`。

净 PnL = 该 event 的全部 `结算` 行 `pnl` 之和 + `平` 行 `pnl` 之和；`成交` 行 pnl=0，taker 费已含在 `平` 行。若某市场没有成交但每天有奖励 `结算` 行，仍算有效 event；奖励/返佣因低于 $1 为 0 也如实记 0，不剔除。

## 证据

- **官方规则，已读**：`docs.polymarket.com/programs/liquidity-rewards`（Q-score 公式、`c=3.0`、UTC 日 epoch、每分钟随机采样、最多 1,440 样本、每日午夜 UTC 支付、$1 最低支付、2026-08 crypto TWAP 奖励已结束）；`docs.polymarket.com/programs/maker-rebates`（20%/15%/25% 返佣比例、`fee_equivalent` 公式、按市场分配、每日 pUSD、$1 最低、geopolitics 0）；`docs.polymarket.com/trading/fees`（`fee=C×feeRate×p×(1-p)`、maker 0、费率表、5 位小数）；`docs.polymarket.com/market-data/market-details`（`rewardsMinSize` 单位股、`rewardsMaxSpread` 单位美分、`feeSchedule.rate/rebateRate`、tick）；`docs.polymarket.com/market-data/prices-order-books`（book 的 `timestamp` 毫秒、bids/asks）。以上是规则原文，不是收益实测。
- **公开接口快照，已读**：2026-10-21T05:16Z `GET https://clob.polymarket.com/rewards/markets/current` 返回 14,383 个奖励市场，`total_daily_rate` 合计 $144,267.25696；登记快照筛出 37 个 event、日率合计 $1,225.00；2026-10-21T05:40Z 同一规则重跑为 40 个 event，`record.py` 开始时重选最多 40 个。2026-10-21 同日用 `GET https://clob.polymarket.com/books` 和 `GET https://clob.polymarket.com/book` 读取 74 个 token 的当前盘口，用 `GET https://data-api.polymarket.com/trades?market=...` 读取成交字段（`side`、`size`、`price`、`timestamp`、`transactionHash`、`asset`）。这些是接口返回值，不是独立审计。
- **前向尚未开始**：`forward/quant-034/PLAN.md` 已按 GUIDE 第 13 节登记，开始时间 2026-10-22T00:00:00Z，结束 2026-11-05T00:00:00Z；`ledger.csv` 目前只有表头，`state.json` 尚未生成。因此本条 `evidence: 无`、`result: 未测`；没有把未开始的记录写成已有证据。
- **对照条目，已读**：dot-032 是同一 `M-M4-poly-rewards` 机制的规则/费用/数据筛查稿，明确说完整盈利回测未做、前向未启动；muse-800 是 crypto 5 分钟完整集铸造做市，靠 taker rebate 和价差，公开账户数据是 venue API 返回值（来源自报，未独立审计）；muse 的两条奖励池草稿没有前向记录。以上对照的收益数字均未用于本条结论。
- **未做完整回放**：历史 L2 没有免费公开源，`/rewards/markets/current` 只给当前配置，逐钱包历史 Q 份额和奖励支付也未取得；本条不声称已证明盈利，只用 14 天前向检验。

## 数据

- **Gamma**：`https://gamma-api.polymarket.com/markets?condition_ids=...`（每次最多 20 个 condition id）和 `https://gamma-api.polymarket.com/events?slug=...`；免费免密钥；返回市场、规则、`rewardsMinSize`、`rewardsMaxSpread`、`clobRewards`、`feeSchedule`、`endDate`、`clobTokenIds`、`orderPriceMinTickSize`。
- **CLOB**：`https://clob.polymarket.com/rewards/markets/current`（当前奖励配置，500 条/页）；`https://clob.polymarket.com/rewards/markets/{condition_id}`（单市场奖励配置，100 条/页）；`https://clob.polymarket.com/books`（批量盘口，最多 500 个 token）；`https://clob.polymarket.com/book?token_id=...`（单盘口）；免费免密钥。`/rewards/markets/{condition_id}` 返回 `tokens`、`rewards_config`、`rewards_min_size`、`rewards_max_spread`、`market_competitiveness`。
- **data-api**：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000`；免费免密钥；每个市场约最近 2 万笔成交，字段含 `side`、`size`、`price`、`timestamp`、`transactionHash`、`asset`、`conditionId`。用于成交判定和 markout 风险检查，不足以重建完整历史 L2。
- **返佣查询**：`https://clob.polymarket.com/rebates/current?date=YYYY-MM-DD&maker_address=...` 可查某地址某日返佣；本条是纸面记录，没有钱包地址，未调用该接口取实际支付。
- **缺失**：历史 L2、逐钱包历史 Q 份额、实际奖励/返佣到账、竞争者完整订单；这些只能前向记录，不能回放。

## 两周内怎么检验

- **登记**：`forward/quant-034/PLAN.md`，登记序号 1，开始 2026-10-22T00:00:00Z，结束 2026-11-05T00:00:00Z。规则、最多 40 个市场、报价/成交/奖励/返佣/库存/失败标准都在 PLAN 里写死。
- **记录**：操作员每小时从仓库根目录运行 `python3 bots/quant/forward/quant-034/record.py`；`ledger.csv` 只追加，`state.json` 只存状态。每行 note 带确定性 `uid`，重复运行不重复追加；记错另起 `action=更正` 行。
- **独立结果**：登记快照 37 个、运行时最多 40 个 event（`event_id=condition_id`），同一市场跨日合并；预计 14 天内完成 ≥30 个。若维护期有市场退出，按实际有效 event 数计。
- **失败标准**：有效 event `<30`，或每 event 净 PnL 中位 `<=0`，或总净 PnL `<=0`；任一触发即失败。
- **成本口径**：maker 费 0；奖励和返佣按官方公式；期末卖出库存按 taker 费；资金占用按现金；不计利息、不计链上 gas（记录期不做 split/merge）。
- **数据核对**：主项目可用 data-api 的逐笔成交核对 `成交` 行（`price_source` 的 transactionHash/时间戳），用 Gamma/CLOB 当前配置核对 `挂`/`撤` 行，用 `/rewards/markets/{condition_id}` 核对当日池子和 `rewardsMinSize`/`MaxSpread`。历史盘口无法复核，这是本条的主要可验证性限制。

## 成本与容量

- **报价规模**：每侧 20 股；每个市场最多 40 股/outcome 库存；最多 40 个市场最大占用约 $2,400（含在挂），低于单场所 2,500 USDT；总资金 5,000 USDT，不加杠杆。
- **成本**：maker 费 0；成交时没有 taker 费；期末卖出库存按 `C×feeRate×p×(1-p)` 计 taker 费；记录期不做 split/merge/redeem，不计 gas；资金占用不计利息。主要经济成本是逆向选择（成交后价格朝不利方向走）和库存方向风险，前向用 `平` 行实现。
- **奖励/返佣**：奖励 = 当日池子 × Q 份额；返佣 = 成交股数 × feeRate × p × (1-p) × rebateRate。两者都按市场-日应用 $1 最低支付（保守）。
- **年化贡献算法**：`年化贡献 = 14 天净 PnL × (365/14) ÷ 5,000`。由于没有历史回放、奖励份额事前不可知，且快照 Q 份额会随竞争变化，`contribution` 先写 `不清楚`；等 `RESULT.md` 有 14 天实际纸面净 PnL 后再按上式补，不把快照算术当预测。
- **容量**：最多 40 个事件、14 天，每个市场每个 outcome 最多 40 股总成交（两笔 20 股，达到库存上限即停），理论最大成交 40×2×40=3,200 股；实际成交取决于是否有人打到我们的价位。奖励按日结算，天天有样本；返佣按成交逐笔计提。

## 风险

- **规则/政策风险（最大）**：奖励池、`rewardsMinSize`、`rewardsMaxSpread`、`feeRate`、`rebateRate` 都由平台单方设定且可随时调整；官方已结束 2026-08 的 crypto 5m/15m/4h TWAP 奖励。池子跌破维护阈值时本条会停止该市场，样本数可能少于 30。
- **竞争稀释**：Q 份额是相对值；其他 maker 加大尺寸或收紧价差会稀释我们的份额。快照里部分薄市场显示 100% 可见份额，但其他 maker 随时可能进入，不能把快照当收益预测。
- **逆向选择**：长日期事件市场平时流慢，新闻/数据瞬间的 taker 流可能是知情的；成交后价格朝不利方向走会吃掉奖励。报价规则用“中间价移动 >3¢ 撤单并暂停 1 小时”限制，但不能消除。
- **成交模型风险**：data-api 只有最近约 2 万笔，且不包含队列位置；我们用“可见深度全部排在我们前面”的保守假设，真实成交可能更多或更少；如果一次拉取有缺口，note 记 `trade_gap`，不补造。
- **奖励/返佣口径风险**：官方未说明 $1 最低支付按市场、地址还是日合并；本条按市场-日单独截断，偏保守。官方 Q-score 每分钟随机采样，我们只有小时快照；`share_mean` 是近似，不是官方 Q_final。
- **库存/结算风险**：只做二元 Yes/No，但单边成交会留下方向库存；期末按 `best_bid` 卖出，薄市场可能滑点很大；若市场提前结算，按 Gamma 1/0 处理。选中的市场 `endDate` 都晚于记录结束，正常情况下不持有到结算。
- **相关性风险**：最多 40 个 event 里有多个 Dota 2、Valorant、足球/篮球市场，同一游戏生态或同一赛季内可能同时受一个新闻驱动；GUIDE 按 event slug 计数，但主项目若按更粗的“同一标的/数据源”合并，独立结果会少于实际选中的 30–40 个。这是本条最需要主项目复核的地方。
- **平台/链上风险**：Polymarket global CLOB、Polygon、pUSD/USDC 结算、预言机争议、地区限制；本条只读公开接口，不交易、不连钱包，纸面记录不产生真实链上风险，但真实执行会有。
- **数据可验证性**：历史 L2 无公开源，主项目只能核对成交和当前配置，不能完整复核我们的盘口快照；`price_source` 记录快照时间戳和成交哈希，便于抽查但不能重放整本订单簿。

## 改进了什么

不适用（`kind: supplement`）。相对最接近的 dot-032，本条新增的是可执行的前向证据和记账口径，而不是新付款方：

1. **从“规则稿”到已登记前向**：dot-032 的 forward 只是未启动计划；本条按 GUIDE 第 13 节登记 `forward/quant-034/`，写死开始/结束、最多 40 个市场、报价/撤单/成交/库存/结算规则和失败标准，并交确定性 `record.py`。
2. **机械选池并给出可核对的数量**：用 `/rewards/markets/current` + Gamma 的 `total_daily_rate`、`rewardsMinSize`、`rewardsMaxSpread`、`feeSchedule.rate`、`endDate`、价格区间，一层层筛出 37 个（登记快照）/最多 40 个（开始时重选）不同 event slug；不是手挑几个示例市场。dot-032 只给了 5 个示例。
3. **奖励和返佣合并记账**：每条 `成交` 按市场 `feeSchedule` 计 `rebate_gross`，每日 `结算` 同时记 reward 和 rebate 的 gross/paid；dot-032 主要整理 Q-score，没有把 maker rebate 逐笔并入同一本账。
4. **明确的排队成交规则**：`queue_ahead` = 挂单时价格不劣于我们的全部可见 bid size；只算挂单时间之后的真实 taker SELL，累计超过队列才成交；dot-032 只写“不能只看到 print 就假定己方成交”，没有给出可执行的队列算法。
5. **库存上限和期末退出**：40 股/outcome 上限、到限停报、结束按 `best_bid` 卖出并计 taker 费；dot-032 只有“每侧最多 50 份”的静态上限，没有退出路径。
6. **独立结果按 event 计并核对数量**：`event_id=condition_id`，登记快照 37 个、运行时最多 40 个不同 event slug；dot-032 说“30 个独立簇未知”，本条在快照上给出 37 并写进 PLAN。

与 muse-800 的区别：muse-800 做 crypto 5 分钟 Up/Down 的完整集铸造 + 双边 post-only 卖单，收益主要来自 taker rebate 和价差；本条做长日期二元奖励市场，不铸造完整集、不卖单、只挂双边买单，收益主要来自流动性奖励，返佣是次要项。与 known/M-M4-poly-rewards 的关系：M-M4 是主项目已有的“预测市场挂单领奖励”机制，dot-032 是它的规则整理稿；本条是对 dot-032 的补充，不是新机制。

## 与 composer-011 的关系（先到先得）

composer-011（2026-10-21 07:16 CEST 推送，早于本条 08:12 CEST）和本条是**同一机制**：在有 CLOB 流动性奖励池的 Polymarket 二元市场双边挂被动单，赚奖励 + maker 返佣 ± 价差，付款方都是平台奖励预算和 taker 费返佣池，同属 known/M-M4-poly-rewards。按 GUIDE 第 3.3 节，本条不占新机制，只是 composer-011（及 dot-032）的补充；两份前向登记都已冻结，规则以各自 PLAN 为准，本节只陈述差异，不改 `forward/quant-034/PLAN.md`。

| 方面 | composer-011 | quant-034 |
|---|---|---|
| 选市 | 每天 06:00 UTC 按 Gamma `rewardsDailyRate` 降序取前 3 个 politics/crypto/finance 市场，每日可换 | 开始时按 `/rewards/markets/current` 冻结最多 40 个 event：日率≥$20、`rewards_min_size`=20、`max_spread`≥3、`feeSchedule.rate`>0、价格 0.10–0.90、`endDate`≥2026-11-20，跨板块；维护期跌破 $10 等退出 |
| 报价 | 只在 Yes token 上挂买+卖两边，`bid=min(best_bid+0.001, mid−maxSpread/2)`、ask 对称，spread<0.02 当日不报 | YES、NO 各挂一笔**买单**（不挂卖单、不裸卖），`bid=floor_to_tick(min(best_ask−tick, mid−0.01))`，须 `0≤s≤rewardsMaxSpread`；mid 移动>3¢ 撤单暂停 1 小时 |
| 份数/库存 | 每边 max(minSize,200)、≤400 份；净 Yes 绝对值≤500 | 每侧 20 股（=minSize）；每 outcome 库存≤40 股；期末按 best_bid 卖出并计 taker 费 |
| 成交判定 | data-api 成交价**等于**挂单价且方向相反即成交，当日该价位量<size 时部分成交；另扣半个 spread | 只算挂单后、`side=SELL`、`price≤我们买价` 的 taker 成交，且须累计超过挂单时可见的 `queue_ahead`（价格不劣于我们的全部 bid）才算我们成交；不另扣半 spread，逆向选择由期末平仓实现 |
| 奖励公式 | 满足 minSize/maxSpread 记 1 单位，按 `rate × 1/3` 均分，不用 Q-score | 按官方 Q-score（`S=((v−s)/v)^2`、`Q_min` 含 `c=3.0`）对比盘口其他可见订单算份额，小时样本平均 × 当日 `total_daily_rate`；按市场-日套 $1 最低支付 |
| 返佣 | 对手 taker 费 × 固定 20% | 逐笔 `C×feeRate×p×(1−p)×rebateRate`，取各市场 `feeSchedule`（15–25%，geopolitics 0）；按市场-日套 $1 最低支付 |
| 独立结果 | 每日最多 3 个市场，14 天内累计 distinct conditionId 才可能到 30 | 一开始即有 37–40 个 event，同市场跨日合并 |

上述差异只是检验口径不同，不说明本条更好：两条都尚无实测，谁的口径更接近真实收益要等两份 RESULT.md 对照，所以 `kind` 仍写 `supplement` 而不写 `improvement`。

## 门槛自查

1. **机制说得清**：满足 — 付款方是平台流动性奖励预算和 taker 费返佣池；Q-score、返佣比例、费率和最低支付都有官方原文，规则和记账口径写在 PLAN 里。
2. **有免费数据能检验**：满足（有限制）— Gamma、CLOB `/rewards/markets/current`、`/rewards/markets/{condition_id}`、`/books`、data-api `/trades` 都免费免密钥；历史 L2 没有公开源，所以只能前向，不能回放；登记快照 37 个 event 已在 2026-10-21T05:16Z 核对，开始时按同一规则重选最多 40 个。
3. **小资金能做**：满足 — 每侧 20 股、每 outcome 最多 40 股库存，最多 40 个市场最大占用约 $2,400，低于单场所 2,500；总资金 5,000，不加杠杆、不借钱、不裸卖。
4. **不重复**：满足 — `kind: supplement`，`improves: composer-011, dot-032`；同机制 composer-011 先推送，本条只补执行口径；和 muse-800（5m 完整集铸造）、muse 的返佣/奖励池草稿、known/M-M4 的付款方相同但执行市场、库存路径和记账不同；本条只补 dot-032 的执行与证据，不主张新机制。
5. **扣成本后粗算够用**：不确定 — 没有历史回放，奖励份额和逆向选择成本事前不可知；快照 Q 份额不能当预测。本条正是用 14 天前向回答这个问题，不硬写正收益。
6. **两周内能检验**：满足 — 登记快照 37、运行时最多 40 个 event、14 天、固定失败标准（有效 event<30 或每 event 净 PnL 中位≤0 或总净 PnL≤0）；若维护期市场退出，按实际有效 event 数如实判定。
7. **出处可查**：满足 — 官方文档、CLOB/Gamma/data-api 端点、快照日期和数字都给了链接与访问日期；来源自报的对照条目（dot-032、muse-800）已标“未独立审计”，未把它们的收益当本条证据。

## 出处

- https://docs.polymarket.com/programs/liquidity-rewards — 访问 2026-10-21 — 已读（Methodology、Equations、Worked Example、UTC epoch、1,440 samples、$1 最低支付、crypto TWAP 奖励已结束）
- https://docs.polymarket.com/programs/maker-rebates — 访问 2026-10-21 — 已读（返佣比例表、fee_equivalent 公式、按市场分配、每日 pUSD、$1 最低、geopolitics 0）
- https://docs.polymarket.com/trading/fees — 访问 2026-10-21 — 已读（fee 公式、maker 0、费率表、5 位小数）
- https://docs.polymarket.com/market-data/market-details — 访问 2026-10-21 — 已读（rewardsMinSize/MaxSpread 单位、feeSchedule.rate/rebateRate、tick）
- https://docs.polymarket.com/market-data/prices-order-books — 访问 2026-10-21 — 已读（book timestamp、bids/asks、/books 批量上限 500）
- https://docs.polymarket.com/api-reference/rewards/get-current-active-rewards-configurations — 访问 2026-10-21 — 已读（`/rewards/markets/current`，500 条/页，LTE= 末页）
- https://docs.polymarket.com/api-reference/rewards/get-raw-rewards-for-a-specific-market — 访问 2026-10-21 — 已读（`/rewards/markets/{condition_id}`，100 条/页，tokens/rewards_config）
- https://docs.polymarket.com/api-reference/rebates/get-current-rebated-fees-for-a-maker — 访问 2026-10-21 — 已读（`/rebates/current`，需 date 和 maker_address；本条未调用）
- https://docs.polymarket.com/market-data/public-analytics — 访问 2026-10-21 — 已读（data-api trades 字段和 `side/size/price/timestamp/transactionHash` 语义）
- https://clob.polymarket.com/rewards/markets/current — 访问 2026-10-21T05:16Z — 已读（14,383 个奖励市场，日率合计 $144,267.25696）
- https://clob.polymarket.com/rewards/markets/0xbe91fb5f94bce3e9e0f8e1ee13033c2e3a35bb9bededbbb43de5bf28d79478b0 — 访问 2026-10-21 — 已读（单市场奖励配置、tokens、rewards_min_size、rewards_max_spread）
- https://clob.polymarket.com/books — 访问 2026-10-21 — 已读（74 个 token 的当前盘口、timestamp、tick_size）
- https://data-api.polymarket.com/trades?market=0x3738ad9665480991affe3ba286cd035516e17d1f8b7703e05088ec19c70c21a4&limit=5 — 访问 2026-10-21 — 已读（成交字段样例；本条实际用同一端点逐市场读取）
- https://gamma-api.polymarket.com/markets?condition_ids=0xbe91fb5f94bce3e9e0f8e1ee13033c2e3a35bb9bededbbb43de5bf28d79478b0 — 访问 2026-10-21 — 已读（feeSchedule、rewardsMinSize/MaxSpread、endDate、clobTokenIds）
- bots/dot/entries/dot-032-polymarket-liquidity-rewards.md — 访问 2026-10-21 — 已读（同机制规则稿；其 forward 未启动，收益未证明）
- bots/muse/entries/muse-800-polymarket-5m-complete-set-mm.md — 访问 2026-10-21 — 已读（crypto 5m 完整集铸造 + rebate；公开账户数据为 venue API，来源自报，未独立审计）
- known/KNOWN.md — 访问 2026-10-21 — 已读（M-M4-poly-rewards 暂缓；本条为 supplement）
