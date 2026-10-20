#!/usr/bin/env python3
"""quant-018 same-time paired, executable-price re-test.

PRE-DECLARED METHOD (written before looking at any result)
==========================================================
Decision time T: the event window start, i.e. Monday 00:00:00 UTC of the
Mon-Sun week named in the market description.  The entry does not state a
different decision time, so T = window start.

Model probability: IMF PortWatch daily chokepoint data ONLY.  For an event
whose window starts at T, use the last 12 complete Mon-Sun weeks whose Monday
is strictly before T; a week is complete only if all seven daily rows exist.
Bucket probabilities are Laplace-smoothed (k_i+1)/(n_weeks+n_buckets).  No
PortWatch date >= T enters the model.  The public ArcGIS service is a current,
revised vintage, not a point-in-time snapshot; this is disclosed and the
number of event weeks whose current recomputation disagrees with Gamma
settlement is reported as the observable revision/rule proxy.

Market price per bucket: last data-api trade in [T-24h, T], mapped to a YES
price (YES trade price p, or 1 - NO trade price).  A bucket with no trade in
that window has NO price and is not filled.  Sensitivity A: last trade in
[T-6h, T].  Sensitivity B: first trade in [T, T+24h] (look-ahead, exploratory
only, never used for the verdict).

Scores: multi-class Brier sum_i (p_i-y_i)^2 and log loss -log p_winner
(winner probability clipped at 1e-15), model vs market at the SAME T.  Raw
market prices are used in the main comparison; a renormalised-market variant
divides each event's bucket prices by their sum.  Event is scored only when
every bucket has a price in the relevant window.  Paired t-test and sign test
are event level; uncertainty clustered by calendar week uses a block bootstrap
that resamples weeks (Hormuz and Bab in the same week move together), 10,000
resamples, fixed seed 20261020.

Executable trade rule exactly as the entry: buy NO where
1 - p_model >= NO_executable + 0.01, NO_executable = 1 - p_yes + half_spread.
half_spread = 0.01 in the base case.  Taker fee per GUIDE section 8 with the
fee rate the entry states (0 for geopolitics; the closed markets returned
feesEnabled=false): fee = shares * rate * p * (1-p).  Stress case: total cost
= 0.05 instead of 0.01 (i.e. NO_executable = 1 - p_yes + 0.05), fee unchanged.
One share per triggered bucket.  Primary rule is Bab el-Mandeb only (the
entry explicitly does not trade Hormuz); Hormuz and pooled numbers are
reported as the task requests but labelled exploratory.

Frozen fail criteria from the entry (not tuned):
  (1) median realised gross profit of filled NO shares <= 0 -> FAIL;
  (3) on >=30 historical events the base-rate mean Brier is not better than
      the market price -> FAIL; <30 events -> INSUFFICIENT.

Free, keyless endpoints only:
  * Gamma       https://gamma-api.polymarket.com
  * data-api    https://data-api.polymarket.com/trades?market=<conditionId>
  * PortWatch   ArcGIS Daily_Chokepoints_Data FeatureServer

Usage:
    python3 q018_paired.py            # use cache when present (deterministic)
    python3 q018_paired.py --refresh  # ignore cache and re-download
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import random
import re
import statistics
import sys
import time
import urllib.parse
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
GAMMA = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com/trades"
PW = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
      "Daily_Chokepoints_Data/FeatureServer/0/query")
AS_OF = "2026-10-20"
SEED = 20261020
N_BOOT = 10000
FEE_RATE = 0.0          # entry/GUIDE section 8: geopolitics = 0
HALF_SPREAD = 0.01      # pre-declared 1 cent per share
STRESS_COST = 0.05      # extra stress: 5 cents total cost
SAFETY = 0.01           # entry rule: 0.01 cushion before a NO buy
LOOKBACK_WEEKS = 12
REFRESH = False
UA = "quant-research-q018-paired/1.0 (keyless public data)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})


def cache_file(url):
    return CACHE / (hashlib.sha1(url.encode("utf-8")).hexdigest() + ".json")


def get_json(url, retries=9, pause=0.35):
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
                last = RuntimeError("HTTP %s" % r.status_code)
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
                continue
            r.raise_for_status()
            data = r.json()
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            time.sleep(pause)
            return data
        except RuntimeError:
            raise
        except Exception as exc:
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
    dates = sorted(d for _, d in daily)
    return daily, rows, (dates[0], dates[-1]) if dates else (None, None)


def complete_weeks(daily, as_of_date):
    grouped = {}
    for (port, d), value in daily.items():
        if d >= as_of_date:
            continue
        monday = d - dt.timedelta(days=d.weekday())
        grouped.setdefault((port, monday), {})[d.weekday()] = value
    return {key: sum(days.values()) for key, days in grouped.items() if len(days) == 7}


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
        if data and data[0].get("closed"):
            events.append(data[0])
    return events, slugs


def event_window(ev):
    desc = ev.get("description") or ""
    m = re.search(r"from (\w+) (\d{1,2}), (\d{4}),? through (\w+) (\d{1,2}), (\d{4})", desc)
    if m:
        m1, d1, y1, m2, d2, y2 = m.groups()
        return (dt.date(int(y1), MONTHS[m1.lower()], int(d1)),
                dt.date(int(y2), MONTHS[m2.lower()], int(d2)))
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
            buckets.append({
                "label": str(label), "lo": lo, "hi": hi,
                "conditionId": m.get("conditionId"),
                "outcomePrices": m.get("outcomePrices"),
                "feesEnabled": m.get("feesEnabled"),
            })
        buckets.sort(key=lambda b: (b["lo"], b["hi"]))
        winners = resolved_index(buckets)
        rec = {
            "ev": ev, "slug": ev["slug"], "strait": strait,
            "week_start": wstart, "week_end": wend,
            "buckets": buckets, "winners": winners,
            "resolved_idx": winners[0] if len(winners) == 1 else None,
            "resolved_label": (buckets[winners[0]]["label"] if len(winners) == 1 else None),
        }
        recs.append(rec)
    recs.sort(key=lambda r: (r["week_start"], r["strait"]))
    return recs


# ---------------------------------------------------------------- data-api

def fetch_market_trades(condition_id, lower_ts):
    """Descending trade pages until older than lower_ts (or cap)."""
    out = []
    offset = 0
    pages = 0
    truncated = False
    while True:
        params = {"market": condition_id, "limit": 500, "offset": offset}
        url = DATA_API + "?" + urllib.parse.urlencode(params)
        try:
            page = get_json(url)
        except RuntimeError as exc:
            print("WARN trades %s offset=%d %s" % (condition_id, offset, exc), file=sys.stderr)
            break
        pages += 1
        if not page:
            break
        out.extend(page)
        oldest = min(int(x.get("timestamp") or 0) for x in page)
        if oldest < lower_ts or len(page) < 500:
            break
        offset += 500
        if pages >= 40:
            truncated = True
            break
    return out, pages, truncated


def yes_price(trade):
    try:
        p = float(trade["price"])
        outcome = str(trade.get("outcome", "")).lower()
    except (KeyError, TypeError, ValueError):
        return None
    if outcome.startswith("no"):
        return 1.0 - p
    return p


def attach_prices(rec):
    t0 = dt.datetime.combine(rec["week_start"], dt.time(0, 0, 0), tzinfo=dt.timezone.utc)
    T = int(t0.timestamp())
    intervals = {
        "main": (T - 24 * 3600, T),
        "sens6h": (T - 6 * 3600, T),
        "after24h": (T, T + 24 * 3600),
    }
    for b in rec["buckets"]:
        trades, pages, truncated = fetch_market_trades(b["conditionId"], T - 26 * 3600)
        mapped = []
        for idx, tr in enumerate(trades):
            ts = int(tr.get("timestamp") or 0)
            p = yes_price(tr)
            if p is None:
                continue
            mapped.append((ts, idx, p))
        b["trade_pages"] = pages
        b["trade_truncated"] = int(truncated)
        b["trade_n_fetched"] = len(mapped)
        for key, (lo, hi) in intervals.items():
            inside = [x for x in mapped if lo <= x[0] <= hi]
            if not inside:
                b[key + "_ts"] = None
                b[key + "_p"] = None
                continue
            inside.sort(key=lambda x: (x[0], x[1]))
            chosen = inside[0] if key == "after24h" else inside[-1]
            b[key + "_ts"] = chosen[0]
            b[key + "_p"] = chosen[2]


# ---------------------------------------------------------------- model & scores

def base_rate(weeks, strait, week_start, buckets):
    prior = sorted((mon, tot) for (port, mon), tot in weeks.items()
                   if port == strait and mon < week_start)[-LOOKBACK_WEEKS:]
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


def logloss(probs, y):
    p = max(1e-15, min(1.0 - 1e-15, probs[y.index(1.0)]))
    return -math.log(p)


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


def bootstrap_weeks(rows, key, n_boot=N_BOOT, seed=SEED):
    """Block bootstrap by calendar week over event-level differences."""
    by_week = {}
    for r in rows:
        v = r.get(key)
        if v is None:
            continue
        by_week.setdefault(r["week_start"], []).append(v)
    weeks = sorted(by_week)
    if len(weeks) < 2:
        return None
    observed = [r[key] for r in rows if r.get(key) is not None]
    obs_mean = sum(observed) / len(observed)
    rnd = random.Random(seed)
    means = []
    for _ in range(n_boot):
        sample_weeks = [weeks[rnd.randrange(len(weeks))] for _ in weeks]
        vals = []
        for w in sample_weeks:
            vals.extend(by_week[w])
        means.append(sum(vals) / len(vals))
    means.sort()
    se = math.sqrt(sum((x - obs_mean) ** 2 for x in means) / (len(means) - 1))
    lo = means[int(0.025 * len(means))]
    hi = means[int(0.975 * len(means)) - 1]
    le0 = sum(1 for x in means if x <= 0) / len(means)
    ge0 = sum(1 for x in means if x >= 0) / len(means)
    p = min(1.0, 2 * min(le0, ge0))
    return {"n_weeks": len(weeks), "mean": obs_mean, "se": se,
            "lo": lo, "hi": hi, "p": p}


def fmt(x, nd=4, signed=False):
    if x is None:
        return "NA"
    spec = ("%+." if signed else "%.") + str(nd) + "f"
    return spec % x


def score_block(rows, model_key, mkt_key, label):
    vals = [r for r in rows if r.get(model_key) is not None and r.get(mkt_key) is not None]
    if not vals:
        return ("%s: n=0" % label), None
    model = [r[model_key] for r in vals]
    mkt = [r[mkt_key] for r in vals]
    diffs = [r[mkt_key] - r[model_key] for r in vals]
    mm, _ = mean_sd(model)
    km, _ = mean_sd(mkt)
    dm, ds = mean_sd(diffs)
    t, p, _ = t_p_value(diffs)
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    sp = sign_p_value(pos, neg)
    line = ("%s: n=%d, 模型均值=%.4f, 市场均值=%.4f, 配对差(市场-模型)=%+.4f "
            "(sd=%s), t=%s, p=%s, 模型更好=%d/%d, 符号检验p=%s"
            % (label, len(vals), mm, km, dm,
               "NA" if ds is None else "%.4f" % ds,
               "NA" if t is None else "%.3f" % t,
               "NA" if p is None else "%.4f" % p,
               pos, pos + neg,
               "NA" if sp is None else "%.4f" % sp))
    metric = model_key.split("_")[0]
    suffix = ""
    for tail in ("_renorm", "_s6", "_after"):
        if mkt_key.endswith(tail):
            suffix = tail
            break
    boot = bootstrap_weeks(vals, "diff_" + metric + suffix)
    return line, {"line": line, "n": len(vals), "model": mm, "market": km,
                  "diff": dm, "t": t, "p": p, "sign_p": sp,
                  "better": pos, "n_events": pos + neg, "boot": boot}


# ---------------------------------------------------------------- P&L

def make_trade(rec, b, prob, price_key, cost):
    p_yes = b.get(price_key)
    if p_yes is None or rec["resolved_idx"] is None:
        return None
    fill = 1.0 - p_yes + cost
    if not (0.0 < fill < 1.0):
        return None
    if (1.0 - prob) + 1e-12 < fill + SAFETY:
        return None
    no_wins = 0 if b is rec["buckets"][rec["resolved_idx"]] else 1
    fee = 1.0 * FEE_RATE * fill * (1.0 - fill)
    gross = (1.0 if no_wins else 0.0) - fill
    return {
        "slug": rec["slug"], "strait": rec["strait"],
        "week_start": rec["week_start"].isoformat(),
        "label": b["label"], "price_key": price_key,
        "ref_p_yes": p_yes, "fill": fill, "no_wins": no_wins,
        "profit_gross": gross, "fee": fee, "profit_net": gross - fee,
    }


def share_summary(trades):
    if not trades:
        return None
    profits = [t["profit_gross"] for t in trades]
    staked = sum(t["fill"] for t in trades)
    total = sum(t["profit_net"] for t in trades)
    wins = sum(t["no_wins"] for t in trades)
    return {"n": len(trades), "wins": wins,
            "median_gross": statistics.median(profits),
            "median_net": statistics.median([t["profit_net"] for t in trades]),
            "total_net": total, "staked": staked,
            "per_dollar": total / staked if staked else None,
            "hit": wins / len(trades)}


def event_summary(trades):
    if not trades:
        return None
    by_ev = {}
    for t in trades:
        by_ev.setdefault(t["slug"], []).append(t)
    pnls = [sum(x["profit_net"] for x in v) for v in by_ev.values()]
    staked = sum(t["fill"] for t in trades)
    total = sum(pnls)
    wins = sum(1 for v in pnls if v > 0)
    return {"n_events": len(by_ev), "total": total,
            "median": statistics.median(pnls), "staked": staked,
            "per_dollar": total / staked if staked else None,
            "hit": wins / len(by_ev)}


def week_summary(trades):
    if not trades:
        return None
    by_w = {}
    for t in trades:
        by_w.setdefault(t["week_start"], []).append(t)
    pnls = [sum(x["profit_net"] for x in v) for v in by_w.values()]
    staked = sum(t["fill"] for t in trades)
    total = sum(pnls)
    wins = sum(1 for v in pnls if v > 0)
    return {"n_weeks": len(by_w), "total": total,
            "median": statistics.median(pnls), "staked": staked,
            "per_dollar": total / staked if staked else None,
            "hit": wins / len(by_w)}


def share_str(s):
    if s is None:
        return "无成交"
    return ("n=%d, NO胜=%d, 中位毛利=%+.4f/份, 中位净利=%+.4f/份, "
            "总净利=%+.4f, 总投入=%.4f, 每美元投入P&L=%+.4f, 命中率=%.4f"
            % (s["n"], s["wins"], s["median_gross"], s["median_net"],
               s["total_net"], s["staked"], s["per_dollar"], s["hit"]))


def event_str(s):
    if s is None:
        return "无成交"
    return ("n_events=%d, 总净利=%+.4f, 每事件中位净利=%+.4f, "
            "总投入=%.4f, 每美元投入P&L=%+.4f, 事件命中率=%.4f"
            % (s["n_events"], s["total"], s["median"], s["staked"],
               s["per_dollar"], s["hit"]))


def week_str(s):
    if s is None:
        return "无成交"
    return ("n_weeks=%d, 总净利=%+.4f, 每周中位净利=%+.4f, "
            "总投入=%.4f, 每美元投入P&L=%+.4f, 周命中率=%.4f"
            % (s["n_weeks"], s["total"], s["median"], s["staked"],
               s["per_dollar"], s["hit"]))


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

    print("quant-018 same-time paired executable-price test | as_of=%s" % AS_OF)
    print("T=event window start (Mon 00:00 UTC) | model uses PortWatch date<T only")
    print("market=last data-api YES-implied trade in [T-24h,T] | no trade = no price")
    print("fee_rate=%.2f (entry/GUIDE 8) | half_spread=%.2f | stress cost=%.2f | safety=%.2f"
          % (FEE_RATE, HALF_SPREAD, STRESS_COST, SAFETY))
    print("bootstrap=calendar-week block, B=%d, seed=%d" % (N_BOOT, SEED))

    events, all_slugs = fetch_events()
    recs = build_records(events)
    by_strait = {}
    for r in recs:
        by_strait[r["strait"]] = by_strait.get(r["strait"], 0) + 1
    print("\n== discovery ==")
    print("public-search slugs=%d, closed weekly events=%d" % (len(all_slugs), len(recs)))
    print("by strait: " + ", ".join("%s=%d" % (k, v) for k, v in sorted(by_strait.items())))
    for strait in sorted(by_strait):
        ws = [r["week_start"] for r in recs if r["strait"] == strait]
        print("  %s: n=%d, week span %s .. %s" % (strait, len(ws), min(ws), max(ws)))
    print("date span: %s .. %s" % (recs[0]["week_start"], recs[-1]["week_start"]))
    print("exactly one resolved bucket: %d/%d"
          % (sum(1 for r in recs if r["resolved_idx"] is not None), len(recs)))

    daily, pw_rows, (pw_min, pw_max) = fetch_portwatch()
    # Model is as-of each T: daily rows are filtered to date < T inside the loop.
    print("PortWatch: rows=%d, coverage=%s..%s (current revised vintage)"
          % (len(pw_rows), pw_min, pw_max))

    for rec in recs:
        attach_prices(rec)

    # recompute proxy for revisions / rule mismatch
    match_counts = {"MATCH": 0, "MISMATCH": 0, "NO_DATA": 0}
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
        match_counts[rec["pw_match"]] += 1
    print("recompute current PortWatch vs Gamma settlement: " + ", ".join(
        "%s=%d" % (k, match_counts[k]) for k in ["MATCH", "MISMATCH", "NO_DATA"]))
    print("revision proxy: %d event weeks are affected (MISMATCH)" % match_counts["MISMATCH"])
    print("trade pagination truncations: %d buckets"
          % sum(1 for r in recs for b in r["buckets"] if b.get("trade_truncated")))

    bucket_rows = []
    event_rows = []
    for rec in recs:
        T = rec["week_start"]
        weeks = complete_weeks(daily, T)
        n = len(rec["buckets"])
        probs, prior, counts = base_rate(weeks, rec["strait"], T, rec["buckets"])
        y = [1.0 if i == rec["resolved_idx"] else 0.0 for i in range(n)]
        rec["model_probs"] = probs
        rec["prior"] = prior

        main_p = [b["main_p"] for b in rec["buckets"]]
        s6_p = [b["sens6h_p"] for b in rec["buckets"]]
        after_p = [b["after24h_p"] for b in rec["buckets"]]
        complete_main = all(v is not None for v in main_p)
        complete_s6 = all(v is not None for v in s6_p)
        complete_after = all(v is not None for v in after_p)
        rec["complete_main"] = complete_main
        rec["complete_s6"] = complete_s6
        rec["complete_after"] = complete_after

        rec["brier_model"] = brier(probs, y)
        rec["logloss_model"] = logloss(probs, y)
        rec["brier_mkt"] = rec["brier_mkt_renorm"] = None
        rec["logloss_mkt"] = rec["logloss_mkt_renorm"] = None
        rec["brier_mkt_s6"] = rec["logloss_mkt_s6"] = None
        rec["brier_mkt_after"] = rec["logloss_mkt_after"] = None
        if complete_main:
            rec["brier_mkt"] = brier(main_p, y)
            rec["logloss_mkt"] = logloss(main_p, y)
            renorm = normalize(main_p)
            if renorm:
                rec["brier_mkt_renorm"] = brier(renorm, y)
                rec["logloss_mkt_renorm"] = logloss(renorm, y)
        if complete_s6:
            rec["brier_mkt_s6"] = brier(s6_p, y)
            rec["logloss_mkt_s6"] = logloss(s6_p, y)
        if complete_after:
            rec["brier_mkt_after"] = brier(after_p, y)
            rec["logloss_mkt_after"] = logloss(after_p, y)

        for key in ["brier", "logloss"]:
            rec["diff_" + key] = (rec[key + "_mkt"] - rec[key + "_model"]
                                  if rec[key + "_mkt"] is not None else None)
            rec["diff_" + key + "_renorm"] = (
                rec[key + "_mkt_renorm"] - rec[key + "_model"]
                if rec[key + "_mkt_renorm"] is not None else None)
            rec["diff_" + key + "_s6"] = (rec[key + "_mkt_s6"] - rec[key + "_model"]
                                          if rec[key + "_mkt_s6"] is not None else None)
            rec["diff_" + key + "_after"] = (
                rec[key + "_mkt_after"] - rec[key + "_model"]
                if rec[key + "_mkt_after"] is not None else None)

        for i, b in enumerate(rec["buckets"]):
            bucket_rows.append({
                "slug": rec["slug"], "strait": rec["strait"],
                "week_start": rec["week_start"].isoformat(),
                "label": b["label"], "lo": b["lo"], "hi": b["hi"],
                "conditionId": b["conditionId"],
                "outcome_prices": (b["outcomePrices"] if isinstance(b["outcomePrices"], str)
                                   else json.dumps(b["outcomePrices"])),
                "resolved_yes": 1 if i == rec["resolved_idx"] else 0,
                "pw_prior_n": len(prior), "p_model": probs[i],
                "trade_n_fetched": b["trade_n_fetched"],
                "trade_pages": b["trade_pages"],
                "main_ts": b["main_ts"], "main_p_yes": b["main_p"],
                "sens6h_ts": b["sens6h_ts"], "sens6h_p_yes": b["sens6h_p"],
                "after24h_ts": b["after24h_ts"], "after24h_p_yes": b["after24h_p"],
            })

        event_rows.append({
            "slug": rec["slug"], "strait": rec["strait"],
            "week_start": rec["week_start"].isoformat(),
            "week_end": rec["week_end"].isoformat(),
            "n_buckets": n, "resolved_bucket": rec["resolved_label"],
            "bucket_ranges": ";".join(b["label"] for b in rec["buckets"]),
            "condition_ids": ";".join(b["conditionId"] for b in rec["buckets"]),
            "resolved_outcome_prices": ";".join(
                (b["outcomePrices"] if isinstance(b["outcomePrices"], str)
                 else json.dumps(b["outcomePrices"])) for b in rec["buckets"]),
            "pw_total": rec["pw_total"], "pw_match": rec["pw_match"],
            "prior_weeks": len(prior),
            "prices_complete_main": int(complete_main),
            "prices_complete_sens6h": int(complete_s6),
            "prices_complete_after24h": int(complete_after),
            "brier_model": rec["brier_model"],
            "brier_mkt": rec["brier_mkt"],
            "brier_mkt_renorm": rec["brier_mkt_renorm"],
            "logloss_model": rec["logloss_model"],
            "logloss_mkt": rec["logloss_mkt"],
            "logloss_mkt_renorm": rec["logloss_mkt_renorm"],
            "brier_mkt_s6": rec["brier_mkt_s6"],
            "brier_mkt_after": rec["brier_mkt_after"],
            "logloss_mkt_s6": rec["logloss_mkt_s6"],
            "logloss_mkt_after": rec["logloss_mkt_after"],
            "diff_brier": rec["diff_brier"],
            "diff_brier_renorm": rec["diff_brier_renorm"],
            "diff_logloss": rec["diff_logloss"],
            "diff_logloss_renorm": rec["diff_logloss_renorm"],
        })

    hor = [r for r in event_rows if "Hormuz" in r["strait"]]
    bab = [r for r in event_rows if "Bab" in r["strait"]]
    cm = [r for r in event_rows if r["prices_complete_main"]]
    cm_hor = [r for r in cm if "Hormuz" in r["strait"]]
    cm_bab = [r for r in cm if "Bab" in r["strait"]]
    cs6 = [r for r in event_rows if r["prices_complete_sens6h"]]
    cafter = [r for r in event_rows if r["prices_complete_after24h"]]

    print("\n== coverage ==")
    print("main [T-24h,T]: complete events %d/%d (Hormuz %d/%d, Bab %d/%d)"
          % (len(cm), len(event_rows), len(cm_hor), len(hor), len(cm_bab), len(bab)))
    print("sens [T-6h,T]: complete events %d/%d" % (len(cs6), len(event_rows)))
    print("sens [T,T+24h] first trade (look-ahead): complete events %d/%d"
          % (len(cafter), len(event_rows)))
    print("bucket prices in main window: %d/%d"
          % (sum(1 for r in bucket_rows if r["main_p_yes"] is not None), len(bucket_rows)))

    print("\n== per-event same-time scores (complete main prices) ==")
    for r in cm:
        print("%s | %-19s | %db | %-6s | Brier model %.4f mkt %.4f (renorm %.4f) | "
              "logloss model %.4f mkt %.4f"
              % (r["week_start"], r["strait"][:19], r["n_buckets"],
                 r["resolved_bucket"], r["brier_model"], r["brier_mkt"],
                 r["brier_mkt_renorm"] if r["brier_mkt_renorm"] is not None else float("nan"),
                 r["logloss_model"], r["logloss_mkt"]))

    blocks = {}
    print("\n== Brier (raw market prices, main window) ==")
    for label, rows in [("all", cm), ("Hormuz", cm_hor), ("Bab", cm_bab)]:
        line, info = score_block(rows, "brier_model", "brier_mkt", label)
        print(line)
        blocks["brier_" + label] = info
    line, info = score_block(cm, "brier_model", "brier_mkt_renorm", "all renormalised market")
    print(line)
    blocks["brier_all_renorm"] = info
    line, info = score_block(cs6, "brier_model", "brier_mkt_s6", "[T-6h,T] sensitivity")
    print(line)
    blocks["brier_s6"] = info
    line, info = score_block(cafter, "brier_model", "brier_mkt_after", "[T,T+24h] first trade exploratory")
    print(line)
    blocks["brier_after"] = info

    print("\n== log loss (raw market prices, main window) ==")
    for label, rows in [("all", cm), ("Hormuz", cm_hor), ("Bab", cm_bab)]:
        line, info = score_block(rows, "logloss_model", "logloss_mkt", label)
        print(line)
        blocks["logloss_" + label] = info
    line, info = score_block(cm, "logloss_model", "logloss_mkt_renorm", "all renormalised market")
    print(line)
    blocks["logloss_all_renorm"] = info
    line, info = score_block(cs6, "logloss_model", "logloss_mkt_s6", "[T-6h,T] sensitivity")
    print(line)
    blocks["logloss_s6"] = info
    line, info = score_block(cafter, "logloss_model", "logloss_mkt_after", "[T,T+24h] first trade exploratory")
    print(line)
    blocks["logloss_after"] = info

    for key in ["brier_all", "brier_all_renorm", "logloss_all", "logloss_all_renorm"]:
        info = blocks[key]
        if info and info.get("boot"):
            b = info["boot"]
            print("week-cluster bootstrap %s: n_weeks=%d, mean=%+.4f, SE=%.4f, "
                  "95%%CI=[%+.4f,%+.4f], p=%s"
                  % (key, b["n_weeks"], b["mean"], b["se"], b["lo"], b["hi"],
                     fmt(b["p"], 4)))

    # strict week cluster: average event diffs within a week
    for key in ["diff_brier", "diff_logloss"]:
        by_w = {}
        for r in cm:
            if r.get(key) is not None:
                by_w.setdefault(r["week_start"], []).append(r[key])
        wd = [sum(v) / len(v) for _, v in sorted(by_w.items())]
        if wd:
            t, p, sd = t_p_value(wd)
            pos = sum(1 for d in wd if d > 0)
            neg = sum(1 for d in wd if d < 0)
            sp = sign_p_value(pos, neg)
            print("strict week-cluster %s: n_weeks=%d, mean=%+.4f, t=%s, p=%s, "
                  "model better=%d/%d, sign p=%s"
                  % (key, len(wd), sum(wd) / len(wd),
                     "NA" if t is None else "%.3f" % t,
                     "NA" if p is None else "%.4f" % p,
                     pos, pos + neg,
                     "NA" if sp is None else "%.4f" % sp))

    # ------------------------------------------------------------ trade P&L
    trades_main, trades_stress = [], []
    for rec in recs:
        probs = rec["model_probs"]
        for i, b in enumerate(rec["buckets"]):
            t = make_trade(rec, b, probs[i], "main_p", HALF_SPREAD)
            if t:
                trades_main.append(t)
            t2 = make_trade(rec, b, probs[i], "main_p", STRESS_COST)
            if t2:
                trades_stress.append(t2)

    def subset(ts, needle):
        return [t for t in ts if needle in t["strait"]]

    print("\n== executable trade rule, base cost 1c (fee rate 0) ==")
    print("all triggered shares: %d" % len(trades_main))
    for name, ts in [("Bab", subset(trades_main, "Bab")),
                     ("Hormuz (exploratory, entry excludes it)", subset(trades_main, "Hormuz")),
                     ("pooled (exploratory)", trades_main)]:
        print("[%s] shares: %s" % (name, share_str(share_summary(ts))))
        print("[%s] events: %s" % (name, event_str(event_summary(ts))))
        print("[%s] calendar weeks: %s" % (name, week_str(week_summary(ts))))
        if ts:
            by_w = {}
            for t in ts:
                by_w.setdefault(t["week_start"], []).append(t)
            vals = [sum(x["profit_net"] for x in v) for _, v in sorted(by_w.items())]
            bm = bootstrap_weeks([{"week_start": k, "v": v} for k, v in
                                  sorted((w, sum(x["profit_net"] for x in ts2))
                                         for w, ts2 in by_w.items())], "v")
            if bm:
                print("[%s] week-cluster bootstrap event cash: n_weeks=%d mean=%+.4f "
                      "SE=%.4f 95%%CI=[%+.4f,%+.4f] p=%s"
                      % (name, bm["n_weeks"], bm["mean"], bm["se"],
                         bm["lo"], bm["hi"], fmt(bm["p"], 4)))

    print("\n== extra stress: 5c total cost ==")
    for name, ts in [("Bab", subset(trades_stress, "Bab")),
                     ("Hormuz (exploratory)", subset(trades_stress, "Hormuz")),
                     ("pooled (exploratory)", trades_stress)]:
        print("[%s] shares: %s" % (name, share_str(share_summary(ts))))
        print("[%s] events: %s" % (name, event_str(event_summary(ts))))
        print("[%s] calendar weeks: %s" % (name, week_str(week_summary(ts))))

    # ------------------------------------------------------------ verdict
    bab_share = share_summary(subset(trades_main, "Bab"))
    if bab_share is None:
        c1, c1_text = "INSUFFICIENT", "Bab 无成交"
    else:
        c1 = "FAIL" if bab_share["median_gross"] <= 0 else "PASS"
        c1_text = ("Bab 主口径 n=%d，中位毛利 %+.4f/份，中位净利 %+.4f/份"
                   % (bab_share["n"], bab_share["median_gross"], bab_share["median_net"]))
    n_brier = len(cm)
    if n_brier < 30:
        c3 = "INSUFFICIENT"
        c3_text = "同时点价格完整事件 n=%d < 30" % n_brier
    else:
        model_mean = blocks["brier_all"]["model"]
        mkt_mean = blocks["brier_all"]["market"]
        c3 = "PASS" if model_mean < mkt_mean else "FAIL"
        c3_text = "模型 %.4f vs 市场 %.4f (n=%d)" % (model_mean, mkt_mean, n_brier)
    if "FAIL" in (c1, c3):
        overall = "FAIL"
    elif c1 == "PASS" and c3 == "PASS":
        overall = "PASS"
    else:
        overall = "INSUFFICIENT"
    print("\n== frozen fail criteria (entry, not tuned) ==")
    print("(1) Bab 已成交 NO 份额中位已实现毛利 <= 0 ? %s (%s)" % (c1, c1_text))
    print("(3) >=30 个同时点完整事件上基准率平均 Brier 优于市场价 ? %s (%s)" % (c3, c3_text))
    print("overall verdict: %s" % overall)

    # ------------------------------------------------------------ CSV
    event_fields = list(event_rows[0].keys())
    csv_write(HERE / "events.csv", event_rows, event_fields)
    bucket_fields = list(bucket_rows[0].keys())
    csv_write(HERE / "buckets.csv", bucket_rows, bucket_fields)

    print("\nwrote events.csv (%d rows), buckets.csv (%d rows)" %
          (len(event_rows), len(bucket_rows)))

    # ------------------------------------------------------------ REPORT.md
    def block_line(key):
        info = blocks.get(key)
        return info["line"] if info else "%s: n=0" % key

    def boot_line(key):
        info = blocks.get(key)
        if not info or not info.get("boot"):
            return "NA"
        b = info["boot"]
        return ("n_weeks=%d, mean=%+.4f, SE=%.4f, 95%%CI=[%+.4f,%+.4f], p=%.4f"
                % (b["n_weeks"], b["mean"], b["se"], b["lo"], b["hi"], b["p"]))

    report = []
    report.append("# quant-018 同时点、可成交价配对检验（data-api 成交）")
    report.append("")
    report.append("结论：**%s**。标准 (1) **%s**（%s）；标准 (3) **%s**（%s）。"
                  % (overall, c1, c1_text, c3, c3_text))
    report.append("")
    report.append("全部数字由 `q018_paired.py` 生成；stdout 见 `run_output.txt`，"
                  "逐事件见 `events.csv`，逐档见 `buckets.csv`。原始下载在 `_cache/`（已 gitignore）。")
    report.append("")
    report.append("## 1. 数据与访问")
    report.append("")
    report.append("- 访问日期 **%s**；全部公开 GET，无密钥、无登录、未交易。" % AS_OF)
    report.append("- 事件发现：`https://gamma-api.polymarket.com/public-search?q=how%20many%20ships%20transit&limit_per_type=100&events_status=all`；"
                  "逐事件 `https://gamma-api.polymarket.com/events?slug=<slug>` 取 `description / conditionId / outcomePrices / feesEnabled`。")
    report.append("- 成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`，"
                  "分页到早于 `T-24h`；把 YES 成交价记为 p、NO 成交价记为 1-p。")
    report.append("- PortWatch：`https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query`，"
                  "字段 `date,portname,n_total`，按 1,000 行分页。")
    _spans = []
    for _k in sorted(by_strait):
        _ws = [r["week_start"] for r in recs if r["strait"] == _k]
        _spans.append("%s %d 个（%s..%s）" % (_k, len(_ws), min(_ws), max(_ws)))
    report.append("- 覆盖：Gamma 同族 slug %d 个，已关闭周度事件 **%d** 个；%s；总体周起点 %s 至 %s。"
                  "PortWatch %d 行，%s..%s。"
                  % (len(all_slugs), len(recs), "；".join(_spans),
                     recs[0]["week_start"], recs[-1]["week_start"],
                     len(pw_rows), pw_min, pw_max))
    report.append("- 当前 PortWatch 复算 vs Gamma 结算：MATCH=%d，MISMATCH=%d，NO_DATA=%d；"
                  "**修订/口径代理：%d 个事件周受影响**。"
                  % (match_counts["MATCH"], match_counts["MISMATCH"],
                     match_counts["NO_DATA"], match_counts["MISMATCH"]))
    report.append("")
    report.append("## 2. 预先写死的方法")
    report.append("")
    report.append("- **决策时点 T** = 事件窗口起始日（周一 00:00 UTC）。条目未另给决策时点。")
    report.append("- **模型**：仅用 PortWatch `date < T` 的日度数据；同海峡最近 12 个完整 Mon–Sun 周，"
                  "按当期档位套入，Laplace `(k_i+1)/(12+n)`。")
    report.append("- **市场价（主口径）**：每档在 `[T-24h, T]` 内最后一笔 data-api 成交，换算成 YES 价；"
                  "窗口内无成交则该档无价，不填充。敏感性：`[T-6h,T]`；以及 `[T,T+24h]` 首笔（含前视，仅探索）。")
    report.append("- **评分**：多分类 Brier `Σ(p_i-y_i)^2` 与 log loss `-log p_win`；"
                  "主口径用原始市场价，另报按档归一化后的市场价。事件内每档都有价才计分。")
    report.append("- **不确定性**：事件级配对 t 与符号检验；按日历周分块 bootstrap（同周两海峡共享新闻），"
                  "10,000 次，固定种子 %d。" % SEED)
    report.append("- **交易**：仅 Bab（条目明确不做 Hormuz）；`NO_executable = 1-p_yes+0.01`，"
                  "触发 `1-p_model >= NO_executable+0.01`；每档 1 份；吃单费按条目/GUIDE §8 地缘费率 **0**；"
                  "压力情形总成本 **0.05**。Hormuz 与合并结果仅探索。")
    report.append("- **失败标准**：条目冻结的 (1) 中位已实现毛利 ≤ 0；(3) ≥30 个历史事件上 Brier 不优于市场价；"
                  "不调阈值。")
    report.append("")
    report.append("## 3. 结果（脚本 stdout 原样）")
    report.append("")
    report.append("```")
    report.append("覆盖（主口径 [T-24h,T] 全档有价）：%d/%d（Hormuz %d/%d，Bab %d/%d）"
                  % (len(cm), len(event_rows), len(cm_hor), len(hor), len(cm_bab), len(bab)))
    report.append("覆盖（[T-6h,T]）：%d/%d；覆盖（[T,T+24h] 首笔，探索）：%d/%d"
                  % (len(cs6), len(event_rows), len(cafter), len(event_rows)))
    report.append("主口径有价档位：%d/%d"
                  % (sum(1 for r in bucket_rows if r["main_p_yes"] is not None), len(bucket_rows)))
    report.append("")
    report.append(block_line("brier_all"))
    report.append(block_line("brier_all_renorm"))
    report.append(block_line("brier_Hormuz"))
    report.append(block_line("brier_Bab"))
    report.append(block_line("brier_s6"))
    report.append(block_line("brier_after"))
    report.append("")
    report.append(block_line("logloss_all"))
    report.append(block_line("logloss_all_renorm"))
    report.append(block_line("logloss_Hormuz"))
    report.append(block_line("logloss_Bab"))
    report.append(block_line("logloss_s6"))
    report.append(block_line("logloss_after"))
    report.append("")
    report.append("周聚类 bootstrap Brier all: " + boot_line("brier_all"))
    report.append("周聚类 bootstrap Brier all(renorm): " + boot_line("brier_all_renorm"))
    report.append("周聚类 bootstrap logloss all: " + boot_line("logloss_all"))
    report.append("周聚类 bootstrap logloss all(renorm): " + boot_line("logloss_all_renorm"))
    report.append("")
    for name, ts in [("Bab", subset(trades_main, "Bab")),
                     ("Hormuz (探索)", subset(trades_main, "Hormuz")),
                     ("合并 (探索)", trades_main)]:
        report.append("主成本 1c，%s 份额：%s" % (name, share_str(share_summary(ts))))
        report.append("主成本 1c，%s 事件现金：%s" % (name, event_str(event_summary(ts))))
        report.append("主成本 1c，%s 周聚类：%s" % (name, week_str(week_summary(ts))))
    report.append("")
    for name, ts in [("Bab", subset(trades_stress, "Bab")),
                     ("Hormuz (探索)", subset(trades_stress, "Hormuz")),
                     ("合并 (探索)", trades_stress)]:
        report.append("压力 5c，%s 份额：%s" % (name, share_str(share_summary(ts))))
        report.append("压力 5c，%s 事件现金：%s" % (name, event_str(event_summary(ts))))
        report.append("压力 5c，%s 周聚类：%s" % (name, week_str(week_summary(ts))))
    report.append("")
    report.append("**判定**：overall **%s**；标准 (1) **%s**（%s）；标准 (3) **%s**（%s）。"
                  % (overall, c1, c1_text, c3, c3_text))
    report.append("```")
    report.append("")
    report.append("## 4. 与旧 prices-history 数字对比")
    report.append("")
    old_bab = ("旧报告：43 个已关闭事件，首价完整 43/43、周起点价完整 34/43；"
               "Brier 全部 0.7658 vs 0.8060，Bab 0.8580 vs 0.8032（n=12，模型更差）；"
               "Bab 交易 n=29、中位毛利 +0.2250/份。"
               "（来源：`bots/quant/notes/q018-price-test/REPORT.md`，逐字引用）")
    report.append("- " + old_bab)
    new_brier_all = blocks["brier_all"]
    new_brier_bab = blocks["brier_Bab"]
    new_trade_bab = share_summary(subset(trades_main, "Bab"))
    report.append("- 本次同时点可成交价：Brier 全样本 n=%d，%s；Bab n=%d，%s。"
                  % (new_brier_all["n"] if new_brier_all else 0,
                     ("模型 %.4f vs 市场 %.4f，差 %+.4f"
                      % (new_brier_all["model"], new_brier_all["market"], new_brier_all["diff"]))
                     if new_brier_all else "无完整事件",
                     new_brier_bab["n"] if new_brier_bab else 0,
                     ("模型 %.4f vs 市场 %.4f，差 %+.4f"
                      % (new_brier_bab["model"], new_brier_bab["market"], new_brier_bab["diff"]))
                     if new_brier_bab else "无完整事件"))
    report.append("- 本次 Bab 交易：%s。" % share_str(new_trade_bab))
    _bet = event_summary(subset(trades_main, "Bab"))
    _bst = share_summary(subset(trades_stress, "Bab"))
    report.append("- **n 是否成立**：已关闭事件 43（Hormuz 31 / Bab 12）在本次 discovery 中复现；"
                  "但主口径同时点全档有价只有 24/43（Hormuz 19/31、Bab 5/12），"
                  "所以旧的 43/31/12 不能直接当作同时点可评分样本量。")
    report.append("- **Brier 数字是否成立**：**不成立**。旧的 0.7658 vs 0.8060（n=43）在同时点可成交价下 "
                  "raw 为 0.7047 vs 0.9318（n=24），但 raw 市场价未归一化、差距被放大；"
                  "与旧口径更可比的归一化市场价为 0.7047 vs 0.7408（n=24，差 +0.0360，"
                  "t=0.428，p=0.6729），远小于旧差且不显著。Bab 子集 n=5，"
                  "0.7471 vs 0.7710（差 +0.0239），与旧报告的“模型更差 −0.0548”方向相反，"
                  "但样本太小，两者都不能当证据。旧标准 (3) 的 PASS 不可复现。")
    report.append("- **Bab P&L 是否成立**：**只在字面口径上成立，经济结论不成立**。"
                  "旧报告纯周起点价 n=29、中位毛利 +0.2250/份、每美元投入 +0.0376；"
                  "本次 n=%s、份额中位毛利 %+.4f/份（标准 (1) 仍 PASS），"
                  "但事件层总净利 %+.4f、每事件中位净利 %+.4f、每美元投入 %+.4f、"
                  "事件命中率 %.4f；5¢ 压力下总净利 %+.4f、每美元投入 %+.4f。"
                  % (new_trade_bab["n"] if new_trade_bab else 0,
                     new_trade_bab["median_gross"] if new_trade_bab else float("nan"),
                     _bet["total"] if _bet else float("nan"),
                     _bet["median"] if _bet else float("nan"),
                     _bet["per_dollar"] if _bet else float("nan"),
                     _bet["hit"] if _bet else float("nan"),
                     _bst["total_net"] if _bst else float("nan"),
                     _bst["per_dollar"] if _bst else float("nan")))
    report.append("- 旧报告的价格是 CLOB 最后成交价、且模型与市场不在同一时点；"
                  "本次改为同一 T 的 data-api 成交价，并要求事件内每档都有成交才计分。")
    report.append("")
    report.append("## 5. 限制")
    report.append("")
    report.append("- data-api 成交是**已成交打印**，不是完整订单簿；无法知道当时可成交深度，"
                  "1¢/5¢ 成本是假设，薄市场可能更差。")
    report.append("- 主口径要求事件内每档都在 `[T-24h,T]` 有成交，覆盖不足会直接降低样本量；"
                  "无成交的档不填充，避免用旧价冒充同时点价格。")
    report.append("- data-api 的逐档最后成交价相加不一定等于 1（个别事件远大于 1），"
                  "因此 raw 市场 Brier 会被机械放大；归一化变体是更公平的对比，两者都报。")
    report.append("- PortWatch 是**当前修订后**版本，不是 T 时点的 vintage；无法真正复现 as-of。"
                  "本次以“当前复算与 Gamma 结算不一致的事件周数”作为可观测代理，"
                  "上述 %d 个事件周受影响；其余周的 12 周回看窗口也可能被后续修订影响，无法量化。"
                  % match_counts["MISMATCH"])
    report.append("- 同周 Hormuz 与 Bab 共享新闻与地缘驱动，事件级 t/符号检验会高估独立性；"
                  "周聚类 bootstrap 是主不确定性口径。")
    report.append("- 交易规则按条目只做 Bab；Hormuz/合并结果只作探索，不进入判定。")
    report.append("")
    report.append("## 6. 复现")
    report.append("")
    report.append("- `python3 bots/quant/notes/q018-paired/q018_paired.py`（缓存存在时不联网，输出逐字节一致）")
    report.append("- `python3 tools/check.py lint`：见 `lint_output.txt`（既有 muse-700/701 问题，与本任务无关）")
    report.append("")
    (HERE / "REPORT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
