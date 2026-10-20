# C24 fixed 5-percentage-point band: protocol frozen before variant results
Frozen at 2026-10-20 09:28 UTC. Retrospective research, not a historical preregistration.

Only one variant, no optimization: keep BTC/ETH/SOL, Monday open checks, 5000 total / 2500 initial venue / 2500 idle cash, target min(2200, 90% venue equity), sell before buy, actual-notional costs 0.003 and 0.006, final close liquidation. Use original Portfolio and simulate code unchanged except subclass interception of C24 rebalance requests.

At Monday open define venue equity A=cash+marked holdings, per-asset current weight value/A and target weight min(2200,0.9*A)/(3*A). Rebalance if any absolute per-asset difference exceeds 0.05. Initial zero holdings always enter. To preserve original position target ceiling rather than silently authorize excess risk, a Monday total position above min(2200,0.9*A) also forces the original rebalance, even inside the band. Non-Monday price drift and venue NAV over 2500 remain measured violations, not retroactively corrected. No cash withdrawal/transfer feature added. Exactly 5pp is not a trigger; hard target-cap override is strict with original EPS.

Input 2023-01-01..2026-09-30, original simulation 2024-01-01..2026-09-30 (1004 days); 2023 warmup only. Compare 2024, carry-in 2025-01-01..2026-09-30 retrospective holdout, full period. Same initial cash and cost and terminal liquidation for both. This cached history was previously visible; no genuinely unseen OOS claim.

Report PnL, fees, traded notional, turnover/5000, maximum drawdown, average marked risky holdings, directional mark-to-market gross PnL, venue violations, contiguous episodes. Require lower costs AND clear net/risk improvement in both cost cases and holdout, no capital violation, not mere lower exposure before suggesting improvement. Otherwise negative supplement only. Do not count months, symbols, legs, costs, or tests as independent outcomes. No 30-independent-results claim.
