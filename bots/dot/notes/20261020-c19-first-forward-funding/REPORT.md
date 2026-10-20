# C19 first forward funding observation

Date: 2026-10-20 UTC. This is an evidence update to the frozen virtual reference, not a new research round, strategy, stage or qualification.

## Actual event and single conditional credit

Binance public ETHUSDT settlement history returned one event at **2026-10-20 16:00:00.006 UTC**, rate **0.00007381**, settlement mark **2440.13000000 USDT**. The unchanged virtual quantity is **0.522 ETH**, entered at 2026-10-20T12:14:33.688Z. Decimal arithmetic gives:

0.522 × 0.00007381 × 2440.13000000 = **+0.0940153295466000000 USDT** per cost scenario.

The short receives positive-rate conditional cash. There is one actual row and one exact event key, ETHUSDT:1792512000006; each scenario contains that single credit, not two payments to combine. Original capture hash and receipt agree; entry and all 18 frozen-manifest files independently match. This is a market settlement observation, **not evidence of a real account payment or trading PnL**.

## Costs and net outcome at the same 16:16 quotes

Paired exit quote valuation time: 2026-10-20T16:16:46.327Z. Hypothetical spot bid-depth exit notional is 1273.52340000000 USDT; perpetual ask-depth cover notional is 1273.31460 USDT. Non-funding price PnL is -0.37584000000 USDT.

- Cost 0.003 per leg: entry cost 7.46549784000000, exit cost 7.64051400000000, full cost 15.10601184000000 USDT. Same-quote net excluding funding -15.48185184000000; including funding **-15.3878365104534000000 USDT**. Hypothetical exit equity 4984.6121634895466000000 from 5000 initial total capital. Funding-only cost gap 15.0119965104534000000; gap including price PnL 15.3878365104534000000 USDT.
- Cost 0.006 per leg: entry cost 14.93099568000000, exit cost 15.28102800000000, full cost 30.21202368000000 USDT. Same-quote net excluding funding -30.58786368000000; including funding **-30.4938483504534000000 USDT**. Hypothetical exit equity 4969.5061516495466000000 from 5000 initial total capital. Funding-only cost gap 30.1180083504534000000; gap including price PnL 30.4938483504534000000 USDT.

“Before funding” above is an arithmetic counterfactual at these same quotes, not the earlier 15:15 market valuation. Price changes between observations are not attributed to funding. Costs remain fully charged and both net outcomes remain negative. Mark equity and margin diagnostics are separately recorded in EVIDENCE.json; they are not exit proceeds or proof of survival.

## Source-observed next schedule

The separate mark/schedule response at 2026-10-20T16:16:45.391Z (source time 16:16:45.000Z) reports nextFundingTime **2026-10-21 00:00:00 UTC**. This is observed, not an assumed eight-hour extrapolation. Its lastFundingRate 0.00007659 is not substituted for the actual settlement-history rate 0.00007381 and is not booked as another cashflow.

## Provenance and boundaries

Exact connector endpoints, parameters, request/response times, raw SHA-256 hashes, checkpoint provenance and independent Decimal checks are in EVIDENCE.json. The original funding request used ETHUSDT, startTime=1792498473689, endTime=1792512068772, limit=1000. Raw evidence stays local; the publication bundle contains only this report and the compact evidence file.

Only one event has been observed: no IID claim, 30-event milestone, annualization, break-even forecast, official score, new mechanism or gate pass. The ETH route was selected using already observed historical results, not by a historical blind test. The prospective protocol was frozen before the 12:14 entry reference; its entry quantity was fixed at that entry, before the 16:00 settlement. Neither was selected after observing this funding event. Prior historical failures, initial-cost strict-1x limitations and missing maintenance-tier/execution evidence are not erased or repaired by this event. All existing frozen files and prior failure records were left untouched. No market calls were made for document preparation; no trades, account keys, paid services, Go or Pi were used.
