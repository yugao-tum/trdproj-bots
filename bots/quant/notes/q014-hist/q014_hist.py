#!/usr/bin/env python3
"""quant-014 historical executable-price backtest (SPX close markets).

All choices below were frozen BEFORE looking at results.

DATA (free, keyless)
  * SPX daily closes: FRED SP500 CSV
      https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500
    5 random closes are cross-checked against the resolved Polymarket bracket
    (the realised close is inferred from `outcomePrices`, not from a second
    price feed; see the cross-check section of the output).
  * Gamma (rules, strikes, outcomes):
      series_id=10383  spx-daily-up-or-down          (SPX daily Up/Down)
      series_id=10603  spx-multi-strikes-weekly       (weekly "above" ladders)
      series_id=10856  sp-500-monthly-close-negrisk   (monthly close ladders)
      public-search q in {SPX, S&P 500, spx close, spx above, S&P 500 above}
  * Executable fills: data-api /trades?market=<conditionId>&limit=500&offset=N
    Outcome "No"/"Down" is mapped to YES price = 1 - price.

PRE-DECLARED UNIVERSE
  All CLOSED Polymarket SPX events whose resolution is an official SPX close:
    daily_updown    spx-up-or-down-on-<date>       (1 market/event)
    weekly_above    spx-above-on-<date>            (multi-strike ladder)
    monthly_above   spx-above-<month>[-<year>]     (multi-strike ladder)
    monthly_close   spx-close-<month> / what-will-sp-500-spx-close-at-in-<month>
                                                   (bracket ladder)
  EXCLUDED: spx-opens-up-or-down-on-<date> (same trading day as up/down, entry
  says count once), spx-hit-* ("ever touched", different model), SPY markets,
  currently-open events.  One event resolving on a trading day = one result.

PRE-DECLARED TIMING / PRICE
  Resolution timestamp = 16:00 America/New_York on the settlement trading day.
  PRIMARY decision time = resolution - 6 h (14:00 ET), the entry's p6 quote.
  SENSITIVITY decision time = previous US close (16:00 ET on prior trading day).
  Model spot = last official SPX close strictly before the decision date.
  Market price = last data-api trade in [decision - 6 h, decision].
  ask_YES = p_yes + 0.01, bid_YES = p_yes - 0.01 (per task).

PRE-DECLARED MODEL (exactly the entry)
  Zero-drift lognormal, sigma = stdev of the last 20 daily log returns ending
  at the model spot, annualised by sqrt(252); T = (# trading days from spot to
  resolution)/252; P(S_T>K)=Phi((ln(S/K)-0.5*sigma^2*T)/(sigma*sqrt(T))).
  Daily Up/Down is the entry's discrete answer P(up)=0.5000 (not 0.498x from
  the continuous formula), because the entry writes exactly 0.5000.

PRE-DECLARED RULE / COSTS
  threshold = 2 * (fee + half_spread), fee = 0.04 * p * (1-p) per share
  (Gamma feeSchedule rate 0.04, GUIDE section 8 finance taker fee), half_spread
  = 0.01. Buy YES iff p_model - ask >= threshold. Buy NO iff bid - p_model >=
  threshold. Hold to Gamma outcomePrices. Equal-close 50-50 pays 0.5.
  Event P&L/share = mean of triggered legs' net/share (equal 1 share per leg).
  net/share = payoff - execution price - fee(execution price).

PRE-DECLARED FAILURE CRITERION (quote from bots/quant/entries/
quant-014-pm-spx-lognormal-calibration.md, "失败标准（写死，事后不改）")
  1. 日频吃单子集（|p6-0.5| >= 0.10）扣费后每份净损益均值 <= 0；
  2. 阶梯腿 30 天内成交不到 50 份（容量失败，不是策略失败）；
  3. 模型 Brier 在 30 个 event 上劣于常数 0.53。
  We evaluate #1 on the daily subset (yes/no split), and #3 on all priced
  daily events.  #2 is a forward-capacity test and is not testable here.
  Verdict: FAIL if #1 mean <= 0 or (#3 holds with >=30 events); PASS if #1
  mean > 0 and the daily subset has >=30 independent ISO-week clusters;
  otherwise INSUFFICIENT.

Reproducibility: every download is cached under _cache/. Re-running from cache
must print byte-identical output (no timestamps, fixed bootstrap seed 20261020).
"""

import csv
import json
import math
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE = Path(__file__).resolve().parent
CACHE = BASE / "_cache"
TRADES_DIR = CACHE / "trades"
GAMMA_DIR = CACHE / "gamma"
SEARCH_DIR = CACHE / "search"
for d in (CACHE, TRADES_DIR, GAMMA_DIR, SEARCH_DIR):
    d.mkdir(parents=True, exist_ok=True)

