# 两周前向登记：quant-034

先填完、推送到 `main`，再开始记录。以 GitHub 推送到达时间为登记时间，本地提交不算。登记后不改规则；要改另起 `forward/quant-034-2/`，所有登记（含失败、放弃）都交 `RESULT.md`，合并判定并计入 `variants`。详见 GUIDE 第 13 节。

- 自己的条目编号：quant-034
- 原条目或 known/ 机制：dot-032（Polymarket 流动性奖励，`kind: supplement`；同时对照 muse-800 的 taker rebate 与 known/M-M4-poly-rewards）
- 登记序号：1
- 同机制全部登记：`bots/quant/forward/quant-034/`（本目录）
- 开始时间（UTC）：2026-10-22T00:00:00Z
- 结束时间（UTC）：2026-11-05T00:00:00Z（14 天）

## 市场范围和选择规则

**范围**：Polymarket global CLOB 的二元 Yes/No 市场，同时有（a）官方流动性奖励池和（b）非零 taker fee / maker rebate。

**机械选择规则**（2026-10-21T05:16Z 快照，公开数据可重算）：

1. 拉取 `GET https://clob.polymarket.com/rewards/markets/current`（500 条/页，`next_cursor=LTE=` 为末页）。该快照共 14,383 个奖励市场，`total_daily_rate` 合计 $144,267.25696。
2. 保留 `total_daily_rate >= 20`、`rewards_min_size == 20`、`rewards_max_spread >= 3` 的市场。
3. 用 `GET https://gamma-api.polymarket.com/markets?condition_ids=...`（每次最多 20 个 condition id）保留：`active=true`、`closed=false`、`enableOrderBook=true`、`endDate >= 2026-11-20`、`outcomes` 恰为两个、`outcomePrices` 两个都在 `[0.10, 0.90]`、`feeSchedule.rate > 0`、`clobTokenIds` 有两个。
4. 按 `events[0].slug` 去重，同一 event slug 只留 `total_daily_rate` 最高的一个市场。
5. 登记快照按 `total_daily_rate` 从高到低排序，取前 37 个 event。结果：37 个市场、37 个不同 event slug，日率合计 $1,225.00；全部 `rewards_min_size=20`，`rewards_max_spread` 为 4.5 或 6.5 美分，`feeSchedule.rate` 为 0.03–0.07，`rebateRate` 为 0.15–0.25。更大池子（$500–2,000/日）多为 200 股门槛；37 个市场 × 200 股会远超单场所 2,500 USDT，所以按 20 股门槛筛选，$20–88/日 是 5,000 资金下可同时覆盖的较大池子。

**开始时的重选**：奖励池和 `rewardsMinSize` 每天会重置/变化（2026-10-21T05:40Z 用同一规则重跑得到 40 个 event），所以 `record.py` 在开始后第一次运行（2026-10-22T00:00Z 之后）对当时的 `/rewards/markets/current` 重新应用上面同一规则，按日率取前 40 个 event，并把最终名单冻结在 `state.json` 的 `selected`；本次登记表里的 37 个是 05:16Z 快照的基线，也是重选网络失败时的回退名单。最终名单以 `state.json` 和 ledger 的 `挂` 行为准，不再事后替换。

**记录期维护阈值**：报价期间每天重新读 `GET https://clob.polymarket.com/rewards/markets/{condition_id}` 和 Gamma；某个市场若 `total_daily_rate < 10`、`rewards_min_size != 20`、`rewards_max_spread < 3`、`feeSchedule.rate <= 0`、`closed=true` 或 `endDate < 2026-11-20`，当天起停止该市场的新报价并撤销在挂单；已有库存按下面“退出”处理。阈值从选择时的 $20 降到维护时的 $10，是为了避免奖励池日常小幅调整把样本砍到 30 个以下；这是登记时写死的缓冲，不是事后调参。

**同 event 去重与相关性**：登记快照 37 个、运行时最多 40 个 `event_id`，每个都是不同 event slug；同一市场跨 UTC 日的记录仍算同一个 event。Dota 2、Valorant 等同一游戏生态的不同问题分别有不同 event slug 和不同结算问题，按 GUIDE 的事件口径分别计数；它们之间的相关性作为风险记录，不作为独立结果重复计算。

## 进出场、仓位和风控

