import json, csv, gzip, datetime as dt
from collections import defaultdict

CACHE = '_cache'
STATES = ['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']

import os
ev = (json.loads(gzip.open(f'{CACHE}/events_closed.json.gz', 'rt').read())
      if os.path.exists(f'{CACHE}/events_closed.json.gz') else json.load(open(f'{CACHE}/events_closed.json')))
tr = json.loads(gzip.open(f'{CACHE}/trades_all.json.gz', 'rt').read())['trades']
ph = {p['slug']: p for p in json.load(open(f'{CACHE}/ph_decision.json'))}

# ---------- USDM base rates ----------
data = {}
for st in STATES:
    rows = []
    with open(f'{CACHE}/usdm/{st}.csv') as f:
        for r in csv.DictReader(f):
            rows.append((r['MapDate'], float(r['D4'])))
    rows.sort()
    data[st] = rows

def bucket(x):
    if x == 0: return '0'
    if x < 0.05: return '(0,.05)'
    if x < 0.25: return '[.05,.25)'
    if x < 1: return '[.25,1)'
    if x < 5: return '[1,5)'
    return '>=5'

trans = []
for st, rows in data.items():
    for i in range(len(rows) - 1):
        d0, x = rows[i]; d1, y = rows[i + 1]
        if (dt.date(int(d1[:4]), int(d1[4:6]), int(d1[6:])) -
                dt.date(int(d0[:4]), int(d0[4:6]), int(d0[6:]))).days != 7:
            continue
        trans.append((d1, bucket(x), y >= 0.05))
trans.sort()

def p_bucket(b, before):
    sel = [t for t in trans if t[0] < before and t[1] == b]
    n = len(sel); k = sum(1 for t in sel if t[2])
    return (k + 1) / (n + 2), n, k

# ---------- market dataset ----------
def d4(st, md):
    for d, v in data[st]:
        if d == md: return v
    return None

def side_prices(t):
    # taker buying Yes is an ask-side print for Yes; taker selling Yes is a bid-side print.
    p, o, s = t['price'], t['outcome'], t['side']
    if o == 'Yes' and s == 'BUY': return p, None
    if o == 'No' and s == 'SELL': return 1 - p, None
    if o == 'Yes' and s == 'SELL': return None, p
    if o == 'No' and s == 'BUY': return None, 1 - p
    return None, None

mk = []
for e in ev:
    if not e['slug'].startswith('state-d4-drought-'): continue
    week = e['slug'].replace('state-d4-drought-', '')
    md = week.replace('-', '')
    prior_date = (dt.date.fromisoformat(week) - dt.timedelta(days=7)).strftime('%Y%m%d')
    end = dt.datetime.fromisoformat(e['endDate'].replace('Z', '+00:00'))
    cutoff = (end - dt.timedelta(hours=13, minutes=1)).timestamp()
    for m in e['markets']:
        st = m['slug'].split('-')[-1].upper()
        op = json.loads(m['outcomePrices'])
        res = float(op[0]) > 0.5
        asks, bids = [], []
        for t in tr.get(m['slug'], []):
            ya, yb = side_prices(t)
            if ya is not None: asks.append((t['timestamp'], ya, t['size']))
            if yb is not None: bids.append((t['timestamp'], yb, t['size']))
        mk.append({
            'week': week, 'state': st, 'slug': m['slug'], 'prior': d4(st, prior_date),
            'cur': d4(st, md), 'res': res, 'cutoff': cutoff,
            'asks': sorted(asks), 'bids': sorted(bids),
            'ph': ph.get(m['slug'], {}).get('tokens', [{}])[0].get('p_at_cutoff'),
            'ph_n': ph.get(m['slug'], {}).get('tokens', [{}])[0].get('n'),
        })

print('state markets', len(mk), 'resolved Yes', sum(1 for m in mk if m['res']))
print('settlement mismatches USDM vs market',
      sum(1 for m in mk if m['cur'] is not None and ((m['cur'] >= 0.05) != m['res'])))

