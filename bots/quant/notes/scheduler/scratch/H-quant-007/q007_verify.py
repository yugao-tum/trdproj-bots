#!/usr/bin/env python3
"""Re-fetch every source cited by quant-007 and print what it actually says."""
import json, urllib.request, urllib.error, ssl

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read()
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()


def line(tag, status, body, extra=""):
    print("%-58s HTTP %-3s %8d B  %s" % (tag, status, len(body), extra))


print("== 1. Gamma: October 2026 event ==")
u = "https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-october"
st, b = fetch(u)
line("gamma october event", st, b)
e = json.loads(b)[0]
print("  id", e["id"], "endDate", e["endDate"], "startDate", e["startDate"])
print("  negRisk", e["negRisk"], "arms", len(e["markets"]), "volume", round(e["volume"], 2),
      "liquidity", round(e.get("liquidity", 0), 2), "updatedAt", e.get("updatedAt"))
names = [m["groupItemTitle"] for m in e["markets"]]
print("  named", len([n for n in names if not n.startswith("Company") and n != "Other"]),
      "placeholders", len([n for n in names if n.startswith("Company") or n == "Other"]))
print("  feeSchedules", {json.dumps(m.get("feeSchedule")) for m in e["markets"]})
d = e["description"]
for frag in ["checked on October 31, 2026, 12:00 PM ET",
             "overall-no-style-control", "Adjustments: None", "AutoEval",
             "ordered primarily by their leaderboard rank",
             "unrounded, granular values", "would be ranked ahead of", "Other"]:
    print("  quote contains %-45s %s" % (frag, frag in d))
g = [m for m in e["markets"] if m["groupItemTitle"] == "Google"][0]
a = [m for m in e["markets"] if m["groupItemTitle"] == "Anthropic"][0]
for nm, m in (("Google", g), ("Anthropic", a)):
    print("  %-9s last %s bid %s ask %s tick %s spread %s" % (
        nm, m.get("lastTradePrice"), m.get("bestBid"), m.get("bestAsk"),
        m.get("orderPriceMinTickSize"), m.get("spread")))
named = [float(json.loads(m["outcomePrices"])[0]) for m in e["markets"]
         if not m["groupItemTitle"].startswith("Company") and m["groupItemTitle"] != "Other"]
print("  named-arm Yes sum %.4f (n=%d)" % (sum(named), len(named)))

print("\n== 2. Gamma: November 2026 event ==")
u = "https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-november"
st, b = fetch(u); line("gamma november event", st, b)
e2 = json.loads(b)[0]
print("  endDate", e2["endDate"], "arms", len(e2["markets"]), "volume", round(e2["volume"], 2))
for nm in ("Google", "Anthropic", "OpenAI"):
    m = [x for x in e2["markets"] if x["groupItemTitle"] == nm][0]
    print("  %-9s bid %s ask %s spread %s" % (nm, m.get("bestBid"), m.get("bestAsk"), m.get("spread")))

print("\n== 3. Gamma: series 10030 ==")
st, b = fetch("https://gamma-api.polymarket.com/series/10030"); line("series 10030", st, b)
s = json.loads(b)
print("  title", s["title"], "| recurrence", s["recurrence"], "| createdAt", s["createdAt"], "| restricted", s["restricted"])

print("\n== 4. Gamma: closed events (count, first/last, rules) ==")
st, b = fetch("https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true"); line("closed events", st, b)
ce = json.loads(b)
ce = sorted(ce, key=lambda x: x["endDate"])
print("  count", len(ce), "| first", ce[0]["slug"], ce[0]["endDate"], "| last", ce[-1]["slug"], ce[-1]["endDate"])
print("  arms per event", [len(x["markets"]) for x in ce])
print("  rank-column rule events:", sum("arena rank" in (x.get("description") or "") for x in ce))

print("\n== 5. Gamma: open events ==")
st, b = fetch("https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=false"); line("open events", st, b)
print("  count", len(json.loads(b)), [x["slug"] for x in json.loads(b)])

print("\n== 6. CLOB books cited in entry ==")
for nm, tok in [("Google", "111088620532234518037120406087772586039940496346205331791940213760503764823657"),
                ("Anthropic", "17398972530137600675762712744895375915722542439211248541948693649429200536957")]:
    st, b = fetch("https://clob.polymarket.com/book?token_id=" + tok)
    line("clob book %s" % nm, st, b)
    if st == 200:
        d = json.loads(b)
        print("   bids", d["bids"][:2], "asks", d["asks"][:2])

print("\n== 7. resolution-source pages (entry claims 403) ==")
for u in ["https://arena.ai/leaderboard/text/overall-no-style-control",
          "https://arena.ai/leaderboard/text/overall",
          "https://arena.ai/api/leaderboard/text",
          "https://lmarena.ai/leaderboard/text"]:
    st, b = fetch(u); line(u, st, b, "403 expected per entry")

print("\n== 8. Wayback CDX index ==")
st, b = fetch("https://web.archive.org/cdx/search/cdx?url=arena.ai/leaderboard/text/overall-no-style-control&output=json&limit=6&from=2026&filter=statuscode:200")
line("wayback cdx arena", st, b, b[:200].decode("utf-8", "replace"))

print("\n== 9. NEW source: HF lmarena leaderboard-dataset ==")
st, b = fetch("https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset")
line("hf dataset api", st, b)
if st == 200:
    h = json.loads(b)
    print("  gated", h["gated"], "private", h["private"], "lastModified", h["lastModified"])
    print("  license", [t for t in h["tags"] if t.startswith("license")])
st, b = fetch("https://datasets-server.huggingface.co/rows?dataset=lmarena-ai%2Fleaderboard-dataset&config=text&split=full&offset=0&length=3")
line("hf rows api", st, b)
if st == 200:
    h = json.loads(b)
    print("  fields", [f["name"] for f in h["features"]])
    print("  first row", h["rows"][0]["row"])
