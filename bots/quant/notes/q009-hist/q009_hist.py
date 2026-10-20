#!/usr/bin/env python3
"""
quant-009 historical executable-price backtest.

PRE-DECLARED DESIGN (written before any P&L was computed; do not tune after seeing results)
===========================================================================================

Universe
--------
Enumerate with Gamma public-search (keyless) using the fixed query list in QUERIES below,
paginating while pagination.hasMore.  Keep an event only if event.closed is true and the
market is closed.  Keep a market only if its question (or event title) contains "list/
listed/listing" and at least one in-scope venue token (binance|coinbase|robinhood|upbit),
and its endDate is in the past.  Explicitly exclude, as different templates:
  * "... within 30 days of TGE" (relative-to-TGE deadline, placeholder endDate);
  * "announces ... listing" / "listing announcement" (announcement != spot listing);
  * "another Pump.fun coin" (no single token);
  * "Binance or Bybit" / Hyperliquid / other out-of-scope venue (entry is Binance,
    Coinbase, Robinhood, Upbit);
  * "which exchange will X list on", tokenized stocks, politics/name-list false positives.
Dedupe by conditionId.  Counts per venue and date span are printed.

One token-venue-deadline = one market result.  Markets for the same token+venue with
different deadlines are one cluster.  Multi-outcome "next coin listed on <venue>" events
are one independent result per event (cluster key = event slug); their "none of the named
coins" option is not a token and is not traded (but remains part of the event's resolution).

Model (walk-forward, no look-ahead)
-----------------------------------
p_model = 1 - exp(-lambda * T), T = days from entry to the market endDate.
lambda is a constant per-day listing hazard estimated only from markets whose resolution
was known (closedTime) strictly before the entry timestamp:
    lambda = (# Yes among resolved markets) / sum(exposure_days)
    exposure_days = [min(closedTime, endDate) - startDate] in days (>= 1 hour).
Using min(closedTime,endDate) censors early No resolutions (e.g. "first coin" races) at
the time the race was decided, and dates Yes events at resolution time.
Minimum history: >= 8 resolved token-venue markets, >= 1 Yes, and >= 365 cumulative
exposure days.  Markets whose entry timestamp comes before that are skipped (p_model=None).
Entry rule "p_model=1 if the exchange already announced" is NOT implemented: no keyless,
machine-readable, historical announcement timestamp exists for Coinbase/Robinhood/Upbit,
so all trades use the base-rate branch only.  (Binance CMS has some announcement dates but
not for every token; using it only for a subset would be a different, unannounced rule.)

Entry, executable price, fees
-----------------------------
Entry timestamp = endDate - 7 days (primary); sensitivity = endDate - 3 days.
Executable price = last data-api trade in [entry-2d, entry] (i.e. [endDate-9d,
endDate-7d] primary), converted to a YES price (outcome "No" -> 1 - price).
ask = trade_yes + 0.01, bid = trade_yes - 0.01 (half-spread assumption, as in the entry).
Buy YES if p_model - ask >= 0.01 + p_model*(1-p_model)*0.07.
Buy NO  if bid - p_model >= 0.01 + p_model*(1-p_model)*0.07.
(Threshold uses p_model exactly as written in the entry; the fee actually charged uses the
execution price p per GUIDE section 8.)
fee/share = 0.07 * entry_price * (1 - entry_price).  NO entry price = 1 - bid.
If both sides trigger, take the larger edge.  Hold to Gamma resolution; no early exit.
Net/share = payoff - entry_price - fee.

Independent result / verdict
----------------------------
Cluster result = mean net/share over triggered markets in the cluster (equal shares);
clusters with no trigger are not in the P&L median but count as priced history.
"Independent events with executable prices" = clusters with >= 1 priced market.
Frozen criterion, mapped to the requested three-way verdict:
  * total clusters < 30 OR priced clusters < 30  -> INSUFFICIENT
  * priced clusters >= 30 and median cluster net <= 0 -> FAIL
  * priced clusters >= 30 and median cluster net > 0  -> PASS
Mean cluster net is also reported with a cluster bootstrap 95% CI (10,000 draws, seed 42)
and total net per dollar staked.
Brier / log loss compare the walk-forward p_model with the last-trade market YES price on
all priced markets (binary resolution, payoff > 0.5 = Yes).

All downloads are cached under _cache/ and reused verbatim.  Output is deterministic:
no wall-clock timestamps are printed, only the fixed ACCESS_DATE.
"""

