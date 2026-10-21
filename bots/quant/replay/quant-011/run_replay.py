#!/usr/bin/env python3
"""quant-011 historical executable-price backtest.

PRE-DECLARED DESIGN (written before looking at any result)
==========================================================
Leagues (football-data code -> Polymarket tag/prefix):
  E0  Premier League   EPL / epl-
  I1  Serie A          serie-a / ita-, serie-a-, italian-serie-a-
  SP1 La Liga          la-liga / lal-, la-liga-
  D1  Bundesliga       bundesliga / bun-, bundesliga-
  F1  Ligue 1          ligue-1 / fl1-, ligue-1-
These are the entry's two leagues (E0/I1) plus the other three top-5
European leagues for which both football-data CSVs and closed Polymarket
match events with a draw market exist.

Base-rate model (the entry's rule):
  qD = (1/B365D) / (1/B365H + 1/B365D + 1/B365A) from football-data
  closing B365 odds.  Buckets are 0.04 wide starting at qD=0.14
  ([0.14,0.18), [0.18,0.22), ...).  The base rate for a match is the
  realised draw frequency in the SAME league and SAME bucket using only
  football-data seasons STRICTLY BEFORE the match's season (expanding
  walk-forward, no same-season leakage).  If that cell has n < 30, fall
  back to the pooled five-league cell for prior seasons (still n >= 30);
  otherwise the match is not tradable.

Decision time T = kickoff - 1h, kickoff from the Gamma market
`gameStartTime`.  Primary market print: the last data-api trade on the
draw market's YES (a NO print at p is converted to YES = 1-p) with
timestamp in [T-6h, T].  Sensitivity prints: last trade in [T-24h, T-1h]
and last trade in [T-1h, T] (freshness check).
Only prints exist in the public data, so executable ask is approximated
as last YES print + 0.01 (one cent half-spread).  No print => unpriced,
no fill.

Trade rule (entry): buy draw YES when
  0.15 <= ask <= 0.30  (entry price band / wide qD bucket)
  base_rate is available and ask <= base_rate - 0.02
where 0.02 is the entry's cost buffer (its own example: fee ~0.008 +
half-spread 0.01, rounded up).  One share per match, hold to settlement,
one independent observation per match.  Taker fee per GUIDE section 8:
  fee per share = 0.05 * ask * (1 - ask)     (sports taker rate 0.05)
  net per share = draw_payout - ask - fee
The 1c half-spread is already embedded in the ask, so it is not charged
a second time.

Resolution check: Gamma draw-market outcomePrices vs football-data FTR.
Mismatches are reported; P&L/Brier use FTR as outcome of record and
mismatches are excluded from the scored sample.

Verdict (entry's frozen rule): INSUFFICIENT if triggered < 30; else FAIL
if median net P&L per share <= 0; else PASS.

Sources (keyless, no login, no wallet):
  gamma-api.polymarket.com/events/keyset  (closed events)
  data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N
  www.football-data.co.uk/mmz4281/<season>/<league>.csv

Usage:
  python3 run_replay.py --match-only   # linkage diagnostics, no trades
  python3 run_replay.py                # full run, cache when present
  python3 run_replay.py --refresh      # ignore cache
  python3 run_replay.py --cache-dir DIR --out-dir DIR   # keep raw cache outside replay/
"""

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
import math
import re
import statistics
import sys
import threading
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
# Raw downloads and the intermediate matches.csv stay under scratch/ (gitignored).
DEFAULT_SCRATCH = HERE.parents[1] / "notes/scheduler/scratch/P-quant-011"
CACHE = DEFAULT_SCRATCH / "_cache"
OUT_DIR = DEFAULT_SCRATCH
GAMMA = "https://gamma-api.polymarket.com"
DATA = "https://data-api.polymarket.com"
FD = "https://www.football-data.co.uk/mmz4281"
AS_OF = "2026-10-21"

FEE_RATE = 0.05
HALF_SPREAD = 0.01
THRESHOLD = 0.02
BAND_LO, BAND_HI = 0.15, 0.30
PRIMARY_HOURS = (6, 0)       # [T-6h, T]
SENS_HOURS = (24, 1)         # [T-24h, T-1h]
NARROW_HOURS = (1, 0)        # [T-1h, T] freshness check
MIN_BUCKET_N = 30
SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324",
           "2425", "2526", "2627"]

