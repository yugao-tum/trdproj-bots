#!/usr/bin/env python3
"""quant-007: re-fetch EVERY source cited by the entry and print what it says.

No credentials, all keyless public GETs. Prints HTTP status, byte size and the
specific field/quote the entry relies on, so each claim can be checked line by line.
"""
import json, os, time, urllib.request, urllib.error, urllib.parse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []


def fetch(url, headers=None, timeout=90, tries=3):
    last = (0, b"", {})
    for a in range(tries):
        req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)
        except Exception as e:
            last = (0, str(e).encode(), {})
            time.sleep(1.5 * (a + 1))
    return last


def line(tag, st, body, extra=""):
    print("%-58s HTTP %-3s %9d B  %s" % (tag, st, len(body), extra))
    if st != 200:
        FAILS.append((tag, st))


def jget(url, tag):
    st, b, _ = fetch(url)
    line(tag, st, b)
    return st, (json.loads(b) if st == 200 and b[:1] in b"[{" else None)


print("== A. Gamma events/markets (entry rules, arms, prices, fees) ==")
u = "https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-october"
st, e = jget(u, "gamma october event")
if e:
    e = e[0]
    d = e["description"]
    print("  id=%s startDate=%s endDate=%s updatedAt=%s" % (e["id"], e["startDate"], e["endDate"], e.get("updatedAt")))
    print("  negRisk=%s arms=%d volume=%.2f liquidity=%.2f" % (e["negRisk"], len(e["markets"]), e["volume"], e.get("liquidity", 0)))
    quotes = ["checked on October 31, 2026, 12:00 PM ET",
              "https://arena.ai/leaderboard/text/overall-no-style-control",
              "style control off (Adjustments: None)",
              "Models marked \u201cAutoEval\u201d",
              "ordered primarily by their leaderboard rank",
              "including any underlying, unrounded, granular values",
              "would be ranked ahead",
              'resolve to "Other"']
    for q in quotes:
        print("  quote %-72s %s" % (q[:72], q in d))
    names = [m["groupItemTitle"] for m in e["markets"]]
    named = [n for n in names if not n.startswith("Company") and n != "Other"]
    ph = [n for n in names if n.startswith("Company") or n == "Other"]
    print("  named=%d placeholders=%d named_arms=%s" % (len(named), len(ph), named))
    print("  placeholder_arms=%s" % ph)
    s = sum(float(json.loads(m["outcomePrices"])[0]) for m in e["markets"]
            if m["groupItemTitle"] in named)
    print("  named-arm Yes sum = %.4f" % s)
    fees = {}
    for m in e["markets"]:
        fs = json.dumps(m.get("feeSchedule"), sort_keys=True)
        fees[fs] = fees.get(fs, 0) + 1
    print("  feeSchedule distribution:", fees)
    for nm in ("Google", "Anthropic", "OpenAI"):
        m = [x for x in e["markets"] if x["groupItemTitle"] == nm][0]
        print("  %-9s last=%s bid=%s ask=%s tick=%s spread=%s" % (
            nm, m.get("lastTradePrice"), m.get("bestBid"), m.get("bestAsk"),
            m.get("orderPriceMinTickSize"), m.get("spread")))
    print("  orderMinSize=%s (unique %s)" % (
        [m.get("orderMinSize") for m in e["markets"]][:1],
        sorted({m.get("orderMinSize") for m in e["markets"]})))

u = "https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-november"
st, e2 = jget(u, "gamma november event")
if e2:
    e2 = e2[0]
    names = [m["groupItemTitle"] for m in e2["markets"]]
    print("  endDate=%s arms=%d volume=%.2f" % (e2["endDate"], len(e2["markets"]), e2["volume"]))
    print("  placeholders=%s" % [n for n in names if n.startswith("Company") or n == "Other"])
    for nm in ("Google", "Anthropic", "OpenAI"):
        m = [x for x in e2["markets"] if x["groupItemTitle"] == nm][0]
        print("  %-9s last=%s bid=%s ask=%s spread=%s" % (
            nm, m.get("lastTradePrice"), m.get("bestBid"), m.get("bestAsk"), m.get("spread")))

