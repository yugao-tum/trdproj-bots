# Frozen historical methodology

## Timing and status

These are fixed retrospective historical simulations. Rule freezing preceded each rule's run, but does not make the 2025+ time split genuinely unseen future data. No strategy promotion, profitability guarantee or live execution claim follows from reproduction.

- Original C21–C24: preregistration includes a clarification dated 2026-10-19 16:22 UTC before the full historical run. The output freeze was recorded at 2026-10-19T17:06:34.753771+00:00
- Half-capital sensitivity: preregistration dated 2026-10-19 UTC; reviewed code/fixture execution freeze recorded at 2026-10-19T18:39:27.237464+00:00
- C40: rules dated 2026-10-19 18:49 UTC; preregistration file freeze recorded at 2026-10-19T18:50:05.237985+00:00; execution freeze recorded at 2026-10-19T18:58:33.048802+00:00

Original preregistration SHA256 values (the instruction-style originals are not included):

- C21–C24: a06b26eb52b99e315ebdcc8cca368e68d123b3889602fcd1e3d227d154c9453e
- Half-capital: 102a3ab2688bd6acdf5799cf6af0166c24033dff14c4917154017f187fd6d003
- C40: a09d74912129d590e6121670bfc76f530df23a44e15d24e1f8a63a620bd0bdff

## Common accounting

Each scenario starts with 5,000 USDT independently, with no leverage, borrowing, shorts, outside transfers or interest. Fees are a fixed 0.003 or 0.006 times each actual traded notional, on entry, rebalance and exit. Sales execute before buys. Spot and sensitivity buy quantities shrink when necessary to retain nonnegative cash; C40's fixed budget is checked before entry. Holdings and cash may not be negative.

Signals use only the preceding completed day or earlier. Execution is at the current daily open; the final sample day's close forces liquidation and charges its fee. Final-day rule trades are retained. The original screen and half-capital sample run from 2024-01-01 through 2026-09-30. C40 starts 2024-01-02 to allow a complete preceding funding day. Prices from 2023 are warmup only.

The 2025-01-01 retrospective split carries the actual 2024-12-31 holdings, cash and total NAV forward. Earlier entry fees are already present in carry-in NAV, and are not charged twice. Both period return on actual start NAV and contribution to fixed 5,000 capital are reported. CAGR uses full calendar days with exponent 365/day_count. Drawdown is based on daily close NAV including the period start NAV.

## Original four mechanisms

Capital: 2,500 USDT at the venue and 2,500 idle outside it. On each rebalance, target invested notional is min(2,200, 0.9 × current venue NAV at the execution open).

- C21: On Monday, hold SOL if the previous close exceeds the simple mean of the previous 200 closes; otherwise cash
- C22: On Monday, rank BTC, ETH and SOL by the previous close divided by the close 60 days earlier minus one. Hold only the highest with momentum strictly above zero, otherwise cash. Exact ties follow the original BTC, ETH, SOL iteration order (and frozen 1e-15 comparison)
- C23: SOL simple 14-change average-gain/average-loss RSI, not Wilder smoothing. Enter if the previous-day RSI is strictly below 30. Exit if strictly above 50 or after 14 calendar holding days. Evaluate daily for next-open execution; an exit does not also reenter that day
- C24: Hold BTC, ETH and SOL equally by value, rebalancing each Monday

## Single half-capital sensitivity and passive benchmarks

Only initial venue deployment and target cap are halved: venue 1,250, idle outside 3,750, invested cap 1,100. Total capital remains 5,000, target fraction remains 0.9 and dynamic diagnostic threshold remains 2,500. The four mechanism rules, dates and accounting are unchanged. No other scaling or parameter search is permitted.

SOL_HODL invests 1,100 notional in SOL at the 2024-01-01 open. EW_HODL divides 1,100 equally among BTC/ETH/SOL at that open. Each holds fixed quantities without intermediate rebalancing and exits at 2026-09-30 close, with both costs applied. Initial fees come from the 1,250 venue balance. SOL_HODL is paired with C21/C23 and EW_HODL with C22/C24 for descriptive risk comparison, not proof of alpha.

## Fifth mechanism: C40 spot proxy

BTC is the declared primary symbol; ETH and SOL are predeclared same-mechanism sensitivities, each with its own 5,000-capital scenario. Venue deployment is 1,250, idle capital 3,750, invested cap 1,100 and fraction 0.9.

When flat, buy at today's open if all three completed funding observations on the preceding UTC day (00:00, 08:00, 16:00) are strictly negative and that day's close is at least 1.01 times the minimum close in the previous 20 days including that day. Today's 00:00 funding event is never used in today's entry decision.

Exit at today's open if the preceding day's 08:00 and 16:00 funding observations are both nonnegative, or the entry date plus seven calendar days has been reached. Do not reenter on an exit day. There is no intraday stop, futures holding or funding income. This is a simplified funding-sign proxy, not a replication of a broader discretionary crowding strategy; historical open interest/CVD is unavailable. See the preserved rule bullets in C40_PREREGISTRATION.md.

## Capital diagnoses and failure interpretation

Record initial/additional contributed venue capital including fee buffers, pretrade open marks, closing venue NAV and cash plus sum(quantity × each asset's daily high). The 2,500-USDT dynamic limit is a strict study interpretation of a roughly 2,500-per-venue guideline, not a claim that the guide explicitly defined dynamic NAV. An observed open/close mark above it is a confirmed observed-mark breach; the sum of nonsynchronous daily highs is only a possible upper-bound breach. Daily bars do not establish intraday executable depth.

Retain full, 2024 and 2025+ period results, fee-doubling stress, monthly PnL and the original program's best-month-removal calculation. For C40 the preregistered economic gate fails if full-period CAGR on the 5,000-capital account is below 8% and there is no separate evidence of a ≥3% low-trend-correlation portfolio role. This package neither adds that evidence nor claims an independent-event gate passed. Episodes, months and cross-coin observations need event-cluster review before independence claims.

Stop on input hash/calendar/schema failure or accounting illegality. Do not replace data or alter thresholds to obtain favorable results. Negative results, zero signals, insufficient samples and capital-limit diagnostics must remain visible.
