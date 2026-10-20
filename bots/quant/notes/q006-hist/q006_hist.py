#!/usr/bin/env python3
"""quant-006 historical executable-price backtest.

Data:
  * Gamma events (closed, tag=tennis) -> winner market, resolution, match start.
  * data-api /trades for each conditionId -> last trade per outcome in a pre-declared window.
  * Sackmann ATP/WTA match CSVs (archival mirror) -> point-in-time Elo replay.

All downloads are cached under _cache/ and are not committed.
"""
import argparse
import datetime as dt
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "_cache"
GAMMA_CACHE = CACHE / "gamma"
SACK_CACHE = CACHE / "sackmann"
TRADE_CACHE = CACHE / "trades"
for d in (GAMMA_CACHE, SACK_CACHE, TRADE_CACHE):
    d.mkdir(parents=True, exist_ok=True)

SACK_RAW = "https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/{tour}/{tour}_matches_{year}.csv"
GAMMA = "https://gamma-api.polymarket.com/events"
TRADES = "https://data-api.polymarket.com/trades"

# pre-declared constants
ELO_SCALE = 400.0
ELO_INIT = 1500.0
ELO_YEARS = list(range(2010, 2027))
PM_DATE_MIN = dt.date(2026, 1, 1)
PM_DATE_MAX = dt.date(2026, 5, 25)       # Sackmann archive last date actually observed
SACK_DATE_WINDOW_BACK = 15              # tournament week(s) start may precede PM match
SACK_DATE_WINDOW_FWD = 2
PRICE_WINDOWS = {
    "main": (dt.timedelta(hours=6), dt.timedelta(minutes=15)),
    "sens": (dt.timedelta(hours=24), dt.timedelta(hours=1)),
}
FEE_RATE = 0.05
HALF_SPREAD = 0.01
EDGE_MIN = 0.02
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (research; quant-006)"}


def log(*a):
    print(*a)


def get_json(url, params=None, cache_path=None, retries=4, timeout=40):
    if cache_path and cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers=HTTP_HEADERS)
            if r.status_code == 200:
                val = r.json()
                if cache_path:
                    cache_path.write_text(json.dumps(val, ensure_ascii=False), encoding="utf-8")
                return val
            last = f"HTTP {r.status_code}: {r.text[:120]}"
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(0.6 * (i + 1))
    raise RuntimeError(f"GET failed {url} {params}: {last}")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def surname(name):
    tok = norm(name).split()
    return tok[-1] if tok else ""


def first_initial(name):
    tok = norm(name).split()
    return tok[0][0] if tok else ""


def person_match(short_name, full_name):
    """Match a PM display name/outcome to a Sackmann full name.

    Handles compound surnames (Barrios vs Barrios Vera) without letting a
    middle name (Martin in Tomas Martin Etcheverry) create a false match.
    """
    p = norm(short_name).split()
    q = norm(full_name).split()
    if not p or not q:
        return False
    if p == q or set(p) == set(q):
        return True
    if p[-1] == q[-1]:
        return True
    if p[0] in q and p[-1] in q:
        return True
    if first_initial(short_name) == first_initial(full_name) and p[-1] in q[-2:]:
        return True
    return False


# ---------------------------------------------------------------- Gamma events
def fetch_gamma_events(date_min, date_max):
    """Gamma caps offset at ~2100, so split the range into 15-day windows."""
    a = dt.datetime.fromisoformat(date_min.replace("Z", "+00:00"))
    b = dt.datetime.fromisoformat(date_max.replace("Z", "+00:00"))
    windows, cur = [], a
    while cur < b:
        nxt = min(b, cur + dt.timedelta(days=15))
        windows.append((cur, nxt))
        cur = nxt
    events = []
    for w0, w1 in windows:
        offset = 0
        while True:
            params = {
                "closed": "true", "tag_slug": "tennis",
                "end_date_min": w0.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date_max": w1.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 100, "offset": offset,
            }
            cache_path = GAMMA_CACHE / f"events_{params['end_date_min'][:10]}_{params['end_date_max'][:10]}_{offset:05d}.json"
            d = get_json(GAMMA, params=params, cache_path=cache_path)
            if not isinstance(d, list):
                raise RuntimeError(f"Gamma returned non-list at {params}: {str(d)[:200]}")
            events.extend(d)
            log(f"  gamma {params['end_date_min'][:10]}..{params['end_date_max'][:10]} offset={offset:5d} got={len(d):3d} total={len(events)}")
            if len(d) < 100:
                break
            offset += 100
    # de-duplicate while preserving order
    seen, out = set(), []
    for e in events:
        key = e.get("id") or e.get("slug")
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out