import csv
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import sys

import numpy as np
import requests

ACCESS_DATE = "2026-10-20"
BASE = pathlib.Path(__file__).resolve().parent
CACHE = BASE / "_cache"
CACHE.mkdir(exist_ok=True)
OUT = BASE
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "q009-hist-research/1.0"})

QUERIES = [
    "listed on binance",
    "listed on coinbase",
    "listed on robinhood",
    "list on upbit",
    "binance list",
    "coinbase list",
    "next coin on coinbase",
    "next coin on robinhood",
    "listed on upbit",
    "listed on bybit",
    "listed on kraken",
    "listed on okx",
    "spot listed",
    "will be listed on",
    "listed on exchange",
    "coin listed on",
    "listed for trading",
    "will coinbase list",
    "will binance list",
    "coinbase listing",
    "binance listing",
    "listed on coinbase or binance",
]

VENUES = ("binance", "coinbase", "robinhood", "upbit")
VENUE_RE = re.compile(r"\b(binance|coinbase|robinhood|upbit)\b", re.I)
LIST_RE = re.compile(r"\b(list|listed|listing)\b", re.I)
EXCLUDE_SUBSTR = [
    "within 30 days of tge",
    "announc",          # announcement markets are not spot-listing markets
    "another pump",     # no single token
    "or bybit",         # out-of-scope venue
    "tokenized stock",
    "which exchange",
    "first to list tokenized",
]
NONE_TOKEN_RE = re.compile(r"\bnone of the named\b", re.I)
TOKEN_DOLLAR_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9]*)")
TOKEN_WILL_BE_RE = re.compile(r"\bwill\s+(.+?)\s+be\s+(?:listed|list)\b", re.I)
TOKEN_LIST_VERB_RE = re.compile(
    r"\b(?:binance|coinbase|robinhood|upbit)\s+(?:list|lists|listing)\s+(.+)$", re.I
)
TOKEN_BEFORE_LISTED_RE = re.compile(r"^\s*(.+?)\s+(?:spot\s+)?listed\b", re.I)

MIN_HIST_MARKETS = 8
MIN_HIST_YES = 1
MIN_HIST_EXPOSURE_DAYS = 365.0
FEE_RATE = 0.07
HALF_SPREAD = 0.01
BASE_EDGE = 0.01
SEED = 42
BOOT_N = 10000


# ---------------------------------------------------------------- cache / fetch
def _cache_path(prefix, key):
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]
    return CACHE / f"{prefix}_{h}.json"


def fetch_json(url, params=None, prefix="get", key=None):
    cpath = _cache_path(prefix, key or (url + "?" + json.dumps(params or {}, sort_keys=True)))
    if cpath.exists():
        return json.loads(cpath.read_text())
    r = SESSION.get(url, params=params, timeout=45)
    r.raise_for_status()
    data = r.json()
    cpath.write_text(json.dumps(data, sort_keys=True))
    return data


def parse_dt(s):
    if not s:
        return None
    s = str(s).strip().replace(" ", "T", 1) if re.match(r"^\d{4}-\d\d-\d\d ", s) else str(s)
    s = s.replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def unix(d):
    return int(d.timestamp()) if d is not None else None


# ---------------------------------------------------------------- enumerate
def enumerate_events():
    events = {}
    per_query = []
    for q in QUERIES:
        page = 1
        n_before = len(events)
        while True:
            params = {"q": q, "limit_per_type": 50}
            if page > 1:
                params["page"] = page
            key = json.dumps(params, sort_keys=True)
            data = fetch_json(
                "https://gamma-api.polymarket.com/public-search", params, prefix="search", key=key
            )
            evs = data.get("events", []) or []
            for e in evs:
                events.setdefault(e.get("slug"), e)
            pag = data.get("pagination") or {}
            if not pag.get("hasMore") or page >= 10:
                break
            page += 1
        per_query.append((q, len(events) - n_before, len(events)))
    return events, per_query


