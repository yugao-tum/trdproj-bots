import json, statistics, datetime as dt
import numpy as np
from urllib.request import Request, urlopen

cache = '_cache'
ev = json.load(open(f'{cache}/events_closed0.json'))
tr = json.load(open(f'{cache}/trades_all.json'))['trades']

# --- capacity distribution: 320 state markets ---
def cutoff_for(e):
    end = dt.datetime.fromisoformat(e['endDate'].replace('Z', '+00:00'))
    return (end - dt.timedelta(hours=13, minutes=1)).timestamp()

all_vol, pre_vol, zero_all, zero_pre = [], [], 0, 0
for e in ev:
    if not e['slug'].startswith('state-d4-drought-'):
        continue
    cut = cutoff_for(e)
    for m in e['markets']:
        ts = tr.get(m['slug'], [])
        if not ts:
            zero_all += 1
        va = sum(t['size'] * t['price'] for t in ts)
        vp = sum(t['size'] * t['price'] for t in ts if t['timestamp'] <= cut)
        if vp == 0:
            zero_pre += 1
        else:
            pre_vol.append(vp)
        if va > 0:
            all_vol.append(va)
print('state markets', sum(len(e['markets']) for e in ev if e['slug'].startswith('state-d4-drought-')))
print('zero-trade (all history)', zero_all, '| zero before cutoff', zero_pre)
print('markets with trades >=1 lifetime', len(all_vol))
print('all-trade notional: n=%d median=%.2f p90=%.2f max=%.2f' % (
    len(all_vol), np.median(all_vol), np.quantile(all_vol, 0.9, method='linear'), max(all_vol)))
print('pre-cutoff notional: n=%d median=%.2f p90=%.2f max=%.2f' % (
    len(pre_vol), np.median(pre_vol), np.quantile(pre_vol, 0.9, method='linear'), max(pre_vol)))

# --- snapshot byte sizes (pages drift) ---
for u in ['https://droughtmonitor.unl.edu/',
          'https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx',
          'https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-13',
          'https://gamma-api.polymarket.com/events?slug=states-in-d4-drought-2026-10-13']:
    req = Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    d = urlopen(req, timeout=60).read()
    print('HTTP', len(d), u)

# --- cost arithmetic at p=0.50 ---
p = 0.50
fee = 0.05 * p * (1 - p)
slip = 0.01
print('p=0.50 fee/share=%.4f total=%.4f pct_of_stake=%.2f%%' % (fee, fee + slip, 100 * (fee + slip) / p))
for p in (0.82, 0.93):
    fee = 0.05 * p * (1 - p)
    print('p=%.2f fee/share=%.4f total=%.4f pct_of_stake=%.2f%%' % (p, fee, fee + slip, 100 * (fee + slip) / p))

# --- DST note ---
print('EDT: 23:59 UTC = 19:59 ET, lead before Thu 08:30 ET = 12.5h')
print('EST: 23:59 UTC = 18:59 ET, lead before Thu 08:30 ET = 13.5h')
