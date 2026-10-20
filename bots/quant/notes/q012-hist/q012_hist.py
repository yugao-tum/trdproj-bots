#!/usr/bin/env python3
"""quant-012 historical executable-price backtest.

Data sources (all free, keyless):
  * Gamma public-search / events  (closed earthquake count ladders)
  * data-api /trades              (real fills on closed markets)
  * USGS FDSN event query CSV     (base-rate counts)

Pre-declared choices (fixed before looking at results):
  * Decision time = event window start. No count has elapsed at decision time.
  * Base-rate model = empirical distribution of counts in consecutive windows of
    the SAME length as the event window, ending immediately before window start,
    built from USGS data before window start only (2000-01-01 onwards).
    Add 0.5 pseudo-count to every bracket, then normalise (Laplace smoothing).
  * Executable YES price = last data-api fill in [start-24h, start], mapped to
    YES (Yes fill price, or 1-No fill price). Sensitivity = first fill after start.
  * Trade rule = entry's 1 cent safety margin: buy NO iff
    market_yes - model_yes > 0.01.
  * Execution: taker buy NO at (1-market_yes) + 0.01 half-spread (1 cent),
    fee = 0.05 * p_no * (1-p_no) per share (GUIDE section 8, weather = 5%).
    Hold to resolution.
  * Realised gross per share = NO payoff (1/0) - execution price.
  * Log loss compares the base-rate model with the normalised market YES
    distribution across brackets, per event. Sign test is two-sided binomial.
  * Strict independent results: same (window_start, window_end) across the 5.5
    and 6.5 series count once. Loose = one per event.
"""

import bisect
import csv
import json
import math
import os
import re
import statistics
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

DATA = Path(__file__).resolve().parent
CACHE = DATA / "_cache"
GAMMA_EVENTS = CACHE / "gamma_events"
TRADES = CACHE / "trades"
SEARCH = CACHE / "search"
USGS = CACHE / "usgs"
for d in (GAMMA_EVENTS, TRADES, SEARCH, USGS):
    d.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
ET = ZoneInfo("America/New_York")
FEE_RATE = 0.05
HALF_SPREAD = 0.01
EDGE_MIN = 0.01
PSEUDO = 0.5


def cached_json(url, params, path, tries=8):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    last = None
    for attempt in range(tries):
        try:
            r = SESSION.get(url, params=params, timeout=90)
            if r.status_code == 200:
                data = r.json()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                time.sleep(0.12)
                return data
            last = f"HTTP {r.status_code}"
            if r.status_code == 429:
                time.sleep(2.0 * (attempt + 1))
            else:
                time.sleep(1.0)
        except Exception as exc:  # network hiccup
            last = repr(exc)
            time.sleep(1.5)
    raise RuntimeError(f"fetch failed {url} {params}: {last}")


def cached_text(url, params, path, tries=8):
    if path.exists():
        return path.read_text(encoding="utf-8")
    last = None
    for attempt in range(tries):
        try:
            r = SESSION.get(url, params=params, timeout=180)
            if r.status_code == 200:
                path.write_text(r.text, encoding="utf-8")
                return r.text
            last = f"HTTP {r.status_code}"
            time.sleep(2.0 * (attempt + 1))
        except Exception as exc:
            last = repr(exc)
            time.sleep(1.5)
    raise RuntimeError(f"fetch failed {url} {params}: {last}")


def collect_events():
    """All closed count-ladder events matching the entry's slug patterns."""
    seen = {}
    for q in ("earthquake", "magnitude", "earthquakes"):
        path = SEARCH / f"{q}.json"
        if path.exists():
            events = json.loads(path.read_text(encoding="utf-8"))
        else:
            events = []
            page = 1
            while True:
                d = cached_json(
                    "https://gamma-api.polymarket.com/public-search",
                    {"q": q, "limit_per_type": 50, "events_status": "closed", "page": page},
                    SEARCH / f"{q}_{page}.json",
                )
                events.extend(d.get("events", []))
                if not d.get("pagination", {}).get("hasMore"):
                    break
                page += 1
            with open(path, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False)
        for e in events:
            slug = e.get("slug", "")
            if slug.startswith("how-many") and "earthquake" in slug and e.get("closed"):
                seen[slug] = e
    events = []
    for slug in sorted(seen):
        d = cached_json(
            "https://gamma-api.polymarket.com/events",
            {"slug": slug},
            GAMMA_EVENTS / f"{slug}.json",
        )
        ev = d[0] if isinstance(d, list) and d else (d if isinstance(d, dict) else None)
        if ev and ev.get("closed"):
            events.append(ev)
    return events


