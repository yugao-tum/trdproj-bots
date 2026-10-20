# B24 — Cricsheet T20 ratings vs Polymarket (quant-027)

Entry: `bots/quant/entries/quant-027-cricsheet-t20-pm-ratings.md`

## Reproduce (from this directory)

Raw inputs are large and live outside the repo:

- Cricsheet: `t20s_male_json.zip` (14,479,929 B) and `ipl_json.zip` (5,187,770 B), unzipped to
  `/tmp/opencode/cricsheet/t20m/` and `/tmp/opencode/cricsheet/ipl/`.
- Polymarket data-api trades: `/tmp/opencode/trades/<conditionId>.json` (~102 MB total).
- Gamma snapshots: `/tmp/opencode/cricket_events.json`, `/tmp/opencode/cand2.json`,
  `/tmp/opencode/matched.json`, `/tmp/opencode/price_raw.json`.

Pipeline:

```
python3 parse_cricsheet.py      # -> matches.csv (4,870 male matches)
python3 build_ratings.py       # -> ratings.csv, calib.json (pre-2024 Elo)
python3 ballstats.py           # -> ballstats.csv (delivery-level run rates)
python3 model.py               # -> model_out.csv, model_coef.json
python3 match_pm.py            # -> /tmp/opencode/matched.json (team+date matching)
python3 fetch_prices.py        # -> /tmp/opencode/price_raw.json (cached data-api trades)
python3 evaluate.py            # -> priced.csv, bets_1c.csv, evaluate.log
python3 final_test.py          # -> clean_matches.csv, bets_final_1c.csv, final_test.log
python3 report_numbers.py      # -> numbers.log
python3 verify_rules.py        # -> rules.json, verify_rules.log
```

`evaluate.py` is a diagnostic on all 203 decisive matches (two-sided rule, 276 bets); the
pre-registered one-side rule and the clean 198-match sample are in `final_test.py`.

`_cache/` is gitignored. No raw data is committed; all derived CSVs here are <1 MB.

## Headline result

198 clean independent matches (T20I 131 + IPL 67), 2024-06-11..2026-03-24.
Pre-registered rule: one side/match, model edge >=5c, last pre-match trade +1c half-spread,
0.05 taker fee. Result: 117 bets, mean net **-0.0414/share** (total -4.85), win 29.9%.
Model log loss 0.6553 vs market 0.5107. Verdict: FAIL (no edge; gate 5 not met).

Post-hoc (not pre-registered, not an edge claim): market price 0.35–0.65 subset +0.0258/share
(39 bets), favorite-only subset +0.0717/share (23 bets); both unstable by year/league.
