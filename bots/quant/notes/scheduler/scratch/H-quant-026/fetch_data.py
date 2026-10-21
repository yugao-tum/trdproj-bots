import json, urllib.request, urllib.error, os, time, gzip, csv
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE = '_cache'
UA = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
STATES = ['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']

def get(url, headers=UA, timeout=90, retries=3):
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code}'
            if e.code in (400, 403, 404):
                break
            time.sleep(1)
        except Exception as e:
            last = str(e)
            time.sleep(1)
    raise RuntimeError(f'{url} -> {last}')

os.makedirs(f'{CACHE}/usdm', exist_ok=True)

# 1) closed events
st, b = get('https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100')
ev = json.loads(b)
with gzip.open(f'{CACHE}/events_closed.json.gz', 'wt') as f:
    f.write(json.dumps(ev))
print('closed events', len(ev), 'markets', sum(len(e.get('markets') or []) for e in ev), 'bytes', len(b))

# 2) USDM state CSVs
def fetch_state(st):
    fips = {'AL':'01','AZ':'04','AR':'05','CA':'06','CO':'08','CT':'09','DE':'10','FL':'12','GA':'13','ID':'16','IL':'17','IN':'18','IA':'19','KS':'20','KY':'21','LA':'22','ME':'23','MD':'24','MA':'25','MI':'26','MN':'27','MS':'28','MO':'29','MT':'30','NE':'31','NV':'32','NH':'33','NJ':'34','NM':'35','NY':'36','NC':'37','ND':'38','OH':'39','OK':'40','OR':'41','PA':'42','RI':'44','SC':'45','SD':'46','TN':'47','TX':'48','UT':'49','VT':'50','VA':'51','WA':'53','WV':'54','WI':'55','WY':'56'}[st]
    url = ('https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent'
           f'?aoi={fips}&startdate=1%2F1%2F2000&enddate=10%2F20%2F2026&statisticsType=1')
    s, bb = get(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/csv'})
    open(f'{CACHE}/usdm/{st}.csv', 'wb').write(bb)
    return st, s, len(bb), bb.splitlines()[0][:60]

with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(fetch_state, s) for s in STATES]
    for f in as_completed(futs):
        print('usdm', *f.result())

# 3) trades for every closed market (<=1000 per market; these markets have <= a few hundred)
markets = []
for e in ev:
    for m in e.get('markets') or []:
        markets.append({'event': e['slug'], 'slug': m['slug'], 'conditionId': m['conditionId'],
                        'endDate': e['endDate'], 'outcomes': m.get('outcomes'),
                        'outcomePrices': m.get('outcomePrices'), 'clobTokenIds': m.get('clobTokenIds')})

def fetch_trades(m):
    url = f"https://data-api.polymarket.com/trades?market={m['conditionId']}&limit=1000"
    s, b = get(url)
    return m['slug'], json.loads(b)

trades = {}
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = [ex.submit(fetch_trades, m) for m in markets]
    for f in as_completed(futs):
        slug, t = f.result()
        trades[slug] = t
raw = json.dumps({'markets': markets, 'trades': trades}).encode()
open(f'{CACHE}/trades_all.json.gz', 'wb').write(gzip.compress(raw))
print('markets', len(markets), 'trades', sum(len(v) for v in trades.values()),
      'gzip bytes', os.path.getsize(f'{CACHE}/trades_all.json.gz'))

# 4) CLOB prices-history: interval=max, only decision-time snapshot retained.
#    Verified: closed markets keep only ~7 days of history; older weeks return {"history":[]}.
state_markets = [m for m in markets if m['slug'].startswith('state-d4-drought-')]

def fetch_ph(m):
    import datetime as dt
    toks = json.loads(m['clobTokenIds'])
    end = dt.datetime.fromisoformat(m['endDate'].replace('Z', '+00:00'))
    cutoff = (end - dt.timedelta(hours=13, minutes=1)).timestamp()
    out = {'slug': m['slug'], 'cutoff': cutoff, 'tokens': []}
    for tok in toks:
        try:
            s, b = get(f'https://clob.polymarket.com/prices-history?market={tok}&interval=max')
            h = json.loads(b).get('history', [])
            pre = [p for p in h if p['t'] <= cutoff]
            out['tokens'].append({'token': tok, 'n': len(h),
                                  'first_t': h[0]['t'] if h else None,
                                  'last_t': h[-1]['t'] if h else None,
                                  'p_at_cutoff': pre[-1]['p'] if pre else None,
                                  'age_h': (cutoff - pre[-1]['t']) / 3600 if pre else None})
        except Exception as e:
            out['tokens'].append({'token': tok, 'error': str(e)})
    return out

phs = []
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = [ex.submit(fetch_ph, m) for m in state_markets]
    for f in as_completed(futs):
        phs.append(f.result())
json.dump(phs, open(f'{CACHE}/ph_decision.json', 'w'))
cov = [p for p in phs if any(t.get('p_at_cutoff') is not None for t in p['tokens'])]
print('state markets', len(state_markets), 'prices-history with decision price', len(cov),
      'empty history', sum(1 for p in phs if all(t.get('n', 0) == 0 for t in p['tokens'])))
# 5) current open event snapshot (forward record, no trading)
try:
    s, b = get('https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-20')
    open(f'{CACHE}/open_2026-10-20.json', 'wb').write(b)
    d = json.loads(b)
    print('open event', d[0]['slug'], d[0]['endDate'], 'markets', len(d[0]['markets']))
except Exception as e:
    print('open event ERR', e)
