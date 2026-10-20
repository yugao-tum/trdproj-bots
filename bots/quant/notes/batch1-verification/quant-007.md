# quant-007 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

抓取日 2026-10-20（UTC），全部为 keyless 公开 GET，无登录、无 API key、无下单。

| # | URL | HTTP | 取到的原文片段 / 数字 | 用在哪一节 |
|---|---|---|---:|---|
| 1 | `https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-october` | 200（143,922 B） | `"id":"841230"`；`This market will resolve according to the company which owns the model which has the highest arena rank based on the arena.ai Text Arena (Overall) when the table under the "Leaderboard" tab is checked on October 31, 2026, 12:00 PM ET.`；`...at https://arena.ai/leaderboard/text/overall-no-style-control with style control off (Adjustments: None) and filtered for "Models"`；`Models marked “AutoEval” ... will not be considered`；`If two or more models are tied on rank, they will be ordered by their Arena score, including any underlying, unrounded, granular values`；`“Google” would be ranked ahead of “SpaceXAI”`；`If it becomes permanently unavailable, this market will resolve to "Other"`；`"startDate":"2026-08-13T00:02:19Z"`、`"endDate":"2026-10-31T16:00:00Z"`、`"updatedAt":"2026-10-20T04:00:58.254529Z"`、`"negRisk":true`、`"volume":2956232.941996`、`"liquidity":1513204.40709`、32 markets、`"feeSchedule":{"exponent":1,"rate":0.04,"takerOnly":true,"rebateRate":0.25}`、Google `bestBid 0.742 / bestAsk 0.743 / orderPriceMinTickSize 0.001`、Anthropic `bestBid 0.23 / bestAsk 0.24 / spread 0.01 / orderPriceMinTickSize 0.01`、OpenAI `0.006/0.008`、`orderMinSize 5`、`Company A–I,K`+`Other` 每臂 `["0.5","0.5"]/bid 0 ask 1` | 规则、证据、成本 |
| 2 | 同上（算术） | — | 21 个具名臂 `outcomePrices[0]` 求和 = **0.9955**；32 臂求和 = **6.4955** | 证据、风险（非套利） |
| 3 | `https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-november` | 200 | `"endDate":"2026-12-01T04:59:00Z"`、`"volume":341608.787719`、35 markets、Anthropic `0.41 / bid 0.39 / ask 0.43 / spread 0.04`、Google `0.515 / bid 0.50 / ask 0.53 / spread 0.03`、OpenAI `0.041 / 0.035 / 0.047`、占位到 `Company M` | 证据、成本 |
| 4 | `https://gamma-api.polymarket.com/series/10030` | 200（43,662 B） | `"title":"Best AI Company"`、`"recurrence":"monthly"`、`"createdAt":"2025-02-01T00:23:50.592739Z"`、`"restricted":true` | 数据（频率/起始） |
| 5 | `https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true` | 200（1,810,300 B） | 返回 **22** 个已结算 event；最早 `top-ai-model-on-december-31`（`endDate 2024-12-31T12:00:00Z`，5 markets，volume 1,108,146.9）；最新 `which-company-has-the-best-ai-model-end-of-september-20260717143435868`（`2026-09-30T16:00:00Z`，32 markets）；各期臂数 5→32，volume 逐期（例：`which-company-has-best-ai-model-end-of-2025` 36,331,301.2） | 数据、门槛自查 6 |
| 6 | `https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=false` | 200（424,391 B） | **3** 个在开：`which-company-has-best-ai-model-end-of-2026`（26 臂，`endDate 2026-12-31T17:00:00Z`）、`which-company-has-the-best-ai-model-end-of-october`（32 臂）、`...-end-of-november`（35 臂） | 数据（每月 1 个） |
| 7 | 同日 `serEv.json` 中 2024-12 与 2025-09 两期 description | 200（同 #5 响应） | 2024-12 全文 = `This is a negrisk market group over which will be the top AI model on December 31, 2024, 12:00 PM ET.`（101 字符，无结算源）；2025-09 = `the highest arena score based off the Chatbot Arena LLM Leaderboard (https://lmarena.ai/)`、`with the style control off`、平手按字母序、源永久不可用则"按另一个结算源" | 规则（改版） |
| 8 | `https://clob.polymarket.com/book?token_id=111088620532234518037120406087772586039940496346205331791940213760503764823657` | 200（4,327 B） | bids 首档 `0.742×196`、asks 首档 `0.743×128.15`；前 10 档 bid 合计 1,240.1 USD、ask 2,387.7 USD | 成本与容量 |
| 9 | `https://clob.polymarket.com/book?token_id=17398972530137600675762712744895375915722542439211248541948693649429200536957` | 200（2,308 B） | bids 首档 `0.23×570.38`、asks 首档 `0.24×186.59`；前 10 档 bid 1,220.7 USD、ask 7,448.4 USD | 成本与容量 |
| 10 | `https://arena.ai/leaderboard/text/overall-no-style-control` | **403**（5,554 B 阻断页） | 结算源原文所在页；无内容可取 | 证据（未取得） |
| 11 | `https://arena.ai/leaderboard/text/overall` | **403**（5,481 B） | 同上 | 证据（未取得） |
| 12 | `https://arena.ai/api/leaderboard/text` | **403**（5,469 B） | 猜测的 JSON 端点，被阻断 | 证据（未取得） |
| 13 | `https://lmarena.ai/leaderboard/text` | **403**（5,436 B） | 旧域名同样阻断 | 证据（未取得） |
| 14 | `https://web.archive.org/cdx/search/cdx?url=arena.ai/leaderboard/text/overall-no-style-control&output=json&limit=6&from=2026&filter=statuscode:200` | 200（1,260 B） | 索引含 `20260130012509`、`20260206191801`、`20260209233652` 等 statuscode 200 快照（证明历史快照存在） | 数据、门槛自查 2 |
| 15 | `https://web.archive.org/cdx/search/cdx?url=lmarena.ai/leaderboard/text&output=json&limit=5&from=2026&filter=statuscode:200` | 200（833 B） | `20260101210823` 等；`urlkey "ai,lmarena)/leaderboard/text"` | 数据 |
| 16 | `https://web.archive.org/cdx/search/cdx?url=lmarena.ai/leaderboard/text&output=json&from=20260801&filter=statuscode:200&limit=4` | 200 | 返回空数组 `[]`（2026-08 起该 URL 无成功快照） | 数据缺口 |
| 17 | `https://web.archive.org/web/20260101210823/https://lmarena.ai/leaderboard/text` | 200（1,591,011 B） | 抓到 HTML，但未解析出榜单表（`grep` 到的 `1456.5/1444.9/...` 经复核是 SVG `path` 坐标，不是 Arena 分数）→ **不作为数据，未引用任何分数** | 未用 |
| 18 | `https://web.archive.org/web/20260130012509/https://arena.ai/leaderboard/text/overall-no-style-control` | **000**（两次：默认 UA、`-A Mozilla/5.0`+60s） | 无响应/超时，无文件 | 证据（失败） |
| 19 | `http://archive.org/wayback/available?url=lmarena.ai/leaderboard/text&timestamp=20260901` | **000** | 无响应 | 未用 |
| 20 | `https://gamma-api.polymarket.com/public-search?q=best%20AI%20model&limit_per_type=20` | 200（2,121,848 B） | 返回的是 `elon-musk-of-tweets-*` 等 event，与 AI 榜无关 → 未用；改用 `series_id=10030` 枚举 | 未用 |
| 21 | `https://gamma-api.polymarket.com/markets?closed=false&limit=100&order=endDate&ascending=false` | 200（630,205 B） | 未用于任何数字 | 未用 |

