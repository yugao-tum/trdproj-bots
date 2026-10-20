# Independent lagged-SMA200 completion supplement

This additive check closes the previously missing frozen BTC lagged-SMA200 gross benchmark comparison. It does not replace or modify the sealed main replay or its code-only distribution. No raw datasets are included here.

## Local reproduction

Use the previously supplied code-only reproduction distribution and separately held declared market inputs. With Python3.9+ standard library:

    python verify_sma.py --core /local/code-only/reproduce.py --inputs /local/code-only/sources --warmup /local/spot_daily.csv --out /local/supplement-results

The inputs directory must have the original inputs.json in its parent. The core reproduction code and warmup hashes are checked against source-hashes.json. All eight original source hashes are then checked by the core replay. This supplement generates the cash paths afresh in a temporary directory; it does not ingest role09 derived results. compare_supplement.py reads role09 correlation and endpoint outputs only for the final independent comparison. To repeat that check, supply --reference /local/role09/sma200-supplement. Run python test_sma.py beside the generated compact tables and comparison.json.

Additional declared input: spot_daily.csv, SHA-256 a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a. This is previously frozen public Binance spot history, including2023 warmup. Public endpoint family: https://api.binance.com/api/v3/klines. Relevant columns are symbol,open_time_utc,close. Preserve the full original file for byte verification; the code reads only BTCUSDT closes and overlays the original declared main/extension Binance daily close data for2024 onward. This is provenance/schema guidance, not a data download. Exact historical bytes are not guaranteed through future acquisition, normalization or provider revisions. Public code requires separately supplied declared raw files; never commit them or hide them inside ZIP.

## Frozen definitions and findings

Signal for day t is prior close strictly greater than the arithmetic mean of the prior200 closes. Current close never enters the signal. Benchmark daily gross return is that signal times BTC close-to-close return. Start capital5000;2500 is denominator sensitivity only. This gross benchmark omits transaction costs and is not a costed executable trading recommendation.

All36 cases ×2endpoint views ×2capital bases ×2frequencies produce288 correlations. September standalone ends at its hypothetical exit cash. October continuation keeps September unliquidated mark NAV and charges its hypothetical exit only at October19. All33 complete months remain; October's19-day partial return is separate, not a34th full month. No fitting, asset selection, correlation cutoff or GUIDE pass is introduced.

All288 independent correlations reconcile to role09 within1.085e-13. Benchmark endpoint PnL differs by at most6.37e-12 USDT from floating-point presentation; partial-October returns agree within1.05e-15. Gross benchmark PnL on5000 is4340.449748 at September30 and4152.219082 at October19. The partial October benchmark return is−2.015221%. These results are descriptive, dependent observations, not independent strategy outcomes.

The eight failed BTC/SOL B paths retain counterfactual labels in all64 associated correlation rows and both endpoint views. Other paths remain conditional, not survival-certified. Positive whole-window returns and low daily correlation do not erase failed local cash paths. No official score, new mechanism, investment-OOS or historical MMR certification is claimed.
