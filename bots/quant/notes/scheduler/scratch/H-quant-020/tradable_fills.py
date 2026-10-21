#!/usr/bin/env python3
"""H-quant-020 historical TRADABLE-fill check (2026-10-21).

Question: the entry's out-of-sample backtest used data-api last-trade price
plus a PRE-DECLARED 1 cent half-spread.  Is the edge still there when the
entry price is an OBSERVED taker BUY-YES print (an actual ask-side fill),
with the same 0.05 taker fee and the same 60/40 time split?

Design (frozen before looking at the result):
  * Universe = the 101 in-band events in ../q020-oos/events.csv (band
    0.40 <= p24 <= 0.55 already fixed by the entry; no re-fitting).
  * For each event, read data-api trades in [endDate-72h, endDate-24h].
  * entry_ask = YES-equivalent price of the LAST ask-side print in that
    window.  Ask-side prints are (side BUY, outcome Yes) at price p and
    (side SELL, outcome No) at 1 - p.  This is an observed fill, not p + 1c.
    If there is no ask-side print, the event is "unpriced_observed" and is
    reported but not used in the primary result.
  * fee/share = 0.05 * ask * (1 - ask); net/share = payout - ask - fee.
  * DISCOVERY/HOLDOUT are copied from q020-oos/events.csv (same 60/40 split).
  * Secondary (same subset): entry = last YES print of any side + 0.01,
    exactly the q020-oos assumption, for an apples-to-apples comparison.
  * Effective spread: bid-side prints are (SELL, Yes) at p and (BUY, No)
    at 1 - p.  For events with both an ask-side and a bid-side print, print
    ask-bid and its half.
  * Block bootstrap by ISO week of endDate, 10,000 draws, seed 20261020.

All endpoints keyless; cache under _cache/ (gitignored).
"""
import csv, datetime as dt, json, statistics, time
from pathlib import Path
import numpy as np
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"; CACHE.mkdir(exist_ok=True)
DATA_API = "https://data-api.polymarket.com"
AS_OF = "2026-10-21"
FEE = 0.05
SEED = 20261020
NBOOT = 10000
S = requests.Session(); S.headers.update({"User-Agent": "quant-research-H-quant-020/1.0 (keyless)"})

# q020-oos is three levels up: scratch/H-quant-020 -> scratch -> scheduler -> notes? no
# HERE = bots/quant/notes/scheduler/scratch/H-quant-020
# parents[0]=scratch parents[1]=scheduler parents[2]=notes
CSV = HERE.parents[2] / "q020-oos" / "events.csv"

def get_trades(cid, lo, hi):
    key = CACHE / ("trades_%s_%d_%d.json" % (cid, lo, hi))
    if key.exists():
        return json.loads(key.read_text())
    kept, off, reached, truncated = [], 0, False, False
    while off <= 10000:
        for attempt in range(5):
            try:
                r = S.get(DATA_API + "/trades", params={"market": cid, "limit": 500, "offset": off}, timeout=60)
                if r.status_code == 400:
                    data = {"_http400": r.text[:200]}
                else:
                    r.raise_for_status(); data = r.json()
                break
            except Exception:
                if attempt == 4: raise
                time.sleep(1.5 * (attempt + 1))
        if isinstance(data, dict):
            truncated = not reached; break
        if not isinstance(data, list) or not data: break
        for t in data:
            ts = int(t.get("timestamp", 0))
            if lo <= ts <= hi: kept.append(t)
        oldest = min(int(t.get("timestamp", 0)) for t in data)
        if oldest < lo: reached = True; break
        if len(data) < 500: reached = True; break
        if off >= 10000: truncated = True; break
        off += 500
    kept.sort(key=lambda t: (int(t.get("timestamp", 0)), t.get("transactionHash", "")))
    out = {"trades": kept, "truncated": truncated, "reached_start": reached}
    key.write_text(json.dumps(out, separators=(",", ":")))
    return out

def yes_ask_price(t):
    if t.get("outcome") == "Yes" and t.get("side") == "BUY":
        return float(t["price"])
    if t.get("outcome") == "No" and t.get("side") == "SELL":
        return 1.0 - float(t["price"])
    return None

def yes_bid_price(t):
    if t.get("outcome") == "Yes" and t.get("side") == "SELL":
        return float(t["price"])
    if t.get("outcome") == "No" and t.get("side") == "BUY":
        return 1.0 - float(t["price"])
    return None

def last_print(trades, pred):
    xs = [t for t in trades if pred(t)]
    if not xs: return None, None
    t = xs[-1]
    return float(t["price"]), int(t["timestamp"])

