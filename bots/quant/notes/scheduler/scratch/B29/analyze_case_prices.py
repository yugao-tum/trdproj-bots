import json,datetime
d=json.load(open("bots/quant/notes/scheduler/scratch/B29/_cache/case_prices.json"))
def daily(h):
    out={}
    for x in h:
        day=datetime.datetime.utcfromtimestamp(x["t"]).strftime("%Y-%m-%d")
        out[day]=x["p"]
    return out
for slug,ms in d.items():
    print("="*90); print(slug)
    for m in ms:
        dd=daily(m["hist"])
        days=sorted(dd)
        print(" ",m["q"][:70],"out",m["out"])
        if days:
            # print every ~5 days and last
            sel=[days[0]]+[x for i,x in enumerate(days) if i%5==0]+[days[-1]]
            print("   ",[(x,dd[x]) for x in sorted(set(sel))])
