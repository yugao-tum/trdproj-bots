# DEPRECATED for cold reproduction: this file needs _cache/races.json etc. and
# a hard-coded w01 path. Use bots/quant/replay/quant-021/verify_sources.py
# (self-bootstrapping, 89 checks) instead; see run_r3_verify_sources.txt.
import datetime as dt
import json
import pathlib
import re
import statistics as st
import urllib.error
import urllib.request

H = {"User-Agent": "research/1.0"}
HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "_cache"
REPLAY = HERE.parents[3] / "replay" / "quant-021"


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
    return ok


def main():
    ok = True
    races = json.loads((CACHE / "races.json").read_text())
    print("=== Ergast base rates ===")
    ok &= check("races 269", len(races) == 269, str(len(races)))
    pole_win = sum(1 for r in races.values() if r.get("pole") and r.get("pole") == r.get("winner"))
    fit = [r for r in races.values() if 2014 <= r["season"] <= 2023 and r.get("pole") and r.get("winner")]
    fit_win = sum(1 for r in fit if r["pole"] == r["winner"])
    test = [r for r in races.values() if 2024 <= r["season"] <= 2026 and r.get("pole") and r.get("winner")]
    test_win = sum(1 for r in test if r["pole"] == r["winner"])
    s2026 = [r for r in races.values() if r["season"] == 2026 and r.get("pole") and r.get("winner")]
    s2026_win = sum(1 for r in s2026 if r["pole"] == r["winner"])
    for label, a, b in (
        ("150/269", f"{pole_win}/{len(races)}", "150/269"),
        ("110/204", f"{fit_win}/{len(fit)}", "110/204"),
        ("40/65", f"{test_win}/{len(test)}", "40/65"),
        ("12/17", f"{s2026_win}/{len(s2026)}", "12/17"),
    ):
        ok &= check(label, f"{a}" == b, f"got {a}")
    sc, data = get("https://api.jolpi.ca/ergast/f1/2024/qualifying.json?limit=100&offset=0")
    mr = data["MRData"] if data else {}
    ok &= check("2024 qualifying limit=100 total=479", mr.get("limit") == "100" and mr.get("total") == "479",
                f"limit={mr.get('limit')} total={mr.get('total')}")

    print("\n=== schedule / no look-ahead ===")
    schedule = json.loads((CACHE / "schedule.json").read_text())
    cuts = json.loads((CACHE / "v3_cuts.json").read_text())
    slacks = [(c["cut"] - c["cut_q"]) / 3600 for c in cuts if c.get("cut_q")]
    ok &= check("49 events", len(cuts) == 49, str(len(cuts)))
    ok &= check("all qualifying end <= race-day 00:00 cutoff", all(x >= 0 for x in slacks),
                f"min={min(slacks):.1f}h median={st.median(slacks):.1f}h max={max(slacks):.1f}h")
    ok &= check("schedule 275 races with Qualifying", len(schedule) == 275, str(len(schedule)))

    print("\n=== Gamma F1 events ===")
    events = json.loads((CACHE / "closed_events.json").read_text())
    unique = {e["id"]: e for e in events}
    sel = [e for e in unique.values() if re.search(r"Winner|Pole|Podium", e.get("title", ""), re.I)]
    ok &= check("401 unique closed F1 events", len(unique) == 401, str(len(unique)))
    ok &= check("149 Winner/Pole/Podium events", len(sel) == 149, str(len(sel)))
    ok &= check("3433 markets", sum(len(e["markets"]) for e in sel) == 3433,
                str(sum(len(e["markets"]) for e in sel)))
    winner_map = json.loads((CACHE / "winner_map.json").read_text())
    lens = sorted(len(next(e for e in unique.values() if e["slug"] == x["event_slug"])["markets"])
                  for x in winner_map.values())
    ok &= check("49 matched winner events, markets 9-31 median 27",
                len(winner_map) == 49 and lens[0] == 9 and lens[-1] == 31 and st.median(lens) == 27,
                f"n={len(winner_map)} min={lens[0]} median={st.median(lens)} max={lens[-1]}")

    print("\n=== example events: resolution text / fees ===")
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
    for slug, needles in phrases.items():
        sc, data = get("https://gamma-api.polymarket.com/events?slug=" + slug)
        event = data[0] if data else {}
        desc = event.get("description", "") or ""
        ok &= check("slug " + slug + " HTTP 200", sc == 200, str(sc))
        for needle in needles:
            ok &= check("  phrase: " + needle[:58], needle.lower() in desc.lower())
        rates = sorted({json.dumps(m.get("feeSchedule"), sort_keys=True) for m in event.get("markets", [])})
        ok &= check("  feeSchedule rate 0.05", all('"rate": 0.05' in r for r in rates), str(rates))
        if "singapore" in slug:
            yes = [(m.get("groupItemTitle"), m.get("outcomePrices")) for m in event["markets"]
                   if m.get("outcomePrices") in ('["1", "0"]', '["1","0"]')]
            ok &= check("  resolved YES Verstappen", any("Verstappen" in (x[0] or "") for x in yes), str(yes))

    print("\n=== CLOB prices-history limits ===")
    token = json.loads((CACHE / "trades" / "2026-17.json").read_text())["yes_token"]
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    sc15, d15 = get(f"https://clob.polymarket.com/prices-history?market={token}&startTs={now-15*86400}&endTs={now}&fidelity=60")
    sc20, d20 = get(f"https://clob.polymarket.com/prices-history?market={token}&startTs={now-20*86400}&endTs={now}&fidelity=60")
    scmax, dmax = get(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&fidelity=60")
    scmix, dmix = get(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&startTs={now-14*86400}&endTs={now}&fidelity=60")
    ok &= check("15-day span HTTP 200", sc15 == 200, str(sc15))
    ok &= check("20-day span HTTP 400", sc20 == 400, str(sc20))
    ok &= check("interval=max HTTP 200 with points", scmax == 200 and len(dmax.get("history", [])) > 0,
                str(len(dmax.get("history", [])) if dmax else None))
    ok &= check("interval=max + start/end HTTP 200 with points",
                scmix == 200 and len(dmix.get("history", [])) > 0,
                str(len(dmix.get("history", [])) if dmix else None))

    print("\n=== data-api trades ===")
    trade_files = sorted((CACHE / "trades").glob("*.json"))
    counts = []
    covered = 0
    first_before_start = 0
    for path in trade_files:
        j = json.loads(path.read_text())
        counts.append(j["n_all"])
        tok = j["yes_token"]
        post = [t for t in j["trades"] if t["asset"] == tok and j["cut"] < t["timestamp"] < j["start"] and t["side"] == "BUY"]
        if any(t["timestamp"] <= j["cut"] for t in j["trades"] if t["asset"] == tok):
            covered += 1
        if post and post[0]["timestamp"] < j["start"]:
            first_before_start += 1
    ok &= check("49 trade files", len(trade_files) == 49, str(len(trade_files)))
    ok &= check("per-market trades 212-3000", min(counts) == 212 and max(counts) == 3000,
                f"min={min(counts)} max={max(counts)}")
    ok &= check("49/49 have pre-cutoff trade", covered == 49, str(covered))
    ok &= check("49/49 first post-cutoff BUY before race", first_before_start == 49, str(first_before_start))
    cid = json.loads((CACHE / "trades" / "2026-17.json").read_text())["conditionId"]
    sc, d = get(f"https://data-api.polymarket.com/trades?market={cid}&limit=3&offset=0&takerOnly=true")
    ok &= check("data-api fields include side/price/size/timestamp/asset/outcome",
                sc == 200 and d and {"side", "price", "size", "timestamp", "asset", "outcome"} <= set(d[0]),
                str(sc))

    print("\n=== replay files and headline numbers ===")
    result = json.loads((REPLAY / "results.json").read_text())
    primary = result["primary"]
    ok &= check("replay SUMMARY.md exists", (REPLAY / "SUMMARY.md").exists())
    ok &= check("replay script exists", (REPLAY / "run_replay.py").exists())
    ok &= check("primary n=23 wins=13", primary["n"] == 23 and primary["wins"] == 13,
                f"n={primary['n']} wins={primary['wins']}")
    ok &= check("primary mean +0.2003", abs(primary["mean"] - 0.2003) < 0.0002, f"{primary['mean']:+.4f}")
    ok &= check("bootstrap CI contains 0", result["bootstrap"]["ci95"][0] < 0 < result["bootstrap"]["ci95"][1],
                str([round(x, 4) for x in result["bootstrap"]["ci95"]]))
    variant = {v["id"]: v for v in result["variants"]}
    ok &= check("V12 rule B mean +0.1684", abs(variant["V12"]["mean"] - 0.1684) < 0.0002)
    ok &= check("V16 unconditional mean +0.1419", abs(variant["V16"]["mean"] - 0.1419) < 0.0002)
    ok &= check("V05 +1h +0.1973", abs(variant["V05"]["mean"] - 0.1973) < 0.0002)
    ok &= check("V06 +3h +0.1889", abs(variant["V06"]["mean"] - 0.1889) < 0.0002)
    ok &= check("V09 qual-end +0.1562", abs(variant["V09"]["mean"] - 0.1562) < 0.0002)
    ok &= check("V11 qual-end executable +0.2539", abs(variant["V11"]["mean"] - 0.2539) < 0.0002)
    ok &= check("V26 p<=0.20 -0.0183", abs(variant["V26"]["mean"] + 0.0183) < 0.0002)
    ok &= check("break-even gap 0.20", abs(result["break_even_gap"] - 0.20) < 1e-9)
    cross = result["cross_section"]
    ok &= check("cross-section 1173 markets, 940 priced", cross["markets"] == 940, str(cross["markets"]))
    ok &= check("price sum median 1.042, max 1.568",
                abs(cross["price_sum_median"] - 1.042) < 0.001 and abs(cross["price_sum_max"] - 1.568) < 0.001)

    print("\n=== local cited notes ===")
    for rel in ("bots/quant/notes/r2prep-verification/quant-021.md",
                "bots/quant/notes/q006-hist/REPORT.md",
                "bots/quant/notes/scheduler/scratch/H-quant-021/REPORT.md"):
        ok &= check(rel, pathlib.Path("/home/box/quant/oc-jobs/quant-batch/c20261021-070001-research/wt/w01", rel).exists())

    print("\nALL PASS" if ok else "\nSOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