def extract_token(question, title):
    s = question.strip()
    m = TOKEN_DOLLAR_RE.search(s)
    if m:
        return m.group(1).upper()
    m = TOKEN_WILL_BE_RE.search(s)
    if m:
        return re.sub(r"[^A-Za-z0-9]", "", m.group(1)).upper()
    m = TOKEN_LIST_VERB_RE.search(s)
    if m:
        cand = m.group(1)
        cand = re.split(r"\s+by\s+|\s+in\s+|\s+before\s+|\?", cand, flags=re.I)[0]
        cand = re.sub(r"[^A-Za-z0-9]", "", cand)
        if cand:
            return cand.upper()
    m = TOKEN_BEFORE_LISTED_RE.search(s)
    if m:
        cand = re.sub(r"\$", "", m.group(1))
        cand = re.sub(r"[^A-Za-z0-9]", "", cand)
        if cand and cand.lower() not in VENUES:
            return cand.upper()
    m = TOKEN_DOLLAR_RE.search(title)
    if m:
        return m.group(1).upper()
    return None


def venue_of(text):
    vs = sorted({v.lower() for v in VENUE_RE.findall(text or "")})
    if not vs:
        return None
    return "+".join(vs)


def build_universe(events):
    rows = []
    seen_cid = set()
    for slug, e in sorted(events.items()):
        if not e.get("closed"):
            continue
        title = e.get("title", "") or ""
        blob = title.lower()
        if any(x in blob for x in EXCLUDE_SUBSTR):
            continue
        is_next_slug = slug.startswith("next-coin") or slug.startswith("first-coin")
        if not (
            (LIST_RE.search(title) and VENUE_RE.search(title))
            or (is_next_slug and VENUE_RE.search(title))
        ):
            continue
        for m in e.get("markets", []):
            if not m.get("closed"):
                continue
            q = m.get("question", "") or ""
            qb = q.lower()
            if any(x in qb for x in EXCLUDE_SUBSTR):
                continue
            if NONE_TOKEN_RE.search(q):
                continue
            if not (LIST_RE.search(q) and (VENUE_RE.search(q) or VENUE_RE.search(title))):
                continue
            cid = m.get("conditionId")
            if not cid or cid in seen_cid:
                continue
            end = parse_dt(m.get("endDate"))
            if end is None:
                continue
            token = extract_token(q, title)
            venue = venue_of(q if VENUE_RE.search(q) else title)
            if not token or not venue:
                continue
            outcomes = m.get("outcomes") or []
            prices = m.get("outcomePrices") or []
            yes_pay = None
            try:
                if isinstance(prices, str):
                    prices = json.loads(prices)
                if isinstance(outcomes, str):
                    outcomes = json.loads(outcomes)
                for i, o in enumerate(outcomes):
                    if str(o).lower() == "yes":
                        yes_pay = float(prices[i])
                        break
                if yes_pay is None and len(prices) == 2:
                    yes_pay = float(prices[0])
            except Exception:
                yes_pay = None
            start = parse_dt(m.get("startDate")) or parse_dt(m.get("createdAt"))
            closed = parse_dt(m.get("closedTime"))
            is_next = slug.startswith("next-coin") or slug.startswith("first-coin")
            cluster = slug if is_next else f"{token}|{venue}"
            rows.append(
                {
                    "event_slug": slug,
                    "event_title": title,
                    "market_slug": m.get("slug", ""),
                    "condition_id": cid,
                    "question": q,
                    "venue": venue,
                    "token": token,
                    "cluster": cluster,
                    "multi_event": bool(is_next),
                    "end_date": end,
                    "start_date": start,
                    "closed_time": closed,
                    "yes_payoff": yes_pay,
                    "volume": m.get("volumeNum") or m.get("volume") or 0.0,
                }
            )
            seen_cid.add(cid)
    rows.sort(key=lambda r: (r["end_date"], r["event_slug"], r["market_slug"]))
    return rows


