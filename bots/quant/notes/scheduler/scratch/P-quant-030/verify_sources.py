"""Re-fetch the sources cited by quant-030 and print HTTP status plus a short,
verifiable snippet. Run from the repo root:
    python3 bots/quant/notes/scheduler/scratch/P-quant-030/verify_sources.py
"""
import re
import requests

UA = {"User-Agent": "quant-research/2026 (public data; contact research@example.com)"}

EVENTS = [
    "united-airlines-ual-q3-consolidated-passenger-load-factor-20261008120016000",
    "mcdonalds-mcd-q3-global-comparable-sales-growth-20261008120128000",
    "united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130",
    "delta-dal-q2-passenger-load-factor",
    "costco-q3-us-adjusted-comparable-sales-growth",
    "boeing-airplane-deliveries-above-in-q1",
    "will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419",
]

PAGES = [
    ("boeing", "https://investors.boeing.com/investors/news/press-release-details/2026/Boeing-Announces-First-Quarter-Deliveries/default.aspx", ["Total 143", "April 14, 2026"]),
    ("tsmc_monthly", "https://investor.tsmc.com/english/monthly-revenue/2026", ["410,726", "416,975", "442,680"]),
    ("tsmc_3323", "https://pr.tsmc.com/english/news/3323", ["442.68", "2,404.48"]),
    ("tsmc_3326", "https://pr.tsmc.com/english/news/3326", ["1,270.38", "40.20"]),
    ("sec_tsmc_apr", "https://www.sec.gov/Archives/edgar/data/1046179/000104617926000213/tsm-revenue20260508.htm", ["410.73"]),
    ("sec_tsmc_may", "https://www.sec.gov/Archives/edgar/data/1046179/000104617926000367/tsm-revenue20260610.htm", ["416.98"]),
    ("sec_tsmc_june", "https://www.sec.gov/Archives/edgar/data/1046179/000104617926000447/tsm-revenue20260713.htm", ["442.68", "2,404.48"]),
    ("sec_tsmc_q2", "https://www.sec.gov/Archives/edgar/data/1046179/000104617926000451/a2q26e_withguidancexfinal.htm", ["1,270.38", "40.20", "31.60"]),
    ("costco_apr", "https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-April-Sales-Results/default.aspx", ["8.0%", "7.8%"]),
    ("costco_q3", "https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-Third-Quarter-and-Year-To-Date-Operating-Results-For-Fiscal-2026/default.aspx", ["6.8%", "6.6%"]),
    ("fool_march", "https://www.fool.com/investing/2026/05/08/is-costco-stock-a-buy-sell-or-hold-after-april-sal/", ["6.2%"]),
    ("sec_dal", "https://www.sec.gov/Archives/edgar/data/27904/000002790426000031/dal-20260630.htm", ["84.8", "66,767", "78,694"]),
    ("sec_ual", "https://www.sec.gov/Archives/edgar/data/0000100517/000010051726000135/ual_erx06302026xex991.htm", ["83.4", "72,765", "87,279"]),
    ("airside_ual", "https://theairside.news/en/invest-united", ["82.3", "82.4", "85.9"]),
    ("airside_dal", "https://theairside.news/en/invest-delta", ["82.7", "84.9", "88.1"]),
    ("bts_t100", "https://data.bts.gov/resource/q4tb-tbff.json", []),
]


def snippet(text, needles):
    text = re.sub(r"\s+", " ", text)
    hits = []
    for n in needles:
        i = text.find(n)
        if i >= 0:
            hits.append(f"{n}@ {text[max(0, i - 45):i + len(n) + 45]}")
    return " | ".join(hits) if hits else "(needle not found)"


print("== Gamma events ==")
for slug in EVENTS:
    r = requests.get("https://gamma-api.polymarket.com/events", params={"slug": slug}, headers=UA, timeout=40)
    d = r.json() if r.status_code == 200 else []
    e = d[0] if isinstance(d, list) and d else {}
    print(f"{slug}: HTTP {r.status_code}, markets={len(e.get('markets', []))}, title={e.get('title')!r}")

print("\n== Official / reference pages ==")
for name, url, needles in PAGES:
    try:
        r = requests.get(url, headers=UA, timeout=40)
        print(f"{name}: HTTP {r.status_code}, bytes={len(r.content)}")
        if r.status_code == 200 and needles:
            print("  ", snippet(r.text, needles))
    except Exception as e:
        print(f"{name}: ERROR {type(e).__name__}: {e}")

print("\n== CLOB prices-history window boundary ==")
import datetime, json

def ts(s):
    return int(datetime.datetime.fromisoformat(s).replace(tzinfo=datetime.timezone.utc).timestamp())

e = requests.get("https://gamma-api.polymarket.com/events",
                 params={"slug": "will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419"},
                 headers=UA, timeout=40).json()[0]
tok = json.loads(e["markets"][2]["clobTokenIds"])[0]
for days in (15, 16):
    r = requests.get("https://clob.polymarket.com/prices-history",
                     params={"market": tok, "startTs": ts("2026-07-20T00:00:00") - days * 86400,
                             "endTs": ts("2026-07-20T00:00:00"), "fidelity": 60},
                     headers=UA, timeout=40)
    n = len(r.json().get("history", [])) if r.status_code == 200 else "-"
    print(f"TSM $41B {days}d: HTTP {r.status_code}, points={n}, body={r.text[:90]}")

print("\n== Boeing CLOB points are all after the 18:27 trade ==")
e = requests.get("https://gamma-api.polymarket.com/events",
                 params={"slug": "boeing-airplane-deliveries-above-in-q1"},
                 headers=UA, timeout=40).json()[0]
for m in e["markets"]:
    if m.get("groupItemTitle") in ("140", "145"):
        tok = json.loads(m["clobTokenIds"])[0]
        r = requests.get("https://clob.polymarket.com/prices-history",
                         params={"market": tok, "startTs": ts("2026-04-10T00:00:00"),
                                 "endTs": ts("2026-04-15T00:00:00"), "fidelity": 60},
                         headers=UA, timeout=40)
        pts = [(datetime.datetime.fromtimestamp(x["t"], datetime.timezone.utc).strftime("%Y-%m-%d %H:%MZ"), x["p"])
               for x in r.json().get("history", [])]
        print(f"Boeing above-{m['groupItemTitle']}: HTTP {r.status_code}, {pts}")
