# B21 — NFL moneyline: public Elo vs Polymarket pregame price

Run date: 2026-10-20 (UTC). No keys, no accounts, read-only public GETs.

## Final pipeline

Run `./run_all.sh` from this directory to reproduce the full pipeline (it downloads
`_cache/games.csv` and the Gamma event list first). Individual steps:

1. `fetch_pregame_nflkick.py` — reads `_cache/nfl_events_all.json`, takes the 805 NFL game
   events, maps each slug to the nflverse kickoff (`kick_map.json`), and calls
   `data-api.polymarket.com/trades?market=<conditionId>&limit=60&end=<kick-3600>`.
   Output: `pregame_quotes.json`.
2. `match_elo2.py` — computes Elo from nflverse `games.csv` (2010+, K=20, HFA=55,
   season regression 2/3, margin multiplier 1+ln(mov)), matches Polymarket games to
   nflverse by unordered team pair and date ±1 day. Output: `matched2.pkl`.
3. `summary4.py` — deduplicates outcomes, writes `games_final.csv`,
   `elo_final_trades.csv` (actual fees), `elo_final_trades_uniform3.csv` (3% stress),
   and `summary4.stdout.txt`.

Old `matched.pkl`, `summary2.*`, `summary3.*`, `games_638.csv`, `games_657.csv` are
from an earlier 657-game pass that anchored T−60 on Polymarket `startTime`; they are
kept only as exploratory history. Final numbers are the 654-game pass in `summary4`.

## Final result (654 games, 2024-09-05..2026-10-20)

- Brier: Elo 0.21868, PM 0.20932, Vegas 0.20909.
- Elo rule, edge >= 2c, actual fees: 462 trades, +1.76c/share, ROI +2.23%,
  bootstrap 95% CI [-2.31c, +5.85c].
- Fee-bearing 2026 subset (44 games, rate 0.03/0.05): 30 trades, -3.65c/share,
  ROI -3.40%, total -1.09.
- Uniform 3% stress: 440 trades, +0.52c/share, ROI -1.02%.

Verdict: the pre-registered rule fails; no deployable edge. See the entry
`bots/quant/entries/quant-024-nfl-moneyline-elo-vs-price.md`.
