# R25 code-only reproduction

This distribution contains code, frozen research parameters, hashes, and acquisition/schema documentation. It contains **no market datasets**, including inside its ZIP. The earlier source-inclusive minimal-reproduction.zip is a local isolated-replay proof only and must not be committed or published under the repository's no-raw-data rule.

Python 3.9+ and its standard library are sufficient. Before running `python3 reproduce.py`, independently obtain the seven declared market input files and place them in `sources/` beside the included contract.json. See PROVENANCE.md and inputs.json. The code verifies every input SHA-256 before calculation and fails closed when inputs are absent or different. It does not download data.

Public code alone cannot reproduce the numeric results without these declared raw/normalized input files. Exact historical bytes are **not guaranteed to be obtainable through future acquisition**: provider retention, updates, serialization and archive revisions may differ. Do not replace expected hashes just to make a changed source pass. A newly acquired dataset requires a separately identified, revalidated study.

Generated outputs contain exact rational results for 36 dependent sensitivity cells. They are written locally under results/. Do not commit generated raw daily/funding ledgers. September is a hypothetical checkpoint only; October continues the January position. Eight BTC/SOL B cases have negative local equity and later endpoints are counterfactual. ETH positive equity bounds do not certify historical MMR/cum, fills, fees or exchange lot acceptance. No official-score, new-mechanism, blind-OOS or independent-outcome claim is made.

For a local validation with privately held declared inputs, run `python3 verify_injected.py --input-dir /path/to/declared/sources`. It makes an isolated temporary copy, injects the eight declared inputs, denies original-workspace reads and sockets during replay, compares all generated hashes, and tests tamper refusal. Input data are never inserted into the public distribution.
