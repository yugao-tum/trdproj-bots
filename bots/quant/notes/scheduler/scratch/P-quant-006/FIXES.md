# P-quant-006 FIXES — 2026-10-21

Entry: `bots/quant/entries/quant-006-tennis-elo-pm-pricing.md` (id `quant-006`, date `2026-10-20`, `status: 草稿` kept unchanged).
Scope read: every file under `bots/quant/notes/scheduler/reviews/`, `checks/` and `audit/` that mentions `P-quant-006` or `quant-006`:
`reviews/c20261020-1423-research.md`, `checks/I02.md`, `audit/c20261020-1423-research.md`,
`audit/c20261020-170337-research.md`, `audit/c20261021-030001-research.md`.
Only `checks/I02.md` lists entry-specific corrections for quant-006. The review/audit mentions are either family-duplication comparisons (B21/B24 vs quant-006) or confirm that the JeffSackmann 404 was already disclosed and that the entry was correctly demoted; none asks for another text change in this entry.

## Review/check items → changes → evidence

1. **`checks/I02.md` #1 (`:66`): 219 was mislabeled as "after removing doubles/winner/rank/qualifying".**
   - Changed to: "剔除 doubles 后 **atp-/wta- 比赛事件 219 个**；其中 **129 个是 2026 美网资格赛**，主赛事单打只有 **90 个**（`winner/rank` 在 slug/title 中为 0）"; also states the 900-event page is a pagination lower bound and gives 7.3/day including qualifying vs 3.0/day for main draw.
   - Evidence: `verify_sources.py` / `verify_sources.out` (2026-10-21): 9 pages × 100, 900 unique events; 267 `atp-`/`wta-`, 48 doubles, **219 non-doubles**, **129 qualifying**, **90 main-draw singles**.

2. **`checks/I02.md` #2 (`:85`): two-week count derived from the wrong 219 base.**
   - Changed to: "900 个 event 里有 219 个 atp-/wta- 比赛（含 129 个美网资格赛；主赛事 90 个）→ 两周约 42–102 场（主赛事 90×14/30≈42；含资格赛 219×14/30≈102）"; the "30 triggers unknown" conclusion is kept.
   - Evidence: same `verify_sources.out` counts; arithmetic 90×14/30=42.0 and 219×14/30=102.2.

3. **`checks/I02.md` #3 (`:35`): "16 sub-markets" was written as the universal template.**
   - Changed to: "ATP 正赛 event 可有 16 个子市场 (`atp-friend-geerts-2026-08-25` 有 16 个)；ITF 低级别 event 当前只有 3 个（胜负、completed-match、单盘胜者），模板随赛事级别变化."
   - Evidence: `verify_sources.out` — `atp-friend-geerts-2026-08-25` has 16 markets; the 2026-10-21 `closed=false` tennis snapshots show `itf-*` events with 3 markets (and `wta-gibson-krueger-2026-10-22` with 2).

4. **`checks/I02.md` #4 (`:117` and header `:21`): gate 6 was called "not met" even though the ≥30-result test had been completed and failed.**
   - Header changed to: "门槛 1、5 因此改为不满足；门 6 的检验已完成（1366 个独立结果），按预注册标准判 FAIL."
   - Gate 6 changed to: "满足（已完成历史检验并 FAIL；2026-10-20 更新，复用已合并的 q006-hist，不重跑）".
   - Evidence: `verify_backtest.out` — 2080 priced, 1366 triggered, median −0.114895 ≤ 0 → `CRITERION ... -> FAIL`. Gate 6 asks whether ≥30 independent public-data results can be obtained and a failure rule pre-registered; both are true. The economic failure stays in gate 5.

5. **`checks/I02.md` #5 (`:48` and `:94`): example 4 `endDate` was conflated with the rule's 50-50 deadline.**
   - `:48` now: "ATP 规则的 50-50 截止是 `2026-09-08 23:59 ET`（EDT，即 `2026-09-09T03:59Z`）；示例 4 的 event `endDate=2026-09-01T09:00:00Z` 是开赛后的平台归档时间（= `2026-09-01 05:00 ET`），不是该截止时刻."
   - `:94` now says the same and deletes "endDate 是开赛后约 7 天的最迟结算日".
   - Evidence: live Gamma `atp-friend-geerts-2026-08-25` description (cached `_cache/gamma_atp_friend.bin`, re-fetched 2026-10-21, HTTP 200): "…has not been determined by September 8, 2026, 11:59 PM ET (14 days after the scheduled start)…"; event field `endDate=2026-09-01T09:00:00Z`.

