# Public input provenance and normalization

Only data_provenance.json and the synthetic fixture are included. No real market data is distributed.

## Archive coverage

- Spot: 45 monthly archives for each of BTCUSDT, ETHUSDT and SOLUSDT, January 2023 through September 2026 (135 ZIPs)
- Funding: 33 monthly archives for each symbol, January 2024 through September 2026 (99 ZIPs)
- Source archive and .CHECKSUM locations, exact archive SHA256, CSV member name, uncompressed byte size, row count and timestamp units are recorded per archive
- Original retrieval interval: 2026-10-19T16:30:55.901525Z through 2026-10-19T16:35:06.804032Z
- The stored original provenance-manifest hash is included; raw request logs and local paths are omitted

## spot_daily.csv

Fields in exact order:

symbol, open_time_utc, open_time_raw, open, high, low, close, volume, close_time_utc, close_time_raw, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore

Official spot ZIP members contain 12 columns without a header. Preserve every source numeric field as its original text. Add symbol and ISO UTC open/close timestamps. Raw open/close timestamps before 2025 are milliseconds; from 2025 they are microseconds. The utility selects a divisor of 1,000 or 1,000,000 using the raw timestamp magnitude, converts using Python datetime.fromtimestamp(..., timezone.utc), and replaces +00:00 by Z. ISO timestamps preserve Python's default fractional precision (six digits where present). Prices are not rounded or recomputed.

The frozen loader checks the exact schema, finite positive OHLC, consistent highs/lows, finite nonnegative volume/count fields, unique aligned daily calendars, UTC midnight open, exact day-end close and equality of raw versus ISO times. Each symbol has 1,369 dates. Year 2023 is warmup only.

## funding.csv

Fields in exact order:

symbol, calc_time_utc, calc_time_raw, calc_time_raw_utc, funding_interval_hours, last_funding_rate, jitter_ms

Official funding members have the header calc_time,funding_interval_hours,last_funding_rate. Preserve these three source fields exactly, including exponent or trailing-zero notation. Convert raw integer milliseconds to Python floating-point seconds. Normalize to the nearest 28,800-second grid point using round(seconds / 28800) * 28800. Store raw and normalized UTC separately. Serialize jitter_ms as str((raw_seconds - grid_seconds) * 1000), matching the historical normalization, including binary floating-point representation. Observed jitter is at most approximately 26 ms; the frozen validator permits at most 30 ms and 0.001 ms serialization-rounding difference while requiring exact raw millisecond UTC equality.

The C40 loader checks a complete three-events-per-day grid, three symbols, 3,012 events per symbol, finite rates within absolute 0.05, 8-hour intervals, no duplicates and consistent raw/normalized times. The funding rate is only a signal; the spot-only simulation receives no funding cashflow.

## Serialization and validation

Sort rows by symbol ascending then UTC timestamp ascending. Use Python csv.writer defaults, UTF-8 without BOM, CRLF record terminators, one exact schema header, and a final CRLF. prepare_inputs.py verifies both final byte hashes before writing either normalized file. Never edit, interpolate, forward-fill, drop or replace rows to force a hash match.

## Synthetic fixture

fixtures/mini_spot_daily.csv is an artificial nine-row constant-price test fixture: BTC 100, ETH 50 and SOL 20 over three dates. It is self-written testing material, not market history. The original fixture SHA256 is recorded in source_origins.json.
