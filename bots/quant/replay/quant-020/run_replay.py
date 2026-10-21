#!/usr/bin/env python3
"""quant-020 round-2 replay: historical TRADABLE-price backtest, net of fees.

Rule (frozen in the entry, not re-fitted here)
  Universe: Polymarket "<company> beat quarterly EPS?" events.
  Band: 0.40 <= p_24h <= 0.55  ->  taker BUY YES, hold to settlement.
  p_24h is the frozen 2026-10-20 data-api snapshot (last YES trade in
  [endDate-72h, endDate-24h]); events_frozen.csv is the derived snapshot.

Tradable entry price (what this replay adds)
  The last ask-side data-api print in [endDate-72h, endDate-24h]:
    BUY Yes @ p        -> YES-equivalent ask = p
    SELL No @ p        -> YES-equivalent ask = 1 - p
  This is an observed taker fill, not CLOB prices-history and not "last
  price + 1 cent".  If there is no ask-side print the event is unpriced.

Costs
  Taker fee per share = rate * ask * (1 - ask), rate = 0.05 primary
  (0.04 and 0.00 as sensitivity).  No other cost is added because the fill
  price is an observed ask-side print (the half-spread is inside it).
  Net/share = payout(1/0) - ask - fee.

Splits / uncertainty
  DISCOVERY/HOLDOUT: the 60/40 time split copied from the frozen snapshot.
  STRICT_OOS: drop every event in the latest-250-endDate selection window
  that was used to choose the 0.40-0.55 band (cutoff = 250th newest endDate).
  ISO-week block bootstrap, 10,000 draws, seed 20261020.

All endpoints are free and keyless.  Downloads are cached under _cache/
(gitignored).  Run:
    python3 run_replay.py
"""
import collections
import csv
import datetime as dt
import json
import statistics
import time
from pathlib import Path

import numpy as np
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
CACHE.mkdir(exist_ok=True)
DATA_API = "https://data-api.polymarket.com"
EVENTS = HERE / "events_frozen.csv"
FEE = 0.05
SEED = 20261020
NBOOT = 10000
SELECTION_N = 250
STAKE = 20.0          # USDT per event for the contribution / drawdown arithmetic
ACCOUNT = 5000.0
S = requests.Session()
S.headers.update({"User-Agent": "quant-research-quant-020-replay/1.0 (keyless)"})


def get_trades(cid, lo, hi):
    key = CACHE / ("trades_%s_%d_%d.json" % (cid, lo, hi))
    if key.exists():
        return json.loads(key.read_text())
    kept, off, reached, truncated = [], 0, False, False
    while off <= 10000:
        data = None
        for attempt in range(5):
            try:
                r = S.get(DATA_API + "/trades",
                          params={"market": cid, "limit": 500, "offset": off}, timeout=60)
                if r.status_code == 400:
                    data = {"_http400": r.text[:200]}
                else:
                    r.raise_for_status()
                    data = r.json()
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(1.0 * (attempt + 1))
        if isinstance(data, dict):
            truncated = not reached
            break
        if not data:
            reached = True
            break
        for t in data:
            ts = int(t.get("timestamp", 0))
            if lo <= ts <= hi:
                kept.append(t)
        oldest = min(int(t.get("timestamp", 0)) for t in data)
        if oldest < lo or len(data) < 500:
            reached = True
            break
        if off >= 10000:
            truncated = True
            break
        off += 500
    kept.sort(key=lambda t: (int(t.get("timestamp", 0)), t.get("transactionHash", "")))
    out = {"trades": kept, "truncated": truncated, "reached_start": reached}
    key.write_text(json.dumps(out, separators=(",", ":")))
    return out


def ask_price(t):
    if t.get("outcome") == "Yes" and t.get("side") == "BUY":
        return float(t["price"])
    if t.get("outcome") == "No" and t.get("side") == "SELL":
        return 1.0 - float(t["price"])
    return None


def bid_price(t):
    if t.get("outcome") == "Yes" and t.get("side") == "SELL":
        return float(t["price"])
    if t.get("outcome") == "No" and t.get("side") == "BUY":
        return 1.0 - float(t["price"])
    return None


def iso_week(s):
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return "%04d-W%02d" % d.isocalendar()[:2]


