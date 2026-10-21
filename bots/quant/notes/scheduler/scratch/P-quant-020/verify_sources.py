#!/usr/bin/env python3
"""Re-fetch the public sources cited by quant-020 and recompute the numbers
that the audit flagged (S1-2/S2: GAAP 344/537 contamination; S7/S11: monthly
table sums to 1365 not 1378; S3-4: template URLs not requestable).

All endpoints keyless.  Downloads cached under _cache/ (gitignored).
Run: python3 verify_sources.py
"""
import collections
import datetime as dt
import json
import re
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
CACHE.mkdir(exist_ok=True)
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
S = requests.Session()
S.headers.update({"User-Agent": "quant-research-P-quant-020/1.0 (keyless)"})


def get(url, params=None, name=None):
    key = CACHE / (name or re.sub(r"[^A-Za-z0-9_.-]+", "_", url + json.dumps(params or {}, sort_keys=True))[:180] + ".json")
    if key.exists():
        return json.loads(key.read_text())
    for attempt in range(5):
        r = S.get(url, params=params, timeout=60)
        if r.status_code == 429:
            import time
            time.sleep(2 * (attempt + 1))
            continue
        r.raise_for_status()
        data = r.json()
        key.write_text(json.dumps(data, separators=(",", ":")))
        return data
    raise RuntimeError("failed " + url)


def page_events(closed):
    out, offset = [], 0
    while True:
        data = get(GAMMA + "/events", {"tag_slug": "earnings", "limit": 100, "offset": offset,
                                       "closed": str(closed).lower(), "order": "endDate",
                                       "ascending": "true" if not closed else "false"},
                   name=f"events_closed_{closed}_{offset}.json")
        if not isinstance(data, list) or not data:
            break
        out.extend(data)
        if len(data) < 100:
            break
        offset += 100
        if offset > 3000:
            break
    return out


def classify(slug):
    s = slug or ""
    if "-nongaap-" in s:
        return "nongaap"
    if "-gaap-" in s:
        return "gaap"
    return "untagged"


def yesno(market):
    op = market.get("outcomePrices")
    if isinstance(op, str):
        try:
            op = json.loads(op)
        except Exception:
            return None
    if op == ["1", "0"]:
        return 1
    if op == ["0", "1"]:
        return 0
    return None