ET = ZoneInfo("America/New_York")
UA = {"User-Agent": "Mozilla/5.0 (research; quant-014 historical backtest)"}
SESSION = requests.Session()
SESSION.headers.update(UA)

FEE_RATE = 0.04
HALF_SPREAD = 0.01
EDGE_MULT = 2.0
SIGMA_N = 20
BOOT_N = 10000
BOOT_SEED = 20261020
PRICE_WINDOW_H = 6
MAX_WORKERS = 8

SERIES = {10383: "daily_updown", 10603: "weekly_above", 10856: "monthly_close"}
SEARCH_QUERIES = ["SPX", "S&P 500", "spx close", "spx above", "S&P 500 above"]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
MONTH_RE = r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)"


def fetch_json(url, path, params=None, tries=8):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    last = None
    for attempt in range(tries):
        try:
            r = SESSION.get(url, params=params, timeout=60)
            if r.status_code == 200:
                data = r.json()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                time.sleep(0.08)
                return data
            last = "HTTP %s" % r.status_code
            time.sleep(1.0 + attempt)
        except Exception as exc:
            last = repr(exc)
            time.sleep(1.2 + attempt)
    raise RuntimeError("fetch failed %s %s: %s" % (url, params, last))


def fetch_text(url, path, tries=8):
    if path.exists():
        return path.read_text(encoding="utf-8")
    last = None
    for attempt in range(tries):
        try:
            r = SESSION.get(url, timeout=90)
            if r.status_code == 200 and not r.text.lstrip().startswith("<!DOCTYPE"):
                path.write_text(r.text, encoding="utf-8")
                return r.text
            last = "HTTP %s / challenge" % r.status_code
            time.sleep(1.0 + attempt)
        except Exception as exc:
            last = repr(exc)
            time.sleep(1.2 + attempt)
    raise RuntimeError("fetch failed %s: %s" % (url, last))


# --------------------------------------------------------------------------
# 1. SPX daily closes (FRED)
# --------------------------------------------------------------------------
def load_spx():
    txt = fetch_text("https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500",
                     CACHE / "fred_sp500.csv")
    dates, closes = [], {}
    for line in txt.splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 2 or parts[1] in (".", ""):
            continue
        y, m, d = (int(x) for x in parts[0].split("-"))
        try:
            v = float(parts[1])
        except ValueError:
            continue
        dates.append(date(y, m, d))
        closes[date(y, m, d)] = v
    dates.sort()
    idx = {d: i for i, d in enumerate(dates)}
    closes_list = [closes[d] for d in dates]
    rets = [math.log(closes_list[i] / closes_list[i - 1])
            for i in range(1, len(closes_list))]
    return dates, idx, closes_list, rets


def sigma_at(prev_idx, rets):
    win = rets[prev_idx - SIGMA_N:prev_idx]
    if len(win) < 2:
        return None
    return statistics.stdev(win) * math.sqrt(252.0)


def Phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_above(S, K, sig, T):
    if K is None:
        return 1.0
    if T <= 0:
        return 1.0 if S > K else 0.0
    if sig is None or sig <= 0:
        return 1.0 if S > K else 0.0
    d2 = (math.log(S / K) - 0.5 * sig * sig * T) / (sig * math.sqrt(T))
    return Phi(d2)


# --------------------------------------------------------------------------
# 2. Universe enumeration (Gamma)
# --------------------------------------------------------------------------
def load_series(sid):
    out = []
    off = 0
    while True:
        path = GAMMA_DIR / ("series_%d_%d.json" % (sid, off))
        data = fetch_json("https://gamma-api.polymarket.com/events", path,
                          {"series_id": sid, "limit": 100, "offset": off,
                           "closed": "true", "order": "endDate", "ascending": "true"})
        out.extend(data)
        if len(data) < 100 or off >= 2000:
            break
        off += 100
    return out


def load_search(q):
    out = []
    page = 1
    while page <= 12:
        path = SEARCH_DIR / ("%s_%d.json" % (re.sub(r"[^a-z0-9]+", "_", q.lower()), page))
        data = fetch_json("https://gamma-api.polymarket.com/public-search", path,
                          {"q": q, "limit_per_type": 50, "events_status": "closed",
                           "page": page})
        evs = data.get("events", [])
        out.extend(evs)
        if not data.get("pagination", {}).get("hasMore") or not evs:
            break
        page += 1
    return out


