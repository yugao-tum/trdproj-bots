# C34 r13: real-price replacement, partial event proof

Native takeover completed retained-evidence processing and one actual market panel. The requested three officially evidenced event panels are NOT achieved. This is not a successful backtest or a new mechanism.

## Useful result
- APE's original calendar implies a −14.19% 72-hour move at a 5.85 USD starting price. That outcome is not reproduced by the independently obtained official Binance APEUSDT/BTCUSDT May 2023 hourly observations.
- Official pre-event ApeCoin page snapshot (2023-05-14 11:43:29 UTC) establishes launch date, monthly vesting quantities and Ethereum contract. May 17 is a monthly-anniversary inference, NOT a verified release transaction. The published rounded components sum to approximately 15,601,325.76 tokens; the charity tranche can be tokens or equivalent value. Neither total actual tokens released nor the exact unlock hour is proved.
- The inferred local May 17 date has no stated timezone. We conservatively test 50 possible hourly origins from May 16 10:00 UTC through May 18 11:00 UTC. The 72-hour open-to-open APE changes range from −1.096681% to +2.899851%; APE minus BTC changes range +0.050875% to +2.631326%. This is descriptive sensitivity, not a tradable profit, causal effect or confirmed unlock response.

## Data and validation
Event selection was frozen before any price acquisition; its unchanged SHA-256 is recorded in provenance. Official archive listing independently establishes APEUSDT archives from March 2022, contradicting the calendar's April 28 listing field. It establishes archive availability, not an exact trading-launch timestamp.

Two monthly archives plus their official checksum files were downloaded sequentially, with more than one second between requests. Each contains 744 actual hourly rows. Checksums match; all 1,488 rows have unique contiguous UTC timestamps, valid OHLC order and volumes, and correct close-time bounds. The local panel contains 146 joined hours using 292 raw symbol rows, with zero missing joins. Eight invariant groups pass; seven unit tests pass, including six adversarial rejection cases. Synthetic mutations exist only as test fixtures.

## Exact missing proof
- BIT: official tokenomics request returned 403. Stopped, no retry or alternate-route bypass.
- SAND: retained official 2020 whitepaper supplies broad vesting, but does not establish the calendar's August 14 2023 event day, actual tranche or execution. No day fabricated from its chart or calendar.
- APT: official schedule says no core/investor release in the first twelve months and 3/48 in the thirteenth month. It does not substantiate the copied October 12 2023 20M core/investor row. No corrected date invented.
- OP: dated official May 17 2023 announcement supports May 31, not hour or numerical unlock quantity. The linked current public sheet is updated October 14 2026 and contains annual historical aggregates, so it cannot prove pre-event May 31 quantity. The official allocations page archived May 30 2023 was additionally retrieved; it supplies generic allocation/lockups, still no event quantity. A historical-sheet index request timed out without body and was not repeated.
- Forty-seven later calendar rows were not investigated. Do not claim all 52 events were vetted or that the first three globally eligible events have been found. Search budget was already exhausted by Go. Seven of 32 source attempts and 60 of 64 dataset requests remain; source failure is not a quota exhaustion claim.

## Provenance and disposition
Prior Go work and native completion are recorded separately. All 26 retained files and four frozen input hashes passed verification. No Go/Pi/meiying call, credential operation, trade or publication was performed by this continuation. Exact native model ID is not exposed to the child and is not invented. Parent may append verified dispatcher metadata.

Sources and hashes are in provenance.json. Primary sources: https://web.archive.org/web/20230514114329id_/https://apecoin.com/about ; https://gov.optimism.io/t/5995/1 ; https://web.archive.org/web/20230530143802id_/https://community.optimism.io/docs/governance/allocations/ ; https://github.com/binance/binance-public-data .

Publish only RESULT.md, event-ledger.json, provenance.json, join_checks.py, test_join_checks.py, test-results.json, unit-test-results.txt, time-sensitivity.json and publication-manifest.json. Raw sources, downloaded archives, HTTP metadata and the local market panel are excluded. The parser expects raw inputs locally; the published URLs/checksums make it reproducible without redistributing data. C34 stays evidence-gap / descriptive, not qualified.
