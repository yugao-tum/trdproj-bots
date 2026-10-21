#!/usr/bin/env python3
import json, re, math, glob, os
from datetime import date, timedelta

def parse_table(txt):
    g = {}
    for line in txt.splitlines():
        m = re.match(r'^\s*(\d{4})\s+(.*)$', line)
        if not m:
            continue
        yr = int(m.group(1)); toks = m.group(2).split()
        if len(toks) < 12:
            continue
        for mo in range(1, 13):
            v = toks[mo-1]
            if v.startswith('*'):
                continue
            try:
                g[(yr, mo)] = int(v)/100.0
            except ValueError:
                pass
    return g

cur = parse_table(open('_cache/gistemp.txt', errors='ignore').read())
snaps = []
for fn in sorted(glob.glob('_cache/wbsnaps/*.txt')):
    ts = os.path.basename(fn)[:14]
    snaps.append((ts, parse_table(open(fn, errors='ignore').read())))
print('snapshots parsed:', len(snaps), 'span', snaps[0][0], snaps[-1][0])
first = {}
for (y, m) in sorted(k for k in cur if k >= (2024, 1) and k <= (2026, 9)):
    end = date(y+(m == 12), (m % 12)+1, 1)-timedelta(days=1)
    lo = (end+timedelta(days=14)).strftime('%Y%m%d')
    hi = (end+timedelta(days=55)).strftime('%Y%m%d')
    for ts, g in snaps:
        if lo <= ts[:8] <= hi and (y, m) in g:
            first[(y, m)] = (ts, g[(y, m)]); break
print('months with first-release proxy:', len(first), '/33')
for (y, m) in sorted(first):
    ts, v = first[(y, m)]
    print(f'{y}-{m:02d} snap {ts[:8]} first {v:+.2f} revised {cur[(y, m)]:+.2f} diff {cur[(y, m)]-v:+.2f}')
diffs = [cur[k]-v for k, (ts, v) in first.items()]; n = len(diffs); mean = sum(diffs)/n
print('SUMMARY n=', n, 'mean_rev=', round(mean, 4), 'mean_abs=', round(sum(abs(x) for x in diffs)/n, 4),
      'sd_rev=', round((sum((x-mean)**2 for x in diffs)/(n-1))**0.5, 4), 'max_abs=', round(max(abs(x) for x in diffs), 4))
def bidx(x):
    return math.floor((x+0.005)/0.05)
same = sum(bidx(cur[k]) == bidx(v) for k, (ts, v) in first.items())
print('bracket unchanged:', same, '/', n, '=', round(same/n, 4))
print('exact same 0.01:', sum(abs(cur[k]-v) < 0.0001 for k, (ts, v) in first.items()), '/', n)

# walk-forward model hits on the same 30 months, import from walkforward
import walkforward as W
sub = [r for r in W.out120 if r['t'] in first]
hf = sum(bidx(r['pred']) == bidx(first[r['t']][1]) for r in sub)
hr = sum(bidx(r['pred']) == bidx(r['actual']) for r in sub)
print('walkforward subset n=', len(sub), 'hit_revised=', hr, 'hit_first=', hf, 'diff=', hf-hr)
for k, (ts, v) in sorted(first.items()):
    if bidx(cur[k]) != bidx(v):
        pred = next(r['pred'] for r in W.out120 if r['t'] == k)
        print('  BRACKET CHANGE', k, 'first', v, 'revised', cur[k], 'pred', round(pred, 3),
              'bracket_first', bidx(v), 'bracket_rev', bidx(cur[k]), 'bracket_pred', bidx(pred))
