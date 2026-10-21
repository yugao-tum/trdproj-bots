#!/usr/bin/env python3
"""Independent arithmetic check of replay/quant-004/trades.csv.

Does not import backtest.py; recomputes total PnL, win rate, t, max drawdown,
annualised contribution and per-row fee/slip/pnl from the raw columns.
"""
import csv
import math
import os
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
TRADES = os.path.join(ROOT, 'bots', 'quant', 'replay', 'quant-004', 'trades.csv')
CAPITAL = 5000.0
FEE_RATE = 0.04


def iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))


def main():
    with open(TRADES, newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    pnls, bad = [], []
    for r in rows:
        price, fee, slip = float(r['price']), float(r['fee']), float(r['slip'])
        shares, notional = float(r['shares']), float(r['fill_notional'])
        recomputed_fee = FEE_RATE * price * (1 - price)
        if abs(recomputed_fee - fee) > 1e-4:
            bad.append((r['event'], 'fee', fee, recomputed_fee))
        if abs(shares * price - notional) > 1e-3:
            bad.append((r['event'], 'shares*price', notional, shares * price))
        win = int(r['win'])
        recomputed_pnl = shares * (win - price - fee - slip)
        if abs(recomputed_pnl - float(r['pnl'])) > 1e-3:
            bad.append((r['event'], 'pnl', float(r['pnl']), recomputed_pnl))
        pnls.append(recomputed_pnl)
    n = len(pnls)
    total = sum(pnls)
    mean = total / n
    sd = (sum((x - mean) ** 2 for x in pnls) / (n - 1)) ** 0.5
    t = mean / (sd / math.sqrt(n))
    eq = peak = mdd = 0.0
    for r in sorted(rows, key=lambda x: x['end']):
        eq += float(r['pnl'])
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    first = min(iso(r['end']) for r in rows)
    last = max(iso(r['end']) for r in rows)
    days = (last - first).days
    ann = total / CAPITAL * 365.25 / days * 100
    print(f'rows={n} independent_events={len(set(r["event"] for r in rows))}')
    print(f'total_pnl={total:.2f} USD mean={mean:.2f} sd={sd:.2f} t={t:.2f}')
    print(f'win_rate={sum(int(r["win"]) for r in rows) / n:.4f}')
    print(f'max_drawdown={mdd:.2f} USD = {mdd / CAPITAL * 100:.2f}% of {CAPITAL:.0f}')
    print(f'window={first.date()}..{last.date()} days={days}')
    print(f'annualised={ann:.2f}% (total/{CAPITAL:.0f}*365.25/{days})')
    print(f'arithmetic_mismatches={len(bad)}')
    for b in bad:
        print('  MISMATCH', b)


if __name__ == '__main__':
    main()