LEAGUES = {
    "E0": {"name": "Premier League", "tags": ["EPL", "premier-league"],
           "prefixes": ("epl-",)},
    "I1": {"name": "Serie A", "tags": ["serie-a"],
           "prefixes": ("ita-", "serie-a-", "italian-serie-a-")},
    "SP1": {"name": "La Liga", "tags": ["la-liga"],
            "prefixes": ("lal-", "la-liga-")},
    "D1": {"name": "Bundesliga", "tags": ["bundesliga"],
           "prefixes": ("bun-", "bundesliga-")},
    "F1": {"name": "Ligue 1", "tags": ["ligue-1"],
           "prefixes": ("fl1-", "ligue-1-")},
}

REFRESH = False
UA = "quant-research-q011/1.0 (keyless public data)"
_tls = threading.local()


def session():
    s = getattr(_tls, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        _tls.s = s
    return s


def cache_key(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def get_json(url, retries=6, pause=0.05):
    path = CACHE / (cache_key(url) + ".json")
    if path.exists() and not REFRESH:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink()
    last = None
    for attempt in range(retries):
        try:
            r = session().get(url, timeout=60)
            if r.status_code in (400, 422):
                raise RuntimeError("HTTP %s: %s" % (r.status_code, r.text[:200]))
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError("HTTP %s" % r.status_code)
            r.raise_for_status()
            data = r.json()
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, separators=(",", ":")),
                            encoding="utf-8")
            time.sleep(pause)
            return data
        except Exception as exc:  # noqa: BLE001 - retry network errors
            last = exc
            time.sleep(min(2 ** attempt * 0.5, 8))
    raise RuntimeError("GET failed %s: %s" % (url, last))


def get_text(url):
    path = CACHE / (cache_key(url) + ".txt")
    if path.exists() and not REFRESH:
        return path.read_text(encoding="latin-1")
    last = None
    for attempt in range(6):
        try:
            r = session().get(url, timeout=60)
            if r.status_code == 404:
                raise RuntimeError("HTTP 404")
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError("HTTP %s" % r.status_code)
            r.raise_for_status()
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(r.content.decode("latin-1"), encoding="latin-1")
            time.sleep(0.05)
            return r.content.decode("latin-1")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(min(2 ** attempt * 0.5, 8))
    raise RuntimeError("GET failed %s: %s" % (url, last))


# ---------------------------------------------------------------- Gamma
def fetch_league_events(tag):
    events = []
    cursor = None
    for _ in range(100):
        params = {"closed": "true", "tag_slug": tag, "limit": 100}
        if cursor:
            params["after_cursor"] = cursor
        url = GAMMA + "/events/keyset?" + urllib.parse.urlencode(params)
        payload = get_json(url)
        page = payload.get("events", [])
        events.extend(page)
        cursor = payload.get("next_cursor")
        if not page or not cursor:
            break
    return events


def draw_market(event):
    for m in event.get("markets", []):
        q = (m.get("question") or "").lower()
        slug = (m.get("slug") or "").lower()
        if "end in a draw" in q or slug.endswith("-draw"):
            return m
    return None


def parse_json_list(value):
    if isinstance(value, list):
        return value
    try:
        return json.loads(value or "[]")
    except Exception:
        return []


def parse_dt(value):
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(text)
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def league_of(slug):
    for code, cfg in LEAGUES.items():
        if slug.startswith(cfg["prefixes"]):
            return code
    return None


def split_teams(title, slug):
    text = title or ""
    if ":" in text:
        text = text.split(":", 1)[1]
    text = re.sub(r"\s+[-–]\s+.*$", "", text).strip()
    parts = re.split(r"\s+vs\.?\s+", text, maxsplit=1, flags=re.I)
    if len(parts) == 2 and parts[0] and parts[1]:
        return parts[0].strip(), parts[1].strip()
    body = re.sub(r"-more-markets$", "", slug)
    body = re.sub(r"-\d{4}-\d{2}-\d{2}.*$", "", body)
    body = re.sub(r"-\d{2}-\d{2}$", "", body)
    body = re.sub(r"^(epl|lal|bun|fl1|ita|serie-a|la-liga|bundesliga|"
                  r"ligue-1|italian-serie-a)-", "", body)
    parts = body.split("-vs-", 1)
    if len(parts) == 2:
        return parts[0].replace("-", " "), parts[1].replace("-", " ")
    return "", ""


def collect_events():
    by_id = {}
    for code, cfg in LEAGUES.items():
        for tag in cfg["tags"]:
            for ev in fetch_league_events(tag):
                if ev.get("id") in by_id:
                    continue
                slug = ev.get("slug") or ""
                if league_of(slug) != code:
                    continue
                label = ((ev.get("title") or "") + " " + slug).lower()
                if re.search(r"half ?time|1st half|first half|second half|"
                             r"ht result|halftime", label):
                    continue
                dm = draw_market(ev)
                if not dm:
                    continue
                if not dm.get("conditionId"):
                    continue
                by_id[ev["id"]] = (code, ev, dm)
    return list(by_id.values())


