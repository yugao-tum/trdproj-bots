import json, os, datetime

CACHE = "bots/quant/notes/scheduler/scratch/P-quant-030/_cache"


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def load(slug):
    return json.load(open(os.path.join(CACHE, f"event_{slug}.json")))


def show(slug, lo, hi, only=None):
    e = load(slug)
    print("=" * 110)
    print(slug, lo, "->", hi)
    for m in e["markets"]:
        cid = m["conditionId"]
        tr = json.load(open(os.path.join(CACHE, f"trades_{cid}.json")))
        sel = [t for t in tr if lo <= fmt(t["timestamp"]) <= hi]
        if only:
            sel = [t for t in sel if t.get("outcome") in only]
        if not sel:
            continue
        print("--", m.get("groupItemTitle") or m["question"], "|", len(sel), "trades")
        for t in sorted(sel, key=lambda x: x["timestamp"]):
            print("   ", fmt(t["timestamp"]), t["side"], f"px={t['price']:.6f}",
                  t.get("outcome"), f"sz={t['size']}")


show("will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419",
     "2026-07-13 05:00:00", "2026-07-13 08:00:00")
show("boeing-airplane-deliveries-above-in-q1",
     "2026-04-14 00:00:00", "2026-04-14 23:59:59")
show("costco-q3-us-adjusted-comparable-sales-growth",
     "2026-05-20 00:00:00", "2026-05-29 23:59:59")
show("united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130",
     "2026-07-01 00:00:00", "2026-07-02 23:59:59")
show("delta-dal-q2-passenger-load-factor",
     "2026-07-01 00:00:00", "2026-07-03 23:59:59")
