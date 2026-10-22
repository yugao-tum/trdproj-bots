#!/usr/bin/env python3
"""Summarize the canonical quant-005 replay and its variants from events.csv.

Canonical scope (frozen in the entry): Elon 48h series only; overlapping windows
deduplicated on the America/New_York local-noon boundary; decision at 50% of the
window; conservative empirical distribution; taker fee 0.05*p*(1-p); ask =
last data-api YES trade in the 6h before decision + 1 cent; hold to resolution.
"""
import json, math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

NY = ZoneInfo("America/New_York")
NOTIONAL = 200.0
START_EQ = 5000.0

def local_ts(s):
    return datetime.fromisoformat(s).astimezone(NY).timestamp()

def dedup(rows):
    erows = sorted([r for r in rows if r["series"] == "elon48"],
                   key=lambda r: local_ts(r["window_end_utc"]))
    kept, last_end = [], None
    for r in erows:
        start = local_ts(r["window_start_utc"])
        if last_end is None or start >= last_end:
            kept.append(r)
            last_end = local_ts(r["window_end_utc"])
    return erows, kept

def truthy(v):
    return v is True or (isinstance(v, str) and v.lower() in ("true", "1")) or (isinstance(v, (int, float)) and v == 1)

def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def summarize(rows, trig="triggered", share="net_per_share", dollar="net_per_dollar",
              win="win", ts="decision_ts"):
    sel = [r for r in rows if truthy(r.get(trig)) and num(r.get(share)) is not None]
    if not sel:
        return {"n": 0}
    vals = [num(r[share]) for r in sel]
    dvals = [num(r[dollar]) for r in sel if num(r.get(dollar)) is not None]
    wins = [1.0 if truthy(r.get(win)) else 0.0 for r in sel]
    return {"n": len(sel), "median_share": float(np.median(vals)),
            "mean_share": float(np.mean(vals)),
            "median_dollar": float(np.median(dvals)) if dvals else None,
            "mean_dollar": float(np.mean(dvals)) if dvals else None,
            "hit": float(np.mean(wins))}

def account(rows, trig="triggered", dollar="net_per_dollar", end="window_end_utc"):
    sel = [r for r in rows if truthy(r.get(trig)) and num(r.get(dollar)) is not None]
    sel.sort(key=lambda r: r[end])
    eq = START_EQ
    peak = eq
    mdd = 0.0
    net = 0.0
    for r in sel:
        pnl = NOTIONAL * num(r[dollar])
        net += pnl
        eq = max(0.0, eq + pnl)
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)
    if not sel:
        return {"n": 0}
    t0 = datetime.fromisoformat(min(r["window_start_utc"] for r in sel))
    t1 = datetime.fromisoformat(max(r[end] for r in sel))
    span_days = max((t1 - t0).total_seconds() / 86400.0, 1.0)
    return {"n": len(sel), "net_usdt": net, "end_equity": eq,
            "max_dd_pct": mdd * 100.0, "span_days": span_days,
            "contribution_pct": net / START_EQ * 365.0 / span_days * 100.0,
            "notional_per_event": NOTIONAL}

def main():
    df = pd.read_csv("events.csv")
    rows = df.to_dict("records")
    erows, kept = dedup(rows)
    out = {}
    out["canonical_f50"] = summarize(kept)
    out["canonical_f50_account"] = account(kept)
    out["canonical_f75"] = summarize(kept, "triggered_75", "net_per_share_75",
                                     "net_per_dollar_75", "win_75", "decision_ts_75")
    out["canonical_f75_account"] = account(kept, "triggered_75", "net_per_dollar_75", "window_end_utc")
    out["pooled_f50"] = summarize(rows)
    out["pooled_f50_account"] = account(rows)
    out["pooled_f75"] = summarize(rows, "triggered_75", "net_per_share_75",
                                  "net_per_dollar_75", "win_75", "decision_ts_75")
    out["pooled_f75_account"] = account(rows, "triggered_75", "net_per_dollar_75", "window_end_utc")
    out["elon48_rows"] = len(erows)
    out["elon48_kept"] = len(kept)
    out["elon48_triggered_nodedup"] = int(sum(1 for r in erows if bool(r.get("triggered"))))
    out["dataset_access_date_utc"] = "2026-10-21"
    out["analysis_run_date_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(json.dumps(out, indent=2, ensure_ascii=False))
    with open("variant_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