def main():
    closed = page_events(True)
    opens = page_events(False)
    print("as_of=2026-10-21 (re-fetch)")
    print("Gamma tag_slug=earnings closed events: %d" % len(closed))
    markets = [(e, m) for e in closed for m in (e.get("markets") or [])]
    print("closed markets: %d" % len(markets))
    ends = sorted(e.get("endDate", "") for e in closed if e.get("endDate"))
    print("closed endDate span: %s .. %s" % (ends[0], ends[-1]))

    by = collections.defaultdict(lambda: [0, 0])  # outcome
    for e, m in markets:
        y = yesno(m)
        if y is None:
            continue
        c = classify(e.get("slug"))
        by[c][0] += y
        by[c][1] += 1
    total_y = sum(v[0] for v in by.values())
    total_n = sum(v[1] for v in by.values())
    print("outcome YES %d / markets %d = %.4f" % (total_y, total_n, total_y / total_n))
    for c in ("gaap", "nongaap", "untagged"):
        y, n = by[c]
        print("  slug %-8s %4d/%4d = %.4f" % (c, y, n, y / n if n else 0))

    untagged = [(e, m) for e, m in markets if classify(e.get("slug")) == "untagged"]
    print("untagged markets: %d" % len(untagged))
    ug = collections.Counter((e.get("slug"), e.get("endDate")) for e, m in untagged)
    for (slug, end), n in sorted(ug.items()):
        ys = [yesno(m) for e, m in untagged if e.get("slug") == slug and e.get("endDate") == end]
        print("  %s | %s | markets=%d YES=%d" % (slug, end, n, sum(y for y in ys if y is not None)))
    mrbeast = [(e, m) for e, m in untagged if "mrbeast" in (e.get("slug") or "").lower()]
    old = [(e, m) for e, m in untagged if "beat-earnings-estimate" in (e.get("slug") or "")]
    print("  MrBeast markets: %d (YES %d)" % (len(mrbeast), sum(yesno(m) or 0 for e, m in mrbeast)))
    print("  old will-*-beat-earnings-estimate markets: %d (YES %d)" % (len(old), sum(yesno(m) or 0 for e, m in old)))
    strict = [(e, m) for e, m in markets if classify(e.get("slug")) != "untagged"]
    sy = sum(yesno(m) for e, m in strict if yesno(m) is not None)
    print("strict tagged gaap+nongaap: %d/%d = %.4f" % (sy, len(strict), sy / len(strict)))
    # audit reconciliation: if the 13 old untagged earnings markets are folded into GAAP
    oldy = sum(yesno(m) or 0 for e, m in old)
    gy, gn = by["gaap"]
    print("GAAP + old untagged (excl MrBeast): %d/%d = %.4f" % (gy + oldy, gn + len(old), (gy + oldy) / (gn + len(old))))
    print("GAAP + all untagged: %d/%d = %.4f" % (gy + len([1 for e, m in untagged if yesno(m) == 1]),
                                                 gn + len(untagged),
                                                 (gy + len([1 for e, m in untagged if yesno(m) == 1])) / (gn + len(untagged))))

    months = collections.Counter((e.get("endDate") or "")[:7] for e in closed)
    print("monthly closed events (all months):")
    for k in sorted(months):
        print("  %s %d" % (k, months[k]))
    recent = {k: months[k] for k in sorted(months)[-13:]}
    print("last 13 months sum: %d ; total %d ; earlier omitted: %d" % (
        sum(recent.values()), len(closed), len(closed) - sum(recent.values())))
    print("last 13 months: " + ", ".join("%s=%d" % (k, v) for k, v in recent.items()))

    fees = collections.Counter()
    for e, m in markets:
        fs = m.get("feeSchedule")
        if fs is None:
            fees["null"] += 1
        else:
            fees[str(fs.get("rate"))] += 1
    print("closed feeSchedule counts: %s" % dict(fees))

    print("open events: %d" % len(opens))
    om = [(e, m) for e in opens for m in (e.get("markets") or [])]
    ofees = collections.Counter()
    for e, m in om:
        fs = m.get("feeSchedule")
        ofees["null" if fs is None else str(fs.get("rate"))] += 1
    print("open markets: %d feeSchedule counts: %s" % (len(om), dict(ofees)))

    # public-search template hit
    ps = get(GAMMA + "/public-search", {"q": "earnings", "limit_per_type": 20,
                                       "events_status": "all"}, name="public_search.json")
    evs = ps.get("events") or ps.get("data") or []
    print("public-search q=earnings events=%d pagination=%s" % (len(evs), ps.get("pagination")))
    if evs:
        e0 = evs[0]
        print("  first slug=%s resolutionSource=%s restricted=%s volume=%s"
              % (e0.get("slug"), e0.get("resolutionSource"), e0.get("restricted"), e0.get("volume")))

    # Rule text phrases from the cited HIMS event
    hev = get(GAMMA + "/events", {"slug": "hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05"}, name="hims_event.json")
    e = hev[0] if isinstance(hev, list) else hev
    desc = (e.get("description") or "") + " " + " ".join((m.get("description") or "") for m in e.get("markets") or [])
    phrases = ["as of market creation", "SeekingAlpha estimates", "greater than $0.05",
               "within 96h", "45 calendar days", "rounded to the nearest cent",
               "IFRS EPS will be treated as GAAP EPS", "diluted GAAP EPS",
               "fat finger errors", "Lyft"]
    print("HIMS rule phrase hits:")
    for p in phrases:
        print("  %-45s %s" % (p, "YES" if p in desc else "NO"))
    print("HIMS resolutionSource=%s restricted=%s volume=%s" % (
        e.get("resolutionSource"), e.get("restricted"), e.get("volume")))

    # Concrete requestable URL examples (audit S3-4)
    g = S.get(GAMMA + "/events", params={"tag_slug": "earnings", "limit": 1, "offset": 0,
                                         "closed": "true", "order": "endDate", "ascending": "false"}, timeout=60)
    print("concrete Gamma offset=0 HTTP %d bytes=%d" % (g.status_code, len(g.content)))
    # a real CLOB token from the first closed market
    tok = None
    for e, m in markets:
        ct = m.get("clobTokenIds")
        if isinstance(ct, str):
            try:
                ct = json.loads(ct)
            except Exception:
                ct = None
        if ct:
            tok = ct[0]
            break
    if tok:
        end = None
        for e, m in markets:
            ct = m.get("clobTokenIds")
            if isinstance(ct, str):
                ct = json.loads(ct)
            if ct and ct[0] == tok:
                end = dt.datetime.fromisoformat(e["endDate"].replace("Z", "+00:00"))
                break
        if end:
            params = {"market": tok, "startTs": int((end - dt.timedelta(hours=72)).timestamp()),
                      "endTs": int(end.timestamp()), "fidelity": 60}
            r = S.get(CLOB + "/prices-history", params=params, timeout=60)
            print("concrete CLOB prices-history HTTP %d bytes=%d points=%s" % (
                r.status_code, len(r.content), len(r.json().get("history", [])) if r.status_code == 200 else "-"))
    # SEC EDGAR full-text search
    r = S.get("https://efts.sec.gov/LATEST/search-index", params={"q": "form:8-K items:2.02", "forms": "8-K"}, timeout=60)
    print("SEC EDGAR search-index HTTP %d bytes=%d" % (r.status_code, len(r.content)))
    if r.status_code == 200:
        try:
            print("  hits.total=%s" % r.json().get("hits", {}).get("total"))
        except Exception:
            pass


if __name__ == "__main__":
    main()
