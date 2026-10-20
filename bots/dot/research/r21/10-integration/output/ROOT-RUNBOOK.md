# Root-only pre-entry and resume runbook

This document neither grants a lock nor performs a request. Role10 made no entry and no external call. One existing coordinator owns all future reads; do not launch a collector or duplicate automation. No real-order/account endpoints are permitted.

## 1. Verify and explicitly freeze

Read main STATUS and existing tasks/checkpoint pointer first. If a forward checkpoint exists, validate and resume it; never replace an existing entry. For the first entry only, root records its explicit decision and UTC integer-millisecond lock time after sign-off.

Read exact bytes of 10-integration/output/FROZEN-ARTIFACTS.json. Its schema is r21.forward-artifact-manifest.v1 and its sha256 keys are paths relative to r21-proposal. Hash the raw manifest bytes; independently read and verify every listed file against the manifest. Do not use cached hashes. Configuration canonical hash is b30f87538f3f88e8b709058c25325eb6094ce54bfcb6d24e3f9f8da5628fffe6; its raw file hash is separately in the manifest. All listed code and tests must remain immutable after lock. A change requires explicit reconciliation, not silent adoption under an old lock.

Load role04 virtual_ledger, role05 quote_audit and role06 scheduler from verified files. Call scheduler.lock_protocol(scheduler.new_checkpoint(), protocol_sha256, locked_at_ms, artifact_manifest_sha256), only if no prior checkpoint exists. This records root's workflow decision, not a cryptographic signature. Atomically persist the checkpoint and verified STATUS pointer, with a single-writer mutex or genuinely atomic storage compare-and-swap. A revision read followed by os.replace alone is not a cross-process CAS. Keep all mutable state outside the frozen artifact set.

Call scheduler.verified_due_work(checkpoint, now_ms, manifest_bytes, artifact_bytes), supplying fresh bytes for every manifest path. This is mandatory before any production request or resume; bare due_work is insufficient.

## 2. Reserve exactly one fresh observation

Root explicitly authorizes role03 to obtain one NEW spot/perpetual ETHUSDT depth pair after the recorded lock. Do not reuse the 11:53 UTC feasibility books. Reserve quote_pair with scheduler.reserve_request(checkpoint, 'quote_pair', unique_request_id, now_ms); atomically save the reservation before the public reads. It consumes the rolling-hour budget even if a later local validation fails. Quote_pair is two public endpoint reads counted as one paired observation, not authorization for retries.

Root may separately authorize one public mark/schedule observation for source-observed next funding time; record it separately in the external-request ledger. This extra schedule read is NOT silently covered by quote_pair. Keep retrieved filter provenance and its older exchange timestamp explicit; do not call it an atomic fresh filter observation. No fresh filter request is implicit in this runbook.

Record request start/end UTC milliseconds, response reference/hash, complete returned books and known exchange-event timestamps. Response time is not an invented spot exchange-event time. Normalize using role04.normalize_public_interface(fresh_role03_interface). The returned keys are spot, perp, spot_filter, perp_filter. Independently call role05.check_pair(spot, perp, now_ms, locked_at_ms); independently compare its budget_quantity/VWAP/shared-grid outputs to role04's result. Validate both calls from contemporaneous timestamps: do not wait for a slow human review and then falsely declare the five-second age gate passed. Either capture and perform the verified offline validation promptly in the same observation workflow, or classify the observation invalid and wait for the next permitted hour.

## 3. Purely virtual initialization and atomic commit

Call role04.initialize_virtual(spot, perp, spot_filter, perp_filter, checkpoint['root_lock'], validation_now_ms). This must pass both rootlock and quantity/book checks. Zero funding events are expected. Preserve warning fields for unknown spot exchange time and dynamic order acceptance.

In memory, derive scheduler.complete_request(reserved, 'quote_pair', request_id, 'ok', completed_at_ms, response_ref=persisted_reference), then scheduler.attach_ledger(completed, ledger). If separately observed nextFundingTime is still in the future, apply scheduler.record_schedule(state, nextFundingTime, observed_at_ms, source_ref); do not infer an eight-hour schedule. Validate the entire resulting envelope with validate_restored and verified_due_work. Under the same single-writer/CAS protection, compare the on-disk revision to the reserved revision and atomically commit one envelope containing ledger, cursor, event keys, completed request and source evidence. Read back and verify content/hash. No partial saving of cash or seen keys.

If data validation fails, complete the reserved request as invalid with its evidence, without entry. A 403 is forbidden/persistent halt; a 429 honors explicit Retry-After/reset and the stricter hourly limit, or halts if missing. If execution outcome is uncertain, retain inflight and reconcile before another request. Do not obtain another snapshot in the same hour merely to make the test pass.

## 4. Existing hourly continuation

Before every wake, reload/check hashes with verified_due_work. Funding requests are allowed only when a source-observed settlement is due and after a validated entry; startTime is last committed actual timestamp +1 ms. Reserve before the public request. Apply role04.apply_funding only to validated actual rows strictly after entry and not after as-of time; equal duplicates do not charge twice, conflicts reject the whole batch. Empty response advances nothing; a full page is not complete-history proof. Commit completion and all funding cash/events/cursor together using the same atomic discipline.

Each allowed paired exit quote uses fresh spot bid/perpetual ask VWAP and all assumed cost legs. Missing/stale books produce null exit valuation. Funding-only cost-recovery gap excludes basis/PnL; basis/PnL is shown separately. A nonpositive observed margin invokes scheduler.record_feasibility_failure and remains counterfactual_only thereafter, even if later margin recovers. First-30 review is descriptive and does not stop observation. No annualized short-window return, break-even-day forecast, official qualification, actual execution or real liquidation-survival claim is authorized.

## Verified no-network CLI

The frozen helper initialize_checkpoint.py consumes an ALREADY locked and reserved checkpoint; it does not create the root decision or issue a request. Invoke immediately after the pair is saved, within the same root orchestration:

python 10-integration/output/initialize_checkpoint.py --base /absolute/path/to/r21-proposal --checkpoint /absolute/path/to/checkpoint.json --interface /absolute/path/to/new-interface.json --manifest /absolute/path/to/10-integration/output/FROZEN-ARTIFACTS.json --request-id THE_PERSISTED_REQUEST_ID

It reads real current UTC using time.time_ns with no now override; independently compares quantity and both VWAPs; takes an fcntl exclusive lock at checkpoint.json.lock; verifies unchanged bytes before fsync/replace and readback. Every other checkpoint writer must use that SAME lock path, not a separate lock. Invalid data persist the reserved request as invalid with no entry; tampered artifacts stop before code import and leave the reservation for reconciliation. It performs no network and no auto-retry. The optional separately authorized schedule observation must be persisted later with the same lock/revision discipline; the initializer does not invent a schedule.

Six synthetic temporary-state tests cover valid zero-funding initialization and no replacement, stale snapshot invalidation, code/manifest tamper, missing reservation, and malformed decimal input. These tests are not actual entry or market evidence.