st, s = jget("https://gamma-api.polymarket.com/series/10030", "gamma series 10030")
if s:
    print("  title=%s recurrence=%s createdAt=%s restricted=%s" % (
        s["title"], s["recurrence"], s["createdAt"], s["restricted"]))

st, ce = jget("https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true",
              "gamma closed events")
if ce:
    ce = sorted(ce, key=lambda x: x["endDate"])
    print("  count=%d first=%s %s last=%s %s" % (
        len(ce), ce[0]["slug"], ce[0]["endDate"], ce[-1]["slug"], ce[-1]["endDate"]))
    print("  arms per event=%s" % [len(x["markets"]) for x in ce])
    print("  rank-column-rule events=%d" % sum("arena rank" in (x.get("description") or "") for x in ce))
    wins = {x["slug"]: [m["groupItemTitle"] for m in x["markets"]
                        if json.loads(m["outcomePrices"])[0] == "1"] for x in ce}
    print("  events with exactly one settled winner=%d/%d" % (
        sum(len(v) == 1 for v in wins.values()), len(wins)))

st, oe = jget("https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=false",
              "gamma open events")
if oe:
    print("  count=%d slugs=%s" % (len(oe), [x["slug"] for x in oe]))

print("\n== B. CLOB books cited in entry (now empty, as entry says) ==")
for nm, tok in [("Google", "111088620532234518037120406087772586039940496346205331791940213760503764823657"),
                ("Anthropic", "17398972530137600675762712744895375915722542439211248541948693649429200536957")]:
    st, b, _ = fetch("https://clob.polymarket.com/book?token_id=" + tok)
    line("clob book %s" % nm, st, b)
    if st == 200:
        d = json.loads(b)
        print("   bids[:2]=%s asks[:2]=%s" % (d["bids"][:2], d["asks"][:2]))

print("\n== C. historical price / trades endpoints ==")
u = ("https://clob.polymarket.com/prices-history?market=114976310403134140071475285729050128086700898119247346798479138721789575328536"
     "&interval=max&fidelity=1440")
st, b, _ = fetch(u); line("clob prices-history closed 2026-09", st, b)
if st == 200:
    h = json.loads(b).get("history", [])
    print("   points=%d first_t=%s last_t=%s last_p=%s" % (
        len(h), h[0]["t"] if h else None, h[-1]["t"] if h else None, h[-1]["p"] if h else None))

u = ("https://data-api.polymarket.com/trades?market=0x537df24dbae425e973a421983b6ee570d582cac06b5fdbebef099d3d07913985"
     "&limit=1000")
st, b, _ = fetch(u); line("data-api trades closed event", st, b)
if st == 200:
    t = json.loads(b)
    print("   trades=%d fields=%s" % (len(t), sorted(t[0].keys()) if t else []))

print("\n== D. resolution source pages (entry claims 403) ==")
for u in ["https://arena.ai/leaderboard/text/overall-no-style-control",
          "https://arena.ai/leaderboard/text/overall",
          "https://arena.ai/api/leaderboard/text",
          "https://lmarena.ai/leaderboard/text"]:
    st, b, _ = fetch(u)
    print("%-62s HTTP %-3s %8d B  (expect 403)" % (u, st, len(b)))

print("\n== E. Wayback CDX indexes ==")
for u, tag in [
    ("https://web.archive.org/cdx/search/cdx?url=arena.ai/leaderboard/text/overall-no-style-control&output=json&limit=6&from=2026&filter=statuscode:200", "cdx arena"),
    ("https://web.archive.org/cdx/search/cdx?url=lmarena.ai/leaderboard/text&output=json&limit=5&from=2026&filter=statuscode:200", "cdx lmarena"),
]:
    st, b, _ = fetch(u); line(tag, st, b, b[:180].decode("utf-8", "replace"))

print("\n== F. HuggingFace leaderboard mirror ==")
st, h = jget("https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset", "hf dataset api")
if h:
    print("  gated=%s private=%s lastModified=%s" % (h["gated"], h["private"], h["lastModified"]))
    print("  license=%s" % [t for t in h["tags"] if t.startswith("license")])

