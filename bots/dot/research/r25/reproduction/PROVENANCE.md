# Public source provenance and local placement schema

These are acquisition directions and schemas, not a dataset or an automatic downloader. Honor provider access controls, rate limits, current licensing and archive documentation. No authenticated accounts or keys are needed for the documented public market sources. No network acquisition was performed by this reproduction task.

## Kraken spot inputs

Public source families:
- Official OHLCVT archive assets: https://assets.kraken.com/marketing/institutions/Kraken_OHLCVT_Full.zip.part00 (multipart archive family; inspect current official metadata before acquisition).
- Public OHLC API: https://api.kraken.com/0/public/OHLC

Pairs: XBTUSDT maps to BTCUSDT; ETHUSDT and SOLUSDT retain their names. Required local files are sources/BTCUSDT.json, sources/ETHUSDT.json and sources/SOLUSDT.json. Each is normalized JSON with top-level asset, source_pair, quote and rows. Each row contains timestamp (UTC Unix seconds), open/high/low/close (decimal strings), volume, trades and source. The original source envelope can contain additional fields; SHA verification requires the original full bytes.

The replay requires one UTC daily row per day from 2024-01-01 through 2026-10-19 inclusive. Official archive members XBTUSDT_1440.csv, ETHUSDT_1440.csv and SOLUSDT_1440.csv supply dates through 2026-09-30; public interval=1440 OHLC supplies October1–19 only. The archived period remains authoritative and overlap must not be silently overwritten. Future rolling OHLC responses may no longer include those dates. Archive multipart versions and offsets may change; historical source bytes cannot be promised by these directions.

## Binance daily inputs

Official public derivatives endpoint families:
- https://fapi.binance.com/fapi/v1/klines
- https://fapi.binance.com/fapi/v1/markPriceKlines
- Public spot kline family: https://api.binance.com/api/v3/klines

Local files: sources/prices-main.csv (2024-01-01 through2026-09-30) and sources/prices-extension.csv (2026-10-01 through2026-10-19). Required original CSV header: symbol,date_utc,open_time_ms,close_time_ms,spot_open,spot_high,spot_low,spot_close,perp_open,perp_high,perp_low,perp_close,mark_open,mark_high,mark_low,mark_close. Symbols are BTCUSDT, ETHUSDT, SOLUSDT. Preserve decimal strings, UTC millisecond times, original row order and CSV encoding for byte equality. The core replay uses Binance perp/mark columns and Kraken spot prices; Binance spot columns enable matched-quantity reference attribution outside the core replay.

## Binance funding inputs

Official public endpoint family: https://fapi.binance.com/fapi/v1/fundingRate

Local files: sources/funding-main.csv and sources/funding-extension.csv, with periods matching the daily files. Required original header: symbol,fundingTime,fundingTime_utc,fundingRate,markPrice,rateType,source_page. Funding time is the actual Unix millisecond timestamp, not a rounded8-hour slot. fundingRate and markPrice preserve exact decimal strings; source_page is provenance metadata. Do not substitute daily marks for settlement marks. The original dataset contains3069 events per asset including entry; replay strictly excludes the event exactly at entry and retains3068. Do not fabricate absent events, marks or row metadata.

## Parameter and hash closure

sources/contract.json is included and is research configuration, not a market dataset. inputs.json contains SHA-256 digests for this contract and the seven market files. expected-output-hashes.json records three deterministic output hashes. These hashes verify the original frozen local inputs/results; they do not guarantee that later public queries recreate the same byte serialization. No credentials, private coordination identifiers or raw rows are included in this distribution.
