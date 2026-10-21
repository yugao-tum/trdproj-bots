#!/usr/bin/env python3
"""Re-fetch every concrete source cited by quant-021 and check the claimed facts."""
import datetime as dt
import json
import pathlib
import re
import statistics as st
import urllib.error
import urllib.request

H = {"User-Agent": "quant-research/1.0"}
ROOT = pathlib.Path(__file__).resolve().parents[6]
REPLAY = ROOT / "bots" / "quant" / "replay" / "quant-021"
ENTRY = ROOT / "bots" / "quant" / "entries" / "quant-021-f1-pole-winner-base-rate.md"
fails = []


def get(url, timeout=60):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=H)
            with urllib.request.urlopen(req, timeout=timeout) as fh:
                return fh.status, json.load(fh)
        except urllib.error.HTTPError as exc:
            return exc.code, None
        except Exception:
            if attempt == 3:
                return None, None
    return None, None


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" | " + detail if detail else ""))
    if not ok:
        fails.append(label)
    return ok


def main():
    print("verified_at_utc", dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))

    print("\n=== Ergast-compatible API ===")
    sc, d = get("https://api.jolpi.ca/ergast/f1/2024/qualifying.json?limit=100&offset=0")
    mr = d["MRData"] if d else {}
    check("2024 qualifying HTTP 200", sc == 200, str(sc))
    check("limit=100 total=479", mr.get("limit") == "100" and mr.get("total") == "479",
          f"limit={mr.get('limit')} total={mr.get('total')}")
    sc, d = get("https://api.jolpi.ca/ergast/f1/2024/results.json?limit=100&offset=0")
    check("2024 results HTTP 200 and RaceTable", sc == 200 and d and "RaceTable" in d["MRData"], str(sc))
    sc, d = get("https://api.jolpi.ca/ergast/f1/2026.json")
    rows = d["MRData"]["RaceTable"]["Races"] if d else []
    check("2026 schedule HTTP 200 with Qualifying.date/time",
          sc == 200 and rows and all((r.get("Qualifying") or {}).get("date") for r in rows),
          f"{len(rows)} races")
    r24 = next(r for r in rows if False) if False else None
    # 2024 Italian GP: pole Norris, winner Leclerc (pagination-bug example in the entry)
    sc, q = get("https://api.jolpi.ca/ergast/f1/2024/qualifying.json?limit=100&offset=0")
    sc2, r = get("https://api.jolpi.ca/ergast/f1/2024/results.json?limit=100&offset=0")
    qrows = [x for x in (q or {}).get("MRData", {}).get("RaceTable", {}).get("Races", []) if x.get("round") == "16"]
    rrows = [x for x in (r or {}).get("MRData", {}).get("RaceTable", {}).get("Races", []) if x.get("round") == "16"]
    pole = None
    for x in qrows:
        for row in x.get("QualifyingResults", []):
            if row.get("position") == "1":
                pole = row["Driver"]["driverId"]
    winner = None
    for x in rrows:
        for row in x.get("Results", []):
            if row.get("position") == "1":
                winner = row["Driver"]["driverId"]
    print("2024 round 16 partial-page pole/winner", pole, winner)

    print("\n=== Gamma F1 family ===")
    events = []
    for off in range(0, 500, 100):
        sc, d = get(f"https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset={off}")
        check(f"gamma F1 page offset={off} HTTP 200", sc == 200 and isinstance(d, list), str(sc))
        if not isinstance(d, list) or not d:
            break
        events.extend(d)
    unique = {e["id"]: e for e in events}
    sel = [e for e in unique.values() if re.search(r"Winner|Pole|Podium", e.get("title", ""), re.I)]
    check("401 unique closed F1 events", len(unique) == 401, str(len(unique)))
    check("149 Winner/Pole/Podium events", len(sel) == 149, str(len(sel)))
    check("3433 markets in those events", sum(len(e.get("markets", [])) for e in sel) == 3433,
          str(sum(len(e.get("markets", [])) for e in sel)))
    winner_events = [e for e in sel if re.search(r"Winner", e.get("title", ""), re.I)
                     and not re.search(r"Pole|Podium", e.get("title", ""), re.I)]
    lens = sorted(len(e.get("markets", [])) for e in winner_events)
    check("winner events 9-39 markets, median 27 (entry instruments field)",
          len(winner_events) >= 49 and lens[0] == 9 and lens[-1] == 39 and st.median(lens) == 27,
          f"n={len(winner_events)} min={lens[0]} max={lens[-1]} median={st.median(lens)}")

    print("\n=== Gamma example events / rule quotes ===")
    phrases = {
        "f1-united-states-grand-prix-winner-2026-10-25": [
            "resolve in favor of the driver who is officially listed in first place in the Final Classification",
            "Disqualifications or changes made after the publication of the Final Classification will not affect market resolution",
            "rescheduled to a date after Nov 1, 2026",
        ],
        "f1-united-states-grand-prix-driver-pole-position-2026-10-24": [
            "officially recognized by Formula 1 as having set the fastest time during the qualifying session",
            "regardless of any subsequent penalties, disqualifications, or changes to the starting grid",
        ],
        "f1-united-states-grand-prix-driver-podium-2026-10-25": [
            "finishes within the top three positions in the official",
            "permanently canceled, this market will resolve 50-50",
        ],
        "f1-singapore-grand-prix-winner-2026-10-11": [
            "resolve in favor of the driver who is officially listed in first place in the Final Classification",
        ],
    }
    tokens = {}
    conditions = {}
    for slug, needles in phrases.items():
        sc, d = get("https://gamma-api.polymarket.com/events?slug=" + slug)
        event = d[0] if d else {}
        desc = event.get("description") or ""
        check(f"{slug} HTTP 200", sc == 200, str(sc))
        check(f"{slug} resolutionSource formula1", "formula1.com/en/results" in (event.get("resolutionSource") or ""),
              str(event.get("resolutionSource")))
        check(f"{slug} restricted=true", event.get("restricted") is True, str(event.get("restricted")))
        for needle in needles:
            check("  phrase: " + needle[:52], needle.lower() in desc.lower())
        rates = sorted({json.dumps(m.get("feeSchedule"), sort_keys=True) for m in event.get("markets", [])})
        check("  feeSchedule rate 0.05", bool(rates) and all('"rate": 0.05' in x for x in rates), str(rates))
        if event.get("markets"):
            m = event["markets"][0]
            tok = json.loads(m["clobTokenIds"])[0]
            tokens[slug] = tok
            conditions[slug] = m["conditionId"]
        if "singapore" in slug:
            yes = [(m.get("groupItemTitle"), m.get("outcomePrices")) for m in event.get("markets", [])
                   if m.get("outcomePrices") in ('["1", "0"]', '["1","0"]')]
            check("  resolved YES Verstappen", any("Verstappen" in (x[0] or "") for x in yes), str(yes))

    print("\n=== CLOB prices-history limits ===")
    token = tokens["f1-singapore-grand-prix-winner-2026-10-11"]
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    sc15, d15 = get(f"https://clob.polymarket.com/prices-history?market={token}&startTs={now-15*86400}&endTs={now}&fidelity=60")
    sc20, d20 = get(f"https://clob.polymarket.com/prices-history?market={token}&startTs={now-20*86400}&endTs={now}&fidelity=60")
    scmax, dmax = get(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&fidelity=60")
    scmix, dmix = get(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&startTs={now-14*86400}&endTs={now}&fidelity=60")
    check("15-day span HTTP 200", sc15 == 200, str(sc15))
    check("20-day span HTTP 400", sc20 == 400, str(sc20))
    check("interval=max HTTP 200 with points", scmax == 200 and dmax and len(dmax.get("history", [])) > 0,
          str(len(dmax.get("history", [])) if dmax else None))
    check("interval=max + start/end HTTP 200 with points",
          scmix == 200 and dmix and len(dmix.get("history", [])) > 0,
          str(len(dmix.get("history", [])) if dmix else None))

    print("\n=== data-api trades ===")
    cid = conditions["f1-singapore-grand-prix-winner-2026-10-11"]
    sc, d = get(f"https://data-api.polymarket.com/trades?market={cid}&limit=3&offset=0&takerOnly=true")
    check("data-api HTTP 200 with trades", sc == 200 and isinstance(d, list) and bool(d), str(sc))
    check("fields side/price/size/timestamp/asset/outcome",
          bool(d) and {"side", "price", "size", "timestamp", "asset", "outcome"} <= set(d[0]),
          str(sorted(d[0]) if d else None))

    print("\n=== replay artifacts / headline numbers ===")
    res = json.loads((REPLAY / "results.json").read_text())
    primary = res["primary"]
    check("replay script + SUMMARY + trades + events + cross-section exist",
          all((REPLAY / f).exists() for f in
              ("run_replay.py", "SUMMARY.md", "trades.csv", "all_events.csv", "cross_section.csv")))
    check("primary n=23 wins=13", primary["n"] == 23 and primary["wins"] == 13,
          f"n={primary['n']} wins={primary['wins']}")
    check("primary mean +0.2003", abs(primary["mean"] - 0.2003) < 0.0002, f"{primary['mean']:+.4f}")
    check("primary sum +4.6077", abs(primary["sum"] - 4.6077) < 0.0002, f"{primary['sum']:+.4f}")
    check("bootstrap 95% [-0.0101,+0.4115] contains 0",
          abs(res["bootstrap"]["ci95"][0] + 0.0101) < 0.0002
          and abs(res["bootstrap"]["ci95"][1] - 0.4115) < 0.0002,
          str([round(x, 4) for x in res["bootstrap"]["ci95"]]))
    check("contribution 4.542% rounds to 4.5%", abs(res["contribution_pct"] - 4.542) < 0.002,
          str(res["contribution_pct"]))
    v = {x["id"]: x for x in res["variants"]}
    for ident, want in (("V02", 0.1994), ("V03", 0.2000), ("V04", 0.2089), ("V05", 0.1973),
                        ("V06", 0.1889), ("V09", 0.1562), ("V11", 0.2539), ("V12", 0.1684),
                        ("V16", 0.1419), ("V18", 0.1850), ("V22", 0.4506), ("V26", -0.0183)):
        check(f"{ident} mean {want:+.4f}", abs(v[ident]["mean"] - want) < 0.0002, f"{v[ident]['mean']:+.4f}")
    cross = res["cross_section"]
    check("cross-section 940 priced markets / 49 events",
          cross["markets"] == 940 and cross["events"] == 49,
          f"{cross['markets']}/{cross['events']}")
    check("event price-sum median 1.042 (1.0415), min 0.99, max 1.568",
          abs(cross["price_sum_median"] - 1.0415) < 0.001
          and cross["price_sum_min"] == 0.99 and cross["price_sum_max"] == 1.568,
          f"{cross['price_sum_median']}/{cross['price_sum_min']}/{cross['price_sum_max']}")
    check("49 events with prices, 32 pole wins", res["events"] == 49 and res["pole_wins"] == 32,
          f"{res['events']}/{res['pole_wins']}")
    check("model fit p0=110/204=0.5392", abs(res["p0"] - 110 / 204) < 1e-9, f"{res['p0']:.6f}")

    print("\n=== local citations ===")
    for rel in ("bots/quant/notes/scheduler/scratch/H-quant-021/REPORT.md",
                "bots/quant/notes/scheduler/scratch/H-quant-021/r2_verify_sources.py",
                "bots/quant/notes/scheduler/scratch/H-quant-021/run_r2_verify_sources.txt",
                "bots/quant/notes/q006-hist/REPORT.md",
                "bots/quant/notes/r2prep-verification/quant-021.md",
                "bots/quant/entries/quant-021-f1-pole-winner-base-rate.md"):
        check(rel, (ROOT / rel).exists())

    print("\n=== entry field consistency ===")
    text = ENTRY.read_text()
    for field, value in (("evidence", "回放"), ("result", "不显著"), ("slot", "-"),
                         ("variants", "27"), ("variants_ext", "-"),
                         ("window", "2014-03-16..2026-10-11"), ("max_dd", "-"),
                         ("contribution", "4.5%")):
        check(f"front matter {field}: {value}", re.search(rf"^{field}: {re.escape(value)}$", text, re.M) is not None)

    print("\n" + ("ALL PASS" if not fails else "FAILURES: " + "; ".join(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