def iso_week(s):
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return "%04d-W%02d" % d.isocalendar()[:2]

rows = list(csv.DictReader(CSV.open()))
band = [r for r in rows if r["in_band"] == "True"]
print("H-quant-020 observed-fill check as_of=%s" % AS_OF)
print("universe: in-band events from q020-oos/events.csv = %d (band frozen in entry)" % len(band))

out_rows, trunc, no_buy = [], 0, []
for i, r in enumerate(band, 1):
    end = dt.datetime.fromisoformat(r["endDate"].replace("Z", "+00:00"))
    lo = int((end - dt.timedelta(hours=72)).timestamp())
    hi = int((end - dt.timedelta(hours=24)).timestamp())
    tw = get_trades(r["conditionId"], lo, hi)
    trades = tw["trades"]
    if tw["truncated"]: trunc += 1
    buy, buy_ts = last_print(trades, lambda t: yes_ask_price(t) is not None)
    sell, sell_ts = last_print(trades, lambda t: yes_bid_price(t) is not None)
    if buy is not None:
        buy = yes_ask_price(next(t for t in reversed(trades) if yes_ask_price(t) is not None))
        buy_t = next(t for t in reversed(trades) if yes_ask_price(t) is not None)
        buy_size = float(buy_t.get("size", 0))
    else:
        buy_size = None
    if sell is not None:
        sell = yes_bid_price(next(t for t in reversed(trades) if yes_bid_price(t) is not None))
    anyyes, any_ts = last_print(trades, lambda t: t.get("outcome") == "Yes")
    if buy is None:
        no_buy.append(r["slug"])
    y = int(r["y"])
    ask = buy
    fee = FEE * ask * (1 - ask) if ask is not None else None
    net = y - ask - fee if ask is not None else None
    ask1 = min(1.0, float(r["p24"]) + 0.01) if r["p24"] not in ("", None) else None
    fee1 = FEE * ask1 * (1 - ask1) if ask1 is not None else None
    net1 = y - ask1 - fee1 if ask1 is not None else None
    rr = {
        "slug": r["slug"], "endDate": r["endDate"], "week": iso_week(r["endDate"]),
        "split": r["split"], "y": y, "n_trades": len(trades),
        "buy_yes": buy, "buy_yes_ts": buy_ts, "buy_yes_size": buy_size,
        "sell_yes": sell, "sell_yes_ts": sell_ts,
        "any_yes": anyyes,
        "ask_observed": ask, "fee_observed": fee, "net_observed": net,
        "ask_plus1c_same": ask1, "fee_plus1c_same": fee1, "net_plus1c_same": net1,
        "spread": (buy - sell) if (buy is not None and sell is not None) else None,
        "truncated": tw["truncated"],
        "capital_days": (end - dt.datetime.fromtimestamp(buy_ts, dt.timezone.utc)).total_seconds()/86400.0 if buy_ts else None,
    }
    out_rows.append(rr)
    if i % 20 == 0: print("  priced %d/%d..." % (i, len(band)))

print("events with an ask-side print in [-72h,-24h]: %d/%d" % (sum(1 for r in out_rows if r["ask_observed"] is not None), len(out_rows)))
print("events with no ask-side print: %d" % len(no_buy))
if no_buy: print("  " + ", ".join(no_buy))
print("data-api truncated markets: %d" % trunc)

def boot(vals_by_week):
    weeks = sorted(vals_by_week); rng = np.random.default_rng(SEED)
    means = np.empty(NBOOT)
    for i in range(NBOOT):
        draw = rng.integers(0, len(weeks), size=len(weeks))
        vv = []
        for j in draw: vv.extend(vals_by_week[weeks[j]])
        means[i] = float(np.mean(vv))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))

def report(label, subset, net_key, ask_key):
    n = len(subset)
    if not n:
        print("%s: n=0" % label); return
    nets = [r[net_key] for r in subset]; asks = [r[ask_key] for r in subset]
    ys = sum(r["y"] for r in subset)
    stake = sum(asks); total = sum(nets)
    byw = {}
    for r in subset: byw.setdefault(r["week"], []).append(r[net_key])
    lo, hi = boot(byw)
    print("%s: n=%d YESrate=%.4f meanAsk=%.4f medianNet=%+.4f meanNet=%+.4f totalNet=%+.4f perDollar=%+.4f CI=[%+.4f,%+.4f]"
          % (label, n, ys/n, stake/n, statistics.median(nets), total/n, total, total/stake, lo, hi))
    return dict(n=n, yesrate=ys/n, meanAsk=stake/n, medianNet=statistics.median(nets),
                meanNet=total/n, totalNet=total, perDollar=total/stake, ci=(lo,hi))

