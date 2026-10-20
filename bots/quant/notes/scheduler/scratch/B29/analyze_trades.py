import json,datetime
d=json.load(open("bots/quant/notes/scheduler/scratch/B29/_cache/case_trades.json"))
def fmt(t): return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime("%m-%d %H:%M")
for slug,ms in d.items():
    print("="*100); print(slug)
    for m in ms:
        print("--",m["q"],"out",m["history"])
        rows=[]
        for tr in m["trades"]:
            yes = tr["price"] if tr.get("outcome")=="Yes" else 1-tr["price"]
            rows.append((tr["timestamp"],tr["side"],tr["price"],tr.get("outcome"),yes,tr["size"]))
        rows.sort()
        for r in rows:
            print("   ",fmt(r[0]),r[1],f"px={r[2]:.4f}",r[3],f"yes={r[4]:.4f}",f"sz={r[5]:.1f}")
