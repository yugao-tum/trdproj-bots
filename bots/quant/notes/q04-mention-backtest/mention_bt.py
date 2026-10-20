#!/usr/bin/env python3
"""
Q04 reproducible backtest for Polymarket "mention" markets.

PRE-SPECIFIED CHOICES (written before looking at any backtest result)
--------------------------------------------------------------------
* Universe / sample: all CLOSED events from Gamma with tag_slug=mention-markets
  (and, as a fallback, tag_slug=mentions).  We take the 200 most recent events
  whose endDate <= run time.  This is a deliberate, deterministic sample cap so
  the run fits the time budget; counts of every stage are printed.
* Resolution: a market is used only if its final outcomePrices align with its
  outcomes and are exactly "1","0" or "0","1" (YES resolved / NO resolved).
* Entry price: CLOB prices-history for the YES token.  Primary horizon H24 =
  last observed mid price with timestamp <= endDate - 24h.  Alternative H6 =
  last observed mid price with timestamp <= endDate - 6h.  History is requested
  with interval=max&fidelity=60 (cached raw JSON); the selection code takes the
  last point on/before the cutoff and only points within a 10-day lookback
  window are eligible, so the selected point is at most ~9 days stale
  (staleness is reported).  Markets with no eligible point are excluded for
  that horizon.
* Fee: per-share taker fee = rate * price * (1-price), where price is the price
  actually paid (p for YES, 1-p for NO).  rate comes from the market's
  feeSchedule.rate if present, else feeRate, else the documented default 0.04.
* Half spread: 0.01 USDC per share (i.e. an assumed 2-cent spread) because
  historical L2 books are not public.  This is an assumption, not measured.
* P&L: buy 1 share, hold to resolution.  cash out = entry price + fee + half
  spread; payout = 1 if the bought side wins, else 0.  Net return per USDC
  risked = (payout - cash_out) / cash_out.  A trade is a "win" if net P&L > 0.
* Rules (ALL reported, no cherry-picking):
    R1  buy NO  when 0.05 <= YES price <= 0.35
    R2  buy YES when 0.65 <= YES price <= 0.95
    R3  buy NO  for all markets with 0.05 <= YES price <= 0.95
* Event-level statistics: average trades within an event first, then mean and
  t-stat = mean / (sample_sd / sqrt(n_events)) across events.
* Out-of-sample split: sort events with >=1 trade by endDate, split at the
  median event index into first half / second half.
* Calibration: 10 equal-width entry-price buckets [0,.1), ..., [.9,1].

Only keyless public GETs are used.  Raw JSON is cached under ./cache/.
Run: python3 mention_bt.py
"""

import concurrent.futures as cf
import csv
import datetime as dt
import json
import math
import os
import statistics as st
import sys
import threading
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0"
BASE = "https://gamma-api.polymarket.com/events"
CLOB = "https://clob.polymarket.com/prices-history"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
TAG_SLUGS = ["mention-markets", "mentions"]
N_RECENT_EVENTS = 200
RATE_PER_SEC = 5.0
DEFAULT_FEE_RATE = 0.04
HALF_SPREAD = 0.01
LOOKBACK_SEC = 10 * 86400
HORIZONS = [("H24", 24 * 3600), ("H6", 6 * 3600)]

os.makedirs(CACHE, exist_ok=True)
os.makedirs(os.path.join(CACHE, "clob"), exist_ok=True)

# ---------------------------------------------------------------- HTTP / cache
class RateLimiter:
    def __init__(self, rate):
        self.interval = 1.0 / rate
        self.next_time = 0.0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.monotonic()
            slot = max(now, self.next_time)
            self.next_time = slot + self.interval
        delay = slot - time.monotonic()
        if delay > 0:
            time.sleep(delay)


limiter = RateLimiter(RATE_PER_SEC)


def http_get_json(url, tries=3):
    last = None
    for attempt in range(tries):
        limiter.wait()
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (400, 404):
                return None
            time.sleep(1 + attempt)
        except Exception as e:  # network / JSON
            last = e
            time.sleep(1 + attempt)
    print("  [warn] GET failed:", url, repr(last), file=sys.stderr)
    return None