print("\n[1] PRIMARY: entry at last observed ask-side print, fee 0.05")
for lab in ("discovery", "holdout"):
    report(lab.upper(), [r for r in out_rows if r["split"] == lab and r["ask_observed"] is not None], "net_observed", "ask_observed")
report("POOLED", [r for r in out_rows if r["ask_observed"] is not None], "net_observed", "ask_observed")

print("\n[2] SAME subset, q020-oos assumption: last YES print + 1c, fee 0.05")
for lab in ("discovery", "holdout"):
    report(lab.upper(), [r for r in out_rows if r["split"] == lab and r["ask_observed"] is not None and r["net_plus1c_same"] is not None], "net_plus1c_same", "ask_plus1c_same")
report("POOLED", [r for r in out_rows if r["ask_observed"] is not None and r["net_plus1c_same"] is not None], "net_plus1c_same", "ask_plus1c_same")

print("\n[3] ALL 101 in-band, q020-oos assumption (reproduction check)")
for lab in ("discovery", "holdout"):
    report(lab.upper(), [r for r in out_rows if r["split"] == lab and r["ask_plus1c_same"] is not None], "net_plus1c_same", "ask_plus1c_same")
report("POOLED", [r for r in out_rows if r["ask_plus1c_same"] is not None], "net_plus1c_same", "ask_plus1c_same")

spreads = [r["spread"] for r in out_rows if r["spread"] is not None]
diffs = [r["ask_observed"] - r["ask_plus1c_same"] for r in out_rows if r["ask_observed"] is not None and r["ask_plus1c_same"] is not None]
print("\n[4] observed vs assumed entry")
print("observed effective spread (ask-side - bid-side): n=%d mean=%+.4f median=%+.4f"
      % (len(spreads), sum(spreads)/len(spreads), statistics.median(spreads)) if spreads else "no spreads")
print("observed ask - (last YES + 1c): n=%d mean=%+.4f median=%+.4f"
      % (len(diffs), sum(diffs)/len(diffs), statistics.median(diffs)))
print("negative differences = observed ask below the +1c assumption: %d/%d" % (sum(1 for d in diffs if d < 0), len(diffs)))
sizes = [r["buy_yes_size"] * r["ask_observed"] for r in out_rows if r["ask_observed"] is not None and r.get("buy_yes_size")]
print("ask-print notional (size*price): n=%d median=%.1f USDT; >=200 USDT: %d/%d"
      % (len(sizes), statistics.median(sizes), sum(1 for x in sizes if x >= 200), len(sizes)))

print("\n[5] fee sensitivity on the same observed-ask sample")
obs = [r for r in out_rows if r["ask_observed"] is not None]
for fr in (0.05, 0.04, 0.00):
    print("  fee_rate=%.2f" % fr)
    for lab in ("discovery", "holdout", None):
        sub = [r for r in obs if (lab is None or r["split"] == lab)]
        nets = [r["y"] - r["ask_observed"] - fr * r["ask_observed"] * (1 - r["ask_observed"]) for r in sub]
        stake = sum(r["ask_observed"] for r in sub)
        print("    %-9s n=%d medianNet=%+.4f meanNet=%+.4f perDollar=%+.4f"
              % (lab or "POOLED", len(sub), statistics.median(nets), sum(nets)/len(nets), sum(nets)/stake))

# verdict
hold = [r for r in out_rows if r["split"] == "holdout" and r["ask_observed"] is not None]
if len(hold) < 30:
    print("\nVERDICT: INSUFFICIENT observed-fill holdout n=%d < 30" % len(hold))
else:
    nets = [r["net_observed"] for r in hold]; ys = sum(r["y"] for r in hold); ma = sum(r["ask_observed"] for r in hold)/len(hold)
    med = statistics.median(nets)
    bad = (med <= 0) or (ys/len(hold) <= ma)
    print("\nVERDICT: %s (n=%d medianNet=%+.4f YESrate=%.4f meanAsk=%.4f)"
          % ("FAIL" if bad else "PASS", len(hold), med, ys/len(hold), ma))

with (HERE / "tradable_fills.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys())); w.writeheader()
    for r in out_rows: w.writerow(r)
print("\nwrote tradable_fills.csv (%d rows)" % len(out_rows))
