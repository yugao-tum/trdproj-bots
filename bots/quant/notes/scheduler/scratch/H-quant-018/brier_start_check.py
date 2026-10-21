#!/usr/bin/env python3
"""Recompute the start-price Brier row that the entry mislabelled.

Reads the merged q018-price-test/buckets.csv (2026-10-20) and reports:
  * first-price normalised market Brier (the row the entry called "周起点价子集")
  * start-price normalised market Brier on the same 34 events
  * model Brier on those 34 events
No network, no refitting; all inputs are the merged report's own bucket table.
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
B = REPO / "bots" / "quant" / "notes" / "q018-price-test" / "buckets.csv"
b = pd.read_csv(B)
print("input:", B.relative_to(REPO))


def brier(col):
    vals = []
    for slug, g in b.groupby("slug"):
        if g[col].isna().any() or g[col].sum() <= 0:
            continue
        p = (g[col] / g[col].sum()).to_numpy()
        y = g.resolved_yes.to_numpy()
        vals.append(((p - y) ** 2).sum())
    return np.array(vals)


first = brier("first_p")
start = brier("start_p")
rows = []
for slug, g in b.groupby("slug"):
    if g.start_p.isna().any():
        continue
    p = (g.start_p / g.start_p.sum()).to_numpy()
    y = g.resolved_yes.to_numpy()
    rows.append((slug, float(((g.p_model.to_numpy() - y) ** 2).sum()),
                 float(((p - y) ** 2).sum())))
d = pd.DataFrame(rows, columns=["slug", "model", "start"])
d["diff"] = d.start - d.model
print(f"first-price normalised: n={len(first)} mean={first.mean():.6f}")
print(f"start-price normalised: n={len(start)} mean={start.mean():.6f}")
print(f"paired 34 events: model={d.model.mean():.6f} start={d.start.mean():.6f} "
      f"start-model={d['diff'].mean():+.6f}")
print("Bab subset (start-price complete):")
bab = d[d.slug.str.contains("bab")]
print(f"  n={len(bab)} model={bab.model.mean():.6f} start={bab.start.mean():.6f} "
      f"start-model={bab['diff'].mean():+.6f}")
print("Hormuz subset (start-price complete):")
hor = d[~d.slug.str.contains("bab")]
print(f"  n={len(hor)} model={hor.model.mean():.6f} start={hor.start.mean():.6f} "
      f"start-model={hor['diff'].mean():+.6f}")
print("\nInterpretation: the entry's '周起点价子集' row used first_p (0.8060 for all 43; "
      "0.8093 on the 34-event subset), not start_p.  With the price actually used by the "
      "start-of-week strategy, the market (0.7436) beats the model (0.7747) on the same 34 "
      "events.  Standard (3) therefore PASSes only for the first-price comparison.")