def classify(slug):
    s = slug.lower()
    if "spx-opens-up-or-down-on-" in s:
        return "daily_opens_excluded"
    if "spx-up-or-down-on-" in s:
        return "daily_updown"
    if "spx-above-on-" in s:
        return "weekly_above"
    if s.startswith("spx-hit-") or "-hit-" in s:
        return "hit_excluded"
    if s.startswith("spx-close-") or s.startswith("what-will-sp-500-spx-close-at-in-"):
        return "monthly_close"
    if re.match(r"^spx-above-", s) and re.search(MONTH_RE + r"[a-z]*-?\d{4}", s):
        return "monthly_above"
    if s.startswith("sp-500-spx-above-end-of-"):
        return "monthly_above"
    return None


def load_universe():
    raw = {}
    for sid in SERIES:
        for e in load_series(sid):
            raw[e["slug"]] = e
    for q in SEARCH_QUERIES:
        for e in load_search(q):
            raw[e["slug"]] = e
    events = []
    seen = set()
    for slug, e in raw.items():
        if slug in seen:
            continue
        seen.add(slug)
        if not e.get("closed"):
            continue
        typ = classify(slug)
        if typ in (None, "daily_opens_excluded", "hit_excluded"):
            continue
        events.append((typ, e))
    events.sort(key=lambda x: (x[0], x[1]["slug"]))
    return events


def parse_slug_date(slug, fallback_year):
    m = re.search(MONTH_RE + r"-(\d{1,2})(?:-(\d{4}))?", slug.lower())
    if not m:
        return None
    year = int(m.group(3)) if m.group(3) else fallback_year
    return date(year, MONTHS[m.group(1)], int(m.group(2)))


def month_of(text, fallback_year):
    m = re.search(MONTH_RE, text.lower())
    if not m:
        return None, None
    mon = MONTHS[m.group(1)]
    y = re.search(r"(20\d\d)", text)
    year = int(y.group(1)) if y else fallback_year
    return year, mon


def resolution_date(typ, e, dates, idx):
    slug = e["slug"]
    end = e.get("endDate", "")
    fb_year = int(end[:4]) if end[:4].isdigit() else 2026
    if typ in ("daily_updown", "weekly_above"):
        d = parse_slug_date(slug, fb_year)
        if d is None:
            return None
        if d in idx:
            return d
        j = idx.get(d)
        # nearest trading day at or before the nominal date, within 7 days
        for cand in dates[max(0, (j if j is not None else len(dates)) - 1):0:-1]:
            if cand <= d and (d - cand).days <= 7:
                return cand
        return None
    year, mon = month_of(slug, fb_year)
    if mon is None:
        year, mon = month_of(e.get("title", ""), fb_year)
    if mon is None:
        return None
    cands = [d for d in dates if d.year == year and d.month == mon]
    return cands[-1] if cands else None


def parse_range(label):
    nums = [int(x.replace(",", "")) for x in re.findall(r"[\d,]+", label or "")]
    if not nums:
        return None
    txt = (label or "").strip()
    if txt.startswith("<"):
        return (None, nums[0])
    if txt.startswith(">"):
        return (nums[0], None)
    if len(nums) >= 2:
        return (nums[0], nums[1])
    return (nums[0], None)


def yes_payoff(m):
    try:
        outs = json.loads(m.get("outcomes") or "[]")
        ps = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
    except Exception:
        return None
    if len(outs) != 2 or len(ps) != 2:
        return None
    for i, o in enumerate(outs):
        if str(o).lower() in ("yes", "up"):
            return ps[i]
    return None


def build_legs(events, dates, idx, closes, rets):
    legs = []
    for typ, e in events:
        res = resolution_date(typ, e, dates, idx)
        if res is None or res not in idx:
            legs.append({"type": typ, "event_slug": e["slug"], "skip": "no_resolution_date"})
            continue
        i = idx[res]
        prev_idx = i - 1
        if prev_idx < SIGMA_N + 1:
            legs.append({"type": typ, "event_slug": e["slug"], "skip": "no_history"})
            continue
        prev = dates[prev_idx]
        spot = closes[prev_idx]
        sig = sigma_at(prev_idx, rets)
        T = (i - prev_idx) / 252.0
        for m in e.get("markets", []):
            cid = m.get("conditionId")
            if not cid:
                continue
            y = yes_payoff(m)
            if y is None:
                continue
            label = m.get("groupItemTitle") or m.get("slug") or ""
            if typ == "daily_updown":
                p = 0.5
                kind = "binary"
                lo, hi = None, None
            else:
                rng = parse_range(label)
                if rng is None:
                    legs.append({"type": typ, "event_slug": e["slug"],
                                 "market_slug": m.get("slug"), "skip": "no_strike"})
                    continue
                lo, hi = rng
                p = p_above(spot, lo, sig, T) - p_above(spot, hi, sig, T)
                kind = "above" if hi is None else "bracket"
            legs.append({
                "type": typ, "event_slug": e["slug"], "market_slug": m.get("slug"),
                "condition_id": cid, "group": label, "kind": kind, "lo": lo, "hi": hi,
                "resolution_date": res, "iso_week": "%d-W%02d" % res.isocalendar()[:2],
                "prev_date": prev, "spot": spot, "sigma": sig, "T": T,
                "p_model": max(0.0, min(1.0, p)), "outcome_yes": y,
                "closed": bool(m.get("closed")), "skip": None,
            })
    return legs