def boot(sub, key):
    weeks = sorted({r["week"] for r in sub})
    groups = {w: [r[key] for r in sub if r["week"] == w] for w in weeks}
    rng = np.random.default_rng(SEED)
    means = np.empty(NBOOT)
    for i in range(NBOOT):
        pick = rng.integers(0, len(weeks), size=len(weeks))
        vv = []
        for j in pick:
            vv.extend(groups[weeks[j]])
        means[i] = float(np.mean(vv))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def report(label, sub, fee=FEE):
    if not sub:
        print("%-36s n=0" % label)
        return None
    nets = [r["y"] - r["ask"] - fee * r["ask"] * (1 - r["ask"]) for r in sub]
    asks = [r["ask"] for r in sub]
    stake = sum(asks)
    total = sum(nets)
    s = dict(n=len(sub), yes=sum(r["y"] for r in sub) / len(sub),
             meanAsk=stake / len(sub), medianNet=statistics.median(nets),
             meanNet=total / len(nets), total=total, perDollar=total / stake)
    tmp = [dict(r, net=n) for r, n in zip(sub, nets)]
    s["ci"] = boot(tmp, "net")
    print("%-36s n=%3d YES=%.4f meanAsk=%.4f medianNet=%+.4f meanNet=%+.4f total=%+.4f perDollar=%+.4f CI=[%+.4f,%+.4f]"
          % (label, s["n"], s["yes"], s["meanAsk"], s["medianNet"], s["meanNet"],
             s["total"], s["perDollar"], s["ci"][0], s["ci"][1]))
    return s


rows = list(csv.DictReader(EVENTS.open()))
for r in rows:
    r["endDate_dt"] = dt.datetime.fromisoformat(r["endDate"].replace("Z", "+00:00"))
rows.sort(key=lambda r: (r["endDate_dt"], r["slug"]))
cutoff = sorted((r["endDate_dt"] for r in rows), reverse=True)[SELECTION_N - 1]
band = [r for r in rows if r["in_band"].lower() == "true"]
print("quant-020 replay: observed ask-side fills, hold to settlement")
print("frozen universe: %d events; in-band (0.40<=p24<=0.55): %d" % (len(rows), len(band)))
print("selection-window cutoff (250th newest endDate): %s" % cutoff.isoformat())
print("fee=%.2f primary; stake=%.0f USDT/event; account=%.0f USDT" % (FEE, STAKE, ACCOUNT))

out, trunc, p24_mismatch = [], 0, 0
for i, r in enumerate(band, 1):
    end = r["endDate_dt"]
    lo = int((end - dt.timedelta(hours=72)).timestamp())
    hi = int((end - dt.timedelta(hours=24)).timestamp())
    tw = get_trades(r["conditionId"], lo, hi)
    trades = tw["trades"]
    trunc += int(tw["truncated"])
    last_ask = next((t for t in reversed(trades) if ask_price(t) is not None), None)
    last_bid = next((t for t in reversed(trades) if bid_price(t) is not None), None)
    last_yes = next((t for t in reversed(trades) if t.get("outcome") in ("Yes", "No")), None)
    yes_eq = (float(last_yes["price"]) if last_yes and last_yes.get("outcome") == "Yes"
              else (1.0 - float(last_yes["price"]) if last_yes else None))
    ask = ask_price(last_ask) if last_ask else None
    bid = bid_price(last_bid) if last_bid else None
    if last_yes and r["p24"]:
        if abs(yes_eq - float(r["p24"])) > 1e-9:
            p24_mismatch += 1
    out.append(dict(
        slug=r["slug"], endDate=r["endDate"], endDate_dt=end, week=iso_week(r["endDate"]),
        split=r["split"], y=int(r["y"]), p24=float(r["p24"]),
        in_band_old=r["in_band_old"].lower() == "true",
        n_trades=len(trades),
        ask=ask, ask_ts=int(last_ask["timestamp"]) if last_ask else None,
        ask_size=float(last_ask["size"]) if last_ask else None,
        bid=bid,
        spread=(ask - bid) if (ask is not None and bid is not None) else None,
        strict_oos=end < cutoff,
        truncated=tw["truncated"],
    ))
    if i % 20 == 0:
        print("  fetched %d/%d..." % (i, len(band)))

print("observed ask-side print: %d/%d; no ask print: %d"
      % (sum(1 for r in out if r["ask"] is not None), len(out), sum(1 for r in out if r["ask"] is None)))
print("data-api truncated markets: %d" % trunc)
print("refetched last-YES price equals frozen p24: %d/%d (mismatch %d)"
      % (len(out) - p24_mismatch, len(out), p24_mismatch))

