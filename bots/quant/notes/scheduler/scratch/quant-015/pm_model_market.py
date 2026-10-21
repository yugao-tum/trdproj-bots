import json, urllib.request, time, math, re
from datetime import datetime

d = json.load(open('_cache/search.json'))
e = next(x for x in d['events'] if x['slug'] == 'september-2026-temperature-increase-c')
rows = []
for m in e['markets']:
    lab = m['groupItemTitle']
    tok = json.loads(m['clobTokenIds'])[0]
    u = f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60'
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    h = json.load(urllib.request.urlopen(req, timeout=30)).get('history', [])
    rows.append((lab, h))
    time.sleep(0.05)

pred, sig = 1.3861, 0.056299  # from walkforward.out latest target

def ncdf(z):
    return 0.5*(1+math.erf(z/math.sqrt(2)))

def bounds(lab):
    lab = lab.replace('ºC', '').strip()
    if lab.startswith('<'):
        return (-9, float(lab[1:])+0.005)
    if lab.startswith('>'):
        return (float(lab[1:])-0.005, 9)
    a, b = re.split('[–-]', lab)
    return (float(a)-0.005, float(b)+0.005)

def ts(s):
    return int(datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp())

for T in ['2026-10-05T00:00:00Z', '2026-10-09T16:00:00Z']:
    t = ts(T); prices = {}; last = []
    for lab, h in rows:
        ph = [x for x in h if x['t'] <= t]
        prices[lab] = ph[-1]['p'] if ph else None
        if ph:
            last.append(ph[-1]['t'])
    s = sum(prices.values())
    print('time', T, 'sum raw', round(s, 4), 'last points', sorted(set(last)))
    actual = next(lab for lab, h in rows if lab.startswith('1.35'))
    for lab, h in rows:
        lo, hi = bounds(lab)
        if hi >= 9:
            pm = 1-ncdf((lo-pred)/sig)
        elif lo <= -8:
            pm = ncdf((hi-pred)/sig)
        else:
            pm = ncdf((hi-pred)/sig)-ncdf((lo-pred)/sig)
        print(f'  {lab}: model={pm:.4f} market_raw={prices[lab]:.4f} market_norm={prices[lab]/s:.4f}')
    lo, hi = bounds(actual); pm = ncdf((hi-pred)/sig)-ncdf((lo-pred)/sig)
    print(f'  actual {actual}: model_LL={-math.log(pm):.4f} market_LL={-math.log(prices[actual]/s):.4f}')
