#!/usr/bin/env python3
"""Verify every source cited by quant-010 against the live page (2026-10-21).

Read-only, keyless. Prints one line per claim with PASS/FAIL/NOTE and the
observed value. Gamma numbers are point-in-time snapshots; when an event has
resolved since the 2026-10-20 access, the price fields move, so we record the
current value instead of pretending it is unchanged.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) quant-research-q010"}
G = "https://gamma-api.polymarket.com/events?slug="


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def event(slug):
    st, body = get(G + slug)
    data = json.loads(body)
    return st, (data[0] if data else None)


def show(label, cond, detail):
    print(("PASS " if cond else "FAIL ") + label + " | " + detail)


def market(ev, title):
    """Exact title first, then prefix match (Gamma appends '- artist')."""
    for m in ev.get("markets", []):
        if (m.get("groupItemTitle") or "").strip() == title:
            return m
    for m in ev.get("markets", []):
        if (m.get("groupItemTitle") or "").strip().startswith(title + " - "):
            return m
    return None


def mprices(m):
    try:
        return json.loads(m.get("outcomePrices") or "[]")
    except Exception:
        return []


def main():
    print("quant-010 source verification, run %s UTC" % datetime.now(timezone.utc).isoformat())
    print("")

    st, ev = event("what-will-be-the-top-global-netflix-show-this-week-october-20")
    show("netflix-global HTTP 200 + non-empty", st == 200 and ev is not None,
         "HTTP %s, markets=%s" % (st, len(ev.get("markets", [])) if ev else 0))
    if ev:
        d = ev.get("description") or ""
        for frag in ["Tuesday, October 20, 2026, 3:00 PM ET",
                     "previous week (Monday to Sunday)", "English only",
                     "October 23, 2026, 11:59 PM ET"]:
            show("netflix-global description contains %r" % frag, frag in d, "len(desc)=%d" % len(d))
        show("netflix-global resolutionSource is Tudum tv",
             ev.get("resolutionSource") == "https://www.netflix.com/tudum/top10/tv",
             repr(ev.get("resolutionSource")))
        b = market(ev, "Below: Limited Series")
        show("netflix-global has 'Below: Limited Series'", b is not None,
             "outcomePrices=%s bestBid=%s bestAsk=%s" % (
                 mprices(b) if b else None, b and b.get("bestBid"), b and b.get("bestAsk")))
        if b:
            fs = b.get("feeSchedule")
            show("netflix-global Below feeSchedule rate 0.05 takerOnly",
                 isinstance(fs, dict) and fs.get("rate") == 0.05 and fs.get("takerOnly") is True,
                 json.dumps(fs))
        print("NOTE netflix-global current event volume=%s liquidity=%s negRisk=%s" % (
            ev.get("volume"), ev.get("liquidity"), ev.get("negRisk")))

    st, ev = event("what-will-be-the-top-us-netflix-show-this-week-october-20")
    show("netflix-us HTTP 200 + non-empty", st == 200 and ev is not None,
         "HTTP %s, markets=%s" % (st, len(ev.get("markets", [])) if ev else 0))
    if ev:
        b = market(ev, "Below: Limited Series")
        show("netflix-us has 'Below: Limited Series'", b is not None,
             "outcomePrices=%s bestBid=%s bestAsk=%s" % (
                 mprices(b) if b else None, b and b.get("bestBid"), b and b.get("bestAsk")))
        print("NOTE netflix-us current volume=%s liquidity=%s" % (ev.get("volume"), ev.get("liquidity")))

    st, ev = event("1-spotify-song-this-week-october-16-20261012")
    show("spotify-global-oct16 HTTP 200 + non-empty", st == 200 and ev is not None,
         "HTTP %s, markets=%s" % (st, len(ev.get("markets", [])) if ev else 0))
    if ev:
        d = ev.get("description") or ""
        show("spotify description has Fridays + Fri..Thu week",
             "Fridays" in d and "beginning on the preceding Friday and ending on Thursday" in d,
             "resolutionSource=%r" % ev.get("resolutionSource"))
        m = market(ev, "KAROL G - BbY WOW")
        if not m:
            for x in ev.get("markets", []):
                if "KAROL G" in (x.get("groupItemTitle") or ""):
                    m = x
                    break
        show("spotify oct16 has KAROL G BbY WOW market", m is not None,
             ("outcomePrices=%s volume=%s" % (mprices(m), m.get("volume"))) if m else "")
        print("NOTE spotify-global-oct16 current event volume=%s" % ev.get("volume"))

    st, ev = event("1-spotify-song-in-the-us-this-week-october-23-10172026")
    show("spotify-us-oct23 HTTP 200 + non-empty", st == 200 and ev is not None,
         "HTTP %s, markets=%s" % (st, len(ev.get("markets", [])) if ev else 0))
    if ev:
        for t in ["Housewife", "Nicole Kidman"]:
            m = market(ev, t)
            show("spotify-us-oct23 has %r (prefix ok)" % t, m is not None,
                 ("title=%r outcomePrices=%s bestBid=%s bestAsk=%s" % (
                     m.get("groupItemTitle"), mprices(m), m.get("bestBid"), m.get("bestAsk"))) if m else "")

    st, ev = event("1-song-on-spotify-this-week-april-3")
    show("spotify historical april-3 HTTP 200 + non-empty", st == 200 and ev is not None,
         "HTTP %s, markets=%s" % (st, len(ev.get("markets", [])) if ev else 0))

    st, ev = event("top-netflix-show-this-week")
    show("dead probe slug returns empty list", st == 200 and ev is None, "HTTP %s, body=%r" % (st, ev))

    st, body = get("https://open.spotify.com/charts", timeout=40)
    print("NOTE open.spotify.com/charts (entry's cited resolution source) HTTP %s" % st)

    st, body = get("https://charts.spotify.com/charts/view/regional-global-weekly/latest", timeout=40)
    print("NOTE charts.spotify.com weekly page HTTP %s, %d bytes (front-end app)" % (st, len(body)))

    for u in ["https://kworb.net/spotify/",
              "https://kworb.net/spotify/country/global_daily.html",
              "https://kworb.net/spotify/country/us_daily.html"]:
        st, body = get(u, timeout=60)
        text = body.decode("utf-8", "replace")
        date = re.search(r"Spotify Daily Chart - [A-Za-z ]+ - (\d{4}/\d{2}/\d{2})", text)
        print("NOTE %s HTTP %s bytes=%d current-chart-date=%s" % (
            u, st, len(body), date.group(1) if date else "n/a"))

    for u in ["https://www.netflix.com/tudum/top10/tv",
              "https://www.netflix.com/tudum/top10/united-states/tv"]:
        st, body = get(u, timeout=90)
        text = body.decode("utf-8", "replace")
        label = re.search(r"(Global|United States)\s*\|\s*(\d+/\d+/\d+\s*-\s*\d+/\d+/\d+)", text)
        print("NOTE %s HTTP %s bytes=%d current-label=%s" % (
            u, st, len(body), label.group(0) if label else "n/a"))

    st, body = get("https://flixpatrol.com/top10/netflix/world/", timeout=40)
    print("NOTE flixpatrol HTTP %s bytes=%d (entry says 403 on 2026-10-20)" % (st, len(body)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
