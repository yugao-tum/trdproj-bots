# C46 normalized evidence contract (v1, offline only)

All fixture documents are synthetic. The matcher consumes a normalized object with arrays `tokens`, `deposits`, `fills`, `leaves`, `allocations`, `executions`, and `synthetic`. It is not an ABI decoder, Merkle verifier, archive indexer, or finality oracle. A matched result is conditional on evidence assertions supplied by a caller; identifiers or evidence strings alone do not authenticate that evidence.

## Data types and identities

- Atomic amounts: canonical nonnegative decimal strings, never floats or human-unit quantities. Positive allocation amounts only. Decimal metadata: integer registry value bound to chain and token, not a symbol guessed globally.
- Chain IDs and log indexes: integers. Addresses, contract IDs, bundle IDs, leaf IDs and transaction hashes are retained exactly; a production adapter must canonicalize EVM bytes20/bytes32 without losing distinctions. Synthetic labels are deliberately not valid mainnet addresses.
- Leaf-entry identity: `(chain, spoke_pool, bundle, leaf, token, decimals, address)`. A leaf with multiple refund addresses is flattened into separate entries; the adapter must preserve array index/address correspondence. `amount_raw` is the selected refundAmount, NEVER `amountToReturn` (which is a bridge-to-HubPool amount).
- Cash event identity: `(chain, tx_hash, log_index)`. Same event replay is deduplicated; conflicting data or bindings to different leaf-entry identities are refused. Multiple distinct apparent transfers for a leaf remain unknown rather than being summed.

## Required normalized records

1. `tokens`: chain, token, decimals. Duplicate metadata is unknown/rejected rather than selected arbitrarily. This is a supplied registry, not remotely verified here.
2. `deposits`: id, origin_spoke, finalized boolean, complete relay object.
3. `fills`: id, origin_spoke, finalized boolean, type (`fast` only supported), full relay object; repayment {chain, token, decimals, address}; mapping_evidence reference.
4. `relay`: origin_chain, destination_chain, deposit_id, depositor, recipient, exclusive_relayer, input_token, output_token, input_amount, output_amount, fill_deadline, exclusivity_deadline, message. Full normalized equality is required. EVM/SVM conversion, zero-address outputToken substitution and signed parameter updates require a separately validated adapter; this matcher does not infer them. Duplicate source deposits remain ambiguous.
5. `leaves`: leaf-entry identity, amount_raw, components_complete boolean, components array. Each component holds allocation_id, fill_id (or explicit null for deposit refunds), kind and amount_raw. Sum must equal the entry's full refundAmount. Mixed deposit/relayer components are allowed in the description but only explicit relayer components are matched. Completeness and membership are evidence assertions, not cryptographic checks.
6. `allocations`: leaf-entry identity, id, fill_id, kind (`relayer_repayment`), amount_raw, allocation_evidence reference. Per-fill allocation must be supported, never pro-rata-guessed. Missing proof yields unknown; source deposit refunds are rejected even if paid through an ExecutedRelayerRefundRoot event.
7. `executions`: leaf-entry identity, tx_hash, log_index, amount_raw, status (`paid` or `deferred`), finalized boolean, transfer_evidence reference, route (`direct` or `deferred_claim`). A deferred claim additionally requires claim_to_leaf_evidence; actual deferred balances aggregate by token and account, so a claim amount alone cannot identify a leaf. The destination address here is the verified recipient; an address-redirection adapter must explicitly preserve account and final recipient mapping before use. Unsupported redirects stay unmatched.

## Outputs

`matched`: explicit component, exact repayment identity and one finalized cash transfer are supplied. `rejected`: contradictory identity, prohibited refund kind, duplicate attribution or malformed supported values. `unknown`: absent/ambiguous evidence, aggregate allocation, deferred payment, missing source, or unconfirmed cash. `unallocated_amount_raw` is the leaf amount not attributed as cash by this matcher; it may include depositor components or pending claims and is NOT receivable valuation or a loss.

No LP fee, bad-debt deduction, currency conversion, economic return or PnL is calculated. Refund amounts are treated as already net protocol amounts and preserved without another fee subtraction. Missing payments remain zero attributed cash, not an additional bad-debt expense. No capital/reuse scheduling or investment decision is implemented.

Unsupported/remaining: proof validity, root challenge success, deployment/version identity, source completeness, token mappings at the relevant block, reorgs, event extraction, transaction success receipts, transfer token behavior, gas, inventory flows, signed-update normalization, Solana handling, historical availability and actual real samples. Do not feed untrusted malformed production data without a validating adapter; this is an offline contract prototype.