# ---------- tradable-fill backtest ----------
def pick(quotes, cutoff, age_h):
    q = [x for x in quotes if x[0] <= cutoff and (cutoff - x[0]) / 3600 <= age_h]
    return q[-1] if q else None

def run(margin=0.05, age=72, slip=0.01, rate=0.05, max_age_price=None, size_cap=None,
        weeks=None, worst=False):
    out = []
    for m in mk:
        if m['prior'] is None: continue
        if weeks is not None and m['week'] not in weeks: continue
        wk = m['week']
        prior_date = (dt.date.fromisoformat(wk) - dt.timedelta(days=7)).strftime('%Y%m%d')
        if m['prior'] >= 0.05:
            q = pick(m['asks'], m['cutoff'], age)
            if q is None: continue
            if worst:
                w = [x for x in m['asks'] if x[0] <= m['cutoff'] and (m['cutoff'] - x[0]) / 3600 <= age]
                q = (q[0], max(x[1] for x in w), sum(x[2] for x in w))
            pb, n, k = p_bucket(bucket(m['prior']), prior_date)
            if q[1] > pb - margin: continue
            fill = q[1] + slip; payoff = 1 if m['res'] else 0; side = 'YES'
        elif m['prior'] == 0:
            q = pick(m['bids'], m['cutoff'], age)
            if q is None: continue
            noask = 1 - q[1]
            if worst:
                w = [x for x in m['bids'] if x[0] <= m['cutoff'] and (m['cutoff'] - x[0]) / 3600 <= age]
                noask = 1 - min(x[1] for x in w)
            pb, n, k = p_bucket('0', prior_date)
            if noask > (1 - pb) - margin: continue
            fill = noask + slip; payoff = 0 if m['res'] else 1; side = 'NO'
        else:
            continue
        if fill >= 1: continue
        fee = rate * fill * (1 - fill)
        shares = q[2]
        if size_cap is not None: shares = min(shares, size_cap)
        pnl_ps = payoff - fill - fee
        out.append({'week': wk, 'state': m['state'], 'side': side, 'fill': fill,
                    'fee': fee, 'pnl_ps': pnl_ps, 'shares': shares,
                    'cost': shares * (fill + fee), 'pnl': shares * pnl_ps,
                    'pb': pb, 'age': (m['cutoff'] - q[0]) / 3600})
    return out

def show(tag, ts):
    if not ts:
        print(f'{tag}: n 0'); return
    pnl = sum(t['pnl'] for t in ts); cap = sum(t['cost'] for t in ts)
    pnl_ps = sum(t['pnl_ps'] for t in ts); cap_ps = sum(t['fill'] + t['fee'] for t in ts)
    wins = sum(1 for t in ts if t['pnl_ps'] > 0)
    wks = sorted(set(t['week'] for t in ts))
    print(f'{tag}: n {len(ts)} wins {wins} weeks {len(wks)} ({wks[0]}..{wks[-1]}) '
          f'shares {sum(t["shares"] for t in ts):.2f} cost ${cap:.2f} pnl ${pnl:.2f} '
          f'ROI {pnl/cap:+.2%} | per-share pnl {pnl_ps:+.4f} cost {cap_ps:.4f} '
          f'ROI {pnl_ps/cap_ps:+.2%}')
    return pnl, cap

print('\n=== A. primary reproduction (72h stale quote, last ask fill +1c, last trade size) ===')
base = run()
show('primary', base)

print('\n=== B. quote freshness: same rule, max age of last ask-side trade ===')
for a in [72, 24, 6, 1]:
    show(f'age<={a}h', run(age=a))

print('\n=== C. conservative fill: worst (highest) ask-side price inside the window ===')
for a in [72, 24, 6]:
    show(f'worst-ask age<={a}h', run(age=a, worst=True))

