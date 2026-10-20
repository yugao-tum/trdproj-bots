---
id: quant-024
name_zh: NFL 单场胜负：Elo 对赛前价
name_en: NFL moneyline — public Elo rating vs Polymarket pregame price (CFB as second league, forward only)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: sports
kind: new
improves: -
category: S
return_type: direction
instruments: NFL 单场胜负 moneyline（模板 `nfl-<away>-<home>-YYYY-MM-DD`）；CFB 同模板 `cfb-<team>-vs-<team>` 仅作前向第二联赛，未进本次历史样本
venues: Polymarket
data: nflverse `games.csv`（免费免密钥，1999–2026，含比分与收盘 moneyline）；Polymarket Gamma（事件/规则/费用字段）与 data-api trades（免费免密钥，可按 `end` 取赛前最后一笔）；ESPN scoreboard（免费免密钥）；历史盘口本身无公开 L2，用成交价 +1¢ 近似 ask；CFB 只有 2024 年市场且 feeSchedule 为空，未做历史回测
test_2w: 历史 654 场（2024-09-05–2026-10-20）按比赛计 1 个独立结果；赛前 60 分钟按 2¢ Elo 边缘进场，扣该市场 taker 费与 1¢ 价差；失败标准 = 净收益/份 ≤0 或 95% bootstrap CI 含 0（本次已失败：全样本 +1.76¢/份但 CI 含 0；2026 收费子样本 30 笔 −3.65¢/份）
status: 草稿
confidence: 高
---

## 一句话

在 Polymarket 的 NFL 单场胜负市场，赛前 60 分钟用 nflverse 公开比分自算的 Elo 得到 `p_model`；当 `p_model − 可成交价 − 吃单费 ≥ 0.02` 时买入该侧并持有到结算。**本条的预注册规则在历史 654 场上没有通过：全样本每份 +1.76¢ 但 95% 区间含 0，2026 年开始收费后的 44 场里 30 笔为 −3.65¢/份、ROI −3.4%。结论是不要部署。**

## 钱从哪里来

假设的付款方是把主队、明星队或热门队价格挂得偏离公开评级的对手盘；NFL 盘口在赛前一周到开赛之间由大量娱乐型资金定价，而公开 Elo 只需要历史比分就能算，信息成本低，所以偏差可能不会被立刻抹平。**这条只是待检验的机制假设，不是本条已经证实的收益来源。** 本次检验的结果是：Elo 的概率校准比 Polymarket 自己的价格差（Brier 0.21868 对 0.20932），扣费后也没有稳定正收益；因此本条不能写成“谁在持续付钱给你”，只能写成“理论上的对手方 + 已证伪的检验”。

## 规则

### 市场模板与示例（Gamma 快照，2026-10-20）

