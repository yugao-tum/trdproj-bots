#!/usr/bin/env python3
"""quant-020 executable-price, time-split out-of-sample backtest.

PRE-DECLARED DESIGN (written before looking at any result)
=========================================================
Endpoint / unit
  * Closed "will <company> beat quarterly EPS" events from Gamma tag_slug=earnings.
    Event filter: slug contains "earnings", or a market question contains "EPS".
    One Gamma event = one company-quarter = one independent result.  If the same
    company prefix has two events with the same endDate (GAAP vs non-GAAP), keep
    the lexicographically first slug and report the dropped duplicate.
  * Outcome = Gamma market outcomePrices: ["1","0"] -> YES, ["0","1"] -> NO.

Time split (by market endDate, set before looking at P&L)
  * Sort deduped events by (endDate, slug). The earliest 60% = DISCOVERY,
    the latest 40% = HOLDOUT.  The split index is int(0.60 * N).
  * The trading rule is FROZEN as in the entry and is not re-fitted:
    band 0.40 <= p_24h <= 0.55, buy YES.

Executable price
  * p_24h = last data-api YES trade (No trades converted with 1 - price) with
    timestamp in [endDate-72h, endDate-24h], i.e. at or before endDate-24h
    within the prior 48h.  No trade in that window -> event is unpriced.
  * entry ask = p_24h + 0.01 (pre-declared 1 cent half-spread, entry assumption).
  * Sensitivity: p_6h = last trade with timestamp in [endDate-54h, endDate-6h],
    entry ask = p_6h + 0.01.
  * Taker fee: GUIDE section 8 formula, fee/share = rate * p * (1-p), using the
    rate the entry states: 0.05 (all observed earnings markets use 0.05).
  * Net P&L per share = payout(1 or 0) - entry ask - fee/share.
  * Total per $ staked = sum(net) / sum(entry ask).

Data-api limit / truncation
  * limit=500, offset 0,500,... up to 10000 (the endpoint rejects offsets >10000).
    A market is marked truncated if offset 10000 still returns a full page whose
    oldest trade is newer than the window start.

Old price source (for comparison on the SAME in-band events)
  * p_old = last CLOB prices-history last-trade price with t <= endDate-24h in the
    [endDate-72h, endDate] window; entry ask_old = p_old + 0.01; same fee formula.

Uncertainty
  * Block bootstrap by ISO earnings week of endDate: resample week clusters with
    replacement 10,000 times, fixed seed 20261020; report 2.5/97.5 percentiles
    of the mean net P&L per share.

Verdict on HOLDOUT (entry's frozen failure criterion)
  * INSUFFICIENT if fewer than 30 holdout in-band events.
  * FAIL if median net P&L/share <= 0 OR holdout YES rate <= mean entry price.
  * PASS otherwise.

All endpoints are free and keyless.  Downloads are cached under _cache/ (gitignored).
Rerunning from cache reproduces the printed output exactly.

Usage:
    python3 q020_oos.py            # use cache when present
    python3 q020_oos.py --refresh  # ignore cache
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
import statistics
import time
from pathlib import Path

import numpy as np
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
AS_OF = "2026-10-20"
FEE_RATE = 0.05
HALF_SPREAD = 0.01
BAND_LO, BAND_HI = 0.40, 0.55
SPLIT_FRAC = 0.60
SEED = 20261020
N_BOOT = 10000
MIN_HOLDOUT = 30
REFRESH = False
UA = "quant-research-q020/1.0 (keyless public data)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def cache_file(key):
    return CACHE / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json")


def get_json(url, params=None, retries=6, pause=0.25, cache_key=None):
    """Cached JSON GET.  HTTP 400 is returned as {'_http400': text} for offset caps."""
    key = cache_key or (url + "?" + json.dumps(params or {}, sort_keys=True))
    path = cache_file(key)
    if path.exists() and not REFRESH:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink()
    last = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=60)
            if r.status_code == 400:
                return {"_http400": r.text[:300]}
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError("HTTP %s" % r.status_code)
            r.raise_for_status()
            data = r.json()
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            time.sleep(pause)
            return data
        except RuntimeError:
            last = "HTTP error"
            time.sleep(pause * (2 ** attempt))
        except Exception as exc:
            last = exc
            time.sleep(pause * (2 ** attempt))
    raise RuntimeError("GET failed: %s (%s)" % (key, last))


def parse_iso(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def epoch(value):
    return int(value.timestamp())


def load_events():
    events, offset = [], 0
    while True:
        page = get_json(
            GAMMA + "/events",
            {
                "tag_slug": "earnings",
                "limit": 100,
                "offset": offset,
                "closed": "true",
                "order": "endDate",
                "ascending": "false",
            },
        )
        if not isinstance(page, list) or not page:
            break
        events.extend(page)
        offset += 100
        if len(page) < 100:
            break
    return events


def is_earnings_event(event):
    if "earnings" in event.get("slug", "").lower():
        return True
    return any("EPS" in (m.get("question") or "") for m in event.get("markets", []))


def market_outcome(market):
    op = market.get("outcomePrices")
    if isinstance(op, str):
        op = json.loads(op)
    if not op or len(op) < 2:
        return None
    if str(op[0]) == "1":
        return 1
    if str(op[1]) == "1":
        return 0
    return None


def fetch_window_trades(condition_id, end_dt):
    """Cached trades in [end-72h, end-6h]; newest-first pagination with offset cap."""
    start_ts = epoch(end_dt - dt.timedelta(hours=72))
    stop_ts = epoch(end_dt - dt.timedelta(hours=6))
    key = "trades:%s:%d:%d" % (condition_id, start_ts, stop_ts)
    path = cache_file(key)
    if path.exists() and not REFRESH:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink()

    kept, offset, truncated, reached = [], 0, False, False
    while offset <= 10000:
        data = get_json(
            DATA_API + "/trades",
            {"market": condition_id, "limit": 500, "offset": offset},
        )
        if isinstance(data, dict) and "_http400" in data:
            truncated = not reached
            break
        if not isinstance(data, list) or not data:
            break
        for trade in data:
            ts = int(trade.get("timestamp", 0))
            if start_ts <= ts <= stop_ts:
                kept.append(trade)
        oldest = min(int(t.get("timestamp", 0)) for t in data)
        if oldest < start_ts:
            reached = True
            break
        if len(data) < 500:
            reached = True
            break
        if offset >= 10000:
            truncated = True
            break
        offset += 500

    kept.sort(key=lambda t: (int(t.get("timestamp", 0)), t.get("transactionHash", "")))
    out = {"trades": kept, "truncated": truncated, "reached_start": reached}
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    return out


def yes_price(trade):
    price = float(trade["price"])
    return 1.0 - price if trade.get("outcome") == "No" else price


def last_yes_price(trades, upper_ts, lower_ts):
    candidates = [
        t for t in trades
        if lower_ts <= int(t.get("timestamp", 0)) <= upper_ts
    ]
    if not candidates:
        return None, None
    t = candidates[-1]
    return yes_price(t), int(t["timestamp"])


def fetch_old_price(token_id, end_dt, cut_dt):
    start_ts = epoch(end_dt - dt.timedelta(hours=72))
    end_ts = epoch(end_dt)
    key = "clob:%s:%d:%d" % (token_id, start_ts, end_ts)
    path = cache_file(key)
    if path.exists() and not REFRESH:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink()
    else:
        data = get_json(
            CLOB + "/prices-history",
            {"market": token_id, "startTs": start_ts, "endTs": end_ts, "fidelity": 60},
        )
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    cut_ts = epoch(cut_dt)
    history = data.get("history", []) if isinstance(data, dict) else []
    pre = [p for p in history if int(p.get("t", 0)) <= cut_ts]
    if not pre:
        return None, None
    last = pre[-1]
    return float(last["p"]), int(last["t"])


def trade_cost(p):
    return FEE_RATE * p * (1.0 - p)


def metrics(rows, value_key="net"):
    n = len(rows)
    if n == 0:
        return None
    vals = [r[value_key] for r in rows]
    asks = [r["ask"] for r in rows]
    yes = sum(r["y"] for r in rows)
    stake = sum(asks)
    total = sum(vals)
    days = [r["capital_days"] for r in rows]
    per_dollar = total / stake if stake else float("nan")
    mean_days = sum(days) / n
    annual = per_dollar * 365.0 / mean_days if mean_days > 0 else float("nan")
    return {
        "n": n,
        "yes": yes,
        "yes_rate": yes / n,
        "mean_p": sum(r["p24"] for r in rows) / n,
        "mean_ask": sum(asks) / n,
        "median_net": statistics.median(vals),
        "mean_net": total / n,
        "total_net": total,
        "total_stake": stake,
        "per_dollar": per_dollar,
        "mean_days": mean_days,
        "annual": annual,
    }


def bootstrap_mean_ci(rows, value_key="net", n_boot=N_BOOT, seed=SEED):
    """Block bootstrap by ISO week of endDate; resample week clusters."""
    if not rows:
        return None, None
    by_week = {}
    for r in rows:
        by_week.setdefault(r["week"], []).append(r[value_key])
    weeks = sorted(by_week)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        draw = rng.integers(0, len(weeks), size=len(weeks))
        vals = []
        for j in draw:
            vals.extend(by_week[weeks[j]])
        means[i] = float(np.mean(vals))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def fmt_m(m):
    return ("n=%d YESrate=%.4f meanP=%.4f meanAsk=%.4f medianNet=%+.4f "
            "meanNet=%+.4f totalNet=%+.4f stake=%.4f perDollar=%+.4f "
            "meanDays=%.2f annual=%+.2f%%" % (
                m["n"], m["yes_rate"], m["mean_p"], m["mean_ask"],
                m["median_net"], m["mean_net"], m["total_net"], m["total_stake"],
                m["per_dollar"], m["mean_days"], m["annual"] * 100))


def main():
    global REFRESH
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    REFRESH = args.refresh

    print("quant-020 executable-price time-split OOS backtest")
    print("as_of=%s fee_rate=%.2f half_spread=%.2f band=[%.2f,%.2f] split=%.0f%% seed=%d"
          % (AS_OF, FEE_RATE, HALF_SPREAD, BAND_LO, BAND_HI,
             SPLIT_FRAC * 100, SEED))

    raw = load_events()
    earnings = [e for e in raw if is_earnings_event(e)]
    print("\n[1] enumeration")
    print("Gamma closed events (tag_slug=earnings): %d" % len(raw))
    print("earnings-beat events after slug/question filter: %d" % len(earnings))
    dates = [e["endDate"] for e in earnings]
    print("date span: %s .. %s" % (min(dates), max(dates)))
    multi = [e for e in earnings if len(e.get("markets", [])) != 1]
    print("events with != 1 market: %d" % len(multi))

    # one event = one company-quarter; drop same company+endDate duplicate
    earnings.sort(key=lambda e: (e["endDate"], e["slug"]))
    seen, deduped, dropped = set(), [], []
    for e in earnings:
        parts = e["slug"].split("-")
        company = parts[1] if parts[0] == "will" and len(parts) > 1 else parts[0]
        day = e["endDate"][:10]
        if (company, day) in seen:
            dropped.append(e["slug"])
            continue
        seen.add((company, day))
        deduped.append(e)
    print("deduped company-quarter events: %d" % len(deduped))
    if dropped:
        print("dropped same company+date duplicates: %s" % ", ".join(dropped))

    n_disc = int(len(deduped) * SPLIT_FRAC)
    split_event = deduped[n_disc]
    print("split: discovery=%d (first %d) holdout=%d; first holdout endDate=%s"
          % (n_disc, n_disc, len(deduped) - n_disc, split_event["endDate"]))
    print("discovery endDate range: %s .. %s"
          % (deduped[0]["endDate"], deduped[n_disc - 1]["endDate"]))
    print("holdout endDate range: %s .. %s"
          % (split_event["endDate"], deduped[-1]["endDate"]))

    rows, truncated_markets, no_outcome = [], [], []
    for idx, e in enumerate(deduped):
        m = e["markets"][0]
        end_dt = parse_iso(e["endDate"])
        y = market_outcome(m)
        if y is None:
            no_outcome.append(e["slug"])
        cid = m.get("conditionId") or ""
        token_ids = m.get("clobTokenIds")
        if isinstance(token_ids, str):
            token_ids = json.loads(token_ids)
        token = token_ids[0] if token_ids else None
        week = "%04d-W%02d" % end_dt.isocalendar()[:2]
        split = "discovery" if idx < n_disc else "holdout"

        tw = fetch_window_trades(cid, end_dt)
        if tw.get("truncated"):
            truncated_markets.append(e["slug"])
        trades = tw.get("trades", [])

        p24, ts24 = last_yes_price(
            trades, epoch(end_dt - dt.timedelta(hours=24)),
            epoch(end_dt - dt.timedelta(hours=72)))
        p6, ts6 = last_yes_price(
            trades, epoch(end_dt - dt.timedelta(hours=6)),
            epoch(end_dt - dt.timedelta(hours=54)))

        row = {
            "slug": e["slug"], "endDate": e["endDate"], "week": week,
            "split": split, "conditionId": cid, "y": y,
            "n_trades_window": len(trades),
            "p24": p24, "p24_ts": ts24, "p6": p6, "p6_ts": ts6,
            "ask": None, "fee": None, "net": None,
            "ask6": None, "fee6": None, "net6": None,
            "p_old": None, "ask_old": None, "fee_old": None, "net_old": None,
            "in_band": False, "in_band_old": False,
            "truncated": bool(tw.get("truncated")),
            "capital_days": None,
        }
        if p24 is not None and y is not None:
            ask = min(1.0, p24 + HALF_SPREAD)
            fee = trade_cost(ask)
            row.update(ask=ask, fee=fee, net=y - ask - fee,
                       in_band=(BAND_LO <= p24 <= BAND_HI),
                       capital_days=(end_dt - dt.datetime.fromtimestamp(ts24, dt.timezone.utc)).total_seconds() / 86400.0)
        if p6 is not None and y is not None:
            ask6 = min(1.0, p6 + HALF_SPREAD)
            fee6 = trade_cost(ask6)
            row.update(ask6=ask6, fee6=fee6, net6=y - ask6 - fee6)
        rows.append(row)
        if (idx + 1) % 100 == 0:
            print("  priced %d/%d events..." % (idx + 1, len(deduped)))

    print("events with clean outcomePrices: %d/%d" % (len(deduped) - len(no_outcome), len(deduped)))
    if no_outcome:
        print("no clean outcome: %s" % ", ".join(no_outcome))
    priced = [r for r in rows if r["p24"] is not None]
    print("events with a trade in [-72h,-24h] window: %d/%d" % (len(priced), len(rows)))
    print("events with a trade in [-54h,-6h] sensitivity window: %d/%d"
          % (sum(1 for r in rows if r["p6"] is not None), len(rows)))
    print("data-api truncated markets (offset cap): %d" % len(truncated_markets))
    if truncated_markets:
        print("  " + ", ".join(truncated_markets))

    band_priced = [r for r in rows if r["in_band"]]
    print("in-band events (0.40<=p24<=0.55): %d/%d priced = %.2f%%"
          % (len(band_priced), len(priced), 100.0 * len(band_priced) / len(priced)))
    dated = sorted(rows, key=lambda r: r["endDate"])
    max_all = max_band = 0
    for i, r in enumerate(dated):
        d0 = parse_iso(r["endDate"])
        d1 = d0 + dt.timedelta(days=14)
        win = [x for x in dated[i:] if parse_iso(x["endDate"]) < d1]
        max_all = max(max_all, len(win))
        max_band = max(max_band, sum(1 for x in win if x["in_band"]))
    print("max events in any rolling 14-day window: %d; max in-band in any 14-day window: %d"
          % (max_all, max_band))

    # old prices-history only for events in the executable band
    band_all = [r for r in rows if r["in_band"]]
    old_fail = []
    for r in band_all:
        e = next(e for e in deduped if e["slug"] == r["slug"])
        m = e["markets"][0]
        token_ids = m.get("clobTokenIds")
        if isinstance(token_ids, str):
            token_ids = json.loads(token_ids)
        token = token_ids[0] if token_ids else None
        end_dt = parse_iso(e["endDate"])
        p_old, t_old = fetch_old_price(token, end_dt, end_dt - dt.timedelta(hours=24))
        if p_old is None:
            old_fail.append(r["slug"])
            continue
        ask_old = min(1.0, p_old + HALF_SPREAD)
        fee_old = trade_cost(ask_old)
        r.update(p_old=p_old, ask_old=ask_old, fee_old=fee_old,
                 net_old=r["y"] - ask_old - fee_old,
                 in_band_old=(BAND_LO <= p_old <= BAND_HI))
    print("old prices-history available for in-band events: %d/%d"
          % (sum(1 for r in band_all if r["p_old"] is not None), len(band_all)))
    if old_fail:
        print("old price missing: %s" % ", ".join(old_fail))

    print("\n[2] results (executable data-api price, 1c half-spread, fee rate 0.05)")
    for label, subset in (
        ("DISCOVERY", [r for r in band_all if r["split"] == "discovery"]),
        ("HOLDOUT", [r for r in band_all if r["split"] == "holdout"]),
        ("POOLED", band_all),
    ):
        m = metrics(subset)
        if m is None:
            print("%s: n=0" % label)
            continue
        lo, hi = bootstrap_mean_ci(subset)
        print("%s: %s" % (label, fmt_m(m)))
        print("  bootstrap 95%% CI mean net/share (week block, %d resamples): [%+.4f, %+.4f]"
              % (N_BOOT, lo, hi))

    print("\n[2b] sensitivity: last trade before endDate-6h ([-54h,-6h])")
    for label, subset in (
        ("DISCOVERY", [r for r in band_all if r["split"] == "discovery" and r["p6"] is not None]),
        ("HOLDOUT", [r for r in band_all if r["split"] == "holdout" and r["p6"] is not None]),
        ("POOLED", [r for r in band_all if r["p6"] is not None]),
    ):
        if not subset:
            print("%s: n=0" % label)
            continue
        vals = [r["net6"] for r in subset]
        asks = [r["ask6"] for r in subset]
        ys = sum(r["y"] for r in subset)
        print("%s: n=%d YESrate=%.4f meanP6=%.4f meanAsk6=%.4f medianNet=%+.4f "
              "meanNet=%+.4f totalNet=%+.4f perDollar=%+.4f" % (
                  label, len(subset), ys / len(subset),
                  sum(r["p6"] for r in subset) / len(subset),
                  sum(asks) / len(subset), statistics.median(vals),
                  sum(vals) / len(subset), sum(vals), sum(vals) / sum(asks)))

    print("\n[2c] same in-band events, old CLOB prices-history price")
    for label, subset in (
        ("DISCOVERY", [r for r in band_all if r["split"] == "discovery" and r["p_old"] is not None]),
        ("HOLDOUT", [r for r in band_all if r["split"] == "holdout" and r["p_old"] is not None]),
        ("POOLED", [r for r in band_all if r["p_old"] is not None]),
    ):
        if not subset:
            print("%s: n=0" % label)
            continue
        m = metrics(subset, "net_old")
        lo, hi = bootstrap_mean_ci(subset, "net_old")
        print("%s: n=%d meanPold=%.4f meanAskOld=%.4f medianNet=%+.4f "
              "meanNet=%+.4f totalNet=%+.4f perDollar=%+.4f CI=[%+.4f,%+.4f]" % (
                  label, m["n"], sum(r["p_old"] for r in subset) / m["n"],
                  m["mean_ask"], m["median_net"], m["mean_net"],
                  m["total_net"], m["per_dollar"], lo, hi))
        diff = [r["ask"] - r["ask_old"] for r in subset]
        old_band = sum(1 for r in subset if r["in_band_old"])
        print("  executable ask - old ask: mean=%+.4f median=%+.4f; old price also in band: %d/%d"
              % (sum(diff) / len(diff), statistics.median(diff), old_band, len(subset)))

    print("\n[3] holdout verdict (entry frozen criterion)")
    hold = [r for r in band_all if r["split"] == "holdout"]
    if len(hold) < MIN_HOLDOUT:
        verdict = "INSUFFICIENT"
        why = "holdout in-band events %d < %d" % (len(hold), MIN_HOLDOUT)
    else:
        m = metrics(hold)
        cond_median = m["median_net"] <= 0
        cond_yes = m["yes_rate"] <= m["mean_ask"]
        verdict = "FAIL" if (cond_median or cond_yes) else "PASS"
        why = ("median net/share %+.4f %s 0; YES rate %.4f %s mean entry price %.4f"
               % (m["median_net"], "<=" if cond_median else ">",
                  m["yes_rate"], "<=" if cond_yes else ">", m["mean_ask"]))
    print("VERDICT: %s (%s)" % (verdict, why))

    out_csv = HERE / "events.csv"
    fields = [
        "slug", "endDate", "week", "split", "conditionId", "y", "n_trades_window",
        "p24", "p24_ts", "ask", "fee", "net", "in_band",
        "p6", "p6_ts", "ask6", "fee6", "net6",
        "p_old", "ask_old", "fee_old", "net_old", "in_band_old",
        "capital_days", "truncated",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fields})
    print("\nwrote %s (%d rows)" % (out_csv.name, len(rows)))
    print("done")


if __name__ == "__main__":
    main()
