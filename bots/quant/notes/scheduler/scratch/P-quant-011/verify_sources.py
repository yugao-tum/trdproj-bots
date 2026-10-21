#!/usr/bin/env python3
"""Verify every source URL cited by quant-011 (keyless public GETs only)."""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "quant-research-q011-verify/1.0 (keyless public data)"}


def get(url, accept_json=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        return r.status, r.geturl(), r.headers.get("content-type", ""), body


def show_market(slug):
    url = "https://gamma-api.polymarket.com/markets?slug=" + slug
    st, final, ct, body = get(url)
    arr = json.loads(body)
    print("\n%s\n  HTTP %s %s %s bytes -> %d market(s)"
          % (url, st, ct, len(body), len(arr)))
    if not arr:
        return
    m = arr[0]
    print("  question: %s" % m.get("question"))
    print("  bestBid=%s bestAsk=%s spread=%s lastTradePrice=%s"
          % (m.get("bestBid"), m.get("bestAsk"), m.get("spread"),
             m.get("lastTradePrice")))
    print("  outcomePrices=%s liquidity=%s endDate=%s"
          % (m.get("outcomePrices"), m.get("liquidity"), m.get("endDate")))
    print("  orderPriceMinTickSize=%s orderMinSize=%s negRisk=%s"
          % (m.get("orderPriceMinTickSize"), m.get("orderMinSize"),
             m.get("negRisk")))
    print("  feeSchedule=%s" % json.dumps(m.get("feeSchedule")))
    desc = m.get("description") or ""
    for needle in [
        "first 90 minutes of regular play plus stoppage time",
        "If the game is postponed",
        "If the game is canceled entirely, with no make-up game",
        "The primary resolution source for this market is the official statistics",
        "If no acceptable data is available within 24 hours",
        "Revisions to officially declared final scores",
    ]:
        print("  description contains %r: %s"
              % (needle, needle.lower() in desc.lower()))


def main():
    print("quant-011 source verification, access 2026-10-21, keyless GET only")

    print("\n== Polymarket fee documentation ==")
    url = "https://docs.polymarket.com/trading/fees"
    st, final, ct, body = get(url)
    text = body.decode("utf-8", "replace")
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain)
    print("%s\n  HTTP %s %s %d bytes" % (url, st, ct, len(body)))
    for needle in ["feeRate", "Makers are never charged fees",
                   "Only takers pay fees", "Sports"]:
        print("  contains %r: %s" % (needle, needle.lower() in plain.lower()))
    m = re.search(r"fee\s*=\s*[^<]{0,120}", plain, re.I)
    print("  fee formula snippet: %s" % (m.group(0) if m else "NOT FOUND"))

    show_market("epl-liv-ars-2026-11-01-draw")
    show_market("sea-ata-par-2026-11-02-draw")

    print("\n== Gamma closed-event keyset (EPL) ==")
    url = ("https://gamma-api.polymarket.com/events/keyset?"
           + urllib.parse.urlencode({"closed": "true", "tag_slug": "EPL",
                                     "limit": 100}))
    st, final, ct, body = get(url)
    payload = json.loads(body)
    evs = payload.get("events", [])
    print("%s\n  HTTP %s %s %d bytes; events=%d next_cursor=%s"
          % (url, st, ct, len(body), len(evs),
             "yes" if payload.get("next_cursor") else "no"))
    if evs:
        e = evs[0]
        draw = [m for m in e.get("markets", [])
                if (m.get("slug") or "").endswith("-draw")
                or "end in a draw" in (m.get("question") or "").lower()]
        print("  sample event: %s | %s | draw markets=%d"
              % (e.get("slug"), e.get("title"), len(draw)))
        if draw:
            print("  sample draw conditionId=%s gameStartTime=%s"
                  % (draw[0].get("conditionId"), draw[0].get("gameStartTime")))

    print("\n== data-api per-trade fills ==")
    with (HERE / "matches.csv").open(newline="", encoding="utf-8") as fh:
        first = next(csv.DictReader(fh))
    cid = first["condition_id"]
    url = ("https://data-api.polymarket.com/trades?"
           + urllib.parse.urlencode({"market": cid, "limit": 5}))
    st, final, ct, body = get(url)
    arr = json.loads(body)
    print("%s\n  HTTP %s %s %d bytes; trades=%d"
          % (url, st, ct, len(body), len(arr)))
    if arr:
        t = arr[0]
        print("  keys: %s" % ",".join(sorted(t.keys())))
        print("  sample: side=%s outcome=%s price=%s size=%s timestamp=%s"
              % (t.get("side"), t.get("outcome"), t.get("price"),
                 t.get("size"), t.get("timestamp")))

    print("\n== football-data.co.uk CSVs (8 separate URLs) ==")
    for season in ("2223", "2324", "2425", "2526"):
        for league in ("E0", "I1"):
            url = ("https://www.football-data.co.uk/mmz4281/%s/%s.csv"
                   % (season, league))
            st, final, ct, body = get(url)
            text = body.decode("latin-1")
            n = len(list(csv.reader(io.StringIO(text)))) - 1
            print("  %s -> HTTP %s %d bytes rows=%d" % (url, st, len(body), n))

    print("\n== CLOB prices-history (entry's example token) ==")
    url = ("https://clob.polymarket.com/prices-history?market="
           "115347507753485536976403009642719279973942206992108120088763998979"
           "109693996472&interval=max&fidelity=60")
    st, final, ct, body = get(url)
    payload = json.loads(body)
    hist = payload.get("history", [])
    print("%s\n  HTTP %s %s %d bytes; points=%d"
          % (url, st, ct, len(body), len(hist)))
    if hist:
        print("  first=%s last=%s" % (hist[0], hist[-1]))
    print("  note: prices-history is NOT used as a fill price in the replay; "
          "the replay uses data-api trades.")


if __name__ == "__main__":
    main()
