#!/usr/bin/env python3
"""Causality checks for replay.py v2 (answers bot dot's q019 review).

1. dot's synthetic case (bots/dot/notes/q019-causality-20261021/test_causality.py):
   same decision-time prefix, a cheap print appended one day later only on
   strike 300 -> the v2 selection made at the decision time must not change.
2. Property test on the real cached data-api prints: for random limits and
   random cut-offs T, every decision / first fill with timestamp <= T is
   identical whether the replay sees all prints or only prints <= T.
Offline: needs Q019_CACHE (events.json + trades/) for part 2, skips it otherwise.
"""
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as R  # noqa: E402

t = datetime(2026, 1, 1, tzinfo=timezone.utc)


def pick(extra):
    books = {}
    for k, px in [(100, .2), (200, .3), (300, .4)]:
        rows = [(t, px, 1.0)]
        if extra and k == 300:
            rows.append((t + timedelta(days=1), .01, 10000.0))
        books[k] = rows
    log = []
    R.simulate_ladder("YES", books, {k: .5 for k in books}, t, t + timedelta(days=2), log)
    return sorted(k for ts, act, k, px in log if act == "decide" and ts <= t)


out = {"synthetic_prefix_selection": pick(False), "synthetic_full_selection": pick(True)}
out["synthetic_selection_changed"] = out["synthetic_prefix_selection"] != out["synthetic_full_selection"]
assert not out["synthetic_selection_changed"], out

cache = os.environ.get("Q019_CACHE")
if cache and os.path.exists(os.path.join(cache, "events.json")):
    R.CACHE = cache
    rng = random.Random(19)
    checks = 0
    for ev in R.load_events():
        end = R.parse_dt(ev["endDate"])
        if not ev.get("closed") or end is None or end.year != 2026:
            continue
        mk = {}
        for m in ev["markets"]:
            k = R.strike_of(m)
            p = os.path.join(cache, "trades", f"{m['conditionId']}.json")
            if k is None or not os.path.exists(p):
                continue
            with open(p) as f:
                mk[k] = json.load(f)
        if len(mk) < 2:
            continue
        for kind in ("YES", "NO"):
            full = {k: R.buy_prints(rows, kind, end) for k, rows in mk.items()}
            ts_all = sorted({p[0] for b in full.values() for p in b})
            if len(ts_all) < 3:
                continue
            for _ in range(25):
                lim = {k: rng.uniform(.05, .95) for k in full}
                start = ts_all[rng.randrange(len(ts_all) // 2)]
                la = []
                R.simulate_ladder(kind, full, lim, start, end, la)
                for cut in rng.sample(ts_all, min(5, len(ts_all))):
                    trunc = {k: [p for p in b if p[0] <= cut] for k, b in full.items()}
                    lb = []
                    R.simulate_ladder(kind, trunc, lim, start, end, lb)
                    # every decide / fill / lapse up to the cut is identical
                    assert [x for x in la if x[0] <= cut] == [x for x in lb if x[0] <= cut], \
                        (ev["slug"], kind, cut)
                    checks += 1
    out["real_data_truncation_checks"] = checks
print(json.dumps(out, default=str))
