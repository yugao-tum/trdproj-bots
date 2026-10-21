# P-quant-031 / quant-031 fixer changelog

- 条目：`bots/quant/entries/quant-031-aaa-gas-daily-bracket.md`
- 队列项：P-quant-031（entry quant-031）
- 修正日期：2026-10-21 UTC
- 保持不动：文件名、`id: quant-031`、`date: 2026-10-20`、`status: 草稿`
- 依据：`bots/quant/notes/scheduler/reviews/c20261020-170337-research.md`（B30 段，唯一直接点名 B30/quant-031 的 review/check 文件）；`bots/quant/notes/scheduler/audit/c20261021-030001-research.md` 只在“held、未深挖”清单里提到 B30，没有新问题；`checks/B22`、`B23` 分别对应 quant-025、quant-026，与本条无关。

## 1. Review 逐条修正

| # | Review 指出的问题 | 本次改法 | 证据 / 复跑 |
|---|---|---|---|
| 1 | `:145` “CLOB prices-history 只保留最近 2–3 周”是一刀切错误 | 删除全局保留期说法；改为“2025 两个事件的 CLOB history 为 0 点（5 档全查），2026-10 已结算事件有 135–172 个分钟点但只从创建日起；p 不是可成交卖价” | `verify_out.txt`：2025 两事件 10 个市场 `ph_points 0`；30 个已结算市场 135–172 点（10-16 约 170、10-18 约 135）；`docs.polymarket.com/api-reference/markets/get-prices-history` 只说明返回 `t/p`，不保证是卖价 |
| 2 | `:35/:124/:203` “0 个 ≤0.95 的可成交样本”把“没有成交”当成“没有卖单” | 全部改成“0 笔 ≤0.95 的实际 BUY 成交；决策时最优卖价未取到”；风险节标题改为“样本里没有 ≤0.95 的成交，是否有可成交卖价未知” | `backtest_trades_out.txt`：≤0.95 fills 0/5；data-api 无历史 L2，只能证明成交不能证明盘口 |
| 3 | 门 6 不满足、门 5 未被证明；只能是待选区，不能算收录 | 门 5/6 明确写“不满足”；新增“处置建议”，写明按七门标准应退回/放弃（drop），若整合者要留只作待选区 | 新增第 3 节回测：≤0.95 0/5；≤0.99 2/5、净 +0.7067 USDC；不限价 3/5、净 +0.4212 USDC；历史 5 + 前向 14 = 19 < 30 |
| 4 | `:194` 与 dot-004 的重复风险 | 保留 `kind: new`，但把区别写窄：dot-004 是一次性政治官宣；本条是每日固定模板、官方统计在收盘前翻页、关键变量是翻页时刻 vs 收盘。明确“若主审按宽口径判同一机制，应改 supplement” | `:194` 段落；门 4 仍写“不确定” |
| 5 | 10-20 已结算，旧文写“未结算观察”是时间漂移 | 全条改为 5 个已结算（10-16…10-20）+ 1 个未结算（10-21）；10-20 事件研究/回测均按已结算处理；`date` 不动 | Gamma 2026-10-21 实抓：5 closed / 1 open；10-20 winner `<$4.2800`；`closedTime 2026-10-20T16:01:44Z` |
| 6 | `:33` “0.3–75 分钟”本身有支撑 | 保留，但限定为“有后续成交的 4 个已结算事件”；10-16 无后续收盘前成交，单列 | `event_study_out.txt`：10-17 28.0、10-18 0.3、10-19 75.0、10-20 10.4 分钟 |
| 7 | `name_zh` 14 字、字段、`improves: -` 正常 | 未改这些字段 | front matter 检查：17 个必填字段齐全；`name_zh` 14 字 |

## 2. 复核时额外发现并修正