def parse_dt(value):
    if not value:
        return None
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        try:
            d = dt.datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def event_record(e):
    """Keep only closed ATP/WTA singles winner events with a clear resolution."""
    slug = e.get("slug", "")
    title = e.get("title", "")
    if not (slug.startswith("atp-") or slug.startswith("wta-") or slug.startswith("wta-") or slug.startswith("atp-")):
        return None
    if slug.split("-")[0] not in ("atp", "wta"):
        return None
    if " vs " not in title or " / " in title or "doubles" in title.lower() or "doubles" in slug.lower():
        return None
    markets = e.get("markets") or []
    main = next((m for m in markets if m.get("slug") == slug), None)
    if main is None:
        return None
    cid = main.get("conditionId")
    outcomes = main.get("outcomes")
    prices = main.get("outcomePrices")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except Exception:
            outcomes = None
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except Exception:
            prices = None
    if not cid or not outcomes or not prices or len(outcomes) != 2 or len(prices) != 2:
        return None
    try:
        prices = [float(x) for x in prices]
    except Exception:
        return None
    if sorted(prices) not in ([0.0, 1.0], [0.5, 0.5]):
        return None
    start = parse_dt(main.get("gameStartTime")) or parse_dt(e.get("startTime")) or parse_dt(e.get("eventDate"))
    if start is None:
        return None
    teams = e.get("teams") or []
    names = [t.get("name") for t in teams if isinstance(t, dict) and t.get("name")]
    if len(names) < 2:
        part = title.split(":", 1)[-1]
        if " vs " not in part:
            return None
        names = [x.strip() for x in part.split(" vs ", 1)]
    return {
        "event_slug": slug,
        "tour": slug.split("-")[0],
        "title": title,
        "tournament": title.split(":", 1)[0].strip() if ":" in title else "",
        "player_a": names[0],
        "player_b": names[1],
        "condition_id": cid,
        "outcomes": [str(x) for x in outcomes],
        "outcome_prices": prices,
        "start_utc": start,
        "match_date": start.date(),
        "volume": e.get("volume"),
        "is_qual": bool(re.search(r"qualif", str(e.get("title", "")), re.I)),
        "start_field": "market.gameStartTime" if main.get("gameStartTime") else (
            "event.startTime" if e.get("startTime") else "event.eventDate"),
    }


# ---------------------------------------------------------------- Sackmann data
def sackmann_path(tour, year):
    return SACK_CACHE / f"{tour}_matches_{year}.csv"


def fetch_sackmann(tour, year):
    p = sackmann_path(tour, year)
    if p.exists() and p.stat().st_size > 100:
        return p
    url = SACK_RAW.format(tour=tour, year=year)
    for i in range(4):
        try:
            r = requests.get(url, timeout=90, headers=HTTP_HEADERS)
            if r.status_code == 200 and len(r.content) > 100:
                p.write_bytes(r.content)
                return p
            err = f"HTTP {r.status_code} size={len(r.content)}"
        except Exception as e:  # noqa: BLE001
            err = repr(e)
        time.sleep(1 + i)
    raise RuntimeError(f"Sackmann download failed {url}: {err}")


