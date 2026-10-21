#!/usr/bin/env python3
"""Independent verification for quant-021.

Checks two things without trusting the entry text:
  1. every cited public source is live and contains the claimed fields/quotes;
  2. the committed replay outputs (results.json / trades.csv / all_events.csv /
     cross_section.csv) reproduce the headline numbers.

It reuses run_replay.py's public fetch helpers, so it also works from a cold
cache (about 7 minutes, same requests as the replay). Raw responses stay in a
cache outside the repository. Standard library only.

Usage:
    python3 verify_sources.py [--cache DIR] [--skip-trades]
"""
import argparse
import csv
import datetime as dt
import json
import math
import pathlib
import random
import re
import statistics as st
import sys
import urllib.error
import urllib.request

sys.dont_write_bytecode = True
import run_replay as rr

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
UA = {"User-Agent": "quant-research-verify/1.0"}

PASS = 0
FAIL = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(("PASS " if ok else "FAIL ") + label + (" | " + detail if detail else ""), flush=True)
    return ok


def get_raw(url, timeout=60):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            return fh.status, fh.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:
        return None, str(exc)


def logloss(pairs):
    return -st.mean(y * math.log(max(p, 1e-12)) + (1 - y) * math.log(max(1 - p, 1e-12))
                    for p, y in pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/quant-021-verify-cache")
    ap.add_argument("--skip-trades", action="store_true")
    args = ap.parse_args()
    cache = pathlib.Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    print("cache", cache, flush=True)

    print("\n=== 1. Ergast base rates (cited 150/269, 110/204, 40/65, 12/17) ===")
    races = rr.fetch_ergast(cache)
    check("races 269", len(races) == 269, str(len(races)))
    pw = sum(1 for r in races.values() if r.get("pole") and r.get("pole") == r.get("winner"))
    fit = [r for r in races.values() if 2014 <= r["season"] <= 2023 and r.get("pole") and r.get("winner")]
    test = [r for r in races.values() if 2024 <= r["season"] <= 2026 and r.get("pole") and r.get("winner")]
    s2026 = [r for r in races.values() if r["season"] == 2026 and r.get("pole") and r.get("winner")]
    check("150/269", f"{pw}/{len(races)}" == "150/269", f"{pw}/{len(races)}")
    check("110/204", f"{sum(1 for r in fit if r['pole'] == r['winner'])}/{len(fit)}" == "110/204",
          f"{sum(1 for r in fit if r['pole'] == r['winner'])}/{len(fit)}")
    check("40/65", f"{sum(1 for r in test if r['pole'] == r['winner'])}/{len(test)}" == "40/65",
          f"{sum(1 for r in test if r['pole'] == r['winner'])}/{len(test)}")
    check("12/17", f"{sum(1 for r in s2026 if r['pole'] == r['winner'])}/{len(s2026)}" == "12/17",
          f"{sum(1 for r in s2026 if r['pole'] == r['winner'])}/{len(s2026)}")
    _, table, p0 = rr.fit_rates(races)
    check("fit table n=36/68/65/20, rates .4737/.5286/.5373/.7273",
          [x["n"] for x in table] == [36, 68, 65, 20]
          and [round(x["rate"], 4) for x in table] == [0.4737, 0.5286, 0.5373, 0.7273],
          str([[x["n"], round(x["rate"], 4)] for x in table]))
    check("constant p0 = 110/204 = .5392", abs(p0 - 110 / 204) < 1e-12, f"{p0:.6f}")

    pairs_a = [(rr.model_a(r.get("margin"), table), 1 if r["pole"] == r["winner"] else 0) for r in test]
    pairs_b = [(p0, 1 if r["pole"] == r["winner"] else 0) for r in test]
    ll_a, ll_b = logloss(pairs_a), logloss(pairs_b)
    br_a = st.mean((p - y) ** 2 for p, y in pairs_a)
    br_b = st.mean((p - y) ** 2 for p, y in pairs_b)
    check("OOS log loss .6706 vs .6781", abs(ll_a - 0.6706) < 0.0002 and abs(ll_b - 0.6781) < 0.0002,
          f"{ll_a:.4f} vs {ll_b:.4f}")
    check("OOS Brier .2388 vs .2425", abs(br_a - 0.2388) < 0.0002 and abs(br_b - 0.2425) < 0.0002,
          f"{br_a:.4f} vs {br_b:.4f}")

    sc, body = get_raw("https://api.jolpi.ca/ergast/f1/2024/qualifying.json?limit=100&offset=0")
    try:
        mr = json.loads(body)["MRData"]
    except Exception:
        mr = {}
    check("2024 qualifying HTTP 200, limit=100 total=479",
          sc == 200 and mr.get("limit") == "100" and mr.get("total") == "479",
          f"http={sc} limit={mr.get('limit')} total={mr.get('total')}")

    print("\n=== 2. Gamma F1 universe and event rules ===")
    events = rr.fetch_gamma(cache)
    unique = {e["id"]: e for e in events}
    sel = [e for e in unique.values() if re.search(r"Winner|Pole|Podium", e.get("title", ""), re.I)]
    check("401 unique closed F1 events", len(unique) == 401, str(len(unique)))
    check("149 Winner/Pole/Podium events", len(sel) == 149, str(len(sel)))
    check("3433 markets", sum(len(e["markets"]) for e in sel) == 3433,
          str(sum(len(e["markets"]) for e in sel)))

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
        sc, body = get_raw("https://gamma-api.polymarket.com/events?slug=" + slug)
        try:
            event = json.loads(body)[0]
        except Exception:
            event = {}
        desc = event.get("description", "") or ""
        check("event " + slug + " HTTP 200", sc == 200 and bool(event), str(sc))
        for needle in needles:
            check("  phrase: " + needle[:56], needle.lower() in desc.lower())
        rates = sorted({json.dumps(m.get("feeSchedule"), sort_keys=True) for m in event.get("markets", [])})
        check("  per-market feeSchedule rate 0.05, rebate 0.15",
              bool(rates) and all('"rate": 0.05' in x and '"rebateRate": 0.15' in x for x in rates),
              str(len(rates)) + " distinct schedules")
        if "singapore" in slug:
            yes = []
            for m in event.get("markets", []):
                try:
                    outs = json.loads(m["outcomes"])
                    pr = json.loads(m["outcomePrices"])
                except Exception:
                    continue
                if outs[0] == "Yes" and float(pr[0]) >= 0.5:
                    yes.append((m.get("groupItemTitle"), m.get("outcomePrices")))
            check("  resolved YES Verstappen [\"1\",\"0\"]",
                  any("Verstappen" in (x[0] or "") for x in yes), str(yes))

    print("\n=== 3. event matching, timing, and trade prints ===")
    schedule = rr.fetch_schedule(cache)
    check("Ergast schedule 275 races", len(schedule) == 275, str(len(schedule)))
    matched = rr.match_events(events, races)
    check("49 matched Winner events", len(matched) == 49, str(len(matched)))
    lens = sorted(len(unique[next(e["id"] for e in unique.values() if e["slug"] == matched[k]["event"]["slug"])]["markets"])
                  for k in matched)
    check("markets/event 9-31, median 27",
          lens[0] == 9 and lens[-1] == 31 and st.median(lens) == 27,
          f"n={len(lens)} min={lens[0]} median={st.median(lens)} max={lens[-1]}")

    cuts = []
    trade_counts = []
    covered = first_buy_before_start = 0
    tokens = {}
    diag = []
    for key in sorted(matched):
        item = matched[key]
        race = item["race"]
        cut, start, qual_end = rr.event_times(race, schedule)
        cuts.append({"cut": cut, "cut_q": qual_end})
        market = rr.pole_market(item["event"], race["pole"])
        if market is None:
            check("unique pole market " + key, False)
            continue
        token = rr.yes_token(market)
        tokens[key] = token
        pair = market.get("conditionId")
        if args.skip_trades:
            continue
        trades = rr.fetch_trades(market, cut, start, cache)
        trade_counts.append(len(trades))
        pre = sorted([t for t in trades if t["asset"] == token and t["timestamp"] <= cut],
                     key=lambda z: z["timestamp"])
        post = sorted([t for t in trades if t["asset"] == token and cut < t["timestamp"] < start],
                      key=lambda z: z["timestamp"])
        buys = [t for t in post if t["side"] == "BUY"]
        if pre:
            covered += 1
        if buys and buys[0]["timestamp"] < start:
            first_buy_before_start += 1
        p_hist, _ = rr.last_price(token, cut, cache)
        e100, q100 = rr.vwap(buys, 100)
        try:
            outs = json.loads(market["outcomes"])
            pr = json.loads(market["outcomePrices"])
            y = float(pr[outs.index("Yes")])
        except Exception:
            y = None
        # timestamp when the first 100 shares finish
        qty, t100 = 0.0, None
        for t in buys:
            qty += t["size"]
            if qty >= 100 - 1e-9:
                t100 = t["timestamp"]
                break
        diag.append({
            "key": key, "p_hist": p_hist, "first": buys[0]["price"] if buys else None,
            "exec100": e100, "y": y, "model": rr.model_a(race.get("margin"), table),
            "last_pre_side": pre[-1]["side"] if pre else None,
            "first_delay_h": (buys[0]["timestamp"] - cut) / 3600 if buys else None,
            "fill100_h": (t100 - cut) / 3600 if t100 else None,
        })
    slacks = [(c["cut"] - c["cut_q"]) / 3600 for c in cuts if c["cut_q"]]
    check("49/49 qualifying end +2h <= race-day 00:00 cutoff",
          len(slacks) == 49 and min(slacks) >= 0,
          f"min={min(slacks):.1f}h median={st.median(slacks):.1f}h max={max(slacks):.1f}h")
    if not args.skip_trades:
        check("per-market trade prints 212-3000", min(trade_counts) == 212 and max(trade_counts) == 3000,
              f"min={min(trade_counts)} max={max(trade_counts)}")
        check("49/49 have a pre-cutoff print", covered == 49, str(covered))
        check("49/49 first post-cutoff BUY before race start", first_buy_before_start == 49,
              str(first_buy_before_start))
        cid = next(m for m in matched["2026-17"]["event"]["markets"]
                   if rr.yes_token(m) == tokens["2026-17"]).get("conditionId")
        sc, body = get_raw(f"https://data-api.polymarket.com/trades?market={cid}&limit=3&offset=0&takerOnly=true")
        try:
            sample = json.loads(body)
        except Exception:
            sample = []
        need = {"side", "price", "size", "timestamp", "asset", "outcome"}
        check("data-api fields side/price/size/timestamp/asset/outcome",
              sc == 200 and bool(sample) and need <= set(sample[0]), str(sc))

        fg = [d["first"] - d["p_hist"] for d in diag if d["first"] is not None and d["p_hist"] is not None]
        eg = [d["exec100"] - d["p_hist"] for d in diag if d["exec100"] is not None and d["p_hist"] is not None]
        check("first - p_hist mean +0.0096, max +0.0450",
              abs(st.mean(fg) - 0.0096) < 0.0002 and abs(max(fg) - 0.0450) < 0.0002,
              f"mean={st.mean(fg):+.4f} max={max(fg):+.4f}")
        check("exec100 - p_hist mean +0.0086",
              abs(st.mean(eg) - 0.0086) < 0.0002, f"mean={st.mean(eg):+.4f}")
        check("49 events, 32 pole-sitter wins", len(diag) == 49 and sum(1 for d in diag if d["y"] == 1) == 32,
              f"n={len(diag)} wins={sum(1 for d in diag if d['y'] == 1)}")
        sel = [d for d in diag if d["p_hist"] is not None and d["exec100"] is not None
               and d["p_hist"] <= d["model"] - 0.05]
        sides = {s: sum(1 for d in sel if d["last_pre_side"] == s) for s in ("BUY", "SELL")}
        check("rule A triggers 23; last pre-cutoff side BUY 21 / SELL 2",
              len(sel) == 23 and sides == {"BUY": 21, "SELL": 2}, f"n={len(sel)} sides={sides}")
        fd = [d["first_delay_h"] for d in sel if d["first_delay_h"] is not None]
        f100 = [d["fill100_h"] for d in sel if d["fill100_h"] is not None]
        check("first fill delay median .62h max 2.99h; 100-share median 1.04h max 6.38h",
              abs(st.median(fd) - 0.62) < 0.01 and abs(max(fd) - 2.99) < 0.01
              and abs(st.median(f100) - 1.04) < 0.01 and abs(max(f100) - 6.38) < 0.01,
              f"first median={st.median(fd):.2f} max={max(fd):.2f}; 100 median={st.median(f100):.2f} max={max(f100):.2f}")

    print("\n=== 4. CLOB prices-history limits and earliest point ===")
    token = tokens.get("2026-17") or next(iter(tokens.values()))
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    sc15, b15 = get_raw(f"https://clob.polymarket.com/prices-history?market={token}&startTs={now-15*86400}&endTs={now}&fidelity=60")
    sc20, b20 = get_raw(f"https://clob.polymarket.com/prices-history?market={token}&startTs={now-20*86400}&endTs={now}&fidelity=60")
    scmax, bmax = get_raw(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&fidelity=60")
    scmix, bmix = get_raw(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&startTs={now-14*86400}&endTs={now}&fidelity=60")
    check("15-day span HTTP 200", sc15 == 200, str(sc15))
    check("20-day span HTTP 400 with interval-too-long error",
          sc20 == 400 and "interval is too long" in b20, f"http={sc20} body={b20[:90]}")
    check("interval=max HTTP 200 with points", scmax == 200 and len(json.loads(bmax).get("history", [])) > 0)
    check("interval=max + startTs/endTs HTTP 200 with points",
          scmix == 200 and len(json.loads(bmix).get("history", [])) > 0)
    # earliest cited point: 2024 Italian GP token, t=1724947202 (2024-08-29)
    it = tokens.get("2024-16")
    if it:
        race = matched["2024-16"]["race"]
        cut, _, _ = rr.event_times(race, schedule)
        sc, body = get_raw(f"https://clob.polymarket.com/prices-history?market={it}&startTs={cut-12*86400}&endTs={cut}&fidelity=60")
        hist = json.loads(body).get("history", []) if sc == 200 else []
        check("2024-16 series starts 2024-08-29 (t=1724947202)",
              bool(hist) and hist[0]["t"] == 1724947202,
              f"first={hist[0] if hist else None}")

    print("\n=== 5. committed replay outputs reproduce headline numbers ===")
    result = json.loads((HERE / "results.json").read_text())
    primary = result["primary"]
    check("primary n=23 wins=13", primary["n"] == 23 and primary["wins"] == 13,
          f"n={primary['n']} wins={primary['wins']}")
    check("primary mean +0.2003", abs(primary["mean"] - 0.2003) < 0.0002, f"{primary['mean']:+.4f}")
    check("primary sd .5204 t=1.85", abs(primary["sd"] - 0.5204) < 0.0002 and abs(primary["t"] - 1.85) < 0.01,
          f"sd={primary['sd']:.4f} t={primary['t']:.3f}")
    rows = list(csv.DictReader((HERE / "trades.csv").open()))
    vals = [float(r["net_per_share"]) for r in rows]
    check("trades.csv 23 rows, sum +4.6077, mean +0.2003",
          len(rows) == 23 and abs(sum(vals) - 4.6077) < 0.001 and abs(st.mean(vals) - 0.2003) < 0.0002,
          f"n={len(rows)} sum={sum(vals):.4f} mean={st.mean(vals):.4f}")
    check("median +0.5789, without best +0.1701",
          abs(st.median(vals) - 0.5789) < 0.001 and abs((sum(vals) - max(vals)) / (len(vals) - 1) - 0.1701) < 0.001,
          f"median={st.median(vals):.4f}")
    rng = random.Random(20261021)
    boots = sorted(st.mean([vals[rng.randrange(len(vals))] for _ in vals]) for _ in range(20000))
    ci = [boots[500], boots[19499]]
    p_le0 = sum(1 for x in boots if x <= 0) / len(boots)
    check("bootstrap 95% [-.0101,+.4115], P(mean<=0)=.031",
          abs(ci[0] + 0.0101) < 0.0005 and abs(ci[1] - 0.4115) < 0.0005 and abs(p_le0 - 0.031) < 0.001,
          f"ci=[{ci[0]:+.4f},{ci[1]:+.4f}] p={p_le0:.3f}")
    check("break-even gap 0.20", abs(result["break_even_gap"] - 0.20) < 1e-9,
          str(result["break_even_gap"]))
    check("contribution 4.54%", abs(result["contribution_pct"] - 4.54) < 0.01,
          f"{result['contribution_pct']:.2f}% months={result['months']:.2f}")
    check("27 variants, ids V01..V27", len(result["variants"]) == 27
          and {v["id"] for v in result["variants"]} == {f"V{i:02d}" for i in range(1, 28)},
          str(len(result["variants"])))
    v = {x["id"]: x for x in result["variants"]}
    for vid, want in (("V02", 0.1994), ("V03", 0.2000), ("V04", 0.2089), ("V05", 0.1973),
                      ("V06", 0.1889), ("V07", 0.2336), ("V09", 0.1562), ("V11", 0.2539),
                      ("V12", 0.1684), ("V16", 0.1419), ("V18", 0.1850), ("V22", 0.4506),
                      ("V26", -0.0183)):
        check(f"{vid} mean {want:+.4f}", abs(v[vid]["mean"] - want) < 0.0002, f"{v[vid]['mean']:+.4f}")
    ae = list(csv.DictReader((HERE / "all_events.csv").open()))
    check("all_events.csv 49 rows, 32 wins, 2024-09-01..2026-10-11",
          len(ae) == 49 and sum(1 for x in ae if float(x["y"]) == 1) == 32
          and min(x["date"] for x in ae) == "2024-09-01"
          and max(x["date"] for x in ae) == "2026-10-11",
          f"n={len(ae)}")
    cs = list(csv.DictReader((HERE / "cross_section.csv").open()))
    cheap = [x for x in cs if float(x["p_hist"]) <= 0.20]
    cheap_net = st.mean(float(x["net_per_share"]) for x in cheap)
    check("cross_section 940 priced; p<=.20 n=852 wins=9 net -0.0183",
          len(cs) == 940 and len(cheap) == 852 and sum(1 for x in cheap if float(x["y"]) == 1) == 9
          and abs(cheap_net + 0.0183) < 0.0002,
          f"n={len(cs)} cheap={len(cheap)} net={cheap_net:+.4f}")

    print("\n=== 6. replay package shape and entry/front-matter consistency ===")
    entry_path = REPO / "bots/quant/entries/quant-021-f1-pole-winner-base-rate.md"
    entry = entry_path.read_text()
    front = entry.split("---", 2)[1]

    def field(name):
        m = re.search(r"^" + re.escape(name) + r":\s*(.+)$", front, re.M)
        return m.group(1).strip() if m else None

    check("entry exists and status 待核 (unchanged)", "status: 待核" in front)
    check("date 2026-10-20 (unchanged)", field("date") == "2026-10-20", str(field("date")))
    check("evidence 回放", field("evidence") == "回放", str(field("evidence")))
    check("result 不显著", field("result") == "不显著", str(field("result")))
    check("slot -", field("slot") == "-", str(field("slot")))
    check("variants 27", field("variants") == "27", str(field("variants")))
    check("variants_ext -", field("variants_ext") == "-", str(field("variants_ext")))
    check("window 2014-03-16..2026-10-11", field("window") == "2014-03-16..2026-10-11", str(field("window")))
    check("max_dd - (Polymarket, optional)", field("max_dd") == "-", str(field("max_dd")))
    check("contribution 4.5%", field("contribution") == "4.5%", str(field("contribution")))
    check("entry cites this verifier", "verify_sources.py" in entry)
    check("replay SUMMARY has 27 variant rows", (HERE / "SUMMARY.md").read_text().count("| V") >= 27)
    files = [p for p in HERE.iterdir() if p.is_file()]
    check("all replay files < 1 MB", all(p.stat().st_size < 1_000_000 for p in files),
          f"largest={max(p.stat().st_size for p in files)} bytes")
    check("no binaries in replay", not any(p.suffix.lower() in {".pkl", ".parquet", ".npy", ".zip", ".gz", ".db", ".xlsx"} for p in files))

    for rel in ("bots/quant/notes/r2prep-verification/quant-021.md",
                "bots/quant/notes/q006-hist/REPORT.md",
                "bots/quant/notes/scheduler/scratch/H-quant-021/REPORT.md"):
        check("cited note " + rel, (REPO / rel).exists())

    print(f"\n{PASS} PASS, {FAIL} FAIL")
    print("ALL PASS" if FAIL == 0 else "SOME FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
