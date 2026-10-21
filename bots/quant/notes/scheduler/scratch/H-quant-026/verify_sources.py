import json, urllib.request, urllib.error, datetime as dt, re, os

UA = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
def get(url, headers=UA):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b''
    except Exception as e:
        return None, str(e).encode()

def head(url, headers=UA):
    req = urllib.request.Request(url, headers=headers, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None

print('--- 1. cited URLs ---')
urls = [
    ('drought home', 'https://droughtmonitor.unl.edu/'),
    ('usdm datatables', 'https://droughtmonitor.unl.edu/DmData/DataTables.aspx'),
    ('usdm comprehensive', 'https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx'),
    ('usdm api al', 'https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=01&startdate=8%2F1%2F2026&enddate=10%2F20%2F2026&statisticsType=1'),
    ('gamma series', 'https://gamma-api.polymarket.com/events?series_id=12688&closed=true&limit=100'),
    ('gamma state 10-13', 'https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-13'),
    ('gamma bracket 10-13', 'https://gamma-api.polymarket.com/events?slug=states-in-d4-drought-2026-10-13'),
    ('gamma open 10-20', 'https://gamma-api.polymarket.com/events?slug=state-d4-drought-2026-10-20'),
    ('data-api sample', 'https://data-api.polymarket.com/trades?market=0xbf70aa5a4a493a1201d21be0121d3de42ceb58121fb6401da0bd4c1beb83cfdd&limit=1000'),
    ('gamma drought tag', 'https://gamma-api.polymarket.com/events?tag_slug=drought&closed=true&limit=100'),
]
cache = {}
for name, u in urls:
    hdr = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/csv'} if 'usdmdataservices' in u else UA
    s, b = get(u, hdr); cache[name] = b
    print(f'{name:20s} HTTP {s} bytes {len(b)}')

# home phrases
home = re.sub(r'<[^>]+>', '', cache['drought home'].decode('utf-8', 'ignore'))
for phrase in ['released each Thursday at 8:30 a.m. Eastern Time',
               'Map released: October 15, 2026',
               'Data valid: October 13, 2026']:
    print('home contains', repr(phrase), phrase in home)

# USDM Accept header behaviour
s1, b1 = get(urls[2][1], {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/csv'})
s2, b2 = get(urls[2][1], {'User-Agent': 'Mozilla/5.0'})
print('usdm Accept:text/csv ->', s1, len(b1), '| no Accept ->', s2, len(b2), '| csv header', b1.splitlines()[0][:70])
print('usdm direct guessed csv HTTP', head('https://droughtmonitor.unl.edu/data/csv/20260901_dmstatistics.csv'))

# gamma counts and fields
ev = json.loads(cache['gamma series'])
print('closed events', len(ev), 'markets', sum(len(e.get('markets') or []) for e in ev))
ev_state = json.loads(cache['gamma state 10-13'])[0]
ev_br = json.loads(cache['gamma bracket 10-13'])[0]
print('state event', ev_state['slug'], 'endDate', ev_state['endDate'], 'markets', len(ev_state['markets']))
print('bracket event', ev_br['slug'], 'endDate', ev_br['endDate'], 'markets', len(ev_br['markets']))
print('state fee', ev_state['markets'][0].get('feeSchedule'), 'negRisk', ev_state['markets'][0].get('negRisk'))
print('bracket fee', ev_br['markets'][0].get('feeSchedule'), 'negRisk', ev_br['markets'][0].get('negRisk'))
print('state resolutionSource', ev_state['markets'][0].get('resolutionSource'))
print('event resolutionSource', ev_state.get('resolutionSource'))
print('state restricted', sum(1 for m in ev_state['markets'] if m.get('restricted')), '/', len(ev_state['markets']))
print('bracket restricted', sum(1 for m in ev_br['markets'] if m.get('restricted')), '/', len(ev_br['markets']))
print('state outcomes', ev_state['markets'][0].get('outcomes'), 'bracket outcomes', ev_br['markets'][0].get('outcomes'))

# exact rule quote comparison
md = open('../../../../entries/quant-026-drought-d4-weekly-continuity.md', encoding='utf-8').read()
blocks = re.findall(r'((?:^>.*\n)+)', md, flags=re.M)
def norm(s):
    s = re.sub(r'(?m)^> ?', '', s)
    return ' '.join(s.split())
print('blockquotes found', len(blocks))
for i, blk in enumerate(blocks):
    for label, evx in [('state', ev_state), ('bracket', ev_br)]:
        desc = evx['markets'][0].get('description', '')
        if norm(blk) == ' '.join(desc.split()):
            print(f'blockquote {i+1} exact match {label} description ({len(desc)} chars)')
# fallback substring checks
for q in ['D4 area below 0.05% is treated as cartographic noise',
          'Revisions remain subject to the cutoff above',
          'The count ranges over all 48 coterminous states',
          'resolve to the "0 states" bracket']:
    hit = [i+1 for i, blk in enumerate(blocks) if q in norm(blk)]
    print('quote key', repr(q[:40]), 'in blockquotes', hit)

# trades fields
tr = json.loads(cache['data-api sample'])
print('sample trades', len(tr), 'keys', sorted(tr[0].keys()) if tr else None)
print('sample first', {k: tr[0][k] for k in ('size', 'price', 'side', 'outcome', 'timestamp')} if tr else None)

# drought tag composition
tag = json.loads(cache['gamma drought tag'])
print('tag drought events', len(tag))
print('  state weekly', sum(1 for e in tag if e['slug'].startswith('state-d4-drought-')))
print('  bracket weekly', sum(1 for e in tag if e['slug'].startswith('states-in-d4-drought-')))
print('  other', sum(1 for e in tag if not e['slug'].startswith(('state-d4-drought-', 'states-in-d4-drought-'))))
for e in tag:
    if not e['slug'].startswith(('state-d4-drought-', 'states-in-d4-drought-')):
        print('   other:', e['slug'], e.get('endDate'), 'closed', e.get('closed'))

print('\n--- 2. CLOB prices-history retention for closed vs open markets ---')
evs = sorted(ev, key=lambda e: e['endDate'])
for e in [evs[0], evs[7], evs[8], evs[14], evs[15]]:
    m = e['markets'][0]; tok = json.loads(m['clobTokenIds'])[0]
    s, b = get(f'https://clob.polymarket.com/prices-history?market={tok}&interval=max')
    h = json.loads(b).get('history', []) if s == 200 else []
    print(f"{e['slug']:36s} end {e['endDate'][:10]} n {len(h)}"
          + (f" first {dt.datetime.fromtimestamp(h[0]['t'], dt.UTC).isoformat()}"
             f" last {dt.datetime.fromtimestamp(h[-1]['t'], dt.UTC).isoformat()}" if h else ''))
# AR 10-13 anomaly: midpoint at cutoff vs next-day print vs settlement
m_ar = [m for m in ev_state['markets'] if m['slug'].endswith('-ar')][0]
tok = json.loads(m_ar['clobTokenIds'])[0]
s, b = get(f'https://clob.polymarket.com/prices-history?market={tok}&interval=max')
h = json.loads(b)['history']
end = dt.datetime.fromisoformat(ev_state['endDate'].replace('Z', '+00:00'))
cut = (end - dt.timedelta(hours=13, minutes=1)).timestamp()
pre = [x for x in h if x['t'] <= cut]
print('AR 10-13: midpoint at cutoff', pre[-1]['p'] if pre else None,
      '| last series point', h[-1]['p'] if h else None,
      '| settlement outcomePrices', m_ar['outcomePrices'], '| trades', len(json.loads(cache['data-api sample']) or []))
s, b = get('https://data-api.polymarket.com/trades?market=' + m_ar['conditionId'] + '&limit=1000')
print('AR 10-13 data-api trades', len(json.loads(b)))
