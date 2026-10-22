#!/usr/bin/env python3
"""Offline re-check of every quantitative claim in the quant-019 entry.

Reads only files in this directory plus the merged verification note that holds
the original b16_flow.py output. No network, no look-ahead, no new parameters.
Exit code 0 iff every check passes.
"""
import csv
import json
import os
import random
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ENTRY = os.path.join(ROOT, "bots", "quant", "entries",
                     "quant-019-measles-cdc-count-ladder.md")

fails = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        fails.append(label)


def near(a, b, tol=5e-3):
    return abs(a - b) <= tol


# ---------------------------------------------------------------- flow anchors
# Numbers quoted verbatim in the entry; reproduce them from the CDC print and
# the two adjacent settled count windows.
cdc, cdc_day = 4410.0, 15
lo30, hi30 = 3600.0, 3700.0
f_lo = (cdc - hi30) / cdc_day
f_hi = (cdc - lo30) / cdc_day
f_mid = (f_lo + f_hi) / 2
check("anchor A flow low = 47.33/d", near(f_lo, 47.333, 0.01), f"{f_lo:.3f}")
check("anchor A flow high = 54.00/d", near(f_hi, 54.0, 0.01), f"{f_hi:.3f}")

# 50% level of the Oct-31 ladder: linear interpolation 4800@0.92 -> 4900@0.39
x50 = 4800 + (0.92 - 0.5) / (0.92 - 0.39) * 100
f_b = (x50 - cdc) / 16
ratio = f_mid / f_b
check("Oct-31 50% level = 4,879 cases", near(x50, 4879, 1.5), f"{x50:.1f}")
check("anchor B flow = 29.33/d", near(f_b, 29.33, 0.02), f"{f_b:.3f}")
check("anchor A/B ratio = 1.73x", near(ratio, 1.73, 0.01), f"{ratio:.3f}")

# ------------------------------------------------------------ replay artefacts
with open(os.path.join(HERE, "replay_summary.json")) as f:
    summary = json.load(f)
with open(os.path.join(HERE, "fills.csv"), newline="") as f:
    fills = list(csv.DictReader(f))

check("fills.csv rows = 17", len(fills) == 17, f"{len(fills)}")
check("independent events = 7", len(summary["per_event"]) == 7,
      f"{len(summary['per_event'])}")

yes = summary["variants"]["YES"]["all"]
no = summary["variants"]["NO"]["all"]
check("YES fills/cost/net/ret = 10/2043.16/-538.50/-26.36%",
      yes["fills"] == 10 and near(yes["cost"], 2043.16, 0.02)
      and near(yes["net"], -538.50, 0.02) and near(yes["ret"], -0.26356, 5e-4),
      f"{yes}")
check("NO fills/cost/net/ret = 7/503.22/-479.48/-95.28%",
      no["fills"] == 7 and near(no["cost"], 503.22, 0.02)
      and near(no["net"], -479.48, 0.02) and near(no["ret"], -0.95282, 5e-4),
      f"{no}")
check("max drawdown YES = 23.76%", near(summary["max_dd"]["YES"], 0.237648, 1e-5),
      f"{summary['max_dd']['YES']:.5f}")
check("contribution = -34.90% of 5,000",
      near(summary["contribution"], -0.34902, 1e-4),
      f"{summary['contribution']:.5f}")

# independent-result count and event-level dispersion
for kind in ("YES", "NO"):
    ev = {}
    for row in fills:
        if row["kind"] != kind:
            continue
        ev.setdefault(row["event"], [0.0, 0.0])
        ev[row["event"]][0] += float(row["cost"])
        ev[row["event"]][1] += float(row["net"])
    rets = [n / c for c, n in ev.values()]
    random.seed(19)
    boot = sorted(statistics.mean(random.choices(rets, k=len(rets)))
                  for _ in range(20000))
    lo, hi = boot[500], boot[19500]
    print(f"       {kind}: events={len(rets)} median={statistics.median(rets):+.4f} "
          f"mean={statistics.mean(rets):+.4f} bootstrap95=[{lo:+.4f},{hi:+.4f}]")
    if kind == "YES":
        check("YES event median < 0", statistics.median(rets) < 0)
        check("YES bootstrap CI crosses 0", lo < 0 < hi)
    else:
        check("NO bootstrap CI entirely < 0", hi < 0)

# failure criterion #1: median gross margin per YES share <= 0
gm = [float(r["payout"]) / float(r["shares"]) - float(r["avg_price"])
      for r in fills if r["kind"] == "YES"]
check("YES per-share gross median = -0.044 (<= 0: failure triggered)",
      near(statistics.median(gm), -0.04375, 5e-4),
      f"{statistics.median(gm):+.5f} n={len(gm)}")

# -------------------------------------------------------- entry consistency
text = open(ENTRY).read()
fm = text.split("---", 2)[1]
fields = dict(re.findall(r"^([a-z_0-9]+):\s*(.*)$", fm, re.M))
expect = {
    "evidence": "回放", "result": "不显著", "slot": "-",
    "variants": "4", "variants_ext": "-",
    "window": "2026-01-01..2026-10-01",
    "max_dd": "23.8%（按结算日累计已实现，非盯市）",
    "contribution": "-25.9%",
}
for k, v in expect.items():
    check(f"front matter {k}: {v}", fields.get(k) == v, repr(fields.get(k)))
check("entry keeps status: 待核 (task says do not change)", fields.get("status") == "待核")
check("entry keeps date: 2026-10-20 (task says do not change)",
      fields.get("date") == "2026-10-20")
for s in ("26.36%", "95.28%", "60.98%", "37.04%", "50.46%", "23.76%"):
    check(f"entry quotes {s}", s in text)

# ------------------------------------------------------------ source artefacts
dot = os.path.join(ROOT, "bots", "dot", "notes",
                   "20261021-goal-review-0920.md")
note = os.path.join(ROOT, "bots", "quant", "notes", "batch2-verification",
                    "quant-019.md")
check("dot causality review exists", os.path.exists(dot), dot)
check("merged b16_flow verification note exists", os.path.exists(note), note)
if os.path.exists(note):
    nt = open(note).read()
    for s in ("47.33..54.00", "29.33", "1.73", "4879 cases"):
        check(f"merged note contains {s}", s in nt)

print()
print(f"checks failed: {len(fails)}")
raise SystemExit(1 if fails else 0)