print('\n=== D. size cap (last trade size still used as liquidity ceiling) ===')
for sc in [None, 100, 50, 20]:
    show(f'size_cap={sc}', run(size_cap=sc))

print('\n=== E. slippage sensitivity (primary window) ===')
for s in [0.0, 0.01, 0.02, 0.05, 0.10]:
    show(f'slip={int(s*100)}c', run(slip=s))

print('\n=== F. margin sensitivity (primary window) ===')
for mg in [0.0, 0.02, 0.03, 0.05, 0.08, 0.10]:
    show(f'margin={int(mg*100)}c', run(margin=mg))

print('\n=== G. concentration / no 2026-08-25 ===')
allweeks = sorted(set(m['week'] for m in mk))
show('without 08-25', run(weeks=set(allweeks) - {'2026-08-25'}))

print('\n=== H. temporal holdout: choose margin on first 4 weeks, apply to last 4 ===')
isw = set(allweeks[:4]); oosw = set(allweeks[4:])
best = None
for mg in [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10]:
    ts = run(margin=mg, weeks=isw)
    pnl = sum(t['pnl_ps'] for t in ts); cap = sum(t['fill'] + t['fee'] for t in ts)
    roi = pnl / cap if cap else 0
    print(f'IS margin {int(mg*100)}c: n {len(ts)} pnl/share {pnl:+.4f} cost {cap:.4f} ROI {roi:+.2%}')
    if best is None or pnl > best[1]: best = (mg, pnl)
print('IS-chosen margin', best)
show('HOLDOUT last 4 weeks at IS margin', run(margin=best[0], weeks=oosw))
show('HOLDOUT last 4 weeks at 5c', run(margin=0.05, weeks=oosw))

print('\n=== I. CLOB prices-history midpoint screen on the last 4 weeks (NOT executable) ===')
print('weeks with midpoint at cutoff:', sum(1 for m in mk if m['ph'] is not None), '/', len(mk))
for mg in [0.05]:
    n_trig = 0; pnl = 0.0; cost = 0.0; det = []
    for m in mk:
        if m['week'] not in set(allweeks[4:]) or m['prior'] is None or m['ph'] is None: continue
        prior_date = (dt.date.fromisoformat(m['week']) - dt.timedelta(days=7)).strftime('%Y%m%d')
        if m['prior'] >= 0.05:
            pb, _, _ = p_bucket(bucket(m['prior']), prior_date)
            if m['ph'] <= pb - mg:
                fill = m['ph'] + 0.01; fee = 0.05 * fill * (1 - fill)
                pnl += (1 if m['res'] else 0) - fill - fee; cost += fill + fee
                n_trig += 1; det.append((m['week'], m['state'], 'YES', round(m['ph'], 3), round(pb, 3), m['res']))
        elif m['prior'] == 0:
            pb, _, _ = p_bucket('0', prior_date)
            if 1 - m['ph'] <= (1 - pb) - mg:
                fill = (1 - m['ph']) + 0.01; fee = 0.05 * fill * (1 - fill)
                pnl += (0 if m['res'] else 1) - fill - fee; cost += fill + fee
                n_trig += 1; det.append((m['week'], m['state'], 'NO', round(1 - m['ph'], 3), round(1 - pb, 3), m['res']))
    print(f'midpoint triggers at {int(mg*100)}c: n {n_trig} pnl/share {pnl:+.4f} cost {cost:.4f} '
          f'ROI {pnl/cost:+.2%} (upper bound; midpoint is not an ask)')
    for d in det[:20]: print('  ', d)

print('\n=== J. per-trade detail, primary ===')
for t in base:
    print(f"{t['week']} {t['state']:2s} {t['side']:3s} fill {t['fill']:.3f} fee {t['fee']:.4f} "
          f"shares {t['shares']:.2f} pnl ${t['pnl']:+.2f} pb {t['pb']:.3f} age {t['age']:.1f}h")

