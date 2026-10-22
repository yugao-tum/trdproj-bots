#!/usr/bin/env python3
"""Build the frozen replay inputs for bots/quant/replay/quant-018/.

Sources (all already fetched and verified by earlier merged notes):
  * draft-era Bab buckets: bots/quant/notes/q018-paired/buckets.csv
    (same-time [T-24h,T] last data-api trade, built 2026-10-20).
  * post-decision Bab fills: bots/quant/notes/postdecision-fills-20261021/
    q018_strict_buckets.csv (PR #21; first data-api print at/after T, with
    its timestamp, built 2026-10-21).
  * post-draft OOS event: live Gamma + data-api + PortWatch, fetched by
    tradable_backtest.py on 2026-10-21 (Bab week of October 12).

Canonical copy in the replay directory; the scratch copy is kept for the
scheduler evidence trail.  This script never picks or tunes parameters; it only projects the columns the
replay needs into three small CSVs (< 1 MB) and prints sha1/row counts.
"""
import hashlib
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[4]
PAIRED = REPO / "bots" / "quant" / "notes" / "q018-paired" / "buckets.csv"
STRICT = (REPO / "bots" / "quant" / "notes" / "postdecision-fills-20261021"
          / "q018_strict_buckets.csv")
OUT = REPO / "bots" / "quant" / "replay" / "quant-018" / "inputs"
OUT.mkdir(parents=True, exist_ok=True)

COLS = ["slug", "week_start", "label", "conditionId", "p_model", "main_p_yes", "resolved_yes"]


def sha1(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()


def main():
    print("source:", PAIRED.relative_to(REPO))
    print("source sha1:", sha1(PAIRED))
    d = pd.read_csv(PAIRED)
    bab = d[d.strait.str.contains("Bab")].copy()
    bab = bab[COLS]
    bab.to_csv(OUT / "buckets_bab.csv", index=False, float_format="%.12g")
    print(f"buckets_bab.csv: {len(bab)} rows, {bab.slug.nunique()} events, "
          f"{bab.main_p_yes.notna().sum()} buckets with a [T-24h,T] trade")
    print("buckets_bab.csv sha1:", sha1(OUT / "buckets_bab.csv"))
    print("events:", bab.groupby("week_start").size().to_dict())

    oos = pd.DataFrame([
        dict(slug="how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z",
             week_start="2026-10-12", label="<170", p_model=0.058823529411764705,
             main_p_yes=0.20000000000000001, resolved_yes=0),
        dict(slug="how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z",
             week_start="2026-10-12", label="170-189", p_model=0.29411764705882354,
             main_p_yes=0.21000000500000005, resolved_yes=1),
        dict(slug="how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z",
             week_start="2026-10-12", label="190-209", p_model=0.47058823529411764,
             main_p_yes=0.22000001690000004, resolved_yes=0),
        dict(slug="how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z",
             week_start="2026-10-12", label="210-229", p_model=0.11764705882352941,
             main_p_yes=0.25, resolved_yes=0),
        dict(slug="how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z",
             week_start="2026-10-12", label="230+", p_model=0.058823529411764705,
             main_p_yes=0.17, resolved_yes=0),
    ])
    oos.to_csv(OUT / "oos_bab_oct12.csv", index=False, float_format="%.12g")
    print(f"oos_bab_oct12.csv: {len(oos)} rows (values printed by "
          f"tradable_backtest.py on 2026-10-21)")
    print("oos_bab_oct12.csv sha1:", sha1(OUT / "oos_bab_oct12.csv"))

    print("source:", STRICT.relative_to(REPO))
    print("source sha1:", sha1(STRICT))
    s = pd.read_csv(STRICT)
    sb = s[s.strait == "Bab el-Mandeb Strait"].copy()
    sb = sb[["slug", "week_start", "label", "p_model", "resolved_yes",
             "main_p_yes", "strict_p_yes", "strict_ts"]]
    sb.to_csv(OUT / "strict_bab.csv", index=False, float_format="%.12g")
    print(f"strict_bab.csv: {len(sb)} rows, {sb.slug.nunique()} events, "
          f"{sb.strict_p_yes.notna().sum()} buckets with a post-T first print")
    print("strict_bab.csv sha1:", sha1(OUT / "strict_bab.csv"))


if __name__ == "__main__":
    main()