- NFL 模板：每个比赛一个 event，slug 为 `nfl-<away3>-<home3>-YYYY-MM-DD`；event 下第一个市场通常就是全场胜负，slug 与 event 相同，outcomes 为两队名。
- 示例 1（已结算，收费时代）：[`nfl-hou-jax-2026-10-18`](https://polymarket.com/event/nfl-hou-jax-2026-10-18)，event 309 个市场（2026-10-20 本轮快照），胜负市场 `conditionId=0x073b358ca8a2fdcbee75fbe0cc3a93dea55a12ac1ff81cf15fd51257008aa9c8`，`outcomes=["Texans","Jaguars"]`、结算 `outcomePrices=["1","0"]`、`feeSchedule={"exponent":1,"rate":0.03,"takerOnly":true,"rebateRate":0.15}`、`resolutionSource="https://www.nfl.com/scores"`。
- 示例 2（已结算，免收费时代）：[`nfl-nyg-dal-2024-09-26`](https://polymarket.com/event/nfl-nyg-dal-2024-09-26)，`outcomes=["Giants","Cowboys"]`、`outcomePrices=["0","1"]`、`feesEnabled=false`、`feeSchedule=null`、`resolutionSource` 为空字符串。
- 示例 3（已结算，免收费时代）：[`nfl-buf-ne-2025-01-05`](https://polymarket.com/event/nfl-buf-ne-2025-01-05)，`outcomes=["Bills","Patriots"]`、`resolutionSource="https://www.nfl.com/"`、`feesEnabled=false`。
- CFB 模板：`cfb-<team>-vs-<team>`；示例 [`cfb-florida-st-vs-georgia-tech`](https://polymarket.com/event/cfb-florida-st-vs-georgia-tech)，2024-08-24，`outcomes=["Florida St.","Georgia Tech"]`、`feeSchedule=null`、`feesEnabled=false`、`resolutionSource` 为空字符串。

### 结算规则原文（逐字引，必须逐市场读）

**2026 收费版 NFL 胜负市场**（`nfl-hou-jax-2026-10-18`，description 原文）：

> In the upcoming NFL football game between Texans and Jaguars, scheduled for October 18 at 9:30AM ET:
> This market will resolve to "Texans" if Texans win the game.
> This market will resolve to "Jaguars" if Jaguars win the game.
> Overtime is included if played.
> If the game ends in a tie, this market will resolve 50-50.
> If the game is postponed, this market will remain open until the game has been completed.
> If the game is canceled entirely, with no make-up game, this market will resolve 50-50.

结算源：`https://www.nfl.com/scores`（市场字段 `resolutionSource`，2026-10-20 访问 HTTP 200）。

**2024 免收费版 NFL 胜负市场**（`nfl-nyg-dal-2024-09-26`，description 原文）：

> In the upcoming NFL game, scheduled for September 26 at 8:15 PM ET:
> If the New York Giants win, the market will resolve to “Giants”.
> If the Dallas Cowboys win, the market will resolve to “Cowboys”.
> If the game is not completed by October 3, 2024 (11:59 PM ET) or it ends in a tie, the market will resolve 50-50.

注意：两个赛季的规则**不是同一模板**。2024 版只写“到某日 23:59 ET 未完成或打平 → 50-50”，没有 2026 版的“延期保持开放、彻底取消 50-50、加时计入”三句；2024 版 `resolutionSource` 为空字符串。回测里所有场次都正常完赛，只有 2 场平局按 50-50 计，所以规则差异不影响主要结论，但实盘必须先读该市场自己的 description。

**CFB 2024 版**（`cfb-florida-st-vs-georgia-tech`，description 原文）：

> In the upcoming NCAA Football game, scheduled for August 24 at 12:00 PM ET:
> If the Florida State Seminoles win, the market will resolve to “Florida St.”
> If the Georgia Tech Yellow Jackets win, the market will resolve to “Georgia Tech”.
> If the game is not completed by August 31, 2024 (11:59 PM ET) or it ends in a tie, the market will resolve 50-50.

CFB 2024 市场的 `resolutionSource` 为空字符串，`feeSchedule=null`。2026-10-20 在 `tag_slug=cfb` 下分页到 225 个含 `-vs-` 的已结算单场事件，`startDate` 全在 2024（含 2025-01 的碗赛）；本轮在 `tag_slug=cfb&closed=false` 和 `public-search?q=cfb` 里没有取到在挂的 2026 CFB 单场（返回的是期货/奖项类）。因此 CFB 只作为前向第二联赛，不进入本次历史回测；当前 CFB 单场费率也未取到。

### 模型（预注册，不按结果调参）

- 数据：nflverse `games.csv`，只取 `season>=2010` 且 `away_score/home_score` 非空的行；按 `gameday, game_id` 排序。
- 初始 Elo 1500；赛季切换时 `Elo ← 1500 + (Elo−1500)×2/3`；主场优势 `HFA=55`；`K=20`；分差乘数 `mov=1` 时 1，`mov>1` 时 `1+ln(mov)`；平局按 0.5 计。
- 赛前主队胜率 `p_home = 1/(1+10^(−((Elo_home+55−Elo_away)/400)))`，客队 `1−p_home`。**这是唯一的主模型，没有用 Polymarket 价格拟合任何参数。**
- 对照（只作诊断，不参与主规则）：把 nflverse `home_moneyline/away_moneyline` 转成隐含概率后按比例去水，得到 `p_vegas`。

### 进场、出场、仓位

- 时点：开赛前 60 分钟（`T−60m`）。用 data-api `trades?market=<conditionId>&limit=60&end=<T−60m 的 Unix 秒>` 取该时点之前最近 60 笔成交，取每个 outcome 的最后一口成交价。
- 可成交价：`ask = min(0.99, last_trade_price + 0.01)`。历史 L2 盘口没有公开来源，1¢ 是保守的价差假设；不是真实报价。
- 费用：按该市场 `feeSchedule.rate`，`fee = rate × ask × (1−ask)`（GUIDE §8 的吃单费公式，按每份计）。2024–2025 市场 `feesEnabled=false`，按 0 费；2026 收费市场按其字段。
- 信号：`edge = p_model − ask − fee`；`edge ≥ 0.02` 才买该侧，否则不交易。两边都满足时只买 edge 更大的一边；单场最多一注。
- 仓位：每注 50 USDT；同一天最多 5 场；未结算总敞口 ≤ 1,250 USDT；Polymarket 单场所总资金 ≤ 2,500 USDT；不加杠杆、不借钱。
- 出场：只有结算；不赛中平仓、不对冲。结算按上面引用的该市场规则，加时计入，平局 50-50，延期等完成，彻底取消 50-50。
- 过滤：开赛前 60 分钟没有两侧成交、或 `ask ≥ 0.95`、或球队无法与 nflverse 对上、或找不到该场的 nflverse 比分/收盘线 → 跳过并计数。

## 证据

### 1. 样本是怎么来的（本轮脚本，全部可复现）

- Gamma `tag_slug=nfl&closed=true` 分页到 1,854 个 event，其中 slug 严格匹配 `nfl-[a-z]{2,3}-[a-z]{2,3}-YYYY-MM-DD` 的 **805 场**；每场取 slug 与 event 相同的全场胜负市场。
- data-api 按 `market=<conditionId>&limit=60&end=T−60m` 取赛前成交：**801/805** 场两侧都有赛前成交。
- 与 nflverse `games.csv` 按“球队对 + 日期 ±1 天”匹配：**654 场**进入回测（2024: 252，2025: 284，2026: 118；日期 2024-09-05–2026-10-20）；147 场季前赛因 nflverse 不收季前赛、日期差超过 1 天而剔除。2 场平局按 0.5 计。
- 费率字段：2024–2025 的 536 场 `feeSchedule` 全为空（抽查的 2024/2025 市场 `feesEnabled=false`），按 0 费计；2026 的 118 场里 44 场 `feeSchedule.rate>0`（27 场 0.03、17 场 0.05），其余为 0 或字段缺失（按 0 计）。
- 本条的收益数字**全部来自本轮脚本**，没有引用任何第三方“自报收益”；不存在“来源自报，未核实”的收益结论。

### 2. 主结果：Elo 概率比 PM 差，扣费后不显著

| 指标 | Elo | Polymarket T−60 价 | Vegas 收盘去水 |
|---|---:|---:|---:|
| Brier（654 场，越低越好） | 0.21868 | 0.20932 | 0.20909 |
| 与 PM 的平均绝对偏差 | 8.19¢ | — | 1.27¢ |

- 主队平均：Elo/PM/Vegas 分别为 0.5719/0.5566/0.5487，实际主队胜率 0.5398。Elo 平均高估主队约 3.2¢，PM 的平均主队价高于 Vegas 约 0.8¢；但 PM 与 Vegas 的个体偏差只有 1.27¢ 的平均绝对值。
- 预注册规则（`edge ≥ 2¢`，按实际费率）：**462 笔**，胜率 **52.81%**，每份平均净收益 **+1.76¢**，平均 ROI **+2.23%**，累计 **+8.13**（每笔 1 份的利润之和）；bootstrap 95% 区间 **−2.31¢ 到 +5.85¢**，含 0。分年每份均值：2024 +2.6¢（190 笔）、2025 +0.9¢（188 笔）、2026 +1.8¢（84 笔）。
- 把 2024–2025 也一律按 3% 收费做压力测试：**440 笔**，每份 **+0.52¢**，平均 ROI **−1.02%**，区间 −3.68¢ 到 +4.77¢。结论对费率假设敏感。
- **收费时代子样本（最关键）**：2026-09-10–2026-10-20 的 44 场收费市场（rate 0.03/0.05）里，规则触发 **30 笔**，胜率 **48.33%**，每份 **−3.65¢**，平均 ROI **−3.40%**，累计 **−1.09**。也就是说，全样本的正号主要来自 2024–2025 的免手续费市场；一旦按当前费率交易，规则是亏的。
- 阈值稳健性（不改变结论）：把阈值从 2¢ 提到 5¢/8¢，收费子样本只剩 22/17 笔，均值转为 +4.57¢/+5.78¢；再提到 10¢/12¢/15¢ 又转为 −0.9¢/−15.1¢/−18.1¢。样本太小且不单调，不能把 5–8¢ 的正号当作 edge。

### 3. 对照诊断：收盘线比 Elo 更接近 PM，但同样不显著

- 用 `p_vegas` 代替 Elo，`edge ≥ 0`：**188 笔**，每份 **+3.19¢**，平均 ROI **+4.26%**，区间 −3.20¢ 到 +9.64¢；分年 2024 −1.9¢、2025 +6.6¢、2026 +8.8¢。
- `edge ≥ 0.5¢`：**111 笔**，每份 **+2.19¢**，平均 ROI **+7.98%**，区间 −6.59¢ 到 +10.89¢；2024 仍为 −1.3¢。
- 收费子样本里收盘线只剩 2 笔（threshold 0），无法检验；因此这条只能说明“PM 与收盘线的平均偏差约 1.3¢”，不能说明收费后还能赚钱。
- 这个对照与 `muse-own-polymarket-pinnacle-line-shopping` 的机制族相近（外部 sharp 线 vs PM），但那条用实时 Pinnacle 赔率和 4.5pp 阈值、赚 30–90 秒滞后；本条主规则不用实时赔率，只用免费收盘线做诊断，且结论为负。若核对认为仍属同一机制，应按 `supplement` 处理，`improves: muse-own-polymarket-pinnacle-line-shopping`。

### 4. 与最近已有条目的区别

- `quant-006`（网球 Elo 对 PM）：同为 Elo 族，但联赛、数据源（Tennis Abstract 周榜 vs nflverse 自算）、参数（网球用 400 尺度、无主场优势；本条 K=20、HFA=55、赛季回归 2/3）、样本和结论都不同。按仓库“换市场算变体”的严格口径，本条与 quant-006 有重叠；正文把它写清楚，若核对判为变体，应按 supplement 处理。
- `quant-011`（足球平局基准率）：市场结构不同（三向盘平局 vs 两向胜负），模型不同（历史频率桶 vs Elo）。
- `dot-013`（NBA 伤病消息重定价）：触发变量是伤病报告的新变化和时间戳，不是公开评分模型；本条不读伤病报告。
- `muse-own2-live-goal-lag`：赛中进球事件后的分钟级收敛；本条不碰赛中。
- 与 `known/` 的 `A-A3-poly-cross-market`、`V-V2-poly-longshot`：本条不是跨市场完整集，也不是单纯卖冷门；它检验的是“公开 Elo 能否给单场胜负定价”。

## 数据

- nflverse `games.csv`：`https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`，2026-10-20 访问，HTTP 200，**2,185,310 bytes，7,548 行，46 列**；含 `gameday/away_team/home_team/away_score/home_score/away_moneyline/home_moneyline/game_type`。免费、免密钥、无需注册。本轮回测用 2010 年起算 Elo，2024–2026 场次评分。
- Polymarket Gamma：`https://gamma-api.polymarket.com/events?tag_slug=nfl&closed=true&limit=100&offset=0`（`offset` 每次加 100 分页），分页到 1,854 个 event；`https://gamma-api.polymarket.com/events?slug=nfl-hou-jax-2026-10-18` 等单事件查询；免费、免密钥。规则原文、`outcomes`、`outcomePrices`、`feeSchedule`、`feesEnabled`、`resolutionSource` 都从这里取。
- Polymarket data-api 成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=60&end=<unix>`；免费、免密钥。`end` 参数实测可用（会返回该时间之前的最新成交）；`limit` 上限 1000，`offset` 可翻页。2024 年的市场也能取到完整成交（示例 `nfl-nyg-dal-2024-09-26` 共 1,328 笔）。
- CLOB 价格历史：`https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60`。**对 2024 年已结算市场返回 `{"history":[]}`**（实测 `nfl-nyg-dal-2024-09-26` 的 token 为空），所以历史价格只能用 data-api 成交重建；这与 batch3 短名单的发现一致。
- ESPN 记分板（备用/CFB 前向）：`https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261019`，HTTP 200，22,971 bytes；CFB `.../football/college-football/scoreboard?dates=20241130`，HTTP 200，426,992 bytes、25 场。免费、免密钥。
- 结算源：NFL 官方 `https://www.nfl.com/scores`（2026 市场字段），2026-10-20 访问 HTTP 200；2024/2025 市场字段为空或 `https://www.nfl.com/`，规则本身未逐字指定页面。
- 脚本与输出（全部在 `bots/quant/notes/scheduler/scratch/B21/`）：
  - `run_all.sh` — 从零重跑：下载 nflverse `games.csv` 与 Gamma 事件列表，再依次跑下面的脚本
  - `fetch_events.py` → `_cache/nfl_events_all.json`；`fetch_pregame.py` → 第一版 `pregame_quotes.json`
  - `fetch_pregame_nflkick.py` → 最终 `pregame_quotes.json`（805 场取数，801 场两侧都有 T−60 成交；开赛时间用 nflverse `gameday+gametime` 换算 UTC）
  - `match_elo2.py` → `matched2.pkl`（654 场匹配）；`build_kick_map.py` → `kick_map.json`
  - `summary4.py` → `summary4.stdout.txt`、`games_final.csv`、`elo_final_trades.csv`（主结果、收费子样本、3% 压力测试、阈值稳健性）
  - `explore.py` / `vegas_rule.py` / `combo.py` / `buckets.py` 是早一版 657 场样本的探索脚本（方向参考，不作为最终数字）
  - 原始下载运行期间放在 `_cache/`（`.gitignore` 已忽略）；运行后已清理大文件，可按上面的 URL 重取

## 两周内怎么检验

预注册办法（已在历史上执行，前向只需复核）：

1. 取两周内 NFL 全部有 Polymarket 全场胜负市场的比赛（赛季内约 16 场/周，两周约 32 场；休赛期 0 场），每场算 **1 个独立结果**；同一场的让分、总分、单节市场不重复计数。
2. 在开赛前 60 分钟记录两侧最后成交价、加 1¢ 作为 ask，按该市场 `feeSchedule.rate` 计费；Elo 用当日之前已完赛的比分重算，不能用赛后数据。
3. 主规则：`p_model − ask − fee ≥ 0.02` 买入该侧，持有到结算；每场最多一注。
4. 失败标准（预先写死）：触发样本 ≥30 笔时，每份净收益 ≤0，或净收益的 95% bootstrap 区间含 0，或收费子样本 ROI ≤0；任一条成立即判失败，不因分年、分价格桶“挑好的”重试。
5. 本次历史检验已触发失败：全样本 462 笔 +1.76¢/份但区间含 0；收费子样本 30 笔 −3.65¢/份、ROI −3.40%。前向两周只作为确认，不改变“暂不部署”的结论。
6. CFB 前向：同一模板、同一 Elo 规则，但 2026-10-20 本轮没有取到在挂的 CFB 单场，且 2024 年 CFB 市场 `feeSchedule=null`、无 `resolutionSource`；在拿到当前费率和至少 30 场前向结果前，CFB 只能记为“未检验”。

## 成本与容量

- 吃单费：`fee = 份数 × rate × p × (1−p)`。NFL 2026 收费市场实测 `rate=0.03`（27 场）和 `0.05`（17 场）；2024–2025 的样本市场 `feesEnabled=false`，费率按 0 计。
- 折成投入资本：`rate × (1−p)`。以 `rate=0.03`、`p=0.5` 计，每份费 0.75¢，占 50¢ 本金的 1.5%；加 1¢ 价差，往返约 1.75¢/份 = 3.4% 本金。`p=0.7` 时费 0.63¢ + 1¢ = 1.63¢，占 71¢ 的 2.3%；`p=0.3` 时同费但占 31¢ 的 5.3%。低价侧的成本占比最高，而亏损样本正集中在低价侧。
- 挂单：本条不挂单，全部按吃单计；`rebateRate=0.15`（2026 NFL）不计入收益，避免“挂单必然成交”的假设。
- 容量：单注 50 USDT，赛季内每周约 16 场、按 70.6% 触发率约 11 注/周；两周 32 场约 22–23 注。单注 50 USDT × 同时最多 25 注 = 1,250 USDT，低于 Polymarket 单场所 2,500 USDT 上限，5,000 USDT 总量放得下。容量不是瓶颈，证据才是。
- 资金占用：每注从 T−60m 持有到结算，NFL 通常 3–4 小时（周日比赛）到 3 天（周四/周一分散）；按平均持有 1 天计，单注资金每月可周转约 20 次。全样本 +2.23%/笔的粗算年化约 10–12%，但这是把不显著的均值线性放大，且收费子样本为负，**不能当作可实现收益**。

## 风险

- **最大风险：这是负结果。** 2026 收费子样本 30 笔 −3.65¢/份，说明按当前费率执行会稳定亏钱；全样本的正号主要来自 2024–2025 免手续费时代，不能外推。
- **模型风险**：Elo 只用比分，不含伤病、首发四分卫、天气、旅行、休息天数；Brier 比 PM 差 0.0094，说明它不是一个更好的概率估计。用更复杂的 EPA/FPI 模型可能改善校准，但没有免费历史评分可复现，本条不把“换模型”写成已解决。
- **成交价不是报价**：data-api 只有成交，没有历史 L2；`ask = 最后成交 + 1¢` 可能低估薄市场的真实价差，也可能高估（最后一口是卖单时）。这是本条最大的执行层不确定性。
- **费用字段不一致**：2024–2025 `feeSchedule` 缺失且 `feesEnabled=false`，2026 有 0、0.03、0.05 三种；把缺失按 0 计对 2024–2025 是事实，对 2026 的 28 场缺失是假设。按 3% 统一收费的压力测试把全样本打到 −1.02% ROI，结论不变。
- **规则随赛季变化**：2024 版没有“延期保持开放/彻底取消 50-50/加时计入”三句，2026 版有；CFB 2024 版只有“到某日未完成或打平 → 50-50”。实盘必须逐市场读 description，不能套用上一场。
- **平局/延期/取消**：NFL 平局 50-50；延期保持开放；彻底取消 50-50。样本只有 2 场平局，未覆盖延期/取消，尾部规则未经过实测。
- **球队映射与日期偏移**：Polymarket slug 的队名缩写与 nflverse 不完全一致（`was/wsh`、`la/lar`、`las/lv`），周四夜赛的 slug 日期可能比 nflverse `gameday` 晚一天；本条用“球队对 + 日期 ±1 天”匹配，654 场全部匹配，但仍可能有错配（尤其是同队同周同对手的重复赛程，NFL 常规赛不会发生）。
- **选择偏差**：804 场有赛前成交，654 场进入回测；147 场季前赛被剔除。季前赛的定价可能更无效，剔除它们会让结论偏保守；反过来，只保留有成交的市场会漏掉最薄的市场。
- **数据源风险**：nflverse 是社区维护的免费数据，`games.csv` 的收盘 moneyline 可能来自单一 book、时间戳不是严格收盘；ESPN/Gamma/data-api 都可能改字段或限流。所有数字都可重跑，但未来重跑可能因数据更新而略有差异。
- **平台/结算风险**：Polymarket 用 UMA 结算，规则争议、结算延迟、市场暂停都可能让“持有到结算”无法按预期退出；本条不处理这些尾部。
- **CFB 未检验**：2024 年 CFB 单场市场 `feeSchedule=null`、`resolutionSource` 为空字符串，本轮也没有取到在挂的 2026 CFB 单场；把 CFB 折进来只是模板层面的第二联赛，不构成证据。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清：满足。** 机制假设明确：公开 Elo 给出赛前胜率，PM 的娱乐型资金把主队/热门挂偏，偏差持续存在时买入被低估侧。本条同时明确：本次检验没有证实这个假设，2026 收费子样本为负。
2. **有免费数据能检验：满足。** nflverse `games.csv`、Gamma、data-api trades、ESPN 全部免费免密钥；654 场已结算比赛、每场 1 个独立结果，远超 30 个；起始日期 2024-09-05（2024 赛季）。CFB 部分不满足：只有 2024 年市场且费率字段为空，未做历史回测。
3. **小资金能做：满足。** 每注 50 USDT，最多 25 注同时持有 = 1,250 USDT，低于 Polymarket 单场所 2,500 USDT；总资金 5,000 USDT；不加杠杆、不借钱。但“能做”不等于“值得做”。
4. **不重复：不确定（已说明）。** 与 quant-006 同属 Elo 族，与 muse 的 Pinnacle 比价同属“外部公允价 vs PM”族；本条的关键变量是 NFL/CFB、nflverse 自算 Elo、赛前 60 分钟和 2¢ 阈值，结论为负。若核对按“换市场=变体”判重，应按 `supplement` 处理，`improves: quant-006` 或 `muse-own-polymarket-pinnacle-line-shopping`。
5. **扣成本后粗算够用：不满足。** 全样本每份 +1.76¢ 但 95% 区间含 0；统一 3% 收费后 ROI −1.02%；2026 收费子样本 30 笔 −3.65¢/份、ROI −3.40%。按 GUIDE §8 的吃单费和半个价差，扣完后没有稳定正收益。
6. **两周内能检验：满足。** 历史 654 场已按“每场 1 个独立结果”跑完；两周前向赛季内约 32 场，足以得到 ≥30 个独立结果；失败标准预先写死（净收益 ≤0 或 95% CI 含 0 或收费子样本 ROI ≤0），本次已触发失败。
7. **出处可查：满足。** 每个 URL 都在 2026-10-20 实际打开；脚本、原始 stdout、`games_final.csv` 和逐笔交易 CSV 都在 `bots/quant/notes/scheduler/scratch/B21/`；规则原文逐字引用；没有来源自报的收益数字。

## 出处

- `https://gamma-api.polymarket.com/events?tag_slug=nfl&closed=true&limit=100&offset=0` — 访问 2026-10-20 — 已读（分页到 1,854 个 event，筛出 805 场）
- `https://gamma-api.polymarket.com/events?slug=nfl-hou-jax-2026-10-18` — 访问 2026-10-20 — 已读（规则、outcomes、feeSchedule、resolutionSource）
- `https://polymarket.com/event/nfl-hou-jax-2026-10-18` — 访问 2026-10-20 — 已读
- `https://gamma-api.polymarket.com/events?slug=nfl-nyg-dal-2024-09-26` — 访问 2026-10-20 — 已读（2024 版规则、feesEnabled=false、resolutionSource 为空）
- `https://polymarket.com/event/nfl-nyg-dal-2024-09-26` — 访问 2026-10-20 — 已读
- `https://gamma-api.polymarket.com/events?slug=nfl-buf-ne-2025-01-05` — 访问 2026-10-20 — 已读（2025 版规则、resolutionSource=nfl.com）
- `https://gamma-api.polymarket.com/events?slug=cfb-florida-st-vs-georgia-tech` — 访问 2026-10-20 — 已读（CFB 规则、feeSchedule=null、无 resolutionSource）
- `https://polymarket.com/event/cfb-florida-st-vs-georgia-tech` — 访问 2026-10-20 — 已读
- `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv` — 访问 2026-10-20 — 已读（HTTP 200，2,185,310 bytes，7,548 行，46 列）
- `https://data-api.polymarket.com/trades?market=0x652913133a6f632326d2e7c5e60527a9a669bc71f44a1eeec3c31b6db7d5cda7&limit=5&end=1727380800` — 访问 2026-10-20 — 已读（2024 市场赛前成交可用；`end` 参数生效）
- `https://clob.polymarket.com/prices-history?market=54283007212914572893413484651421353989343981154437785159441670116509122149268&interval=max&fidelity=60` — 访问 2026-10-20 — 已读（返回 `{"history":[]}`，老市场无历史价格）
- `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261019` — 访问 2026-10-20 — 已读（HTTP 200，22,971 bytes）
- `https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates=20241130` — 访问 2026-10-20 — 已读（HTTP 200，426,992 bytes，25 场）
- `https://www.nfl.com/scores` — 访问 2026-10-20 — 已读（HTTP 200；作为 2026 市场字段指定的结算源）
- `bots/quant/notes/scheduler/scratch/B21/summary4.stdout.txt` — 本轮生成 — 已读（主结果、收费子样本、3% 压力测试、阈值稳健性、Brier）
- `bots/quant/notes/batch3-shortlist.md` — 访问 2026-10-20 — 已读（NFL 候选来源；本条把它从预研变成可复现检验）