# ------------------------------------------------------- football-data
def fd_season(season):
    return "20%s/%s" % (season[:2], season[2:])


def season_of_date(d):
    start = d.year if d.month >= 8 else d.year - 1
    return "%02d%02d" % (start % 100, (start + 1) % 100)


def load_football_data():
    rows = []
    for code in LEAGUES:
        for season in SEASONS:
            url = "%s/%s/%s.csv" % (FD, season, code)
            try:
                text = get_text(url)
            except Exception as exc:  # noqa: BLE001
                print("WARN fd fetch %s %s: %s" % (code, season, exc))
                continue
            if not text.strip():
                continue
            df = pd.read_csv(io.StringIO(text), encoding="latin-1")
            df.columns = [c.strip() for c in df.columns]
            for _, r in df.iterrows():
                ftr = str(r.get("FTR", "")).strip().upper()
                try:
                    b365h = float(r.get("B365H"))
                    b365d = float(r.get("B365D"))
                    b365a = float(r.get("B365A"))
                except Exception:
                    continue
                if ftr not in ("H", "D", "A"):
                    continue
                if not all(math.isfinite(x) and x > 1.0
                           for x in (b365h, b365d, b365a)):
                    continue
                date = pd.to_datetime(r.get("Date"), dayfirst=True,
                                      errors="coerce")
                if pd.isna(date):
                    continue
                inv = 1 / b365h + 1 / b365d + 1 / b365a
                qd = (1 / b365d) / inv
                rows.append({
                    "league": code,
                    "season": season,
                    "season_label": fd_season(season),
                    "date": date.date(),
                    "home": str(r.get("HomeTeam", "")).strip(),
                    "away": str(r.get("AwayTeam", "")).strip(),
                    "ftr": ftr,
                    "qD": qd,
                })
    return rows


# ------------------------------------------------------------ matching
DROP_TOKENS = {
    "fc", "cf", "sc", "ac", "afc", "cd", "sv", "vfl", "vfb", "tsg",
    "fsv", "ogc", "rc", "as", "ssc", "us", "ss", "calcio", "club",
    "de", "futbol", "football", "the", "afc", "bk", "if", "ff",
    "rcd", "ud", "ca", "sad", "ssc", "real",
}

ALIASES = {
    # England
    "manchester city": "man city", "man city": "man city",
    "manchester united": "man united", "manchester utd": "man united",
    "man united": "man united", "nottm forest": "nottm forest",
    "nottingham forest": "nottm forest", "newcastle united": "newcastle",
    "tottenham hotspur": "tottenham", "wolverhampton": "wolves",
    "wolverhampton wanderers": "wolves", "brighton and hove albion": "brighton",
    "spurs": "tottenham", "villa": "aston villa", "athletic": "ath bilbao",
    "espanyol": "espanol", "espanyol barcelona": "espanol",
    "atletico": "ath madrid", "sociedad": "sociedad", "betis": "betis",
    "racing club": "santander", "racing santander": "santander",
    "real racing club": "santander",
    "brighton hove albion": "brighton", "west ham united": "west ham",
    "leicester city": "leicester", "ipswich town": "ipswich",
    "sheffield utd": "sheffield united", "luton town": "luton",
    "leeds united": "leeds", "norwich city": "norwich", "hull city": "hull",
    "west bromwich albion": "west brom", "coventry city": "coventry",
    "afc bournemouth": "bournemouth", "cardiff city": "cardiff",
    # Italy
    "ac milan": "milan", "milan": "milan", "inter milan": "inter",
    "internazionale": "inter", "as roma": "roma", "ssc napoli": "napoli",
    "hellas verona": "verona", "parma calcio 1913": "parma",
    # Spain
    "atletico madrid": "ath madrid", "atletico de madrid": "ath madrid",
    "athletic bilbao": "ath bilbao", "athletic club": "ath bilbao",
    "real sociedad": "sociedad", "real betis": "betis",
    "rayo vallecano": "vallecano", "celta vigo": "celta",
    "deportivo alaves": "alaves", "real valladolid": "valladolid",
    "real oviedo": "oviedo", "fc barcelona": "barcelona",
    # Germany
    "bayern munich": "bayern munich", "bayern munchen": "bayern munich",
    "borussia dortmund": "dortmund", "bayer leverkusen": "leverkusen",
    "rb leipzig": "rb leipzig", "vfb stuttgart": "stuttgart",
    "eintracht frankfurt": "ein frankfurt", "ein Frankfurt": "ein frankfurt",
    "borussia monchengladbach": "m gladbach", "mgladbach": "m gladbach",
    "vfl wolfsburg": "wolfsburg", "union berlin": "union berlin",
    "1 fc union berlin": "union berlin", "sc freiburg": "freiburg",
    "tsg hoffenheim": "hoffenheim", "1 fsv mainz 05": "mainz",
    "mainz 05": "mainz", "fc augsburg": "augsburg",
    "werder bremen": "werder bremen", "vfl bochum": "bochum",
    "1 fc heidenheim": "heidenheim", "fc st pauli": "st pauli",
    "holstein kiel": "holstein kiel", "fc koln": "fc koln",
    # France
    "paris saint germain": "paris sg", "paris st germain": "paris sg",
    "psg": "paris sg", "olympique marseille": "marseille",
    "olympique de marseille": "marseille", "olympique lyonnais": "lyon",
    "as monaco": "monaco", "losc lille": "lille", "ogc nice": "nice",
    "rc lens": "lens", "stade rennais": "rennes",
    "stade rennais fc 1901": "rennes", "as saint etienne": "st etienne",
}


