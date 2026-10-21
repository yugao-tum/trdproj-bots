#!/usr/bin/env python3
"""
quant-016 historical executable-price backtest.

PRE-DECLARED DESIGN (written before any P&L was computed; do not tune after results)
====================================================================================

Universe (all closed Polymarket Rotten Tomatoes score events we can enumerate)
-----------------------------------------------------------------------------
Gamma keyless endpoint:
  https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500
      &closed=true&order=endDate&ascending=false
Every returned event is kept (no sampling).  Query, count and endDate span are printed.
Each event is mapped to its RT film page with the keyless RT search page
(https://www.rottentomatoes.com/search?search=<film title>): choose the exact-title
result whose release year is closest to the event year.  Unmapped events are recorded
with the reason.  One event = one independent result (all its thresholds share one
settlement).  Range-style brackets are excluded from trading/scoring, as the entry
explicitly says "不做区间写法"; the only such event is reported separately.

Decision time and snapshots
---------------------------
T = the rule's reading time, parsed from the Gamma rules text as
    "at 10:00 AM ET on <Month D, YYYY>" -> America/New_York -> UTC.
Primary decision time t = latest Wayback capture in [T-72h, T-12h] of
    https://www.rottentomatoes.com/m/<rt_slug>
whose page contains a parsable `criticsScore` object with reviewCount >= 1 and
likedCount+notLikedCount >= 1.  Sensitivity window [T-7d, T-24h].
Capture lists come from the CDX API:
    https://web.archive.org/cdx/search/cdx?url=rottentomatoes.com/m/<slug>
        &output=json&from=...&to=...&filter=statuscode:200
(fallback: Wayback timemap JSON / availability API if CDX is temporarily unavailable).
If the latest capture in the window is not parsable, we walk backwards through the
captures in that window, as declared.  Events with no such capture are skipped and
counted.  Archive requests are throttled to <= 1/second, retried with backoff, and all
raw responses are cached under _cache/.

Model (exactly the entry's Beta-Binomial)
-----------------------------------------
At t read k=likedCount, m=notLikedCount, n=k+m, and the displayed score (if any).
The latent fresh proportion is p ~ Beta(k+1, m+1) (uniform prior).
RT displays floor(100*p).  For a cumulative threshold T:
    displayed >= T  <=>  floor(100*p) >= T  <=>  p >= T/100
    P_T = 1 - I_{T/100}(k+1, m+1)   (regularized incomplete beta).
Probabilities are forced non-increasing in T within an event (PAVA isotonic), although
for the same Beta posterior they are already monotone.
"No score by deadline" tail: if the snapshot already contains a non-empty `score`,
the tail probability is set to 0 (declared).  If the snapshot has counts but no displayed
score, we use the entry's upper-bound prior q0 = 14/85 = 0.16470588235294117; then
P_YES(T) = (1-q0)*P_T and the q0 mass resolves all thresholds NO.  No other prior is used.

Executable price, fee, trigger, holding
---------------------------------------
For each threshold market, use the last data-api trade in [t-6h, t]:
    https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&start=..&end=..
`outcome="Yes"` gives the YES price directly; `outcome="No"` -> YES price = 1-price.
Mid = that YES price.  Conservative taker execution (the entry proposed maker; this is
the conservative taker-at-touch test, stated here):
    ask_yes = mid + 0.01, bid_yes = mid - 0.01
    buy YES at ask_yes; buy NO at 1-bid_yes (= mid_no + 0.01).
Fee per share = feeSchedule.rate * entry_price * (1-entry_price), rate taken from the
market's Gamma `feeSchedule` (the family is culture, GUIDE section 8 rate 0.05; the
observed value is also 0.05).  Taker fee is charged; maker rebate is ignored (conservative).
Trigger, as in the entry's edge test (edge measured vs mid, so the 1c half-spread is paid
in addition to being counted in the hurdle):
    YES: P_T - mid           > fee(ask_yes) + 0.01 + 0.02
    NO : mid - P_T           > fee(no_ask)  + 0.01 + 0.02
If both fire, take the larger edge.  Hold to Gamma resolution (`outcomePrices`, YES at
index of outcome "Yes"); no early exit.  One share per triggered threshold.
Gross/share = payoff - entry_price; Net/share = gross/share - fee.

Independent result / verdict
----------------------------
Event result = sum of net/share over its triggered thresholds (equal one share each).
"Independent priced event" = an event with >= 1 threshold having BOTH a model snapshot
and an executable trade in the price window.  Frozen criterion, mapped to the requested
three-way verdict (pre-declared):
  * independent priced events < 30                                  -> INSUFFICIENT
  * >= 30 and (model Brier > market Brier OR model log loss > market
    log loss OR median event net <= 0 OR median filled-share gross <= 0) -> FAIL
  * >= 30 and none of the above                                     -> PASS
Mean event net is reported with an event-cluster bootstrap 95% CI
(10,000 draws, seed 20261021).  Brier/log loss are reported on all scored thresholds and
at event level (mean of per-event means, so a 15-bracket event does not dominate).

Everything is deterministic: no wall-clock time is printed, only ACCESS_DATE.  Re-runs
read _cache/ and reproduce the same stdout and events.csv.
"""

import collections
import csv
import datetime as dt
import gzip
import hashlib
import html
import json
import math
import os
import pathlib
import random
import re
import sys
import time

import numpy as np
import requests

ACCESS_DATE = "2026-10-21"
SEED = 20261021
BASE = pathlib.Path(__file__).resolve().parent
CACHE = BASE / "_cache"
OUT = BASE
CACHE.mkdir(exist_ok=True)

GAMMA = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
ARCHIVE = "https://web.archive.org"
AVAIL = "https://archive.org/wayback/available"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "q016-hist-research/1.0 (academic, keyless, <=1 req/s to archive.org)",
    "Accept-Language": "en-US,en;q=0.9",
})
RT_SESSION = requests.Session()
RT_SESSION.headers.update({
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
})

