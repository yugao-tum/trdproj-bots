# quant-010 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

访问日期除非另写，均为 2026-10-20。只列本次实际执行的 GET；未登录、未用密钥、未付费。

1. `https://gamma-api.polymarket.com/events?slug=top-netflix-show-this-week` — HTTP 200 — 返回 `[]`；该猜测 slug 无数据。
2. `https://gamma-api.polymarket.com/markets?closed=false&limit=100&tag_slug=culture` — HTTP 200 — 首条为 `Xi Jinping out before 2027?`，与本条无关；只用于确认 tag 查询可用，未取数。
3. `https://gamma-api.polymarket.com/public-search?q=netflix` — HTTP 200 — 返回事件含 `what-will-be-the-2-us-netflix-show-this-week-october-20`，规则原文 “updates its Top 10 TV shows list ... Tuesday, October 20, 2026, 3:00 PM ET”；`resolutionSource=https://www.netflix.com/tudum/top10/united-states/tv`。
4. `https://gamma-api.polymarket.com/public-search?q=netflix%20%231` — HTTP 200 — 返回 2021 年 Squid Game 等历史 Netflix #1 事件；说明该题材至少可回溯到 2021。
5. `https://gamma-api.polymarket.com/public-search?q=spotify` — HTTP 200 — 返回 `2-spotify-artist-in-october-20261031`、`top-spotify-album-2026` 等；未用作本条证据。
6. `https://gamma-api.polymarket.com/public-search?q=top%20netflix%20show` — HTTP 200 — 返回 `what-will-be-the-top-us-netflix-show-this-week-october-20`、`what-will-be-the-top-global-netflix-show-this-week-october-20`，endDate 均 `2026-10-21T03:59:00Z`。
7. `https://gamma-api.polymarket.com/events?slug=what-will-be-the-top-global-netflix-show-this-week-october-20` — HTTP 200（2026-10-20 两次抓取）— 17 个市场；event `volume=5065.164545`、`liquidity=4423.9158`；description 含 “Tuesday, October 20, 2026, 3:00 PM ET”、“previous week (Monday to Sunday)”、“total views globally ... (English only)”、“If the top10.netflix.com update does not occur by October 23, 2026, 11:59 PM ET, this market will resolve to "Other"”；`Below` 价格 `["0.9975","0.0025"]`、`bestBid=0.997`、`bestAsk=0.998`、`spread=0.001`、`volume=1153.424795`、`feeSchedule={"exponent":1,"rate":0.05,"takerOnly":true,"rebateRate":0.25}`。
8. `https://gamma-api.polymarket.com/public-search?q=%231%20song` — HTTP 200 — 返回 2026 年 `1-song-on-spotify-this-week-march-27` 等历史 #1 song 事件。
9. `https://gamma-api.polymarket.com/events?slug=1-song-on-spotify-this-week-april-3` — HTTP 200 — 22 个市场；description 含 “updates it on Fridays ... beginning on the preceding Friday and ending on Thursday”、“week labeled April 3”、“default to "Other"”；市场 `rewardsMinSize=50`、`rewardsMaxSpread=4.5`；该历史事件 `feeSchedule` 为 `null`（新市场才有）。
10. `https://flixpatrol.com/top10/netflix/world/` — HTTP 403（5454 bytes）— 未见页面内容；加 `-A 'Mozilla/5.0'` 后 HTTP 403（5433 bytes）。未引用其任何数字。
11. `https://kworb.net/spotify/` — HTTP 200（23351 bytes）— 页面标题 “Spotify Charts”，正文 “Aggregates of all daily and weekly charts provided by Spotify”；链接含 `country/global_daily.html`、`country/us_daily.html`。
12. `https://www.netflix.com/tudum/top10/tv` — HTTP 200（3409990 bytes）— 页面 “Global | 10/5/26 - 10/11/26”；表首行 `01Below: Limited Series`, Views `17,000,000`, Runtime `4:04`, Hours Viewed `69,300,000`；日期字符串最早见 `2021-06-28`。
13. `https://charts.spotify.com/charts/view/regional-global-weekly/latest` — HTTP 200（12650 bytes）— 前端页面，未解析出榜单数字，未引用。
14. `https://kworb.net/spotify/country/global_daily.html` — HTTP 200（89439 bytes）— “Spotify Daily Chart - Global - 2026/10/18”；第 1 名 “KAROL G - BbY WOW (w/ Judeline , rusowsky)”，“4,719,966” streams，“35,919,162” 7Day。
15. `https://gamma-api.polymarket.com/public-search?q=top%20song` — HTTP 200 — 返回 2021–2022 年 “top song on Spotify Charts hit … streams” 事件；未用作本条证据。
16. `https://gamma-api.polymarket.com/public-search?q=spotify%20this%20week` — HTTP 200 — 返回 `1-song-on-spotify-this-week-december-25`、`…january-30`、`…march-27` 等。
17. `https://gamma-api.polymarket.com/public-search?q=song%20this%20week` — HTTP 200 — 返回 `1-spotify-song-this-week-august-28`、`1-spotify-song-this-week-october-2-20260925t140000000z` 等；确认 Spotify 周事件按周连续。
18. `https://gamma-api.polymarket.com/events?slug=1-spotify-song-this-week-october-2-20260925t140000000z` — HTTP 200 — 14 个市场；`resolutionSource=https://open.spotify.com/charts`；description 与第 9 条同模板，周标签 October 2；市场 `feeSchedule` rate 0.05、`takerOnly=true`、`rebateRate=0.25`。
19. `https://gamma-api.polymarket.com/events?slug=what-will-be-the-top-us-netflix-show-this-week-october-20` — HTTP 200 — 16 个市场；event `volume=1834.890906`、`liquidity=5938.23516`（updatedAt 2026-10-20T04:04:56Z）；`Below` 价格 `["0.995","0.005"]`、`bestBid=0.991`、`bestAsk=0.999`、`spread=0.008`。
20. `https://gamma-api.polymarket.com/public-search?q=spotify%20song%20this%20week%20october%2016` — HTTP 200 — 返回 `1-spotify-song-this-week-october-16-20261012`、`2-spotify-song-this-week-october-16-20261012`、`1-spotify-song-in-the-us-this-week-october-16-20261012`、`2-spotify-song-in-the-us-this-week-october-16-20261012` 四个事件。
21. `https://gamma-api.polymarket.com/events?slug=1-spotify-song-this-week-october-16-20261012` — HTTP 200 — 14 个市场；event `volume=8072.917061`；`KAROL G - BbY WOW` 价格 `["1","0"]`、`volume=4383.916683`；`feeSchedule` rate 0.05。
22. `https://gamma-api.polymarket.com/public-search?q=spotify%20song%20this%20week%20october%2023` — HTTP 200 — 返回 `1-spotify-song-in-the-us-this-week-october-23-10172026`，endDate `2026-10-23T23:59:00Z`。
23. `https://gamma-api.polymarket.com/events?slug=1-spotify-song-in-the-us-this-week-october-23-10172026` — HTTP 200 — 15 个市场；event `volume=8505.801068`、`liquidity=10002.81181`；`Housewife` `["0.9615","0.0385"]`、`bestBid=0.938`、`bestAsk=0.985`、`spread=0.047`、`volume=2337.933896`；`Nicole Kidman` `["0.028","0.972"]`、`bestBid=0.011`、`bestAsk=0.045`、`spread=0.034`；`feeSchedule` rate 0.05。
24. `https://kworb.net/spotify/country/us_daily.html` — HTTP 200（87091 bytes）— “Spotify Daily Chart - United States - 2026/10/18”；第 1 名 “Tate McRae - Housewife”，当日 “1,127,046” streams。
25. `https://www.netflix.com/tudum/top10/united-states/tv` — HTTP 200（3372722 bytes）— “United States | 10/5/26 - 10/11/26”；表首行 `01Below: Limited Series`，与全球页一致。