print('\n=== K. TRUE EXECUTION: signal from pre-cutoff quotes, fill at FIRST ask-side trade AFTER cutoff ===')
def run_exec(margin=0.05, delay_h=0.0, max_wait_h=24.0, slip=0.01, rate=0.05, size_cap=None):
    out = []
    for m in mk:
        if m['prior'] is None: continue
        wk = m['week']
        prior_date = (dt.date.fromisoformat(wk) - dt.timedelta(days=7)).strftime('%Y%m%d')
        if m['prior'] >= 0.05:
            q = pick(m['asks'], m['cutoff'], 72)
            if q is None: continue
            pb, n, k = p_bucket(bucket(m['prior']), prior_date)
            if q[1] > pb - margin: continue
            # first ask-side print strictly after cutoff+delay, before resolution end
            f = [x for x in m['asks'] if x[0] >= m['cutoff'] + delay_h * 3600
                 and (x[0] - m['cutoff']) / 3600 <= max_wait_h]
            if not f: continue
            ex = f[0]; fill = ex[1] + slip
            payoff = 1 if m['res'] else 0; side = 'YES'
        elif m['prior'] == 0:
            q = pick(m['bids'], m['cutoff'], 72)
            if q is None: continue
            pb, n, k = p_bucket('0', prior_date)
            if (1 - q[1]) > (1 - pb) - margin: continue
            f = [x for x in m['bids'] if x[0] >= m['cutoff'] + delay_h * 3600
                 and (x[0] - m['cutoff']) / 3600 <= max_wait_h]
            if not f: continue
            ex = f[0]; fill = (1 - ex[1]) + slip
            payoff = 0 if m['res'] else 1; side = 'NO'
        else:
            continue
        if fill >= 1: continue
        fee = rate * fill * (1 - fill)
        shares = ex[2] if size_cap is None else min(ex[2], size_cap)
        pnl_ps = payoff - fill - fee
        out.append({'week': wk, 'state': m['state'], 'side': side, 'fill': fill, 'fee': fee,
                    'pnl_ps': pnl_ps, 'shares': shares, 'cost': shares * (fill + fee),
                    'pnl': shares * pnl_ps, 'pb': pb,
                    'wait': (ex[0] - m['cutoff']) / 3600})
    return out

for d in [0, 1, 6, 12]:
    for sc in [None, 50]:
        ts = run_exec(delay_h=d, max_wait_h=24, size_cap=sc)
        tag = f'exec first print after cutoff+{d}h (<=24h), size_cap={sc}'
        show(tag, ts)
print('\nfirst-print execution at 5c, per trade:')
for t in run_exec():
    print(f"{t['week']} {t['state']:2s} {t['side']:3s} fill {t['fill']:.3f} wait {t['wait']:.1f}h "
          f"shares {t['shares']:.2f} pnl ${t['pnl']:+.2f} pb {t['pb']:.3f}")
print('\nfirst-print execution, margin sensitivity:')
for mg in [0.0, 0.03, 0.05, 0.08]:
    show(f'exec margin {int(mg*100)}c', run_exec(margin=mg))
print('\nexecuted-vs-signal coverage at 5c: signals 23; with post-cutoff print',
      len(run_exec()), '; captures $',
      round(sum(t['pnl'] for t in run_exec()), 2), 'of primary $',
      round(sum(t['pnl'] for t in base), 2))

