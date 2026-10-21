# P-quant-003 verification run (2026-10-21, worker w04)

Purpose: independently re-run the canonical round-2 replay for `quant-003` from a
clean cache and re-verify every cited source. The canonical, runnable replay stays
in `bots/quant/replay/quant-003/` (scripts, parameters, `SUMMARY.md`). This
directory holds the verification scripts, their stdout and the run's CSV products.

## Commands

```bash
cd bots/quant/notes/scheduler/scratch/P-quant-003
python3 replay_quant003.py --cache ./_cache > verify_replay.stdout.txt 2>&1
python3 diagnose_replay.py > diagnostics.stdout.txt 2>&1
python3 source_check.py > source_check_verify.txt 2>&1
sha256sum results_*.csv equity_curve.csv k6_weights.csv \
  ../../../../replay/quant-003/results_*.csv \
  ../../../../replay/quant-003/equity_curve.csv \
  ../../../../replay/quant-003/k6_weights.csv > sha256_compare.txt
```

`replay_quant003.py`, `diagnose_replay.py` and `fetch_data.py` are byte-identical
copies of the canonical scripts in `bots/quant/replay/quant-003/`. Raw monthly
zip downloads live in `_cache/` (git-ignored); no binary enters the repo.

## Result of the independent re-run

- Common panel 2022-01-01..2024-12-31, 1,096 daily bars; 1,095 open-to-open returns.
- Clean-cache outputs are byte-identical to the committed replay products
  (`sha256_compare.txt`; four `IDENTICAL` diffs).
- GATE k=6: net +61.82%, CAGR +17.40%, max drawdown -20.01% (daily), Sharpe 0.92,
  average exposure 0.19; 44 risk-off segments in 1,036 valid days.
- B1 plain 30d tsmom basket: +88.73%, CAGR +23.58%, MDD -23.86%, Sharpe 0.99.
- GATE k=6 wins on fold Sharpe in only 1/3 folds; daily difference -6.24%/yr,
  t = -0.68, corr 0.762; compound gap -26.92 pp.
- `result: 正` is the absolute net return; the pre-registered superiority test
  fails, so the entry recommends **DROP** and keeps the result as counter-evidence.

## Source re-check

All seven cited URLs returned HTTP 200 on 2026-10-21 (`source_check_verify.txt`):
the two listing pages plus six example monthly klines files (BTC 2022-01 /
2024-12, GRT 2022-01, XLM 2024-12, ADA 2023-06). Local cache bounds are
2022-01-01..2024-12-31 for all ten symbols; zero files outside the allowed
window. No 2021-or-earlier and no 2025-or-later data were downloaded or read.
