# R25 role08: matched-quantity basis, cost and collateral attribution

Offline exact-Fraction replay from frozen source files, without role03 or other R25 derived JSON. 36 cases × 2 endpoints; all four fee combinations retained. 12 fixed A references each get two Kraken-cost comparisons at each endpoint. B receives both b1250 and b625 matched-q anchors, not a selected winner. All returns use total 5000.

## Identity and interpretation
PnL = funding + q[(Kraken St−S0)+(Binance P0−Pt)] − cK q(S0+St) − cB q(P0+Pt). Same-q difference from old Binance spot/perp = q[(Kraken St−Binance St)−(Kraken S0−Binance S0)] + cB q(Binance S0+Binance St)−cK q(Kraken S0+Kraken St). Funding and perp cost/price effects cancel at matched quantity. Exact rational residuals are zero.
Old 5000 capital consisted of 2500 active same-venue capital plus 2500 idle. New 5000 is 2500 Kraken plus 2500 Binance. Moving the spot purchase out of Binance raises local Binance collateral by q×Binance S0×(1+cB). This is relocation of existing capital, not profit, funding alpha, or an extra 2500. It contributes exactly zero endpoint PnL at matched q but changes local solvency. Unrealized Kraken inventory cannot collateralize Binance. B expansion is a separate linear exposure effect, not venue improvement.
Each endpoint has one entry and hypothetical exit. September exit is not charged to the continuing October path. B mathematical quantities are floored at 1e-24; neither historical lot sizes nor executable quantities are claimed. Current fee stress assumptions are not historical/account fees. Observed negative-margin endpoints are counterfactual; absence of evidence does not certify survival with unknown MMR/cum/intraday ordering. No new mechanism, OOS or investment qualification.

## Complete A matched-quantity comparison (USDT)
| Asset/budget/cB | End | old same-venue | cK .011 PnL | basis delta | cost delta .011 | cK .014 PnL | cost delta .014 |
|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT/1250/0.003 | 2026-09-30 | 426.078352 | 395.536944 | -0.892659 | -29.648749 | 384.418031 | -40.767662 |
| BTCUSDT/1250/0.003 | 2026-10-19 | 430.124999 | 400.979234 | 0.117176 | -29.262942 | 390.006135 | -40.236041 |
| BTCUSDT/625/0.003 | 2026-09-30 | 213.275225 | 197.987601 | -0.446824 | -14.840800 | 192.421985 | -20.406416 |
| BTCUSDT/625/0.003 | 2026-10-19 | 215.300791 | 200.711761 | 0.058653 | -14.647683 | 195.219132 | -20.140312 |
| BTCUSDT/1250/0.006 | 2026-09-30 | 402.635201 | 383.272263 | -0.889999 | -18.472939 | 372.186483 | -29.558719 |
| BTCUSDT/1250/0.006 | 2026-10-19 | 406.965568 | 388.845713 | 0.116827 | -18.236682 | 377.905313 | -29.177082 |
| BTCUSDT/625/0.006 | 2026-09-30 | 201.540213 | 191.848038 | -0.445492 | -9.246683 | 186.299019 | -14.795702 |
| BTCUSDT/625/0.006 | 2026-10-19 | 203.707791 | 194.637845 | 0.058478 | -9.128424 | 189.161596 | -14.604673 |
| ETHUSDT/1250/0.003 | 2026-09-30 | 322.933348 | 301.175866 | -0.076372 | -21.681109 | 293.045524 | -29.811451 |
| ETHUSDT/1250/0.003 | 2026-10-19 | 325.753234 | 305.333065 | 0.049096 | -20.469266 | 297.657305 | -28.145026 |
| ETHUSDT/625/0.003 | 2026-09-30 | 161.657215 | 150.765637 | -0.038231 | -10.853347 | 146.695669 | -14.923315 |
| ETHUSDT/625/0.003 | 2026-10-19 | 163.068822 | 152.846689 | 0.024577 | -10.246710 | 149.004280 | -14.089119 |
| ETHUSDT/1250/0.006 | 2026-09-30 | 305.758161 | 292.171434 | -0.076144 | -13.510583 | 284.065319 | -21.616698 |
| ETHUSDT/1250/0.006 | 2026-10-19 | 309.476296 | 296.769292 | 0.048950 | -12.755954 | 289.116405 | -20.408841 |
| ETHUSDT/625/0.006 | 2026-09-30 | 153.059147 | 146.257782 | -0.038117 | -6.763248 | 142.199950 | -10.821079 |
| ETHUSDT/625/0.006 | 2026-10-19 | 154.920404 | 148.559419 | 0.024504 | -6.385489 | 144.728468 | -10.216440 |
| SOLUSDT/1250/0.003 | 2026-09-30 | 253.778107 | 232.125972 | -0.122394 | -21.529741 | 224.052732 | -29.602981 |
| SOLUSDT/1250/0.003 | 2026-10-19 | 256.611669 | 235.873207 | -0.489577 | -20.248886 | 228.279874 | -27.842219 |
| SOLUSDT/625/0.003 | 2026-09-30 | 127.018291 | 116.181197 | -0.061259 | -10.775835 | 112.140466 | -14.816566 |
| SOLUSDT/625/0.003 | 2026-10-19 | 128.436516 | 118.056723 | -0.245038 | -10.134755 | 114.256190 | -13.935288 |
| SOLUSDT/1250/0.006 | 2026-09-30 | 236.926258 | 223.386728 | -0.122029 | -13.417501 | 215.337546 | -21.466683 |
| SOLUSDT/1250/0.006 | 2026-10-19 | 240.705403 | 227.599443 | -0.488118 | -12.617842 | 220.028738 | -20.188547 |
| SOLUSDT/625/0.006 | 2026-09-30 | 118.583521 | 111.806876 | -0.061077 | -6.715568 | 107.778194 | -10.744250 |
| SOLUSDT/625/0.006 | 2026-10-19 | 120.475014 | 113.915374 | -0.244307 | -6.315333 | 110.126175 | -10.104532 |