# ---------------------------------------------------------------- trades
def get_last_trade(cid, start_ts, end_ts):
    key = f"{cid}|{start_ts}|{end_ts}"
    cpath = _cache_path("trades", key)
    data = None
    if cpath.exists():
        data = json.loads(cpath.read_text())
    else:
        collected = []
        offset = 0
        while offset < 10000:
            params = {
                "market": cid,
                "limit": 500,
                "offset": offset,
                "start": start_ts,
                "end": end_ts,
            }
            r = SESSION.get("https://data-api.polymarket.com/trades", params=params, timeout=45)
            r.raise_for_status()
            chunk = r.json()
            if not isinstance(chunk, list) or not chunk:
                break
            collected.extend(chunk)
            if len(chunk) < 500:
                break
            offset += 500
        data = collected
        cpath.write_text(json.dumps(data, sort_keys=True))
    best = None
    for i, t in enumerate(data):
        ts = t.get("timestamp")
        if ts is None:
            continue
        if not (start_ts <= ts <= end_ts):
            continue
        if best is None or ts > best[0] or (ts == best[0] and i > best[1]):
            best = (ts, i, t)
    if best is None:
        return None
    t = best[2]
    try:
        price = float(t.get("price"))
    except (TypeError, ValueError):
        return None
    outcome = str(t.get("outcome", ""))
    yes_price = 1.0 - price if outcome.lower() == "no" else price
    return {
        "trade_ts": best[0],
        "trade_price": price,
        "trade_outcome": outcome,
        "yes_price": min(1.0, max(0.0, yes_price)),
        "trade_size": t.get("size"),
    }


def price_rows(rows, days_before):
    out = []
    for r in rows:
        entry = r["end_date"] - dt.timedelta(days=days_before)
        start = entry - dt.timedelta(days=2)
        tr = get_last_trade(r["condition_id"], unix(start), unix(entry))
        rr = dict(r)
        rr["entry_time"] = entry
        rr["entry_window_start"] = start
        rr["trade"] = tr
        out.append(rr)
    return out


# ---------------------------------------------------------------- model
def fit_lambda(rows, entry_time):
    hist = []
    for r in rows:
        ct = r["closed_time"]
        st = r["start_date"]
        if ct is None or st is None or r["yes_payoff"] is None:
            continue
        if ct >= entry_time:
            continue
        exp_end = min(ct, r["end_date"])
        days = (exp_end - st).total_seconds() / 86400.0
        if days <= 0:
            days = 1.0 / 24.0
        hist.append((1 if r["yes_payoff"] > 0.5 else 0, days))
    n = len(hist)
    n_yes = sum(y for y, _ in hist)
    exposure = sum(d for _, d in hist)
    ok = n >= MIN_HIST_MARKETS and n_yes >= MIN_HIST_YES and exposure >= MIN_HIST_EXPOSURE_DAYS
    lam = (n_yes / exposure) if ok and exposure > 0 else None
    return lam, n, n_yes, exposure, ok


def p_model_for(lam, days):
    if lam is None:
        return None
    return 1.0 - math.exp(-lam * days)


def simulate(rows, days_before):
    priced = price_rows(rows, days_before)
    lam_info = {}
    for r in priced:
        lam, n, ny, expo, ok = fit_lambda(rows, r["entry_time"])
        r["lam"] = lam
        r["hist_n"] = n
        r["hist_yes"] = ny
        r["hist_exposure"] = expo
        r["hist_ok"] = ok
        r["p_model"] = p_model_for(lam, days_before)
        r["side"] = None
        r["entry_price"] = None
        r["fee"] = None
        r["payoff"] = None
        r["net"] = None
        r["edge"] = None
        tr = r["trade"]
        r["priced"] = tr is not None and r["p_model"] is not None and r["yes_payoff"] is not None
        if not r["priced"]:
            continue
        p = r["p_model"]
        px = tr["yes_price"]
        ask = px + HALF_SPREAD
        bid = px - HALF_SPREAD
        thr = BASE_EDGE + p * (1 - p) * FEE_RATE
        edge_yes = p - ask - thr
        no_px = 1.0 - bid
        edge_no = bid - p - thr
        side = None
        entry_price = None
        edge = None
        if edge_yes >= 0 and (edge_no < 0 or edge_yes >= edge_no) and 0 < ask < 1:
            side, entry_price, edge = "YES", ask, edge_yes
        elif edge_no >= 0 and 0 < no_px < 1:
            side, entry_price, edge = "NO", no_px, edge_no
        r["side"] = side
        r["edge"] = edge if side else None
        if side is None:
            continue
        r["entry_price"] = entry_price
        r["fee"] = FEE_RATE * entry_price * (1 - entry_price)
        r["payoff"] = r["yes_payoff"] if side == "YES" else 1.0 - r["yes_payoff"]
        r["net"] = r["payoff"] - entry_price - r["fee"]
    return priced