st, b, _ = fetch("https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/raw/main/README.md")
line("hf README.md", st, b)
if st == 200:
    txt = b.decode("utf-8", "replace")
    for cfg in ("text", "text_style_control"):
        print("  config %-18s present=%s" % (cfg, ("config_name: " + cfg) in txt))
    for col in ("model_name", "organization", "rating", "rank", "category", "leaderboard_publish_date"):
        print("  schema column %-24s present=%s" % (col, ("name: " + col) in txt))
    print("  license line=%s" % [x for x in txt.splitlines() if x.startswith("license:")])

st, b, hd = fetch("https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/resolve/main/text/full-00000-of-00001.parquet",
                   headers={"User-Agent": UA, "Range": "bytes=0-3"})
line("hf text parquet (range 0-3)", st, b, "content-range=%s" % hd.get("Content-Range"))
print("  parquet magic=%r" % b[:4])

for cfg in ("text", "text_style_control"):
    u = ("https://datasets-server.huggingface.co/statistics?dataset=lmarena-ai%2Fleaderboard-dataset"
     "&config=" + cfg + "&split=full")
    st, b, _ = fetch(u, timeout=120)
    line("hf stats %s" % cfg, st, b)
    if st == 200:
        d = json.loads(b)
        print("   rows=%d" % d["num_examples"])
        for col in d["statistics"]:
            if col["column_name"] == "category":
                print("   overall_rows=%s" % col["column_statistics"]["frequencies"].get("overall"))
            if col["column_name"] == "leaderboard_publish_date":
                print("   date_min=%s date_max=%s" % (
                    col["column_statistics"]["min"], col["column_statistics"]["max"]))

st, b, _ = fetch("https://datasets-server.huggingface.co/rows?dataset=lmarena-ai%2Fleaderboard-dataset&config=text&split=full&offset=0&length=3")
line("hf datasets-server rows", st, b)
if st == 200:
    d = json.loads(b)
    print("  fields=%s" % [f["name"] for f in d["features"]])

print("\n== G. HF mirror rank-1 spot checks against the backtest snapshot dates ==")
import pandas as pd
raw = pd.read_csv(os.path.join(HERE, "backtest_raw.csv"))
spot = raw[(raw.lead == 7)][["slug", "snap", "lb_arm", "lb_model"]].dropna().drop_duplicates("snap")
for _, r in spot.tail(3).iterrows():
    where = ('"category"=\'overall\' AND "leaderboard_publish_date"=\'%s\' AND "rank"=1' % r["snap"])
    q = urllib.parse.urlencode({"dataset": "lmarena-ai/leaderboard-dataset", "config": "text",
                                "split": "full", "where": where, "length": 3})
    st, b, _ = fetch("https://datasets-server.huggingface.co/filter?" + q, timeout=120, tries=2)
    if st == 200:
        d = json.loads(b)
        rows = [x["row"] for x in d.get("rows", [])]
        got = (rows[0]["organization"], rows[0]["model_name"]) if rows else None
        print("  snap %s: mirror=%s expected_arm=%s expected_model=%s match=%s"
              % (r["snap"], got, r["lb_arm"], r["lb_model"],
                 bool(got) and got[0].lower() == str(r["lb_arm"]).lower()
                 and got[1] == r["lb_model"]))
    else:
        print("  snap %s: HTTP %s (未取到)" % (r["snap"], st))

print("\n== H. merged notes reused by this entry ==")
for p in ["../../../../notes/batch1-verification/quant-007.md",
          "../../../../notes/r1-audit/AUDIT.md",
          "REPORT.md", "q007_hist.py", "q007_analyze.py", "q007_fills.py",
          "q007_verify.py", "q007_hist_sc.py", "fetch_output.txt",
          "analyze_output.txt", "fills_output.txt", "verify_output.txt",
          "fetch_sc_output.txt", "backtest_raw.csv", "backtest_sc.csv",
          "q007_trades.py", "q007_trades_output.txt", "q007_trades_fills.csv"]:
    fp = os.path.normpath(os.path.join(HERE, p))
    print("  %-52s exists=%s size=%s" % (p, os.path.exists(fp), os.path.getsize(fp) if os.path.exists(fp) else "-"))

print("\n== SUMMARY ==")
bad = [(t, st) for t, st in FAILS if st not in (206,)]
print("hard failures (excluding expected 403/206):", bad if bad else "none")
print("note: arena/lmarena 403 is the entry's stated fact; parquet 206 is a range GET")