未能核实、因此条目内一律写"未查到"的项：榜单当前 Rank / Top1 与 Top2 的 Arena 分数与置信区间 / AutoEval 名单 / 任何历史日期的榜单快照内容 / 历史"领头者被翻盘"基率 / 22 个已结算 event 的实际冠军与当期 Rank 是否一致。

---

## glm-5.3 事实核查报告

# Fact-check report — B04.md (月度AI榜首市场)

## Refetch results (15 fetches)

**VERIFIED exactly (Gamma):** event id 841230; all rule quotes ("Rank column…overall-no-style-control…style control off (Adjustments: None)", AutoEval exclusion, granular-score tiebreak, "Google" ahead of "SpaceXAI", permanently-unavailable→"Other"); startDate/endDate; negRisk/restricted/enableOrderBook; 32 arms = 21 named + Company A–I,K + Other (all `0.5/0.5, bid 0/ask 1`); Google 0.742/0.743 tick 0.001, Anthropic 0.23/0.24, OpenAI 0.006/0.008; `feeSchedule {rate 0.04, takerOnly, rebateRate 0.25}`; `orderMinSize 5`; volumes 2,956,232.941996 / 341,608.787719; named-arm sum **0.9955** and all-32 sum **6.4955**; Nov event 35 arms to Company M, endDate 2026-12-01T04:59Z, 0.39/0.43 & 0.50/0.53; series 10030 (monthly, createdAt 2025-02-01T00:23:50Z); **22** closed events (earliest `top-ai-model-on-december-31`, endDate 2024-12-31T12:00Z, 5 arms; latest 2026-09, 32 arms, Rank-column rule); 3 open events (incl. end-of-2026, 26 arms); 2024-12 description = 101 chars, exact text as quoted; 2025-09 quotes (lmarena.ai, style control off, alphabetical tiebreak, "another resolution source") exact. arena.ai (3 paths) and lmarena.ai all **403** today as stated. Google `last_trade_price 0.736` ✓.

