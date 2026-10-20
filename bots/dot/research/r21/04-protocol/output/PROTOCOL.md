# Purely virtual paired-hedge observation protocol

Status: implemented and synthetically tested; no position initialized from actual quotes. The existing 11:53 feasibility books predate any final root lock and are rejected as entry references. There is no network, account, order, wallet, signature or process-launch function in this module.

## Freeze and entry contract

The root must record the canonical CONFIG SHA256 and implementation SHA256 from this bundle before requesting a new paired quote snapshot. CONFIG hash is the protocol_sha256 used by the code. Root lock fields: authorized_by="root", entry_authorized=true, protocol_sha256, locked_at_ms. These fields are an internal workflow assertion, not cryptographic identity/authentication and not permission to trade. No actual root lock is issued by this task; test locks are synthetic only.

Pass current filters and fresh normalized books to initialize_virtual. Both request starts must be at/after the recorded lock. The full earliest-request-start to latest-response-end interval must be at most 5,000 ms. Both responses must be no older than 5,000 ms at evaluation. Where exchange-event time exists it must be no more than 5,000 ms behind the response and no more than 1,000 ms ahead. Missing spot exchange-event time is retained as unknown; fresh retrieval does not establish event freshness or simultaneous executability.

Books must have positive, unique, sorted levels and an uncrossed two-sided market. Symbol must be ETHUSDT. Reject shallow depth instead of reducing allocation solely to fit liquidity. This conservative prerequisite may reject a rare boundary case where a smaller, budget-limited amount could fit; no optimality or guaranteed fill is claimed.

Compute the rational least-common-multiple of active quantity grids. Zero MARKET_LOT_SIZE step/minimum means that constraint is disabled, not that the common grid is zero. Combine positive minimum quantities and the tightest positive maximum quantities. Current source adapter yields common step0.001, spot market maximum3721.03953083, futures market maximum2000. These are retrieved observations, not historical rules or a guarantee of current order acceptance.

Start with floor[1250 / (best spot ask ×1.003)] on the common grid. Require the spot book to cover that upper quantity, then binary-search the greatest grid amount whose full ask-depth cash cost times1.003 stays within1250. Perpetual bid-depth must cover exactly that quantity. Check each market's quote-based minimum notional. Spot's true market NOTIONAL rule uses a 5-minute weighted average and dynamic price filters are not evaluated: mark actual-order acceptance unverified. No true order is sent.

Primary venue cash2500; external idle cash2500. Spot purchase includes its0.003 assumed friction. Deduct separate perpetual entry friction from the remaining venue collateral. Fixed sensitivity0.006 uses identical chosen quantity, with separately calculated cash. Stress spot spend may exceed the primary1250 allocation by extra assumed friction, but never total venue cash. The generic0.003/0.006 costs are additional conservative assumptions on observed bid/ask prices, potentially overlapping spread costs; they are not verified taker commissions.

Entry timestamp is the latest paired response end, so funding at or before it is excluded. The ledger is a hypothetical synchronized reference, not two actual fills. Short notional divided by margin can exceed1, consistent only with the proposed hedge interpretation; it is not a claim that strict1x or all venue rules are satisfied.

## Funding and resume contract

apply_funding is an atomic pure value transform. Exact (symbol, actual fundingTime) keys control deduplication; equal repeated records are no-ops, conflicting duplicates reject the entire batch. Preserve millisecond jitter and all signed rates. Reject future records beyond observed_as_of_ms. Only records strictly after entry are booked as conditional cash q×rate×actual settlement mark. No compounding, quantity changes, collateral transfers or borrowing.

The scheduler wraps this ledger and persists it with an expected revision and atomic replacement. Its request-reservation/inflight states are separate from ledger economic state. It must not reserve a new call on an uncertain prior outcome or use a request high-watermark as proof of economic cashflow. last_funding_time_ms is the maximum accepted event timestamp, not a proof that earlier intervals have complete coverage; the collector/scheduler retains coverage evidence separately.

## Valuation and interpretation

Report mark-based margin/equity separately from hypothetical exit equity based on fresh spot bids and perpetual asks. Missing, stale or insufficient exit books produce null exit valuation, never a stale fill. All entry and exit friction remains charged; no cost amortization is hidden. Output funding cash, price P&L, full assumed four-leg friction, funding needed to break even at current exit quotes and remaining shortfall. Break-even-days forecasts and short-window annualized returns are deliberately null. Thirty funding periods are a descriptive evidence milestone, not a ten-day full-cost-recovery hurdle, forced exit or qualification claim.

Negative mark margin is flagged; nonnegative margin is not continuous liquidation-survival proof. Historical maintenance tiers, funding eligibility, current dynamic acceptance and fills require separate evidence. The module cannot claim an official contest stage or score.

## Reproduction

Run: python -m unittest -v test_virtual_ledger.py

All24 synthetic unit tests pass. A separate offline adapter check against role03's retained feasibility snapshot reproduced q0.522 and common step0.001, then confirmed a new lock rejects those old books. That diagnostic did not create or save a real-input virtual position. Full source/raw response data remains local, not in this code bundle.

## Independent-review hardening
All input observation, request, response, lock and actual funding timestamps must be integer Unix milliseconds in 2000–2099. Booleans, floating point, strings and epoch-seconds are rejected rather than coerced. Book-side callers accept only bids or asks. Synthetic tests use representative epoch-ms. These are validation constraints, not a price-selection rule change. The root lock must bind the final implementation/config/test/criteria manifest in addition to the CONFIG protocol hash. CONFIG hash alone does not bind implementation bytes.

The valuation reports both negative and nonpositive observed margin. A nonpositive margin invalidates feasible-path status; the supervising checkpoint must retain that event permanently. Subsequent ledger continuation must be explicitly counterfactual and may not erase the earlier failure. This module does not certify maintenance-tier survival even when its margin remains positive.

The exit quote valuation carries its own quote_valuation_time_ms, not the last funding timestamp. funding_only_cost_recovery_gap is full assumed entry+exit cost minus accrued funding, floored at zero, deliberately excluding price P&L. It differs from remaining_funding_shortfall_at_current_quotes, which includes observed price P&L; neither is a forecast of days to recovery. These fields align with the independently frozen 08 criteria (SHA256 7fc8fda037a2b4d9b431520ed96ac26e3881556d272654d6e55864d659ed673e).
