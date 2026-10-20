# quant-005 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

抓取时间：2026-10-20（UTC）。全部为 keyless 公开 GET，无 API key、无登录、未下单。

| # | URL（实抓原文） | HTTP | 我从里面取的东西（原文片段 / 数字） |
|---|---|---|---|
| 1 | `https://gamma-api.polymarket.com/events?slug=elon-musk-of-tweets-october-20-26` | 200，body=`[]` | 该 slug 不存在 → 改用 public-search 找真实 slug。未作为出处引用。 |
| 2 | `https://gamma-api.polymarket.com/public-search?q=elon%20musk%20tweets&limit_per_type=10&events_status=active` | 200，581,459 B | 6 个 active slug：`elon-musk-of-tweets-october-13-october-20-2026`、`-october-16-october-23-2026`、`-october-19-october-21-2026`、`-october-20-october-27-2026`、`-october-22-october-24-2026`、`elon-musk-of-tweets-october-2026`。用来发现 slug 命名规律（正文未直接引用）。 |
| 3 | `https://gamma-api.polymarket.com/events?slug=elon-musk-of-tweets-october-19-october-21-2026` | 200，42,981 B | title “Elon Musk # tweets October 19 - October 21, 2026?”；`endDate=2026-10-21T16:00:00Z`；`volume=94153.668804`；`liquidity=53563.09908`；`negRisk=true`；`restricted=true`；`resolutionSource='https://x.com/elonmusk'`；tags `Culture/Politics/Tweet Markets/Recurring`；series `{id:"10816", ticker/slug:"elon-tweets-48h", title:"Elon Tweets 48H", recurrence:"daily", createdAt:"2025-12-29T18:59:23.165746Z", volume24hr:346875.646022}`。规则原文逐字取用：“from October 19 12:00 PM ET to October 21, 2026 12:00 PM ET”、“only main feed posts, quote posts and reposts will count”、“Replies will NOT count towards the total - however, replies on the main feed such as https://x.com/elonmusk/status/1786073478711353576 will be counted by the tracker”、“Deleted posts will count as long as they remain available long enough to be captured by the tracker (~5 minutes)”、“Community reposts which are not counted by the tracker not count toward the total”、“The resolution source for this market is the 'Post Counter' figure for posts found at https://xtracker.polymarket.com. Individual posts can be viewed by clicking "Export Data". If the tracker does not update correctly in accordance with the rules, X itself may be used as a secondary resolution source.” 10 档与 `outcomePrices`：`<40 ["0.07","0.93"]`、`40-64 ["0.55","0.45"]`、`65-89 ["0.335","0.665"]`、`90-114 ["0.055","0.945"]`、`115-139 ["0.0085","0.9915"]`、`140-164 ["0.004","0.996"]`、`165-189 ["0.0015","0.9985"]`、`190-214 ["0.0005","0.9995"]`、`215-239 ["0.0005","0.9995"]`、`240+ ["0.0005","0.9995"]`。每档 `feeSchedule={exponent:1, rate:0.05, takerOnly:true, rebateRate:0.25}`。`orderPriceMinTickSize`：`<40` 为 0.001，中段为 0.01。 |
| 4 | `https://gamma-api.polymarket.com/events?slug=elon-musk-of-tweets-october-17-october-19-2026` | 200 | `closed=true`；`40-64` 档 `outcomePrices=["1","0"]`；其余 9 档 `["0","1"]`；全部 `closedTime` 为 `2026-10-19 18:03:14/15/44+00`、`umaResolutionStatus="resolved"`、`resolvedBy=0x69c47De9D4D3Dad79590d61b9e05918E03775f24`；`<40` 档 `closedTime 2026-10-18 19:12:12+00`（该档提前归零）。 |
| 5 | `https://gamma-api.polymarket.com/events?slug=donald-trump-of-truth-social-posts-october-20-october-27-2026` | 200 | title “Donald Trump # Truth Social posts October 20 - October 27, 2026?”；`endDate=2026-10-27T16:00:00Z`；`volume=11389.525684`；`liquidity=31857.22875`；series `{id:"11108", slug:"trump-truth-social", recurrence:"daily", volume24hr:21980.33482}`；规则原文 “between October 20, 12:00 PM ET and October 27, 2026, 12:00 PM ET”、“the "Post Counter" figure for posts found at https://xtracker.polymarket.com”、“Truth Social itself may be used as a secondary resolution source”；11 档 `<20 ["0.0045",...]` … `200+ ["0.195","0.805"]`，每档 `rate=0.05`。 |
| 6 | `https://gamma-api.polymarket.com/public-search?q=truth%20social%20posts&limit_per_type=10&events_status=active` | 200，136,997 B | 3 个 active slug：`donald-trump-of-truth-social-posts-october-13-october-20-2026`、`-october-16-october-23-2026`、`-october-20-october-27-2026` → 正文“3 个并行 7 天窗口”。 |
| 7 | `https://gamma-api.polymarket.com/public-search?q=elon%20musk%20tweets&limit_per_type=25&events_status=closed&page=1` | 200，1,016,157 B | `pagination={hasMore:True, totalResults:342}`；25 条结果含历史变体 slug（如 `of-elon-musk-tweets-between-january-10-16`、`elon-musk-number-of-tweets-25-times-8-12`、`elon-musk-of-tweets-february-21-february-23`、`elon-musk-of-tweets-october-17-october-19-2026`）。 |
| 8 | `https://gamma-api.polymarket.com/events?series_id=10816&limit=500&closed=true` | 200 | 只返回 **100** 条事件（`limit` 上限被压到 100）；`endDate` 最小 `2026-01-03T17:00:00Z`、最大 `2026-08-22T16:00:00Z`；按 endDate 月份计数 `2026-01:13, 02:12, 03:13, 04:13, 05:13, 06:13, 07:13, 08:10`（08 月因 100 条截断不完整）。 |
| 9 | `https://xtracker.polymarket.com` | 200，11,054 B，`text/html` | 规则点名的界面站，确为 Next.js 页面（非 JSON 接口）。 |
| 10 | `https://xtracker.polymarket.com/api/users/elonmusk` | 200，3,612 B | `{"handle":"elonmusk","platformId":"44196397","platform":"X","lastSync":"2026-10-13T22:55:30.002Z","lastSyncError":"2026-10-20T04:00:38.825Z"}`；7 个 `trackings`，全部 `isActive:true`，`metrics:{}`、`target:null`，`createdAt` 分别 2026-08-24、2026-10-13、2026-10-17（两条）、2026-10-19、2026-10-20 等。 |
| 11 | `https://xtracker.polymarket.com/api/trackings/183475ce-0cd8-46ba-9b4c-ed53187f4bd2` | 200 | 该 tracking 单条记录：`metrics:{}`、`target:null` → **没有** 官方 Post Counter 计数字段（正文“未查到”）。 |
| 12 | `https://xtracker.polymarket.com/api/users/elonmusk/posts?limit=3` 与 `?limit=100&offset=0` | 200（后者 4,840,334 B） | 两次都返回全量 **13,671** 条（`limit` 参数被忽略）；字段 `id/userId/platformId/content/createdAt/importedAt/metrics(null)`；`createdAt` 最早 `2025-10-31T00:17:35.000Z`、最新 `2026-10-20T02:41:54.000Z`；首条 `importedAt=2026-10-20T02:45:30.035Z`（比 createdAt 晚约 3.6 分钟，与规则“~5 minutes”抓取窗口相符）。 |
| 13 | `https://clob.polymarket.com/book?token_id=22442061711236593150409027149743058571520366316242909612280801414810466891148`（`40-64` 的 Yes token） | 200（带 `User-Agent: Mozilla/5.0`）；不带 UA 的 `urllib` 请求 4 个 token 全部 **403 Forbidden** | bids 末三档 `(0.52,298.6) (0.53,162.51) (0.54,257.39)`；asks 首三档 `(0.57,232.52) (0.58,214.45) (0.59,86.91)`；`timestamp=1792468954667`。 |
| 14 | `https://clob.polymarket.com/prices-history?market=34767215645050247279179635677802776215709078037234086703701315748816860889727&interval=max&fidelity=60` | 200 | 已结算市场仍有价格历史：`history` 长度 **86**，首 `{t:1792083636,p:0.515}`、末 `{t:1792432830,p:0.9995}` → 正文“86 个点 / 约 97 小时”。 |
| 15 | `https://clob.polymarket.com/prices-history?market=<同上>&startTs=1789000000&endTs=1792530000&fidelity=60` | **400 Bad Request** | `startTs/endTs` 参数格式不被接受 → 正文据实写明“实测 400”。 |
| 16 | `https://gamma-api.polymarket.com/events?limit=20&closed=false&order=volume24hr&ascending=false&tag_slug=elon-musk` | 200，896,561 B | `tag_slug` 过滤未生效（返回 Tesla/SpaceX 合并等无关事件）→ 未使用、未引用。 |

