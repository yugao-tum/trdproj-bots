import requests, json, time, os, datetime
CACHE="bots/quant/notes/scheduler/scratch/B29/_cache"
os.makedirs(CACHE,exist_ok=True)
cases=json.load(open("/tmp/kpi_cases.json"))
def ts(s): return int(datetime.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def history(tok,start,end):
    key=f"{tok[-24:]}_{start}_{end}.json"
    p=os.path.join(CACHE,key)
    if os.path.exists(p): return json.load(open(p))
    r=requests.get("https://clob.polymarket.com/prices-history",params={"market":tok,"startTs":start,"endTs":end,"fidelity":60},timeout=40)
    d=r.json().get("history",[]) if r.status_code==200 else []
    json.dump(d,open(p,"w")); time.sleep(0.1); return d
def hist_range(tok,a,b):
    """a,b ISO dates; chunk 6 days"""
    s=datetime.datetime.fromisoformat(a); e=datetime.datetime.fromisoformat(b)
    out=[]
    while s<e:
        nxt=min(s+datetime.timedelta(days=6),e)
        out+=history(tok,int(s.replace(tzinfo=datetime.timezone.utc).timestamp()),int(nxt.replace(tzinfo=datetime.timezone.utc).timestamp()))
        s=nxt
    return out
windows={
 "boeing-airplane-deliveries-above-in-q1":("2026-03-25","2026-04-23"),
 "will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419":("2026-06-25","2026-07-18"),
 "united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130":("2026-06-20","2026-07-16"),
 "delta-dal-q2-passenger-load-factor":("2026-06-20","2026-07-11"),
 "united-airlines-ual-q3-consolidated-passenger-load-factor-20261008120016000":("2026-09-15","2026-10-20"),
 "costco-q3-us-adjusted-comparable-sales-growth":("2026-05-01","2026-05-29"),
}
out={}
for slug,e in cases.items():
    if slug not in windows: continue
    a,b=windows[slug]
    out[slug]=[]
    for m in e["markets"]:
        toks=json.loads(m["clobTokenIds"]) if isinstance(m.get("clobTokenIds"),str) else m.get("clobTokenIds")
        tok=toks[0]
        h=hist_range(tok,a,b)
        out[slug].append({"q":m["question"],"token":tok,"hist":h,"out":m.get("outcomePrices"),"end":m.get("endDate")})
    print(slug, [(x["q"][-16:],len(x["hist"])) for x in out[slug]])
json.dump(out,open("bots/quant/notes/scheduler/scratch/B29/_cache/case_prices.json","w"))
