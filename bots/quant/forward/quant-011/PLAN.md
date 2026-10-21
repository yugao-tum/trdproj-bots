# 两周前向登记：quant-011

- 自己的条目编号：quant-011（`bots/quant/entries/quant-011-soccer-draw-pricing.md`）
- 原条目或 known/ 机制：quant-011；足球三向盘的平局市场按历史平局基准率定价
- 登记序号：1
- 同机制全部登记：`bots/quant/forward/quant-011/`（本目录；没有其他 quant-011 前向登记）
- 开始时间（UTC）：2026-10-22T00:00:00Z
- 结束时间（UTC）：2026-11-05T00:00:00Z（14 天）

## 市场范围和选择规则

- 数据源：Polymarket Gamma 公开接口（免费、免密钥）
  - `https://gamma-api.polymarket.com/events?tag_slug=soccer&closed=false&start_time_min=2026-10-22T00:00:00Z&start_time_max=2026-11-05T00:00:00Z&limit=100&offset=<0,100,...>`
  - 每个 event 读 `markets[]`、`startTime`、`endDate`、`slug`、`title`、`closed`、`outcomePrices`、`clobTokenIds`、`feeSchedule`。
- 市场模板：Polymarket 足球三向事件里的“平局”二元市场，问题原文含 `end in a draw`（例：`Will Liverpool FC vs. Arsenal FC end in a draw?`）。同一 event 下另有主胜、客胜、比分、半场等市场；本条只做“平局 Yes/No”主市场。
- 选入条件（全部满足）：
  1. event 带 `tag_slug=soccer`、`closed=false`，`startTime` 在 [2026-10-22T00:00:00Z, 2026-11-05T00:00:00Z)；
  2. event 至少有一个 market 的 question 含 `end in a draw`，且该 market 的 `outcomes` 恰为 `["Yes","No"]`、有两个 `clobTokenIds`；
  3. 同一 event 还能找到主胜、客胜两个“Will <队> win on <日期>?”市场，各有两个 Yes/No token（用于计算市场隐含平局概率，供 `note` 记录；缺失则跳过）；
  4. 平局 market 的 `feeSchedule.rate` 可读；缺失按 0.05。
- 排除条件：没有平局市场、不是三向比赛、`startTime` 缺失、比赛已开始、盘口缺失/空盘、价差 > 0.02。所有联赛都纳入，不按联赛预筛（登记时固定，避免事后挑联赛）。
- 抓取方式：record.py 每小时只抓 `startTime` 在 `[now-2h, now+48h]` 的事件（分页取全）；更晚的比赛在进入 48 小时窗口后再抓，规则不变。
- 2026-10-21 实测：`tag_slug=soccer`、`closed=false`、`startTime` 落在窗口内的 event 共 **2,100** 个（同日早先一次为 2,000 个；仍是分页上限附近，实际可能更多），其中含平局市场的三向 event **414** 个（早先一次为 400 个；前 500 个 event 中有 89 个）。414 个三向 event 覆盖英超、西甲、德甲、法甲、意甲、英冠、MLS、日本、墨西哥、哥伦比亚等联赛。

## 进出场、仓位和风控

- 决策时刻：每场比赛 `T = event.startTime`（UTC）前 **6 小时**，即 `D = T - 6h`。只处理 `D <= now < T` 且尚未记录过的 event；`T <= now` 视为错过，写入 state 的 skipped，不补记。
- 进场价：record.py 在 `D` 之后第一次运行时，对平局 Yes token 请求
  `https://clob.polymarket.com/book?token_id=<draw_yes_token>`
  取响应 `timestamp`（毫秒）作为 `price_source`；`best_ask = min(asks[].price)`，`best_bid = max(bids[].price)`。必须 `0.01 < best_ask < 0.99`，且 `best_ask - best_bid <= 0.02`；否则本次不交易，下一小时重试（不写 seen）。
- 基准率 `p_hat`：登记时固定为 **0.2546**，来自 football-data.co.uk 的 E0/I1/SP1/D1/F1 五个联赛 2022/23–2025/26 共 5,942 场有 `FTR` 的比赛，其中 1,513 场平局（`1513 / 5942 = 0.2546`）。这是本条“历史平局基准率”的前向操作化：为了避免联赛小样本和赛中改参数，整个 14 天只用这一个常数，不按比赛、赔率或盘口调整。条目原稿的 E0+I1 合并平局率为 0.2582（3,040 场），与前向常数同量级；差异写在风险里。
- 市场隐含平局概率（只用于 note 和事后校准，不参与进场）：`qD = draw_ask / (home_ask + draw_ask + away_ask)`，三个 ask 都取同一轮盘口快照；若 `qD` 不在 [0.05, 0.60] 或分母 ≤0，跳过（盘口异常）。
- 进场条件：
  - `fee = rate × draw_ask × (1 - draw_ask)`，`rate` 取平局市场 `feeSchedule.rate`，缺失按 0.05；
  - `edge = p_hat - draw_ask - fee - 0.005`；只有 `edge > 0.005` 才买平局 Yes；0.005 是预留滑点，半个价差已含在 `draw_ask` 里，不再重复加；
  - 买价就是 `draw_ask`（吃单），不挂单。
