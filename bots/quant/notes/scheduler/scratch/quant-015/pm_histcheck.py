#!/usr/bin/env python3
import json, urllib.request, time

d = json.load(open('_cache/search.json'))
rows = []
total = 0
for e in d['events']:
    toks = []
    for m in e.get('markets', []):
        try:
            toks.append(json.loads(m['clobTokenIds'])[0])
        except Exception:
            pass
    counts = []
    for tok in toks:
        total += 1
        u = f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60'
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            j = json.load(urllib.request.urlopen(req, timeout=30))
            h = j.get('history', [])
            counts.append(len(h))
        except Exception:
            counts.append('ERR')
        time.sleep(0.05)
    rows.append((e['slug'], e.get('closed'), counts))
for r in rows:
    print(r)
print('YES tokens queried:', total)
print('events with any nonempty:', sum(1 for _, _, c in rows if any(isinstance(x, int) and x > 0 for x in c)))