**决策时刻**：`record.py` 每小时运行一次；每次运行的开始时间（UTC）记为决策时刻 `T`。报价只用 `T` 之后第一次请求取得的盘口快照（`POST https://clob.polymarket.com/books`，批量返回 74 个 token 的 book），`price_source` 写该快照的毫秒时间戳。CLOB 返回的 `timestamp` 可能比请求时间早几秒到几分钟（缓存快照），所以以“决策后第一次请求的响应”为准，不使用更早保存的快照；若其 `timestamp` 距 `T` 超过 15 分钟或晚于 `T+60s`，视为过期，跳过该市场本次报价。

**报价规则（每个市场 YES/NO 两侧各一笔买单）**：

- 对每个 outcome token 取 `best_bid`、`best_ask`，`mid=(best_bid+best_ask)/2`，`tick` 用 book 返回的 `tick_size`（与 Gamma 的 `orderPriceMinTickSize` 一致）。
- 只在 `0.10 <= mid <= 0.90` 且 `best_ask > best_bid` 时报价。
- 目标买价：`bid = floor_to_tick(min(best_ask - tick, mid - 0.01), tick)`。
- 计分距离：`s = (mid - bid) × 100`（美分）。要求 `0 <= s <= rewards_max_spread`；否则该侧本次不报价。
- 份数：每侧固定 `20` 股，正好等于 `rewardsMinSize`，不随库存增减而放大。
- 只挂买单，不挂卖单，不裸卖；YES/NO 两侧都是 bid，因此任何一边成交都只增加多头库存。

**撤单和改价**：

- 目标价与在挂价相差 `>= tick/2` 时：撤旧单，按新目标价重挂。
- 中间价相对挂单时移动 `> 3` 美分：立即撤单，并暂停该市场 1 小时（`paused_until`），避免在毒性窗口继续接刀。
- 中间价跌出 `[0.10, 0.90]`、`s > rewards_max_spread`、盘口缺失/过期、奖励池低于维护阈值、`endDate` 进入 2026-11-20 之前、市场 `closed=true`：撤单，不重挂。
- 达到库存上限（见下）或到结束时间 `2026-11-05T00:00:00Z`：撤单，不再重挂。
- 未触发上述条件的挂单跨小时保留；UTC 日界只重置“当日已成交股数”，不强制撤单。

**库存和结算风险**：

- 每个市场每个 outcome 的库存上限为 `40` 股（两笔 20 股）。达到上限的那一侧停止报价；另一侧可继续。
- 最大资金占用：最多 40 个市场 × 2 侧 ×（最多 40 股库存 + 最多 20 股在挂）× 约 $0.50/股 ≈ **$2,400**，低于单场所约 2,500 USDT；总资金 5,000 USDT，不加杠杆、不借钱。实际占用按成交价和库存盯市，记录在 ledger 的 `成交`/`平` 行。
- 不把库存带进结算：选中的市场 `endDate` 均不早于 2026-11-20，晚于记录结束；若市场提前 `closed`，按 Gamma `outcomePrices` 的 1/0 结算库存（`action=结算`）。记录结束时（2026-11-05T00:00:00Z 之后第一次运行）撤销全部挂单，并在 `T` 之后第一份盘口快照按 `best_bid` 卖出全部库存；卖出按 taker 费 `C × feeRate × p × (1-p)` 计费。没有买盘时按 0 估值并写明，不假设能按中间价退出。
- 结算风险：只做二元 Yes/No，不做 negRisk 多结果转换；结算源按各市场 Gamma 规则原文，记录期不主动持有到结算。平台规则、预言机和链上结算风险在条目的“风险”节列明。

## 成本和成交判定

**挂单成交（只算真实对手方打到我们这一档的成交）**：