1. **样本从 4 个变成 5 个已结算**：10-20 已 `closed=true`，获胜档 `<$4.2800`。全条事件数、市场数、YES 成交笔数（6/10/21/13/11=61）、成交量、closedTime、门 2/5/6 全部改为 5 个。
2. **10-21 未结算事件的费率是 0**：`feeSchedule={"rate":0,"rebateRate":0,"takerOnly":true}`，不是 0.04。已结算 5 个事件 30 个市场仍是 0.04；回测按 0.04 保守计。
3. **CLOB `prices-history` 会产生假收益**：10-17 07:56:59 实际 YES 成交 0.98，08:00 序列 `p=0.55`；10-16 07:27 最后一笔 0.8171，11:10 序列 `p=0.735`。若把 `p` 当卖价，0.95 门槛会显示 4/5 笔、+331 USDC 的假收益；已弃用，只作“中间价陷阱”证据。
4. **CDX 计数更新**：2026-08-01–10-21 为 294 个 200 快照（旧文 292 是到 10-20），04:00–10:59 候选仍 43 个；本次实际解析 64 个快照、分布在 33 个日期，其中 16 个日期至少有一张显示当天值（旧文 47 个）。
5. **翻页时刻表述收紧**：旧文“最晚一次翻页发生在 10:01–10:22”无法由快照证明；改为“07:30 前没有任何快照显示当天值；所有日期首次看到当天值 07:30–11:03；5 个事件日集中在 09:56–11:03；这只是存档上界”。10-16 只能界定在 04:42–11:00 之间。
6. **public-search 计数不可复现**：旧文 `q=gas prices on` 返回 9 个、`q=aaa gas` `totalResults=21`；本次分别返回 5 个、5 个（后者全是 2022 一次性阈值）。已删除旧计数，改以 `series_id=12954` 的 6 个为准。
7. **2025 近似事件复核**：Feb-21 `$3.16` 最后 YES 成交 08:16:08 @0.9857；Feb-28 `$3.14 or less` 10:26:39 SELL 0.99；YES 成交 38/32 笔。均与旧文一致。

## 3. 新增的历史可成交回测（净费）

规则：对每个已结算事件，取事件日最早一张同时满足 `Price as of`=当天且 `Yesterday Avg.`=前一天 `Current Avg.` 的 Wayback 快照作为决策时点；之后、14:00 UTC 前，取对应档 YES 的第一笔实际 data-api BUY 成交；费用 `0.04×p×(1−p)`，另加 0.5 美分半价差；持有到结算；每事件最多 250 USDC，并按该笔实际份数封顶。

```text
limit<=0.95 fills 0 of 5
limit<=0.99 fills 2 of 5
  10-18 11:25:41 p=0.988457 size=75.5  net/sh=0.006087  net$=+0.4595
  10-19 10:20:54 p=0.988360 size=40.0  net/sh=0.006180  net$=+0.2472
  total_net=+0.7067 USDC, cost=114.74, ROI=0.62%
market (first print, any price) fills 3 of 5
  +0.4595 +0.2472 -0.2855 (10-20 13:59:21 @0.999)
  total_net=+0.4212 USDC, cost=185.69, ROI=0.23%
```

结论：**没有可证明的正 EV**。0.95 门槛下 5 个事件 0 笔；放宽到 0.99 只有 2 笔，合计 +0.71 USDC；不限价 3 笔也只有 +0.42 USDC。07:00 的事后赢家回放（首笔 0.49–0.88）只作诊断，不能当收益证据。

## 4. 处置结论（直说）

**建议退回/放弃（drop）。** 理由：

- 门 5 不满足：≤0.95 实际 BUY 成交 0/5；≤0.99 只有 2 笔、+0.7067 USDC。
- 门 6 不满足：历史 5 个独立事件，两周前向约 14 个，合计 19 个 <30。
- 门 2 只能靠前向记录补齐；门 4 仍有 dot-004 宽口径重复风险。
- 如果整合者需要一个“待选区”参考，可保留为 `待选区`；但按 `待核`/`收录` 标准，不应占用第 2 轮名额。

## 5. 复跑文件与命令

全部在 `bots/quant/notes/scheduler/scratch/P-quant-031/`；原始下载在 `_cache/`（`.gitignore` 已写 `_cache/`，每个文件 <1 MB）。

```bash
cd bots/quant/notes/scheduler/scratch/P-quant-031
python3 fetch_cdx.py > fetch_cdx_out.txt 2>&1         # Wayback CDX index (294 rows), needed by fetch_snapshots
python3 fetch.py > fetch_out.txt 2>&1                 # Gamma events + 30 markets + CLOB history + data-api trades
python3 fetch_snapshots.py > fetch_snapshots_out.txt  # Wayback 64 snapshots (curl retries for TLS EOF)
python3 parse_snapshots.py > parse_snapshots_out.txt  # aaa_snapshots_all.csv
python3 verify.py > verify_out.txt 2>&1                # rules/fees/outcomes/closedTime/2025 checks
python3 event_study.py > event_study_out.txt 2>&1      # ex-post event study
python3 backtest_trades.py > backtest_trades_out.txt  # net-of-fee historical backtest (tradable prints)
python3 backtest.py > backtest_out.txt 2>&1            # CLOB-mid diagnostic only (rejected)
python3 recheck.py > recheck_out.txt 2>&1              # CDX counts, date coverage, 2025 trades, print sizes
```

