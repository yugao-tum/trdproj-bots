#!/usr/bin/env python3
"""Historical tradable-price checks for quant-016 (model-free, pre-registered).

Pre-registered rules (written before looking at output):
  A  buy NO  on every bracket whose last YES fill at T-24h is >= 0.90
  B  buy YES on every bracket whose last YES fill at T-24h is <= 0.10
  C  buy NO  on every bracket whose last YES fill at T-24h is in [0.25, 0.75]
  (T = event endDate in Gamma; each rule holds to resolution, 1 share per bracket)
Execution: last data-api fill at/before T-h, +1c half-spread, taker fee
0.05*p*(1-p) per share. Maker-fee-0 variant also reported.
Independent unit = event (brackets in one event share one resolution).
No parameter was fitted; all 85 closed events are out-of-sample. A time split at
2026-08-01 is reported only as a stability check.
"""
import json, os, datetime, math, statistics, collections

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
ROWS = json.load(open(os.path.join(BASE, "markets.json")))
HORIZONS = {"T-7d": 7 * 86400, "T-48h": 48 * 3600, "T-24h": 24 * 3600, "T-6h": 6 * 3600}
FEE_RATE = 0.05
HALF = 0.01

def ph(tok):
    p = os.path.join(CACHE, f"ph_{tok}.json")
    try:
        return json.load(open(p)).get("history", [])
    except Exception:
        return []

def trades(cid):
    p = os.path.join(CACHE, f"tr_{cid}.json")
    try:
        return json.load(open(p))
    except Exception:
        return []

def fill_at(row, ts, max_age=86400):
    """Most recent YES-equivalent fill at/before ts, no older than max_age."""
    best = None
    for t in trades(row["conditionId"]):
        tst = int(t.get("timestamp", 0))
        if tst <= ts and (best is None or tst > best[0]):
            price = float(t.get("price", 0))
            yes = price if t.get("outcome") == "Yes" else 1.0 - price
            best = (tst, yes, t.get("side"), t.get("outcome"), price)
        if tst > ts and False:
            pass
    if best is None or ts - best[0] > max_age:
        return None
    return {"ts": best[0], "p": best[1], "age_h": (ts - best[0]) / 3600.0}

def clob_at(row, ts, max_age=6 * 3600):
    best = None
    for x in ph(row["yes_token"]):
        t = int(x["t"])
        if t <= ts and (best is None or t > best[0]):
            best = (t, float(x["p"]))
    if best is None or ts - best[0] > max_age:
        return None
    return {"ts": best[0], "p": best[1], "age_h": (ts - best[0]) / 3600.0}

def net(kind, p, outcome, maker=False):
    """Return net P&L per share for buying YES/NO at YES-price p."""
    if kind == "YES":
        q = p
        pay = outcome
    else:
        q = 1.0 - p
        pay = 1 - outcome
    cost = q + HALF
    fee = 0.0 if maker else FEE_RATE * q * (1 - q)
    return pay - cost - fee

def rule_stats(rows, side, pred):
    per_event = collections.defaultdict(list)
    for r in rows:
        if pred(r["p"]):
            per_event[r["event"]].append(net(side, r["p"], r["outcome_yes"]))
    ev = [sum(v) / len(v) for v in per_event.values()]
    allv = [x for v in per_event.values() for x in v]
    if not allv:
        return None
    pos = sum(1 for x in ev if x > 0)
    # two-sided sign test, normal approximation
    n = len(ev)
    z = (pos - n / 2) / math.sqrt(n / 4) if n else 0
    return {
        "n_brackets": len(allv), "n_events": n,
        "mean_net": statistics.mean(allv), "median_net": statistics.median(allv),
        "total_net": sum(allv),
        "event_mean": statistics.mean(ev), "event_median": statistics.median(ev),
        "pos_events": pos, "neg_events": n - pos, "z": z,
    }

def fmt(x):
    return "None" if x is None else f"{x:.6f}"

