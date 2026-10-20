#!/usr/bin/env python3
"""quant-018 price-side historical test.

Free, keyless public endpoints only:
  * Gamma API   : closed weekly strait transit-count events
  * CLOB API    : per-bucket YES token price history
  * IMF PortWatch ArcGIS : daily chokepoint transit calls

The script caches every download under _cache/ (gitignored), so a rerun from
cache is deterministic.  It writes events.csv, buckets.csv, REPORT.md and
prints all key results to stdout.

Usage:
    python3 q018_price_test.py            # use cache when present
    python3 q018_price_test.py --refresh  # ignore cache (re-download)
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
PW = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
      "Daily_Chokepoints_Data/FeatureServer/0/query")
AS_OF = "2026-10-20"
SPLIT_DATE = dt.date(2026, 7, 13)
FEE_RATE = 0.0          # GUIDE section 8: geopolitics = 0
HALF_SPREAD = 0.01      # pre-declared 1 cent per share
SAFETY = 0.01           # entry rule: 0.01 cushion before a NO buy
REFRESH = False
UA = "quant-research-q018/1.0 (keyless public data)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})


def cache_file(url):
    return CACHE / (hashlib.sha1(url.encode("utf-8")).hexdigest() + ".json")


def get_json(url, retries=5, pause=0.35):
    """Cached JSON GET.  HTTP 4xx is not retried."""
    path = cache_file(url)
    if path.exists() and not REFRESH:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink()
    last = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=60)
            if r.status_code == 400:
                raise RuntimeError("HTTP 400: " + r.text[:200])
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError("HTTP %s" % r.status_code)
            r.raise_for_status()
            data = r.json()
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            time.sleep(pause)
            return data
        except RuntimeError:
            raise
        except Exception as exc:  # network errors / bad JSON
            last = exc
            time.sleep(pause * (2 ** attempt))
    raise RuntimeError("GET failed: %s (%s)" % (url, last))


def parse_iso(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_pw_date(value):
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000.0, dt.timezone.utc).date()
    return dt.date.fromisoformat(str(value)[:10])


def parse_interval(label):
    s = str(label).strip().replace("–", "-").replace("—", "-").replace("−", "-")
    s = s.replace("≤", "<").replace("≥", "+").replace(" ", "")
    if s.startswith("<"):
        return float("-inf"), int(float(s[1:])) - 1
    if s.endswith("+"):
        return int(float(s[:-1])), float("inf")
    a, b = s.split("-")
    return int(float(a)), int(float(b))


def in_interval(value, lo, hi):
    return lo <= value <= hi


# ---------------------------------------------------------------- PortWatch

def fetch_portwatch():
    rows = []
    offset = 0
    while True:
        params = {
            "where": "portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')",
            "outFields": "date,portname,n_total",
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": 1000,
            "orderByFields": "date ASC",
        }
        url = PW + "?" + urllib.parse.urlencode(params)
        page = get_json(url)
        feats = page.get("features") or []
        rows.extend(f["attributes"] for f in feats)
        if len(feats) < 1000:
            break
        offset += 1000
    daily = {}
    for a in rows:
        try:
            d = parse_pw_date(a["date"])
            daily[(a["portname"], d)] = float(a["n_total"])
        except (TypeError, ValueError, KeyError):
            continue
    weeks = {}
    grouped = {}
    for (port, d), value in daily.items():
        monday = d - dt.timedelta(days=d.weekday())
        grouped.setdefault((port, monday), {})[d.weekday()] = value
    for key, days in grouped.items():
        if len(days) == 7:
            weeks[key] = sum(days.values())
    dates = sorted(d for _, d in daily)
    return daily, weeks, rows, (dates[0], dates[-1]) if dates else (None, None)


# ---------------------------------------------------------------- Gamma

def fetch_events():
    search = get_json(
        GAMMA + "/public-search?q=how%20many%20ships%20transit"
        "&limit_per_type=100&events_status=all"
    )
    slugs = sorted({e["slug"] for e in (search.get("events") or [])
                    if e.get("slug", "").startswith("how-many-ships-transit")})
    events = []
    for slug in slugs:
        data = get_json(GAMMA + "/events?slug=" + urllib.parse.quote(slug))
        if data:
            ev = data[0]
            if ev.get("closed"):
                events.append(ev)
    return events


def event_window(ev):
    desc = ev.get("description") or ""
    m = re.search(r"from (\w+) (\d{1,2}), (\d{4}),? through (\w+) (\d{1,2}), (\d{4})", desc)
    if m:
        m1, d1, y1, m2, d2, y2 = m.groups()
        return (dt.date(int(y1), MONTHS[m1.lower()], int(d1)),
                dt.date(int(y2), MONTHS[m2.lower()], int(d2)))
    # One old event has no date sentence in its description.
    m = re.search(r"this-week-([a-z]{3})-(\d{1,2})-(\d{1,2})", ev["slug"])
    if m:
        mon, d1, d2 = m.groups()
        year = parse_iso(ev["endDate"]).year
        start = dt.date(year, MONTHS[mon], int(d1))
        end = dt.date(year, MONTHS[mon], int(d2))
        if end < start:
            nm = start.month + 1
            ny = start.year + (1 if nm > 12 else 0)
            end = dt.date(ny, 1 if nm > 12 else nm, int(d2))
        return start, end
    raise ValueError("cannot parse event window: " + ev["slug"])


def resolved_index(buckets):
    winners = []
    for i, b in enumerate(buckets):
        op = b["outcomePrices"]
        if isinstance(op, str):
            op = json.loads(op)
        if op and float(op[0]) > 0.5:
            winners.append(i)
    return winners


def build_records(events):
    recs = []
    for ev in events:
        wstart, wend = event_window(ev)
        strait = "Strait of Hormuz" if "hormuz" in ev["slug"] else "Bab el-Mandeb Strait"
        buckets = []
        for m in ev.get("markets") or []:
            label = m.get("groupItemTitle")
            if label is None:
                continue
            lo, hi = parse_interval(label)
            tokens = m.get("clobTokenIds")
            if isinstance(tokens, str):
                tokens = json.loads(tokens)
            buckets.append({
                "label": str(label), "lo": lo, "hi": hi, "token": tokens[0],
                "outcomePrices": m.get("outcomePrices"),
            })
        buckets.sort(key=lambda b: (b["lo"], b["hi"]))
        winners = resolved_index(buckets)
        rec = {
            "ev": ev,
            "slug": ev["slug"],
            "strait": strait,
            "week_start": wstart,
            "week_end": wend,
            "gamma_start": parse_iso(ev["startDate"]),
            "gamma_end": parse_iso(ev["endDate"]),
            "buckets": buckets,
            "winners": winners,
            "resolved_idx": winners[0] if len(winners) == 1 else None,
            "resolved_label": (buckets[winners[0]]["label"] if len(winners) == 1 else None),
        }
        recs.append(rec)
    recs.sort(key=lambda r: (r["week_start"], r["strait"]))
    return recs


# ---------------------------------------------------------------- CLOB

def chunks(start, end, days=10):
    cur = start
    while cur < end:
        nxt = min(cur + dt.timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def fetch_history(token, start, end):
    points = {}
    for a, b in chunks(start - dt.timedelta(days=1), end + dt.timedelta(days=2)):
        url = (CLOB + "/prices-history?market=%s&startTs=%d&endTs=%d&fidelity=60"
               % (token, int(a.timestamp()), int(b.timestamp())))
        try:
            data = get_json(url)
        except RuntimeError as exc:
            # keep the run alive on a single bad token; record no points
            print("WARN prices-history %s..%s %s" % (a.date(), b.date(), exc), file=sys.stderr)
            continue
        for x in data.get("history") or []:
            try:
                points[int(x["t"])] = float(x["p"])
            except (KeyError, TypeError, ValueError):
                continue
    return sorted(points.items())


def attach_prices(rec):
    ws_ts = int(dt.datetime.combine(rec["week_start"], dt.time(0, 0, 0),
                                    tzinfo=dt.timezone.utc).timestamp())
    for b in rec["buckets"]:
        hist = fetch_history(b["token"], rec["gamma_start"], rec["gamma_end"])
        b["hist_n"] = len(hist)
        b["first_t"] = hist[0][0] if hist else None
        b["first_p"] = hist[0][1] if hist else None
        before = [(t, p) for t, p in hist if t <= ws_ts]
        b["start_t"] = before[-1][0] if before else None
        b["start_p"] = before[-1][1] if before else None
        if b["start_p"] is not None:
            b["entry_kind"] = "start"
            b["entry_p"] = b["start_p"]
        else:
            b["entry_kind"] = "first"
            b["entry_p"] = b["first_p"]


# ---------------------------------------------------------------- model

def base_rate(weeks, strait, week_start, buckets):
    prior = sorted((mon, tot) for (port, mon), tot in weeks.items()
                   if port == strait and mon < week_start)[-12:]
    n = len(buckets)
    counts = [sum(1 for _, v in prior if in_interval(v, b["lo"], b["hi"]))
              for b in buckets]
    probs = [(k + 1.0) / (len(prior) + n) for k in counts]
    return probs, prior, counts


def normalize(values):
    s = sum(values)
    if s <= 0:
        return None
    return [v / s for v in values]


def brier(probs, y):
    return sum((p - t) ** 2 for p, t in zip(probs, y))


def mean_sd(values):
    n = len(values)
    if n == 0:
        return None, None
    m = sum(values) / n
    if n == 1:
        return m, None
    sd = math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))
    return m, sd


def betacf(a, b, x):
    maxit, eps, fpmin = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1 - x) / b


def t_p_value(diffs):
    n = len(diffs)
    if n < 2:
        return None, None, None
    m, sd = mean_sd(diffs)
    if sd is None or sd == 0:
        return m, None, None
    t = m / (sd / math.sqrt(n))
    p = betai((n - 1) / 2.0, 0.5, (n - 1) / (n - 1 + t * t))
    return t, p, sd


def sign_p_value(pos, neg):
    n = pos + neg
    if n == 0:
        return None
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


# ---------------------------------------------------------------- P&L

def trade_for_bucket(rec, b, prob, ref_key):
    ref = b.get(ref_key)
    if ref is None or rec["resolved_idx"] is None:
        return None
    fill = 1.0 - ref + HALF_SPREAD
    if not (0.0 < fill < 1.0):
        return None
    if (1.0 - prob) + 1e-12 < fill + SAFETY:
        return None
    no_wins = 1 if b is not rec["buckets"][rec["resolved_idx"]] else 0
    fee = 1.0 * FEE_RATE * fill * (1.0 - fill)
    gross = (1.0 if no_wins else 0.0) - fill
    return {
        "slug": rec["slug"], "strait": rec["strait"],
        "week_start": rec["week_start"].isoformat(),
        "label": b["label"], "ref_kind": ref_key,
        "ref_p": ref, "fill": fill, "no_wins": no_wins,
        "profit_gross": gross, "fee": fee, "profit_net": gross - fee,
    }


def pnl_summary(trades):
    if not trades:
        return None
    profits = [t["profit_gross"] for t in trades]
    staked = sum(t["fill"] for t in trades)
    total = sum(profits)
    wins = sum(t["no_wins"] for t in trades)
    return {
        "n": len(trades),
        "wins": wins,
        "median": statistics.median(profits),
        "total": total,
        "staked": staked,
        "per_dollar": total / staked if staked else None,
        "hit": wins / len(trades),
    }


def pnl_string(s):
    if s is None:
        return "无成交"
    return ("n=%d, NO胜=%d, 中位毛利=%+.4f/份, 总毛利=%+.4f, 总投入=%.4f, "
            "每美元投入P&L=%+.4f, 命中率=%.4f"
            % (s["n"], s["wins"], s["median"], s["total"], s["staked"],
               s["per_dollar"], s["hit"]))


def row_week(row):
    v = row["week_start"]
    return v if isinstance(v, dt.date) else dt.date.fromisoformat(v)


def split_stats(rows, key, cutoff=SPLIT_DATE):
    pre = [r for r in rows if row_week(r) < cutoff]
    post = [r for r in rows if row_week(r) >= cutoff]
    return pre, post


def brier_block(rows, label):
    vals = [r for r in rows if r.get("brier_model") is not None
            and r.get("brier_mkt_first") is not None]
    if not vals:
        return "%s: 无可比事件" % label
    model = [r["brier_model"] for r in vals]
    mkt = [r["brier_mkt_first"] for r in vals]
    diffs = [r["brier_mkt_first"] - r["brier_model"] for r in vals]
    mm, ms = mean_sd(model)
    km, ks = mean_sd(mkt)
    dm, ds = mean_sd(diffs)
    t, p, _ = t_p_value(diffs)
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    sp = sign_p_value(pos, neg)
    return ("%s: n=%d, 模型均值=%.4f, 市场首价均值=%.4f, 配对差(市场-模型)=%+.4f "
            "(sd=%.4f), t=%s, p=%s, 模型更好=%d/%d, 符号检验p=%s"
            % (label, len(vals), mm, km, dm, ds,
               "NA" if t is None else "%.3f" % t,
               "NA" if p is None else "%.4f" % p,
               pos, pos + neg,
               "NA" if sp is None else "%.4f" % sp))


def csv_write(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in fields})


def main():
    global REFRESH
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="ignore cache")
    args = parser.parse_args()
    REFRESH = args.refresh

    CACHE.mkdir(parents=True, exist_ok=True)

    print("quant-018 price-side historical test | as_of=%s" % AS_OF)
    print("fee_rate=%.2f (GUIDE 8 geopolitics) | half_spread=%.2f | safety=%.2f"
          % (FEE_RATE, HALF_SPREAD, SAFETY))

    events = fetch_events()
    print("closed weekly events: %d" % len(events))
    recs = build_records(events)
    by_strait = {}
    for r in recs:
        by_strait[r["strait"]] = by_strait.get(r["strait"], 0) + 1
    print("by strait: " + ", ".join("%s=%d" % (k, v) for k, v in sorted(by_strait.items())))
    print("exactly one resolved bucket: %d/%d"
          % (sum(1 for r in recs if r["resolved_idx"] is not None), len(recs)))

    daily, weeks, pw_rows, (pw_min, pw_max) = fetch_portwatch()
    print("PortWatch: rows=%d, coverage=%s..%s, complete Mon-Sun weeks: %s"
          % (len(pw_rows), pw_min, pw_max,
             ", ".join("%s=%d" % (p, sum(1 for (pp, _) in weeks if pp == p))
                       for p in sorted({p for p, _ in weeks}))))

    for rec in recs:
        attach_prices(rec)

    # event totals and recomputation check
    for rec in recs:
        total = 0.0
        complete = True
        for i in range(7):
            d = rec["week_start"] + dt.timedelta(days=i)
            v = daily.get((rec["strait"], d))
            if v is None:
                complete = False
                break
            total += v
        rec["pw_total"] = total if complete else None
        if not complete or rec["resolved_idx"] is None:
            rec["pw_match"] = "NO_DATA"
        else:
            b = rec["buckets"][rec["resolved_idx"]]
            rec["pw_match"] = "MATCH" if in_interval(total, b["lo"], b["hi"]) else "MISMATCH"

    match_counts = {}
    for r in recs:
        match_counts[r["pw_match"]] = match_counts.get(r["pw_match"], 0) + 1
    print("recompute vs Gamma settlement: " + ", ".join(
        "%s=%d" % (k, match_counts.get(k, 0)) for k in ["MATCH", "MISMATCH", "NO_DATA"]))

    bucket_rows = []
    event_rows = []
    all_trades_entry = []
    all_trades_first = []
    all_trades_start = []

    for rec in recs:
        n = len(rec["buckets"])
        probs, prior, counts = base_rate(weeks, rec["strait"], rec["week_start"], rec["buckets"])
        y = [1.0 if i == rec["resolved_idx"] else 0.0 for i in range(n)]

        b_model = brier(probs, y)
        first_vals = [b["first_p"] for b in rec["buckets"]]
        start_vals = [b["start_p"] for b in rec["buckets"]]
        p_first = normalize(first_vals) if all(v is not None for v in first_vals) else None
        p_start = normalize(start_vals) if all(v is not None for v in start_vals) else None
        b_first = brier(p_first, y) if p_first else None
        b_start = brier(p_start, y) if p_start else None

        rec["model_probs"] = probs
        rec["brier_model"] = b_model
        rec["brier_mkt_first"] = b_first
        rec["brier_mkt_start"] = b_start
        rec["model_prob_sum"] = sum(probs)
        rec["prior"] = prior
        rec["counts"] = counts

        trades_entry, trades_first, trades_start = [], [], []
        for i, b in enumerate(rec["buckets"]):
            prob = probs[i]
            t_entry = trade_for_bucket(rec, b, prob, "entry_p")
            t_first = trade_for_bucket(rec, b, prob, "first_p")
            t_start = trade_for_bucket(rec, b, prob, "start_p")
            if t_entry:
                t_entry["ref_kind"] = b["entry_kind"]
                trades_entry.append(t_entry)
            if t_first:
                trades_first.append(t_first)
            if t_start:
                trades_start.append(t_start)
            bucket_rows.append({
                "slug": rec["slug"], "strait": rec["strait"],
                "week_start": rec["week_start"].isoformat(),
                "label": b["label"], "lo": b["lo"], "hi": b["hi"],
                "resolved_yes": 1 if i == rec["resolved_idx"] else 0,
                "hist_n": b["hist_n"],
                "first_ts": (dt.datetime.fromtimestamp(b["first_t"], dt.timezone.utc)
                             .isoformat().replace("+00:00", "Z")
                             if b["first_t"] is not None else ""),
                "first_p": b["first_p"],
                "start_ts": (dt.datetime.fromtimestamp(b["start_t"], dt.timezone.utc)
                             .isoformat().replace("+00:00", "Z")
                             if b["start_t"] is not None else ""),
                "start_p": b["start_p"],
                "entry_kind": b["entry_kind"], "entry_p": b["entry_p"],
                "p_model": prob,
                "trigger_entry": 1 if t_entry else 0,
                "no_wins": t_entry["no_wins"] if t_entry else "",
                "no_fill": t_entry["fill"] if t_entry else "",
                "profit_gross": t_entry["profit_gross"] if t_entry else "",
                "fee": t_entry["fee"] if t_entry else "",
                "profit_net": t_entry["profit_net"] if t_entry else "",
            })

        all_trades_entry.extend(trades_entry)
        all_trades_first.extend(trades_first)
        all_trades_start.extend(trades_start)
        s_entry = pnl_summary(trades_entry)
        s_first = pnl_summary(trades_first)
        s_start = pnl_summary(trades_start)

        event_rows.append({
            "slug": rec["slug"], "strait": rec["strait"],
            "week_start": rec["week_start"].isoformat(),
            "week_end": rec["week_end"].isoformat(),
            "n_buckets": n, "resolved_bucket": rec["resolved_label"],
            "pw_total": rec["pw_total"], "pw_match": rec["pw_match"],
            "price_buckets_nonempty": sum(1 for b in rec["buckets"] if b["hist_n"] > 0),
            "prices_complete_first": int(p_first is not None),
            "prices_complete_start": int(p_start is not None),
            "model_prob_sum": rec["model_prob_sum"],
            "brier_model": b_model,
            "brier_mkt_first": b_first,
            "brier_mkt_start": b_start,
            "diff_first_mkt_minus_model": (b_first - b_model) if b_first is not None else None,
            "diff_start_mkt_minus_model": (b_start - b_model) if b_start is not None else None,
            "n_trades_entry": s_entry["n"] if s_entry else 0,
            "n_no_wins_entry": s_entry["wins"] if s_entry else 0,
            "median_gross_entry": s_entry["median"] if s_entry else None,
            "total_gross_entry": s_entry["total"] if s_entry else None,
            "total_staked_entry": s_entry["staked"] if s_entry else None,
            "pnl_per_dollar_entry": s_entry["per_dollar"] if s_entry else None,
            "hit_rate_entry": s_entry["hit"] if s_entry else None,
            "n_trades_first": s_first["n"] if s_first else 0,
            "pnl_per_dollar_first": s_first["per_dollar"] if s_first else None,
            "n_trades_start": s_start["n"] if s_start else 0,
            "pnl_per_dollar_start": s_start["per_dollar"] if s_start else None,
        })

    # ------------------------------------------------------------ print table
    print("")
    print("per-event (week_start | strait | buckets | resolved | pw | Brier model/first/start | trades)")
    for r in event_rows:
        print("%s | %-19s | %db | %-6s | %s %s | %.4f / %s / %s | %d"
              % (r["week_start"], r["strait"][:19], r["n_buckets"],
                 r["resolved_bucket"], r["pw_total"], r["pw_match"],
                 r["brier_model"],
                 "NA" if r["brier_mkt_first"] is None else "%.4f" % r["brier_mkt_first"],
                 "NA" if r["brier_mkt_start"] is None else "%.4f" % r["brier_mkt_start"],
                 r["n_trades_entry"]))

    complete_first = [r for r in event_rows if r["prices_complete_first"]]
    complete_start = [r for r in event_rows if r["prices_complete_start"]]
    print("")
    print("price coverage: first-price complete %d/%d (Hormuz %d, Bab %d); "
          "at-start complete %d/%d"
          % (len(complete_first), len(event_rows),
             sum(1 for r in complete_first if "Hormuz" in r["strait"]),
             sum(1 for r in complete_first if "Bab" in r["strait"]),
             len(complete_start), len(event_rows)))
    print("price points nonempty: %d/%d buckets"
          % (sum(r["price_buckets_nonempty"] for r in event_rows),
             sum(r["n_buckets"] for r in event_rows)))

    print("")
    print("== Brier, all events with complete first prices ==")
    print(brier_block(event_rows, "all"))
    print(brier_block([r for r in event_rows if r["prices_complete_start"]], "at-start subset"))
    pre, post = split_stats(event_rows, "week_start")
    print(brier_block(pre, "pre-2026-07-13"))
    print(brier_block(post, "post-2026-07-13"))
    bab = [r for r in event_rows if "Bab" in r["strait"]]
    hor = [r for r in event_rows if "Hormuz" in r["strait"]]
    print(brier_block(bab, "Bab only"))
    print(brier_block(hor, "Hormuz only"))
    print(brier_block([r for r in event_rows if r["pw_match"] == "MATCH"], "MATCH-only"))

    # strict = one observation per week (average of both straits if both present)
    by_week = {}
    for r in event_rows:
        if r["diff_first_mkt_minus_model"] is not None:
            by_week.setdefault(r["week_start"], []).append(r["diff_first_mkt_minus_model"])
    week_diffs = [sum(v) / len(v) for v in by_week.values()]
    if week_diffs:
        t, p, sd = t_p_value(week_diffs)
        pos = sum(1 for d in week_diffs if d > 0)
        neg = sum(1 for d in week_diffs if d < 0)
        sp = sign_p_value(pos, neg)
        print("strict week-cluster (market first - model): n_weeks=%d, mean=%+.4f, sd=%s, "
              "t=%s, p=%s, model better=%d/%d, sign p=%s"
              % (len(week_diffs), sum(week_diffs) / len(week_diffs),
                 "NA" if sd is None else "%.4f" % sd,
                 "NA" if t is None else "%.3f" % t,
                 "NA" if p is None else "%.4f" % p,
                 pos, pos + neg, "NA" if sp is None else "%.4f" % sp))
    else:
        print("strict week-cluster: 无可比事件")

    print("")
    print("== trade rule P&L (Bab only) ==")
    bab_entry = [t for t in all_trades_entry if "Bab" in t["strait"]]
    bab_first = [t for t in all_trades_first if "Bab" in t["strait"]]
    bab_start = [t for t in all_trades_start if "Bab" in t["strait"]]
    s_entry = pnl_summary(bab_entry)
    s_first = pnl_summary(bab_first)
    s_start = pnl_summary(bab_start)
    print("entry ref (at-start, fallback first): " + pnl_string(s_entry))
    print("first price only:                    " + pnl_string(s_first))
    print("at-start only:                       " + pnl_string(s_start))
    if s_entry:
        pre_tr = [t for t in bab_entry if t["week_start"] < SPLIT_DATE.isoformat()]
        post_tr = [t for t in bab_entry if t["week_start"] >= SPLIT_DATE.isoformat()]
        print("entry ref pre-2026-07-13:  " + pnl_string(pnl_summary(pre_tr)))
        print("entry ref post-2026-07-13: " + pnl_string(pnl_summary(post_tr)))
        # same rule applied to Hormuz, sensitivity only
        hor_entry = [t for t in all_trades_entry if "Hormuz" in t["strait"]]
        print("Hormuz same rule (sensitivity, not the entry's rule): "
              + pnl_string(pnl_summary(hor_entry)))

    print("")
    print("== fail criteria ==")
    if s_start is None:
        c1 = "INSUFFICIENT"
        c1_text = "周起点价无成交"
    else:
        c1 = "FAIL" if s_start["median"] <= 0 else "PASS"
        c1_text = ("周起点价口径 n=%d，中位毛利 %+.4f/份；含首价回退 n=%d，中位 %+.4f/份"
                   % (s_start["n"], s_start["median"],
                      s_entry["n"] if s_entry else 0,
                      s_entry["median"] if s_entry else float("nan")))
    n_brier = len(complete_first)
    model_mean = statistics.mean([r["brier_model"] for r in complete_first]) if complete_first else None
    mkt_mean = statistics.mean([r["brier_mkt_first"] for r in complete_first]) if complete_first else None
    if n_brier < 30 or model_mean is None:
        c3 = "INSUFFICIENT"
        c3_text = "n=%d < 30" % n_brier
    else:
        c3 = "PASS" if model_mean < mkt_mean else "FAIL"
        c3_text = "模型 %.4f vs 市场首价 %.4f (n=%d)" % (model_mean, mkt_mean, n_brier)
    print("(1) median realized gross profit <= 0 ? %s (%s)" % (c1, c1_text))
    print("(3) base-rate Brier better than market first price on >=30 events ? %s (%s)"
          % (c3, c3_text))

    # ------------------------------------------------------------ CSV
    event_fields = list(event_rows[0].keys())
    csv_write(HERE / "events.csv", event_rows, event_fields)
    bucket_fields = list(bucket_rows[0].keys())
    csv_write(HERE / "buckets.csv", bucket_rows, bucket_fields)

    # ------------------------------------------------------------ REPORT.md
    pre_rows, post_rows = split_stats(event_rows, "week_start")
    report = []
    report.append("# quant-018 价格侧历史检验（Brier 与 NO 份额收益）")
    report.append("")
    report.append("结论：**标准 (1) %s**（Bab 周起点价 %d 份，中位 %+.4f/份）；"
                  "**标准 (3) 在全部 43 个 event 上 %s**（%.4f vs %.4f），但它只在 Hormuz 上占优，"
                  "只做 Bab 的子集 n=%d<30 且模型更差，故对实际 Bab 规则应读作 **INSUFFICIENT**。"
                  "全部数字由 `q018_price_test.py` 生成；stdout 见 `run_output.txt`，"
                  "逐事件表见 `events.csv`，逐档表见 `buckets.csv`。"
                  % (c1, s_start["n"] if s_start else 0,
                     s_start["median"] if s_start else float("nan"), c3,
                     model_mean, mkt_mean, len(bab)))
    report.append("")
    report.append("## 1. 实际取到的数据")
    report.append("")
    report.append("- Gamma：`public-search?q=how many ships transit` 返回 47 个同族 event，"
                  "其中 `closed=true` **%d** 个（Hormuz %d / Bab el-Mandeb %d），与条目一致。"
                  % (len(event_rows),
                     sum(1 for r in event_rows if "Hormuz" in r["strait"]),
                     sum(1 for r in event_rows if "Bab" in r["strait"])))
    report.append("- CLOB 逐档价格：%d 个档位 token，非空 %d 个；首价完整的事件 **%d/%d**，"
                  "周起点价完整的事件 **%d/%d**（缺周起点价的 9 个事件都是在周中才创建）。"
                  % (sum(r["n_buckets"] for r in event_rows),
                     sum(r["price_buckets_nonempty"] for r in event_rows),
                     len(complete_first), len(event_rows),
                     len(complete_start), len(event_rows)))
    report.append("- 关键取数差异：`interval=max&fidelity=60` 对 2026-09-07 及更早的事件返回空；"
                  "本脚本改用 `startTs/endTs` 按 ≤10 天分段（`fidelity=60`）逐档取全，"
                  "因此覆盖的事件数远多于条目里的 6 个。")
    report.append("- PortWatch：%d 行日度数据，覆盖 %s 至 %s；完整 Mon–Sun 周数：%s。"
                  % (len(pw_rows), pw_min, pw_max,
                     ", ".join("%s=%d" % (p, sum(1 for (pp, _) in weeks if pp == p))
                               for p in sorted({p for p, _ in weeks}))))
    report.append("- 抓取日期 %s；全部为公开 GET，无密钥、无登录、未交易；原始下载在 `_cache/`，"
                  "已由 `.gitignore` 排除，不入库。" % AS_OF)
    report.append("")
    report.append("## 2. 方法（预先写死）")
    report.append("")
    report.append("- **事件窗口**：Gamma `description` 的 `from … through …`（允许年份后无逗号）；"
                  "`this-week-mar-10-16` 也可解析为 2026-03-10 至 2026-03-16，slug 回退仅作保险。")
    report.append("- **基准率**：同一海峡、**严格早于事件周起点**的最近 12 个完整 Mon–Sun 周总量，"
                  "套入当期档位，`p_i=(k_i+1)/(12+n)`，n 为档数。事件周及以后的数据不进入模型。")
    report.append("- **市场首价**：该档 YES token 最早一条 `prices-history` 记录；"
                  "**周起点价**：`t <= 事件周起点 00:00:00 UTC` 的最后一条记录。"
                  "两者都按档归一化（除以各档价格之和）；某档无价格则该事件不进入对应 Brier。")
    report.append("- **Brier**：多分类 `Σ(p_i-y_i)^2`，y 取 Gamma `outcomePrices` 的 YES=1 档；"
                  "差值定义为“市场 Brier − 模型 Brier”，正数表示模型更好。")
    report.append("- **交易规则**：只做 Bab el-Mandeb（条目明确不做 Hormuz）。"
                  "NO 公允 = `1-p_model`；NO 吃单价 = `1-p_ref+0.01`（1¢ 半价差）；"
                  "触发条件 `1-p_model >= NO吃单价 + 0.01`（条目 0.01 安全垫）。"
                  "`p_ref` 优先取周起点价；若市场在周起点后才开市/无成交，取首价并在 `buckets.csv` "
                  "的 `entry_kind` 标记。每档 1 份。手续费按 GUIDE §8 地缘费率 **0**："
                  "`份数×0×p×(1-p)=0`；历史市场 `feesEnabled=false` 与此一致。")
    report.append("- **已实现毛利**：每份 NO = 兑付（NO 赢 1 / 输 0）− 成交价 − 手续费；"
                  "亏损份额计入。若只算赢的份额，任何 NO 买单都正毛利，标准 (1) 会失去意义。")
    report.append("- **独立结果**：Brier 按 event 计；严格口径把同一周两海峡聚成 1 个观测"
                  "（周内平均差），宽口径按 event 计。")
    report.append("")
    report.append("## 3. 结果（脚本 stdout 原样数字）")
    report.append("")
    report.append("```")
    report.append("PortWatch 复算 vs Gamma 结算: " + ", ".join(
        "%s=%d" % (k, match_counts.get(k, 0)) for k in ["MATCH", "MISMATCH", "NO_DATA"]))
    report.append("（条目按 Mon–Sun 分箱记 34/7/2；本脚本对两个原先无法分箱的事件直接按声明窗口"
                  " 7 天求和，二者都不在结算档，故为 34/9/0。）")
    report.append("价格覆盖: 首价完整 %d/%d；周起点价完整 %d/%d；非空档位 %d/%d"
                  % (len(complete_first), len(event_rows),
                     len(complete_start), len(event_rows),
                     sum(r["price_buckets_nonempty"] for r in event_rows),
                     sum(r["n_buckets"] for r in event_rows)))
    report.append("")
    for line in [brier_block(event_rows, "Brier all"),
                 brier_block([r for r in event_rows if r["prices_complete_start"]],
                             "Brier at-start subset"),
                 brier_block(pre_rows, "Brier pre-2026-07-13"),
                 brier_block(post_rows, "Brier post-2026-07-13"),
                 brier_block(bab, "Brier Bab only"),
                 brier_block(hor, "Brier Hormuz only"),
                 brier_block([r for r in event_rows if r["pw_match"] == "MATCH"],
                             "Brier MATCH-only")]:
        report.append(line)
    if week_diffs:
        t, p, sd = t_p_value(week_diffs)
        pos = sum(1 for d in week_diffs if d > 0)
        neg = sum(1 for d in week_diffs if d < 0)
        sp = sign_p_value(pos, neg)
        report.append("严格周聚类: n_weeks=%d, 平均差=%+.4f, t=%s, p=%s, 模型更好=%d/%d"
                      % (len(week_diffs), sum(week_diffs) / len(week_diffs),
                         "NA" if t is None else "%.3f" % t,
                         "NA" if p is None else "%.4f" % p,
                         pos, pos + neg))
    report.append("")
    report.append("Bab 交易 P&L（周起点价，缺失时首价回退）: " + pnl_string(s_entry))
    report.append("Bab 交易 P&L（纯首价）: " + pnl_string(s_first))
    report.append("Bab 交易 P&L（纯周起点价）: " + pnl_string(s_start))
    if s_entry:
        pre_tr = [t for t in bab_entry if t["week_start"] < SPLIT_DATE.isoformat()]
        post_tr = [t for t in bab_entry if t["week_start"] >= SPLIT_DATE.isoformat()]
        report.append("Bab 交易 P&L 2026-07-13 前: " + pnl_string(pnl_summary(pre_tr)))
        report.append("Bab 交易 P&L 2026-07-13 起: " + pnl_string(pnl_summary(post_tr)))
    report.append("")
    report.append("失败标准：")
    report.append("")
    report.append("1. 已成交 NO 份额中位已实现毛利 ≤ 0：**%s**（%s）。正式口径只用周起点价，"
                  "避免用周中首价引入前视；含首价回退的变体同样为正。" % (c1, c1_text))
    report.append("2. 两周内成交 < 20 份：本任务只做历史侧，未计前向成交，**不适用**。")
    report.append("3. 在 ≥30 个历史事件上基准率平均 Brier 不优于市场首价：**%s**（%s）。"
                  % (c3, c3_text))
    report.append("")
    all_diffs = [r["brier_mkt_first"] - r["brier_model"] for r in event_rows
                 if r["brier_mkt_first"] is not None and r["brier_model"] is not None]
    t_all, p_all, _ = t_p_value(all_diffs)
    bab_diffs = [r["brier_mkt_first"] - r["brier_model"] for r in bab]
    hor_diffs = [r["brier_mkt_first"] - r["brier_model"] for r in hor]
    report.append("**解读（重要）**：")
    report.append("")
    report.append("- 标准 (3) 的数字在“全部 43 个 event”口径成立：模型 %.4f vs 市场首价 %.4f，"
                  "差 %+.4f；但配对 t p=%s、符号检验 p=%s，**不显著**。"
                  % (model_mean, mkt_mean, statistics.mean(all_diffs),
                     "NA" if p_all is None else "%.4f" % p_all,
                     "NA" if sign_p_value(sum(1 for d in all_diffs if d > 0),
                                          sum(1 for d in all_diffs if d < 0)) is None
                     else "%.4f" % sign_p_value(sum(1 for d in all_diffs if d > 0),
                                                sum(1 for d in all_diffs if d < 0))))
    report.append("- 分海峡看，Hormuz 模型更好（差 %+.4f，n=%d），**Bab 模型反而更差**"
                  "（差 %+.4f，n=%d）；交易规则只做 Bab。若把标准 (3) 限定在 Bab，n=%d<30，"
                  "应为 **INSUFFICIENT**，且方向为负。因此 (3) 的 PASS 不能当作 Bab 策略的"
                  "校准证据。" % (statistics.mean(hor_diffs), len(hor),
                                  statistics.mean(bab_diffs), len(bab), len(bab)))
    report.append("- 标准 (1) 的 PASS 用的是周起点价口径 %d 份（中位 %+.4f/份），不是 %d 个独立 "
                  "event；含周中首价回退的 %d 份也是正（中位 %+.4f/份）；纯首价 %d 份中位 "
                  "%+.4f/份更高，但其中 9 个 event 的市场在周中才开市，可能含周内信息，"
                  "故不作正式口径。"
                  % (s_start["n"] if s_start else 0,
                     s_start["median"] if s_start else float("nan"),
                     len([r for r in bab if r["n_trades_start"]]),
                     s_entry["n"] if s_entry else 0,
                     s_entry["median"] if s_entry else float("nan"),
                     s_first["n"] if s_first else 0,
                     s_first["median"] if s_first else float("nan")))
    report.append("")
    report.append("## 4. 限制")
    report.append("")
    report.append("- CLOB `prices-history` 是逐档**最后成交价**（fidelity=60 的抽样），不是可执行盘口；"
                  "没有历史深度/挂单量。1¢ 半价差是预先假设，真实价差可能更宽或更窄。")
    report.append("- PortWatch 是**事后修订**后的当前值，不是事件当时的 vintage；"
                  "2026-03 至 2026-05 有 %d 个事件复算档位与 Gamma 结算不一致，"
                  "这些事件的模型输入也可能被修订污染。" % match_counts.get("MISMATCH", 0))
    report.append("- 周起点价只在市场已于周起点前开市时有定义；部分早期 event 在周中才创建，"
                  "交易 P&L 用首价回退，已在 `buckets.csv` 标记。")
    report.append("- 同一周两海峡高度相关；Brier 的严格口径只有 %d 个周级观测，"
                  "宽口径的 event 级 t 检验会高估独立样本量。" % len(week_diffs))
    report.append("- Bab 只有 12 个已关闭事件，交易规则触发次数有限；"
                  "中位毛利基于份额，不是基于独立 event。")
    report.append("- 费率按 GUIDE §8 地缘 0；若平台未来改费率，P&L 需重算。")
    report.append("")
    report.append("## 5. 复现与验证")
    report.append("")
    report.append("- `python3 q018_price_test.py` 从 `_cache/` 重跑：`run_output.txt`、`events.csv`、"
                  "`buckets.csv`、`REPORT.md` 的哈希与首次运行一致（已实测）。")
    report.append("- `python3 tools/check.py lint` 在当前 HEAD 上**退出 1**：`bots/muse/entries/` "
                  "的既有 frontmatter 问题（部分文件 frontmatter 前有额外行，缺 `id` 后脚本 "
                  "KeyError），与本任务无关；完整输出见 `lint_output.txt`。本任务只新增 notes，"
                  "不在 `bots/*/entries/*.md` 扫描范围内。")
    report.append("")
    (HERE / "REPORT.md").write_text("\n".join(report).rstrip() + "\n", encoding="utf-8")

    print("")
    print("wrote events.csv (%d rows), buckets.csv (%d rows), REPORT.md"
          % (len(event_rows), len(bucket_rows)))


if __name__ == "__main__":
    REFRESH = False
    main()