def cluster_results(priced):
    by = {}
    for r in priced:
        if not r.get("side"):
            continue
        by.setdefault(r["cluster"], []).append(r)
    out = {}
    for c, rs in by.items():
        out[c] = {
            "n_trades": len(rs),
            "net_mean": float(np.mean([x["net"] for x in rs])),
            "net_median": float(np.median([x["net"] for x in rs])),
            "staked": float(sum(x["entry_price"] for x in rs)),
            "pnl": float(sum(x["net"] for x in rs)),
        }
    return out


def bootstrap_ci(cluster_nets, n_boot=BOOT_N, seed=SEED):
    if not cluster_nets:
        return None
    arr = np.asarray(cluster_nets, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    means = arr[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(priced, label):
    priced_ok = [r for r in priced if r.get("priced")]
    traded = [r for r in priced if r.get("side")]
    clusters_priced = {r["cluster"] for r in priced_ok}
    cr = cluster_results(priced)
    cnets = [v["net_mean"] for v in cr.values()]
    n_yes = sum(1 for r in traded if r["side"] == "YES")
    n_no = sum(1 for r in traded if r["side"] == "NO")
    hit = sum(1 for r in traded if r["net"] > 0)
    total_pnl = float(sum(r["net"] for r in traded))
    total_staked = float(sum(r["entry_price"] for r in traded))
    return {
        "label": label,
        "n_markets": len(priced),
        "n_priced": len(priced_ok),
        "n_priced_clusters": len(clusters_priced),
        "n_traded": len(traded),
        "n_traded_clusters": len(cnets),
        "n_yes": n_yes,
        "n_no": n_no,
        "hit": hit,
        "hit_rate": (hit / len(traded)) if traded else None,
        "median_net": float(np.median(cnets)) if cnets else None,
        "mean_net": float(np.mean(cnets)) if cnets else None,
        "total_pnl": total_pnl,
        "total_staked": total_staked,
        "per_dollar": (total_pnl / total_staked) if total_staked else None,
        "ci": bootstrap_ci(cnets),
        "cluster_results": cr,
    }


def model_scores(priced):
    rows = [
        r
        for r in priced
        if r.get("priced") and r.get("p_model") is not None and r["yes_payoff"] is not None
    ]
    if not rows:
        return None
    eps = 1e-6
    y = np.array([1.0 if r["yes_payoff"] > 0.5 else 0.0 for r in rows])
    pm = np.clip(np.array([r["p_model"] for r in rows]), eps, 1 - eps)
    mk = np.clip(np.array([r["trade"]["yes_price"] for r in rows]), eps, 1 - eps)
    brier_m = float(np.mean((pm - y) ** 2))
    brier_k = float(np.mean((mk - y) ** 2))
    ll_m = float(np.mean(-(y * np.log(pm) + (1 - y) * np.log(1 - pm))))
    ll_k = float(np.mean(-(y * np.log(mk) + (1 - y) * np.log(1 - mk))))
    better = int(np.sum((pm - y) ** 2 < (mk - y) ** 2))
    worse = int(np.sum((pm - y) ** 2 > (mk - y) ** 2))
    ties = len(rows) - better - worse
    return {
        "n": len(rows),
        "brier_model": brier_m,
        "brier_market": brier_k,
        "ll_model": ll_m,
        "ll_market": ll_k,
        "better": better,
        "worse": worse,
        "ties": ties,
        "mean_abs_diff": float(np.mean(np.abs(pm - mk))),
        "n_yes": int(y.sum()),
    }


def sign_test_p(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


# ---------------------------------------------------------------- output
def write_csv(priced_main, priced_sens):
    path = OUT / "markets.csv"
    cols = [
        "entry_mode", "event_slug", "event_title", "market_slug", "condition_id", "question",
        "venue", "token", "cluster", "multi_event", "end_date", "start_date", "closed_time",
        "yes_payoff", "entry_time", "trade_ts", "trade_outcome", "trade_price", "trade_price_yes",
        "p_model", "side", "entry_price", "fee", "payoff", "net", "edge",
        "hist_n", "hist_yes", "hist_exposure_days", "hist_ok", "priced",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for mode, rows in (("primary_7d", priced_main), ("sensitivity_3d", priced_sens)):
            for r in rows:
                tr = r.get("trade") or {}
                w.writerow(
                    [
                        mode,
                        r["event_slug"], r["event_title"], r["market_slug"], r["condition_id"],
                        r["question"], r["venue"], r["token"], r["cluster"], int(r["multi_event"]),
                        r["end_date"].isoformat(), r["start_date"].isoformat() if r["start_date"] else "",
                        r["closed_time"].isoformat() if r["closed_time"] else "",
                        f"{r['yes_payoff']:.10f}" if r["yes_payoff"] is not None else "",
                        r["entry_time"].isoformat(),
                        tr.get("trade_ts", ""), tr.get("trade_outcome", ""),
                        f"{tr.get('trade_price'):.10f}" if tr else "",
                        f"{tr.get('yes_price'):.10f}" if tr else "",
                        f"{r['p_model']:.10f}" if r.get("p_model") is not None else "",
                        r.get("side") or "",
                        f"{r['entry_price']:.10f}" if r.get("entry_price") is not None else "",
                        f"{r['fee']:.10f}" if r.get("fee") is not None else "",
                        f"{r['payoff']:.10f}" if r.get("payoff") is not None else "",
                        f"{r['net']:.10f}" if r.get("net") is not None else "",
                        f"{r['edge']:.10f}" if r.get("edge") is not None else "",
                        r["hist_n"], r["hist_yes"], f"{r['hist_exposure']:.4f}",
                        int(r["hist_ok"]), int(r.get("priced", False)),
                    ]
                )
    return path


def fmt(x, nd=6):
    return "n/a" if x is None else f"{x:+.{nd}f}"


def main():
    events, per_query = enumerate_events()
    rows = build_universe(events)
    print("=" * 78)
    print("quant-009 historical executable-price backtest (data-api fills + walk-forward base rate)")
    print(f"access date {ACCESS_DATE} | queries {len(QUERIES)} | unique Gamma events {len(events)}")
    print("=" * 78)
    print("\n[1] Enumeration")
    print(f"  candidate events: {len({r['event_slug'] for r in rows})}  markets (deduped by conditionId): {len(rows)}")
    by_venue = {}
    for r in rows:
        by_venue.setdefault(r["venue"], []).append(r)
    venue_keys = list(VENUES) + sorted(k for k in by_venue if "+" in k and k not in VENUES)
    for v in venue_keys:
        rs = by_venue.get(v, [])
        print(f"    {v:20s} events={len({x['event_slug'] for x in rs}):2d} markets={len(rs):2d}")
    if rows:
        print(f"  date span (endDate): {rows[0]['end_date'].date()} .. {rows[-1]['end_date'].date()}")
        n_clusters = len({r["cluster"] for r in rows})
        print(f"  independent clusters (token+venue; next/first-coin event = 1): {n_clusters}")
    print("  queries (delta unique events, cumulative):")
    for q, d, c in per_query:
        print(f"    {q!r:38s} +{d:2d} -> {c:2d}")

    print("\n[2] Walk-forward base rate and pricing")
    priced_main = simulate(rows, 7)
    priced_sens = simulate(rows, 3)
    n_clusters = len({r["cluster"] for r in rows})
    fit_ok = [r for r in priced_main if r.get("hist_ok")]
    print(f"  markets with valid walk-forward lambda: {len(fit_ok)}/{len(rows)}")
    skipped = [r for r in rows if not any(x["condition_id"] == r["condition_id"] and x.get("hist_ok") for x in priced_main)]
    print(f"  skipped for <{MIN_HIST_MARKETS} resolved markets / <{MIN_HIST_YES} Yes / <{MIN_HIST_EXPOSURE_DAYS:.0f}d exposure: {len(skipped)}")
    if fit_ok:
        lams = [r["lam"] for r in fit_ok]
        print(f"  lambda/day: min={min(lams):.8f} median={float(np.median(lams)):.8f} max={max(lams):.8f}")
    for r in priced_main:
        if r.get("priced") and r.get("trade"):
            print(
                f"    {r['end_date'].date()} {r['venue']:18s} {r['token']:12s} "
                f"px={r['trade']['yes_price']:.4f} p={r['p_model']:.4f} "
                f"n_hist={r['hist_n']:2d} side={r['side'] or '-':3s} net={fmt(r['net'])}"
            )

    n_no_lambda = sum(1 for r in priced_main if r.get("p_model") is None)
    n_no_fill = sum(1 for r in priced_main if r.get("p_model") is not None and r.get("trade") is None)
    n_no_payoff = sum(1 for r in priced_main if r.get("yes_payoff") is None)
    nofill = [r for r in priced_main if r.get("p_model") is not None and r.get("trade") is None]
    n_closed_before = sum(
        1 for r in nofill if r.get("closed_time") is not None and r["closed_time"] <= r["entry_time"]
    )
    print(f"  unpriced breakdown: no walk-forward lambda={n_no_lambda}, no fill in 2d window={n_no_fill} "
          f"(of which already resolved before entry={n_closed_before}), no resolution price={n_no_payoff}")

    s_main = summarize(priced_main, "primary_7d")
    s_sens = summarize(priced_sens, "sensitivity_3d")

    print("\n[3] Results (per independent cluster/event, equal 1 share per triggered market)")
    for s in (s_main, s_sens):
        print(f"  -- {s['label']}")
        print(f"     markets priced={s['n_priced']}/{s['n_markets']}  clusters priced={s['n_priced_clusters']}")
        print(f"     triggered trades={s['n_traded']}  clusters/events={s['n_traded_clusters']}  YES={s['n_yes']} NO={s['n_no']}")
        print(f"     median net/share={fmt(s['median_net'])}  mean net/share={fmt(s['mean_net'])}")
        ci = s["ci"]
        print(f"     cluster bootstrap 95% CI of mean: [{fmt(ci[0])}, {fmt(ci[1])}]" if ci else "     CI n/a")
        print(f"     hit rate={s['hit']}/{s['n_traded']} = " + (f"{s['hit_rate']:.3f}" if s['hit_rate'] is not None else "n/a"))
        print(f"     total net={s['total_pnl']:+.6f} on staked={s['total_staked']:.6f} -> per $ staked={fmt(s['per_dollar'])}")

    print("\n[4] Walk-forward model vs market price on priced markets")
    for s, pr in (("primary_7d", priced_main), ("sensitivity_3d", priced_sens)):
        ms = model_scores(pr)
        if not ms:
            print(f"  -- {s}: no priced markets")
            continue
        print(f"  -- {s}: n={ms['n']} market-YES={ms['n_yes']}")
        print(f"     Brier  model={ms['brier_model']:.6f}  market={ms['brier_market']:.6f}  diff={ms['brier_model']-ms['brier_market']:+.6f}")
        print(f"     LogLoss model={ms['ll_model']:.6f}  market={ms['ll_market']:.6f}  diff={ms['ll_model']-ms['ll_market']:+.6f}")
        print(f"     model lower Brier on {ms['better']}, market lower on {ms['worse']}, ties {ms['ties']}, sign p={sign_test_p(ms['better'], ms['better']+ms['worse']):.4f}")
        print(f"     mean |p_model - market|={ms['mean_abs_diff']:.6f}")

    print("\n[5] Triggered cluster detail (primary_7d)")
    cr = s_main["cluster_results"]
    for c in sorted(cr):
        v = cr[c]
        print(f"    {c:42s} trades={v['n_trades']:2d} mean_net={v['net_mean']:+.6f} median={v['net_median']:+.6f} pnl={v['pnl']:+.6f}")

    print("\n[6] Frozen fail criterion / verdict")
    n_ind = s_main["n_priced_clusters"]
    if n_clusters < 30 or n_ind < 30:
        verdict = "INSUFFICIENT"
        reason = f"independent clusters {n_clusters} and priced clusters {n_ind}; need both >= 30"
    elif s_main["median_net"] is None or s_main["median_net"] <= 0:
        verdict = "FAIL"
        reason = f"priced clusters {n_ind} >= 30 and median cluster net {fmt(s_main['median_net'])} <= 0"
    else:
        verdict = "PASS"
        reason = f"priced clusters {n_ind} >= 30 and median cluster net {fmt(s_main['median_net'])} > 0"
    print(f"    independent clusters        = {n_clusters} (need >=30)")
    print(f"    priced independent clusters = {n_ind} (need >=30)")
    print(f"    median cluster net/share   = {fmt(s_main['median_net'])} (FAIL if <=0)")
    print(f"    triggered clusters         = {s_main['n_traded_clusters']}")
    print(f"    VERDICT = {verdict} ({reason})")

    path = write_csv(priced_main, priced_sens)
    print(f"\n[7] wrote {path.relative_to(BASE.parent.parent.parent.parent)} ({sum(1 for _ in open(path))-1} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
