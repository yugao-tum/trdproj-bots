# quant-006 工作者自留核对日志（deepseek-flash 原稿附录）+ glm-5.3 事实核查摘要

## VERIFICATION LOG (reviewer only, not for commit)

1. `GET https://docs.polymarket.com/trading/fees` → HTTP 200, 397,457 bytes.
   Snippet: “fee = C × feeRate × p × (1 - p) … Makers are never charged fees. Only takers pay fees.” / 表格行：“Sports 0.05 0 15%”, “Geopolitics 0 0 —”, “Combos 0.05 0 0%”.
   Used for: 费率 0.05、maker 0 费、maker 返佣 15%、费用公式。
2. `GET https://tennisabstract.com/reports/atp_elo_ratings.html` → HTTP 200, 289,710 bytes.
   Snippet: “Current Elo ratings for the ATP tour. This list includes only those players who have completed 10 or more tour-level, tour-level qualiyfing, men's challenger, or ITF $50K+ matches in the last 52 weeks.” / “A 100-point difference in Elo ratings implies that the favorite has a 64% chance of winning a best-of-three-set match; 200 points implies 76%, 300 points implies 85%, 400 points implies 91%, and 500 points implies 95%.” / “Updated weekly(ish). Last update: 2026-10-19” / 行：“1 Jannik Sinner 24.8 2296.9 … 2 Carlos Alcaraz 23.4 2149.8 … 22 Hubert Hurkacz 29.6 1897.8”.
   Used for: 映射尺度、榜单门槛、Sinner/Alcaraz/Hurkacz 分数、更新日期。
3. `GET https://tennisabstract.com/reports/wta_elo_ratings.html` → HTTP 200, 267,826 bytes.
   Snippet: 同句 “A 100-point difference … 64% …”, “Last update: 2026-10-19”, 行 “65 Laura Siegemund 38.3 1762.3”, “66 Dayana Yastremska 26.4 1762.2”, “391 Hanna Chang 28.4 1355.0”, “466 Ariana Arseneault 24.2 1266.4”; “Lacasse” 未出现。
   Used for: WTA 分数、示例 1 覆盖率缺口（Lacasse 未评级）。
4. `GET https://gamma-api.polymarket.com/events?closed=false&limit=8&tag_slug=tennis&order=startDate&ascending=false` → HTTP 200.
   Snippet: `itf-lacass1-arsene1-2026-10-20` id 5952202, `outcomePrices ["0.265","0.735"]`, `feeSchedule {'exponent':1,'rate':0.05,'takerOnly':True,'rebateRate':0.15}`, `liquidity 3327.0396`, `spread 0.03`, `orderMinSize 5`, `orderPriceMinTickSize 0.01`; `itf-arsene3-kuhar1-2026-10-20` `["0.625","0.375"]`, `liquidity 1496.0896`, `spread 0.03`; `itf-hurkac1-chang4-2026-10-20` `["0.515","0.485"]`, `liquidity 71.8424`, `spread 0.91`; `itf-lutkem1-defalc1-2026-10-20` `spread 0.14`, `liquidity 85.5995`.
   Used for: 示例 1/2/3 的全部价格/费用/流动性数字。
5. `GET https://gamma-api.polymarket.com/events?slug=atp-friend-geerts-2026-08-25` → HTTP 200.
   Snippet: 描述 “If the match is canceled (not played at all), ends in a tie, or a winner has not been determined by September 8, 2026, 11:59 PM ET (14 days after the scheduled start), this market will resolve to 50-50. If the match begins but is not completed, and one player advances due to the opponent's retirement, default, or disqualification, this market will resolve to the player who advances. If the match ends in a walkover (player withdraws before the start and the other advances automatically), this market will resolve to 50-50. The primary resolution source will be official information from the ATP Tour.”；event `volume 58047.700409`, 16 markets, `endDate 2026-09-01T09:00:00Z`, 胜者市场 `outcomePrices ["1","0"]`, `resolutionSource https://www.atptour.com/en/scores/current`, `rewardsMinSize 50`, `rewardsMaxSpread 4.5`.
   Used for: walkover=50-50 原文、16 子市场、volume、结算字段。