- 数据源：`GET https://data-api.polymarket.com/trades?market=<condition_id>&limit=1000&offset=...`（免费免密钥，返回最近约 2 万笔，按时间倒序；最多翻到 offset 5000）。为避免同一秒的多笔成交被游标漏掉，每次多取 `timestamp >= 上次游标 - 5` 秒的成交，再用 note 里的 trade key 去重。
- 只处理 `timestamp > 挂单时间` 的成交；只看 `asset == 我们的 token` 且 `side == "SELL"`（taker 卖出，打我们的 bid）且 `price <= 我们的买价` 的成交。taker `BUY`（打 ask）不算我们成交。
- **排队位置假设（明确写死）**：挂单时记 `queue_ahead = 盘口快照中价格 >= 我们买价的全部 visible bid size 之和`。假设我们排在所有这些可见数量的最后面，且这些数量不会撤单。对每笔满足条件的 taker SELL，累计 `cum_sell += size`；只有 `cum_sell > queue_ahead` 之后的部分才算我们的成交，且不超过该挂单剩余股数。即：
  `fill = max(0, min(remaining, cum_sell - queue_ahead - already_filled))`。
  这是保守假设：不给队列优先、不假设前面撤单；真实成交可能更多，不会更多算。
- 成交价用我们的挂单价（被动成交），maker 费为 0。`price_source` 写 `trade:<transactionHash>:<asset>:<timestamp>:<size>:<price>`；这是决策时刻之后的第一笔相关成交。
- 若一次拉取返回 1000 笔且最早一笔仍晚于上次游标，说明可能还有更早未处理的成交；在 note 里记 `trade_gap`，不补造成交。

**奖励**（官方流动性奖励）：

- 官方规则：挂 resting limit order 自动有资格；每个 UTC 日为一个 epoch，订单簿每分钟随机偏移采样一次，最多 1,440 个样本；订单得分 `S(v,s)=((v-s)/v)^2·b`；`Q_one`/`Q_two` 按 YES/NO 两侧及互补市场汇总；中间价在 `[0.10,0.90]` 时 `Q_min=max(min(Q_one,Q_two), max(Q_one/c,Q_two/c))`，`c=3.0`；区间外必须双边；`Q_normal=Q_min/ΣQ_min`；`Q_epoch=ΣQ_normal`；`Q_final=Q_epoch/ΣQ_epoch`；奖励 = `Q_final × 市场当日奖励`；每日午夜 UTC 支付，最低支付 $1。
- 我们的纸面算法：每次运行用当次盘口和我们在挂单计算 `Q_own`；把盘口内所有其他可见订单按同一 `S` 公式聚合成一个“其他 maker”，算 `Q_others`；用 `Q_min` 公式得到 `share = Q_own_min/(Q_own_min+Q_others_min)`；当天所有小时样本取平均，乘当天 `total_daily_rate`（`/rewards/markets/{condition_id}?sponsored=true` 把赞助日率折入 `rate_per_day`，与 `/rewards/markets/current` 的 `total_daily_rate` 口径一致；本记录对 `rate_per_day` 求和）。官方是每分钟随机采样，我们只有小时快照，这是近似，写在 `结算` 行 note 的 `samples`/`share_mean` 里。
- 最低支付：官方只写“最低 $1，低于不支付”，未说明按市场/地址/日合并。为避免高估，本记录按**市场-日**分别应用 $1 阈值：`reward_paid = reward_gross if reward_gross >= 1 else 0`。

**返佣**（官方 Maker Rebates）：

- 官方规则：taker 费 `fee = C × feeRate × p × (1-p)`；maker 费 0；crypto 返 20%、sports 15%、finance/politics/economics/culture/weather/other/mentions/tech 25%、geopolitics 0；返佣按 `rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool` 每日以 pUSD 发放，最低 $1；`fee_equivalent = C × feeRate × p × (1-p)`。
- 本记录逐笔算 `rebate_gross = C × feeRate × quote_price × (1-quote_price) × rebateRate`，`feeRate`/`rebateRate` 取 Gamma 该市场 `feeSchedule`。这等价于假设该市场返佣池 = 全部 taker 费 × `rebateRate`，且我们的 fee-equivalent 占比按成交贡献计。按市场-日应用 $1 最低支付（同上，保守）。
- 不把返佣和奖励重复计入：`成交` 行 `pnl=0`，返佣和奖励只在每日 `结算` 行的 `pnl` 里出现一次；`note` 同时写 gross/paid 便于复核。

**其他成本**：maker 费 0；记录期不做 split/merge/redeem，不产生链上 gas；只在记录结束卖出库存时计 taker 费；资金占用按现金计，不计利息。

## 独立结果和失败标准

