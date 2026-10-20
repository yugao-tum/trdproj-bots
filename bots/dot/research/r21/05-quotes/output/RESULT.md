# r21 role05: Independent quote/depth audit

## Finding
The existing feasibility snapshot is arithmetically coherent, but it is not a virtual entry. Its request/response envelope is 2,468 ms. Spot does not provide an exchange event timestamp, so contemporaneous retrieval does not prove atomic exchange-state synchronization. The present entry check rejects the old snapshot as pre-lock observation. No position, order or account action was created.

Independent Decimal arithmetic gives a conservative common quantity grid of 0.001 ETH, maximum whole-grid budget quantity 0.522 ETH, spot ask-side VWAP 2,385.48 USDT and perpetual bid-side VWAP 2,384.47 USDT. The quote-based spot cost including the additional assumed 0.30% friction fits the 1,250 USDT budget; the next common-grid quantity does not. These figures describe this one already-seen feasibility observation, not a selected future fill or current market price.

## Independent checks
- Positive quantity grids use rational LCM after integer scaling. Flooring never rounds up. Spot's MARKET_LOT_SIZE step of zero is not treated as a positive grid. Its separate maximum quantity remains enforced.
- Buy uses ask depth; short reference uses bid depth. VWAP consumes actual visible sizes in sorted levels. No midpoint, mark or last price substitutes for executable-side depth.
- The full best-ask budget upper quantity must be covered by visible ask depth before binary search. Missing capacity is rejected instead of shrinking size merely to fit the snapshot. Perpetual depth must cover the chosen same quantity.
- Both complete request intervals are enclosed in at most 5,000 ms. Response age, protocol-lock ordering, optional exchange event age, timestamp units, crossed books, duplicated/unsorted levels and non-finite values are checked.
- A missing exchange timestamp remains missing. It does not become request time, response time or proof of actual fills.
- 25 synthetic tests passed, covering grids, side orientation, partial depth, no capacity resize, stale/future times, exactly-five-second boundary, minimum notionals and absent filters.

## Scope limits
The retrospective capture-time arithmetic check uses a hypothetical lock at the first request solely for testing the interface; it is not the root's actual frozen-protocol lock. It must never initialize a ledger.

Spot's market minimum-notional filter uses an average-price reference over five minutes. Current ask VWAP is not that average, so this audit verifies only a quote-based notional threshold. Actual order acceptance is unproved. Futures filter data was reused from an earlier retrieved snapshot whose server timestamp was older still; effective-time and historical-rule claims are not made.

Snapshot prices can move before an order could arrive, quoted quantity can disappear, and two venues' engines are not atomic. Even a successful future protocol check would produce a conditional reference observation, not an actual fill. No historical liquidation tier is inferred here.

## Inputs and reproduction
Inputs are role03's interfaces.json and its cited raw public-connector response hashes. Raw data remains local and is not included in the publication package. RESULT.json records the normalized input hash.

Run locally from this directory:
- python -m unittest -v
- python audit_sources.py

The second command creates a descriptive result only; it has no network, account, order or position side effects. Its current-time rejection field may vary while remaining rejected for the old observation. quote_audit.py and its synthetic tests are independently runnable without research datasets. Artifact test counts are not independent economic events.
