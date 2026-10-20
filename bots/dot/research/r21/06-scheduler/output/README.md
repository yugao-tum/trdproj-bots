# r21 role06: durable read-only forward checkpoint contract

## Result

This is an implemented and synthetically tested **offline scheduler contract**, not a running collector or virtual position. No network request, process, automation, account operation, order, credential handling or mutation of the main STATUS file occurred. The initial checkpoint template has null protocol lock, entry and ledger. It cannot generate a due request until root locks the protocol.

The existing root/hourly coordinator owns calls. Do not start a second collector or automation. Files here contain no network or clock implementation. Callers provide UTC integer milliseconds.

## Single atomic state

`r21.forward-checkpoint.v1` wraps role04's `r21.virtual-ledger.v1` ledger.

- `protocol_sha256` and `root_lock` identify the exact frozen protocol. The lock is immutable within one checkpoint. Root's workflow approval is a record, not a cryptographic authentication mechanism.
- `entry` is copied from role04's validated ledger only. A feasibility quote never constitutes an entry.
- `ledger.funding_events`, keyed by `ETHUSDT:<actualFundingTime>`, is the **only cash-charge deduplication authority**. The scheduler does not maintain a competing seen-event set.
- `ledger.last_funding_time_ms` equals the maximum committed actual funding time, or entry time before any funding. The next request starts at this cursor plus one millisecond.
- `source_status` contains a separately reserved request for `quote_pair` and `funding_history`, the last attempted time, outcome, halt state and explicit reset time.
- `last_snapshot` identifies the last persisted successful quote-pair response. This is not proof the quotes passed role05 validation.
- `funding_schedule` is a source-observed next funding time. No perpetual eight-hour assumption is hard-coded.
- `revision` enables compare-and-swap checks before one atomic checkpoint replacement. Ledger cash, event keys, cursor and request completion must commit together.

The supplied JSON schema describes structure. The pure Python functions add protocol identity, entry-boundary, cursor, previous-event immutability and request checks. Restore additionally recomputes each event q×rate×mark at Decimal precision 50, verifies event key/time and each cost account funding_cash against the deterministic event sum; exotic rounding-order differences fail closed for reconciliation. Role04 remains responsible for input validity; role05 remains responsible for quote synchronization/depth. Passing scheduler tests does not establish the whole pipeline is valid.

## Resume sequence for the existing coordinator

1. Read the main research status and its verified pointer to the intended forward checkpoint. Do not invent or initialize a replacement if one already exists.
2. Read the complete checkpoint once, retain its revision and validate it with `validate_restored`.
3. If `root_lock` is null, no entry reference can be collected by this scheduler. Root must first record the final approved CONFIG protocol hash and the separate artifact_manifest_sha256 using lock_protocol(empty, config_sha, lock_time_ms, manifest_sha). The template is not that lock.
4. If a request remains `inflight`, stop that source's automatic reads. Reconcile its persisted response/request record first. Recovered response bytes can complete the same reserved request. A known unexecuted request may be marked invalid with evidence; elapsed time alone is not evidence.
5. Production resume must call `verified_due_work(checkpoint, now_ms, manifest_bytes, artifact_bytes)`, passing freshly read bytes from the frozen filesystem. The raw manifest SHA must match root_lock.artifact_manifest_sha256 and every artifact hash must match. Bare `due_work(checkpoint, now_ms)` is a planning primitive for tests only, not the production resume gate. This returns an informational plan only. It does not execute anything.
6. Immediately before a permitted public read, use `reserve_request`. Verify the old revision is unchanged and atomically persist the reservation. A reservation consumes that source's rolling one-hour request budget even when the local runtime later fails.
7. Root performs only the explicitly authorized public read using the existing connector. Store its exact response before analysis. No alternate endpoint/provider is a recovery path for a source denial.
8. For quotes, role05 validates the paired observation and role04 may construct the entry or valuation. Missing, stale, crossed, partial or invalid books cannot be treated as executable values.
9. For funding, pass records to role04's all-or-nothing batch function. Equal duplicate events are ignored; conflicting duplicates fail closed. Reject records at or before entry or after the observation's as-of time. Do not count a query, source row or implementation test as a new realized funding episode.
10. Prepare `complete_request` and `attach_ledger` changes in memory. Atomically replace **one envelope** containing the updated ledger, event cursor, request completion and source evidence. Never save “seen” before cash, or cash before “seen.” Recheck the original on-disk revision immediately before the replacement; on a race, reread and reconcile rather than replay.
11. An empty funding response advances no cursor. A full 1,000-row response is not proof of full coverage: retain the gap and request another page only on a later allowed hourly check, starting after the last committed actual time.
12. Once a known expected settlement has been recorded, the scheduler requires a newly observed next funding time. A separate budgeted public schedule observation may provide it. The scheduler itself does not authorize extra mark calls or assume the next interval. If the schedule is unavailable, record that missing information rather than silently skipping or fabricating settlements.
13. `review_first_30` requests a descriptive review after 30 distinct committed settlement timestamps. It does not certify IID independence and does not stop the research or close the virtual position. There is no seven-hour cutoff. Only the user's stop/replacement instruction or a source/authorization blocker stops the applicable work.

