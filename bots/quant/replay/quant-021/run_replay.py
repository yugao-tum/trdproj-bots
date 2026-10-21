#!/usr/bin/env python3
"""quant-021 replay: F1 pole-sitter winner markets, fills from data-api trades.

Public, keyless endpoints only. Raw responses are cached outside the repository
(default /tmp/quant-021-cache); only derived CSV/JSON are written next to this script.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import random
import re
import statistics as st
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
UA = {"User-Agent": "quant-research/1.0"}
FEE_RATE = 0.05
HALF_SPREAD = 0.01
SHARES = 100
CAPITAL = 5000.0
BINS = [(0.0, 0.05), (0.05, 0.20), (0.20, 0.50), (0.50, 99.0)]
FIT_SEASONS = range(2014, 2024)
TEST_SEASONS = range(2024, 2027)


def get_json(url, cache_dir, retries=5):
    key = hashlib.sha1(url.encode()).hexdigest()[:20] + ".json"
    path = cache_dir / key
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as fh:
                data = json.load(fh)
            path.write_text(json.dumps(data))
            return data
        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                return {"_http": 400}
            last = exc
            time.sleep(1.2 * (attempt + 1))
        except Exception as exc:
            last = exc
            time.sleep(1.2 * (attempt + 1))
    return {"_err": str(last)}


def get_status(url, cache_dir):
    key = hashlib.sha1(url.encode()).hexdigest()[:20] + ".meta"
    path = cache_dir / key
    if path.exists():
        return int(path.read_text())
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as fh:
            code, data = fh.status, json.load(fh)
    except urllib.error.HTTPError as exc:
        path.write_text(str(exc.code))
        return exc.code, {"_http": exc.code}
    path.write_text(str(code))
    return code, data


def tsec(value):
    if not value:
        return None
    m = re.match(r"^(?:(\d+):)?(\d+):(\d+\.?\d*)$", value)
    if m:
        return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = re.match(r"^(\d+):(\d+\.?\d*)$", value)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return None


def iso_ts(date, clock):
    if not date:
        return None
    clock = (clock or "00:00:00").replace("Z", "+00:00")
    return int(dt.datetime.fromisoformat(date + "T" + clock).timestamp())


def fetch_gamma(cache_dir):
    events = []
    for offset in range(0, 500, 100):
        data = get_json(
            f"https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset={offset}",
            cache_dir,
        )
        if not isinstance(data, list) or not data:
            break
        events.extend(data)
    unique = {}
    for event in events:
        unique[event["id"]] = event
    return list(unique.values())


def fetch_ergast(cache_dir):
    raw = {}
    for season in list(range(2014, 2027)):
        for kind in ("qualifying", "results"):
            rows, offset = [], 0
            while True:
                data = get_json(
                    f"https://api.jolpi.ca/ergast/f1/{season}/{kind}.json?limit=100&offset={offset}",
                    cache_dir,
                )
                try:
                    mr = data["MRData"]
                    total = int(mr["total"])
                    rows.extend(mr["RaceTable"]["Races"])
                except Exception:
                    break
                offset += 100
                if offset >= total:
                    break
            raw[(season, kind)] = rows
    races = {}
    for season in range(2014, 2027):
        merged = {}
        for kind, key in (("qualifying", "QualifyingResults"), ("results", "Results")):
            by_round = {}
            for race in raw[(season, kind)]:
                rnd = int(race["round"])
                by_round.setdefault(rnd, {"race": race, "rows": []})["rows"].extend(race.get(key, []))
            merged[kind] = by_round
        for rnd in sorted(merged["results"]):
            race = merged["results"][rnd]["race"]
            rec = {
                "season": season,
                "round": rnd,
                "name": race["raceName"],
                "date": race["date"],
                "time": race.get("time"),
            }
            if rnd in merged["qualifying"]:
                seen = {}
                for row in merged["qualifying"][rnd]["rows"]:
                    driver = row["Driver"]["driverId"]
                    best = None
                    for session in ("Q3", "Q2", "Q1"):
                        value = tsec(row.get(session))
                        if value is not None and (best is None or value < best):
                            best = value
                    cand = {"d": driver, "pos": int(row["position"]), "best": best}
                    if driver not in seen or cand["pos"] < seen[driver]["pos"]:
                        seen[driver] = cand
                qual = sorted(seen.values(), key=lambda z: z["pos"])
                if qual:
                    rec["pole"] = qual[0]["d"]
                    others = [z["best"] for z in qual[1:] if z["best"] is not None]
                    rec["margin"] = round(min(others) - qual[0]["best"], 3) if qual[0]["best"] and others else None
            results = merged["results"][rnd]["rows"]
            if results:
                winner = min(results, key=lambda z: int(z["position"]))
                rec["winner"] = winner["Driver"]["driverId"]
            races[f"{season}-{rnd}"] = rec
    return races


def fetch_schedule(cache_dir):
    out = {}
    for season in range(2014, 2027):
        data = get_json(f"https://api.jolpi.ca/ergast/f1/{season}.json", cache_dir)
        try:
            rows = data["MRData"]["RaceTable"]["Races"]
        except Exception:
            continue
        for race in rows:
            out[f"{season}-{race['round']}"] = {
                "date": race.get("date"),
                "time": race.get("time"),
                "qual_date": (race.get("Qualifying") or {}).get("date"),
                "qual_time": (race.get("Qualifying") or {}).get("time"),
            }
    return out


def select_winner_events(events):
    picked = []
    for event in events:
        title = event.get("title", "")
        slug = event.get("slug", "")
        if not re.search(r"Winner", title, re.I):
            continue
        if re.search(r"Pole|Podium|Sprint|Constructor|Safety|Red Flag|Head", title, re.I):
            continue
        if "indycar" in slug.lower() or "indy" in title.lower():
            continue
        if not slug.startswith("f1-") and not slug.endswith("-winner") and "grand-prix" not in slug:
            continue
        picked.append(event)
    return picked


def match_events(events, races):
    rows = []
    for event in select_winner_events(events):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", event.get("slug", ""))
        when = dt.date.fromisoformat(m.group(1)) if m else dt.date.fromisoformat(event["endDate"][:10])
        best = None
        for race in races.values():
            if race["season"] < 2024:
                continue
            delta = abs((dt.date.fromisoformat(race["date"]) - when).days)
            if delta <= 7 and (best is None or delta < best[0]):
                best = (delta, race)
        if best:
            rows.append({"event": event, "race": best[1], "diff": best[0]})
    by_race = {}
    for row in rows:
        key = f"{row['race']['season']}-{row['race']['round']}"
        if key not in by_race or len(row["event"]["markets"]) > len(by_race[key]["event"]["markets"]):
            by_race[key] = row
    return by_race


def pole_market(event, pole):
    surname = pole.split("_")[-1].lower()
    cand = [
        m for m in event["markets"]
        if m.get("groupItemTitle") and surname in m["groupItemTitle"].lower().replace("-", " ")
    ]
    return cand[0] if len(cand) == 1 else None


def yes_token(market):
    tokens = json.loads(market["clobTokenIds"])
    outcomes = json.loads(market["outcomes"])
    return tokens[outcomes.index("Yes")]


def event_times(race, schedule):
    cut = iso_ts(race["date"], "00:00:00Z")
    start = iso_ts(race["date"], race.get("time") or "00:00:00Z")
    if start <= cut:
        start = cut + 15 * 3600
    sched = schedule.get(f"{race['season']}-{race['round']}", {})
    qual = iso_ts(sched.get("qual_date"), sched.get("qual_time"))
    return cut, start, (qual + 2 * 3600 if qual else None)


def fetch_trades(market, cut, start, cache_dir):
    rows, offset = [], 0
    while offset < 20000:
        data = get_json(
            f"https://data-api.polymarket.com/trades?limit=1000&offset={offset}"
            f"&market={market['conditionId']}&takerOnly=true",
            cache_dir,
        )
        if not isinstance(data, list) or not data:
            break
        rows.extend(data)
        if len(data) < 1000 or data[-1]["timestamp"] <= cut - 86400:
            break
        offset += 1000
    return rows


def vwap(fills, cap):
    qty = cost = 0.0
    for fill in fills:
        take = min(fill["size"], cap - qty)
        if take <= 0:
            break
        cost += take * fill["price"]
        qty += take
        if qty >= cap - 1e-9:
            break
    return (cost / qty if qty > 1e-12 else None), qty


def last_price(token, end_ts, cache_dir):
    data = get_json(
        f"https://clob.polymarket.com/prices-history?market={token}"
        f"&startTs={end_ts - 3 * 86400}&endTs={end_ts}&fidelity=60",
        cache_dir,
    )
    hist = data.get("history") if isinstance(data, dict) else None
    return (hist[-1]["p"] if hist else None), (end_ts - hist[-1]["t"]) / 3600 if hist else None


def fee(price):
    return FEE_RATE * price * (1 - price)


def net(y, price):
    return y - price - fee(price) - HALF_SPREAD


def fit_rates(races):
    fit = [
        r for r in races.values()
        if 2014 <= r["season"] <= 2023 and r.get("pole") and r.get("winner")
    ]
    table = []
    for lo, hi in BINS:
        sub = [r for r in fit if r.get("margin") is not None and lo <= r["margin"] < hi]
        wins = sum(1 for r in sub if r["pole"] == r["winner"])
        table.append({"lo": lo, "hi": hi, "n": len(sub), "wins": wins,
                      "raw": wins / len(sub) if sub else None,
                      "rate": (wins + 1) / (len(sub) + 2)})
    p0 = sum(1 for r in fit if r["pole"] == r["winner"]) / len(fit)
    return fit, table, p0


def model_a(margin, table):
    if margin is None:
        return 0.333
    for row in table:
        if row["lo"] <= margin < row["hi"]:
            return row["rate"]
    return 0.333


def summarize(label, selected, fill):
    vals = [net(r["y"], r[fill]) for r in selected]
    return {
        "id": label,
        "n": len(selected),
        "wins": sum(1 for r in selected if r["y"] == 1),
        "sum": sum(vals),
        "mean": st.mean(vals) if vals else 0.0,
        "sd": st.pstdev(vals) if len(vals) > 1 else 0.0,
        "t": (st.mean(vals) / (st.pstdev(vals) / math.sqrt(len(vals)))) if len(vals) > 1 and st.pstdev(vals) > 0 else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default=os.environ.get("QUANT021_CACHE", "/tmp/quant-021-cache"))
    parser.add_argument("--skip-cross", action="store_true")
    args = parser.parse_args()
    cache_dir = pathlib.Path(args.cache)
    cache_dir.mkdir(parents=True, exist_ok=True)
    print("cache", cache_dir, flush=True)

    events = fetch_gamma(cache_dir)
    print("gamma events", len(events), flush=True)
    races = fetch_ergast(cache_dir)
    print("ergast races", len(races), flush=True)
    schedule = fetch_schedule(cache_dir)
    print("ergast schedule", len(schedule), flush=True)
    matched = match_events(events, races)
    print("matched winner events", len(matched), flush=True)
    fit, table, p0 = fit_rates(races)
    print("fit races", len(fit), "p0", round(p0, 4), flush=True)

    rows = []
    for key, item in sorted(matched.items()):
        race = item["race"]
        event = item["event"]
        cut, start, qual_end = event_times(race, schedule)
        market = pole_market(event, race["pole"])
        if market is None:
            print("skip no unique market", key, flush=True)
            continue
        token = yes_token(market)
        outcomes = json.loads(market["outcomes"])
        prices = json.loads(market["outcomePrices"])
        y = float(prices[outcomes.index("Yes")])
        p_hist, age_hist = last_price(token, cut, cache_dir)
        trades = fetch_trades(market, cut, start, cache_dir)
        tr = [t for t in trades if t["asset"] == token]
        post = sorted([t for t in tr if cut < t["timestamp"] < start], key=lambda z: z["timestamp"])
        buys = [t for t in post if t["side"] == "BUY"]
        first, _ = vwap(buys, 1)
        e20, q20 = vwap(buys, 20)
        e100, q100 = vwap(buys, 100)

        def delayed(hours):
            sub = [t for t in buys if t["timestamp"] >= cut + hours * 3600]
            e, q = vwap(sub, 100)
            return e, q

        e1, q1 = delayed(1)
        e3, q3 = delayed(3)
        rec = {
            "key": key, "race": race["name"], "season": race["season"], "date": race["date"],
            "pole": race["pole"], "margin": race.get("margin"), "y": y,
            "p_hist": p_hist, "age_hist_h": age_hist,
            "first": first, "exec20": e20, "exec100": e100, "q100": q100,
            "exec100_1h": e1, "exec100_3h": e3,
            "n_buy": len(buys), "buy_shares": sum(t["size"] for t in buys),
            "modelA": model_a(race.get("margin"), table),
        }
        if qual_end:
            p_q, _ = last_price(token, qual_end, cache_dir)
            post_q = sorted([t for t in tr if qual_end < t["timestamp"] < start], key=lambda z: z["timestamp"])
            buys_q = [t for t in post_q if t["side"] == "BUY"]
            first_q, _ = vwap(buys_q, 1)
            e100_q, q100_q = vwap(buys_q, 100)
            rec.update({"p_hist_q": p_q, "first_q": first_q, "exec100_q": e100_q, "q100_q": q100_q})
        rows.append(rec)
        print("event", key, race["name"], "p_hist", p_hist, "exec100", round(e100, 4) if e100 else None,
              "buys", len(buys), flush=True)

    rows.sort(key=lambda r: (r["season"], r["date"]))

    def trigger(rows_in, model, cushion=0.05, fill="exec100", trigger_fill=False, trigger_key="p_hist"):
        out = []
        for r in rows_in:
            target = (model_a(r["margin"], table) if model == "A" else p0) - cushion
            base = r[fill] if trigger_fill else r.get(trigger_key)
            if r.get(fill) is None or base is None:
                continue
            if base <= target:
                out.append(r)
        return out

    variants = []

    def add(ident, family, rule, fill, selected, note=""):
        row = summarize(ident, selected, fill)
        row.update({"family": family, "rule": rule, "fill": fill, "note": note})
        variants.append(row)
        return row

    add("V01", "A", "A cushion .05 midnight", "exec100", trigger(rows, "A"), "primary")
    add("V02", "A", "A cushion .05 midnight", "first", trigger(rows, "A"))
    add("V03", "A", "A cushion .05 midnight", "exec20", trigger(rows, "A"))
    add("V04", "A", "A cushion .05 midnight", "p_hist", trigger(rows, "A"), "non-tradable reference")
    add("V05", "A", "A cushion .05 midnight +1h", "exec100_1h", trigger(rows, "A"))
    add("V06", "A", "A cushion .05 midnight +3h", "exec100_3h", trigger(rows, "A"))
    add("V07", "A", "A cushion .05 midnight, trigger&fill exec100", "exec100", trigger(rows, "A", fill="exec100", trigger_fill=True))
    add("V08", "A", "A cushion .05 midnight, trigger&fill first", "first", trigger(rows, "A", fill="first", trigger_fill=True))
    add("V09", "A", "A cushion .05 qual-end, fill exec100_q", "exec100_q", trigger(rows, "A", fill="exec100_q", trigger_key="p_hist_q"))
    add("V10", "A", "A cushion .05 qual-end, trigger&fill first_q", "first_q", trigger(rows, "A", fill="first_q", trigger_fill=True))
    add("V11", "A", "A cushion .05 qual-end, trigger&fill exec100_q", "exec100_q", trigger(rows, "A", fill="exec100_q", trigger_fill=True))
    add("V12", "B", "B constant cushion .05 midnight", "exec100", trigger(rows, "B"))
    add("V13", "B", "B constant cushion .05 midnight", "first", trigger(rows, "B"))
    add("V14", "B", "B constant cushion .05 midnight", "p_hist", trigger(rows, "B"), "non-tradable reference")
    add("V15", "B", "B constant cushion .05 midnight +3h", "exec100_3h", trigger(rows, "B"))
    add("V16", "unconditional", "all pole sitters", "exec100", [r for r in rows if r.get("exec100") is not None])
    add("V17", "unconditional", "all pole sitters +3h", "exec100_3h", [r for r in rows if r.get("exec100_3h") is not None])
    for idx, cushion in enumerate((0.0, 0.02, 0.08, 0.10, 0.15), start=18):
        add(f"V{idx:02d}", "cushion", f"A cushion {cushion:.2f} midnight", "exec100", trigger(rows, "A", cushion=cushion))

    primary = trigger(rows, "A")
    primary_vals = [net(r["y"], r["exec100"]) for r in primary]
    random.seed(20261021)
    boots = sorted(st.mean([primary_vals[random.randrange(len(primary_vals))] for _ in primary_vals]) for _ in range(20000))
    ci = [boots[500], boots[19499]]

    per_season = {}
    for season in (2024, 2025, 2026):
        sel = [r for r in primary if r["season"] == season]
        per_season[season] = summarize(f"A {season}", sel, "exec100")

    break_even = None
    for step in range(0, 401):
        gap = step / 1000
        total = sum(net(r["y"], r["exec100"] + gap) for r in primary)
        if total <= 0:
            break_even = gap
            break

    cross = {}
    if not args.skip_cross:
        cross_rows = []
        def work(item):
            key, wrapper = item
            event = wrapper["event"]
            race = matched[key]["race"]
            cut, _, _ = event_times(race, schedule)
            pole_sur = race["pole"].split("_")[-1].lower()
            out = []
            for m in event.get("markets", []):
                title = m.get("groupItemTitle")
                if not title:
                    continue
                try:
                    token = yes_token(m)
                    outcomes = json.loads(m["outcomes"])
                    prices = json.loads(m["outcomePrices"])
                    y = float(prices[outcomes.index("Yes")])
                except Exception:
                    continue
                p, _ = last_price(token, cut, cache_dir)
                if p is None:
                    continue
                out.append({"key": key, "driver": title, "p": p, "y": y,
                            "is_pole": int(pole_sur in title.lower().replace("-", " "))})
            return out
        with ThreadPoolExecutor(max_workers=8) as pool:
            for part in pool.map(work, sorted(matched.items())):
                cross_rows.extend(part)
        cross_rows.sort(key=lambda r: (r["key"], -r["p"]))
        by_event = {}
        for r in cross_rows:
            by_event.setdefault(r["key"], []).append(r)
        sums = sorted(sum(x["p"] for x in arr) for arr in by_event.values())
        bands = []
        for lo, hi in [(0.0, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 0.30), (0.30, 0.50), (0.50, 0.70), (0.70, 1.01)]:
            sub = [r for r in cross_rows if lo <= r["p"] < hi]
            po = [r for r in sub if r["is_pole"]]
            no = [r for r in sub if not r["is_pole"]]
            bands.append({"lo": lo, "hi": hi, "n": len(sub), "meanp": st.mean([r["p"] for r in sub]),
                          "win": st.mean([r["y"] for r in sub]),
                          "mean_net": st.mean([net(r["y"], r["p"]) for r in sub]),
                          "pole_n": len(po), "pole_win": st.mean([r["y"] for r in po]) if po else None,
                          "nonpole_n": len(no), "nonpole_win": st.mean([r["y"] for r in no]) if no else None})
        cheap = []
        for cap in (0.05, 0.10, 0.15, 0.20, 0.30):
            sub = [r for r in cross_rows if r["p"] <= cap]
            cheap.append({"cap": cap, "n": len(sub), "wins": sum(1 for r in sub if r["y"] == 1),
                          "mean_net": st.mean([net(r["y"], r["p"]) for r in sub]),
                          "sum": sum(net(r["y"], r["p"]) for r in sub)})
        for idx, cap in enumerate((0.05, 0.10, 0.15, 0.20, 0.30), start=23):
            sub = [r for r in cross_rows if r["p"] <= cap]
            vals = [net(r["y"], r["p"]) for r in sub]
            variants.append({"id": f"V{idx:02d}", "family": "cheap", "rule": f"buy all drivers p<={cap:.2f}",
                             "fill": "p_hist", "n": len(sub), "wins": sum(1 for r in sub if r["y"] == 1),
                             "sum": sum(vals), "mean": st.mean(vals), "sd": st.pstdev(vals),
                             "note": "cross-section, non-tradable price"})
        cross = {"markets": len(cross_rows), "events": len(by_event),
                 "priced": len(cross_rows), "bands": bands, "cheap": cheap,
                 "price_sum_median": st.median(sums), "price_sum_min": min(sums),
                 "price_sum_max": max(sums), "price_sum_le_1_17": sum(1 for x in sums if x <= 1.17)}
        with (HERE / "cross_section.csv").open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["event", "driver", "is_pole", "p_hist", "y", "net_per_share"])
            for r in cross_rows:
                writer.writerow([r["key"], r["driver"], r["is_pole"], r["p"], r["y"], round(net(r["y"], r["p"]), 6)])

    months = None
    if primary:
        first_date = min(dt.date.fromisoformat(r["date"]) for r in primary)
        last_date = max(dt.date.fromisoformat(r["date"]) for r in primary)
        months = (last_date - first_date).days / 30.4375
    contribution = None
    if months:
        annual = sum(primary_vals) * SHARES / months * 12
        contribution = annual / CAPITAL * 100

    results = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": {
            "fee_rate": FEE_RATE, "half_spread": HALF_SPREAD, "shares_per_trade": SHARES,
            "capital_usdt": CAPITAL, "cutoff": "race day 00:00 UTC",
            "fill": "data-api taker BUY in (cutoff, race start), VWAP to 100 shares",
            "model_fit": "2014-2023", "test": "2024-2026", "cushion": 0.05,
            "bins": [{"lo": b[0], "hi": b[1]} for b in BINS],
        },
        "fit": table, "p0": p0, "events": len(rows),
        "pole_wins": sum(1 for r in rows if r["y"] == 1),
        "mean_p_hist": st.mean([r["p_hist"] for r in rows if r["p_hist"] is not None]),
        "mean_modelA": st.mean([r["modelA"] for r in rows]),
        "primary": summarize("A exec100", primary, "exec100"),
        "per_season": per_season,
        "bootstrap": {"n": len(primary_vals), "mean": st.mean(primary_vals),
                      "sd": st.pstdev(primary_vals), "ci95": ci,
                      "p_mean_le_0": sum(1 for x in boots if x <= 0) / len(boots)},
        "break_even_gap": break_even,
        "variants": variants,
        "cross_section": cross,
        "months": months,
        "annual_usdt": (sum(primary_vals) * SHARES / months * 12) if months else None,
        "contribution_pct": contribution,
    }
    (HERE / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
    with (HERE / "all_events.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        cols = ["key", "race", "season", "date", "pole", "margin", "modelA", "p_hist", "first", "exec20",
                "exec100", "exec100_1h", "exec100_3h", "p_hist_q", "exec100_q", "y", "n_buy", "buy_shares"]
        writer.writerow(cols)
        for r in rows:
            writer.writerow([r.get(c) for c in cols])
    with (HERE / "trades.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["event", "race", "season", "date", "pole", "margin", "p_model", "p_hist",
                         "p_fill", "shares", "y", "fee_per_share", "half_spread", "net_per_share", "net_usdt"])
        for r in primary:
            writer.writerow([r["key"], r["race"], r["season"], r["date"], r["pole"], r["margin"],
                             round(r["modelA"], 6), r["p_hist"], round(r["exec100"], 6), SHARES,
                             r["y"], round(fee(r["exec100"]), 6), HALF_SPREAD,
                             round(net(r["y"], r["exec100"]), 6),
                             round(net(r["y"], r["exec100"]) * SHARES, 4)])

    print("\n=== primary ===")
    print(json.dumps(results["primary"], ensure_ascii=False))
    print("bootstrap", json.dumps(results["bootstrap"], ensure_ascii=False))
    print("break_even_gap", break_even)
    print("contribution_pct", contribution, "months", months)
    print("\n=== variants ===")
    for v in variants:
        print(f"{v['id']} {v['rule'][:46]:46s} {v['fill']:12s} n={v['n']:3d} wins={v['wins']:3d} "
              f"sum={v['sum']:+8.4f} mean={v['mean']:+8.4f}")
    if cross:
        print("\n=== cross-section ===")
        print("markets", cross["markets"], "events", cross["events"], "price_sum",
              cross["price_sum_median"], cross["price_sum_min"], cross["price_sum_max"],
              "le1.17", cross["price_sum_le_1_17"])
        for b in cross["bands"]:
            print(f"[{b['lo']:.2f},{b['hi']:.2f}) n={b['n']:3d} meanp={b['meanp']:.3f} win={b['win']:.3f} "
                  f"net={b['mean_net']:+.4f} pole={b['pole_n']}/{b['pole_win']} nonpole={b['nonpole_n']}/{b['nonpole_win']}")


if __name__ == "__main__":
    main()