def parse_window(ev):
    desc = ev.get("description", "")
    m = re.search(
        r"between\s+([A-Z][a-z]+ \d{1,2}, \d{4}, \d{1,2}:\d{2} [AP]M ET)"
        r"\s*(?:,)?\s*and\s+([A-Z][a-z]+ \d{1,2}, \d{4}, \d{1,2}:\d{2} [AP]M ET)",
        desc,
        re.I,
    )
    if not m:
        return None
    def conv(s):
        return datetime.strptime(s.upper(), "%B %d, %Y, %I:%M %p ET").replace(tzinfo=ET)
    start = conv(m.group(1))
    end = conv(m.group(2)) + timedelta(minutes=1)  # 23:59 ET -> next day 00:00 ET
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def parse_bracket(label):
    s = str(label).strip().lower().replace("–", "-")
    if s.startswith("≤") or s.startswith("<=") or s.endswith(" or fewer"):
        n = int(re.findall(r"\d+", s)[0])
        return 0, n
    if s.startswith("<"):
        n = int(re.findall(r"\d+", s)[0])
        return 0, n - 1
    if s.startswith(">") or s.startswith("more than"):
        n = int(re.findall(r"\d+", s)[0])
        return n + 1, None
    if s.endswith("+"):
        n = int(re.findall(r"\d+", s)[0])
        return n, None
    if re.fullmatch(r"\d+", s):
        n = int(s)
        return n, n
    nums = [int(x) for x in re.findall(r"\d+", s)]
    if len(nums) == 2:
        return nums[0], nums[1]
    raise ValueError(f"unparsed bracket {label!r}")


def event_magnitude(ev):
    text = ev.get("slug", "") + " " + ev.get("title", "")
    if re.search(r"5pt5|5\.5", text):
        return 5.5
    if re.search(r"6pt5|6-5|6\.5", text):
        return 6.5
    if re.search(r"7pt0|7\.0", text):
        return 7.0
    m = re.search(r"magnitude of (\d+(?:\.\d+)?)", ev.get("description", ""))
    return float(m.group(1)) if m else None


def load_usgs(threshold):
    # filename uses minmagnitude = threshold - 0.1 and filters mag >= threshold
    qthr = round(threshold - 0.1, 1)
    path = USGS / f"usgs_{qthr}.csv"
    if not path.exists():
        cached_text(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            {
                "format": "csv",
                "starttime": "2000-01-01",
                "endtime": "2026-10-20",
                "minmagnitude": qthr,
                "orderby": "time-asc",
            },
            path,
        )
    times = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                mag = float(row["mag"])
            except (TypeError, ValueError):
                continue
            if mag < threshold:
                continue
            ts = datetime.fromisoformat(row["time"].replace("Z", "+00:00")).timestamp()
            times.append(ts)
    times.sort()
    return times


def empirical_probs(times, start_ts, length_s, brackets):
    lo_year = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()
    counts = []
    end = start_ts
    while end - length_s >= lo_year:
        ws = end - length_s
        counts.append(bisect.bisect_left(times, end) - bisect.bisect_left(times, ws))
        end = ws
    counts.sort()
    n = len(counts)
    if n == 0:
        return None, 0
    max_k = max(b[1] if b[1] is not None else max(counts) for b in brackets)
    freq = {k: counts.count(k) / n for k in range(max_k + 1)}
    raw = []
    for lo, hi in brackets:
        if hi is None:
            p = sum(v for k, v in freq.items() if k >= lo)
        else:
            p = sum(freq.get(k, 0.0) for k in range(lo, hi + 1))
        raw.append(p * n + PSEUDO)
    tot = sum(raw)
    return [x / tot for x in raw], n


