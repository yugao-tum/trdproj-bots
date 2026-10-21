# P-quant-030 FIXES — 2026-10-21

Entry: `bots/quant/entries/quant-030-kpi-bracket-monthly-nowcast.md` (id `quant-030`, date `2026-10-20`, status kept `草稿`).
Scope read: `notes/scheduler/reviews/c20261020-170337-research.md` (B29 section; the only file with quant-030-specific corrections), `reviews/c20261020-1423-research.md`, both `audit/` files, all `checks/`. The 1423 review/audit mention quant-030 only as a distinct comparison for quant-015; `checks/` has no quant-030 item.

## Review items → changes → evidence

1. **Open-market fee counts wrong (line 103).**
   - Changed to: 2026-10-21 re-fetch of `closed=false` = 102 events / 497 markets, **464 `rate=0` (`feeType=zero_fees`), 27 `0.04`, 6 `0.05`**; the old "486×0.04, 8×0.05" is explicitly marked wrong. §成本 now says 0.04 is a conservative upper bound, not the live open-market fee.
   - Evidence: `verify_family.py` / `verify_family.out` (`OPEN ... fee rates: {0: 464, 0.04: 27, 0.05: 6}`). The review's 10-21 snapshot (484/6/4) differs because the open set drifted again; both are timestamped.

2. **TSM "first executable" was a taker SELL, not a taker BUY.**
   - Changed: table, §3(b), §成本 net example, gate 5. Entry now uses the actual taker **BUY NO @0.912887, 514.01 shares, 2026-07-13 05:32:08Z** (100 s after the 05:30:28Z page timestamp), fee 0.003181/share, 1¢ half-spread → **+0.073932/share, +$38.00, +8.1% over ~3 days**. The 06:46:29 `SELL No @0.860366` is explicitly labelled a later taker sell into a bid, not an entry.
   - Evidence: `inspect_trades.out` TSM block; `backtest.out` case [1]; TSMC page `dateModified = 2026-07-13T13:30:28+08:00` (cached `_cache/tsmc_3323.html`).

3. **Costco 0.92 NO print — review said wrong bracket / 0 trades in 6.5–7.5.**
   - Re-fetch **contradicts the review's premise**: `2026-05-22 22:38:55 BUY No @0.92, 20 shares` **is** in the `6.5%–7.5%` market (conditionId `0xccbb7ca2…`, 11 trades, Gamma volume 620.53). The same wallet (`0xd1a63a24…`) bought NO in all six brackets at 22:38:53–22:38:55, i.e. a basket, and the 0.92 also appears in `<4.5%`.
   - Therefore I did **not** move it to `<4.5%`; instead I removed the "80–90¢ gap" framing: it is a **taker BUY NO inside a multi-bracket basket**, not an executable YES ask. Costco stays an excluded observation; the first `BUY Yes` in that bracket is 05-28 20:15:05 @0.88, after the earnings release.
   - Evidence: `inspect_trades.out` Costco block; per-bracket trade files in `_cache/`; wallet/timestamp cross-check printed from all six `trades_<conditionId>.json`.

4. **UAL trade date off by one day.**
   - Changed both occurrences to **2026-07-01 09:09:52** (`BUY Yes 50 @0.07`, 83–84 market).
   - Evidence: `inspect_trades.out` UAL block; data-api cached trade.

5. **Announcement timestamps assumed.**
   - TSM: replaced "公告时刻未取到 / 06:00 分界" with the sourced `dateModified` 05:30:28Z and the 05:32:08 trade.
   - Boeing: now says the page gives only `April 14, 2026` (no hour), so 18:26/18:27 can only prove "same day", not non-look-ahead.
   - Evidence: `_cache/tsmc_3323.html`, `_cache/boeing.html`; `inspect_trades.out`.

6. **Open volume stats stale/time-varying.**
   - Kept the 2026-10-20 numbers but labelled them as a snapshot and added the 2026-10-21 re-fetch: closed sum $4,703,475 / median $8,353; open sum $1,682,295 / median $3,850 / p90 $7,410. Closed event count updated 192/931 → 196/951 (10-21), open 102/494 → 102/497.
   - Evidence: `verify_family.out`.

7. **Gates 5 and 6 not met.**
   - Gate 5 rewritten: **strict rule-in n=0**; TSM above-41 fails the pre-registered "nowcast ≥2% from threshold" test (40.20 vs 41 = **1.95%**) and the monthly-TWD/quarterly-USD caliber is borderline. Relaxing the distance to 1.9% leaves n=1 (+8.1%/3 days, ~$469 capital).
   - Gate 6 unchanged in verdict (n=5 historical, 2–4/quarter forward; strict rule-in 0).
   - Verdict made explicit in the header and §3: **as a tradable strategy this should be dropped; do not promote to `待核` in round 2. Keep `草稿` as a boundary note only.**

## New: historical tradable-price backtest, net of fees

- Script/output: `backtest.py` / `backtest.out`.
- Method: actual data-api **taker prints** (not daily close, not mid, not the opposite resting quote), fee = `p × 0.04 × (1−p)` per GUIDE §8, net = `settlement − entry − fee − half-spread`; 1¢ base, 3¢/5¢ stress.
- Results:
  - TSM above-41 NO: 05:32:08 @0.912887, 514.01 sh → fee 0.003181, net +0.073932/sh, **+$38.00 (+8.1%)**; borderline (1.95% < 2%).
  - TSM above-40 YES: 05:31:55 @0.934495, 721.54 sh → net +0.053057/sh, +$38.28; excluded (0.5% distance).
  - Boeing above-140 YES: 18:27:46 @0.98, 29 sh → +$0.27 at 1¢, negative at 3¢; excluded (quarterly, no release time).
  - Costco 6.5–7.5 YES: no pre-earnings YES ask; post-release @0.88 → +$1.19 (upper bound only); excluded.
  - DAL 83–85 YES: 07-02 @0.238136, 37.55 sh → +$27.96 (+312.7%); excluded (37.55 < 50 sh, BTS time unverified).
  - UAL `<83` naive: no matching YES print around 07-01; counterexample only.
- Conclusion: strict rule-in **0 trades**; the one near-miss is tiny and fails a pre-registered filter. No claim of positive EV is made.

## Files written

- `bots/quant/entries/quant-030-kpi-bracket-monthly-nowcast.md` (edits only; id/date/status unchanged).
- `bots/quant/notes/scheduler/scratch/P-quant-030/`: `.gitignore` (`_cache/`), `verify_family.py/.out`, `verify_cases.py/.out`, `inspect_trades.py/.out`, `backtest.py/.out`, `_cache/` raw JSON/HTML, this `FIXES.md`. The two Gamma family dumps and the DAL 8-K were >1 MB, so they are stored gzipped (389 KB / 224 KB / 78 KB); the scripts re-download plain JSON if the `.gz` is not expanded.

## Verdict

Drop as a strategy (0 rule-in trades, capacity $9–$469/fill, gates 5/6 fail). Retain only as a `草稿` boundary/negative note; do **not** promote to `待核`.
