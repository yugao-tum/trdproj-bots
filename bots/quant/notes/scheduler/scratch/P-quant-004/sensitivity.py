#!/usr/bin/env python3
"""Leave-one-out / concentration / bootstrap check for replay/quant-004/trades.csv."""
import csv
import os
import random
import statistics
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
TRADES = os.path.join(ROOT, 'bots', 'quant', 'replay', 'quant-004', 'trades.csv')


def main():
    with open(TRADES, newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    pnl = [float(r['pnl']) for r in rows]
    print('n', len(pnl), 'total', round(sum(pnl), 2), 'median', round(statistics.median(pnl), 2))
    s = sorted(pnl, reverse=True)
    for k in (1, 2, 3):
        print(f'drop_top{k}: total={sum(s[k:]):.2f} median={statistics.median(s[k:]):.2f}')
    print('by_word', Counter(r['word'] for r in rows))
    print('wins', sum(int(r['win']) for r in rows), 'losses', len(rows) - sum(int(r['win']) for r in rows))
    random.seed(7)
    means = [sum(random.choice(pnl) for _ in pnl) / len(pnl) for _ in range(20000)]
    means.sort()
    print('bootstrap_mean_95ci', round(means[500], 2), round(means[19499], 2),
          'total_95ci', round(means[500] * len(pnl), 2), round(means[19499] * len(pnl), 2))


if __name__ == '__main__':
    main()
