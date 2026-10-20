# CapitalAccount v1 (long-only spot, no network)

Import `CapitalAccount` from `capital_account.py`. Frozen SHA256: `814528b5a1a70ea13e6aa258ce13b12c64516c8683d12456ec60e3df368a8c7c`.

Initialize with `fee=.003 or .006, withdrawal_fee=0 or 1, delay_opens=0 or 1`; default initial venue cash1250, external3750, sweep target1250, cap2500. Fixed withdrawal scenarios are (0,0) and (1,1); terms are assumptions, not verified fees or service guarantees.

Each consecutive UTC trading day: `begin_day(date_string, opens)` settles pending transfers and records pre-action open exposure; optional `sweep(opens)`; optional `rebalance(opens, target_notionals)` ONLY at the strategy's original signal/rebalance events; finally `snapshot(closes, highs)` ONCE. Price and target dictionaries use the same symbol keys. Empty target liquidates, omission of rebalance retains inventory. Targets are absolute USDT notional. Sales precede cash-limited proportionately resized buys. Never transfer external capital back in.

Sweep consumes available cash then sells only enough inventory proportionately to permit withdrawing above-target equity after sales cost. Fixed withdrawal fee is deducted from gross transfer. Net transfers <=0 are skipped. Day-delayed funds remain part of total wealth but not tradable; external funds never earn yield. Set delay=1 only on a consecutive daily series; missing next-day observation cannot evidence actual receipt. Record skipped small excesses, not a promise that1250 is a strict cap.

Public state: `cash`, `external`, `qty`, `pending` (due date/net amount), `fees`, `withdrawal_costs`, `trades`, `transfers`. `venue(prices)`, `transit()`, `total(prices)` are read-only marks. Snapshot exposes components, net PnL, cumulative costs, daily PnL, conservation residual, pre-sweep open risk, close risk and simultaneous-high upper bound. Pending ownership/custody is unverified: conservative venue risk adds in-transit value to venue value. Use `open_pre_conservative` and add `in_transit` to close/high bounds. Do not treat daily upper bound as simultaneous observed breach or absence as all-day execution proof.

After the final close snapshot ONLY: `liquidate_after_snapshot(closes)` executes a conditional terminal close liquidation and checks cost conservation. Never snapshot again that day; retain preliquidation risk fields. Baseline runner reports terminal mark and net-liquidation valuation separately without terminal execution.

Run `python -m unittest -v test_capital_account` (9 synthetic tests) and `python run_benchmarks.py` (frozen local official data). Consecutive-day/checksum guards in runner; callers own signal causality, data checks, market fills and all eligibility claims. Repeated same-day snapshots and non-open trading before snapshot are outside v1 contract. Baseline is1BTC risk interval, not1004 independent outcomes.
