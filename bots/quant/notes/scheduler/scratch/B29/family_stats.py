import json,collections,re
closed=json.load(open("/tmp/kpis_closed.json"))
op=json.load(open("/tmp/kpis_open.json"))
def stat(E,name):
    ev=len(E); mk=sum(len(e.get("markets",[])) for e in E)
    fees=collections.Counter()
    for e in E:
        for m in e.get("markets",[]):
            f=m.get("feeSchedule") or {}
            fees[f.get("rate")]+=1
    vol=[e.get("volume") or 0 for e in E]
    print(name,"events",ev,"markets",mk)
    print("  fee rates:",dict(fees))
    print("  event volume: sum %.0f median %.0f p90 %.0f max %.0f"%(sum(vol),sorted(vol)[len(vol)//2],sorted(vol)[int(len(vol)*0.9)],max(vol)))
    print("  endDate months:",dict(sorted(collections.Counter((e.get("endDate") or "")[:7] for e in E).items())))
stat(closed,"CLOSED"); stat(op,"OPEN")
kw=["load factor","comparable sales","comparable store sales","same restaurant","same store","revenue","organic","monthly active","mau","subscriber","deliveries","shipments","orders","margin","arr","bookings","traffic"]
c=collections.Counter()
for e in closed:
    t=e["title"].lower()
    for k in kw:
        if k in t: c[k]+=1
print("closed metric keywords:",c.most_common())
# market counts per event distribution
mc=collections.Counter(len(e.get("markets",[])) for e in closed)
print("closed markets-per-event:",dict(sorted(mc.items())))
