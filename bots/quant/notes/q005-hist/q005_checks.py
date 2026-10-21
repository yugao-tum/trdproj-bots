#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent checks for q005 v2/v3 frozen-scope figures and DST dedup."""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent


def stats(rows):
    sel = rows[rows.triggered]
    if sel.empty:
        return (0, float("nan"), float("nan"), float("nan"))
    return (len(sel), float(sel.net_per_share.mean()),
            float(sel.net_per_share.median()), float(sel.win.mean()))


def ts(s):
    return datetime.fromisoformat(s).timestamp()


def dedup_gap(rows):
    kept, last = [], None
    for _, r in rows.sort_values("window_end_utc").iterrows():
        e = ts(r.window_end_utc)
        if last is None or e - last >= 48 * 3600:
            kept.append(r)
            last = e
    return pd.DataFrame(kept)


def dedup_overlap(rows):
    kept, last_end = [], None
    for _, r in rows.sort_values("window_end_utc").iterrows():
        start = ts(r.window_start_utc)
        if last_end is None or start >= last_end:
            kept.append(r)
            last_end = ts(r.window_end_utc)
    return pd.DataFrame(kept)


for name in ("events_v1.csv", "events.csv"):
    df = pd.read_csv(BASE / name)
    er = df[df.series == "elon48"]
    old = dedup_gap(er)
    new = dedup_overlap(er)
    print(f"{name} frozen Elon48: rows={len(er)}, triggered(no dedup)={int(er.triggered.sum())}")
    print(f"  old absolute-48h dedup -> kept={len(old)}, triggered n/mean/median/hit={stats(old)}")
    print(f"  new overlap dedup      -> kept={len(new)}, triggered n/mean/median/hit={stats(new)}")
    for slug in ("elon-musk-of-tweets-march-5-march-7",
                 "elon-musk-of-tweets-march-7-march-9"):
        r = er[er.slug == slug]
        if len(r):
            r = r.iloc[0]
            print(f"  {slug}: start={r.window_start_utc} end={r.window_end_utc} "
                  f"triggered={bool(r.triggered)} net_per_share={r.net_per_share} "
                  f"kept_new={slug in set(new.slug)}")

ver = json.loads((BASE / "_cache" / "fetch_meta.json").read_text())
print(f"access_date_utc={ver['access_date_utc']}")