FEE_RATE_DEFAULT = 0.05
HALF_SPREAD = 0.01
BUFFER = 0.02
TAIL_Q0 = 14.0 / 85.0
BOOL_N = 10000

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

_last_archive = 0.0


# --------------------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------------------
def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(s))[:180]


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True)


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def http_get(url, params=None, session=SESSION, tries=5, timeout=60, sleep=0.4):
    last = None
    for i in range(tries):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except Exception as e:  # network/TLS
            last = f"{type(e).__name__}: {e}"
        time.sleep(sleep * (i + 1))
    raise RuntimeError(f"GET failed {url} {params}: {last}")


def _throttle_archive():
    global _last_archive
    wait = 1.05 - (time.monotonic() - _last_archive)
    if wait > 0:
        time.sleep(wait)


def archive_get(url, params=None, cache_path=None, tries=7):
    """Keyless archive.org GET, <=1 req/s, backoff, decompress, cache bytes."""
    if cache_path is not None and cache_path.exists():
        return cache_path.read_bytes()
    last = None
    for i in range(tries):
        _throttle_archive()
        try:
            r = SESSION.get(url, params=params, timeout=75)
            _last_archive = time.monotonic()
            body = r.content
            if r.status_code == 200 and b"Temporarily Offline" not in body[:4000]:
                if body[:2] == b"\x1f\x8b":
                    body = gzip.decompress(body)
                if cache_path is not None:
                    write_bytes(cache_path, body)
                return body
            last = f"HTTP {r.status_code}"
        except Exception as e:
            _last_archive = time.monotonic()
            last = f"{type(e).__name__}: {e}"
        time.sleep(min(30, 2 ** i))
    raise RuntimeError(f"archive GET failed {url} {params}: {last}")


# --------------------------------------------------------------------------------------
# 1. Gamma enumeration
# --------------------------------------------------------------------------------------
def load_events():
    cache = CACHE / "gamma_closed.json"
    if cache.exists():
        return read_json(cache)
    r = http_get(f"{GAMMA}/events", {
        "tag_slug": "rotten-tomatoes", "limit": 500, "closed": "true",
        "order": "endDate", "ascending": "false",
    })
    data = r.json()
    write_json(cache, data)
    return data


def event_title_film(e):
    t = e.get("title", "")
    m = re.match(r'^[\"“](.+?)[\"”]\s+Rotten Tomatoes', t, re.I)
    if m:
        return m.group(1)
    return re.sub(r"\s*Rotten Tomatoes.*$", "", t, flags=re.I).strip(' "“”')


def parse_threshold(gi):
    s = str(gi).strip()
    m = re.fullmatch(r"(\d+)\s*\+?", s)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------------------
# 2. map event -> RT slug via the live keyless RT search page
# --------------------------------------------------------------------------------------
def norm_text(x):
    x = html.unescape(x).lower()
    return re.sub(r"[^a-z0-9]+", "", x)


def parse_rt_search(page):
    rows = []
    for blk in page.split('data-qa="data-row"')[1:]:
        h = re.search(r'href="(https://www\.rottentomatoes\.com/m/[^"]+)"', blk)
        a = re.search(r'alt="([^"]*)"', blk)
        y = re.search(r'release-year="([^"]*)"', blk)
        if h and a:
            rows.append({
                "title": html.unescape(a.group(1)),
                "rt_slug": h.group(1).split("/m/")[-1].split("/")[0],
                "year": y.group(1) if y else "",
            })
    return rows


def map_event(e):
    film = event_title_film(e)
    event_year = int((e.get("endDate") or e.get("closedTime") or "2026")[:4])
    key = hashlib.sha1(film.encode("utf-8")).hexdigest()[:16]
    cache = CACHE / "rt_search" / f"{key}.html"
    if cache.exists():
        page = cache.read_text(encoding="utf-8", errors="replace")
    else:
        r = RT_SESSION.get("https://www.rottentomatoes.com/search",
                           params={"search": film}, timeout=45)
        page = r.text
        if r.status_code == 200:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(page, encoding="utf-8")
    rows = parse_rt_search(page)
    exact = [x for x in rows if norm_text(x["title"]) == norm_text(film)]

    def dy(x):
        try:
            return abs(int(x["year"]) - event_year)
        except Exception:
            return 99

    exact_sorted = sorted(exact, key=dy)
    if exact_sorted:
        pick = exact_sorted[0]
        return {
            "film": film, "rt_slug": pick["rt_slug"], "rt_title": pick["title"],
            "rt_year": pick["year"], "map_method": "rt_search_exact_title",
            "map_note": "" if dy(pick) <= 1 else f"release_year_diff={dy(pick)}",
        }
    # fallback: event slug's film part with hyphens -> underscores
    base = re.sub(r"-rotten-tomato(es)?-score.*$", "", e["slug"])
    return {
        "film": film, "rt_slug": base.replace("-", "_"), "rt_title": "",
        "rt_year": "", "map_method": "slug_fallback_no_exact_title",
        "map_note": f"search_rows={len(rows)}",
    }


# --------------------------------------------------------------------------------------
# 3. resolution time from the rules text
# --------------------------------------------------------------------------------------
def resolution_time(e):
    desc = e.get("description", "")
    m = re.search(r"at 10:00 AM ET on ([A-Z][a-z]+) (\d{1,2}), (\d{4})", desc)
    if m:
        try:
            from zoneinfo import ZoneInfo
            local = dt.datetime(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)),
                                10, 0, tzinfo=ZoneInfo("America/New_York"))
            return local.astimezone(dt.timezone.utc), "rules_text_10am_ET"
        except Exception:
            pass
    c = e.get("closedTime") or e.get("endDate")
    return dt.datetime.fromisoformat(c.replace("Z", "+00:00")), "closedTime_fallback"