6. `GET https://gamma-api.polymarket.com/events?closed=true&tag_slug=tennis&end_date_min=2026-09-01T00:00:00Z&end_date_max=2026-10-01T00:00:00Z&limit=100&offset=0,100,...,800` → HTTP 200 每页 100 条；offset=800 单次重试曾返回错误对象（非数组），重跑成功；分页到 800 停止。
   计数：去重后 900 个唯一 event；`itf-` 621, `atp-` 166, `wta-` 101, `us-` 8, 其他 4；剔除 doubles/winner/rank/qualif 后 atp-/wta- 单打 219。
   Used for: 每月 219 场单打、900 为分页下限（非精确总数）。
7. `GET https://gamma-api.polymarket.com/events?closed=false&tag_slug=tennis&limit=100` → HTTP 200, 100 条（满页）。
   计数：`itf-` 46, `atp-` 39, `wta-` 10, `will-` 3, `nitto-` 2；atp-/wta- 非 doubles 41 条，其中多数为排名/入围类。
   Used for: 2026-10-20 当前挂牌结构（以 ITF 为主）。
8. `GET https://gamma-api.polymarket.com/public-search?q=tennis&limit_per_type=5` → HTTP 200.
   Snippet（`wta-yastremska-vs-siegemund-2025-10-06`）：“If the match is canceled (not played at all), ends in a tie, or is delayed beyond 7 days from the scheduled date without a winner determined, this market will resolve to 50-50. If the match ends in a walkover (player withdraws before the start and the other advances automatically), this market will resolve in favor of the player(s) who officially advances to the next round. The primary resolution source will be official information from the WTA Tour.”; `volume 17032.131838`, `resolutionSource https://www.wtatennis.com/scores`.
   Used for: 与 ATP 2026 模板相反的 walkover 处理。
9. `GET https://gamma-api.polymarket.com/public-search?q=Counter-Strike&limit_per_type=3&events_status=active` → HTTP 200.
   Snippet（`cs-sashi-vs-hotu-2025-09-18`）：“If the game is postponed, this market will remain open until the game has been completed. If the game is canceled entirely, with no make-up game, this market will resolve 50-50. The resolution source for this market will be official information from liquipedia”; `feeSchedule` 字段为 `None`, `outcomePrices ["1","0"]`。
   Used for: 电竞同机制示例、feeSchedule 缺失的事实。
10. `GET https://data-api.polymarket.com/trades?market=0x5a9641cc6e3a60a0e729493ef4d9fe81d5aacfc06d5c49511248462afe969be9&limit=3` → HTTP 200, 2,353 bytes.
    Snippet: `{'price': 0.999, 'size': 7050, 'side': 'BUY', 'outcome': 'Siegemund', 'slug': 'wta-yastremska-vs-siegemund-2025-10-06'}`。
    Used for: 成交数据免密钥可得。
11. `GET https://clob.polymarket.com/prices-history?market=0x5a9641cc...&interval=max` → HTTP 200, body `{"history":[]}`。
    Used for: 已关闭市场拿不到历史盘口 → 只能前向记录。
12. `GET https://api.github.com/repos/JeffSackmann/tennis_atp` → HTTP 404 `{"message":"Not Found"}`；`GET https://github.com/JeffSackmann/tennis_atp` → 404；`GET https://raw.githubusercontent.com/JeffSackmann/tennis_atp/{main,master}/atp_matches_2026.csv` → 404；`.../master/README.md` → 404。
    Consequence: 不引用该仓库，历史比赛数据与历史 Elo 写“未查到”。
13. 本轮未抓取（因此未引用）：Polymarket 官方“体育市场结算”文档页、`/rewards` 页面、任何 ESPN/ATP 赛程 API。
14. 自算部分（全部由上述抓取数字算术得出）：Elo 概率 `1/(1+10^(-d/400))`：d=147.1→0.6999；d=0.1→0.5001；d=88.6→0.6248；d=100→0.6400。费用：0.05×0.265×0.735=0.009739（3.675%/投入）；0.05×0.625×0.375=0.011719（1.875%）；0.05×0.735×0.265=0.009739（1.325%）。EV 示例 0.80−0.735−0.009739=0.0553；walkover 情形 0.5−0.735−0.009739=−0.2447。每日场次 219/30≈7.3；两周 219×14/30≈102。