def fetch_trades(cid, start_ts):
    path = TRADES / f"{cid}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    cutoff = start_ts - 24 * 3600
    out = []
    offset = 0
    for _ in range(30):  # safety cap: 15k fills
        d = cached_json(
            "https://data-api.polymarket.com/trades",
            {"market": cid, "limit": 500, "offset": offset},
            TRADES / f"{cid}.__page{offset}.json",
        )
        if not d:
            break
        for t in d:
            out.append(
                {
                    "timestamp": int(t["timestamp"]),
                    "price": float(t["price"]),
                    "outcome": t["outcome"],
                    "side": t["side"],
                    "size": float(t.get("size", 0)),
                }
            )
        if len(d) < 500 or min(x["timestamp"] for x in d) < cutoff:
            break
        offset += 500
    # fold page cache into one file, remove page files
    out.sort(key=lambda x: x["timestamp"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    for p in TRADES.glob(f"{cid}.__page*.json"):
        p.unlink()
    return out


def yes_price(trade):
    return trade["price"] if trade["outcome"].lower() == "yes" else 1.0 - trade["price"]


def pick_prices(trades, start_ts):
    pre = [t for t in trades if start_ts - 86400 <= t["timestamp"] <= start_ts]
    post = [t for t in trades if t["timestamp"] > start_ts]
    p_pre = yes_price(pre[-1]) if pre else None
    p_post = yes_price(post[0]) if post else None
    t_pre = pre[-1]["timestamp"] if pre else None
    t_post = post[0]["timestamp"] if post else None
    return p_pre, p_post, t_pre, t_post


def binom_sign_test(pos, neg):
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def main():
    print("=" * 78)
    print("quant-012 historical executable-price backtest")
    print("decision time = window start; base rate uses only earlier USGS data")
    print("=" * 78)

    events = collect_events()
    print(f"\n[1] Closed earthquake count-ladder events found on Gamma: {len(events)}")
    series = {}
    for ev in events:
        mag = event_magnitude(ev)
        w = parse_window(ev)
        key = f"M{mag}+" if mag else "?"
        series.setdefault(key, []).append((ev, w))
    for key in sorted(series):
        rows = series[key]
        ok = [w for _, w in rows if w]
        span = (
            f"{min(w[0] for w in ok).date()} .. {max(w[1] for w in ok).date()}"
            if ok else "未取到"
        )
        nb = sorted({len(ev.get("markets", [])) for ev, _ in rows})
        print(f"  {key:6s} events={len(rows):3d}  buckets/event={nb}  span={span}")

    usgs = {m: load_usgs(m) for m in (5.5, 6.5, 7.0)}

    event_rows = []
    bucket_rows = []
    skipped = []

    for ev in events:
        mag = event_magnitude(ev)
        w = parse_window(ev)
        if not mag or not w:
            skipped.append((ev.get("slug"), "window/magnitude unparsed"))
            continue
        start_ts, end_ex = w[0].timestamp(), w[1].timestamp()
        length = end_ex - start_ts

        markets = []
        for m in ev.get("markets", []):
            try:
                lo, hi = parse_bracket(m.get("groupItemTitle"))
            except Exception:
                skipped.append((ev.get("slug"), f"bracket {m.get('groupItemTitle')!r}"))
                continue
            op = json.loads(m.get("outcomePrices") or "[]")
            resolved_yes = bool(op and float(op[0]) > 0.5)
            markets.append(
                {
                    "label": m.get("groupItemTitle"),
                    "lo": lo,
                    "hi": hi,
                    "cid": m.get("conditionId"),
                    "resolved_yes": resolved_yes,
                }
            )
        if not markets or not any(x["resolved_yes"] for x in markets):
            skipped.append((ev.get("slug"), "no resolved winner"))
            continue
        markets.sort(key=lambda x: x["lo"])
        brackets = [(x["lo"], x["hi"]) for x in markets]
        full_coverage = (
            brackets[0][0] == 0
            and brackets[-1][1] is None
            and all(brackets[i][1] is not None and brackets[i][1] + 1 == brackets[i + 1][0]
                    for i in range(len(brackets) - 1))
        )
        probs, n_hist = empirical_probs(usgs[mag], start_ts, length, brackets)
        if probs is None:
            skipped.append((ev.get("slug"), "no history for base rate"))
            continue

        won = next(x for x in markets if x["resolved_yes"])
        count = sum(1 for t in usgs[mag] if start_ts <= t < end_ex)
        if won["lo"] <= count and (won["hi"] is None or count <= won["hi"]):
            match = "MATCH"
        else:
            match = "MISMATCH"

        for mk, p in zip(markets, probs):
            trades = fetch_trades(mk["cid"], start_ts)
            p_pre, p_post, t_pre, t_post = pick_prices(trades, start_ts)
            mk["p_pre"] = p_pre
            mk["t_pre"] = t_pre
            mk["p_post"] = p_post
            mk["model"] = p
            mk["n_trades"] = len(trades)
            edge = (p_pre - p) if p_pre is not None else None
            traded = edge is not None and edge > EDGE_MIN
            gross = net = fee = no_price = None
            if traded:
                no_price = min(0.9999, (1.0 - p_pre) + HALF_SPREAD)
                fee = FEE_RATE * no_price * (1.0 - no_price)
                payoff = 0.0 if mk["resolved_yes"] else 1.0
                gross = payoff - no_price
                net = gross - fee
            bucket_rows.append(
                {
                    "event_slug": ev["slug"],
                    "series": f"M{mag}+",
                    "bucket": mk["label"],
                    "lo": mk["lo"],
                    "hi": "" if mk["hi"] is None else mk["hi"],
                    "resolved_yes": int(mk["resolved_yes"]),
                    "market_yes_pre": "" if p_pre is None else f"{p_pre:.6f}",
                    "market_yes_first_after": "" if p_post is None else f"{p_post:.6f}",
                    "pre_trade_utc": "" if t_pre is None else datetime.fromtimestamp(t_pre, timezone.utc).isoformat(),
                    "pre_trade_age_hours": "" if t_pre is None else f"{(start_ts - t_pre)/3600:.2f}",
                    "model_yes": f"{p:.6f}",
                    "edge_pre": "" if edge is None else f"{edge:.6f}",
                    "traded": int(traded),
                    "n_trades": mk["n_trades"],
                    "no_exec_price": "" if no_price is None else f"{no_price:.6f}",
                    "taker_fee_per_share": "" if fee is None else f"{fee:.6f}",
                    "gross_per_share": "" if gross is None else f"{gross:.6f}",
                    "net_per_share": "" if net is None else f"{net:.6f}",
                    "strict_group": f"{w[0].date()}_{w[1].date()}",
                }
            )

        priced = [x for x in markets if x["p_pre"] is not None]
        model_ll = market_ll = None
        if len(markets) > 1 and len(priced) == len(markets):
            raw = [max(1e-9, x["p_pre"]) for x in markets]
            s = sum(raw)
            mp = [x / s for x in raw]
            model_p = probs[markets.index(won)]
            market_p = mp[markets.index(won)]
            model_ll = -math.log(max(model_p, 1e-12))
            market_ll = -math.log(max(market_p, 1e-12))
        traded = [x for x in markets if x.get("p_pre") is not None and (x["p_pre"] - x["model"]) > EDGE_MIN]
        event_rows.append(
            {
                "event_slug": ev["slug"],
                "series": f"M{mag}+",
                "window_start_utc": w[0].isoformat(),
                "window_end_excl_utc": w[1].isoformat(),
                "window_days": f"{length / 86400:.4f}",
                "n_hist_windows": n_hist,
                "usgs_count": count,
                "resolved_bucket": won["label"],
                "usgs_match": match,
                "n_buckets": len(markets),
                "n_priced_pre": len(priced),
                "n_traded": len(traded),
                "bracket_coverage": "full" if full_coverage else "partial",
                "model_logloss": "" if model_ll is None else f"{model_ll:.6f}",
                "market_logloss": "" if market_ll is None else f"{market_ll:.6f}",
                "strict_group": f"{w[0].date()}_{w[1].date()}",
            }
        )

    # ---------- results ----------
    print(f"\n[2] Backtest sample: {len(event_rows)} events with a resolved bracket")
    if skipped:
        print(f"    skipped: {len(skipped)}")
        for slug, why in skipped:
            print(f"      - {slug}: {why}")

    priced_events = [r for r in event_rows if r["n_priced_pre"] > 0]
    all_priced = [r for r in event_rows if r["n_priced_pre"] == r["n_buckets"]]
    traded_buckets = [b for b in bucket_rows if b["traded"] == 1]
    strict_groups = {r["strict_group"] for r in event_rows}
    strict_priced = {r["strict_group"] for r in priced_events}
    loose = len(event_rows)
    print(f"    events with at least one pre-window fill: {len(priced_events)}")
    print(f"    events with every bracket priced pre-window: {len(all_priced)}")
    weekly_strict = {r["strict_group"] for r in priced_events if float(r["window_days"]) < 10}
    partial = [r for r in event_rows if r["bracket_coverage"] == "partial"]
    traded_events = {b["event_slug"] for b in bucket_rows if b["traded"] == 1}
    strict_traded = {b["strict_group"] for b in bucket_rows if b["traded"] == 1}
    print(f"    independent results: loose={loose}, strict={len(strict_groups)} "
          f"(strict with prices={len(strict_priced)}, weekly-only={len(weekly_strict)}, "
          f"strict with trades={len(strict_traded)})")
    print(f"    events with non-exhaustive bracket sets: {len(partial)}")
    print(f"    traded NO buckets: {len(traded_buckets)}")

    matches = [r for r in event_rows if r["usgs_match"] == "MATCH"]
    print(f"    USGS own-count vs resolved bracket: {len(matches)}/{len(event_rows)} "
          f"MATCH ({len(matches)/len(event_rows):.1%})")
    for ser in sorted({r["series"] for r in event_rows}):
        rows = [r for r in event_rows if r["series"] == ser]
        ok = sum(1 for r in rows if r["usgs_match"] == "MATCH")
        print(f"      {ser:6s} {ok}/{len(rows)} MATCH")

    if traded_buckets:
        gross = [float(b["gross_per_share"]) for b in traded_buckets]
        net = [float(b["net_per_share"]) for b in traded_buckets]
        staked = [float(b["no_exec_price"]) for b in traded_buckets]
        wins = [1 for b in traded_buckets if b["resolved_yes"] == 0]
        print("\n[3] Realised results of filled NO shares (1 share per bucket)")
        print(f"    median gross/share = {statistics.median(gross):+.4f}")
        print(f"    median net/share   = {statistics.median(net):+.4f}")
        print(f"    mean gross/share   = {statistics.mean(gross):+.4f}")
        print(f"    mean net/share     = {statistics.mean(net):+.4f}")
        print(f"    hit rate (NO won)  = {len(wins)}/{len(traded_buckets)} = "
              f"{len(wins)/len(traded_buckets):.1%}")
        print(f"    total net P&L      = {sum(net):+.4f} on {sum(staked):.4f} staked "
              f"= {sum(net)/sum(staked):+.2%} per $ staked")
        ages = [float(b["pre_trade_age_hours"]) for b in traded_buckets
                if b["pre_trade_age_hours"] != ""]
        if ages:
            print(f"    pre-window fill age: median {statistics.median(ages):.2f}h, "
                  f"max {max(ages):.2f}h before window start")
    else:
        gross, net, staked = [], [], []
        print("\n[3] No bucket passed the entry's 1-cent edge threshold.")

    ll_rows = [r for r in event_rows if r["model_logloss"] and r["market_logloss"]]
    model_better = sum(1 for r in ll_rows if float(r["model_logloss"]) < float(r["market_logloss"]))
    market_better = sum(1 for r in ll_rows if float(r["model_logloss"]) > float(r["market_logloss"]))
    print("\n[4] Multi-class log loss, base-rate model vs market (paired per event)")
    print(f"    events compared = {len(ll_rows)}")
    if ll_rows:
        mll = statistics.mean(float(r["model_logloss"]) for r in ll_rows)
        kll = statistics.mean(float(r["market_logloss"]) for r in ll_rows)
        print(f"    mean model log loss  = {mll:.6f}")
        print(f"    mean market log loss = {kll:.6f}")
        diffs = [float(r["market_logloss"]) - float(r["model_logloss"]) for r in ll_rows]
        print(f"    median paired (market - model) log loss = {statistics.median(diffs):+.6f}")
        print(f"    aggregate model log loss = "
              f"{sum(float(r['model_logloss']) for r in ll_rows)/len(ll_rows):.6f}")
        print(f"    model better on {model_better} events, market better on {market_better}")
        print(f"    two-sided sign test p = {binom_sign_test(model_better, market_better):.4f}")

        print("\n[4b] Log-loss robustness subsets")
        for name, subset in (
            ("all paired", ll_rows),
            ("USGS MATCH only", [r for r in ll_rows if r["usgs_match"] == "MATCH"]),
            ("full bracket coverage", [r for r in ll_rows if r["bracket_coverage"] == "full"]),
            ("MATCH + M6.5", [r for r in ll_rows if r["usgs_match"] == "MATCH" and r["series"] == "M6.5+"]),
            ("MATCH + M5.5", [r for r in ll_rows if r["usgs_match"] == "MATCH" and r["series"] == "M5.5+"]),
        ):
            if not subset:
                continue
            mo = statistics.mean(float(r["model_logloss"]) for r in subset)
            ma = statistics.mean(float(r["market_logloss"]) for r in subset)
            mb = sum(1 for r in subset if float(r["model_logloss"]) < float(r["market_logloss"]))
            kb = sum(1 for r in subset if float(r["model_logloss"]) > float(r["market_logloss"]))
            print(f"    {name:23s} n={len(subset):2d} model={mo:.4f} market={ma:.4f} "
                  f"model_better={mb} market_better={kb}")

    # sensitivity: first fill after window start instead of last before
    sens = []
    sens_buckets = []
    for b in bucket_rows:
        if not b["market_yes_first_after"]:
            continue
        p = float(b["market_yes_first_after"])
        mp = float(b["model_yes"])
        if p - mp > EDGE_MIN:
            no_price = min(0.9999, (1 - p) + HALF_SPREAD)
            fee = FEE_RATE * no_price * (1 - no_price)
            payoff = 0.0 if b["resolved_yes"] == "1" else 1.0
            sens_buckets.append((payoff - no_price, payoff - no_price - fee, no_price))
    print("\n[5] Sensitivity: first fill AFTER window start (not the primary rule)")
    if sens_buckets:
        print(f"    traded buckets = {len(sens_buckets)}")
        print(f"    median gross/share = {statistics.median(x[0] for x in sens_buckets):+.4f}")
        print(f"    median net/share   = {statistics.median(x[1] for x in sens_buckets):+.4f}")
        print(f"    total net P&L      = {sum(x[1] for x in sens_buckets):+.4f} on "
              f"{sum(x[2] for x in sens_buckets):.4f} staked")
    else:
        print("    no bucket passed the threshold with post-start prices")

    # ---------- verdict ----------
    print("\n[6] Frozen fail criteria")
    med_gross = statistics.median(gross) if gross else None
    model_ll_mean = (
        statistics.mean(float(r["model_logloss"]) for r in ll_rows) if ll_rows else None
    )
    market_ll_mean = (
        statistics.mean(float(r["market_logloss"]) for r in ll_rows) if ll_rows else None
    )
    print(f"    (1) median realised gross/share = "
          f"{'NA' if med_gross is None else f'{med_gross:+.4f}'} (FAIL if <= 0)")
    if model_ll_mean is not None:
        print(f"    (2) model vs market log loss = {model_ll_mean:.6f} vs "
              f"{market_ll_mean:.6f} (FAIL if model worse)")
    else:
        print("    (2) model vs market log loss = 未取到 (no paired events)")
    fail_1 = med_gross is not None and med_gross <= 0
    fail_2 = (
        model_ll_mean is not None and market_ll_mean is not None
        and model_ll_mean > market_ll_mean
    )
    strict_n = len(strict_priced)
    if strict_n < 30:
        verdict = f"INSUFFICIENT ({strict_n} strict independent results < 30)"
    elif fail_1 or fail_2:
        verdict = "FAIL"
    else:
        verdict = "PASS"
    print(f"    strict independent results = {strict_n}")
    print(f"    VERDICT = {verdict}")

    # ---------- write tables ----------
    def write_csv(path, rows, fields):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})

    bfields = [
        "event_slug", "series", "bucket", "lo", "hi", "resolved_yes",
        "market_yes_pre", "market_yes_first_after", "pre_trade_utc",
        "pre_trade_age_hours", "model_yes", "edge_pre",
        "traded", "n_trades", "no_exec_price", "taker_fee_per_share",
        "gross_per_share", "net_per_share", "strict_group",
    ]
    efields = [
        "event_slug", "series", "window_start_utc", "window_end_excl_utc",
        "window_days", "n_hist_windows", "usgs_count", "resolved_bucket",
        "usgs_match", "n_buckets", "n_priced_pre", "n_traded",
        "bracket_coverage", "model_logloss", "market_logloss", "strict_group",
    ]
    write_csv(DATA / "buckets.csv", bucket_rows, bfields)
    write_csv(DATA / "events.csv", event_rows, efields)

    print(f"\n[7] wrote {DATA / 'buckets.csv'} ({len(bucket_rows)} rows)")
    print(f"    wrote {DATA / 'events.csv'} ({len(event_rows)} rows)")


if __name__ == "__main__":
    main()