# --------------------------------------------------------------------------
# 3. Executable fills (data-api)
# --------------------------------------------------------------------------
def load_trades(cid):
    path = TRADES_DIR / ("%s.json" % cid)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    out = []
    off = 0
    while off < 20000:
        try:
            r = SESSION.get("https://data-api.polymarket.com/trades",
                            params={"market": cid, "limit": 500, "offset": off},
                            timeout=60)
            if r.status_code != 200:
                time.sleep(1.0)
                continue
            d = r.json()
        except Exception:
            time.sleep(1.2)
            continue
        out.extend(d)
        if len(d) < 500:
            break
        off += 500
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    return out


def yes_price_of_trade(t):
    try:
        p = float(t["price"])
    except Exception:
        return None
    o = str(t.get("outcome", "")).lower()
    if o in ("yes", "up"):
        return p
    if o in ("no", "down"):
        return 1.0 - p
    return None


def last_price(leg, trades, decision_ts):
    lo = decision_ts - PRICE_WINDOW_H * 3600
    best = None
    n = 0
    for t in trades:
        ts = t.get("timestamp")
        if ts is None or ts < lo or ts > decision_ts:
            continue
        p = yes_price_of_trade(t)
        if p is None:
            continue
        n += 1
        if best is None or ts >= best[0]:
            best = (ts, p, float(t.get("size") or 0), t.get("side"), t.get("outcome"))
    if best is None:
        return None
    return {"p_yes": max(0.001, min(0.999, best[1])), "n": n,
            "ts": best[0], "size": best[2], "side": best[3], "outcome": best[4]}


def evaluate(leg, quote):
    p = leg["p_model"]
    m = quote["p_yes"]
    ask = min(0.999, m + HALF_SPREAD)
    bid = max(0.001, m - HALF_SPREAD)
    no_cost = 1.0 - bid
    fee_yes = FEE_RATE * ask * (1.0 - ask)
    fee_no = FEE_RATE * no_cost * (1.0 - no_cost)
    thr_yes = EDGE_MULT * (fee_yes + HALF_SPREAD)
    thr_no = EDGE_MULT * (fee_no + HALF_SPREAD)
    edge_yes = p - ask
    edge_no = bid - p
    side = None
    if edge_yes >= thr_yes and edge_yes >= edge_no:
        side = "YES"
    elif edge_no >= thr_no:
        side = "NO"
    if side == "YES":
        exec_p, fee = ask, fee_yes
        payoff = leg["outcome_yes"]
        edge, thr = edge_yes, thr_yes
    elif side == "NO":
        exec_p, fee = no_cost, fee_no
        payoff = 1.0 - leg["outcome_yes"]
        edge, thr = edge_no, thr_no
    else:
        return {"side": None, "p_market": m, "ask": ask, "bid": bid,
                "exec_price": None, "fee": None, "payoff": None,
                "net": None, "edge": max(edge_yes, edge_no),
                "threshold": min(thr_yes, thr_no), "triggered": False}
    net = payoff - exec_p - fee
    return {"side": side, "p_market": m, "ask": ask, "bid": bid,
            "exec_price": exec_p, "fee": fee, "payoff": payoff, "net": net,
            "edge": edge, "threshold": thr, "triggered": True}


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def median(xs):
    return statistics.median(xs) if xs else float("nan")


def pct(xs, q):
    if not xs:
        return float("nan")
    s = sorted(xs)
    k = (len(s) - 1) * q / 100.0
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def brier(ps, ys):
    return mean([(p - y) ** 2 for p, y in zip(ps, ys)])


def logloss(ps, ys):
    eps = 1e-9
    return -mean([math.log(max(eps, min(1 - eps, p if y else 1 - p)))
                  for p, y in zip(ps, ys)])