# --------------------------------------------------------------------------------------
# 4. Wayback capture list and page parsing
# --------------------------------------------------------------------------------------
def cdx_captures(rt_slug, start, end):
    cache = CACHE / "cdx" / f"{safe_name(rt_slug)}_{start:%Y%m%d%H%M}_{end:%Y%m%d%H%M}.json"
    if cache.exists():
        try:
            cached = read_json(cache)
            if isinstance(cached, list) and (not cached or
                                             (isinstance(cached[0], dict) and "ts" in cached[0])):
                return cached
        except Exception:
            pass
    params = {
        "url": f"rottentomatoes.com/m/{rt_slug}",
        "output": "json",
        "from": start.strftime("%Y%m%d%H%M%S"),
        "to": end.strftime("%Y%m%d%H%M%S"),
        "filter": "statuscode:200",
    }
    raw = archive_get(f"{ARCHIVE}/cdx/search/cdx", params=params, cache_path=cache)
    text = raw.decode("utf-8", errors="replace").strip()
    rows = []
    if text:
        try:
            j = json.loads(text)
            if j and isinstance(j, list):
                head = j[0]
                for row in j[1:]:
                    rec = dict(zip(head, row))
                    rows.append({
                        "ts": rec.get("timestamp", ""),
                        "original": rec.get("original", ""),
                        "status": rec.get("statuscode", ""),
                    })
        except Exception:
            rows = []
    write_json(cache, rows)
    return rows


def timemap_captures(rt_slug):
    cache = CACHE / "timemap" / f"{safe_name(rt_slug)}.json"
    url = f"{ARCHIVE}/web/timemap/json/https://www.rottentomatoes.com/m/{rt_slug}"
    raw = archive_get(url, cache_path=cache)
    text = raw.decode("utf-8", errors="replace")
    try:
        j = json.loads(text)
        head = j[0]
        rows = []
        for row in j[1:]:
            rec = dict(zip(head, row))
            rows.append({"ts": rec.get("timestamp", ""),
                         "original": rec.get("original", ""),
                         "status": rec.get("statuscode", "")})
        return rows
    except Exception:
        return []


def availability_closest(rt_slug, when):
    key = f"{safe_name(rt_slug)}_{when:%Y%m%d%H%M%S}.json"
    cache = CACHE / "avail" / key
    if cache.exists():
        try:
            return read_json(cache)
        except Exception:
            pass
    raw = archive_get(AVAIL, params={
        "url": f"rottentomatoes.com/m/{rt_slug}",
        "timestamp": when.strftime("%Y%m%d%H%M%S"),
    })
    obj = json.loads(raw.decode("utf-8", errors="replace"))
    write_json(cache, obj)
    return obj


def ts_of(s):
    return dt.datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)


def extract_critics(page_text):
    idx = page_text.find('"criticsScore"')
    while idx != -1:
        b = page_text.find("{", idx)
        if b == -1:
            return None
        depth = 0
        in_str = False
        esc = False
        end = -1
        for i in range(b, min(len(page_text), b + 20000)):
            ch = page_text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
        if end == -1:
            return None
        try:
            obj = json.loads(page_text[b:end])
        except Exception:
            idx = page_text.find('"criticsScore"', idx + 1)
            continue
        if "likedCount" in obj or "reviewCount" in obj:
            out = {}
            for k in ("likedCount", "notLikedCount", "reviewCount", "score", "scorePercent"):
                v = obj.get(k)
                if k in ("likedCount", "notLikedCount", "reviewCount"):
                    try:
                        v = int(v)
                    except Exception:
                        v = 0
                out[k] = v
            out["snippet"] = page_text[idx:end][:400]
            return out
        idx = page_text.find('"criticsScore"', idx + 1)
    return None


def fetch_snapshot(rt_slug, ts):
    cache = CACHE / "pages" / safe_name(rt_slug) / f"{ts}.html"
    if cache.exists():
        raw = cache.read_bytes()
    else:
        url = f"{ARCHIVE}/web/{ts}id_/https://www.rottentomatoes.com/m/{rt_slug}"
        raw = archive_get(url, cache_path=cache)
    text = raw.decode("utf-8", errors="replace")
    return text


def pick_in_window(rt_slug, start, end, captures):
    """Latest capture in [start,end] whose criticsScore parses; walks backwards."""
    cands = sorted({c["ts"] for c in captures
                    if c.get("status") == "200" and start <= ts_of(c["ts"]) <= end},
                   reverse=True)
    for ts in cands:
        try:
            text = fetch_snapshot(rt_slug, ts)
        except Exception:
            continue
        sc = extract_critics(text)
        if not sc:
            continue
        k = int(sc.get("likedCount") or 0)
        m = int(sc.get("notLikedCount") or 0)
        rc = int(sc.get("reviewCount") or 0)
        if rc >= 1 and k + m >= 1:
            return {"ts": ts, "critics": sc, "candidates": len(cands)}
    return None


def snapshots_for_event(rt_slug, t_primary_end, t_sens_end, T):
    # one capture list over the sensitivity window (superset of primary)
    start = T - dt.timedelta(days=7)
    end = T
    captures = None
    src = "cdx"
    try:
        captures = cdx_captures(rt_slug, start, end)
    except Exception:
        captures = None
    if captures is None or len(captures) == 0:
        try:
            captures = timemap_captures(rt_slug)
            src = "timemap"
        except Exception:
            captures = []
            src = "none"
    if captures:
        captures = [c for c in captures
                    if c.get("status") == "200" and start <= ts_of(c["ts"]) <= end]
    primary = pick_in_window(rt_slug, T - dt.timedelta(hours=72),
                             T - dt.timedelta(hours=12), captures) if captures else None
    sens = pick_in_window(rt_slug, T - dt.timedelta(days=7),
                          T - dt.timedelta(hours=24), captures) if captures else None
    # last-resort availability API if CDX/timemap had nothing in the primary window
    if primary is None:
        try:
            obj = availability_closest(rt_slug, T - dt.timedelta(hours=12))
            c = (obj.get("archived_snapshots") or {}).get("closest") or {}
            if c.get("status") == "200":
                ts = c["timestamp"]
                if T - dt.timedelta(hours=72) <= ts_of(ts) <= T - dt.timedelta(hours=12):
                    text = fetch_snapshot(rt_slug, ts)
                    sc = extract_critics(text)
                    if sc and int(sc.get("reviewCount") or 0) >= 1 and \
                            int(sc.get("likedCount") or 0) + int(sc.get("notLikedCount") or 0) >= 1:
                        primary = {"ts": ts, "critics": sc, "candidates": 1}
                        src = "availability"
        except Exception:
            pass
    return primary, sens, src