def norm_name(name):
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    tokens = [t for t in text.split() if t and t not in DROP_TOKENS]
    text = " ".join(tokens)
    text = re.sub(r"\b(1[0-9]{3}|0[0-9])\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return ALIASES.get(text, text)


def team_sim(a, b):
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    if ta and tb and (ta <= tb or tb <= ta):
        return 0.93
    jac = len(ta & tb) / len(ta | tb)
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    return max(seq, 0.5 * seq + 0.5 * jac)


def match_to_fd(code, kickoff, pm_home, pm_away, fd_rows):
    d = kickoff.date()
    best = None
    for r in fd_rows:
        if r["league"] != code:
            continue
        delta = abs((r["date"] - d).days)
        if delta > 1:
            continue
        hs = team_sim(pm_home, r["home"])
        as_ = team_sim(pm_away, r["away"])
        if hs < 0.55 or as_ < 0.55:
            continue
        score = (hs + as_) / 2 - 0.03 * delta
        if score < 0.68:
            continue
        if best is None or score > best[0]:
            best = (score, r)
    return best[1] if best else None


def bucket_index(q):
    return int(math.floor((q - 0.14) / 0.04))


def bucket_label(idx):
    lo = 0.14 + 0.04 * idx
    return "[%.2f,%.2f)" % (lo, lo + 0.04)


# --------------------------------------------------------------- trades
def fetch_trades(condition_id, lower_ts, upper_ts, max_pages=40):
    """Newest-first pages until the page goes below lower_ts."""
    out = []
    for page in range(max_pages):
        url = "%s/trades?%s" % (DATA, urllib.parse.urlencode({
            "market": condition_id, "limit": 500, "offset": page * 500,
        }))
        data = get_json(url)
        if not data:
            break
        out.extend(data)
        stamps = [int(t.get("timestamp", 0)) for t in data]
        if min(stamps) < lower_ts:
            break
    return out


def yes_price(trade):
    try:
        p = float(trade.get("price"))
    except Exception:
        return None
    outcome = str(trade.get("outcome", "")).lower()
    if outcome == "yes":
        return p
    if outcome == "no":
        return 1.0 - p
    return None


def last_yes_in(trades, lo_ts, hi_ts):
    best = None
    for t in trades:
        ts = int(t.get("timestamp", 0))
        if lo_ts <= ts <= hi_ts:
            p = yes_price(t)
            if p is None:
                continue
            if best is None or ts > best[0]:
                best = (ts, p)
    return best


def resolved_draw(dm):
    outcomes = parse_json_list(dm.get("outcomes"))
    prices = parse_json_list(dm.get("outcomePrices"))
    for i, o in enumerate(outcomes):
        if str(o).lower() == "yes" and i < len(prices):
            try:
                return float(prices[i]) > 0.5
            except Exception:
                return None
    return None


# ------------------------------------------------------------- analysis
def fee(price):
    return FEE_RATE * price * (1 - price)


def sign_test(diffs):
    pos = sum(1 for x in diffs if x > 1e-12)
    neg = sum(1 for x in diffs if x < -1e-12)
    n = pos + neg
    if n == 0:
        return pos, neg, 1.0
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return pos, neg, min(1.0, 2 * tail)


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def fmt_pct(x):
    return "n/a" if x is None else "%+.2f%%" % (100 * x)


def summarize(rows, ask_key, trig_key, net_key):
    priced = sum(1 for r in rows if r.get(ask_key) is not None)
    trig = [r for r in rows if r.get(trig_key)]
    n = len(trig)
    if n == 0:
        return {"n": 0, "priced": priced}
    nets = [r[net_key] for r in trig]
    staked = sum(r[ask_key] for r in trig)
    return {
        "n": n,
        "priced": priced,
        "median": statistics.median(nets),
        "mean": statistics.fmean(nets),
        "total": sum(nets),
        "per_dollar": sum(nets) / staked if staked else None,
        "hit": sum(1 for x in nets if x > 0) / n,
    }


def summary_line(label, s):
    if s["n"] == 0:
        return "| %s | %d | 0 | - | - | - | - | - |" % (label, s["priced"])
    return ("| %s | %d | %d | %+.4f | %+.4f | %+.4f | %+.2f%% | %.1f%% |"
            % (label, s["priced"], s["n"], s["median"], s["mean"],
               s["total"], 100 * s["per_dollar"], 100 * s["hit"]))


def main():
    global REFRESH, CACHE, OUT_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--match-only", action="store_true")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    REFRESH = args.refresh
    if args.cache_dir:
        CACHE = Path(args.cache_dir)
    if args.out_dir:
        OUT_DIR = Path(args.out_dir)

    print("quant-011 historical executable-price backtest")
    print("access date: %s | leagues: %s" % (AS_OF, ", ".join(LEAGUES)))
    print("fee=%.2f half_spread=%.2f threshold=%.2f band=[%.2f,%.2f]"
          % (FEE_RATE, HALF_SPREAD, THRESHOLD, BAND_LO, BAND_HI))
    print("primary window [T-6h,T], sensitivity [T-24h,T-1h], T=kickoff-1h")
    print()

    events = collect_events()
    print("Gamma closed soccer events with a draw market in chosen leagues: %d"
          % len(events))
    per_league = {}
    for code, ev, dm in events:
        per_league[code] = per_league.get(code, 0) + 1
    print("  by league: " + ", ".join("%s=%d" % (k, per_league.get(k, 0))
                                      for k in LEAGUES))

    fd_rows = load_football_data()
    print("football-data rows with FTR and B365 odds: %d (seasons %s..%s)"
          % (len(fd_rows), SEASONS[0], SEASONS[-1]))
    print()

    # Link events to football-data rows; de-duplicate one event per row.
    candidates = []
    unmatched = []
    for code, ev, dm in events:
        kickoff = parse_dt(dm.get("gameStartTime")) or parse_dt(ev.get("endDate"))
        if kickoff is None:
            unmatched.append((code, ev, "no gameStartTime"))
            continue
        pm_home, pm_away = split_teams(ev.get("title"), ev.get("slug", ""))
        if not pm_home or not pm_away:
            unmatched.append((code, ev, "cannot parse teams"))
            continue
        row = match_to_fd(code, kickoff, pm_home, pm_away, fd_rows)
        if row is None:
            unmatched.append((code, ev, "no football-data row"))
            continue
        candidates.append({"code": code, "ev": ev, "dm": dm,
                           "kickoff": kickoff, "pm_home": pm_home,
                           "pm_away": pm_away, "row": row})

    by_row = {}
    for c in candidates:
        key = (c["row"]["league"], c["row"]["date"], c["row"]["home"],
               c["row"]["away"])
        c["dup_count"] = 0
        if key not in by_row:
            by_row[key] = c
        else:
            c["dup_count"] = 1
            keep = by_row[key]
            # prefer the slug without "more-markets", then the earlier id
            if "more-markets" in keep["ev"]["slug"] and \
                    "more-markets" not in c["ev"]["slug"]:
                c["dup_count"] = keep.get("dup_count", 0) + 1
                by_row[key] = c
    matched = list(by_row.values())
    dup = len(candidates) - len(matched)

    total = len(events)
    print("Linkage: %d / %d events matched to a football-data row (%.1f%%), "
          "%d unmatched, %d duplicate events collapsed"
          % (len(matched), total, 100 * len(matched) / total if total else 0,
             len(unmatched), dup))
    if unmatched:
        print("Unmatched examples:")
        for code, ev, why in unmatched[:15]:
            print("  %s | %s | %s | %s"
                  % (code, ev.get("slug"), ev.get("title"), why))
    print()

    if args.match_only:
        print("--match-only: stopping before trade downloads.")
        return

    fd_by_league = {}
    for r in fd_rows:
        fd_by_league.setdefault(r["league"], []).append(r)
    fd_by_season_league = {}
    for r in fd_rows:
        fd_by_season_league.setdefault((r["league"], r["season"]), []).append(r)

    # Pre-compute walk-forward base rates per (league, season, bucket).
    base_cache = {}

    def base_rate(code, season, qd):
        idx = bucket_index(qd)
        key = (code, season, idx)
        if key in base_cache:
            return base_cache[key]
        prior = [r for r in fd_rows
                 if r["league"] == code and r["season"] < season
                 and bucket_index(r["qD"]) == idx]
        n = len(prior)
        if n >= MIN_BUCKET_N:
            rate = sum(1 for r in prior if r["ftr"] == "D") / n
            out = (rate, n, "league")
        else:
            pooled = [r for r in fd_rows
                      if r["season"] < season
                      and bucket_index(r["qD"]) == idx]
            n2 = len(pooled)
            if n2 >= MIN_BUCKET_N:
                rate = sum(1 for r in pooled if r["ftr"] == "D") / n2
                out = (rate, n2, "pooled")
            else:
                out = (None, n, "insufficient")
        base_cache[key] = out
        return out

    lower_margin = 24 * 3600
    max_window = max(PRIMARY_HOURS[0], SENS_HOURS[0], NARROW_HOURS[0]) * 3600
    rows = []
    print("Downloading data-api trades for %d linked draw markets ..."
          % len(matched))

    def work(c):
        dm = c["dm"]
        T = c["kickoff"] - dt.timedelta(hours=1)
        Tts = int(T.timestamp())
        lower = Tts - max_window
        try:
            trades = fetch_trades(dm["conditionId"], lower, Tts)
        except Exception as exc:  # noqa: BLE001
            return c, None, str(exc)
        return c, trades, None

    results = []
    errors = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(work, c) for c in matched]
        done = 0
        for fut in as_completed(futures):
            c, trades, err = fut.result()
            done += 1
            if err:
                errors += 1
                c["trade_error"] = err
                results.append(c)
                continue
            c["trades"] = trades
            results.append(c)
            if done % 250 == 0:
                print("  %d / %d markets fetched" % (done, len(futures)))
    print("  trade fetch errors: %d" % errors)

    for c in results:
        r = c["row"]
        T = c["kickoff"] - dt.timedelta(hours=1)
        Tts = int(T.timestamp())
        p_lo = Tts - PRIMARY_HOURS[0] * 3600
        p_hi = Tts - PRIMARY_HOURS[1] * 3600
        s_lo = Tts - SENS_HOURS[0] * 3600
        s_hi = Tts - SENS_HOURS[1] * 3600
        n_lo = Tts - NARROW_HOURS[0] * 3600
        n_hi = Tts - NARROW_HOURS[1] * 3600
        trades = c.get("trades") or []
        prim = last_yes_in(trades, p_lo, p_hi)
        sens = last_yes_in(trades, s_lo, s_hi)
        narrow = last_yes_in(trades, n_lo, n_hi)
        base, bn, bsrc = base_rate(c["code"], r["season"], r["qD"])
        y = 1.0 if r["ftr"] == "D" else 0.0
        res = resolved_draw(c["dm"])
        res_match = (res is not None and (res == (r["ftr"] == "D")))
        row = {
            "league": c["code"],
            "season": r["season_label"],
            "date": r["date"].isoformat(),
            "kickoff_utc": c["kickoff"].isoformat(),
            "event_slug": c["ev"]["slug"],
            "condition_id": c["dm"]["conditionId"],
            "pm_home": c["pm_home"],
            "pm_away": c["pm_away"],
            "fd_home": r["home"],
            "fd_away": r["away"],
            "ftr": r["ftr"],
            "resolved_draw": res,
            "resolution_match": res_match,
            "qD": r["qD"],
            "bucket": bucket_label(bucket_index(r["qD"])),
            "base_rate": base,
            "base_n": bn,
            "base_source": bsrc,
            "trades_fetched": len(trades),
            "trades_primary": sum(1 for t in trades
                                  if p_lo <= int(t.get("timestamp", 0)) <= p_hi),
            "trades_sens": sum(1 for t in trades
                               if s_lo <= int(t.get("timestamp", 0)) <= s_hi),
        }
        for prefix, point, ask_key, trig_key, net_key in [
            ("prim", prim, "ask", "triggered", "net"),
            ("sens", sens, "sens_ask", "sens_triggered", "sens_net"),
            ("narrow", narrow, "narrow_ask", "narrow_triggered", "narrow_net"),
        ]:
            if point is None:
                row[ask_key] = None
                row[trig_key] = False
                row[net_key] = None
                row[prefix + "_yes_last"] = None
                row[prefix + "_ts"] = None
                continue
            ts, yp = point
            ask = yp + HALF_SPREAD
            row[prefix + "_yes_last"] = yp
            row[prefix + "_ts"] = ts
            row[ask_key] = ask
            trig = (base is not None and BAND_LO <= ask <= BAND_HI
                    and ask <= base - THRESHOLD)
            row[trig_key] = trig
            row[net_key] = (y - ask - fee(ask)) if trig else None
        rows.append(row)

    rows.sort(key=lambda x: (x["date"], x["league"], x["event_slug"]))

    # ------------------------------------------------------------ output
    priced = [r for r in rows if r["prim_yes_last"] is not None]
    res_known = [r for r in rows if r["resolved_draw"] is not None]
    res_ok = [r for r in res_known if r["resolution_match"]]
    print()
    print("Priced (primary window has a print): %d / %d matched matches"
          % (len(priced), len(rows)))
    print("Resolved draw outcome available: %d; agrees with FTR: %d (%.1f%%)"
          % (len(res_known), len(res_ok),
             100 * len(res_ok) / len(res_known) if res_known else 0))
    mism = [r for r in res_known if not r["resolution_match"]]
    if mism:
        print("Resolution mismatches (first 10):")
        for r in mism[:10]:
            print("  %s %s %s-%s | FTR=%s resolved_draw=%s"
                  % (r["date"], r["league"], r["fd_home"], r["fd_away"],
                     r["ftr"], r["resolved_draw"]))
    print()

    # Exclude resolution mismatches from scoring / P&L.
    good = [r for r in rows if r["resolution_match"]]
    print("Primary window results (one share per triggered match, "
          "mismatches excluded):")
    print("| group | priced | triggered | median net/share | mean net/share | "
          "total net/share | total per $ staked | hit rate |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    s_all = summarize(good, "ask", "triggered", "net")
    print(summary_line("ALL", s_all))
    for code in LEAGUES:
        s = summarize([r for r in good if r["league"] == code],
                      "ask", "triggered", "net")
        print(summary_line(code, s))
    seasons = sorted({r["season"] for r in good})
    for season in seasons:
        s = summarize([r for r in good if r["season"] == season],
                      "ask", "triggered", "net")
        print(summary_line(season, s))
    print()

    print("Sensitivity window [T-24h,T-1h] results:")
    print("| group | priced | triggered | median net/share | mean net/share | "
          "total net/share | total per $ staked | hit rate |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    ss_all = summarize(good, "sens_ask", "sens_triggered", "sens_net")
    print(summary_line("ALL", ss_all))
    for code in LEAGUES:
        s = summarize([r for r in good if r["league"] == code],
                      "sens_ask", "sens_triggered", "sens_net")
        print(summary_line(code, s))
    for season in seasons:
        s = summarize([r for r in good if r["season"] == season],
                      "sens_ask", "sens_triggered", "sens_net")
        print(summary_line(season, s))
    print()

    print("Freshness window [T-1h,T] summary:")
    print("| group | priced | triggered | median net/share | mean net/share | "
          "total net/share | total per $ staked | hit rate |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    print(summary_line("ALL", summarize(good, "narrow_ask", "narrow_triggered", "narrow_net")))
    for code in LEAGUES:
        print(summary_line(code, summarize([r for r in good if r["league"] == code],
                                           "narrow_ask", "narrow_triggered", "narrow_net")))
    print()

    # Trigger diagnostics.
    trig = [r for r in good if r["triggered"]]
    if trig:
        print("Primary trigger diagnostics: n=%d, base_rate median=%.4f, "
              "ask median=%.4f, fee median=%.5f"
              % (len(trig), statistics.median([r["base_rate"] for r in trig]),
                 statistics.median([r["ask"] for r in trig]),
                 statistics.median([fee(r["ask"]) for r in trig])))
        gross_nets = [((1.0 if r["ftr"] == "D" else 0.0) - r["ask"])
                      for r in trig]
        print("  zero-fee stress (ask still includes 1c half-spread): "
              "median=%+.4f mean=%+.4f total=%+.4f per $ staked=%+.2f%%"
              % (statistics.median(gross_nets), statistics.fmean(gross_nets),
                 sum(gross_nets),
                 100 * sum(gross_nets) / sum(r["ask"] for r in trig)))
        spread_wide = sum(1 for r in priced if r["ask"] - r["prim_yes_last"]
                          > 0.02)
        print("Priced matches with modelled half-spread >0.02: %d / %d"
              % (spread_wide, len(priced)))
    else:
        print("Primary trigger diagnostics: no triggered matches.")
    print()

    # Brier / log loss, paired sign test on priced matches with FTR outcome.
    scored = [r for r in good if r["prim_yes_last"] is not None
              and r["base_rate"] is not None]
    if scored:
        bs_b, bs_m, ll_b, ll_m = [], [], [], []
        for r in scored:
            y = 1.0 if r["ftr"] == "D" else 0.0
            pb, pm = r["base_rate"], r["prim_yes_last"]
            bs_b.append(brier(pb, y))
            bs_m.append(brier(pm, y))
            ll_b.append(logloss(pb, y))
            ll_m.append(logloss(pm, y))
        n = len(scored)
        print("Probability scores on %d priced matches (outcome = FTR):" % n)
        print("  Brier base=%.5f market=%.5f  (market loss - base loss=%+.5f)"
              % (statistics.fmean(bs_b), statistics.fmean(bs_m),
                 statistics.fmean(bs_m) - statistics.fmean(bs_b)))
        print("  LogLoss base=%.5f market=%.5f  (market loss - base loss=%+.5f)"
              % (statistics.fmean(ll_b), statistics.fmean(ll_m),
                 statistics.fmean(ll_m) - statistics.fmean(ll_b)))
        db = [m - b for b, m in zip(bs_b, bs_m)]
        dl = [m - b for b, m in zip(ll_b, ll_m)]
        pb_pos, pb_neg, pb_p = sign_test(db)
        pl_pos, pl_neg, pl_p = sign_test(dl)
        print("  Brier sign test: base better %d, market better %d, ties %d, "
              "two-sided p=%.4f" % (pb_pos, pb_neg, n - pb_pos - pb_neg, pb_p))
        print("  LogLoss sign test: base better %d, market better %d, ties %d, "
              "two-sided p=%.4f" % (pl_pos, pl_neg, n - pl_pos - pl_neg, pl_p))
        for code in LEAGUES:
            sub = [r for r in scored if r["league"] == code]
            if not sub:
                continue
            bb = [brier(r["base_rate"], 1.0 if r["ftr"] == "D" else 0.0)
                  for r in sub]
            mm = [brier(r["prim_yes_last"], 1.0 if r["ftr"] == "D" else 0.0)
                  for r in sub]
            print("    %s n=%d Brier base=%.5f market=%.5f"
                  % (code, len(sub), statistics.fmean(bb), statistics.fmean(mm)))
    else:
        print("Probability scores: no scored matches.")
    print()

    # Verdict.
    if s_all["n"] < 30:
        verdict = "INSUFFICIENT"
        why = "triggered %d < 30" % s_all["n"]
    elif s_all["median"] <= 0:
        verdict = "FAIL"
        why = "median net/share %.4f <= 0" % s_all["median"]
    else:
        verdict = "PASS"
        why = "median net/share %.4f > 0" % s_all["median"]
    print("VERDICT: %s (%s)" % (verdict, why))
    print()

    # matches.csv
    cols = ["league", "season", "date", "kickoff_utc", "event_slug",
            "condition_id", "pm_home", "pm_away", "fd_home", "fd_away",
            "ftr", "resolved_draw", "resolution_match", "qD", "bucket",
            "base_rate", "base_n", "base_source", "trades_fetched",
            "trades_primary", "trades_sens", "prim_yes_last", "ask", "triggered",
            "net", "sens_yes_last", "sens_ask", "sens_triggered", "sens_net",
            "narrow_yes_last", "narrow_ask", "narrow_triggered", "narrow_net"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "matches.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rows:
            out = {k: r.get(k) for k in cols}
            for k in ("qD", "base_rate", "prim_yes_last", "ask", "net",
                      "sens_yes_last", "sens_ask", "sens_net",
                      "narrow_yes_last", "narrow_ask", "narrow_net"):
                if isinstance(out.get(k), float):
                    out[k] = round(out[k], 6)
            w.writerow(out)
    print("wrote matches.csv (%d rows)" % len(rows))

    # Unmatched report (also useful in REPORT).
    print("Linkage by league: " + ", ".join(
        "%s=%d" % (code, sum(1 for r in rows if r["league"] == code))
        for code in LEAGUES))
    print("Resolution match rate by league: " + ", ".join(
        "%s=%.1f%%" % (code, 100 * sum(1 for r in rows
                                       if r["league"] == code
                                       and r["resolution_match"])
                       / max(1, sum(1 for r in rows if r["league"] == code)))
        for code in LEAGUES))


if __name__ == "__main__":
    main()
