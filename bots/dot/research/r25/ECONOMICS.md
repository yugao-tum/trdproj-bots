# R25 same-5000 economics

## Findings and scope

All 36 prespecified A1250/A625/B × asset × two-by-two cost cases are retained, with 1,023 daily rows per case and both September 30 and October 19 endpoints. All 72 endpoint arithmetic PnLs are positive under this frozen grid. This does NOT make every path achievable: BTC B4 and SOL B4 have sampled negative Binance-local equity; all 16 affected endpoint rows are explicitly counterfactual. No sampled-negative ETH path is found here, which does not certify solvency or maintenance-margin adequacy. See role07 for the stronger daily-high bound and conditional MMR analysis.

There are only three underlying asset histories. The 36 sensitivity cases share funding, price and fee inputs and are not independent observations, experiments, or evidence of portfolio diversification. No portfolio summation or statistical significance claim is made. October prices/history were already observed: this is not investment out-of-sample evidence.

## Same-capital method

Every strategy starts with 5,000 USDT: 2,500 Kraken and 2,500 Binance, with no transfer, borrowing, lending, replenishment, reinvestment or cross-collateralization. A quantities are preserved exactly from the contract; B quantities are independently derived by exact Fraction floor at 1e-24 from the frozen two-venue cap. The 24 A and 12 B quantities are never inferred from rounded displays or unpublished derived JSON. All 36 satisfy the declared entry affordability bounds. Fixed mathematical quantities are not certified historical exchange lot sizes.

Daily NAV = remaining Kraken cash + q×Kraken close + Binance entry-fee-debited cash + cumulative actual funding cash + q×(Binance entry perp price − daily Binance mark close). Funding uses actual fundingTime strictly after 2024-01-01 00:00 UTC and rate×the funding event's mark, not a daily approximation. Daily funding cash and every intermediate NAV are retained, including negative daily/monthly contributions and post-failure counterfactual paths. No mark-based wealth is transferable across venues.

Endpoint liquidation value replaces mark with perpetual close and deducts q×cK×Kraken close and q×cB×perp close, in addition to the entry costs already debited. These are proxy valuations, not executable fills. Hypothetical liquidated NAV is also tabulated every day for sensitivity, without actually changing the held position. Both drawdown series start at initial NAV 5,000. Marked drawdown includes entry fees but not hypothetical exit fees; liquidation-value drawdown includes both. Neither is a liquidation-risk measure: small combined drawdowns can coexist with bankrupt local short collateral.

All return denominators are 5,000, never the old case budget or spot notional. Compound annualization is (ending liquidation NAV / 5000)^(365 / calendar_days) − 1; simple annualization is return×365/calendar_days. Calendar days include every UTC holding day: 1,004 through Sep30 and 1,023 through Oct19, treating each 23:59:59.999 endpoint as its inclusive daily close. This differs by one millisecond from literal elapsed time and has no meaningful numerical impact. Annualization is a historical descriptive transformation, not a forecast, and remains labeled counterfactual for failed paths.

## Benchmarks and financing assumptions

Idle cash holds all 5,000 with zero interest and zero cost. Matched-q buy-and-hold buys the same q at the same Kraken entry cost, holds the same inventory, retains all unspent capital as zero-yield cash, and sells with the same Kraken exit cost. It has no futures, funding receipts, financing charges or short-margin risk. The corresponding 5000-normalized terminal PnL/return and daily marked/liquidated NAV are in the tables. This isolates hedged versus unhedged economics at the same inventory and total capital, rather than comparing strategy returns against a smaller notional denominator.

A separate full-5000 unlevered Kraken buy-and-hold comparator spends all 5,000 inclusive of entry cost. This is an alternative initial capital allocation, not an authorized transfer or a portfolio obeying the strategy's 2500/2500 split; it has greater spot exposure and risk. It is clearly separate from matched-q. All comparators and strategy assume no custody charge, tax, holding carry, deposit/withdrawal cost, financing cost, or interest income. These are unmeasured omissions, not evidence such costs are zero. Kraken current-fee plus buffer and Binance all-in stresses are conditional assumptions, not actual historical/account fees. The base cell is not described as conservative.

## Base-cell endpoint table

Costs cK=0.011 and cB=0.003. Dollar figures are USDT. CF marks known local-negative paths; conditional does not mean certified safe.

