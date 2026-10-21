import requests,json,os,time,datetime
CACHE="bots/quant/notes/scheduler/scratch/B29/_cache"
cases=json.load(open("/tmp/kpi_cases.json"))
want={
 "costco-q3-us-adjusted-comparable-sales-growth":None,
 "boeing-airplane-deliveries-above-in-q1":None,
 "will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419":None,
 "united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130":None,
 "delta-dal-q2-passenger-load-factor":None,
}
out={}
for slug in want:
    e=cases[slug]; out[slug]=[]
    for m in e["markets"]:
        cid=m["conditionId"]
        p=os.path.join(CACHE,f"trades_{cid[:16]}.json")
        if os.path.exists(p): tr=json.load(open(p))
        else:
            tr=[]; off=0
            while off<20000:
                r=requests.get("https://data-api.polymarket.com/trades",params={"market":cid,"limit":1000,"offset":off},timeout=40)
                d=r.json() if r.status_code==200 else []
                if not d: break
                tr+=d; off+=len(d)
                if len(d)<1000: break
                time.sleep(0.1)
            json.dump(tr,open(p,"w"))
        out[slug].append({"q":m["question"],"cond":cid,"trades":tr,"history":m.get("outcomePrices")})
        print(slug[:40],m["question"][-30:],"trades",len(tr))
json.dump(out,open(os.path.join(CACHE,"case_trades.json"),"w"))
