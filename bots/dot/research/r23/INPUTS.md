# Reproduction inputs and acquisition

Python 3 standard library only. From this package run:

    python reproduce.py --root /path/to/research-root --out .
    python -m unittest test_reproduce.py

No absolute machine path is required by code. `--root` must contain the relative paths listed in source-hashes.json. Raw market inputs are intentionally NOT redistributed. The optional test command checks the packaged aggregate; running reproduce first additionally validates original observations and frozen endpoints.

Inputs:
- workers/data-probe/data/history/spot_daily.csv: original retained public spot daily observation export; OHLC, symbol and raw epoch. 2025+ spot raw epochs may be microseconds; code normalizes only when >10^14. This is the source CSV, not a fresh raw response or proof of executable spot fills.
- continuation-20261020/workers/r20-proposal/04-prices/raw/{BTCUSDT,ETHUSDT,SOLUSDT}-{mark,perp}.json: retained Binance public connector response wrappers. Mark method get_futures_usds_mark_price_kline_candlestick_data; perpetual-trade method get_futures_usds_kline_candlestick_data. Each symbol: interval 1d, startTime 1704067200000, endTime 1790812799999, limit1500. Wrapper stores response.structuredContent.result. Perp OHLC is used for frozen entry/exit proxy only, never as mark high.
- continuation-20261020/workers/r20-proposal/01-funding/raw/{symbol}-page*.json: retained public funding history responses in structured_response.result, with fundingTime, fundingRate and markPrice. Original requests, page boundaries and retrieval metadata are retained in each wrapper. Window is the same; paginate without inventing events. Preserve exact milliseconds; exclude fundingTime equal to entry under the frozen convention. No USER_DATA/leverageBracket/account endpoint is needed.
- continuation-20261020/workers/r23-proposal/05-minute-data/output/raw-mark1m-tool.json: public mark kline method, ETHUSDT, interval1m, startTime1755993600000, endTime1756079999999, limit1500. Raw response includes text content and structuredContent; both are independently compared.
- continuation-20261020/workers/r20-proposal/05-ledger/output/ledger-results.json: read only as frozen expected endpoint output after independently calculating the endpoint; no parameters are read from its scenario results, no old code is imported.

For byte-identical verification use the retained original captures whose hashes are listed. A new public download may have different serialization or revised observations and will not necessarily match hashes. Public source service restrictions, terms and rate limits still apply. This package does not authorize bypassing denials or guarantee future data availability. Local hashes are not official archive signatures. All official explanatory links and historical-version limits are in REPORT.md.
