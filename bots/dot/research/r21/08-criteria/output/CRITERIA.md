# Prospective evidence criteria — r21 role08

## Status and selection disclosure

These criteria precede any root-locked prospective entry reference. They do not initialize a virtual position or authorize a real transaction. ETH1250 is a post-hoc research priority selected after examining three assets and twelve r20 scenarios. Preserve every earlier scenario and failure. A prospective record can test its subsequent behavior but cannot retroactively make the original choice blinded or a new mechanism.

The prior conditional ETH case had venue-capital CAGR4.524% versus total-capital2.306%; trend correlation was approximately−0.051 daily but+0.382 monthly over33 calendar blocks. Those are in-sample descriptions, not a forward low-correlation certificate. Source: r20/08-benchmarks/output/RESULT.md and RESULT.json, hashed in manifest.json.

## Fixed first review window

Count the first30 distinct actual ETHUSDT funding settlement timestamps strictly after the entry reference. Retain signed payments, including every negative payment. A duplicate response is not another outcome; a conflicting same-key response or unresolved missing period blocks a complete-window verdict. Thirty records alone do not prove there were no gaps. Schedule changes must be reconciled, not filled with assumed8-hour events.

The window is a descriptive checkpoint, not a forced stop, an IID sample, an accepted competition stage, or proof of annual profitability. At the currently observed8-hour schedule it would take about10 days, but timing remains conditional on actual scheduling. Continuous research/recording does not stop at30 or seven hours.

## Required paired reporting

- Actual observed funding records, signed conditional cash amounts, negative-payment share, date range, unique-event count, unresolved gaps and source outages.
- Accrued funding for the fixed first30-event window separately from all-to-date funding when observations continue. Top-three positive payment share is a concentration diagnostic only; zero positive sum yields null rather than a fabricated percentage.
- Complete assumed entry costs and hypothetical exit costs, with the observed quote/VWAP basis and quote valuation timestamp. No fee amortization, no hidden removal of entry costs and no replacement of missing executable exit quotes with mark price.
- Full quoted-exit conditional net value and nonannualized returns on both5000 total and2500 venue capital. A quote observed after the30th payment is labeled with its own timestamp, not passed off as the exact value at that settlement.
- Funding-only cost-recovery gap in USDT: max(0, full assumed entry+exit cost minus observed funding cash). This is not the total strategy P&L: basis/price changes remain in the separate full cash ledger.
- break_even_days stays null. No forecast assumes current or average funding remains constant. No annualized return is produced for the initial short window.
- Main0.003 and fixed0.006 cost cases retain the same quantity and are reported together; no favorable cost case is selected.

## Prespecified distinctions

1. Data-quality failure: invalid/missing/inconsistent prices or filters, failed freshness/depth checks, conflicting funding identity, unreconciled gaps, or missing protocol lock. Reject the affected entry/valuation or mark the window incomplete. Do not fabricate data or count it as an economic loss. A403 or429 is a source-operational state subject to the scheduler's stopping/backoff rules, not a strategy verdict.
2. Capital failure: observed margin equity at or below zero invalidates feasible-path status. Continue any later arithmetic only with a conspicuous counterfactual label. If positive, do not infer liquidation survival: historical/current maintenance tiers, deductions and execution costs still require their own evidence. Source-supported maintenance scenarios are separate, explicitly conditional diagnostics.
3. Economic weakness: negative cumulative funding, negative quoted-exit net P&L, concentrated gains or a cost-recovery shortfall are reported unchanged. A negative10-day net result including full round-trip costs does not by itself disprove a multi-year carry mechanism, and positive10-day results do not establish an annual edge. No automatic permanent failure threshold is invented after seeing outcomes.
4. Correlation: the initial window cannot certify portfolio low correlation. Later reports retain the same fixed trend-reference definition from r20 and show aligned daily and non-overlapping calendar-month results, sample counts and dependence. Fewer than two paired observations or zero variance yields null. No numerical 'low correlation' threshold is invented or optimized; even a point estimate with more observations is descriptive, not a statistical guarantee. A future formal acceptance rule must be separately frozen before it is applied, not chosen to fit these returns.
5. Qualification: none is self-awarded. Data collection, implementation tests, thirty observed settlements and a valid conditional ledger are different evidence stages. Operator recognition and remaining GUIDE requirements stay separate.

## Verification and use

criteria.py is an independent offline reporting helper, not the position ledger or a network collector. It requires exact ETH funding event keys, explicit gap reconciliation and an explicit timestamp for supplied quote-valued net P&L. Root/role04 owns protocol lock and ledger state; role06 owns request scheduling and atomic ledger/cursor persistence. No real market observation has been evaluated by this helper.

Run python -m unittest test_criteria.py. Eighteen synthetic boundary tests pass. No network, account, order, wallet or credential access is present.
