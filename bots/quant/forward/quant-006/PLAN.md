# 两周前向登记：quant-006

- 自己的条目编号：quant-006（`bots/quant/entries/quant-006-tennis-elo-pm-pricing.md`）
- 原条目或 known/ 机制：quant-006；公开 Elo 给 Polymarket 网球单打胜者市场定价
- 登记序号：1
- 同机制全部登记：`bots/quant/forward/quant-006/`（本目录；没有其他 quant-006 前向登记）
- 开始时间（UTC）：2026-10-22T00:00:00Z
- 结束时间（UTC）：2026-11-05T00:00:00Z（14 天）

## 市场范围和选择规则

- 数据源：Polymarket Gamma 公开接口（免费、免密钥）
  - `https://gamma-api.polymarket.com/events?tag_slug=tennis&closed=false&start_time_min=2026-10-22T00:00:00Z&start_time_max=2026-11-05T00:00:00Z&limit=100&offset=<0,100,...>`
  - 每个事件再读 `markets[]`、`startTime`、`slug`、`title`、`closed`、`outcomePrices`、`clobTokenIds`、`feeSchedule`。
- 市场模板：Polymarket 网球单打“比赛胜者”二元市场，event slug 形如 `atp-<球员1>-<球员2>-YYYY-MM-DD`、`wta-...`、`itf-...`；每个比赛 event 下另有让盘、总分、单盘胜者等衍生市场，本条只做 slug 与 event slug 完全相同的“胜者”主市场。
- 选入条件（全部满足）：
  1. event 带 `tag_slug=tennis`，`closed=false`，`startTime` 在 [2026-10-22T00:00:00Z, 2026-11-05T00:00:00Z)；
  2. event slug 以 `atp-`、`wta-` 或 `itf-` 开头；
  3. event title 含 ` vs `，且 slug/title 不含 `doubles`、title 不含 `/`（排除双打）；
  4. 存在一个 market，其 slug 与 event slug 完全相同，且 `outcomes` 恰为两名球员、`clobTokenIds` 恰为两个 token；
  5. 两名球员都能在 Tennis Abstract 当前 ATP/WTA Elo 榜唯一匹配（见下）；匹配不到的比赛跳过，不猜。
- 排除条件：双打、资格赛/团体赛等非单打模板；没有胜者主市场；没有 `startTime`；比赛已开始；Elo 榜匹配不唯一。
- Elo 来源：`https://tennisabstract.com/reports/atp_elo_ratings.html` 与 `https://tennisabstract.com/reports/wta_elo_ratings.html`（免费、免密钥，页面标注 `Last update: 2026-10-19`）。取 `Player` 列与总 `Elo` 列。姓名先做 Unicode 去重音、转小写、去标点；先精确匹配全名，再尝试“姓 + 首字母”，只有唯一候选才采用。`atp-` 只用 ATP 榜，`wta-` 只用 WTA 榜，`itf-` 两榜都试且必须唯一。
- 抓取方式：record.py 每小时只抓 `startTime` 在 `[now-2h, now+48h]` 的事件（分页取全）；更晚的比赛在进入 48 小时窗口后再抓，规则不变。这样既不漏掉 6 小时决策点，也避免每次拉整个 14 天。

## 进出场、仓位和风控

- 决策时刻：每场比赛 `T = event.startTime`（UTC）前 **6 小时**，即 `D = T - 6h`。只处理 `D <= now < T` 且尚未记录过的 event；`T <= now` 的比赛视为错过，跳过并写入 state 的 skipped，不补记。
- 进场价：record.py 在 `D` 之后第一次运行时，对胜者主市场的两个 outcome token 各请求一次
  `https://clob.polymarket.com/book?token_id=<token>`
  取该响应的 `timestamp`（毫秒）作为 `price_source`；`best_ask = min(asks[].price)`，`best_bid = max(bids[].price)`。必须两个 token 的盘口都非空，且 `0.01 < best_ask < 0.99`；否则本次不交易，下一小时重试（不写 seen）。
- 价差闸门：`best_ask - best_bid <= 0.04`。超过 4 美分的盘口不交易（Elo 的 2 美分阈值不足以覆盖更宽的半价差）。
- 模型：
  - `p_A = 1 / (1 + 10^((Elo_B - Elo_A)/400))`，`p_B = 1 - p_A`；
  - 只用总 Elo，不做场地分项、不做参数搜索；
  - 买入 A 的 edge：`edge_A = p_A - ask_A - fee_A`；买入 B 的 edge：`edge_B = p_B - ask_B - fee_B`；
  - `fee_i = rate × ask_i × (1 - ask_i)`，`rate` 取该市场 `feeSchedule.rate`（网球实测 0.05），字段缺失按 0.05。
