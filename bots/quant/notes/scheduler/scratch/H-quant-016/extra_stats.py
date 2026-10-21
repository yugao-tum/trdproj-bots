#!/usr/bin/env python3
"""Descriptive diagnostics: how much boundary uncertainty is left at T-24h?

Uses the same cached data as backtest.py. The "market-implied boundary" is the
highest threshold with YES fill >= 0.5; it uses only prices observable at T-24h.
The final boundary is the highest threshold that actually resolved YES (ex post).
Nothing here is fitted; the market-implied trade is exploratory, not pre-registered.
"""
import json, os, datetime, statistics, collections, math

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
ROWS = json.load(open(os.path.join(BASE, "markets.json")))
HALF = 0.01
FEE = 0.05

def trades(cid):
    try:
        return json.load(open(os.path.join(CACHE, f"tr_{cid}.json")))
    except Exception:
        return []

def fill_at(row, ts, max_age=86400):
    best = None
    for t in trades(row["conditionId"]):
        tst = int(t.get("timestamp", 0))
        if tst <= ts and (best is None or tst > best[0]):
            price = float(t.get("price", 0))
            best = (tst, price if t.get("outcome") == "Yes" else 1 - price)
    if best is None or ts - best[0] > max_age:
        return None
    return best[1]

def net(side, p, outcome):
    q = p if side == "YES" else 1 - p
    pay = outcome if side == "YES" else 1 - outcome
    return pay - (q + HALF) - FEE * q * (1 - q)

rows = []
for r in ROWS:
    p = fill_at(r, r["end_ts"] - 86400)
    if p is not None:
        rows.append(dict(r, p=p))

byev = collections.defaultdict(list)
for r in rows:
    byev[r["event"]].append(r)

print("events with >=1 T-24h fill:", len(byev))
errs = []
implied_trade = []
for ev, rs in byev.items():
    rs = sorted(rs, key=lambda x: x["threshold"])
    yes = [r["threshold"] for r in rs if r["outcome_yes"] == 1]
    if not yes:
        continue
    final_lo = max(yes)
    hi = [r for r in rs if r["threshold"] > final_lo]
    final_hi = min([r["threshold"] for r in hi], default=None)
    above = [r for r in rs if r["p"] >= 0.5]
    if not above:
        continue
    implied_lo = max(r["threshold"] for r in above)
    errs.append(implied_lo - final_lo)
    # Tradable-by-price boundary pair at T-24h.
    lo_row = next(r for r in rs if r["threshold"] == implied_lo)
    hi_rows = [r for r in rs if r["threshold"] > implied_lo]
    if hi_rows:
        hi_row = min(hi_rows, key=lambda r: r["threshold"])
        implied_trade.append((net("YES", lo_row["p"], lo_row["outcome_yes"]),
                              net("NO", hi_row["p"], hi_row["outcome_yes"]),
                              lo_row["p"], hi_row["p"]))

print("\nmarket-implied boundary vs final boundary (threshold points)")
print("  n =", len(errs), " exact =", sum(1 for e in errs if e == 0),
      " |error|<=1 =", sum(1 for e in errs if abs(e) <= 1),
      " |error|<=2 =", sum(1 for e in errs if abs(e) <= 2))
print("  error distribution:", dict(sorted(collections.Counter(errs).items())))

print("\nmarket-implied boundary pair held to resolution (1 share each, taker+1c)")
print("  n_events =", len(implied_trade))
if implied_trade:
    for i, name in enumerate(["YES lo", "NO hi"]):
        v = [x[i] for x in implied_trade]
        pos = sum(1 for x in v if x > 0)
        print(f"  {name}: mean_net={statistics.mean(v):+.4f} median={statistics.median(v):+.4f} "
              f"total={sum(v):+.4f} pos/neg={pos}/{len(v)-pos}")

# Middle-band YES rule (exploratory, not pre-registered)
mid = [r for r in rows if 0.25 <= r["p"] <= 0.90]
pe = collections.defaultdict(list)
for r in mid:
    pe[r["event"]].append(net("YES", r["p"], r["outcome_yes"]))
ev = [sum(v) / len(v) for v in pe.values()]
if ev:
    pos = sum(1 for x in ev if x > 0)
    n = len(ev)
    # exact two-sided sign test
    from math import comb
    k = min(pos, n - pos)
    pval = min(1.0, 2 * sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n)
    print("\nexploratory buy YES on 0.25<=p<=0.90 at T-24h")
    print(f"  brackets={len(mid)} events={n} mean_net={statistics.mean([x for v in pe.values() for x in v]):+.4f} "
          f"event_mean={statistics.mean(ev):+.4f} event_median={statistics.median(ev):+.4f} "
          f"pos/neg={pos}/{n-pos} sign_test_p={pval:.4f}")

# Event-level Brier: market vs constant base rate, both evaluated on the same rows
print("\nevent-level Brier (mean over brackets, then over events)")
brier_m, brier_c = [], []
base = statistics.mean(r["outcome_yes"] for r in rows)
for ev, rs in byev.items():
    brier_m.append(statistics.mean((r["p"] - r["outcome_yes"]) ** 2 for r in rs))
    brier_c.append(statistics.mean((base - r["outcome_yes"]) ** 2 for r in rs))
print("  events =", len(brier_m), " market =", round(statistics.mean(brier_m), 6),
      " constant =", round(statistics.mean(brier_c), 6),
      " median market =", round(statistics.median(brier_m), 6))