def boot_ci(vals_by_week):
    weeks = sorted(vals_by_week)
    if len(weeks) < 2:
        return (float("nan"), float("nan"), len(weeks))
    rng = random.Random(BOOT_SEED)
    k = len(weeks)
    means = []
    for _ in range(BOOT_N):
        idxs = rng.choices(range(k), k=k)
        pool = []
        for j in idxs:
            pool.extend(vals_by_week[weeks[j]])
        means.append(sum(pool) / len(pool))
    return (pct(means, 2.5), pct(means, 97.5), len(weeks))


def event_nets(rows):
    """One result per event: mean net/share over triggered legs."""
    by = defaultdict(list)
    for r in rows:
        if r.get("primary") and r["primary"].get("triggered"):
            by[r["event_slug"]].append(r["primary"]["net"])
    return {k: mean(v) for k, v in by.items()}


def describe(name, ev_nets):
    vals = list(ev_nets.values())
    weeks = defaultdict(list)
    for slug, v in ev_nets.items():
        weeks[EVENT_WEEK[slug]].append(v)
    lo, hi, nw = boot_ci(weeks)
    print("%-34s events=%4d  mean=%+.5f  median=%+.5f  hit=%.3f  "
          "weeks=%3d  boot95=[%+.5f,%+.5f]"
          % (name, len(vals), mean(vals), median(vals),
             sum(1 for v in vals if v > 0) / len(vals) if vals else float("nan"),
             nw, lo, hi))
    return {"n": len(vals), "mean": mean(vals), "median": median(vals),
            "hit": sum(1 for v in vals if v > 0) / len(vals) if vals else float("nan"),
            "weeks": nw, "ci": (lo, hi)}


EVENT_WEEK = {}


def run_crosscheck(rows, dates, idx, closes):
    rng = random.Random(BOOT_SEED)
    daily, ladder, seen = [], [], set()
    for l in rows:
        if l["event_slug"] in seen:
            continue
        seen.add(l["event_slug"])
        (daily if l["type"] == "daily_updown" else ladder).append(l)
    rng.shuffle(daily)
    rng.shuffle(ladder)
    picks = daily[:3] + ladder[:2]
    print("\n=== SPX SOURCE CROSS-CHECK (5 random resolution dates) ===")
    print("FRED close vs Polymarket outcomePrices-implied settlement")
    print("%-46s %-12s %10s %10s %8s %8s %s"
          % ("event", "market", "FRED close", "prev close", "mkt YES", "implied", "match"))
    ok = 0
    for l in picks:
        res_c = closes[idx[l["resolution_date"]]]
        if l["type"] == "daily_updown":
            exp = 1.0 if res_c > l["spot"] else (0.0 if res_c < l["spot"] else 0.5)
        elif l["kind"] == "above":
            exp = 1.0 if res_c > l["lo"] else 0.0
        elif l["lo"] is None:
            exp = 1.0 if res_c < l["hi"] else 0.0
        elif l["hi"] is None:
            exp = 1.0 if res_c > l["lo"] else 0.0
        else:
            exp = 1.0 if l["lo"] <= res_c < l["hi"] else 0.0
        match = abs(exp - l["outcome_yes"]) < 1e-9
        ok += int(match)
        print("%-46s %-12s %10.2f %10.2f %8.3f %8.3f %s"
              % (l["event_slug"][:46], l.get("group", "")[:12], res_c, l["spot"],
                 l["outcome_yes"], exp, "OK" if match else "MISMATCH"))
    print("matched %d/5" % ok)


