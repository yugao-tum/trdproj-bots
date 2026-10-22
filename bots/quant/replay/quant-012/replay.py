#!/usr/bin/env python3
"""quant-012 canonical replay: earthquake weekly-count ladders vs USGS base rates.

What this does (all choices fixed before looking at the result):

  * Universe: closed Polymarket "how-many ... earthquakes ..." ladder events,
    found through Gamma public-search (free, keyless), same universe as
    notes/q012-hist (68 events / 514 brackets).
  * Decision time t0 = the event window start stated in the market rules
    (ET Monday 00:00, converted to UTC). The base-rate model uses only USGS
    events that happened strictly BEFORE t0.
  * Model: empirical distribution of counts in consecutive, adjacent historical
    windows of the same length ending at t0 (USGS FDSN, min magnitude per
    series), Laplace pseudo-count 0.5 per bracket.
  * Entry signal: market_yes(t) - model_yes > 0.01  -> buy NO, hold to
    settlement. market_yes(t) comes from the FIRST data-api per-trade fill at
    or after t0 (never a price printed before the decision time).
  * Execution: taker buy NO at (1 - market_yes) + 0.01 (one cent concession),
    capped at 0.999. Taker fee = rate * p * (1-p) per share with rate = 0.05
    (the weather schedule observed on 2026-10 schedules; conservative for
    markets whose live feeSchedule is 0). Fee-0 sensitivity is variant 2.
  * Sizing: 100 shares per bracket, at most 300 USDT per event, 1,000 USDT
    sleeve out of the 5,000 USDT account. Greedy by edge, events in fill order.
  * Settlement: NO pays 1 if the bracket did not win, else 0; cash arrives at
    window_end + 48h (rule allows up to 48h for late/reported quakes).
  * Drawdown: daily equity = cash + open positions at cost (realised only, no
    floating mark). Labelled as such in SUMMARY.md.

Outputs (all text, < 1 MB):
  trades.csv    one row per bracket that passed the signal, with fill details
  events.csv    one row per event (independent result)
  run_output.txt is produced by the caller: python3 replay.py | tee run_output.txt

Raw downloads are cached under _cache/ (gitignored, never committed).
"""

import argparse
import bisect
import csv
import json
import math
import re
import statistics
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
GAMMA = CACHE / "gamma"
USGS = CACHE / "usgs"
TRADES = CACHE / "trades"
for d in (GAMMA, USGS, TRADES):
    d.mkdir(parents=True, exist_ok=True)

S = requests.Session()
S.headers["User-Agent"] = "quant-research/1.0 (public keyless data)"

ET = ZoneInfo("America/New_York")
FEE_RATE = 0.05
HALF_SPREAD = 0.01
EDGE_MIN = 0.01
PSEUDO = 0.5
SLEEVE = 1000.0
ACCOUNT = 5000.0
SHARES_PER_BUCKET = 100
MAX_USDT_PER_EVENT = 300.0
SETTLE_LAG_H = 48.0


def get_json(url, params, path, tries=6):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    last = None
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=90)
            if r.status_code == 200:
                d = r.json()
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False)
                time.sleep(0.08)
                return d
            last = f"HTTP {r.status_code}"
            time.sleep(1.5 * (i + 1))
        except Exception as exc:
            last = repr(exc)
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url} {params}: {last}")


def get_text(url, params, path, tries=6):
    if path.exists():
        return path.read_text(encoding="utf-8")
    last = None
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=180)
            if r.status_code == 200:
                path.write_text(r.text, encoding="utf-8")
                return r.text
            last = f"HTTP {r.status_code}"
            time.sleep(1.5 * (i + 1))
        except Exception as exc:
            last = repr(exc)
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url} {params}: {last}")