- 仓位：`size = min(50, floor(50 / draw_ask))` 份；`size < 5` 不交易（`orderMinSize` 实测为 5 份）。单场名义 ≤50 USDT；同时最多 20 场未结算，合计名义 ≤500 USDT；Polymarket 单场所 ≤2,500 USDT。总资金按 5,000 USDT 纸面账户计，不加杠杆。
- 出场：持有到结算，不中途卖、不加仓、不摊平。取消/改期的结算按 Gamma 规则（平局市场取消整场可能结算 Yes），record.py 只读 Gamma 结果，不自行假设。
- 风控：同一 event 只开一次；单场只买平局 Yes，不买主胜/客胜，不做三向对冲；若开赛前 `startTime` 改到窗口外，按最新 `startTime` 跳过。

## 成本和成交判定

- 全部吃单，不挂单；maker 返佣不计入收益。
- 吃单费按 GUIDE 第 8 节：`fee = 份数 × 费率 × p × (1 - p)`，`p = draw_ask`，费率取市场 `feeSchedule.rate`，缺失按 0.05（体育板块实测 0.05）。
- 半个买卖价差：成交价用决策时刻之后第一份盘口快照的 `best_ask`，`best_ask = mid + (ask-bid)/2`，半个价差已包含在 `draw_ask` 中；不再另加。`price_source` 写该快照的毫秒时间戳（转 ISO），例如 `clob_book:2026-10-22T12:00:03Z`。
- 成交判定：纸面按 `best_ask` 全额成交 `size` 份；不模拟逐档深度。若 `size × ask` 超过前 3 档卖单累计金额，仍按 `best_ask` 记（保守性较弱，写在风险里）；实际 `size` 上限 50 份、名义 ≤50 USDT。
- 结算行 `fee=0`，开仓行 `fee` 已记总费；结算行 `pnl = size × (payout - draw_ask) - fee`。

## 独立结果和失败标准

- `event_id` 规则：用 Gamma `event.id`（字符串）。**一场比赛 = 1 个独立结果**；同一 event 的平局、主胜、客胜、比分、半场等市场全部只算 1 个；同一比赛因平台重复挂盘产生的多个 event，按 `startTime + 主队 + 客队` 去重后只算 1 个（record.py 用 event.id 记账，RESULT.md 手工按该规则合并）。
- 预计独立结果数：2026-10-21 在 Gamma 上实测 `tag_slug=soccer`、`closed=false`、`startTime` 落在窗口内且含平局市场的三向 event 共 **414** 个（同日早先一次 400 个；前 500 个 event 中 89 个；分页到 2,100 后统计）。窗口 14 天，预计 ≥400 个独立比赛结果，远高于 30。实际成交数取决于盘口是否满足 `ask <= p_hat - fee - 0.005` 和价差 ≤0.02；按 2026-10-21 的 89 个样本，平局 ask 中位 0.26、33 个 ≤0.24；扣除缺失盘口和价差/费用后，预计整个窗口成交 30–80 个 event。
- 失败标准（事先固定，不事后改）：
  1. 已结算 event ≥30 个后，**已成交子集**按 event 先平均的每份净收益均值 ≤0（扣吃单费；结算价按 Gamma）；
  2. 或已成交子集的平局命中率 ≤ 平均入场价（即 `p_hat` 的 edge 不存在）；
  3. 若到结束时已成交 event <30，记“交易样本不足”，不用 400 个未成交 event 冒充 30 个收益结果。
  任一成立即判失败。

## 记录和推送

- 明细文件：`bots/quant/forward/quant-011/ledger.csv`，单个文件不超过 1 MB；超过就按周拆成 `ledger-2.csv` 等。
- 至少每天推送一次；开仓行在结算行之前推送；只追加，旧行不改，记错另起 `更正` 行并在 `note` 指向原行。
- `action`：`开`、`平`、`挂`、`撤`、`成交`、`结算`、`更正`；本条只用 `开`、`结算`、`更正`。
- `pnl`：该行实现的净损益，开仓行写 0，结算行写扣费后净额。
- 表头：

```csv
time_utc,event_id,market,action,side,price,price_source,size,fee,pnl,note
```

- 结束写 `RESULT.md`：独立结果数、扣成本收益、与登记时的差异、问题；更新条目证据和结果，在 `LOG.md` 申请核对，不占当轮 15 条限额。所有文件登记到 `INDEX.md`。
