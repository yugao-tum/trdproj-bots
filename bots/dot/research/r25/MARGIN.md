# R25 role07: Binance-local margin prefix evidence

All 36 cells are retained; 72 conditional hypothetical local endpoints remain visible. Exactly 16 endpoints (eight BTC/SOL B bankruptcy cases × two dates) are marked post-local-bankruptcy; the other 56 are not. Conditional maintenance-plus-reserve failures are separate from this zero-equity classification. There is no liquidation-proceeds estimate and no actual historical liquidation claim. Quantities derive from the contract, Kraken entry, and Binance entry without loading another role’s quantity matrix. The optional matrix check confirms all 36 exact rational quantities.

## Conclusions
- Eight cells have proven local zero-equity failure: the four BTC B and four SOL B cells. This is a concrete failure finding, not merely an uncertified label. Their later endpoint values are explicitly counterfactual.
- BTC B: first observed nonpositive funding-mark equity is 2024-11-13 16:00:00 UTC (before funding); first guaranteed daily-high failure is November 13. SOL B: first guaranteed daily-high failure is November 11, earlier than the first observed funding-mark negative at November 12 00:00:00.002 UTC.
- All 24 A cells and all four ETH B cells have positive conservative zero-equity lower bounds throughout the source window. This supports a zero-equity bound under this replay, not actual maintenance-margin or executable survival certification.
- ETH B minimum lower bounds are $163.6171–$177.9319. Its minimum zero-cum MMR safe bounds range from 3.0472196% to 3.3236529%. Under the explicitly hypothetical constant zero-cum rates through 2.5%, all four remain above maintenance across the conservative bounds; 5% can fail. These rates are sensitivity parameters, not historical tier evidence.

- Reserve sensitivity changes one conditional ETH result: ETH B cK=0.011/cB=0.006 has guaranteed headroom failure on 2025-08-24 under 2.5% MMR plus its 0.6% mark-based exit reserve (minimum lower headroom −$2.833982). The other three ETH B cells retain positive bounds at 2.5% plus their respective reserves. This is not a zero-equity bankruptcy finding.
## Mathematical scope and thresholds
Main safe-MMR thresholds and sensitivity assume cum=0 and exclude any exit-cost/liquidation reserve. Separate with_exit_reserve_sensitivity subtracts cB*q*mark from headroom, solely as an all-in exit-cost stress reserve. It is not evidence of historical liquidation fees. The safe-MMR bound with this reserve is the unreserved bound minus cB. Actual historical bracket, cumulative deduction and liquidation-reserve rules remain unavailable.
Let C=2500−cB*q*P. Binance-local equity E(t)=C+F(t)+q(P−m(t)), with short funding F(t)=Σ q*m_i*r_i for actual settlement timestamps strictly greater than entry. Kraken inventory, acquisition cost, and fees never enter Binance-local equity. No venue transfers, resizing, or replenishment are permitted.
At every funding mark we evaluate before and after the cashflow. The zero-equity bankruptcy mark is P+(C+F)/q. For an assumed maintenance rule max(r*q*m−cum,0), headroom is E−max(r*q*m−cum,0). Where the unclamped requirement is positive, the threshold mark is (C+F+q*P+cum)/(q*(1+r)), and break-even r=(E+cum)/(q*m). Actual historical tier/rate/cumulative deduction, liquidation fee and engine timing are absent; hence no exact liquidation time is asserted.
For each UTC day, Fmin and Fmax include the starting balance and every actual intraday funding prefix, including negative payments. At observed daily high H, L=C+Fmin+q(P−H) and U=C+Fmax+q(P−H). L is a lower bound on all equity during the day, while U is an upper bound on equity at the high. L≤0 alone is merely a potential breach; U≤0 guarantees zero-equity failure at some time that day. For a hypothetical zero-cum r, subtract r*q*H from both bounds. A funding-mark breach is an observed model-state breach; the first daily guaranteed breach identifies a day, not an intraday timestamp. Earlier unobserved actual liquidation cannot be excluded.
An entire day positive at L is stronger than simply observing positive funding marks. Quantities use exact Fraction and floor-to-1e−24 for B; numerical cashflow replay uses IEEE double. Test tolerances are 1e−7 dollars or tighter, far below reported headroom gaps. This is not historical exchange lot sizing.

