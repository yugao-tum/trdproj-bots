# H-quant-020 independent offline arithmetic check

Source: yugao-tum/trdproj-bots, fixed commit 766c28ea4804fab2b8b9a30b29b7cbe72ae033bc. Scope is the derived `tradable_fills.csv` and source-only inspection of `tradable_fills.py`. Source script was never executed. No market API, cache rebuild, trades, credentials, model calls, or remote writes. This is attribution/arithmetic verification, not a new mechanism or official score.

## Recomputed results

101 unique event rows; 97 have a selected ask proxy. All four missing ask proxies are holdout rows (three y=0, one y=1). Discovery has 54/54 priced; holdout 43/47. Split labels are copied from the source table, not independently recreated as a 60/40 split. The band-selected table itself is not 60/40. Discovery endDate range is 2025-09-29 through 2026-05-04; holdout 2026-05-05 through 2026-10-20.

Equal-event, one-share hypothetical net = y - ask - rate*ask*(1-ask):

| Group | Priced n | Mean ask | Mean fee at 0.05 | Mean net at 0.05 | Mean net at 0.04 | Mean net at zero fee |
|---|---:|---:|---:|---:|---:|---:|
| Pooled | 97 | 0.51745491 | 0.01201131 | -0.01400231 | -0.01160004 | -0.00199100 |
| Discovery | 54 | 0.52053919 | 0.01197641 | -0.08807116 | -0.08567587 | -0.07609475 |
| Holdout | 43 | 0.51358163 | 0.01205514 | +0.07901439 | +0.08142542 | +0.09106953 |

Stored ask, fee, net and capital_days match independent reconstruction exactly under Python floating-point arithmetic. The reported fee coefficient 0.05 is a modeled assumption, not an independently verified actual fee schedule or charged fee. Holdout mean and median (+0.44758 at 0.05) are positive; that does not override the negative pooled mean. No confidence intervals or significance claims were recomputed.

The same-97-row alternative `ask_plus1c_same` gives mean net +0.01880126 pooled, -0.04935466 discovery, +0.10439241 holdout at 0.05. Source line 135 computes this from upstream p24+0.01, not from the local `any_yes` column. Upstream p24 provenance is outside this bounded check.

## Ask-side selection and timing: code evidence versus independently testable data

Source lines 68-76 filter the inclusive endDate-minus-72h to minus-24h window and order by timestamp then transaction hash. Lines 81-99 map BUY Yes at p and SELL No at 1-p to an ask-side YES-equivalent proxy and select the last qualifying record. Lines 118-123 extract selected price, timestamp and size. This establishes the implementation, not the raw-event truth or taker-side semantics of the external API.

All 97 selected timestamps satisfy the window: age before endDate min 24.005556h, median 26.624722h, max 62.114167h. Thus the chosen print need not be executable at the nominal minus-24h decision time. Selection of the last historical print is not evidence that a strategy could have received that fill.

The derived CSV does not contain raw side/outcome, original raw price, transaction hash, condition/token ID, full trade sequence, or retrieved response/cache provenance. Consequently it cannot independently verify the mapping for each selected record, the last-print choice, tie ordering, deduplication, API completeness, or actual aggressor/taker role. All 101 truncated flags are False, but reached_start is not exported; these flags alone do not prove completeness.

For 93 events with both selected sides, ask-minus-bid mean is 0.07163796 and median 0.03999998; four are negative. Only two have matching timestamps. Median absolute timestamp gap is 2.061667h, maximum 30.010278h. This is a difference between asynchronous prints, not a contemporaneous quoted spread or an independently verified effective-spread estimate.

## Capacity: narrow supported observation

For all 97 priced rows, selected size times YES-equivalent ask has median 4.835 and maximum 200.000000011916; one row meets >=200 using the unrounded fields. The maximum is effectively 200 with floating-point/record precision, not evidence of meaningfully greater capacity.

These quantities describe one selected historical print per event. For SELL No observations the calculation uses complemented YES price; without original side/outcome it cannot be called verified original traded dollar notional for every row. The source labels the unit USDT, but this check has not verified settlement currency; use “YES-equivalent notional” when quoting.

Absent fields include order-book snapshots/depth, available quantities at the decision time, queue priority, competing flow, latency, slippage curves, actual order acceptance/fills, and strategy cash/deployment constraints. Neither executable $200 capacity nor zero capacity is established. A small selected print does not establish the market could not absorb more. n_trades is a count, not aggregate depth or volume.

## Reproduction and publication boundary

Run `python verify_offline.py --source-dir /path/to/external/inputs --output /path/to/results.json` using only external pinned inputs and the standard library. Supply tradable_fills.csv and tradable_fills.py from the fixed URLs in source_manifest.json; both must match the listed LF-normalized SHA256. Source Python is hashed, never imported or executed. `source_manifest.json` records fixed-commit source URLs and Git blob IDs; `results.json` records input SHA256s (text normalized to LF on saving). Keep `sources/` local: do not publish the raw/derived source dataset. The concise report, arithmetic script, aggregate results and manifest are separate artifacts for the parent to review.

Stopped after supported calculations and explicit missing-field identification. No additional data acquisition is needed or justified within this check.
