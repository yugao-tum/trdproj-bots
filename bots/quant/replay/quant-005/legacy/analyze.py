#!/usr/bin/env python3
"""quant-005 walk-forward replay at data-api fill prices.

Rule (pre-registered in the entry):
  at 20/30/50% of the 48h window, compute an empirical conditional distribution
  of the final post count from prior closed windows with a similar early count
  (30 nearest neighbours), compare with the first YES trade at/after the decision
  time (plus a slippage cushion), and buy the bracket with the largest positive
  edge. Hold to settlement. Taker fee = 0.05 * p * (1-p) per share.

The walk-forward is strictly chronological: priors are windows that ended before
the current window started. No current-window information is used.
"""
import csv
import datetime as dt
import json
import math
import os
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve()
CACHE = pathlib.Path(os.environ.get("Q005_CACHE", HERE.parents[2]
                                     / "notes/scheduler/scratch/H-quant-005/_cache"))
OUT = HERE.parent
MIN_PRIOR = 30
K = 30
ALPHA = 0.5
FEE_RATE = 0.05
NOTIONAL = 200.0  # USDT per event; entry cap is 400, depth is roughly 300


def load():
    ev = list(csv.DictReader(open(CACHE / "events.csv", encoding="utf-8")))
    tr = list(csv.DictReader(open(CACHE / "trades.csv", encoding="utf-8")))
    for e in ev:
        e["start"] = dt.datetime.fromisoformat(e["window_start"])
        e["end"] = dt.datetime.fromisoformat(e["window_end"])
        e["n_final"] = int(e["n_final"])
        for k in ("early_20", "early_30", "early_50"):
            e[k] = int(e[k])
    ev.sort(key=lambda e: e["start"])
    by = {}
    for r in tr:
        if "price" in r and r["price"]:
            by[(r["event_id"], r["frac"], r["bracket"])] = r
    return ev, by


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return 0
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def model_probs(priors, early, brackets, trim):
    pool = priors
    if trim and len(pool) >= 10:
        cut = quantile([p[1] for p in pool], 0.90)
        pool = [p for p in pool if p[1] <= cut]
    if len(pool) < 20:
        return None, 0
    near = sorted(pool, key=lambda p: abs(p[0] - early))[:K]
    n = len(near)
    probs = {}
    for b in brackets:
        c = sum(1 for _, fin in near if b[0] <= fin <= b[1])
        probs[b] = (c + ALPHA) / (n + ALPHA * len(brackets))
    return probs, n


def run(ev, fills, frac, slip, edge_min, trim, label):
    key = int(frac * 100)
    trades = []
    for i, e in enumerate(ev):
        priors = [(p[f"early_{key}"], p["n_final"]) for p in ev[:i]
                  if p["end"] <= e["start"]]
        if len(priors) < MIN_PRIOR:
            continue
        rows = [r for (eid, f, _), r in fills.items() if eid == e["event_id"] and f == f"{int(frac*100)}%"]
        if not rows:
            continue
        brackets = [(int(r["lo"]), int(r["hi"])) for r in rows]
        probs, n = model_probs(priors, e[f"early_{key}"], brackets, trim)
        if probs is None:
            continue
        best = None
        for r in rows:
            b = (int(r["lo"]), int(r["hi"]))
            p = probs[b]
            exec_px = float(r["price"]) + slip
            if exec_px >= 1:
                continue
            fee = FEE_RATE * exec_px * (1 - exec_px)
            edge = p - exec_px - fee
            if best is None or edge > best["edge"]:
                best = {**r, "p": p, "exec_px": exec_px, "fee": fee, "edge": edge}
        if best is None or best["edge"] <= edge_min:
            continue
        won = int(best["won"])
        shares = NOTIONAL / best["exec_px"]
        pnl = shares * (won - best["exec_px"] - best["fee"])
        trades.append({
            "event_id": e["event_id"],
            "window_end": e["end"].isoformat(),
            "frac": f"{int(frac*100)}%",
            "bracket": best["bracket"],
            "n_final": e["n_final"],
            "won": won,
            "early": e[f"early_{key}"],
            "n_prior": n,
            "model_p": round(best["p"], 6),
            "fill_price": float(best["price"]),
            "exec_price": round(best["exec_px"], 6),
            "fee": round(best["fee"], 6),
            "edge": round(best["edge"], 6),
            "delay_h": float(best["delay_h"]),
            "shares": round(shares, 4),
            "pnl": round(pnl, 4),
        })
    return summarize(trades, label, frac, slip, edge_min, trim)