| Asset/case | End | PnL | Return /5000 | Annualized | Marked MDD | Matched-q buyhold PnL | Status |
|---|---|---:|---:|---:|---:|---:|---|
| BTCUSDT/A1250 | 2026-09-30 | 395.536944 | 7.9107% | 2.8065% | -0.3523% | 1175.440275 | conditional |
| BTCUSDT/A1250 | 2026-10-19 | 400.979234 | 8.0196% | 2.7906% | -0.3523% | 1127.370349 | conditional |
| BTCUSDT/A625 | 2026-09-30 | 197.987601 | 3.9598% | 1.4218% | -0.1763% | 588.371336 | conditional |
| BTCUSDT/A625 | 2026-10-19 | 200.711761 | 4.0142% | 1.4142% | -0.1763% | 564.309742 | conditional |
| BTCUSDT/B | 2026-09-30 | 785.579322 | 15.7116% | 5.4485% | -0.6997% | 2334.552026 | CF |
| BTCUSDT/B | 2026-10-19 | 796.388300 | 15.9278% | 5.4148% | -0.6997% | 2239.079933 | CF |
| ETHUSDT/A1250 | 2026-09-30 | 301.175866 | 6.0235% | 2.1492% | -0.3628% | 190.576445 | conditional |
| ETHUSDT/A1250 | 2026-10-19 | 305.333065 | 6.1067% | 2.1374% | -0.3628% | 40.715793 | conditional |
| ETHUSDT/A625 | 2026-09-30 | 150.765637 | 3.0153% | 1.0859% | -0.1816% | 95.400669 | conditional |
| ETHUSDT/A625 | 2026-10-19 | 152.846689 | 3.0569% | 1.0801% | -0.1816% | 20.381920 | conditional |
| ETHUSDT/B | 2026-09-30 | 598.256456 | 11.9651% | 4.1943% | -0.7207% | 378.561503 | conditional |
| ETHUSDT/B | 2026-10-19 | 606.514325 | 12.1303% | 4.1696% | -0.7207% | 80.877948 | conditional |
| SOLUSDT/A1250 | 2026-09-30 | 232.125972 | 4.6425% | 1.6634% | -1.0567% | 171.002114 | conditional |
| SOLUSDT/A1250 | 2026-10-19 | 235.873207 | 4.7175% | 1.6583% | -1.0567% | 12.792635 | conditional |
| SOLUSDT/A625 | 2026-09-30 | 116.181197 | 2.3236% | 0.8386% | -0.5442% | 85.588141 | conditional |
| SOLUSDT/A625 | 2026-10-19 | 118.056723 | 2.3611% | 0.8361% | -0.5442% | 6.402832 | conditional |
| SOLUSDT/B | 2026-09-30 | 460.956810 | 9.2191% | 3.2579% | -1.9885% | 339.576775 | CF |
| SOLUSDT/B | 2026-10-19 | 468.398085 | 9.3680% | 3.2466% | -1.9885% | 25.403673 | CF |

## Funding concentration, dependence, and October

Monthly funding blocks use UTC calendar months, including partial Oct1–19 as a partial month, not as a full-month comparison. Top-three share divides the three largest positive months by all positive monthly funding; negative months are reported separately. The additional top-three/net share can exceed 100% when negative months offset gains. HHI uses positive monthly cash weights, not case counts. These shares are quantity-invariant for each asset, not independent case evidence.

| Asset | Funding through Oct19, A1250 base | Negative months | Top-3 positive-month share | Positive-month HHI | Oct funding, A1250 base | Oct continuous marked change | Oct hypothetical exit-PnL change |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 450.139104 | 3 | 28.658% | 0.052589 | 4.091504 | 4.816196 | 5.442290 |
| ETHUSDT | 339.490491 | 3 | 33.399% | 0.068593 | 2.096000 | 2.067021 | 4.157198 |
| SOLUSDT | 270.513379 | 8 | 43.327% | 0.097994 | 2.121473 | 1.560492 | 3.747235 |

October is the continuation of the January position, not a sell/reopen after September. The October endpoint-PnL difference includes changed endpoint basis and changed hypothetical exit costs; it must not be mislabeled October funding yield. Every case's exact comparison is in october-increments.csv.

Daily funding per-unit Pearson correlations through Oct19 are BTC–ETH 0.870450, BTC–SOL 0.623896 and ETH–SOL 0.709373, with 1,023 contemporaneous UTC days. These are cash-amount correlations (funding mark exposure included), not funding-rate correlations. Market correlations use daily strategy NAV changes versus each coin's Kraken close-to-close percentage return, Jan2 onward, with 1,003/1,022 pairs. This avoids correlating trending NAV levels. Case correlations likewise use daily NAV changes. They remain descriptive, serially dependent and post-failure counterfactual where applicable; no inference, diversification guarantee, market-neutral certification or independent sample count is claimed.

## Full-grid cost sensitivity

The following retains all four fee cells for every asset/case at Oct19. The span combines quantity and cost effects where quantity changes; it is not a pure fee derivative. A quantities depend on cB as frozen; B has the same q across cB at a fixed cK because the Kraken cap binds.

| Asset/case | Min PnL | Max PnL | Grid span | Counterfactual cells |
|---|---:|---:|---:|---:|
| BTCUSDT/A1250 | 377.905313 | 400.979234 | 23.073921 | 0 |
| BTCUSDT/A625 | 189.161596 | 200.711761 | 11.550165 | 0 |
| BTCUSDT/B | 750.577027 | 796.388300 | 45.811274 | 4 |
| ETHUSDT/A1250 | 289.116405 | 305.333065 | 16.216659 | 0 |
| ETHUSDT/A625 | 144.728468 | 152.846689 | 8.118221 | 0 |
| ETHUSDT/B | 574.313786 | 606.514325 | 32.200539 | 0 |
| SOLUSDT/A1250 | 220.028738 | 235.873207 | 15.844468 | 0 |
| SOLUSDT/A625 | 110.126175 | 118.056723 | 7.930548 | 0 |
| SOLUSDT/B | 436.943405 | 468.398085 | 31.454680 | 4 |

All 72 endpoint rows, not just the base summaries, are in endpoint-economics.csv; both-endpoint grid ranges are in cost-sensitivity.csv. Positive endpoint combined PnL cannot rescue a failed local account and is not an executable performance claim.


## Reproduction scope
The accompanying code-only bundle requires separately supplied, hash-matching declared source inputs. Original data and full generated ledgers are retained locally and are not in this repository. Exact future reacquisition is not guaranteed. The isolated local verification receipt covers reconstruction with the frozen local inputs; it is not a claim that this public package is self-contained.

## Frozen SMA200 benchmark completion
The original market/case/funding correlations did not include the frozen BTC lagged-SMA200 PnL reference. The appended SMA200 report and full 288-row correlation table complete that comparison for all 36 cases without retuning. Daily and 33-full-month conclusions differ materially; no GUIDE cutoff or pass is inferred. Failed paths remain counterfactual diagnostics.