print('\n=== L. signal-level: which pre-cutoff signals ever got a real post-cutoff fill? ===')
sig = []
for m in mk:
    if m['prior'] is None: continue
    wk = m['week']; prior_date = (dt.date.fromisoformat(wk) - dt.timedelta(days=7)).strftime('%Y%m%d')
    if m['prior'] >= 0.05:
        q = pick(m['asks'], m['cutoff'], 72)
        if q is None: continue
        pb, _, _ = p_bucket(bucket(m['prior']), prior_date)
        if q[1] > pb - 0.05: continue
        fills = [x for x in m['asks'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= 72]
        sig.append((wk, m['state'], 'YES', q[1], (m['cutoff']-q[0])/3600, len(fills),
                    fills[0][1] if fills else None))
    elif m['prior'] == 0:
        q = pick(m['bids'], m['cutoff'], 72)
        if q is None: continue
        pb, _, _ = p_bucket('0', prior_date)
        if (1-q[1]) > (1-pb) - 0.05: continue
        fills = [x for x in m['bids'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= 72]
        sig.append((wk, m['state'], 'NO', 1-q[1], (m['cutoff']-q[0])/3600, len(fills),
                    (1-fills[0][1]) if fills else None))
print('signals', len(sig), 'with any post-cutoff print within 72h', sum(1 for s in sig if s[5] > 0))
print('median pre-cutoff quote age of signals (h):',
      round(sorted(s[4] for s in sig)[len(sig)//2], 1))
print('filled signals: median pre-cutoff age (h):',
      round(sorted(s[4] for s in sig if s[5] > 0)[sum(1 for s in sig if s[5] > 0)//2], 1) if any(s[5] > 0 for s in sig) else None)
print('unfilled signals: median pre-cutoff age (h):',
      round(sorted(s[4] for s in sig if s[5] == 0)[sum(1 for s in sig if s[5] == 0)//2], 1) if any(s[5] == 0 for s in sig) else None)
for s in sig:
    print('  ', s)

print('\n=== N. execution BEFORE the Thursday 12:30 UTC USDM release (12h31m after Wed 23:59 cutoff) ===')
REL = 12 + 31/60.0

def exec_market_order(margin=0.05, slip=0.01, rate=0.05, size_cap=None):
    out = []
    for m in mk:
        if m['prior'] is None: continue
        wk = m['week']; prior_date = (dt.date.fromisoformat(wk) - dt.timedelta(days=7)).strftime('%Y%m%d')
        if m['prior'] >= 0.05:
            q = pick(m['asks'], m['cutoff'], 72)
            if q is None: continue
            pb, _, _ = p_bucket(bucket(m['prior']), prior_date)
            if q[1] > pb - margin: continue
            f = [x for x in m['asks'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= REL]
            if not f: continue
            ex = f[0]; fill = ex[1] + slip; payoff = 1 if m['res'] else 0; side = 'YES'
        elif m['prior'] == 0:
            q = pick(m['bids'], m['cutoff'], 72)
            if q is None: continue
            pb, _, _ = p_bucket('0', prior_date)
            if (1-q[1]) > (1-pb) - margin: continue
            f = [x for x in m['bids'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= REL]
            if not f: continue
            ex = f[0]; fill = (1-ex[1]) + slip; payoff = 0 if m['res'] else 1; side = 'NO'
        else:
            continue
        if fill >= 1: continue
        fee = rate*fill*(1-fill); shares = ex[2] if size_cap is None else min(ex[2], size_cap)
        out.append({'week': wk, 'state': m['state'], 'side': side, 'fill': fill, 'fee': fee,
                    'shares': shares, 'cost': shares*(fill+fee), 'pnl': shares*(payoff-fill-fee),
                    'pnl_ps': payoff-fill-fee, 'wait': (ex[0]-m['cutoff'])/3600})
    return out

def exec_limit(margin=0.05, slip=0.01, rate=0.05, size_cap=None):
    out = []
    for m in mk:
        if m['prior'] is None: continue
        wk = m['week']; prior_date = (dt.date.fromisoformat(wk) - dt.timedelta(days=7)).strftime('%Y%m%d')
        if m['prior'] >= 0.05:
            q = pick(m['asks'], m['cutoff'], 72)
            if q is None: continue
            pb, _, _ = p_bucket(bucket(m['prior']), prior_date)
            if q[1] > pb - margin: continue
            limit = q[1] + slip
            f = [x for x in m['asks'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= REL and x[1] <= limit]
            if not f: continue
            ex = f[0]; fill = limit; payoff = 1 if m['res'] else 0; side = 'YES'
        elif m['prior'] == 0:
            q = pick(m['bids'], m['cutoff'], 72)
            if q is None: continue
            pb, _, _ = p_bucket('0', prior_date)
            noask = 1-q[1]
            if noask > (1-pb) - margin: continue
            limit = noask + slip
            f = [x for x in m['bids'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= REL and (1-x[1]) <= limit]
            if not f: continue
            ex = f[0]; fill = limit; payoff = 0 if m['res'] else 1; side = 'NO'
        else:
            continue
        fee = rate*fill*(1-fill); shares = ex[2] if size_cap is None else min(ex[2], size_cap)
        out.append({'week': wk, 'state': m['state'], 'side': side, 'fill': fill, 'fee': fee,
                    'shares': shares, 'cost': shares*(fill+fee), 'pnl': shares*(payoff-fill-fee),
                    'pnl_ps': payoff-fill-fee, 'wait': (ex[0]-m['cutoff'])/3600})
    return out

for sc in [None, 50, 20]:
    show(f'exec market-order pre-release cap={sc}', exec_market_order(size_cap=sc))
for sc in [None, 50, 20]:
    show(f'exec limit-fill pre-release cap={sc}', exec_limit(size_cap=sc))
print('\nmarket-order pre-release trades:')
for t in exec_market_order():
    print(' ', t)
print('\nlimit-fill pre-release trades:')
for t in exec_limit():
    print(' ', t)

print('\n=== O. what the stale-quote trades would have had to pay at the next real print ===')
for m in mk:
    if m['prior'] is None: continue
    wk = m['week']; prior_date = (dt.date.fromisoformat(wk) - dt.timedelta(days=7)).strftime('%Y%m%d')
    if m['prior'] >= 0.05:
        q = pick(m['asks'], m['cutoff'], 72)
        if q is None: continue
        pb, _, _ = p_bucket(bucket(m['prior']), prior_date)
        if q[1] > pb - 0.05: continue
        f = [x for x in m['asks'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= 72]
        nxt = f[0] if f else None
        print(f"{wk} {m['state']:2s} YES signal {q[1]:.3f} (age {(m['cutoff']-q[0])/3600:.1f}h) "
              f"next_print {nxt[1] if nxt else None} at {(nxt[0]-m['cutoff'])/3600 if nxt else None} "
              f"post_release={((nxt[0]-m['cutoff'])/3600 > REL) if nxt else None} res {m['res']}")
    elif m['prior'] == 0:
        q = pick(m['bids'], m['cutoff'], 72)
        if q is None: continue
        pb, _, _ = p_bucket('0', prior_date)
        if (1-q[1]) > (1-pb) - 0.05: continue
        f = [x for x in m['bids'] if m['cutoff'] <= x[0] and (x[0]-m['cutoff'])/3600 <= 72]
        nxt = f[0] if f else None
        print(f"{wk} {m['state']:2s} NO  signal {1-q[1]:.3f} (age {(m['cutoff']-q[0])/3600:.1f}h) "
              f"next_print {1-nxt[1] if nxt else None} at {(nxt[0]-m['cutoff'])/3600 if nxt else None} "
              f"post_release={((nxt[0]-m['cutoff'])/3600 > REL) if nxt else None} res {m['res']}")

print('\n=== P. settlement / base-rate sanity ===')
print('resolved Yes', sum(1 for m in mk if m['res']), '/', len(mk))
print('USDM says Yes', sum(1 for m in mk if m['cur'] is not None and m['cur'] >= 0.05), '/', len(mk))
print('all prior>=0.05 persisted', sum(1 for m in mk if m['prior'] is not None and m['prior'] >= 0.05 and m['res']),
      '/', sum(1 for m in mk if m['prior'] is not None and m['prior'] >= 0.05))
print('all prior==0 entered D4', sum(1 for m in mk if m['prior'] == 0 and m['res']),
      '/', sum(1 for m in mk if m['prior'] == 0))