计算复核：
- 示例 A 费：100×0.05×0.985×0.015 = 0.073875；半价差 (0.985−0.938)/2×100 = 2.35；合计 2.423875；2.423875/98.50 = 0.024608… = 2.46%；100−98.50−2.423875 = −0.923875。
- 示例 B 费：100×0.05×0.045×0.955 = 0.214875；半价差 (0.045−0.011)/2×100 = 1.70；合计 1.914875；1.914875/4.50 = 0.425527… = 42.55%。
- 示例 C 费：100×0.05×0.998×0.002 = 0.00998；半价差 (0.998−0.997)/2×100 = 0.05；合计 0.05998；0.05998/99.80 = 0.000601… = 0.0601%；100−99.80−0.05998 = 0.14002。
- 独立簇：Netflix 美国+全球同周合并 1，Spotify 全球+美国同周合并 1；约 2 簇/周。
- 未核实项：FlixPatrol 可用性、Netflix 官方日榜、kworb 逐日历史覆盖、Spotify 官方榜与 kworb 的口径差异、任何实际盈利。

---

## glm-5.3 事实核查报告

# Fact-check report — B07.md (quant, 周榜日更抢跑)

**Fetches:** 15 URLs re-fetched (all 6 Gamma event slugs, 2 public-search queries, kworb ×3, Tudum ×2, FlixPatrol, charts.spotify, dead-slug probe).