obs = [r for r in out if r["ask"] is not None]
print("\n[1] PRIMARY: last observed ask-side print, fee 0.05")
res = {}
res["discovery"] = report("DISCOVERY", [r for r in obs if r["split"] == "discovery"])
res["holdout"] = report("HOLDOUT", [r for r in obs if r["split"] == "holdout"])
res["pooled"] = report("POOLED", obs)
res["strict"] = report("STRICT_OOS (outside selection window)", [r for r in obs if r["strict_oos"]])
res["selection"] = report("SELECTION (inside selection window)", [r for r in obs if not r["strict_oos"]])

print("\n[2] Robustness: band flag from original CLOB p_24h (in_band_old)")
old = [r for r in obs if r["in_band_old"]]
res["strict_old"] = report("STRICT_OOS old-band", [r for r in old if r["strict_oos"]])

print("\n[3] Fee sensitivity on the observed-ask sample")
for fee in (0.05, 0.04, 0.00):
    report("POOLED fee=%.2f" % fee, obs, fee)
    report("STRICT_OOS fee=%.2f" % fee, [r for r in obs if r["strict_oos"]], fee)

print("\n[4] Entry-price assumption check: last YES print + 1c (q020-oos style)")
plus1 = []
for r in obs:
    a = min(1.0, r["p24"] + 0.01)
    plus1.append(dict(r, ask=a))
res["strict_plus1c"] = report("STRICT_OOS last-YES+1c", [r for r in plus1 if r["strict_oos"]])

print("\n[5] Effective spread and print size")
spreads = [r["spread"] for r in obs if r["spread"] is not None]
notionals = [r["ask"] * r["ask_size"] for r in obs if r["ask_size"]]
print("observed ask-bid: n=%d mean=%+.4f median=%+.4f" % (
    len(spreads), sum(spreads) / len(spreads), statistics.median(spreads)))
print("ask-print notional: median=%.1f USDT; >=200 USDT: %d/%d" % (
    statistics.median(notionals), sum(1 for x in notionals if x >= 200), len(notionals)))

# Contribution and realized drawdown (20 USDT per event, sequential, no compounding)
obs_sorted = sorted(obs, key=lambda r: r["endDate_dt"])
pnls, cum, peak, max_dd = [], 0.0, 0.0, 0.0
for r in obs_sorted:
    net = r["y"] - r["ask"] - FEE * r["ask"] * (1 - r["ask"])
    pnl = STAKE * net / r["ask"]
    pnls.append(pnl)
    cum += pnl
    peak = max(peak, cum)
    max_dd = max(max_dd, peak - cum)
span_days = (rows[-1]["endDate_dt"] - rows[0]["endDate_dt"]).days
contrib = (sum(pnls) / ACCOUNT) * (365.0 / span_days) * 100.0
print("\n[6] Account arithmetic with %.0f USDT/event" % STAKE)
print("span: %s .. %s (%d days)" % (rows[0]["endDate"], rows[-1]["endDate"], span_days))
print("total PnL=%.2f USDT; max realized drawdown=%.2f USDT = %.2f%% of %.0f"
      % (sum(pnls), max_dd, max_dd / ACCOUNT * 100, ACCOUNT))
print("annualised contribution = %.2f%% of %.0f USDT" % (contrib, ACCOUNT))

verdict = "负" if res["pooled"]["meanNet"] < 0 and res["pooled"]["n"] >= 30 else "不显著"
print("\nVERDICT: result=%s (POOLED meanNet=%+.4f/share, n=%d; STRICT_OOS meanNet=%+.4f/share, n=%d)"
      % (verdict, res["pooled"]["meanNet"], res["pooled"]["n"], res["strict"]["meanNet"], res["strict"]["n"]))

with (HERE / "trades.csv").open("w", newline="") as fh:
    cols = ["slug", "endDate", "week", "split", "y", "p24", "in_band_old", "n_trades",
            "ask", "ask_ts", "ask_size", "bid", "spread", "strict_oos", "truncated"]
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r in out:
        w.writerow({k: r[k] for k in cols})
summary = dict(primary=res, span_days=span_days, stake=STAKE,
               total_pnl=sum(pnls), max_dd_usdt=max_dd,
               max_dd_pct=max_dd / ACCOUNT * 100, contribution_pct=contrib,
               verdict=verdict, cutoff=cutoff.isoformat())
(HERE / "results.json").write_text(json.dumps(summary, indent=2, default=str))
print("\nwrote trades.csv (%d rows) and results.json" % len(out))
