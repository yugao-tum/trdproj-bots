#!/usr/bin/env python3
"""Fetch public data for quant-005 replay.

Sources (all free, no key):
  - Gamma events (series 10816, closed)          -> _cache/events.json
  - xtracker Elon posts feed                      -> _cache/posts.json
  - data-api per-trade fills for every market     -> _cache/trades/<conditionId>.json

Raw files stay in scratch/H-quant-005/_cache/ and are gitignored.
"""
import concurrent.futures as cf
import datetime as dt
import json
import os
import pathlib
import urllib.request

CACHE = pathlib.Path(os.environ.get("Q005_CACHE", pathlib.Path(__file__).resolve().parents[2]
                                     / "notes/scheduler/scratch/H-quant-005/_cache"))
UA = {"User-Agent": "quant-research/1.0 (public data only)"}
EVENTS = "https://gamma-api.polymarket.com/events?series_id=10816&closed=true&limit=100&offset={off}"
POSTS = "https://xtracker.polymarket.com/api/users/elonmusk/posts?limit=100&offset=0"
TRADES = "https://data-api.polymarket.com/trades?market={cid}&limit=10000&offset=0"


def get_json(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "trades").mkdir(exist_ok=True)

    events = []
    for off in (0, 100, 200, 300):
        page = get_json(EVENTS.format(off=off))
        if not page:
            break
        events += page
    # one archived duplicate event shares a window with the tradable event: drop archived slugs
    events = [e for e in events if not e["slug"].startswith("arch-")]
    (CACHE / "events.json").write_text(json.dumps(events), encoding="utf-8")

    posts = get_json(POSTS)["data"]
    (CACHE / "posts.json").write_text(json.dumps(posts), encoding="utf-8")

    cids = sorted({m["conditionId"] for e in events for m in e["markets"]})
    todo = [c for c in cids if not (CACHE / "trades" / f"{c}.json").exists()]
    print(f"events={len(events)} markets={len(cids)} to_fetch={len(todo)}", flush=True)

    def one(cid):
        try:
            data = get_json(TRADES.format(cid=cid))
            (CACHE / "trades" / f"{cid}.json").write_text(json.dumps(data), encoding="utf-8")
            return cid, len(data), None
        except Exception as exc:  # noqa: BLE001 - report and continue
            return cid, 0, repr(exc)

    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for i, (cid, n, err) in enumerate(pool.map(one, todo), 1):
            if err:
                print(f"FAIL {cid} {err}", flush=True)
            if i % 100 == 0:
                print(f"{i}/{len(todo)} fetched", flush=True)
    print("done", dt.datetime.now(dt.timezone.utc).isoformat(), flush=True)


if __name__ == "__main__":
    main()