### 本文自算（脚本均在本地临时目录运行，未写入仓库）

- `count(createdAt ∈ [2026-10-17T16:00Z, 2026-10-19T16:00Z)) = 62`（对 13,671 条记录过滤）。
- 180 个自然日（2026-04-23…2026-10-19）日计数：`mean=30.678`、`variance=281.728`、`var/mean=9.183`、min 6、max 134。
- 160 个滚动 48h 窗口（结束 16:00Z，末窗口 2026-10-19T16:00Z，回推 160 天）：`mean=63.20`、`variance=673.36`、min 22、max 171；`40≤x<65` 的 78 个 = 48.7%。
- 条件筛（前 10.70h 计数 ≤11）：命中 61/160；总数 `mean=51.3`、`median=51`、min 22、max 100；落档 `<40` 15、`40-64` 37、`65-89` 7、`90-114` 2、`115+` 0。
- 当前窗口：`11` 条，`elapsed=(2026-10-20T02:41:54Z − 2026-10-19T16:00Z)/3600 = 10.70 h`，`remaining=37.30 h`。
- 费用：`0.05×0.57×0.43=0.012255`、`0.05×0.55×0.45=0.012375`、`0.05×0.07×0.93=0.003255`、`0.05×0.335×0.665=0.011139`；半价差 `(0.57−0.54)/2=0.015`；`0.012375+0.015=0.027375`，`/0.555=4.93%`；`0.61−0.555−0.027375=+0.0277/pc`。
- 十档中间价相加 `0.07+0.55+0.335+0.055+0.0085+0.004+0.0015+0.0005+0.0005+0.0005=1.025`。

