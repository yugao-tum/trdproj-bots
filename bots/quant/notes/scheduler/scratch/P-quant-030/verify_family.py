import requests, json, collections, os, time

CACHE = "bots/quant/notes/scheduler/scratch/P-quant-030/_cache"
os.makedirs(CACHE, exist_ok=True)


def get(url, params):
    r = requests.get(url, params=params, timeout=40)
    r.raise_for_status()
    return r.json()


def fetch(tag, closed):
    key = f"events_{tag}_{'closed' if closed else 'open'}.json"
    p = os.path.join(CACHE, key)
    if os.path.exists(p):
        return json.load(open(p))
    out = []
    off = 0
    while True:
        d = get("https://gamma-api.polymarket.com/events",
                {"tag_slug": tag, "limit": 100, "offset": off,
                 "closed": "true" if closed else "false",
                 "order": "endDate", "ascending": "false" if closed else "true"})
        if not d:
            break
        out += d
        off += len(d)
        if len(d) < 100:
            break
        time.sleep(0.1)
    json.dump(out, open(p, "w"))
    return out


def stat(E, name):
    ev = len(E)
    mk = sum(len(e.get("markets", [])) for e in E)
    fees = collections.Counter()
    ftypes = collections.Counter()
    for e in E:
        for m in e.get("markets", []):
            f = m.get("feeSchedule") or {}
            fees[f.get("rate")] += 1
            ftypes[m.get("feeType")] += 1
    vol = [e.get("volume") or 0 for e in E]
    vol.sort()
    print(name, "events", ev, "markets", mk)
    print("  fee rates:", dict(fees))
    print("  feeType:", dict(ftypes))
    print("  event volume: sum %.0f median %.0f p90 %.0f max %.0f" % (
        sum(vol), vol[len(vol) // 2], vol[int(len(vol) * 0.9)], max(vol)))
    print("  endDate months:", dict(sorted(collections.Counter((e.get("endDate") or "")[:7] for e in E).items())))
    return vol


closed = fetch("kpis", True)
op = fetch("kpis", False)
stat(closed, "CLOSED")
stat(op, "OPEN")

kw = ["load factor", "comparable sales", "comparable store sales", "same restaurant",
      "same store", "revenue", "organic", "monthly active", "mau", "subscriber",
      "deliveries", "shipments", "orders", "margin", "arr", "bookings", "traffic"]
c = collections.Counter()
for e in closed:
    t = e["title"].lower()
    for k in kw:
        if k in t:
            c[k] += 1
print("closed metric keywords:", c.most_common())
print("closed markets-per-event:", dict(sorted(collections.Counter(
    len(e.get("markets", [])) for e in closed).items())))
