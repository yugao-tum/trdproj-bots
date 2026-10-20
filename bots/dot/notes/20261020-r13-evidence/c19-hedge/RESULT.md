# C19 r13: authentic synchronized pilot, conditional accounting only

Completed 2026-10-20 UTC. Native OpenAI agent, actual model ID not exposed; assigned xhigh. External model calls 0; OpenCode/Pi 0. Task continuation-r13-10. Existing C19 improvement overlaps known A-A1-funding-carry. No new mechanism, executed trade, qualified outcome or full historical strategy backtest.

## Evidence acquired
Before new price observations, froze earliest seven days in existing funding window: 2024-01-01 00:00 UTC to 2024-01-08 00:00 UTC. Official January 2024 spot, USD-M perpetual trade and mark 1h archives for BTCUSDT, ETHUSDT and SOLUSDT: 9 ZIPs plus 9 CHECKSUM files, all HTTP 200 and SHA256 verified. Each monthly archive has 744 rows; all nine pilot grids contain 169 hourly timestamps including the exit endpoint, with zero duplicate or missing hours. Synchronized pilot: 507 rows. Prices are USDT/base coin; timestamps milliseconds; bar close timestamp minus open is 3,599,999 ms. Funding raw timestamps and eight-hour interval fields retained from previously verified immutable funding CSV; pilot raw/normalized offsets at most 1 ms. These clocks align at bar-open resolution, not proven simultaneous executable quotes.

## Fixed example, not an ex-post coin choice
BTC fixed before outcomes. Own capital 5000 USDT, 1200 spent on spot, same fixed quantity short, no rebalancing. Entry spot/perp trade opens are adversely shifted 5bps per leg; exit likewise. Assumed fees spot 10bps and perp 5bps each side on actual notional. Initial short collateral equals actual short entry notional. First and exit-instant funding excluded. Twenty eligible funding rates applied to contemporaneous mark-bar open as an explicit settlement-mark proxy.

- Quantity: 0.02836562797781254 BTC.
- Funding proxy cash: +4.80474354 USDT.
- Entry/exit fees: 1.79983153 / 1.86862757 USDT; adverse fills already embedded in price PnL.
- Conditional final cash: 4999.89694066 USDT; net -0.10305934 USDT.
- Initial venue cash committed: 2401.46288219 USDT.
- Minimum collateral equity minus short mark notional: -197.31044832 USDT. The fixed no-top-up example FAILS a continuing full-collateral condition. It is not a demonstrated unlevered feasible strategy. No liquidation conclusion follows without historical margin rules. The ending cash is a counterfactual accounting continuation, not capital-feasible realized return.

## Accounting and verification
conditional-hedge-ledger.csv separates external idle cash, margin deposit, funding cash, spot MTM, perpetual mark MTM, basis, each fee and final realized hypothetical cash. No notional sale proceeds credited to short cash. Equity identity: idle + spot mark value + margin deposit + funding + short MTM. Exit returns margin only once and realizes the trade-price, not mark-price, short PnL. 169 equity reconciliations and exit identity pass; 8 separate tests cover hedge signs, negative funding, actual-notional fees, boundaries, independent exit identity, grids and preservation of all five input hashes. Tests are not independent market outcomes.

## Sources and exact gaps
[Official archive documentation](https://github.com/binance/binance-public-data) describes spot/futures candle fields and SHA256 sidecars. [Official USD-M documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) distinguishes candle mark values from markPrice attached to an actual funding charge. Full downloaded source bodies, UTC times and hashes are retained in archive-source-manifest.json/raw. No live account or REST trading endpoint used.

Exact historical funding-charge markPrice, executable fills, historical fees/quantity filters, margin tiers and intrahour collateral survival remain unknown. Candle opens cannot establish those facts. No denied requests, no retries, no X discovery needed for this narrowly defined official data acquisition. Full 33-month extension would require 288 additional ZIPs plus 288 CHECKSUM requests (576), beyond this role's 64 dataset-call envelope; not started. More prices alone will not fix settlement-mark or capital feasibility.

## Delivery boundaries
Publish only this report, scripts, manifests and aggregate reconciliation/tests as appropriate. Keep raw/ and synchronized-pilot.csv local: they contain market archives/extracts. The hypothetical derived ledger is local unless parent decides an aggregate-only public presentation. Budget: 18 dataset calls, 2 raw documentation GETs, 1 web open call (2 bodies), 1 web find call (2 operations), 0 searches, 0 external model calls. Cost unknown. No full-window funding-bound recomputation. No frozen/other-agent files edited. Parent alone batches publication.

Publication clarification: the assumed fees/slippage in this conditional example are not the GUIDE 0.30%-per-side admission hurdle. No admission or cost-hurdle pass is claimed.
