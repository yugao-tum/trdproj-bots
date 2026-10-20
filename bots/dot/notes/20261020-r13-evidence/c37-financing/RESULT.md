# C37 complete retained-receipt decoding (r13-04)

## Result
The full 12 retained receipts contain 1,295 logs, not the abridged r12 payload. All logs were extracted in original log-index order with raw topic/data retained locally. 1,229 decode to supported official event schemas; 66 events across 29 topic signatures remain explicitly unclassified, with zero schema mismatch. All 80 occurrences of 0xe413… decode to Aave LiquidationCall, including 68 in the large first transaction. The decoder never discards an unknown log.

**Three transactions have positive borrowed-financing evidence, nine remain unknown; zero proven self-funded.** This corrects the r12 all-unknown conclusion for the three retained temporal samples. Official Balancer mainnet deployment output binds the emitting Vault address 0xba12222222228d8ba445958a75a0704d566bf2c8; Keccak of FlashLoan(address,address,uint256,uint256) matches 0x0d7d75… exactly. Each recipient equals the transaction's liquidation payment address, and exact-amount disbursement plus repayment transfers are retained.

- Temporal 03 / 0xf02dce79fc5e8ce80e658c167bc32f0f248d3c3e6984bb164842582d2b5c5cb9: WETH raw loan 149982084406354801, fee 0. Disbursement log 231, WETH-to-USDT route logs 232–234, debt payment log 245 (USDT 251655927), liquidation 246, Vault repayment 253, FlashLoan 254. Borrowed financing is verified; it is not a same-token loan-to-debt match.
- Temporal 05 / 0x72d4ff6861ee338250d0f3a9f08a5d94c24984beb72d058491dd74aa300b36e0: USDC raw loan 1043653946, fee 0. Disbursement 540, same amount debt payment 550, liquidation 551, repayment 558 directly from swap pool to Vault, FlashLoan 561. Repayment need not originate from the recipient to count as a Vault return.
- Temporal 06 / 0x61206dc84f45aa8eea92203fe7dbb4bbf2e2ce0ff6ea22420ccefb07de023f6c: USDT raw loan 77686217402, fee 0. Disbursement 46, same amount debt payment 56, liquidation 57, Vault repayment 62, FlashLoan 63.

Amounts are raw token units, not USD or normalized profit. FlashLoan event emission follows repayment; log order must not be mistaken for loan origination time. A positive event and transfer chain establish borrowed participation, not that every fungible unit exclusively came from borrowing, nor who ultimately owns the contract.

## Evidence and scope
All 19 input-manifest SHA-256 digests verified before extraction. Remote dedup snapshot e068c98ad3f5a9aa7834e55ac2ef6caf210b7dd9 read in full programmatically: known and claims baseline retained; this is C37 evidence supplementation only. No new mechanism, backtest, qualification or PnL. Official source files and immutable Git blob/content hashes are in abi-source-bindings.json. Balancer IVault was also refetched at commit e91a2b643a49856f51a648d175667c1b48cf3377, matching the first read's blob c55f9d25c1a0b76975ca03229302f0c76a7608c7. Aave core v1.19.3 and origin interfaces, GHO token, Uniswap v2/v3 and ERC20 interfaces support schema decoding. Signature compatibility does not establish bytecode equivalence for every emitter. Positive financing is separately restricted to the official Vault deployment address.

Sources:
- https://github.com/balancer/balancer-v2-monorepo/blob/e91a2b643a49856f51a648d175667c1b48cf3377/pkg/interfaces/contracts/vault/IVault.sol
- https://github.com/balancer/balancer-deployments/blob/master/v2/tasks/20210418-vault/output/mainnet.json (frozen blob 609ec8f9c52e777ed030619233dee0f4a0f420e9)
- https://github.com/aave/aave-v3-core/blob/v1.19.3/contracts/interfaces/IPool.sol (blob ef306e737f93a6ae9a4e54fb2ed3684aee35b64f)

Access window 2026-10-20 08:48–08:51 UTC. No denied source, no RPC, no keys, no trades, no Pi/meiying/OpenCode calls. Two connector-schema mistakes executed no source action and were corrected once. No web/X search was needed because this is complete-local-receipt evidence decoding, not discovery.

## Limits and tests
17 deterministic tests pass: Keccak reference vectors and non-SHA3 check; known event hashes; all 12 receipts / 1,295 logs / 80 liquidations; zero decode mismatch; no own-funds inference; three positive loans with disbursement/return; false emitter and wrong recipient rejected; truncated payload/invalid bool/address rejected; unknown logs preserved. Unknown signatures have not been assigned guessed meanings. Full semantic decoding of those 66 peripheral/custom events remains incomplete. Trace/prestate and historical implementation bindings are not present and were not requested again. Nine unknown financing classifications are deliberately not upgraded from absence of a matched event. In particular, tx1's many GHO/burn/deficit events and token flows do not prove the pre-transaction source of the payer's capital.

Artifacts: complete-log-decoder.py; test-decoder.py; decoded-events.json; financing-classification.csv; abi-source-bindings.json; unknown-event-inventory.json; tests.log. The complete decoded raw event archive and source body cache stay local; publish aggregate CSV/result/code/hash bindings only. Replay requires the retained inputs and source cache; do not claim the small public subset alone is fully portable.

Runtime: native OpenAI agent, task continuation-r13-04. Exact model identifier is not exposed in this child runtime and is recorded unknown, not guessed; requested reasoning xhigh, actual effort not introspectable. Native task count 1; DeepSeek/OpenCode task count 0. Cost unknown.