- 进场条件：`max(edge_A, edge_B) > 0.02`，买 edge 较大的一侧；若两侧都 >0.02，只买较大的一侧（一场最多一注）。`ask` 已经是“中间价 + 半个价差”的可成交价，不再重复加半个价差；0.02 是预留的滑点/模型误差缓冲。
- 仓位：`size = min(50, floor(50 / ask))` 份；`size < 5` 不交易（Gamma `orderMinSize` 实测为 5 份）。单场名义金额 ≤ 50 USDT；同时最多 20 场未结算，合计名义 ≤ 500 USDT；Polymarket 单场所 ≤ 2,500 USDT。总资金按 5,000 USDT 纸面账户计，不加杠杆。
- 出场：持有到结算，不中途卖、不加仓、不摊平；结算由 Gamma `outcomePrices` 决定。结算价 `1/0` 按赢/输，`0.5/0.5` 按每份 0.5 赔付。
- 风控：同一 event 只开一次；若 `startTime` 改期到窗口外，按 Gamma 最新 `startTime` 跳过；若比赛取消/改期，按 Gamma 结算结果记，不自行假设。

## 成本和成交判定

- 全部吃单，不挂单；maker 返佣不计入收益。
- 吃单费按 GUIDE 第 8 节：`fee = 份数 × 费率 × p × (1 - p)`，`p` 为实际成交价（best ask），费率取市场 `feeSchedule.rate`，缺失按 0.05。
- 半个买卖价差：用决策时刻之后第一份盘口快照的 `best_ask` 作为成交价，`best_ask = mid + (ask-bid)/2`，所以半个价差已经包含在 `ask` 里；不再另加一次。`price_source` 写该快照的毫秒时间戳（转 ISO），例如 `clob_book:2026-10-22T12:00:03Z`。
- 成交判定：纸面按 `best_ask` 全额成交 `size` 份；不模拟逐档深度。若 `size × ask` 超过盘口前 3 档卖单累计金额，仍按 `best_ask` 记（这是保守性较弱的假设，写在风险里）；实际 `size` 上限 50 份、名义 ≤50 USDT，通常小于前 3 档。
- 结算行 `fee=0`，开仓行的 `fee` 已记总费；结算行 `pnl = size × (payout - ask) - fee`。

## 独立结果和失败标准

- `event_id` 规则：用 Gamma `event.id`（字符串）。**一场比赛 = 1 个独立结果**；同一比赛的单盘胜者、让盘、总分等衍生市场全部不计，双打不计，同一球员同一天的多场比赛按不同 event 各算 1 个。
- 预计独立结果数：2026-10-21 在 Gamma 上实测 `tag_slug=tennis`、`closed=false`、`startTime` 落在窗口内的 event 共 **44** 个（同日早先一次为 39 个），其中去重后的单打（排除 doubles、title 含 `/`）**35** 个（ATP 25、WTA 9、ITF 1；早先一次为 30 个）；过去 14 天（2026-10-08..10-22）Gamma 返回 2,000 个已关闭网球 event（接口上限，非精确总数）。窗口内每天还会新增比赛，预计整个窗口单打 event ≥60 个，满足 ≥30 个独立结果。若到结束时已结算单打 event <30，记为“样本不足”，不冒充通过。
- 失败标准（事先固定，不事后改）：
  1. 已结算 event ≥30 个后，按 event 先平均的**每份净收益均值 ≤ 0**（扣吃单费；结算价按 Gamma）；
  2. 或模型对已结算 event 的 Brier 分数不优于同一时点市场中间价（`(best_bid+best_ask)/2`）。
  任一成立即判失败；若已结算 <30 个，只写“样本不足”，不写通过。

## 记录和推送

- 明细文件：`bots/quant/forward/quant-006/ledger.csv`，单个文件不超过 1 MB；超过就按周拆成 `ledger-2.csv` 等。
- 至少每天推送一次；开仓行在结算行之前推送；只追加，旧行不改，记错另起 `更正` 行并在 `note` 指向原行。
- `action`：`开`、`平`、`挂`、`撤`、`成交`、`结算`、`更正`；本条只用 `开`、`结算`、`更正`。
- `pnl`：该行实现的净损益，开仓行写 0，结算行写扣费后净额。
- 表头：

```csv
time_utc,event_id,market,action,side,price,price_source,size,fee,pnl,note
```

- 结束写 `RESULT.md`：独立结果数、扣成本收益、与登记时的差异、问题；更新条目证据和结果，在 `LOG.md` 申请核对，不占当轮 15 条限额。所有文件登记到 `INDEX.md`。