## All B results and matched b1250 expansion (USDT)
Both anchor sizes and all exact components are retained in B-matched-anchor-expansion.csv. This table shows b1250 for compactness, not filtering cases.
| Case | End | matched-q venue delta | B expansion | B PnL | B return /5000 | Classification |
|---|---|---:|---:|---:|---:|---|
| BTCUSDT_B_bdual2500_k0.011_c0.003 | 2026-09-30 | -30.541408 | 390.042378 | 785.579322 | 15.711586% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.011_c0.003 | 2026-10-19 | -29.145766 | 395.409067 | 796.388300 | 15.927766% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.011_c0.006 | 2026-09-30 | -19.362938 | 380.223199 | 763.495462 | 15.269909% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.011_c0.006 | 2026-10-19 | -18.119854 | 385.752311 | 774.598025 | 15.491960% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.014_c0.003 | 2026-09-30 | -41.660321 | 376.819059 | 761.237089 | 15.224742% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.014_c0.003 | 2026-10-19 | -40.118865 | 382.296699 | 772.302834 | 15.446057% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.014_c0.006 | 2026-09-30 | -30.448718 | 367.032084 | 739.218567 | 14.784371% | Counterfactual after negative local margin |
| BTCUSDT_B_bdual2500_k0.014_c0.006 | 2026-10-19 | -29.060255 | 372.671714 | 750.577027 | 15.011541% | Counterfactual after negative local margin |
| ETHUSDT_B_bdual2500_k0.011_c0.003 | 2026-09-30 | -21.757481 | 297.080590 | 598.256456 | 11.965129% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.011_c0.003 | 2026-10-19 | -20.420170 | 301.181260 | 606.514325 | 12.130286% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.011_c0.006 | 2026-09-30 | -13.586727 | 289.933201 | 582.104635 | 11.642093% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.011_c0.006 | 2026-10-19 | -12.707004 | 294.495836 | 591.265129 | 11.825303% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.014_c0.003 | 2026-09-30 | -29.887823 | 287.338593 | 580.384117 | 11.607682% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.014_c0.003 | 2026-10-19 | -28.095930 | 291.860561 | 589.517866 | 11.790357% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.014_c0.006 | 2026-09-30 | -21.692842 | 280.214763 | 564.280082 | 11.285602% | Conditional accounting, not certified survival |
| ETHUSDT_B_bdual2500_k0.014_c0.006 | 2026-10-19 | -20.359891 | 285.197381 | 574.313786 | 11.486276% | Conditional accounting, not certified survival |
| SOLUSDT_B_bdual2500_k0.011_c0.003 | 2026-09-30 | -21.652135 | 228.830838 | 460.956810 | 9.219136% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.011_c0.003 | 2026-10-19 | -20.738463 | 232.524879 | 468.398085 | 9.367962% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.011_c0.006 | 2026-09-30 | -13.539530 | 221.541486 | 444.928215 | 8.898564% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.011_c0.006 | 2026-10-19 | -13.105959 | 225.719403 | 453.318847 | 9.066377% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.014_c0.003 | 2026-09-30 | -29.725375 | 219.555855 | 443.608587 | 8.872172% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.014_c0.003 | 2026-10-19 | -28.331795 | 223.698156 | 451.978030 | 9.039561% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.014_c0.006 | 2026-09-30 | -21.588712 | 212.289869 | 427.627414 | 8.552548% | Counterfactual after negative local margin |
| SOLUSDT_B_bdual2500_k0.014_c0.006 | 2026-10-19 | -20.676665 | 216.914667 | 436.943405 | 8.738868% | Counterfactual after negative local margin |

