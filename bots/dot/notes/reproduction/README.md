# Fixed-rule historical simulation reproduction package

This offline, standard-library Python package reproduces five fixed mechanisms and two passive risk benchmarks from frozen public data. It contains self-written simulation code, synthetic hand tests, public download locations and hashes. It contains no raw market data, downloaded strategy code, credentials, source-article copies or model transcripts. This is a reproduction package, not a newly tested strategy, profitability promise, investment recommendation or live track record.

## Scope

| Family | Scenarios | Fixed rules |
|---|---:|---|
| Original spot screen | 8 | C21–C24 at 0.30% and 0.60% cost per actual trade leg |
| Half-capital sensitivity | 12 | Same four mechanisms plus SOL_HODL and EW_HODL, each at both costs |
| C40 spot proxy | 6 | BTC, ETH and SOL separately, each at both costs |

These are five mechanisms, not 26 independent discoveries. Each scenario has separate total capital of 5,000 USDT; scenarios are not simultaneous deployments. The 2025+ label “OOS” is a retrospective fixed-rule time split, not genuinely unseen future data. All outputs, including unfavorable outcomes and zero-trade cases, are retained. No parameter search or winner selection is performed.

## Requirements and inputs

Python 3.10 or newer is required by the type syntax; exact byte-level regression was validated with CPython 3.12.14 on Linux. There are no third-party dependencies and nothing to install. Runs perform no network requests. A different runtime may format floating-point text differently; any exact-hash mismatch must be investigated rather than silently tolerated.

The two externally supplied inputs are:

- spot_daily.csv: 4,107 rows; BTCUSDT, ETHUSDT and SOLUSDT; 2023-01-01 through 2026-09-30
- funding.csv: 9,036 rows; the same symbols on a complete 8-hour grid; 2024-01-01 through 2026-09-30

The exact schemas, normalized hashes, sizes, 234 official monthly archive URLs, official checksum URLs, member names and archive hashes are in data_provenance.json. Retrieval was recorded on 2026-10-19 from Binance's public data archive. No new online availability claim is made by this package. Do not bypass access restrictions or use account credentials to obtain these public files.

## Reproduce from official downloads

1. Independently obtain every ZIP and matching .CHECKSUM listed in data_provenance.json. Place them in any local archive directory, flat or nested. ZIP basenames must be unique. The package does not download them.
2. Reconstruct the normalized inputs with the offline utility:

    python prepare_inputs.py --archive-dir /path/to/downloaded-archives --output-dir /path/to/normalized-inputs

   It verifies all 234 ZIP hashes and official checksum values, reads the single expected CSV member without disk extraction, preserves original numeric text, sorts by symbol/time and reproduces both frozen normalized CSV hashes. It refuses existing output files or any hash mismatch. See DATA_SCHEMA.md for normalization details.
3. Run the synthetic hand tests without market inputs:

    python run.py hand-tests --output-dir /path/to/hand-test-run

4. Reproduce all 26 frozen scenarios and run exact regression:

    python run.py reproduce --input-dir /path/to/normalized-inputs --output-dir /path/to/new-reproduction-run

5. Recheck an existing run without rerunning simulations:

    python run.py verify --output-dir /path/to/new-reproduction-run

Use a fresh output directory outside this release package. The wrapper refuses existing family output directories; it never edits the input files or original frozen outputs. The output tree has spot-screen/, spot-halfcap/, c40/ and verification.json. Generated daily ledgers can exceed 1 MB and are intentionally excluded from the release. Do not add generated inputs or output ledgers to a repository governed by a 1 MB/file limit.

Use run.py as the entry point; the original spot_screen.py is deliberately preserved byte-for-byte, including its original relative defaults. The wrapper explicitly supplies input/output paths. The other copies have only path/configuration/report-provenance adaptations; economic logic and parameters are unchanged.

## Tests and exact comparison

The run counted 43 synthetic/unit-test methods and one historical half-scale regression. These are software tests, not independent trades or new strategy backtests.

Synthetic/unit tests cover fees and budget constraints; terminal liquidation; signal timing and future-data perturbations; funding-grid, missing/duplicate/NaN checks; 7-day holding exits; OOS state and fee carry-in; and passive benchmarks with no rebalance. A historical half-scale accounting regression checks all four original rules at both costs against the reproduced original ledger.

expected_outputs.json contains frozen reference hashes. Every delivered CSV output is checked byte-for-byte. Summary/data-quality JSON is parsed, only the exact listed metadata fields are removed, then serialized with sorted keys and compact separators before SHA256 comparison. No economic field is excluded, no numeric rounding is applied, and no tolerance is used for the 26-scenario regression. The separate half-scale relationship test retains its original floating-point tolerance.

Explicit JSON exclusions are local input/script paths, runtime timestamps, sensitivity script hash changed by packaging, and two non-economic author/provenance labels. Generated Markdown and runtime manifests contain naturally variable timestamps, paths and code/output hashes; they are not claimed byte-identical. All their economic content is covered by structured JSON/CSV checks. Input and unchanged-loader hashes remain checked exactly.

## Methodology and interpretation

Read METHODOLOGY.md and C40_PREREGISTRATION.md before interpreting results. Preserved timestamps describe rule freezing before their historical runs, not prospective prediction. The original data had already existed. Daily open/close fills are assumptions; historical order-book depth and extra execution slippage were not verified.

The study reports both contributed capital and strict 2,500-USDT dynamic venue diagnostics. The guide's “roughly 2,500 per venue” wording did not specify dynamic NAV. Daily highs across multiple coins are not simultaneous; their sum is only a possible upper bound. Episodes, months, bars, trade legs and correlated coins are not automatically independent events. No 30-independent-result claim is made.

## Source identity and packaging audit

source_origins.json records SHA256 for every original and packaged source/test/fixture. Unchanged files are marked explicitly. PACKAGING.patch is the exact textual diff except that removed private absolute root, internal folder label and internal attribution/access-log text are replaced by clearly labeled placeholders. The original-source hashes are retained. The unredacted audit patch is deliberately not a public release file. No trading logic or parameter changes were made; the C40 public preregistration keeps all original rule bullets verbatim.

RELEASE_MANIFEST.json inventories the proposed release by relative path, byte size and SHA256. It excludes itself from self-hashing and is indexed by INDEX.md. This package records the reviewed 2026-10-19 research release.