# --------------------------------------------------------------------------------------
# 5. Beta posterior / thresholds / resolution
# --------------------------------------------------------------------------------------
def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        dele = d * c
        h *= dele
        if abs(dele - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def model_probs(k, m, thresholds, has_score):
    a, b = k + 1.0, m + 1.0
    q0 = 0.0 if has_score else TAIL_Q0
    vals = []
    for T in thresholds:
        p = 1.0 - betai(a, b, min(0.999999999, max(1e-9, T / 100.0)))
        vals.append((1.0 - q0) * p)
    # isotonic non-increasing (pool adjacent violators)
    blocks = [[v, 1] for v in vals]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] < blocks[i + 1][0] - 1e-15:
            v = blocks[i][0] * blocks[i][1] + blocks[i + 1][0] * blocks[i + 1][1]
            w = blocks[i][1] + blocks[i + 1][1]
            blocks[i:i + 2] = [[v / w, w]]
            if i > 0:
                i -= 1
        else:
            i += 1
    out = []
    for v, w in blocks:
        out.extend([v] * w)
    return out


def market_resolution(m):
    try:
        outcomes = json.loads(m.get("outcomes") or "[]")
        prices = json.loads(m.get("outcomePrices") or "[]")
    except Exception:
        return None, None
    if not prices:
        return None, None
    yi = outcomes.index("Yes") if "Yes" in outcomes else 0
    yp = float(prices[yi])
    return (1 if yp > 0.5 else 0), yp


def final_interval(threshold_markets):
    """Return (lo, hi, all_no). Displayed final score is in [lo, hi)."""
    yes, no = [], []
    for t, m in threshold_markets:
        y, _ = market_resolution(m)
        if y == 1:
            yes.append(t)
        elif y == 0:
            no.append(t)
    if yes:
        lo = max(yes)
        hi = min([x for x in no if x > lo], default=100)
        return lo, hi, False
    return None, (min(no) if no else None), True


# --------------------------------------------------------------------------------------
# 6. data-api trades
# --------------------------------------------------------------------------------------
def get_trades(condition_id, start, end):
    start_i, end_i = int(start.timestamp()), int(end.timestamp())
    cache = CACHE / "trades" / f"{safe_name(condition_id)}_{start_i}_{end_i}.json"
    if cache.exists():
        try:
            return read_json(cache)
        except Exception:
            pass
    out = []
    offset = 0
    for _ in range(5):
        r = http_get(f"{DATA_API}/trades", {
            "market": condition_id, "limit": 500, "offset": offset,
            "start": start_i, "end": end_i,
        }, tries=5)
        chunk = r.json()
        out.extend(chunk)
        if len(chunk) < 500:
            break
        offset += 500
    write_json(cache, out)
    return out


def yes_price_from_trade(tr):
    try:
        p = float(tr.get("price"))
    except Exception:
        return None
    if not (0.0 <= p <= 1.0):
        return None
    if str(tr.get("outcome", "")).lower() == "no":
        return 1.0 - p
    return p


def last_yes_price(trades, t):
    best = None
    for tr in trades:
        try:
            ts = dt.datetime.fromtimestamp(int(tr["timestamp"]), tz=dt.timezone.utc)
        except Exception:
            continue
        if ts > t:
            continue
        p = yes_price_from_trade(tr)
        if p is None:
            continue
        if best is None or ts >= best[0]:
            best = (ts, p)
    return best


# --------------------------------------------------------------------------------------
# 7. scoring helpers
# --------------------------------------------------------------------------------------
def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = min(1 - 1e-9, max(1e-9, p))
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def bootstrap_mean(vals, seed=SEED, n=BOOL_N):
    if not vals:
        return (None, None)
    rng = np.random.default_rng(seed)
    a = np.asarray(vals, dtype=float)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    means = a[idx].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def median(xs):
    return float(np.median(xs)) if xs else None


def mean(xs):
    return float(np.mean(xs)) if xs else None


def fmt(x, nd=6):
    return "n/a" if x is None else f"{x:+.{nd}f}"


def fmtp(x, nd=6):
    return "n/a" if x is None else f"{x:.{nd}f}"


# --------------------------------------------------------------------------------------
# 8. build the event table
# --------------------------------------------------------------------------------------
def build_rows(events):
    rows = []
    for e in sorted(events, key=lambda x: x["slug"]):
        mp = map_event(e)
        T, tsrc = resolution_time(e)
        tms = []
        for m in e.get("markets", []):
            gi = m.get("groupItemTitle", "")
            th = parse_threshold(gi)
            tms.append({"market": m, "gi": gi, "T": th})
        if any(x["T"] is None for x in tms):
            # interval-style event (e.g. Mufasa): the entry excludes the whole event
            thr_markets = []
            range_markets = tms
        else:
            thr_markets = sorted([(x["T"], x["market"]) for x in tms])
            range_markets = []
        lo, hi, all_no = final_interval(thr_markets)
        year = int((e.get("endDate") or e.get("closedTime") or "2026")[:4])
        rows.append({
            "event": e, "mp": mp, "T": T, "time_source": tsrc,
            "threshold_markets": thr_markets, "range_markets": range_markets,
            "final_lo": lo, "final_hi": hi, "final_all_no": all_no,
            "event_year": year,
            "primary": None, "sens": None, "snap_source": None, "snap_error": "",
        })
    return rows