**Time-varying (worker gave timestamp 2026-10-20):** liquidity 1,513,204.41→1,499,598.10; OpenAI Nov ask 0.047→0.045; CLOB top-of-book prices/sizes match (0.742×196, 0.24×186.59 exact; 0.743 size 108.17 vs 128.15; 0.23 size 584.87 vs 570.38) but top-10 depth sums now 2,501/3,141 (Google) and 1,565/7,959 (Anthropic) vs claimed 1,240/2,388 and 1,221/7,448 — consistent with a minutes-earlier real fetch; capacity conclusions unaffected.

**Could not re-verify:** Wayback CDX index (my fetch HTTP 000, same failure mode worker reported for content); worker's honesty about failures makes this credible.

## Problems

1. **Front-matter `id: quant-XXX`** — placeholder; GUIDE §7 requires id matching filename (e.g. `quant-004`). Fix before submission.
2. **MISMATCH — "500 份 Anthropic @0.24 ≈ 386 美元"**: 500×0.24 = **120 USDT** (386 = 500×0.772, looks like the No-side price). Repeated in 门槛自查 3 ("372–386 美元" → should be 120–372). Google's 372 is correct.
3. Minor: "约 11.4 天" is 11.5 days by the same timestamps; harmless.
4. Minor: liquidity figure drifted (time-varying; keep timestamp note).

## Rule compliance

No keys/paid data (all keyless GETs) ✓; no backtest claims — explicitly `backtest_count = 0`, `observed_net_return = null` ✓; fee formula = GUIDE §8 (费率×p×(1−p), maker 0/ rebate noted) ✓; 来源自报 labeling not needed (all first-hand, own arithmetic marked) ✓; 门槛自查 honest (admits gates 2/6 fail) ✓; status 草稿 ✓; all cost arithmetic (breakevens 75.11/25.23/45.98/55.50%, 1.0953%–6.9312%) recomputed correct.

## Duplication

None: KNOWN.md (135) has no arena/leaderboard mechanism; dot entries/CLAIMS (C01–C49, dot-001–049) and muse have nothing on AI-arena markets; entry correctly distinguishes dot-032; quant's own CLAIMS.md has B04 claimed 进行中 ✓.

VERDICT: FIX — substance is exceptionally well-verified, but the `quant-XXX` id placeholder and the 386-vs-120 USDT capital error must be corrected before submission.

GATES_PASSING: 4/7
