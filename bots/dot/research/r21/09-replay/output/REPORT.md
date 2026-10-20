# r21 role09 independent offline replay and safety review

## Outcome
37/37 independent checks pass against the source hashes in RESULT.json. No new strategy, actual entry, fill, account payment, survival certification, or qualified result is claimed. This is a synthetic unit/replay audit, not a real backtest.

The independent oracle uses Python Fraction exact rational arithmetic, cumulative interval overlap for depth valuation, and exhaustive common-grid enumeration. It does not copy the production Decimal sweep/binary-search algorithms. System-under-test modules are imported solely to compare outputs against independent expected values.

## Defects found and verified fixed
- Role04 previously accepted arbitrary book-side keys and seconds-sized timestamps. Owner added bids/asks whitelisting and strict integer epoch-ms validation, excluding bool/float/string, across lock, quote and funding boundaries. Independent adversarial checks now pass.
- Role06 previously accepted corrupted funding account balances and event money/time on restart. Owner added precise event q × rate × mark, key/time and aggregate cash invariants. Independent cash, event and time tamper checks now reject corruption.
- CONFIG-only hashing is not code freezing. Root must separately bind final implementation/config/criteria artifact hashes before any fresh entry observation. The optional artifact manifest binding survives ledger attachment and roundtrip. The workflow must verify file hashes before resume; the hash field is an audit commitment, not authentication.

## Verified invariants
Common .002/.003 grid yields .006; maximum affordable q matches exhaustive rational oracle; spot asks/perp bids match independent quote cash; both .003/.006 cases preserve venue capital and identical q. Funding signs, duplicate no-op, conflict atomicity, entry-boundary exclusion, future rejection and four-cost-leg exit cash identities and the funding-only recovery gap (excluding price P&L) pass. Serialized checkpoint resume, stale revisions, 403 stop, 429 missing-reset stop, exact reset boundary plus hourly minimum, uncertain-request crash hold and prelock no-action pass.

The existing role03 feasibility snapshot was parsed only to verify conditional filter labels and demonstrate rejection by a later root lock. It was not initialized as an entry. Synthetic root locks in tests confer no production authorization.

## Acceptance and unit boundaries
Quoted spot notional above minimum is only a quote-based conditional check. The spot five-minute weighted average and other dynamic acceptance references were not retrieved or invented. Adapter retains acceptance_verified=false and dynamic_reference_unverified=true. No actual exchange acceptance is certified. ETHUSDT fixes quantity in ETH and quote price in USDT by source schema; a naked positive number cannot reveal a semantic unit swap. Invalid nonfinite/negative prices, wrong symbol/side and time units are rejected; provenance and schema remain necessary to detect a plausible but mislabeled numeric price. Do not represent those checks as universal unit detection.

## Safety surface
AST inventories of imports and calls for role04 virtual_ledger.py, role05 quote_audit.py and role06 scheduler.py are in RESULT.json. Reviewed code has no HTTP, account, wallet, credential, signed request, order, subprocess or background scheduling interface. Execution was offline and created no daemon. This is a static surface review plus synthetic execution, not a formal proof about arbitrary future integrations or unrelated processes in the shared environment. Root alone remains the authorized public-read coordinator.

No unresolved test failure. Production entry remains gated on root final lock and fresh paired source observation; no maintenance-history completeness or real-order acceptance follows from this test suite.

## Final initializer and scheduler update
Scheduler latest sticky feasibility failure and root-bound artifact gate were independently tested; both pass. The initializer received independent static review and its six owner-written synthetic tests were rerun successfully (these six are not counted as independent tests). It uses live time.time_ns without a caller-provided clock; requires saved root lock, reservation and unchanged manifest; independently compares role05 q and both VWAPs; atomically writes with flock, file fsync, replace and directory fsync, then reads back. Audit found and owner fixed malformed Decimal exception handling and missing invalid-branch readback. Both success and invalid paths now verify saved state; no existing entry replacement.

The helper uses filesystem calls only, not external commands or network. Locking is advisory and assumes all checkpoint writers cooperate. Frozen artifacts must not be modified concurrently between hash verification and import. No crash/power-loss fault injection was performed; physical durability is not claimed beyond reviewed fsync/replace semantics. All initializer tests use temporary synthetic state, no actual entry. Reviewed final source hashes are in RESULT.json.