## Rate limits and failures

- At most one quote-pair request and one due funding-history request per rolling hour. A quote pair is one logical request comprising the pre-approved spot/perpetual read pair, not two independent retries.
- Funding history is due only after a source-observed expected settlement and only after a validated entry. Late wakes query from the last committed time; there is no catch-up request storm.
- HTTP403 sets a persistent halt for that source. No timed retry is inferred.
- HTTP429 uses its explicit Retry-After delta-seconds/HTTP-date or explicit reset. No header/reset means persistent halt. Before the reset, only stored state and the next allowed time are inspected.
- Explicit reset expiry does not override the stricter rolling hourly budget or an unresolved in-flight request.
- An uncertain request outcome keeps its reservation. An invalid data response clears the reservation but still consumes the hourly attempt.
- Source errors are retained with request ID, outcome, evidence reference and next allowed time.
- No automatic unhalt function exists. Root must reconcile genuinely new permission/source evidence and record a deliberate state transition, without reviving withdrawn provider authorization.

## Verification

Run `python -m unittest -v test_scheduler.py`.

Tests cover lock gating, no implicit entry, immutable protocol identity, restore, stale revision, request reservation, hourly cadence, missing/late schedule, schedule changes, empty data, funding cursor boundary and conflict, uncertainty, 403, both forms of Retry-After, missing reset, 30-event review without a forced stop, and user stop.

All fixture entries, response references, amounts and dates in the tests are synthetic. No initialized production checkpoint is delivered.


## Frozen artifact lock and failed-path persistence

The final integration manifest is produced by root/role10, not this module. Format:
`{"schema":"r21.forward-artifact-manifest.v1","sha256":{"04-protocol/output/virtual_ledger.py":"..."}}`.
It must cover the exact protocol code/config, quote validator, scheduler and criteria code/config listed in REQUIRED_ARTIFACTS; additionally bind their tests and any other executable dependency. Exclude mutable checkpoint/STATUS, and the manifest itself to avoid a self-hash cycle. Root locks the SHA256 of the exact serialized manifest bytes, not a canonical re-encoding. Filesystem bytes must be reread and verified on every resume before due-work or request reservation. No input position may be started until the independent replay and integration checks pass.

`record_feasibility_failure(checkpoint, observed_at_ms, evidence_ref)` permanently records a validated observed_nonpositive_margin result. Later price recovery cannot clear this latch. Further accounting is counterfactual_only, not a feasible continuation. Persist it atomically with that valuation's evidence. This latch is an evidence failure, not a user stop or a forced 30-event/seven-hour cutoff.

All 26 scheduler tests pass. These are offline synthetic tests, not live backtests or a qualifying strategy result. The schema, template and module are implementation artifacts, not an initialized production checkpoint.