# --------------------------------------------------------------------------------------
# 9. simulate one decision window
# --------------------------------------------------------------------------------------
def simulate(rows, which):
    """which = 'primary' or 'sens'.  Fill row[which] with thresholds/trades/metrics."""
    for row in rows:
        snap = row.get(which)
        if not snap:
            continue
        sc = snap["critics"]
        k = int(sc.get("likedCount") or 0)
        m = int(sc.get("notLikedCount") or 0)
        has_score = bool(sc.get("score") not in (None, ""))
        thr = [t for t, _ in row["threshold_markets"]]
        probs = model_probs(k, m, thr, has_score)
        t = ts_of(snap["ts"])
        p_start = t - dt.timedelta(hours=6)
        trades_by_market = {}
        if row["threshold_markets"]:
            all_start = p_start
            all_end = max(t, t)
            for th, mk in row["threshold_markets"]:
                cid = mk.get("conditionId")
                if not cid:
                    continue
                try:
                    trades_by_market[cid] = get_trades(cid, all_start, all_end)
                except Exception:
                    trades_by_market[cid] = None
        det = []
        for (th, mk), pm in zip(row["threshold_markets"], probs):
            cid = mk.get("conditionId")
            trades = trades_by_market.get(cid)
            rec = {"T": th, "market": mk, "p": pm, "mid": None, "ts": None,
                   "side": None, "entry": None, "fee": 0.0, "payoff": None,
                   "gross": None, "net": None, "edge": None, "y": None}
            y, _ = market_resolution(mk)
            rec["y"] = y
            if trades is None:
                det.append(rec)
                continue
            last = last_yes_price(trades, t)
            if last is None:
                det.append(rec)
                continue
            mid = last[1]
            rec["mid"] = mid
            rec["ts"] = last[0]
            if not (0.0 < mid < 1.0):
                det.append(rec)
                continue
            rate = FEE_RATE_DEFAULT
            fs = mk.get("feeSchedule")
            if isinstance(fs, str):
                try:
                    fs = json.loads(fs)
                except Exception:
                    fs = None
            if isinstance(fs, dict) and fs.get("rate") is not None:
                try:
                    rate = float(fs["rate"])
                except Exception:
                    pass
            ask_y = mid + HALF_SPREAD
            bid_y = mid - HALF_SPREAD
            no_ask = 1.0 - bid_y
            fee_y = rate * ask_y * (1.0 - ask_y)
            fee_n = rate * no_ask * (1.0 - no_ask)
            edge_y = pm - mid
            edge_n = mid - pm
            hurdle_y = fee_y + HALF_SPREAD + BUFFER
            hurdle_n = fee_n + HALF_SPREAD + BUFFER
            if ask_y <= 1.0 and edge_y > hurdle_y and edge_y >= edge_n:
                rec.update({"side": "YES", "entry": ask_y, "fee": fee_y,
                            "payoff": float(y), "gross": float(y) - ask_y,
                            "net": float(y) - ask_y - fee_y, "edge": edge_y})
            elif no_ask <= 1.0 and edge_n > hurdle_n:
                rec.update({"side": "NO", "entry": no_ask, "fee": fee_n,
                            "payoff": 1.0 - float(y), "gross": (1.0 - float(y)) - no_ask,
                            "net": (1.0 - float(y)) - no_ask - fee_n, "edge": edge_n})
            det.append(rec)
        row[which + "_detail"] = det


# --------------------------------------------------------------------------------------
# 10. metrics
# --------------------------------------------------------------------------------------
def collect_metrics(rows, which):
    trades = []
    event_nets = []
    priced_events = 0
    model_b, mkt_b, model_l, mkt_l = [], [], [], []
    event_b_pairs, event_l_pairs = [], []
    for row in rows:
        det = row.get(which + "_detail")
        if not det:
            continue
        ev_trades = [d for d in det if d.get("side")]
        scored = [d for d in det if d.get("mid") is not None and d.get("y") is not None]
        if scored:
            priced_events += 1
        if ev_trades:
            trades.extend(ev_trades)
            event_nets.append(sum(d["net"] for d in ev_trades))
        if scored:
            eb_m, eb_k, el_m, el_k = [], [], [], []
            for d in scored:
                y = d["y"]
                model_b.append(brier(d["p"], y))
                mkt_b.append(brier(d["mid"], y))
                model_l.append(logloss(d["p"], y))
                mkt_l.append(logloss(d["mid"], y))
                eb_m.append(brier(d["p"], y))
                eb_k.append(brier(d["mid"], y))
                el_m.append(logloss(d["p"], y))
                el_k.append(logloss(d["mid"], y))
            event_b_pairs.append((mean(eb_m), mean(eb_k)))
            event_l_pairs.append((mean(el_m), mean(el_k)))
    staked = sum(d["entry"] for d in trades)
    total_net = sum(d["net"] for d in trades)
    gross = [d["gross"] for d in trades]
    ci = bootstrap_mean(event_nets, SEED, BOOL_N)
    return {
        "trades": trades, "event_nets": event_nets, "priced_events": priced_events,
        "staked": staked, "total_net": total_net,
        "median_event_net": median(event_nets), "mean_event_net": mean(event_nets),
        "ci": ci,
        "median_gross": median(gross), "mean_net_trade": mean([d["net"] for d in trades]),
        "median_net_trade": median([d["net"] for d in trades]),
        "hit": (sum(1 for d in trades if d["net"] > 0), len(trades)),
        "model_brier": mean(model_b), "mkt_brier": mean(mkt_b),
        "model_ll": mean(model_l), "mkt_ll": mean(mkt_l),
        "n_scored": len(model_b),
        "event_brier_model": mean([x[0] for x in event_b_pairs]),
        "event_brier_mkt": mean([x[1] for x in event_b_pairs]),
        "event_ll_model": mean([x[0] for x in event_l_pairs]),
        "event_ll_mkt": mean([x[1] for x in event_l_pairs]),
        "event_scored": len(event_b_pairs),
    }