def main():
    dates, idx, closes, rets = load_spx()
    events = load_universe()
    print("=" * 78)
    print("quant-014 historical executable-price backtest")
    print("=" * 78)
    print("SPX closes: FRED SP500 CSV, %d trading days %s..%s"
          % (len(dates), dates[0], dates[-1]))
    print("Universe queries: series 10383/10603/10856 + public-search %s"
          % ", ".join(SEARCH_QUERIES))

    typ_counts = Counter(t for t, _ in events)
    print("\n=== ENUMERATED CLOSED EVENTS ===")
    for t in ("daily_updown", "weekly_above", "monthly_above", "monthly_close"):
        evs = [e for tt, e in events if tt == t]
        if evs:
            ds = sorted(e.get("endDate", "")[:10] for e in evs)
            print("%-16s events=%4d  span=%s..%s" % (t, len(evs), ds[0], ds[-1]))
        else:
            print("%-16s events=%4d" % (t, 0))
    ex = Counter(classify(s) for s in [])
    print("excluded by design: spx-opens-up-or-down (same day as up/down), "
          "spx-hit-* (ever-touched), SPY, open events")

    legs = build_legs(events, dates, idx, closes, rets)
    bad = [l for l in legs if l.get("skip")]
    legs = [l for l in legs if not l.get("skip")]
    print("\nlegs built=%d  unusable=%d (no date/strike/outcome)" % (len(legs), len(bad)))

    # Fetch all trades concurrently.
    cids = sorted({l["condition_id"] for l in legs})
    print("fetching data-api trades for %d conditionIds (cache-first)..." % len(cids))
    trades = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(load_trades, cid): cid for cid in cids}
        done = 0
        for fut in as_completed(futs):
            cid = futs[fut]
            try:
                trades[cid] = fut.result()
            except Exception:
                trades[cid] = []
            done += 1
            if done % 50 == 0:
                print("  ... %d/%d" % (done, len(cids)))

    res_ts = {}
    prev_close_ts = {}
    for d in dates:
        res_ts[d] = datetime(d.year, d.month, d.day, 16, 0, tzinfo=ET).timestamp()
        prev_close_ts[d] = res_ts[d]

    # Primary and sensitivity quotes.
    rows = []
    for l in legs:
        EVENT_WEEK[l["event_slug"]] = l["iso_week"]
        cid = l["condition_id"]
        tr = trades.get(cid, [])
        rdec = res_ts[l["resolution_date"]]
        dprim = rdec - PRICE_WINDOW_H * 3600
        qprim = last_price(l, tr, dprim)
        qsens = last_price(l, tr, prev_close_ts[l["prev_date"]])
        if qprim is None:
            l["skip"] = "no_trade_in_6h"
            l["primary"] = None
            l["sens"] = None
            l["n_prim"] = 0
            l["n_sens"] = 0
            continue
        l["primary"] = evaluate(l, qprim)
        l["sens"] = evaluate(l, qsens) if qsens else None
        l["n_prim"] = qprim["n"]
        l["n_sens"] = qsens["n"] if qsens else 0
        l["prim_price"] = qprim["p_yes"]
        l["prim_size"] = qprim["size"]
        l["sens_price"] = qsens["p_yes"] if qsens else None
        rows.append(l)

    # ---------------- funnel ----------------
    print("\n=== SAMPLE FUNNEL (primary decision = close-6h) ===")
    all_ev = sorted({l["event_slug"] for l in legs} | {b["event_slug"] for b in bad})
    priced_ev = {l["event_slug"] for l in rows}
    trig_ev = {l["event_slug"] for l in rows if l["primary"]["triggered"]}
    skip_reasons = Counter(l["skip"] for l in legs if l.get("skip"))
    print("events enumerated (closed, modelable types) = %d" % len(all_ev))
    print("legs (event x market)                         = %d" % (len(legs) + len(bad)))
    print("legs with a fill in the 6h window             = %d" % len(rows))
    print("events with >=1 priced leg                    = %d" % len(priced_ev))
    print("events with >=1 triggered leg                 = %d" % len(trig_ev))
    print("legs triggered                                = %d" % sum(1 for l in rows if l["primary"]["triggered"]))
    print("skip reasons (legs): %s" % (dict(sorted(skip_reasons.items())) or "{}"))

    print("\nper type:")
    print("%-16s %7s %7s %7s %7s" % ("type", "events", "priced", "trigEv", "trigLegs"))
    for t in ("daily_updown", "weekly_above", "monthly_above", "monthly_close"):
        evs = {l["event_slug"] for l in legs if l["type"] == t}
        pr = {l["event_slug"] for l in rows if l["type"] == t}
        tr_ev = {l["event_slug"] for l in rows if l["type"] == t and l["primary"]["triggered"]}
        tr_lg = sum(1 for l in rows if l["type"] == t and l["primary"]["triggered"])
        print("%-16s %7d %7d %7d %7d" % (t, len(evs), len(pr), len(tr_ev), tr_lg))

    trig = [l for l in rows if l["primary"]["triggered"]]
    print("\nYES/NO split (triggered legs): YES=%d  NO=%d"
          % (sum(1 for l in trig if l["primary"]["side"] == "YES"),
             sum(1 for l in trig if l["primary"]["side"] == "NO")))

    run_crosscheck(rows, dates, idx, closes)

    # ---------------- results ----------------
    print("\n=== PRIMARY RESULTS (decision = resolution close - 6h) ===")
    daily = [l for l in rows if l["type"] == "daily_updown"]
    daily_trig = [l for l in daily if l["primary"]["triggered"]]
    daily_sub = [l for l in daily if abs(l["prim_price"] - 0.5) >= 0.10]

    def leg_stats(name, ls, which="primary"):
        nets = [l[which]["net"] for l in ls]
        costs = [l[which]["exec_price"] for l in ls]
        print("%-34s legs=%4d  mean=%+.5f  median=%+.5f  hit=%.3f  "
              "total_net=%+.2f  per_$1=%.4f"
              % (name, len(ls), mean(nets), median(nets),
                 sum(1 for n in nets if n > 0) / len(nets) if nets else float("nan"),
                 sum(nets), sum(nets) / sum(costs) if costs else float("nan")))

    leg_stats("all triggered legs", trig)

    daily_sub_nets = []
    daily_sub_gross = []
    for l in daily_sub:
        p = l["prim_price"]
        side_yes = p < 0.5
        exec_p = (p + HALF_SPREAD) if side_yes else (1 - p + HALF_SPREAD)
        fee = FEE_RATE * exec_p * (1 - exec_p)
        payoff = l["outcome_yes"] if side_yes else 1 - l["outcome_yes"]
        mid_cost = p if side_yes else 1 - p
        daily_sub_nets.append(payoff - exec_p - fee)
        daily_sub_gross.append(payoff - mid_cost)
    print("%-34s legs=%4d  gross_mean=%+.5f  net_mean=%+.5f  net_median=%+.5f  hit=%.3f"
          % ("daily subset |p6-0.5|>=0.10 FADE", len(daily_sub), mean(daily_sub_gross),
             mean(daily_sub_nets), median(daily_sub_nets),
             sum(1 for n in daily_sub_nets if n > 0) / len(daily_sub_nets)
             if daily_sub_nets else float("nan")))

    # entry's original test direction: buy the side the market price is on.
    follow_nets, follow_gross = [], []
    for l in daily_sub:
        p = l["prim_price"]
        side_yes = p > 0.5
        exec_p = (p + HALF_SPREAD) if side_yes else (1 - p + HALF_SPREAD)
        fee = FEE_RATE * exec_p * (1 - exec_p)
        payoff = l["outcome_yes"] if side_yes else 1 - l["outcome_yes"]
        mid_cost = p if side_yes else 1 - p
        follow_nets.append(payoff - exec_p - fee)
        follow_gross.append(payoff - mid_cost)
    print("%-34s legs=%4d  gross_mean=%+.5f  net_mean=%+.5f  net_median=%+.5f  hit=%.3f"
          % ("daily subset |p6-0.5|>=0.10 FOLLOW", len(daily_sub), mean(follow_gross),
             mean(follow_nets), median(follow_nets),
             sum(1 for n in follow_nets if n > 0) / len(follow_nets)
             if follow_nets else float("nan")))

    sub_costs = []
    for l in daily_sub:
        p = l["prim_price"]
        sub_costs.append((p + HALF_SPREAD) if p < 0.5 else (1 - p + HALF_SPREAD))
    print("%-34s total_net=%+.2f  per_$1=%.4f"
          % ("daily subset FADE", sum(daily_sub_nets),
             sum(daily_sub_nets) / sum(sub_costs) if sub_costs else float("nan")))

    for t in ("daily_updown", "weekly_above", "monthly_above", "monthly_close"):
        leg_stats("  triggered legs / %s" % t,
                  [l for l in trig if l["type"] == t])

    # per-event results
    print("\nper-event (mean net/share across triggered legs of the event):")
    stats_all = describe("all triggered events", event_nets(trig))
    stats_daily = describe("daily triggered events", event_nets(daily_trig))
    sub_rows = [l for l in daily_sub if l["primary"]["triggered"]]
    # subset nets differ from rule net only in that side is forced away from 0.5;
    # rule side is the same, so reuse evaluate() nets.
    stats_sub = describe("daily subset events", event_nets(sub_rows))

    # sensitivity
    sens_rows = [l for l in rows if l["sens"] and l["sens"]["triggered"]]
    sens_daily = [l for l in sens_rows if l["type"] == "daily_updown"]
    print("\n=== SENSITIVITY (decision = previous US close) ===")
    print("priced legs=%d  triggered=%d" % (sum(1 for l in rows if l["sens"]), len(sens_rows)))
    leg_stats("sensitivity triggered legs", sens_rows, "sens")
    if sens_daily:
        describe("sensitivity daily events", event_nets(sens_daily))

    # calibration
    print("\n=== CALIBRATION / BRIER (primary market quote) ===")
    dys = [l["outcome_yes"] for l in daily]
    dpm = [l["p_model"] for l in daily]
    dmm = [l["prim_price"] for l in daily]
    print("daily priced events = %d" % len(daily))
    print("Brier  model P(up)=0.5      = %.5f" % brier(dpm, dys))
    print("Brier  constant 0.50        = %.5f" % brier([0.5] * len(dys), dys))
    print("Brier  constant 0.53        = %.5f" % brier([0.53] * len(dys), dys))
    print("Brier  market p6            = %.5f" % brier(dmm, dys))
    print("logloss model P(up)=0.5     = %.5f" % logloss(dpm, dys))
    print("logloss constant 0.53       = %.5f" % logloss([0.53] * len(dys), dys))
    print("logloss market p6           = %.5f" % logloss(dmm, dys))
    all_ys = [l["outcome_yes"] for l in rows]
    print("all priced legs=%d  Brier model=%.5f  market=%.5f"
          % (len(rows), brier([l["p_model"] for l in rows], all_ys),
             brier([l["prim_price"] for l in rows], all_ys)))

    # ---------------- verdict ----------------
    print("\n=== VERDICT (frozen criterion) ===")
    print("criterion #1: daily taker subset |p6-0.5|>=0.10, net mean <= 0 -> FAIL")
    print("criterion #3: model Brier worse than constant 0.53 on >=30 events -> FAIL")
    print("subset n=%d  net_mean=%+.5f  net_median=%+.5f  weeks=%d"
          % (len(daily_sub_nets), mean(daily_sub_nets), median(daily_sub_nets),
             stats_sub["weeks"]))
    print("model Brier=%.5f vs constant 0.53=%.5f on %d events"
          % (brier(dpm, dys), brier([0.53] * len(dys), dys), len(daily)))
    crit1 = mean(daily_sub_nets) <= 0 if daily_sub_nets else None
    crit3 = (brier(dpm, dys) > brier([0.53] * len(dys), dys)) and len(daily) >= 30
    if crit1:
        verdict = "FAIL"
    elif crit3:
        verdict = "FAIL"
    elif daily_sub_nets and stats_sub["weeks"] >= 30:
        verdict = "PASS"
    else:
        verdict = "INSUFFICIENT"
    print("VERDICT: %s" % verdict)

    # ---------------- write events.csv ----------------
    out_csv = BASE / "events.csv"
    cols = ["event_type", "event_slug", "resolution_date", "iso_week", "market_slug",
            "condition_id", "group", "kind", "spot", "sigma", "T", "p_model",
            "p_market_yes", "ask", "bid", "side", "exec_price", "fee", "outcome_yes",
            "payoff", "net_per_share", "triggered", "edge", "threshold",
            "n_trades_6h", "last_trade_size", "sens_p_market", "sens_net",
            "sens_triggered", "skip_reason"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for l in legs:
            if l.get("primary") is None:
                w.writerow([l["type"], l["event_slug"], l["resolution_date"], l["iso_week"],
                            l["market_slug"], l["condition_id"], l["group"], l["kind"],
                            "%.2f" % l["spot"], "%.4f" % l["sigma"], "%.6f" % l["T"],
                            "%.6f" % l["p_model"], "", "", "", "", "", "", "%.3f" % l["outcome_yes"],
                            "", "", "0", "", "", l.get("n_prim", 0), "", "", "", "0", l["skip"]])
                continue
            p = l["primary"]
            s = l["sens"] or {}
            w.writerow([l["type"], l["event_slug"], l["resolution_date"], l["iso_week"],
                        l["market_slug"], l["condition_id"], l["group"], l["kind"],
                        "%.2f" % l["spot"], "%.4f" % l["sigma"], "%.6f" % l["T"],
                        "%.6f" % l["p_model"], "%.6f" % p["p_market"],
                        "%.4f" % p["ask"], "%.4f" % p["bid"], p["side"] or "",
                        "" if p["exec_price"] is None else "%.4f" % p["exec_price"],
                        "" if p["fee"] is None else "%.6f" % p["fee"],
                        "%.3f" % l["outcome_yes"],
                        "" if p["payoff"] is None else "%.3f" % p["payoff"],
                        "" if p["net"] is None else "%.5f" % p["net"],
                        "1" if p["triggered"] else "0", "%.5f" % p["edge"],
                        "%.5f" % p["threshold"], l["n_prim"], "%.2f" % l["prim_size"],
                        "" if l["sens_price"] is None else "%.6f" % l["sens_price"],
                        "" if s.get("net") is None else "%.5f" % s["net"],
                        "1" if s.get("triggered") else "0", ""])
    print("\nwrote %s (%d legs)" % (out_csv.name, len(legs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
