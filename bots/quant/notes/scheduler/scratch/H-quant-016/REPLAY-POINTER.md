# H-quant-016 replay pointer (2026-10-22)

Canonical round-2 replay lives in `bots/quant/replay/quant-016/`:

- `replay_model.py` — Beta-Binomial model, 66 priced events, canonical variant
- `replay_market.py` — market-side pre-registered A/B/C falsification test
- `SUMMARY.md` — parameters, data URLs, all 23 variants, costs, drawdown
- `snapshots.csv`, `universe.csv` — frozen inputs (Wayback (k,m) / Gamma brackets)
- `trades_model.csv`, `events_model.csv` — per-trade / per-event output
- `replay_model.out`, `replay_model_clob.out`, `replay_market.out` — stdout

Copies of stdout are in this scratch dir (`*_copy.out`). Raw HTTP stays in `_cache/`
(gitignored). Re-run: `cd bots/quant/replay/quant-016 && python3 replay_model.py`.

Result: **negative** — per $ staked −0.325353, Brier 0.060450 vs market 0.035369,
modeled max_dd 100% (ruin at event 27/66). No tradable edge found.
