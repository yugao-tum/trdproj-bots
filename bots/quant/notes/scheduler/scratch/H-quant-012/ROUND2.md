# H-quant-012 — round-2 canonical replay (2026-10-21)

The canonical, runnable replay now lives in `bots/quant/replay/quant-012/`
(it was moved there per the round-2 deliverable rule). This scratch directory
keeps the earlier round-1 hardening scripts and stdout:

- `analyze_merged.py` / `analyze_merged_output.txt` — out-of-sample split and fee-0
  sensitivity on the pre-window price convention.
- `maker_proxy.py` / `maker_proxy_output.txt` — maker fill proxy and the 81/103
  crossing check (still quoted in `replay/quant-012/SUMMARY.md` variants 8-9).
- `verify_sources.py` / `verify_sources_output.txt` — round-1 source re-check.
- `REPORT.md` — round-1 report.

2026-10-22 additions (round-2 hardening):

- `verify_entry_urls.py` / `verify_entry_urls_output.txt` — extracts all 18
  unique URLs from the entry's 出处 section (templates replaced with the
  concrete examples used), all HTTP 200, and re-checks the USGS/Gamma/CLOB/
  data-api numbers; also checks every cited local evidence path exists.
- `bots/quant/replay/quant-012/mtm.py` / `mtm_output.txt` /
  `equity_mtm.csv` — daily mark-to-market drawdown including floating PnL:
  21.61% (347.59 USDT, trough 2026-08-24) vs 21.53% realised.
- Canonical replay re-ran on 2026-10-22: same 183 fills / 65 events / 40 strict
  groups, +4.94% fee 0.05. USGS revised `august-17-august-23` M5.5+ count
  14 -> 13, so own-count match is now 58/68 (M5.5+ 18/28, was 19/28);
  headline PnL unchanged.

Round-2 canonical replay and outputs (moved, not duplicated here):

- `bots/quant/replay/quant-012/replay.py` + `run_output.txt`
- `bots/quant/replay/quant-012/analysis.py` + `analysis_output.txt`
- `bots/quant/replay/quant-012/verify_sources.py` + `verify_output.txt`
- `bots/quant/replay/quant-012/trades.csv` / `events.csv` / `equity.csv`
- `bots/quant/replay/quant-012/SUMMARY.md`

Headline (fee 0.05, 1 share per bracket, first data-api print at/after window start):
183 fills / 65 events / 40 strict groups, +4.94% of notional, event-clustered
bootstrap 95% CI [-0.0036, +0.0836]; out-of-time (fill >= 2026-07-01) -0.10%;
capacity portfolio (1,000 USDT sleeve) +3.54%, max drawdown 21.5% (daily,
realised), annualised contribution on 5,000 USDT +8.50%. Verdict: 不显著;
recommend demotion at review. Exact stdout: `replay/quant-012/run_output.txt`.