### 未取的（正文已写“未查到”，勿当作者遗漏）

- xtracker 官方 “Post Counter” 数值接口 / 历史计数快照。
- 已结算市场的历史逐小时价差（`prices-history` 只给价格点，无 bid/ask）。
- 历史 L2 盘口（GUIDE 第 8 节：无公开源）。
- 除 #14 那一个 token 之外，其他 market/token 的 `prices-history` 是否都可取（未逐个验证，已在门槛 6 标注为降级风险）。

---

## glm-5.3 事实核查报告

# Fact-Check Report: B02.md (quant, Polymarket post-count brackets)

**Re-fetched 12 URLs.** Nearly every number/quote verifies; the worker's self-computed statistics reproduce **exactly** from the re-downloaded xtracker dump (13,671 posts at their snapshot, window count = 62, current-window 11 posts/10.70 h, 180-day mean 30.678/var 281.728/ratio 9.18, 160-window mean 63.20/var 673.36/min 22/max 171/78 in 40–64, conditional n=61 mean 51.3 median 51 brackets 15/37/7/2/0, daily 28/36/21, all fee arithmetic, mid-sum 1.025).

**Problems (all minor):**
1. Front-matter `id: quant-XXX` — invalid placeholder; GUIDE §7 requires id to match the filename (e.g. `quant-002-post-count-brackets.md`). Must fix before commit.
2. `timestamp=1792468954667（毫秒，本文换算约 2026-10-20T03:52Z）` — MISMATCH: that epoch = **2026-10-20T04:02:34Z** (~10 min off). Immaterial, but fix the conversion.
3. `160 个滚动 48h 窗口（结束于 16:00Z，2026-05-12 至 2026-10-19）` — off-by-one label: first window **ends** 2026-05-13 (starts 05-11). Stats still reproduce exactly.
4. `totalResults=342` — now 343 (live counter; new closures). Time-varying, acceptable.

**Time-varying (worker gave snapshot; OK):** outcomePrices (0.07/0.55/0.335 → 0.074/0.555/0.305; sum 1.025→1.0045), book bid/ask (0.54/0.57 → 0.54/0.55), liquidity (Elon 53,563→51,448; Trump 31,857→25,125), lastSyncError (04:00:38→04:05:43), posts count (13,671→13,672), active Trump windows (3→4, a new one opened — actually supports claim (a)). Volumes, series IDs, all 10+11 brackets, `feeSchedule{rate:0.05,exponent:1,takerOnly,rebateRate:0.25}`, monthly counts 13/12/13/13/13/13/13/10, settled `40-64 ["1","0"]`, `closedTime 18:03:14`, `resolvedBy 0x69c4…`, 86 price points 0.515→0.9995 (~97 h), startTs→400, no-UA→403, and **all rule quotes verbatim** (incl. the "Community reposts … not count" grammar error): VERIFIED.

**Rule compliance:** required fields present except `id`; `pm_category: mentions`, `category: S`, `status: 草稿` all valid. Fee uses GUIDE §8 formula and correctly prefers the market's actual 0.05 over GUIDE's 0.04 table, flagging the discrepancy. Volume/liquidity honestly marked 来源自报. 门槛自查 is honest (backtest_count=0 explicit; +4.9% labeled single-timepoint, "不能据此声称有正收益"). No keys/paid data/trading. No backtest claims.

**Duplication:** none — no tweet/xtracker/post-count mechanism in KNOWN.md (135), dot entries, or claims; B02 registered in quant CLAIMS.md; distinct from B01 (word-occurrence) and dot C01 (weather).

VERDICT: FIX — evidence is fully reproducible and honest, but the `id: quant-XXX` placeholder (plus two trivial arithmetic/label slips) must be corrected before submission.
GATES_PASSING: 6/7