def print_metrics(name, met):
    tr = met["trades"]
    print(f"-- {name}")
    print(f"   independent priced events={met['priced_events']}  scored thresholds={met['n_scored']}")
    print(f"   triggered trades={len(tr)}  events/triggered={len([x for x in met['event_nets']])}"
          f"  YES={sum(1 for d in tr if d['side']=='YES')}"
          f"  NO={sum(1 for d in tr if d['side']=='NO')}")
    print(f"   median event net/share={fmt(met['median_event_net'])}"
          f"  mean event net/share={fmt(met['mean_event_net'])}")
    lo, hi = met["ci"]
    print(f"   event-cluster bootstrap 95% CI of mean: [{fmt(lo)}, {fmt(hi)}]")
    print(f"   median trade gross/share={fmt(met['median_gross'])}"
          f"  median trade net/share={fmt(met['median_net_trade'])}"
          f"  mean trade net/share={fmt(met['mean_net_trade'])}")
    print(f"   hit rate (net>0)={met['hit'][0]}/{met['hit'][1]}"
          f" = {met['hit'][0]/met['hit'][1] if met['hit'][1] else 0:.3f}")
    print(f"   total net={fmt(met['total_net'])} on staked={fmtp(met['staked'])}"
          f" -> per $ staked={fmt(met['total_net']/met['staked']) if met['staked'] else 'n/a'}")
    print(f"   Brier  model={fmtp(met['model_brier'])} market={fmtp(met['mkt_brier'])}"
          f" diff={fmt((met['model_brier']-met['mkt_brier']) if met['model_brier'] is not None and met['mkt_brier'] is not None else None)}")
    print(f"   LogLoss model={fmtp(met['model_ll'])} market={fmtp(met['mkt_ll'])}"
          f" diff={fmt((met['model_ll']-met['mkt_ll']) if met['model_ll'] is not None and met['mkt_ll'] is not None else None)}")
    print(f"   event-level (equal weight per event) Brier model={fmtp(met['event_brier_model'])}"
          f" market={fmtp(met['event_brier_mkt'])}"
          f"  LogLoss model={fmtp(met['event_ll_model'])} market={fmtp(met['event_ll_mkt'])}")


# --------------------------------------------------------------------------------------
# 11. spot checks
# --------------------------------------------------------------------------------------
def live_rt_score(rt_slug):
    cache = CACHE / "rt_live" / f"{safe_name(rt_slug)}.html"
    if cache.exists():
        text = cache.read_text(encoding="utf-8", errors="replace")
        return extract_critics(text) if text else None
    cache.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = RT_SESSION.get(f"https://www.rottentomatoes.com/m/{rt_slug}", timeout=45)
        text = r.text if r.status_code == 200 else ""
    except Exception:
        text = ""
    cache.write_text(text, encoding="utf-8")
    return extract_critics(text) if text else None


def post_resolution_score(rt_slug, T):
    """Earliest archive capture after settlement (+12h, within 30d): the settled RT score."""
    start, end = T + dt.timedelta(hours=12), T + dt.timedelta(days=30)
    captures = []
    try:
        captures = cdx_captures(rt_slug, start, end)
    except Exception:
        captures = []
    if not captures:
        try:
            captures = [c for c in timemap_captures(rt_slug)
                        if c.get("status") == "200" and start <= ts_of(c["ts"]) <= end]
        except Exception:
            captures = []
    cands = sorted({c["ts"] for c in captures
                    if c.get("status") == "200" and start <= ts_of(c["ts"]) <= end})
    for ts in cands[:6]:
        try:
            sc = extract_critics(fetch_snapshot(rt_slug, ts))
        except Exception:
            sc = None
        if sc:
            return ts, sc
    return None, None


def spot_checks(rows, candidates):
    rng = random.Random(SEED)
    picks = rng.sample(candidates, min(3, len(candidates)))
    print("\n== spot checks (3 random events, seed %d)" % SEED)
    for row in picks:
        snap = row["primary"] or row["sens"]
        which = "primary" if row["primary"] else "sensitivity"
        sc = snap["critics"]
        print(f"\n-- {row['event']['slug']}  (RT /m/{row['mp']['rt_slug']}, {which} snapshot {snap['ts']})")
        print(f"   archived criticsScore snippet: {sc.get('snippet','')[:300]}")
        print(f"   parsed: liked={sc.get('likedCount')} notLiked={sc.get('notLikedCount')}"
              f" reviewCount={sc.get('reviewCount')} score={sc.get('score')}")
        lo, hi, all_no = row["final_lo"], row["final_hi"], row["final_all_no"]
        if all_no:
            print(f"   Gamma settlement: all brackets NO; final score < {hi}")
        else:
            print(f"   Gamma settlement: YES max={lo}, next NO={hi}; final displayed score in [{lo},{hi})")
        lts, lsc = post_resolution_score(row["mp"]["rt_slug"], row["T"])
        if lsc:
            print(f"   first archive capture after settlement ({lts}): "
                  f"liked={lsc.get('likedCount')} notLiked={lsc.get('notLikedCount')}"
                  f" reviewCount={lsc.get('reviewCount')} score={lsc.get('score')}")
        else:
            print("   first archive capture after settlement: 未取到")
        live = live_rt_score(row["mp"]["rt_slug"])
        if live:
            print(f"   live RT today (may have drifted): liked={live.get('likedCount')}"
                  f" notLiked={live.get('notLikedCount')}"
                  f" reviewCount={live.get('reviewCount')} score={live.get('score')}")
        else:
            print("   live RT today: 未取到")


