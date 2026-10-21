# P-quant-017 round-2 preparation report

Entry: `bots/quant/entries/quant-017-app-store-rank-markets.md`
Date/status kept: `date: 2026-10-20`, `status: 草稿`, `id: quant-017`, filename unchanged.
All work free/keyless; no trading, wallets, accounts or keys.

## What was added

1. **Closed the CHECK list** in `notes/scheduler/checks/quant-017.md`:
   - `#1` board candidate list now `Vinted / Muse / ChatGPT / TikTok Pro / Claude / Google Gemini / KICK` (McDonald's only on `#2`).
   - Rank-persistence headline replaced with the **full sample** from
     `notes/r2prep-verification/quant-017.md` §2.1:
     pre-registered `P1=53/60=88.33%` (CI 77.8–94.2%), `P2=17/23=73.91%`;
     widened `P1=71/79=89.87%` (CI 81.3–94.8%), `P2=25/34=73.53%`.
   - EV unit fixed (`−2.1%`, not `−1.8%`); CLOB point range `62–711`.
   - Gate 4 marked `不满足/待主审` (same fixed-time public-leaderboard mechanism as quant-007).
2. **New historical tradable-price backtest** (`fetch_bt_data.py`, `backtest_017.py`):
   - CLOB `prices-history` 10-minute last-trade series for the only 8 closed free
     `#1`/`#2` boards with history (2026-09-25, 10-02, 10-09, 10-16), 43 market series.
   - Fee `0.05` from the closed-market `feeSchedule`; half-spread assumed 0/0.5/1.5¢.
   - Price-only proxy for the chart filter (Wayback has no 2026 snapshots).
   - Results (T−60, 1.5¢ half-spread, no filter): 8 trades, 6 wins, mean **−1.04¢/share**, total **−8.33¢**.
     T−30: mean −1.39¢, total −11.11¢. T−10: mean +0.30¢, total +2.38¢.
   - Strict proxy (`p≥0.90` and `cost≤0.98`): only 2–3 trades, total +5.43¢ to +9.55¢ — too small to prove anything.
   - Two big losses are `Other` wins, which the real rule cannot hedge and the chart filter is meant to skip.
3. **Source re-check** (`verify_live.py`, 2026-10-21): RSS and charts page agree on the first 12 names;
   on the Oct-23 boards all 14 real candidate arms now report `feeType=zero_fees` / `rate=0`
   (on 2026-10-20 they were `culture_fees` / `0.05`; the 4 `Reserved` + `Other` placeholder arms
   still report `culture_fees` / `0.05`). `umaBond/umaReward` are `None` today (a 2026-10-20 note
   recorded 500/5). The entry reports both, and the backtest keeps the conservative 0.05 fee.

## Verdict on the 7 gates

| Gate | Verdict |
|---|---|
| 1 mechanism clear | PASS |
| 2 free data | PARTIAL (return-side history = 4 independent dates) |
| 3 small capital | PASS (200/600 USDT; book 125.76–1,056.54 USDC/arm) |
| 4 not duplicate | FAIL/待主审 (variant of quant-007) |
| 5 cost-adjusted | FAIL (no usable positive proof; 4-date backtest inconclusive) |
| 6 two-week test | FAIL (2–3 independent results vs 30) |
| 7 sources | PASS |

Unambiguous passes: **1, 3, 7 = 3/7**; gate 2 partial; 4/5/6 not met.

## Plain verdict

**Do not submit this as a 收录 candidate.** It is a variant of quant-007 with no proven edge.
As a supplement it can stay in 待选区; if the integrator applies the seven gates strictly,
the entry should be returned/dropped rather than promoted.

## Files in this directory

- `fetch_bt_data.py` / `fetch_bt_data.stdout.txt` — event + CLOB series fetch.
- `backtest_017.py` / `backtest_017.stdout.txt` — backtest (reads `_cache/`, no network).
- `recompute_ev.py` / `recompute_ev.stdout.txt` — full-sample persistence and EV tables.
- `verify_live.py` / `verify_live.stdout.txt` — 2026-10-21 source re-check.
- `_cache/` — raw JSON, git-ignored (`.gitignore` contains `_cache/`).
