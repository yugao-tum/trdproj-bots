#!/usr/bin/env python3
"""quant-004 replay: Trump weekly mention markets priced from historical word base rates.

Fills use real taker trade prints from Polymarket data-api (NOT CLOB prices-history).
Signal for market (word W, week t): p_hat = Laplace smoothed hit rate of W in the
same speaker's earlier weekly events whose period ended before week t started.
Decision time = event creationDate + 2h. Entry = first taker BUY print at/after
decision time on the chosen token. Fees: 0.04*p*(1-p) per share (mentions fee),
plus a per-share slippage buffer (base 0.01).

Primary rule is fixed a priori: threshold edge > 0.10, min history n >= 6,
slippage 0.01. Other variants are reported for multiple-testing context.
"""
import csv, json, math, os, re, sys, time
from datetime import datetime, timezone
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.abspath(os.path.join(ROOT, '..', '..', 'notes', 'scheduler', 'scratch', 'P-quant-004', '_cache'))
os.makedirs(CACHE, exist_ok=True)
GAMMA = 'https://gamma-api.polymarket.com/events'
DATA = 'https://data-api.polymarket.com/trades'
S = requests.Session()

def iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))

def fetch_events():
    rows = []
    off = 0
    while off < 1500:
        r = S.get(GAMMA, params={'tag_slug': 'mention-markets', 'closed': 'true', 'limit': 100,
                                 'offset': off, 'order': 'endDate', 'ascending': 'false'}, timeout=40)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        for e in batch:
            if not (e.get('title') or '').startswith('What will Trump say this week'):
                continue
            if not e.get('endDate') or not e.get('creationDate'):
                continue
            for m in e.get('markets', []):
                try:
                    toks = json.loads(m.get('clobTokenIds') or '[]')
                    prices = json.loads(m.get('outcomePrices') or '[]')
                except Exception:
                    continue
                if len(toks) < 2 or len(prices) < 2:
                    continue
                word = (m.get('groupItemTitle') or '').strip()
                if not word:
                    continue
                rows.append({'event': e['slug'], 'word': word.lower(), 'word_raw': word,
                             'question': m.get('question', ''), 'conditionId': m.get('conditionId', ''),
                             'yes_token': str(toks[0]), 'no_token': str(toks[1]),
                             'outcome_yes': 1 if float(prices[0]) > 0.5 else 0,
                             'creation': e['creationDate'], 'end': e['endDate'],
                             'volume': float(m.get('volume') or 0)})
        off += 100
    rows.sort(key=lambda x: x['creation'])
    return rows

def load_events():
    path = os.path.join(CACHE, 'trump_weekly_markets.csv')
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as fh:
            cached = list(csv.DictReader(fh))
        for r in cached:
            r['outcome_yes'] = int(r['outcome_yes'])
            r['volume'] = float(r['volume'])
        return cached
    rows = fetch_events()
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    return rows

_trades = {}
def trades_for(cond):
    if cond in _trades:
        return _trades[cond]
    out, off = [], 0
    while off < 40000:
        r = S.get(DATA, params={'market': cond, 'limit': 10000, 'offset': off}, timeout=60)
        if r.status_code != 200:
            break
        b = r.json()
        if not b:
            break
        out += b
        if len(b) < 10000:
            break
        off += 10000
    _trades[cond] = out
    return out

def first_buy(trades, asset, t0):
    c = [x for x in trades if str(x.get('asset')) == asset and x.get('side') == 'BUY'
         and int(x.get('timestamp', 0)) >= t0]
    if not c:
        return None
    return min(c, key=lambda x: int(x['timestamp']))