def summarize(trades, label, frac, slip, edge_min, trim):
    if not trades:
        return {"label": label, "frac": frac, "slip": slip, "edge_min": edge_min, "trim": trim,
                "n": 0, "result": "负", "net": 0, "roi": 0, "win_rate": 0,
                "avg_per_share": 0, "median_per_share": 0, "max_dd": 0, "contribution": 0}
    per_share = [(t["won"] - t["exec_price"] - t["fee"]) for t in trades]
    invested = sum(t["shares"] * t["exec_price"] for t in trades)
    net = sum(t["pnl"] for t in trades)
    equity, peak, mdd = 5000.0, 5000.0, 0.0
    for t in sorted(trades, key=lambda x: x["window_end"]):
        equity += t["pnl"]
        peak = max(peak, equity)
        mdd = max(mdd, (peak - equity) / peak)
    days = (dt.datetime.fromisoformat(trades[-1]["window_end"])
            - dt.datetime.fromisoformat(trades[0]["event_id"] and trades[0]["window_end"])).days
    # span from first decision to last settlement is not stored; use window_end span + 2d
    span = max(days, 1) + 2
    return {
        "label": label, "frac": frac, "slip": slip, "edge_min": edge_min, "trim": trim,
        "n": len(trades),
        "wins": sum(t["won"] for t in trades),
        "win_rate": round(sum(t["won"] for t in trades) / len(trades), 4),
        "net": round(net, 2),
        "invested": round(invested, 2),
        "roi": round(net / invested, 4) if invested else 0,
        "avg_per_share": round(statistics.mean(per_share), 4),
        "median_per_share": round(statistics.median(per_share), 4),
        "avg_edge": round(statistics.mean(t["edge"] for t in trades), 4),
        "median_delay_h": round(statistics.median(t["delay_h"] for t in trades), 2),
        "max_dd": round(mdd * 100, 2),
        "contribution": round(net / 5000 * 365 / span * 100, 2),
        "span_days": span,
        "result": "正" if net > 0 and len(trades) >= 30 else ("负" if net <= 0 and len(trades) >= 30 else "不显著"),
    }


VARIANTS = [
    ("primary f30 trim10 slip1 edge0", 0.30, 0.01, 0.0, True),
    ("f20 trim10 slip1 edge0", 0.20, 0.01, 0.0, True),
    ("f50 trim10 slip1 edge0", 0.50, 0.01, 0.0, True),
    ("f30 no-trim slip1 edge0", 0.30, 0.01, 0.0, False),
    ("f30 trim10 slip2 edge0", 0.30, 0.02, 0.0, True),
    ("f30 trim10 slip1 edge2c", 0.30, 0.01, 0.02, True),
]


def main():
    ev, fills = load()
    results, all_trades = [], []
    for label, frac, slip, edge_min, trim in VARIANTS:
        res = run(ev, fills, frac, slip, edge_min, trim, label)
        results.append(res)
        if label.startswith("primary"):
            # re-run to capture trades (run returns summary only)
            pass
    # capture primary trades
    trades = []
    for i, e in enumerate(ev):
        priors = [(p["early_30"], p["n_final"]) for p in ev[:i] if p["end"] <= e["start"]]
        if len(priors) < MIN_PRIOR:
            continue
        rows = [r for (eid, f, _), r in fills.items() if eid == e["event_id"] and f == "30%"]
        if not rows:
            continue
        brackets = [(int(r["lo"]), int(r["hi"])) for r in rows]
        probs, n = model_probs(priors, e["early_30"], brackets, True)
        if probs is None:
            continue
        best = None
        for r in rows:
            b = (int(r["lo"]), int(r["hi"]))
            p = probs[b]
            exec_px = float(r["price"]) + 0.01
            fee = FEE_RATE * exec_px * (1 - exec_px)
            edge = p - exec_px - fee
            if best is None or edge > best["edge"]:
                best = {**r, "p": p, "exec_px": exec_px, "fee": fee, "edge": edge}
        if best is None or best["edge"] <= 0:
            continue
        shares = NOTIONAL / best["exec_px"]
        trades.append({
            "event_id": e["event_id"], "window_end": e["end"].isoformat(), "frac": "30%",
            "bracket": best["bracket"], "n_final": e["n_final"], "won": int(best["won"]),
            "early": e["early_30"], "n_prior": n, "model_p": round(best["p"], 6),
            "fill_price": float(best["price"]), "exec_price": round(best["exec_px"], 6),
            "fee": round(best["fee"], 6), "edge": round(best["edge"], 6),
            "delay_h": float(best["delay_h"]), "shares": round(shares, 4),
            "pnl": round(shares * (int(best["won"]) - best["exec_px"] - best["fee"]), 4),
        })

    fields = list(trades[0].keys()) if trades else []
    with open(OUT / "trades.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(trades)
    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{'variant':38s} {'n':>4s} {'win%':>6s} {'net$':>9s} {'ROI%':>8s} {'avg/sh':>8s} {'med/sh':>8s} {'mdd%':>6s} {'contrib%':>9s}")
    for r in results:
        print(f"{r['label']:38s} {r['n']:4d} {100*r['win_rate']:6.1f} {r['net']:9.2f} {100*r['roi']:8.2f} "
              f"{r['avg_per_share']:8.4f} {r['median_per_share']:8.4f} {r['max_dd']:6.2f} {r['contribution']:9.2f}")
    print(f"\nprimary trades={len(trades)} written to trades.csv")


if __name__ == "__main__":
    main()