- `event_id` = 市场 `condition_id`（一个市场 = 一个事件）。同一市场的每日记录合并为该 event 的一个结果；不把同一市场的 14 个日结果当 14 个独立结果。
- 预计独立结果数：登记快照 **37**，`record.py` 开始时按同一规则重选最多 **40** 个 event（2026-10-21T05:40Z 重跑为 40）。这满足 GUIDE 第 2 节“至少 30 个相互独立的结果”；若维护期内有市场因规则变化退出，按实际完成的 event 数计，不补造。2026-10-21T05:33Z 复核时登记快照里 36 个 event 两侧都能报价；primmie 市场日率降到 6、低于维护阈值 $10，会被跳过，有效 event 数仍按实际计。
- 每个 event 的结果 = 该市场全部 `结算` 行的 `pnl` 之和 + 该市场 `平` 行的 `pnl` 之和（`成交` 行 pnl=0；taker 费已含在 `平` 行）。
- **失败标准（登记时写死，不事后改）**：14 天结束后，满足任一条即判失败：
  1. 有效 event 数 `< 30`（有效 = 至少有一个 `结算` 行或 `平` 行，且记录未因数据缺口作废）；
  2. 有效 event 的净 PnL 中位数 `<= 0`；
  3. 全部 event 净 PnL 合计 `<= 0`。
- 若记录期内某市场没有任何成交、但每天都有奖励 `结算` 行，仍算一个有效 event；若奖励和返佣都因低于 $1 而为 0，仍如实记 0，不剔除。
- 不因为结果不好而改规则；失败也交 `RESULT.md`。

## 记录和推送

- 明细文件：`bots/quant/forward/quant-034/ledger.csv`，表头固定为：
  `time_utc,event_id,market,action,side,price,price_source,size,fee,pnl,note`
- 运行方式（仓库根目录，操作员每小时一次）：
  ```bash
  python3 bots/quant/forward/quant-034/record.py
  ```
- 只读公开接口，不下单、不连钱包、不用密钥；网络错误打印到 stderr 并以 0 退出。2026-10-22T00:00:00Z 之前运行不写任何文件。
- 状态只写 `bots/quant/forward/quant-034/state.json`；`ledger.csv` 只追加。记错另起 `action=更正` 行，`note` 指向原行（`uid`），不改旧行。
- 幂等：每行 note 带确定性 `uid`；重复运行不会重复追加同一行。`state.json` 记录报价、库存、已处理成交、每日奖励样本和已结算日。
- 试运行（不写文件、不建 state）：
  ```bash
  FORWARD_DRY_RUN=1 python3 bots/quant/forward/quant-034/record.py
  ```
- 至少每天推送一次；`挂`/`成交` 行在对应 `撤`/`平`/`结算` 之前推送。

## 登记快照的 37 个市场（2026-10-21T05:16Z；record.py 开始时按同一规则重选，最多 40 个）