## All cells (dollar headroom; zero-cum MMR bounds)
|Cell|Min observed equity|Min daily lower bound|Safe MMR bound %|First observed ≤0|First guaranteed high day|First potential high day|
|---|---:|---:|---:|---|---|---|
|BTCUSDT_A1250_cK0.011_cB0.003|431.886365|394.927472|10.630901|-|-|-|
|BTCUSDT_A625_cK0.011_cB0.003|1464.797438|1446.297517|77.778478|-|-|-|
|BTCUSDT_B_cK0.011_cB0.003|-1607.498255|-1680.902629|-22.782024|2024-11-13T16:00:00+00:00 before|2024-11-13|2024-11-13|
|BTCUSDT_A1250_cK0.011_cB0.006|434.322910|397.474151|10.731433|-|-|-|
|BTCUSDT_A625_cK0.011_cB0.006|1466.019365|1447.574613|78.080000|-|-|-|
|BTCUSDT_B_cK0.011_cB0.006|-1614.921003|-1688.325377|-22.882628|2024-11-13T16:00:00+00:00 before|2024-11-13|2024-11-13|
|BTCUSDT_A1250_cK0.014_cB0.003|431.886365|394.927472|10.630901|-|-|-|
|BTCUSDT_A625_cK0.014_cB0.003|1464.797438|1446.297517|77.778478|-|-|-|
|BTCUSDT_B_cK0.014_cB0.003|-1595.345894|-1668.533095|-22.681479|2024-11-13T16:00:00+00:00 before|2024-11-13|2024-11-13|
|BTCUSDT_A1250_cK0.014_cB0.006|434.322910|397.474151|10.731433|-|-|-|
|BTCUSDT_A625_cK0.014_cB0.006|1466.019365|1447.574613|78.080000|-|-|-|
|BTCUSDT_B_cK0.014_cB0.006|-1602.746681|-1675.933882|-22.782083|2024-11-13T16:00:00+00:00 before|2024-11-13|2024-11-13|
|ETHUSDT_A1250_cK0.011_cB0.003|1395.101356|1327.549450|49.112619|-|-|-|
|ETHUSDT_A625_cK0.011_cB0.003|1946.898752|1913.082940|141.381958|-|-|-|
|ETHUSDT_B_cK0.011_cB0.003|305.226711|171.041443|3.185492|-|-|-|
|ETHUSDT_A1250_cK0.011_cB0.006|1394.667364|1327.316754|49.250772|-|-|-|
|ETHUSDT_A625_cK0.011_cB0.006|1946.682733|1912.967764|141.796298|-|-|-|
|ETHUSDT_B_cK0.011_cB0.006|297.802332|163.617064|3.047220|-|-|-|
|ETHUSDT_A1250_cK0.014_cB0.003|1395.101356|1327.549450|49.112619|-|-|-|
|ETHUSDT_A625_cK0.014_cB0.003|1946.898752|1913.082940|141.381958|-|-|-|
|ETHUSDT_B_cK0.014_cB0.003|311.720123|177.931853|3.323653|-|-|-|
|ETHUSDT_A1250_cK0.014_cB0.006|1394.667364|1327.316754|49.250772|-|-|-|
|ETHUSDT_A625_cK0.014_cB0.006|1946.682733|1912.967764|141.796298|-|-|-|
|ETHUSDT_B_cK0.014_cB0.006|304.317709|170.529440|3.185381|-|-|-|
|SOLUSDT_A1250_cK0.011_cB0.003|688.550871|394.198648|10.902212|-|-|-|
|SOLUSDT_A625_cK0.011_cB0.003|1593.352945|1446.026933|79.903123|-|-|-|
|SOLUSDT_B_cK0.011_cB0.003|-1097.183910|-1681.709891|-23.421465|2024-11-12T00:00:00.002000+00:00 before|2024-11-11|2024-11-11|
|SOLUSDT_A1250_cK0.011_cB0.006|690.222918|396.747831|11.005509|-|-|-|
|SOLUSDT_A625_cK0.011_cB0.006|1594.191839|1447.305169|80.212958|-|-|-|
|SOLUSDT_B_cK0.011_cB0.006|-1104.604859|-1689.130840|-23.524818|2024-11-12T00:00:00.002000+00:00 before|2024-11-11|2024-11-11|
|SOLUSDT_A1250_cK0.014_cB0.003|688.550871|394.198648|10.902212|-|-|-|
|SOLUSDT_A625_cK0.014_cB0.003|1593.352945|1446.026933|79.903123|-|-|-|
|SOLUSDT_B_cK0.014_cB0.003|-1086.541354|-1669.337968|-23.318148|2024-11-12T00:00:00.002000+00:00 before|2024-11-11|2024-11-11|
|SOLUSDT_A1250_cK0.014_cB0.006|690.222918|396.747831|11.005509|-|-|-|
|SOLUSDT_A625_cK0.014_cB0.006|1594.191839|1447.305169|80.212958|-|-|-|
|SOLUSDT_B_cK0.014_cB0.006|-1093.940348|-1676.736962|-23.421501|2024-11-12T00:00:00.002000+00:00 before|2024-11-11|2024-11-11|


## Reproduction scope
The accompanying code-only bundle requires separately supplied, hash-matching declared source inputs. Original data and full generated ledgers are retained locally and are not in this repository. Exact future reacquisition is not guaranteed. The isolated local verification receipt covers reconstruction with the frozen local inputs; it is not a claim that this public package is self-contained.