def run(rows, thr=0.10, min_n=6, slip=0.01, fee_rate=0.04, size=100.0, min_notional=10.0, cap=True):
    by_word = {}
    for r in rows:
        by_word.setdefault(r['word'], []).append(r)
    events = {}
    for r in rows:
        events.setdefault(r['event'], []).append(r)
    results, skipped = [], 0
    for ev, ms in sorted(events.items(), key=lambda kv: kv[1][0]['creation']):
        cands = []
        for r in ms:
            t0 = iso(r['creation']).timestamp() + 2 * 3600
            hist = [h for h in by_word[r['word']]
                    if iso(h['end']).timestamp() < iso(r['creation']).timestamp()]
            n, hits = len(hist), sum(int(h['outcome_yes']) for h in hist)
            if n < min_n:
                continue
            p_hat = (hits + 1.0) / (n + 2.0)
            tr = trades_for(r['conditionId'])
            if not tr:
                continue
            yb = first_buy(tr, r['yes_token'], t0)
            nb = first_buy(tr, r['no_token'], t0)
            if yb:
                py = float(yb['price'])
                avail = py * float(yb.get('size') or 0)
                cy = fee_rate * py * (1 - py) + slip
                if avail >= min_notional and p_hat - py - cy > thr:
                    cands.append((p_hat - py - cy, r, 'YES', py, cy, avail))
            if nb:
                pn = float(nb['price'])
                avail = pn * float(nb.get('size') or 0)
                cn = fee_rate * pn * (1 - pn) + slip
                if avail >= min_notional and (1 - p_hat) - pn - cn > thr:
                    cands.append(((1 - p_hat) - pn - cn, r, 'NO', pn, cn, avail))
        if not cands:
            skipped += 1
            continue
        edge, r, side, price, cost, avail = max(cands, key=lambda x: x[0])
        win = 1 if (r['outcome_yes'] == 1) == (side == 'YES') else 0
        pnl_ps = win - price - cost
        notional = min(size, avail) if cap else size
        shares = notional / price
        results.append({'event': ev, 'word': r['word_raw'], 'side': side, 'price': price,
                        'fee': fee_rate * price * (1 - price), 'slip': slip, 'edge': edge,
                        'n_hist': len([h for h in by_word[r['word']] if iso(h['end']).timestamp() < iso(r['creation']).timestamp()]),
                        'outcome_yes': int(r['outcome_yes']), 'win': win,
                        'fill_notional': notional, 'shares': shares, 'pnl': shares * pnl_ps,
                        'ret_on_100': pnl_ps / price, 'end': r['end']})
    return results, skipped

def stats(results):
    if not results:
        return {}
    pnls = [x['pnl'] for x in results]
    n = len(pnls)
    mean = sum(pnls) / n
    sd = (sum((x - mean) ** 2 for x in pnls) / (n - 1)) ** 0.5 if n > 1 else 0.0
    t = mean / (sd / math.sqrt(n)) if sd else 0.0
    total = sum(pnls)
    rets = [x['ret_on_100'] for x in results]
    # equity by settlement (endDate), max drawdown in USDT / 5000
    eq, peak, mdd = 0.0, 0.0, 0.0
    for x in sorted(results, key=lambda x: x['end']):
        eq += x['pnl']; peak = max(peak, eq); mdd = max(mdd, peak - eq)
    days = (iso(max(x['end'] for x in results)) - iso(min(results, key=lambda x: x['end'])['end'])).days or 1
    ann = total / 5000.0 * (365.25 / days) * 100
    return {'n': n, 'total': total, 'mean': mean, 'sd': sd, 't': t, 'win': sum(x['win'] for x in results) / n,
            'avg_ret': sum(rets) / n, 'mdd_usd': mdd, 'mdd_pct': mdd / 5000 * 100, 'days': days, 'ann': ann}

def main():
    rows = load_events()
    print(f'events rows={len(rows)} tournaments={len(set(r["event"] for r in rows))} '
          f'window={min(r["creation"] for r in rows)}..{max(r["end"] for r in rows)}', flush=True)
    variants = [(0.05, 6, 0.01, 10, True), (0.10, 6, 0.01, 10, True), (0.15, 6, 0.01, 10, True),
                (0.05, 10, 0.01, 10, True), (0.10, 10, 0.01, 10, True), (0.15, 10, 0.01, 10, True),
                (0.10, 6, 0.02, 10, True), (0.10, 10, 0.02, 10, True),
                (0.10, 6, 0.01, 0, True), (0.10, 6, 0.01, 20, True),
                (0.10, 6, 0.01, 0, False)]
    allres = {}
    for thr, mn, sl, mnot, cp in variants:
        t0 = time.time()
        res, skipped = run(rows, thr=thr, min_n=mn, slip=sl, min_notional=mnot, cap=cp)
        st = stats(res)
        allres[(thr, mn, sl, mnot, cp)] = (res, st)
        print(f'variant thr={thr} min_n={mn} slip={sl} min_notional={mnot} cap={cp}: '
              f'trades={len(res)} events_no_trade={skipped} '
              f'total={st.get("total",0):.2f} USD t={st.get("t",0):.2f} win={st.get("win",0):.3f} '
              f'avg_ret={st.get("avg_ret",0):.4f} ann={st.get("ann",0):.2f}% '
              f'mdd={st.get("mdd_pct",0):.2f}% ({time.time()-t0:.1f}s)', flush=True)
    res, st = allres[(0.10, 6, 0.01, 10, True)]
    path = os.path.join(ROOT, 'trades.csv')
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0]))
        w.writeheader()
        for x in res:
            w.writerow({k: (f'{v:.6f}' if isinstance(v, float) else v) for k, v in x.items()})
    print(f'wrote {path} rows={len(res)}', flush=True)
    return allres

if __name__ == '__main__':
    main()