**Verified (spot-check of every number-bearing claim):** Netflix global event — 17 markets, `negRisk=true`, `volume=5065.164545`, `liquidity=4423.9158`, Below `["0.9975","0.0025"]`/0.997/0.998/0.001/1153.424795, `feeSchedule {1,0.05,true,0.25}`, `feeType=culture_fees` — all exact. Rule text verbatim ("Tuesday, October 20, 2026, 3:00 PM ET", "previous week (Monday to Sunday)", "English only", Oct 23 11:59 PM ET→Other). Spotify 10-16 (14 mkts, 8072.917061, BbY WOW `["1","0"]`/4383.916683) and 10-23 US (15 mkts, 8505.801068, Housewife/Kidman full quote sets) — exact. April-3 historical (22 mkts, feeSchedule null, rewards 50/4.5) ✓. kworb 2026/10/18: BbY WOW 4,719,966 & 35,919,162; Housewife 1,127,046 ✓ (byte sizes match log exactly). Tudum Global/US 10/5–10/11/26, Below, 17,000,000 / 69,300,000, `2021-06-28` ✓. FlixPatrol 403 ✓; charts.spotify 200/12650B ✓; `top-netflix-show-this-week`→`[]` ✓; four Oct-16 sibling events ✓. All fee/half-spread arithmetic (A: −0.923875; B: 42.55%; C: 0.0601%) recomputed correct; fee formula and 0.05 culture rate match GUIDE §8.

**Problems:**
1. **L2** `id: quant-XXX` — placeholder; GUIDE §7 requires id matching filename (e.g. `quant-007`). Fix before commit.
2. **L35/L173 MISMATCH** — US Netflix event `liquidity=15578.90959`; source now returns `liquidity=5938.23516` (same `volume=1834.890906`, updatedAt 04:04:56Z, 4 min after worker's snapshot). "15578" appears nowhere in current JSON. Likely transcription error, not time-variance (liquidity rarely drops 62% in minutes with unchanged volume). Fix: re-fetch and correct, or strike the figure.
3. **L37/L103 time-varying (OK)** — Spotify US `liquidity=10002.81181` now 10596.26534; acceptable, timestamp given.
4. **L12** `return_type: direction` is defensible (event outcome), but mechanism ("价格向 0/1 收敛"/面值兑付) fits `convergence`; closest analogue dot-004 uses `convergence`. Suggest reviewer ruling, not an error.
5. **Duplication:** no match in KNOWN.md (135) or other entries. Borderline vs dot-004 (confirmed-fact convergence, politics) / dot C14 (culture actual-value lag, folded into C04). Distinct key variable (daily→weekly nowcast vs confirmed fact); honestly flagged in 门槛自查#4 and quant CLAIMS.md ("区别 dot C14"). Not a hard dupe.
6. Compliance otherwise good: 来源自报 labels present, honest `backtest_count=0`, gate 5 self-declared 不满足， free keyless sources only, failure criteria pre-written.

VERDICT: FIX — every substantive number, rule quote and calculation verifies against sources except one liquidity figure and an unfilled id placeholder, both trivially correctable.

GATES_PASSING: 5/7 (1,2,3,6,7 pass — 2/6 conditionally on forward-only prices; 4 pending dedup ruling; 5 fails as entry honestly admits).