def get_events(tag, offset):
    path = os.path.join(CACHE, f"events_{tag}_{offset}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    url = f"{BASE}?tag_slug={tag}&closed=true&limit=100&offset={offset}"
    data = http_get_json(url)
    if data is None:
        data = []
    with open(path, "w") as f:
        json.dump(data, f)
    return data


def get_history(token):
    path = os.path.join(CACHE, "clob", f"{token}.json")
    if os.path.exists(path):
        with open(path) as f:
            obj = json.load(f)
            if isinstance(obj, dict) and obj.get("_error"):
                return None
            return obj.get("history", []) if isinstance(obj, dict) else obj
    # startTs/endTs are filled by caller via a side file?  Simpler: interval=max
    # is the documented endpoint, but it is large for long-lived markets.  We
    # use interval=max here to keep one cache file per token; the selection code
    # picks the point on/before the cutoff from the whole series.
    url = f"{CLOB}?market={token}&interval=max&fidelity=60"
    obj = http_get_json(url)
    if obj is None:
        with open(path, "w") as f:
            json.dump({"_error": True}, f)
        return None
    with open(path, "w") as f:
        json.dump(obj, f)
    return obj.get("history", [])


# ------------------------------------------------------------------ parsing
def parse_dt(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def as_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            v = json.loads(x)
            return v if isinstance(v, list) else []
        except Exception:
            return []
    return []


def fee_rate_of(m):
    fs = m.get("feeSchedule")
    if isinstance(fs, str):
        try:
            fs = json.loads(fs)
        except Exception:
            fs = None
    if isinstance(fs, dict) and fs.get("rate") is not None:
        try:
            return float(fs["rate"]), "feeSchedule"
        except Exception:
            pass
    if m.get("feeRate") is not None:
        try:
            return float(m["feeRate"]), "feeRate"
        except Exception:
            pass
    return DEFAULT_FEE_RATE, "default"


def resolution(m):
    outs = [str(x).strip().lower() for x in as_list(m.get("outcomes"))]
    prices = [str(x).strip() for x in as_list(m.get("outcomePrices"))]
    toks = [str(x) for x in as_list(m.get("clobTokenIds"))]
    if len(outs) != 2 or len(prices) != 2 or len(toks) != 2:
        return None
    if "yes" not in outs or "no" not in outs:
        return None
    yi, ni = outs.index("yes"), outs.index("no")
    if prices[yi] == "1" and prices[ni] == "0":
        resolved_yes = True
    elif prices[yi] == "0" and prices[ni] == "1":
        resolved_yes = False
    else:
        return None
    return {"yes_token": toks[yi], "resolved_yes": resolved_yes}


def pick_price(history, cutoff, window_start):
    """Last point with t <= cutoff and t >= window_start."""
    if not history:
        return None
    best = None
    for pt in history:
        try:
            t = float(pt["t"])
            p = float(pt["p"])
        except Exception:
            continue
        if window_start <= t <= cutoff:
            if best is None or t > best[0]:
                best = (t, p)
    if best is None:
        return None
    return best


# ------------------------------------------------------------------ metrics
def summarize(trades):
    """trades: list of dicts with ret, event_id."""
    if not trades:
        return {
            "trades": 0,
            "events": 0,
            "win_rate": float("nan"),
            "mean_ret": float("nan"),
            "event_mean_ret": float("nan"),
            "event_tstat": float("nan"),
        }
    rets = [t["ret"] for t in trades]
    by_event = {}
    for t in trades:
        by_event.setdefault(t["event_id"], []).append(t["ret"])
    emeans = [sum(v) / len(v) for v in by_event.values()]
    if len(emeans) >= 2:
        sd = st.stdev(emeans)
        tstat = (sum(emeans) / len(emeans)) / (sd / math.sqrt(len(emeans))) if sd > 0 else float("nan")
    else:
        tstat = float("nan")
    return {
        "trades": len(trades),
        "events": len(by_event),
        "win_rate": sum(1 for r in rets if r > 0) / len(rets),
        "mean_ret": sum(rets) / len(rets),
        "event_mean_ret": sum(emeans) / len(emeans),
        "event_tstat": tstat,
    }


def fmt(x, n=4):
    if x is None:
        return "NA"
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "NA"
    if isinstance(x, float):
        return f"{x:.{n}f}"
    return str(x)


# ------------------------------------------------------------------ main
def main():
    t_start = time.time()
    now = dt.datetime.now(dt.timezone.utc)

    # 1) collect events
    events = {}
    tag_counts = {}
    for tag in TAG_SLUGS:
        offset = 0
        got = 0
        while True:
            page = get_events(tag, offset)
            if not page:
                break
            got += len(page)
            for e in page:
                eid = str(e.get("id"))
                events.setdefault(eid, e)
            print(f"[collect] tag={tag} offset={offset} got={len(page)} cumulative={got}")
            if len(page) < 100:
                break
            offset += 100
        tag_counts[tag] = got

    print(f"[collect] raw event rows by tag: {tag_counts}")
    print(f"[collect] distinct events after de-dup: {len(events)}")

    # Keep only events with a valid, already-past endDate.
    dated = []
    for e in events.values():
        ed = parse_dt(e.get("endDate"))
        if ed is not None and ed <= now:
            dated.append((ed, e))
    dated.sort(key=lambda x: x[0])
    print(f"[collect] distinct events with endDate <= now ({now.isoformat()}): {len(dated)}")

    sample = dated[-N_RECENT_EVENTS:] if len(dated) > N_RECENT_EVENTS else dated
    print(f"[collect] PRE-SPECIFIED sample: {len(sample)} most recent events "
          f"({sample[0][1].get('endDate')} .. {sample[-1][1].get('endDate')})")

    # 2) flatten markets and select fetchable ones
    markets = []
    skip = {"not_closed": 0, "bad_resolution": 0, "no_yes_token": 0, "no_date": 0}
    for ed, e in sample:
        eid = str(e.get("id"))
        for m in (e.get("markets") or []):
            if not m.get("closed"):
                skip["not_closed"] += 1
                continue
            res = resolution(m)
            if res is None:
                skip["bad_resolution"] += 1
                continue
            mid = parse_dt(m.get("endDate")) or ed
            if mid is None:
                skip["no_date"] += 1
                continue
            rate, rate_src = fee_rate_of(m)
            markets.append({
                "event_id": eid,
                "event_slug": e.get("slug"),
                "event_date": mid.isoformat(),
                "event_ts": mid.timestamp(),
                "market_id": str(m.get("id")),
                "market_slug": m.get("slug"),
                "question": m.get("question"),
                "yes_token": res["yes_token"],
                "resolved_yes": res["resolved_yes"],
                "fee_rate": rate,
                "fee_src": rate_src,
                "volume": m.get("volume"),
            })
    print(f"[markets] usable closed/resolved markets in sample: {len(markets)}")
    print(f"[markets] skipped: {skip}")

    # 3) fetch CLOB history (concurrent, global 5 req/s limiter)
    print(f"[clob] fetching {len(markets)} price histories at <= {RATE_PER_SEC}/s ...")
    hist = {}

    def work(m):
        return m["yes_token"], get_history(m["yes_token"])

    done = 0
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(work, m) for m in markets]
        for fut in cf.as_completed(futs):
            tok, h = fut.result()
            hist[tok] = h
            done += 1
            if done % 250 == 0:
                el = time.time() - t_start
                print(f"[clob] {done}/{len(markets)} done, elapsed {el:.0f}s")
    n_ok = sum(1 for h in hist.values() if h)
    print(f"[clob] histories non-empty: {n_ok}/{len(markets)} "
          f"(empty/failed: {len(markets)-n_ok})")

    # 4) entry prices per horizon
    for label, secs in HORIZONS:
        for m in markets:
            cutoff = m["event_ts"] - secs
            got = pick_price(hist.get(m["yes_token"]), cutoff, m["event_ts"] - LOOKBACK_SEC)
            if got is None:
                m[f"p_{label}"] = None
                m[f"age_{label}"] = None
            else:
                m[f"p_{label}"] = got[1]
                m[f"age_{label}"] = (cutoff - got[0]) / 86400.0

    # 5) calibration + rules
    rows_cal = []
    rows_res = []
    detail = []

    rules = [
        ("R1", "NO", 0.05, 0.35),
        ("R2", "YES", 0.65, 0.95),
        ("R3", "NO", 0.05, 0.95),
    ]

    for label, _ in HORIZONS:
        subset = [m for m in markets if m.get(f"p_{label}") is not None]
        print(f"\n===== HORIZON {label}: {len(subset)} markets with an entry price "
              f"({len({m['event_id'] for m in subset})} events) =====")
        ages = [m[f"age_{label}"] for m in subset]
        if ages:
            ages_sorted = sorted(ages)
            print(f"[{label}] selected-point staleness (days before cutoff): "
                  f"median={st.median(ages):.2f} p90={ages_sorted[int(0.9*(len(ages_sorted)-1))]:.2f} "
                  f"max={max(ages):.2f}")

        # calibration
        buckets = {}
        for m in subset:
            p = m[f"p_{label}"]
            b = min(int(p * 10), 9)
            buckets.setdefault(b, []).append(m)
        print(f"\n[{label}] CALIBRATION by entry YES price")
        print(f"{'bucket':<10} {'n_mkt':>6} {'n_evt':>6} {'mean_p':>8} {'yes_rate':>9}")
        for b in range(10):
            ms = buckets.get(b, [])
            if ms:
                mp = sum(m[f"p_{label}"] for m in ms) / len(ms)
                yr = sum(1 for m in ms if m["resolved_yes"]) / len(ms)
                ne = len({m["event_id"] for m in ms})
                lo, hi = b / 10.0, (b + 1) / 10.0
            else:
                mp = yr = float("nan")
                ne = 0
                lo, hi = b / 10.0, (b + 1) / 10.0
            label_b = f"{lo:.1f}-{hi:.1f}"
            print(f"{label_b:<10} {len(ms):>6} {ne:>6} {fmt(mp,4):>8} {fmt(yr,4):>9}")
            rows_cal.append({
                "horizon": label, "bucket": label_b, "n_markets": len(ms),
                "n_events": ne, "mean_price": mp, "realized_yes_rate": yr,
            })

        # fee source counts
        src_counts = {}
        for m in subset:
            src_counts[m["fee_src"]] = src_counts.get(m["fee_src"], 0) + 1
        print(f"[{label}] fee rate sources: {src_counts}")

        # rules
        print(f"\n[{label}] RULES (fee=rate*price*(1-price), half-spread={HALF_SPREAD}, "
              f"return on cash outlay)")
        for rname, side, lo, hi in rules:
            trades = []
            for m in subset:
                p = m[f"p_{label}"]
                if not (lo - 1e-12 <= p <= hi + 1e-12):
                    continue
                if side == "YES":
                    price = p
                    win = m["resolved_yes"]
                else:
                    price = 1.0 - p
                    win = not m["resolved_yes"]
                fee = m["fee_rate"] * price * (1.0 - price)
                cash = price + fee + HALF_SPREAD
                payout = 1.0 if win else 0.0
                ret = (payout - cash) / cash
                trades.append({
                    "ret": ret, "event_id": m["event_id"],
                    "event_date": m["event_date"], "side": side,
                    "yes_price": p, "paid": price, "fee": fee,
                    "win": win, "market_id": m["market_id"],
                })
                detail.append({
                    "horizon": label, "rule": rname, "side": side,
                    "event_id": m["event_id"], "event_slug": m["event_slug"],
                    "event_date": m["event_date"], "market_id": m["market_id"],
                    "market_slug": m["market_slug"], "question": m["question"],
                    "yes_price": p, "paid": price, "fee_rate": m["fee_rate"],
                    "fee": fee, "cash_out": cash, "resolved_yes": m["resolved_yes"],
                    "win": win, "ret": ret,
                })
            overall = summarize(trades)

            # time halves by event date
            ev_dates = {}
            for t in trades:
                ev_dates[t["event_id"]] = t["event_date"]
            ev_sorted = sorted(ev_dates.items(), key=lambda kv: kv[1])
            mid = len(ev_sorted) // 2
            first_ids = {eid for eid, _ in ev_sorted[:mid]}
            second_ids = {eid for eid, _ in ev_sorted[mid:]}
            halves = [
                ("ALL", trades),
                ("FIRST_HALF", [t for t in trades if t["event_id"] in first_ids]),
                ("SECOND_HALF", [t for t in trades if t["event_id"] in second_ids]),
            ]
            print(f"  {rname} buy {side} for YES in [{lo},{hi}]")
            for split_name, ts in halves:
                s = summarize(ts)
                print(f"    {split_name:<12} trades={s['trades']:>4} events={s['events']:>4} "
                      f"win={fmt(s['win_rate'],4):>6} mean_ret/USDC={fmt(s['mean_ret'],5):>8} "
                      f"event_mean={fmt(s['event_mean_ret'],5):>8} t={fmt(s['event_tstat'],2):>6}")
                rows_res.append({
                    "horizon": label, "rule": rname, "side": side,
                    "yes_lo": lo, "yes_hi": hi, "split": split_name,
                    "trades": s["trades"], "events": s["events"],
                    "win_rate": s["win_rate"], "mean_ret_per_usdc": s["mean_ret"],
                    "event_mean_ret": s["event_mean_ret"],
                    "event_tstat": s["event_tstat"],
                })

    # 6) save
    outdir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(outdir, "calibration.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_cal[0].keys()))
        w.writeheader()
        w.writerows(rows_cal)
    with open(os.path.join(outdir, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_res[0].keys()))
        w.writeheader()
        w.writerows(rows_res)
    with open(os.path.join(outdir, "trades.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
        w.writeheader()
        w.writerows(detail)

    print(f"\n[save] calibration.csv ({len(rows_cal)} rows), "
          f"results.csv ({len(rows_res)} rows), trades.csv ({len(detail)} rows)")
    print(f"[done] elapsed {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