## Local collateral evidence
| Case | Old same-q collateral | New Binance collateral | First new negative evidence | Minimum daily lower bound |
|---|---:|---:|---|---:|
| BTCUSDT_A_b1250_k0.011_c0.003 | 1247.646146 | 2496.262668 | None | 394.927472 |
| BTCUSDT_A_b625_k0.011_c0.003 | 1873.129263 | 2498.129263 | None | 1446.297517 |
| BTCUSDT_B_bdual2500_k0.011_c0.003 | 12.689253 | 2492.577252 | 2024-11-13T16:00:00.000+00:00 | -1680.902629 |
| BTCUSDT_A_b1250_k0.011_c0.006 | 1243.928304 | 2492.547609 | None | 397.474151 |
| BTCUSDT_A_b625_k0.011_c0.006 | 1871.269684 | 2496.269684 | None | 1447.574613 |
| BTCUSDT_B_bdual2500_k0.011_c0.006 | -2.150907 | 2485.154504 | 2024-11-13T16:00:00.000+00:00 | -1688.325377 |
| BTCUSDT_A_b1250_k0.014_c0.003 | 1247.646146 | 2496.262668 | None | 394.927472 |
| BTCUSDT_A_b625_k0.014_c0.003 | 1873.129263 | 2498.129263 | None | 1446.297517 |
| BTCUSDT_B_bdual2500_k0.014_c0.003 | 20.048160 | 2492.599213 | 2024-11-13T16:00:00.000+00:00 | -1668.533095 |
| BTCUSDT_A_b1250_k0.014_c0.006 | 1243.928304 | 2492.547609 | None | 397.474151 |
| BTCUSDT_A_b625_k0.014_c0.006 | 1871.269684 | 2496.269684 | None | 1447.574613 |
| BTCUSDT_B_bdual2500_k0.014_c0.006 | 5.251906 | 2485.198425 | 2024-11-13T16:00:00.000+00:00 | -1675.933882 |
| ETHUSDT_A_b1250_k0.011_c0.003 | 1247.735743 | 2496.262399 | None | 1327.549450 |
| ETHUSDT_A_b625_k0.011_c0.003 | 1873.128994 | 2498.128994 | None | 1913.082940 |
| ETHUSDT_B_bdual2500_k0.011_c0.003 | 12.499306 | 2492.575621 | None | 171.041443 |
| ETHUSDT_A_b1250_k0.011_c0.006 | 1244.017634 | 2492.547074 | None | 1327.316754 |
| ETHUSDT_A_b625_k0.011_c0.006 | 1871.269148 | 2496.269148 | None | 1912.967764 |
| ETHUSDT_B_bdual2500_k0.011_c0.006 | -2.343048 | 2485.151242 | None | 163.617064 |
| ETHUSDT_A_b1250_k0.014_c0.003 | 1247.735743 | 2496.262399 | None | 1327.549450 |
| ETHUSDT_A_b625_k0.014_c0.003 | 1873.128994 | 2498.128994 | None | 1913.082940 |
| ETHUSDT_B_bdual2500_k0.014_c0.003 | 19.858776 | 2492.597586 | None | 177.931853 |
| ETHUSDT_A_b1250_k0.014_c0.006 | 1244.017634 | 2492.547074 | None | 1327.316754 |
| ETHUSDT_A_b625_k0.014_c0.006 | 1871.269148 | 2496.269148 | None | 1912.967764 |
| ETHUSDT_B_bdual2500_k0.014_c0.006 | 5.060334 | 2485.195173 | None | 170.529440 |
| SOLUSDT_A_b1250_k0.011_c0.003 | 1247.534844 | 2496.263001 | None | 394.198648 |
| SOLUSDT_A_b625_k0.011_c0.003 | 1873.129597 | 2498.129597 | None | 1446.026933 |
| SOLUSDT_B_bdual2500_k0.011_c0.003 | 12.849004 | 2492.579050 | 2024-11-11 daily-high (time unknown) | -1681.709891 |
| SOLUSDT_A_b1250_k0.011_c0.006 | 1243.817334 | 2492.548274 | None | 396.747831 |
| SOLUSDT_A_b625_k0.011_c0.006 | 1871.270350 | 2496.270350 | None | 1447.305169 |
| SOLUSDT_B_bdual2500_k0.011_c0.006 | -1.988885 | 2485.158101 | 2024-11-11 daily-high (time unknown) | -1689.130840 |
| SOLUSDT_A_b1250_k0.014_c0.003 | 1247.534844 | 2496.263001 | None | 394.198648 |
| SOLUSDT_A_b625_k0.014_c0.003 | 1873.129597 | 2498.129597 | None | 1446.026933 |
| SOLUSDT_B_bdual2500_k0.014_c0.003 | 20.207439 | 2492.601006 | 2024-11-11 daily-high (time unknown) | -1669.337968 |
| SOLUSDT_A_b1250_k0.014_c0.006 | 1243.817334 | 2492.548274 | None | 396.747831 |
| SOLUSDT_A_b625_k0.014_c0.006 | 1871.270350 | 2496.270350 | None | 1447.305169 |
| SOLUSDT_B_bdual2500_k0.014_c0.006 | 5.413449 | 2485.202012 | 2024-11-11 daily-high (time unknown) | -1676.736962 |
