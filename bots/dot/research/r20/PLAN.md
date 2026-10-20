# r20: C19 exact funding-settlement mark evidence

This is a continuation/supplement of existing C19, not a new mechanism. Previous frozen tests remain unchanged. A public Binance connector capability probe returned actual fundingTime, fundingRate and markPrice for four BTC payments on 2024-01-01/02. This is a concrete source breakthrough; it is not proof of profit. Inputs/results already seen in prior rounds and the probe are disclosed; no claim of blinded discovery.

## Frozen economic definitions
- Fixed assets BTCUSDT, ETHUSDT, SOLUSDT, no asset selection.
- Fixed window 2024-01-01 00:00 UTC to 2026-09-30 23:59:59.999 UTC.
- Preserve all returned actual funding timestamps and recorded settlement marks. Reconcile rates against previous archive; never replace actual mark with candle OHLC without a separate label.
- Entry is first daily-open price proxy, exit final daily-close price proxy. These are conditional prices, not our executable fills. Exact funding amount is conditional on a specified constant quantity: short receives q * rate * settlement mark. Include payments strictly after entry and no later than exit, not the payment coincident with opening.
- Total 5,000 USDT. One venue starts with 2,500, external cash 2,500. Two prespecified spot purchase cash budgets: 1,250 and 625, inclusive of spot entry costs. Remaining venue cash funds perpetual collateral and entry fee. Buy q = budget / [spot entry * (1+cost)], short identical q. No borrowing, no dynamic resizing, no transfers, no reinvestment, no optimizing allocations.
- Main cost 0.003 per side per leg; fixed stress 0.006. Perpetual entry fee deducted from collateral once, exit fee once; spot fee already included in entry quantity, sale cost on exit proceeds. Use Decimal and explicit conservation identities.
- Record cash, spot value, perp P&L, funding and margin equity separately. Funding settlement marks give observed collateral diagnostics, not continuous liquidation proof. Daily mark high/low provide conservative intraday bounds; no unknown maintenance tier fabricated. A negative observed margin equity invalidates feasible execution; lack of negativity is not proof of survival. Report the distinct stricter fully-collateralized notional test, not as an invented exchange liquidation rule.
- Report all 12 scenarios (3 assets x 2 budgets x 2 costs), never select the winner. Include total-capital return/CAGR and leg-denominator labels, spot-hold benchmark with same cost/cash budget, funding-only cash contribution, basis/P&L decomposition and data coverage.
- Treat approximately 2,500 venue rule separately from a stricter mark-to-market hard cap, since GUIDE does not mandate daily liquidation. Do not certify qualification from a favorable interpretation.
- Historical fee tier, quantity filters, actual fills and maintenance margin remain unknown unless independently sourced. Full conditional cash accounting is not real trading or qualified backtest.