def load_sackmann():
    frames = []
    for tour in ("atp", "wta"):
        for year in ELO_YEARS:
            try:
                p = fetch_sackmann(tour, year)
            except Exception as e:  # noqa: BLE001
                log(f"  WARN sackmann {tour} {year}: {e}")
                continue
            df = pd.read_csv(p, low_memory=False)
            if df.empty:
                continue
            need = {"tourney_date", "winner_name", "loser_name", "match_num", "tourney_name"}
            if not need.issubset(df.columns):
                log(f"  WARN sackmann {tour} {year} missing columns, skipped")
                continue
            df = df[["tourney_date", "tourney_name", "match_num", "winner_name", "loser_name",
                     "score", "round", "tourney_level"]].copy()
            df["tour"] = tour
            df["year"] = year
            frames.append(df)
    if not frames:
        raise RuntimeError("no Sackmann data")
    df = pd.concat(frames, ignore_index=True)
    df["tourney_date"] = pd.to_datetime(df["tourney_date"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["tourney_date", "winner_name", "loser_name"])
    df["match_num"] = pd.to_numeric(df["match_num"], errors="coerce").fillna(0)
    df = df.sort_values(["tour", "tourney_date", "match_num"]).reset_index(drop=True)
    df["w_sur"] = df.winner_name.map(surname)
    df["l_sur"] = df.loser_name.map(surname)
    df["w_ini"] = df.winner_name.map(first_initial)
    df["l_ini"] = df.loser_name.map(first_initial)
    df["w_norm"] = df.winner_name.map(norm)
    df["l_norm"] = df.loser_name.map(norm)
    return df


def tournament_tokens(s):
    stop = {"open", "tennis", "championships", "championship", "masters", "atp", "wta",
            "qualification", "qualifying", "cup", "the", "and", "de"}
    return {t for t in norm(s).split() if t not in stop and len(t) > 2}


def match_target(rec, sack):
    """Match on surnames inside the tournament window; disambiguate by tournament name."""
    tour = rec["tour"]
    D = rec["match_date"]
    sa, sb = surname(rec["player_a"]), surname(rec["player_b"])
    ia, ib = first_initial(rec["player_a"]), first_initial(rec["player_b"])
    sub = sack[(sack.tour == tour)
               & (sack.tourney_date >= pd.Timestamp(D - dt.timedelta(days=SACK_DATE_WINDOW_BACK)))
               & (sack.tourney_date <= pd.Timestamp(D + dt.timedelta(days=SACK_DATE_WINDOW_FWD)))]
    pa, pb = rec["player_a"], rec["player_b"]
    if sub.empty:
        return None
    mask = sub.apply(lambda r: (
        (person_match(pa, r.winner_name) and person_match(pb, r.loser_name)) or
        (person_match(pb, r.winner_name) and person_match(pa, r.loser_name))), axis=1)
    pair = sub[mask]
    if pair.empty:
        return None
    if len(pair) == 1:
        row = pair.iloc[0]
        method = "name"
    else:
        # first-initial filter
        q = pair[((pair.w_ini == ia) & (pair.l_ini == ib)) | ((pair.w_ini == ib) & (pair.l_ini == ia))]
        if len(q) == 1:
            pair, row, method = q, q.iloc[0], "surname+initial"
        else:
            toks = tournament_tokens(rec.get("tournament", ""))
            scored = []
            if toks:
                for _, r in pair.iterrows():
                    st = tournament_tokens(r.tourney_name)
                    scored.append((len(toks & st) / max(1, len(toks)), r))
            scored.sort(key=lambda x: x[0], reverse=True)
            if scored and scored[0][0] >= 0.5 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
                row, method = scored[0][1], "surname+tournament"
            else:
                return None
    # Record which surname pair orientation matched
    same = row.w_sur == sa and row.l_sur == sb
    return {
        "sack_tourney": row.tourney_name,
        "sack_date": row.tourney_date.date(),
        "sack_round": row["round"],
        "sack_winner": row.winner_name,
        "sack_loser": row.loser_name,
        "match_method": method,
        "date_lag_days": (D - row.tourney_date.date()).days,
        "same_orientation": bool(same),
        "sack_level": row.tourney_level,
    }


# ---------------------------------------------------------------- Elo replay
def build_elo_targets(sack, targets):
    """Replay Sackmann matches before each target's tournament week.

    A target is rated as of the start of its tournament (strictly before tourney_date),
    so no match from the target tournament is used.
    """
    out = {}
    for tour in ("atp", "wta"):
        ts = [t for t in targets if t["tour"] == tour]
        if not ts:
            continue
        sub = sack[sack.tour == tour].sort_values(["tourney_date", "match_num"])
        rows = list(sub[["tourney_date", "winner_name", "loser_name"]].itertuples(index=False, name=None))
        ratings, counts, last_seen = {}, {}, {}
        cursor = 0
        for cutoff in sorted({t["sack_date"] for t in ts}):
            while cursor < len(rows) and rows[cursor][0].date() < cutoff:
                d, w, l = rows[cursor]
                rw, rl = ratings.get(w, ELO_INIT), ratings.get(l, ELO_INIT)
                nw, nl = counts.get(w, 0), counts.get(l, 0)
                exp_w = 1.0 / (1.0 + 10 ** ((rl - rw) / ELO_SCALE))
                kw = 250.0 / ((nw + 5.0) ** 0.4)
                kl = 250.0 / ((nl + 5.0) ** 0.4)
                ratings[w] = rw + kw * (1.0 - exp_w)
                ratings[l] = rl + kl * (0.0 - (1.0 - exp_w))
                counts[w] = nw + 1
                counts[l] = nl + 1
                last_seen[w] = d.date()
                last_seen[l] = d.date()
                cursor += 1
            for t in ts:
                if t["sack_date"] != cutoff:
                    continue
                # target players are the two participants; map from matched Sackmann names
                pw, pl = t["sack_winner"], t["sack_loser"]
                rw, rl = ratings.get(pw, ELO_INIT), ratings.get(pl, ELO_INIT)
                out[t["event_slug"]] = {
                    "elo_winner": rw, "elo_loser": rl,
                    "n_winner": counts.get(pw, 0), "n_loser": counts.get(pl, 0),
                    "p_model_winner": 1.0 / (1.0 + 10 ** ((rl - rw) / ELO_SCALE)),
                }
    return out


# ---------------------------------------------------------------- trades
def fetch_trades(cid):
    p = TRADE_CACHE / f"{cid}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    out, off = [], 0
    while off < 20000:
        params = {"market": cid, "limit": 500, "offset": off}
        data = get_json(TRADES, params=params, cache_path=None)
        if not isinstance(data, list) or not data:
            break
        out.extend(data)
        if len(data) < 500:
            break
        off += 500
    p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def last_print(trades, outcome, start, back, before):
    lo, hi = start - back, start - before
    hits = []
    for t in trades:
        if str(t.get("outcome", "")).strip() != outcome:
            continue
        try:
            ts = dt.datetime.fromtimestamp(int(t["timestamp"]), tz=dt.timezone.utc)
            price = float(t["price"])
        except Exception:
            continue
        if lo <= ts <= hi:
            hits.append((ts, price, t.get("side"), float(t.get("size", 0) or 0)))
    if not hits:
        return None
    hits.sort(key=lambda x: x[0])
    return hits[-1]


def side_ask(trade_price):
    if trade_price is None:
        return None
    return min(0.99, max(0.01, trade_price + HALF_SPREAD))


def fee_per_share(ask):
    return FEE_RATE * ask * (1.0 - ask)


def choose_trade(rec, elo, trades, window):
    back, before = window
    start = rec["start_utc"]
    per = {}
    for o in rec["outcomes"]:
        per[o] = last_print(trades, o, start, back, before)
    if any(v is None for v in per.values()):
        return None
    prices = {o: per[o][1] for o in rec["outcomes"]}
    asks = {o: side_ask(prices[o]) for o in rec["outcomes"]}
    fees = {o: fee_per_share(asks[o]) for o in rec["outcomes"]}
    # map outcomes directly to the matched Sackmann winner/loser
    p_for = {}
    for o in rec["outcomes"]:
        if person_match(o, rec["sack_winner"]):
            p_for[o] = elo["p_model_winner"]
        elif person_match(o, rec["sack_loser"]):
            p_for[o] = 1.0 - elo["p_model_winner"]
        else:
            p_for[o] = None
    if any(v is None for v in p_for.values()):
        return None
    edges = {o: p_for[o] - asks[o] - fees[o] for o in rec["outcomes"]}
    best_o = max(rec["outcomes"], key=lambda o: edges[o])
    triggered = edges[best_o] > EDGE_MIN
    return {
        "last_trade": prices, "ask": asks, "fee": fees,
        "p_model": p_for, "edge": edges, "best_side": best_o,
        "triggered": triggered, "trade_ts": {o: per[o][0] for o in rec["outcomes"]},
        "trade_side": {o: per[o][2] for o in rec["outcomes"]},
        "trade_size": {o: per[o][3] for o in rec["outcomes"]},
    }


def payout_for(outcome, rec):
    idx = rec["outcomes"].index(outcome)
    return rec["outcome_prices"][idx]


def brier_logloss(p, y):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return (p - y) ** 2, -(y * math.log(p) + (1 - y) * math.log(1 - p))


def sign_test(diffs):
    nz = [d for d in diffs if d != 0]
    n = len(nz)
    if n == 0:
        return 0, 0, 1.0
    k = sum(1 for d in nz if d > 0)
    # exact two-sided binomial
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / (2 ** n)
    return k, n, min(1.0, 2 * tail)


def median(vals):
    if not vals:
        return float("nan")
    s = sorted(vals)
    m = len(s) // 2
    return s[m] if len(s) % 2 else 0.5 * (s[m - 1] + s[m])


def mean(vals):
    return sum(vals) / len(vals) if vals else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-events", type=int, default=0, help="debug: cap Gamma events")
    ap.add_argument("--max-matched", type=int, default=0, help="debug: cap matched events")
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()

    log("== quant-006 historical executable-price backtest ==")
    log("access date: 2026-10-20 (UTC); all sources free and keyless")
    log("Sackmann archive mirror: https://github.com/Aneeshers/tennis-sackmann-archive")
    probe = [
        ("canonical repo API", "https://api.github.com/repos/JeffSackmann/tennis_atp"),
        ("canonical raw 2026", "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2026.csv"),
        ("mirror raw ATP 2026", "https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/atp/atp_matches_2026.csv"),
        ("mirror raw WTA 2026", "https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/wta/wta_matches_2026.csv"),
    ]
    log("source probes:")
    for name, url in probe:
        try:
            rr = requests.get(url, timeout=30, headers=HTTP_HEADERS, stream=True)
            log(f"  {name}: HTTP {rr.status_code} bytes={len(rr.raw.read(2048))} (first 2KB)")
        except Exception as e:  # noqa: BLE001
            log(f"  {name}: ERROR {e}")

    # 1) Gamma events
    log("\n[1] fetching closed tennis events from Gamma")
    raw_events = fetch_gamma_events("2025-12-25T00:00:00Z", "2026-05-27T00:00:00Z")
    if args.max_events:
        raw_events = raw_events[:args.max_events]
    log(f"  raw events: {len(raw_events)}")
    recs = []
    for e in raw_events:
        try:
            r = event_record(e)
        except Exception:
            r = None
        if r and PM_DATE_MIN <= r["match_date"] <= PM_DATE_MAX:
            recs.append(r)
    log(f"  ATP/WTA closed singles winner events with clear resolution in {PM_DATE_MIN}..{PM_DATE_MAX}: {len(recs)}")
    from collections import Counter
    log(f"  by tour: {dict(Counter(r['tour'] for r in recs))}")
    log(f"  start field used: {dict(Counter(r['start_field'] for r in recs))}")

    # 2) Sackmann data
    log("\n[2] loading Sackmann match CSVs (2010-2026)")
    sack = load_sackmann()
    for tour in ("atp", "wta"):
        sub = sack[sack.tour == tour]
        log(f"  {tour}: {len(sub)} matches, {sub.tourney_date.min().date()} .. {sub.tourney_date.max().date()}")
    log(f"  last 2026 tourney_date by tour: "
        f"ATP={sack[(sack.tour=='atp') & (sack.year==2026)].tourney_date.max().date()} "
        f"WTA={sack[(sack.tour=='wta') & (sack.year==2026)].tourney_date.max().date()}")

    # 3) match events to Sackmann
    log("\n[3] matching events to Sackmann by surname + tournament-week window")
    matched = []
    method_counts = Counter()
    lag_counts = Counter()
    for r in recs:
        try:
            m = match_target(r, sack)
        except Exception:
            m = None
        if not m:
            continue
        r = dict(r)
        r.update(m)
        matched.append(r)
        method_counts[m["match_method"]] += 1
        lag_counts[m["date_lag_days"]] += 1
    if args.max_matched:
        matched = matched[:args.max_matched]
    method_counts = Counter(r["match_method"] for r in matched)
    lag_counts = Counter(r["date_lag_days"] for r in matched)
    from collections import Counter as _C
    q_by_tour = {t: (sum(1 for r in recs if r["tour"] == t), sum(1 for r in matched if r["tour"] == t)) for t in ("atp", "wta")}
    log(f"  matched: {len(matched)} / {len(recs)} = {len(matched)/max(1,len(recs)):.1%}")
    log(f"  by tour (matched/sampled): {q_by_tour}")
    log(f"  qualifiers in sample: {sum(1 for r in recs if r['is_qual'])}; matched qualifiers: {sum(1 for r in matched if r['is_qual'])}")
    nonq = [r for r in recs if not r["is_qual"]]
    nonq_m = [r for r in matched if not r["is_qual"]]
    log(f"  non-qualifier match rate: {len(nonq_m)}/{len(nonq)} = {len(nonq_m)/max(1,len(nonq)):.1%}")
    log(f"  match methods: {dict(method_counts)}")
    log(f"  date lag (PM match date - Sackmann tourney_date, days): "
        f"min={min(lag_counts) if lag_counts else 'n/a'} max={max(lag_counts) if lag_counts else 'n/a'}")
    log(f"  events with lag <= 2 days: {sum(v for k,v in lag_counts.items() if k <= 2)} / {len(matched)}")
    log("  NOTE: Sackmann only publishes tourney_date (week start), not actual match date, so the")
    log("        literal PM-date +/-2 matching is impossible; a tournament-week window (-15/+2) is used")
    log("        and the subset with lag<=2 is reported above.")

    # one independent result per actual match: keep the first PM listing by start time
    matched.sort(key=lambda r: (r["start_utc"], r["event_slug"]))
    seen_m, dedup = set(), []
    for r in matched:
        key = (r["tour"], r["sack_tourney"], r["sack_date"], r["sack_winner"], r["sack_loser"])
        if key in seen_m:
            continue
        seen_m.add(key)
        dedup.append(r)
    log(f"  duplicate Sackmann matches removed: {len(matched)-len(dedup)}; independent matches: {len(dedup)}")
    matched = dedup

    # 4) Elo
    log("\n[4] point-in-time Elo replay (K=250/(n+5)^0.4, initial 1500, strict pre-tournament cutoff)")
    elo = build_elo_targets(sack, matched)
    log(f"  events with Elo: {len(elo)} / {len(matched)}")

    # 5) trades (parallel)
    log("\n[5] fetching data-api trades and extracting pre-match executable prices")
    trade_map = {}
    uniq = {}
    for r in matched:
        uniq[r["condition_id"]] = r
    def work(item):
        cid, rec = item
        try:
            return cid, fetch_trades(cid), None
        except Exception as e:  # noqa: BLE001
            return cid, None, repr(e)
    warns = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [ex.submit(work, it) for it in uniq.items()]
        done = 0
        for f in as_completed(futs):
            cid, data, err = f.result()
            done += 1
            if err:
                warns.append((cid, err))
            else:
                trade_map[cid] = data
            if done % 100 == 0:
                log(f"  trades fetched: {done}/{len(uniq)}")
    for cid, err in sorted(warns):
        log(f"  WARN trades {cid}: {err}")
    log(f"  markets with trade data: {len(trade_map)} / {len(uniq)}")

    # 6) price / trigger / P&L
    log("\n[6] pricing and frozen trade rule")
    rows = []
    for r in matched:
        e = elo.get(r["event_slug"])
        tr = trade_map.get(r["condition_id"])
        if not e or not tr:
            continue
        w_main = choose_trade(r, e, tr, PRICE_WINDOWS["main"])
        w_sens = choose_trade(r, e, tr, PRICE_WINDOWS["sens"])
        row = {
            "event_slug": r["event_slug"], "tour": r["tour"], "match_date": r["match_date"].isoformat(),
            "start_utc": r["start_utc"].isoformat(), "tournament_pm": r["tournament"],
            "player_a": r["player_a"], "player_b": r["player_b"],
            "outcome_a": r["outcomes"][0], "outcome_b": r["outcomes"][1],
            "resolved_prices": "|".join(f"{x:g}" for x in r["outcome_prices"]),
            "sack_tourney": r["sack_tourney"], "sack_date": r["sack_date"].isoformat(),
            "sack_winner": r["sack_winner"], "sack_loser": r["sack_loser"],
            "sack_round": r.get("sack_round"), "is_qual": r["is_qual"], "match_method": r["match_method"],
            "date_lag_days": r["date_lag_days"],
            "elo_a": None, "elo_b": None, "n_a": None, "n_b": None,
            "p_model_a": None, "p_model_b": None,
            "condition_id": r["condition_id"],
        }
        # orientation: map outcome A directly to the matched Sackmann winner/loser
        pwin = e["p_model_winner"]
        a_is_winner = person_match(r["outcomes"][0], r["sack_winner"])
        a_is_loser = person_match(r["outcomes"][0], r["sack_loser"])
        if a_is_winner:
            pa = pwin
        elif a_is_loser:
            pa = 1.0 - pwin
        else:
            # outcome names cannot be mapped (e.g. unexpected aliases); fill neutral and flag
            pa = 0.5
        row["model_map_ok"] = bool(a_is_winner or a_is_loser)
        row["p_model_a"] = pa
        row["p_model_b"] = 1.0 - pa
        row["elo_a"] = e["elo_winner"] if a_is_winner else (e["elo_loser"] if a_is_loser else None)
        row["elo_b"] = e["elo_loser"] if a_is_winner else (e["elo_winner"] if a_is_loser else None)
        row["n_a"] = e["n_winner"] if a_is_winner else (e["n_loser"] if a_is_loser else None)
        row["n_b"] = e["n_loser"] if a_is_winner else (e["n_winner"] if a_is_loser else None)
        row["has_price_main"] = bool(w_main)
        row["has_price_sens"] = bool(w_sens)
        if w_main:
            ask = w_main["ask"][w_main["best_side"]]
            fee = w_main["fee"][w_main["best_side"]]
            payout = payout_for(w_main["best_side"], r)
            trigger = w_main["triggered"]
            net = payout - ask - fee if trigger else None
            row.update({
                "price_a": w_main["last_trade"][r["outcomes"][0]],
                "price_b": w_main["last_trade"][r["outcomes"][1]],
                "ask_a": w_main["ask"][r["outcomes"][0]],
                "ask_b": w_main["ask"][r["outcomes"][1]],
                "edge_a": w_main["edge"][r["outcomes"][0]],
                "edge_b": w_main["edge"][r["outcomes"][1]],
                "triggered": trigger, "side": w_main["best_side"] if trigger else "",
                "entry_ask": ask if trigger else None, "fee": fee if trigger else None,
                "payout": payout if trigger else None, "net_pnl": net,
            })
        else:
            row.update({"triggered": None, "side": "", "entry_ask": None, "fee": None,
                        "payout": None, "net_pnl": None})
        if w_sens:
            ask = w_sens["ask"][w_sens["best_side"]]
            fee = w_sens["fee"][w_sens["best_side"]]
            payout = payout_for(w_sens["best_side"], r)
            row.update({
                "price_a_sens": w_sens["last_trade"][r["outcomes"][0]],
                "price_b_sens": w_sens["last_trade"][r["outcomes"][1]],
                "edge_a_sens": w_sens["edge"][r["outcomes"][0]],
                "edge_b_sens": w_sens["edge"][r["outcomes"][1]],
                "triggered_sens": w_sens["triggered"],
                "side_sens": w_sens["best_side"] if w_sens["triggered"] else "",
                "entry_ask_sens": ask if w_sens["triggered"] else None,
                "fee_sens": fee if w_sens["triggered"] else None,
                "net_pnl_sens": payout - ask - fee if w_sens["triggered"] else None,
            })
        else:
            row.update({"triggered_sens": None, "side_sens": "", "entry_ask_sens": None,
                        "fee_sens": None, "net_pnl_sens": None})
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        log("ERROR: no rows")
        return 1
    outdir = ROOT
    out_cols = [
        "event_slug", "match_date", "tour", "tournament_pm", "player_a", "player_b",
        "outcome_a", "outcome_b", "resolved_prices", "sack_tourney", "sack_date",
        "sack_round", "sack_winner", "sack_loser", "match_method", "date_lag_days",
        "elo_a", "elo_b", "n_a", "n_b", "p_model_a", "condition_id",
        "price_a", "price_b", "edge_a", "edge_b", "triggered", "side", "entry_ask",
        "fee", "payout", "net_pnl", "triggered_sens", "side_sens", "net_pnl_sens",
    ]
    df[out_cols].to_csv(outdir / "matches.csv", index=False, float_format="%.6f")

    priced = df[df.has_price_main == True].copy()
    trig = priced[priced.triggered == True].copy()
    log(f"  rows: {len(df)}")
    log(f"  matches with both outcome prices in main window: {len(priced)} "
        f"({len(priced)/len(df):.1%} of matched with Elo+trades)")
    log(f"  triggered: {len(trig)} ({len(trig)/max(1,len(priced)):.1%} of priced)")

    def summarize(label, t, netcol, askcol):
        nets = [float(x) for x in t[netcol].dropna().tolist()]
        if not nets:
            log(f"  {label}: no triggered trades")
            return
        asks = [float(x) for x in t.loc[t[netcol].notna(), askcol].tolist()]
        hits = sum(1 for x in t.loc[t[netcol].notna(), "payout"].tolist() if float(x) >= 0.999)
        log(f"  {label}: n={len(nets)} median={median(nets):+.6f} mean={mean(nets):+.6f} "
            f"hit_rate={hits/len(nets):.3f} total_net={sum(nets):+.4f} "
            f"per_$staked={sum(nets)/sum(asks):+.6f}")

    log("\n[7] results (frozen criterion: median net P&L/share <= 0 on triggered => FAIL)")
    if len(trig) >= 30:
        log(f"  N triggered = {len(trig)} (>=30)")
    else:
        log(f"  N triggered = {len(trig)} (<30 => INSUFFICIENT, no padding)")
    summarize("main [start-6h,start-15m]", trig, "net_pnl", "entry_ask")
    sens_trig = priced[priced.triggered_sens == True].copy()
    log(f"  sensitivity window triggered: {len(sens_trig)}")
    summarize("sens [start-24h,start-1h]", sens_trig, "net_pnl_sens", "entry_ask_sens")

    # price bands
    if len(trig):
        bands = [("ask<0.3", lambda x: x < 0.3), ("0.3<=ask<=0.7", lambda x: 0.3 <= x <= 0.7), ("ask>0.7", lambda x: x > 0.7)]
        for name, fn in bands:
            b = trig[trig.entry_ask.map(fn)]
            if len(b):
                nets = [float(x) for x in b.net_pnl.dropna().tolist()]
                log(f"  band {name}: n={len(nets)} median={median(nets):+.6f} mean={mean(nets):+.6f}")

    # Brier / log loss, paired, on priced matches with a clear 1/0 resolution
    bic = priced[priced.resolved_prices.isin(["1|0", "0|1"])].copy()
    log(f"\n[8] forecast comparison on priced, clearly-resolved matches: {len(bic)}")
    b_elo, b_mkt, l_elo, l_mkt, d_b, d_l = [], [], [], [], [], []
    for _, r in bic.iterrows():
        y = 1.0 if r.resolved_prices == "1|0" else 0.0
        pa = float(r.p_model_a)
        if r.price_a is None or r.price_b is None:
            continue
        denom = float(r.price_a) + float(r.price_b)
        if denom <= 0:
            continue
        pm = float(r.price_a) / denom
        be, le = brier_logloss(pa, y)
        bm, lm = brier_logloss(pm, y)
        b_elo.append(be); b_mkt.append(bm); l_elo.append(le); l_mkt.append(lm)
        d_b.append(be - bm); d_l.append(le - lm)
    if b_elo:
        k, n, pval = sign_test(d_b)
        log(f"  Elo  Brier={mean(b_elo):.6f}  market Brier={mean(b_mkt):.6f}  diff(elo-mkt)={mean(d_b):+.6f}")
        log(f"  Elo  logloss={mean(l_elo):.6f}  market logloss={mean(l_mkt):.6f}  diff(elo-mkt)={mean(d_l):+.6f}")
        log(f"  Brier paired sign test: elo worse in {k}/{n}, better in {n-k}/{n}, two-sided p={pval:.4f}")
        k2, n2, pval2 = sign_test(d_l)
        log(f"  logloss paired sign test: elo worse in {k2}/{n2}, better in {n2-k2}/{n2}, two-sided p={pval2:.4f}")
    else:
        log("  no pairs")
    log(f"  mean |p_model - p_market| = {mean([abs(float(r.p_model_a) - float(r.price_a)/(float(r.price_a)+float(r.price_b))) for _, r in bic.iterrows() if r.price_a is not None and r.price_b is not None and (float(r.price_a)+float(r.price_b))>0]):.6f}")

    # robustness: matches whose PM date is closest to the Sackmann week start
    sub2 = df[(df.date_lag_days <= 2) & (df.triggered.notna())].copy()
    tr2 = sub2[sub2.triggered == True]
    log(f"\n[8b] robustness: date_lag_days <= 2 subset (closest to literal PM-date +/-2)")
    log(f"  priced={len(sub2)} triggered={len(tr2)} "
        f"median={median([float(x) for x in tr2.net_pnl.dropna().tolist()]):+.6f} "
        f"mean={mean([float(x) for x in tr2.net_pnl.dropna().tolist()]):+.6f}"
        if len(tr2) else "  no triggered trades")

    # verdict
    log("\n[9] verdict")
    if len(trig) < 30:
        verdict = "INSUFFICIENT"
        log(f"  {verdict}: only {len(trig)} triggered trades; frozen criterion needs >=30. No padding.")
    else:
        med = median([float(x) for x in trig.net_pnl.dropna().tolist()])
        verdict = "FAIL" if med <= 0 else "PASS"
        log(f"  median net P&L/share = {med:+.6f} -> {verdict} (criterion: median <= 0 => FAIL)")

    # extra facts
    log("\n[10] data accounting")
    if len(df):
        log(f"  PM match date range: {df.match_date.min()} .. {df.match_date.max()}")
        log(f"  Sackmann tourney_date range (matched): {df.sack_date.min()} .. {df.sack_date.max()}")
        log(f"  matched by tour: {dict(Counter(df.tour))}")
        log(f"  match method: {dict(Counter(df.match_method))}")
        log(f"  priced by tour: {dict(Counter(priced.tour))}")
        log(f"  triggered by tour: {dict(Counter(trig.tour)) if len(trig) else {}}")
        log(f"  resolutions: {dict(Counter(df.resolved_prices))}")
        log(f"  triggered resolutions: {dict(Counter(trig.resolved_prices)) if len(trig) else {}}")
        log(f"  median prior matches: a={df.n_a.median():.1f} b={df.n_b.median():.1f}")
        if len(trig):
            log(f"  triggered side distribution: {dict(Counter(trig.side))}")
            log(f"  triggered entry ask: min={trig.entry_ask.min():.4f} median={trig.entry_ask.median():.4f} max={trig.entry_ask.max():.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