def main():
    print("events", len({r['event'] for r in ROWS}), "brackets", len(ROWS))
    print("horizon  priced_brackets  priced_events  median_fill_age_h  median_clob_age_h")
    data = {}
    for label, back in HORIZONS.items():
        out = []
        for r in ROWS:
            ts = r["end_ts"] - back
            f = fill_at(r, ts)
            c = clob_at(r, ts)
            rec = dict(r)
            rec["p"] = f["p"] if f else None
            rec["fill_age_h"] = f["age_h"] if f else None
            rec["p_clob"] = c["p"] if c else None
            rec["clob_age_h"] = c["age_h"] if c else None
            out.append(rec)
        data[label] = out
        priced = [r for r in out if r["p"] is not None]
        print(f"{label:6s}  {len(priced):5d}  {len({r['event'] for r in priced}):5d}  "
              f"{statistics.median([r['fill_age_h'] for r in priced]):8.2f}  "
              f"{statistics.median([r['clob_age_h'] for r in out if r['p_clob'] is not None]):8.2f}")

    # Calibration at T-24h (fills)
    print("\n== T-24h price calibration (last fill, YES-equivalent) ==")
    rows = [r for r in data["T-24h"] if r["p"] is not None]
    buckets = [(0, .05), (.05, .10), (.10, .25), (.25, .50), (.50, .75), (.75, .90), (.90, .95), (.95, 1.0001)]
    print("bucket        n   events  mean_p  realised_yes  brier   mean_net_YES  mean_net_NO")
    brier = []
    for lo, hi in buckets:
        b = [r for r in rows if lo <= r["p"] < hi]
        if not b:
            continue
        mp = statistics.mean(r["p"] for r in b)
        ry = statistics.mean(r["outcome_yes"] for r in b)
        br = statistics.mean((r["p"] - r["outcome_yes"]) ** 2 for r in b)
        brier.extend((r["p"] - r["outcome_yes"]) ** 2 for r in b)
        print(f"[{lo:.2f},{hi:.2f})  {len(b):4d}  {len({r['event'] for r in b}):5d}  "
              f"{mp:.4f}  {ry:.4f}  {br:.4f}  "
              f"{statistics.mean(net('YES',r['p'],r['outcome_yes']) for r in b):+.4f}  "
              f"{statistics.mean(net('NO',r['p'],r['outcome_yes']) for r in b):+.4f}")
    print("overall market Brier (bracket-level):", round(statistics.mean(brier), 6))
    base = statistics.mean(r["outcome_yes"] for r in rows)
    print("overall YES base rate:", round(base, 6),
          " constant-Brier:", round(statistics.mean((base - r["outcome_yes"]) ** 2 for r in rows), 6))

    print("\n== pre-registered rules at T-24h (taker fee + 1c half-spread) ==")
    for name, side, pred in [
        ("A buy NO  p>=0.90", "NO", lambda p: p >= .90),
        ("B buy YES p<=0.10", "YES", lambda p: p <= .10),
        ("C buy NO  0.25<=p<=0.75", "NO", lambda p: .25 <= p <= .75),
    ]:
        s = rule_stats(rows, side, pred)
        if not s:
            print(name, "no trades"); continue
        print(f"{name}: brackets={s['n_brackets']} events={s['n_events']} "
              f"mean_net={fmt(s['mean_net'])} median_net={fmt(s['median_net'])} "
              f"total_net={fmt(s['total_net'])} event_mean={fmt(s['event_mean'])} "
              f"event_median={fmt(s['event_median'])} pos/neg={s['pos_events']}/{s['neg_events']} z={s['z']:.2f}")

    print("\n== maker-fee-0 variant (same fills, no fee; 1c half-spread still charged) ==")
    for name, side, pred in [
        ("A buy NO  p>=0.90", "NO", lambda p: p >= .90),
        ("B buy YES p<=0.10", "YES", lambda p: p <= .10),
        ("C buy NO  0.25<=p<=0.75", "NO", lambda p: .25 <= p <= .75),
    ]:
        pe = collections.defaultdict(list)
        for r in rows:
            if pred(r["p"]):
                pe[r["event"]].append(net(side, r["p"], r["outcome_yes"], maker=True))
        allv = [x for v in pe.values() for x in v]
        ev = [sum(v) / len(v) for v in pe.values()]
        print(f"{name}: n={len(allv)} events={len(ev)} mean_net={statistics.mean(allv):+.6f} "
              f"event_mean={statistics.mean(ev):+.6f} total_net={sum(allv):+.4f}")

    print("\n== horizon sensitivity (same pre-registered rules) ==")
    for label in ("T-48h", "T-24h", "T-6h"):
        hrs = [r for r in data[label] if r["p"] is not None]
        for name, side, pred in [
            ("A", "NO", lambda p: p >= .90),
            ("B", "YES", lambda p: p <= .10),
            ("C", "NO", lambda p: .25 <= p <= .75),
        ]:
            s = rule_stats(hrs, side, pred)
            if s:
                print(f"{label} {name}: brackets={s['n_brackets']:3d} events={s['n_events']:2d} "
                      f"mean_net={fmt(s['mean_net'])} event_mean={fmt(s['event_mean'])} "
                      f"pos/neg={s['pos_events']}/{s['neg_events']}")

    # CLOB-price sensitivity (same rules, replace the last fill with the last CLOB point)
    print("\n== CLOB-price sensitivity at T-24h (taker fee + 1c half-spread) ==")
    rows_c = [dict(r, p=r["p_clob"]) for r in data["T-24h"] if r["p_clob"] is not None]
    print("priced brackets:", len(rows_c), "events:", len({r["event"] for r in rows_c}))
    for name, side, pred in [
        ("A buy NO  p>=0.90", "NO", lambda p: p >= .90),
        ("B buy YES p<=0.10", "YES", lambda p: p <= .10),
        ("C buy NO  0.25<=p<=0.75", "NO", lambda p: .25 <= p <= .75),
    ]:
        s = rule_stats(rows_c, side, pred)
        if s:
            print(f"{name}: brackets={s['n_brackets']} events={s['n_events']} "
                  f"mean_net={fmt(s['mean_net'])} event_mean={fmt(s['event_mean'])} "
                  f"pos/neg={s['pos_events']}/{s['neg_events']}")

    # Time stability / pseudo-OOS split
    print("\n== time split (closed before vs after 2026-08-01) ==")
    cutoff = datetime.datetime(2026, 8, 1, tzinfo=datetime.timezone.utc).timestamp()
    for name, side, pred in [
        ("A buy NO  p>=0.90", "NO", lambda p: p >= .90),
        ("B buy YES p<=0.10", "YES", lambda p: p <= .10),
        ("C buy NO  0.25<=p<=0.75", "NO", lambda p: .25 <= p <= .75),
    ]:
        for lab, sel in [("in", lambda r: r["end_ts"] < cutoff), ("out", lambda r: r["end_ts"] >= cutoff)]:
            s = rule_stats([r for r in rows if sel(r)], side, pred)
            if s:
                print(f"{name} {lab:3s}: events={s['n_events']:2d} brackets={s['n_brackets']:3d} "
                      f"mean_net={fmt(s['mean_net'])} event_mean={fmt(s['event_mean'])} "
                      f"pos/neg={s['pos_events']}/{s['neg_events']}")

    # Boundary bracket descriptive (uses final outcome only to select, not to trade)
    print("\n== eventual boundary bracket: price at each horizon (descriptive, NOT a P&L test) ==")
    byev = collections.defaultdict(list)
    for r in data["T-24h"]:
        byev[r["event"]].append(r)
    for label in HORIZONS:
        plo, phi = [], []
        for ev, rs in byev.items():
            yes = [r["threshold"] for r in rs if r["outcome_yes"] == 1]
            no = [r["threshold"] for r in rs if r["outcome_yes"] == 0]
            if not yes:
                continue
            lo = max(yes)
            hi = min([n for n in no if n > lo], default=None)
            if hi is None:
                continue
            rl = next(x for x in data[label] if x["event"] == ev and x["threshold"] == lo)
            rh = next(x for x in data[label] if x["event"] == ev and x["threshold"] == hi)
            if rl["p"] is not None and rh["p"] is not None:
                plo.append(rl["p"]); phi.append(rh["p"])
        if plo:
            print(f"{label}: n_events={len(plo)} median_p(lo)={statistics.median(plo):.4f} "
                  f"median_p(hi)={statistics.median(phi):.4f} "
                  f"share p(lo)>=0.95={sum(1 for x in plo if x>=.95)/len(plo):.3f} "
                  f"share p(hi)<=0.05={sum(1 for x in phi if x<=.05)/len(phi):.3f}")

if __name__ == "__main__":
    main()