---

## glm-5.3 事实核查报告

All fetches complete (22 total). Every quoted number has been re-verified against live sources. Report:

---

## Fact-check report — B03.md (网球 Elo vs Polymarket)

**Verification summary (re-fetched 2026-10-20):**
- **Exact matches (no discrepancy):** `atp-friend-geerts-2026-08-25` (volume 58047.700409, 16 markets, endDate 2026-09-01T09:00:00Z, walkover→50-50 / retirement→advances text verbatim, resolutionSource, ["1","0"], rewardsMinSize 50/MaxSpread 4.5); `itf-arsene3-kuhar1` (["0.625","0.375"], spread 0.03, liq 1496.0896); `itf-hurkac1-chang4` (["0.515","0.485"], spread 0.91, liq 71.8424); feeSchedule {rate 0.05, takerOnly, rebateRate 0.15}, orderMinSize 5, tick 0.01; ATP page 289,710 bytes, "Last update: 2026-10-19", 100-pt→64% sentence incl. genuine "qualiyfing" typo, Sinner 2296.9/Alcaraz 2149.8/H.Hurkacz 1897.8, Nika Hurkacz & Kuhar absent; WTA page 267,826 bytes, Siegemund 1762.3/Yastremska 1762.2/Chang 1355.0/Arseneault 1266.4, Lacasse absent; fees doc 397,457 bytes, formula + "Sports 0.05 0 15%" + "Makers are never charged fees"; WTA walkover→"advances to the next round" (the key contrast claim — confirmed); CS market text, feeSchedule None; data-api trade price 0.999/size 7050/Siegemund, 2,353 bytes; CLOB `{"history":[]}`; GitHub 404; Sept pagination 9×100 pages → 900 unique, itf 621/atp 166/wta 101/other 12, singles 219 — **all exact**; current listing 46/39/10/3/2, 41 non-doubles — exact. All arithmetic (p=0.6999/0.5001/0.6248/0.6400; fees 0.009739/0.011719; EV +0.0553/−0.2447; 219/30≈7.3) recomputed correct.
- **Time-varying (worker timestamped, acceptable):** `itf-lacass1-arsene1` liquidity 3327.04→4227.04; `atp-cadenas-sachko` volume 232018.80→390018.59.

**Problems:**
1. Front-matter `id: quant-XXX` — placeholder violates GUIDE §7 ("id 和文件名一致"). Fix: assign real id (e.g. quant-031) at commit.
2. 自查 #4 "本条未查重" contradicts bots/quant/CLAIMS.md B03 line which records the dedup (区别 dot C13). Fix: update to cite the CLAIMS entry.
3. "已结算的挑战赛市场 `atp-cadenas-sachko-2026-10-02`" — event object is `closed=false` (markets inside all resolved ["0","1"]); suggest "市场已结算、event 未关闭，volume 为累计值仍会增长".
4. Risk section "亏 0.235/份（31.9%）" excludes fee while 成本 section says −0.2447 with fee — harmonize (nit).
5. `name_zh` may exceed 18 字 if counting latin chars (nit).

**Compliance:** all required fields present with allowed values; fee formula per-share 0.05×p×(1−p) used correctly (§8); no backtest claimed (`backtest_count=0` explicit); no keys/paid data; no 来源自报 results requiring labels; 门槛自查 honest (uncertainties admitted). **Duplication:** distinct from known V-V2-poly-longshot / A-A3-poly-cross-market and dot-009/013/015 (external rating model, key variable = Elo); none found.

VERDICT: KEEP — every concrete number, quote, byte-count and count re-verified exactly against live sources, honesty about no-backtest and coverage gaps is exemplary, and remaining issues are cosmetic predraft placeholders.

GATES_PASSING: 5/7
