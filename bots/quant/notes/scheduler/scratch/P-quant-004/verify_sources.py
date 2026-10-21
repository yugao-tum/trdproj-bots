#!/usr/bin/env python3
"""Re-fetch the URLs cited by bots/quant/entries/quant-004-pm-mention-base-rates.md.

Read-only public GETs, no keys. PDFs go to /tmp (never into the repo).
Prints HTTP status, byte size and targeted content checks so the entry's
quoted numbers can be re-verified.
"""
import json
import os
import re
import subprocess
import tempfile
import requests

UA = {'User-Agent': 'Mozilla/5.0'}
S = requests.Session()
S.headers.update(UA)
TMP = tempfile.mkdtemp(prefix='q004_verify_')


def get(url, **kw):
    try:
        r = S.get(url, timeout=40, **kw)
        return r
    except Exception as exc:  # noqa: BLE001
        print(f'ERROR {url} -> {exc}')
        return None


def line(label, r, extra=''):
    if r is None:
        return
    print(f'{label}: HTTP {r.status_code} bytes={len(r.content)} {extra}')


def main():
    # 1-2 contract PDFs
    pdfs = {
        'Event': 'https://polymarket-upload.s3.us-east-2.amazonaws.com/market_products/Mentions/Event+Mentions+Contract+DeFi.pdf',
        'Period': 'https://polymarket-upload.s3.us-east-2.amazonaws.com/market_products/Mentions/Period+Mentions+Contract+DeFi.pdf',
    }
    clauses = {
        'Event': ['during remarks at', 'If the event contains a Q&A', 'Expanded forms of acronyms',
                  'displays on screen but does not say aloud', 'No Qualifying Event',
                  'remain open and remarks made during the rescheduled event will count',
                  'first official release', 'Transcripts or any subsequent releases'],
        'Period': ['Only remarks made between the starting', 'recorded before the starting',
                   'official social media accounts'],
    }
    for name, url in pdfs.items():
        r = get(url)
        line(f'PDF {name}', r)
        if r is None or r.status_code != 200:
            continue
        path = os.path.join(TMP, f'{name}.pdf')
        with open(path, 'wb') as fh:
            fh.write(r.content)
        txt = subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True).stdout
        txt = re.sub(r'\s+', ' ', txt)
        hits = [c for c in clauses[name] if c in txt]
        print(f'  clauses_found={len(hits)}/{len(clauses[name])} missing={[c for c in clauses[name] if c not in txt]}')

    # Gamma endpoints
    open_r = get('https://gamma-api.polymarket.com/events?tag_slug=mention-markets&limit=100&closed=false')
    line('Gamma open events', open_r)
    if open_r is not None and open_r.status_code == 200:
        ev = open_r.json()
        print(f'  open_events={len(ev)} market_counts={sorted(len(e.get("markets", [])) for e in ev)[-4:]}')

    total = 0
    weekly = []
    for off in range(0, 1500, 100):
        r = get('https://gamma-api.polymarket.com/events', params={
            'tag_slug': 'mention-markets', 'closed': 'true', 'limit': 100,
            'offset': off, 'order': 'endDate', 'ascending': 'false'})
        if r is None or r.status_code != 200:
            print(f'  closed offset={off} FAILED')
            continue
        batch = r.json()
        if not batch:
            break
        total += len(batch)
        weekly += [e for e in batch if (e.get('title') or '').startswith('What will Trump say this week')]
    print(f'Gamma closed events: total={total} trump_weekly={len(weekly)}')
    if weekly:
        mkts = sum(len(e.get('markets', [])) for e in weekly)
        print(f'  weekly_markets={mkts} creation={min(e["creationDate"] for e in weekly)}..{max(e["creationDate"] for e in weekly)}'
              f' end={min(e["endDate"] for e in weekly)}..{max(e["endDate"] for e in weekly)}')

    # Specific event snapshots quoted in the entry
    kansas = get('https://gamma-api.polymarket.com/events?slug=what-will-trump-say-during-his-midterm-rally-in-kansas-october-19')
    line('Gamma Kansas event', kansas)
    if kansas is not None and kansas.status_code == 200:
        ev = kansas.json()[0]
        mk = {m.get('groupItemTitle'): m for m in ev.get('markets', [])}
        tax = next((m for k, m in mk.items() if k and 'Tax' in k), None)
        print(f'  markets={len(ev.get("markets", []))} tax_ask={tax and tax.get("bestAsk")}'
              f' tax_spread={tax and tax.get("spread")} tax_volume={tax and tax.get("volume")}')

    week = get('https://gamma-api.polymarket.com/events?slug=what-will-trump-say-this-week-october-19-october-25-20261025')
    line('Gamma weekly event', week)
    if week is not None and week.status_code == 200:
        ev = week.json()[0]
        print(f'  markets={len(ev.get("markets", []))}'
              f' written_clause={"Written usages of terms" in (ev.get("description") or "")}')

    nflx = get('https://gamma-api.polymarket.com/events?slug=what-will-netflix-say-during-their-next-earnings-call-october-20')
    line('Gamma Netflix event', nflx)
    if nflx is not None and nflx.status_code == 200:
        ev = nflx.json()[0]
        m = next((x for x in ev.get('markets', []) if 'AI' in (x.get('groupItemTitle') or '')), None)
        print(f'  markets={len(ev.get("markets", []))} fee={m and m.get("feeSchedule")}')
        if m:
            toks = json.loads(m.get('clobTokenIds') or '[]')
            if toks:
                ph = get('https://clob.polymarket.com/prices-history', params={
                    'market': str(toks[0]), 'interval': 'max', 'fidelity': 60})
                line('CLOB prices-history (background only)', ph)
                if ph is not None and ph.status_code == 200:
                    print(f'  points={len(ph.json().get("history", []))}')

    sr = get('https://gamma-api.polymarket.com/public-search', params={'q': 'mention', 'limit_per_type': 5})
    line('Gamma public-search', sr)
    if sr is not None and sr.status_code == 200:
        txt = sr.text
        print(f'  elon_snl_volume_495007_57={"495007.57" in txt}')

    tags = get('https://gamma-api.polymarket.com/tags', params={'limit': 20, 'search': 'mention'})
    line('Gamma tags search', tags)
    if tags is not None and tags.status_code == 200:
        labels = [t.get('label') for t in tags.json()]
        print(f'  irrelevant_to_mentions={"mention-markets" not in labels} first_labels={labels[:3]}')

    # data-api trade print source (old market cited in the entry)
    cond = '0xc740b31ab2b090aa78e86623ab820ccd24131b4a6fcb1beacdb44602deea737e'
    tr = get('https://data-api.polymarket.com/trades', params={'market': cond, 'limit': 10000, 'offset': 0})
    line('data-api trades (old market)', tr)
    if tr is not None and tr.status_code == 200:
        b = tr.json()
        print(f'  trades={len(b)} has_side_price={"side" in (b[0] if b else {})}')

    # transcript / background sources
    transcript_urls = {
        'presidency.ucsb search': 'https://www.presidency.ucsb.edu/advanced-search?field-keywords=%22remarks%22&items_per_page=25',
        'factba.se': 'https://www.factba.se/',
        'whitehouse remarks': 'https://www.whitehouse.gov/remarks/',
        'fool transcript index': 'https://www.fool.com/earnings-call-transcripts/',
        'fool nflx path (expected 404)': 'https://www.fool.com/earnings/call-transcripts/nflx/',
        'rollcall factbase trump (expected 404)': 'https://rollcall.com/factbase/trump/',
    }
    for label, url in transcript_urls.items():
        r = get(url)
        extra = ''
        if r is not None and r.status_code == 200:
            m = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.S | re.I)
            if m:
                extra = 'title=' + re.sub(r'\s+', ' ', m.group(1)).strip()[:70]
            if label.startswith('presidency'):
                mm = re.search(r'of ([\d,]+) records found', re.sub(r'\s+', ' ', r.text))
                extra += f' records={mm.group(1) if mm else "?"}'
        line(label, r, extra)

    # replay deliverables exist and are small
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
    for rel in ['bots/quant/replay/quant-004/backtest.py',
                'bots/quant/replay/quant-004/trades.csv',
                'bots/quant/replay/quant-004/SUMMARY.md',
                'bots/quant/entries/quant-004-pm-mention-base-rates.md']:
        p = os.path.join(root, rel)
        print(f'FILE {rel}: exists={os.path.exists(p)} bytes={os.path.getsize(p) if os.path.exists(p) else 0}')


if __name__ == '__main__':
    main()