| # | condition_id | event_slug | 日率 USDC | max_spread¢ | feeRate | rebateRate | endDate |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `0xbe91fb5f94bce3e9e0f8e1ee13033c2e3a35bb9bededbbb43de5bf28d79478b0` | `ncaa-football-2026-d1-rushing-yards-leader-20260803210835729` | 88.00 | 4.5 | 0.05 | 0.15 | 2027-01-04 |
| 2 | `0x3acd686a68c85bd79724db76c5f681003dd6cae2e9a033b7a27136e672926267` | `1win-fdv-above-one-day-after-launch` | 80.00 | 4.5 | 0.07 | 0.20 | 2028-01-01 |
| 3 | `0x3da9e515e164ecf0c795a7ee039ccdf28ab304e009b3870fbd83ce90355c03e1` | `which-dota-2-teams-will-make-a-roster-change-before-2027-1792421285780` | 50.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 4 | `0x42d1fefc149165e314c36cdcb0ec3dc94abe2cc55c3914bffdd96cf764eb6eb8` | `will-collapse-return-to-competitive-dota-2-before-2027` | 50.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 5 | `0x4c5399503e0f3d98161d6877f861557993317860d45d36b55870f4ea2cb74b4e` | `will-dota-2-average-more-steam-players-in-november-than-in-october` | 50.00 | 4.5 | 0.05 | 0.25 | 2026-12-16 |
| 6 | `0x4dd20ba2fdd0aee411252a7f1c005673086e943550fd375a616fec8c897a5371` | `will-gpk-return-to-competitive-dota-2-before-2027` | 50.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 7 | `0x6a15853865d5fa9d289bdc52c68d03c7b9fa3fa116b7b96ed586845836434fe5` | `will-a-dota-2-match-fixing-ban-be-announced-before-2027` | 50.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 8 | `0xc6e411dc124805a9bbe452a0fd1391b6498373747e7587049990d1df4113a9c2` | `will-a-1m-dota-2-team-disband-before-2027` | 50.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 9 | `0xd199af947c28d67b6869dd641b9301a2819d40a2647da88e9b6d7c90b10b9dfe` | `will-a-250k-dota-2-player-retire-before-2027` | 50.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 10 | `0x26f021f7eed8dda3b99bcb4163cf1b28d1cdd921da4c8922799fb91541da8147` | `valorant-offseason-chronicle-next-team-1788364450495` | 40.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 11 | `0x5480ecf5de966b99184a0e442103d4c7ab145855229ac073bb17861c3910af5d` | `will-marvell-q3-data-center-revenue-be-above` | 40.00 | 6.5 | 0.04 | 0.25 | 2026-12-01 |
| 12 | `0xd5137800eeb19473b1cc6cfe2b5377e807519fe71b4cdd387f0c68e148b99763` | `which-league-will-cristiano-ronaldo-join-next` | 35.00 | 4.5 | 0.05 | 0.15 | 2027-09-01 |
| 13 | `0xdb0eaf3f75d4f9b3f0116504e131adc0432a427bc1f74133dc0911e976330056` | `ufc-who-will-rafael-fiziev-fight-next-20260629205941824` | 33.00 | 4.5 | 0.03 | 0.25 | 2027-06-27 |
| 14 | `0x8c76cbb830ac6280d44ed51400ec51baf9f166606fe4c75ebb20239b26ce2407` | `ppa-2026-27-end-of-year-rankings-player-to-be-number-1-womens` | 32.00 | 4.5 | 0.05 | 0.15 | 2027-05-16 |
| 15 | `0xea0fd6ed032120efdbad9363e022c4b334b7a01e136c981e74b96ccf26f59e7e` | `pro-football-2026-27-receiving-yards-leader-20260715211950725` | 30.00 | 4.5 | 0.05 | 0.15 | 2027-01-27 |
| 16 | `0x9200ca2fe44fe5c867bbcee41e9437fd54acfc1706d5ceff52ae11921439c84c` | `ufc-who-will-jean-silva-fight-next` | 26.00 | 4.5 | 0.05 | 0.15 | 2027-09-15 |
| 17 | `0xb7e7ce498a7a75240e54b210fbc656a8b6cb0b46029e33f626a566b6215a76c3` | `ncaa-football-conference-of-heisman-winner-20260803170245586` | 26.00 | 4.5 | 0.05 | 0.15 | 2026-12-27 |
| 18 | `0x5d55f32e24d98f7fc4604ccfa9f7fc13640fbce99df4f76bf60ed449faf8975d` | `ballon-d-or-2026-5th-place-20261019193417541` | 25.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 19 | `0x7fafeb4e1a61a52f4705bbb9b6b739d18c46d03bf8cc285ac331997f6be4f334` | `valorant-offseason-oxy-next-team-1788364450495` | 25.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 20 | `0x1598d9ae1a10d2c1520d9dddc437b6bc32c73d580356f2760a6eb63922b75ec9` | `ncaa-football-2026-pac-12-conference-winner-20260731204848103` | 24.00 | 4.5 | 0.05 | 0.15 | 2026-12-19 |
| 21 | `0x1c7539a2a44e84e9b5971ba9937f57542e114dcec2500cb3fb862327bbf9e2fd` | `ufc-brendan-allen-next-fight` | 24.00 | 4.5 | 0.05 | 0.15 | 2027-10-13 |
| 22 | `0xa73af3849cb731ec3e16c656be32df9189629d7e41fef33dbef8ccc8e3478ada` | `fantasy-football-2026-27-rb-points-leader-20260807010548393` | 24.00 | 4.5 | 0.05 | 0.15 | 2027-01-27 |
| 23 | `0x34346c899f1b4b117e6c400f80b36a9f30f355dc1274e8075cb0fb09c7a14603` | `afcon-2027-qualifying-group-l-winner` | 23.00 | 4.5 | 0.05 | 0.15 | 2027-03-31 |
| 24 | `0x8652314642ea8e1b8b1f5fded33bd3deb328fff284b5f8d015ef62e0c39cae3c` | `valorant-offseason-primmie-next-team-1788364450495` | 23.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 25 | `0xaef9dfe556082b10a374bee22470df845528e752cf74a25585131b434d2ad61c` | `afc-asian-cup-2027-group-a-winner` | 23.00 | 4.5 | 0.05 | 0.15 | 2027-02-06 |
| 26 | `0x429ad9c277f9613720d27edbb9d7e68ef6cac4fb69d94fa91651cbdf8f786e6a` | `mlb-al-platinum-glove-winner` | 22.00 | 4.5 | 0.03 | 0.25 | 2027-01-01 |
| 27 | `0x9668e92f98ea6db7b505c54acfd5cbff6ce7e104cf51a92a459b7aa32228494c` | `valorant-offseason-boaster-next-team-1788882258365` | 22.00 | 4.5 | 0.05 | 0.15 | 2027-01-01 |
| 28 | `0xa9f05e47899ca6878d798795a84a7ce9b483d900d11fbf732fe8d969bb41b427` | `how-many-triple-crowns-will-ben-johns-win-in-the-2026-27-ppa-tour-season` | 22.00 | 4.5 | 0.05 | 0.15 | 2027-05-16 |
| 29 | `0xb4625976d6318a7373c9bee1d33ef48ce5ee10ca05e4d5d20a2aa8304daadcb9` | `mls-eastern-conference-champion-2026` | 22.00 | 4.5 | 0.05 | 0.15 | 2026-12-12 |
| 30 | `0xd3162486c8aeccf42a6d4aa3ec8d21f865a0eb8cada144ddd4e284f05a093daa` | `liga-mx-2026-27-largest-goal-differential-20260722172229841` | 22.00 | 4.5 | 0.05 | 0.15 | 2027-06-28 |
| 31 | `0xec79335bee42601d2bb8642eedf98905bef8cf028ddda91e73d8b78fb4f880aa` | `afcon-2027-qualifying-group-h-winner` | 22.00 | 4.5 | 0.05 | 0.15 | 2027-03-31 |
| 32 | `0x65c7002c05e9ad53c34c17649c36e59d112e770c20ceeea598ccb3b92161b6d6` | `premier-league-most-assists-2026-27` | 21.00 | 4.5 | 0.05 | 0.15 | 2027-06-15 |
| 33 | `0xc439ddda67d1d2c5275e54b01691bc947051ac9a9bfe48364fe2a4d98c593b56` | `how-many-tesla-deliveries-in-q4-2026` | 21.00 | 6.5 | 0.04 | 0.25 | 2027-03-01 |
| 34 | `0x10502c298452a3301280fdacb2e3a17d88f79b773bae5ef190c67c04be662d89` | `will-manchester-city-be-relegated-from-the-premier-league-in-2026-27` | 20.00 | 6.5 | 0.05 | 0.15 | 2027-07-01 |
| 35 | `0x28c8f300e3c6d4d4434f5e7e3b313b9bf41ba6ae656163d1fdabb27f7eb00800` | `copa-sudamericana-2026-winner` | 20.00 | 4.5 | 0.05 | 0.15 | 2026-11-22 |
| 36 | `0x273bfff7e975966338cf1d2c8c9485175e5c019a1d865be8a7f6ccf5bfae26bf` | `manchester-city-punishment-announced-by` | 20.00 | 6.5 | 0.05 | 0.15 | 2026-11-21 |
| 37 | `0x7a9b9fc81b9945c6adcf6f3d731627823aa96281096533e7b40ed6d86844637b` | `who-will-attend-the-2026-ballon-dor-ceremony-20261016121846566` | 20.00 | 6.5 | 0.05 | 0.15 | 2026-12-01 |

数据来源：`https://clob.polymarket.com/rewards/markets/current`、`https://gamma-api.polymarket.com/markets?condition_ids=...`，访问 2026-10-21T05:16Z。上表是登记快照；`record.py` 开始时按同一规则重选最多 40 个并写入 `state.json` 的 `selected`。日率和费用字段会变，记录期每天重读；以记录期实际配置为准。