# ---------------------------------------------------------------- universe
def collect_events(limit=None):
    seen = {}
    for q in ("earthquake", "magnitude", "earthquakes"):
        page = 1
        while page <= 10:
            d = get_json(
                "https://gamma-api.polymarket.com/public-search",
                {"q": q, "limit_per_type": 50, "events_status": "closed", "page": page},
                GAMMA / f"search_{q}_{page}.json",
            )
            for e in d.get("events", []):
                slug = e.get("slug", "")
                if slug.startswith("how-many") and "earthquake" in slug and e.get("closed"):
                    seen[slug] = e
            if not d.get("pagination", {}).get("hasMore"):
                break
            page += 1
    events = []
    for slug in sorted(seen):
        d = get_json(
            "https://gamma-api.polymarket.com/events",
            {"slug": slug},
            GAMMA / f"ev_{slug}.json",
        )
        ev = d[0] if isinstance(d, list) and d else (d if isinstance(d, dict) else None)
        if ev and ev.get("closed"):
            events.append(ev)
        if limit and len(events) >= limit:
            break
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
    end = conv(m.group(2)) + timedelta(minutes=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def parse_bracket(label):
    s = str(label).strip().lower().replace("–", "-")
    if s.startswith("≤") or s.startswith("<=") or s.endswith(" or fewer"):
        return 0, int(re.findall(r"\d+", s)[0])
    if s.startswith("<"):
        return 0, int(re.findall(r"\d+", s)[0]) - 1
    if s.startswith(">") or s.startswith("more than"):
        return int(re.findall(r"\d+", s)[0]) + 1, None
    if s.endswith("+"):
        return int(re.findall(r"\d+", s)[0]), None
    if re.fullmatch(r"\d+", s):
        return int(s), int(s)
    nums = [int(x) for x in re.findall(r"\d+", s)]
    if len(nums) == 2:
        return nums[0], nums[1]
    raise ValueError(f"unparsed bracket {label!r}")


def event_magnitude(ev):
    text = ev.get("slug", "") + " " + ev.get("title", "")
    if re.search(r"5pt5|5\.5", text):
        return 5.5
    if re.search(r"6pt5|6\.5", text):
        return 6.5
    if re.search(r"7pt0|7\.0", text):
        return 7.0
    m = re.search(r"magnitude of (\d+(?:\.\d+)?)", ev.get("description", ""))
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------- USGS
def load_usgs(threshold):
    qthr = round(threshold - 0.1, 1)
    path = USGS / f"usgs_{qthr}.csv"
    get_text(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        {
            "format": "csv",
            "starttime": "2000-01-01",
            "endtime": "2026-10-21",
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
            if mag >= threshold:
                times.append(
                    datetime.fromisoformat(row["time"].replace("Z", "+00:00")).timestamp()
                )
    times.sort()
    return times


def count_dist(times, end_ts, length_s):
    """Empirical distribution of counts in adjacent windows ending at end_ts."""
    lo = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()
    counts = []
    end = end_ts
    while end - length_s >= lo:
        ws = end - length_s
        counts.append(bisect.bisect_left(times, end) - bisect.bisect_left(times, ws))
        end = ws
    return counts, len(counts)


def conditional_probs(times, t_fill, length_s, brackets, k_seen):
    """Rule 2 of the entry: condition on k quakes already seen and on the
    remaining window length, then shift the count distribution by k."""
    elapsed = t_fill
    # caller passes the remaining length as length_s and t_fill as the window end
    counts, n = count_dist(times, t_fill, length_s)
    if not counts:
        return None
    max_k = max(b[1] if b[1] is not None else max(counts) for b in brackets)
    freq = {x: counts.count(x) / n for x in range(max_k + 1)}
    raw = []
    for a, b in brackets:
        lo = max(0, a - k_seen)
        if b is None:
            p = sum(v for x, v in freq.items() if x >= lo)
            feasible = True
        elif b - k_seen < 0:
            p, feasible = 0.0, False
        else:
            p = sum(freq.get(x, 0.0) for x in range(lo, b - k_seen + 1))
            feasible = True
        raw.append(p * n + (PSEUDO if feasible else 0.0))
    tot = sum(raw)
    if tot <= 0:
        return None
    return [x / tot for x in raw]


def empirical_probs(times, start_ts, length_s, brackets):
    lo = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()
    counts = []
    end = start_ts
    while end - length_s >= lo:
        ws = end - length_s
        counts.append(bisect.bisect_left(times, end) - bisect.bisect_left(times, ws))
        end = ws
    if not counts:
        return None, 0
    n = len(counts)
    max_k = max(b[1] if b[1] is not None else max(counts) for b in brackets)
    freq = {k: counts.count(k) / n for k in range(max_k + 1)}
    raw = []
    for a, b in brackets:
        if b is None:
            p = sum(v for k, v in freq.items() if k >= a)
        else:
            p = sum(freq.get(k, 0.0) for k in range(a, b + 1))
        raw.append(p * n + PSEUDO)
    tot = sum(raw)
    return [x / tot for x in raw], n


# ---------------------------------------------------------------- trades
def fetch_trades(cid, t0, t1):
    """Newest-first data-api fills, paged backwards until older than t0-24h."""
    out = []
    offset = 0
    for _ in range(12):
        d = get_json(
            "https://data-api.polymarket.com/trades",
            {"market": cid, "limit": 500, "offset": offset},
            TRADES / f"{cid}__{offset}.json",
        )
        if not d:
            break
        for x in d:
            ts = int(x["timestamp"])
            if t0 - 86400 <= ts <= t1 + 86400:
                out.append(
                    {
                        "t": ts,
                        "price": float(x["price"]),
                        "outcome": x["outcome"],
                        "size": float(x.get("size", 0)),
                    }
                )
        oldest = min(int(x["timestamp"]) for x in d)
        if len(d) < 500 or oldest < t0 - 86400:
            break
        offset += 500
    out.sort(key=lambda x: x["t"])
    return out


def yes_price(tr):
    return tr["price"] if tr["outcome"].lower() == "yes" else 1.0 - tr["price"]


def pick(trades, t0, t1):
    """First fill at/after t0 (canonical) and last fill in [t0-24h, t0] (baseline)."""
    post = [x for x in trades if t0 <= x["t"] <= t1]
    pre = [x for x in trades if t0 - 86400 <= x["t"] < t0]
    first = post[0] if post else None
    last = pre[-1] if pre else None
    return first, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="smoke test: first N events")
    args = ap.parse_args()

    print("=" * 78)
    print("quant-012 replay: tradable-price fills after decision time")
    print("=" * 78)

    events = collect_events(args.limit)
    print(f"\n[1] closed ladder events pulled from Gamma: {len(events)}")

    usgs = {m: load_usgs(m) for m in (5.5, 6.5, 7.0)}
    for m, t in usgs.items():
        print(f"    USGS M{m:.1f}+ events since 2000-01-01: {len(t)}")

    buckets = []
    pre_candidates = []
    cond_candidates = []
    ev_rows = []
    skipped = []

    for ev in events:
        mag = event_magnitude(ev)
        w = parse_window(ev)
        if not mag or not w:
            skipped.append((ev.get("slug"), "window/magnitude unparsed"))
            continue
        t0, t1 = w[0].timestamp(), w[1].timestamp()
        mkts = []
        for m in ev.get("markets", []):
            try:
                lo, hi = parse_bracket(m.get("groupItemTitle"))
            except Exception:
                skipped.append((ev.get("slug"), f"bracket {m.get('groupItemTitle')!r}"))
                continue
            op = json.loads(m.get("outcomePrices") or "[]")
            mkts.append(
                {
                    "label": m.get("groupItemTitle"),
                    "lo": lo,
                    "hi": hi,
                    "cid": m.get("conditionId"),
                    "resolved_yes": bool(op and float(op[0]) > 0.5),
                    "fee_rate": float((m.get("feeSchedule") or {}).get("rate") or 0.0),
                }
            )
        if not mkts or not any(x["resolved_yes"] for x in mkts):
            skipped.append((ev.get("slug"), "no resolved winner"))
            continue
        mkts.sort(key=lambda x: x["lo"])
        probs, n_hist = empirical_probs(usgs[mag], t0, t1 - t0, [(x["lo"], x["hi"]) for x in mkts])
        if probs is None:
            skipped.append((ev.get("slug"), "no history"))
            continue
        won = next(x for x in mkts if x["resolved_yes"])
        count = sum(1 for t in usgs[mag] if t0 <= t < t1)
        match = won["lo"] <= count and (won["hi"] is None or count <= won["hi"])

        for mk, p in zip(mkts, probs):
            trades = fetch_trades(mk["cid"], t0, t1)
            first, last = pick(trades, t0, t1)
            mk["model"] = p
            mk["first"] = first
            mk["last"] = last
            mk["n_trades"] = len(trades)
            mk["post_yes"] = yes_price(first) if first else None
            mk["pre_yes"] = yes_price(last) if last else None
            mk["delay_h"] = (first["t"] - t0) / 3600 if first else None
            mk["k_seen"] = None
            mk["model_cond"] = None
            if first is not None:
                mk["k_seen"] = sum(1 for x in usgs[mag] if t0 <= x < first["t"])
                remain = max(3600.0, (t1 - first["t"]))
                cp = conditional_probs(usgs[mag], first["t"], remain,
                                       [(x["lo"], x["hi"]) for x in mkts], mk["k_seen"])
                if cp is not None:
                    mk["model_cond"] = cp[mkts.index(mk)]

        # model vs market log loss (only events with every bracket priced post-t0)
        model_ll = market_ll = None
        if len(mkts) > 1 and all(x["post_yes"] is not None for x in mkts):
            raw = [max(1e-9, x["post_yes"]) for x in mkts]
            s = sum(raw)
            mp = [x / s for x in raw]
            model_ll = -math.log(max(probs[mkts.index(won)], 1e-12))
            market_ll = -math.log(max(mp[mkts.index(won)], 1e-12))

        n_priced = sum(1 for x in mkts if x["post_yes"] is not None)
        n_signals = sum(
            1 for x in mkts if x["post_yes"] is not None and x["post_yes"] - x["model"] > EDGE_MIN
        )
        ev_rows.append(
            {
                "event_slug": ev["slug"],
                "series": f"M{mag}+",
                "window_start_utc": w[0].isoformat(),
                "window_end_excl_utc": w[1].isoformat(),
                "window_days": f"{(t1 - t0) / 86400:.4f}",
                "usgs_count": count,
                "resolved_bucket": won["label"],
                "usgs_match": "MATCH" if match else "MISMATCH",
                "n_buckets": len(mkts),
                "n_priced_post": n_priced,
                "n_signals": n_signals,
                "model_logloss": "" if model_ll is None else f"{model_ll:.6f}",
                "market_logloss": "" if market_ll is None else f"{market_ll:.6f}",
                "strict_group": f"{w[0].date()}_{w[1].date()}",
            }
        )

        for mk in mkts:
            if mk["post_yes"] is None:
                continue
            payoff = 0.0 if mk["resolved_yes"] else 1.0
            if mk["pre_yes"] is not None and mk["pre_yes"] - mk["model"] > EDGE_MIN:
                pre_no = min(0.999, (1.0 - mk["pre_yes"]) + HALF_SPREAD)
                pre_candidates.append(
                    {
                        "event_slug": ev["slug"],
                        "series": f"M{mag}+",
                        "strict_group": f"{w[0].date()}_{w[1].date()}",
                        "resolved_yes": int(mk["resolved_yes"]),
                        "shares": 1,
                        "cost": pre_no,
                        "pre_net_per_share": payoff - pre_no - FEE_RATE * pre_no * (1 - pre_no),
                    }
                )
            if mk["model_cond"] is not None and mk["k_seen"] is not None and mk["k_seen"] < 3:
                edge_c = mk["post_yes"] - mk["model_cond"]
                if edge_c > EDGE_MIN:
                    p_no_c = min(0.999, (1.0 - mk["post_yes"]) + HALF_SPREAD)
                    cond_candidates.append(
                        {
                            "event_slug": ev["slug"],
                            "series": f"M{mag}+",
                            "bucket": mk["label"],
                            "strict_group": f"{w[0].date()}_{w[1].date()}",
                            "resolved_yes": int(mk["resolved_yes"]),
                            "k_seen": mk["k_seen"],
                            "model_cond": mk["model_cond"],
                            "market_yes_post": mk["post_yes"],
                            "edge_cond": edge_c,
                            "fill_utc": datetime.fromtimestamp(mk["first"]["t"], timezone.utc).isoformat(),
                            "no_entry": p_no_c,
                            "shares": 1,
                            "cost": p_no_c,
                            "net_cond": payoff - p_no_c - FEE_RATE * p_no_c * (1 - p_no_c),
                        }
                    )
            edge = mk["post_yes"] - mk["model"]
            if edge <= EDGE_MIN:
                continue
            p_no = min(0.999, (1.0 - mk["post_yes"]) + HALF_SPREAD)
            fee05 = FEE_RATE * p_no * (1.0 - p_no)
            pre_no = None
            if mk["pre_yes"] is not None:
                pre_no = min(0.999, (1.0 - mk["pre_yes"]) + HALF_SPREAD)
            buckets.append(
                {
                    "event_slug": ev["slug"],
                    "series": f"M{mag}+",
                    "bucket": mk["label"],
                    "lo": mk["lo"],
                    "hi": "" if mk["hi"] is None else mk["hi"],
                    "resolved_yes": int(mk["resolved_yes"]),
                    "model_yes": f"{mk['model']:.6f}",
                    "market_yes_post": f"{mk['post_yes']:.6f}",
                    "edge": f"{edge:.6f}",
                    "fill_ts": mk["first"]["t"],
                    "fill_utc": datetime.fromtimestamp(mk["first"]["t"], timezone.utc).isoformat(),
                    "delay_h": f"{mk['delay_h']:.2f}",
                    "no_entry": f"{p_no:.6f}",
                    "fee_005": f"{fee05:.6f}",
                    "gross_per_share": f"{payoff - p_no:+.6f}",
                    "net_per_share": f"{payoff - p_no - fee05:+.6f}",
                    "net_per_share_fee0": f"{payoff - p_no:+.6f}",
                    "market_yes_pre": "" if mk["pre_yes"] is None else f"{mk['pre_yes']:.6f}",
                    "no_entry_pre": "" if pre_no is None else f"{pre_no:.6f}",
                    "pre_net_per_share": ""
                    if pre_no is None
                    else f"{payoff - pre_no - FEE_RATE * pre_no * (1 - pre_no):+.6f}",
                    "gamma_fee_rate": f"{mk['fee_rate']:.4f}",
                    "strict_group": f"{w[0].date()}_{w[1].date()}",
                    "window_end_ts": t1,
                    "settle_ts": t1 + SETTLE_LAG_H * 3600,
                }
            )

    print(f"\n[2] events with a resolved bracket: {len(ev_rows)}; skipped: {len(skipped)}")
    for slug, why in skipped[:10]:
        print(f"      - {slug}: {why}")

    # ---------------- signal-level (1 share) and capacity portfolio ----------------
    buckets.sort(key=lambda b: b["fill_ts"])

    def stats(rows, key):
        if not rows:
            return (0, 0, 0.0, 0.0, 0.0, 0.0)
        v = [float(r[key]) for r in rows]
        s = sum(r["shares"] * float(r[key]) for r in rows)
        st = sum(r["cost"] for r in rows)
        return (len(rows), len({r["event_slug"] for r in rows}),
                statistics.median(v), statistics.mean(v), s, (s / st * 100 if st else 0.0))

    all_rows = []
    for b in buckets:
        b = dict(b)
        b["shares"] = 1
        b["cost"] = float(b["no_entry"])
        b["pnl_fee005"] = float(b["net_per_share"])
        b["pnl_fee0"] = float(b["net_per_share_fee0"])
        all_rows.append(b)

    # capacity-constrained sleeve: settle cash before each new fill
    cash = SLEEVE
    open_pos, done, skipped_cash = [], [], 0
    per_event_used = {}
    for b in buckets:
        for p in [x for x in open_pos if x["settle_ts"] <= b["fill_ts"]]:
            cash += p["shares"] * (0.0 if int(p["resolved_yes"]) else 1.0)
            open_pos.remove(p)
            done.append(p)
        cost = SHARES_PER_BUCKET * float(b["no_entry"])
        fee = SHARES_PER_BUCKET * FEE_RATE * float(b["no_entry"]) * (1.0 - float(b["no_entry"]))
        used = per_event_used.get(b["event_slug"], 0.0)
        if used + cost > MAX_USDT_PER_EVENT or cost + fee > cash:
            skipped_cash += 1
            continue
        b = dict(b)
        b["shares"] = SHARES_PER_BUCKET
        b["cost"] = round(cost, 6)
        b["pnl_fee005"] = round(SHARES_PER_BUCKET * float(b["net_per_share"]), 6)
        b["pnl_fee0"] = round(SHARES_PER_BUCKET * float(b["net_per_share_fee0"]), 6)
        cash -= cost + fee
        per_event_used[b["event_slug"]] = used + cost
        open_pos.append(b)
    for p in open_pos:
        cash += p["shares"] * (0.0 if int(p["resolved_yes"]) else 1.0)
        done.append(p)
    open_pos = []

    # daily equity, realised only, open positions at cost
    eq, maxdd, maxdd_usdt = [], 0.0, 0.0
    if done:
        d0 = min(datetime.fromtimestamp(b["fill_ts"], timezone.utc).date() for b in done)
        d1 = max(datetime.fromtimestamp(b["settle_ts"], timezone.utc).date() for b in done)
        d = d0
        while d <= d1:
            day_end = datetime(d.year, d.month, d.day, 23, 59, tzinfo=timezone.utc).timestamp()
            realised = sum(b["pnl_fee005"] for b in done if b["settle_ts"] <= day_end)
            pos_cost = sum(b["cost"] for b in done if b["fill_ts"] <= day_end < b["settle_ts"])
            eq.append((d.isoformat(), SLEEVE + realised, pos_cost))
            d += timedelta(days=1)
        peak = -1e18
        for _, e, _ in eq:
            peak = max(peak, e)
            if peak - e > maxdd_usdt:
                maxdd_usdt = peak - e
                maxdd = (peak - e) / peak * 100

    net05 = sum(b["pnl_fee005"] for b in done)
    staked = sum(b["cost"] for b in done)
    days = (
        max(b["settle_ts"] for b in done) - min(b["fill_ts"] for b in done)
    ) / 86400 if done else 0.0
    ann = net05 * 365.0 / days / ACCOUNT * 100 if days else 0.0

    print("\n[3] canonical signal-level (first print at/after window start, taker NO, fee 0.05)")
    n, evn, med, mean, tot, pct = stats(all_rows, "net_per_share")
    print(f"    filled brackets = {n}; independent events = {evn}; "
          f"strict groups = {len({b['strict_group'] for b in all_rows})}")
    print(f"    median net/share = {med:+.4f}; mean net/share = {mean:+.4f}")
    print(f"    total net = {tot:+.4f} USDT on {sum(float(b['no_entry']) for b in all_rows):.4f} USDT "
          f"notional (1 share each) = {pct:+.2f}%")
    tot0 = sum(float(b["net_per_share_fee0"]) for b in all_rows)
    print(f"    fee-0 total = {tot0:+.4f} USDT = "
          f"{tot0 / sum(float(b['no_entry']) for b in all_rows) * 100:+.2f}%")
    delays = [float(b["delay_h"]) for b in all_rows]
    print(f"    fill delay after t0: median {statistics.median(delays):.2f}h, "
          f"p90 {sorted(delays)[int(0.9 * (len(delays) - 1))]:.2f}h, max {max(delays):.2f}h")
    print(f"    NO won {sum(1 for b in all_rows if int(b['resolved_yes']) == 0)}/{n} brackets; "
          f"NO lost {sum(1 for b in all_rows if int(b['resolved_yes']) == 1)}")

    print("\n[3b] capacity portfolio (sleeve 1,000 USDT; 100 shares/bracket; <=300 USDT/event)")
    if done:
        print(f"    filled brackets = {len(done)}; independent events = {len({b['event_slug'] for b in done})}; "
              f"skipped for cash/event cap = {skipped_cash}")
        print(f"    net = {net05:+.2f} USDT on {staked:.2f} USDT cost = "
              f"{net05 / staked * 100:+.2f}% (fee 0.05)")
        print(f"    cash at end = {cash:.2f} USDT (start {SLEEVE:.0f})")
        print(f"    max drawdown (daily, realised only) = {maxdd:.2f}% ({maxdd_usdt:.2f} USDT)")
        print(f"    sample span = {days:.1f} days; annualised contribution on {ACCOUNT:.0f} USDT = "
              f"{ann:+.2f}%")
    else:
        print("    no fills")

    print("\n[4] splits of the canonical signal (1 share each, net per share, fee 0.05)")
    for name, subset in (
        ("all", all_rows),
        ("delay <= 24h", [b for b in all_rows if float(b["delay_h"]) <= 24]),
        ("M6.5+", [b for b in all_rows if b["series"] == "M6.5+"]),
        ("M5.5+", [b for b in all_rows if b["series"] == "M5.5+"]),
        ("M7.0+", [b for b in all_rows if b["series"] == "M7.0+"]),
        ("fill < 2026-07-01", [b for b in all_rows if b["fill_utc"] < "2026-07-01"]),
        ("fill >= 2026-07-01", [b for b in all_rows if b["fill_utc"] >= "2026-07-01"]),
    ):
        n, evn, med, mean, tot, pct = stats(subset, "net_per_share")
        print(f"    {name:20s} n={n:3d} events={evn:2d} median={med:+.4f} mean={mean:+.4f} "
              f"total={tot:+.4f} = {pct:+.2f}%")

    print("\n[5] baseline variant: last print in [t0-24h, t0), same taker rule")
    if pre_candidates:
        n, evn, med, mean, tot, pct = stats(pre_candidates, "pre_net_per_share")
        print(f"    n={n} events={evn} median={med:+.4f} mean={mean:+.4f} total={tot:+.4f} "
              f"= {pct:+.2f}%")
    else:
        print("    none")

    print("\n[5b] variant: conditional intra-week model (entry rule 2, k<3), same fills")
    if cond_candidates:
        n, evn, med, mean, tot, pct = stats(cond_candidates, "net_cond")
        print(f"    n={n} events={evn} median={med:+.4f} mean={mean:+.4f} total={tot:+.4f} = {pct:+.2f}%")
        print(f"    k_seen distribution = {dict(sorted(__import__('collections').Counter(x['k_seen'] for x in cond_candidates).items()))}")
        out = HERE / "cond_trades.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cond_candidates[0].keys()))
            w.writeheader()
            w.writerows(cond_candidates)
    else:
        print("    none")

    print("\n[6] model vs market log loss (events with every bracket priced post-t0)")
    ll = [r for r in ev_rows if r["model_logloss"] and r["market_logloss"]]
    if ll:
        mo = statistics.mean(float(r["model_logloss"]) for r in ll)
        ma = statistics.mean(float(r["market_logloss"]) for r in ll)
        mb = sum(1 for r in ll if float(r["model_logloss"]) < float(r["market_logloss"]))
        print(f"    events={len(ll)} model={mo:.6f} market={ma:.6f} model_better={mb}")
    else:
        print("    none")

    print(f"\n[7] USGS own count vs resolved bracket: "
          f"{sum(1 for r in ev_rows if r['usgs_match'] == 'MATCH')}/{len(ev_rows)} MATCH")
    for ser in sorted({r["series"] for r in ev_rows}):
        rows = [r for r in ev_rows if r["series"] == ser]
        print(f"    {ser:6s} {sum(1 for r in rows if r['usgs_match'] == 'MATCH')}/{len(rows)}")

    port = {(b["event_slug"], b["bucket"]): b for b in done}
    with open(HERE / "trades.csv", "w", newline="", encoding="utf-8") as f:
        cols = [
            "event_slug", "series", "bucket", "lo", "hi", "resolved_yes",
            "model_yes", "market_yes_post", "edge", "fill_utc", "delay_h",
            "no_entry", "fee_005", "gross_per_share", "net_per_share",
            "net_per_share_fee0", "market_yes_pre", "no_entry_pre",
            "pre_net_per_share", "gamma_fee_rate", "strict_group", "settle_ts",
            "port_shares", "port_cost", "port_pnl",
        ]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for b in all_rows:
            row = dict(b)
            p = port.get((b["event_slug"], b["bucket"]))
            row["port_shares"] = p["shares"] if p else 0
            row["port_cost"] = p["cost"] if p else 0.0
            row["port_pnl"] = p["pnl_fee005"] if p else 0.0
            w.writerow(row)
    with open(HERE / "events.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ev_rows[0].keys()))
        w.writeheader()
        w.writerows(ev_rows)
    with open(HERE / "equity.csv", "w", newline="", encoding="utf-8") as f:
        f.write("date,equity_usdt,open_position_cost_usdt\n")
        for row in eq:
            f.write(f"{row[0]},{row[1]:.6f},{row[2]:.6f}\n")
    print(f"\n[8] wrote trades.csv ({len(all_rows)} signal rows, {len(done)} in portfolio), "
          f"events.csv ({len(ev_rows)} rows), "
          f"equity.csv ({len(eq)} rows)")


if __name__ == "__main__":
    main()