# --------------------------------------------------------------------------------------
# 12. main
# --------------------------------------------------------------------------------------
def main():
    events = load_events()
    end_dates = sorted([e.get("endDate") for e in events if e.get("endDate")])
    print("quant-016 historical executable-price backtest")
    print(f"access date: {ACCESS_DATE}")
    print("Gamma query: tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false")
    print(f"closed events enumerated: {len(events)}")
    print(f"date span (endDate): {end_dates[0][:10] if end_dates else 'n/a'} .. "
          f"{end_dates[-1][:10] if end_dates else 'n/a'}"
          f"   (one event has endDate=null, closedTime {[e.get('closedTime') for e in events if not e.get('endDate')]})")

    rows = build_rows(events)
    n_markets = sum(len(e.get("markets", [])) for e in events)
    n_thr = sum(len(r["threshold_markets"]) for r in rows)
    n_range = sum(len(r["range_markets"]) for r in rows)
    print(f"markets: {n_markets} (cumulative-threshold markets {n_thr}, range-style {n_range})")
    rate_counter = collections.Counter()
    for r in rows:
        for _, mk in r["threshold_markets"]:
            fs = mk.get("feeSchedule")
            if isinstance(fs, str):
                try:
                    fs = json.loads(fs)
                except Exception:
                    fs = None
            if isinstance(fs, dict):
                rate_counter[(fs.get("rate"), fs.get("takerOnly"))] += 1
    print(f"feeSchedule (rate, takerOnly) observed: {dict(sorted(rate_counter.items(), key=str))}")
    mapped = [r for r in rows if r["mp"]["rt_slug"]]
    print(f"mapped to RT slug: {len(mapped)}/{len(rows)}")
    for r in rows:
        if not r["mp"]["rt_slug"]:
            print(f"  UNMAPPED {r['event']['slug']}: {r['mp']['map_note']}")

    # archive snapshots
    for r in rows:
        if r["range_markets"]:
            r["snap_error"] = "range_style_brackets_excluded"
            continue
        try:
            p, s, src = snapshots_for_event(
                r["mp"]["rt_slug"],
                r["T"] - dt.timedelta(hours=12),
                r["T"] - dt.timedelta(hours=24),
                r["T"])
            r["primary"], r["sens"], r["snap_source"] = p, s, src
        except Exception as e:
            r["snap_error"] = f"{type(e).__name__}: {e}"

    have_p = [r for r in rows if r["primary"]]
    have_s = [r for r in rows if r["sens"]]
    no_snap = [r for r in rows if not r["primary"] and not r["range_markets"]]
    srcs = collections.Counter(r["snap_source"] for r in rows if r["primary"])
    print(f"\nWayback: events with primary snapshot={len(have_p)}"
          f"  with sensitivity snapshot={len(have_s)}"
          f"  no primary snapshot (excl. range)={len(no_snap)}"
          f"  range-excluded={sum(1 for r in rows if r['range_markets'])}"
          f"  capture-list source={dict(sorted(srcs.items()))}")
    for r in rows:
        if r["snap_error"]:
            print(f"  SNAP-SKIP {r['event']['slug']}: {r['snap_error']}")

    # simulate
    simulate(rows, "primary")
    simulate(rows, "sens")

    met_p = collect_metrics(rows, "primary")
    met_s = collect_metrics(rows, "sens")

    print("\n" + "=" * 78)
    print_metrics("primary window [T-72h, T-12h], price [t-6h, t]", met_p)
    print_metrics("sensitivity [T-7d, T-24h], price [t-6h, t]", met_s)

    # snapshot freshness / agreement
    lags = [(r["T"] - ts_of(r["primary"]["ts"])).total_seconds() / 3600.0
            for r in have_p if r["primary"]]
    if lags:
        lags_sorted = sorted(lags)
        print(f"\nsnapshot lag T-t: median={median(lags):.2f}h"
              f" min={lags_sorted[0]:.2f}h max={lags_sorted[-1]:.2f}h")
    agree = 0
    agree_den = 0
    below_min = 0
    for r in have_p:
        sc = r["primary"]["critics"]
        try:
            sv = int(str(sc.get("score")).strip())
        except Exception:
            continue
        lo, hi, all_no = r["final_lo"], r["final_hi"], r["final_all_no"]
        if all_no:
            agree_den += 1
            if hi is not None and sv < hi:
                below_min += 1
        else:
            agree_den += 1
            if lo is not None and hi is not None and lo <= sv < hi:
                agree += 1
    n_noscore = sum(1 for r in have_p
                    if r["primary"]["critics"].get("score") in (None, ""))
    print(f"primary snapshots with displayed score: {len(have_p)-n_noscore}/{len(have_p)}"
          f"  (no-display-score snapshots use tail q0={TAIL_Q0:.6f}; with a score q0=0)")
    print(f"snapshot score equals final settlement interval (exact YES-range): {agree}/{agree_den}"
          f"  (all-NO events consistent with below-min: {below_min}/{sum(1 for r in have_p if r['final_all_no'])})")

    # triggered detail
    print("\ntriggered event detail (primary):")
    any_trig = False
    for r in rows:
        det = r.get("primary_detail") or []
        tr = [d for d in det if d.get("side")]
        if tr:
            any_trig = True
            print(f"  {r['event']['slug']}: "
                  + "; ".join(f"{d['side']}@{d['T']}+ p={d['p']:.3f} mid={d['mid']:.3f}"
                              f" net={d['net']:+.4f}" for d in tr)
                  + f"  sum_net={sum(d['net'] for d in tr):+.4f}")
    if not any_trig:
        print("  (none)")

    # spot checks
    spot_checks(rows, [r for r in rows if r["primary"] or r["sens"]])

    # verdict
    n_ev = met_p["priced_events"]
    if n_ev < 30:
        verdict = "INSUFFICIENT"
    else:
        worse_brier = (met_p["model_brier"] is not None and met_p["mkt_brier"] is not None
                       and met_p["model_brier"] > met_p["mkt_brier"])
        worse_ll = (met_p["model_ll"] is not None and met_p["mkt_ll"] is not None
                    and met_p["model_ll"] > met_p["mkt_ll"])
        bad_med_ev = (met_p["median_event_net"] is None or met_p["median_event_net"] <= 0)
        bad_med_gross = (met_p["median_gross"] is None or met_p["median_gross"] <= 0)
        verdict = "FAIL" if (worse_brier or worse_ll or bad_med_ev or bad_med_gross) else "PASS"
    print("\n" + "=" * 78)
    print(f"VERDICT: {verdict}")
    print(f"  independent priced events (primary) = {n_ev}  (threshold for verdict: 30)")
    if n_ev < 30:
        print("  -> fewer than 30 independent priced events: INSUFFICIENT")
    else:
        print(f"  model Brier {fmtp(met_p['model_brier'])} vs market {fmtp(met_p['mkt_brier'])}")
        print(f"  model logloss {fmtp(met_p['model_ll'])} vs market {fmtp(met_p['mkt_ll'])}")
        print(f"  median event net {fmt(met_p['median_event_net'])}; "
              f"median filled-share gross {fmt(met_p['median_gross'])}")

    # events.csv
    csv_path = OUT / "events.csv"
    fields = [
        "event_slug", "event_title", "film", "rt_slug", "map_method",
        "resolution_utc", "time_source", "event_end_date", "n_thresholds",
        "range_excluded", "snapshot_ts_primary", "snapshot_lag_h", "k", "m", "n",
        "score_t", "tail_q0", "snapshot_ts_sens", "snapshot_lag_h_sens",
        "k_sens", "m_sens", "score_sens", "final_lo", "final_hi", "final_all_no",
        "snapshot_score_equals_final", "priced_thresholds", "triggered",
        "yes_triggered", "no_triggered", "event_net", "event_staked", "event_hit",
        "model_brier_event", "market_brier_event", "model_ll_event", "market_ll_event",
        "snap_source", "note",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            det_p = r.get("primary_detail") or []
            det_s = r.get("sens_detail") or []
            tr = [d for d in det_p if d.get("side")]
            scored = [d for d in det_p if d.get("mid") is not None and d.get("y") is not None]
            p0 = r["primary"]["critics"] if r["primary"] else {}
            s0 = r["sens"]["critics"] if r["sens"] else {}
            eq = ""
            try:
                sv = int(str(p0.get("score")).strip())
                if r["final_all_no"]:
                    eq = "below_min" if (r["final_hi"] is not None and sv < r["final_hi"]) else "inconsistent"
                elif r["final_lo"] is not None:
                    eq = "yes" if r["final_lo"] <= sv < r["final_hi"] else "no"
            except Exception:
                eq = ""
            w.writerow({
                "event_slug": r["event"]["slug"],
                "event_title": r["event"].get("title", ""),
                "film": r["mp"]["film"],
                "rt_slug": r["mp"]["rt_slug"],
                "map_method": r["mp"]["map_method"],
                "resolution_utc": r["T"].isoformat(),
                "time_source": r["time_source"],
                "event_end_date": r["event"].get("endDate") or "",
                "n_thresholds": len(r["threshold_markets"]),
                "range_excluded": len(r["range_markets"]),
                "snapshot_ts_primary": r["primary"]["ts"] if r["primary"] else "",
                "snapshot_lag_h": (round((r["T"] - ts_of(r["primary"]["ts"])).total_seconds() / 3600, 4)
                                   if r["primary"] else ""),
                "k": p0.get("likedCount", ""), "m": p0.get("notLikedCount", ""),
                "n": (int(p0.get("likedCount") or 0) + int(p0.get("notLikedCount") or 0)
                      if p0 else ""),
                "score_t": p0.get("score", ""),
                "tail_q0": (0.0 if p0.get("score") not in (None, "") else TAIL_Q0) if p0 else "",
                "snapshot_ts_sens": r["sens"]["ts"] if r["sens"] else "",
                "snapshot_lag_h_sens": (round((r["T"] - ts_of(r["sens"]["ts"])).total_seconds() / 3600, 4)
                                        if r["sens"] else ""),
                "k_sens": s0.get("likedCount", ""), "m_sens": s0.get("notLikedCount", ""),
                "score_sens": s0.get("score", ""),
                "final_lo": "" if r["final_lo"] is None else r["final_lo"],
                "final_hi": "" if r["final_hi"] is None else r["final_hi"],
                "final_all_no": r["final_all_no"],
                "snapshot_score_equals_final": eq,
                "priced_thresholds": len(scored),
                "triggered": len(tr),
                "yes_triggered": sum(1 for d in tr if d["side"] == "YES"),
                "no_triggered": sum(1 for d in tr if d["side"] == "NO"),
                "event_net": round(sum(d["net"] for d in tr), 8) if tr else "",
                "event_staked": round(sum(d["entry"] for d in tr), 8) if tr else "",
                "event_hit": (sum(d["net"] for d in tr) > 0) if tr else "",
                "model_brier_event": (round(mean([brier(d["p"], d["y"]) for d in scored]), 8)
                                      if scored else ""),
                "market_brier_event": (round(mean([brier(d["mid"], d["y"]) for d in scored]), 8)
                                       if scored else ""),
                "model_ll_event": (round(mean([logloss(d["p"], d["y"]) for d in scored]), 8)
                                   if scored else ""),
                "market_ll_event": (round(mean([logloss(d["mid"], d["y"]) for d in scored]), 8)
                                    if scored else ""),
                "snap_source": r["snap_source"] or "",
                "note": r["snap_error"],
            })
    print(f"\nwrote {csv_path.name} ({csv_path.stat().st_size} bytes, {len(rows)} rows)")


if __name__ == "__main__":
    main()