关键 stdout：`verify_out.txt`、`event_study_out.txt`、`backtest_trades_out.txt`；快照表：`aaa_snapshots_all.csv`；Polymarket 三个示例页重取均为 HTTP 200，见 `url_check_out.txt`。

## 6. 未解决 / 开放问题

- 全仓 `python3 tools/check.py lint` 仍在既有的 `bots/muse/entries/muse-700-defined-risk-iron-fly.md`、`muse-701-skew-harvest-sign-correction.md` 上 `KeyError: 'id'`（front matter 前有 blockquote），与本条无关；本条 17 个必填字段已单独检查。
- Wayback 在本环境间歇性 `SSL: UNEXPECTED_EOF_WHILE_READING`；脚本用 `curl` 重试后取到 64 个快照，原始 HTML 在 `_cache/`。
- data-api 只有成交、没有历史 L2；本文的“可成交”是实际 BUY 成交价代理，不能证明决策时点一定有 ≤0.95 的卖单。
- 历史独立事件只有 5 个，前向两周约 14 个，仍不足以按 GUIDE 门槛 6 完成 30 个独立结果。

## 7. 2026-10-21 04:00 UTC 复核补充

从空 `_cache/` 重新拉取 CDX、Gamma、CLOB、data-api 与 64 张 Wayback 快照，重跑全部脚本；关键结论与第 3 节完全一致（≤0.95 0/5；≤0.99 2/5、净 +0.7067 USDC；不限价 3/5、净 +0.4212 USDC；YES 成交 6/10/21/13/11=61）。本轮又发现并修正了几处数字/措辞：

| 问题 | 改法 | 证据 |
|---|---|---|
| CLOB 点数写成“135–155” | 改为 **135–172**（10-16 约 170、10-17 151–153、10-18 135–137、10-19 150–155、10-20 150–155） | 重跑 `fetch.py` / `verify_out.txt`：10-16 获胜档 172 点，10-18 135 点 |
| “64 个快照覆盖 16 个日期” | 改为 **64 个快照分布在 33 个日期，其中 16 个日期至少有一张显示当天值** | `recheck_out.txt`：`PARSED_SNAPSHOTS 64 DATES 33`，`FIRST_CURRENT_BY_DATE` 16 行 |
| “事件日首次看到当天值 07:30–11:03” | 改为“**所有解析日期**首次看到当天值 07:30–11:03；**5 个事件日集中在 09:56–11:03**” | `recheck_out.txt`：最早 10-06 07:30，事件日最早 10-19 09:56 |
| 10-16 写“07:27 后再无成交” | 明确为“**14:00 UTC 收盘前**无后续成交；14:22:36 的 0.9892 是收盘后成交” | 重抓 data-api：10-16 获胜档 14:22:36 BUY 0.989244，82.19 份 |
| 容量段“单笔 20–264 份” | 改为“收盘前获胜档 YES **4.25–264.18 份**，约 4.24–201.42 USDC” | `recheck.py`：收盘前 25 笔，size min/max 4.248/264.18，USDC min/max 4.24/201.42 |
| 风险节标题仍写“没有可抢的价” | 改为“**样本里没有 ≤0.95 的成交，是否有可成交卖价未知**” | 与 review #2 的要求一致 |
| 2025 Feb-28 “SELL @0.99” | 复核方向正确，无需改 | data-api：10:26:39 SELL 0.99，2.2 份；YES 共 32 笔；Feb-21 YES 38 笔 |

**处置结论不变：建议退回/放弃（drop）。** 门 5 不满足（≤0.95 成交 0/5；≤0.99 仅 2 笔、净 +0.7067 USDC），门 6 不满足（历史 5 + 两周前向约 14 = 19 < 30），门 2 只能靠前向记录，门 4 仍有 dot-004 宽口径重复风险。若整合者需要一个待选区参考，可保留为 `待选区`；按 `待核`/`收录` 标准不应占用第 2 轮名额。`status: 草稿` 和 `date: 2026-10-20` 未改。
