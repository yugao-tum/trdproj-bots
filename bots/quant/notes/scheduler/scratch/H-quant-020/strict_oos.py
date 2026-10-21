#!/usr/bin/env python3
"""Strict pre-selection out-of-sample check for quant-020 (2026-10-21).

The original 247-event calibration that chose the 0.40-0.55 band used the
LATEST 250 closed earnings events as of 2026-10-20 ("sample_price.py" in
bots/quant/notes/batch2-verification/quant-020.md).  The q020-oos 60/40
holdout starts on 2026-05-05 and therefore overlaps that selection window.
This script asks a stricter question:

  Excluding every event that belonged to the latest-250 selection window,
  is the observed-ask-fill edge still positive?

Design (frozen before computing the result):
  * Selection-window proxy = the 250 newest endDate rows of the frozen
    2026-10-20 q020-oos/events.csv snapshot; cutoff = the 250th newest endDate.
  * STRICT_OOS = in-band events with endDate < cutoff.
  * SELECTION = in-band events with endDate >= cutoff.
  * Entry price = last ask-side data-api print in [endDate-72h, endDate-24h],
    exactly as in tradable_fills.py (BUY Yes at p, SELL No at 1-p).
  * Net/share = payout - ask - fee, fee = rate * ask * (1-ask); rate 0.05
    primary, 0.04 and 0.00 as sensitivity.
  * Uncertainty = ISO-week block bootstrap, 10,000 draws, seed 20261020.
  * Robustness = select events by the ORIGINAL CLOB p_24h band flag
    (in_band_old in events.csv) instead of the data-api p24 flag.

Inputs are the already-frozen files; no network calls.
"""
import csv
import datetime as dt
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EVENTS = HERE.parents[2] / "q020-oos" / "events.csv"
FILLS = HERE / "tradable_fills.csv"
SELECTION_N = 250
FEE = 0.05
SEED = 20261020
NBOOT = 10000


def iso_week(ts):
    return "%04d-W%02d" % ts.isocalendar()[:2]


def boot(sub):
    weeks = sorted(sub["week"].unique())
    groups = {w: sub.loc[sub["week"] == w, "net"].to_numpy() for w in weeks}
    rng = np.random.default_rng(SEED)
    means = np.empty(NBOOT)
    for i in range(NBOOT):
        pick = rng.integers(0, len(weeks), size=len(weeks))
        means[i] = np.concatenate([groups[weeks[j]] for j in pick]).mean()
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def report(label, sub, fee=FEE):
    if sub.empty:
        print("%-34s n=0" % label)
        return None
    s = sub.copy()
    s["net"] = s["y"] - s["ask_observed"] - fee * s["ask_observed"] * (1 - s["ask_observed"])
    lo, hi = boot(s)
    n = len(s)
    stake = s["ask_observed"].sum()
    total = s["net"].sum()
    print("%-34s n=%3d YES=%.4f meanAsk=%.4f medianNet=%+.4f meanNet=%+.4f "
          "total=%+.4f perDollar=%+.4f CI=[%+.4f,%+.4f]"
          % (label, n, s["y"].mean(), s["ask_observed"].mean(),
             statistics.median(s["net"]), s["net"].mean(), total,
             total / stake, lo, hi))
    return s


ev = pd.read_csv(EVENTS)
ev["endDate"] = pd.to_datetime(ev["endDate"], utc=True)
ev["in_band"] = ev["in_band"].astype(str).str.lower() == "true"
ev["in_band_old"] = ev["in_band_old"].astype(str).str.lower() == "true"

newest = ev.sort_values(["endDate", "slug"], ascending=[False, True]).head(SELECTION_N)
cutoff = newest["endDate"].min()

fills = pd.read_csv(FILLS)
fills["endDate"] = pd.to_datetime(fills["endDate"], utc=True)
fills = fills.merge(ev[["slug", "in_band", "in_band_old", "p_old", "p24"]],
                    on="slug", how="left", suffixes=("", "_event"))
fills["week"] = fills["endDate"].map(iso_week)
obs = fills[fills["ask_observed"].notna()].copy()
obs["strict_oos"] = obs["endDate"] < cutoff

print("H-quant-020 STRICT pre-selection OOS as_of=2026-10-21")
print("input: q020-oos/events.csv (%d closed events) + tradable_fills.csv" % len(ev))
print("selection-window proxy: newest %d closed events as of 2026-10-20" % SELECTION_N)
print("cutoff (250th newest endDate): %s" % cutoff.isoformat())
print("in-band events: %d; with observed ask print: %d" % (int(ev["in_band"].sum()), len(obs)))

print("\n[0] where the old 60/40 split sits")
for split in ("discovery", "holdout"):
    s = obs[obs["split"] == split]
    print("  %-9s n=%d  pre-selection=%d  inside-selection-window=%d"
          % (split, len(s), int(s["strict_oos"].sum()), int((~s["strict_oos"]).sum())))

print("\n[1] PRIMARY observed-ask fills, data-api band flag, fee=0.05")
report("STRICT_OOS (endDate < cutoff)", obs[obs["strict_oos"]])
report("SELECTION (endDate >= cutoff)", obs[~obs["strict_oos"]])
report("POOLED (all observed)", obs)

print("\n[2] Robustness: band membership from ORIGINAL CLOB p_24h (in_band_old)")
old = obs[obs["in_band_old"] == True]
report("STRICT_OOS old-band", old[old["strict_oos"]])
report("SELECTION old-band", old[~old["strict_oos"]])
report("POOLED old-band", old)

print("\n[3] Fee sensitivity, STRICT_OOS sample (data-api band flag)")
for fee in (0.05, 0.04, 0.00):
    report("strict_oos fee=%.2f" % fee, obs[obs["strict_oos"]], fee)
print("\n[4] Fee sensitivity, SELECTION sample (data-api band flag)")
for fee in (0.05, 0.04, 0.00):
    report("selection fee=%.2f" % fee, obs[~obs["strict_oos"]], fee)

print("\n[5] Same sample under q020-oos +1c assumption instead of observed ask")
for label, sub in (("STRICT_OOS", obs[obs["strict_oos"]]), ("SELECTION", obs[~obs["strict_oos"]])):
    s = sub.copy()
    s["ask_observed"] = s["ask_plus1c_same"]
    report(label + " +1c", s, FEE)

print("\n[6] cutoff sensitivity, observed ask, fee=0.05 (pre-cutoff sample)")
for c in ("2026-06-01", "2026-07-01", "2026-07-15", "2026-07-30T13:00:00Z", "2026-08-01"):
    cc = pd.Timestamp(c, tz="UTC")
    report("pre-" + c[:10], obs[obs["endDate"] < cc])

print("\nVERDICT: STRICT_OOS mean net per share is negative; the positive result")
print("is concentrated in the latest-250 window that was used to choose the band.")
print("This is not a clean out-of-sample pass.")