6. **Requested addition: historical tradable-price backtest, net of fees.**
   - The entry already carried the q006-hist result; this pass re-derived it independently from `bots/quant/notes/q006-hist/matches.csv` with `verify_backtest.py` and made the fee formula explicit in `## 证据`: `net/share = payout − entry_ask − 0.05×entry_ask×(1−entry_ask)`.
   - Evidence `verify_backtest.out`: 2166 rows, **2080 priced**, **1366 triggered**; median **−0.114895**, mean **−0.031543**, hit **642/1366**, total net **−43.088336**, notional staked **678.166047**, fees **14.422290**, per-$staked **−0.063537**. Formula check: **0/1366 fee mismatches and 0/1366 net mismatches above 2e-6** (CSV is 6-dp rounded). Sensitivity window **1379** trades, median **−0.094095**; `date_lag_days ≤ 2` **800** trades, median **−0.182217**. Zero half-spread + zero fee: median **−0.100000**, mean **−0.010985**.

7. **Source re-verification (all cited URLs, 2026-10-21).**
   - Evidence `verify_sources.py` / `verify_sources.out`:
     - `tennisabstract.com/reports/atp_elo_ratings.html` 200, 290,077 B, `Last update: 2026-10-19`, 100-pt=64% sentence present; WTA 200, 268,193 B, same update date; Sinner 2296.9 / Alcaraz 2149.8 / Hurkacz 1897.8, Siegemund 1762.3 / Yastremska 1762.2 / Chang 1355.0 / Arseneault 1266.4, Lacasse absent — all consistent.
     - `docs.polymarket.com/trading/fees` 200, formula and Sports 0.05 / maker 0 / 15% present.
     - Gamma open/event/search endpoints 200; `atp-friend-geerts-2026-08-25` volume 58047.700409, 16 markets, winner `["1","0"]`, ATP resolution source, walkover/50-50 text verbatim; WTA search returns the "officially advances to the next round" walkover clause; CS search returns the "remain open until the game has been completed" + liquipedia clause.
     - data-api trades 200 with the same `0.999 / 7050 / BUY / Siegemund` print; CLOB `prices-history` 200 `{"history":[]}`.
     - archive mirror repo 200; `atp_matches_2026.csv` 200, 300,795 B (last `tourney_date` 2026-05-25); all four JeffSackmann URLs 404.
   - Entry `## 出处` now carries the 2026-10-21 recheck line and updated byte counts for the two Elo pages.

## Files written

- `bots/quant/entries/quant-006-tennis-elo-pm-pricing.md` — edits only; filename, `id`, `date: 2026-10-20` and `status: 草稿` unchanged.
- `bots/quant/notes/scheduler/scratch/P-quant-006/`: `.gitignore` (`_cache/`), `verify_sources.py/.out`, `verify_backtest.py/.out`, `_cache/` raw responses (all files <1 MB; pagination dumps >1 MB were deleted after extracting the counts), this `FIXES.md`.

## Lint

`python3 tools/check.py lint` still exits 1 on the pre-existing `bots/muse/entries/muse-700-*.md` / `muse-701-*.md` front matter, then crashes at `tools/check.py:88` with `KeyError: 'id'`. This entry was checked separately: all 17 required fields present, `id` matches filename, `date=2026-10-20`, `status=草稿`, `name_zh` 13 chars.

## Verdict

**DROP as a tradable strategy; do not promote to `待核` in round 2.** The mechanism is clearly stated and the test is now fully documented (2080 priced matches / 1366 independent triggered results), but it loses after fees and even with fees and the 1¢ half-spread set to zero (median −0.100000/share), and Elo is worse than the market (Brier 0.216187 vs 0.196510). Gate 5 fails; gates 1 and 6 are recorded according to `checks/I02.md`. Keep `草稿` only as a negative/boundary record.
