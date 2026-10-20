# B22 scratch — SPC tornado-risk daily markets

All data keyless. `_cache/` is gitignored and can be deleted/rebuilt.

## Pipeline

```bash
python3 fetch_outlooks.py   # Gamma events -> _cache/events_meta.json; SPC archive -> _cache/geojson/
python3 fetch_headers.py    # HTTP Last-Modified of each archived GeoJSON -> _cache/last_modified.csv
python3 classify.py         # point-in-polygon for final/2000/1630 -> _cache/classified.json
python3 fetch_trades.py     # data-api trades for 1,550 conditionIds -> _cache/trades/
python3 reproduce.py        # numbers cited in quant-025 -> reproduce.out
```

Supporting (not required for the cited numbers): `analyze_trades.py`, `open_calib.py`, `first_trade_scan.py`, `threshold_scan.py`, `primary_yes_rule.py`.

## Key outputs (`reproduce.out`)

- 62 daily events, 1,550 city markets, 10,674 executed trades.
- Archived 0100Z SPC tornado polygons vs Gamma settlements: **0 / 1,550 mismatches**.
- 1630Z vs 2000Z classifications: identical (0 flips); 2000Z -> 0100Z: 5 True->False, 0 False->True.
- 15 city-days inside at 2000Z; 10 survive to final (66.7%).
- Primary rule (first `BUY Yes` <= 0.25 after the archived GeoJSON is available, `Last-Modified`+2 min): 6 trades / 3 independent days, $16.03 cost, +$658.23 net after 0.05 fee + 1c buffer; +$629.75 at 5c buffer.
- Broad price proxy (any trade <= 0.25): 10 trades / 7 days, $16.93 cost, +$674.71 net.

## Caveat

Historic order books are not public. Trades are used as execution-price proxies; the entry labels this and reports 3c/5c buffer sensitivity. The sample is 3–7 independent days, far below 30; the entry is a 草稿/待选区 candidate, not a proven strategy. The `Last-Modified` gate avoids using the nominal 1630Z/2000Z time as if the machine-readable polygon were already available.
