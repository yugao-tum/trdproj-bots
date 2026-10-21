#!/usr/bin/env python3
"""Small keyless data-api fetch helper used by the strict-fill re-runs.

Only public data-api endpoints are used.  Raw responses are cached under
/tmp/postdecision-fills-cache (never inside the repository).
"""
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

CACHE = os.environ.get(
    "POSTDECISION_FILLS_CACHE", "/tmp/postdecision-fills-cache"
)
DATA_API = "https://data-api.polymarket.com/trades"
UA = {"User-Agent": "quant-research-postdecision-fills/1.0 (keyless public data)"}
_LOCK = threading.Lock()
_SESSION_LOCAL = threading.local()


def _cache_path(key):
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json")


def _get(url, retries=6):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.load(fh)
        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                return {"_http400": True}
            last = exc
        except Exception as exc:
            last = exc
        time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("GET failed: %s (%s)" % (url, last))


def fetch_trades(condition_id, lo_ts, hi_ts, limit=500):
    """Return trades with lo_ts <= timestamp <= hi_ts, ascending by timestamp.

    data-api returns newest first.  Paginate backwards until an entire page is
    older than lo_ts, so no post-decision trade is missed.
    """
    key = "trades:%s:%d:%d:%d" % (condition_id, int(lo_ts), int(hi_ts), limit)
    path = _cache_path(key)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    kept = []
    offset = 0
    while offset <= 10000:
        params = {"market": condition_id, "limit": limit, "offset": offset}
        url = DATA_API + "?" + urllib.parse.urlencode(params)
        page = _get(url)
        if isinstance(page, dict) and page.get("_http400"):
            break
        if not isinstance(page, list) or not page:
            break
        kept.extend(page)
        oldest = min(int(t.get("timestamp") or 0) for t in page)
        if oldest < lo_ts or len(page) < limit:
            break
        offset += limit

    rows = [t for t in kept if lo_ts <= int(t.get("timestamp") or 0) <= hi_ts]
    rows.sort(key=lambda t: (int(t.get("timestamp") or 0),
                             str(t.get("transactionHash") or "")))
    with _LOCK:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, separators=(",", ":"))
    return rows


def yes_price(trade):
    p = float(trade["price"])
    return 1.0 - p if str(trade.get("outcome", "")).lower().startswith("no") else p


def first_yes_price(trades, start_ts, end_ts=None):
    """First trade at/after start_ts, mapped to a YES-equivalent price."""
    for t in trades:
        ts = int(t.get("timestamp") or 0)
        if ts < start_ts:
            continue
        if end_ts is not None and ts > end_ts:
            break
        return yes_price(t), ts
    return None, None
